#!/usr/bin/env python3
"""
Phase 10BD/10BH/10BJ Scoring Engine for pethubonline.com
- 10BD: Best Answer Scoring (8 dimensions)
- 10BH: Cluster Dominance Program
- 10BJ: Authority Moat Engine (7 dimensions)

Uses READ-ONLY WordPress REST API access.
"""

import json
import csv
import re
import os
import subprocess
import sys
from html import unescape
from collections import defaultdict

# ─── Configuration ───────────────────────────────────────────────────────────

WP_API = "https://pethubonline.com/wp-json/wp/v2"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"

OUTPUT_BD = "/var/lib/freelancer/projects/40416335/phase10bd_data"
OUTPUT_BH = "/var/lib/freelancer/projects/40416335/phase10bh_data"
OUTPUT_BJ = "/var/lib/freelancer/projects/40416335/phase10bj_data"

# Category ID -> Cluster mapping based on site taxonomy
CATEGORY_CLUSTER_MAP = {
    1377: "Cat Supplies",
    1459: "Cat Toys",
    1413: "Indoor Cats",
    1401: "Dog Beds",
    1396: "Pet Beds",
    1489: "Dog Care",
    1467: "Dog Food",
    1422: "Dog Harnesses",
    1450: "Dog Health",
    1376: "Dog Supplies",
    1441: "Dog Toys",
    1442: "Puppy Care",
    1474: "Training Supplies",
    1397: "Pet Care",
    1379: "Product Reviews",
    1391: "Pet Health",
    1380: "Buying Guides",
    1460: "Interactive Toys",
    1455: "Orthopaedic Care",
    1487: "Health & Wellness",
    1: "Uncategorized",
}

# Map to 13 core clusters
CLUSTER_CONSOLIDATION = {
    "Cat Supplies": "Cat Supplies",
    "Cat Toys": "Cat Toys",
    "Indoor Cats": "Indoor Cats",
    "Dog Beds": "Dog Beds",
    "Pet Beds": "Dog Beds",
    "Dog Care": "Dog Care",
    "Dog Food": "Dog Food",
    "Dog Harnesses": "Dog Harnesses",
    "Dog Health": "Dog Health",
    "Dog Supplies": "Dog Supplies",
    "Dog Toys": "Dog Toys",
    "Puppy Care": "Puppy Care",
    "Training Supplies": "Dog Training",
    "Pet Care": "Pet Care General",
    "Product Reviews": "Product Reviews",
    "Pet Health": "Dog Health",
    "Buying Guides": "Product Reviews",
    "Interactive Toys": "Cat Toys",
    "Orthopaedic Care": "Dog Beds",
    "Health & Wellness": "Dog Health",
    "Uncategorized": "Uncategorized",
}

# UK trust organisations
UK_ORGS = [
    "RSPCA", "PDSA", "BVA", "RCVS", "Kennel Club", "Dogs Trust",
    "Cats Protection", "PFMA", "FEDIAF", "Blue Cross", "Battersea",
    "DEFRA", "Animal Health Trust", "Pet Food Manufacturers",
    "British Veterinary", "Royal College of Veterinary",
    "Veterinary Medicines Directorate", "Pet Industry Federation",
    "International Cat Care", "Governing Council of the Cat Fancy",
    "GCCF", "TICA", "Wood Green", "Mayhew", "NAWT",
    "National Animal Welfare Trust", "Pet Charity", "APBC",
    "Association of Pet Behaviour Counsellors", "ABTC",
    "Animal Behaviour and Training Council", "University of",
    "NHS", "NICE guidelines", "British Small Animal Veterinary",
    "BSAVA",
]


def fetch_all_posts():
    """Fetch all published posts via WP REST API using curl."""
    all_posts = []
    page = 1
    while True:
        url = f"{WP_API}/posts?per_page=100&page={page}&context=edit"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", f"{WP_USER}:{WP_PASS}", url],
            capture_output=True, text=True
        )
        try:
            posts = json.loads(result.stdout)
        except json.JSONDecodeError:
            break
        if not posts or isinstance(posts, dict):
            break
        all_posts.extend(posts)
        if len(posts) < 100:
            break
        page += 1
    return all_posts


def strip_html(html_text):
    """Remove HTML tags and Gutenberg comments, decode entities."""
    text = re.sub(r'<!--.*?-->', '', html_text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_cluster(post):
    """Determine the primary cluster for a post using priority-based assignment."""
    cats = post.get("categories", [])
    title = get_title(post).lower()

    # Priority 1: Check for high-priority specific clusters first
    # These take precedence when present regardless of order
    PRIORITY_CATS = {
        1442: "Puppy Care",       # Puppy Care always wins
        1413: "Indoor Cats",      # Indoor Cats always wins
        1467: "Dog Food",         # Dog Food is specific
        1422: "Dog Harnesses",    # Dog Harnesses is specific
        1474: "Dog Training",     # Training Supplies -> Dog Training
    }
    for cat_id in cats:
        if cat_id in PRIORITY_CATS:
            return PRIORITY_CATS[cat_id]

    # Priority 2: Title-based heuristics (works for all posts, not just uncategorized)
    grooming_keywords = ["groom", "shampoo", "brush", "nail clip", "nail trim", "coat care",
                         "deshed", "de-shed", "bathing"]
    if any(kw in title for kw in grooming_keywords):
        return "Dog Grooming"
    if "puppy" in title:
        return "Puppy Care"
    if "indoor cat" in title or "house cat" in title:
        return "Indoor Cats"
    if "dog food" in title or ("feeding" in title and "dog" in title):
        return "Dog Food"
    if "harness" in title:
        return "Dog Harnesses"
    if "training" in title and "dog" in title:
        return "Dog Training"

    # Priority 3: Standard category mapping (most specific first)
    SPECIFICITY_ORDER = [
        1459, 1441, 1401, 1396, 1450, 1489, 1377, 1376, 1391, 1460, 1455, 1487,
        1397, 1379, 1380, 1,
    ]
    for cat_id in SPECIFICITY_ORDER:
        if cat_id in cats:
            raw = CATEGORY_CLUSTER_MAP.get(cat_id, "Uncategorized")
            cluster = CLUSTER_CONSOLIDATION.get(raw, raw)
            if cluster != "Uncategorized":
                return cluster

    # Priority 4: Fallback — any non-Uncategorized
    for cat_id in cats:
        raw = CATEGORY_CLUSTER_MAP.get(cat_id, "Uncategorized")
        cluster = CLUSTER_CONSOLIDATION.get(raw, raw)
        if cluster != "Uncategorized":
            return cluster

    # Priority 5: Title-based fallback for truly uncategorized
    if "cat" in title:
        return "Cat Supplies"
    if "dog bed" in title or "dog's bed" in title:
        return "Dog Beds"
    if "dog toy" in title:
        return "Dog Toys"
    if "dog" in title:
        return "Dog Supplies"

    return "Uncategorized"


def get_title(post):
    """Extract post title."""
    t = post.get("title", {})
    return t.get("raw", t.get("rendered", "Untitled"))


def get_content_raw(post):
    """Get raw content from post."""
    c = post.get("content", {})
    return c.get("raw", c.get("rendered", ""))


def count_tables(content):
    """Count HTML/Gutenberg tables and their rows."""
    tables = re.findall(r'<table[^>]*>.*?</table>', content, re.DOTALL | re.IGNORECASE)
    total_rows = 0
    total_cols = 0
    for table in tables:
        rows = re.findall(r'<tr[^>]*>', table, re.IGNORECASE)
        total_rows += len(rows)
        # Count columns from first row
        first_row = re.search(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL | re.IGNORECASE)
        if first_row:
            cols = len(re.findall(r'<t[hd][^>]*>', first_row.group(1), re.IGNORECASE))
            total_cols = max(total_cols, cols)
    return len(tables), total_rows, total_cols


def count_faqs(content):
    """Count FAQ questions and measure answer quality."""
    # Look for FAQ section patterns
    faq_section = re.search(
        r'(?:FAQ|Frequently Asked|Common Questions)(.*?)(?=<h[12]|$)',
        content, re.DOTALL | re.IGNORECASE
    )
    # Count question patterns
    questions = re.findall(
        r'<(?:h[2-4]|strong|b)[^>]*>\s*(?:Q[:.]?\s*)?([^<]*\?)\s*</(?:h[2-4]|strong|b)>',
        content, re.IGNORECASE
    )
    # Also count wp:heading followed by question marks
    heading_questions = re.findall(
        r'<h[2-4][^>]*>[^<]*\?[^<]*</h[2-4]>',
        content, re.IGNORECASE
    )
    faq_count = max(len(questions), len(heading_questions))

    # Measure answer length after FAQ headings
    avg_answer_len = 0
    if faq_section:
        answers = re.findall(r'<p[^>]*>(.*?)</p>', faq_section.group(1), re.DOTALL)
        if answers:
            avg_answer_len = sum(len(strip_html(a)) for a in answers) / len(answers)

    return faq_count, avg_answer_len


def count_uk_orgs(content):
    """Count UK organisation references."""
    text = content.upper()
    found = set()
    total = 0
    for org in UK_ORGS:
        pattern = org.upper()
        occurrences = text.count(pattern)
        if occurrences > 0:
            found.add(org)
            total += occurrences
    return len(found), total


def count_glossary_terms(content):
    """Count defined/glossary terms."""
    # Look for glossary/key terms sections
    glossary_section = re.search(
        r'(?:Glossary|Key Terms|Definitions|Terminology)(.*?)(?=<h[12]|$)',
        content, re.DOTALL | re.IGNORECASE
    )
    terms = 0
    if glossary_section:
        # Count defined terms (bold or dt elements)
        terms = len(re.findall(
            r'<(?:strong|b|dt)[^>]*>[^<]+</(?:strong|b|dt)>',
            glossary_section.group(1), re.IGNORECASE
        ))

    # Also count bold definitions throughout the text (pattern: <strong>Term</strong> — definition)
    inline_defs = re.findall(
        r'<strong>[^<]{3,50}</strong>\s*(?:—|–|-|:)\s*',
        content, re.IGNORECASE
    )
    return max(terms, len(inline_defs))


def count_specific_numbers(content):
    """Count specific numbers, measurements, prices, timelines."""
    text = strip_html(content)
    # UK prices
    prices = re.findall(r'£[\d,.]+', text)
    # Measurements
    measurements = re.findall(r'\d+\s*(?:cm|mm|kg|g|ml|litres?|inches?|feet|ft|metres?|m\b)', text, re.IGNORECASE)
    # Timelines
    timelines = re.findall(r'\d+\s*(?:days?|weeks?|months?|years?|hours?|minutes?)', text, re.IGNORECASE)
    # Percentages
    percentages = re.findall(r'\d+%', text)
    # Temperature
    temps = re.findall(r'\d+\s*°[CF]', text)
    # Step counts
    steps = re.findall(r'(?:step|stage|phase)\s*\d+', text, re.IGNORECASE)
    # General specific numbers
    numbers = re.findall(r'\b\d{2,}\b', text)

    return {
        "prices": len(prices),
        "measurements": len(measurements),
        "timelines": len(timelines),
        "percentages": len(percentages),
        "temperatures": len(temps),
        "steps": len(steps),
        "total_specific": len(prices) + len(measurements) + len(timelines) + len(percentages) + len(temps) + len(steps),
    }


def count_internal_links(content):
    """Count internal links to pethubonline.com."""
    links = re.findall(r'href="[^"]*pethubonline\.com[^"]*"', content, re.IGNORECASE)
    return len(links)


def count_lists(content):
    """Count list items in content."""
    items = re.findall(r'<li[^>]*>', content, re.IGNORECASE)
    return len(items)


def count_headings(content):
    """Count headings by level."""
    h2 = len(re.findall(r'<h2[^>]*>', content, re.IGNORECASE))
    h3 = len(re.findall(r'<h3[^>]*>', content, re.IGNORECASE))
    h4 = len(re.findall(r'<h4[^>]*>', content, re.IGNORECASE))
    return h2, h3, h4


def has_section(content, *patterns):
    """Check if content has a section matching any of the patterns."""
    for pat in patterns:
        if re.search(pat, content, re.IGNORECASE):
            return True
    return False


def get_first_paragraphs(content, n=3):
    """Get first n paragraphs of content."""
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', content, re.DOTALL)
    return ' '.join(strip_html(p) for p in paragraphs[:n])


def word_count(text):
    """Count words in text."""
    clean = strip_html(text)
    return len(clean.split())


# ─── PHASE 10BD: Best Answer Scoring ─────────────────────────────────────────

def score_directness(post, content, title):
    """Score how directly the post answers its title question (0-100)."""
    first_paras = get_first_paragraphs(content, 3)
    title_clean = strip_html(title).lower()

    # Extract key topic words from title (remove stop words)
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'for',
                  'and', 'or', 'but', 'in', 'on', 'at', 'to', 'of', 'with', 'by',
                  'your', 'our', 'my', 'how', 'what', 'why', 'when', 'where', 'which',
                  'do', 'does', 'can', 'should', 'will', 'would', 'could', 'best',
                  'top', 'guide', 'complete', 'ultimate', 'uk'}
    title_words = set(w for w in re.findall(r'\w+', title_clean) if w not in stop_words and len(w) > 2)

    first_lower = first_paras.lower()
    score = 0

    # Check how many title words appear in first paragraphs
    if title_words:
        overlap = sum(1 for w in title_words if w in first_lower)
        word_ratio = overlap / len(title_words)
        score += word_ratio * 35

    # Check for direct answer patterns
    direct_patterns = [
        r'(?:the answer is|in short|simply put|the short answer)',
        r'(?:yes,|no,|it depends)',
        r'(?:you should|we recommend|the best (?:option|choice|way))',
        r'(?:here\'s what you need to know|here is)',
        r'(?:the (?:ideal|recommended|optimal|right|perfect))',
    ]
    for pat in direct_patterns:
        if re.search(pat, first_lower):
            score += 8

    # Check for "At a Glance" or "Key Takeaways" near the top
    early_content = content[:2000].lower()
    if 'at a glance' in early_content or 'key takeaway' in early_content or 'quick answer' in early_content:
        score += 20

    # Penalise if first paragraph is very generic/thin
    if len(first_paras) < 100:
        score -= 15
    elif len(first_paras) > 200:
        score += 10

    return max(0, min(100, int(score)))


def score_usefulness(post, content, text):
    """Score practical, actionable guidance (0-100)."""
    score = 0
    numbers = count_specific_numbers(content)

    # Specific measurements and data
    score += min(20, numbers["total_specific"] * 2)

    # Step-by-step instructions
    if numbers["steps"] > 0:
        score += min(15, numbers["steps"] * 3)

    # Lists (actionable)
    list_count = count_lists(content)
    score += min(15, list_count)

    # UK-specific prices
    if numbers["prices"] > 0:
        score += min(15, numbers["prices"] * 3)

    # Timelines
    if numbers["timelines"] > 0:
        score += min(10, numbers["timelines"] * 2)

    # Action verbs in headings
    headings_text = ' '.join(re.findall(r'<h[2-4][^>]*>(.*?)</h[2-4]>', content, re.IGNORECASE))
    action_words = ['how to', 'step', 'guide', 'tips', 'ways to', 'checklist', 'what to',
                    'choose', 'pick', 'select', 'avoid', 'prevent', 'treat', 'feed', 'train']
    for aw in action_words:
        if aw in headings_text.lower():
            score += 3

    # Content length bonus (longer = more useful typically)
    wc = word_count(content)
    if wc > 3000:
        score += 10
    elif wc > 2000:
        score += 5

    return max(0, min(100, int(score)))


def score_completeness(post, content, text):
    """Score topic coverage completeness (0-100)."""
    score = 0
    h2, h3, h4 = count_headings(content)

    # Section count (more sections = more complete)
    score += min(25, h2 * 3)
    score += min(15, h3 * 1.5)

    # Has FAQ section
    if has_section(content, r'FAQ', r'Frequently Asked', r'Common Questions'):
        score += 12

    # Has glossary/definitions
    if has_section(content, r'Glossary', r'Key Terms', r'Definitions', r'Terminology'):
        score += 10

    # Has comparison section
    table_count, _, _ = count_tables(content)
    if table_count > 0:
        score += 10

    # Has practical/how-to section
    if has_section(content, r'How to', r'Step-by-Step', r'Practical', r'What to Do'):
        score += 8

    # Content depth (word count)
    wc = word_count(content)
    if wc > 5000:
        score += 15
    elif wc > 3000:
        score += 10
    elif wc > 2000:
        score += 5

    # Has At a Glance / Summary
    if has_section(content, r'At a Glance', r'Summary', r'Overview', r'Key Takeaway'):
        score += 8

    # Has warnings/considerations
    if has_section(content, r'Warning', r'Caution', r'Important', r'Things to Avoid', r'Common Mistakes'):
        score += 5

    return max(0, min(100, int(score)))


def score_practical_guidance(post, content, text):
    """Score UK-relevant practical advice (0-100)."""
    score = 0
    numbers = count_specific_numbers(content)

    # UK prices
    score += min(20, numbers["prices"] * 4)

    # Measurements
    score += min(15, numbers["measurements"] * 2)

    # Timelines
    score += min(15, numbers["timelines"] * 2)

    # Temperatures
    score += min(5, numbers["temperatures"] * 2)

    # UK-specific content markers
    uk_markers = ['uk', 'britain', 'british', 'england', 'scotland', 'wales',
                  'northern ireland', 'nhs', 'sterling', '£', 'veterinary surgery',
                  'pet shop', 'high street', 'amazon.co.uk', 'argos', 'pets at home']
    text_lower = text.lower()
    uk_count = sum(1 for m in uk_markers if m in text_lower)
    score += min(15, uk_count * 3)

    # Specific product/brand recommendations
    brand_patterns = re.findall(
        r'(?:we recommend|our top pick|best option|editor.s choice)',
        text_lower
    )
    score += min(10, len(brand_patterns) * 3)

    # Breed/age-specific advice
    breed_mentions = re.findall(
        r'(?:labrador|golden retriever|french bulldog|cockapoo|spaniel|'
        r'terrier|german shepherd|poodle|dachshund|chihuahua|'
        r'siamese|persian|bengal|ragdoll|british shorthair|maine coon)',
        text_lower
    )
    score += min(10, len(set(breed_mentions)) * 2)

    # Step counts / numbered instructions
    score += min(10, numbers["steps"] * 2)

    return max(0, min(100, int(score)))


def score_comparison_richness(post, content, text):
    """Score comparison tables and depth (0-100)."""
    table_count, total_rows, max_cols = count_tables(content)

    score = 0

    # Table count (big impact)
    score += min(30, table_count * 10)

    # Row count
    score += min(25, total_rows * 2)

    # Column count
    score += min(15, max_cols * 3)

    # Comparison language in headings
    comp_headings = len(re.findall(
        r'<h[2-4][^>]*>[^<]*(?:vs|versus|compared?|comparison|differences?|alternatives?|pros and cons)[^<]*</h[2-4]>',
        content, re.IGNORECASE
    ))
    score += min(15, comp_headings * 5)

    # Pros/cons patterns
    pros_cons = len(re.findall(r'(?:pros?|cons?|advantages?|disadvantages?|benefits?|drawbacks?)\s*:', text.lower()))
    score += min(15, pros_cons * 3)

    return max(0, min(100, int(score)))


def score_trust_depth(post, content, text):
    """Score UK organisation references (0-100)."""
    org_variety, org_total = count_uk_orgs(content)

    score = 0

    # Variety of orgs (most important)
    score += min(40, org_variety * 6)

    # Frequency of citations
    score += min(25, org_total * 2)

    # Methodology/evidence language
    evidence_patterns = [
        r'(?:research shows|studies? (?:show|suggest|indicate|found))',
        r'(?:according to|as recommended by|based on)',
        r'(?:evidence-based|peer-reviewed|clinical|scientific)',
        r'(?:veterinary advice|vet-approved|vet-recommended)',
        r'(?:our methodology|our research|our sources)',
    ]
    for pat in evidence_patterns:
        if re.search(pat, text.lower()):
            score += 5

    # Specific year citations
    year_citations = re.findall(r'\b20[12]\d\b', text)
    score += min(10, len(year_citations) * 2)

    return max(0, min(100, int(score)))


def score_extractability(post, content, text):
    """Score AI extractability (0-100)."""
    score = 0

    # At a Glance section
    if has_section(content, r'At a Glance'):
        score += 18

    # Key Takeaways
    if has_section(content, r'Key Takeaway'):
        score += 15

    # FAQ section
    if has_section(content, r'FAQ', r'Frequently Asked'):
        score += 15

    # Key Terms / Glossary
    if has_section(content, r'Key Terms', r'Glossary'):
        score += 12

    # Bold definitions (structured knowledge)
    bold_defs = len(re.findall(r'<strong>[^<]{3,50}</strong>\s*(?:—|–|-|:)', content))
    score += min(15, bold_defs * 2)

    # Structured lists
    list_items = count_lists(content)
    score += min(10, list_items // 2)

    # Tables (structured data)
    table_count, _, _ = count_tables(content)
    score += min(10, table_count * 4)

    # Clear heading hierarchy
    h2, h3, h4 = count_headings(content)
    if h2 >= 3 and h3 >= 2:
        score += 5

    return max(0, min(100, int(score)))


def score_citation_confidence(post, content, text):
    """Score overall citation-worthiness (0-100)."""
    score = 0

    # UK org references
    org_variety, org_total = count_uk_orgs(content)
    score += min(20, org_variety * 3)

    # Specific data points
    numbers = count_specific_numbers(content)
    score += min(15, numbers["total_specific"])

    # Authoritative tone (3rd person, formal)
    formal_patterns = [
        r'(?:it is (?:recommended|important|essential|advisable))',
        r'(?:owners should|pet owners should)',
        r'(?:veterinary professionals|qualified vet)',
        r'(?:always consult|seek advice from)',
    ]
    for pat in formal_patterns:
        if re.search(pat, text.lower()):
            score += 4

    # UK-specific content
    uk_refs = len(re.findall(r'(?:UK|United Kingdom|Britain|British)', text))
    score += min(10, uk_refs * 2)

    # Content depth
    wc = word_count(content)
    if wc > 4000:
        score += 12
    elif wc > 2500:
        score += 8
    elif wc > 1500:
        score += 4

    # Source diversity
    if has_section(content, r'Sources', r'References', r'Further Reading', r'Useful Links'):
        score += 10

    # Structured knowledge
    table_count, _, _ = count_tables(content)
    score += min(8, table_count * 3)

    faq_count, _ = count_faqs(content)
    score += min(8, faq_count * 2)

    return max(0, min(100, int(score)))


def calculate_best_answer_score(scores):
    """Weighted average across 8 dimensions."""
    weights = {
        "directness": 0.15,
        "usefulness": 0.15,
        "completeness": 0.10,
        "practical_guidance": 0.15,
        "comparison_richness": 0.15,
        "trust_depth": 0.10,
        "extractability": 0.10,
        "citation_confidence": 0.10,
    }
    total = sum(scores[dim] * w for dim, w in weights.items())
    return round(total, 1)


# ─── PHASE 10BJ: Authority Moat Scoring ──────────────────────────────────────

def score_glossary_depth(post, content, text):
    """Score glossary/definition depth (0-100)."""
    terms = count_glossary_terms(content)
    score = 0

    # Term count
    score += min(40, terms * 4)

    # Dedicated glossary section
    if has_section(content, r'Glossary', r'Key Terms', r'Definitions', r'Terminology'):
        score += 20

    # Inline definitions (bold term — definition pattern)
    inline_defs = len(re.findall(r'<strong>[^<]{3,50}</strong>\s*(?:—|–|-)\s*[A-Z]', content))
    score += min(20, inline_defs * 3)

    # Integration into body (terms used multiple times)
    if terms > 5:
        score += 10
    elif terms > 2:
        score += 5

    # Variety assessment (different types of terms)
    if terms > 8:
        score += 10

    return max(0, min(100, int(score)))


def score_practical_depth_moat(post, content, text):
    """Score practical depth for moat (0-100)."""
    numbers = count_specific_numbers(content)
    score = 0

    # Prices (UK)
    score += min(20, numbers["prices"] * 4)

    # Measurements
    score += min(15, numbers["measurements"] * 2)

    # Timelines
    score += min(15, numbers["timelines"] * 2)

    # Steps
    score += min(15, numbers["steps"] * 3)

    # Total data density
    wc = max(word_count(content), 1)
    density = numbers["total_specific"] / (wc / 1000)
    if density > 10:
        score += 20
    elif density > 5:
        score += 15
    elif density > 2:
        score += 10
    elif density > 1:
        score += 5

    # Percentages (precision indicator)
    score += min(10, numbers["percentages"] * 2)

    # Temperature mentions (care precision)
    score += min(5, numbers["temperatures"] * 2)

    return max(0, min(100, int(score)))


def score_comparison_depth_moat(post, content, text):
    """Score comparison depth for moat (0-100)."""
    table_count, total_rows, max_cols = count_tables(content)
    score = 0

    # Table count
    score += min(25, table_count * 8)

    # Row richness
    score += min(20, total_rows * 1.5)

    # Column richness
    score += min(15, max_cols * 3)

    # Variety of comparison types
    comp_types = 0
    if re.search(r'(?:price|cost|value)', content, re.IGNORECASE):
        comp_types += 1
    if re.search(r'(?:size|dimension|weight)', content, re.IGNORECASE):
        comp_types += 1
    if re.search(r'(?:material|fabric|construction)', content, re.IGNORECASE):
        comp_types += 1
    if re.search(r'(?:rating|score|review)', content, re.IGNORECASE):
        comp_types += 1
    if re.search(r'(?:pros|cons|advantage|disadvantage)', content, re.IGNORECASE):
        comp_types += 1
    score += min(20, comp_types * 5)

    # Comparison headings
    comp_headings = len(re.findall(
        r'<h[2-4][^>]*>[^<]*(?:vs|comparison|compared|alternatives)[^<]*</h[2-4]>',
        content, re.IGNORECASE
    ))
    score += min(20, comp_headings * 6)

    return max(0, min(100, int(score)))


def score_faq_depth_moat(post, content, text):
    """Score FAQ depth for moat (0-100)."""
    faq_count, avg_answer_len = count_faqs(content)
    score = 0

    # Question count
    score += min(35, faq_count * 5)

    # Answer quality (length)
    if avg_answer_len > 200:
        score += 20
    elif avg_answer_len > 100:
        score += 12
    elif avg_answer_len > 50:
        score += 6

    # Dedicated FAQ section
    if has_section(content, r'FAQ', r'Frequently Asked'):
        score += 15

    # Question variety (different question words)
    q_text = ' '.join(re.findall(r'<h[2-4][^>]*>([^<]*\?)[^<]*</h[2-4]>', content, re.IGNORECASE))
    q_words = set()
    for qw in ['what', 'how', 'why', 'when', 'where', 'which', 'can', 'should', 'do', 'is', 'are']:
        if qw in q_text.lower():
            q_words.add(qw)
    score += min(15, len(q_words) * 3)

    # Schema markup for FAQ (wp:yoast/faq-block or similar)
    if 'faq' in content.lower() and ('schema' in content.lower() or 'yoast' in content.lower()):
        score += 10

    # Bonus for many questions
    if faq_count >= 10:
        score += 5

    return max(0, min(100, int(score)))


def score_semantic_density(post, content, text):
    """Score semantic density / keyword variety (0-100)."""
    score = 0
    text_lower = text.lower()
    wc = max(word_count(content), 1)

    # Unique meaningful words (vocabulary richness)
    words = re.findall(r'\b[a-z]{4,}\b', text_lower)
    unique_words = len(set(words))
    vocab_ratio = unique_words / max(len(words), 1)

    if vocab_ratio > 0.4:
        score += 20
    elif vocab_ratio > 0.3:
        score += 15
    elif vocab_ratio > 0.2:
        score += 10

    # Unique word count
    if unique_words > 500:
        score += 15
    elif unique_words > 300:
        score += 10
    elif unique_words > 150:
        score += 5

    # Internal links (topical connectivity)
    internal_links = count_internal_links(content)
    score += min(20, internal_links * 3)

    # Heading topic coverage
    h2, h3, h4 = count_headings(content)
    score += min(15, (h2 + h3) * 1.5)

    # Entity variety (pet types, breeds, products mentioned)
    entities = set()
    pet_types = ['dog', 'cat', 'puppy', 'kitten', 'pet']
    for pt in pet_types:
        if pt in text_lower:
            entities.add(pt)
    # Breeds
    breeds = re.findall(
        r'(?:labrador|retriever|bulldog|spaniel|terrier|shepherd|poodle|'
        r'siamese|persian|bengal|ragdoll|shorthair|maine coon|cockapoo)',
        text_lower
    )
    entities.update(breeds)
    score += min(15, len(entities) * 2)

    # Content sections coverage
    section_types = 0
    checks = [
        r'(?:introduction|overview|what is)',
        r'(?:how to|guide|steps)',
        r'(?:benefits?|advantages?|why)',
        r'(?:tips?|advice|recommendation)',
        r'(?:faq|questions?)',
        r'(?:conclusion|summary|final)',
    ]
    for check in checks:
        if re.search(check, content, re.IGNORECASE):
            section_types += 1
    score += min(15, section_types * 3)

    return max(0, min(100, int(score)))


def calculate_authority_moat_score(scores):
    """Simple average of 7 moat dimensions."""
    dims = ["glossary_depth", "trust_depth", "practical_depth",
            "comparison_depth", "faq_depth", "citation_confidence", "semantic_density"]
    total = sum(scores[d] for d in dims)
    return round(total / len(dims), 1)


# ─── Main Processing ─────────────────────────────────────────────────────────

def process_all():
    """Main entry point: fetch posts, score everything, generate all CSVs."""
    print("Fetching all published posts...")
    posts = fetch_all_posts()
    print(f"Fetched {len(posts)} posts")

    all_scores = []

    for i, post in enumerate(posts):
        title = get_title(post)
        content = get_content_raw(post)
        text = strip_html(content)
        cluster = get_cluster(post)
        post_id = post["id"]

        # Phase 10BD scores
        bd_scores = {
            "directness": score_directness(post, content, title),
            "usefulness": score_usefulness(post, content, text),
            "completeness": score_completeness(post, content, text),
            "practical_guidance": score_practical_guidance(post, content, text),
            "comparison_richness": score_comparison_richness(post, content, text),
            "trust_depth": score_trust_depth(post, content, text),
            "extractability": score_extractability(post, content, text),
            "citation_confidence": score_citation_confidence(post, content, text),
        }
        bd_scores["best_answer_score"] = calculate_best_answer_score(bd_scores)

        # Phase 10BJ scores
        bj_scores = {
            "glossary_depth": score_glossary_depth(post, content, text),
            "trust_depth": score_trust_depth(post, content, text),
            "practical_depth": score_practical_depth_moat(post, content, text),
            "comparison_depth": score_comparison_depth_moat(post, content, text),
            "faq_depth": score_faq_depth_moat(post, content, text),
            "citation_confidence": score_citation_confidence(post, content, text),
            "semantic_density": score_semantic_density(post, content, text),
        }
        bj_scores["authority_moat_score"] = calculate_authority_moat_score(bj_scores)

        all_scores.append({
            "id": post_id,
            "title": title,
            "cluster": cluster,
            "bd": bd_scores,
            "bj": bj_scores,
        })

        if (i + 1) % 20 == 0:
            print(f"  Scored {i + 1}/{len(posts)} posts...")

    print(f"Scoring complete for {len(all_scores)} posts")

    # ─── Generate Phase 10BD CSVs ─────────────────────────────────────────

    # 1. best_answer_scores.csv
    print("Generating Phase 10BD CSVs...")
    bd_path = os.path.join(OUTPUT_BD, "best_answer_scores.csv")
    with open(bd_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "title", "cluster", "directness", "usefulness",
                         "completeness", "practical_guidance", "comparison_richness",
                         "trust_depth", "extractability", "citation_confidence",
                         "best_answer_score"])
        for s in sorted(all_scores, key=lambda x: -x["bd"]["best_answer_score"]):
            writer.writerow([
                s["id"], s["title"], s["cluster"],
                s["bd"]["directness"], s["bd"]["usefulness"],
                s["bd"]["completeness"], s["bd"]["practical_guidance"],
                s["bd"]["comparison_richness"], s["bd"]["trust_depth"],
                s["bd"]["extractability"], s["bd"]["citation_confidence"],
                s["bd"]["best_answer_score"],
            ])
    print(f"  Saved: {bd_path}")

    # 2. best_answer_leaderboard.csv (Top 25 + Bottom 25)
    sorted_bd = sorted(all_scores, key=lambda x: -x["bd"]["best_answer_score"])
    leaderboard_path = os.path.join(OUTPUT_BD, "best_answer_leaderboard.csv")
    with open(leaderboard_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "id", "title", "cluster", "best_answer_score",
                         "weakest_dimension", "weakest_score"])

        # Top 25
        for rank, s in enumerate(sorted_bd[:25], 1):
            dims = {k: v for k, v in s["bd"].items() if k != "best_answer_score"}
            weakest_dim = min(dims, key=dims.get)
            writer.writerow([
                rank, s["id"], s["title"], s["cluster"],
                s["bd"]["best_answer_score"], weakest_dim, dims[weakest_dim],
            ])

        # Bottom 25
        bottom_25 = sorted_bd[-25:]
        for rank, s in enumerate(bottom_25, len(sorted_bd) - 24):
            dims = {k: v for k, v in s["bd"].items() if k != "best_answer_score"}
            weakest_dim = min(dims, key=dims.get)
            writer.writerow([
                rank, s["id"], s["title"], s["cluster"],
                s["bd"]["best_answer_score"], weakest_dim, dims[weakest_dim],
            ])
    print(f"  Saved: {leaderboard_path}")

    # 3. easiest_upgrades.csv
    upgrades = []
    for s in all_scores:
        dims = {k: v for k, v in s["bd"].items() if k != "best_answer_score"}
        weakest_dim = min(dims, key=dims.get)
        weakest_val = dims[weakest_dim]
        # Estimate lift: if we bring weakest dimension to 70, what's the overall gain?
        weights = {
            "directness": 0.15, "usefulness": 0.15, "completeness": 0.10,
            "practical_guidance": 0.15, "comparison_richness": 0.15,
            "trust_depth": 0.10, "extractability": 0.10, "citation_confidence": 0.10,
        }
        # Calculate total potential lift from improving ALL weak dimensions to 70
        # This gives more differentiated lifts
        total_lift = 0
        for dim_name, dim_val in dims.items():
            if dim_val < 70:
                improvement = 70 - dim_val
                total_lift += improvement * weights[dim_name]
        # estimated_lift = improving just the weakest dimension to cluster median (~65)
        # Plus bonus for having many weak dimensions (easier overall improvement)
        weakest_target = min(65, weakest_val + 40)
        primary_lift = (weakest_target - weakest_val) * weights[weakest_dim]
        # Secondary lift bonus: count of dimensions below 50 (each adds marginal lift)
        dims_below_50 = sum(1 for v in dims.values() if v < 50)
        secondary_bonus = dims_below_50 * 1.5
        lift = primary_lift + secondary_bonus

        # Generate specific upgrade action
        actions = {
            "directness": "Add clear opening answer in first 2 sentences; add At a Glance box",
            "usefulness": "Add specific measurements, step-by-step instructions, UK prices",
            "completeness": "Add FAQ section, glossary, comparison table, practical guide section",
            "practical_guidance": "Add UK prices (£), specific measurements, breed-specific timelines",
            "comparison_richness": "Add comparison table with 5+ rows, pros/cons for each option",
            "trust_depth": "Add RSPCA/PDSA/BVA/Kennel Club references and citations",
            "extractability": "Add At a Glance box, Key Takeaways, FAQ schema, bold definitions",
            "citation_confidence": "Add UK org references, specific data points, evidence-based language",
        }

        upgrades.append({
            "id": s["id"],
            "title": s["title"],
            "cluster": s["cluster"],
            "current_score": s["bd"]["best_answer_score"],
            "weakest_dimension": weakest_dim,
            "weakest_score": weakest_val,
            "estimated_lift": round(lift, 1),
            "upgrade_action": actions[weakest_dim],
        })

    # Sort by estimated lift (highest first)
    upgrades.sort(key=lambda x: -x["estimated_lift"])
    upgrades_path = os.path.join(OUTPUT_BD, "easiest_upgrades.csv")
    with open(upgrades_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "title", "cluster", "current_score",
                         "weakest_dimension", "weakest_score", "estimated_lift",
                         "upgrade_action"])
        for u in upgrades[:25]:
            writer.writerow([
                u["id"], u["title"], u["cluster"], u["current_score"],
                u["weakest_dimension"], u["weakest_score"],
                u["estimated_lift"], u["upgrade_action"],
            ])
    print(f"  Saved: {upgrades_path}")

    # ─── Generate Phase 10BH CSVs ─────────────────────────────────────────

    print("Generating Phase 10BH CSVs...")
    clusters = defaultdict(list)
    for s in all_scores:
        clusters[s["cluster"]].append(s)

    # cluster_dominance_v2.csv
    cluster_stats = []
    for cluster_name, cluster_posts in clusters.items():
        bd_scores_list = [p["bd"]["best_answer_score"] for p in cluster_posts]
        avg_score = round(sum(bd_scores_list) / len(bd_scores_list), 1)
        min_score = min(bd_scores_list)
        max_score = max(bd_scores_list)
        above_80 = sum(1 for s in bd_scores_list if s >= 80)
        below_60 = sum(1 for s in bd_scores_list if s < 60)

        # Find weakest dimension cluster-wide
        dim_avgs = {}
        dims = ["directness", "usefulness", "completeness", "practical_guidance",
                "comparison_richness", "trust_depth", "extractability", "citation_confidence"]
        for dim in dims:
            dim_avgs[dim] = round(
                sum(p["bd"][dim] for p in cluster_posts) / len(cluster_posts), 1
            )
        weakest_dim = min(dim_avgs, key=dim_avgs.get)

        # Priority actions
        actions = []
        if dim_avgs["comparison_richness"] < 50:
            actions.append("Add comparison tables to all posts")
        if dim_avgs["trust_depth"] < 60:
            actions.append("Add UK org references (RSPCA, PDSA, BVA)")
        if dim_avgs["practical_guidance"] < 60:
            actions.append("Add UK prices, measurements, timelines")
        if dim_avgs["extractability"] < 60:
            actions.append("Add At a Glance, FAQ, Key Terms sections")
        if dim_avgs["directness"] < 60:
            actions.append("Improve opening paragraphs with direct answers")
        if not actions:
            actions.append("Maintain quality; focus on below-60 posts")

        cluster_stats.append({
            "cluster": cluster_name,
            "post_count": len(cluster_posts),
            "avg_score": avg_score,
            "min_score": min_score,
            "max_score": max_score,
            "above_80": above_80,
            "below_60": below_60,
            "weakest_dimension": weakest_dim,
            "dimension_score": dim_avgs[weakest_dim],
            "priority_actions": "; ".join(actions),
        })

    cluster_stats.sort(key=lambda x: x["avg_score"])
    dom_path = os.path.join(OUTPUT_BH, "cluster_dominance_v2.csv")
    with open(dom_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["cluster", "post_count", "avg_score", "min_score", "max_score",
                         "above_80", "below_60", "weakest_dimension", "dimension_score",
                         "priority_actions"])
        for cs in cluster_stats:
            writer.writerow([
                cs["cluster"], cs["post_count"], cs["avg_score"],
                cs["min_score"], cs["max_score"], cs["above_80"],
                cs["below_60"], cs["weakest_dimension"], cs["dimension_score"],
                cs["priority_actions"],
            ])
    print(f"  Saved: {dom_path}")

    # cluster_roadmaps_v2.csv
    # Priority order: Indoor Cats, Puppy Care, Dog Beds, Dog Grooming, Cat Supplies
    priority_clusters = ["Indoor Cats", "Puppy Care", "Dog Beds", "Dog Care", "Cat Supplies",
                         "Cat Toys", "Dog Toys", "Dog Supplies", "Dog Food", "Dog Harnesses",
                         "Dog Health", "Dog Training", "Pet Care General", "Product Reviews",
                         "Uncategorized"]
    roadmap_path = os.path.join(OUTPUT_BH, "cluster_roadmaps_v2.csv")
    with open(roadmap_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["cluster", "current_avg", "target_avg", "action_required",
                         "posts_affected", "estimated_lift", "priority"])

        priority_rank = 1
        for pc in priority_clusters:
            if pc not in clusters:
                continue
            cluster_posts = clusters[pc]
            bd_scores_list = [p["bd"]["best_answer_score"] for p in cluster_posts]
            current_avg = round(sum(bd_scores_list) / len(bd_scores_list), 1)
            target_avg = 80.0

            if current_avg >= target_avg:
                gap = 0
            else:
                gap = target_avg - current_avg

            # Identify posts below target
            below_target = [p for p in cluster_posts if p["bd"]["best_answer_score"] < target_avg]

            # Find most common weakest dimension
            dim_counts = defaultdict(int)
            for p in below_target:
                dims = {k: v for k, v in p["bd"].items() if k != "best_answer_score"}
                weakest = min(dims, key=dims.get)
                dim_counts[weakest] += 1

            if dim_counts:
                most_common_weakness = max(dim_counts, key=dim_counts.get)
            else:
                most_common_weakness = "none"

            actions_map = {
                "directness": f"Rewrite opening paragraphs of {len(below_target)} posts with direct answers",
                "usefulness": f"Add actionable guidance (steps, prices, measurements) to {len(below_target)} posts",
                "completeness": f"Add FAQ + glossary + comparison sections to {len(below_target)} posts",
                "practical_guidance": f"Add UK prices/measurements/timelines to {len(below_target)} posts",
                "comparison_richness": f"Add comparison tables (5+ rows) to {len(below_target)} posts",
                "trust_depth": f"Add UK org citations (RSPCA/PDSA/BVA) to {len(below_target)} posts",
                "extractability": f"Add At a Glance + Key Terms + FAQ sections to {len(below_target)} posts",
                "citation_confidence": f"Add evidence-based references to {len(below_target)} posts",
                "none": "Cluster at target; maintain quality",
            }

            estimated_lift = round(gap * 0.7, 1)  # Realistic 70% of theoretical gap closure

            writer.writerow([
                pc, current_avg, target_avg,
                actions_map.get(most_common_weakness, f"Improve {most_common_weakness}"),
                len(below_target),
                estimated_lift,
                priority_rank,
            ])
            priority_rank += 1
    print(f"  Saved: {roadmap_path}")

    # ─── Generate Phase 10BJ CSVs ─────────────────────────────────────────

    print("Generating Phase 10BJ CSVs...")

    # authority_moat_scores.csv
    bj_path = os.path.join(OUTPUT_BJ, "authority_moat_scores.csv")
    with open(bj_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "title", "cluster", "glossary_depth", "trust_depth",
                         "practical_depth", "comparison_depth", "faq_depth",
                         "citation_confidence", "semantic_density", "authority_moat_score"])
        for s in sorted(all_scores, key=lambda x: -x["bj"]["authority_moat_score"]):
            writer.writerow([
                s["id"], s["title"], s["cluster"],
                s["bj"]["glossary_depth"], s["bj"]["trust_depth"],
                s["bj"]["practical_depth"], s["bj"]["comparison_depth"],
                s["bj"]["faq_depth"], s["bj"]["citation_confidence"],
                s["bj"]["semantic_density"], s["bj"]["authority_moat_score"],
            ])
    print(f"  Saved: {bj_path}")

    # authority_moat_leaderboard.csv
    sorted_bj = sorted(all_scores, key=lambda x: -x["bj"]["authority_moat_score"])
    bj_leader_path = os.path.join(OUTPUT_BJ, "authority_moat_leaderboard.csv")
    with open(bj_leader_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "id", "title", "cluster", "authority_moat_score",
                         "strongest_moat", "weakest_moat"])
        for rank, s in enumerate(sorted_bj, 1):
            dims = {k: v for k, v in s["bj"].items() if k != "authority_moat_score"}
            strongest = max(dims, key=dims.get)
            weakest = min(dims, key=dims.get)
            writer.writerow([
                rank, s["id"], s["title"], s["cluster"],
                s["bj"]["authority_moat_score"], strongest, weakest,
            ])
    print(f"  Saved: {bj_leader_path}")

    # ─── Summary ──────────────────────────────────────────────────────────

    print("\n" + "=" * 70)
    print("SCORING COMPLETE — SUMMARY")
    print("=" * 70)

    print(f"\nTotal posts scored: {len(all_scores)}")
    print(f"Clusters found: {len(clusters)}")

    # BD summary
    all_bd = [s["bd"]["best_answer_score"] for s in all_scores]
    print(f"\n--- Phase 10BD: Best Answer Scores ---")
    print(f"  Average: {round(sum(all_bd)/len(all_bd), 1)}")
    print(f"  Median:  {sorted(all_bd)[len(all_bd)//2]}")
    print(f"  Min:     {min(all_bd)}")
    print(f"  Max:     {max(all_bd)}")
    print(f"  Above 80: {sum(1 for s in all_bd if s >= 80)}")
    print(f"  Below 60: {sum(1 for s in all_bd if s < 60)}")

    # BJ summary
    all_bj = [s["bj"]["authority_moat_score"] for s in all_scores]
    print(f"\n--- Phase 10BJ: Authority Moat Scores ---")
    print(f"  Average: {round(sum(all_bj)/len(all_bj), 1)}")
    print(f"  Median:  {sorted(all_bj)[len(all_bj)//2]}")
    print(f"  Min:     {min(all_bj)}")
    print(f"  Max:     {max(all_bj)}")

    # BH cluster summary
    print(f"\n--- Phase 10BH: Cluster Dominance ---")
    for cs in cluster_stats:
        status = "OK" if cs["avg_score"] >= 80 else "NEEDS WORK" if cs["avg_score"] >= 60 else "CRITICAL"
        print(f"  {cs['cluster']:20s} avg={cs['avg_score']:5.1f} posts={cs['post_count']:3d} [{status}]")

    print(f"\n--- Output Files ---")
    print(f"  {bd_path}")
    print(f"  {leaderboard_path}")
    print(f"  {upgrades_path}")
    print(f"  {dom_path}")
    print(f"  {roadmap_path}")
    print(f"  {bj_path}")
    print(f"  {bj_leader_path}")

    return all_scores


if __name__ == "__main__":
    process_all()
