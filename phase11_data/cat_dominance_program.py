#!/usr/bin/env python3
"""
Phase 11N - Cat Cluster Dominance Program for PetHub Online
============================================================
Goal: Move 3 cat clusters from COMPETITIVE to CLEAR LEADERSHIP vs Cats.com

Target clusters: Cat Supplies (1377), Cat Toys (1459), Indoor Cats (1413)
Competitor: Cats.com (2,150+ guides, veterinary advisor network)
PetHub advantages: UK-specific authority, glossary depth, structured Gutenberg blocks

Scoring: Cat Dominance Index (0-100)
  - UK Authority Edge  (25%)
  - Content Depth      (25%)
  - Structure Quality  (20%)
  - Evidence Strength  (15%)
  - Freshness          (15%)
"""

import csv
import json
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser

# ── Configuration ──────────────────────────────────────────────────────────
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_API = "https://pethubonline.com/wp-json/wp/v2/posts"
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase11_data"

CLUSTERS = {
    "Cat Supplies": 1377,
    "Cat Toys": 1459,
    "Indoor Cats": 1413,
}

# ── UK Authority Markers ──────────────────────────────────────────────────
UK_ORGS = [
    "rspca", "pdsa", "bva", "british veterinary association",
    "cats protection", "battersea", "blue cross", "wood green",
    "international cat care", "feline advisory bureau",
    "defra", "animal welfare act", "pet food manufacturers association",
    "pfma", "uk pet food", "royal veterinary college", "rvc",
    "veterinary medicines directorate", "vmd",
    "pet industry federation", "pif",
]

UK_BRANDS = [
    "pets at home", "lily's kitchen", "forthglade", "canagan",
    "applaws", "harringtons", "whiskas", "felix", "sheba",
    "iams", "james wellbeloved", "burgess", "encore",
    "natures menu", "scrumbles", "pooch & mutt", "barking heads",
    "republic of cats", "katkin", "untamed",
    "zooplus", "bitiba", "medicanimal", "viovet",
    "pets corner", "jollyes", "pet planet",
]

UK_LOCATIONS = [
    "uk", "united kingdom", "britain", "british", "england",
    "scotland", "wales", "london", "manchester", "birmingham",
    "edinburgh", "glasgow", "cardiff", "belfast", "liverpool",
    "leeds", "bristol", "nottingham", "sheffield",
]

UK_REGULATIONS = [
    "animal welfare act 2006", "pet animals act",
    "microchipping of cats", "cats act", "dangerous wild animals act",
    "breeding and sale of dogs", "pet travel scheme",
    "animal health and welfare", "uk law", "uk regulation",
    "trading standards", "consumer rights act",
]

# Topics Cats.com is known to cover extensively per cluster
CATS_COM_TOPICS = {
    "Cat Supplies": [
        "best cat food brands review",
        "automatic cat feeders comparison",
        "cat water fountains guide",
        "cat litter comparison",
        "cat carrier buying guide",
        "cat grooming tools review",
        "cat beds and bedding guide",
        "senior cat supplies",
        "kitten essentials checklist",
        "eco-friendly cat products",
        "cat scratching posts comparison",
        "cat harness and leash guide",
        "cat supplements and vitamins",
        "cat dental care products",
        "cat collar and tag guide",
        "raw food for cats guide",
        "prescription cat food guide",
        "biodegradable cat litter",
        "heated cat beds review",
        "cat microchip guide",
    ],
    "Cat Toys": [
        "best interactive cat toys",
        "puzzle toys for cats",
        "catnip toys review",
        "laser pointer toys safety",
        "feather wand toys comparison",
        "electronic cat toys guide",
        "diy cat toy ideas",
        "toys for senior cats",
        "kitten toy essentials",
        "cat tunnel and tent guide",
        "best cat balls and chasers",
        "cat tree and climbing toys",
        "treat dispensing toys",
        "robotic cat toys review",
        "enrichment toys for indoor cats",
    ],
    "Indoor Cats": [
        "keeping cats happy indoors",
        "indoor cat exercise guide",
        "cat-proofing your home",
        "indoor vs outdoor cats debate",
        "indoor cat enrichment ideas",
        "catio building guide",
        "indoor cat diet guide",
        "indoor cat behaviour problems",
        "apartment cats guide",
        "vertical space for indoor cats",
        "window perches for cats",
        "indoor cat breeds guide",
        "managing multi-cat indoor household",
        "indoor cat mental stimulation",
        "transitioning outdoor cat indoors",
        "indoor cat plants safety",
        "indoor cat litter setup",
        "indoor cat socialization",
    ],
}


# ── HTML Stripping ─────────────────────────────────────────────────────────
class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_text(self):
        return " ".join(self.fed)


def strip_html(html_str):
    s = HTMLStripper()
    s.feed(html_str or "")
    return s.get_text()


# ── WordPress API Fetcher ──────────────────────────────────────────────────
def fetch_cluster_posts(category_id, cluster_name):
    """Fetch all published posts in a cluster via WP REST API."""
    posts = []
    page = 1
    while True:
        url = f"{WP_API}?per_page=100&page={page}&categories={category_id}&status=publish&context=edit"
        print(f"  Fetching {cluster_name} page {page}: {url[:80]}...")
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"  ERROR: curl returned {result.returncode}")
            break

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"  ERROR: Invalid JSON response")
            break

        if isinstance(data, dict) and "code" in data:
            print(f"  API error: {data.get('message', 'unknown')}")
            break

        if not isinstance(data, list) or len(data) == 0:
            break

        posts.extend(data)
        print(f"  Got {len(data)} posts (total: {len(posts)})")

        if len(data) < 100:
            break

        page += 1
        time.sleep(2)

    time.sleep(2)
    return posts


# ── Analysis Functions ─────────────────────────────────────────────────────

def count_uk_citations(text):
    """Count UK-specific citations in text."""
    text_lower = text.lower()
    hits = {"orgs": [], "brands": [], "locations": [], "regulations": []}

    for org in UK_ORGS:
        if org in text_lower:
            hits["orgs"].append(org)

    for brand in UK_BRANDS:
        if brand in text_lower:
            hits["brands"].append(brand)

    for loc in UK_LOCATIONS:
        # Word boundary match to avoid false positives
        if re.search(r'\b' + re.escape(loc) + r'\b', text_lower):
            hits["locations"].append(loc)

    for reg in UK_REGULATIONS:
        if reg in text_lower:
            hits["regulations"].append(reg)

    return hits


def count_faqs(content):
    """Count FAQ items in content."""
    faq_count = 0
    # Look for FAQ schema blocks
    faq_count += len(re.findall(r'wp:yoast/faq-block', content, re.IGNORECASE))
    # Look for FAQ-style Q&A patterns
    faq_count += len(re.findall(r'<h[23][^>]*>\s*(?:Q:|FAQ|Frequently Asked)', content, re.IGNORECASE))
    # Look for question-style headings
    faq_count += len(re.findall(r'<h[234][^>]*>[^<]*\?</h[234]>', content))
    # Yoast FAQ question items
    faq_count += len(re.findall(r'"question"\s*:', content))
    return faq_count


def count_comparison_tables(content):
    """Count and assess comparison tables."""
    table_count = len(re.findall(r'<table', content, re.IGNORECASE))
    # Also count wp:table blocks
    table_count += len(re.findall(r'wp:table', content))
    # Dedup if both present (rough)
    actual_tables = max(table_count // 2, table_count - len(re.findall(r'wp:table', content)))
    if actual_tables == 0:
        actual_tables = table_count
    return min(actual_tables, 20)  # Cap sanity


def analyze_structure(content):
    """Analyze Gutenberg block structure and heading hierarchy."""
    blocks = {
        "gutenberg_blocks": len(re.findall(r'<!-- wp:', content)),
        "h2_count": len(re.findall(r'<h2', content, re.IGNORECASE)),
        "h3_count": len(re.findall(r'<h3', content, re.IGNORECASE)),
        "h4_count": len(re.findall(r'<h4', content, re.IGNORECASE)),
        "list_count": len(re.findall(r'<[ou]l', content, re.IGNORECASE)),
        "image_count": len(re.findall(r'<img', content, re.IGNORECASE)),
        "blockquote_count": len(re.findall(r'<blockquote', content, re.IGNORECASE)),
        "has_toc": bool(re.search(r'table.of.contents|wp:generateblocks|rank-math.*toc', content, re.IGNORECASE)),
    }
    return blocks


def analyze_evidence(text):
    """Analyze evidence quality: citations, data points, expert references."""
    evidence = {
        "source_citations": 0,
        "data_points": 0,
        "expert_refs": 0,
        "url_refs": 0,
    }
    # Source patterns
    evidence["source_citations"] += len(re.findall(
        r'(?:according to|source:|cited from|research from|study by|published in|reported by)',
        text, re.IGNORECASE
    ))
    # Data points (numbers with context)
    evidence["data_points"] += len(re.findall(
        r'\b\d+(?:\.\d+)?(?:\s*%|\s*percent|\s*pounds?|\s*kg|\s*grams?|\s*mg|\s*calories)',
        text, re.IGNORECASE
    ))
    # Expert references (but not fabricated ones)
    evidence["expert_refs"] += len(re.findall(
        r'(?:veterinar|vet[s ]|animal behaviourist|feline specialist|cat expert)',
        text, re.IGNORECASE
    ))
    # URL references
    evidence["url_refs"] += len(re.findall(r'https?://', text))

    return evidence


def analyze_freshness(post):
    """Analyze content freshness."""
    freshness = {
        "pub_date": post.get("date", ""),
        "mod_date": post.get("modified", ""),
        "has_2026_markers": False,
        "days_since_update": 999,
        "seasonal_relevance": False,
    }

    text = strip_html(post.get("content", {}).get("rendered", ""))

    # Check for 2026 markers
    if re.search(r'2026', text):
        freshness["has_2026_markers"] = True

    # Calculate days since last modification
    mod_str = post.get("modified", post.get("date", ""))
    if mod_str:
        try:
            mod_date = datetime.fromisoformat(mod_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            freshness["days_since_update"] = (now - mod_date).days
        except (ValueError, TypeError):
            pass

    # Seasonal relevance
    current_month = datetime.now().month
    seasonal_terms = {
        12: ["christmas", "winter", "holiday", "gift"],
        1: ["new year", "winter", "january"],
        2: ["valentine", "february"],
        3: ["spring", "march"],
        4: ["spring", "easter", "april"],
        5: ["spring", "may", "summer"],
        6: ["summer", "june"],
        7: ["summer", "july"],
        8: ["summer", "august"],
        9: ["autumn", "fall", "september"],
        10: ["autumn", "fall", "halloween", "october"],
        11: ["autumn", "fall", "november", "bonfire"],
    }
    for term in seasonal_terms.get(current_month, []):
        if term in text.lower():
            freshness["seasonal_relevance"] = True
            break

    return freshness


# ── Scoring Engine ─────────────────────────────────────────────────────────

def score_uk_authority(uk_hits, word_count):
    """Score UK Authority Edge (0-25)."""
    score = 0

    # UK org citations (up to 8 pts)
    org_count = len(uk_hits["orgs"])
    score += min(org_count * 2, 8)

    # UK brand mentions (up to 5 pts)
    brand_count = len(uk_hits["brands"])
    score += min(brand_count * 1.0, 5)

    # UK location references (up to 5 pts)
    loc_count = len(uk_hits["locations"])
    score += min(loc_count * 1.0, 5)

    # UK regulation references (up to 5 pts)
    reg_count = len(uk_hits["regulations"])
    score += min(reg_count * 2.5, 5)

    # Citation density bonus (up to 2 pts)
    total_uk = org_count + brand_count + loc_count + reg_count
    if word_count > 0:
        density = total_uk / (word_count / 1000)
        score += min(density * 0.5, 2)

    return min(round(score, 1), 25)


def score_content_depth(word_count, section_count, faq_count, table_count):
    """Score Content Depth (0-25)."""
    score = 0

    # Word count (up to 8 pts) - aiming for 2500+ words for dominance
    if word_count >= 3000:
        score += 8
    elif word_count >= 2000:
        score += 6
    elif word_count >= 1500:
        score += 4
    elif word_count >= 1000:
        score += 3
    elif word_count >= 500:
        score += 1

    # Section count (up to 6 pts)
    score += min(section_count * 0.75, 6)

    # FAQ depth (up to 6 pts)
    score += min(faq_count * 1.5, 6)

    # Comparison tables (up to 5 pts)
    score += min(table_count * 2.5, 5)

    return min(round(score, 1), 25)


def score_structure(blocks):
    """Score Structure Quality (0-20)."""
    score = 0

    # Gutenberg block usage (up to 5 pts)
    gb = blocks["gutenberg_blocks"]
    if gb >= 15:
        score += 5
    elif gb >= 10:
        score += 4
    elif gb >= 5:
        score += 3
    elif gb >= 1:
        score += 1

    # Heading hierarchy (up to 5 pts)
    if blocks["h2_count"] >= 3 and blocks["h3_count"] >= 2:
        score += 5
    elif blocks["h2_count"] >= 2:
        score += 3
    elif blocks["h2_count"] >= 1:
        score += 1

    # Lists (up to 4 pts)
    score += min(blocks["list_count"] * 1.0, 4)

    # Images (up to 3 pts)
    score += min(blocks["image_count"] * 0.75, 3)

    # ToC present (2 pts)
    if blocks["has_toc"]:
        score += 2

    # Blockquotes for emphasis (1 pt)
    if blocks["blockquote_count"] > 0:
        score += 1

    return min(round(score, 1), 20)


def score_evidence(evidence):
    """Score Evidence Strength (0-15)."""
    score = 0

    # Source citations (up to 5 pts)
    score += min(evidence["source_citations"] * 1.25, 5)

    # Data points (up to 4 pts)
    score += min(evidence["data_points"] * 0.5, 4)

    # Expert references (up to 3 pts)
    score += min(evidence["expert_refs"] * 1.0, 3)

    # URL references (up to 3 pts)
    score += min(evidence["url_refs"] * 0.5, 3)

    return min(round(score, 1), 15)


def score_freshness(freshness_data):
    """Score Freshness (0-15)."""
    score = 0

    # Recency of update (up to 6 pts)
    days = freshness_data["days_since_update"]
    if days <= 30:
        score += 6
    elif days <= 90:
        score += 4
    elif days <= 180:
        score += 3
    elif days <= 365:
        score += 1

    # 2026 markers in content (5 pts)
    if freshness_data["has_2026_markers"]:
        score += 5

    # Seasonal relevance (4 pts)
    if freshness_data["seasonal_relevance"]:
        score += 4

    return min(round(score, 1), 15)


def classify_position(dominance_index):
    """Classify competitive position based on dominance index."""
    if dominance_index >= 75:
        return "CLEAR LEADERSHIP"
    elif dominance_index >= 55:
        return "STRONG COMPETITIVE"
    elif dominance_index >= 40:
        return "COMPETITIVE"
    elif dominance_index >= 25:
        return "EMERGING"
    else:
        return "NEEDS ATTENTION"


# ── Gap Analysis ───────────────────────────────────────────────────────────

def identify_gaps(cluster_name, posts, post_scores):
    """Identify gaps where Cats.com likely leads."""
    gaps = []
    text_all = " ".join(
        strip_html(p.get("content", {}).get("rendered", "")).lower()
        for p in posts
    )
    titles_lower = [strip_html(p.get("title", {}).get("rendered", "")).lower() for p in posts]

    # 1. Content volume gap
    pethub_count = len(posts)
    cats_com_estimated = {
        "Cat Supplies": 180,
        "Cat Toys": 95,
        "Indoor Cats": 120,
    }
    estimated = cats_com_estimated.get(cluster_name, 100)
    if pethub_count < estimated:
        gap_size = estimated - pethub_count
        gaps.append({
            "cluster": cluster_name,
            "gap_type": "Content Volume",
            "description": f"PetHub has {pethub_count} posts vs Cats.com estimated ~{estimated} guides ({gap_size} gap)",
            "priority": "HIGH" if gap_size > 50 else "MEDIUM",
            "estimated_effort": f"{min(gap_size, 30)} new posts needed in next 90 days",
            "impact": "HIGH",
        })

    # 2. Veterinary authority gap
    vet_posts = sum(1 for s in post_scores if s["evidence_strength"] >= 8)
    gaps.append({
        "cluster": cluster_name,
        "gap_type": "Veterinary Authority",
        "description": f"Cats.com has named veterinary advisors. PetHub has {vet_posts}/{pethub_count} posts with strong evidence. Need UK vet partnerships.",
        "priority": "HIGH",
        "estimated_effort": "Partner with 1-2 UK vets for review badges",
        "impact": "HIGH",
    })

    # 3. Topic coverage gaps
    cats_com_topics = CATS_COM_TOPICS.get(cluster_name, [])
    missing_topics = []
    for topic in cats_com_topics:
        topic_words = topic.lower().split()
        # Check if at least 60% of topic words appear in any title
        found = False
        for title in titles_lower:
            match_count = sum(1 for w in topic_words if w in title)
            if match_count >= len(topic_words) * 0.5:
                found = True
                break
        # Also check full text for topic coverage
        if not found:
            key_phrase = " ".join(topic_words[:3])
            if key_phrase in text_all:
                found = True
        if not found:
            missing_topics.append(topic)

    if missing_topics:
        gaps.append({
            "cluster": cluster_name,
            "gap_type": "Topic Coverage",
            "description": f"Missing {len(missing_topics)} topics Cats.com likely covers: {'; '.join(missing_topics[:5])}{'...' if len(missing_topics) > 5 else ''}",
            "priority": "HIGH" if len(missing_topics) > 5 else "MEDIUM",
            "estimated_effort": f"Create {len(missing_topics)} targeted posts",
            "impact": "HIGH",
        })

    # 4. UK authority density gap
    low_uk_posts = sum(1 for s in post_scores if s["uk_authority"] < 10)
    if low_uk_posts > 0:
        gaps.append({
            "cluster": cluster_name,
            "gap_type": "UK Authority Density",
            "description": f"{low_uk_posts}/{pethub_count} posts have weak UK-specific citations (< 10/25). This is PetHub's key differentiator.",
            "priority": "HIGH",
            "estimated_effort": f"Enhance {low_uk_posts} posts with UK org refs, brands, regulations",
            "impact": "MEDIUM",
        })

    # 5. Freshness gap
    stale_posts = sum(1 for s in post_scores if s["freshness"] < 6)
    if stale_posts > 0:
        gaps.append({
            "cluster": cluster_name,
            "gap_type": "Content Freshness",
            "description": f"{stale_posts}/{pethub_count} posts lack 2026 freshness markers or haven't been updated recently",
            "priority": "MEDIUM",
            "estimated_effort": f"Update {stale_posts} posts with 2026 dates and current info",
            "impact": "MEDIUM",
        })

    # 6. Structure/table gap
    no_table_posts = sum(1 for s in post_scores if s.get("table_count", 0) == 0)
    if no_table_posts > pethub_count * 0.5:
        gaps.append({
            "cluster": cluster_name,
            "gap_type": "Comparison Tables",
            "description": f"{no_table_posts}/{pethub_count} posts lack comparison tables. Tables improve dwell time and featured snippet eligibility.",
            "priority": "MEDIUM",
            "estimated_effort": f"Add comparison tables to {no_table_posts} posts",
            "impact": "MEDIUM",
        })

    return gaps


# ── Plan Generation ────────────────────────────────────────────────────────

def generate_plan(cluster_name, posts, post_scores, gaps):
    """Generate dominance acceleration plan."""
    plan = []

    # STRENGTHEN: Existing posts that need enhancement
    for score in post_scores:
        actions = []
        if score["uk_authority"] < 12:
            actions.append("Add UK org citations (RSPCA/PDSA/BVA), UK brand mentions, UK regulations")
        if score["content_depth"] < 12:
            actions.append("Expand content depth: add FAQs, comparison tables, more sections")
        if score["structure_quality"] < 10:
            actions.append("Improve structure: add Gutenberg blocks, heading hierarchy, lists, images")
        if score["evidence_strength"] < 8:
            actions.append("Strengthen evidence: add source citations, data points, expert references")
        if score["freshness"] < 6:
            actions.append("Update freshness: add 2026 dates, current pricing, seasonal content")

        if actions and score["dominance_index"] < 65:
            plan.append({
                "cluster": cluster_name,
                "action_type": "strengthen",
                "target": f"Post {score['post_id']}: {score['title'][:60]}",
                "description": "; ".join(actions[:3]),
                "priority": "HIGH" if score["dominance_index"] < 40 else "MEDIUM",
                "expected_impact": f"Could raise dominance from {score['dominance_index']} to {min(score['dominance_index'] + 25, 85)}",
            })

    # CREATE: New content based on gaps
    cats_com_topics = CATS_COM_TOPICS.get(cluster_name, [])
    titles_lower = [strip_html(p.get("title", {}).get("rendered", "")).lower() for p in posts]
    text_all = " ".join(
        strip_html(p.get("content", {}).get("rendered", "")).lower()
        for p in posts
    )

    for topic in cats_com_topics:
        topic_words = topic.lower().split()
        found = False
        for title in titles_lower:
            match_count = sum(1 for w in topic_words if w in title)
            if match_count >= len(topic_words) * 0.5:
                found = True
                break
        if not found:
            key_phrase = " ".join(topic_words[:3])
            if key_phrase in text_all:
                found = True
        if not found:
            plan.append({
                "cluster": cluster_name,
                "action_type": "create",
                "target": topic.title(),
                "description": f"New guide: '{topic}' with UK-specific angle, comparison tables, FAQ section, RSPCA/BVA citations",
                "priority": "HIGH",
                "expected_impact": "Fills topic gap vs Cats.com, adds UK authority",
            })

    # EXPLOIT: Unique UK angles
    uk_angles = {
        "Cat Supplies": [
            "UK pet food labelling regulations vs US standards",
            "Pets At Home vs independent UK pet shops comparison",
            "UK-specific cat nutrition guidelines (PFMA standards)",
            "Regional UK cat supply availability guide",
            "UK vet-recommended products (not available on Cats.com)",
        ],
        "Cat Toys": [
            "UK cat toy safety standards (CE/UKCA marking)",
            "UK-made cat toys and sustainable brands",
            "Indoor enrichment for UK flat-dwelling cats",
            "Seasonal UK cat toys (bonfire night, Christmas)",
            "UK charity shop cat toy finds and DIY UK materials",
        ],
        "Indoor Cats": [
            "Indoor cats in UK flats - space-efficient solutions",
            "UK weather and keeping cats indoors safely",
            "Cats Protection indoor cat guidelines",
            "UK rental properties and indoor cat policies",
            "Indoor cats and UK microchipping law compliance",
        ],
    }

    for angle in uk_angles.get(cluster_name, []):
        plan.append({
            "cluster": cluster_name,
            "action_type": "exploit",
            "target": angle,
            "description": f"UK-exclusive angle Cats.com cannot replicate: {angle}",
            "priority": "HIGH",
            "expected_impact": "Unique UK authority that Cats.com cannot match from US base",
        })

    return plan


# ── Main Execution ─────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("Phase 11N - Cat Cluster Dominance Program")
    print("PetHub Online vs Cats.com")
    print("=" * 70)
    print()

    all_scores = []
    all_gaps = []
    all_plans = []
    all_summaries = []

    for cluster_name, cat_id in CLUSTERS.items():
        print(f"\n{'─' * 60}")
        print(f"CLUSTER: {cluster_name} (Category ID: {cat_id})")
        print(f"{'─' * 60}")

        # 1. Fetch posts
        posts = fetch_cluster_posts(cat_id, cluster_name)
        if not posts:
            print(f"  WARNING: No posts found for {cluster_name}")
            all_summaries.append({
                "cluster": cluster_name,
                "post_count": 0,
                "avg_dominance": 0,
                "vs_cats_com_position": "NO CONTENT",
                "gap_count": 0,
                "top_priority_action": "Create foundational content immediately",
            })
            continue

        print(f"  Found {len(posts)} published posts")

        # 2. Analyze each post
        cluster_scores = []
        for post in posts:
            post_id = post.get("id", 0)
            title = strip_html(post.get("title", {}).get("rendered", "Untitled"))
            content_raw = post.get("content", {}).get("raw", "") or post.get("content", {}).get("rendered", "")
            content_rendered = post.get("content", {}).get("rendered", "")
            text = strip_html(content_rendered)
            word_count = len(text.split())

            # Analysis
            uk_hits = count_uk_citations(text)
            faq_count = count_faqs(content_raw or content_rendered)
            table_count = count_comparison_tables(content_raw or content_rendered)
            structure = analyze_structure(content_raw or content_rendered)
            evidence = analyze_evidence(text)
            freshness = analyze_freshness(post)
            section_count = structure["h2_count"] + structure["h3_count"]

            # Scoring
            s_uk = score_uk_authority(uk_hits, word_count)
            s_depth = score_content_depth(word_count, section_count, faq_count, table_count)
            s_struct = score_structure(structure)
            s_evidence = score_evidence(evidence)
            s_fresh = score_freshness(freshness)
            dominance_index = round(s_uk + s_depth + s_struct + s_evidence + s_fresh, 1)
            position = classify_position(dominance_index)

            score_record = {
                "post_id": post_id,
                "title": title,
                "cluster": cluster_name,
                "uk_authority": s_uk,
                "content_depth": s_depth,
                "structure_quality": s_struct,
                "evidence_strength": s_evidence,
                "freshness": s_fresh,
                "dominance_index": dominance_index,
                "competitive_position": position,
                "word_count": word_count,
                "table_count": table_count,
                "faq_count": faq_count,
            }
            cluster_scores.append(score_record)
            all_scores.append(score_record)

        # 3. Identify gaps
        cluster_gaps = identify_gaps(cluster_name, posts, cluster_scores)
        all_gaps.extend(cluster_gaps)

        # 4. Generate plan
        cluster_plan = generate_plan(cluster_name, posts, cluster_scores, cluster_gaps)
        all_plans.extend(cluster_plan)

        # 5. Cluster summary
        avg_dom = round(sum(s["dominance_index"] for s in cluster_scores) / len(cluster_scores), 1) if cluster_scores else 0
        position_counts = defaultdict(int)
        for s in cluster_scores:
            position_counts[s["competitive_position"]] += 1

        # Determine overall cluster position
        if avg_dom >= 65:
            cluster_position = "APPROACHING LEADERSHIP"
        elif avg_dom >= 50:
            cluster_position = "STRONG COMPETITIVE"
        elif avg_dom >= 35:
            cluster_position = "COMPETITIVE"
        else:
            cluster_position = "BUILDING"

        high_priority_plans = [p for p in cluster_plan if p["priority"] == "HIGH"]
        top_action = high_priority_plans[0]["description"][:100] if high_priority_plans else "Maintain current trajectory"

        summary = {
            "cluster": cluster_name,
            "post_count": len(posts),
            "avg_dominance": avg_dom,
            "vs_cats_com_position": cluster_position,
            "gap_count": len(cluster_gaps),
            "top_priority_action": top_action,
        }
        all_summaries.append(summary)

        # Print cluster report
        print(f"\n  CLUSTER REPORT: {cluster_name}")
        print(f"  Posts: {len(posts)} | Avg Dominance: {avg_dom}/100 | Position: {cluster_position}")
        print(f"  Position breakdown: {dict(position_counts)}")
        print(f"  Gaps identified: {len(cluster_gaps)}")
        print(f"  Plan actions: {len(cluster_plan)}")

        # Top and bottom posts
        sorted_scores = sorted(cluster_scores, key=lambda x: x["dominance_index"], reverse=True)
        print(f"\n  TOP 3 posts:")
        for s in sorted_scores[:3]:
            print(f"    [{s['dominance_index']:5.1f}] {s['title'][:65]}")
        if len(sorted_scores) > 3:
            print(f"\n  BOTTOM 3 posts (need most work):")
            for s in sorted_scores[-3:]:
                print(f"    [{s['dominance_index']:5.1f}] {s['title'][:65]}")

        print(f"\n  KEY GAPS:")
        for g in cluster_gaps[:3]:
            print(f"    [{g['priority']}] {g['gap_type']}: {g['description'][:80]}")

    # ── Write CSVs ─────────────────────────────────────────────────────────

    # a. cat_dominance_scores.csv
    scores_path = os.path.join(OUTPUT_DIR, "cat_dominance_scores.csv")
    with open(scores_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "post_id", "title", "cluster", "uk_authority", "content_depth",
            "structure_quality", "evidence_strength", "freshness",
            "dominance_index", "competitive_position"
        ])
        writer.writeheader()
        for s in all_scores:
            writer.writerow({k: s[k] for k in writer.fieldnames})
    print(f"\n  Wrote {scores_path} ({len(all_scores)} rows)")

    # b. cat_dominance_gaps.csv
    gaps_path = os.path.join(OUTPUT_DIR, "cat_dominance_gaps.csv")
    with open(gaps_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "cluster", "gap_type", "description", "priority",
            "estimated_effort", "impact"
        ])
        writer.writeheader()
        for g in all_gaps:
            writer.writerow(g)
    print(f"  Wrote {gaps_path} ({len(all_gaps)} rows)")

    # c. cat_dominance_plan.csv
    plan_path = os.path.join(OUTPUT_DIR, "cat_dominance_plan.csv")
    with open(plan_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "cluster", "action_type", "target", "description",
            "priority", "expected_impact"
        ])
        writer.writeheader()
        for p in all_plans:
            writer.writerow(p)
    print(f"  Wrote {plan_path} ({len(all_plans)} rows)")

    # d. cat_dominance_summary.csv
    summary_path = os.path.join(OUTPUT_DIR, "cat_dominance_summary.csv")
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "cluster", "post_count", "avg_dominance",
            "vs_cats_com_position", "gap_count", "top_priority_action"
        ])
        writer.writeheader()
        for s in all_summaries:
            writer.writerow(s)
    print(f"  Wrote {summary_path} ({len(all_summaries)} rows)")

    # ── Final Summary ──────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("OVERALL CAT DOMINANCE SUMMARY")
    print("=" * 70)
    total_posts = sum(s["post_count"] for s in all_summaries)
    overall_avg = round(
        sum(s["avg_dominance"] * s["post_count"] for s in all_summaries) / total_posts, 1
    ) if total_posts > 0 else 0

    print(f"Total cat posts analyzed: {total_posts}")
    print(f"Overall average dominance: {overall_avg}/100")
    print(f"Total gaps identified: {len(all_gaps)}")
    print(f"Total plan actions: {len(all_plans)}")
    print()

    for s in all_summaries:
        print(f"  {s['cluster']:20s} | {s['post_count']:3d} posts | Avg: {s['avg_dominance']:5.1f} | {s['vs_cats_com_position']}")

    print()
    print("TARGET: Move all 3 clusters to CLEAR LEADERSHIP (avg >= 75)")
    print("PATH: Strengthen existing content + fill topic gaps + exploit UK angles")
    print()

    # Summary of action types
    strengthen = sum(1 for p in all_plans if p["action_type"] == "strengthen")
    create = sum(1 for p in all_plans if p["action_type"] == "create")
    exploit = sum(1 for p in all_plans if p["action_type"] == "exploit")
    print(f"Action breakdown: {strengthen} posts to strengthen | {create} new posts to create | {exploit} UK-exclusive angles to exploit")
    print("=" * 70)


if __name__ == "__main__":
    main()
