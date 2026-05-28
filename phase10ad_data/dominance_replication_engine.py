#!/usr/bin/env python3
"""
10AD-A: Dominance Replication Engine
pethubonline.com - WordPress Pet Supplies Blog

Compares all content clusters against the reference cluster "Dog Toys" (strongest),
identifies gaps, and generates cluster-specific reinforcement plans.
"""

import subprocess
import json
import csv
import re
import os
import sys
import html
from collections import defaultdict

# ─── Configuration ───────────────────────────────────────────────────────────

WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase10ad_data"

REFERENCE_CLUSTER = "Dog Toys"

# Cluster keyword rules (order matters - first match wins for some, but we check specificity)
CLUSTER_RULES = {
    "Dog Toys": [
        "dog toy", "tug", "fetch", "chew toy",
        "enrichment.*dog", "mental stimulation.*dog",
        "dog.*enrichment", "dog.*mental stimulation",
    ],
    "Dog Food": ["dog food", "puppy food", "dry food", "dry vs wet"],
    "Dog Beds": ["dog bed"],
    "Dog Harnesses": ["harness"],
    "Dog Health": ["flea", "joint supplement", "dental care", "dog health"],
    "Dog Care": [
        "grooming", "seasonal dog", "first-time dog", "first time dog",
        "dental health", "measure your dog",
    ],
    "Cat Toys": ["cat toy", "cat play"],
    "Cat Supplies": ["cat "],
    "Puppy Care": ["puppy", "socialisation", "socialization"],
    "Dog Supplies": [
        "collar", "lead", "bowl", "training treat",
        "interactive dog", "indestructible",
    ],
    "Pet Care General": [
        "pet ", "multi-pet", "multi pet", "first aid", "seasonal pet",
    ],
    "Educational": [
        "terminology", "glossary", "explained", "enrichment", "behaviour", "behavior",
    ],
}

# Priority classification for specific clusters
CLUSTER_PRIORITY_ORDER = [
    "Dog Toys", "Dog Food", "Dog Beds", "Dog Harnesses", "Dog Health",
    "Dog Care", "Cat Toys", "Cat Supplies", "Puppy Care", "Dog Supplies",
    "Pet Care General", "Educational",
]

DIMENSIONS = [
    "Trust Density",
    "FAQ Coverage",
    "Glossary Coverage",
    "Comparison Tables",
    "Practical Guidance",
    "External References",
    "Internal Links",
    "Answer Readiness",
    "Educational Depth",
    "Trust Intensity",
]

TRUSTED_DOMAINS = [
    "rspca.org", "bva.co.uk", "fediaf.org", "battersea.org",
    "cats.org.uk", "gov.uk", "pdsa.org", "bluecross.org",
]


# ─── API Fetching ────────────────────────────────────────────────────────────

def fetch_all_posts():
    """Fetch all published posts via curl with pagination."""
    all_posts = []
    page = 1
    while True:
        url = f"{WP_API}/posts?status=publish&per_page=100&page={page}&context=edit"
        print(f"  Fetching page {page}...", end=" ", flush=True)
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            print(f"CURL ERROR: {result.stderr}")
            break
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"JSON PARSE ERROR on page {page}")
            break
        if not isinstance(data, list) or len(data) == 0:
            print("empty batch, done.")
            break
        print(f"got {len(data)} posts")
        all_posts.extend(data)
        if len(data) < 100:
            break
        page += 1
    return all_posts


# ─── Cluster Classification ─────────────────────────────────────────────────

def classify_post(title):
    """Classify a post into a cluster based on title keywords. Returns cluster name."""
    title_lower = title.lower()

    # Check specific clusters first (order matters for specificity)
    # "Dog Beds" must be checked before generic "bed" matching
    # "Cat Toys" before generic "cat "
    # "Dog Harnesses" needs to exclude cat harnesses

    for cluster_name in CLUSTER_PRIORITY_ORDER:
        keywords = CLUSTER_RULES[cluster_name]
        for kw in keywords:
            # Handle regex patterns
            if ".*" in kw:
                if re.search(kw, title_lower):
                    # Exclusions
                    if cluster_name == "Dog Harnesses" and "cat" in title_lower:
                        continue
                    if cluster_name == "Dog Beds" and "cat" in title_lower:
                        continue
                    return cluster_name
            else:
                if kw in title_lower:
                    # Exclusions
                    if cluster_name == "Dog Harnesses" and "cat" in title_lower:
                        continue
                    if cluster_name == "Dog Beds" and "cat" in title_lower:
                        continue
                    if cluster_name == "Cat Supplies" and "dog" in title_lower:
                        continue
                    return cluster_name

    return "Unclassified"


# ─── Scoring Functions ───────────────────────────────────────────────────────

def strip_html(text):
    """Strip HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    return text


def score_trust_density(content):
    """Dimension 1: 'Editorial Standards' or 'editorial methodology' in content."""
    content_lower = content.lower()
    hits = 0
    if "editorial standards" in content_lower:
        hits += 1
    if "editorial methodology" in content_lower:
        hits += 1
    if "editorial policy" in content_lower:
        hits += 1
    if "fact-check" in content_lower or "fact check" in content_lower:
        hits += 1
    if "reviewed by" in content_lower or "medically reviewed" in content_lower:
        hits += 1
    # Score: 0 hits=0, 1 hit=40, 2 hits=65, 3+=85, 5=100
    scores = {0: 0, 1: 40, 2: 65, 3: 85, 4: 95, 5: 100}
    return min(scores.get(hits, 100), 100)


def score_faq_coverage(content):
    """Dimension 2: FAQ / h3 headings count."""
    content_lower = content.lower()
    faq_block = len(re.findall(r'wp:yoast-seo/faq-block|wp-block-yoast-faq|class="faq"', content_lower))
    h3_count = len(re.findall(r'<h3[^>]*>', content_lower))
    faq_headings = len(re.findall(r'<h[23][^>]*>[^<]*(?:faq|frequently asked|common question)', content_lower))
    total = faq_block * 3 + h3_count + faq_headings * 2
    # Normalize: 0=0, 3=30, 6=50, 10=70, 15+=90, 20+=100
    if total == 0:
        return 0
    return min(int((total / 15) * 100), 100)


def score_glossary_coverage(content):
    """Dimension 3: Key Terms block + definition count (<strong>X</strong> - pattern)."""
    content_lower = content.lower()
    key_terms = 1 if "key terms" in content_lower or "glossary" in content_lower else 0
    definitions = len(re.findall(r'<strong>[^<]+</strong>\s*[—–\-–—]\s*', content))
    total = key_terms * 5 + definitions
    if total == 0:
        return 0
    return min(int((total / 12) * 100), 100)


def score_comparison_tables(content):
    """Dimension 4: wp-block-table count."""
    table_count = len(re.findall(r'wp-block-table|<table', content.lower()))
    if table_count == 0:
        return 0
    return min(int((table_count / 3) * 100), 100)


def score_practical_guidance(content):
    """Dimension 5: Checklists, ordered lists, practical examples."""
    content_lower = content.lower()
    checklists = len(re.findall(r'checklist|check list|✓|✅|☑', content_lower))
    ordered_lists = len(re.findall(r'<ol', content_lower))
    ul_lists = len(re.findall(r'<ul', content_lower))
    step_patterns = len(re.findall(r'step \d|step-by-step|how to', content_lower))
    practical = len(re.findall(r'practical|example|tip:|pro tip|quick tip', content_lower))
    total = checklists * 2 + ordered_lists + ul_lists + step_patterns * 2 + practical
    if total == 0:
        return 0
    return min(int((total / 12) * 100), 100)


def score_external_references(content):
    """Dimension 6: Trusted external domain references."""
    hits = 0
    content_lower = content.lower()
    for domain in TRUSTED_DOMAINS:
        count = content_lower.count(domain)
        hits += count
    if hits == 0:
        return 0
    return min(int((hits / 5) * 100), 100)


def score_internal_links(content):
    """Dimension 7: href='https://pethubonline.com/' count."""
    links = len(re.findall(r'href=["\']https?://pethubonline\.com/', content.lower()))
    if links == 0:
        return 0
    return min(int((links / 8) * 100), 100)


def score_answer_readiness(content):
    """Dimension 8: FAQ + quick answer blocks + structured answers."""
    content_lower = content.lower()
    faq = len(re.findall(r'faq|frequently asked', content_lower))
    quick_answer = len(re.findall(r'quick answer|short answer|in brief|tldr|tl;dr|at a glance', content_lower))
    structured = len(re.findall(r'<h[23][^>]*>.*\?</h[23]>', content_lower))
    total = faq * 2 + quick_answer * 3 + structured
    if total == 0:
        return 0
    return min(int((total / 10) * 100), 100)


def score_educational_depth(content):
    """Dimension 9: Word count, heading count, list blocks."""
    plain = strip_html(content)
    word_count = len(plain.split())
    headings = len(re.findall(r'<h[1-6][^>]*>', content.lower()))
    lists = len(re.findall(r'<[ou]l', content.lower()))
    # Word count score component (2000+ words = full marks)
    wc_score = min(word_count / 2000, 1.0) * 40
    # Headings score component (10+ = full marks)
    h_score = min(headings / 10, 1.0) * 30
    # Lists score component (5+ = full marks)
    l_score = min(lists / 5, 1.0) * 30
    return min(int(wc_score + h_score + l_score), 100)


def score_trust_intensity(content):
    """Dimension 10: methodology links + editorial links + corrections links + AI transparency + disclosure."""
    content_lower = content.lower()
    hits = 0
    hits += len(re.findall(r'methodology', content_lower))
    hits += len(re.findall(r'editorial', content_lower))
    hits += len(re.findall(r'correction', content_lower))
    hits += len(re.findall(r'ai transparency|ai.generated|ai disclosure', content_lower))
    hits += len(re.findall(r'disclosure|affiliate disclosure|sponsored', content_lower))
    hits += len(re.findall(r'updated on|last updated|reviewed on', content_lower))
    if hits == 0:
        return 0
    return min(int((hits / 8) * 100), 100)


SCORING_FUNCTIONS = [
    score_trust_density,
    score_faq_coverage,
    score_glossary_coverage,
    score_comparison_tables,
    score_practical_guidance,
    score_external_references,
    score_internal_links,
    score_answer_readiness,
    score_educational_depth,
    score_trust_intensity,
]


def score_post(content):
    """Score a single post across all 10 dimensions. Returns list of 10 scores."""
    return [fn(content) for fn in SCORING_FUNCTIONS]


# ─── Main Engine ─────────────────────────────────────────────────────────────

def main():
    print("=" * 72)
    print("  10AD-A: DOMINANCE REPLICATION ENGINE")
    print("  pethubonline.com | Reference Cluster: Dog Toys")
    print("=" * 72)
    print()

    # Step 1: Fetch all posts
    print("[1/5] Fetching all published posts...")
    posts = fetch_all_posts()
    print(f"  Total posts fetched: {len(posts)}")
    print()

    if not posts:
        print("ERROR: No posts fetched. Exiting.")
        sys.exit(1)

    # Step 2: Classify posts into clusters
    print("[2/5] Classifying posts into clusters...")
    clusters = defaultdict(list)
    for post in posts:
        title_raw = post.get("title", {})
        if isinstance(title_raw, dict):
            title = title_raw.get("rendered", title_raw.get("raw", ""))
        else:
            title = str(title_raw)
        title = html.unescape(title)

        content_raw = post.get("content", {})
        if isinstance(content_raw, dict):
            content = content_raw.get("rendered", content_raw.get("raw", ""))
        else:
            content = str(content_raw)

        cluster = classify_post(title)
        clusters[cluster].append({
            "id": post.get("id"),
            "title": title,
            "content": content,
            "slug": post.get("slug", ""),
            "link": post.get("link", ""),
        })

    for name in sorted(clusters.keys()):
        print(f"  {name}: {len(clusters[name])} posts")
    print()

    # Step 3: Score all posts
    print("[3/5] Scoring all posts across 10 dimensions...")
    cluster_scores = {}  # cluster -> list of (post_info, scores_list)
    for cluster_name, posts_in_cluster in clusters.items():
        scored = []
        for p in posts_in_cluster:
            scores = score_post(p["content"])
            scored.append((p, scores))
        cluster_scores[cluster_name] = scored

    # Step 4: Compute reference model (Dog Toys average scores)
    print("[4/5] Computing reference model from Dog Toys cluster...")
    ref_posts = cluster_scores.get(REFERENCE_CLUSTER, [])
    if not ref_posts:
        print(f"  WARNING: No posts found in '{REFERENCE_CLUSTER}' cluster!")
        ref_avg = [0.0] * 10
    else:
        ref_avg = [0.0] * 10
        for _, scores in ref_posts:
            for i in range(10):
                ref_avg[i] += scores[i]
        ref_avg = [s / len(ref_posts) for s in ref_avg]

    print(f"  Dog Toys reference ({len(ref_posts)} posts):")
    for i, dim in enumerate(DIMENSIONS):
        print(f"    {dim}: {ref_avg[i]:.1f}")
    print()

    # ─── CSV 1: Dominance Reference Model (Dog Toys per-post scores) ─────
    csv1_path = os.path.join(OUTPUT_DIR, "Dominance_Reference_Model.csv")
    with open(csv1_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["Post ID", "Title", "Slug", "Link"] + DIMENSIONS + ["Average Score"]
        writer.writerow(header)
        for p, scores in ref_posts:
            avg = sum(scores) / len(scores) if scores else 0
            row = [p["id"], p["title"], p["slug"], p["link"]] + scores + [round(avg, 1)]
            writer.writerow(row)
    print(f"  CSV 1 written: {csv1_path}")

    # Step 5: Gap analysis and reinforcement plans
    print("[5/5] Computing gap analysis and reinforcement plans...")
    print()

    gap_rows = []
    plan_rows = []

    for cluster_name in CLUSTER_PRIORITY_ORDER:
        if cluster_name == REFERENCE_CLUSTER:
            continue
        scored_posts = cluster_scores.get(cluster_name, [])
        if not scored_posts:
            continue

        # Compute cluster average
        cluster_avg = [0.0] * 10
        for _, scores in scored_posts:
            for i in range(10):
                cluster_avg[i] += scores[i]
        cluster_avg = [s / len(scored_posts) for s in cluster_avg]

        # Calculate gaps
        gaps = []
        for i in range(10):
            gap = ref_avg[i] - cluster_avg[i]
            priority = "Critical" if gap > 30 else "High" if gap > 15 else "Medium" if gap > 5 else "Low"
            gaps.append((DIMENSIONS[i], ref_avg[i], cluster_avg[i], gap, priority))
            gap_rows.append([
                cluster_name, DIMENSIONS[i],
                round(ref_avg[i], 1), round(cluster_avg[i], 1),
                round(gap, 1), priority,
            ])

        # Sort gaps by size descending for reinforcement plan
        sorted_gaps = sorted(gaps, key=lambda x: x[3], reverse=True)
        for rank, (dim, ref_score, cl_score, gap, priority) in enumerate(sorted_gaps, 1):
            if gap <= 0:
                continue  # No action needed if cluster matches or exceeds reference
            action = generate_action(cluster_name, dim, gap, cl_score)
            plan_rows.append([
                cluster_name, dim, round(gap, 1), action, rank,
            ])

    # Also handle Unclassified if present
    if "Unclassified" in cluster_scores and cluster_scores["Unclassified"]:
        scored_posts = cluster_scores["Unclassified"]
        cluster_avg = [0.0] * 10
        for _, scores in scored_posts:
            for i in range(10):
                cluster_avg[i] += scores[i]
        cluster_avg = [s / len(scored_posts) for s in cluster_avg]
        for i in range(10):
            gap = ref_avg[i] - cluster_avg[i]
            priority = "Critical" if gap > 30 else "High" if gap > 15 else "Medium" if gap > 5 else "Low"
            gap_rows.append([
                "Unclassified", DIMENSIONS[i],
                round(ref_avg[i], 1), round(cluster_avg[i], 1),
                round(gap, 1), priority,
            ])

    # ─── CSV 2: Cluster Gap Analysis ─────────────────────────────────────
    csv2_path = os.path.join(OUTPUT_DIR, "Cluster_Gap_Analysis.csv")
    with open(csv2_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Cluster", "Dimension", "Dog Toys Score", "Cluster Score", "Gap", "Priority"])
        for row in gap_rows:
            writer.writerow(row)
    print(f"  CSV 2 written: {csv2_path}")

    # ─── CSV 3: Reinforcement Plans ──────────────────────────────────────
    csv3_path = os.path.join(OUTPUT_DIR, "Reinforcement_Plans.csv")
    with open(csv3_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Cluster", "Dimension", "Gap", "Action Items", "Priority Rank"])
        for row in plan_rows:
            writer.writerow(row)
    print(f"  CSV 3 written: {csv3_path}")
    print()

    # ─── Summary Report ──────────────────────────────────────────────────
    print("=" * 72)
    print("  DOMINANCE REPLICATION ENGINE — SUMMARY REPORT")
    print("=" * 72)
    print()
    print(f"Total posts analyzed: {len(posts)}")
    print(f"Clusters identified: {len(clusters)}")
    print(f"Reference cluster: {REFERENCE_CLUSTER} ({len(ref_posts)} posts)")
    print()

    print("REFERENCE MODEL (Dog Toys Average Scores):")
    print("-" * 50)
    for i, dim in enumerate(DIMENSIONS):
        bar = "#" * int(ref_avg[i] / 5)
        print(f"  {dim:25s} {ref_avg[i]:5.1f}  {bar}")
    ref_overall = sum(ref_avg) / len(ref_avg) if ref_avg else 0
    print(f"  {'OVERALL':25s} {ref_overall:5.1f}")
    print()

    print("CLUSTER COMPARISON (Average Overall Score):")
    print("-" * 60)
    print(f"  {'Cluster':25s} {'Score':>7s} {'Gap':>7s} {'Status'}")
    print(f"  {'-'*25:25s} {'-'*7:>7s} {'-'*7:>7s} {'-'*12}")

    for cluster_name in CLUSTER_PRIORITY_ORDER + ["Unclassified"]:
        scored_posts = cluster_scores.get(cluster_name, [])
        if not scored_posts:
            continue
        cluster_avg = [0.0] * 10
        for _, scores in scored_posts:
            for i in range(10):
                cluster_avg[i] += scores[i]
        cluster_avg = [s / len(scored_posts) for s in cluster_avg]
        overall = sum(cluster_avg) / 10
        gap = ref_overall - overall
        if cluster_name == REFERENCE_CLUSTER:
            status = "REFERENCE"
        elif gap > 20:
            status = "CRITICAL GAP"
        elif gap > 10:
            status = "NEEDS WORK"
        elif gap > 0:
            status = "MINOR GAP"
        else:
            status = "ON PAR"
        print(f"  {cluster_name:25s} {overall:7.1f} {gap:+7.1f} {status}")

    print()
    print("TOP CRITICAL GAPS (gap > 15):")
    print("-" * 60)
    critical_gaps = [r for r in gap_rows if r[4] > 15]
    critical_gaps.sort(key=lambda r: r[4], reverse=True)
    for row in critical_gaps[:20]:
        print(f"  {row[0]:25s} | {row[1]:25s} | Gap: {row[4]:+.1f} ({row[5]})")

    if not critical_gaps:
        print("  None found.")

    print()
    print(f"Files generated:")
    print(f"  1. {csv1_path}")
    print(f"  2. {csv2_path}")
    print(f"  3. {csv3_path}")
    print()
    print("Engine complete.")


def generate_action(cluster_name, dimension, gap, current_score):
    """Generate specific actionable steps based on cluster, dimension, and gap size."""
    actions = {
        "Trust Density": [
            f"Add 'Editorial Standards' section to all {cluster_name} posts",
            "Include 'editorial methodology' reference in post footer",
            "Add 'Reviewed by' or 'Fact-checked' attribution",
            "Link to site-wide editorial policy page",
        ],
        "FAQ Coverage": [
            f"Add FAQ section with 3-5 questions to each {cluster_name} post",
            "Use H3 headings for each FAQ question",
            "Structure FAQs with schema markup for rich snippets",
            "Cover common customer questions specific to this topic",
        ],
        "Glossary Coverage": [
            f"Add 'Key Terms' block to each {cluster_name} post",
            "Use <strong>Term</strong> - Definition format for 5+ terms per post",
            "Include niche-specific terminology relevant to the cluster",
            "Cross-link glossary terms between posts in the cluster",
        ],
        "Comparison Tables": [
            f"Add at least 1 comparison table per {cluster_name} post",
            "Use wp-block-table for structured product/feature comparisons",
            "Include columns for price range, features, pros/cons",
            "Add tables comparing top-rated items in the category",
        ],
        "Practical Guidance": [
            f"Add step-by-step guides or checklists to {cluster_name} posts",
            "Include ordered lists for how-to instructions",
            "Add 'Quick Tips' or 'Pro Tips' callout boxes",
            "Provide practical examples with real product recommendations",
        ],
        "External References": [
            f"Add citations from RSPCA, BVA, PDSA to {cluster_name} posts",
            "Link to gov.uk pet regulations where relevant",
            "Reference Battersea, Blue Cross, or FEDIAF guidelines",
            "Cite cats.org.uk for cat-related content or general pet welfare bodies",
        ],
        "Internal Links": [
            f"Add 3-5 internal links per {cluster_name} post to related content",
            "Cross-link between cluster posts (hub and spoke model)",
            "Link to pillar pages and related cluster posts",
            "Ensure every post links to at least 2 other pethubonline.com pages",
        ],
        "Answer Readiness": [
            f"Add 'Quick Answer' summary box at top of {cluster_name} posts",
            "Include FAQ blocks with structured question-answer format",
            "Add 'At a Glance' or 'TL;DR' sections",
            "Format answers to match Google featured snippet patterns",
        ],
        "Educational Depth": [
            f"Expand {cluster_name} posts to 1500+ words minimum",
            "Add more H2/H3 subheadings for detailed topic coverage",
            "Include bulleted and numbered lists for better structure",
            "Add more subsections covering related subtopics",
        ],
        "Trust Intensity": [
            f"Add methodology disclosure to {cluster_name} posts",
            "Include editorial process links and AI transparency notes",
            "Add 'Last Updated' dates and correction policy links",
            "Include affiliate disclosure and sponsored content notices",
        ],
    }

    dim_actions = actions.get(dimension, ["Review and improve this dimension"])

    # Select actions based on gap severity
    if gap > 30:
        selected = dim_actions  # All actions for critical gaps
    elif gap > 15:
        selected = dim_actions[:3]  # Top 3 for high gaps
    else:
        selected = dim_actions[:2]  # Top 2 for medium gaps

    return " | ".join(selected)


if __name__ == "__main__":
    main()
