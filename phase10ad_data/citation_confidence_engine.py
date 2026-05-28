#!/usr/bin/env python3
"""
10AD-D: Citation Confidence Engine
pethubonline.com - WordPress Pet Supplies Blog (144 published posts)

Scores every post for CITATION CONFIDENCE — how likely the page is to be
cited by AI systems, educational resources, or reference materials.
Goal: push more pages above a 70+ citation threshold.
"""

import subprocess
import json
import csv
import re
import os
import sys
import html
from collections import defaultdict

# ─── Configuration ───────────────────────────────────────────────────────────

WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase10ad_data"

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
    "educational_usefulness": 0.15,
    "comparison_usefulness": 0.10,
    "trust_reinforcement": 0.15,
    "practical_specificity": 0.10,
    "glossary_richness": 0.10,
    "extractability": 0.15,
    "answer_usefulness": 0.10,
    "reference_quality": 0.10,
    "summary_usefulness": 0.05,
}

DIMENSION_LABELS = {
    "educational_usefulness": "Educational Usefulness",
    "comparison_usefulness": "Comparison Usefulness",
    "trust_reinforcement": "Trust Reinforcement",
    "practical_specificity": "Practical Specificity",
    "glossary_richness": "Glossary Richness",
    "extractability": "Extractability",
    "answer_usefulness": "Answer Usefulness",
    "reference_quality": "Reference Quality",
    "summary_usefulness": "Summary Usefulness",
}

# Improvement actions per dimension
IMPROVEMENT_ACTIONS = {
    "educational_usefulness": "Add more headings (H2/H3), expand word count to 1500+, include educational intent phrases (guide, how to, explained, complete guide)",
    "comparison_usefulness": "Add comparison tables (wp-block-table), 'vs' sections, pro/con lists, side-by-side feature breakdowns",
    "trust_reinforcement": "Add 'Our Methodology' or 'Editorial Standards' links, fact-check disclaimers, 'reviewed by' attributions, vet-reviewed badges",
    "practical_specificity": "Include specific measurements (cm/kg/ml), brand names, UK-specific guidance, price ranges, dosage/quantity recommendations",
    "glossary_richness": "Add 'Key Terms' section with bold-dash definitions, inline terminology explanations, glossary blocks",
    "extractability": "Add FAQ schema blocks (wp-block-yoast-faq), quick-answer sections, TL;DR summaries, structured Q&A pairs",
    "answer_usefulness": "Use question-format headings (How/What/Why/When), provide direct 1-2 sentence answers immediately after headings",
    "reference_quality": "Add external citations to RSPCA, BVA, PDSA, gov.uk, Battersea, Blue Cross, FEDIAF; include source attribution phrases",
    "summary_usefulness": "Add 'At a Glance' box, 'Key Takeaways' list, conclusion/summary section, bullet-point recap at top or bottom",
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

def score_educational_usefulness(raw_content, plain_text, title):
    """
    Word count depth, heading structure, educational intent signals.
    """
    words = plain_text.split()
    word_count = len(words)

    # Word count component (0-40): 500=10, 1000=20, 1500=30, 2000+=40
    if word_count >= 2000:
        wc_score = 40
    elif word_count >= 500:
        wc_score = 10 + (word_count - 500) * 30 / 1500
    else:
        wc_score = word_count * 10 / 500

    # Heading structure (0-30): count H2 and H3 tags
    h2_count = len(re.findall(r'<h2[\s>]', raw_content, re.I))
    h3_count = len(re.findall(r'<h3[\s>]', raw_content, re.I))
    heading_total = h2_count + h3_count
    if heading_total >= 8:
        heading_score = 30
    elif heading_total >= 4:
        heading_score = 15 + (heading_total - 4) * 15 / 4
    else:
        heading_score = heading_total * 15 / 4

    # Educational intent signals (0-30)
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


def score_comparison_usefulness(raw_content, plain_text, title):
    """
    Comparison tables, 'vs', 'compared to', pro/con sections.
    """
    score = 0
    combined_lower = (title + " " + plain_text).lower()
    raw_lower = raw_content.lower()

    # Comparison tables (wp-block-table or <table)
    table_count = len(re.findall(r'wp-block-table|<table[\s>]', raw_lower))
    score += min(35, table_count * 15)

    # "vs" or "versus" or "compared to" signals
    vs_count = len(re.findall(r'\bvs\.?\b|\bversus\b|\bcompared to\b|\bcomparison\b', combined_lower))
    score += min(25, vs_count * 5)

    # Pro/con sections
    procon_signals = [r'\bpros?\b.*\bcons?\b', r'\badvantages?\b', r'\bdisadvantages?\b',
                      r'\bstrengths?\b.*\bweaknesses?\b', r'\bbenefits\b.*\bdrawbacks\b']
    procon_hits = sum(1 for pat in procon_signals if re.search(pat, combined_lower))
    score += min(20, procon_hits * 7)

    # Side-by-side / "difference between"
    diff_signals = [r'\bdifference between\b', r'\bside[- ]by[- ]side\b', r'\bwhich is better\b']
    diff_hits = sum(1 for pat in diff_signals if re.search(pat, combined_lower))
    score += min(20, diff_hits * 10)

    return clamp(score)


def score_trust_reinforcement(raw_content, plain_text, title):
    """
    Editorial standards links, methodology references, fact-check signals.
    """
    score = 0
    combined_lower = (title + " " + raw_content + " " + plain_text).lower()

    # Editorial standards / methodology references
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

    # Disclaimer / transparency signals
    disclaimer_signals = [
        r'disclaimer', r'affiliate', r'transparency',
        r'we (may )?earn', r'commission', r'always consult',
        r'consult your vet', r'speak to your vet',
    ]
    disclaimer_hits = sum(1 for pat in disclaimer_signals if re.search(pat, combined_lower))
    score += min(25, disclaimer_hits * 8)

    # Author / expertise signals
    author_signals = [
        r'written by', r'author:', r'contributor',
        r'years of experience', r'qualified',
    ]
    author_hits = sum(1 for pat in author_signals if re.search(pat, combined_lower))
    score += min(25, author_hits * 10)

    return clamp(score)


def score_practical_specificity(raw_content, plain_text, title):
    """
    Specific measurements, quantities, brand names, UK-specific guidance.
    """
    score = 0
    combined_lower = (title + " " + plain_text).lower()

    # Measurements (cm, mm, kg, g, ml, litres, inches, etc.)
    measurement_count = len(re.findall(
        r'\b\d+(\.\d+)?\s*(cm|mm|kg|g|ml|litres?|liters?|inches?|feet|ft|lbs?|oz|metres?|meters?)\b',
        combined_lower
    ))
    score += min(25, measurement_count * 3)

    # Quantities / price ranges
    quantity_count = len(re.findall(r'£\d+|\$\d+|\d+\s*pack|\d+\s*pieces?|\d+\s*servings?', combined_lower))
    score += min(15, quantity_count * 3)

    # Brand names (capitalized multi-word or known brands)
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

    # UK-specific guidance
    uk_signals = [
        r'\buk\b', r'\bunited kingdom\b', r'\bbritish\b', r'\bengland\b',
        r'\bwales\b', r'\bscotland\b', r'\bnhs\b', r'\brspca\b',
        r'\bbva\b', r'\bgov\.uk\b', r'\bkennel club\b', r'£',
    ]
    uk_hits = sum(1 for pat in uk_signals if re.search(pat, combined_lower))
    score += min(20, uk_hits * 5)

    # Dosage / frequency / specific numbers
    specificity_count = len(re.findall(
        r'\b\d+\s*(times?|x)\s*(a|per)\s*(day|week|month)\b|\bevery\s+\d+\s+(hours?|days?|weeks?)\b',
        combined_lower
    ))
    score += min(20, specificity_count * 5)

    return clamp(score)


def score_glossary_richness(raw_content, plain_text, title):
    """
    Key Terms blocks, bold-dash definitions, inline terminology.
    """
    score = 0
    combined_lower = (title + " " + plain_text).lower()
    raw_lower = raw_content.lower()

    # Key Terms / Glossary sections
    glossary_signals = [
        r'key terms', r'glossary', r'terminology', r'definitions?\s*:',
        r'what does .* mean', r'what is a .*\?',
    ]
    glossary_hits = sum(1 for pat in glossary_signals if re.search(pat, combined_lower))
    score += min(30, glossary_hits * 10)

    # Bold-dash definitions: <strong>Term</strong> – definition
    # Also <strong>Term</strong> - definition or <b>Term</b> – definition
    bold_def_count = len(re.findall(
        r'<(?:strong|b)>[^<]+</(?:strong|b)>\s*[–—\-:]\s*\w',
        raw_content
    ))
    score += min(35, bold_def_count * 5)

    # Inline terminology explanations: "X (also known as Y)", "X, meaning Y"
    inline_terms = len(re.findall(
        r'\(also (known|called|referred) as\b|\balso known as\b|\bmeaning\b.*\bis\b|\bi\.e\.\b|\be\.g\.\b',
        combined_lower
    ))
    score += min(20, inline_terms * 5)

    # Definition list patterns (dl/dt/dd or wp-block-details)
    deflist_count = len(re.findall(r'<dt[\s>]|<dd[\s>]|wp-block-details', raw_lower))
    score += min(15, deflist_count * 5)

    return clamp(score)


def score_extractability(raw_content, plain_text, title):
    """
    FAQ blocks, quick-answer sections, structured Q&A, TL;DR.
    """
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
                    r'in (a )?nutshell', r'bottom line']
    tldr_hits = sum(1 for pat in tldr_signals if re.search(pat, combined_lower))
    score += min(15, tldr_hits * 8)

    # Structured lists (ordered/unordered) aid extractability
    list_count = len(re.findall(r'<(?:ul|ol)[\s>]', raw_lower))
    score += min(15, list_count * 3)

    return clamp(score)


def score_answer_usefulness(raw_content, plain_text, title):
    """
    Direct answers to questions in headings, conversational query matches.
    """
    score = 0
    combined_lower = (title + " " + plain_text).lower()
    raw_lower = raw_content.lower()

    # Question-format headings
    q_headings = re.findall(
        r'<h[2-4][^>]*>(.*?)</h[2-4]>',
        raw_content, re.I
    )
    question_heading_count = 0
    for h in q_headings:
        h_text = strip_html(h).strip().lower()
        if re.match(r'^(how|what|why|when|where|which|can|do|does|is|are|should)\b', h_text):
            question_heading_count += 1
    score += min(30, question_heading_count * 5)

    # Direct answer signals (sentences that directly answer)
    direct_answer_signals = [
        r'\bthe (?:best|top|most|safest|cheapest)\b',
        r'\bwe recommend\b', r'\bour (?:top )?pick\b',
        r'\byes[,.]', r'\bno[,.]',
        r'\bthe answer is\b', r'\bin short\b',
        r'\bsimply put\b', r'\bto summarise\b', r'\bto summarize\b',
    ]
    answer_hits = sum(1 for pat in direct_answer_signals if re.search(pat, combined_lower))
    score += min(25, answer_hits * 5)

    # Conversational query match (title matches common search patterns)
    conversational_patterns = [
        r'^(how|what|why|when|which|can|do|does|is|are|should)\b',
        r'\bbest\b.*\bfor\b', r'\bhow to\b', r'\btips for\b',
    ]
    title_lower = title.lower()
    conv_hits = sum(1 for pat in conversational_patterns if re.search(pat, title_lower))
    score += min(20, conv_hits * 10)

    # Numbered steps or action items
    step_count = len(re.findall(r'\bstep \d\b|\b\d+\.\s+[A-Z]', plain_text))
    score += min(15, step_count * 3)

    # Bold key answers
    bold_answers = len(re.findall(r'<strong>[^<]{5,80}</strong>', raw_content))
    score += min(10, bold_answers * 2)

    return clamp(score)


def score_reference_quality(raw_content, plain_text, title):
    """
    External citations to trusted domains, source attributions.
    """
    score = 0
    raw_lower = raw_content.lower()
    combined_lower = (title + " " + plain_text).lower()

    # Trusted domain references
    trusted_hit_count = 0
    for domain in TRUSTED_DOMAINS:
        occurrences = len(re.findall(re.escape(domain), raw_lower))
        trusted_hit_count += min(occurrences, 3)  # cap per domain
    score += min(45, trusted_hit_count * 8)

    # Generic external links (any href to external sites)
    external_links = len(re.findall(r'href=["\']https?://(?!pethubonline\.com)', raw_lower))
    score += min(20, external_links * 3)

    # Source attribution phrases
    source_signals = [
        r'according to', r'source:', r'reference:', r'cited from',
        r'as reported by', r'data from', r'published by',
        r'as stated by', r'research from', r'study by',
    ]
    source_hits = sum(1 for pat in source_signals if re.search(pat, combined_lower))
    score += min(20, source_hits * 5)

    # Footnotes or endnotes
    footnote_count = len(re.findall(r'\[\d+\]|<sup>\d+</sup>|<footnote', raw_lower))
    score += min(15, footnote_count * 5)

    return clamp(score)


def score_summary_usefulness(raw_content, plain_text, title):
    """
    'At a glance', summary sections, key takeaways, conclusion sections.
    """
    score = 0
    combined_lower = (title + " " + plain_text).lower()
    raw_lower = raw_content.lower()

    # At a glance / key takeaways in headings
    summary_heading_signals = [
        r'<h[2-4][^>]*>.*?(?:at a glance|key takeaways?|summary|in summary|conclusion|final thoughts|wrap[- ]?up|the bottom line).*?</h[2-4]>',
    ]
    for pat in summary_heading_signals:
        hits = len(re.findall(pat, raw_lower))
        score += min(30, hits * 15)

    # Summary phrases in body
    summary_body_signals = [
        r'\bat a glance\b', r'\bkey takeaways?\b', r'\bin summary\b',
        r'\bto summarise\b', r'\bto summarize\b', r'\bfinal thoughts\b',
        r'\bconclusion\b', r'\bwrap[- ]?up\b', r'\boverall\b.*\brecommend',
        r'\bthe bottom line\b', r'\bhere\'?s what (you|we) (learned|covered)\b',
    ]
    body_hits = sum(1 for pat in summary_body_signals if re.search(pat, combined_lower))
    score += min(35, body_hits * 7)

    # Bullet list near end (last 20% of content)
    content_len = len(raw_content)
    if content_len > 200:
        tail = raw_content[int(content_len * 0.8):].lower()
        tail_lists = len(re.findall(r'<(?:ul|ol)[\s>]', tail))
        score += min(20, tail_lists * 10)

    # Recap / overview signals
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
        "educational_usefulness": score_educational_usefulness(raw_content, plain_text, title),
        "comparison_usefulness": score_comparison_usefulness(raw_content, plain_text, title),
        "trust_reinforcement": score_trust_reinforcement(raw_content, plain_text, title),
        "practical_specificity": score_practical_specificity(raw_content, plain_text, title),
        "glossary_richness": score_glossary_richness(raw_content, plain_text, title),
        "extractability": score_extractability(raw_content, plain_text, title),
        "answer_usefulness": score_answer_usefulness(raw_content, plain_text, title),
        "reference_quality": score_reference_quality(raw_content, plain_text, title),
        "summary_usefulness": score_summary_usefulness(raw_content, plain_text, title),
    }

    # Weighted overall
    overall = sum(dimensions[k] * DIMENSION_WEIGHTS[k] for k in DIMENSION_WEIGHTS)
    overall = clamp(overall)

    # Threshold status
    if overall >= 85:
        threshold = "above_85"
    elif overall >= 70:
        threshold = "above_70"
    else:
        threshold = "below_70"

    # Weakest dimension
    weakest_key = min(dimensions, key=dimensions.get)
    weakest_label = DIMENSION_LABELS[weakest_key]

    return {
        "post_id": post_id,
        "title": title,
        "slug": slug,
        "cluster": cluster,
        "dimensions": dimensions,
        "overall": overall,
        "threshold": threshold,
        "weakest_key": weakest_key,
        "weakest_label": weakest_label,
    }


# ─── CSV Writers ─────────────────────────────────────────────────────────────

def write_scores_csv(results):
    """Write Citation_Confidence_Scores.csv"""
    path = os.path.join(OUTPUT_DIR, "Citation_Confidence_Scores.csv")
    dim_keys = list(DIMENSION_WEIGHTS.keys())

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["post_id", "title", "slug", "cluster"]
        header += [DIMENSION_LABELS[k] for k in dim_keys]
        header += ["overall_citation_confidence", "threshold_status"]
        writer.writerow(header)

        for r in sorted(results, key=lambda x: x["overall"], reverse=True):
            row = [r["post_id"], r["title"], r["slug"], r["cluster"]]
            row += [r["dimensions"][k] for k in dim_keys]
            row += [r["overall"], r["threshold"]]
            writer.writerow(row)

    print(f"  Wrote {path} ({len(results)} rows)")


def write_improvement_csv(results):
    """Write Citation_Improvement_Plan.csv"""
    path = os.path.join(OUTPUT_DIR, "Citation_Improvement_Plan.csv")

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "post_id", "title", "cluster", "current_confidence",
            "weakest_dimension", "improvement_action", "estimated_gain", "priority"
        ])

        # Sort by overall ascending (worst first = highest priority)
        for rank, r in enumerate(sorted(results, key=lambda x: x["overall"]), 1):
            weakest = r["weakest_key"]
            current_dim_score = r["dimensions"][weakest]
            # Estimated gain: if we bring weakest to 70, what's the overall delta?
            potential_new = max(current_dim_score, 70)
            gain = (potential_new - current_dim_score) * DIMENSION_WEIGHTS[weakest]
            gain = round(gain, 1)

            # Priority: P1 if below 50 overall, P2 if 50-70, P3 if above 70
            if r["overall"] < 50:
                priority = "P1-Critical"
            elif r["overall"] < 70:
                priority = "P2-High"
            else:
                priority = "P3-Maintain"

            writer.writerow([
                r["post_id"], r["title"], r["cluster"], r["overall"],
                r["weakest_label"], IMPROVEMENT_ACTIONS[weakest],
                f"+{gain}", priority,
            ])

    print(f"  Wrote {path} ({len(results)} rows)")


def write_cluster_summary_csv(results):
    """Write Cluster_Citation_Summary.csv"""
    path = os.path.join(OUTPUT_DIR, "Cluster_Citation_Summary.csv")

    # Group by cluster
    clusters = defaultdict(list)
    for r in results:
        clusters[r["cluster"]].append(r)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "cluster", "post_count", "avg_citation_confidence",
            "posts_above_70", "posts_above_85",
            "strongest_citation_pages", "weakest_dimension"
        ])

        for cluster_name in CLUSTER_PRIORITY_ORDER + ["Unclassified"]:
            if cluster_name not in clusters:
                continue
            posts = clusters[cluster_name]
            count = len(posts)
            avg_conf = round(sum(p["overall"] for p in posts) / count, 1)
            above_70 = sum(1 for p in posts if p["overall"] >= 70)
            above_85 = sum(1 for p in posts if p["overall"] >= 85)

            # Strongest citation pages (top 3 by overall)
            top_pages = sorted(posts, key=lambda x: x["overall"], reverse=True)[:3]
            strongest = "; ".join(f"{p['title'][:50]} ({p['overall']})" for p in top_pages)

            # Weakest dimension across cluster (lowest avg dimension)
            dim_avgs = {}
            for dk in DIMENSION_WEIGHTS:
                dim_avgs[dk] = sum(p["dimensions"][dk] for p in posts) / count
            weakest_dim_key = min(dim_avgs, key=dim_avgs.get)
            weakest_dim = f"{DIMENSION_LABELS[weakest_dim_key]} (avg {dim_avgs[weakest_dim_key]:.1f})"

            writer.writerow([
                cluster_name, count, avg_conf, above_70, above_85,
                strongest, weakest_dim,
            ])

    print(f"  Wrote {path} ({len(clusters)} clusters)")


# ─── Summary Printer ────────────────────────────────────────────────────────

def print_summary(results):
    """Print comprehensive summary to stdout."""
    total = len(results)
    if total == 0:
        print("No posts found.")
        return

    avg_overall = sum(r["overall"] for r in results) / total
    above_70 = [r for r in results if r["overall"] >= 70]
    above_85 = [r for r in results if r["overall"] >= 85]
    below_70 = [r for r in results if r["overall"] < 70]

    print("\n" + "=" * 80)
    print("  CITATION CONFIDENCE ENGINE - RESULTS SUMMARY")
    print("=" * 80)

    print(f"\n  Total posts analysed:        {total}")
    print(f"  Average citation confidence: {avg_overall:.1f}")
    print(f"  Posts ABOVE 85 (excellent):  {len(above_85)} ({len(above_85)*100/total:.1f}%)")
    print(f"  Posts ABOVE 70 (good):       {len(above_70)} ({len(above_70)*100/total:.1f}%)")
    print(f"  Posts BELOW 70 (needs work): {len(below_70)} ({len(below_70)*100/total:.1f}%)")

    # Per-dimension averages
    print(f"\n  {'DIMENSION AVERAGES':─<60}")
    for dk in DIMENSION_WEIGHTS:
        avg = sum(r["dimensions"][dk] for r in results) / total
        bar = "█" * int(avg / 2.5) + "░" * (40 - int(avg / 2.5))
        print(f"  {DIMENSION_LABELS[dk]:<28} {avg:5.1f}  {bar}")

    # Per-cluster breakdown
    print(f"\n  {'CLUSTER BREAKDOWN':─<60}")
    clusters = defaultdict(list)
    for r in results:
        clusters[r["cluster"]].append(r)

    print(f"  {'Cluster':<22} {'Count':>5} {'Avg':>6} {'>70':>5} {'>85':>5}")
    print(f"  {'─'*22} {'─'*5} {'─'*6} {'─'*5} {'─'*5}")
    for cname in CLUSTER_PRIORITY_ORDER + ["Unclassified"]:
        if cname not in clusters:
            continue
        posts = clusters[cname]
        cavg = sum(p["overall"] for p in posts) / len(posts)
        c70 = sum(1 for p in posts if p["overall"] >= 70)
        c85 = sum(1 for p in posts if p["overall"] >= 85)
        print(f"  {cname:<22} {len(posts):>5} {cavg:>6.1f} {c70:>5} {c85:>5}")

    # Top 10 strongest
    top10 = sorted(results, key=lambda x: x["overall"], reverse=True)[:10]
    print(f"\n  {'TOP 10 STRONGEST CITATION-READY PAGES':─<60}")
    for i, r in enumerate(top10, 1):
        print(f"  {i:>2}. [{r['overall']:>3}] {r['title'][:65]}")
        print(f"       Cluster: {r['cluster']}  |  /{r['slug']}")

    # Top 10 weakest
    bottom10 = sorted(results, key=lambda x: x["overall"])[:10]
    print(f"\n  {'TOP 10 WEAKEST (PRIORITY IMPROVEMENTS)':─<60}")
    for i, r in enumerate(bottom10, 1):
        print(f"  {i:>2}. [{r['overall']:>3}] {r['title'][:65]}")
        print(f"       Weakest: {r['weakest_label']}  |  Cluster: {r['cluster']}")

    # Priority actions
    print(f"\n  {'RECOMMENDED PRIORITY ACTIONS':─<60}")
    p1_posts = [r for r in results if r["overall"] < 50]
    p2_posts = [r for r in results if 50 <= r["overall"] < 70]

    # Find most common weak dimensions
    weak_dim_counts = defaultdict(int)
    for r in below_70:
        weak_dim_counts[r["weakest_key"]] += 1

    print(f"\n  P1-Critical (below 50): {len(p1_posts)} posts need urgent improvement")
    print(f"  P2-High (50-70):        {len(p2_posts)} posts need targeted upgrades")
    print(f"  P3-Maintain (70+):      {len(above_70)} posts in good shape")

    if weak_dim_counts:
        print(f"\n  Most common weak dimensions across below-70 posts:")
        for dk, count in sorted(weak_dim_counts.items(), key=lambda x: -x[1])[:5]:
            print(f"    - {DIMENSION_LABELS[dk]}: {count} posts ({count*100/max(len(below_70),1):.0f}%)")
            print(f"      Action: {IMPROVEMENT_ACTIONS[dk][:100]}...")

    print("\n" + "=" * 80)


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print("=" * 80)
    print("  10AD-D: CITATION CONFIDENCE ENGINE")
    print("  pethubonline.com")
    print("=" * 80)

    # Step 1: Fetch all posts
    print("\n[1/3] Fetching all published posts...")
    posts = fetch_all_posts()
    if not posts:
        print("ERROR: No posts fetched. Exiting.")
        sys.exit(1)
    print(f"  Total posts fetched: {len(posts)}")

    # Step 2: Score every post
    print("\n[2/3] Scoring citation confidence for each post...")
    results = []
    for i, post in enumerate(posts, 1):
        r = score_post(post)
        results.append(r)
        if i % 20 == 0 or i == len(posts):
            print(f"  Scored {i}/{len(posts)} posts...", flush=True)

    # Step 3: Write output CSVs
    print("\n[3/3] Writing output CSVs...")
    write_scores_csv(results)
    write_improvement_csv(results)
    write_cluster_summary_csv(results)

    # Print summary
    print_summary(results)

    print("\nDone. All CSV files written to:")
    print(f"  {OUTPUT_DIR}/Citation_Confidence_Scores.csv")
    print(f"  {OUTPUT_DIR}/Citation_Improvement_Plan.csv")
    print(f"  {OUTPUT_DIR}/Cluster_Citation_Summary.csv")


if __name__ == "__main__":
    main()
