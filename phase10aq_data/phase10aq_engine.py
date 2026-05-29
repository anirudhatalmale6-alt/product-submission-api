#!/usr/bin/env python3
"""
Phase 10AQ Topical Dominance Engine + Phase 10AP Indexing Analysis
Scores ALL published posts across 10 dimensions, calculates cluster dominance.
"""

import subprocess
import json
import csv
import re
import time
import os
from datetime import datetime, timezone
from html.parser import HTMLParser

# ─── Config ───────────────────────────────────────────────────────────────────
BASE_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUT_DIR = "/var/lib/freelancer/projects/40416335/phase10aq_data"
DELAY = 0.5

# ─── HTML helpers ─────────────────────────────────────────────────────────────

class HTMLTextExtractor(HTMLParser):
    """Extract plain text from HTML."""
    def __init__(self):
        super().__init__()
        self.result = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip = True

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip = False

    def handle_data(self, data):
        if not self.skip:
            self.result.append(data)

    def get_text(self):
        return ' '.join(self.result)


def strip_html(html_str):
    """Remove HTML tags, return plain text."""
    if not html_str:
        return ""
    extractor = HTMLTextExtractor()
    try:
        extractor.feed(html_str)
    except Exception:
        return re.sub(r'<[^>]+>', ' ', html_str)
    return extractor.get_text()


def wp_api_get(endpoint):
    """Call WP REST API using curl subprocess."""
    url = f"{BASE_URL}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        print(f"  [WARN] curl error for {endpoint}: {result.stderr[:200]}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  [WARN] JSON decode error for {endpoint}: {result.stdout[:200]}")
        return None


# ─── Step 1: Fetch all published posts ────────────────────────────────────────

def fetch_all_posts():
    """Paginate through all published posts."""
    all_posts = []
    page = 1
    while True:
        print(f"  Fetching posts page {page}...")
        data = wp_api_get(f"posts?per_page=100&page={page}&status=publish&_fields=id,title,link,content,date,modified")
        if data is None or (isinstance(data, dict) and data.get('code')):
            break
        if not isinstance(data, list) or len(data) == 0:
            break
        all_posts.extend(data)
        print(f"    Got {len(data)} posts (total so far: {len(all_posts)})")
        if len(data) < 100:
            break
        page += 1
        time.sleep(DELAY)
    return all_posts


# ─── Cluster classification ──────────────────────────────────────────────────

CLUSTER_RULES = [
    # Order matters — first match wins
    ("Dog Toys",       [r"dog toy", r"enrichment", r"puzzle", r"chew toy", r"fetch", r"tug\b"]),
    ("Dog Food",       [r"dog food", r"nutrition", r"kibble", r"feeding", r"dog diet"]),
    ("Dog Health",     [r"dog health", r"dental", r"flea", r"joint", r"supplement", r"tick", r"worm"]),
    ("Dog Training",   [r"dog train", r"behaviour", r"behavior", r"socialisation", r"socialization", r"treat\b"]),
    ("Cat Toys",       [r"cat toy", r"catnip", r"interactive cat", r"wand", r"scratching"]),
    ("Cat Supplies",   [r"cat suppli", r"cat litter", r"cat bed", r"cat collar", r"cat harness"]),
    ("Dog Grooming",   [r"dog groom", r"shampoo", r"brush", r"nail clip", r"coat care"]),
    ("Dog Harnesses",  [r"dog harness", r"dog collar", r"dog lead", r"no.pull", r"dog leash"]),
    ("Dog Beds",       [r"dog bed", r"orthopaedic", r"orthopedic", r"cooling mat", r"dog crate"]),
    ("Puppy Care",     [r"puppy", r"teething", r"vaccination"]),
    ("Indoor Cats",    [r"indoor cat", r"house cat"]),
    ("Educational",    [r"glossary", r"terminology", r"explained"]),
]


def classify_post(title):
    """Classify a post into a cluster based on title keywords."""
    t = title.lower()
    for cluster_name, patterns in CLUSTER_RULES:
        for pat in patterns:
            if re.search(pat, t):
                return cluster_name
    return "Uncategorized"


# ─── Step 2: Scoring dimensions ──────────────────────────────────────────────

UK_AUTHORITIES = [
    r"rspca", r"pdsa", r"bva\b", r"kennel\s*club", r"fediaf", r"pfma",
    r"blue\s*cross", r"cats\s*protection", r"battersea", r"defra",
    r"royal\s*veterinary", r"rcvs", r"pet\s*food\s*manufacturers",
    r"animal\s*welfare", r"british\s*veterinary", r"uk\s*pet\s*food",
    r"vets4pets", r"medivet", r"vet\s*charity"
]


def count_headings(html):
    """Count H1-H6 headings."""
    return len(re.findall(r'<h[1-6][^>]*>', html, re.I))


def count_internal_links(html):
    """Count links to pethubonline.com."""
    return len(re.findall(r'href=["\']https?://pethubonline\.com[^"\']*["\']', html, re.I))


def count_authority_refs(text):
    """Count UK authority references."""
    count = 0
    for pat in UK_AUTHORITIES:
        count += len(re.findall(pat, text, re.I))
    return count


def has_pattern(text, pattern):
    """Check if pattern exists in text (case-insensitive)."""
    return bool(re.search(pattern, text, re.I))


def score_saturation(word_count):
    if word_count >= 3000: return 100
    if word_count >= 2000: return 80
    if word_count >= 1000: return 60
    if word_count >= 500: return 40
    return 20


def score_authority_density(text):
    refs = count_authority_refs(text)
    return min(refs * 15, 100)


def score_semantic_coverage(html):
    headings = count_headings(html)
    links = count_internal_links(html)
    return min(headings * 5 + links * 3, 100)


def score_glossary_density(text):
    count = 0
    for pat in [r"glossary", r"terminology", r"defined\b", r"what\s+is\s+a?\s*\w+\?",
                r"definition", r"meaning\s+of", r"refers\s+to"]:
        count += len(re.findall(pat, text, re.I))
    return min(count * 10, 100)


def score_trust_intensity(html, text):
    score = 0
    # Trust footer
    if has_pattern(html, r'trust.footer|editorial.standards|trusted.by'):
        score += 15
    # Editorial process link
    if has_pattern(html, r'editorial.process|editorial.policy|our.standards'):
        score += 15
    # Corrections link
    if has_pattern(html, r'correction|update.policy|accuracy'):
        score += 15
    # Affiliate disclosure
    if has_pattern(text, r'affiliate|commission|earn.from|paid.link'):
        score += 10
    # AI transparency
    if has_pattern(text, r'ai.transparen|ai.disclosure|ai.assisted|artificial.intelligence.disclosure'):
        score += 15
    # UK authority refs
    if count_authority_refs(text) > 0:
        score += 15
    # "How We Evaluated"
    if has_pattern(text, r'how\s+we\s+evaluat|how\s+we\s+test|our\s+testing\s+process|how\s+we\s+review'):
        score += 15
    return min(score, 100)


def score_citation_confidence(html, text):
    score = 0
    if has_pattern(text, r'at\s+a\s+glance'):
        score += 15
    if has_pattern(text, r'key\s+takeaway'):
        score += 15
    if has_pattern(text, r'decision\s+summary|buying\s+decision|our\s+verdict'):
        score += 15
    if has_pattern(text, r'faq|frequently\s+asked|common\s+question'):
        score += 15
    if has_pattern(text, r'source|reference|cited|according\s+to'):
        score += 15
    if has_pattern(html, r'<table'):
        score += 15
    if has_pattern(text, r'glossary'):
        score += 10
    return min(score, 100)


def score_practical_usefulness(text):
    score = 0
    if has_pattern(text, r'troubleshoot|common\s+issue|problem.solving'):
        score += 15
    if has_pattern(text, r'when\s+to\s+seek|consult\s+your\s+vet|see\s+a\s+vet|visit\s+your\s+vet|when\s+to\s+call'):
        score += 15
    if has_pattern(text, r'warning\s+sign|red\s+flag|watch\s+for|look\s+out\s+for'):
        score += 10
    if has_pattern(text, r'common\s+mistake|avoid\s+these|don.t\s+make'):
        score += 15
    if has_pattern(text, r'realistic.expectation|what\s+to\s+expect|expect\s+that'):
        score += 15
    if has_pattern(text, r'routine|schedule|daily|weekly|how\s+often'):
        score += 10
    if has_pattern(text, r'good\s+choice\s+if|best\s+for|ideal\s+for|suitable\s+for|recommended\s+for'):
        score += 10
    if has_pattern(text, r'beginner|first.time|getting\s+started|new\s+owner|starter'):
        score += 10
    return min(score, 100)


def score_comparison_usefulness(html, text):
    score = 0
    if has_pattern(html, r'<table'):
        score += 25
        # Check for 4+ rows
        rows = len(re.findall(r'<tr', html, re.I))
        if rows >= 5:  # header + 4 data rows
            score += 15
        # Best For column
        if has_pattern(html, r'best\s+for|ideal\s+for|recommended\s+for'):
            score += 20
        # Suitability info
        if has_pattern(text, r'suitab|suited\s+for|great\s+for|perfect\s+for'):
            score += 15
        # Multiple dimensions (price, rating, features)
        dims = 0
        for dim_pat in [r'price|cost|£', r'rating|score|stars', r'feature|spec',
                        r'size|weight|dimension', r'material|fabric', r'durab|quality']:
            if has_pattern(text, dim_pat):
                dims += 1
        if dims >= 3:
            score += 15
        # Proper HTML table
        if has_pattern(html, r'<thead|<th'):
            score += 10
    return min(score, 100)


def score_ai_readiness(html, text):
    score = 0
    if has_pattern(text, r'faq|frequently\s+asked'):
        score += 20
    if has_pattern(text, r'at\s+a\s+glance'):
        score += 20
    if has_pattern(text, r'key\s+takeaway'):
        score += 20
    # Structured headings (H2 + H3)
    h2s = len(re.findall(r'<h2[^>]*>', html, re.I))
    h3s = len(re.findall(r'<h3[^>]*>', html, re.I))
    if h2s >= 3 and h3s >= 2:
        score += 20
    # Direct answers
    if has_pattern(text, r'the\s+answer\s+is|in\s+short|simply\s+put|the\s+short\s+answer|bottom\s+line'):
        score += 20
    return min(score, 100)


def score_indexing_momentum(word_count, html, modified_str):
    score = 0
    # Word count component (25)
    if word_count >= 3000:
        score += 25
    elif word_count >= 2000:
        score += 20
    elif word_count >= 1000:
        score += 15
    elif word_count >= 500:
        score += 10
    else:
        score += 5

    # Internal links component (25)
    ilinks = count_internal_links(html)
    if ilinks >= 10:
        score += 25
    elif ilinks >= 5:
        score += 20
    elif ilinks >= 3:
        score += 15
    elif ilinks >= 1:
        score += 10
    else:
        score += 5

    # Heading density component (25)
    headings = count_headings(html)
    if headings >= 15:
        score += 25
    elif headings >= 10:
        score += 20
    elif headings >= 5:
        score += 15
    elif headings >= 3:
        score += 10
    else:
        score += 5

    # Freshness score (25) - based on modified date
    try:
        mod_date = datetime.fromisoformat(modified_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        days_old = (now - mod_date).days
        if days_old <= 7:
            score += 25
        elif days_old <= 14:
            score += 22
        elif days_old <= 30:
            score += 18
        elif days_old <= 60:
            score += 12
        elif days_old <= 90:
            score += 8
        else:
            score += 5
    except Exception:
        score += 5

    return min(score, 100)


def score_post(post):
    """Score a single post across all 10 dimensions."""
    html = post.get('content', {}).get('rendered', '')
    text = strip_html(html).lower()
    title = post.get('title', {}).get('rendered', '')
    modified = post.get('modified', '')
    word_count = len(text.split())

    scores = {
        'saturation': score_saturation(word_count),
        'authority_density': score_authority_density(text),
        'semantic_coverage': score_semantic_coverage(html),
        'glossary_density': score_glossary_density(text),
        'trust_intensity': score_trust_intensity(html, text),
        'citation_confidence': score_citation_confidence(html, text),
        'practical_usefulness': score_practical_usefulness(text),
        'comparison_usefulness': score_comparison_usefulness(html, text),
        'ai_readiness': score_ai_readiness(html, text),
        'indexing_momentum': score_indexing_momentum(word_count, html, modified),
    }

    # Topical dominance score = average of all 10
    scores['topical_dominance_score'] = round(
        sum(scores.values()) / 10, 1
    )

    return {
        'id': post['id'],
        'title': strip_html(title),
        'cluster': classify_post(strip_html(title)),
        'url': post.get('link', ''),
        'word_count': word_count,
        **scores
    }


# ─── Step 3 & 4: Cluster aggregation and output ──────────────────────────────

def generate_outputs(scored_posts):
    """Generate all CSV output files."""

    # ── 1. all_post_scores.csv ──
    post_fields = [
        'id', 'title', 'cluster', 'url', 'word_count',
        'saturation', 'authority_density', 'semantic_coverage',
        'glossary_density', 'trust_intensity', 'citation_confidence',
        'practical_usefulness', 'comparison_usefulness', 'ai_readiness',
        'indexing_momentum', 'topical_dominance_score'
    ]
    with open(os.path.join(OUT_DIR, 'all_post_scores.csv'), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=post_fields, extrasaction='ignore')
        writer.writeheader()
        for p in sorted(scored_posts, key=lambda x: x['topical_dominance_score'], reverse=True):
            writer.writerow(p)
    print(f"  Wrote all_post_scores.csv ({len(scored_posts)} posts)")

    # ── 2. cluster_dominance.csv ──
    clusters = {}
    dims = ['saturation', 'authority_density', 'semantic_coverage', 'glossary_density',
            'trust_intensity', 'citation_confidence', 'practical_usefulness',
            'comparison_usefulness', 'ai_readiness', 'indexing_momentum']

    for p in scored_posts:
        c = p['cluster']
        if c not in clusters:
            clusters[c] = {d: [] for d in dims}
            clusters[c]['_posts'] = []
        for d in dims:
            clusters[c][d].append(p[d])
        clusters[c]['_posts'].append(p)

    cluster_rows = []
    for c, data in clusters.items():
        row = {'cluster': c, 'post_count': len(data['_posts'])}
        dim_avgs = {}
        for d in dims:
            avg = round(sum(data[d]) / len(data[d]), 1) if data[d] else 0
            dim_avgs[d] = avg
        row['avg_saturation'] = dim_avgs['saturation']
        row['avg_authority'] = dim_avgs['authority_density']
        row['avg_semantic'] = dim_avgs['semantic_coverage']
        row['avg_glossary'] = dim_avgs['glossary_density']
        row['avg_trust'] = dim_avgs['trust_intensity']
        row['avg_citation'] = dim_avgs['citation_confidence']
        row['avg_practical'] = dim_avgs['practical_usefulness']
        row['avg_comparison'] = dim_avgs['comparison_usefulness']
        row['avg_ai_readiness'] = dim_avgs['ai_readiness']
        row['avg_indexing'] = dim_avgs['indexing_momentum']
        row['topical_dominance_score'] = round(sum(dim_avgs.values()) / len(dim_avgs), 1)
        cluster_rows.append(row)

    cluster_rows.sort(key=lambda x: x['topical_dominance_score'], reverse=True)
    for i, r in enumerate(cluster_rows, 1):
        r['rank'] = i

    cluster_fields = ['cluster', 'post_count', 'avg_saturation', 'avg_authority',
                      'avg_semantic', 'avg_glossary', 'avg_trust', 'avg_citation',
                      'avg_practical', 'avg_comparison', 'avg_ai_readiness',
                      'avg_indexing', 'topical_dominance_score', 'rank']
    with open(os.path.join(OUT_DIR, 'cluster_dominance.csv'), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=cluster_fields)
        writer.writeheader()
        for r in cluster_rows:
            writer.writerow(r)
    print(f"  Wrote cluster_dominance.csv ({len(cluster_rows)} clusters)")

    # ── 3. dimension_heatmap.csv ──
    heatmap_rows = []
    dim_labels = {
        'saturation': 'Saturation', 'authority_density': 'Authority Density',
        'semantic_coverage': 'Semantic Coverage', 'glossary_density': 'Glossary Density',
        'trust_intensity': 'Trust Intensity', 'citation_confidence': 'Citation Confidence',
        'practical_usefulness': 'Practical Usefulness', 'comparison_usefulness': 'Comparison Usefulness',
        'ai_readiness': 'AI Readiness', 'indexing_momentum': 'Indexing Momentum'
    }
    avg_map = {
        'saturation': 'avg_saturation', 'authority_density': 'avg_authority',
        'semantic_coverage': 'avg_semantic', 'glossary_density': 'avg_glossary',
        'trust_intensity': 'avg_trust', 'citation_confidence': 'avg_citation',
        'practical_usefulness': 'avg_practical', 'comparison_usefulness': 'avg_comparison',
        'ai_readiness': 'avg_ai_readiness', 'indexing_momentum': 'avg_indexing'
    }
    for cr in cluster_rows:
        for d, label in dim_labels.items():
            s = cr[avg_map[d]]
            if s >= 70:
                status = 'green'
            elif s >= 50:
                status = 'amber'
            else:
                status = 'red'
            heatmap_rows.append({
                'cluster': cr['cluster'],
                'dimension': label,
                'score': s,
                'status': status
            })
    with open(os.path.join(OUT_DIR, 'dimension_heatmap.csv'), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['cluster', 'dimension', 'score', 'status'])
        writer.writeheader()
        for r in heatmap_rows:
            writer.writerow(r)
    print(f"  Wrote dimension_heatmap.csv ({len(heatmap_rows)} rows)")

    # ── 4. dominance_gaps.csv ──
    gap_actions = {
        'Saturation': 'Expand post word counts to 2000-3000+ words with deeper content',
        'Authority Density': 'Add UK authority references (RSPCA, PDSA, BVA, Kennel Club, FEDIAF)',
        'Semantic Coverage': 'Add more H2/H3 headings and internal links to related posts',
        'Glossary Density': 'Add glossary sections, define key terms, link to glossary hub',
        'Trust Intensity': 'Add editorial process links, corrections policy, AI transparency, affiliate disclosure',
        'Citation Confidence': 'Add At a Glance boxes, Key Takeaways, FAQ sections, comparison tables',
        'Practical Usefulness': 'Add troubleshooting sections, "when to see a vet", common mistakes, routines',
        'Comparison Usefulness': 'Add comparison tables with 4+ rows, Best For columns, multi-dimension data',
        'AI Readiness': 'Add FAQ schema, At a Glance, Key Takeaways, structured headings, direct answers',
        'Indexing Momentum': 'Increase word counts, add internal links, refresh/update older posts',
    }
    gap_rows = []
    for cr in cluster_rows:
        weakest_dim = None
        weakest_score = 999
        for d, label in dim_labels.items():
            s = cr[avg_map[d]]
            if s < weakest_score:
                weakest_score = s
                weakest_dim = label
        gap = max(0, round(70 - weakest_score, 1))
        gap_rows.append({
            'cluster': cr['cluster'],
            'weakest_dimension': weakest_dim,
            'score': weakest_score,
            'gap_to_70': gap,
            'recommended_action': gap_actions.get(weakest_dim, 'Improve content quality')
        })
    with open(os.path.join(OUT_DIR, 'dominance_gaps.csv'), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['cluster', 'weakest_dimension', 'score', 'gap_to_70', 'recommended_action'])
        writer.writeheader()
        for r in gap_rows:
            writer.writerow(r)
    print(f"  Wrote dominance_gaps.csv ({len(gap_rows)} rows)")

    # ── 5. publication_summary.csv ──
    summary_rows = []
    for cr in cluster_rows:
        c = cr['cluster']
        posts_in = [p for p in scored_posts if p['cluster'] == c]
        scores_list = [p['topical_dominance_score'] for p in posts_in]
        summary_rows.append({
            'cluster': c,
            'total_published': len(posts_in),
            'pages_above_70': sum(1 for s in scores_list if s > 70),
            'pages_above_80': sum(1 for s in scores_list if s > 80),
            'pages_below_50': sum(1 for s in scores_list if s < 50),
            'avg_score': round(sum(scores_list) / len(scores_list), 1) if scores_list else 0
        })
    with open(os.path.join(OUT_DIR, 'publication_summary.csv'), 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['cluster', 'total_published', 'pages_above_70', 'pages_above_80', 'pages_below_50', 'avg_score'])
        writer.writeheader()
        for r in summary_rows:
            writer.writerow(r)
    print(f"  Wrote publication_summary.csv ({len(summary_rows)} rows)")

    return cluster_rows


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("Phase 10AQ Topical Dominance Engine")
    print("=" * 70)

    # Step 1: Fetch
    print("\n[STEP 1] Fetching all published posts...")
    posts = fetch_all_posts()
    print(f"  Total posts fetched: {len(posts)}")

    if not posts:
        print("  ERROR: No posts fetched. Check API credentials.")
        return

    # Step 2: Score
    print("\n[STEP 2] Scoring all posts across 10 dimensions...")
    scored = []
    for i, post in enumerate(posts):
        title = strip_html(post.get('title', {}).get('rendered', ''))
        scored_post = score_post(post)
        scored.append(scored_post)
        if (i + 1) % 25 == 0:
            print(f"  Scored {i + 1}/{len(posts)} posts...")
    print(f"  Scored all {len(scored)} posts")

    # Step 3 & 4: Aggregate and output
    print("\n[STEP 3-4] Generating output files...")
    cluster_rows = generate_outputs(scored)

    # Print summary
    print("\n" + "=" * 70)
    print("TOPICAL DOMINANCE RANKING")
    print("=" * 70)
    print(f"{'Rank':<5} {'Cluster':<22} {'Posts':<7} {'Score':<8} {'Weakest Dimension'}")
    print("-" * 70)

    # Build gap lookup
    gap_lookup = {}
    gap_path = os.path.join(OUT_DIR, 'dominance_gaps.csv')
    with open(gap_path, 'r') as f:
        reader = csv.DictReader(f)
        for r in reader:
            gap_lookup[r['cluster']] = r['weakest_dimension']

    for cr in cluster_rows:
        weakest = gap_lookup.get(cr['cluster'], '?')
        print(f"  {cr['rank']:<3} {cr['cluster']:<22} {cr['post_count']:<7} {cr['topical_dominance_score']:<8} {weakest}")

    # Dimension status summary
    print("\n" + "=" * 70)
    print("DIMENSION STATUS SUMMARY (red = <50, amber = 50-69, green = 70+)")
    print("=" * 70)
    heatmap_path = os.path.join(OUT_DIR, 'dimension_heatmap.csv')
    red_count = amber_count = green_count = 0
    with open(heatmap_path, 'r') as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r['status'] == 'red':
                red_count += 1
            elif r['status'] == 'amber':
                amber_count += 1
            else:
                green_count += 1
    total = red_count + amber_count + green_count
    print(f"  GREEN (70+):  {green_count}/{total} cells ({round(green_count/total*100, 1)}%)")
    print(f"  AMBER (50-69): {amber_count}/{total} cells ({round(amber_count/total*100, 1)}%)")
    print(f"  RED   (<50):  {red_count}/{total} cells ({round(red_count/total*100, 1)}%)")

    print(f"\nAll outputs saved to: {OUT_DIR}/")
    print("Done.")


if __name__ == '__main__':
    main()
