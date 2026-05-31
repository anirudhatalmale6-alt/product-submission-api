#!/usr/bin/env python3
"""
Authority Remediation Plan Generator for PetHub (pethubonline.com)
Audits all published posts for authority metrics and generates CSV.
"""

import subprocess
import json
import time
import csv
import re
from html.parser import HTMLParser
from datetime import datetime, timezone
from collections import defaultdict

# WordPress credentials
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_API = "https://pethubonline.com/wp-json/wp/v2"

OUTPUT_CSV = "/var/lib/freelancer/projects/40416335/phase12_data/Authority_Remediation_Plan.csv"


class HTMLTextExtractor(HTMLParser):
    """Extract plain text from HTML."""
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
    """Strip HTML tags and return plain text."""
    extractor = HTMLTextExtractor()
    try:
        extractor.feed(html_content or '')
    except:
        pass
    return extractor.get_text()


def wp_api_call(endpoint):
    """Make a WordPress REST API call using curl via subprocess."""
    url = f"{WP_API}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", f"{WP_USER}:{WP_PASS}", url],
        capture_output=True, text=True
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  ERROR: Failed to parse response for {endpoint}")
        print(f"  Response: {result.stdout[:200]}")
        return None


def fetch_all_posts():
    """Fetch all published posts with pagination."""
    all_posts = []
    for page in range(1, 5):
        print(f"  Fetching posts page {page}/4...")
        endpoint = f"posts?status=publish&per_page=50&page={page}&_fields=id,title,content,categories,modified"
        data = wp_api_call(endpoint)
        if data is None:
            print(f"  WARNING: Page {page} returned no data")
            break
        if isinstance(data, dict) and data.get('code'):
            print(f"  WARNING: API error on page {page}: {data.get('message', 'unknown')}")
            break
        all_posts.extend(data)
        print(f"  Got {len(data)} posts (total: {len(all_posts)})")
        if len(data) < 50:
            break
        time.sleep(1)
    return all_posts


def fetch_categories():
    """Fetch all categories."""
    print("  Fetching categories...")
    data = wp_api_call("categories?per_page=100")
    if data is None or (isinstance(data, dict) and data.get('code')):
        return {}
    cat_map = {}
    for cat in data:
        cat_map[cat['id']] = cat['name']
    print(f"  Got {len(cat_map)} categories")
    return cat_map


def count_internal_links(html_content):
    """Count internal links (to pethubonline.com)."""
    pattern = r'href=["\']https?://(www\.)?pethubonline\.com[^"\']*["\']'
    matches = re.findall(pattern, html_content or '', re.IGNORECASE)
    return len(matches)


def count_external_links(html_content):
    """Count external links (not pethubonline.com)."""
    all_links = re.findall(r'href=["\']https?://([^"\']+)["\']', html_content or '', re.IGNORECASE)
    external = [l for l in all_links if 'pethubonline.com' not in l.lower()]
    return len(external)


def has_sources_section(html_content):
    """Check for Sources or References heading."""
    pattern = r'<h[2-4][^>]*>[^<]*(Sources|References|Citations|Bibliography|Works Cited)[^<]*</h[2-4]>'
    return bool(re.search(pattern, html_content or '', re.IGNORECASE))


def has_faq_section(html_content):
    """Check for FAQ section."""
    patterns = [
        r'<h[2-4][^>]*>\s*(FAQ|Frequently Asked Questions|Common Questions)\s*</h[2-4]>',
        r'class=["\'][^"\']*faq[^"\']*["\']',
        r'wp-block-yoast-faq',
    ]
    for p in patterns:
        if re.search(p, html_content or '', re.IGNORECASE):
            return True
    return False


def has_comparison_content(html_content):
    """Check for comparison tables or vs. content."""
    patterns = [
        r'<table',
        r'\bvs\.?\b',
        r'comparison',
        r'compared to',
        r'pros and cons',
    ]
    score = 0
    for p in patterns:
        if re.search(p, html_content or '', re.IGNORECASE):
            score += 1
    return score >= 2  # Need at least 2 signals


def count_h2(html_content):
    """Count H2 headings."""
    return len(re.findall(r'<h2', html_content or '', re.IGNORECASE))


def has_trust_signals(html_content):
    """Check for editorial disclosure, author box, etc."""
    patterns = [
        r'editorial',
        r'disclosure',
        r'reviewed by',
        r'written by',
        r'author',
        r'veterinar',
        r'expert',
        r'medically reviewed',
        r'fact.check',
    ]
    found = 0
    for p in patterns:
        if re.search(p, html_content or '', re.IGNORECASE):
            found += 1
    return found >= 1


def calculate_freshness_days(modified_date):
    """Calculate days since last modified."""
    try:
        # WordPress returns dates without timezone, assume UTC
        mod_str = modified_date.replace('Z', '').replace('+00:00', '')
        mod = datetime.fromisoformat(mod_str).replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - mod
        return max(0, delta.days)
    except Exception as e:
        print(f"  Date parse error: {modified_date} -> {e}")
        return 999


def calculate_authority_score(metrics):
    """
    Calculate authority score 0-100 based on metrics.

    Scoring breakdown:
    - Word count: 0-20 pts (2000+ words = 20)
    - Internal links: 0-10 pts (5+ = 10)
    - External references: 0-15 pts (5+ = 15)
    - Sources section: 0-15 pts
    - FAQ section: 0-10 pts
    - Comparison content: 0-5 pts
    - Freshness: 0-10 pts (< 90 days = 10)
    - H2 structure: 0-10 pts (5+ H2s = 10)
    - Trust signals: 0-5 pts
    """
    score = 0

    # Word count (0-20)
    wc = metrics['word_count']
    if wc >= 2000:
        score += 20
    elif wc >= 1500:
        score += 15
    elif wc >= 1000:
        score += 10
    elif wc >= 500:
        score += 5

    # Internal links (0-10)
    il = metrics['internal_links']
    if il >= 5:
        score += 10
    elif il >= 3:
        score += 7
    elif il >= 1:
        score += 4

    # External references (0-15)
    er = metrics['external_refs']
    if er >= 5:
        score += 15
    elif er >= 3:
        score += 10
    elif er >= 1:
        score += 5

    # Sources section (0-15)
    if metrics['has_sources']:
        score += 15

    # FAQ section (0-10)
    if metrics['has_faq']:
        score += 10

    # Comparison content (0-5)
    if metrics['has_comparison']:
        score += 5

    # Freshness (0-10)
    fd = metrics['freshness_days']
    if fd <= 30:
        score += 10
    elif fd <= 90:
        score += 7
    elif fd <= 180:
        score += 4
    elif fd <= 365:
        score += 2

    # H2 structure (0-10)
    h2 = metrics['h2_count']
    if h2 >= 5:
        score += 10
    elif h2 >= 3:
        score += 7
    elif h2 >= 1:
        score += 4

    # Trust signals (0-5)
    if metrics['trust_signals']:
        score += 5

    return score


def identify_issues(metrics):
    """Identify authority issues for a post."""
    issues = []
    if metrics['word_count'] < 1000:
        issues.append("thin content (<1000 words)")
    if metrics['internal_links'] == 0:
        issues.append("no internal links")
    if metrics['external_refs'] == 0:
        issues.append("no external references")
    if not metrics['has_sources']:
        issues.append("no sources/references section")
    if not metrics['has_faq']:
        issues.append("no FAQ section")
    if metrics['freshness_days'] > 180:
        issues.append(f"stale content ({metrics['freshness_days']}d)")
    if metrics['h2_count'] < 3:
        issues.append("weak heading structure")
    if not metrics['trust_signals']:
        issues.append("no trust signals")
    if metrics['external_refs'] < 3:
        issues.append("insufficient citations")
    return "; ".join(issues) if issues else "none"


def recommend_actions(metrics):
    """Generate remediation actions based on issues."""
    actions = []
    if metrics['word_count'] < 1000:
        actions.append("Expand content to 1500+ words with expert insights")
    if metrics['internal_links'] == 0:
        actions.append("Add 3-5 internal links to related posts")
    elif metrics['internal_links'] < 3:
        actions.append("Increase internal links to 3+")
    if metrics['external_refs'] == 0:
        actions.append("Add 3-5 authoritative external citations (vet journals, research)")
    elif metrics['external_refs'] < 3:
        actions.append("Add more authoritative citations")
    if not metrics['has_sources']:
        actions.append("Add Sources/References section with cited links")
    if not metrics['has_faq']:
        actions.append("Add FAQ section with 3-5 common questions")
    if metrics['freshness_days'] > 180:
        actions.append("Update content with latest information and reset modified date")
    if metrics['h2_count'] < 3:
        actions.append("Restructure with 5+ H2 headings for better organization")
    if not metrics['trust_signals']:
        actions.append("Add author bio, editorial disclosure, or expert review note")
    if not metrics['has_comparison']:
        actions.append("Consider adding comparison table or pros/cons")
    return "; ".join(actions) if actions else "none needed"


def main():
    print("=" * 70)
    print("AUTHORITY REMEDIATION AUDIT - PetHub (pethubonline.com)")
    print("=" * 70)
    print()

    # Fetch data
    print("[1/3] Fetching posts from WordPress API...")
    posts = fetch_all_posts()
    print(f"  Total posts fetched: {len(posts)}")
    print()

    print("[2/3] Fetching categories...")
    categories = fetch_categories()
    print()

    # Analyze posts
    print("[3/3] Analyzing authority metrics for each post...")
    results = []

    for i, post in enumerate(posts):
        post_id = post['id']
        title = post['title']['rendered'] if isinstance(post['title'], dict) else post['title']
        content = post['content']['rendered'] if isinstance(post['content'], dict) else post.get('content', '')
        modified = post.get('modified', '')
        cat_ids = post.get('categories', [])

        # Determine category/cluster
        cluster = "Uncategorized"
        if cat_ids and categories:
            # Use first non-"Uncategorized" category
            for cid in cat_ids:
                name = categories.get(cid, '')
                if name and name.lower() != 'uncategorized':
                    cluster = name
                    break
            if cluster == "Uncategorized" and cat_ids:
                cluster = categories.get(cat_ids[0], "Uncategorized")

        # Compute metrics
        plain_text = strip_html(content)
        word_count = len(plain_text.split())

        metrics = {
            'word_count': word_count,
            'internal_links': count_internal_links(content),
            'external_refs': count_external_links(content),
            'has_sources': has_sources_section(content),
            'has_faq': has_faq_section(content),
            'has_comparison': has_comparison_content(content),
            'freshness_days': calculate_freshness_days(modified),
            'h2_count': count_h2(content),
            'trust_signals': has_trust_signals(content),
        }

        authority_score = calculate_authority_score(metrics)
        issues = identify_issues(metrics)
        actions = recommend_actions(metrics)

        results.append({
            'cluster': cluster,
            'post_id': post_id,
            'title': title,
            'authority_score': authority_score,
            'word_count': metrics['word_count'],
            'internal_links': metrics['internal_links'],
            'external_refs': metrics['external_refs'],
            'has_sources': 'Yes' if metrics['has_sources'] else 'No',
            'has_faq': 'Yes' if metrics['has_faq'] else 'No',
            'has_comparison': 'Yes' if metrics['has_comparison'] else 'No',
            'freshness_days': metrics['freshness_days'],
            'issues': issues,
            'remediation_actions': actions,
        })

        if (i + 1) % 20 == 0:
            print(f"  Analyzed {i+1}/{len(posts)} posts...")

    print(f"  Analyzed all {len(posts)} posts.")
    print()

    # Sort by authority_score ascending (worst first)
    results.sort(key=lambda x: x['authority_score'])

    # Write CSV
    print(f"Writing CSV to {OUTPUT_CSV}...")
    fieldnames = [
        'cluster', 'post_id', 'title', 'authority_score', 'word_count',
        'internal_links', 'external_refs', 'has_sources', 'has_faq',
        'has_comparison', 'freshness_days', 'issues', 'remediation_actions'
    ]

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"  CSV written with {len(results)} rows.")
    print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()

    # Cluster rankings
    cluster_scores = defaultdict(list)
    for r in results:
        cluster_scores[r['cluster']].append(r['authority_score'])

    print("CLUSTER RANKINGS (by average authority score):")
    print("-" * 50)
    cluster_avgs = []
    for cluster, scores in cluster_scores.items():
        avg = sum(scores) / len(scores)
        cluster_avgs.append((cluster, avg, len(scores)))

    cluster_avgs.sort(key=lambda x: x[1])
    for rank, (cluster, avg, count) in enumerate(cluster_avgs, 1):
        print(f"  {rank:2}. {cluster:<35} Avg: {avg:5.1f}  ({count} posts)")

    print()
    print("WEAKEST POSTS (bottom 15):")
    print("-" * 50)
    for r in results[:15]:
        title_short = r['title'][:50] + "..." if len(r['title']) > 50 else r['title']
        print(f"  ID {r['post_id']:5} | Score: {r['authority_score']:3} | {title_short}")
        print(f"         Issues: {r['issues'][:80]}")
        print()

    # Top remediation actions
    print("TOP REMEDIATION ACTIONS (by frequency):")
    print("-" * 50)
    action_counts = defaultdict(int)
    for r in results:
        if r['remediation_actions'] != 'none needed':
            for action in r['remediation_actions'].split('; '):
                action_counts[action] += 1

    sorted_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)
    for action, count in sorted_actions[:10]:
        print(f"  [{count:3} posts] {action}")

    print()
    print("=" * 70)
    avg_all = sum(r['authority_score'] for r in results) / len(results) if results else 0
    below_50 = sum(1 for r in results if r['authority_score'] < 50)
    print(f"OVERALL: {len(results)} posts audited | Avg score: {avg_all:.1f}/100 | Below 50: {below_50} posts")
    print(f"CSV saved: {OUTPUT_CSV}")
    print("=" * 70)


if __name__ == "__main__":
    main()
