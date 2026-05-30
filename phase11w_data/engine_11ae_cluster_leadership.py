#!/usr/bin/env python3
"""
Phase 11AE - Cluster Leadership Enhanced
=========================================
Builds enhanced leadership scoring by combining data from:
- Cluster_Leadership_Rankings.csv (baseline)
- Query_Ownership_Matrix.csv (query density)
- Visibility_Readiness_Posts.csv / Clusters.csv (visibility)
- AI_Citation_Observation.csv (citation confidence)
- Featured_Snippet_Readiness.csv (snippet readiness)
- Quick_Answer_Log.csv (quick answer coverage)

New dimensions: ownership, visibility, authority_moat, citation_confidence,
ai_readiness, search_coverage

Output: Cluster_Leadership_Enhanced.csv (11 rows)
"""

import csv
import os
import statistics

WORK_DIR = "/var/lib/freelancer/projects/40416335/phase11w_data"
LEADERSHIP_CSV = os.path.join(WORK_DIR, "Cluster_Leadership_Rankings.csv")
QUERY_CSV = os.path.join(WORK_DIR, "Query_Ownership_Matrix.csv")
VIS_POSTS_CSV = os.path.join(WORK_DIR, "Visibility_Readiness_Posts.csv")
VIS_CLUSTERS_CSV = os.path.join(WORK_DIR, "Visibility_Readiness_Clusters.csv")
CITATION_CSV = os.path.join(WORK_DIR, "AI_Citation_Observation.csv")
SNIPPET_CSV = os.path.join(WORK_DIR, "Featured_Snippet_Readiness.csv")
QUICK_ANSWER_CSV = os.path.join(WORK_DIR, "Quick_Answer_Log.csv")
OUTPUT_CSV = os.path.join(WORK_DIR, "Cluster_Leadership_Enhanced.csv")


def load_csv(filepath):
    """Load CSV file as list of dicts."""
    rows = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def safe_float(val, default=0.0):
    """Safe float conversion."""
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def main():
    print("Phase 11AE - Cluster Leadership Enhanced")
    print("=" * 45)

    # Load all data sources
    leadership = load_csv(LEADERSHIP_CSV)
    query_data = load_csv(QUERY_CSV)
    vis_posts = load_csv(VIS_POSTS_CSV)
    vis_clusters = load_csv(VIS_CLUSTERS_CSV)
    citation_data = load_csv(CITATION_CSV)
    snippet_data = load_csv(SNIPPET_CSV)
    quick_answer_data = load_csv(QUICK_ANSWER_CSV)

    print(f"Loaded: {len(leadership)} clusters, {len(query_data)} query rows, "
          f"{len(citation_data)} citation rows")

    # --- Build per-cluster aggregations ---

    # 1. Query ownership: total queries owned per cluster
    cluster_queries = {}
    cluster_posts_set = {}
    for row in query_data:
        cluster = row.get('cluster', '')
        queries = int(row.get('total_owned_queries', 0))
        if cluster not in cluster_queries:
            cluster_queries[cluster] = 0
            cluster_posts_set[cluster] = set()
        cluster_queries[cluster] += queries
        cluster_posts_set[cluster].add(row.get('post_id', ''))

    # 2. Citation confidence per cluster (avg citability score)
    cluster_citations = {}
    for row in citation_data:
        cluster = row.get('cluster', '')
        score = safe_float(row.get('citability_score', 0))
        if cluster not in cluster_citations:
            cluster_citations[cluster] = []
        cluster_citations[cluster].append(score)

    # 3. Snippet readiness per cluster
    cluster_snippets = {}
    for row in snippet_data:
        cluster = row.get('cluster', '')
        pct = safe_float(row.get('snippet_readiness_pct', 0))
        if cluster not in cluster_snippets:
            cluster_snippets[cluster] = []
        cluster_snippets[cluster].append(pct)

    # 4. Quick answer coverage per cluster
    cluster_qa = {}
    for row in quick_answer_data:
        cluster = row.get('cluster', '')
        status = row.get('status', '')
        action = row.get('action', '')
        if cluster not in cluster_qa:
            cluster_qa[cluster] = {'total': 0, 'has_answer': 0}
        cluster_qa[cluster]['total'] += 1
        if action in ('already_exists', 'added') or status == 'success':
            cluster_qa[cluster]['has_answer'] += 1

    # 5. Visibility readiness per cluster (from cluster-level data)
    cluster_vis = {}
    for row in vis_clusters:
        cluster = row.get('cluster', '')
        score = safe_float(row.get('visibility_readiness_score', 0))
        cluster_vis[cluster] = score

    # 6. Visibility per-post for authority moat calculation
    cluster_vis_posts = {}
    for row in vis_posts:
        cluster = row.get('cluster', '')
        score = safe_float(row.get('visibility_readiness_score', 0))
        if cluster not in cluster_vis_posts:
            cluster_vis_posts[cluster] = []
        cluster_vis_posts[cluster].append(score)

    # --- Calculate total possible queries (max across all clusters) ---
    total_possible_queries = max(cluster_queries.values()) if cluster_queries else 1
    max_posts = max(len(v) for v in cluster_posts_set.values()) if cluster_posts_set else 1

    # --- Build enhanced leadership scores ---
    enhanced_rows = []

    # Get all leadership scores for moat calculation
    all_leadership_scores = sorted(
        [safe_float(r.get('leadership_score', 0)) for r in leadership],
        reverse=True
    )

    for row in leadership:
        cluster = row['cluster']
        posts = int(row.get('posts', 0))
        original_score = safe_float(row.get('leadership_score', 0))

        # Ownership: total queries owned / max possible (normalized)
        total_owned = cluster_queries.get(cluster, 0)
        ownership = round(min(total_owned / max(total_possible_queries, 1) * 100, 100), 1)

        # Visibility: from cluster-level readiness
        visibility = round(cluster_vis.get(cluster, 0), 1)

        # Authority moat: how far ahead of the next cluster below
        idx = all_leadership_scores.index(original_score) if original_score in all_leadership_scores else -1
        if idx >= 0 and idx < len(all_leadership_scores) - 1:
            next_below = all_leadership_scores[idx + 1]
            authority_moat = round(original_score - next_below, 1)
        else:
            authority_moat = 0.0

        # Citation confidence: average citability score for cluster
        cit_scores = cluster_citations.get(cluster, [0])
        citation_confidence = round(statistics.mean(cit_scores), 1) if cit_scores else 0.0

        # AI readiness: combined quick answer coverage + snippet readiness
        qa_stats = cluster_qa.get(cluster, {'total': 1, 'has_answer': 0})
        qa_coverage = (qa_stats['has_answer'] / max(qa_stats['total'], 1)) * 100

        snippet_scores = cluster_snippets.get(cluster, [0])
        avg_snippet = statistics.mean(snippet_scores) if snippet_scores else 0.0

        ai_readiness = round((qa_coverage * 0.6 + avg_snippet * 0.4), 1)

        # Search coverage: queries per post density
        queries_per_post = round(total_owned / max(posts, 1), 1)
        # Normalize to 0-100 scale (20 queries/post = 100)
        search_coverage = round(min(queries_per_post / 20 * 100, 100), 1)

        # Enhanced leadership score: weighted composite
        enhanced_score = round(
            original_score * 0.25 +
            ownership * 0.15 +
            visibility * 0.15 +
            citation_confidence * 0.10 * (100/max(max(cit_scores) if cit_scores else 1, 1)) +
            ai_readiness * 0.15 +
            search_coverage * 0.10 +
            authority_moat * 0.10 * (100/max(max(all_leadership_scores), 1)),
            1
        )

        # Grade assignment
        if enhanced_score >= 70:
            grade = 'A'
        elif enhanced_score >= 55:
            grade = 'B'
        elif enhanced_score >= 40:
            grade = 'C'
        elif enhanced_score >= 25:
            grade = 'D'
        else:
            grade = 'F'

        enhanced_rows.append({
            'rank': 0,  # Will be set after sorting
            'cluster': cluster,
            'posts': posts,
            'original_leadership_score': original_score,
            'ownership': ownership,
            'visibility': visibility,
            'authority_moat': authority_moat,
            'citation_confidence': citation_confidence,
            'ai_readiness': ai_readiness,
            'search_coverage': search_coverage,
            'total_queries_owned': total_owned,
            'queries_per_post': queries_per_post,
            'enhanced_leadership_score': enhanced_score,
            'grade': grade
        })

    # Sort by enhanced score descending and assign ranks
    enhanced_rows.sort(key=lambda x: x['enhanced_leadership_score'], reverse=True)
    for i, row in enumerate(enhanced_rows):
        row['rank'] = i + 1

    # Write output
    fieldnames = [
        'rank', 'cluster', 'posts', 'original_leadership_score',
        'ownership', 'visibility', 'authority_moat', 'citation_confidence',
        'ai_readiness', 'search_coverage', 'total_queries_owned',
        'queries_per_post', 'enhanced_leadership_score', 'grade'
    ]

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enhanced_rows)

    print(f"\nWrote {len(enhanced_rows)} rows to {OUTPUT_CSV}")

    # Display results
    print(f"\n{'Rank':<5} {'Cluster':<20} {'Posts':<6} {'Orig':<6} {'Owner':<7} {'Vis':<6} "
          f"{'Moat':<6} {'Cite':<6} {'AIRdy':<6} {'SrchC':<6} {'Enh':<6} {'Grd':<4}")
    print("-" * 95)
    for r in enhanced_rows:
        print(f"{r['rank']:<5} {r['cluster']:<20} {r['posts']:<6} "
              f"{r['original_leadership_score']:<6} {r['ownership']:<7} "
              f"{r['visibility']:<6} {r['authority_moat']:<6} "
              f"{r['citation_confidence']:<6} {r['ai_readiness']:<6} "
              f"{r['search_coverage']:<6} {r['enhanced_leadership_score']:<6} {r['grade']:<4}")

    # Analysis summary
    print(f"\nKey Insights:")
    top = enhanced_rows[0]
    bottom = enhanced_rows[-1]
    print(f"  Strongest cluster: {top['cluster']} (score: {top['enhanced_leadership_score']}, grade: {top['grade']})")
    print(f"  Weakest cluster: {bottom['cluster']} (score: {bottom['enhanced_leadership_score']}, grade: {bottom['grade']})")

    # Biggest movers (rank change from original)
    original_ranks = {}
    for row in leadership:
        original_ranks[row['cluster']] = int(row.get('rank', 0))

    print(f"\n  Rank Changes:")
    for r in enhanced_rows:
        orig_rank = original_ranks.get(r['cluster'], 0)
        change = orig_rank - r['rank']
        direction = "UP" if change > 0 else "DOWN" if change < 0 else "SAME"
        if change != 0:
            print(f"    {r['cluster']}: {orig_rank} -> {r['rank']} ({direction} {abs(change)})")
        else:
            print(f"    {r['cluster']}: {r['rank']} (unchanged)")


if __name__ == "__main__":
    main()
