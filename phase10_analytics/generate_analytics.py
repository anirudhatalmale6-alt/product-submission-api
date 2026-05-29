#!/usr/bin/env python3
"""
PetHub Online Phase 10 Analytics - Generate 8 CSV tracking dashboards.
READ-ONLY: Does not modify any WordPress posts.
"""

import csv
import json
import subprocess
import os
import re
import html
from collections import defaultdict
import time

# ─── Configuration ───────────────────────────────────────────────────────────
WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUT_DIR = "/var/lib/freelancer/projects/40416335/phase10_analytics"
DATA_AQ = "/var/lib/freelancer/projects/40416335/phase10aq_data"
DATA_AO = "/var/lib/freelancer/projects/40416335/phase10ao_data"
DATA_AL = "/var/lib/freelancer/projects/40416335/phase10al_data"
DATA_AM = "/var/lib/freelancer/projects/40416335/phase10am_data"
DATA_AK = "/var/lib/freelancer/projects/40416335/phase10ak_data"

# ─── Helper: WP API fetch ────────────────────────────────────────────────────
def wp_fetch(endpoint, params=None):
    """Fetch from WP REST API using curl subprocess."""
    url = f"{WP_API}/{endpoint}"
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    return json.loads(result.stdout)

def fetch_all_posts():
    """Fetch all published posts with pagination."""
    all_posts = []
    page = 1
    while True:
        print(f"  Fetching page {page}...")
        url = f"{WP_API}/posts?per_page=100&page={page}&status=publish"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True, timeout=60
        )
        try:
            posts = json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"  JSON decode error on page {page}, stopping.")
            break
        if not isinstance(posts, list) or len(posts) == 0:
            break
        all_posts.extend(posts)
        print(f"  Got {len(posts)} posts (total: {len(all_posts)})")
        if len(posts) < 100:
            break
        page += 1
        time.sleep(0.5)
    return all_posts

# ─── Helper: Load CSV into list of dicts ─────────────────────────────────────
def load_csv(path):
    """Load CSV file, return list of dicts."""
    if not os.path.exists(path):
        print(f"  WARNING: {path} not found")
        return []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def write_csv(path, rows, fieldnames):
    """Write list of dicts to CSV."""
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Written: {path} ({len(rows)} rows)")

# ─── Load all prior data ─────────────────────────────────────────────────────
print("Loading prior data...")
dominance_data = load_csv(f"{DATA_AQ}/cluster_dominance.csv")
all_post_scores = load_csv(f"{DATA_AQ}/all_post_scores.csv")
cluster_profiles = load_csv(f"{DATA_AO}/cluster_profiles.csv")
reference_profile = load_csv(f"{DATA_AO}/reference_profile.csv")
citation_scores = load_csv(f"{DATA_AL}/citation_scores.csv")
trust_depth_scores = load_csv(f"{DATA_AM}/trust_depth_scores.csv")
ak_dashboard = load_csv(f"{DATA_AK}/cluster_dashboard.csv")
ak_phases = load_csv(f"{DATA_AK}/before_after_all_phases.csv")

# Build lookups
post_by_id = {}
for p in all_post_scores:
    pid = p.get('id', '')
    post_by_id[pid] = p

# Cluster -> list of posts
cluster_posts = defaultdict(list)
for p in all_post_scores:
    cluster_posts[p['cluster']].append(p)

# Citation by id
citation_by_id = {}
for c in citation_scores:
    citation_by_id[c.get('id', '')] = c

# Trust depth by id
trust_by_id = {}
for t in trust_depth_scores:
    trust_by_id[t.get('id', '')] = t

# Reference profile (Dog Toys element coverage)
ref_elements = {}
for r in reference_profile:
    try:
        ref_elements[r['element']] = float(r['dog_toys_pct'])
    except (ValueError, TypeError):
        pass  # Skip non-numeric rows like avg_word_count, avg_internal_links

# Cluster profiles: cluster -> element -> pct
cluster_element_coverage = defaultdict(dict)
for cp in cluster_profiles:
    cluster_element_coverage[cp['cluster']][cp['element']] = float(cp['pct'])

# AK dashboard baseline
ak_baseline = {}
for row in ak_dashboard:
    ak_baseline[row.get('Cluster', '')] = row

# All clusters from dominance data
all_clusters = []
dominance_map = {}
for d in dominance_data:
    c = d['cluster']
    all_clusters.append(c)
    dominance_map[c] = d

# ─── Fetch all published posts ────────────────────────────────────────────────
print("\nFetching all published posts from WP API...")
wp_posts = fetch_all_posts()
print(f"Total posts fetched: {len(wp_posts)}")

# Build WP post lookup by ID
wp_post_by_id = {}
for p in wp_posts:
    wp_post_by_id[str(p['id'])] = p

# Strip HTML helper
def strip_html(text):
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', '', text)
    return html.unescape(text).strip()

# Content analysis helpers
def has_table(content):
    """Check if content has an HTML table."""
    return bool(re.search(r'<table[\s>]', content, re.IGNORECASE))

def table_quality(content):
    """Assess table quality: none/weak/strong."""
    if not has_table(content):
        return 'none'
    # Count rows
    rows = len(re.findall(r'<tr[\s>]', content, re.IGNORECASE))
    # Count headers
    headers = len(re.findall(r'<th[\s>]', content, re.IGNORECASE))
    if rows >= 4 and headers >= 2:
        return 'strong'
    elif rows >= 2:
        return 'weak'
    return 'weak'

def has_faq_section(content):
    """Check for FAQ section."""
    return bool(re.search(r'(frequently\s+asked|faq|common\s+questions)', content, re.IGNORECASE))

def has_glossary_section(content):
    """Check for glossary/terminology section."""
    return bool(re.search(r'(glossary|terminology|key\s+terms|definitions)', content, re.IGNORECASE))

def has_trust_footer(content):
    """Check for trust footer elements."""
    patterns = [
        r'(our\s+research|how\s+we\s+(?:test|evaluate|review|research))',
        r'(editorial\s+(?:policy|standards|process))',
        r'(fact[\s-]?check|reviewed\s+by)',
        r'(why\s+(?:you\s+can\s+)?trust)',
        r'(correction\s+policy|accuracy)',
    ]
    return sum(1 for pat in patterns if re.search(pat, content, re.IGNORECASE))

def has_comparison_content(content):
    """Check for comparison elements."""
    has_tbl = has_table(content)
    has_vs = bool(re.search(r'\bvs\.?\b|\bversus\b|\bcompared?\b|\bcomparison\b', content, re.IGNORECASE))
    has_pros_cons = bool(re.search(r'(pros?\s+and\s+cons?|advantages?\s+and\s+disadvantages?)', content, re.IGNORECASE))
    return has_tbl or has_vs or has_pros_cons

def detect_recommended_table_type(title, content):
    """Suggest table type based on content analysis."""
    title_lower = title.lower()
    if 'vs' in title_lower or 'comparison' in title_lower or 'compared' in title_lower:
        return 'head-to-head comparison'
    if 'best' in title_lower:
        return 'product comparison matrix'
    if 'guide' in title_lower or 'how to' in title_lower:
        return 'feature/specification summary'
    if 'glossary' in title_lower or 'terminology' in title_lower:
        return 'term definition table'
    if re.search(r'(schedule|timeline|stages)', title_lower):
        return 'timeline/schedule table'
    return 'general comparison table'


# ─── 1. TOPICAL_MOMENTUM.csv ─────────────────────────────────────────────────
print("\n1. Generating TOPICAL_MOMENTUM.csv...")

# Build AK baseline scores (from cluster_dashboard.csv Overall Authority column)
ak_authority_scores = {}
for row in ak_dashboard:
    cluster_name = row.get('Cluster', '')
    try:
        ak_authority_scores[cluster_name] = float(row.get('Overall Authority', 0))
    except (ValueError, TypeError):
        ak_authority_scores[cluster_name] = 0

momentum_rows = []
# Sort clusters by current dominance rank
sorted_clusters = sorted(all_clusters, key=lambda c: int(dominance_map[c].get('rank', 99)))

for cluster in sorted_clusters:
    d = dominance_map[cluster]
    current = float(d['topical_dominance_score'])

    # Try to find baseline from AK dashboard
    baseline = ak_authority_scores.get(cluster, current)
    if baseline == 0:
        baseline = current  # If no baseline, use current as T0

    delta = round(current - baseline, 2)

    # Momentum direction
    if delta > 3:
        direction = 'accelerating'
    elif delta < -3:
        direction = 'decelerating'
    else:
        direction = 'stable'

    current_rank = int(d['rank'])
    # For rank change, we don't have prior rank data from AK in comparable form
    # so we mark it as 0 (no change measurable) for T0 baseline
    rank_change = 0

    momentum_rows.append({
        'cluster': cluster,
        'current_dominance_score': current,
        'baseline_score': round(baseline, 2),
        'delta': delta,
        'momentum_direction': direction,
        'current_rank': current_rank,
        'rank_change': rank_change
    })

write_csv(
    f"{OUT_DIR}/TOPICAL_MOMENTUM.csv",
    momentum_rows,
    ['cluster', 'current_dominance_score', 'baseline_score', 'delta', 'momentum_direction', 'current_rank', 'rank_change']
)


# ─── 2. REPLICATION_COMPLETION.csv ───────────────────────────────────────────
print("\n2. Generating REPLICATION_COMPLETION.csv...")

# Map cluster_profiles elements to the 6 parity categories
element_to_parity = {
    'faq': 'faq',
    'glossary': 'glossary',
    'trust_footer': 'trust',
    'how_we_evaluated': 'trust',
    'why_we_reference': 'trust',
    'comparison_table': 'comparison',
    'key_takeaways': 'practical_guidance',
    'beginner_recs': 'practical_guidance',
    'common_mistakes': 'practical_guidance',
    'when_to_seek_help': 'practical_guidance',
    'budget_premium': 'practical_guidance',
    'uk_authority_refs': 'authority',
    'at_a_glance': 'authority',
}

def calc_parity(cluster, parity_cat):
    """Calculate parity % for a cluster vs Dog Toys for a given category."""
    elements_in_cat = [e for e, cat in element_to_parity.items() if cat == parity_cat]
    if not elements_in_cat:
        return 100.0

    cluster_avg = 0
    ref_avg = 0
    count = 0
    for elem in elements_in_cat:
        ref_val = ref_elements.get(elem, 0)
        cluster_val = cluster_element_coverage.get(cluster, {}).get(elem, 0)
        ref_avg += ref_val
        cluster_avg += cluster_val
        count += 1

    if count == 0 or ref_avg == 0:
        return 100.0

    parity = (cluster_avg / ref_avg) * 100
    return min(round(parity, 1), 100.0)

replication_rows = []
for cluster in sorted_clusters:
    faq_p = calc_parity(cluster, 'faq')
    glossary_p = calc_parity(cluster, 'glossary')
    trust_p = calc_parity(cluster, 'trust')
    comparison_p = calc_parity(cluster, 'comparison')
    practical_p = calc_parity(cluster, 'practical_guidance')
    authority_p = calc_parity(cluster, 'authority')

    overall = round((faq_p + glossary_p + trust_p + comparison_p + practical_p + authority_p) / 6, 1)

    replication_rows.append({
        'cluster': cluster,
        'faq_parity_pct': faq_p,
        'glossary_parity_pct': glossary_p,
        'trust_parity_pct': trust_p,
        'comparison_parity_pct': comparison_p,
        'practical_guidance_parity_pct': practical_p,
        'authority_parity_pct': authority_p,
        'overall_replication_pct': overall
    })

write_csv(
    f"{OUT_DIR}/REPLICATION_COMPLETION.csv",
    replication_rows,
    ['cluster', 'faq_parity_pct', 'glossary_parity_pct', 'trust_parity_pct', 'comparison_parity_pct', 'practical_guidance_parity_pct', 'authority_parity_pct', 'overall_replication_pct']
)


# ─── 3. CITATION_LEADERBOARD.csv ─────────────────────────────────────────────
print("\n3. Generating CITATION_LEADERBOARD.csv...")

citation_rows = []
for cluster in sorted_clusters:
    posts = cluster_posts.get(cluster, [])
    if not posts:
        continue

    # Get citation scores - use both all_post_scores and citation_scores
    citation_data = []
    for p in posts:
        pid = p['id']
        title = p['title']

        # Primary: from all_post_scores citation_confidence column
        cite_score = float(p.get('citation_confidence', 0))

        # Secondary: from citation_scores.csv if available
        if pid in citation_by_id:
            alt_score = float(citation_by_id[pid].get('citation_score', 0))
            # Use the higher of the two (or the one that exists)
            if alt_score > 0:
                cite_score = max(cite_score, alt_score)

        citation_data.append({
            'id': pid,
            'title': title,
            'score': cite_score
        })

    if not citation_data:
        continue

    avg_citation = round(sum(c['score'] for c in citation_data) / len(citation_data), 1)

    sorted_by_score = sorted(citation_data, key=lambda x: x['score'], reverse=True)
    highest = sorted_by_score[0]
    lowest = sorted_by_score[-1]

    pages_above_70 = sum(1 for c in citation_data if c['score'] >= 70)
    pages_above_80 = sum(1 for c in citation_data if c['score'] >= 80)

    citation_rows.append({
        'cluster': cluster,
        'avg_citation_confidence': avg_citation,
        'highest_citation_page_id': highest['id'],
        'highest_citation_page_title': highest['title'],
        'highest_citation_score': highest['score'],
        'lowest_citation_page_id': lowest['id'],
        'lowest_citation_page_title': lowest['title'],
        'lowest_citation_score': lowest['score'],
        'pages_above_70': pages_above_70,
        'pages_above_80': pages_above_80
    })

write_csv(
    f"{OUT_DIR}/CITATION_LEADERBOARD.csv",
    citation_rows,
    ['cluster', 'avg_citation_confidence', 'highest_citation_page_id', 'highest_citation_page_title', 'highest_citation_score', 'lowest_citation_page_id', 'lowest_citation_page_title', 'lowest_citation_score', 'pages_above_70', 'pages_above_80']
)


# ─── 4. TRUST_DEPTH_SCORES.csv ───────────────────────────────────────────────
print("\n4. Generating TRUST_DEPTH_SCORES.csv...")

trust_rows = []
for cluster in sorted_clusters:
    posts = cluster_posts.get(cluster, [])
    if not posts:
        continue

    trust_data = []
    for p in posts:
        pid = p['id']
        title = p['title']

        # Trust depth from AM data: methodology_depth + source_support + editorial_transparency + evidence_support
        if pid in trust_by_id:
            t = trust_by_id[pid]
            meth = float(t.get('methodology_depth', 0))
            src = float(t.get('source_support', 0))
            edit = float(t.get('editorial_transparency', 0))
            evid = float(t.get('evidence_support', 0))
            trust_depth = round((meth + src + edit + evid) / 4 * 100, 1)
        else:
            # Estimate from all_post_scores trust_intensity
            trust_val = float(p.get('trust_intensity', 0))
            trust_depth = trust_val  # Use trust_intensity as proxy

        # Trust coverage: has_footer + has_disclosure + has_correction_policy
        # Check from AM data if available
        if pid in trust_by_id:
            t = trust_by_id[pid]
            has_corr = float(t.get('correction_visibility', 0))
            has_disc = float(t.get('disclosure_visibility', 0))
            has_ai = float(t.get('ai_transparency', 0))
            trust_coverage = round((has_corr + has_disc + has_ai) / 3 * 100, 1)
        else:
            # Estimate from trust_intensity score
            trust_val = float(p.get('trust_intensity', 0))
            if trust_val >= 100:
                trust_coverage = 100.0
            elif trust_val >= 85:
                trust_coverage = 90.0
            elif trust_val >= 70:
                trust_coverage = 75.0
            else:
                trust_coverage = 60.0

        trust_data.append({
            'id': pid,
            'title': title,
            'trust_depth': trust_depth,
            'trust_coverage': trust_coverage
        })

    if not trust_data:
        continue

    avg_depth = round(sum(t['trust_depth'] for t in trust_data) / len(trust_data), 1)
    avg_coverage = round(sum(t['trust_coverage'] for t in trust_data) / len(trust_data), 1)
    gap = round(avg_depth - avg_coverage, 1)

    sorted_by_depth = sorted(trust_data, key=lambda x: x['trust_depth'], reverse=True)
    deepest = sorted_by_depth[0]
    shallowest = sorted_by_depth[-1]

    trust_rows.append({
        'cluster': cluster,
        'avg_trust_depth': avg_depth,
        'avg_trust_coverage': avg_coverage,
        'trust_depth_vs_coverage_gap': gap,
        'deepest_post_id': deepest['id'],
        'deepest_post_title': deepest['title'],
        'shallowest_post_id': shallowest['id'],
        'shallowest_post_title': shallowest['title']
    })

write_csv(
    f"{OUT_DIR}/TRUST_DEPTH_SCORES.csv",
    trust_rows,
    ['cluster', 'avg_trust_depth', 'avg_trust_coverage', 'trust_depth_vs_coverage_gap', 'deepest_post_id', 'deepest_post_title', 'shallowest_post_id', 'shallowest_post_title']
)


# ─── 5. COMPARISON_COVERAGE.csv ──────────────────────────────────────────────
print("\n5. Generating COMPARISON_COVERAGE.csv...")

comparison_coverage_rows = []
all_posts_needing_tables = []  # For CSV 8

for cluster in sorted_clusters:
    posts = cluster_posts.get(cluster, [])
    if not posts:
        continue

    total = len(posts)
    posts_with_tbl = 0
    posts_needing = []
    strong_comparisons = 0
    weak_comparisons = 0

    for p in posts:
        pid = p['id']
        title = p['title']

        # Check comparison_usefulness score from the scored data
        comp_score = float(p.get('comparison_usefulness', 0))

        # Also check actual content if available
        wp_content = ''
        if pid in wp_post_by_id:
            wp_content = wp_post_by_id[pid].get('content', {}).get('rendered', '')

        content_has_table = has_table(wp_content) if wp_content else False
        content_tq = table_quality(wp_content) if wp_content else 'none'

        # Determine if post has table based on score AND content
        if comp_score >= 80 or content_has_table:
            posts_with_tbl += 1
            if comp_score >= 90 or content_tq == 'strong':
                strong_comparisons += 1
            else:
                weak_comparisons += 1
        else:
            posts_needing.append(pid)
            all_posts_needing_tables.append({
                'id': pid,
                'title': title,
                'cluster': cluster,
                'has_table': content_has_table,
                'table_quality': content_tq,
                'comparison_score': comp_score,
                'wp_content': wp_content
            })

    coverage_pct = round((posts_with_tbl / total) * 100, 1) if total > 0 else 0.0

    comparison_coverage_rows.append({
        'cluster': cluster,
        'total_posts': total,
        'posts_with_table': posts_with_tbl,
        'comparison_coverage_pct': coverage_pct,
        'posts_needing_tables': ';'.join(str(x) for x in posts_needing) if posts_needing else '',
        'posts_with_strong_comparisons': strong_comparisons,
        'posts_with_weak_comparisons': weak_comparisons
    })

write_csv(
    f"{OUT_DIR}/COMPARISON_COVERAGE.csv",
    comparison_coverage_rows,
    ['cluster', 'total_posts', 'posts_with_table', 'comparison_coverage_pct', 'posts_needing_tables', 'posts_with_strong_comparisons', 'posts_with_weak_comparisons']
)


# ─── 6. AUTHORITY_VELOCITY.csv ───────────────────────────────────────────────
print("\n6. Generating AUTHORITY_VELOCITY.csv...")

authority_rows = []
authority_data = []

for cluster in sorted_clusters:
    d = dominance_map[cluster]
    posts = cluster_posts.get(cluster, [])

    # Current authority: average of authority_density from all_post_scores
    if posts:
        current_authority = round(sum(float(p.get('authority_density', 0)) for p in posts) / len(posts), 1)
    else:
        current_authority = float(d.get('avg_authority', 0))

    # AK baseline authority
    ak_authority = 0
    if cluster in ak_baseline:
        try:
            ak_authority = float(ak_baseline[cluster].get('Overall Authority', 0))
        except (ValueError, TypeError):
            ak_authority = 0

    delta = round(current_authority - ak_authority, 1) if ak_authority > 0 else 0

    authority_data.append({
        'cluster': cluster,
        'current_authority_score': current_authority,
        'phase10ak_authority_score': ak_authority if ak_authority > 0 else 'N/A',
        'authority_delta': delta if ak_authority > 0 else 'N/A',
    })

# Calculate velocity rank based on delta
ranked = sorted(
    [a for a in authority_data if a['authority_delta'] != 'N/A'],
    key=lambda x: float(x['authority_delta']),
    reverse=True
)
for i, a in enumerate(ranked):
    a['velocity_rank'] = i + 1
    delta_val = float(a['authority_delta'])
    if delta_val > 5:
        a['acceleration_status'] = 'accelerating'
    elif delta_val < -5:
        a['acceleration_status'] = 'decelerating'
    else:
        a['acceleration_status'] = 'stable'

# For those without AK baseline, assign rank after
na_items = [a for a in authority_data if a['authority_delta'] == 'N/A']
next_rank = len(ranked) + 1
for a in na_items:
    a['velocity_rank'] = next_rank
    a['acceleration_status'] = 'baseline_established'
    next_rank += 1

write_csv(
    f"{OUT_DIR}/AUTHORITY_VELOCITY.csv",
    authority_data,
    ['cluster', 'current_authority_score', 'phase10ak_authority_score', 'authority_delta', 'velocity_rank', 'acceleration_status']
)


# ─── 7. SEMANTIC_COMPLETION.csv ──────────────────────────────────────────────
print("\n7. Generating SEMANTIC_COMPLETION.csv...")

# Map scored dimensions to semantic categories
# faq_coverage = avg faq presence in cluster posts
# glossary_coverage = avg glossary_density
# trust_coverage = avg trust_intensity
# comparison_coverage = avg comparison_usefulness
# citation_coverage = avg citation_confidence
# practical_coverage = avg practical_usefulness
# authority_coverage = avg authority_density

semantic_rows = []
for cluster in sorted_clusters:
    d = dominance_map[cluster]
    posts = cluster_posts.get(cluster, [])

    if not posts:
        continue

    n = len(posts)

    # Calculate per-dimension averages from post scores
    # FAQ coverage: posts with high scores / those with FAQ sections
    faq_scores = []
    glossary_scores = []
    trust_scores = []
    comparison_scores = []
    citation_scores_list = []
    practical_scores = []
    authority_scores = []

    for p in posts:
        # FAQ: estimate from saturation + whether title/content suggests FAQ
        pid = p['id']
        sat = float(p.get('saturation', 0))

        # Use cluster profile data if available for FAQ
        faq_pct = cluster_element_coverage.get(cluster, {}).get('faq', 0)
        faq_scores.append(faq_pct)

        # Glossary
        glossary_scores.append(float(p.get('glossary_density', 0)))

        # Trust
        trust_scores.append(float(p.get('trust_intensity', 0)))

        # Comparison
        comparison_scores.append(float(p.get('comparison_usefulness', 0)))

        # Citation
        citation_scores_list.append(float(p.get('citation_confidence', 0)))

        # Practical
        practical_scores.append(float(p.get('practical_usefulness', 0)))

        # Authority
        authority_scores.append(float(p.get('authority_density', 0)))

    faq_cov = round(sum(faq_scores) / n, 1) if faq_scores else 0
    glossary_cov = round(sum(glossary_scores) / n, 1) if glossary_scores else 0
    trust_cov = round(sum(trust_scores) / n, 1) if trust_scores else 0
    comparison_cov = round(sum(comparison_scores) / n, 1) if comparison_scores else 0
    citation_cov = round(sum(citation_scores_list) / n, 1) if citation_scores_list else 0
    practical_cov = round(sum(practical_scores) / n, 1) if practical_scores else 0
    authority_cov = round(sum(authority_scores) / n, 1) if authority_scores else 0

    overall = round((faq_cov + glossary_cov + trust_cov + comparison_cov + citation_cov + practical_cov + authority_cov) / 7, 1)

    semantic_rows.append({
        'cluster': cluster,
        'faq_coverage': faq_cov,
        'glossary_coverage': glossary_cov,
        'trust_coverage': trust_cov,
        'comparison_coverage': comparison_cov,
        'citation_coverage': citation_cov,
        'practical_coverage': practical_cov,
        'authority_coverage': authority_cov,
        'overall_semantic_completion_pct': overall
    })

write_csv(
    f"{OUT_DIR}/SEMANTIC_COMPLETION.csv",
    semantic_rows,
    ['cluster', 'faq_coverage', 'glossary_coverage', 'trust_coverage', 'comparison_coverage', 'citation_coverage', 'practical_coverage', 'authority_coverage', 'overall_semantic_completion_pct']
)


# ─── 8. COMPARISON_GAP_REPORTS.csv ───────────────────────────────────────────
print("\n8. Generating COMPARISON_GAP_REPORTS.csv...")

gap_rows = []
for item in all_posts_needing_tables:
    pid = item['id']
    title = item['title']
    cluster = item['cluster']
    content_has_table = item['has_table']
    tq = item['table_quality']
    comp_score = item['comparison_score']

    # Determine recommended table type
    rec_type = detect_recommended_table_type(title, item.get('wp_content', ''))

    # Priority: lower comparison score = higher priority
    if comp_score == 0:
        priority = 'critical'
    elif comp_score < 50:
        priority = 'high'
    elif comp_score < 70:
        priority = 'medium'
    else:
        priority = 'low'

    gap_rows.append({
        'id': pid,
        'title': title,
        'cluster': cluster,
        'has_table': content_has_table,
        'table_quality': tq,
        'recommended_table_type': rec_type,
        'priority': priority
    })

# Sort by priority (critical > high > medium > low)
priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
gap_rows.sort(key=lambda x: priority_order.get(x['priority'], 4))

write_csv(
    f"{OUT_DIR}/COMPARISON_GAP_REPORTS.csv",
    gap_rows,
    ['id', 'title', 'cluster', 'has_table', 'table_quality', 'recommended_table_type', 'priority']
)


# ─── Summary ──────────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("ANALYTICS GENERATION COMPLETE")
print("="*70)
print(f"\nOutput directory: {OUT_DIR}")
print(f"Files generated:")
for fname in [
    'TOPICAL_MOMENTUM.csv',
    'REPLICATION_COMPLETION.csv',
    'CITATION_LEADERBOARD.csv',
    'TRUST_DEPTH_SCORES.csv',
    'COMPARISON_COVERAGE.csv',
    'AUTHORITY_VELOCITY.csv',
    'SEMANTIC_COMPLETION.csv',
    'COMPARISON_GAP_REPORTS.csv'
]:
    fpath = f"{OUT_DIR}/{fname}"
    if os.path.exists(fpath):
        with open(fpath) as f:
            lines = sum(1 for _ in f) - 1  # subtract header
        print(f"  {fname}: {lines} rows")
    else:
        print(f"  {fname}: MISSING")
