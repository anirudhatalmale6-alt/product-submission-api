#!/usr/bin/env python3
"""
10AE-A: Cluster Dominance Replication + Completeness Matrix
pethubonline.com — WordPress pet supplies blog

Builds comprehensive CLUSTER COMPLETENESS MATRICES tracking 12 dimensions
per cluster and generates dominance replication plans from the Dog Toys
reference model.
"""

import subprocess
import json
import csv
import re
import os
import sys
from collections import defaultdict
from html import unescape

# ── Configuration ──────────────────────────────────────────────────────────
WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase10ae_data"

# Priority clusters for replication (ordered)
PRIORITY_CLUSTERS = [
    "Dog Supplies", "Cat Supplies", "Dog Health", "Puppy Care",
    "Dog Harnesses", "Dog Beds", "Pet Care General"
]

# Reference authorities for dimension 12
REFERENCE_AUTHORITIES = [
    "rspca", "bva", "pdsa", "gov.uk", "battersea", "blue cross",
    "bluecross", "fediaf"
]

# ── WordPress API Fetching ─────────────────────────────────────────────────
def fetch_all_posts():
    """Fetch all published posts via WP REST API using curl."""
    all_posts = []
    page = 1
    while True:
        url = f"{WP_BASE}/posts?status=publish&per_page=100&page={page}&context=edit"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"  [WARN] curl error on page {page}: {result.stderr}")
            break
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"  [WARN] JSON decode error on page {page}")
            break
        if not isinstance(data, list) or len(data) == 0:
            break
        all_posts.extend(data)
        print(f"  Fetched page {page}: {len(data)} posts (total: {len(all_posts)})")
        if len(data) < 100:
            break
        page += 1
    return all_posts


# ── HTML / Content Utilities ───────────────────────────────────────────────
def strip_html(html_str):
    """Strip HTML tags and decode entities."""
    if not html_str:
        return ""
    text = re.sub(r'<[^>]+>', ' ', html_str)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_rendered(post, field):
    """Get rendered content from a post field."""
    val = post.get(field, "")
    if isinstance(val, dict):
        return val.get("rendered", "")
    return val or ""


# ── Cluster Classification ─────────────────────────────────────────────────
def classify_post(title):
    """Classify a post into a cluster based on title keywords."""
    t = title.lower()

    # Dog Toys — check first (most specific)
    if any(kw in t for kw in ["dog toy", "tug", "fetch", "chew toy"]):
        return "Dog Toys"
    if "enrichment" in t and "dog" in t:
        return "Dog Toys"
    if "mental stimulation" in t and "dog" in t:
        return "Dog Toys"

    # Dog Food
    if any(kw in t for kw in ["dog food", "puppy food", "dry food", "dry vs wet"]):
        return "Dog Food"

    # Dog Beds
    if "dog bed" in t:
        return "Dog Beds"

    # Dog Harnesses (not cat)
    if "harness" in t and "cat" not in t:
        return "Dog Harnesses"

    # Dog Health
    if any(kw in t for kw in ["flea", "joint supplement", "dental care", "dog health"]):
        return "Dog Health"

    # Dog Care
    if any(kw in t for kw in ["grooming", "seasonal dog", "first-time dog",
                               "dental health", "measure your dog"]):
        return "Dog Care"

    # Cat Toys
    if any(kw in t for kw in ["cat toy", "cat play"]):
        return "Cat Toys"

    # Puppy Care
    if any(kw in t for kw in ["puppy", "socialisation"]):
        return "Puppy Care"

    # Dog Supplies (check after more specific dog clusters)
    if any(kw in t for kw in ["collar", "lead", "bowl", "training treat",
                               "interactive dog", "indestructible"]):
        return "Dog Supplies"

    # Cat Supplies (not dog)
    if "cat " in t and "dog" not in t:
        return "Cat Supplies"

    # Educational
    if any(kw in t for kw in ["terminology", "glossary", "explained",
                               "enrichment", "behaviour"]):
        return "Educational"

    # Pet Care General
    if any(kw in t for kw in ["pet ", "multi-pet", "first aid", "seasonal pet"]):
        return "Pet Care General"

    # Fallback: try broader dog/cat classification
    if "dog" in t:
        return "Dog Care"
    if "cat" in t:
        return "Cat Supplies"
    if "pet" in t:
        return "Pet Care General"

    return "Uncategorized"


# ── 12 Completeness Dimensions ─────────────────────────────────────────────

def score_glossary_density(content_raw, content_text):
    """D1: Key Terms blocks + bold-dash definitions count per post."""
    score = 0
    # Key Terms / Glossary blocks
    key_terms_blocks = len(re.findall(r'(?i)(key\s+terms?|glossary|definitions?)\s*[:\-]', content_raw))
    score += min(key_terms_blocks * 20, 40)

    # Bold-dash definitions: <strong>Term</strong> – definition pattern
    bold_dash = len(re.findall(r'<strong>[^<]+</strong>\s*[–—\-]\s*\w', content_raw))
    score += min(bold_dash * 5, 40)

    # Also count <dt>/<dd> definition lists
    dl_items = len(re.findall(r'<dt[^>]*>', content_raw))
    score += min(dl_items * 5, 20)

    return min(score, 100)


def score_comparison_density(content_raw, content_text):
    """D2: wp-block-table count + 'vs' content + pro/con sections."""
    score = 0
    # Tables
    tables = len(re.findall(r'wp-block-table|<table', content_raw))
    score += min(tables * 15, 30)

    # "vs" comparisons
    vs_count = len(re.findall(r'(?i)\bvs\.?\b', content_text))
    score += min(vs_count * 5, 25)

    # Pro/Con sections
    procon = len(re.findall(r'(?i)(pros?\s*(and|&)\s*cons?|advantages?\s*(and|&)\s*disadvantages?)', content_text))
    score += min(procon * 15, 30)

    # Comparison headings
    comp_headings = len(re.findall(r'(?i)<h[2-4][^>]*>[^<]*(compar|vs\.|versus|differ)[^<]*</h[2-4]>', content_raw))
    score += min(comp_headings * 10, 15)

    return min(score, 100)


def score_trust_density(content_raw, content_text):
    """D3: Editorial standards + methodology + fact-check signals."""
    score = 0
    trust_signals = [
        r'(?i)editorial\s+standards?', r'(?i)methodology', r'(?i)fact[\s-]?check',
        r'(?i)reviewed\s+by', r'(?i)veterinar', r'(?i)expert[\s-]?reviewed',
        r'(?i)medically\s+reviewed', r'(?i)evidence[\s-]?based',
        r'(?i)peer[\s-]?reviewed', r'(?i)research\s+shows?',
        r'(?i)studies?\s+(show|suggest|indicate|found)',
        r'(?i)according\s+to', r'(?i)source[sd]?\s*:',
        r'(?i)reference[sd]?\s*:', r'(?i)disclaimer',
        r'(?i)last\s+updated', r'(?i)written\s+by',
        r'(?i)certified', r'(?i)qualified',
    ]
    for pattern in trust_signals:
        matches = len(re.findall(pattern, content_text))
        if matches > 0:
            score += min(matches * 6, 12)

    return min(score, 100)


def score_faq_density(content_raw, content_text):
    """D4: FAQ blocks + question-headings per post."""
    score = 0
    # FAQ schema / blocks
    faq_blocks = len(re.findall(r'(?i)(faq|frequently\s+asked|common\s+questions)', content_raw))
    score += min(faq_blocks * 10, 30)

    # Question headings (h2/h3/h4 containing ?)
    q_headings = len(re.findall(r'<h[2-4][^>]*>[^<]*\?[^<]*</h[2-4]>', content_raw))
    score += min(q_headings * 8, 40)

    # Standalone questions in text (sentences ending with ?)
    questions = len(re.findall(r'[A-Z][^.!?]*\?', content_text))
    score += min(questions * 3, 30)

    return min(score, 100)


def score_practical_usefulness(content_raw, content_text):
    """D5: Checklists + step-by-step + tips + examples."""
    score = 0
    # Checklists / bullet lists
    list_items = len(re.findall(r'<li[^>]*>', content_raw))
    score += min(list_items * 2, 25)

    # Step-by-step / numbered instructions
    steps = len(re.findall(r'(?i)(step\s+\d|step-by-step|how\s+to)', content_text))
    score += min(steps * 8, 25)

    # Tips / Pro tips
    tips = len(re.findall(r'(?i)(top\s+tip|pro\s+tip|quick\s+tip|tip\s*:|\btips?\b)', content_text))
    score += min(tips * 5, 20)

    # Examples
    examples = len(re.findall(r'(?i)(for\s+example|e\.g\.|such\s+as|example\s*:)', content_text))
    score += min(examples * 5, 15)

    # Actionable language
    actionable = len(re.findall(r'(?i)(you\s+should|we\s+recommend|make\s+sure|always\s+check|look\s+for)', content_text))
    score += min(actionable * 3, 15)

    return min(score, 100)


def score_educational_breadth(content_raw, content_text):
    """D6: Word count + heading count + topic variety."""
    score = 0
    # Word count scoring
    words = len(content_text.split())
    if words >= 3000:
        score += 35
    elif words >= 2000:
        score += 28
    elif words >= 1500:
        score += 22
    elif words >= 1000:
        score += 15
    elif words >= 500:
        score += 8
    else:
        score += 3

    # Heading count
    headings = len(re.findall(r'<h[2-6][^>]*>', content_raw))
    score += min(headings * 3, 30)

    # Topic variety (unique heading texts)
    heading_texts = re.findall(r'<h[2-6][^>]*>([^<]+)</h[2-6]>', content_raw)
    unique_topics = len(set(h.strip().lower() for h in heading_texts))
    score += min(unique_topics * 3, 25)

    # Images (visual education)
    images = len(re.findall(r'<img\s', content_raw))
    score += min(images * 2, 10)

    return min(score, 100)


def score_semantic_overlap(content_text, all_cluster_terms):
    """D7: Cross-referencing terminology with other clusters."""
    score = 0
    # Count how many other cluster keyword sets appear in this post
    for cluster_name, terms in all_cluster_terms.items():
        overlap_count = 0
        for term in terms:
            if term.lower() in content_text.lower():
                overlap_count += 1
        if overlap_count > 0:
            score += min(overlap_count * 5, 15)

    return min(score, 100)


def score_ai_answer_coverage(content_raw, content_text):
    """D8: Quick-answer blocks + FAQ + structured Q&A."""
    score = 0
    # Quick answer / TL;DR / summary blocks
    quick = len(re.findall(r'(?i)(quick\s+answer|tl;?\s*dr|in\s+short|at\s+a\s+glance|summary|key\s+takeaway)', content_text))
    score += min(quick * 10, 30)

    # Structured Q&A pairs
    qa_pairs = len(re.findall(r'<h[2-4][^>]*>[^<]*\?[^<]*</h[2-4]>', content_raw))
    score += min(qa_pairs * 8, 30)

    # Schema markup hints
    schema = len(re.findall(r'(?i)(itemtype|schema\.org|FAQPage|HowTo)', content_raw))
    score += min(schema * 10, 20)

    # Direct answer patterns
    direct = len(re.findall(r'(?i)(the\s+answer\s+is|short\s+answer|simply\s+put)', content_text))
    score += min(direct * 8, 20)

    return min(score, 100)


def score_citation_confidence(content_raw, content_text):
    """D9: External references + source quality + extractability."""
    score = 0
    # External links
    ext_links = len(re.findall(r'href=["\']https?://(?!pethubonline\.com)', content_raw))
    score += min(ext_links * 5, 30)

    # Named sources / citations
    citations = len(re.findall(r'(?i)(according\s+to|study\s+(by|from|published)|research\s+(by|from)|source\s*:)', content_text))
    score += min(citations * 8, 30)

    # Reference sections
    ref_sections = len(re.findall(r'(?i)(references?|sources?|bibliography|further\s+reading)\s*:?\s*$', content_text))
    score += min(ref_sections * 15, 20)

    # Specific data/numbers (extractable facts)
    data_points = len(re.findall(r'\d+%|\d+\s*(mg|kg|lbs?|calories?|grams?|ounces?|hours?|minutes?|days?|weeks?|months?|years?)', content_text))
    score += min(data_points * 3, 20)

    return min(score, 100)


def score_authority_balance(content_raw, site_url="pethubonline.com"):
    """D10: Inbound/outbound internal link ratio."""
    score = 0
    # Internal links (outbound from this post to other site pages)
    internal_out = len(re.findall(rf'href=["\']https?://{re.escape(site_url)}[^"\']*["\']', content_raw))
    # Also catch relative links
    internal_out += len(re.findall(r'href=["\']\/[^"\']*["\']', content_raw))

    # Score based on internal linking
    if internal_out >= 8:
        score += 50
    elif internal_out >= 5:
        score += 40
    elif internal_out >= 3:
        score += 30
    elif internal_out >= 1:
        score += 15

    # External outbound (authority signals)
    external_out = len(re.findall(r'href=["\']https?://(?!' + re.escape(site_url) + r')[^"\']+["\']', content_raw))
    if external_out >= 5:
        score += 30
    elif external_out >= 3:
        score += 20
    elif external_out >= 1:
        score += 10

    # Balance bonus: having both internal and external
    if internal_out >= 3 and external_out >= 2:
        score += 20

    return min(score, 100)


def score_crawl_reinforcement(content_raw, content_text):
    """D11: Sitemap presence + internal link depth."""
    score = 0
    # Internal links count as crawl paths
    internal_links = len(re.findall(r'href=["\'](?:https?://pethubonline\.com|/)[^"\']*["\']', content_raw))
    score += min(internal_links * 5, 40)

    # Navigation aids (TOC, breadcrumbs)
    toc = len(re.findall(r'(?i)(table\s+of\s+contents|jump\s+to|on\s+this\s+page)', content_text))
    score += min(toc * 15, 20)

    # Anchor links (deep linking within page)
    anchors = len(re.findall(r'href=["\']#[^"\']+["\']', content_raw))
    score += min(anchors * 5, 20)

    # Related posts / see also sections
    related = len(re.findall(r'(?i)(related\s+(posts?|articles?|reads?)|see\s+also|you\s+might\s+also|read\s+more)', content_text))
    score += min(related * 10, 20)

    return min(score, 100)


def score_reference_support(content_raw, content_text):
    """D12: RSPCA, BVA, PDSA, gov.uk, Battersea, Blue Cross, FEDIAF citation count."""
    score = 0
    text_lower = (content_raw + " " + content_text).lower()

    authority_counts = {}
    for auth in REFERENCE_AUTHORITIES:
        count = text_lower.count(auth.lower())
        if count > 0:
            authority_counts[auth] = count
            score += min(count * 8, 20)

    # Bonus for diversity of authorities cited
    unique_authorities = len(authority_counts)
    if unique_authorities >= 5:
        score += 25
    elif unique_authorities >= 3:
        score += 15
    elif unique_authorities >= 2:
        score += 8
    elif unique_authorities >= 1:
        score += 4

    return min(score, 100)


# ── Cluster Term Sets (for semantic overlap) ───────────────────────────────
CLUSTER_TERMS = {
    "Dog Toys": ["chew", "tug", "fetch", "enrichment", "puzzle", "squeaky", "rubber", "rope", "interactive", "mental stimulation"],
    "Dog Food": ["kibble", "wet food", "dry food", "nutrition", "ingredients", "protein", "grain-free", "raw diet", "feeding"],
    "Dog Beds": ["orthopedic", "memory foam", "bolster", "crate bed", "washable", "cooling", "heated", "nest bed"],
    "Dog Harnesses": ["no-pull", "front-clip", "back-clip", "padded", "adjustable", "reflective", "walking"],
    "Dog Health": ["flea", "tick", "joint", "supplement", "dental", "vaccination", "worming", "arthritis"],
    "Dog Care": ["grooming", "bathing", "nail clipping", "brushing", "coat care", "seasonal", "first-time owner"],
    "Cat Toys": ["feather", "laser", "catnip", "mouse toy", "scratching", "wand", "bell"],
    "Cat Supplies": ["litter", "scratching post", "cat bed", "cat food", "cat carrier", "cat flap"],
    "Puppy Care": ["puppy", "socialisation", "training", "teething", "crate training", "house training"],
    "Dog Supplies": ["collar", "lead", "leash", "bowl", "crate", "treat", "tag", "training"],
    "Pet Care General": ["first aid", "pet insurance", "multi-pet", "seasonal", "travel", "safety"],
    "Educational": ["terminology", "glossary", "behaviour", "psychology", "learning", "explained"],
}


# ── Main Scoring Pipeline ──────────────────────────────────────────────────
def score_post(post, cluster_terms_for_overlap):
    """Score a single post across all 12 dimensions."""
    content_raw = get_rendered(post, "content")
    content_text = strip_html(content_raw)
    title = strip_html(get_rendered(post, "title"))
    cluster = classify_post(title)

    # Build overlap terms excluding own cluster
    other_cluster_terms = {k: v for k, v in cluster_terms_for_overlap.items() if k != cluster}

    scores = {
        "glossary_density": score_glossary_density(content_raw, content_text),
        "comparison_density": score_comparison_density(content_raw, content_text),
        "trust_density": score_trust_density(content_raw, content_text),
        "faq_density": score_faq_density(content_raw, content_text),
        "practical_usefulness": score_practical_usefulness(content_raw, content_text),
        "educational_breadth": score_educational_breadth(content_raw, content_text),
        "semantic_overlap": score_semantic_overlap(content_text, other_cluster_terms),
        "ai_answer_coverage": score_ai_answer_coverage(content_raw, content_text),
        "citation_confidence": score_citation_confidence(content_raw, content_text),
        "authority_balance": score_authority_balance(content_raw),
        "crawl_reinforcement": score_crawl_reinforcement(content_raw, content_text),
        "reference_support": score_reference_support(content_raw, content_text),
    }

    overall = round(sum(scores.values()) / len(scores), 1)

    if overall >= 70:
        tier = "A - Dominant"
    elif overall >= 50:
        tier = "B - Strong"
    elif overall >= 35:
        tier = "C - Developing"
    elif overall >= 20:
        tier = "D - Emerging"
    else:
        tier = "E - Minimal"

    return {
        "post_id": post.get("id"),
        "title": title,
        "cluster": cluster,
        "scores": scores,
        "overall_completeness": overall,
        "completeness_tier": tier,
        "word_count": len(content_text.split()),
    }


def aggregate_cluster_scores(post_results):
    """Aggregate post-level scores into cluster-level averages."""
    cluster_data = defaultdict(list)
    for pr in post_results:
        cluster_data[pr["cluster"]].append(pr)

    cluster_summaries = []
    for cluster_name, posts in sorted(cluster_data.items()):
        n = len(posts)
        dim_names = [
            "glossary_density", "comparison_density", "trust_density",
            "faq_density", "practical_usefulness", "educational_breadth",
            "semantic_overlap", "ai_answer_coverage", "citation_confidence",
            "authority_balance", "crawl_reinforcement", "reference_support"
        ]
        avg_scores = {}
        for dim in dim_names:
            avg_scores[dim] = round(sum(p["scores"][dim] for p in posts) / n, 1)

        overall = round(sum(avg_scores.values()) / len(avg_scores), 1)

        if overall >= 70:
            tier = "A - Dominant"
        elif overall >= 50:
            tier = "B - Strong"
        elif overall >= 35:
            tier = "C - Developing"
        elif overall >= 20:
            tier = "D - Emerging"
        else:
            tier = "E - Minimal"

        cluster_summaries.append({
            "cluster": cluster_name,
            "post_count": n,
            "scores": avg_scores,
            "overall_completeness": overall,
            "completeness_tier": tier,
        })

    return cluster_summaries


def generate_replication_actions(cluster_summaries):
    """Generate dominance replication actions from Dog Toys reference model."""
    # Find Dog Toys cluster as reference
    dog_toys = None
    for cs in cluster_summaries:
        if cs["cluster"] == "Dog Toys":
            dog_toys = cs
            break

    if not dog_toys:
        print("  [WARN] Dog Toys cluster not found! Using highest-scoring cluster as reference.")
        dog_toys = max(cluster_summaries, key=lambda x: x["overall_completeness"])

    dim_names = list(dog_toys["scores"].keys())
    dim_labels = {
        "glossary_density": "Glossary Density",
        "comparison_density": "Comparison Density",
        "trust_density": "Trust Density",
        "faq_density": "FAQ Density",
        "practical_usefulness": "Practical Usefulness",
        "educational_breadth": "Educational Breadth",
        "semantic_overlap": "Semantic Overlap",
        "ai_answer_coverage": "AI-Answer Coverage",
        "citation_confidence": "Citation Confidence",
        "authority_balance": "Authority Balance",
        "crawl_reinforcement": "Crawl Reinforcement",
        "reference_support": "Reference Support",
    }

    replication_templates = {
        "glossary_density": "Add Key Terms / Glossary blocks with bold-dash definitions to {n} posts in {cluster}",
        "comparison_density": "Add comparison tables and vs-style content sections to {n} posts in {cluster}",
        "trust_density": "Add editorial standards, fact-check badges, and expert-review signals to {n} posts in {cluster}",
        "faq_density": "Add FAQ sections with question-headings and structured Q&A to {n} posts in {cluster}",
        "practical_usefulness": "Add checklists, step-by-step guides, and pro-tip callouts to {n} posts in {cluster}",
        "educational_breadth": "Expand word count, add more subheadings, and increase topic depth in {n} posts in {cluster}",
        "semantic_overlap": "Add cross-cluster terminology and internal cross-references to {n} posts in {cluster}",
        "ai_answer_coverage": "Add quick-answer blocks, TL;DR summaries, and structured Q&A for AI extraction in {n} posts in {cluster}",
        "citation_confidence": "Add external citations, named sources, and data points to {n} posts in {cluster}",
        "authority_balance": "Improve internal linking (both inbound and outbound) across {n} posts in {cluster}",
        "crawl_reinforcement": "Add table of contents, anchor links, and related-posts sections to {n} posts in {cluster}",
        "reference_support": "Add RSPCA/BVA/PDSA/gov.uk/Battersea/Blue Cross/FEDIAF citations to {n} posts in {cluster}",
    }

    actions = []
    for cs in cluster_summaries:
        if cs["cluster"] == dog_toys["cluster"]:
            continue  # Skip reference cluster

        # Determine priority
        if cs["cluster"] in PRIORITY_CLUSTERS:
            base_priority = PRIORITY_CLUSTERS.index(cs["cluster"]) + 1
        else:
            base_priority = len(PRIORITY_CLUSTERS) + 1

        for dim in dim_names:
            dt_score = dog_toys["scores"][dim]
            cl_score = cs["scores"][dim]
            gap = round(dt_score - cl_score, 1)

            if gap > 5:  # Only flag meaningful gaps
                # Sub-prioritize by gap size
                if gap >= 30:
                    priority_label = "P1-Critical"
                elif gap >= 15:
                    priority_label = "P2-High"
                else:
                    priority_label = "P3-Medium"

                action_text = replication_templates.get(dim, f"Improve {dim} in {cs['cluster']}").format(
                    n=cs["post_count"], cluster=cs["cluster"]
                )

                actions.append({
                    "cluster": cs["cluster"],
                    "dimension": dim_labels.get(dim, dim),
                    "dog_toys_score": dt_score,
                    "cluster_score": cl_score,
                    "gap": gap,
                    "replication_action": action_text,
                    "target_posts": cs["post_count"],
                    "priority": priority_label,
                    "sort_key": (base_priority, -gap),
                })

    # Sort by priority cluster order, then by gap size (largest first)
    actions.sort(key=lambda x: x["sort_key"])
    # Remove sort_key before export
    for a in actions:
        del a["sort_key"]

    return actions, dog_toys


# ── CSV Writers ────────────────────────────────────────────────────────────
def write_cluster_matrix_csv(cluster_summaries):
    """Write Cluster_Completeness_Matrix.csv"""
    path = os.path.join(OUTPUT_DIR, "Cluster_Completeness_Matrix.csv")
    dim_names = [
        "glossary_density", "comparison_density", "trust_density",
        "faq_density", "practical_usefulness", "educational_breadth",
        "semantic_overlap", "ai_answer_coverage", "citation_confidence",
        "authority_balance", "crawl_reinforcement", "reference_support"
    ]
    headers = ["cluster", "post_count"] + dim_names + ["overall_completeness", "completeness_tier"]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for cs in sorted(cluster_summaries, key=lambda x: -x["overall_completeness"]):
            row = {
                "cluster": cs["cluster"],
                "post_count": cs["post_count"],
                "overall_completeness": cs["overall_completeness"],
                "completeness_tier": cs["completeness_tier"],
            }
            for dim in dim_names:
                row[dim] = cs["scores"][dim]
            writer.writerow(row)

    print(f"  Written: {path}")
    return path


def write_replication_csv(actions):
    """Write Dominance_Replication_Actions.csv"""
    path = os.path.join(OUTPUT_DIR, "Dominance_Replication_Actions.csv")
    headers = ["cluster", "dimension", "dog_toys_score", "cluster_score", "gap",
               "replication_action", "target_posts", "priority"]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for action in actions:
            writer.writerow(action)

    print(f"  Written: {path}")
    return path


def write_per_post_csv(post_results):
    """Write Per_Post_Completeness.csv"""
    path = os.path.join(OUTPUT_DIR, "Per_Post_Completeness.csv")
    dim_names = [
        "glossary_density", "comparison_density", "trust_density",
        "faq_density", "practical_usefulness", "educational_breadth",
        "semantic_overlap", "ai_answer_coverage", "citation_confidence",
        "authority_balance", "crawl_reinforcement", "reference_support"
    ]
    headers = ["post_id", "title", "cluster"] + dim_names + ["overall_completeness", "completeness_tier"]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for pr in sorted(post_results, key=lambda x: (x["cluster"], -x["overall_completeness"])):
            row = {
                "post_id": pr["post_id"],
                "title": pr["title"],
                "cluster": pr["cluster"],
                "overall_completeness": pr["overall_completeness"],
                "completeness_tier": pr["completeness_tier"],
            }
            for dim in dim_names:
                row[dim] = pr["scores"][dim]
            writer.writerow(row)

    print(f"  Written: {path}")
    return path


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    print("=" * 80)
    print("10AE-A: CLUSTER DOMINANCE REPLICATION + COMPLETENESS MATRIX")
    print("pethubonline.com")
    print("=" * 80)

    # Step 1: Fetch all posts
    print("\n[1/5] Fetching all published posts from WordPress API...")
    posts = fetch_all_posts()
    if not posts:
        print("  ERROR: No posts fetched. Check API credentials and connectivity.")
        sys.exit(1)
    print(f"  Total posts fetched: {len(posts)}")

    # Step 2: Classify and score each post
    print("\n[2/5] Scoring all posts across 12 completeness dimensions...")
    post_results = []
    for i, post in enumerate(posts):
        result = score_post(post, CLUSTER_TERMS)
        post_results.append(result)
        if (i + 1) % 25 == 0:
            print(f"  Scored {i + 1}/{len(posts)} posts...")
    print(f"  All {len(post_results)} posts scored.")

    # Step 3: Aggregate to cluster level
    print("\n[3/5] Aggregating cluster-level completeness scores...")
    cluster_summaries = aggregate_cluster_scores(post_results)

    # Cluster distribution
    print(f"\n  Cluster Distribution ({len(cluster_summaries)} clusters):")
    for cs in sorted(cluster_summaries, key=lambda x: -x["post_count"]):
        print(f"    {cs['cluster']:25s}  {cs['post_count']:3d} posts  |  Overall: {cs['overall_completeness']:5.1f}  |  {cs['completeness_tier']}")

    # Step 4: Generate replication actions
    print("\n[4/5] Generating dominance replication plan from Dog Toys reference...")
    actions, dog_toys_ref = generate_replication_actions(cluster_summaries)
    print(f"  Reference cluster: {dog_toys_ref['cluster']} (overall: {dog_toys_ref['overall_completeness']})")
    print(f"  Replication actions generated: {len(actions)}")

    # Step 5: Write CSVs
    print("\n[5/5] Writing output CSVs...")
    write_cluster_matrix_csv(cluster_summaries)
    write_replication_csv(actions)
    write_per_post_csv(post_results)

    # ── Comprehensive Summary ──────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("COMPREHENSIVE SUMMARY")
    print("=" * 80)

    print(f"\nTotal Posts Analyzed: {len(post_results)}")
    print(f"Total Clusters: {len(cluster_summaries)}")
    print(f"Reference Model: {dog_toys_ref['cluster']} (Overall: {dog_toys_ref['overall_completeness']})")

    # Dog Toys reference scores
    print(f"\n--- Dog Toys Reference Scores (12 Dimensions) ---")
    dim_labels_ordered = [
        ("glossary_density", "Glossary Density"),
        ("comparison_density", "Comparison Density"),
        ("trust_density", "Trust Density"),
        ("faq_density", "FAQ Density"),
        ("practical_usefulness", "Practical Usefulness"),
        ("educational_breadth", "Educational Breadth"),
        ("semantic_overlap", "Semantic Overlap"),
        ("ai_answer_coverage", "AI-Answer Coverage"),
        ("citation_confidence", "Citation Confidence"),
        ("authority_balance", "Authority Balance"),
        ("crawl_reinforcement", "Crawl Reinforcement"),
        ("reference_support", "Reference Support"),
    ]
    for key, label in dim_labels_ordered:
        val = dog_toys_ref["scores"][key]
        bar = "#" * int(val / 2)
        print(f"  {label:25s}  {val:5.1f}  {bar}")

    # Tier distribution
    print(f"\n--- Cluster Tier Distribution ---")
    tier_counts = defaultdict(int)
    for cs in cluster_summaries:
        tier_counts[cs["completeness_tier"]] += 1
    for tier in ["A - Dominant", "B - Strong", "C - Developing", "D - Emerging", "E - Minimal"]:
        count = tier_counts.get(tier, 0)
        print(f"  {tier:20s}  {count} cluster(s)")

    # Priority cluster gaps
    print(f"\n--- Priority Cluster Gaps vs Dog Toys ---")
    for prio_name in PRIORITY_CLUSTERS:
        prio_cs = next((cs for cs in cluster_summaries if cs["cluster"] == prio_name), None)
        if prio_cs:
            gap = round(dog_toys_ref["overall_completeness"] - prio_cs["overall_completeness"], 1)
            status = "AHEAD" if gap < 0 else f"GAP: {gap}"
            print(f"  {prio_name:25s}  Overall: {prio_cs['overall_completeness']:5.1f}  |  {status}  |  {prio_cs['completeness_tier']}")
        else:
            print(f"  {prio_name:25s}  (no posts found)")

    # Top replication actions
    print(f"\n--- Top 20 Replication Actions (by priority + gap size) ---")
    for i, action in enumerate(actions[:20]):
        print(f"  {i+1:2d}. [{action['priority']:11s}] {action['cluster']:20s} | {action['dimension']:22s} | Gap: {action['gap']:5.1f} | {action['replication_action'][:80]}")

    # Post-level tier distribution
    print(f"\n--- Post-Level Tier Distribution ---")
    post_tiers = defaultdict(int)
    for pr in post_results:
        post_tiers[pr["completeness_tier"]] += 1
    for tier in ["A - Dominant", "B - Strong", "C - Developing", "D - Emerging", "E - Minimal"]:
        count = post_tiers.get(tier, 0)
        pct = round(100 * count / len(post_results), 1) if post_results else 0
        print(f"  {tier:20s}  {count:3d} posts  ({pct}%)")

    # Top 10 highest-scoring posts
    print(f"\n--- Top 10 Highest-Scoring Posts ---")
    top_posts = sorted(post_results, key=lambda x: -x["overall_completeness"])[:10]
    for i, pr in enumerate(top_posts):
        print(f"  {i+1:2d}. [{pr['overall_completeness']:5.1f}] {pr['cluster']:20s} | {pr['title'][:60]}")

    # Bottom 10 lowest-scoring posts
    print(f"\n--- Bottom 10 Lowest-Scoring Posts (improvement targets) ---")
    bottom_posts = sorted(post_results, key=lambda x: x["overall_completeness"])[:10]
    for i, pr in enumerate(bottom_posts):
        print(f"  {i+1:2d}. [{pr['overall_completeness']:5.1f}] {pr['cluster']:20s} | {pr['title'][:60]}")

    # Dimension-level weakest clusters
    print(f"\n--- Weakest Cluster per Dimension ---")
    for key, label in dim_labels_ordered:
        weakest = min(cluster_summaries, key=lambda x: x["scores"][key])
        print(f"  {label:25s}  Weakest: {weakest['cluster']:20s} ({weakest['scores'][key]:5.1f})")

    print(f"\n--- Output Files ---")
    print(f"  1. {OUTPUT_DIR}/Cluster_Completeness_Matrix.csv")
    print(f"  2. {OUTPUT_DIR}/Dominance_Replication_Actions.csv")
    print(f"  3. {OUTPUT_DIR}/Per_Post_Completeness.csv")

    print("\n" + "=" * 80)
    print("10AE-A COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
