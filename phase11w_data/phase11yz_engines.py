#!/usr/bin/env python3
"""
Phase 11Y: Query Ownership Tiers Engine
Phase 11Z: Visibility Dominance Scoring Engine

Read-only data analysis for pethubonline.com.
No WordPress modifications. No network calls needed — all data from existing CSVs.
"""

import csv
import os
import sys
from collections import defaultdict
from datetime import datetime

BASE_DIR = "/var/lib/freelancer/projects/40416335/phase11w_data"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def read_csv(filename):
    """Read a CSV file and return list of dicts."""
    path = os.path.join(BASE_DIR, filename)
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def write_csv(filename, rows, fieldnames):
    """Write a CSV file from list of dicts."""
    path = os.path.join(BASE_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Written: {filename} ({len(rows)} rows)")


def safe_float(val, default=0.0):
    """Safely convert to float."""
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_int(val, default=0):
    """Safely convert to int."""
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def count_semicolon_items(text):
    """Count semicolon-separated items in a field. Returns 0 for empty strings."""
    text = text.strip()
    if not text:
        return 0
    return len([x for x in text.split(";") if x.strip()])


# ============================================================================
# ENGINE 1: PHASE 11Y — QUERY OWNERSHIP TIERS
# ============================================================================

def run_phase_11y():
    print("\n" + "=" * 70)
    print("ENGINE 1: PHASE 11Y — QUERY OWNERSHIP TIERS")
    print("=" * 70)

    # Read the Query Ownership Matrix
    matrix = read_csv("Query_Ownership_Matrix.csv")
    print(f"  Loaded Query_Ownership_Matrix.csv: {len(matrix)} posts")

    # --- Output 1: Per-post, per-query tier classification ---
    tier_rows = []

    for post in matrix:
        post_id = post["post_id"]
        title = post["title"]
        cluster = post["cluster"]
        slug = post["slug"]

        # TIER 1: OWNED — the target query (always exactly 1)
        target_q = post["target_query"].strip()
        if target_q:
            tier_rows.append({
                "post_id": post_id,
                "title": title,
                "cluster": cluster,
                "slug": slug,
                "query": target_q,
                "tier": "OWNED",
                "tier_rank": 1,
                "tier_description": "Primary target query this post owns"
            })

        # TIER 2: DEFENSIBLE — supporting queries
        supporting = post["supporting_queries"].strip()
        if supporting:
            for q in supporting.split(";"):
                q = q.strip()
                if q:
                    tier_rows.append({
                        "post_id": post_id,
                        "title": title,
                        "cluster": cluster,
                        "slug": slug,
                        "query": q,
                        "tier": "DEFENSIBLE",
                        "tier_rank": 2,
                        "tier_description": "Supporting query directly related to core topic"
                    })

        # TIER 3: EMERGING — FAQ queries (growing search interest)
        faq = post["faq_queries"].strip()
        if faq:
            for q in faq.split(";"):
                q = q.strip()
                if q:
                    tier_rows.append({
                        "post_id": post_id,
                        "title": title,
                        "cluster": cluster,
                        "slug": slug,
                        "query": q,
                        "tier": "EMERGING",
                        "tier_rank": 3,
                        "tier_description": "FAQ query representing growing search interest"
                    })

        # TIER 4: OPPORTUNITY — AI answer queries
        ai_answer = post["ai_answer_queries"].strip()
        if ai_answer:
            for q in ai_answer.split(";"):
                q = q.strip()
                if q:
                    tier_rows.append({
                        "post_id": post_id,
                        "title": title,
                        "cluster": cluster,
                        "slug": slug,
                        "query": q,
                        "tier": "OPPORTUNITY",
                        "tier_rank": 4,
                        "tier_description": "AI search opportunity query"
                    })

        # TIER 5: COMPETITOR_CONTROLLED — competitor queries
        competitor = post["competitor_queries"].strip()
        if competitor:
            for q in competitor.split(";"):
                q = q.strip()
                if q:
                    tier_rows.append({
                        "post_id": post_id,
                        "title": title,
                        "cluster": cluster,
                        "slug": slug,
                        "query": q,
                        "tier": "COMPETITOR_CONTROLLED",
                        "tier_rank": 5,
                        "tier_description": "Query where competitors currently dominate"
                    })

    tier_fieldnames = [
        "post_id", "title", "cluster", "slug", "query",
        "tier", "tier_rank", "tier_description"
    ]
    write_csv("Query_Ownership_Tiers.csv", tier_rows, tier_fieldnames)

    # --- Output 2: Per-cluster tier distribution summary ---
    # Aggregate tier counts per cluster
    cluster_tiers = defaultdict(lambda: {
        "OWNED": 0, "DEFENSIBLE": 0, "EMERGING": 0,
        "OPPORTUNITY": 0, "COMPETITOR_CONTROLLED": 0
    })
    cluster_posts = defaultdict(int)

    for row in tier_rows:
        cluster_tiers[row["cluster"]][row["tier"]] += 1

    # Count posts per cluster from original matrix
    for post in matrix:
        cluster_posts[post["cluster"]] += 1

    summary_rows = []
    for cluster in sorted(cluster_tiers.keys()):
        tiers = cluster_tiers[cluster]
        total = sum(tiers.values())
        posts = cluster_posts[cluster]

        owned = tiers["OWNED"]
        defensible = tiers["DEFENSIBLE"]
        emerging = tiers["EMERGING"]
        opportunity = tiers["OPPORTUNITY"]
        competitor = tiers["COMPETITOR_CONTROLLED"]

        # Percentages
        owned_pct = round(owned / total * 100, 1) if total > 0 else 0
        defensible_pct = round(defensible / total * 100, 1) if total > 0 else 0
        emerging_pct = round(emerging / total * 100, 1) if total > 0 else 0
        opportunity_pct = round(opportunity / total * 100, 1) if total > 0 else 0
        competitor_pct = round(competitor / total * 100, 1) if total > 0 else 0

        # Expansion potential = (opportunity + emerging) / total * 100
        expansion_potential = round((opportunity + emerging) / total * 100, 1) if total > 0 else 0

        summary_rows.append({
            "cluster": cluster,
            "posts": posts,
            "total_queries": total,
            "owned_count": owned,
            "owned_pct": owned_pct,
            "defensible_count": defensible,
            "defensible_pct": defensible_pct,
            "emerging_count": emerging,
            "emerging_pct": emerging_pct,
            "opportunity_count": opportunity,
            "opportunity_pct": opportunity_pct,
            "competitor_controlled_count": competitor,
            "competitor_controlled_pct": competitor_pct,
            "expansion_potential_pct": expansion_potential,
            "analysis_date": datetime.now().strftime("%Y-%m-%d")
        })

    # Sort by expansion potential descending
    summary_rows.sort(key=lambda x: x["expansion_potential_pct"], reverse=True)

    summary_fieldnames = [
        "cluster", "posts", "total_queries",
        "owned_count", "owned_pct",
        "defensible_count", "defensible_pct",
        "emerging_count", "emerging_pct",
        "opportunity_count", "opportunity_pct",
        "competitor_controlled_count", "competitor_controlled_pct",
        "expansion_potential_pct", "analysis_date"
    ]
    write_csv("Query_Ownership_Tiers_Summary.csv", summary_rows, summary_fieldnames)

    # Print summary table
    print("\n  QUERY OWNERSHIP TIERS SUMMARY:")
    print(f"  {'Cluster':<20} {'Total':>6} {'OWNED':>6} {'DEFND':>6} {'EMERG':>6} {'OPPTY':>6} {'COMP':>6} {'Expand%':>8}")
    print("  " + "-" * 80)
    for r in summary_rows:
        print(f"  {r['cluster']:<20} {r['total_queries']:>6} {r['owned_count']:>6} "
              f"{r['defensible_count']:>6} {r['emerging_count']:>6} "
              f"{r['opportunity_count']:>6} {r['competitor_controlled_count']:>6} "
              f"{r['expansion_potential_pct']:>7.1f}%")

    return tier_rows, summary_rows


# ============================================================================
# ENGINE 2: PHASE 11Z — VISIBILITY DOMINANCE SCORING
# ============================================================================

def run_phase_11z():
    print("\n" + "=" * 70)
    print("ENGINE 2: PHASE 11Z — VISIBILITY DOMINANCE SCORING")
    print("=" * 70)

    # Load all source data
    leadership = read_csv("Cluster_Leadership_Rankings.csv")
    ownership_summary = read_csv("Query_Ownership_Summary.csv")
    visibility_clusters = read_csv("Visibility_Readiness_Clusters.csv")
    snippet_readiness = read_csv("Featured_Snippet_Readiness.csv")
    citation_obs = read_csv("AI_Citation_Observation.csv")
    visibility_posts = read_csv("Visibility_Readiness_Posts.csv")
    query_matrix = read_csv("Query_Ownership_Matrix.csv")

    print(f"  Loaded Cluster_Leadership_Rankings.csv: {len(leadership)} clusters")
    print(f"  Loaded Query_Ownership_Summary.csv: {len(ownership_summary)} clusters")
    print(f"  Loaded Visibility_Readiness_Clusters.csv: {len(visibility_clusters)} clusters")
    print(f"  Loaded Featured_Snippet_Readiness.csv: {len(snippet_readiness)} posts")
    print(f"  Loaded AI_Citation_Observation.csv: {len(citation_obs)} posts")
    print(f"  Loaded Visibility_Readiness_Posts.csv: {len(visibility_posts)} posts")
    print(f"  Loaded Query_Ownership_Matrix.csv: {len(query_matrix)} posts")

    # --- Build lookup dictionaries ---

    # Leadership by cluster
    leadership_by_cluster = {}
    for r in leadership:
        leadership_by_cluster[r["cluster"]] = safe_float(r["leadership_score"])

    # Ownership by cluster
    ownership_by_cluster = {}
    max_queries = max(safe_int(r["total_queries"]) for r in ownership_summary)
    for r in ownership_summary:
        total_q = safe_int(r["total_queries"])
        # Normalize total_queries to 0-100 scale
        normalized = round(total_q / max_queries * 100, 1) if max_queries > 0 else 0
        ownership_by_cluster[r["cluster"]] = {
            "total_queries": total_q,
            "avg_queries_per_post": safe_float(r["avg_queries_per_post"]),
            "ownership_score_normalized": normalized
        }

    # Visibility by cluster
    visibility_by_cluster = {}
    for r in visibility_clusters:
        visibility_by_cluster[r["cluster"]] = safe_float(r["visibility_readiness_score"])

    # Snippet readiness by cluster: avg snippet_readiness_pct per cluster
    snippet_by_cluster = defaultdict(list)
    snippet_by_post = {}
    for r in snippet_readiness:
        cluster = r["cluster"]
        pct = safe_float(r["snippet_readiness_pct"])
        snippet_by_cluster[cluster].append(pct)
        snippet_by_post[r["post_id"]] = {
            "snippet_readiness_pct": pct,
            "total_h2s": safe_int(r["total_h2s"]),
            "question_h2s": safe_int(r["question_h2s"])
        }
    snippet_avg_by_cluster = {}
    for cluster, vals in snippet_by_cluster.items():
        snippet_avg_by_cluster[cluster] = round(sum(vals) / len(vals), 1) if vals else 0

    # Citation by cluster: avg citability_score per cluster
    citation_by_cluster = defaultdict(list)
    citation_by_post = {}
    for r in citation_obs:
        cluster = r["cluster"]
        score = safe_float(r["citability_score"])
        citation_by_cluster[cluster].append(score)
        citation_by_post[r["post_id"]] = score
    citation_avg_by_cluster = {}
    for cluster, vals in citation_by_cluster.items():
        citation_avg_by_cluster[cluster] = round(sum(vals) / len(vals), 1) if vals else 0

    # Search coverage by cluster: avg queries_per_post
    coverage_by_cluster = {}
    max_avg_qpp = max(safe_float(r["avg_queries_per_post"]) for r in ownership_summary)
    for r in ownership_summary:
        avg_qpp = safe_float(r["avg_queries_per_post"])
        # Normalize to 0-100
        normalized = round(avg_qpp / max_avg_qpp * 100, 1) if max_avg_qpp > 0 else 0
        coverage_by_cluster[r["cluster"]] = {
            "avg_queries_per_post": avg_qpp,
            "coverage_normalized": normalized
        }

    # Visibility by post
    visibility_by_post = {}
    for r in visibility_posts:
        visibility_by_post[r["post_id"]] = safe_float(r["visibility_readiness_score"])

    # Query matrix by post (for per-post ownership/coverage)
    query_by_post = {}
    for r in query_matrix:
        query_by_post[r["post_id"]] = {
            "total_owned_queries": safe_int(r["total_owned_queries"]),
            "query_density_score": safe_float(r["query_density_score"]),
            "cluster": r["cluster"]
        }

    # Leadership by post: use the cluster's leadership score for each post
    # (no per-post leadership data exists, so cluster value is inherited)

    # -----------------------------------------------------------------------
    # OUTPUT 1: Visibility_Dominance.csv — per-cluster dominance scores
    # -----------------------------------------------------------------------

    # Weights
    W_AUTHORITY = 0.20
    W_OWNERSHIP = 0.15
    W_VISIBILITY = 0.20
    W_SNIPPET = 0.15
    W_CITATION = 0.15
    W_COVERAGE = 0.15

    all_clusters = sorted(
        set(leadership_by_cluster.keys()) |
        set(ownership_by_cluster.keys()) |
        set(visibility_by_cluster.keys())
    )

    # Normalize snippet and citation scores to 0-100 for the composite
    max_snippet = max(snippet_avg_by_cluster.values()) if snippet_avg_by_cluster else 1
    max_citation = max(citation_avg_by_cluster.values()) if citation_avg_by_cluster else 1

    cluster_dominance_rows = []
    for cluster in all_clusters:
        authority = leadership_by_cluster.get(cluster, 0)
        own_data = ownership_by_cluster.get(cluster, {"ownership_score_normalized": 0, "total_queries": 0})
        ownership = own_data["ownership_score_normalized"]
        visibility = visibility_by_cluster.get(cluster, 0)

        snippet_raw = snippet_avg_by_cluster.get(cluster, 0)
        snippet_norm = round(snippet_raw / max_snippet * 100, 1) if max_snippet > 0 else 0

        citation_raw = citation_avg_by_cluster.get(cluster, 0)
        citation_norm = round(citation_raw / max_citation * 100, 1) if max_citation > 0 else 0

        cov_data = coverage_by_cluster.get(cluster, {"coverage_normalized": 0})
        coverage = cov_data["coverage_normalized"]

        # Weighted composite
        overall = round(
            authority * W_AUTHORITY +
            ownership * W_OWNERSHIP +
            visibility * W_VISIBILITY +
            snippet_norm * W_SNIPPET +
            citation_norm * W_CITATION +
            coverage * W_COVERAGE,
            1
        )

        # Grade
        if overall >= 75:
            grade = "A"
        elif overall >= 60:
            grade = "B"
        elif overall >= 45:
            grade = "C"
        elif overall >= 30:
            grade = "D"
        else:
            grade = "F"

        posts_in_cluster = sum(1 for r in query_matrix if r["cluster"] == cluster)

        cluster_dominance_rows.append({
            "cluster": cluster,
            "posts": posts_in_cluster,
            "authority_score": authority,
            "ownership_score": round(ownership, 1),
            "visibility_score": visibility,
            "snippet_score": round(snippet_norm, 1),
            "citation_score": round(citation_norm, 1),
            "search_coverage_score": round(coverage, 1),
            "overall_dominance": overall,
            "grade": grade,
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "weight_formula": "authority(20%)+ownership(15%)+visibility(20%)+snippet(15%)+citation(15%)+coverage(15%)"
        })

    # Sort by overall_dominance descending
    cluster_dominance_rows.sort(key=lambda x: x["overall_dominance"], reverse=True)

    cluster_dom_fields = [
        "cluster", "posts", "authority_score", "ownership_score",
        "visibility_score", "snippet_score", "citation_score",
        "search_coverage_score", "overall_dominance", "grade",
        "analysis_date", "weight_formula"
    ]
    write_csv("Visibility_Dominance.csv", cluster_dominance_rows, cluster_dom_fields)

    # -----------------------------------------------------------------------
    # OUTPUT 2: Visibility_Dominance_Posts.csv — per-post dominance scores
    # -----------------------------------------------------------------------

    # For per-post scoring, we normalize within the post universe
    # Get max values for normalization
    all_post_queries = [safe_int(r["total_owned_queries"]) for r in query_matrix]
    max_post_queries = max(all_post_queries) if all_post_queries else 1
    all_post_citations = [v for v in citation_by_post.values()]
    max_post_citation = max(all_post_citations) if all_post_citations else 1
    all_post_snippets = [v["snippet_readiness_pct"] for v in snippet_by_post.values()]
    max_post_snippet = max(all_post_snippets) if all_post_snippets else 1
    all_post_visibility = [v for v in visibility_by_post.values()]
    max_post_visibility = max(all_post_visibility) if all_post_visibility else 1
    all_post_density = [safe_float(r["query_density_score"]) for r in query_matrix]
    max_post_density = max(all_post_density) if all_post_density else 1

    post_dominance_rows = []
    for post in query_matrix:
        pid = post["post_id"]
        cluster = post["cluster"]
        title = post["title"]
        slug = post["slug"]

        # Authority: inherit from cluster leadership score
        authority = leadership_by_cluster.get(cluster, 0)

        # Ownership: normalize total_owned_queries to 0-100
        total_q = safe_int(post["total_owned_queries"])
        ownership_norm = round(total_q / max_post_queries * 100, 1) if max_post_queries > 0 else 0

        # Visibility: from Visibility_Readiness_Posts
        vis_raw = visibility_by_post.get(pid, 0)
        visibility_norm = round(vis_raw / max_post_visibility * 100, 1) if max_post_visibility > 0 else 0

        # Snippet: from Featured_Snippet_Readiness
        snip_data = snippet_by_post.get(pid, {"snippet_readiness_pct": 0})
        snippet_raw = snip_data["snippet_readiness_pct"] if isinstance(snip_data, dict) else 0
        snippet_norm = round(snippet_raw / max_post_snippet * 100, 1) if max_post_snippet > 0 else 0

        # Citation: from AI_Citation_Observation
        cite_raw = citation_by_post.get(pid, 0)
        citation_norm = round(cite_raw / max_post_citation * 100, 1) if max_post_citation > 0 else 0

        # Search coverage: query_density_score normalized
        density = safe_float(post["query_density_score"])
        coverage_norm = round(density / max_post_density * 100, 1) if max_post_density > 0 else 0

        # Weighted composite
        overall = round(
            authority * W_AUTHORITY +
            ownership_norm * W_OWNERSHIP +
            visibility_norm * W_VISIBILITY +
            snippet_norm * W_SNIPPET +
            citation_norm * W_CITATION +
            coverage_norm * W_COVERAGE,
            1
        )

        # Grade
        if overall >= 75:
            grade = "A"
        elif overall >= 60:
            grade = "B"
        elif overall >= 45:
            grade = "C"
        elif overall >= 30:
            grade = "D"
        else:
            grade = "F"

        post_dominance_rows.append({
            "post_id": pid,
            "title": title,
            "cluster": cluster,
            "slug": slug,
            "authority_score": authority,
            "ownership_score": round(ownership_norm, 1),
            "visibility_score": round(visibility_norm, 1),
            "snippet_score": round(snippet_norm, 1),
            "citation_score": round(citation_norm, 1),
            "search_coverage_score": round(coverage_norm, 1),
            "overall_dominance": overall,
            "grade": grade,
            "analysis_date": datetime.now().strftime("%Y-%m-%d")
        })

    # Sort by overall_dominance descending
    post_dominance_rows.sort(key=lambda x: x["overall_dominance"], reverse=True)

    post_dom_fields = [
        "post_id", "title", "cluster", "slug",
        "authority_score", "ownership_score", "visibility_score",
        "snippet_score", "citation_score", "search_coverage_score",
        "overall_dominance", "grade", "analysis_date"
    ]
    write_csv("Visibility_Dominance_Posts.csv", post_dominance_rows, post_dom_fields)

    # Print summary table
    print("\n  VISIBILITY DOMINANCE — CLUSTER RANKINGS:")
    print(f"  {'Cluster':<20} {'Auth':>5} {'Own':>5} {'Vis':>5} {'Snip':>5} {'Cite':>5} {'Cov':>5} {'TOTAL':>6} {'Grd':>4}")
    print("  " + "-" * 75)
    for r in cluster_dominance_rows:
        print(f"  {r['cluster']:<20} {r['authority_score']:>5.1f} {r['ownership_score']:>5.1f} "
              f"{r['visibility_score']:>5.1f} {r['snippet_score']:>5.1f} {r['citation_score']:>5.1f} "
              f"{r['search_coverage_score']:>5.1f} {r['overall_dominance']:>6.1f} {r['grade']:>4}")

    # Top 10 posts
    print("\n  TOP 10 POSTS BY DOMINANCE:")
    print(f"  {'PostID':>7} {'Title':<55} {'Score':>6} {'Grd':>4}")
    print("  " + "-" * 75)
    for r in post_dominance_rows[:10]:
        title_short = r["title"][:52] + "..." if len(r["title"]) > 55 else r["title"]
        print(f"  {r['post_id']:>7} {title_short:<55} {r['overall_dominance']:>6.1f} {r['grade']:>4}")

    return cluster_dominance_rows, post_dominance_rows


# ============================================================================
# VALIDATION
# ============================================================================

def validate_outputs():
    """Verify all output files have correct row counts and no empty required fields."""
    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)

    issues = []

    # Validate Query_Ownership_Tiers.csv
    tiers = read_csv("Query_Ownership_Tiers.csv")
    print(f"  Query_Ownership_Tiers.csv: {len(tiers)} rows")
    if len(tiers) == 0:
        issues.append("Query_Ownership_Tiers.csv has 0 rows!")

    required_tier_fields = ["post_id", "title", "cluster", "query", "tier", "tier_rank"]
    for field in required_tier_fields:
        empty = sum(1 for r in tiers if not r.get(field, "").strip())
        if empty > 0:
            issues.append(f"Query_Ownership_Tiers.csv: {empty} empty values in '{field}'")

    # Check all tiers are valid
    valid_tiers = {"OWNED", "DEFENSIBLE", "EMERGING", "OPPORTUNITY", "COMPETITOR_CONTROLLED"}
    tier_values = set(r["tier"] for r in tiers)
    invalid = tier_values - valid_tiers
    if invalid:
        issues.append(f"Query_Ownership_Tiers.csv: invalid tiers: {invalid}")
    else:
        tier_counts = []
        for t in sorted(valid_tiers):
            count = sum(1 for r in tiers if r["tier"] == t)
            tier_counts.append(f"{t}: {count}")
        print(f"    Tier distribution: {', '.join(tier_counts)}")

    # Validate Query_Ownership_Tiers_Summary.csv
    summary = read_csv("Query_Ownership_Tiers_Summary.csv")
    print(f"  Query_Ownership_Tiers_Summary.csv: {len(summary)} rows")
    if len(summary) != 11:
        issues.append(f"Query_Ownership_Tiers_Summary.csv: expected 11 clusters, got {len(summary)}")

    required_summary_fields = ["cluster", "total_queries", "expansion_potential_pct"]
    for field in required_summary_fields:
        empty = sum(1 for r in summary if not r.get(field, "").strip())
        if empty > 0:
            issues.append(f"Query_Ownership_Tiers_Summary.csv: {empty} empty values in '{field}'")

    # Validate Visibility_Dominance.csv
    dom = read_csv("Visibility_Dominance.csv")
    print(f"  Visibility_Dominance.csv: {len(dom)} rows")
    if len(dom) != 11:
        issues.append(f"Visibility_Dominance.csv: expected 11 clusters, got {len(dom)}")

    required_dom_fields = ["cluster", "authority_score", "ownership_score", "visibility_score",
                           "snippet_score", "citation_score", "search_coverage_score",
                           "overall_dominance", "grade"]
    for field in required_dom_fields:
        empty = sum(1 for r in dom if not r.get(field, "").strip())
        if empty > 0:
            issues.append(f"Visibility_Dominance.csv: {empty} empty values in '{field}'")

    # Validate Visibility_Dominance_Posts.csv
    dom_posts = read_csv("Visibility_Dominance_Posts.csv")
    print(f"  Visibility_Dominance_Posts.csv: {len(dom_posts)} rows")
    if len(dom_posts) != 168:
        issues.append(f"Visibility_Dominance_Posts.csv: expected 168 posts, got {len(dom_posts)}")

    required_post_fields = ["post_id", "title", "cluster", "authority_score",
                            "ownership_score", "visibility_score", "overall_dominance", "grade"]
    for field in required_post_fields:
        empty = sum(1 for r in dom_posts if not r.get(field, "").strip())
        if empty > 0:
            issues.append(f"Visibility_Dominance_Posts.csv: {empty} empty values in '{field}'")

    # Final result
    if issues:
        print("\n  ISSUES FOUND:")
        for issue in issues:
            print(f"    - {issue}")
        return False
    else:
        print("\n  ALL VALIDATIONS PASSED")
        return True


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("Phase 11Y + 11Z Data Engines")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base directory: {BASE_DIR}")

    # Engine 1: Query Ownership Tiers
    tier_rows, tier_summary = run_phase_11y()

    # Engine 2: Visibility Dominance
    cluster_dom, post_dom = run_phase_11z()

    # Validate all outputs
    ok = validate_outputs()

    if ok:
        print("\nPhase 11Y + 11Z COMPLETE. All 4 output files generated and validated.")
    else:
        print("\nPhase 11Y + 11Z COMPLETE with issues. Please review above.")
        sys.exit(1)
