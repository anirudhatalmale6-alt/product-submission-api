#!/usr/bin/env python3
"""
10AE-E: Citation Dominance Engine
pethubonline.com - WordPress Pet Supplies Blog (144 published posts)

PURPOSE: Optimize pages specifically for AI citation selection. Builds on 10AD-D
(avg citation confidence 36.8, 0 posts above 70) to generate specific actionable
plans to push clusters toward 70+ citation confidence.

Focus: Dog Food cluster (already at 53.8 — closest to 70) and all other clusters.
Generates per-post dominance scores, acceleration plans, and cluster roadmaps.
"""

import subprocess
import json
import csv
import re
import os
import sys
import html
import math
from collections import defaultdict

# ─── Configuration ───────────────────────────────────────────────────────────

WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase10ae_data"

# ─── Cluster Classification ─────────────────────────────────────────────────

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

CLUSTER_PRIORITY_ORDER = [
    "Dog Toys", "Dog Food", "Dog Beds", "Dog Harnesses", "Dog Health",
    "Dog Care", "Cat Toys", "Cat Supplies", "Puppy Care", "Dog Supplies",
    "Pet Care General", "Educational",
]

# Trusted reference domains for Reference Quality scoring
TRUSTED_DOMAINS = [
    "rspca.org", "bva.co.uk", "gov.uk", "pdsa.org",
    "battersea.org", "bluecross.org", "fediaf.org", "cats.org.uk",
]

# Dimension weights for overall citation confidence
DIMENSION_WEIGHTS = {
    "extractability": 0.15,
    "trust_reinforcement": 0.15,
    "comparison_usefulness": 0.10,
    "glossary_richness": 0.10,
    "educational_usefulness": 0.15,
    "answer_usefulness": 0.10,
    "practical_specificity": 0.10,
    "reference_quality": 0.10,
    "summary_usefulness": 0.05,
}

DIMENSION_LABELS = {
    "extractability": "Extractability",
    "trust_reinforcement": "Trust Reinforcement",
    "comparison_usefulness": "Comparison Usefulness",
    "glossary_richness": "Glossary Richness",
    "educational_usefulness": "Educational Clarity",
    "answer_usefulness": "Answer Usefulness",
    "practical_specificity": "Practical Specificity",
    "reference_quality": "Source Quality",
    "summary_usefulness": "Summary Quality",
}

# ─── Detailed Improvement Actions per Dimension ─────────────────────────────
# Each dimension has multiple specific actions with estimated point gains

DIMENSION_ACTIONS = {
    "extractability": [
        ("Add Yoast FAQ block with 5+ Q&A pairs", 12),
        ("Add 'TL;DR' or 'Quick Answer' box at top of post", 8),
        ("Add 'At a Glance' structured summary block", 7),
        ("Convert key points to question-format H3 headings", 6),
        ("Add structured bullet-point answers under each question heading", 5),
    ],
    "trust_reinforcement": [
        ("Add 'Our Methodology' or 'How We Research' section", 10),
        ("Add 'Reviewed by [Name], Veterinary Advisor' attribution", 9),
        ("Add fact-check disclaimer with date", 7),
        ("Insert 'Evidence-Based' label with methodology link", 6),
        ("Add editorial standards footer link", 5),
    ],
    "comparison_usefulness": [
        ("Add wp-block-table comparison table (3+ products/options)", 14),
        ("Add 'X vs Y' section with side-by-side breakdown", 10),
        ("Add Pros/Cons list for each recommended product", 8),
        ("Add 'Which Is Best For...' decision matrix", 7),
        ("Include 'Difference Between' subsection", 5),
    ],
    "glossary_richness": [
        ("Add 'Key Terms' section with 8+ bold-dash definitions", 12),
        ("Add inline '(also known as...)' expansions for technical terms", 6),
        ("Add definition list (dl/dt/dd) block for terminology", 5),
        ("Bold key terms on first use with dash-definition", 5),
        ("Add glossary link cross-references to terminology hub", 4),
    ],
    "educational_usefulness": [
        ("Expand content to 2000+ words with deeper explanations", 8),
        ("Add 4+ H3 sub-sections under each H2", 6),
        ("Add educational intent phrases (guide, explained, complete guide)", 5),
        ("Add step-by-step instructional section", 5),
        ("Include 'Everything You Need to Know' comprehensive breakdown", 4),
    ],
    "answer_usefulness": [
        ("Rewrite 5+ headings as question format (How/What/Why/When)", 10),
        ("Add direct 1-2 sentence answer immediately after each question heading", 8),
        ("Add 'We Recommend' or 'Our Pick' direct answer statements", 5),
        ("Include conversational query matches in H2/H3 text", 5),
        ("Add numbered action steps for how-to queries", 4),
    ],
    "practical_specificity": [
        ("Add UK-specific measurements (cm/kg/ml) throughout", 8),
        ("Add 3+ brand name recommendations with model specifics", 7),
        ("Add price ranges in GBP for each recommendation", 7),
        ("Include breed-specific sizing/dosage tables", 6),
        ("Add frequency/schedule specifics (e.g. 'twice daily', 'every 4 weeks')", 5),
    ],
    "reference_quality": [
        ("Add 3+ RSPCA/BVA/PDSA citations with links", 15),
        ("Add 'According to [Authority]' attribution phrases", 8),
        ("Link to gov.uk pet legislation or DEFRA guidelines", 7),
        ("Add source list/references section at bottom", 6),
        ("Include named veterinary or breed expert sources", 5),
    ],
    "summary_usefulness": [
        ("Add 'At a Glance' bullet-point box at top", 10),
        ("Add 'Key Takeaways' numbered list at bottom", 8),
        ("Add 'Final Thoughts' or 'Conclusion' heading with recap", 7),
        ("Add bullet-point recap of main recommendations", 5),
        ("Add 'What We Covered' summary section", 4),
    ],
}

# Feasibility multipliers per dimension (how easy to implement, 0.0-1.0)
DIMENSION_FEASIBILITY = {
    "extractability": 0.90,       # Easy: add FAQ blocks, Q&A
    "trust_reinforcement": 0.85,  # Medium: need editorial standards
    "comparison_usefulness": 0.80, # Medium: requires table creation
    "glossary_richness": 0.85,    # Easy-medium: add terms sections
    "educational_usefulness": 0.70, # Harder: requires content expansion
    "answer_usefulness": 0.90,    # Easy: rewrite headings
    "practical_specificity": 0.75, # Medium: needs research for specifics
    "reference_quality": 0.65,    # Harder: need to find/verify sources
    "summary_usefulness": 0.95,   # Easiest: add summary blocks
}


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


# ─── Utility Functions ───────────────────────────────────────────────────────

def strip_html(text):
    """Strip HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    return text


def classify_post(title):
    """Classify a post into a cluster based on title keywords."""
    title_lower = title.lower()
    for cluster_name in CLUSTER_PRIORITY_ORDER:
        keywords = CLUSTER_RULES[cluster_name]
        for kw in keywords:
            if ".*" in kw:
                if re.search(kw, title_lower):
                    if cluster_name == "Dog Harnesses" and "cat" in title_lower:
                        continue
                    if cluster_name == "Dog Beds" and "cat" in title_lower:
                        continue
                    return cluster_name
            else:
                if kw in title_lower:
                    if cluster_name == "Dog Harnesses" and "cat" in title_lower:
                        continue
                    if cluster_name == "Dog Beds" and "cat" in title_lower:
                        continue
                    if cluster_name == "Cat Supplies" and "dog" in title_lower:
                        continue
                    return cluster_name
    return "Unclassified"


def clamp(val, lo=0, hi=100):
    return max(lo, min(hi, int(round(val))))


# ─── Citation Confidence Dimension Scorers ───────────────────────────────────

def score_extractability(raw_content, plain_text, title):
    """FAQ blocks, quick-answer sections, structured Q&A, TL;DR, At a Glance."""
    score = 0
    combined_lower = (title + " " + plain_text).lower()
    raw_lower = raw_content.lower()

    # FAQ blocks (Yoast FAQ, rank-math FAQ, generic FAQ schema)
    faq_block_count = len(re.findall(
        r'wp-block-yoast-faq|yoast-faq|rank-math.*faq|schema.*faq|faq-schema',
        raw_lower
    ))
    score += min(30, faq_block_count * 15)

    # FAQ-like sections (heading with FAQ or "frequently asked")
    faq_heading = len(re.findall(
        r'<h[2-4][^>]*>.*?(?:faq|frequently asked|common questions).*?</h[2-4]>',
        raw_lower
    ))
    score += min(20, faq_heading * 10)

    # Question headings (H2/H3 that start with question words)
    question_headings = len(re.findall(
        r'<h[2-4][^>]*>\s*(?:how|what|why|when|where|which|can|do|does|is|are|should)\b',
        raw_lower
    ))
    score += min(20, question_headings * 4)

    # TL;DR or quick summary
    tldr_signals = [r'tl;?dr', r'quick summary', r'quick answer', r'short answer',
                    r'in (a )?nutshell', r'bottom line', r'at a glance']
    tldr_hits = sum(1 for pat in tldr_signals if re.search(pat, combined_lower))
    score += min(15, tldr_hits * 8)

    # Structured lists (ordered/unordered) aid extractability
    list_count = len(re.findall(r'<(?:ul|ol)[\s>]', raw_lower))
    score += min(15, list_count * 3)

    return clamp(score)


def score_trust_reinforcement(raw_content, plain_text, title):
    """Editorial standards, methodology, external citations."""
    score = 0
    combined_lower = (title + " " + raw_content + " " + plain_text).lower()

    trust_signals = [
        r'editorial standards', r'our methodology', r'fact[- ]check',
        r'reviewed by', r'vet[- ]reviewed', r'medically reviewed',
        r'expert[- ]reviewed', r'veterinary[- ]reviewed',
        r'sources?\s*:', r'references?\s*:', r'evidence[- ]based',
        r'peer[- ]reviewed', r'clinically proven', r'research shows',
        r'according to', r'studies? (show|suggest|indicate|found)',
    ]
    trust_hits = sum(1 for pat in trust_signals if re.search(pat, combined_lower))
    score += min(50, trust_hits * 8)

    disclaimer_signals = [
        r'disclaimer', r'affiliate', r'transparency',
        r'we (may )?earn', r'commission', r'always consult',
        r'consult your vet', r'speak to your vet',
    ]
    disclaimer_hits = sum(1 for pat in disclaimer_signals if re.search(pat, combined_lower))
    score += min(25, disclaimer_hits * 8)

    author_signals = [
        r'written by', r'author:', r'contributor',
        r'years of experience', r'qualified',
    ]
    author_hits = sum(1 for pat in author_signals if re.search(pat, combined_lower))
    score += min(25, author_hits * 10)

    return clamp(score)


def score_comparison_usefulness(raw_content, plain_text, title):
    """Tables, vs content, pro/con, feature comparisons."""
    score = 0
    combined_lower = (title + " " + plain_text).lower()
    raw_lower = raw_content.lower()

    table_count = len(re.findall(r'wp-block-table|<table[\s>]', raw_lower))
    score += min(35, table_count * 15)

    vs_count = len(re.findall(r'\bvs\.?\b|\bversus\b|\bcompared to\b|\bcomparison\b', combined_lower))
    score += min(25, vs_count * 5)

    procon_signals = [r'\bpros?\b.*\bcons?\b', r'\badvantages?\b', r'\bdisadvantages?\b',
                      r'\bstrengths?\b.*\bweaknesses?\b', r'\bbenefits\b.*\bdrawbacks\b']
    procon_hits = sum(1 for pat in procon_signals if re.search(pat, combined_lower))
    score += min(20, procon_hits * 7)

    diff_signals = [r'\bdifference between\b', r'\bside[- ]by[- ]side\b', r'\bwhich is better\b']
    diff_hits = sum(1 for pat in diff_signals if re.search(pat, combined_lower))
    score += min(20, diff_hits * 10)

    return clamp(score)


def score_glossary_richness(raw_content, plain_text, title):
    """Key Terms, bold-dash definitions, inline terminology."""
    score = 0
    combined_lower = (title + " " + plain_text).lower()
    raw_lower = raw_content.lower()

    glossary_signals = [
        r'key terms', r'glossary', r'terminology', r'definitions?\s*:',
        r'what does .* mean', r'what is a .*\?',
    ]
    glossary_hits = sum(1 for pat in glossary_signals if re.search(pat, combined_lower))
    score += min(30, glossary_hits * 10)

    bold_def_count = len(re.findall(
        r'<(?:strong|b)>[^<]+</(?:strong|b)>\s*[–—\-:]\s*\w',
        raw_content
    ))
    score += min(35, bold_def_count * 5)

    inline_terms = len(re.findall(
        r'\(also (known|called|referred) as\b|\balso known as\b|\bmeaning\b.*\bis\b|\bi\.e\.\b|\be\.g\.\b',
        combined_lower
    ))
    score += min(20, inline_terms * 5)

    deflist_count = len(re.findall(r'<dt[\s>]|<dd[\s>]|wp-block-details', raw_lower))
    score += min(15, deflist_count * 5)

    return clamp(score)


def score_educational_usefulness(raw_content, plain_text, title):
    """Plain language, beginner explanations, structured headings."""
    words = plain_text.split()
    word_count = len(words)

    if word_count >= 2000:
        wc_score = 40
    elif word_count >= 500:
        wc_score = 10 + (word_count - 500) * 30 / 1500
    else:
        wc_score = word_count * 10 / 500

    h2_count = len(re.findall(r'<h2[\s>]', raw_content, re.I))
    h3_count = len(re.findall(r'<h3[\s>]', raw_content, re.I))
    heading_total = h2_count + h3_count
    if heading_total >= 8:
        heading_score = 30
    elif heading_total >= 4:
        heading_score = 15 + (heading_total - 4) * 15 / 4
    else:
        heading_score = heading_total * 15 / 4

    edu_signals = [
        r'\bguide\b', r'\bhow to\b', r'\bexplained\b', r'\bcomplete guide\b',
        r'\bstep[- ]by[- ]step\b', r'\beverything you need to know\b',
        r'\btips\b', r'\bwhat (is|are)\b', r'\bwhy (do|does|is|are|should)\b',
        r'\bbenefits of\b', r'\bimportance of\b', r'\bunderstanding\b',
        r'\blearn\b', r'\beducational\b', r'\bin-depth\b', r'\bcomprehensive\b',
    ]
    combined = (title + " " + plain_text).lower()
    edu_hits = sum(1 for pat in edu_signals if re.search(pat, combined))
    edu_intent_score = min(30, edu_hits * 5)

    return clamp(wc_score + heading_score + edu_intent_score)


def score_answer_usefulness(raw_content, plain_text, title):
    """Direct answers in headings, conversational query matches."""
    score = 0
    combined_lower = (title + " " + plain_text).lower()

    q_headings = re.findall(r'<h[2-4][^>]*>(.*?)</h[2-4]>', raw_content, re.I)
    question_heading_count = 0
    for h in q_headings:
        h_text = strip_html(h).strip().lower()
        if re.match(r'^(how|what|why|when|where|which|can|do|does|is|are|should)\b', h_text):
            question_heading_count += 1
    score += min(30, question_heading_count * 5)

    direct_answer_signals = [
        r'\bthe (?:best|top|most|safest|cheapest)\b',
        r'\bwe recommend\b', r'\bour (?:top )?pick\b',
        r'\byes[,.]', r'\bno[,.]',
        r'\bthe answer is\b', r'\bin short\b',
        r'\bsimply put\b', r'\bto summarise\b', r'\bto summarize\b',
    ]
    answer_hits = sum(1 for pat in direct_answer_signals if re.search(pat, combined_lower))
    score += min(25, answer_hits * 5)

    conversational_patterns = [
        r'^(how|what|why|when|which|can|do|does|is|are|should)\b',
        r'\bbest\b.*\bfor\b', r'\bhow to\b', r'\btips for\b',
    ]
    title_lower = title.lower()
    conv_hits = sum(1 for pat in conversational_patterns if re.search(pat, title_lower))
    score += min(20, conv_hits * 10)

    step_count = len(re.findall(r'\bstep \d\b|\b\d+\.\s+[A-Z]', plain_text))
    score += min(15, step_count * 3)

    bold_answers = len(re.findall(r'<strong>[^<]{5,80}</strong>', raw_content))
    score += min(10, bold_answers * 2)

    return clamp(score)


def score_practical_specificity(raw_content, plain_text, title):
    """UK-specific guidance, measurements, brand names, prices."""
    score = 0
    combined_lower = (title + " " + plain_text).lower()

    measurement_count = len(re.findall(
        r'\b\d+(\.\d+)?\s*(cm|mm|kg|g|ml|litres?|liters?|inches?|feet|ft|lbs?|oz|metres?|meters?)\b',
        combined_lower
    ))
    score += min(25, measurement_count * 3)

    quantity_count = len(re.findall(r'£\d+|\$\d+|\d+\s*pack|\d+\s*pieces?|\d+\s*servings?', combined_lower))
    score += min(15, quantity_count * 3)

    brand_patterns = [
        r'\bKong\b', r'\bNylabone\b', r'\bRoyal Canin\b', r'\bHarringtons\b',
        r'\bPedigree\b', r'\bWhiskas\b', r'\bFelix\b', r'\bSheba\b',
        r'\bJames Wellbeloved\b', r'\bLily\'?s Kitchen\b', r'\bOrijen\b',
        r'\bAcana\b', r'\bHilife\b', r'\bBurns\b', r'\bAtu\b',
        r'\bRuffwear\b', r'\bJulius[- ]K9\b', r'\bHalti\b',
    ]
    brand_raw = title + " " + plain_text
    brand_hits = sum(1 for pat in brand_patterns if re.search(pat, brand_raw))
    score += min(20, brand_hits * 4)

    uk_signals = [
        r'\buk\b', r'\bunited kingdom\b', r'\bbritish\b', r'\bengland\b',
        r'\bwales\b', r'\bscotland\b', r'\bnhs\b', r'\brspca\b',
        r'\bbva\b', r'\bgov\.uk\b', r'\bkennel club\b', r'£',
    ]
    uk_hits = sum(1 for pat in uk_signals if re.search(pat, combined_lower))
    score += min(20, uk_hits * 5)

    specificity_count = len(re.findall(
        r'\b\d+\s*(times?|x)\s*(a|per)\s*(day|week|month)\b|\bevery\s+\d+\s+(hours?|days?|weeks?)\b',
        combined_lower
    ))
    score += min(20, specificity_count * 5)

    return clamp(score)


def score_reference_quality(raw_content, plain_text, title):
    """RSPCA, BVA, gov.uk, PDSA citations, named sources."""
    score = 0
    raw_lower = raw_content.lower()
    combined_lower = (title + " " + plain_text).lower()

    trusted_hit_count = 0
    for domain in TRUSTED_DOMAINS:
        occurrences = len(re.findall(re.escape(domain), raw_lower))
        trusted_hit_count += min(occurrences, 3)
    score += min(45, trusted_hit_count * 8)

    external_links = len(re.findall(r'href=["\']https?://(?!pethubonline\.com)', raw_lower))
    score += min(20, external_links * 3)

    source_signals = [
        r'according to', r'source:', r'reference:', r'cited from',
        r'as reported by', r'data from', r'published by',
        r'as stated by', r'research from', r'study by',
    ]
    source_hits = sum(1 for pat in source_signals if re.search(pat, combined_lower))
    score += min(20, source_hits * 5)

    footnote_count = len(re.findall(r'\[\d+\]|<sup>\d+</sup>|<footnote', raw_lower))
    score += min(15, footnote_count * 5)

    return clamp(score)


def score_summary_usefulness(raw_content, plain_text, title):
    """At a glance, key takeaways, conclusion sections."""
    score = 0
    combined_lower = (title + " " + plain_text).lower()
    raw_lower = raw_content.lower()

    summary_heading_signals = [
        r'<h[2-4][^>]*>.*?(?:at a glance|key takeaways?|summary|in summary|conclusion|final thoughts|wrap[- ]?up|the bottom line).*?</h[2-4]>',
    ]
    for pat in summary_heading_signals:
        hits = len(re.findall(pat, raw_lower))
        score += min(30, hits * 15)

    summary_body_signals = [
        r'\bat a glance\b', r'\bkey takeaways?\b', r'\bin summary\b',
        r'\bto summarise\b', r'\bto summarize\b', r'\bfinal thoughts\b',
        r'\bconclusion\b', r'\bwrap[- ]?up\b', r'\boverall\b.*\brecommend',
        r'\bthe bottom line\b', r'\bhere\'?s what (you|we) (learned|covered)\b',
    ]
    body_hits = sum(1 for pat in summary_body_signals if re.search(pat, combined_lower))
    score += min(35, body_hits * 7)

    content_len = len(raw_content)
    if content_len > 200:
        tail = raw_content[int(content_len * 0.8):].lower()
        tail_lists = len(re.findall(r'<(?:ul|ol)[\s>]', tail))
        score += min(20, tail_lists * 10)

    recap_signals = [r'\brecap\b', r'\bquick overview\b', r'\bhighlights?\b']
    recap_hits = sum(1 for pat in recap_signals if re.search(pat, combined_lower))
    score += min(15, recap_hits * 8)

    return clamp(score)


# ─── Master Scoring Function ────────────────────────────────────────────────

def score_post(post):
    """Score a single post across all 9 citation confidence dimensions."""
    title_obj = post.get("title", {})
    title = strip_html(title_obj.get("rendered", "") if isinstance(title_obj, dict) else str(title_obj))

    content_obj = post.get("content", {})
    raw_content = content_obj.get("rendered", "") if isinstance(content_obj, dict) else str(content_obj)
    plain_text = strip_html(raw_content)

    slug = post.get("slug", "")
    post_id = post.get("id", 0)
    cluster = classify_post(title)

    dimensions = {
        "extractability": score_extractability(raw_content, plain_text, title),
        "trust_reinforcement": score_trust_reinforcement(raw_content, plain_text, title),
        "comparison_usefulness": score_comparison_usefulness(raw_content, plain_text, title),
        "glossary_richness": score_glossary_richness(raw_content, plain_text, title),
        "educational_usefulness": score_educational_usefulness(raw_content, plain_text, title),
        "answer_usefulness": score_answer_usefulness(raw_content, plain_text, title),
        "practical_specificity": score_practical_specificity(raw_content, plain_text, title),
        "reference_quality": score_reference_quality(raw_content, plain_text, title),
        "summary_usefulness": score_summary_usefulness(raw_content, plain_text, title),
    }

    # Weighted overall
    overall = sum(dimensions[k] * DIMENSION_WEIGHTS[k] for k in DIMENSION_WEIGHTS)
    overall = clamp(overall)

    # Gap to 70
    gap_to_70 = max(0, 70 - overall)

    # Feasibility score: weighted by how improvable the weakest dimensions are
    dim_gaps = {}
    for k, v in dimensions.items():
        dim_gap = max(0, 70 - v)
        dim_gaps[k] = dim_gap

    # Feasibility: average feasibility of top-3 worst dimensions, weighted by gap size
    sorted_gaps = sorted(dim_gaps.items(), key=lambda x: -x[1])[:3]
    if sum(g for _, g in sorted_gaps) > 0:
        feasibility = sum(
            DIMENSION_FEASIBILITY[k] * g for k, g in sorted_gaps
        ) / sum(g for _, g in sorted_gaps) * 100
    else:
        feasibility = 100
    feasibility = clamp(feasibility)

    return {
        "post_id": post_id,
        "title": title.strip(),
        "slug": slug,
        "cluster": cluster,
        "dimensions": dimensions,
        "overall_citation_confidence": overall,
        "gap_to_70": gap_to_70,
        "feasibility_score": feasibility,
    }


# ─── Acceleration Plan Generator ────────────────────────────────────────────

def generate_acceleration_plan(scored_post):
    """
    For each post, identify top 3 dimensions to improve and generate
    specific actions with estimated confidence gains.
    """
    dims = scored_post["dimensions"]
    overall = scored_post["overall_citation_confidence"]
    gap = scored_post["gap_to_70"]

    if gap == 0:
        return {
            "action_1": "Already at/above 70 — maintain quality",
            "estimated_gain_1": 0,
            "action_2": "Monitor for decay",
            "estimated_gain_2": 0,
            "action_3": "Consider pushing to 85+ elite tier",
            "estimated_gain_3": 0,
            "total_estimated_gain": 0,
            "priority": "P4-Maintain",
        }

    # Find top 3 dimensions with most improvement potential
    # Potential = (gap to 70 for that dimension) * weight * feasibility
    dim_potential = []
    for k, v in dims.items():
        dim_gap = max(0, 80 - v)  # target 80 per dimension to get overall to 70
        weight = DIMENSION_WEIGHTS[k]
        feasibility = DIMENSION_FEASIBILITY[k]
        potential = dim_gap * weight * feasibility
        dim_potential.append((k, v, dim_gap, potential))

    dim_potential.sort(key=lambda x: -x[3])
    top_3 = dim_potential[:3]

    actions = []
    for dim_key, dim_score, dim_gap, potential in top_3:
        # Pick best action for this dimension
        available_actions = DIMENSION_ACTIONS.get(dim_key, [])
        if available_actions:
            # Pick the action with highest estimated gain that makes sense
            best_action, base_gain = available_actions[0]
            # Scale gain by how much room there is
            scale_factor = min(1.0, dim_gap / 50)
            adjusted_gain = round(base_gain * scale_factor * DIMENSION_WEIGHTS[dim_key] * 10, 1)
            # Ensure minimum gain of 1 if there's a gap
            if dim_gap > 0 and adjusted_gain < 1:
                adjusted_gain = 1.0
            action_text = f"[{DIMENSION_LABELS[dim_key]}] {best_action} (current: {dim_score}/100)"
        else:
            action_text = f"[{DIMENSION_LABELS[dim_key]}] Improve content quality"
            adjusted_gain = 2.0

        actions.append((action_text, adjusted_gain))

    # Pad to 3 if needed
    while len(actions) < 3:
        actions.append(("No further action needed", 0))

    total_gain = sum(a[1] for a in actions)

    # Priority assignment based on gap and feasibility
    avg_feasibility = sum(DIMENSION_FEASIBILITY[t[0]] for t in top_3) / len(top_3) if top_3 else 0
    if overall >= 55 and gap <= 15:
        priority = "P1-Sprint"  # Close to 70, quick wins
    elif overall >= 45 and gap <= 25:
        priority = "P2-Accelerate"
    elif overall >= 35 and gap <= 35:
        priority = "P3-Build"
    else:
        priority = "P4-Foundation"

    # Boost priority if high feasibility
    if avg_feasibility >= 0.85 and priority == "P3-Build":
        priority = "P2-Accelerate"

    return {
        "action_1": actions[0][0],
        "estimated_gain_1": actions[0][1],
        "action_2": actions[1][0],
        "estimated_gain_2": actions[1][1],
        "action_3": actions[2][0],
        "estimated_gain_3": actions[2][1],
        "total_estimated_gain": round(total_gain, 1),
        "priority": priority,
    }


# ─── Cluster Roadmap Generator ──────────────────────────────────────────────

def generate_cluster_roadmap(cluster_posts):
    """
    For each cluster, compute current averages, target, closest posts to 70,
    and the single highest-impact action.
    """
    roadmaps = {}

    for cluster_name in set(p["cluster"] for p in cluster_posts):
        posts = [p for p in cluster_posts if p["cluster"] == cluster_name]
        if not posts:
            continue

        avg_confidence = round(sum(p["overall_citation_confidence"] for p in posts) / len(posts), 1)
        target_avg = 70.0

        # Posts closest to 70 (sorted by confidence descending)
        sorted_posts = sorted(posts, key=lambda x: -x["overall_citation_confidence"])
        closest_to_70 = [
            f"{p['title'][:50]}... ({p['overall_citation_confidence']})"
            if len(p['title']) > 50 else f"{p['title']} ({p['overall_citation_confidence']})"
            for p in sorted_posts[:3]
        ]
        closest_str = "; ".join(closest_to_70)

        # Find the weakest dimension across the cluster
        dim_averages = defaultdict(list)
        for p in posts:
            for k, v in p["dimensions"].items():
                dim_averages[k].append(v)

        dim_avg_scores = {k: sum(v) / len(v) for k, v in dim_averages.items()}
        weakest_dim = min(dim_avg_scores, key=dim_avg_scores.get)
        weakest_avg = dim_avg_scores[weakest_dim]

        # Find the best single action for the cluster
        # Highest impact = lowest scoring dimension * highest weight * highest feasibility
        dim_impact = []
        for k, avg_score in dim_avg_scores.items():
            gap = max(0, 70 - avg_score)
            impact = gap * DIMENSION_WEIGHTS[k] * DIMENSION_FEASIBILITY[k]
            dim_impact.append((k, gap, impact, avg_score))

        dim_impact.sort(key=lambda x: -x[2])
        top_dim = dim_impact[0] if dim_impact else None

        if top_dim:
            top_actions = DIMENSION_ACTIONS.get(top_dim[0], [])
            if top_actions:
                top_action = f"[{DIMENSION_LABELS[top_dim[0]]}] {top_actions[0][0]} (cluster avg: {round(top_dim[3], 1)}/100)"
            else:
                top_action = f"Improve {DIMENSION_LABELS[top_dim[0]]}"
        else:
            top_action = "Maintain current quality"

        # Estimated cluster gain if top action applied to all posts
        estimated_cluster_gain = round(
            top_dim[2] * 10 / len(posts) if top_dim else 0, 1
        )
        # More realistic: applying the action boosts the weakest dim by ~15-25 points
        # which translates to overall gain of dim_weight * 20
        if top_dim:
            realistic_gain = round(DIMENSION_WEIGHTS[top_dim[0]] * 20, 1)
            estimated_cluster_gain = max(estimated_cluster_gain, realistic_gain)

        # Priority for cluster
        if avg_confidence >= 50:
            priority = "P1-Sprint-to-70"
        elif avg_confidence >= 40:
            priority = "P2-Accelerate"
        elif avg_confidence >= 30:
            priority = "P3-Build"
        else:
            priority = "P4-Foundation"

        roadmaps[cluster_name] = {
            "cluster": cluster_name,
            "current_avg": avg_confidence,
            "target_avg": target_avg,
            "post_count": len(posts),
            "posts_closest_to_70": closest_str,
            "weakest_dimension": f"{DIMENSION_LABELS[weakest_dim]} (avg {round(weakest_avg, 1)})",
            "top_action": top_action,
            "estimated_cluster_gain": estimated_cluster_gain,
            "priority": priority,
        }

    return roadmaps


# ─── CSV Writers ─────────────────────────────────────────────────────────────

def write_dominance_scores_csv(scored_posts, filepath):
    """Write Citation_Dominance_Scores.csv"""
    fieldnames = [
        "post_id", "title", "cluster",
        "Extractability", "Trust Reinforcement", "Comparison Usefulness",
        "Glossary Richness", "Educational Clarity", "Answer Usefulness",
        "Practical Specificity", "Source Quality", "Summary Quality",
        "overall_citation_confidence", "gap_to_70", "feasibility_score",
    ]
    dim_keys_ordered = [
        "extractability", "trust_reinforcement", "comparison_usefulness",
        "glossary_richness", "educational_usefulness", "answer_usefulness",
        "practical_specificity", "reference_quality", "summary_usefulness",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        sorted_posts = sorted(scored_posts, key=lambda x: -x["overall_citation_confidence"])
        for p in sorted_posts:
            row = {
                "post_id": p["post_id"],
                "title": p["title"],
                "cluster": p["cluster"],
                "overall_citation_confidence": p["overall_citation_confidence"],
                "gap_to_70": p["gap_to_70"],
                "feasibility_score": p["feasibility_score"],
            }
            for dk, label in zip(dim_keys_ordered, fieldnames[3:12]):
                row[label] = p["dimensions"][dk]
            writer.writerow(row)

    print(f"  Written: {filepath} ({len(scored_posts)} posts)")


def write_acceleration_plan_csv(scored_posts, plans, filepath):
    """Write Citation_Acceleration_Plan.csv"""
    fieldnames = [
        "post_id", "title", "cluster",
        "action_1", "estimated_gain_1",
        "action_2", "estimated_gain_2",
        "action_3", "estimated_gain_3",
        "total_estimated_gain", "priority",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        # Sort by priority then by total_estimated_gain descending
        priority_order = {"P1-Sprint": 0, "P2-Accelerate": 1, "P3-Build": 2, "P4-Foundation": 3, "P4-Maintain": 4}
        sorted_items = sorted(
            zip(scored_posts, plans),
            key=lambda x: (priority_order.get(x[1]["priority"], 5), -x[1]["total_estimated_gain"])
        )

        for post, plan in sorted_items:
            row = {
                "post_id": post["post_id"],
                "title": post["title"],
                "cluster": post["cluster"],
                "action_1": plan["action_1"],
                "estimated_gain_1": plan["estimated_gain_1"],
                "action_2": plan["action_2"],
                "estimated_gain_2": plan["estimated_gain_2"],
                "action_3": plan["action_3"],
                "estimated_gain_3": plan["estimated_gain_3"],
                "total_estimated_gain": plan["total_estimated_gain"],
                "priority": plan["priority"],
            }
            writer.writerow(row)

    print(f"  Written: {filepath} ({len(plans)} plans)")


def write_cluster_roadmap_csv(roadmaps, filepath):
    """Write Cluster_Citation_Roadmap.csv"""
    fieldnames = [
        "cluster", "current_avg", "target_avg", "post_count",
        "posts_closest_to_70", "weakest_dimension",
        "top_action", "estimated_cluster_gain", "priority",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        # Sort by priority
        priority_order = {"P1-Sprint-to-70": 0, "P2-Accelerate": 1, "P3-Build": 2, "P4-Foundation": 3}
        sorted_roadmaps = sorted(
            roadmaps.values(),
            key=lambda x: (priority_order.get(x["priority"], 5), -x["current_avg"])
        )

        for rm in sorted_roadmaps:
            writer.writerow(rm)

    print(f"  Written: {filepath} ({len(roadmaps)} clusters)")


# ─── Summary Printer ────────────────────────────────────────────────────────

def print_summary(scored_posts, plans, roadmaps):
    """Print comprehensive summary of citation dominance analysis."""
    print("\n" + "=" * 80)
    print("10AE-E: CITATION DOMINANCE ENGINE — EXECUTIVE SUMMARY")
    print("=" * 80)

    # Overall stats
    total = len(scored_posts)
    avg_overall = sum(p["overall_citation_confidence"] for p in scored_posts) / total if total else 0
    above_70 = sum(1 for p in scored_posts if p["overall_citation_confidence"] >= 70)
    above_50 = sum(1 for p in scored_posts if p["overall_citation_confidence"] >= 50)
    above_40 = sum(1 for p in scored_posts if p["overall_citation_confidence"] >= 40)

    print(f"\n  Total posts analyzed: {total}")
    print(f"  Average citation confidence: {avg_overall:.1f}")
    print(f"  Posts >= 70 (dominance threshold): {above_70}")
    print(f"  Posts >= 50 (acceleration zone): {above_50}")
    print(f"  Posts >= 40 (build zone): {above_40}")
    print(f"  Posts < 40 (foundation needed): {total - above_40}")

    # Top 10 closest to 70
    print(f"\n{'─' * 80}")
    print("TOP 10 POSTS CLOSEST TO 70 (FASTEST PATH TO CITATION DOMINANCE)")
    print(f"{'─' * 80}")
    sorted_by_confidence = sorted(scored_posts, key=lambda x: -x["overall_citation_confidence"])
    for i, p in enumerate(sorted_by_confidence[:10], 1):
        print(f"  {i:2d}. [{p['cluster']:18s}] {p['title'][:55]:55s} "
              f"conf={p['overall_citation_confidence']:3d}  gap={p['gap_to_70']:2d}  "
              f"feas={p['feasibility_score']:2d}")

    # Dog Food cluster deep dive (closest to 70)
    print(f"\n{'─' * 80}")
    print("DOG FOOD CLUSTER DEEP DIVE (Current avg: 53.8 — CLOSEST TO 70)")
    print(f"{'─' * 80}")
    dog_food_posts = [p for p in scored_posts if p["cluster"] == "Dog Food"]
    dog_food_posts.sort(key=lambda x: -x["overall_citation_confidence"])
    for p in dog_food_posts:
        dims = p["dimensions"]
        weak_dims = sorted(dims.items(), key=lambda x: x[1])[:3]
        weak_str = ", ".join(f"{DIMENSION_LABELS[k]}={v}" for k, v in weak_dims)
        print(f"  [{p['post_id']:5d}] {p['title'][:50]:50s}  conf={p['overall_citation_confidence']:3d}  "
              f"gap={p['gap_to_70']:2d}")
        print(f"         Weakest: {weak_str}")

    # Cluster roadmap summary
    print(f"\n{'─' * 80}")
    print("CLUSTER CITATION ROADMAP")
    print(f"{'─' * 80}")
    priority_order = {"P1-Sprint-to-70": 0, "P2-Accelerate": 1, "P3-Build": 2, "P4-Foundation": 3}
    sorted_roadmaps = sorted(
        roadmaps.values(),
        key=lambda x: (priority_order.get(x["priority"], 5), -x["current_avg"])
    )
    print(f"  {'Cluster':<20s} {'Posts':>5s} {'Avg':>5s} {'Target':>6s} {'Gap':>5s} {'Priority':<18s} {'Est Gain':>8s}")
    print(f"  {'─' * 20} {'─' * 5} {'─' * 5} {'─' * 6} {'─' * 5} {'─' * 18} {'─' * 8}")
    for rm in sorted_roadmaps:
        gap = round(rm["target_avg"] - rm["current_avg"], 1)
        print(f"  {rm['cluster']:<20s} {rm['post_count']:5d} {rm['current_avg']:5.1f} "
              f"{rm['target_avg']:6.1f} {gap:5.1f} {rm['priority']:<18s} +{rm['estimated_cluster_gain']:5.1f}")

    # Priority action breakdown
    print(f"\n{'─' * 80}")
    print("PRIORITY ACTIONS BY CLUSTER")
    print(f"{'─' * 80}")
    for rm in sorted_roadmaps:
        print(f"\n  {rm['cluster']} ({rm['priority']}):")
        print(f"    Weakest: {rm['weakest_dimension']}")
        print(f"    Action:  {rm['top_action']}")
        print(f"    Closest: {rm['posts_closest_to_70'][:120]}")

    # Sprint plan: posts that can reach 70 with least effort
    print(f"\n{'─' * 80}")
    print("SPRINT PLAN: FASTEST 20 POSTS TO REACH 70+ CITATION CONFIDENCE")
    print(f"{'─' * 80}")
    sprint_candidates = sorted(
        zip(scored_posts, plans),
        key=lambda x: (x[0]["gap_to_70"], -x[0]["feasibility_score"])
    )
    for i, (post, plan) in enumerate(sprint_candidates[:20], 1):
        print(f"  {i:2d}. [{post['cluster']:18s}] {post['title'][:45]:45s} "
              f"conf={post['overall_citation_confidence']:3d} gap={post['gap_to_70']:2d} "
              f"est_gain=+{plan['total_estimated_gain']:4.1f} [{plan['priority']}]")

    # Dimension-level weaknesses across all posts
    print(f"\n{'─' * 80}")
    print("SITE-WIDE DIMENSION AVERAGES (0-100)")
    print(f"{'─' * 80}")
    dim_totals = defaultdict(list)
    for p in scored_posts:
        for k, v in p["dimensions"].items():
            dim_totals[k].append(v)
    dim_avgs = {k: sum(v) / len(v) for k, v in dim_totals.items()}
    sorted_dims = sorted(dim_avgs.items(), key=lambda x: x[1])
    for k, avg in sorted_dims:
        bar_len = int(avg / 2)
        bar = "█" * bar_len + "░" * (50 - bar_len)
        status = "CRITICAL" if avg < 20 else "WEAK" if avg < 40 else "MODERATE" if avg < 60 else "STRONG"
        print(f"  {DIMENSION_LABELS[k]:<22s} {avg:5.1f} {bar} [{status}]")

    print(f"\n{'=' * 80}")
    print("FILES GENERATED:")
    print(f"  1. {OUTPUT_DIR}/Citation_Dominance_Scores.csv")
    print(f"  2. {OUTPUT_DIR}/Citation_Acceleration_Plan.csv")
    print(f"  3. {OUTPUT_DIR}/Cluster_Citation_Roadmap.csv")
    print(f"{'=' * 80}\n")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print("=" * 80)
    print("10AE-E: Citation Dominance Engine")
    print("pethubonline.com — 144 published posts")
    print("Building on 10AD-D (avg confidence 36.8, 0 posts above 70)")
    print("=" * 80)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Step 1: Fetch all posts
    print("\n[1/5] Fetching all published posts from WordPress API...")
    posts = fetch_all_posts()
    if not posts:
        print("ERROR: No posts fetched. Exiting.")
        sys.exit(1)
    print(f"  Total posts fetched: {len(posts)}")

    # Step 2: Score all posts
    print("\n[2/5] Scoring all posts across 9 citation dimensions...")
    scored_posts = []
    for i, post in enumerate(posts):
        scored = score_post(post)
        scored_posts.append(scored)
        if (i + 1) % 25 == 0:
            print(f"  Scored {i + 1}/{len(posts)} posts...")
    print(f"  All {len(scored_posts)} posts scored.")

    # Step 3: Generate acceleration plans
    print("\n[3/5] Generating per-post citation acceleration plans...")
    plans = []
    for sp in scored_posts:
        plan = generate_acceleration_plan(sp)
        plans.append(plan)
    print(f"  Generated {len(plans)} acceleration plans.")

    # Step 4: Generate cluster roadmaps
    print("\n[4/5] Building cluster-level citation roadmaps...")
    roadmaps = generate_cluster_roadmap(scored_posts)
    print(f"  Built roadmaps for {len(roadmaps)} clusters.")

    # Step 5: Write CSVs
    print("\n[5/5] Writing output CSVs...")
    write_dominance_scores_csv(
        scored_posts,
        os.path.join(OUTPUT_DIR, "Citation_Dominance_Scores.csv")
    )
    write_acceleration_plan_csv(
        scored_posts, plans,
        os.path.join(OUTPUT_DIR, "Citation_Acceleration_Plan.csv")
    )
    write_cluster_roadmap_csv(
        roadmaps,
        os.path.join(OUTPUT_DIR, "Cluster_Citation_Roadmap.csv")
    )

    # Print summary
    print_summary(scored_posts, plans, roadmaps)


if __name__ == "__main__":
    main()
