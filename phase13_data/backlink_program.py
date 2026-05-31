#!/usr/bin/env python3
"""
Phase 13J: Backlink & Digital PR Program
Identifies link-worthy content and generates outreach targets.
Builds Backlink_Acquisition_Dashboard.csv
"""

import subprocess
import json
import csv
import re
import time
from html.parser import HTMLParser
from collections import defaultdict

WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_API = "https://pethubonline.com/wp-json/wp/v2"

OUTPUT_CSV = "/var/lib/freelancer/projects/40416335/phase13_data/Backlink_Acquisition_Dashboard.csv"


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            self.text_parts.append(data)

    def get_text(self):
        return ' '.join(self.text_parts)


def strip_html(html):
    ext = HTMLTextExtractor()
    try:
        ext.feed(html or '')
    except:
        pass
    return ext.get_text()


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
    posts = []
    for page in range(1, 5):
        data = wp_api_call(f"posts?status=publish&per_page=50&page={page}&_fields=id,title,content,slug,categories")
        if not data or (isinstance(data, dict) and data.get('code')):
            break
        posts.extend(data)
        if len(data) < 50:
            break
        time.sleep(1)
    return posts


def assess_link_worthiness(content, title, plain_text):
    """Score how link-worthy a post is (0-100)."""
    score = 0
    signals = []

    # Data/statistics content (highly linkable)
    if re.search(r'\d+%|\d+ out of \d+|survey|study|statistics|data shows', plain_text, re.IGNORECASE):
        score += 20
        signals.append('data/statistics')

    # Original research/methodology
    if re.search(r'methodology|our (approach|process|criteria)|how we (evaluate|score|rank)', plain_text, re.IGNORECASE):
        score += 15
        signals.append('methodology content')

    # Comprehensive guide (long-form)
    word_count = len(plain_text.split())
    if word_count >= 2000:
        score += 15
        signals.append(f'comprehensive ({word_count} words)')
    elif word_count >= 1500:
        score += 10

    # Visual content (tables, infographics potential)
    if '<table' in (content or '').lower():
        score += 10
        signals.append('data tables')

    # List/resource content
    if re.search(r'(best|top \d+|ultimate guide|complete guide)', title, re.IGNORECASE):
        score += 10
        signals.append('resource list')

    # FAQ content (resource-worthy)
    if re.search(r'FAQ|frequently asked', content or '', re.IGNORECASE):
        score += 5
        signals.append('FAQ resource')

    # Unique angles
    if re.search(r'(UK|British|United Kingdom)', plain_text, re.IGNORECASE):
        score += 10
        signals.append('UK-specific angle')

    # Expert/authority signals
    if re.search(r'(sources|references|citations|bibliography)', content or '', re.IGNORECASE):
        score += 10
        signals.append('well-cited')

    # Comparison content
    if re.search(r'(vs|versus|compared|comparison)', plain_text, re.IGNORECASE):
        score += 5
        signals.append('comparison content')

    return min(score, 100), signals


def identify_outreach_targets(post_title, cluster):
    """Identify potential outreach targets for backlinks."""
    targets = []

    # UK pet blogs
    targets.append({
        'type': 'Pet Blog',
        'targets': 'UK pet bloggers writing about ' + cluster.lower(),
        'approach': 'Guest post or resource mention',
        'difficulty': 'medium',
    })

    # Veterinary sites
    if any(kw in post_title.lower() for kw in ['health', 'care', 'nutrition', 'food', 'safety']):
        targets.append({
            'type': 'Veterinary',
            'targets': 'UK vet practice blogs, PDSA, Blue Cross',
            'approach': 'Resource citation',
            'difficulty': 'hard',
        })

    # Charity/rescue
    targets.append({
        'type': 'Charity/Rescue',
        'targets': 'Battersea, Cats Protection, Dogs Trust, RSPCA',
        'approach': 'Resource page inclusion',
        'difficulty': 'hard',
    })

    # Local media
    if 'uk' in post_title.lower() or 'british' in post_title.lower():
        targets.append({
            'type': 'Local Media',
            'targets': 'UK pet publications, local newspapers pet sections',
            'approach': 'Press release / expert comment',
            'difficulty': 'medium',
        })

    # Forums/communities
    targets.append({
        'type': 'Community',
        'targets': 'Pet forums, Reddit r/pets r/cats r/dogs, Mumsnet pets',
        'approach': 'Helpful resource sharing (no spam)',
        'difficulty': 'easy',
    })

    return targets


def main():
    print("=" * 70)
    print("PHASE 13J: BACKLINK & DIGITAL PR PROGRAM")
    print("=" * 70)
    print()

    print("[1/2] Fetching published posts...")
    posts = fetch_all_posts()
    print(f"  Total: {len(posts)} posts")

    # Get categories
    cat_data = wp_api_call("categories?per_page=100&_fields=id,name")
    categories = {c['id']: c['name'] for c in (cat_data or [])} if cat_data else {}
    print()

    print("[2/2] Analyzing link-worthiness and building outreach plan...")
    results = []

    for post in posts:
        post_id = post['id']
        title = post['title']['rendered'] if isinstance(post['title'], dict) else post['title']
        content = post['content']['rendered'] if isinstance(post['content'], dict) else ''
        slug = post.get('slug', '')
        cat_ids = post.get('categories', [])

        cluster = "Uncategorized"
        for cid in cat_ids:
            name = categories.get(cid, '')
            if name and name.lower() != 'uncategorized':
                cluster = name
                break

        plain_text = strip_html(content)
        link_score, signals = assess_link_worthiness(content, title, plain_text)
        outreach_targets = identify_outreach_targets(title, cluster)

        results.append({
            'post_id': post_id,
            'title': title,
            'slug': slug,
            'cluster': cluster,
            'link_worthiness_score': link_score,
            'link_signals': '; '.join(signals),
            'outreach_target_count': len(outreach_targets),
            'primary_outreach': outreach_targets[0]['type'] if outreach_targets else '',
            'outreach_approach': outreach_targets[0]['approach'] if outreach_targets else '',
            'difficulty': outreach_targets[0]['difficulty'] if outreach_targets else '',
            'url': f'https://pethubonline.com/{slug}/',
        })

    # Sort by link_worthiness_score descending
    results.sort(key=lambda x: x['link_worthiness_score'], reverse=True)

    # Write CSV
    fieldnames = ['post_id', 'title', 'slug', 'cluster', 'link_worthiness_score',
                 'link_signals', 'outreach_target_count', 'primary_outreach',
                 'outreach_approach', 'difficulty', 'url']

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"  CSV written: {OUTPUT_CSV}")
    print()

    # Summary
    print("=" * 70)
    print("BACKLINK ACQUISITION SUMMARY")
    print("=" * 70)
    print()

    avg_score = sum(r['link_worthiness_score'] for r in results) / len(results)
    high_value = sum(1 for r in results if r['link_worthiness_score'] >= 70)
    medium_value = sum(1 for r in results if 40 <= r['link_worthiness_score'] < 70)

    print(f"  Total linkable assets: {len(results)}")
    print(f"  Average link-worthiness: {avg_score:.1f}/100")
    print(f"  High-value targets (70+): {high_value}")
    print(f"  Medium-value targets (40-69): {medium_value}")
    print()

    print("TOP 15 MOST LINKABLE PAGES:")
    print("-" * 60)
    for r in results[:15]:
        title_short = r['title'][:45] + "..." if len(r['title']) > 45 else r['title']
        print(f"  Score:{r['link_worthiness_score']:3} | {title_short}")
        print(f"         Signals: {r['link_signals']}")
        print()

    # Cluster breakdown
    cluster_scores = defaultdict(list)
    for r in results:
        cluster_scores[r['cluster']].append(r['link_worthiness_score'])

    print("CLUSTER LINK-WORTHINESS:")
    print("-" * 60)
    cluster_avgs = [(c, sum(s)/len(s), len(s)) for c, s in cluster_scores.items()]
    cluster_avgs.sort(key=lambda x: x[1], reverse=True)
    for cluster, avg, count in cluster_avgs[:10]:
        print(f"  {cluster:<30} Avg: {avg:5.1f} ({count} posts)")

    print()
    print("=" * 70)
    print("OUTREACH STRATEGY:")
    print("  1. Prioritize high-score pages (70+) for active outreach")
    print("  2. Target UK pet blogs + veterinary sites first (authority transfer)")
    print("  3. Resource page inclusion on charity sites (Battersea, RSPCA)")
    print("  4. Community sharing in relevant forums (helpful, not spammy)")
    print("  5. Track backlink acquisition in monthly reports")
    print("=" * 70)


if __name__ == "__main__":
    main()
