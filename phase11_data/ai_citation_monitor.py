#!/usr/bin/env python3
"""
Phase 11 – AI Citation Monitoring Engine for PetHub Online (pethubonline.com)
=============================================================================
Checks whether PetHub content appears in AI search results and assesses
citation-readiness across 30 strategic queries spanning all PetHub clusters.

Usage:  python3 ai_citation_monitor.py

Outputs (to /var/lib/freelancer/projects/40416335/phase11_data/):
  - ai_citation_queries.csv      Per-query readiness + Google visibility
  - ai_citation_readiness.csv    Per-cluster aggregate readiness
  - ai_citation_gaps.csv         Actionable gap analysis
"""

import csv
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
from collections import defaultdict
from statistics import mean

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
WP_API = "https://pethubonline.com/wp-json/wp/v2"
WP_AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase11_data"
SITE_DOMAIN = "pethubonline.com"

MAX_RETRIES = 3
RETRY_BACKOFF = 5          # seconds * attempt
WP_DELAY = 2               # seconds between WP API calls
GOOGLE_DELAY = 5           # seconds between Google searches
MAX_GOOGLE_SEARCHES = 10   # rate-limit cap

GOOGLE_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. Test Queries – 30 queries across PetHub clusters
# ---------------------------------------------------------------------------
TEST_QUERIES = [
    # Dog Food (3 queries)
    {"query": "best dog food UK", "cluster": "Dog Food"},
    {"query": "dry vs wet dog food", "cluster": "Dog Food"},
    {"query": "dog food ingredients to avoid", "cluster": "Dog Food"},
    # Dog Beds (3 queries)
    {"query": "best dog beds UK", "cluster": "Dog Beds"},
    {"query": "orthopedic dog beds", "cluster": "Dog Beds"},
    {"query": "dog bed sizing guide", "cluster": "Dog Beds"},
    # Cat Supplies (3 queries)
    {"query": "best cat scratching posts UK", "cluster": "Cat Supplies"},
    {"query": "cat GPS trackers UK", "cluster": "Cat Supplies"},
    {"query": "best cat litter", "cluster": "Cat Supplies"},
    # Dog Care (3 queries)
    {"query": "dog grooming guide UK", "cluster": "Dog Care"},
    {"query": "how to trim dog nails", "cluster": "Dog Care"},
    {"query": "puppy essentials checklist", "cluster": "Dog Care"},
    # Dog Health (3 queries)
    {"query": "dog vaccination schedule UK", "cluster": "Dog Health"},
    {"query": "puppy teething guide", "cluster": "Dog Health"},
    {"query": "dog joint supplements", "cluster": "Dog Health"},
    # Dog Toys (3 queries)
    {"query": "indestructible dog toys UK", "cluster": "Dog Toys"},
    {"query": "puzzle toys for dogs", "cluster": "Dog Toys"},
    {"query": "safe dog toy materials", "cluster": "Dog Toys"},
    # Cat Toys (3 queries)
    {"query": "interactive cat toys", "cluster": "Cat Toys"},
    {"query": "cat toys for indoor cats", "cluster": "Cat Toys"},
    {"query": "catnip toys safe", "cluster": "Cat Toys"},
    # Dog Harnesses (3 queries)
    {"query": "no-pull dog harness UK", "cluster": "Dog Harnesses"},
    {"query": "harness vs collar for dogs", "cluster": "Dog Harnesses"},
    {"query": "dog harness fitting guide", "cluster": "Dog Harnesses"},
    # Training (3 queries)
    {"query": "puppy training treats UK", "cluster": "Training Supplies"},
    {"query": "positive reinforcement dog training", "cluster": "Training Supplies"},
    {"query": "dog lead types", "cluster": "Training Supplies"},
    # General / Mixed (3 queries)
    {"query": "pet enrichment ideas", "cluster": "General"},
    {"query": "indoor cat exercise", "cluster": "Indoor Cats"},
    {"query": "senior dog care tips", "cluster": "General"},
]

# Priority subset for actual Google searches (10 queries, most strategic)
GOOGLE_SEARCH_QUERIES = [
    "best dog food UK",
    "best dog beds UK",
    "best cat scratching posts UK",
    "dog grooming guide UK",
    "dog vaccination schedule UK",
    "indestructible dog toys UK",
    "interactive cat toys",
    "no-pull dog harness UK",
    "puppy training treats UK",
    "indoor cat exercise",
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
                ["curl", "-s", "--compressed", "-u", WP_AUTH, url],
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
            print(f"  [429] Rate limited, backing off {RETRY_BACKOFF * attempt}s …")
            time.sleep(RETRY_BACKOFF * attempt)
            continue

        return data

    print("  [ERROR] All retries exhausted")
    return None


def fetch_all_posts():
    """Fetch all published posts (context=edit for raw Gutenberg content)."""
    all_posts = []
    for page in range(1, 5):  # up to 400 posts
        print(f"  Fetching posts page {page} …")
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
            # last page or error
            break
        all_posts.extend(data)
        print(f"    Got {len(data)} posts from page {page}")
        if len(data) < 100:
            break
    print(f"  Total posts fetched: {len(all_posts)}")
    return all_posts


# ---------------------------------------------------------------------------
# Cluster assignment (from citation_preference.csv + fallback)
# ---------------------------------------------------------------------------
CITATION_CSV = "/var/lib/freelancer/projects/40416335/phase10br_data/citation_preference.csv"

def load_cluster_map():
    """Load id -> cluster from phase10br citation_preference.csv."""
    cluster_map = {}
    if not os.path.exists(CITATION_CSV):
        print(f"  [WARN] {CITATION_CSV} not found – cluster fallback only")
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
# Content analysis helpers – binary presence checks
# ---------------------------------------------------------------------------
def has_at_a_glance(content):
    """Check for 'At a Glance' or 'Key Takeaways' block."""
    return bool(re.search(
        r'(at\s+a\s+glance|key\s+takeaway|quick\s+summary|in\s+brief)',
        content, re.IGNORECASE
    ))


def has_faq(content):
    """Check for FAQ / frequently asked questions block."""
    return bool(re.search(
        r'(frequently\s+asked|faq|common\s+questions|questions?\s+answered)',
        content, re.IGNORECASE
    ))


def has_glossary(content):
    """Check for glossary / terminology block."""
    return bool(re.search(
        r'(glossary|terminology|key\s+terms|definitions|what\s+does\s+.*\s+mean)',
        content, re.IGNORECASE
    ))


def has_comparison(content):
    """Check for comparison tables or comparison blocks."""
    has_striped = bool(re.search(r'is-style-stripes', content, re.IGNORECASE))
    has_heading = bool(re.search(
        r'(comparison|compared|vs\b|versus|\bpros\b.*\bcons\b)',
        content, re.IGNORECASE
    ))
    has_table = bool(re.search(r'<table[\s>]', content, re.IGNORECASE))
    return has_striped or (has_heading and has_table) or has_heading


def has_practical_guide(content):
    """Check for step-by-step / how-to / practical guidance blocks."""
    return bool(re.search(
        r'(step[- ]by[- ]step|how\s+to|practical\s+guide|getting\s+started|'
        r'what\s+you.ll\s+need|checklist|action\s+plan|our\s+approach)',
        content, re.IGNORECASE
    ))


def has_research_sources(content):
    """Check for research sources / references / evidence blocks."""
    return bool(re.search(
        r'(research\s+sources|sources?\s+&?\s*references?|evidence[- ]based|'
        r'cited\s+sources|our\s+research|methodology|standards?\s+(we\s+)?follow)',
        content, re.IGNORECASE
    ))


# ---------------------------------------------------------------------------
# Content quality depth scoring – goes beyond binary presence
# ---------------------------------------------------------------------------
UK_AUTHORITIES = [
    "RSPCA", "BVA", "PFMA", "PDSA", "Blue Cross", "RVC", "FEDIAF",
    "Battersea", "Kennel Club", "Cats Protection", "iCatCare", "DEFRA",
]


def count_uk_authorities(content):
    """Count UK authority references (RSPCA, BVA, PFMA, etc.)."""
    text_upper = content.upper()
    return sum(1 for a in UK_AUTHORITIES if a.upper() in text_upper)


def quality_depth_score(content):
    """
    Score content QUALITY depth on 0–100 scale.  Goes beyond binary
    block-presence to measure how rich/deep each block actually is.

    Dimensions (each scored 0-max, total normalised to 100):
      - At a Glance depth:      0-10  (bullet count, word count)
      - FAQ depth:              0-15  (number of Q&A pairs)
      - Glossary depth:         0-10  (number of defined terms)
      - Comparison depth:       0-15  (table row count, striped tables)
      - Practical guide depth:  0-15  (numbered steps, word count)
      - Research sources depth: 0-15  (number of distinct sources/citations)
      - UK authority density:   0-10  (distinct UK authorities cited)
      - Content length:         0-10  (word count proxy for depth)
    Total raw max = 100
    """
    score = 0

    # ── At a Glance depth ──
    aag_match = re.search(
        r'(at\s+a\s+glance|key\s+takeaway|quick\s+summary)',
        content, re.IGNORECASE
    )
    if aag_match:
        # Count bullet points in the 2000 chars after the heading
        start = aag_match.end()
        block = content[start:start + 2000]
        bullets = len(re.findall(r'<li[^>]*>', block, re.IGNORECASE))
        if bullets >= 5:
            score += 10
        elif bullets >= 3:
            score += 7
        elif bullets >= 1:
            score += 4
        else:
            score += 2  # heading exists but minimal bullets

    # ── FAQ depth ──
    faq_match = re.search(
        r'(frequently\s+asked|faq|common\s+questions)',
        content, re.IGNORECASE
    )
    if faq_match:
        start = faq_match.end()
        block = content[start:start + 5000]
        # Count question headings (h3/h4 or strong tags with ?)
        questions = len(re.findall(r'<(h[34]|strong)[^>]*>[^<]*\?', block, re.IGNORECASE))
        if questions >= 5:
            score += 15
        elif questions >= 3:
            score += 10
        elif questions >= 1:
            score += 6
        else:
            score += 3  # section exists but few questions

    # ── Glossary depth ──
    glos_match = re.search(r'(glossary|terminology|key\s+terms)', content, re.IGNORECASE)
    if glos_match:
        start = glos_match.end()
        block = content[start:start + 5000]
        # Count definition-like items (dt tags, bold terms, or bullet items)
        terms = len(re.findall(r'(<dt|<strong|<b>)', block, re.IGNORECASE))
        if terms >= 8:
            score += 10
        elif terms >= 4:
            score += 7
        elif terms >= 1:
            score += 4
        else:
            score += 2

    # ── Comparison depth ──
    tables = re.findall(r'<table[\s\S]*?</table>', content, re.IGNORECASE)
    if tables:
        max_rows = max(len(re.findall(r'<tr[\s>]', t, re.IGNORECASE)) for t in tables)
        striped = bool(re.search(r'is-style-stripes', content))
        if max_rows >= 6 and striped:
            score += 15
        elif max_rows >= 4:
            score += 11
        elif max_rows >= 2:
            score += 7
        else:
            score += 4

    # ── Practical guide depth ──
    prac_match = re.search(
        r'(step[- ]by[- ]step|practical\s+guide|how\s+to|getting\s+started)',
        content, re.IGNORECASE
    )
    if prac_match:
        start = prac_match.end()
        block = content[start:start + 5000]
        steps = len(re.findall(r'<(h[34]|li|ol)[^>]*>', block, re.IGNORECASE))
        if steps >= 8:
            score += 15
        elif steps >= 4:
            score += 10
        elif steps >= 1:
            score += 6
        else:
            score += 3

    # ── Research sources depth ──
    src_match = re.search(
        r'(research\s+sources|sources.*references|standards.*follow)',
        content, re.IGNORECASE
    )
    if src_match:
        start = src_match.end()
        block = content[start:start + 3000]
        # Count hyperlinks (likely citation links)
        links = len(re.findall(r'<a\s+[^>]*href=', block, re.IGNORECASE))
        # Count list items as source entries
        items = len(re.findall(r'<li[^>]*>', block, re.IGNORECASE))
        refs = max(links, items)
        if refs >= 5:
            score += 15
        elif refs >= 3:
            score += 10
        elif refs >= 1:
            score += 6
        else:
            score += 3

    # ── UK authority density ──
    uk_count = count_uk_authorities(content)
    if uk_count >= 6:
        score += 10
    elif uk_count >= 4:
        score += 7
    elif uk_count >= 2:
        score += 4
    elif uk_count >= 1:
        score += 2

    # ── Content length (word count proxy) ──
    # Strip HTML tags for word count
    plain = re.sub(r'<[^>]+>', ' ', content)
    words = len(plain.split())
    if words >= 4000:
        score += 10
    elif words >= 2500:
        score += 7
    elif words >= 1500:
        score += 4
    elif words >= 500:
        score += 2

    return min(score, 100)


def compute_readiness_score(flags):
    """
    Compute a 0-100 STRUCTURE readiness score from content block presence.
    Weights reflect importance for AI citation:
      at_a_glance: 20  (extractable summary)
      faq:         20  (direct Q&A format)
      glossary:    10  (definitional content)
      comparison:  15  (structured decision aid)
      practical:   20  (actionable guidance)
      research:    15  (trust / authority signals)
    """
    weights = {
        "has_at_a_glance": 20,
        "has_faq": 20,
        "has_glossary": 10,
        "has_comparison": 15,
        "has_practical_guide": 20,
        "has_research_sources": 15,
    }
    score = sum(weights[k] for k, v in flags.items() if v)
    return score


# ---------------------------------------------------------------------------
# Query-to-post matching
# ---------------------------------------------------------------------------
def normalise(text):
    """Lowercase, strip non-alpha, collapse whitespace."""
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', ' ', text.lower())).strip()


def build_keyword_set(query):
    """Extract meaningful keywords from a query (drop stop words)."""
    stop = {
        "a", "an", "the", "is", "are", "for", "to", "of", "and", "in",
        "on", "with", "how", "what", "which", "best", "top", "guide",
        "uk", "2025", "2026", "your", "my", "vs", "or",
    }
    words = normalise(query).split()
    return [w for w in words if w not in stop and len(w) > 1]


def match_query_to_posts(query_text, query_cluster, posts, cluster_map):
    """
    Find the best matching post for a query.
    Returns (post_id, post_title, content, score) or (None, None, None, 0).
    Scoring: keyword overlap in title + cluster match bonus + authority bonus.
    """
    keywords = build_keyword_set(query_text)
    query_norm = normalise(query_text)
    best = (None, None, None, 0)

    for post in posts:
        pid = post["id"]
        title_raw = post.get("title", {}).get("raw", "")
        title_norm = normalise(title_raw)
        content_raw = post.get("content", {}).get("raw", "")
        content_norm = normalise(content_raw[:3000])  # first 3K chars for matching

        # Cluster from CSV or fallback
        post_cluster = cluster_map.get(pid, "Uncategorized")

        # ── Scoring ──
        score = 0

        # Keyword overlap in title (strongest signal)
        title_hits = sum(1 for kw in keywords if kw in title_norm)
        score += title_hits * 25

        # Keyword overlap in content intro
        content_hits = sum(1 for kw in keywords if kw in content_norm)
        score += min(content_hits * 5, 30)  # cap at 30

        # Cluster match bonus
        if post_cluster == query_cluster:
            score += 20
        elif query_cluster == "General":
            # General queries can match any cluster
            score += 5

        # Title contains the full query as a substring (strong match)
        if query_norm in title_norm:
            score += 40

        # UK authority references boost
        uk_count = count_uk_authorities(content_raw)
        score += min(uk_count * 3, 15)

        if score > best[3]:
            best = (pid, title_raw, content_raw, score)

    return best


# ---------------------------------------------------------------------------
# AI answer potential assessment
# ---------------------------------------------------------------------------
def assess_ai_answer_potential(query_text, flags, readiness_score):
    """
    Rate a query's likelihood of generating an AI Overview / Featured Snippet.
    Returns 'high', 'medium', or 'low'.
    """
    # Question-format queries are more likely to trigger AI overviews
    is_question = bool(re.search(
        r'^(how|what|why|when|which|is|are|do|does|can|should)',
        query_text.strip(), re.IGNORECASE
    ))
    # "vs" / comparison queries trigger AI overviews
    is_comparison = "vs" in query_text.lower() or "versus" in query_text.lower()
    # "best" queries trigger featured snippets / AI overviews
    is_best = query_text.lower().startswith("best")
    # Guide / checklist queries
    is_guide = bool(re.search(r'(guide|checklist|schedule|tips)', query_text, re.IGNORECASE))

    trigger_score = 0
    if is_question:
        trigger_score += 3
    if is_comparison:
        trigger_score += 2
    if is_best:
        trigger_score += 2
    if is_guide:
        trigger_score += 2

    # Content readiness amplifies potential
    if readiness_score >= 70 and trigger_score >= 3:
        return "high"
    elif readiness_score >= 50 and trigger_score >= 2:
        return "high"
    elif readiness_score >= 40 or trigger_score >= 2:
        return "medium"
    else:
        return "low"


# ---------------------------------------------------------------------------
# 2. Google visibility check (subprocess curl)
# ---------------------------------------------------------------------------
def check_google_visibility(query_text):
    """
    Search Google for the query and check if pethubonline.com appears in top 20.
    Returns True/False or None on error.
    """
    encoded_q = urllib.parse.quote_plus(query_text)
    url = f"https://www.google.com/search?q={encoded_q}&num=20"

    try:
        result = subprocess.run(
            [
                "curl", "-s", "-L",
                "-H", f"User-Agent: {GOOGLE_USER_AGENT}",
                "-H", "Accept: text/html,application/xhtml+xml",
                "-H", "Accept-Language: en-GB,en;q=0.9",
                "--max-time", "15",
                url,
            ],
            capture_output=True, text=True, timeout=20,
        )
        if result.returncode != 0:
            print(f"    [WARN] Google curl failed: {result.stderr[:100]}")
            return None

        html_body = result.stdout
        if not html_body or len(html_body) < 500:
            print(f"    [WARN] Google returned short/empty response ({len(html_body)} bytes)")
            return None

        # Check for CAPTCHA / block
        if "detected unusual traffic" in html_body.lower() or "captcha" in html_body.lower():
            print("    [WARN] Google CAPTCHA detected – stopping searches")
            return None

        # Look for pethubonline.com in the response
        if SITE_DOMAIN in html_body:
            return True
        else:
            return False

    except subprocess.TimeoutExpired:
        print("    [WARN] Google search timed out")
        return None
    except Exception as e:
        print(f"    [ERROR] Google search error: {e}")
        return None


# ---------------------------------------------------------------------------
# Gap analysis
# ---------------------------------------------------------------------------
def determine_gap(query_text, cluster, matched_post_id, flags, readiness_score):
    """
    Determine the gap reason and recommended action for a query.
    Returns (gap_reason, recommended_action) or (None, None) if no gap.
    """
    if matched_post_id is None:
        return (
            "no_matching_content",
            f"Create a new pillar post targeting '{query_text}' in the {cluster} cluster"
        )

    missing_blocks = []
    if not flags["has_at_a_glance"]:
        missing_blocks.append("At a Glance summary")
    if not flags["has_faq"]:
        missing_blocks.append("FAQ section")
    if not flags["has_practical_guide"]:
        missing_blocks.append("Step-by-step practical guide")
    if not flags["has_research_sources"]:
        missing_blocks.append("Research Sources block")
    if not flags["has_comparison"]:
        missing_blocks.append("Comparison table")
    if not flags["has_glossary"]:
        missing_blocks.append("Glossary/terminology section")

    if readiness_score >= 80:
        return (None, None)  # No significant gap

    if readiness_score < 40:
        return (
            "low_readiness",
            f"Major enrichment needed: add {', '.join(missing_blocks[:3])} to boost AI extractability"
        )

    if missing_blocks:
        return (
            "missing_structured_blocks",
            f"Add missing blocks: {', '.join(missing_blocks[:3])}"
        )

    return (None, None)


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------
def main():
    print("=" * 72)
    print("Phase 11 – AI Citation Monitoring Engine for PetHub Online")
    print("=" * 72)

    # ── Step A: Fetch all WordPress posts ──
    print("\n[A] Fetching WordPress posts …")
    posts = fetch_all_posts()
    if not posts:
        print("[FATAL] Could not fetch any posts. Exiting.")
        sys.exit(1)

    # ── Step B: Load cluster map ──
    print("\n[B] Loading cluster assignments …")
    cluster_map = load_cluster_map()

    # ── Step C: Analyse each query ──
    print(f"\n[C] Analysing {len(TEST_QUERIES)} test queries against {len(posts)} posts …")

    query_results = []          # per-query rows
    google_results = {}         # query -> True/False/None
    google_search_count = 0
    captcha_hit = False

    for i, q in enumerate(TEST_QUERIES, 1):
        query_text = q["query"]
        cluster = q["cluster"]
        print(f"\n  [{i:02d}/30] \"{query_text}\" ({cluster})")

        # Match query to best post
        post_id, post_title, post_content, match_score = match_query_to_posts(
            query_text, cluster, posts, cluster_map
        )

        if post_id and post_content:
            flags = {
                "has_at_a_glance": has_at_a_glance(post_content),
                "has_faq": has_faq(post_content),
                "has_glossary": has_glossary(post_content),
                "has_comparison": has_comparison(post_content),
                "has_practical_guide": has_practical_guide(post_content),
                "has_research_sources": has_research_sources(post_content),
            }
            readiness = compute_readiness_score(flags)
            depth = quality_depth_score(post_content)
            uk_refs = count_uk_authorities(post_content)
            plain_text = re.sub(r'<[^>]+>', ' ', post_content)
            word_count = len(plain_text.split())
            print(f"    → Matched: [{post_id}] {post_title[:60]}…")
            print(f"      structure={readiness}/100  depth={depth}/100  words={word_count}  uk_refs={uk_refs}")
        else:
            flags = {k: False for k in [
                "has_at_a_glance", "has_faq", "has_glossary",
                "has_comparison", "has_practical_guide", "has_research_sources",
            ]}
            readiness = 0
            depth = 0
            uk_refs = 0
            word_count = 0
            post_title = ""
            print(f"    → No matching post found")

        # Google visibility check (only for priority queries, within rate limit)
        google_visible = "not_checked"
        if query_text in GOOGLE_SEARCH_QUERIES and google_search_count < MAX_GOOGLE_SEARCHES and not captcha_hit:
            print(f"    Checking Google visibility …")
            time.sleep(GOOGLE_DELAY)
            gv = check_google_visibility(query_text)
            google_search_count += 1
            if gv is True:
                google_visible = "yes"
                print(f"    ✓ pethubonline.com FOUND in Google top 20")
            elif gv is False:
                google_visible = "no"
                print(f"    ✗ pethubonline.com NOT found in Google top 20")
            else:
                google_visible = "error"
                print(f"    ? Google check inconclusive")
                # If we got a captcha, stop further searches
                captcha_hit = True

        # AI answer potential
        ai_potential = assess_ai_answer_potential(query_text, flags, readiness)

        # Gap analysis
        gap_reason, recommended_action = determine_gap(
            query_text, cluster, post_id, flags, readiness
        )

        query_results.append({
            "query": query_text,
            "cluster": cluster,
            "best_matching_post": post_title,
            "post_id": post_id or "",
            "match_score": match_score,
            "readiness_score": readiness,
            "has_at_a_glance": flags["has_at_a_glance"],
            "has_faq": flags["has_faq"],
            "has_glossary": flags["has_glossary"],
            "has_comparison": flags["has_comparison"],
            "has_practical_guide": flags["has_practical_guide"],
            "has_research_sources": flags["has_research_sources"],
            "google_visible": google_visible,
            "ai_answer_potential": ai_potential,
            "gap_reason": gap_reason or "",
            "recommended_action": recommended_action or "",
        })

    # ── Step D: Generate CSV outputs ──
    print("\n" + "=" * 72)
    print("[D] Generating CSV outputs …")

    # D1: ai_citation_queries.csv
    queries_csv = os.path.join(OUTPUT_DIR, "ai_citation_queries.csv")
    with open(queries_csv, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "query", "cluster", "best_matching_post", "post_id",
            "readiness_score", "has_at_a_glance", "has_faq", "has_glossary",
            "has_comparison", "has_practical_guide", "has_research_sources",
            "google_visible", "ai_answer_potential",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in query_results:
            # Convert booleans to yes/no for CSV readability
            out = dict(row)
            for flag in ["has_at_a_glance", "has_faq", "has_glossary",
                         "has_comparison", "has_practical_guide", "has_research_sources"]:
                out[flag] = "yes" if out[flag] else "no"
            writer.writerow(out)
    print(f"  Written: {queries_csv}")

    # D2: ai_citation_readiness.csv (per-cluster aggregate)
    readiness_csv = os.path.join(OUTPUT_DIR, "ai_citation_readiness.csv")
    cluster_agg = defaultdict(lambda: {
        "scores": [], "matched": 0, "google_visible": 0, "ai_ready": 0, "total": 0,
    })
    for row in query_results:
        c = row["cluster"]
        cluster_agg[c]["total"] += 1
        cluster_agg[c]["scores"].append(row["readiness_score"])
        if row["post_id"]:
            cluster_agg[c]["matched"] += 1
        if row["google_visible"] == "yes":
            cluster_agg[c]["google_visible"] += 1
        if row["ai_answer_potential"] == "high" and row["readiness_score"] >= 60:
            cluster_agg[c]["ai_ready"] += 1

    with open(readiness_csv, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "cluster", "total_queries", "avg_readiness",
            "queries_with_matching_content", "google_visible_count",
            "ai_answer_ready_count",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for cluster in sorted(cluster_agg.keys()):
            agg = cluster_agg[cluster]
            writer.writerow({
                "cluster": cluster,
                "total_queries": agg["total"],
                "avg_readiness": round(mean(agg["scores"]), 1) if agg["scores"] else 0,
                "queries_with_matching_content": agg["matched"],
                "google_visible_count": agg["google_visible"],
                "ai_answer_ready_count": agg["ai_ready"],
            })
    print(f"  Written: {readiness_csv}")

    # D3: ai_citation_gaps.csv
    gaps_csv = os.path.join(OUTPUT_DIR, "ai_citation_gaps.csv")
    with open(gaps_csv, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["query", "cluster", "gap_reason", "recommended_action"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in query_results:
            if row["gap_reason"]:
                writer.writerow({
                    "query": row["query"],
                    "cluster": row["cluster"],
                    "gap_reason": row["gap_reason"],
                    "recommended_action": row["recommended_action"],
                })
    print(f"  Written: {gaps_csv}")

    # ── Step E: Print Summary ──
    print("\n" + "=" * 72)
    print("[E] AI Citation Readiness Summary")
    print("=" * 72)

    total_queries = len(query_results)
    matched_queries = sum(1 for r in query_results if r["post_id"])
    avg_readiness = mean([r["readiness_score"] for r in query_results])
    google_checked = sum(1 for r in query_results if r["google_visible"] in ("yes", "no"))
    google_found = sum(1 for r in query_results if r["google_visible"] == "yes")
    ai_ready = sum(1 for r in query_results
                   if r["ai_answer_potential"] == "high" and r["readiness_score"] >= 60)
    gap_count = sum(1 for r in query_results if r["gap_reason"])

    print(f"\n  Total test queries:                  {total_queries}")
    print(f"  Queries with matching content:       {matched_queries}/{total_queries}")
    print(f"  Average readiness score:             {avg_readiness:.1f}/100")
    print(f"  Google visibility (checked/found):   {google_checked} checked, {google_found} found")
    print(f"  AI-answer ready (high + score>=60):  {ai_ready}/{total_queries}")
    print(f"  Queries with gaps:                   {gap_count}")

    print("\n  Per-cluster readiness:")
    print(f"  {'Cluster':<22} {'Queries':>7} {'Avg Score':>10} {'Matched':>8} {'AI Ready':>9}")
    print(f"  {'─' * 22} {'─' * 7} {'─' * 10} {'─' * 8} {'─' * 9}")
    for cluster in sorted(cluster_agg.keys()):
        agg = cluster_agg[cluster]
        avg = mean(agg["scores"]) if agg["scores"] else 0
        print(f"  {cluster:<22} {agg['total']:>7} {avg:>9.1f} {agg['matched']:>8} {agg['ai_ready']:>9}")

    print("\n  Top gaps to address:")
    gaps = [(r["query"], r["cluster"], r["gap_reason"], r["readiness_score"])
            for r in query_results if r["gap_reason"]]
    # Sort by readiness (lowest first = most urgent)
    gaps.sort(key=lambda x: x[3])
    for query, cluster, reason, score in gaps[:10]:
        print(f"    - [{score:>3}/100] \"{query}\" ({cluster}): {reason}")

    print("\n" + "=" * 72)
    print("Phase 11 AI Citation Monitoring complete.")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 72)


if __name__ == "__main__":
    main()
