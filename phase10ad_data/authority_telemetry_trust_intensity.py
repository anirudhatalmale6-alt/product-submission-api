#!/usr/bin/env python3
"""
10AD-H: Live Authority Telemetry Evolution + Trust Intensity Scoring
pethubonline.com — WordPress pet supplies blog

Two combined engines:
A) Live Authority Telemetry — real-time semantic authority operations visibility across all clusters
B) Trust Intensity Scoring — trust depth per page and per cluster

Output CSVs:
1. Trust_Intensity_Scores.csv — per-post trust intensity across 8 dimensions
2. Authority_Telemetry_Dashboard.csv — per-cluster authority telemetry metrics
3. Trust_Cluster_Rankings.csv — cluster rankings with priority actions
"""

import subprocess
import json
import csv
import re
import os
import sys
from collections import defaultdict
from html.parser import HTMLParser
from urllib.parse import urlparse

# ── Configuration ──────────────────────────────────────────────────────────
WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase10ad_data"

# ── HTML Stripping ─────────────────────────────────────────────────────────
class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fed = []
        self.links = []
        self._current_href = None

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            attrs_dict = dict(attrs)
            href = attrs_dict.get('href', '')
            if href:
                self.links.append(href)

    def handle_data(self, data):
        self.fed.append(data)

    def get_text(self):
        return ' '.join(self.fed)

    def get_links(self):
        return self.links


def strip_html(html_content):
    """Return (plain_text, list_of_links) from HTML."""
    stripper = HTMLStripper()
    stripper.feed(html_content or "")
    return stripper.get_text(), stripper.get_links()


def fetch_wp_api(endpoint):
    """Fetch from WordPress API using curl subprocess."""
    url = f"{WP_BASE}{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"  [WARN] curl failed for {url}: {result.stderr[:200]}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  [WARN] JSON decode failed for {url}: {result.stdout[:200]}")
        return None


def fetch_all_posts():
    """Paginate through all published posts."""
    all_posts = []
    page = 1
    while True:
        print(f"  Fetching posts page {page}...")
        data = fetch_wp_api(f"/posts?status=publish&per_page=100&page={page}&context=edit")
        if data is None or not isinstance(data, list) or len(data) == 0:
            break
        all_posts.extend(data)
        print(f"    Got {len(data)} posts (total: {len(all_posts)})")
        if len(data) < 100:
            break
        page += 1
    return all_posts


# ── Cluster Classification ─────────────────────────────────────────────────
CLUSTER_RULES = [
    ("Dog Toys",       ["dog toy", "dog toys", "chew toy", "tug toy", "fetch toy", "puzzle toy for dog", "indestructible toy"]),
    ("Dog Food",       ["dog food", "dog diet", "dog nutrition", "kibble", "raw dog food", "grain-free dog", "best food for dog", "dog treat", "dog treats"]),
    ("Dog Beds",       ["dog bed", "dog beds", "orthopedic bed", "dog mattress", "dog crate pad", "dog sleeping"]),
    ("Dog Harnesses",  ["dog harness", "dog harnesses", "no-pull harness", "dog lead", "dog leash", "dog collar", "dog walking"]),
    ("Dog Health",     ["dog health", "dog vet", "dog vaccination", "dog flea", "dog tick", "dog worm", "dog dental", "dog allergy", "dog illness", "dog symptom", "dog medication"]),
    ("Dog Care",       ["dog groom", "dog grooming", "dog bath", "dog nail", "dog brush", "dog shedding", "dog coat care", "dog ear clean"]),
    ("Cat Toys",       ["cat toy", "cat toys", "cat play", "laser toy cat", "feather toy", "interactive cat"]),
    ("Cat Supplies",   ["cat supply", "cat supplies", "cat litter", "cat bed", "cat tree", "cat scratcher", "cat food", "cat bowl", "cat carrier"]),
    ("Puppy Care",     ["puppy", "puppies", "new puppy", "puppy training", "puppy food", "puppy toy", "puppy crate", "housetraining"]),
    ("Dog Supplies",   ["dog supply", "dog supplies", "dog bowl", "dog crate", "dog kennel", "dog gate", "dog pen", "dog accessory", "dog accessories"]),
    ("Pet Care General", ["pet care", "pet health", "pet insurance", "pet safety", "pet travel", "pet first aid", "pet owner"]),
    ("Educational",    ["guide", "how to", "what is", "tips for", "beginner", "complete guide", "everything you need to know", "explained"]),
]


def classify_cluster(title, content_text):
    """Classify a post into a cluster based on title + content keywords."""
    combined = (title + " " + content_text[:2000]).lower()
    best_cluster = "Pet Care General"
    best_score = 0
    for cluster_name, keywords in CLUSTER_RULES:
        score = 0
        for kw in keywords:
            # Title matches count 3x
            if kw in title.lower():
                score += 3
            if kw in combined:
                score += 1
        if score > best_score:
            best_score = score
            best_cluster = cluster_name
    return best_cluster


# ── Trust Intensity Dimensions ──────────────────────────────────────────────

AUTHORITY_DOMAINS = [
    "rspca.org", "bva.co.uk", "gov.uk", "pdsa.org", "bluecross.org",
    "aspca.org", "avma.org", "vet.cornell.edu", "akc.org", "petmd.com",
    "merckvetmanual.com", "ncbi.nlm.nih.gov", "pubmed", "nature.com",
    "sciencedirect.com", "springer.com", "wiley.com", "who.int",
    "fda.gov", "nih.gov", "cdc.gov", "rvc.ac.uk", "veterinary",
    "university", ".edu", ".gov", "journal", "research"
]


def score_methodology_visibility(text_lower, html_lower):
    """Dimension 1: Methodology Visibility (0-100)."""
    signals = [
        "methodology", "how we test", "our process", "our approach",
        "testing process", "evaluation criteria", "scoring system",
        "how we evaluate", "how we review", "review process",
        "selection criteria", "how we chose", "how we selected",
        "we tested", "we reviewed", "we evaluated", "we compared",
        "hands-on testing", "real-world testing", "in-depth review"
    ]
    score = 0
    for s in signals:
        if s in text_lower:
            score += 15
    return min(score, 100)


def score_editorial_transparency(text_lower, html_lower):
    """Dimension 2: Editorial Transparency (0-100)."""
    signals = [
        "editorial standards", "editorial policy", "editorial team",
        "editor", "reviewed by", "fact-checked", "fact checked",
        "medically reviewed", "vet reviewed", "veterinarian reviewed",
        "expert reviewed", "written by", "author", "contributor",
        "editorial guidelines", "editorial process", "our team"
    ]
    score = 0
    for s in signals:
        if s in text_lower:
            score += 12
    return min(score, 100)


def score_disclosure_visibility(text_lower, html_lower):
    """Dimension 3: Disclosure Visibility (0-100)."""
    signals = [
        "affiliate disclosure", "sponsored", "disclaimer",
        "advertising", "affiliate link", "commission", "earn a commission",
        "affiliate program", "paid partnership", "disclosure",
        "we may earn", "at no extra cost", "no additional cost",
        "support our work", "helps us keep", "ftc"
    ]
    score = 0
    for s in signals:
        if s in text_lower:
            score += 12
    # Check for disclosure HTML blocks
    if "disclosure" in html_lower and ("<div" in html_lower or "<p" in html_lower):
        score += 15
    return min(score, 100)


def score_ai_transparency(text_lower, html_lower):
    """Dimension 4: AI Transparency (0-100)."""
    signals = [
        "ai-generated", "ai transparency", "ai-assisted", "machine learning",
        "artificial intelligence", "ai tool", "chatgpt", "ai content",
        "ai disclosure", "generated with ai", "ai-powered",
        "language model", "automated content"
    ]
    score = 0
    for s in signals:
        if s in text_lower:
            score += 20
    return min(score, 100)


def score_correction_visibility(text_lower, html_lower):
    """Dimension 5: Correction Visibility (0-100)."""
    signals = [
        "correction", "updated", "corrected", "errata", "revision",
        "last updated", "originally published", "update:",
        "editor's note", "editors note", "updated on",
        "revised", "amended", "this article was updated"
    ]
    score = 0
    for s in signals:
        if s in text_lower:
            score += 15
    return min(score, 100)


def score_reference_support(links):
    """Dimension 6: Reference Support — external authority links (0-100)."""
    authority_count = 0
    for link in links:
        link_lower = link.lower()
        for domain in AUTHORITY_DOMAINS:
            if domain in link_lower:
                authority_count += 1
                break
    if authority_count == 0:
        return 0
    elif authority_count == 1:
        return 20
    elif authority_count == 2:
        return 35
    elif authority_count <= 4:
        return 55
    elif authority_count <= 7:
        return 75
    elif authority_count <= 10:
        return 90
    else:
        return 100


def score_educational_clarity(text_lower, html_lower):
    """Dimension 7: Educational Clarity — plain language, beginner explanations (0-100)."""
    signals = [
        "what this means", "in simple terms", "put simply",
        "for beginners", "beginner", "explained", "what is",
        "how does", "why does", "step by step", "step-by-step",
        "easy to understand", "plain language", "in other words",
        "think of it as", "imagine", "for example", "such as",
        "here's what you need to know", "the bottom line",
        "quick tip", "pro tip", "key takeaway", "takeaways",
        "summary", "at a glance", "quick answer", "short answer"
    ]
    score = 0
    for s in signals:
        if s in text_lower:
            score += 8
    return min(score, 100)


def score_trust_block_density(html_lower):
    """Dimension 8: Trust Block Density — trust-related HTML blocks (0-100)."""
    score = 0
    # Disclosure blocks
    if re.search(r'<div[^>]*class="[^"]*disclos', html_lower):
        score += 20
    if re.search(r'<div[^>]*class="[^"]*affiliat', html_lower):
        score += 15
    # Editorial/methodology links in HTML
    trust_link_patterns = [
        r'href="[^"]*editorial', r'href="[^"]*methodology',
        r'href="[^"]*disclosure', r'href="[^"]*about-us',
        r'href="[^"]*review-process', r'href="[^"]*how-we-test'
    ]
    for pat in trust_link_patterns:
        if re.search(pat, html_lower):
            score += 10
    # Trust-related block patterns
    trust_blocks = [
        "editorial note", "author bio", "about the author",
        "reviewed by", "fact-check", "sources:", "references:",
        "further reading", "related articles"
    ]
    for tb in trust_blocks:
        if tb in html_lower:
            score += 10
    # Structured schema hints
    schema_signals = ["itemtype", "schema.org", "structured data", "json-ld"]
    for ss in schema_signals:
        if ss in html_lower:
            score += 10
    return min(score, 100)


def compute_trust_intensity(post):
    """Compute all 8 trust intensity dimensions for a post."""
    html_content = post.get("content", {}).get("rendered", "") or ""
    title = post.get("title", {}).get("rendered", "") or ""

    text, links = strip_html(html_content)
    text_lower = text.lower()
    html_lower = html_content.lower()

    dims = {
        "methodology_visibility": score_methodology_visibility(text_lower, html_lower),
        "editorial_transparency": score_editorial_transparency(text_lower, html_lower),
        "disclosure_visibility": score_disclosure_visibility(text_lower, html_lower),
        "ai_transparency": score_ai_transparency(text_lower, html_lower),
        "correction_visibility": score_correction_visibility(text_lower, html_lower),
        "reference_support": score_reference_support(links),
        "educational_clarity": score_educational_clarity(text_lower, html_lower),
        "trust_block_density": score_trust_block_density(html_lower),
    }

    overall = round(sum(dims.values()) / len(dims), 1)
    dims["overall_trust_intensity"] = overall

    return dims, text, links, html_content


# ── Authority Telemetry Metrics ─────────────────────────────────────────────

def has_faq(text_lower, html_lower):
    """Check if post has FAQ section."""
    faq_signals = ["faq", "frequently asked", "common questions", "q&a", "q & a"]
    return any(s in text_lower or s in html_lower for s in faq_signals)


def has_glossary(text_lower, html_lower):
    """Check if post has glossary/definitions."""
    signals = ["glossary", "definitions", "key terms", "terminology", "what does", "meaning of"]
    return any(s in text_lower for s in signals)


def count_internal_links(links):
    """Count internal links to pethubonline.com."""
    count = 0
    for link in links:
        link_lower = link.lower()
        if "pethubonline.com" in link_lower or link.startswith("/"):
            count += 1
    return count


def count_external_refs(links):
    """Count external reference links."""
    count = 0
    for link in links:
        link_lower = link.lower()
        if "pethubonline.com" not in link_lower and link.startswith("http"):
            count += 1
    return count


def has_comparison_table(html_lower):
    """Check if post has comparison table."""
    return "<table" in html_lower and ("vs" in html_lower or "comparison" in html_lower or "compare" in html_lower)


def has_quick_answer(text_lower, html_lower):
    """Check if post has quick answer block."""
    signals = [
        "quick answer", "short answer", "tldr", "tl;dr",
        "the bottom line", "at a glance", "in brief", "key takeaway"
    ]
    return any(s in text_lower for s in signals)


# ── Main Processing ─────────────────────────────────────────────────────────

def main():
    print("=" * 80)
    print("10AD-H: LIVE AUTHORITY TELEMETRY + TRUST INTENSITY SCORING")
    print("pethubonline.com")
    print("=" * 80)
    print()

    # ── Step 1: Fetch all posts ──
    print("[1/5] Fetching all published posts from WordPress API...")
    posts = fetch_all_posts()
    if not posts:
        print("ERROR: No posts fetched. Exiting.")
        sys.exit(1)
    print(f"  Total posts fetched: {len(posts)}")
    print()

    # ── Step 2: Analyze each post ──
    print("[2/5] Computing Trust Intensity scores for each post...")
    post_records = []
    cluster_data = defaultdict(lambda: {
        "posts": [],
        "word_counts": [],
        "trust_scores": [],
        "trust_dims": defaultdict(list),
        "faq_count": 0,
        "glossary_count": 0,
        "internal_links": [],
        "external_refs": [],
        "comparison_count": 0,
        "quick_answer_count": 0,
    })

    for i, post in enumerate(posts):
        post_id = post.get("id", 0)
        title_raw = post.get("title", {}).get("rendered", "") or ""
        # Clean HTML entities from title
        title = re.sub(r'<[^>]+>', '', title_raw)
        title = title.replace("&#8211;", "-").replace("&#8217;", "'").replace("&amp;", "&").replace("&#8220;", '"').replace("&#8221;", '"')

        # Compute trust intensity
        dims, text, links, html_content = compute_trust_intensity(post)
        html_lower = html_content.lower()
        text_lower = text.lower()

        # Classify cluster
        cluster = classify_cluster(title, text)

        # Word count
        word_count = len(text.split())

        # Build post record
        record = {
            "post_id": post_id,
            "title": title,
            "cluster": cluster,
            **dims,
        }
        post_records.append(record)

        # Accumulate cluster data
        cd = cluster_data[cluster]
        cd["posts"].append(record)
        cd["word_counts"].append(word_count)
        cd["trust_scores"].append(dims["overall_trust_intensity"])
        for dim_name in ["methodology_visibility", "editorial_transparency", "disclosure_visibility",
                         "ai_transparency", "correction_visibility", "reference_support",
                         "educational_clarity", "trust_block_density"]:
            cd["trust_dims"][dim_name].append(dims[dim_name])

        if has_faq(text_lower, html_lower):
            cd["faq_count"] += 1
        if has_glossary(text_lower, html_lower):
            cd["glossary_count"] += 1
        cd["internal_links"].append(count_internal_links(links))
        cd["external_refs"].append(count_external_refs(links))
        if has_comparison_table(html_lower):
            cd["comparison_count"] += 1
        if has_quick_answer(text_lower, html_lower):
            cd["quick_answer_count"] += 1

        if (i + 1) % 20 == 0:
            print(f"  Processed {i + 1}/{len(posts)} posts...")

    print(f"  All {len(posts)} posts analyzed.")
    print()

    # ── Step 3: Write Trust_Intensity_Scores.csv ──
    print("[3/5] Writing Trust_Intensity_Scores.csv...")
    trust_csv = os.path.join(OUTPUT_DIR, "Trust_Intensity_Scores.csv")
    trust_fields = [
        "post_id", "title", "cluster",
        "methodology_visibility", "editorial_transparency", "disclosure_visibility",
        "ai_transparency", "correction_visibility", "reference_support",
        "educational_clarity", "trust_block_density", "overall_trust_intensity"
    ]
    with open(trust_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=trust_fields)
        writer.writeheader()
        for rec in sorted(post_records, key=lambda r: r["overall_trust_intensity"], reverse=True):
            writer.writerow({k: rec[k] for k in trust_fields})
    print(f"  Written: {trust_csv} ({len(post_records)} rows)")

    # ── Step 4: Build Authority Telemetry Dashboard ──
    print("[4/5] Building Authority Telemetry Dashboard...")
    dashboard_records = []
    dimension_names = [
        "methodology_visibility", "editorial_transparency", "disclosure_visibility",
        "ai_transparency", "correction_visibility", "reference_support",
        "educational_clarity", "trust_block_density"
    ]
    dim_labels = {
        "methodology_visibility": "Methodology Visibility",
        "editorial_transparency": "Editorial Transparency",
        "disclosure_visibility": "Disclosure Visibility",
        "ai_transparency": "AI Transparency",
        "correction_visibility": "Correction Visibility",
        "reference_support": "Reference Support",
        "educational_clarity": "Educational Clarity",
        "trust_block_density": "Trust Block Density",
    }

    for cluster_name in sorted(cluster_data.keys()):
        cd = cluster_data[cluster_name]
        post_count = len(cd["posts"])
        if post_count == 0:
            continue

        avg_wc = round(sum(cd["word_counts"]) / post_count, 0)
        avg_trust = round(sum(cd["trust_scores"]) / post_count, 1)
        faq_pct = round(cd["faq_count"] / post_count * 100, 1)
        glossary_pct = round(cd["glossary_count"] / post_count * 100, 1)
        int_link_density = round(sum(cd["internal_links"]) / post_count, 1)
        ext_ref_density = round(sum(cd["external_refs"]) / post_count, 1)
        comparison_pct = round(cd["comparison_count"] / post_count * 100, 1)
        quick_answer_pct = round(cd["quick_answer_count"] / post_count * 100, 1)

        # Overall authority density — composite
        authority_density = round(
            (avg_trust * 0.30) +
            (faq_pct * 0.10) +
            (glossary_pct * 0.05) +
            (min(int_link_density * 10, 100) * 0.15) +
            (min(ext_ref_density * 10, 100) * 0.10) +
            (comparison_pct * 0.10) +
            (quick_answer_pct * 0.05) +
            (min(avg_wc / 30, 100) * 0.15),
            1
        )

        # Strongest and weakest dimension
        dim_avgs = {}
        for dn in dimension_names:
            vals = cd["trust_dims"][dn]
            dim_avgs[dn] = round(sum(vals) / len(vals), 1) if vals else 0

        strongest = max(dim_avgs, key=dim_avgs.get)
        weakest = min(dim_avgs, key=dim_avgs.get)

        dashboard_records.append({
            "cluster": cluster_name,
            "post_count": post_count,
            "avg_word_count": int(avg_wc),
            "avg_trust_intensity": avg_trust,
            "faq_coverage_pct": faq_pct,
            "glossary_coverage_pct": glossary_pct,
            "internal_link_density": int_link_density,
            "external_ref_density": ext_ref_density,
            "comparison_coverage_pct": comparison_pct,
            "quick_answer_coverage_pct": quick_answer_pct,
            "overall_authority_density": authority_density,
            "strongest_dimension": dim_labels[strongest],
            "weakest_dimension": dim_labels[weakest],
        })

    dash_csv = os.path.join(OUTPUT_DIR, "Authority_Telemetry_Dashboard.csv")
    dash_fields = [
        "cluster", "post_count", "avg_word_count", "avg_trust_intensity",
        "faq_coverage_pct", "glossary_coverage_pct", "internal_link_density",
        "external_ref_density", "comparison_coverage_pct", "quick_answer_coverage_pct",
        "overall_authority_density", "strongest_dimension", "weakest_dimension"
    ]
    with open(dash_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=dash_fields)
        writer.writeheader()
        for rec in sorted(dashboard_records, key=lambda r: r["overall_authority_density"], reverse=True):
            writer.writerow(rec)
    print(f"  Written: {dash_csv} ({len(dashboard_records)} clusters)")

    # ── Step 5: Trust Cluster Rankings ──
    print("[5/5] Building Trust Cluster Rankings...")
    ranking_records = []
    for cluster_name in sorted(cluster_data.keys()):
        cd = cluster_data[cluster_name]
        post_count = len(cd["posts"])
        if post_count == 0:
            continue

        avg_trust = round(sum(cd["trust_scores"]) / post_count, 1)
        posts_above_70 = sum(1 for s in cd["trust_scores"] if s >= 70)
        posts_below_40 = sum(1 for s in cd["trust_scores"] if s < 40)

        dim_avgs = {}
        for dn in dimension_names:
            vals = cd["trust_dims"][dn]
            dim_avgs[dn] = round(sum(vals) / len(vals), 1) if vals else 0

        strongest = max(dim_avgs, key=dim_avgs.get)
        weakest = min(dim_avgs, key=dim_avgs.get)

        # Generate priority actions
        actions = []
        if dim_avgs["methodology_visibility"] < 20:
            actions.append("Add methodology/testing process sections")
        if dim_avgs["editorial_transparency"] < 20:
            actions.append("Add editorial review/author credentials")
        if dim_avgs["disclosure_visibility"] < 30:
            actions.append("Add affiliate/advertising disclosures")
        if dim_avgs["ai_transparency"] < 10:
            actions.append("Add AI transparency disclosures if applicable")
        if dim_avgs["reference_support"] < 20:
            actions.append("Add authoritative external references (RSPCA, AVMA, etc.)")
        if dim_avgs["educational_clarity"] < 30:
            actions.append("Improve plain-language explanations and beginner context")
        if dim_avgs["trust_block_density"] < 15:
            actions.append("Add trust HTML blocks (disclosure boxes, editorial links)")
        if dim_avgs["correction_visibility"] < 15:
            actions.append("Add last-updated dates and revision notices")
        if posts_below_40 > posts_above_70:
            actions.append(f"URGENT: {posts_below_40} posts below 40 trust — prioritize trust uplift")
        if not actions:
            actions.append("Maintain current trust levels; focus on consistency")

        ranking_records.append({
            "cluster": cluster_name,
            "avg_trust_intensity": avg_trust,
            "strongest_trust_dimension": dim_labels[strongest],
            "weakest_trust_dimension": dim_labels[weakest],
            "posts_above_70_trust": posts_above_70,
            "posts_below_40_trust": posts_below_40,
            "priority_actions": " | ".join(actions[:3]),
        })

    rank_csv = os.path.join(OUTPUT_DIR, "Trust_Cluster_Rankings.csv")
    rank_fields = [
        "cluster", "avg_trust_intensity", "strongest_trust_dimension",
        "weakest_trust_dimension", "posts_above_70_trust", "posts_below_40_trust",
        "priority_actions"
    ]
    with open(rank_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rank_fields)
        writer.writeheader()
        for rec in sorted(ranking_records, key=lambda r: r["avg_trust_intensity"], reverse=True):
            writer.writerow(rec)
    print(f"  Written: {rank_csv} ({len(ranking_records)} clusters)")
    print()

    # ══════════════════════════════════════════════════════════════════════════
    # COMPREHENSIVE SUMMARY
    # ══════════════════════════════════════════════════════════════════════════
    print("=" * 80)
    print("COMPREHENSIVE AUTHORITY TELEMETRY & TRUST INTENSITY REPORT")
    print("pethubonline.com")
    print("=" * 80)
    print()

    # ── Site-Wide Trust Intensity ──
    all_trust_scores = [r["overall_trust_intensity"] for r in post_records]
    site_avg_trust = round(sum(all_trust_scores) / len(all_trust_scores), 1) if all_trust_scores else 0
    site_max = max(all_trust_scores) if all_trust_scores else 0
    site_min = min(all_trust_scores) if all_trust_scores else 0
    above_70 = sum(1 for s in all_trust_scores if s >= 70)
    above_50 = sum(1 for s in all_trust_scores if s >= 50)
    below_40 = sum(1 for s in all_trust_scores if s < 40)
    below_20 = sum(1 for s in all_trust_scores if s < 20)

    print("--- SITE-WIDE TRUST INTENSITY ---")
    print(f"  Total Posts Analyzed:       {len(post_records)}")
    print(f"  Average Trust Intensity:    {site_avg_trust}/100")
    print(f"  Highest Trust Score:        {site_max}")
    print(f"  Lowest Trust Score:         {site_min}")
    print(f"  Posts >= 70 (Strong Trust): {above_70} ({round(above_70/len(post_records)*100,1)}%)")
    print(f"  Posts >= 50 (Moderate):     {above_50} ({round(above_50/len(post_records)*100,1)}%)")
    print(f"  Posts < 40 (Weak Trust):    {below_40} ({round(below_40/len(post_records)*100,1)}%)")
    print(f"  Posts < 20 (Critical):      {below_20} ({round(below_20/len(post_records)*100,1)}%)")
    print()

    # ── Site-Wide Dimension Averages ──
    print("--- TRUST DIMENSION AVERAGES (SITE-WIDE) ---")
    site_dim_avgs = {}
    for dn in dimension_names:
        vals = [r[dn] for r in post_records]
        avg = round(sum(vals) / len(vals), 1) if vals else 0
        site_dim_avgs[dn] = avg
        bar_len = int(avg / 2)
        bar = "#" * bar_len + "." * (50 - bar_len)
        print(f"  {dim_labels[dn]:30s} {avg:5.1f}/100  [{bar}]")

    strongest_site = max(site_dim_avgs, key=site_dim_avgs.get)
    weakest_site = min(site_dim_avgs, key=site_dim_avgs.get)
    print(f"\n  STRONGEST DIMENSION: {dim_labels[strongest_site]} ({site_dim_avgs[strongest_site]})")
    print(f"  WEAKEST DIMENSION:  {dim_labels[weakest_site]} ({site_dim_avgs[weakest_site]})")
    print()

    # ── Per-Cluster Trust Rankings ──
    print("--- CLUSTER TRUST RANKINGS ---")
    sorted_rankings = sorted(ranking_records, key=lambda r: r["avg_trust_intensity"], reverse=True)
    print(f"  {'Rank':<5} {'Cluster':<22} {'Avg Trust':>10} {'>=70':>5} {'<40':>5} {'Strongest':>28} {'Weakest':>28}")
    print(f"  {'-'*4:<5} {'-'*20:<22} {'-'*9:>10} {'-'*4:>5} {'-'*4:>5} {'-'*26:>28} {'-'*26:>28}")
    for rank, rec in enumerate(sorted_rankings, 1):
        print(f"  {rank:<5} {rec['cluster']:<22} {rec['avg_trust_intensity']:>10.1f} "
              f"{rec['posts_above_70_trust']:>5} {rec['posts_below_40_trust']:>5} "
              f"{rec['strongest_trust_dimension']:>28} {rec['weakest_trust_dimension']:>28}")
    print()

    # ── Authority Telemetry Overview ──
    print("--- AUTHORITY TELEMETRY OVERVIEW ---")
    sorted_dash = sorted(dashboard_records, key=lambda r: r["overall_authority_density"], reverse=True)
    print(f"  {'Cluster':<22} {'Posts':>5} {'AvgWC':>7} {'Trust':>6} {'FAQ%':>6} {'Gloss%':>7} "
          f"{'IntLnk':>7} {'ExtRef':>7} {'Comp%':>6} {'QA%':>5} {'AuthDens':>9}")
    print(f"  {'-'*20:<22} {'-'*4:>5} {'-'*6:>7} {'-'*5:>6} {'-'*5:>6} {'-'*6:>7} "
          f"{'-'*6:>7} {'-'*6:>7} {'-'*5:>6} {'-'*4:>5} {'-'*8:>9}")
    for rec in sorted_dash:
        print(f"  {rec['cluster']:<22} {rec['post_count']:>5} {rec['avg_word_count']:>7} "
              f"{rec['avg_trust_intensity']:>6.1f} {rec['faq_coverage_pct']:>6.1f} {rec['glossary_coverage_pct']:>7.1f} "
              f"{rec['internal_link_density']:>7.1f} {rec['external_ref_density']:>7.1f} "
              f"{rec['comparison_coverage_pct']:>6.1f} {rec['quick_answer_coverage_pct']:>5.1f} "
              f"{rec['overall_authority_density']:>9.1f}")
    print()

    # ── Top 10 Highest Trust Posts ──
    print("--- TOP 10 HIGHEST TRUST INTENSITY POSTS ---")
    sorted_posts = sorted(post_records, key=lambda r: r["overall_trust_intensity"], reverse=True)
    for i, rec in enumerate(sorted_posts[:10], 1):
        print(f"  {i:2}. [{rec['overall_trust_intensity']:5.1f}] (ID:{rec['post_id']}) {rec['title'][:70]}")
        print(f"      Cluster: {rec['cluster']} | Meth:{rec['methodology_visibility']} Ed:{rec['editorial_transparency']} "
              f"Disc:{rec['disclosure_visibility']} Ref:{rec['reference_support']} Edu:{rec['educational_clarity']}")
    print()

    # ── Top 10 Lowest Trust Posts ──
    print("--- TOP 10 LOWEST TRUST INTENSITY POSTS (Priority Fix) ---")
    for i, rec in enumerate(sorted_posts[-10:][::-1], 1):
        print(f"  {i:2}. [{rec['overall_trust_intensity']:5.1f}] (ID:{rec['post_id']}) {rec['title'][:70]}")
        print(f"      Cluster: {rec['cluster']} | Meth:{rec['methodology_visibility']} Ed:{rec['editorial_transparency']} "
              f"Disc:{rec['disclosure_visibility']} Ref:{rec['reference_support']} Edu:{rec['educational_clarity']}")
    print()

    # ── Priority Actions ──
    print("--- PRIORITY ACTIONS BY CLUSTER ---")
    for rec in sorted_rankings:
        print(f"  {rec['cluster']}:")
        actions = rec["priority_actions"].split(" | ")
        for a in actions:
            print(f"    - {a}")
    print()

    # ── Recommended Next Actions ──
    print("--- RECOMMENDED NEXT ACTIONS ---")
    print()
    if site_avg_trust < 30:
        print("  1. CRITICAL: Site-wide trust intensity is very low. Prioritize adding")
        print("     disclosure blocks, editorial credentials, and methodology sections")
        print("     to ALL posts as a bulk operation.")
    elif site_avg_trust < 50:
        print("  1. IMPORTANT: Site-wide trust is moderate. Focus on uplifting the")
        print("     weakest clusters and adding missing trust dimensions systematically.")
    else:
        print("  1. GOOD: Site-wide trust is above average. Focus on consistency")
        print("     and bringing lagging posts up to the cluster average.")

    print(f"\n  2. WEAKEST DIMENSION ({dim_labels[weakest_site]}: {site_dim_avgs[weakest_site]})")
    if weakest_site == "ai_transparency":
        print("     Add AI transparency disclosures where content is AI-assisted.")
    elif weakest_site == "methodology_visibility":
        print("     Add 'How We Test' or 'Our Process' sections to product reviews.")
    elif weakest_site == "reference_support":
        print("     Add authoritative external links (RSPCA, AVMA, AKC, vet schools).")
    elif weakest_site == "trust_block_density":
        print("     Add structured trust HTML blocks: disclosure boxes, author bios, editorial links.")
    elif weakest_site == "editorial_transparency":
        print("     Add author credentials, 'reviewed by' notices, editorial standards page.")
    elif weakest_site == "correction_visibility":
        print("     Add 'last updated' dates and revision/correction notices.")
    else:
        print(f"     Focus on improving {dim_labels[weakest_site]} across all clusters.")

    print(f"\n  3. {below_40} posts are below 40 trust — these need immediate uplift:")
    low_clusters = defaultdict(int)
    for rec in post_records:
        if rec["overall_trust_intensity"] < 40:
            low_clusters[rec["cluster"]] += 1
    for cl, count in sorted(low_clusters.items(), key=lambda x: -x[1]):
        print(f"     - {cl}: {count} posts below 40")

    print(f"\n  4. CLUSTER-SPECIFIC: Focus first on clusters with lowest authority density")
    for rec in sorted_dash[-3:]:
        print(f"     - {rec['cluster']}: Authority Density {rec['overall_authority_density']}, "
              f"Weakest: {rec['weakest_dimension']}")

    print(f"\n  5. INTERNAL LINKING: Increase internal link density across all clusters")
    low_link = [r for r in sorted_dash if r["internal_link_density"] < 3]
    if low_link:
        print(f"     {len(low_link)} clusters have avg <3 internal links per post:")
        for r in low_link:
            print(f"     - {r['cluster']}: {r['internal_link_density']} avg internal links")

    print()
    print("=" * 80)
    print("OUTPUT FILES:")
    print(f"  1. {trust_csv}")
    print(f"  2. {dash_csv}")
    print(f"  3. {rank_csv}")
    print("=" * 80)
    print("10AD-H: Authority Telemetry + Trust Intensity COMPLETE")


if __name__ == "__main__":
    main()
