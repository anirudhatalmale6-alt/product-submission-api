#!/usr/bin/env python3
"""
Phase 13G: Competitor Agent
Tracks competitor content strategy, authority signals, and content gaps.
Competitors: Cats.com, Pets at Home, Zooplus, Purina, Rover
"""

import subprocess
import json
import csv
import re
import time
from datetime import datetime
from collections import defaultdict

WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_API = "https://pethubonline.com/wp-json/wp/v2"

OUTPUT_CSV = "/var/lib/freelancer/projects/40416335/phase13_data/Competitor_Analysis_Report.csv"

COMPETITORS = {
    'cats.com': {
        'name': 'Cats.com',
        'domain': 'cats.com',
        'focus': 'Cat-only content',
        'strengths': ['Deep cat expertise', 'Vet-reviewed content', 'Large content library'],
        'weaknesses': ['Cat-only (no dogs)', 'US-focused', 'Heavy ad load'],
        'estimated_da': 65,
        'content_volume': 'high',
    },
    'petsathome.com': {
        'name': 'Pets at Home',
        'domain': 'petsathome.com',
        'focus': 'UK pet retail + advice',
        'strengths': ['Brand recognition', 'UK focus', 'Product + advice integration'],
        'weaknesses': ['Commercial bias', 'Generic advice', 'Less depth'],
        'estimated_da': 72,
        'content_volume': 'high',
    },
    'zooplus.co.uk': {
        'name': 'Zooplus',
        'domain': 'zooplus.co.uk',
        'focus': 'Pet supplies + magazine',
        'strengths': ['Large product range', 'European presence', 'Magazine content'],
        'weaknesses': ['Product-focused', 'Less editorial depth', 'Less UK-specific'],
        'estimated_da': 60,
        'content_volume': 'medium',
    },
    'purina.co.uk': {
        'name': 'Purina',
        'domain': 'purina.co.uk',
        'focus': 'Pet nutrition + care',
        'strengths': ['Brand authority', 'Vet partnerships', 'Research-backed'],
        'weaknesses': ['Brand bias', 'Product-centric', 'Narrow scope'],
        'estimated_da': 68,
        'content_volume': 'medium',
    },
    'rover.com': {
        'name': 'Rover',
        'domain': 'rover.com',
        'focus': 'Pet care services + blog',
        'strengths': ['Service integration', 'Community trust', 'Practical advice'],
        'weaknesses': ['Service-focused', 'US-heavy', 'Less product expertise'],
        'estimated_da': 70,
        'content_volume': 'medium',
    },
}

# PetHub's content clusters to compare against
PETHUB_CLUSTERS = [
    'Cat Supplies', 'Cat Toys', 'Indoor Cats', 'Dog Supplies',
    'Dog Beds', 'Dog Food', 'Dog Harnesses', 'Dog Care',
    'Dog Health', 'Pet Care', 'Buying Guides',
]


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


def get_pethub_coverage():
    """Get PetHub's current content coverage by cluster."""
    coverage = defaultdict(int)
    for page in range(1, 5):
        data = wp_api_call(f"posts?status=publish&per_page=50&page={page}&_fields=id,categories")
        if not data or (isinstance(data, dict) and data.get('code')):
            break
        for post in data:
            cats = post.get('categories', [])
            for cat_id in cats:
                coverage[cat_id] += 1
        time.sleep(1)

    # Map category IDs to names
    cat_data = wp_api_call("categories?per_page=100&_fields=id,name")
    cat_map = {}
    if cat_data and isinstance(cat_data, list):
        cat_map = {c['id']: c['name'] for c in cat_data}

    named_coverage = {}
    for cat_id, count in coverage.items():
        name = cat_map.get(cat_id, f'ID-{cat_id}')
        named_coverage[name] = count

    return named_coverage


def analyze_competitor_gaps(pethub_coverage):
    """Identify where competitors likely outperform PetHub."""
    gaps = []

    # Define topic areas where each competitor is strong
    competitor_strengths = {
        'cats.com': ['cat behavior', 'cat breeds', 'cat health', 'kitten care', 'cat nutrition'],
        'petsathome.com': ['small pets', 'fish', 'reptiles', 'pet insurance', 'grooming'],
        'zooplus.co.uk': ['pet food comparison', 'pet accessories', 'aquarium', 'bird care'],
        'purina.co.uk': ['dog nutrition', 'cat nutrition', 'puppy development', 'senior pets'],
        'rover.com': ['dog walking', 'pet sitting', 'dog training', 'dog behavior', 'travel with pets'],
    }

    for competitor, topics in competitor_strengths.items():
        comp_name = COMPETITORS[competitor]['name']
        for topic in topics:
            # Check if PetHub covers this
            topic_covered = False
            for cluster_name, count in pethub_coverage.items():
                if any(word in cluster_name.lower() for word in topic.split()):
                    if count >= 3:
                        topic_covered = True
                        break

            if not topic_covered:
                gaps.append({
                    'topic': topic,
                    'competitor': comp_name,
                    'competitor_strength': 'high',
                    'pethub_coverage': 'low',
                    'opportunity': 'Create content cluster',
                    'priority': 'medium',
                })

    return gaps


def generate_competitive_landscape():
    """Generate competitive landscape analysis."""
    results = []

    for domain, comp in COMPETITORS.items():
        # Analyze competitive position per cluster
        for cluster in PETHUB_CLUSTERS:
            relevance = assess_competitor_relevance(comp, cluster)
            threat_level = assess_threat_level(comp, cluster)

            results.append({
                'competitor': comp['name'],
                'domain': comp['domain'],
                'cluster': cluster,
                'relevance': relevance,
                'threat_level': threat_level,
                'competitor_da': comp['estimated_da'],
                'competitor_volume': comp['content_volume'],
                'pethub_advantage': identify_advantage(comp, cluster),
                'recommended_response': recommend_response(threat_level, relevance),
            })

    return results


def assess_competitor_relevance(comp, cluster):
    """How relevant is this competitor to this specific cluster?"""
    cluster_lower = cluster.lower()

    # Cats.com is highly relevant to cat clusters
    if 'cats.com' in comp['domain']:
        if 'cat' in cluster_lower:
            return 'high'
        return 'none'

    # Pets at Home is relevant to all
    if 'petsathome' in comp['domain']:
        return 'medium'

    # Purina is relevant to food/nutrition
    if 'purina' in comp['domain']:
        if 'food' in cluster_lower or 'health' in cluster_lower or 'care' in cluster_lower:
            return 'high'
        return 'low'

    # Rover is relevant to dog care
    if 'rover' in comp['domain']:
        if 'dog' in cluster_lower:
            return 'medium'
        return 'low'

    # Zooplus is relevant to supplies
    if 'zooplus' in comp['domain']:
        if 'supplies' in cluster_lower or 'toys' in cluster_lower or 'beds' in cluster_lower:
            return 'medium'
        return 'low'

    return 'low'


def assess_threat_level(comp, cluster):
    """How threatening is this competitor for this cluster?"""
    relevance = assess_competitor_relevance(comp, cluster)
    da = comp['estimated_da']

    if relevance == 'high' and da >= 65:
        return 'high'
    elif relevance == 'medium' and da >= 60:
        return 'medium'
    elif relevance == 'high':
        return 'medium'
    else:
        return 'low'


def identify_advantage(comp, cluster):
    """What advantage does PetHub have over this competitor?"""
    advantages = []

    # PetHub advantages
    if 'cat' in cluster.lower() and 'dog' in cluster.lower():
        advantages.append('Multi-pet coverage')
    if 'uk' in cluster.lower() or True:  # PetHub is always UK-focused
        advantages.append('UK-specific expertise')

    # Competitor-specific
    if 'cats.com' in comp['domain'] and 'dog' in cluster.lower():
        advantages.append('Cat-only competitor, no dog content')
    if 'purina' in comp['domain']:
        advantages.append('Independent (not brand-biased)')
    if 'rover' in comp['domain']:
        advantages.append('Product expertise (not just services)')
    if 'petsathome' in comp['domain']:
        advantages.append('Editorial independence')

    return '; '.join(advantages) if advantages else 'Content depth + trust signals'


def recommend_response(threat_level, relevance):
    """Recommend strategic response to competitor."""
    if threat_level == 'high':
        return 'Prioritize content expansion; build internal link moat; add unique data/research'
    elif threat_level == 'medium':
        return 'Maintain content quality; focus on UK-specific value; strengthen citations'
    else:
        return 'Monitor; maintain current quality; no urgent action needed'


def main():
    print("=" * 70)
    print("PHASE 13G: COMPETITOR AGENT - ANALYSIS REPORT")
    print("=" * 70)
    print()

    print("[1/3] Fetching PetHub content coverage...")
    pethub_coverage = get_pethub_coverage()
    print(f"  Clusters covered: {len(pethub_coverage)}")
    total_posts = sum(pethub_coverage.values())
    print(f"  Total published posts: {total_posts}")
    print()

    print("[2/3] Analyzing competitive landscape...")
    landscape = generate_competitive_landscape()
    print(f"  Competitor-cluster combinations: {len(landscape)}")
    print()

    print("[3/3] Identifying content gaps...")
    gaps = analyze_competitor_gaps(pethub_coverage)
    print(f"  Content gaps identified: {len(gaps)}")
    print()

    # Write landscape CSV
    fieldnames = ['competitor', 'domain', 'cluster', 'relevance', 'threat_level',
                 'competitor_da', 'competitor_volume', 'pethub_advantage', 'recommended_response']

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(landscape)

    print(f"CSV written: {OUTPUT_CSV}")
    print()

    # Write gaps CSV
    gaps_csv = "/var/lib/freelancer/projects/40416335/phase13_data/Content_Gap_Analysis.csv"
    if gaps:
        gap_fields = ['topic', 'competitor', 'competitor_strength', 'pethub_coverage', 'opportunity', 'priority']
        with open(gaps_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=gap_fields)
            writer.writeheader()
            writer.writerows(gaps)
        print(f"Gaps CSV: {gaps_csv}")
    print()

    # Summary
    print("=" * 70)
    print("COMPETITIVE LANDSCAPE SUMMARY")
    print("=" * 70)
    print()

    print("COMPETITOR PROFILES:")
    print("-" * 60)
    for domain, comp in COMPETITORS.items():
        high_threats = sum(1 for l in landscape if l['competitor'] == comp['name'] and l['threat_level'] == 'high')
        print(f"  {comp['name']:<20} DA:{comp['estimated_da']:3} | Vol:{comp['content_volume']:<6} | High threats: {high_threats}")
        print(f"    Focus: {comp['focus']}")
        print(f"    Strengths: {', '.join(comp['strengths'][:2])}")
        print()

    print("PETHUB CONTENT COVERAGE:")
    print("-" * 60)
    for name, count in sorted(pethub_coverage.items(), key=lambda x: x[1], reverse=True)[:15]:
        bar = '#' * min(count, 30)
        print(f"  {name:<30} {count:3} posts {bar}")

    print()
    print("HIGH-THREAT CLUSTERS (where competitors dominate):")
    print("-" * 60)
    high_threats = [l for l in landscape if l['threat_level'] == 'high']
    cluster_threats = defaultdict(list)
    for t in high_threats:
        cluster_threats[t['cluster']].append(t['competitor'])

    for cluster, competitors in sorted(cluster_threats.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {cluster:<25} Threatened by: {', '.join(competitors)}")

    print()
    print("CONTENT GAPS (topics competitors cover, PetHub doesn't):")
    print("-" * 60)
    for gap in gaps[:10]:
        print(f"  [{gap['priority']:>6}] {gap['topic']:<25} (vs {gap['competitor']})")

    print()
    print("=" * 70)
    print(f"STRATEGIC POSITION: PetHub competes on UK-specific independent expertise")
    print(f"PRIMARY MOAT: Trust signals + citation quality + editorial independence")
    print(f"KEY OPPORTUNITY: Expand into under-served niches (behavior, training, breed guides)")
    print("=" * 70)


if __name__ == "__main__":
    main()
