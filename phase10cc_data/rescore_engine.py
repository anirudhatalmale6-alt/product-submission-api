#!/usr/bin/env python3
"""
Phase 10CC Re-Scoring Engine for PetHub Online (pethubonline.com)
=================================================================
Fetches all 168 published posts from WordPress, analyzes Gutenberg content,
scores across Citation Preference / Authority Moat / AI Answer Preference
dimensions, and generates all 27 deliverable CSVs.

Usage:  python3 rescore_engine.py
"""

import csv
import json
import math
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from statistics import mean

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
WP_API = "https://pethubonline.com/wp-json/wp/v2"
WP_AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase10cc_data"
CITATION_CSV = "/var/lib/freelancer/projects/40416335/phase10br_data/citation_preference.csv"
COMPETITOR_CSV = "/var/lib/freelancer/projects/40416335/phase10cb_data/competitor_analysis.csv"
DISPLACEMENT_CSV = "/var/lib/freelancer/projects/40416335/phase10cb_data/displacement_summary.csv"

MAX_RETRIES = 3
RETRY_BACKOFF = 5  # seconds * attempt

UK_AUTHORITIES = [
    "RSPCA", "BVA", "PFMA", "PDSA", "Blue Cross", "RVC", "FEDIAF",
    "Battersea", "Kennel Club", "Cats Protection", "iCatCare", "DEFRA",
]

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# WordPress API helpers
# ---------------------------------------------------------------------------
def wp_get(endpoint, params=None):
    """GET from WordPress REST API with rate-limiting and retry logic."""
    url = f"{WP_API}/{endpoint}"
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"

    for attempt in range(1, MAX_RETRIES + 1):
        time.sleep(2)  # mandatory pre-request delay
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", WP_AUTH, url],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            print(f"  [WARN] curl failed (attempt {attempt}): {result.stderr[:200]}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF * attempt)
                continue
            return None

        body = result.stdout.strip()
        if not body:
            print(f"  [WARN] empty response (attempt {attempt})")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF * attempt)
                continue
            return None

        # Check for 429 Too Many Requests
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            print(f"  [WARN] JSON decode error (attempt {attempt}): {body[:200]}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF * attempt)
                continue
            return None

        if isinstance(data, dict) and data.get("code") == "rest_too_many_requests":
            print(f"  [429] Rate limited, backing off {RETRY_BACKOFF * attempt}s …")
            time.sleep(RETRY_BACKOFF * attempt)
            continue

        return data

    print("  [ERROR] All retries exhausted")
    return None


def fetch_all_posts():
    """Fetch all published posts (context=edit for raw content)."""
    all_posts = []
    for page in [1, 2]:
        print(f"Fetching posts page {page} …")
        data = wp_get("posts", {
            "per_page": "100",
            "page": str(page),
            "status": "publish",
            "context": "edit",
        })
        if data is None:
            print(f"  [ERROR] Failed to fetch page {page}")
            continue
        if isinstance(data, dict) and "code" in data:
            # Might be last page with error
            print(f"  Page {page} returned: {data.get('code')}")
            break
        all_posts.extend(data)
        print(f"  Got {len(data)} posts from page {page}")
    print(f"Total posts fetched: {len(all_posts)}")
    return all_posts


# ---------------------------------------------------------------------------
# Cluster assignment from previous phase
# ---------------------------------------------------------------------------
def load_cluster_map():
    """Load id->cluster from phase10br citation_preference.csv."""
    cluster_map = {}
    if not os.path.exists(CITATION_CSV):
        print(f"[WARN] {CITATION_CSV} not found – cluster fallback only")
        return cluster_map
    with open(CITATION_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                cluster_map[int(row["id"])] = row["cluster"]
            except (ValueError, KeyError):
                pass
    print(f"Loaded {len(cluster_map)} cluster assignments from CSV")
    return cluster_map


def determine_cluster(post, cluster_map, categories_map):
    """Get cluster for a post: prefer CSV, fallback to WP category."""
    pid = post["id"]
    if pid in cluster_map:
        return cluster_map[pid]
    # Fallback: use first WP category name
    cat_ids = post.get("categories", [])
    for cid in cat_ids:
        if cid in categories_map:
            return categories_map[cid]
    return "Uncategorized"


def fetch_categories():
    """Fetch all WP categories for fallback cluster mapping."""
    cats = {}
    print("Fetching categories …")
    data = wp_get("categories", {"per_page": "100"})
    if data and isinstance(data, list):
        for c in data:
            cats[c["id"]] = c["name"]
        print(f"  Loaded {len(cats)} categories")
    return cats


# ---------------------------------------------------------------------------
# Content analysis helpers
# ---------------------------------------------------------------------------
def count_uk_authorities(content):
    """Count distinct named UK institutions referenced in content."""
    text_upper = content.upper()
    count = 0
    for auth in UK_AUTHORITIES:
        if auth.upper() in text_upper:
            count += 1
    return count


def count_comparison_tables(content):
    """Count tables with is-style-stripes class (HTML figure or Gutenberg comment)."""
    # HTML figure style: <figure class="wp-block-table is-style-stripes">
    html_count = len(re.findall(r'<figure[^>]*wp-block-table[^>]*is-style-stripes', content, re.IGNORECASE))
    # Gutenberg comment style: <!-- wp:table {"className":"is-style-stripes"} -->
    gb_count = len(re.findall(r'wp:table\s[^}]*"className"\s*:\s*"[^"]*is-style-stripes', content))
    # Also count any plain <table> tags as a fallback signal
    plain_tables = len(re.findall(r'<table[\s>]', content, re.IGNORECASE))
    # Use max of specific detections, but at minimum count plain tables
    stripes = html_count + gb_count
    if stripes > 0:
        return stripes
    # If no striped tables but plain tables exist, count those (less weight in scoring)
    return plain_tables


def has_block_pattern(content, pattern):
    """Check if a heading or block contains the given text (case-insensitive)."""
    return bool(re.search(pattern, content, re.IGNORECASE))


def count_heading_matches(content, patterns):
    """Count how many h2/h3 headings match any of the given patterns."""
    headings = re.findall(r'<h[23][^>]*>(.*?)</h[23]>', content, re.IGNORECASE | re.DOTALL)
    count = 0
    for h in headings:
        for p in patterns:
            if re.search(p, h, re.IGNORECASE):
                count += 1
                break
    return count


def count_structured_elements(content):
    """Count tables, ul, ol, blockquotes, h2, h3, h4."""
    tags = ["table", "ul", "ol", "blockquote", "h2", "h3", "h4"]
    total = 0
    for tag in tags:
        total += len(re.findall(f'<{tag}[\\s>]', content, re.IGNORECASE))
    return total


def count_gutenberg_block_types(content):
    """Count distinct block types (Gutenberg comments + HTML wp-block classes)."""
    # Gutenberg comment blocks: <!-- wp:paragraph -->
    gb_blocks = set(re.findall(r'<!-- wp:(\w+(?:/\w+)?)', content))
    # HTML class-based blocks: class="wp-block-table", class="wp-block-heading" etc.
    html_blocks = set(re.findall(r'wp-block-(\w+)', content))
    # Also detect semantic HTML elements used as structural blocks
    html_elements = set()
    for tag in ["table", "ul", "ol", "blockquote", "figure", "details", "summary"]:
        if re.search(f'<{tag}[\\s>]', content, re.IGNORECASE):
            html_elements.add(tag)
    for level in range(1, 7):
        if re.search(f'<h{level}[\\s>]', content, re.IGNORECASE):
            html_elements.add(f"heading-h{level}")
    if re.search(r'<img[\s>]', content, re.IGNORECASE):
        html_elements.add("image")
    all_types = gb_blocks | html_blocks | html_elements
    return len(all_types)


def count_li_in_section(content, section_heading):
    """Count <li> items following a heading that matches section_heading."""
    # Find the section start
    pattern = re.compile(
        r'<h[234][^>]*>[^<]*' + re.escape(section_heading) + r'[^<]*</h[234]>(.*?)(?=<h[234]|$)',
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(content)
    if not match:
        # Try a looser match
        pattern2 = re.compile(
            section_heading + r'.*?</h[234]>(.*?)(?=<h[234]|$)',
            re.IGNORECASE | re.DOTALL,
        )
        match = pattern2.search(content)
    if match:
        section = match.group(1)
        return len(re.findall(r'<li', section, re.IGNORECASE))
    return 0


# ---------------------------------------------------------------------------
# Scoring dimensions
# ---------------------------------------------------------------------------

# --- Citation Preference dimensions ---

def score_reference_quality(content):
    refs = count_uk_authorities(content)
    if refs == 0:
        score = 30
    elif refs == 1:
        score = 50
    elif refs == 2:
        score = 60
    elif refs == 3:
        score = 70
    elif refs == 4:
        score = 80
    else:
        score = 90
    if has_block_pattern(content, r'Research Sources and Standards'):
        score += 5
    return min(score, 100)


def score_comparison_usefulness(content):
    tables = count_comparison_tables(content)
    if tables == 0:
        score = 30
    elif tables == 1:
        score = 55
    elif tables == 2:
        score = 70
    elif tables == 3:
        score = 80
    else:
        score = 90
    # Bonus for comparison headings
    if count_heading_matches(content, [r'Compared', r'Comparison']):
        score += 5
    return min(score, 100)


def score_practical_specificity(content):
    if has_block_pattern(content, r'Step-by-Step|Practical Guide'):
        score = 60
    else:
        score = 30
    # Bonus for numbered steps (ol/li)
    if re.search(r'<ol', content, re.IGNORECASE):
        score += 10
    # Bonus for "Step 1"/"Step 2" patterns
    if re.search(r'Step\s+[12]', content, re.IGNORECASE):
        score += 10
    # Bonus for measurable detail (numbers, timelines, percentages)
    measurable_patterns = [
        r'\d+\s*%', r'\d+\s*ml', r'\d+\s*kg', r'\d+\s*mg',
        r'\d+\s*minutes?', r'\d+\s*hours?', r'\d+\s*days?',
        r'\d+\s*weeks?', r'\d+\s*months?', r'\d+\s*years?',
        r'£\d+', r'\d+\s*calories',
    ]
    measurable_count = 0
    for mp in measurable_patterns:
        if re.search(mp, content, re.IGNORECASE):
            measurable_count += 1
    if measurable_count >= 2:
        score += 10
    return min(score, 100)


def score_extractability(content):
    if has_block_pattern(content, r'At a Glance'):
        score = 70
    else:
        score = 40
    if has_block_pattern(content, r'Key Takeaways'):
        score += 10
    # Clear bullet structure (ul/li with strong tags)
    if re.search(r'<ul[^>]*>.*?<li[^>]*>.*?<strong', content, re.IGNORECASE | re.DOTALL):
        score += 10
    if has_block_pattern(content, r'Decision Summary'):
        score += 10
    return min(score, 100)


def score_trust_depth(content):
    score = 40
    if has_block_pattern(content, r'Why We Reference Sources'):
        score += 15
    if has_block_pattern(content, r'Research Sources and Standards'):
        score += 15
    # Trust footer pattern
    if has_block_pattern(content, r'trust|editorial standards|fact.?check'):
        score += 10
    if has_block_pattern(content, r'How We Evaluated|methodology'):
        score += 10
    refs = count_uk_authorities(content)
    if refs >= 1:
        score += 10
    return min(score, 100)


def score_summary_usefulness(content):
    score = 40
    if has_block_pattern(content, r'At a Glance'):
        score += 15
    if has_block_pattern(content, r'Key Takeaways'):
        score += 15
    if has_block_pattern(content, r'Decision Summary'):
        score += 10
    if has_block_pattern(content, r'What to Do Next'):
        score += 10
    # Structured conclusion
    if has_block_pattern(content, r'Conclusion|Final Thoughts|Summary'):
        score += 10
    return min(score, 100)


# --- Authority Moat dimensions ---

def score_glossary_moat(content):
    if has_block_pattern(content, r'Key Terms'):
        score = 70
        terms = count_li_in_section(content, "Key Terms")
        score += min((terms // 5) * 10, 30)
    else:
        score = 30
    return min(score, 100)


def score_educational_moat(content):
    patterns = [r'Guide', r'Explained', r'Understanding', r'How to']
    matches = count_heading_matches(content, patterns)
    if matches == 0:
        return 40
    elif matches <= 2:
        return 60
    elif matches <= 4:
        return 75
    else:
        return 90


def score_citation_moat(content):
    refs = count_uk_authorities(content)
    if refs == 0:
        return 30
    elif refs <= 2:
        return 50
    elif refs <= 5:
        return 70
    elif refs <= 8:
        return 80
    else:
        return 90


def score_structural_moat(content):
    types = count_gutenberg_block_types(content)
    if types <= 3:
        return 40
    elif types <= 5:
        return 55
    elif types <= 7:
        return 70
    elif types <= 9:
        return 80
    else:
        return 90


# ---------------------------------------------------------------------------
# Full post scoring
# ---------------------------------------------------------------------------

def score_post(content):
    """Score a single post across all dimensions. Returns dict of scores."""
    # Citation Preference dimensions
    ref_q = score_reference_quality(content)
    comp_u = score_comparison_usefulness(content)
    prac_s = score_practical_specificity(content)
    extr = score_extractability(content)
    trust_d = score_trust_depth(content)
    summ_u = score_summary_usefulness(content)
    citation_score = round(mean([ref_q, comp_u, prac_s, extr, trust_d, summ_u]), 1)

    # Authority Moat dimensions
    gloss_m = score_glossary_moat(content)
    trust_m = trust_d  # same logic as trust_depth
    comp_m = comp_u    # same logic as comparison_usefulness
    prac_m = prac_s    # same logic as practical_specificity
    edu_m = score_educational_moat(content)
    cit_m = score_citation_moat(content)
    struct_m = score_structural_moat(content)
    moat_score = round(mean([gloss_m, trust_m, comp_m, prac_m, edu_m, cit_m, struct_m]), 1)

    # AI Answer Preference dimensions
    answer_sup = round(mean([extr, prac_s, summ_u]), 1)
    extraction_sup = score_extraction_superiority(content)
    comp_sup = comp_u  # same as comparison_usefulness
    trust_sup = trust_d  # same as trust_depth
    useful_sup = prac_s  # same as practical_specificity
    ai_pref = round(mean([answer_sup, extraction_sup, comp_sup, trust_sup, useful_sup]), 1)

    # Additional detection flags
    has_practical_guide = has_block_pattern(content, r'Step-by-Step|Practical Guide')
    has_decision_pathway = has_block_pattern(content, r'Decision Summary|Decision Pathway|What to Do Next')
    has_troubleshooting = has_block_pattern(content, r'Troubleshooting|Common Problems|Common Issues')
    comparison_table_count = count_comparison_tables(content)
    trust_blocks = sum([
        1 if has_block_pattern(content, r'Why We Reference Sources') else 0,
        1 if has_block_pattern(content, r'Research Sources and Standards') else 0,
        1 if has_block_pattern(content, r'How We Evaluated|methodology') else 0,
        1 if has_block_pattern(content, r'trust|editorial standards|fact.?check') else 0,
    ])
    named_refs = count_uk_authorities(content)

    # Semantic elements
    glossary_terms = count_li_in_section(content, "Key Terms")
    faq_items = count_heading_matches(content, [r'\?'])
    practical_guides = 1 if has_practical_guide else 0

    return {
        # Citation Preference
        "reference_quality": ref_q,
        "comparison_usefulness": comp_u,
        "practical_specificity": prac_s,
        "extractability": extr,
        "trust_depth": trust_d,
        "summary_usefulness": summ_u,
        "citation_score": citation_score,
        # Authority Moat
        "glossary_moat": gloss_m,
        "trust_moat": trust_m,
        "comparison_moat": comp_m,
        "practical_moat": prac_m,
        "educational_moat": edu_m,
        "citation_moat": cit_m,
        "structural_moat": struct_m,
        "moat_score": moat_score,
        # AI Answer Preference
        "answer_superiority": answer_sup,
        "extraction_superiority": extraction_sup,
        "comparison_superiority": comp_sup,
        "trust_superiority": trust_sup,
        "usefulness_superiority": useful_sup,
        "ai_preference_score": ai_pref,
        # Detection flags
        "has_practical_guide": has_practical_guide,
        "has_decision_pathway": has_decision_pathway,
        "has_troubleshooting": has_troubleshooting,
        "comparison_table_count": comparison_table_count,
        "trust_blocks_count": trust_blocks,
        "named_refs_count": named_refs,
        "glossary_terms": glossary_terms,
        "faq_items": faq_items,
        "practical_guides": practical_guides,
    }


def score_extraction_superiority(content):
    """Count structured elements and map to score."""
    count = count_structured_elements(content)
    if count <= 5:
        return 40
    elif count <= 10:
        return 55
    elif count <= 15:
        return 70
    elif count <= 20:
        return 80
    else:
        return 90


# ---------------------------------------------------------------------------
# CSV writers
# ---------------------------------------------------------------------------

def write_csv(filename, rows, fieldnames):
    """Write rows to CSV using DictWriter for safe quoting."""
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"  Wrote {filename} ({len(rows)} rows)")


# --- 10CC-A: Citation Dominance ---
def generate_10cc_a(scored_posts):
    fields = ["id", "title", "cluster", "reference_quality", "comparison_usefulness",
              "practical_specificity", "extractability", "trust_depth", "summary_usefulness",
              "citation_score"]

    # 1. Citation Dominance Report (all posts)
    write_csv("Citation_Dominance_Report.csv", scored_posts, fields)

    # 2. Citation Leaderboard (top 30)
    top30 = sorted(scored_posts, key=lambda x: x["citation_score"], reverse=True)[:30]
    write_csv("Citation_Leaderboard.csv", top30, fields)

    # 3. Pages above 90
    above90 = [p for p in scored_posts if p["citation_score"] >= 90]
    above90.sort(key=lambda x: x["citation_score"], reverse=True)
    write_csv("Pages_Above_90.csv", above90, fields)


# --- 10CC-B: Comparison Coverage ---
def generate_10cc_b(scored_posts):
    # 4. Comparison Coverage per post
    fields = ["id", "title", "cluster", "comparison_table_count", "comparison_score"]
    rows = []
    for p in scored_posts:
        rows.append({
            "id": p["id"],
            "title": p["title"],
            "cluster": p["cluster"],
            "comparison_table_count": p["comparison_table_count"],
            "comparison_score": p["comparison_usefulness"],
        })
    write_csv("Comparison_Coverage.csv", rows, fields)

    # 5. Comparison Gap Report (score < 70)
    gaps = [r for r in rows if r["comparison_score"] < 70]
    gaps.sort(key=lambda x: x["comparison_score"])
    write_csv("Comparison_Gap_Report.csv", gaps, fields)

    # 6. Comparison Dominance Report per cluster
    cluster_data = defaultdict(lambda: {"scores": [], "tables": 0, "with_tables": 0, "total": 0})
    for p in scored_posts:
        c = p["cluster"]
        cluster_data[c]["scores"].append(p["comparison_usefulness"])
        cluster_data[c]["tables"] += p["comparison_table_count"]
        cluster_data[c]["total"] += 1
        if p["comparison_table_count"] > 0:
            cluster_data[c]["with_tables"] += 1

    cfields = ["cluster", "avg_comparison_score", "total_tables", "posts_with_tables", "coverage_pct"]
    crows = []
    for cluster, d in sorted(cluster_data.items()):
        crows.append({
            "cluster": cluster,
            "avg_comparison_score": round(mean(d["scores"]), 1),
            "total_tables": d["tables"],
            "posts_with_tables": d["with_tables"],
            "coverage_pct": round(d["with_tables"] / d["total"] * 100, 1) if d["total"] else 0,
        })
    write_csv("Comparison_Dominance_Report.csv", crows, cfields)


# --- 10CC-C: Practical Guidance ---
def generate_10cc_c(scored_posts):
    # 7. Practical Guidance Scores
    fields = ["id", "title", "cluster", "has_practical_guide", "has_decision_pathway",
              "has_troubleshooting", "practical_score"]
    rows = []
    for p in scored_posts:
        rows.append({
            "id": p["id"],
            "title": p["title"],
            "cluster": p["cluster"],
            "has_practical_guide": "yes" if p["has_practical_guide"] else "no",
            "has_decision_pathway": "yes" if p["has_decision_pathway"] else "no",
            "has_troubleshooting": "yes" if p["has_troubleshooting"] else "no",
            "practical_score": p["practical_specificity"],
        })
    write_csv("Practical_Guidance_Scores.csv", rows, fields)

    # 8. Decision Support Growth per cluster
    cluster_data = defaultdict(lambda: {"with_decision": 0, "with_practical": 0, "scores": []})
    for p in scored_posts:
        c = p["cluster"]
        cluster_data[c]["scores"].append(p["practical_specificity"])
        if p["has_decision_pathway"]:
            cluster_data[c]["with_decision"] += 1
        if p["has_practical_guide"]:
            cluster_data[c]["with_practical"] += 1

    cfields = ["cluster", "posts_with_decision", "posts_with_practical", "avg_practical_score"]
    crows = []
    for cluster, d in sorted(cluster_data.items()):
        crows.append({
            "cluster": cluster,
            "posts_with_decision": d["with_decision"],
            "posts_with_practical": d["with_practical"],
            "avg_practical_score": round(mean(d["scores"]), 1),
        })
    write_csv("Decision_Support_Growth.csv", crows, cfields)

    # 9. Troubleshooting Expansion (practical_score < 60)
    tfields = ["id", "title", "cluster", "practical_score", "has_troubleshooting"]
    trows = [
        {
            "id": p["id"],
            "title": p["title"],
            "cluster": p["cluster"],
            "practical_score": p["practical_specificity"],
            "has_troubleshooting": "yes" if p["has_troubleshooting"] else "no",
        }
        for p in scored_posts if p["practical_specificity"] < 60
    ]
    trows.sort(key=lambda x: x["practical_score"])
    write_csv("Troubleshooting_Expansion.csv", trows, tfields)


# --- 10CC-D: Trust Depth ---
def generate_10cc_d(scored_posts):
    # 10. Trust Depth Report
    fields = ["id", "title", "cluster", "trust_blocks_count", "named_refs_count", "trust_score"]
    rows = []
    for p in scored_posts:
        rows.append({
            "id": p["id"],
            "title": p["title"],
            "cluster": p["cluster"],
            "trust_blocks_count": p["trust_blocks_count"],
            "named_refs_count": p["named_refs_count"],
            "trust_score": p["trust_depth"],
        })
    write_csv("Trust_Depth_Report.csv", rows, fields)

    # 11. Trust Intensity Leaderboard (top 30)
    top30 = sorted(rows, key=lambda x: x["trust_score"], reverse=True)[:30]
    write_csv("Trust_Intensity_Leaderboard.csv", top30, fields)

    # 12. Authority Reference Expansion per cluster
    cluster_data = defaultdict(lambda: {"scores": [], "below50": 0})
    for p in scored_posts:
        c = p["cluster"]
        cluster_data[c]["scores"].append(p["trust_depth"])
        if p["trust_depth"] < 50:
            cluster_data[c]["below50"] += 1

    cfields = ["cluster", "avg_trust_score", "posts_below_50", "refs_needed"]
    crows = []
    for cluster, d in sorted(cluster_data.items()):
        avg = round(mean(d["scores"]), 1)
        refs_needed = d["below50"] * 2  # estimate: 2 more refs per deficient post
        crows.append({
            "cluster": cluster,
            "avg_trust_score": avg,
            "posts_below_50": d["below50"],
            "refs_needed": refs_needed,
        })
    write_csv("Authority_Reference_Expansion.csv", crows, cfields)


# --- 10CC-E: Semantic Market Share ---
def generate_10cc_e(scored_posts):
    # 13. Semantic Market Share per cluster
    cluster_data = defaultdict(lambda: {
        "glossary_terms": 0, "faq_items": 0,
        "comparison_tables": 0, "practical_guides": 0,
        "posts": 0, "entities": set(),
    })
    for p in scored_posts:
        c = p["cluster"]
        cluster_data[c]["glossary_terms"] += p["glossary_terms"]
        cluster_data[c]["faq_items"] += p["faq_items"]
        cluster_data[c]["comparison_tables"] += p["comparison_table_count"]
        cluster_data[c]["practical_guides"] += p["practical_guides"]
        cluster_data[c]["posts"] += 1
        # Entities: derive from post titles (simplified)
        cluster_data[c]["entities"].add(p["title"])

    cfields = ["cluster", "owned_entities", "glossary_terms", "faq_items",
               "comparison_tables", "practical_guides", "semantic_score", "status"]
    crows = []
    for cluster, d in sorted(cluster_data.items()):
        owned = d["posts"]
        glossary = d["glossary_terms"]
        faq = d["faq_items"]
        comp = d["comparison_tables"]
        prac = d["practical_guides"]
        # Semantic score: weighted composite
        raw = (owned * 2) + (glossary * 1.5) + (faq * 1) + (comp * 3) + (prac * 2)
        # Normalize to 0-100 scale (calibrated for PetHub's range)
        sem_score = min(round(raw / max(owned, 1) * 5, 1), 100)
        if sem_score >= 75:
            status = "DOMINANT"
        elif sem_score >= 50:
            status = "STRONG"
        else:
            status = "DEVELOPING"
        crows.append({
            "cluster": cluster,
            "owned_entities": owned,
            "glossary_terms": glossary,
            "faq_items": faq,
            "comparison_tables": comp,
            "practical_guides": prac,
            "semantic_score": sem_score,
            "status": status,
        })
    write_csv("Semantic_Market_Share.csv", crows, cfields)

    # 14. Owned Entities (posts where PetHub covers definitively)
    owned_fields = ["id", "title", "cluster", "citation_score", "moat_score"]
    # Posts with citation_score >= 65 are "owned"
    owned = [p for p in scored_posts if p["citation_score"] >= 65]
    owned.sort(key=lambda x: x["citation_score"], reverse=True)
    write_csv("Owned_Entities.csv", owned, owned_fields)

    # 15. Contested Entities (incomplete coverage)
    contested = [p for p in scored_posts if p["citation_score"] < 65]
    contested.sort(key=lambda x: x["citation_score"])
    write_csv("Contested_Entities.csv", contested, owned_fields)


# --- 10CC-F: Authority Moat ---
def generate_10cc_f(scored_posts):
    # 16. Authority Moat Report
    fields = ["id", "title", "cluster", "glossary_moat", "trust_moat", "comparison_moat",
              "practical_moat", "educational_moat", "citation_moat", "structural_moat",
              "moat_score"]
    write_csv("Authority_Moat_Report.csv", scored_posts, fields)

    # 17. Moat Leaderboard (top 30)
    top30 = sorted(scored_posts, key=lambda x: x["moat_score"], reverse=True)[:30]
    write_csv("Moat_Leaderboard.csv", top30, fields)

    # 18. Moat Growth Tracker per cluster
    cluster_data = defaultdict(lambda: {"scores": [], "above80": 0, "below70": 0})
    for p in scored_posts:
        c = p["cluster"]
        cluster_data[c]["scores"].append(p["moat_score"])
        if p["moat_score"] >= 80:
            cluster_data[c]["above80"] += 1
        if p["moat_score"] < 70:
            cluster_data[c]["below70"] += 1

    cfields = ["cluster", "avg_moat", "posts_above_80", "posts_below_70", "growth_priority"]
    crows = []
    for cluster, d in sorted(cluster_data.items()):
        avg = round(mean(d["scores"]), 1)
        if avg < 60:
            priority = "CRITICAL"
        elif avg < 70:
            priority = "HIGH"
        elif avg < 80:
            priority = "MEDIUM"
        else:
            priority = "LOW"
        crows.append({
            "cluster": cluster,
            "avg_moat": avg,
            "posts_above_80": d["above80"],
            "posts_below_70": d["below70"],
            "growth_priority": priority,
        })
    write_csv("Moat_Growth_Tracker.csv", crows, cfields)


# --- 10CC-G: Cluster Dominance Roadmaps ---
def generate_10cc_g(scored_posts):
    # Compute per-cluster dimension averages
    cluster_dims = defaultdict(lambda: {
        "citation": [], "comparison": [], "practical": [], "trust": [],
        "extractability": [], "summary": [], "moat": [], "ai_pref": [],
        "posts": [],
    })
    for p in scored_posts:
        c = p["cluster"]
        cluster_dims[c]["citation"].append(p["citation_score"])
        cluster_dims[c]["comparison"].append(p["comparison_usefulness"])
        cluster_dims[c]["practical"].append(p["practical_specificity"])
        cluster_dims[c]["trust"].append(p["trust_depth"])
        cluster_dims[c]["extractability"].append(p["extractability"])
        cluster_dims[c]["summary"].append(p["summary_usefulness"])
        cluster_dims[c]["moat"].append(p["moat_score"])
        cluster_dims[c]["ai_pref"].append(p["ai_preference_score"])
        cluster_dims[c]["posts"].append(p["id"])

    # 19. Cluster Dominance Roadmaps
    fields19 = ["cluster", "dominance_score", "weakest_dim", "action_needed", "posts_to_modify"]
    rows19 = []
    for cluster, d in sorted(cluster_dims.items()):
        dim_avgs = {
            "citation": round(mean(d["citation"]), 1),
            "comparison": round(mean(d["comparison"]), 1),
            "practical": round(mean(d["practical"]), 1),
            "trust": round(mean(d["trust"]), 1),
            "extractability": round(mean(d["extractability"]), 1),
            "summary": round(mean(d["summary"]), 1),
        }
        dominance = round(mean(dim_avgs.values()), 1)
        weakest = min(dim_avgs, key=dim_avgs.get)
        weakest_val = dim_avgs[weakest]

        # Action based on weakest dimension
        actions = {
            "citation": "Add more UK authority references (RSPCA, BVA, PFMA)",
            "comparison": "Add striped comparison tables with Compared/Comparison headings",
            "practical": "Add Step-by-Step blocks, numbered steps, measurable details",
            "trust": "Add Research Sources, Why We Reference Sources, methodology blocks",
            "extractability": "Add At a Glance, Key Takeaways, Decision Summary blocks",
            "summary": "Add At a Glance, Key Takeaways, What to Do Next, Conclusion",
        }

        # Count posts needing work in weakest dimension
        dim_key_map = {
            "citation": "reference_quality", "comparison": "comparison_usefulness",
            "practical": "practical_specificity", "trust": "trust_depth",
            "extractability": "extractability", "summary": "summary_usefulness",
        }
        scored_dim_key = dim_key_map[weakest]
        posts_to_fix = sum(1 for p in scored_posts if p["cluster"] == cluster and p[scored_dim_key] < 70)

        rows19.append({
            "cluster": cluster,
            "dominance_score": dominance,
            "weakest_dim": f"{weakest} ({weakest_val})",
            "action_needed": actions.get(weakest, "Review and improve"),
            "posts_to_modify": posts_to_fix,
        })
    rows19.sort(key=lambda x: x["dominance_score"])
    write_csv("Cluster_Dominance_Roadmaps.csv", rows19, fields19)

    # 20. Cluster Gap Closure (clusters below 75)
    fields20 = ["cluster", "dominance_score", "gap_to_75", "weakest_dimensions", "priority_posts"]
    rows20 = []
    for r in rows19:
        if r["dominance_score"] < 75:
            gap = round(75 - r["dominance_score"], 1)
            # Find the 2 weakest dimensions for this cluster
            d = cluster_dims[r["cluster"]]
            dim_avgs = {
                "citation": round(mean(d["citation"]), 1),
                "comparison": round(mean(d["comparison"]), 1),
                "practical": round(mean(d["practical"]), 1),
                "trust": round(mean(d["trust"]), 1),
                "extractability": round(mean(d["extractability"]), 1),
                "summary": round(mean(d["summary"]), 1),
            }
            sorted_dims = sorted(dim_avgs.items(), key=lambda x: x[1])
            weakest_2 = f"{sorted_dims[0][0]} ({sorted_dims[0][1]}), {sorted_dims[1][0]} ({sorted_dims[1][1]})"

            # Find lowest scoring posts in this cluster
            cluster_posts = [p for p in scored_posts if p["cluster"] == r["cluster"]]
            cluster_posts.sort(key=lambda x: x["citation_score"])
            priority_ids = [str(p["id"]) for p in cluster_posts[:5]]

            rows20.append({
                "cluster": r["cluster"],
                "dominance_score": r["dominance_score"],
                "gap_to_75": gap,
                "weakest_dimensions": weakest_2,
                "priority_posts": "; ".join(priority_ids),
            })
    write_csv("Cluster_Gap_Closure.csv", rows20, fields20)

    # 21. Cluster Acceleration Report
    fields21 = ["cluster", "current_dominance", "target", "gap", "acceleration_actions"]
    rows21 = []
    for r in rows19:
        target = max(80, r["dominance_score"] + 10)  # aim for at least 80 or +10
        gap = round(target - r["dominance_score"], 1)
        d = cluster_dims[r["cluster"]]
        dim_avgs = {
            "citation": round(mean(d["citation"]), 1),
            "comparison": round(mean(d["comparison"]), 1),
            "practical": round(mean(d["practical"]), 1),
            "trust": round(mean(d["trust"]), 1),
        }
        sorted_dims = sorted(dim_avgs.items(), key=lambda x: x[1])
        actions = []
        for dim_name, dim_val in sorted_dims[:2]:
            if dim_name == "citation":
                actions.append(f"Boost citations (avg {dim_val}) with more UK authority refs")
            elif dim_name == "comparison":
                actions.append(f"Add comparison tables (avg {dim_val}) with striped style")
            elif dim_name == "practical":
                actions.append(f"Add practical guides (avg {dim_val}) with step-by-step blocks")
            elif dim_name == "trust":
                actions.append(f"Deepen trust signals (avg {dim_val}) with source methodology blocks")
        rows21.append({
            "cluster": r["cluster"],
            "current_dominance": r["dominance_score"],
            "target": target,
            "gap": gap,
            "acceleration_actions": "; ".join(actions),
        })
    rows21.sort(key=lambda x: x["gap"], reverse=True)
    write_csv("Cluster_Acceleration_Report.csv", rows21, fields21)


# --- 10CC-H: AI Answer Preference ---
def generate_10cc_h(scored_posts):
    # 22. AI Answer Preference (all posts)
    fields = ["id", "title", "cluster", "answer_superiority", "extraction_superiority",
              "comparison_superiority", "trust_superiority", "usefulness_superiority",
              "ai_preference_score"]
    write_csv("AI_Answer_Preference.csv", scored_posts, fields)

    # 23. AI Extraction Superiority (top 30)
    top30_ext = sorted(scored_posts, key=lambda x: x["extraction_superiority"], reverse=True)[:30]
    write_csv("AI_Extraction_Superiority.csv", top30_ext, fields)

    # 24. AI Citation Preference (top 30 by citation_score)
    ai_cit_fields = ["id", "title", "cluster", "citation_score", "ai_preference_score"]
    top30_cit = sorted(scored_posts, key=lambda x: x["citation_score"], reverse=True)[:30]
    write_csv("AI_Citation_Preference.csv", top30_cit, ai_cit_fields)


# --- 10CC-I: Competitor Displacement ---
def generate_10cc_i(scored_posts):
    """Generate competitor displacement reports using existing analysis + current scores."""
    # Load existing competitor data
    competitor_rows = []
    if os.path.exists(COMPETITOR_CSV):
        with open(COMPETITOR_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                competitor_rows.append(row)
        print(f"  Loaded {len(competitor_rows)} competitor analysis rows")

    displacement_rows = []
    if os.path.exists(DISPLACEMENT_CSV):
        with open(DISPLACEMENT_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                displacement_rows.append(row)
        print(f"  Loaded {len(displacement_rows)} displacement summary rows")

    # Compute per-cluster averages
    cluster_avgs = defaultdict(lambda: {"citation": [], "moat": [], "ai_pref": [], "comparison": [], "trust": []})
    for p in scored_posts:
        c = p["cluster"]
        cluster_avgs[c]["citation"].append(p["citation_score"])
        cluster_avgs[c]["moat"].append(p["moat_score"])
        cluster_avgs[c]["ai_pref"].append(p["ai_preference_score"])
        cluster_avgs[c]["comparison"].append(p["comparison_usefulness"])
        cluster_avgs[c]["trust"].append(p["trust_depth"])

    cluster_scores = {}
    for cluster, d in cluster_avgs.items():
        cluster_scores[cluster] = {
            "avg_citation": round(mean(d["citation"]), 1),
            "avg_moat": round(mean(d["moat"]), 1),
            "avg_ai_pref": round(mean(d["ai_pref"]), 1),
            "avg_comparison": round(mean(d["comparison"]), 1),
            "avg_trust": round(mean(d["trust"]), 1),
        }

    # 25. Competitor Displacement Report (updated displacement summary with current scores)
    fields25 = ["cluster", "pethub_strengths", "biggest_competitor_threat",
                 "priority_displacement_action", "displacement_difficulty",
                 "avg_citation_score", "avg_moat_score", "avg_ai_pref_score"]
    rows25 = []
    for row in displacement_rows:
        cluster = row.get("cluster", "")
        cs = cluster_scores.get(cluster, {"avg_citation": 0, "avg_moat": 0, "avg_ai_pref": 0})
        rows25.append({
            "cluster": cluster,
            "pethub_strengths": row.get("pethub_strengths", ""),
            "biggest_competitor_threat": row.get("biggest_competitor_threat", ""),
            "priority_displacement_action": row.get("priority_displacement_action", ""),
            "displacement_difficulty": row.get("displacement_difficulty", ""),
            "avg_citation_score": cs["avg_citation"],
            "avg_moat_score": cs["avg_moat"],
            "avg_ai_pref_score": cs["avg_ai_pref"],
        })
    write_csv("Competitor_Displacement_Report.csv", rows25, fields25)

    # 26. Competitor Gap Map (where PetHub is behind)
    fields26 = ["cluster", "competitor", "competitor_has_guides", "competitor_has_glossary",
                 "competitor_has_comparisons", "competitor_trust_signals",
                 "competitor_advantage", "pethub_avg_comparison", "pethub_avg_trust"]
    rows26 = []
    for row in competitor_rows:
        cluster = row.get("cluster", "")
        comp_adv = row.get("competitor_advantage", "")
        if comp_adv and comp_adv.lower() != "none identified":
            cs = cluster_scores.get(cluster, {"avg_comparison": 0, "avg_trust": 0})
            rows26.append({
                "cluster": cluster,
                "competitor": row.get("competitor", ""),
                "competitor_has_guides": row.get("competitor_has_guides", ""),
                "competitor_has_glossary": row.get("competitor_has_glossary", ""),
                "competitor_has_comparisons": row.get("competitor_has_comparisons", ""),
                "competitor_trust_signals": row.get("competitor_trust_signals", ""),
                "competitor_advantage": comp_adv,
                "pethub_avg_comparison": cs["avg_comparison"],
                "pethub_avg_trust": cs["avg_trust"],
            })
    write_csv("Competitor_Gap_Map.csv", rows26, fields26)

    # 27. PetHub Advantage Map (where PetHub exceeds)
    fields27 = ["cluster", "competitor", "pethub_advantage",
                 "pethub_avg_citation", "pethub_avg_moat", "displacement_opportunity"]
    rows27 = []
    for row in competitor_rows:
        cluster = row.get("cluster", "")
        ph_adv = row.get("pethub_advantage", "")
        if ph_adv:
            cs = cluster_scores.get(cluster, {"avg_citation": 0, "avg_moat": 0})
            rows27.append({
                "cluster": cluster,
                "competitor": row.get("competitor", ""),
                "pethub_advantage": ph_adv,
                "pethub_avg_citation": cs["avg_citation"],
                "pethub_avg_moat": cs["avg_moat"],
                "displacement_opportunity": row.get("displacement_opportunity", ""),
            })
    write_csv("PetHub_Advantage_Map.csv", rows27, fields27)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("Phase 10CC Re-Scoring Engine – PetHub Online")
    print("=" * 70)

    # Load cluster assignments from previous phase
    cluster_map = load_cluster_map()

    # Fetch WP categories for fallback
    categories_map = fetch_categories()

    # Fetch all published posts
    posts = fetch_all_posts()
    if not posts:
        print("[FATAL] No posts fetched. Exiting.")
        sys.exit(1)

    # Score each post
    scored_posts = []
    errors = 0
    for i, post in enumerate(posts):
        try:
            pid = post["id"]
            title = post.get("title", {})
            if isinstance(title, dict):
                title = title.get("raw", title.get("rendered", ""))
            cluster = determine_cluster(post, cluster_map, categories_map)

            # Get raw content (Gutenberg blocks)
            content = post.get("content", {})
            if isinstance(content, dict):
                content = content.get("raw", content.get("rendered", ""))

            scores = score_post(content)
            scores["id"] = pid
            scores["title"] = title
            scores["cluster"] = cluster

            scored_posts.append(scores)

            if (i + 1) % 10 == 0:
                print(f"  Scored {i + 1}/{len(posts)} posts …")

        except Exception as e:
            errors += 1
            pid = post.get("id", "?")
            print(f"  [ERROR] Post {pid}: {e}")
            continue

    print(f"\nScoring complete: {len(scored_posts)} scored, {errors} errors")
    print("-" * 70)

    if not scored_posts:
        print("[FATAL] No posts scored. Exiting.")
        sys.exit(1)

    # Sort by citation score descending (default order)
    scored_posts.sort(key=lambda x: x["citation_score"], reverse=True)

    # Generate all deliverable CSVs
    print("\nGenerating 10CC-A: Citation Dominance …")
    generate_10cc_a(scored_posts)

    print("\nGenerating 10CC-B: Comparison Coverage …")
    generate_10cc_b(scored_posts)

    print("\nGenerating 10CC-C: Practical Guidance …")
    generate_10cc_c(scored_posts)

    print("\nGenerating 10CC-D: Trust Depth …")
    generate_10cc_d(scored_posts)

    print("\nGenerating 10CC-E: Semantic Market Share …")
    generate_10cc_e(scored_posts)

    print("\nGenerating 10CC-F: Authority Moat …")
    generate_10cc_f(scored_posts)

    print("\nGenerating 10CC-G: Cluster Dominance Roadmaps …")
    generate_10cc_g(scored_posts)

    print("\nGenerating 10CC-H: AI Answer Preference …")
    generate_10cc_h(scored_posts)

    print("\nGenerating 10CC-I: Competitor Displacement …")
    generate_10cc_i(scored_posts)

    # Summary statistics
    print("\n" + "=" * 70)
    print("SUMMARY STATISTICS")
    print("=" * 70)
    print(f"Total posts scored: {len(scored_posts)}")
    print(f"Errors during scoring: {errors}")

    cit_scores = [p["citation_score"] for p in scored_posts]
    moat_scores = [p["moat_score"] for p in scored_posts]
    ai_scores = [p["ai_preference_score"] for p in scored_posts]

    print(f"\nCitation Preference:  avg={round(mean(cit_scores), 1)}  "
          f"min={min(cit_scores)}  max={max(cit_scores)}  "
          f">=90: {sum(1 for s in cit_scores if s >= 90)}")
    print(f"Authority Moat:       avg={round(mean(moat_scores), 1)}  "
          f"min={min(moat_scores)}  max={max(moat_scores)}  "
          f">=80: {sum(1 for s in moat_scores if s >= 80)}")
    print(f"AI Answer Preference: avg={round(mean(ai_scores), 1)}  "
          f"min={min(ai_scores)}  max={max(ai_scores)}  "
          f">=80: {sum(1 for s in ai_scores if s >= 80)}")

    # Per-cluster summary
    clusters = defaultdict(list)
    for p in scored_posts:
        clusters[p["cluster"]].append(p)

    print(f"\nClusters: {len(clusters)}")
    print(f"{'Cluster':<22} {'Posts':>5} {'Avg Cit':>8} {'Avg Moat':>9} {'Avg AI':>7}")
    print("-" * 55)
    for cluster in sorted(clusters.keys()):
        cps = clusters[cluster]
        avg_c = round(mean(p["citation_score"] for p in cps), 1)
        avg_m = round(mean(p["moat_score"] for p in cps), 1)
        avg_a = round(mean(p["ai_preference_score"] for p in cps), 1)
        print(f"{cluster:<22} {len(cps):>5} {avg_c:>8} {avg_m:>9} {avg_a:>7}")

    print(f"\nAll 27 CSVs written to: {OUTPUT_DIR}")
    print("=" * 70)
    print("Done.")


if __name__ == "__main__":
    main()
