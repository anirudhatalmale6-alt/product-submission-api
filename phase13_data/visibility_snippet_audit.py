#!/usr/bin/env python3
"""
Phase 13A: Visibility Dominance - Snippet Readiness Audit
Audits all published posts for Featured Snippet optimization potential.
Generates Visibility_Opportunity_Report.csv
"""

import subprocess
import json
import time
import csv
import re
from html.parser import HTMLParser

WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_API = "https://pethubonline.com/wp-json/wp/v2"

OUTPUT_CSV = "/var/lib/freelancer/projects/40416335/phase13_data/Visibility_Opportunity_Report.csv"


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip_tags = {'script', 'style'}
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self._skip = True

    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            self.text_parts.append(data)

    def get_text(self):
        return ' '.join(self.text_parts)


def strip_html(html_content):
    extractor = HTMLTextExtractor()
    try:
        extractor.feed(html_content or '')
    except:
        pass
    return extractor.get_text()


def wp_api_call(endpoint):
    url = f"{WP_API}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", f"{WP_USER}:{WP_PASS}", url],
        capture_output=True, text=True
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def fetch_all_posts():
    all_posts = []
    for page in range(1, 5):
        print(f"  Fetching posts page {page}...")
        endpoint = f"posts?status=publish&per_page=50&page={page}&_fields=id,title,content,categories,slug"
        data = wp_api_call(endpoint)
        if data is None or (isinstance(data, dict) and data.get('code')):
            break
        all_posts.extend(data)
        if len(data) < 50:
            break
        time.sleep(1)
    return all_posts


def fetch_categories():
    data = wp_api_call("categories?per_page=100")
    if data is None or (isinstance(data, dict) and data.get('code')):
        return {}
    return {cat['id']: cat['name'] for cat in data}


def has_definition_block(html):
    """Check for definition-style content (What is X?, X is defined as...)"""
    patterns = [
        r'<p>[^<]{0,50}(is a |are a |refers to |defined as |means )',
        r'<h[2-4][^>]*>[^<]*(What is|What are|Definition of)[^<]*</h[2-4]>',
        r'<strong>[^<]*(What is|What are)[^<]*</strong>',
    ]
    for p in patterns:
        if re.search(p, html or '', re.IGNORECASE):
            return True
    return False


def has_numbered_list(html):
    """Check for ordered lists (how-to snippet potential)"""
    return bool(re.search(r'<ol', html or '', re.IGNORECASE))


def has_bullet_list(html):
    """Check for unordered lists (list snippet potential)"""
    return bool(re.search(r'<ul', html or '', re.IGNORECASE))


def count_tables(html):
    """Count tables (table snippet potential)"""
    return len(re.findall(r'<table', html or '', re.IGNORECASE))


def has_how_to_content(html):
    """Check for how-to structured content"""
    patterns = [
        r'<h[2-4][^>]*>[^<]*(How to|Step \d|Steps to|Guide to)[^<]*</h[2-4]>',
        r'(step 1|step 2|first,|second,|finally,)',
    ]
    score = 0
    for p in patterns:
        if re.search(p, html or '', re.IGNORECASE):
            score += 1
    return score >= 1


def has_faq_schema(html):
    """Check for FAQ-style Q&A blocks"""
    patterns = [
        r'wp-block-yoast-faq',
        r'class=["\'][^"\']*faq[^"\']*["\']',
        r'<h[2-4][^>]*>\s*(FAQ|Frequently Asked)[^<]*</h[2-4]>',
        r'schema.*FAQPage',
    ]
    for p in patterns:
        if re.search(p, html or '', re.IGNORECASE):
            return True
    return False


def has_comparison_table(html):
    """Check for comparison/vs content"""
    patterns = [
        r'<table[^>]*>.*?(vs|versus|comparison|compared)',
        r'\bvs\.?\b.*<table',
        r'<table.*class=["\'][^"\']*comparison',
    ]
    for p in patterns:
        if re.search(p, html or '', re.IGNORECASE | re.DOTALL):
            return True
    if '<table' in (html or '').lower() and re.search(r'\bvs\.?\b|versus|comparison', html or '', re.IGNORECASE):
        return True
    return False


def has_direct_answer(html):
    """Check if first paragraph gives a direct answer (paragraph snippet potential)"""
    first_p = re.search(r'<p[^>]*>([^<]{40,300})</p>', html or '')
    if first_p:
        text = first_p.group(1).lower()
        answer_signals = ['is a ', 'are a ', 'the best ', 'you should ', 'the answer ',
                         'typically ', 'usually ', 'generally ', 'on average ']
        for signal in answer_signals:
            if signal in text:
                return True
    return False


def count_h2_with_questions(html):
    """Count H2s that are questions (People Also Ask potential)"""
    question_h2s = re.findall(
        r'<h2[^>]*>[^<]*(what|how|why|when|where|which|can|do|does|is|are|should)[^<]*\??\s*</h2>',
        html or '', re.IGNORECASE
    )
    return len(question_h2s)


def has_key_takeaways(html):
    """Check for key takeaways / summary box"""
    patterns = [
        r'(Key Takeaway|Key Point|Quick Summary|At a Glance|TL;DR|Bottom Line)',
        r'class=["\'][^"\']*takeaway[^"\']*["\']',
        r'class=["\'][^"\']*summary[^"\']*["\']',
    ]
    for p in patterns:
        if re.search(p, html or '', re.IGNORECASE):
            return True
    return False


def calculate_snippet_readiness(metrics):
    """Calculate snippet readiness score 0-100"""
    score = 0

    # Definition block (paragraph snippet) - 15pts
    if metrics['has_definition']:
        score += 15

    # Numbered list (how-to snippet) - 15pts
    if metrics['has_numbered_list']:
        score += 15

    # Bullet list (list snippet) - 10pts
    if metrics['has_bullet_list']:
        score += 10

    # Tables (table snippet) - 15pts
    if metrics['table_count'] > 0:
        score += 15

    # FAQ schema (FAQ rich result) - 10pts
    if metrics['has_faq']:
        score += 10

    # How-to content - 10pts
    if metrics['has_how_to']:
        score += 10

    # Direct answer in first paragraph - 10pts
    if metrics['has_direct_answer']:
        score += 10

    # Question H2s (PAA potential) - 10pts
    if metrics['question_h2_count'] >= 3:
        score += 10
    elif metrics['question_h2_count'] >= 1:
        score += 5

    # Key takeaways (AI citation potential) - 5pts
    if metrics['has_key_takeaways']:
        score += 5

    return score


def identify_snippet_opportunities(metrics):
    """Identify which snippet types this post could target"""
    opportunities = []
    if metrics['has_definition'] or metrics['has_direct_answer']:
        opportunities.append("Paragraph Snippet")
    if metrics['has_numbered_list'] or metrics['has_how_to']:
        opportunities.append("How-To Snippet")
    if metrics['has_bullet_list']:
        opportunities.append("List Snippet")
    if metrics['table_count'] > 0:
        opportunities.append("Table Snippet")
    if metrics['has_faq']:
        opportunities.append("FAQ Rich Result")
    if metrics['question_h2_count'] >= 2:
        opportunities.append("People Also Ask")
    if metrics['has_key_takeaways']:
        opportunities.append("AI Citation")
    return ", ".join(opportunities) if opportunities else "None identified"


def recommend_snippet_actions(metrics):
    """Generate snippet optimization recommendations"""
    actions = []
    if not metrics['has_definition']:
        actions.append("Add definition paragraph in first 100 words")
    if not metrics['has_numbered_list'] and not metrics['has_how_to']:
        actions.append("Add numbered step-by-step list or how-to section")
    if not metrics['has_bullet_list']:
        actions.append("Add concise bullet-point summary list")
    if metrics['table_count'] == 0:
        actions.append("Add comparison or data table")
    if not metrics['has_faq']:
        actions.append("Add FAQ section with 3-5 questions")
    if not metrics['has_direct_answer']:
        actions.append("Rewrite first paragraph as direct answer")
    if metrics['question_h2_count'] < 2:
        actions.append("Reframe H2s as questions for PAA targeting")
    if not metrics['has_key_takeaways']:
        actions.append("Add Key Takeaways box for AI citation")
    return "; ".join(actions) if actions else "Fully optimized"


def main():
    print("=" * 70)
    print("PHASE 13A: VISIBILITY DOMINANCE - SNIPPET READINESS AUDIT")
    print("=" * 70)
    print()

    print("[1/3] Fetching published posts...")
    posts = fetch_all_posts()
    print(f"  Total: {len(posts)} posts")
    print()

    print("[2/3] Fetching categories...")
    categories = fetch_categories()
    print(f"  Total: {len(categories)} categories")
    print()

    print("[3/3] Analyzing snippet readiness...")
    results = []

    for i, post in enumerate(posts):
        post_id = post['id']
        title = post['title']['rendered'] if isinstance(post['title'], dict) else post['title']
        content = post['content']['rendered'] if isinstance(post['content'], dict) else post.get('content', '')
        slug = post.get('slug', '')
        cat_ids = post.get('categories', [])

        cluster = "Uncategorized"
        if cat_ids and categories:
            for cid in cat_ids:
                name = categories.get(cid, '')
                if name and name.lower() != 'uncategorized':
                    cluster = name
                    break

        plain_text = strip_html(content)
        word_count = len(plain_text.split())

        metrics = {
            'has_definition': has_definition_block(content),
            'has_numbered_list': has_numbered_list(content),
            'has_bullet_list': has_bullet_list(content),
            'table_count': count_tables(content),
            'has_how_to': has_how_to_content(content),
            'has_faq': has_faq_schema(content),
            'has_comparison': has_comparison_table(content),
            'has_direct_answer': has_direct_answer(content),
            'question_h2_count': count_h2_with_questions(content),
            'has_key_takeaways': has_key_takeaways(content),
        }

        snippet_score = calculate_snippet_readiness(metrics)
        opportunities = identify_snippet_opportunities(metrics)
        actions = recommend_snippet_actions(metrics)

        results.append({
            'cluster': cluster,
            'post_id': post_id,
            'title': title,
            'slug': slug,
            'word_count': word_count,
            'snippet_readiness_score': snippet_score,
            'has_definition': 'Yes' if metrics['has_definition'] else 'No',
            'has_numbered_list': 'Yes' if metrics['has_numbered_list'] else 'No',
            'has_bullet_list': 'Yes' if metrics['has_bullet_list'] else 'No',
            'table_count': metrics['table_count'],
            'has_faq': 'Yes' if metrics['has_faq'] else 'No',
            'has_how_to': 'Yes' if metrics['has_how_to'] else 'No',
            'has_direct_answer': 'Yes' if metrics['has_direct_answer'] else 'No',
            'question_h2_count': metrics['question_h2_count'],
            'has_key_takeaways': 'Yes' if metrics['has_key_takeaways'] else 'No',
            'snippet_opportunities': opportunities,
            'optimization_actions': actions,
        })

        if (i + 1) % 25 == 0:
            print(f"  Analyzed {i+1}/{len(posts)}...")

    print(f"  Done: {len(posts)} posts analyzed")
    print()

    # Sort by snippet_readiness_score ascending
    results.sort(key=lambda x: x['snippet_readiness_score'])

    # Write CSV
    fieldnames = [
        'cluster', 'post_id', 'title', 'slug', 'word_count', 'snippet_readiness_score',
        'has_definition', 'has_numbered_list', 'has_bullet_list', 'table_count',
        'has_faq', 'has_how_to', 'has_direct_answer', 'question_h2_count',
        'has_key_takeaways', 'snippet_opportunities', 'optimization_actions'
    ]

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"CSV written: {OUTPUT_CSV}")
    print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    avg_score = sum(r['snippet_readiness_score'] for r in results) / len(results) if results else 0
    above_50 = sum(1 for r in results if r['snippet_readiness_score'] >= 50)
    above_75 = sum(1 for r in results if r['snippet_readiness_score'] >= 75)
    below_25 = sum(1 for r in results if r['snippet_readiness_score'] < 25)

    print(f"  Total posts: {len(results)}")
    print(f"  Average snippet readiness: {avg_score:.1f}/100")
    print(f"  Above 75% (strong): {above_75}")
    print(f"  Above 50% (moderate): {above_50}")
    print(f"  Below 25% (weak): {below_25}")
    print()

    # Cluster breakdown
    from collections import defaultdict
    cluster_scores = defaultdict(list)
    for r in results:
        cluster_scores[r['cluster']].append(r['snippet_readiness_score'])

    print("CLUSTER SNIPPET READINESS:")
    print("-" * 50)
    cluster_avgs = [(c, sum(s)/len(s), len(s)) for c, s in cluster_scores.items()]
    cluster_avgs.sort(key=lambda x: x[1])
    for cluster, avg, count in cluster_avgs:
        print(f"  {cluster:<35} Avg: {avg:5.1f}  ({count} posts)")

    print()
    print("WEAKEST POSTS (bottom 10):")
    print("-" * 50)
    for r in results[:10]:
        title_short = r['title'][:50] + "..." if len(r['title']) > 50 else r['title']
        print(f"  ID {r['post_id']:5} | Score: {r['snippet_readiness_score']:3} | {title_short}")
        print(f"         Opportunities: {r['snippet_opportunities']}")
        print()

    # Opportunity counts
    print("SNIPPET OPPORTUNITY DISTRIBUTION:")
    print("-" * 50)
    opp_counts = defaultdict(int)
    for r in results:
        for opp in r['snippet_opportunities'].split(', '):
            if opp and opp != "None identified":
                opp_counts[opp] += 1

    for opp, count in sorted(opp_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {opp:<25} {count} posts ready")

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
