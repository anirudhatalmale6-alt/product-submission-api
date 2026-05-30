#!/usr/bin/env python3
"""
Phase 11AC - AI Citation Observation Framework (Enhanced)
=========================================================
Reads existing AI_Citation_Observation.csv and enriches each post with
deeper citability sub-scores by fetching actual post content from WordPress API.

Output: AI_Citation_Enhanced.csv (168 rows)
"""

import csv
import json
import math
import os
import re
import subprocess
import time
import html

WORK_DIR = "/var/lib/freelancer/projects/40416335/phase11w_data"
INPUT_CSV = os.path.join(WORK_DIR, "AI_Citation_Observation.csv")
OUTPUT_CSV = os.path.join(WORK_DIR, "AI_Citation_Enhanced.csv")

WP_URL = "https://pethubonline.com/wp-json/wp/v2/posts"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"

CATEGORY_MAP = {
    1377: "Cat Supplies", 1459: "Cat Toys", 1413: "Indoor Cats",
    1376: "Dog Supplies", 1397: "Pet Care", 1401: "Dog Beds",
    1489: "Dog Care", 1467: "Dog Food", 1422: "Dog Harnesses",
    1450: "Dog Health", 1441: "Dog Toys", 1442: "Puppy Care",
    1474: "Training Supplies", 1: "Uncategorized"
}


def fetch_post(post_id):
    """Fetch a single post from WordPress API."""
    time.sleep(2)
    url = f"{WP_URL}/{post_id}"
    result = subprocess.run(
        ["curl", "-s", "-u", f"{WP_USER}:{WP_PASS}", url],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        print(f"  [ERROR] curl failed for post {post_id}: {result.stderr}")
        return None
    try:
        data = json.loads(result.stdout)
        if "id" not in data:
            print(f"  [WARN] No 'id' in response for post {post_id}")
            return None
        return data
    except json.JSONDecodeError:
        print(f"  [ERROR] Invalid JSON for post {post_id}")
        return None


def strip_html(text):
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    return re.sub(r'\s+', ' ', text).strip()


def compute_structured_data_score(content_html, notes_str):
    """Score 0-100: FAQ schema, lists, tables, data points."""
    score = 0

    # FAQ count from notes
    faq_match = re.search(r'(\d+)\s*FAQs?', notes_str)
    faq_count = int(faq_match.group(1)) if faq_match else 0
    score += min(faq_count * 2.5, 25)  # up to 25 pts for FAQs

    # Lists/tables from notes
    lt_match = re.search(r'(\d+)\s*lists?/tables?', notes_str)
    lt_count = int(lt_match.group(1)) if lt_match else 0
    score += min(lt_count * 1.5, 25)  # up to 25 pts for lists/tables

    # Actual HTML structure checks
    table_count = len(re.findall(r'<table', content_html, re.IGNORECASE))
    score += min(table_count * 5, 15)  # up to 15 pts for HTML tables

    ol_ul_count = len(re.findall(r'<(ol|ul)', content_html, re.IGNORECASE))
    score += min(ol_ul_count * 1, 10)  # up to 10 pts for list elements

    # Schema markup presence
    if 'application/ld+json' in content_html or 'FAQPage' in content_html:
        score += 10

    # Data points: numbers with units (e.g., "£29.99", "15kg", "30 minutes")
    data_points = len(re.findall(r'(?:£\d+|\d+\s*(?:kg|g|cm|mm|ml|minutes?|hours?|days?|weeks?|months?|years?|%)\b)', content_html, re.IGNORECASE))
    score += min(data_points * 0.5, 15)  # up to 15 pts for data points

    return min(round(score, 1), 100)


def compute_authority_signals(content_html, notes_str):
    """Score 0-100: source citations, expert references, methodology links."""
    score = 0
    text = strip_html(content_html).lower()

    # Source citations (links count from notes)
    link_match = re.search(r'(\d+)\s*links?', notes_str)
    link_count = int(link_match.group(1)) if link_match else 0
    score += min(link_count * 0.8, 25)  # up to 25 pts for links

    # External authority references
    authority_domains = ['rspca', 'kennel club', 'pdsa', 'blue cross', 'battersea',
                         'vet', 'veterinary', 'bva', 'rcvs', 'defra', 'pet food manufacturers',
                         'pfma', 'dogs trust', 'cats protection', 'university', 'study',
                         'research', 'journal', 'clinical', 'peer-reviewed']
    authority_hits = sum(1 for d in authority_domains if d in text)
    score += min(authority_hits * 3, 25)  # up to 25 pts for authority refs

    # Methodology/transparency signals
    methodology_terms = ['how we compare', 'how this information was gathered',
                         'our methodology', 'sources and references', 'evidence-based',
                         'research standards', 'how we test', 'criteria', 'evaluation']
    method_hits = sum(1 for m in methodology_terms if m in text)
    score += min(method_hits * 5, 25)  # up to 25 pts for methodology

    # Expert quotes / citations
    expert_patterns = [r'according to', r'experts? (?:say|recommend|suggest|advise)',
                       r'veterinar(?:y|ian)', r'animal behaviourist', r'nutritionist']
    expert_hits = sum(len(re.findall(p, text)) for p in expert_patterns)
    score += min(expert_hits * 3, 25)  # up to 25 pts for expert refs

    return min(round(score, 1), 100)


def compute_answer_format_score(content_html, notes_str):
    """Score 0-100: how well content matches AI answer patterns."""
    score = 0
    text = strip_html(content_html)

    # H2 count (structured sections)
    h2_match = re.search(r'(\d+)\s*H2s?', notes_str)
    h2_count = int(h2_match.group(1)) if h2_match else 0
    score += min(h2_count * 1.5, 20)  # up to 20 pts for H2 structure

    # Question-format headings (AI loves Q&A format)
    question_headings = len(re.findall(r'<h[2-4][^>]*>(?:[^<]*\?)', content_html, re.IGNORECASE))
    score += min(question_headings * 3, 20)  # up to 20 pts for Q&A headings

    # Concise opening paragraphs (first <p> under 60 words = AI-friendly)
    first_paras = re.findall(r'<p[^>]*>(.*?)</p>', content_html[:3000], re.DOTALL | re.IGNORECASE)
    if first_paras:
        first_para_words = len(strip_html(first_paras[0]).split())
        if first_para_words <= 40:
            score += 15
        elif first_para_words <= 60:
            score += 10
        elif first_para_words <= 80:
            score += 5

    # Definition patterns ("X is a...", "X refers to...")
    definition_patterns = len(re.findall(r'(?:is a|refers to|means|defined as|known as)', text.lower()))
    score += min(definition_patterns * 2, 15)  # up to 15 pts

    # Bullet point / numbered list density
    list_items = len(re.findall(r'<li', content_html, re.IGNORECASE))
    word_count = len(text.split())
    if word_count > 0:
        list_density = list_items / (word_count / 1000)
        score += min(list_density * 2, 15)  # up to 15 pts for list density

    # Step-by-step / how-to patterns
    howto_patterns = len(re.findall(r'(?:step \d|first,|second,|third,|finally,|how to)', text.lower()))
    score += min(howto_patterns * 2, 15)  # up to 15 pts

    return min(round(score, 1), 100)


def compute_uniqueness_score(content_html, title, cluster):
    """Score 0-100: unique data, original analysis, UK-specific info."""
    score = 0
    text = strip_html(content_html).lower()

    # UK-specific content
    uk_terms = ['uk', 'united kingdom', 'britain', 'british', 'england', 'scotland',
                'wales', 'london', 'nhs', '£', 'rspca', 'kennel club', 'defra',
                'pets at home', 'poundland', 'tesco', 'argos', 'amazon.co.uk',
                'royal mail', 'dpd', 'hermes']
    uk_hits = sum(1 for t in uk_terms if t in text)
    score += min(uk_hits * 2.5, 25)  # up to 25 pts for UK specificity

    # Original data / comparisons
    comparison_patterns = ['compared:', 'vs', 'versus', 'comparison', 'head-to-head',
                           'our testing', 'we tested', 'we found', 'our analysis',
                           'our research', 'based on our']
    comparison_hits = sum(1 for c in comparison_patterns if c in text)
    score += min(comparison_hits * 5, 25)  # up to 25 pts for original analysis

    # Specific data points (prices, dimensions, ratings)
    price_mentions = len(re.findall(r'£\d+', text))
    score += min(price_mentions * 1.5, 15)  # up to 15 pts for pricing data

    # Year-specific / current data
    year_mentions = len(re.findall(r'202[5-6]', text))
    score += min(year_mentions * 2, 10)  # up to 10 pts for current data

    # Niche/specialist content
    specialist_terms = ['breed-specific', 'age-appropriate', 'senior', 'puppy', 'kitten',
                        'large breed', 'small breed', 'brachycephalic', 'long-haired',
                        'indoor cat', 'working dog', 'rescue']
    specialist_hits = sum(1 for s in specialist_terms if s in text)
    score += min(specialist_hits * 3, 15)  # up to 15 pts for niche content

    # Unique formatting (infographics, checklists, schedules)
    format_patterns = ['checklist', 'schedule', 'timetable', 'timeline', 'at a glance',
                       'quick reference', 'cheat sheet', 'printable']
    format_hits = sum(1 for f in format_patterns if f in text)
    score += min(format_hits * 5, 10)  # up to 10 pts for unique formats

    return min(round(score, 1), 100)


def main():
    # Read existing citation data
    rows = []
    with open(INPUT_CSV, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    print(f"Loaded {len(rows)} posts from AI_Citation_Observation.csv")

    # Fetch content for each post and compute enhanced scores
    enhanced_rows = []
    total = len(rows)

    for i, row in enumerate(rows):
        post_id = row['post_id']
        title = row['title']
        cluster = row['cluster']
        notes = row.get('notes', '')

        print(f"[{i+1}/{total}] Processing post {post_id}: {title[:50]}...")

        post_data = fetch_post(post_id)

        if post_data:
            content_html = post_data.get('content', {}).get('rendered', '')

            structured_data = compute_structured_data_score(content_html, notes)
            authority = compute_authority_signals(content_html, notes)
            answer_format = compute_answer_format_score(content_html, notes)
            uniqueness = compute_uniqueness_score(content_html, title, cluster)
        else:
            # Fallback: estimate from notes only
            print(f"  [FALLBACK] Using notes-only estimation for post {post_id}")
            content_html = ""
            structured_data = compute_structured_data_score("", notes)
            authority = compute_authority_signals("", notes)
            answer_format = compute_answer_format_score("", notes)
            uniqueness = compute_uniqueness_score("", title, cluster)

        # Compute enhanced citability score (weighted average of all factors)
        original_score = float(row['citability_score'])
        enhanced_score = round(
            original_score * 0.30 +
            structured_data * 0.20 +
            authority * 0.15 +
            answer_format * 0.20 +
            uniqueness * 0.15,
            1
        )

        # Determine confidence level based on data quality
        if post_data:
            enhanced_confidence = "high" if enhanced_score >= 55 else "medium" if enhanced_score >= 40 else "low"
        else:
            enhanced_confidence = row.get('confidence_level', 'low')

        enhanced_rows.append({
            'post_id': post_id,
            'title': title,
            'cluster': cluster,
            'url_slug': row['url_slug'],
            'citation_status': row['citation_status'],
            'original_citability_score': row['citability_score'],
            'structured_data_score': structured_data,
            'authority_signals_score': authority,
            'answer_format_score': answer_format,
            'uniqueness_score': uniqueness,
            'enhanced_citability_score': enhanced_score,
            'word_count': row['word_count'],
            'confidence_level': enhanced_confidence,
            'has_structured_data': row['has_structured_data'],
            'has_source_citations': row['has_source_citations'],
            'has_qa_format': row['has_qa_format'],
            'has_unique_data': row['has_unique_data'],
            'notes': notes
        })

    # Sort by enhanced_citability_score descending
    enhanced_rows.sort(key=lambda x: float(x['enhanced_citability_score']), reverse=True)

    # Write output
    fieldnames = [
        'post_id', 'title', 'cluster', 'url_slug', 'citation_status',
        'original_citability_score', 'structured_data_score', 'authority_signals_score',
        'answer_format_score', 'uniqueness_score', 'enhanced_citability_score',
        'word_count', 'confidence_level', 'has_structured_data', 'has_source_citations',
        'has_qa_format', 'has_unique_data', 'notes'
    ]

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enhanced_rows)

    print(f"\nWrote {len(enhanced_rows)} rows to {OUTPUT_CSV}")

    # Summary stats
    scores = [float(r['enhanced_citability_score']) for r in enhanced_rows]
    print(f"\nSummary:")
    print(f"  Min score: {min(scores)}")
    print(f"  Max score: {max(scores)}")
    print(f"  Mean score: {round(sum(scores)/len(scores), 1)}")
    print(f"  High confidence: {sum(1 for r in enhanced_rows if r['confidence_level']=='high')}")
    print(f"  Medium confidence: {sum(1 for r in enhanced_rows if r['confidence_level']=='medium')}")
    print(f"  Low confidence: {sum(1 for r in enhanced_rows if r['confidence_level']=='low')}")

    # Top 10
    print(f"\nTop 10 by enhanced citability:")
    for r in enhanced_rows[:10]:
        print(f"  {r['enhanced_citability_score']} | {r['title'][:60]} | struct={r['structured_data_score']} auth={r['authority_signals_score']} ans={r['answer_format_score']} uniq={r['uniqueness_score']}")


if __name__ == "__main__":
    main()
