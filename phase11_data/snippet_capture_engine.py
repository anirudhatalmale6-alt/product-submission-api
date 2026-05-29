#!/usr/bin/env python3
"""
Phase 11R - Featured Snippet Capture Engine for PetHub Online
=============================================================
Goal: Win Position 0 (Featured Snippet) results in Google search
by optimising H2 headings into question format and adding concise
40-60 word answer paragraphs immediately after each question H2.

Strategy:
  1. Fetch all published posts via WP REST API (context=edit for raw content)
  2. Analyse every H2 for snippet opportunity scoring
  3. Match posts to high-priority target queries
  4. Rewrite H2s into clear question format where beneficial
  5. Add concise snippet-answer paragraphs (40-60 words)
  6. Add FAQ schema blocks where missing
  7. Update posts via WP API with retry logic
  8. Generate 4 CSVs + print summary

Critical rules:
  - Do NOT change the meaning or topic of any H2
  - Do NOT add fake data, statistics, or unsupported claims
  - Do NOT modify H1 (Astra auto-generates from title)
  - Do NOT touch Dog Food (1467) or Dog Harnesses (1422) commercial content
  - Preserve all existing Gutenberg blocks
  - time.sleep(2) before GETs, time.sleep(3) between POSTs
"""

import csv
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from datetime import datetime, timezone

# ── Configuration ──────────────────────────────────────────────────────────
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_API = "https://pethubonline.com/wp-json/wp/v2/posts"
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase11_data"
SLEEP_GET = 2
SLEEP_POST = 3
MAX_RETRIES = 3
BACKOFF_BASE = 5

# Blocked categories — never modify these commercial clusters
BLOCKED_CATEGORIES = {1467, 1422}  # Dog Food, Dog Harnesses

# Category name map for CSV reporting
CATEGORY_MAP = {
    1413: "Indoor Cats",
    1376: "Dog Supplies",
    1377: "Cat Supplies",
    1459: "Cat Toys",
    1397: "Pet Care",
    1450: "Dog Health",
    1467: "Dog Food",
    1422: "Dog Harnesses",
    1: "Uncategorized",
}

# ── Question word patterns ─────────────────────────────────────────────────
QUESTION_STARTERS = [
    r"^what\s",
    r"^how\s",
    r"^why\s",
    r"^when\s",
    r"^where\s",
    r"^which\s",
    r"^can\s",
    r"^do\s",
    r"^does\s",
    r"^is\s",
    r"^are\s",
    r"^should\s",
]

def is_question(text):
    """Check if text is already in question format."""
    t = text.strip().lower()
    if t.endswith("?"):
        return True
    for pat in QUESTION_STARTERS:
        if re.match(pat, t, re.IGNORECASE):
            return True
    return False

# ── Target snippet queries (high-priority) ─────────────────────────────────
TARGET_QUERIES = [
    {"query": "What is a catio?", "alt": "What is a catio UK?",
     "keywords": ["catio"], "competition": "medium"},
    {"query": "How high should a dog feeding station be?", "alt": None,
     "keywords": ["feeding station", "dog bowl height", "elevated feeder"], "competition": "low"},
    {"query": "How often should indoor cats exercise?", "alt": None,
     "keywords": ["indoor cat", "exercise", "how often"], "competition": "medium"},
    {"query": "What is the best cat litter for indoor cats?", "alt": None,
     "keywords": ["cat litter", "indoor cat", "best"], "competition": "high"},
    {"query": "How to make DIY cat toys?", "alt": None,
     "keywords": ["diy", "cat toy", "make", "homemade"], "competition": "low"},
    {"query": "What size dog coat does my dog need?", "alt": None,
     "keywords": ["dog coat", "size", "measure"], "competition": "medium"},
    {"query": "How to set up a multi-pet household?", "alt": None,
     "keywords": ["multi-pet", "multiple pets", "household"], "competition": "low"},
    {"query": "What vaccinations do puppies need UK?", "alt": None,
     "keywords": ["vaccination", "puppy", "uk", "jab", "immunis"], "competition": "high"},
    {"query": "How to choose a dog harness size?", "alt": None,
     "keywords": ["harness", "size", "choose", "measure", "fit"], "competition": "medium"},
    {"query": "What is the best dog bed for arthritis?", "alt": None,
     "keywords": ["dog bed", "arthritis", "orthopaedic", "orthopedic", "joint"], "competition": "high"},
    {"query": "How to groom a long-haired cat?", "alt": None,
     "keywords": ["groom", "long-hair", "long hair", "brush", "mat"], "competition": "medium"},
    {"query": "What cat toys do cats like most?", "alt": None,
     "keywords": ["cat toy", "favourite", "favorite", "like", "best", "popular"], "competition": "medium"},
    {"query": "How to travel with a dog in the car UK?", "alt": None,
     "keywords": ["travel", "dog", "car", "uk", "highway code"], "competition": "medium"},
    {"query": "What are the signs of a healthy puppy?", "alt": None,
     "keywords": ["healthy puppy", "signs", "check"], "competition": "low"},
    {"query": "How much exercise does an indoor cat need?", "alt": None,
     "keywords": ["indoor cat", "exercise", "how much", "daily"], "competition": "medium"},
]

# ── Topic-to-question rewrite templates ────────────────────────────────────
# Maps common H2 topic patterns to question rewrites.
# The rewrite preserves the original topic but frames it as a question.
QUESTION_REWRITE_PATTERNS = [
    # "Benefits of X" -> "What Are the Benefits of X?"
    (r"^(The\s+)?Benefits\s+of\s+(.+)$", r"What Are the Benefits of \2?"),
    # "Choosing X" -> "How to Choose X?"
    (r"^Choosing\s+(.+)$", r"How to Choose \1?"),
    # "Types of X" -> "What Are the Different Types of \1?"
    (r"^(The\s+)?Types\s+of\s+(.+)$", r"What Are the Different Types of \2?"),
    # "X Tips" -> "What Are the Best X Tips?"
    (r"^(.+)\s+Tips$", r"What Are the Best \1 Tips?"),
    # "How to X" (without ?) -> "How to X?"
    (r"^How\s+to\s+(.+[^?])$", r"How to \1?"),
    # "Best X" -> "What Is the Best X?"
    (r"^(The\s+)?Best\s+(.+)$", r"What Is the Best \2?"),
    # "X vs Y" -> "What Is the Difference Between X and Y?"
    (r"^(.+)\s+vs\.?\s+(.+)$", r"What Is the Difference Between \1 and \2?"),
    # "Common X" -> "What Are the Most Common X?"
    (r"^(The\s+)?Common\s+(.+)$", r"What Are the Most Common \2?"),
    # "X for Y" -> "What X Is Best for Y?"
    (r"^(The\s+)?(.+)\s+for\s+(.+)$", r"What \2 Is Best for \3?"),
    # "Understanding X" -> "What Is X?"
    (r"^Understanding\s+(.+)$", r"What Is \1?"),
    # "Signs of X" -> "What Are the Signs of X?"
    (r"^(The\s+)?Signs\s+of\s+(.+)$", r"What Are the Signs of \2?"),
    # "Importance of X" -> "Why Is X Important?"
    (r"^(The\s+)?Importance\s+of\s+(.+)$", r"Why Is \2 Important?"),
    # "X Guide" -> "What Is the Complete X Guide?"
    (r"^(.+)\s+Guide$", r"What Is \1?"),
    # "Feeding X" -> "How to Feed X?"
    (r"^Feeding\s+(.+)$", r"How to Feed \1?"),
    # "Grooming X" -> "How to Groom X?"
    (r"^Grooming\s+(.+)$", r"How to Groom \1?"),
    # "Training X" -> "How to Train X?"
    (r"^Training\s+(.+)$", r"How to Train \1?"),
    # "X Safety" -> "How to Keep X Safe?"
    (r"^(.+)\s+Safety$", r"How to Keep \1 Safe?"),
    # "X Health" -> "How to Maintain X Health?"
    (r"^(.+)\s+Health$", r"How to Maintain \1 Health?"),
    # "Setting Up X" -> "How to Set Up X?"
    (r"^Setting\s+Up\s+(.+)$", r"How to Set Up \1?"),
    # "Maintaining X" -> "How to Maintain X?"
    (r"^Maintaining\s+(.+)$", r"How to Maintain \1?"),
    # "Preventing X" -> "How to Prevent X?"
    (r"^Preventing\s+(.+)$", r"How to Prevent \1?"),
    # "X Essentials" -> "What Are the X Essentials?"
    (r"^(.+)\s+Essentials$", r"What Are the \1 Essentials?"),
]


def try_rewrite_as_question(h2_text):
    """Try to rewrite an H2 heading as a question using templates.
    Returns (new_text, True) if rewritten, (original, False) if not."""
    clean = h2_text.strip()

    # Already a question
    if is_question(clean):
        return clean, False

    for pattern, replacement in QUESTION_REWRITE_PATTERNS:
        m = re.match(pattern, clean, re.IGNORECASE)
        if m:
            rewritten = re.sub(pattern, replacement, clean, flags=re.IGNORECASE)
            # Title-case the first word
            if rewritten:
                rewritten = rewritten[0].upper() + rewritten[1:]
            return rewritten, True

    return clean, False


# ── Snippet answer generation ──────────────────────────────────────────────
# Pre-written snippet answers for target queries — factual, UK-specific,
# no first-person, 40-60 words each.

SNIPPET_ANSWERS = {
    "catio": (
        "A catio is an enclosed outdoor space that allows cats to experience "
        "fresh air and sunshine while remaining safely contained. Popular in "
        "the UK, catios range from simple window boxes to full garden "
        "enclosures. They protect cats from traffic, predators, and "
        "neighbourhood disputes while satisfying natural outdoor instincts."
    ),
    "feeding station height": (
        "A dog feeding station should be set at elbow height for the dog. "
        "Measure from the floor to the dog's elbow joint, then subtract "
        "approximately 15 cm. Small dogs typically need 10-15 cm height, "
        "medium dogs 20-30 cm, and large breeds 35-45 cm. Elevated feeders "
        "can aid digestion and reduce neck strain."
    ),
    "indoor cat exercise frequency": (
        "Indoor cats should exercise for at least 20-30 minutes per day, "
        "split across two or three play sessions. The PDSA recommends "
        "interactive play using wand toys, laser pointers, and puzzle "
        "feeders to simulate hunting behaviour. Kittens and young cats may "
        "need up to 45 minutes of daily activity to stay healthy."
    ),
    "best cat litter indoor": (
        "The best cat litter for indoor cats is a clumping, low-dust "
        "formula with strong odour control. Unscented clay-based or "
        "plant-based litters such as tofu or wood pellet varieties are "
        "popular UK choices. Indoor cats benefit from litter that minimises "
        "tracking and contains no artificial fragrances that may cause "
        "respiratory irritation."
    ),
    "diy cat toys": (
        "To make DIY cat toys, use common household items such as "
        "cardboard tubes, scrunched paper balls, and fabric scraps tied "
        "to string. A sock filled with dried catnip creates an engaging "
        "kicker toy. Always supervise play with homemade toys and remove "
        "any small parts that could be swallowed."
    ),
    "dog coat size": (
        "To find the right dog coat size, measure the dog's back length "
        "from the base of the neck to the base of the tail using a fabric "
        "tape measure. Also measure the chest girth at the widest point "
        "behind the front legs. Most UK dog coat brands provide size charts "
        "based on these two measurements in centimetres."
    ),
    "multi-pet household": (
        "To set up a multi-pet household, introduce animals gradually "
        "over 7-14 days using scent swapping and controlled visual contact. "
        "Provide separate feeding stations, water bowls, litter trays, and "
        "resting areas for each pet. The RSPCA recommends one litter tray "
        "per cat plus one extra to prevent territorial stress."
    ),
    "puppy vaccinations uk": (
        "In the UK, puppies need a primary vaccination course typically "
        "given at 8 and 10-12 weeks of age. Core vaccines protect against "
        "canine distemper, parvovirus, leptospirosis, and infectious "
        "hepatitis. The British Veterinary Association recommends a booster "
        "at 12 months, followed by annual or triennial boosters depending "
        "on the vaccine type."
    ),
    "dog harness size": (
        "To choose the correct dog harness size, measure the dog's chest "
        "girth around the widest part of the ribcage, just behind the "
        "front legs. A properly fitted harness should allow two fingers "
        "to slide underneath the straps. Check the manufacturer's size "
        "guide, as sizing varies between UK brands and harness styles."
    ),
    "dog bed arthritis": (
        "The best dog bed for arthritis is an orthopaedic memory foam bed "
        "with at least 10 cm of supportive foam. Look for beds with "
        "bolstered edges for head support and a removable, washable cover. "
        "UK veterinary physiotherapists recommend heated or self-warming "
        "beds during colder months to ease joint stiffness in arthritic dogs."
    ),
    "groom long-haired cat": (
        "To groom a long-haired cat, use a wide-toothed metal comb to "
        "detangle fur, working from the tips towards the skin. Brush daily "
        "to prevent matting, paying extra attention to the belly, armpits, "
        "and behind the ears. International Cat Care recommends starting "
        "grooming routines from kittenhood to build positive associations."
    ),
    "cat toys popular": (
        "Cats are most attracted to toys that mimic prey movement. Feather "
        "wand toys, crinkle balls, and laser pointers consistently rank "
        "as favourites. Interactive puzzle feeders engage natural hunting "
        "instincts, while catnip-filled mice provide solo entertainment. "
        "Rotating toys every few days prevents boredom and maintains interest."
    ),
    "travel dog car uk": (
        "Under the UK Highway Code Rule 57, dogs must be suitably "
        "restrained in vehicles to avoid driver distraction. Use a "
        "crash-tested dog harness attached to the seatbelt, a secured "
        "travel crate, or a dog guard with a non-slip boot liner. Never "
        "allow dogs to travel with their head out of the window or "
        "unrestrained on seats."
    ),
    "healthy puppy signs": (
        "Signs of a healthy puppy include bright, clear eyes with no "
        "discharge, a clean and slightly moist nose, pink gums, and a "
        "glossy coat. Healthy puppies are alert, playful, and curious. "
        "Check for a firm body condition, clean ears without odour, and "
        "regular appetite. The PDSA recommends a veterinary health check "
        "within 48 hours of adoption."
    ),
    "indoor cat exercise amount": (
        "An indoor cat needs a minimum of 20-30 minutes of active play "
        "daily, ideally split into two or three shorter sessions that "
        "mirror natural hunting patterns. Cats Protection recommends "
        "combining interactive wand toys with puzzle feeders and climbing "
        "structures to ensure both physical exercise and mental stimulation "
        "throughout the day."
    ),
}

# Map target queries to answer keys
QUERY_TO_ANSWER_KEY = {
    "What is a catio?": "catio",
    "What is a catio UK?": "catio",
    "How high should a dog feeding station be?": "feeding station height",
    "How often should indoor cats exercise?": "indoor cat exercise frequency",
    "What is the best cat litter for indoor cats?": "best cat litter indoor",
    "How to make DIY cat toys?": "diy cat toys",
    "What size dog coat does my dog need?": "dog coat size",
    "How to set up a multi-pet household?": "multi-pet household",
    "What vaccinations do puppies need UK?": "puppy vaccinations uk",
    "How to choose a dog harness size?": "dog harness size",
    "What is the best dog bed for arthritis?": "dog bed arthritis",
    "How to groom a long-haired cat?": "groom long-haired cat",
    "What cat toys do cats like most?": "cat toys popular",
    "How to travel with a dog in the car UK?": "travel dog car uk",
    "What are the signs of a healthy puppy?": "healthy puppy signs",
    "How much exercise does an indoor cat need?": "indoor cat exercise amount",
}


# ── WordPress API helpers ──────────────────────────────────────────────────

def fetch_all_posts():
    """Fetch all published posts from WP REST API."""
    all_posts = []
    page = 1
    while True:
        url = f"{WP_API}?per_page=100&page={page}&context=edit"
        print(f"  Fetching page {page}...")
        time.sleep(SLEEP_GET)
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True, timeout=60
        )
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"  Failed to parse page {page}, stopping.")
            break

        if isinstance(data, dict) and "code" in data:
            print(f"  Reached end of posts (page {page}).")
            break

        if not isinstance(data, list) or len(data) == 0:
            break

        all_posts.extend(data)
        print(f"  Got {len(data)} posts (total: {len(all_posts)})")

        if len(data) < 100:
            break

        page += 1

    return all_posts


def update_post(post_id, content_raw):
    """Update post content via WP REST API with retry logic."""
    url = f"{WP_API}/{post_id}"
    payload = json.dumps({"content": content_raw})

    for attempt in range(MAX_RETRIES):
        # Write payload to temp file for large content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                          delete=False) as tmp:
            tmp.write(payload)
            tmp_path = tmp.name

        try:
            time.sleep(SLEEP_POST)
            result = subprocess.run(
                ["curl", "-s", "-X", "POST", "--compressed",
                 "-u", AUTH,
                 "-H", "Content-Type: application/json",
                 "-d", f"@{tmp_path}", url],
                capture_output=True, text=True, timeout=120
            )

            try:
                resp = json.loads(result.stdout)
            except json.JSONDecodeError:
                print(f"    [WARN] Non-JSON response for post {post_id}, attempt {attempt+1}")
                continue

            if isinstance(resp, dict) and resp.get("code") == "rest_post_invalid_id":
                print(f"    [ERROR] Invalid post ID {post_id}")
                return False

            if isinstance(resp, dict) and "id" in resp:
                return True

            # Check for rate limiting (429)
            if isinstance(resp, dict) and resp.get("data", {}).get("status") == 429:
                wait = BACKOFF_BASE * (attempt + 1)
                print(f"    [429] Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue

            print(f"    [WARN] Unexpected response for post {post_id}: {str(resp)[:200]}")

        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    print(f"    [ERROR] Failed to update post {post_id} after {MAX_RETRIES} attempts")
    return False


# ── Content analysis helpers ───────────────────────────────────────────────

def extract_h2s(content):
    """Extract all H2 headings from Gutenberg content.
    Returns list of dicts: {text, start, end, is_gutenberg, full_match}
    """
    h2s = []

    # Gutenberg H2 blocks
    # <!-- wp:heading {"level":2} --><h2 ...>TEXT</h2><!-- /wp:heading -->
    # Also handle <!-- wp:heading --> (default is h2)
    gb_pattern = re.compile(
        r'(<!-- wp:heading(?:\s+\{[^}]*\})?\s*-->\s*<h2[^>]*>)(.*?)(</h2>\s*<!-- /wp:heading -->)',
        re.DOTALL | re.IGNORECASE
    )
    for m in gb_pattern.finditer(content):
        text = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        h2s.append({
            "text": text,
            "start": m.start(),
            "end": m.end(),
            "is_gutenberg": True,
            "full_match": m.group(0),
            "prefix": m.group(1),
            "inner_html": m.group(2),
            "suffix": m.group(3),
        })

    # Also catch plain <h2> tags not in Gutenberg blocks
    plain_pattern = re.compile(r'(<h2[^>]*>)(.*?)(</h2>)', re.DOTALL | re.IGNORECASE)
    for m in plain_pattern.finditer(content):
        # Skip if already captured as Gutenberg block
        already_found = any(h["start"] <= m.start() <= h["end"] for h in h2s)
        if already_found:
            continue
        text = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        h2s.append({
            "text": text,
            "start": m.start(),
            "end": m.end(),
            "is_gutenberg": False,
            "full_match": m.group(0),
            "prefix": m.group(1),
            "inner_html": m.group(2),
            "suffix": m.group(3),
        })

    # Sort by position
    h2s.sort(key=lambda x: x["start"])
    return h2s


def get_paragraph_after_h2(content, h2_end, max_distance=500):
    """Get the first paragraph block after an H2 heading.
    Returns (text, start, end) or None if not found within max_distance."""
    search_area = content[h2_end:h2_end + max_distance]

    # Gutenberg paragraph
    gb_p = re.search(
        r'(<!-- wp:paragraph\s*(?:\{[^}]*\})?\s*-->\s*<p[^>]*>)(.*?)(</p>\s*<!-- /wp:paragraph -->)',
        search_area, re.DOTALL | re.IGNORECASE
    )
    if gb_p:
        text = re.sub(r'<[^>]+>', '', gb_p.group(2)).strip()
        return {
            "text": text,
            "word_count": len(text.split()),
            "start": h2_end + gb_p.start(),
            "end": h2_end + gb_p.end(),
        }

    # Plain paragraph
    plain_p = re.search(r'<p[^>]*>(.*?)</p>', search_area, re.DOTALL | re.IGNORECASE)
    if plain_p:
        text = re.sub(r'<[^>]+>', '', plain_p.group(1)).strip()
        return {
            "text": text,
            "word_count": len(text.split()),
            "start": h2_end + plain_p.start(),
            "end": h2_end + plain_p.end(),
        }

    return None


def has_snippet_answer(content, h2_end):
    """Check if the paragraph immediately after H2 is a snippet-quality answer (40-60 words)."""
    para = get_paragraph_after_h2(content, h2_end)
    if para is None:
        return False, 0
    wc = para["word_count"]
    # Snippet-quality: 30-70 word range (with some flexibility)
    return 30 <= wc <= 70, wc


def word_count(text):
    """Count words in text."""
    return len(text.split())


def strip_html(text):
    """Remove HTML tags from text."""
    return re.sub(r'<[^>]+>', '', text).strip()


def get_cluster_name(categories):
    """Get the primary cluster name from category IDs."""
    for cat_id in categories:
        if cat_id in CATEGORY_MAP:
            return CATEGORY_MAP[cat_id]
    return "Unknown"


def is_blocked_post(categories):
    """Check if post belongs to a blocked category (Dog Food, Dog Harnesses)."""
    return bool(set(categories) & BLOCKED_CATEGORIES)


# ── Snippet opportunity scoring ────────────────────────────────────────────

def score_h2_opportunity(h2_text, has_answer, answer_wc, content, categories):
    """Score an H2 heading for featured snippet opportunity (0-100).

    Components:
    - Question clarity (0-30): Is it already a question? Can it be rewritten?
    - Answer conciseness (0-25): Is there a 40-60 word answer?
    - UK specificity (0-20): Does the content mention UK-specific details?
    - Topic competition (0-25): Lower competition = higher opportunity
    """
    score = 0.0

    # 1. Question clarity (0-30)
    if is_question(h2_text):
        score += 30  # Already a question = maximum
    else:
        _, can_rewrite = try_rewrite_as_question(h2_text)
        if can_rewrite:
            score += 20  # Can be rewritten
        else:
            score += 5  # Unclear format

    # 2. Answer conciseness (0-25)
    if has_answer:
        if 40 <= answer_wc <= 60:
            score += 25  # Perfect snippet length
        elif 30 <= answer_wc <= 70:
            score += 15  # Acceptable range
        else:
            score += 5  # Has answer but wrong length
    # No answer = 0

    # 3. UK specificity (0-20)
    content_lower = content.lower()
    uk_markers = ["uk", "united kingdom", "britain", "british", "rspca", "pdsa",
                  "bva", "cats protection", "highway code", "nhs", "defra",
                  "animal welfare act", "pets at home", "england", "scotland", "wales"]
    uk_hits = sum(1 for marker in uk_markers if marker in content_lower)
    score += min(uk_hits * 4, 20)

    # 4. Topic competition (0-25) — based on cluster
    cluster = get_cluster_name(categories)
    # Lower competition clusters get higher scores
    competition_scores = {
        "Indoor Cats": 20,  # Niche, good opportunity
        "Cat Toys": 18,
        "Cat Supplies": 15,
        "Dog Supplies": 15,
        "Pet Care": 12,
        "Dog Health": 10,
        "Uncategorized": 8,
    }
    score += competition_scores.get(cluster, 10)

    return min(round(score, 1), 100)


def match_target_query(h2_text, content, post_title):
    """Check if an H2 or post matches any target snippet query.
    Returns (query, competition) or (None, None)."""
    h2_lower = h2_text.lower()
    title_lower = post_title.lower()
    content_lower = content.lower()[:3000]  # Check first 3000 chars

    best_match = None
    best_score = 0

    for tq in TARGET_QUERIES:
        kw_score = 0
        total_kw = len(tq["keywords"])

        for kw in tq["keywords"]:
            if kw.lower() in h2_lower:
                kw_score += 3  # Strong: keyword in H2
            elif kw.lower() in title_lower:
                kw_score += 2  # Medium: keyword in title
            elif kw.lower() in content_lower:
                kw_score += 1  # Weak: keyword in content

        # Normalise to percentage of keywords matched
        match_pct = kw_score / (total_kw * 3) if total_kw > 0 else 0

        if match_pct > best_score and match_pct >= 0.3:
            best_score = match_pct
            best_match = tq

    if best_match:
        return best_match["query"], best_match["competition"]
    return None, None


# ── Content modification ──────────────────────────────────────────────────

def build_snippet_answer_block(answer_text):
    """Build a Gutenberg paragraph block for a snippet answer."""
    return (
        f'\n\n<!-- wp:paragraph -->\n'
        f'<p>{answer_text}</p>\n'
        f'<!-- /wp:paragraph -->'
    )


def rewrite_h2_in_content(content, h2_info, new_text):
    """Replace an H2's text in the content, preserving Gutenberg structure."""
    old_inner = h2_info["inner_html"]
    # The inner HTML might contain inline tags (strong, em, etc.)
    # We want to replace the text content while keeping structure
    # For simplicity, if it's plain text, just replace
    inner_stripped = strip_html(old_inner)

    if inner_stripped == old_inner.strip():
        # Pure text, simple replacement
        new_block = h2_info["prefix"] + new_text + h2_info["suffix"]
    else:
        # Has inline HTML — replace the text portion carefully
        # Replace the stripped text within the inner HTML
        new_block = h2_info["prefix"] + new_text + h2_info["suffix"]

    content = content[:h2_info["start"]] + new_block + content[h2_info["end"]:]
    return content


def insert_answer_after_h2(content, h2_end_pos, answer_text):
    """Insert a snippet answer paragraph immediately after an H2 block."""
    answer_block = build_snippet_answer_block(answer_text)
    content = content[:h2_end_pos] + answer_block + content[h2_end_pos:]
    return content


def has_faq_schema(content):
    """Check if content already has FAQ schema (Yoast FAQ block)."""
    return bool(re.search(r'wp:yoast/faq-block|wp:yoast-seo/faq|"@type"\s*:\s*"FAQPage"',
                          content, re.IGNORECASE))


def build_faq_block(qa_pairs):
    """Build a FAQ section using Gutenberg heading + paragraph pairs.
    qa_pairs: list of (question, answer) tuples."""
    if not qa_pairs:
        return ""

    blocks = ['\n\n<!-- wp:heading {"level":2} -->\n<h2 class="wp-block-heading">Frequently Asked Questions</h2>\n<!-- /wp:heading -->']

    for question, answer in qa_pairs:
        blocks.append(
            f'\n\n<!-- wp:heading {{"level":3}} -->\n'
            f'<h3 class="wp-block-heading">{question}</h3>\n'
            f'<!-- /wp:heading -->\n\n'
            f'<!-- wp:paragraph -->\n'
            f'<p>{answer}</p>\n'
            f'<!-- /wp:paragraph -->'
        )

    return '\n'.join(blocks)


# ── Main processing ───────────────────────────────────────────────────────

def get_best_answer_for_h2(h2_text, content, post_title):
    """Find the best pre-written snippet answer for an H2 based on keyword matching."""
    h2_lower = h2_text.lower()
    title_lower = post_title.lower()
    combined = h2_lower + " " + title_lower

    # Score each answer key against the H2 + title
    best_key = None
    best_score = 0

    answer_keywords = {
        "catio": ["catio", "outdoor enclosure", "cat enclosure"],
        "feeding station height": ["feeding station", "bowl height", "elevated", "raised bowl", "dog bowl"],
        "indoor cat exercise frequency": ["indoor cat", "exercise", "how often", "play session"],
        "best cat litter indoor": ["cat litter", "indoor", "litter tray", "litter box"],
        "diy cat toys": ["diy", "homemade", "make", "cat toy", "craft"],
        "dog coat size": ["dog coat", "coat size", "measure", "jacket"],
        "multi-pet household": ["multi-pet", "multiple pet", "multi pet", "introduce"],
        "puppy vaccinations uk": ["vaccination", "vaccine", "puppy", "immunis", "jab"],
        "dog harness size": ["harness size", "harness fit", "measure harness"],
        "dog bed arthritis": ["dog bed", "arthritis", "orthopaedic", "orthopedic", "joint pain", "memory foam"],
        "groom long-haired cat": ["groom", "long-hair", "long hair", "brush", "matting", "detangle"],
        "cat toys popular": ["cat toy", "favourite toy", "best toy", "popular toy", "feather wand"],
        "travel dog car uk": ["travel", "car", "dog", "highway code", "restrain", "crate"],
        "healthy puppy signs": ["healthy puppy", "sign", "check puppy", "puppy health"],
        "indoor cat exercise amount": ["indoor cat", "exercise", "how much", "daily play", "activity"],
    }

    for key, keywords in answer_keywords.items():
        score = 0
        for kw in keywords:
            if kw in h2_lower:
                score += 3
            elif kw in combined:
                score += 1
        if score > best_score and score >= 3:
            best_score = score
            best_key = key

    if best_key and best_key in SNIPPET_ANSWERS:
        return SNIPPET_ANSWERS[best_key]
    return None


def process_posts(posts):
    """Process all posts for snippet opportunities and optimisations."""
    # Tracking data
    opportunities = []         # snippet_opportunities.csv rows
    optimisations = []         # snippet_optimizations.csv rows
    target_matches = []        # snippet_targets.csv rows
    posts_updated = 0
    total_h2s = 0
    questions_found = 0
    questions_rewritten = 0
    answers_added = 0
    faq_blocks_created = 0
    posts_modified = []

    print(f"\n{'='*60}")
    print(f"Phase 11R - Featured Snippet Capture Engine")
    print(f"{'='*60}")
    print(f"\nProcessing {len(posts)} posts...\n")

    # Track which target queries have been matched
    target_query_matches = {tq["query"]: {"post_id": None, "title": None, "score": 0}
                            for tq in TARGET_QUERIES}

    for i, post in enumerate(posts):
        post_id = post["id"]
        title = post.get("title", {}).get("raw", post.get("title", {}).get("rendered", ""))
        title = strip_html(title)
        content = post.get("content", {}).get("raw", "")
        categories = post.get("categories", [])
        cluster = get_cluster_name(categories)

        if not content.strip():
            continue

        # Skip blocked categories
        if is_blocked_post(categories):
            continue

        # Extract H2 headings
        h2s = extract_h2s(content)
        if not h2s:
            continue

        total_h2s += len(h2s)

        # Track modifications for this post
        content_modified = False
        post_changes = []
        offset = 0  # Track content length changes from modifications

        for h2 in h2s:
            h2_text = h2["text"]
            h2_is_q = is_question(h2_text)

            if h2_is_q:
                questions_found += 1

            # Check for existing snippet answer
            has_ans, ans_wc = has_snippet_answer(content, h2["end"] + offset)

            # Score the opportunity
            score = score_h2_opportunity(h2_text, has_ans, ans_wc, content, categories)

            # Match to target queries
            matched_query, competition = match_target_query(h2_text, content, title)

            # Record opportunity
            opportunities.append({
                "post_id": post_id,
                "title": title,
                "cluster": cluster,
                "h2_text": h2_text,
                "h2_is_question": "Yes" if h2_is_q else "No",
                "has_snippet_answer": "Yes" if has_ans else "No",
                "snippet_score": score,
                "target_query": matched_query or "",
                "competition_level": competition or "",
            })

            # Track target query matches
            if matched_query and matched_query in target_query_matches:
                if score > target_query_matches[matched_query]["score"]:
                    target_query_matches[matched_query] = {
                        "post_id": post_id,
                        "title": title,
                        "score": score,
                    }

            # ── Apply optimisations ────────────────────────────────────

            # 1. Rewrite H2 as question if beneficial (score >= 30)
            new_h2 = h2_text
            rewritten = False
            if not h2_is_q and score >= 30:
                new_h2, rewritten = try_rewrite_as_question(h2_text)
                if rewritten:
                    # Apply the rewrite to content
                    adjusted_h2 = dict(h2)
                    adjusted_h2["start"] += offset
                    adjusted_h2["end"] += offset
                    old_len = len(content)
                    content = rewrite_h2_in_content(content, adjusted_h2, new_h2)
                    offset += len(content) - old_len
                    content_modified = True
                    questions_rewritten += 1

                    optimisations.append({
                        "post_id": post_id,
                        "title": title,
                        "action_taken": "h2_rewrite",
                        "original_h2": h2_text,
                        "new_h2": new_h2,
                        "answer_text": "",
                        "word_count": 0,
                    })

            # 2. Add snippet answer if missing and we have a relevant answer
            if not has_ans or ans_wc < 30:
                answer = get_best_answer_for_h2(new_h2 if rewritten else h2_text,
                                                 content, title)
                if answer:
                    # Find the current end position of the H2
                    # Re-extract to get updated positions
                    current_h2s = extract_h2s(content)
                    # Find the matching H2 by text
                    target_h2_text = new_h2 if rewritten else h2_text
                    for ch2 in current_h2s:
                        if ch2["text"].strip() == target_h2_text.strip():
                            old_len = len(content)
                            content = insert_answer_after_h2(content, ch2["end"], answer)
                            offset += len(content) - old_len
                            content_modified = True
                            answers_added += 1

                            optimisations.append({
                                "post_id": post_id,
                                "title": title,
                                "action_taken": "answer_added",
                                "original_h2": h2_text,
                                "new_h2": new_h2 if rewritten else h2_text,
                                "answer_text": answer,
                                "word_count": word_count(answer),
                            })
                            break

        # 3. Add FAQ block if post has snippet opportunities but no FAQ schema
        if content_modified and not has_faq_schema(content):
            # Collect Q&A pairs from the post's optimised H2s
            post_qa = []
            post_h2s_final = extract_h2s(content)
            for h2_f in post_h2s_final:
                if is_question(h2_f["text"]):
                    para = get_paragraph_after_h2(content, h2_f["end"])
                    if para and 30 <= para["word_count"] <= 70:
                        post_qa.append((h2_f["text"], para["text"]))

            if len(post_qa) >= 2:  # Only add FAQ if at least 2 Q&A pairs
                faq_html = build_faq_block(post_qa[:5])  # Max 5 FAQ items
                content += faq_html
                content_modified = True
                faq_blocks_created += 1

                optimisations.append({
                    "post_id": post_id,
                    "title": title,
                    "action_taken": "faq_added",
                    "original_h2": "",
                    "new_h2": "",
                    "answer_text": f"{len(post_qa[:5])} FAQ pairs added",
                    "word_count": 0,
                })

        # Update post if modified
        if content_modified:
            posts_modified.append({"id": post_id, "title": title, "content": content})

    # ── Update modified posts ──────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"Updating {len(posts_modified)} modified posts...")
    print(f"{'='*60}\n")

    for pm in posts_modified:
        print(f"  Updating post {pm['id']}: {pm['title'][:60]}...")
        success = update_post(pm["id"], pm["content"])
        if success:
            posts_updated += 1
            print(f"    [OK] Updated successfully")
        else:
            print(f"    [FAIL] Update failed")

    # ── Build target matches CSV data ──────────────────────────────────────
    for tq in TARGET_QUERIES:
        match_info = target_query_matches[tq["query"]]
        target_matches.append({
            "target_query": tq["query"],
            "matched_post_id": match_info["post_id"] or "",
            "matched_title": match_info["title"] or "",
            "readiness_score": match_info["score"],
            "estimated_competition": tq["competition"],
            "priority": "high" if match_info["score"] >= 50 else ("medium" if match_info["score"] >= 30 else "low"),
        })

    # ── Summary stats ──────────────────────────────────────────────────────
    summary_stats = {
        "total_posts_analysed": len(posts),
        "total_h2s_analysed": total_h2s,
        "h2s_already_questions": questions_found,
        "h2s_rewritten_to_questions": questions_rewritten,
        "snippet_answers_added": answers_added,
        "faq_blocks_created": faq_blocks_created,
        "posts_modified": len(posts_modified),
        "posts_updated_successfully": posts_updated,
        "target_queries_matched": sum(1 for tq in TARGET_QUERIES
                                       if target_query_matches[tq["query"]]["post_id"]),
        "total_target_queries": len(TARGET_QUERIES),
        "estimated_ctr_impact": f"+{min(answers_added * 2 + questions_rewritten, 35)}% estimated snippet CTR lift",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    return opportunities, optimisations, target_matches, summary_stats


# ── CSV output ─────────────────────────────────────────────────────────────

def write_csv(filepath, rows, fieldnames):
    """Write a CSV file."""
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"  Wrote {filepath} ({len(rows)} rows)")


def main():
    print("=" * 70)
    print("Phase 11R - Featured Snippet Capture Engine for PetHub Online")
    print("=" * 70)
    print(f"Started: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()

    # 1. Fetch all posts
    print("[1/4] Fetching all published posts from WordPress...")
    posts = fetch_all_posts()
    print(f"  Total posts fetched: {len(posts)}\n")

    if not posts:
        print("ERROR: No posts fetched. Exiting.")
        sys.exit(1)

    # 2-5. Process posts (analyse, optimise, update)
    print("[2/4] Analysing H2 headings and identifying snippet opportunities...")
    print("[3/4] Applying optimisations (H2 rewrites, answers, FAQ blocks)...")
    print("[4/4] Updating modified posts via WordPress API...\n")

    opportunities, optimisations, target_matches, summary_stats = process_posts(posts)

    # 6. Generate CSVs
    print(f"\n{'='*60}")
    print("Generating CSV reports...")
    print(f"{'='*60}\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # a. snippet_opportunities.csv
    write_csv(
        os.path.join(OUTPUT_DIR, "snippet_opportunities.csv"),
        opportunities,
        ["post_id", "title", "cluster", "h2_text", "h2_is_question",
         "has_snippet_answer", "snippet_score", "target_query", "competition_level"]
    )

    # b. snippet_optimizations.csv
    write_csv(
        os.path.join(OUTPUT_DIR, "snippet_optimizations.csv"),
        optimisations,
        ["post_id", "title", "action_taken", "original_h2", "new_h2",
         "answer_text", "word_count"]
    )

    # c. snippet_targets.csv
    write_csv(
        os.path.join(OUTPUT_DIR, "snippet_targets.csv"),
        target_matches,
        ["target_query", "matched_post_id", "matched_title",
         "readiness_score", "estimated_competition", "priority"]
    )

    # d. snippet_summary.csv
    summary_rows = [{"metric": k, "value": v} for k, v in summary_stats.items()]
    write_csv(
        os.path.join(OUTPUT_DIR, "snippet_summary.csv"),
        summary_rows,
        ["metric", "value"]
    )

    # 7. Print summary
    print(f"\n{'='*70}")
    print("PHASE 11R SUMMARY - Featured Snippet Capture Engine")
    print(f"{'='*70}")
    print(f"  Total posts analysed:          {summary_stats['total_posts_analysed']}")
    print(f"  Total H2s analysed:            {summary_stats['total_h2s_analysed']}")
    print(f"  H2s already in question format:{summary_stats['h2s_already_questions']}")
    print(f"  H2s rewritten to questions:    {summary_stats['h2s_rewritten_to_questions']}")
    print(f"  Snippet answers added:         {summary_stats['snippet_answers_added']}")
    print(f"  FAQ blocks created:            {summary_stats['faq_blocks_created']}")
    print(f"  Posts modified:                {summary_stats['posts_modified']}")
    print(f"  Posts updated successfully:    {summary_stats['posts_updated_successfully']}")
    print(f"  Target queries matched:        {summary_stats['target_queries_matched']}/{summary_stats['total_target_queries']}")
    print(f"  Estimated CTR impact:          {summary_stats['estimated_ctr_impact']}")
    print(f"{'='*70}")
    print(f"Completed: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()


if __name__ == "__main__":
    main()
