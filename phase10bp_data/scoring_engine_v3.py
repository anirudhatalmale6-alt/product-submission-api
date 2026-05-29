#!/usr/bin/env python3
"""
PetHub Online - Phase 10BP/10BQ/10BR/10BS Scoring Engine v3
============================================================
Four integrated scoring systems using READ-ONLY WordPress API access:
  - 10BP: Cluster Dominance Program v3
  - 10BQ: Authority Moat Expansion Scoring (7 dimensions)
  - 10BR: AI Citation Superiority Scoring
  - 10BS: Topical Ownership Engine

All API access is GET-only via curl subprocess calls.
"""

import subprocess
import json
import csv
import re
import os
import sys
from collections import defaultdict
from html.parser import HTMLParser
import html

# ── Configuration ──────────────────────────────────────────────────────────
WP_API = "https://pethubonline.com/wp-json/wp/v2"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"

BASE_DIR = "/var/lib/freelancer/projects/40416335"
BP_DIR = os.path.join(BASE_DIR, "phase10bp_data")
BQ_DIR = os.path.join(BASE_DIR, "phase10bq_data")
BR_DIR = os.path.join(BASE_DIR, "phase10br_data")
BS_DIR = os.path.join(BASE_DIR, "phase10bs_data")

for d in [BP_DIR, BQ_DIR, BR_DIR, BS_DIR]:
    os.makedirs(d, exist_ok=True)


# ── HTML Utilities ─────────────────────────────────────────────────────────
class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
    def handle_data(self, data):
        self.text_parts.append(data)
    def get_text(self):
        return " ".join(self.text_parts)

def strip_html(html_content):
    s = HTMLStripper()
    s.feed(html.unescape(html_content))
    return s.get_text()

def word_count(text):
    return len(text.split())


# ── API Fetching ───────────────────────────────────────────────────────────
def fetch_api(endpoint, params=""):
    url = f"{WP_API}/{endpoint}?{params}" if params else f"{WP_API}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", f"{WP_USER}:{WP_PASS}", url],
        capture_output=True, text=True, timeout=60
    )
    return json.loads(result.stdout)

def fetch_all_posts():
    """Fetch all published posts with content."""
    all_posts = []
    page = 1
    while True:
        url = f"{WP_API}/posts?per_page=100&page={page}&_fields=id,title,content,categories,tags"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", f"{WP_USER}:{WP_PASS}", url],
            capture_output=True, text=True, timeout=60
        )
        data = json.loads(result.stdout)
        if not data or isinstance(data, dict):
            break
        all_posts.extend(data)
        if len(data) < 100:
            break
        page += 1
    return all_posts

def fetch_categories():
    """Fetch all categories."""
    all_cats = []
    page = 1
    while True:
        url = f"{WP_API}/categories?per_page=100&page={page}"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", f"{WP_USER}:{WP_PASS}", url],
            capture_output=True, text=True, timeout=60
        )
        data = json.loads(result.stdout)
        if not data or isinstance(data, dict):
            break
        all_cats.extend(data)
        if len(data) < 100:
            break
        page += 1
    return {c['id']: html.unescape(c['name']) for c in all_cats}


# ── UK Authority References ───────────────────────────────────────────────
UK_ORGS = [
    "rspca", "pdsa", "bva", "rcvs", "kennel club", "the kennel club",
    "cats protection", "blue cross", "battersea", "dogs trust",
    "pet food manufacturers", "pfma", "defra", "uk gov",
    "british veterinary", "royal veterinary", "animal welfare act",
    "pet industry federation", "uk pet food", "veterinary medicines directorate",
    "animal health", "vet record", "veterinary record", "bmj vet",
    "wood green", "mayhew", "scottish spca", "sspca", "ulster spca",
    "international cat care", "fab", "feline advisory bureau",
    "animal behaviour", "apbc", "association of pet behaviour",
    "pet plan", "petplan", "pet insurance", "vet charity",
    "people's dispensary", "animal welfare foundation",
    "british small animal veterinary", "bsava",
    "european pet food", "fediaf"
]

METHODOLOGY_TERMS = [
    "evidence-based", "evidence based", "peer-reviewed", "peer reviewed",
    "clinical study", "clinical trial", "research shows", "studies show",
    "according to research", "published guidance", "systematic review",
    "meta-analysis", "randomised", "randomized", "double-blind",
    "controlled trial", "longitudinal study", "cohort study",
    "veterinary guidance", "clinical guidance", "vet-recommended",
    "scientifically", "research-backed", "evidence suggests"
]

WELFARE_TERMS = [
    "five freedoms", "animal welfare", "duty of care", "welfare act",
    "welfare standards", "welfare needs", "responsible ownership",
    "breed-specific legislation", "microchipping", "neutering", "spaying",
    "pet welfare", "animal cruelty", "responsible breeding",
    "welfare assessment", "quality of life", "end of life"
]

EDITORIAL_TERMS = [
    "editorial", "fact-checked", "fact checked", "reviewed by",
    "medically reviewed", "vet-reviewed", "veterinary reviewed",
    "last updated", "corrections policy", "editorial standards",
    "disclosure", "affiliate disclosure", "transparency",
    "research standards", "our methodology", "how we research"
]

REGULATORY_TERMS = [
    "animal welfare act", "dangerous dogs act", "pet travel scheme",
    "microchipping regulations", "breeding regulations", "defra",
    "trading standards", "consumer rights", "veterinary medicines",
    "controlled drugs", "prescription diet", "vmd",
    "pet animals act", "animal boarding", "animal activities"
]


# ── Content Analysis Functions ─────────────────────────────────────────────
def count_pattern_matches(text, patterns):
    """Count unique pattern matches in text (case-insensitive)."""
    text_lower = text.lower()
    return sum(1 for p in patterns if p.lower() in text_lower)

def count_tables(html_content):
    """Count HTML tables and their rows."""
    tables = re.findall(r'<table[^>]*>(.*?)</table>', html_content, re.DOTALL | re.IGNORECASE)
    total_rows = 0
    for table in tables:
        rows = re.findall(r'<tr[^>]*>', table, re.IGNORECASE)
        total_rows += len(rows)
    return len(tables), total_rows

def count_comparison_types(html_content):
    """Detect variety of comparison types."""
    text_lower = html_content.lower()
    types = 0
    if re.search(r'<table', text_lower): types += 1  # table comparison
    if re.search(r'vs\.?|versus|compared to|comparison', text_lower): types += 1  # vs comparison
    if re.search(r'pros?\s*(and|&)\s*cons?', text_lower): types += 1  # pros/cons
    if re.search(r'advantage|disadvantage|benefit|drawback', text_lower): types += 1  # adv/disadv
    if re.search(r'rating|score|rank|star', text_lower): types += 1  # rating
    if re.search(r'budget|mid.range|premium|price.range', text_lower): types += 1  # price tiers
    if re.search(r'best for|ideal for|suitable for|recommended for', text_lower): types += 1  # use-case
    return types

def count_prices(text):
    """Count UK price mentions (£ symbol)."""
    return len(re.findall(r'£\d+', text))

def count_measurements(text):
    """Count measurement mentions."""
    return len(re.findall(r'\d+\s*(?:cm|mm|kg|g|ml|l|inches?|feet|ft|oz|lbs?|metres?|meters?)', text, re.IGNORECASE))

def count_timelines(text):
    """Count timeline/duration mentions."""
    return len(re.findall(r'\d+\s*(?:days?|weeks?|months?|years?|hours?|minutes?|mins?)', text, re.IGNORECASE))

def count_steps(html_content):
    """Count step-by-step instruction patterns."""
    steps = len(re.findall(r'step\s*\d+|step\s*[a-z]:|^\s*\d+\.\s', html_content, re.IGNORECASE | re.MULTILINE))
    ordered_lists = len(re.findall(r'<ol[^>]*>', html_content, re.IGNORECASE))
    return steps + ordered_lists * 3  # estimate 3 steps per ol

def count_breed_specifics(text):
    """Count breed-specific mentions."""
    breed_patterns = [
        r'labrador', r'golden retriever', r'german shepherd', r'bulldog',
        r'poodle', r'beagle', r'rottweiler', r'dachshund', r'boxer',
        r'yorkshire', r'spaniel', r'husky', r'chihuahua', r'pug',
        r'border collie', r'jack russell', r'staff', r'whippet',
        r'greyhound', r'terrier', r'setter', r'pointer', r'retriever',
        r'persian', r'siamese', r'bengal', r'british shorthair',
        r'maine coon', r'ragdoll', r'sphynx', r'abyssinian',
        r'small breed', r'large breed', r'medium breed', r'giant breed',
        r'toy breed', r'working breed', r'herding breed', r'sporting breed',
        r'brachycephalic', r'flat.faced'
    ]
    text_lower = text.lower()
    return sum(1 for p in breed_patterns if re.search(p, text_lower))

def count_headings(html_content):
    """Count and categorize headings."""
    h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', html_content, re.IGNORECASE | re.DOTALL)
    h3s = re.findall(r'<h3[^>]*>(.*?)</h3>', html_content, re.IGNORECASE | re.DOTALL)
    h4s = re.findall(r'<h4[^>]*>(.*?)</h4>', html_content, re.IGNORECASE | re.DOTALL)
    return len(h2s), len(h3s), len(h4s), [strip_html(h) for h in h2s + h3s]

def has_section(html_content, *keywords):
    """Check if content has a section matching any keyword."""
    headings = re.findall(r'<h[2-4][^>]*>(.*?)</h[2-4]>', html_content, re.IGNORECASE | re.DOTALL)
    text_lower = html_content.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            return True
    return False

def count_faq_items(html_content):
    """Count FAQ question/answer pairs."""
    # Check for FAQ schema blocks or FAQ headings
    faq_count = len(re.findall(r'<dt|class="faq|wp-block-yoast-faq|<details|question.*?answer',
                                html_content, re.IGNORECASE))
    # Also check Q: patterns
    faq_count += len(re.findall(r'<strong>[^<]*\?</strong>', html_content))
    # Check for explicit FAQ section
    if has_section(html_content, 'frequently asked', 'faq'):
        faq_count = max(faq_count, 3)
    return faq_count

def count_block_types(html_content):
    """Count variety of WordPress block types present."""
    block_types = set()
    if '<p ' in html_content or '<p>' in html_content:
        block_types.add('paragraph')
    if re.search(r'<h[1-6]', html_content, re.IGNORECASE):
        block_types.add('heading')
    if '<table' in html_content.lower():
        block_types.add('table')
    if '<ul' in html_content.lower() or '<ol' in html_content.lower():
        block_types.add('list')
    if '<img' in html_content.lower():
        block_types.add('image')
    if '<blockquote' in html_content.lower():
        block_types.add('quote')
    if 'wp-block-group' in html_content:
        block_types.add('group')
    if 'wp-block-columns' in html_content:
        block_types.add('columns')
    if 'wp-block-separator' in html_content or '<hr' in html_content.lower():
        block_types.add('separator')
    if 'wp-block-buttons' in html_content or 'wp-block-button' in html_content:
        block_types.add('button')
    if '<details' in html_content.lower():
        block_types.add('details')
    if '<figure' in html_content.lower():
        block_types.add('figure')
    if '<strong>' in html_content and ('at a glance' in html_content.lower() or
                                        'key terms' in html_content.lower()):
        block_types.add('info-box')
    if re.search(r'has-background|has-border', html_content):
        block_types.add('styled-group')
    if '<a ' in html_content.lower():
        block_types.add('links')
    if 'wp-block-embed' in html_content:
        block_types.add('embed')
    return block_types

def count_defined_terms(html_content):
    """Count glossary/defined terms."""
    # Bold term followed by colon or dash pattern
    terms = re.findall(r'<strong>[^<]{3,50}</strong>\s*[:–—-]', html_content)
    # Also check for dt/dd patterns
    terms2 = re.findall(r'<dt[^>]*>[^<]+</dt>', html_content, re.IGNORECASE)
    return len(terms) + len(terms2)

def count_external_links(html_content):
    """Count and categorize external links."""
    links = re.findall(r'href="(https?://[^"]+)"', html_content)
    external = [l for l in links if 'pethubonline.com' not in l]
    uk_links = [l for l in external if any(d in l.lower() for d in [
        '.org.uk', '.gov.uk', '.ac.uk', '.co.uk', 'rspca', 'pdsa',
        'bva', 'rcvs', 'kennel', 'cats.org', 'bluecross', 'dogstrust'
    ])]
    return len(external), len(uk_links)

def count_internal_links(html_content):
    """Count internal links."""
    return len(re.findall(r'href="https?://pethubonline\.com[^"]*"', html_content))


# ── Post Analysis ──────────────────────────────────────────────────────────
def analyze_post(post):
    """Complete analysis of a single post, returning all metrics."""
    content_html = post['content']['rendered']
    content_text = strip_html(content_html)
    text_lower = content_text.lower()
    html_lower = content_html.lower()
    wc = word_count(content_text)

    # Basic counts
    tables, table_rows = count_tables(content_html)
    comparison_types = count_comparison_types(content_html)
    prices = count_prices(content_text)
    measurements = count_measurements(content_text)
    timelines = count_timelines(content_text)
    steps = count_steps(content_html)
    breeds = count_breed_specifics(content_text)
    h2_count, h3_count, h4_count, heading_texts = count_headings(content_html)
    faq_items = count_faq_items(content_html)
    block_types = count_block_types(content_html)
    defined_terms = count_defined_terms(content_html)
    ext_links, uk_links = count_external_links(content_html)
    int_links = count_internal_links(content_html)

    # UK org references
    uk_org_count = count_pattern_matches(content_text, UK_ORGS)
    methodology_count = count_pattern_matches(content_text, METHODOLOGY_TERMS)
    welfare_count = count_pattern_matches(content_text, WELFARE_TERMS)
    editorial_count = count_pattern_matches(content_text, EDITORIAL_TERMS)
    regulatory_count = count_pattern_matches(content_text, REGULATORY_TERMS)

    # Section presence
    has_glance = has_section(content_html, 'at a glance', 'at-a-glance')
    has_faq = has_section(content_html, 'faq', 'frequently asked')
    has_key_terms = has_section(content_html, 'key terms', 'glossary', 'terminology')
    has_takeaways = has_section(content_html, 'key takeaways', 'takeaway', 'summary')
    has_quick_answer = has_section(content_html, 'quick answer')

    # Decision pathway elements
    has_troubleshooting = has_section(content_html, 'troubleshoot', 'common problem', 'common issue', 'warning sign')
    has_scenarios = has_section(content_html, 'scenario', 'if your', 'when to', 'situation')
    has_evaluation = has_section(content_html, 'how to choose', 'what to look for', 'evaluation', 'criteria', 'checklist')
    has_decision_path = has_section(content_html, 'decision', 'flowchart', 'which.*right', 'best.*for')

    return {
        'word_count': wc,
        'tables': tables,
        'table_rows': table_rows,
        'comparison_types': comparison_types,
        'prices': prices,
        'measurements': measurements,
        'timelines': timelines,
        'steps': steps,
        'breeds': breeds,
        'h2_count': h2_count,
        'h3_count': h3_count,
        'h4_count': h4_count,
        'heading_texts': heading_texts,
        'faq_items': faq_items,
        'block_types': len(block_types),
        'block_type_names': block_types,
        'defined_terms': defined_terms,
        'ext_links': ext_links,
        'uk_links': uk_links,
        'int_links': int_links,
        'uk_org_count': uk_org_count,
        'methodology_count': methodology_count,
        'welfare_count': welfare_count,
        'editorial_count': editorial_count,
        'regulatory_count': regulatory_count,
        'has_glance': has_glance,
        'has_faq': has_faq,
        'has_key_terms': has_key_terms,
        'has_takeaways': has_takeaways,
        'has_quick_answer': has_quick_answer,
        'has_troubleshooting': has_troubleshooting,
        'has_scenarios': has_scenarios,
        'has_evaluation': has_evaluation,
        'has_decision_path': has_decision_path,
    }


# ── Scoring Functions ──────────────────────────────────────────────────────
def clamp(val, lo=0, hi=100):
    return max(lo, min(hi, val))

# --- Phase 10BP: Cluster Dominance Scores ---
def score_practical(m):
    """Practical score: step-by-step, UK prices, measurements, timelines."""
    s = 0
    s += min(25, m['steps'] * 5)              # steps (max 25)
    s += min(20, m['prices'] * 3)             # UK prices (max 20)
    s += min(20, m['measurements'] * 3)       # measurements (max 20)
    s += min(15, m['timelines'] * 3)          # timelines (max 15)
    s += min(10, m['breeds'] * 2)             # breed specifics (max 10)
    s += min(10, m['int_links'] * 2)          # internal link utility (max 10)
    return clamp(s)

def score_decision(m):
    """Decision score: evaluation frameworks, troubleshooting, scenarios."""
    s = 0
    s += 20 if m['has_evaluation'] else 0
    s += 20 if m['has_troubleshooting'] else 0
    s += 15 if m['has_scenarios'] else 0
    s += 15 if m['has_decision_path'] else 0
    s += min(15, m['comparison_types'] * 3)   # comparison variety
    s += min(15, (m['h2_count'] + m['h3_count']) * 1)  # structural depth for guidance
    return clamp(s)

def score_citation(m):
    """Citation score: UK org references, authority, evidence specificity."""
    s = 0
    s += min(30, m['uk_org_count'] * 5)       # UK org mentions (max 30)
    s += min(20, m['uk_links'] * 5)           # UK authority links (max 20)
    s += min(20, m['ext_links'] * 3)          # external links breadth (max 20)
    s += min(15, m['methodology_count'] * 5)  # methodology references (max 15)
    s += min(15, m['regulatory_count'] * 5)   # regulatory refs (max 15)
    return clamp(s)

def score_comparison(m):
    """Comparison score: tables, rows, variety."""
    s = 0
    s += min(35, m['tables'] * 12)            # table count (max 35)
    s += min(30, m['table_rows'] * 2)         # row depth (max 30)
    s += min(35, m['comparison_types'] * 5)   # comparison variety (max 35)
    return clamp(s)

def score_trust(m):
    """Trust score: methodology, welfare, editorial, source diversity."""
    s = 0
    s += min(25, m['methodology_count'] * 5)  # methodology refs
    s += min(25, m['welfare_count'] * 5)      # welfare refs
    s += min(25, m['editorial_count'] * 5)    # editorial standards
    s += min(25, (m['uk_org_count'] + m['ext_links']) * 2)  # source diversity
    return clamp(s)

def score_extraction(m):
    """Extraction score: At a Glance, FAQ, Key Terms, Key Takeaways, Quick Answer."""
    s = 0
    s += 20 if m['has_glance'] else 0
    s += 20 if m['has_faq'] else 0
    s += 20 if m['has_key_terms'] else 0
    s += 20 if m['has_takeaways'] else 0
    s += 20 if m['has_quick_answer'] else 0
    return clamp(s)


# --- Phase 10BQ: Authority Moat 7-Dimension Scores ---
def moat_glossary(m):
    """Glossary moat: defined terms count, integration quality."""
    terms = m['defined_terms']
    s = min(60, terms * 4)                    # term count (max 60)
    s += 20 if m['has_key_terms'] else 0      # dedicated glossary section
    s += min(20, m['h3_count'] * 2)           # organizational depth
    return clamp(s)

def moat_trust(m):
    """Trust moat: UK org variety, methodology, standards, evidence."""
    s = 0
    s += min(25, m['uk_org_count'] * 4)       # UK org variety
    s += min(25, m['methodology_count'] * 5)  # methodology mentions
    s += min(25, m['editorial_count'] * 5)    # standards refs
    s += min(25, (m['welfare_count'] + m['regulatory_count']) * 4)  # evidence citations
    return clamp(s)

def moat_comparison(m):
    """Comparison moat: table count, row quality, type variety."""
    s = 0
    s += min(35, m['tables'] * 12)            # table count
    s += min(30, m['table_rows'] * 2)         # row quality
    s += min(35, m['comparison_types'] * 5)   # type variety
    return clamp(s)

def moat_practical(m):
    """Practical moat: UK prices, measurements, timelines, steps, breed specifics."""
    s = 0
    s += min(20, m['prices'] * 3)             # UK prices
    s += min(20, m['measurements'] * 3)       # measurements
    s += min(20, m['timelines'] * 3)          # timelines
    s += min(20, m['steps'] * 4)              # step counts
    s += min(20, m['breeds'] * 3)             # breed specifics
    return clamp(s)

def moat_educational(m):
    """Educational moat: FAQ depth, At a Glance quality, Takeaways actionability."""
    s = 0
    s += min(25, m['faq_items'] * 5)          # FAQ depth
    s += 25 if m['has_glance'] else 0         # At a Glance
    s += 25 if m['has_takeaways'] else 0      # Key Takeaways
    s += 25 if m['has_quick_answer'] else 0   # Quick Answer
    return clamp(s)

def moat_citation(m):
    """Citation moat: source variety, authority level, UK specificity, regulatory."""
    s = 0
    s += min(25, m['ext_links'] * 3)          # source variety
    s += min(25, m['uk_links'] * 5)           # authority level (UK)
    s += min(25, m['uk_org_count'] * 4)       # UK specificity
    s += min(25, m['regulatory_count'] * 5)   # regulatory refs
    return clamp(s)

def moat_structural(m):
    """Structural moat: block variety, content organization."""
    s = 0
    s += min(50, m['block_types'] * 5)        # block variety
    heading_depth = m['h2_count'] + m['h3_count'] + m['h4_count']
    s += min(30, heading_depth * 2)           # heading organization
    s += min(20, m['int_links'] * 3)          # internal linking as organization
    return clamp(s)


# --- Phase 10BR: AI Citation Preference Scores ---
def cite_reference_quality(m):
    """How authoritative are the sources? UK gov/vet bodies score highest."""
    s = 0
    s += min(35, m['uk_links'] * 7)           # UK authority links (high weight)
    s += min(25, m['uk_org_count'] * 4)       # UK org mentions
    s += min(20, m['regulatory_count'] * 5)   # regulatory refs
    s += min(20, m['methodology_count'] * 5)  # methodology backing
    return clamp(s)

def cite_comparison_usefulness(m):
    """Can AI extract useful comparison data from tables?"""
    s = 0
    s += min(30, m['tables'] * 10)            # table presence
    s += min(30, m['table_rows'] * 2)         # data richness
    s += min(20, m['comparison_types'] * 4)   # extraction variety
    s += min(20, m['prices'] * 3)             # quantitative data
    return clamp(s)

def cite_practical_specificity(m):
    """Specific numbers AI can quote."""
    s = 0
    s += min(25, m['prices'] * 4)             # prices
    s += min(25, m['measurements'] * 4)       # measurements
    s += min(25, m['timelines'] * 4)          # timelines
    s += min(25, m['breeds'] * 3)             # breed-specific data
    return clamp(s)

def cite_extractability(m):
    """Clean structure AI can parse."""
    s = 0
    s += min(25, m['block_types'] * 3)        # structural variety
    s += min(25, (m['h2_count'] + m['h3_count']) * 2)  # heading structure
    s += min(25, m['defined_terms'] * 3)      # bold definitions
    s += min(25, m['tables'] * 8)             # table parseability
    return clamp(s)

def cite_trust_depth(m):
    """Depth of trust signals."""
    s = 0
    total_trust = (m['methodology_count'] + m['welfare_count'] +
                   m['editorial_count'] + m['regulatory_count'])
    s += min(40, total_trust * 4)             # trust signal breadth
    s += min(30, m['uk_org_count'] * 4)       # org depth
    s += min(30, m['uk_links'] * 6)           # verifiable links
    return clamp(s)

def cite_summary_usefulness(m):
    """How good are At a Glance/Key Takeaways for AI extraction?"""
    s = 0
    s += 25 if m['has_glance'] else 0
    s += 25 if m['has_takeaways'] else 0
    s += 25 if m['has_quick_answer'] else 0
    s += 15 if m['has_faq'] else 0
    s += min(10, m['faq_items'] * 2)          # FAQ depth bonus
    return clamp(s)


# ── Cluster Assignment ─────────────────────────────────────────────────────
def assign_cluster(post, cat_map):
    """Assign primary cluster name based on categories."""
    cats = post.get('categories', [])
    if not cats:
        return "Uncategorized"

    # Priority order for cluster assignment
    priority_cats = [
        1467,  # Dog Food
        1401,  # Dog Beds
        1441,  # Dog Toys
        1422,  # Dog Harnesses
        1450,  # Dog Health
        1489,  # Dog Care
        1474,  # Training Supplies
        1459,  # Cat Toys
        1413,  # Indoor Cats
        1377,  # Cat Supplies
        1442,  # Puppy Care
        1376,  # Dog Supplies
        1396,  # Pet Beds
        1391,  # Pet Health
        1397,  # Pet Care
        1379,  # Product Reviews
        1380,  # Buying Guides
        1455,  # Orthopaedic Care
        1460,  # Interactive Toys
        1487,  # Health & Wellness
    ]

    for pc in priority_cats:
        if pc in cats:
            return cat_map.get(pc, "Uncategorized")

    # Fallback: use first category
    return cat_map.get(cats[0], "Uncategorized")

# Map similar clusters together for better grouping
CLUSTER_MERGE = {
    "Health & Wellness": "Dog Health",
    "Pet Health": "Dog Health",
    "Pet Beds": "Dog Beds",
    "Orthopaedic Care": "Dog Health",
    "Interactive Toys": "Cat Toys",
    "Buying Guides": "Product Reviews",
}

def normalize_cluster(cluster):
    return CLUSTER_MERGE.get(cluster, cluster)


# ── Main Scoring Pipeline ─────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("PetHub Online - Phase 10BP/BQ/BR/BS Scoring Engine v3")
    print("=" * 70)

    # 1. Fetch data
    print("\n[1/6] Fetching posts from WordPress API...")
    posts = fetch_all_posts()
    print(f"  -> {len(posts)} posts fetched")

    print("[2/6] Fetching categories...")
    cat_map = fetch_categories()
    print(f"  -> {len(cat_map)} categories fetched")

    # 3. Analyze all posts
    print("[3/6] Analyzing all posts...")
    post_data = []
    for i, post in enumerate(posts):
        title = html.unescape(post['title']['rendered'])
        pid = post['id']
        cluster = normalize_cluster(assign_cluster(post, cat_map))
        metrics = analyze_post(post)

        # Calculate all scores
        p_score = score_practical(metrics)
        d_score = score_decision(metrics)
        ci_score = score_citation(metrics)
        co_score = score_comparison(metrics)
        t_score = score_trust(metrics)
        e_score = score_extraction(metrics)

        # Cluster dominance weighted average
        cd_score = round(
            p_score * 0.25 + d_score * 0.15 + ci_score * 0.20 +
            co_score * 0.15 + t_score * 0.10 + e_score * 0.15, 1
        )

        # Authority moat 7 dimensions
        g_moat = moat_glossary(metrics)
        tr_moat = moat_trust(metrics)
        cm_moat = moat_comparison(metrics)
        pr_moat = moat_practical(metrics)
        ed_moat = moat_educational(metrics)
        ct_moat = moat_citation(metrics)
        st_moat = moat_structural(metrics)
        authority_moat_v2 = round(
            (g_moat + tr_moat + cm_moat + pr_moat + ed_moat + ct_moat + st_moat) / 7, 1
        )

        # AI citation preference scores
        ref_q = cite_reference_quality(metrics)
        comp_u = cite_comparison_usefulness(metrics)
        prac_s = cite_practical_specificity(metrics)
        extr = cite_extractability(metrics)
        trust_d = cite_trust_depth(metrics)
        summ_u = cite_summary_usefulness(metrics)
        citation_pref = round(
            ref_q * 0.20 + comp_u * 0.15 + prac_s * 0.25 +
            extr * 0.15 + trust_d * 0.10 + summ_u * 0.15, 1
        )

        post_data.append({
            'id': pid,
            'title': title,
            'cluster': cluster,
            'word_count': metrics['word_count'],
            'metrics': metrics,
            # BP scores
            'practical_score': p_score,
            'decision_score': d_score,
            'citation_score': ci_score,
            'comparison_score': co_score,
            'trust_score': t_score,
            'extraction_score': e_score,
            'cluster_dominance_score': cd_score,
            # BQ moat scores
            'glossary_moat': g_moat,
            'trust_moat': tr_moat,
            'comparison_moat': cm_moat,
            'practical_moat': pr_moat,
            'educational_moat': ed_moat,
            'citation_moat': ct_moat,
            'structural_moat': st_moat,
            'authority_moat_v2': authority_moat_v2,
            # BR citation preference
            'reference_quality': ref_q,
            'comparison_usefulness': comp_u,
            'practical_specificity': prac_s,
            'extractability': extr,
            'trust_depth': trust_d,
            'summary_usefulness': summ_u,
            'citation_preference_score': citation_pref,
        })

        if (i + 1) % 20 == 0:
            print(f"  -> Analyzed {i + 1}/{len(posts)} posts...")

    print(f"  -> All {len(posts)} posts analyzed")

    # 4. Phase 10BP: Cluster Dominance
    print("\n[4/6] Phase 10BP: Cluster Dominance v3...")
    clusters = defaultdict(list)
    for pd in post_data:
        clusters[pd['cluster']].append(pd)

    cluster_rows = []
    for cluster_name, cposts in sorted(clusters.items(), key=lambda x: -len(x[1])):
        n = len(cposts)
        avg = lambda k: round(sum(p[k] for p in cposts) / n, 1)
        cluster_rows.append({
            'cluster': cluster_name,
            'post_count': n,
            'practical_score': avg('practical_score'),
            'decision_score': avg('decision_score'),
            'citation_score': avg('citation_score'),
            'comparison_score': avg('comparison_score'),
            'trust_score': avg('trust_score'),
            'extraction_score': avg('extraction_score'),
            'cluster_dominance_score': avg('cluster_dominance_score'),
        })

    # Write cluster_dominance_v3.csv
    with open(os.path.join(BP_DIR, "cluster_dominance_v3.csv"), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=[
            'cluster', 'post_count', 'practical_score', 'decision_score',
            'citation_score', 'comparison_score', 'trust_score', 'extraction_score',
            'cluster_dominance_score'
        ])
        w.writeheader()
        for r in sorted(cluster_rows, key=lambda x: -x['cluster_dominance_score']):
            w.writerow(r)

    # Write cluster_gaps_v3.csv
    gap_rows = []
    TARGET = 75
    for cr in cluster_rows:
        current = cr['cluster_dominance_score']
        gap = round(max(0, TARGET - current), 1)

        # Find weakest dimension
        dims = {
            'practical_score': cr['practical_score'],
            'decision_score': cr['decision_score'],
            'citation_score': cr['citation_score'],
            'comparison_score': cr['comparison_score'],
            'trust_score': cr['trust_score'],
            'extraction_score': cr['extraction_score'],
        }
        weakest_dim = min(dims, key=dims.get)
        weakest_val = dims[weakest_dim]

        # Generate top 3 actions based on weakest dimensions
        sorted_dims = sorted(dims.items(), key=lambda x: x[1])
        actions = []
        for dim_name, dim_val in sorted_dims[:3]:
            if dim_name == 'practical_score' and dim_val < 60:
                actions.append("Add UK prices, measurements, timelines, and step-by-step instructions")
            elif dim_name == 'decision_score' and dim_val < 60:
                actions.append("Add evaluation frameworks, troubleshooting guides, and decision pathways")
            elif dim_name == 'citation_score' and dim_val < 60:
                actions.append("Add UK org references (RSPCA, PDSA, BVA) and authority citations")
            elif dim_name == 'comparison_score' and dim_val < 60:
                actions.append("Add comparison tables with pricing tiers and product evaluations")
            elif dim_name == 'trust_score' and dim_val < 60:
                actions.append("Add methodology references, welfare citations, and editorial standards")
            elif dim_name == 'extraction_score' and dim_val < 60:
                actions.append("Add At a Glance, FAQ, Key Terms, Key Takeaways sections")
            elif dim_val < 75:
                actions.append(f"Improve {dim_name.replace('_', ' ')} from {dim_val} toward 75+")
            else:
                actions.append(f"Maintain {dim_name.replace('_', ' ')} quality ({dim_val})")

        gap_rows.append({
            'cluster': cr['cluster'],
            'current_score': current,
            'target_score': TARGET,
            'gap': gap,
            'weakest_dimension': weakest_dim,
            'weakest_score': weakest_val,
            'top_3_actions': "; ".join(actions[:3]),
        })

    with open(os.path.join(BP_DIR, "cluster_gaps_v3.csv"), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=[
            'cluster', 'current_score', 'target_score', 'gap',
            'weakest_dimension', 'weakest_score', 'top_3_actions'
        ])
        w.writeheader()
        for r in sorted(gap_rows, key=lambda x: -x['gap']):
            w.writerow(r)

    print(f"  -> cluster_dominance_v3.csv: {len(cluster_rows)} clusters")
    print(f"  -> cluster_gaps_v3.csv: {len(gap_rows)} gap analyses")
    above_75 = sum(1 for cr in cluster_rows if cr['cluster_dominance_score'] >= 75)
    print(f"  -> Clusters above 75: {above_75}/{len(cluster_rows)}")

    # 5. Phase 10BQ: Authority Moat v2
    print("\n[5/6] Phase 10BQ: Authority Moat v2...")
    with open(os.path.join(BQ_DIR, "authority_moat_v2.csv"), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=[
            'id', 'title', 'cluster', 'glossary_moat', 'trust_moat',
            'comparison_moat', 'practical_moat', 'educational_moat',
            'citation_moat', 'structural_moat', 'authority_moat_v2'
        ])
        w.writeheader()
        for pd in sorted(post_data, key=lambda x: -x['authority_moat_v2']):
            w.writerow({
                'id': pd['id'],
                'title': pd['title'],
                'cluster': pd['cluster'],
                'glossary_moat': pd['glossary_moat'],
                'trust_moat': pd['trust_moat'],
                'comparison_moat': pd['comparison_moat'],
                'practical_moat': pd['practical_moat'],
                'educational_moat': pd['educational_moat'],
                'citation_moat': pd['citation_moat'],
                'structural_moat': pd['structural_moat'],
                'authority_moat_v2': pd['authority_moat_v2'],
            })

    avg_moat = round(sum(p['authority_moat_v2'] for p in post_data) / len(post_data), 1)
    top_moat = max(post_data, key=lambda x: x['authority_moat_v2'])
    print(f"  -> authority_moat_v2.csv: {len(post_data)} posts scored")
    print(f"  -> Average moat: {avg_moat}")
    print(f"  -> Top: {top_moat['title'][:50]} ({top_moat['authority_moat_v2']})")

    # 6. Phase 10BR: AI Citation Preference
    print("\n[5b/6] Phase 10BR: AI Citation Preference...")
    with open(os.path.join(BR_DIR, "citation_preference.csv"), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=[
            'id', 'title', 'cluster', 'reference_quality', 'comparison_usefulness',
            'practical_specificity', 'extractability', 'trust_depth',
            'summary_usefulness', 'citation_preference_score'
        ])
        w.writeheader()
        for pd in sorted(post_data, key=lambda x: -x['citation_preference_score']):
            w.writerow({
                'id': pd['id'],
                'title': pd['title'],
                'cluster': pd['cluster'],
                'reference_quality': pd['reference_quality'],
                'comparison_usefulness': pd['comparison_usefulness'],
                'practical_specificity': pd['practical_specificity'],
                'extractability': pd['extractability'],
                'trust_depth': pd['trust_depth'],
                'summary_usefulness': pd['summary_usefulness'],
                'citation_preference_score': pd['citation_preference_score'],
            })

    avg_cite = round(sum(p['citation_preference_score'] for p in post_data) / len(post_data), 1)
    top_cite = max(post_data, key=lambda x: x['citation_preference_score'])
    print(f"  -> citation_preference.csv: {len(post_data)} posts scored")
    print(f"  -> Average citation preference: {avg_cite}")
    print(f"  -> Top: {top_cite['title'][:50]} ({top_cite['citation_preference_score']})")

    # 7. Phase 10BS: Topical Ownership Engine
    print("\n[6/6] Phase 10BS: Topical Ownership Engine...")

    ownership_rows = []
    action_rows = []

    for cluster_name, cposts in sorted(clusters.items(), key=lambda x: -len(x[1])):
        n = len(cposts)
        avg_f = lambda k: round(sum(p[k] for p in cposts) / n, 1)

        # 1. dominance — average best answer quality (cluster dominance score)
        dominance = avg_f('cluster_dominance_score')

        # 2. saturation — heading/topic variety coverage
        all_headings = set()
        for p in cposts:
            for h in p['metrics']['heading_texts']:
                all_headings.add(h.lower().strip())
        unique_topics = len(all_headings)
        # Normalize: expect ~50 unique heading topics per well-saturated cluster
        saturation = clamp(round(min(100, (unique_topics / max(1, n * 5)) * 100), 1))

        # 3. authority_density — UK org refs per 1000 words
        total_words = sum(p['word_count'] for p in cposts)
        total_uk_orgs = sum(p['metrics']['uk_org_count'] for p in cposts)
        authority_density_raw = (total_uk_orgs / max(1, total_words)) * 1000
        authority_density = clamp(round(min(100, authority_density_raw * 10), 1))

        # 4. trust_intensity — unique trust signals per post
        avg_trust_signals = sum(
            p['metrics']['methodology_count'] + p['metrics']['welfare_count'] +
            p['metrics']['editorial_count'] + p['metrics']['regulatory_count']
            for p in cposts
        ) / n
        trust_intensity = clamp(round(min(100, avg_trust_signals * 6), 1))

        # 5. practical_usefulness — specific data points per post
        avg_data_points = sum(
            p['metrics']['prices'] + p['metrics']['measurements'] + p['metrics']['timelines']
            for p in cposts
        ) / n
        practical_usefulness = clamp(round(min(100, avg_data_points * 4), 1))

        # 6. citation_confidence — average citation score
        citation_confidence = avg_f('citation_score')

        # 7. moat_score — average authority moat across cluster
        moat_score = avg_f('authority_moat_v2')

        # 8. ai_visibility — average extraction score
        ai_visibility = avg_f('extraction_score')

        # Ownership score (equal weight across all 8 dimensions)
        ownership_score = round(
            (dominance + saturation + authority_density + trust_intensity +
             practical_usefulness + citation_confidence + moat_score + ai_visibility) / 8, 1
        )

        # Classification
        if ownership_score > 75:
            status = "OWNED"
        elif ownership_score >= 50:
            status = "CONTESTED"
        else:
            status = "WEAK"

        ownership_rows.append({
            'cluster': cluster_name,
            'dominance': dominance,
            'saturation': saturation,
            'authority_density': authority_density,
            'trust_intensity': trust_intensity,
            'practical_usefulness': practical_usefulness,
            'citation_confidence': citation_confidence,
            'moat_score': moat_score,
            'ai_visibility': ai_visibility,
            'ownership_score': ownership_score,
            'ownership_status': status,
        })

        # Gap and action analysis
        gap_to_owned = round(max(0, 75 - ownership_score), 1)

        dims_for_action = {
            'dominance': dominance,
            'saturation': saturation,
            'authority_density': authority_density,
            'trust_intensity': trust_intensity,
            'practical_usefulness': practical_usefulness,
            'citation_confidence': citation_confidence,
            'moat_score': moat_score,
            'ai_visibility': ai_visibility,
        }
        sorted_weak = sorted(dims_for_action.items(), key=lambda x: x[1])

        priorities = []
        for dim_name, dim_val in sorted_weak[:3]:
            if dim_name == 'dominance':
                priorities.append(f"Improve overall answer quality across cluster (current: {dim_val})")
            elif dim_name == 'saturation':
                priorities.append(f"Expand subtopic coverage with new posts (current: {dim_val})")
            elif dim_name == 'authority_density':
                priorities.append(f"Add more UK org references per post (current: {dim_val})")
            elif dim_name == 'trust_intensity':
                priorities.append(f"Deepen trust signals: methodology, welfare, editorial (current: {dim_val})")
            elif dim_name == 'practical_usefulness':
                priorities.append(f"Add specific UK prices, measurements, timelines (current: {dim_val})")
            elif dim_name == 'citation_confidence':
                priorities.append(f"Strengthen citation quality and UK authority links (current: {dim_val})")
            elif dim_name == 'moat_score':
                priorities.append(f"Build authority moat: glossary, comparisons, structure (current: {dim_val})")
            elif dim_name == 'ai_visibility':
                priorities.append(f"Add extraction blocks: At a Glance, FAQ, Key Takeaways (current: {dim_val})")

        # Estimate posts to fix (posts below 70 in cluster dominance score)
        posts_below_70 = sum(1 for p in cposts if p['cluster_dominance_score'] < 70)

        action_rows.append({
            'cluster': cluster_name,
            'ownership_status': status,
            'gap_to_owned': gap_to_owned,
            'top_3_priorities': "; ".join(priorities[:3]),
            'estimated_posts_to_fix': posts_below_70,
        })

    # Write topical_ownership.csv
    with open(os.path.join(BS_DIR, "topical_ownership.csv"), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=[
            'cluster', 'dominance', 'saturation', 'authority_density',
            'trust_intensity', 'practical_usefulness', 'citation_confidence',
            'moat_score', 'ai_visibility', 'ownership_score', 'ownership_status'
        ])
        w.writeheader()
        for r in sorted(ownership_rows, key=lambda x: -x['ownership_score']):
            w.writerow(r)

    # Write ownership_actions.csv
    with open(os.path.join(BS_DIR, "ownership_actions.csv"), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=[
            'cluster', 'ownership_status', 'gap_to_owned',
            'top_3_priorities', 'estimated_posts_to_fix'
        ])
        w.writeheader()
        for r in sorted(action_rows, key=lambda x: -x['gap_to_owned']):
            w.writerow(r)

    # Summary
    owned = sum(1 for r in ownership_rows if r['ownership_status'] == 'OWNED')
    contested = sum(1 for r in ownership_rows if r['ownership_status'] == 'CONTESTED')
    weak = sum(1 for r in ownership_rows if r['ownership_status'] == 'WEAK')

    print(f"  -> topical_ownership.csv: {len(ownership_rows)} clusters")
    print(f"  -> ownership_actions.csv: {len(action_rows)} action plans")
    print(f"  -> OWNED: {owned}, CONTESTED: {contested}, WEAK: {weak}")

    # Final summary
    print("\n" + "=" * 70)
    print("SCORING ENGINE v3 COMPLETE")
    print("=" * 70)
    print(f"\nPhase 10BP - Cluster Dominance v3:")
    print(f"  {BP_DIR}/cluster_dominance_v3.csv")
    print(f"  {BP_DIR}/cluster_gaps_v3.csv")
    print(f"\nPhase 10BQ - Authority Moat v2:")
    print(f"  {BQ_DIR}/authority_moat_v2.csv")
    print(f"\nPhase 10BR - AI Citation Preference:")
    print(f"  {BR_DIR}/citation_preference.csv")
    print(f"\nPhase 10BS - Topical Ownership:")
    print(f"  {BS_DIR}/topical_ownership.csv")
    print(f"  {BS_DIR}/ownership_actions.csv")
    print(f"\nScript: {BP_DIR}/scoring_engine_v3.py")

    # Top/bottom clusters
    print("\n--- Top 5 Clusters by Dominance ---")
    for r in sorted(cluster_rows, key=lambda x: -x['cluster_dominance_score'])[:5]:
        print(f"  {r['cluster']}: {r['cluster_dominance_score']} ({r['post_count']} posts)")

    print("\n--- Bottom 5 Clusters by Dominance ---")
    for r in sorted(cluster_rows, key=lambda x: x['cluster_dominance_score'])[:5]:
        print(f"  {r['cluster']}: {r['cluster_dominance_score']} ({r['post_count']} posts)")

    print(f"\n--- Ownership Summary ---")
    for r in sorted(ownership_rows, key=lambda x: -x['ownership_score']):
        print(f"  [{r['ownership_status']:9s}] {r['cluster']}: {r['ownership_score']}")


if __name__ == "__main__":
    main()
