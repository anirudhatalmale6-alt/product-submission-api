#!/usr/bin/env python3
"""
Phase 11K – AI Citation Observation Engine for PetHub Online
=============================================================
Three-tier observation system (CONFIRMED / OBSERVED / ESTIMATED) across
five AI platforms, each tracked independently with NO blended metrics.

Platforms:
  1. ChatGPT        – Favors comprehensive, well-structured factual content
  2. Perplexity     – Favors citations, sources, evidence-backed claims
  3. Gemini         – Favors authoritative, well-organized content with schema
  4. AI Overviews   – Favors ranking content with FAQ blocks, structured data
  5. Bing Copilot   – Favors clear structure, Microsoft ecosystem signals

Tiers:
  CONFIRMED  – Verified through API or direct programmatic observation
  OBSERVED   – Manually checked/spotted but not programmatically verified
  ESTIMATED  – Projected/modeled based on content readiness scores

Usage:  python3 ai_citation_observation.py

Outputs (to /var/lib/freelancer/projects/40416335/phase11_data/):
  - ai_citation_observation_by_platform.csv
  - ai_citation_readiness_by_post.csv
  - ai_citation_gaps.csv
  - ai_citation_summary.csv
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
from datetime import datetime, timezone
from statistics import mean

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase11_data"
SITE_DOMAIN = "pethubonline.com"

MAX_RETRIES = 3
RETRY_BACKOFF = 5
WP_DELAY = 2

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Platform definitions – each has distinct weighting for readiness signals
# ---------------------------------------------------------------------------
PLATFORMS = ["chatgpt", "perplexity", "gemini", "ai_overviews", "copilot"]

PLATFORM_LABELS = {
    "chatgpt": "ChatGPT",
    "perplexity": "Perplexity",
    "gemini": "Gemini",
    "ai_overviews": "Google AI Overviews",
    "copilot": "Bing Copilot",
}

# Per-platform weight profiles for readiness dimensions
# Dimensions: structure, depth, uk_specificity, freshness, evidence
# Weights must sum to 1.0 for each platform
PLATFORM_WEIGHTS = {
    "chatgpt": {
        "structure": 0.25,
        "depth": 0.30,
        "uk_specificity": 0.10,
        "freshness": 0.10,
        "evidence": 0.25,
    },
    "perplexity": {
        "structure": 0.15,
        "depth": 0.20,
        "uk_specificity": 0.10,
        "freshness": 0.15,
        "evidence": 0.40,
    },
    "gemini": {
        "structure": 0.30,
        "depth": 0.25,
        "uk_specificity": 0.10,
        "freshness": 0.10,
        "evidence": 0.25,
    },
    "ai_overviews": {
        "structure": 0.30,
        "depth": 0.15,
        "uk_specificity": 0.15,
        "freshness": 0.20,
        "evidence": 0.20,
    },
    "copilot": {
        "structure": 0.35,
        "depth": 0.20,
        "uk_specificity": 0.10,
        "freshness": 0.15,
        "evidence": 0.20,
    },
}

# Per-platform query-type bonus multipliers
# Some platforms favor certain query patterns more than others
PLATFORM_QUERY_BONUSES = {
    "chatgpt": {
        "comparison": 1.15,
        "how_to": 1.10,
        "best_list": 1.05,
        "factual": 1.20,
        "guide": 1.10,
    },
    "perplexity": {
        "comparison": 1.10,
        "how_to": 1.05,
        "best_list": 1.15,
        "factual": 1.25,
        "guide": 1.10,
    },
    "gemini": {
        "comparison": 1.10,
        "how_to": 1.15,
        "best_list": 1.10,
        "factual": 1.15,
        "guide": 1.20,
    },
    "ai_overviews": {
        "comparison": 1.20,
        "how_to": 1.25,
        "best_list": 1.15,
        "factual": 1.10,
        "guide": 1.15,
    },
    "copilot": {
        "comparison": 1.15,
        "how_to": 1.10,
        "best_list": 1.20,
        "factual": 1.10,
        "guide": 1.10,
    },
}

# ---------------------------------------------------------------------------
# Tier system
# ---------------------------------------------------------------------------
TIER_CONFIRMED = "CONFIRMED"
TIER_OBSERVED = "OBSERVED"
TIER_ESTIMATED = "ESTIMATED"

# File for storing confirmed/observed citations (loaded if exists)
VERIFIED_CITATIONS_FILE = os.path.join(OUTPUT_DIR, "verified_citations.json")


def load_verified_citations():
    """
    Load any previously verified citations (CONFIRMED or OBSERVED).
    Returns dict keyed by (platform, query) -> {tier, date, notes}.
    """
    if not os.path.exists(VERIFIED_CITATIONS_FILE):
        return {}
    try:
        with open(VERIFIED_CITATIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        verified = {}
        for entry in data:
            key = (entry["platform"], entry["query"])
            verified[key] = {
                "tier": entry["tier"],
                "date": entry.get("date", ""),
                "notes": entry.get("notes", ""),
                "score_override": entry.get("score_override"),
            }
        return verified
    except (json.JSONDecodeError, KeyError) as e:
        print(f"  [WARN] Could not load verified citations: {e}")
        return {}


# ---------------------------------------------------------------------------
# 10 Clusters with 4 queries each = 40 queries
# Skip Dog Food and Dog Harness COMMERCIAL queries but include educational
# ---------------------------------------------------------------------------
TEST_QUERIES = [
    # Dog Food – educational only (skip commercial like "buy dog food UK")
    {"query": "what ingredients should I avoid in dog food", "cluster": "Dog Food", "type": "factual"},
    {"query": "dry vs wet dog food nutrition comparison", "cluster": "Dog Food", "type": "comparison"},
    {"query": "how to read dog food labels UK", "cluster": "Dog Food", "type": "how_to"},
    {"query": "puppy food feeding schedule by age", "cluster": "Dog Food", "type": "guide"},

    # Dog Harnesses – educational only (skip commercial like "buy dog harness")
    {"query": "harness vs collar which is safer for dogs", "cluster": "Dog Harnesses", "type": "comparison"},
    {"query": "how to measure a dog for a harness correctly", "cluster": "Dog Harnesses", "type": "how_to"},
    {"query": "no-pull harness training techniques", "cluster": "Dog Harnesses", "type": "guide"},
    {"query": "dog harness types explained", "cluster": "Dog Harnesses", "type": "factual"},

    # Dog Beds
    {"query": "best orthopaedic dog beds for joint pain UK", "cluster": "Dog Beds", "type": "best_list"},
    {"query": "how to choose the right size dog bed", "cluster": "Dog Beds", "type": "how_to"},
    {"query": "dog bed materials comparison memory foam vs bolster", "cluster": "Dog Beds", "type": "comparison"},
    {"query": "when should you replace a dog bed", "cluster": "Dog Beds", "type": "factual"},

    # Cat Supplies
    {"query": "best cat scratching posts UK 2026", "cluster": "Cat Supplies", "type": "best_list"},
    {"query": "cat GPS tracker comparison UK", "cluster": "Cat Supplies", "type": "comparison"},
    {"query": "essential supplies for new cat owners checklist", "cluster": "Cat Supplies", "type": "guide"},
    {"query": "how to choose the right cat litter type", "cluster": "Cat Supplies", "type": "how_to"},

    # Dog Care
    {"query": "dog grooming guide for beginners UK", "cluster": "Dog Care", "type": "guide"},
    {"query": "how to trim dog nails safely at home", "cluster": "Dog Care", "type": "how_to"},
    {"query": "seasonal dog care tips UK weather", "cluster": "Dog Care", "type": "factual"},
    {"query": "first time dog owner essentials checklist", "cluster": "Dog Care", "type": "guide"},

    # Dog Health
    {"query": "puppy vaccination schedule UK NHS recommended", "cluster": "Dog Health", "type": "factual"},
    {"query": "dog joint supplement ingredients that actually work", "cluster": "Dog Health", "type": "factual"},
    {"query": "how to spot dental disease in dogs early", "cluster": "Dog Health", "type": "how_to"},
    {"query": "puppy teething timeline stages and relief", "cluster": "Dog Health", "type": "guide"},

    # Dog Toys
    {"query": "indestructible dog toys for heavy chewers UK", "cluster": "Dog Toys", "type": "best_list"},
    {"query": "puzzle toys for dogs mental stimulation benefits", "cluster": "Dog Toys", "type": "factual"},
    {"query": "dog toy safety which materials to avoid", "cluster": "Dog Toys", "type": "factual"},
    {"query": "how to rotate dog toys to keep interest", "cluster": "Dog Toys", "type": "how_to"},

    # Cat Toys
    {"query": "interactive cat toys for indoor cats UK", "cluster": "Cat Toys", "type": "best_list"},
    {"query": "are catnip toys safe for kittens", "cluster": "Cat Toys", "type": "factual"},
    {"query": "how to choose cat toys by play personality", "cluster": "Cat Toys", "type": "how_to"},
    {"query": "DIY cat toys safe homemade options", "cluster": "Cat Toys", "type": "guide"},

    # Training Supplies
    {"query": "best puppy training treats UK low calorie", "cluster": "Training Supplies", "type": "best_list"},
    {"query": "positive reinforcement vs correction training comparison", "cluster": "Training Supplies", "type": "comparison"},
    {"query": "types of dog leads and when to use each", "cluster": "Training Supplies", "type": "guide"},
    {"query": "how to choose the right training treats for your dog", "cluster": "Training Supplies", "type": "how_to"},

    # Indoor Cats
    {"query": "indoor cat exercise ideas to prevent obesity", "cluster": "Indoor Cats", "type": "how_to"},
    {"query": "indoor cat enrichment beyond toys", "cluster": "Indoor Cats", "type": "guide"},
    {"query": "indoor vs outdoor cat lifespan and health comparison", "cluster": "Indoor Cats", "type": "comparison"},
    {"query": "common indoor cat behaviour problems and solutions", "cluster": "Indoor Cats", "type": "factual"},
]

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
        time.sleep(WP_DELAY)
        try:
            result = subprocess.run(
                ["curl", "-s", "--compressed", "-u", AUTH, url],
                capture_output=True, text=True, timeout=120,
            )
        except subprocess.TimeoutExpired:
            print(f"  [TIMEOUT] curl timed out (attempt {attempt})")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF * attempt)
                continue
            return None

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

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            print(f"  [WARN] JSON decode error (attempt {attempt}): {body[:200]}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF * attempt)
                continue
            return None

        if isinstance(data, dict) and data.get("code") == "rest_too_many_requests":
            print(f"  [429] Rate limited, backing off {RETRY_BACKOFF * attempt}s ...")
            time.sleep(RETRY_BACKOFF * attempt)
            continue

        return data

    print("  [ERROR] All retries exhausted")
    return None


def fetch_all_posts():
    """Fetch all published posts (context=edit for raw content)."""
    all_posts = []
    for page in range(1, 5):  # up to 400 posts
        print(f"  Fetching posts page {page} ...")
        data = wp_get("posts", {
            "per_page": "100",
            "page": str(page),
            "status": "publish",
            "context": "edit",
        })
        if data is None:
            print(f"  [ERROR] Failed to fetch page {page}")
            break
        if isinstance(data, dict) and "code" in data:
            break
        all_posts.extend(data)
        print(f"    Got {len(data)} posts from page {page}")
        if len(data) < 100:
            break
    print(f"  Total posts fetched: {len(all_posts)}")
    return all_posts


# ---------------------------------------------------------------------------
# Cluster assignment
# ---------------------------------------------------------------------------
CITATION_CSV = "/var/lib/freelancer/projects/40416335/phase10br_data/citation_preference.csv"


def load_cluster_map():
    """Load id -> cluster from phase10br citation_preference.csv."""
    cluster_map = {}
    if not os.path.exists(CITATION_CSV):
        print(f"  [WARN] {CITATION_CSV} not found - cluster fallback only")
        return cluster_map
    with open(CITATION_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                cluster_map[int(row["id"])] = row.get("cluster", "Uncategorized")
            except (ValueError, KeyError):
                pass
    print(f"  Loaded {len(cluster_map)} cluster assignments from CSV")
    return cluster_map


# ---------------------------------------------------------------------------
# UK Authorities list
# ---------------------------------------------------------------------------
UK_AUTHORITIES = [
    "RSPCA", "BVA", "PFMA", "PDSA", "Blue Cross", "RVC", "FEDIAF",
    "Battersea", "Kennel Club", "Cats Protection", "iCatCare", "DEFRA",
    "Dogs Trust", "RCVS",
]


def count_uk_authorities(content):
    """Count UK authority references."""
    text_upper = content.upper()
    return sum(1 for a in UK_AUTHORITIES if a.upper() in text_upper)


# ---------------------------------------------------------------------------
# Content scoring dimensions (0-100 each)
# ---------------------------------------------------------------------------
def score_structure(content):
    """
    Structure score: H2s, FAQ blocks, comparison tables, lists, At-a-Glance.
    Measures how extractable the content is for AI systems.
    """
    score = 0

    # H2 headings count (well-organized content)
    h2_count = len(re.findall(r'<h2[\s>]', content, re.IGNORECASE))
    if h2_count >= 8:
        score += 20
    elif h2_count >= 5:
        score += 15
    elif h2_count >= 3:
        score += 10
    elif h2_count >= 1:
        score += 5

    # FAQ block presence and depth
    faq_match = re.search(r'(frequently\s+asked|faq|common\s+questions)', content, re.IGNORECASE)
    if faq_match:
        start = faq_match.end()
        block = content[start:start + 5000]
        questions = len(re.findall(r'<(h[34]|strong)[^>]*>[^<]*\?', block, re.IGNORECASE))
        if questions >= 5:
            score += 20
        elif questions >= 3:
            score += 15
        elif questions >= 1:
            score += 10
        else:
            score += 5

    # At-a-Glance / Key Takeaways
    if re.search(r'(at\s+a\s+glance|key\s+takeaway|quick\s+summary|in\s+brief)', content, re.IGNORECASE):
        score += 15

    # Comparison tables
    tables = re.findall(r'<table[\s\S]*?</table>', content, re.IGNORECASE)
    if tables:
        max_rows = max(len(re.findall(r'<tr[\s>]', t, re.IGNORECASE)) for t in tables)
        if max_rows >= 5:
            score += 15
        elif max_rows >= 3:
            score += 10
        else:
            score += 5

    # Ordered/unordered lists
    list_count = len(re.findall(r'<(ul|ol)[\s>]', content, re.IGNORECASE))
    if list_count >= 5:
        score += 15
    elif list_count >= 3:
        score += 10
    elif list_count >= 1:
        score += 5

    # Glossary/definitions section
    if re.search(r'(glossary|terminology|key\s+terms|definitions)', content, re.IGNORECASE):
        score += 10

    # Step-by-step / practical guide
    if re.search(r'(step[- ]by[- ]step|how\s+to|practical\s+guide)', content, re.IGNORECASE):
        score += 5

    return min(score, 100)


def score_depth(content):
    """
    Depth score: Comprehensive enough to be cited as authoritative.
    Measures word count, section depth, topic coverage breadth.
    """
    score = 0

    # Word count (strip HTML)
    plain = re.sub(r'<[^>]+>', ' ', content)
    words = len(plain.split())
    if words >= 5000:
        score += 30
    elif words >= 3500:
        score += 25
    elif words >= 2500:
        score += 20
    elif words >= 1500:
        score += 12
    elif words >= 800:
        score += 5

    # Section count (h2 + h3)
    sections = len(re.findall(r'<h[23][\s>]', content, re.IGNORECASE))
    if sections >= 12:
        score += 20
    elif sections >= 8:
        score += 15
    elif sections >= 5:
        score += 10
    elif sections >= 3:
        score += 5

    # Internal links (shows interconnection)
    internal_links = len(re.findall(r'href=["\'][^"\']*pethubonline\.com', content, re.IGNORECASE))
    if internal_links >= 5:
        score += 15
    elif internal_links >= 3:
        score += 10
    elif internal_links >= 1:
        score += 5

    # Paragraph depth (multiple paragraphs = deeper content)
    paragraphs = len(re.findall(r'<p[\s>]', content, re.IGNORECASE))
    if paragraphs >= 20:
        score += 15
    elif paragraphs >= 12:
        score += 10
    elif paragraphs >= 6:
        score += 5

    # Image/media count (enriched content)
    media = len(re.findall(r'<(img|figure|video)[\s>]', content, re.IGNORECASE))
    if media >= 3:
        score += 10
    elif media >= 1:
        score += 5

    # Bullet/list item density
    list_items = len(re.findall(r'<li[\s>]', content, re.IGNORECASE))
    if list_items >= 15:
        score += 10
    elif list_items >= 8:
        score += 7
    elif list_items >= 3:
        score += 3

    return min(score, 100)


def score_uk_specificity(content, title=""):
    """
    UK-specificity score: UK-specific content has less competition.
    """
    score = 0
    combined = (title + " " + content).upper()

    # "UK" in title or content
    uk_mentions = len(re.findall(r'\bUK\b', combined))
    if uk_mentions >= 10:
        score += 25
    elif uk_mentions >= 5:
        score += 20
    elif uk_mentions >= 2:
        score += 15
    elif uk_mentions >= 1:
        score += 8

    # UK authority references
    uk_refs = count_uk_authorities(content)
    if uk_refs >= 6:
        score += 25
    elif uk_refs >= 4:
        score += 20
    elif uk_refs >= 2:
        score += 12
    elif uk_refs >= 1:
        score += 6

    # British spelling indicators
    british_terms = len(re.findall(
        r'(colour|behaviour|favourite|organise|specialise|centre|licence|analyse|honour|catalogue)',
        content, re.IGNORECASE
    ))
    if british_terms >= 5:
        score += 15
    elif british_terms >= 2:
        score += 10
    elif british_terms >= 1:
        score += 5

    # GBP / pound references
    gbp_refs = len(re.findall(r'(£|GBP|pounds?\s+sterling)', content, re.IGNORECASE))
    if gbp_refs >= 3:
        score += 15
    elif gbp_refs >= 1:
        score += 8

    # UK-specific brands/retailers (Pets at Home, Vet4Pets, etc.)
    uk_brands = len(re.findall(
        r'(Pets\s+at\s+Home|Vet4Pets|Vets4Pets|Purina\s+UK|NHS|veterinary\s+practice)',
        content, re.IGNORECASE
    ))
    if uk_brands >= 3:
        score += 10
    elif uk_brands >= 1:
        score += 5

    # Year currency (2026/2025)
    if re.search(r'202[56]', combined):
        score += 10

    return min(score, 100)


def score_freshness(post):
    """
    Freshness score: Based on publication/modification dates.
    """
    now = datetime.now(timezone.utc)

    # Get dates
    date_str = post.get("date_gmt", post.get("date", ""))
    modified_str = post.get("modified_gmt", post.get("modified", ""))

    def parse_date(ds):
        if not ds:
            return None
        try:
            # WordPress returns ISO format, sometimes with Z, sometimes without
            ds = ds.replace("Z", "+00:00")
            if "+" not in ds and ds[-1] != "Z":
                ds += "+00:00"
            return datetime.fromisoformat(ds)
        except (ValueError, TypeError):
            return None

    pub_date = parse_date(date_str)
    mod_date = parse_date(modified_str)

    score = 0

    # Modification recency
    if mod_date:
        days_since_mod = (now - mod_date).days
        if days_since_mod <= 7:
            score += 40
        elif days_since_mod <= 30:
            score += 35
        elif days_since_mod <= 60:
            score += 25
        elif days_since_mod <= 90:
            score += 15
        elif days_since_mod <= 180:
            score += 8
        else:
            score += 2

    # Publication recency
    if pub_date:
        days_since_pub = (now - pub_date).days
        if days_since_pub <= 30:
            score += 30
        elif days_since_pub <= 90:
            score += 25
        elif days_since_pub <= 180:
            score += 18
        elif days_since_pub <= 365:
            score += 10
        else:
            score += 3

    # Was it recently updated (mod > pub by significant margin)?
    if mod_date and pub_date and mod_date > pub_date:
        update_gap_days = (mod_date - pub_date).days
        if update_gap_days >= 7:
            score += 15  # shows active maintenance
        elif update_gap_days >= 1:
            score += 8

    # Title contains year (2025/2026)
    title = post.get("title", {}).get("raw", "")
    if "2026" in title:
        score += 15
    elif "2025" in title:
        score += 8

    return min(score, 100)


def score_evidence(content):
    """
    Evidence quality: Citations, sources, data references, guidelines.
    """
    score = 0

    # Research sources section
    if re.search(r'(research\s+sources|sources?\s+&?\s*references?|our\s+research|methodology)',
                 content, re.IGNORECASE):
        # Count links in that section
        src_match = re.search(r'(research\s+sources|sources.*references)', content, re.IGNORECASE)
        if src_match:
            block = content[src_match.end():src_match.end() + 3000]
            links = len(re.findall(r'<a\s+[^>]*href=', block, re.IGNORECASE))
            if links >= 5:
                score += 25
            elif links >= 3:
                score += 20
            elif links >= 1:
                score += 12
            else:
                score += 5

    # UK authority citations
    uk_refs = count_uk_authorities(content)
    if uk_refs >= 6:
        score += 25
    elif uk_refs >= 4:
        score += 20
    elif uk_refs >= 2:
        score += 12
    elif uk_refs >= 1:
        score += 6

    # External links (outbound citations)
    external_links = len(re.findall(
        r'<a\s+[^>]*href=["\']https?://(?!pethubonline\.com)',
        content, re.IGNORECASE
    ))
    if external_links >= 5:
        score += 15
    elif external_links >= 3:
        score += 10
    elif external_links >= 1:
        score += 5

    # Data/statistics markers
    data_markers = len(re.findall(
        r'(\d+%|\d+\s*(mg|kg|g|ml|calories?|kcal)|according\s+to|research\s+shows|studies?\s+suggest|data\s+from)',
        content, re.IGNORECASE
    ))
    if data_markers >= 8:
        score += 15
    elif data_markers >= 4:
        score += 10
    elif data_markers >= 1:
        score += 5

    # Evidence-based language
    evidence_lang = len(re.findall(
        r'(evidence[- ]based|peer[- ]reviewed|clinical\s+trial|veterinary\s+guidance|'
        r'RSPCA\s+(recommend|guideline)|BVA\s+(recommend|guideline)|PFMA\s+(standard|guideline))',
        content, re.IGNORECASE
    ))
    if evidence_lang >= 3:
        score += 15
    elif evidence_lang >= 1:
        score += 8

    # Structured data / schema hints
    if re.search(r'(schema|itemtype|application/ld\+json|structured\s+data)', content, re.IGNORECASE):
        score += 5

    return min(score, 100)


# ---------------------------------------------------------------------------
# Per-platform readiness calculation
# ---------------------------------------------------------------------------
def compute_platform_readiness(platform, structure, depth, uk_spec, freshness, evidence):
    """
    Compute platform-specific readiness score using that platform's weight profile.
    Returns 0-100.
    """
    w = PLATFORM_WEIGHTS[platform]
    raw = (
        structure * w["structure"] +
        depth * w["depth"] +
        uk_spec * w["uk_specificity"] +
        freshness * w["freshness"] +
        evidence * w["evidence"]
    )
    return round(raw, 1)


def compute_query_platform_score(platform, post_readiness, query_type, content_match_strength):
    """
    For a specific query+platform, compute the estimated citation likelihood score.
    Factors in the platform readiness, query type bonus, and content match strength.
    """
    base = post_readiness
    bonus = PLATFORM_QUERY_BONUSES[platform].get(query_type, 1.0)
    # Content match strength (0-1) scales the score
    match_factor = min(content_match_strength / 100.0, 1.0)

    raw = base * bonus * (0.4 + 0.6 * match_factor)
    return round(min(raw, 100), 1)


# ---------------------------------------------------------------------------
# Query-to-post matching
# ---------------------------------------------------------------------------
def normalise(text):
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', ' ', text.lower())).strip()


def build_keyword_set(query):
    stop = {
        "a", "an", "the", "is", "are", "for", "to", "of", "and", "in",
        "on", "with", "how", "what", "which", "best", "top", "guide",
        "uk", "2025", "2026", "your", "my", "vs", "or", "i", "should",
    }
    words = normalise(query).split()
    return [w for w in words if w not in stop and len(w) > 1]


def match_query_to_posts(query_text, query_cluster, posts, cluster_map):
    """
    Find the best matching post for a query.
    Returns (post, match_score) or (None, 0).
    """
    keywords = build_keyword_set(query_text)
    query_norm = normalise(query_text)
    best_post = None
    best_score = 0

    for post in posts:
        pid = post["id"]
        title_raw = post.get("title", {}).get("raw", "")
        title_norm = normalise(title_raw)
        content_raw = post.get("content", {}).get("raw", "")
        content_norm = normalise(content_raw[:3000])

        post_cluster = cluster_map.get(pid, "Uncategorized")

        score = 0

        # Keyword overlap in title
        title_hits = sum(1 for kw in keywords if kw in title_norm)
        score += title_hits * 25

        # Keyword overlap in content intro
        content_hits = sum(1 for kw in keywords if kw in content_norm)
        score += min(content_hits * 5, 30)

        # Cluster match
        if post_cluster == query_cluster:
            score += 20
        elif query_cluster in ("General",):
            score += 5

        # Full query substring match
        if query_norm in title_norm:
            score += 40

        # UK authority boost
        uk_count = count_uk_authorities(content_raw)
        score += min(uk_count * 3, 15)

        if score > best_score:
            best_post = post
            best_score = score

    return best_post, best_score


# ---------------------------------------------------------------------------
# Gap analysis – per platform
# ---------------------------------------------------------------------------
def analyze_gaps_per_platform(post, platform, platform_readiness, structure, depth,
                              uk_spec, freshness, evidence, cluster):
    """
    Generate platform-specific gap analysis.
    Returns list of (gap_type, recommendation, priority).
    """
    gaps = []

    if platform_readiness >= 75:
        # High readiness, minor tweaks only
        if platform == "perplexity" and evidence < 60:
            gaps.append((
                "evidence_weak_for_perplexity",
                "Add more cited sources and research references; Perplexity heavily weights evidence",
                "medium"
            ))
        if platform == "ai_overviews" and structure < 70:
            gaps.append((
                "structure_weak_for_ai_overviews",
                "Add FAQ schema and structured data blocks; AI Overviews extracts from these",
                "medium"
            ))
        return gaps

    # Below 75 readiness - identify platform-specific gaps
    w = PLATFORM_WEIGHTS[platform]

    # Check each dimension against the platform's emphasis
    if structure < 60 and w["structure"] >= 0.25:
        gaps.append((
            "low_structure",
            f"Add H2 headings, FAQ blocks, comparison tables, bullet lists ({PLATFORM_LABELS[platform]} weights structure at {int(w['structure']*100)}%)",
            "high" if structure < 40 else "medium"
        ))

    if depth < 50 and w["depth"] >= 0.20:
        gaps.append((
            "low_depth",
            f"Expand content depth with more sections, examples, and detail ({PLATFORM_LABELS[platform]} weights depth at {int(w['depth']*100)}%)",
            "high" if depth < 30 else "medium"
        ))

    if uk_spec < 40 and w["uk_specificity"] >= 0.10:
        gaps.append((
            "low_uk_specificity",
            f"Add UK authority references (RSPCA, BVA, PDSA), British spelling, GBP pricing",
            "medium"
        ))

    if freshness < 40 and w["freshness"] >= 0.15:
        gaps.append((
            "low_freshness",
            f"Update content with current year references and recent data ({PLATFORM_LABELS[platform]} weights freshness at {int(w['freshness']*100)}%)",
            "high" if freshness < 20 else "medium"
        ))

    if evidence < 50 and w["evidence"] >= 0.20:
        priority = "critical" if platform == "perplexity" and evidence < 30 else "high"
        gaps.append((
            "low_evidence",
            f"Add research citations, external sources, data references ({PLATFORM_LABELS[platform]} weights evidence at {int(w['evidence']*100)}%)",
            priority
        ))

    if not gaps:
        gaps.append((
            "general_improvement",
            f"Overall readiness {platform_readiness:.0f}/100 for {PLATFORM_LABELS[platform]}; improve weakest dimension",
            "low"
        ))

    return gaps


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------
def main():
    print("=" * 76)
    print("Phase 11K - AI Citation Observation Engine for PetHub Online")
    print("Three-Tier System: CONFIRMED / OBSERVED / ESTIMATED")
    print("Five Platforms: ChatGPT | Perplexity | Gemini | AI Overviews | Copilot")
    print("=" * 76)

    # -- Step A: Load verified citations (CONFIRMED + OBSERVED) --
    print("\n[A] Loading verified citations ...")
    verified = load_verified_citations()
    confirmed_count = sum(1 for v in verified.values() if v["tier"] == TIER_CONFIRMED)
    observed_count = sum(1 for v in verified.values() if v["tier"] == TIER_OBSERVED)
    print(f"  Loaded {confirmed_count} CONFIRMED + {observed_count} OBSERVED citations")
    if not verified:
        print("  (No verified citations yet - all assessments will be ESTIMATED)")

    # -- Step B: Fetch all WordPress posts --
    print("\n[B] Fetching WordPress posts ...")
    posts = fetch_all_posts()
    if not posts:
        print("[FATAL] Could not fetch any posts. Exiting.")
        sys.exit(1)

    # -- Step C: Load cluster map --
    print("\n[C] Loading cluster assignments ...")
    cluster_map = load_cluster_map()

    # -- Step D: Score every post on all 5 dimensions --
    print(f"\n[D] Scoring {len(posts)} posts on 5 readiness dimensions ...")
    post_scores = {}
    for post in posts:
        pid = post["id"]
        title = post.get("title", {}).get("raw", "")
        content = post.get("content", {}).get("raw", "")
        cluster = cluster_map.get(pid, "Uncategorized")

        s_structure = score_structure(content)
        s_depth = score_depth(content)
        s_uk = score_uk_specificity(content, title)
        s_freshness = score_freshness(post)
        s_evidence = score_evidence(content)
        overall = round(mean([s_structure, s_depth, s_uk, s_freshness, s_evidence]), 1)

        # Per-platform readiness
        platform_scores = {}
        for plat in PLATFORMS:
            platform_scores[plat] = compute_platform_readiness(
                plat, s_structure, s_depth, s_uk, s_freshness, s_evidence
            )

        post_scores[pid] = {
            "post_id": pid,
            "title": title,
            "cluster": cluster,
            "structure_score": s_structure,
            "depth_score": s_depth,
            "uk_score": s_uk,
            "freshness_score": s_freshness,
            "evidence_score": s_evidence,
            "overall_readiness": overall,
            "platform_readiness": platform_scores,
            "post": post,
        }

    print(f"  Scored {len(post_scores)} posts")
    avg_overall = mean([ps["overall_readiness"] for ps in post_scores.values()])
    print(f"  Average overall readiness: {avg_overall:.1f}/100")

    # -- Step E: Analyze 40 test queries across 5 platforms --
    print(f"\n[E] Analyzing {len(TEST_QUERIES)} queries x {len(PLATFORMS)} platforms = {len(TEST_QUERIES)*len(PLATFORMS)} assessments ...")

    query_results = []
    all_gaps = []
    platform_stats = {p: {"confirmed": 0, "observed": 0, "estimated": 0, "scores": []}
                      for p in PLATFORMS}
    cluster_platform_scores = defaultdict(lambda: {p: [] for p in PLATFORMS})

    for i, q in enumerate(TEST_QUERIES, 1):
        query_text = q["query"]
        cluster = q["cluster"]
        query_type = q["type"]
        print(f"\n  [{i:02d}/{len(TEST_QUERIES)}] \"{query_text}\" ({cluster})")

        # Match to best post
        matched_post, match_score = match_query_to_posts(
            query_text, cluster, posts, cluster_map
        )

        row = {
            "query": query_text,
            "cluster": cluster,
        }

        if matched_post:
            pid = matched_post["id"]
            ps = post_scores[pid]
            title = ps["title"]
            print(f"    Matched: [{pid}] {title[:55]}...")

            for plat in PLATFORMS:
                # Check if we have a verified citation
                vkey = (plat, query_text)
                if vkey in verified:
                    v = verified[vkey]
                    tier = v["tier"]
                    plat_score = v["score_override"] if v["score_override"] is not None else ps["platform_readiness"][plat]
                else:
                    tier = TIER_ESTIMATED
                    plat_score = compute_query_platform_score(
                        plat, ps["platform_readiness"][plat], query_type, match_score
                    )

                row[f"{plat}_score"] = plat_score
                row[f"{plat}_tier"] = tier

                # Track stats
                if tier == TIER_CONFIRMED:
                    platform_stats[plat]["confirmed"] += 1
                elif tier == TIER_OBSERVED:
                    platform_stats[plat]["observed"] += 1
                else:
                    platform_stats[plat]["estimated"] += 1
                platform_stats[plat]["scores"].append(plat_score)
                cluster_platform_scores[cluster][plat].append(plat_score)

                # Gap analysis per platform
                gaps = analyze_gaps_per_platform(
                    matched_post, plat, plat_score,
                    ps["structure_score"], ps["depth_score"],
                    ps["uk_score"], ps["freshness_score"], ps["evidence_score"],
                    cluster
                )
                for gap_type, recommendation, priority in gaps:
                    all_gaps.append({
                        "post_id": pid,
                        "title": title,
                        "cluster": cluster,
                        "platform": PLATFORM_LABELS[plat],
                        "gap_type": gap_type,
                        "recommendation": recommendation,
                        "priority": priority,
                    })

            print(f"    ChatGPT={row['chatgpt_score']:.0f} | Perplexity={row['perplexity_score']:.0f} | "
                  f"Gemini={row['gemini_score']:.0f} | AIOverviews={row['ai_overviews_score']:.0f} | "
                  f"Copilot={row['copilot_score']:.0f}")

        else:
            print(f"    No matching post found")
            for plat in PLATFORMS:
                vkey = (plat, query_text)
                if vkey in verified:
                    v = verified[vkey]
                    tier = v["tier"]
                    plat_score = v["score_override"] if v["score_override"] is not None else 0
                else:
                    tier = TIER_ESTIMATED
                    plat_score = 0

                row[f"{plat}_score"] = plat_score
                row[f"{plat}_tier"] = tier
                platform_stats[plat]["estimated"] += 1
                platform_stats[plat]["scores"].append(plat_score)
                cluster_platform_scores[cluster][plat].append(plat_score)

                all_gaps.append({
                    "post_id": "",
                    "title": "",
                    "cluster": cluster,
                    "platform": PLATFORM_LABELS[plat],
                    "gap_type": "no_matching_content",
                    "recommendation": f"Create content targeting '{query_text}' in {cluster} cluster",
                    "priority": "critical",
                })

        query_results.append(row)

    # -- Step F: Generate CSVs --
    print("\n" + "=" * 76)
    print("[F] Generating CSV outputs ...")

    # F1: ai_citation_observation_by_platform.csv
    obs_csv = os.path.join(OUTPUT_DIR, "ai_citation_observation_by_platform.csv")
    with open(obs_csv, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["query", "cluster"]
        for plat in PLATFORMS:
            fieldnames.extend([f"{plat}_score", f"{plat}_tier"])
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in query_results:
            writer.writerow(row)
    print(f"  Written: {obs_csv}")

    # F2: ai_citation_readiness_by_post.csv
    post_csv = os.path.join(OUTPUT_DIR, "ai_citation_readiness_by_post.csv")
    with open(post_csv, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "post_id", "title", "cluster",
            "structure_score", "depth_score", "uk_score", "freshness_score", "evidence_score",
            "overall_readiness",
            "chatgpt_readiness", "perplexity_readiness", "gemini_readiness",
            "ai_overviews_readiness", "copilot_readiness",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        # Sort by overall readiness descending
        sorted_posts = sorted(post_scores.values(), key=lambda x: x["overall_readiness"], reverse=True)
        for ps in sorted_posts:
            writer.writerow({
                "post_id": ps["post_id"],
                "title": ps["title"],
                "cluster": ps["cluster"],
                "structure_score": ps["structure_score"],
                "depth_score": ps["depth_score"],
                "uk_score": ps["uk_score"],
                "freshness_score": ps["freshness_score"],
                "evidence_score": ps["evidence_score"],
                "overall_readiness": ps["overall_readiness"],
                "chatgpt_readiness": ps["platform_readiness"]["chatgpt"],
                "perplexity_readiness": ps["platform_readiness"]["perplexity"],
                "gemini_readiness": ps["platform_readiness"]["gemini"],
                "ai_overviews_readiness": ps["platform_readiness"]["ai_overviews"],
                "copilot_readiness": ps["platform_readiness"]["copilot"],
            })
    print(f"  Written: {post_csv}")

    # F3: ai_citation_gaps.csv
    gaps_csv = os.path.join(OUTPUT_DIR, "ai_citation_gaps.csv")
    # Deduplicate gaps (same post_id + platform + gap_type)
    seen_gaps = set()
    unique_gaps = []
    for g in all_gaps:
        key = (g["post_id"], g["platform"], g["gap_type"])
        if key not in seen_gaps:
            seen_gaps.add(key)
            unique_gaps.append(g)
    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    unique_gaps.sort(key=lambda g: (priority_order.get(g["priority"], 9), g["cluster"]))

    with open(gaps_csv, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["post_id", "title", "cluster", "platform", "gap_type", "recommendation", "priority"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for g in unique_gaps:
            writer.writerow(g)
    print(f"  Written: {gaps_csv}")

    # F4: ai_citation_summary.csv
    summary_csv = os.path.join(OUTPUT_DIR, "ai_citation_summary.csv")
    with open(summary_csv, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "platform", "confirmed_citations", "observed_citations", "estimated_citations",
            "readiness_score", "top_opportunity_cluster",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for plat in PLATFORMS:
            stats = platform_stats[plat]
            avg_score = round(mean(stats["scores"]), 1) if stats["scores"] else 0

            # Find top opportunity cluster (highest average score for this platform)
            best_cluster = ""
            best_cluster_score = 0
            for cl, plat_scores in cluster_platform_scores.items():
                if plat_scores[plat]:
                    cl_avg = mean(plat_scores[plat])
                    if cl_avg > best_cluster_score:
                        best_cluster_score = cl_avg
                        best_cluster = cl

            writer.writerow({
                "platform": PLATFORM_LABELS[plat],
                "confirmed_citations": stats["confirmed"],
                "observed_citations": stats["observed"],
                "estimated_citations": stats["estimated"],
                "readiness_score": avg_score,
                "top_opportunity_cluster": best_cluster,
            })
    print(f"  Written: {summary_csv}")

    # -- Step G: Print summary --
    print("\n" + "=" * 76)
    print("[G] AI Citation Observation Summary - Phase 11K")
    print("=" * 76)

    print("\n  THREE-TIER OBSERVATION STATUS")
    print("  " + "-" * 72)
    total_assessments = len(TEST_QUERIES) * len(PLATFORMS)
    total_confirmed = sum(s["confirmed"] for s in platform_stats.values())
    total_observed = sum(s["observed"] for s in platform_stats.values())
    total_estimated = sum(s["estimated"] for s in platform_stats.values())
    print(f"  Total assessments:  {total_assessments}")
    print(f"  CONFIRMED:          {total_confirmed}  (verified via API/direct observation)")
    print(f"  OBSERVED:           {total_observed}  (manually checked, not programmatic)")
    print(f"  ESTIMATED:          {total_estimated}  (modeled from content readiness)")
    print()

    print("  PER-PLATFORM READINESS (no blended metrics)")
    print("  " + "-" * 72)
    print(f"  {'Platform':<22} {'Readiness':>9} {'CONFIRMED':>10} {'OBSERVED':>9} {'ESTIMATED':>10} {'Top Cluster'}")
    print(f"  {'=' * 22} {'=' * 9} {'=' * 10} {'=' * 9} {'=' * 10} {'=' * 20}")

    for plat in PLATFORMS:
        stats = platform_stats[plat]
        avg = round(mean(stats["scores"]), 1) if stats["scores"] else 0

        best_cluster = ""
        best_score = 0
        for cl, plat_scores in cluster_platform_scores.items():
            if plat_scores[plat]:
                cl_avg = mean(plat_scores[plat])
                if cl_avg > best_score:
                    best_score = cl_avg
                    best_cluster = cl

        print(f"  {PLATFORM_LABELS[plat]:<22} {avg:>8.1f} {stats['confirmed']:>10} "
              f"{stats['observed']:>9} {stats['estimated']:>10} {best_cluster}")

    print()
    print("  PER-CLUSTER BREAKDOWN BY PLATFORM")
    print("  " + "-" * 72)
    header = f"  {'Cluster':<22}"
    for plat in PLATFORMS:
        label = PLATFORM_LABELS[plat][:8]
        header += f" {label:>9}"
    print(header)
    print(f"  {'=' * 22}" + " =========" * len(PLATFORMS))

    for cluster in sorted(cluster_platform_scores.keys()):
        row_str = f"  {cluster:<22}"
        for plat in PLATFORMS:
            scores = cluster_platform_scores[cluster][plat]
            if scores:
                avg = round(mean(scores), 1)
                row_str += f" {avg:>8.1f}"
            else:
                row_str += f" {'N/A':>9}"
        print(row_str)

    # Post readiness distribution
    print()
    print("  POST READINESS DISTRIBUTION")
    print("  " + "-" * 72)
    all_overall = [ps["overall_readiness"] for ps in post_scores.values()]
    high = sum(1 for s in all_overall if s >= 70)
    med = sum(1 for s in all_overall if 50 <= s < 70)
    low = sum(1 for s in all_overall if s < 50)
    print(f"  High readiness (>=70):   {high} posts")
    print(f"  Medium readiness (50-69): {med} posts")
    print(f"  Low readiness (<50):      {low} posts")

    # Top 5 posts by overall readiness
    print()
    print("  TOP 5 MOST AI-CITATION-READY POSTS")
    print("  " + "-" * 72)
    sorted_by_overall = sorted(post_scores.values(), key=lambda x: x["overall_readiness"], reverse=True)
    for ps in sorted_by_overall[:5]:
        plat_str = " | ".join(
            f"{PLATFORM_LABELS[p][:4]}={ps['platform_readiness'][p]:.0f}"
            for p in PLATFORMS
        )
        print(f"  [{ps['post_id']}] {ps['title'][:50]}")
        print(f"       Overall={ps['overall_readiness']:.1f} | {plat_str}")

    # Gap summary
    print()
    print("  GAP ANALYSIS SUMMARY")
    print("  " + "-" * 72)
    critical_gaps = sum(1 for g in unique_gaps if g["priority"] == "critical")
    high_gaps = sum(1 for g in unique_gaps if g["priority"] == "high")
    medium_gaps = sum(1 for g in unique_gaps if g["priority"] == "medium")
    low_gaps = sum(1 for g in unique_gaps if g["priority"] == "low")
    print(f"  Total unique gaps:   {len(unique_gaps)}")
    print(f"  CRITICAL priority:   {critical_gaps}")
    print(f"  HIGH priority:       {high_gaps}")
    print(f"  MEDIUM priority:     {medium_gaps}")
    print(f"  LOW priority:        {low_gaps}")

    # Gap distribution by platform
    print()
    print("  GAPS BY PLATFORM")
    print("  " + "-" * 72)
    for plat in PLATFORMS:
        plat_gaps = [g for g in unique_gaps if g["platform"] == PLATFORM_LABELS[plat]]
        critical = sum(1 for g in plat_gaps if g["priority"] == "critical")
        high_p = sum(1 for g in plat_gaps if g["priority"] == "high")
        print(f"  {PLATFORM_LABELS[plat]:<22} {len(plat_gaps)} gaps "
              f"({critical} critical, {high_p} high)")

    print()
    print("  NOTE: All current assessments are ESTIMATED.")
    print("  The framework supports adding CONFIRMED and OBSERVED data via:")
    print(f"    {VERIFIED_CITATIONS_FILE}")
    print("  Format: [{\"platform\": \"chatgpt\", \"query\": \"...\", ")
    print("            \"tier\": \"CONFIRMED\", \"date\": \"2026-05-29\",")
    print("            \"notes\": \"...\", \"score_override\": 85}]")

    print("\n" + "=" * 76)
    print("Phase 11K AI Citation Observation Engine complete.")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 76)


if __name__ == "__main__":
    main()
