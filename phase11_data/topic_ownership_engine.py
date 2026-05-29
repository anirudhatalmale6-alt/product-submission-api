#!/usr/bin/env python3
"""
PetHub Online Phase 11 - Topic Ownership Engine
Tracks cluster ownership status and identifies what's needed to push all clusters above 90 dominance.
"""

import csv
import os
import statistics

DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10cc_data"
OUT_DIR = "/var/lib/freelancer/projects/40416335/phase11_data"

# ---------------------------------------------------------------------------
# 1. Load all source CSVs
# ---------------------------------------------------------------------------

def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(filename, rows, fieldnames):
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"  -> Wrote {path} ({len(rows)} rows)")


# Load data
roadmaps = load_csv("Cluster_Dominance_Roadmaps.csv")
citations = load_csv("Citation_Dominance_Report.csv")
moats = load_csv("Authority_Moat_Report.csv")
ai_prefs = load_csv("AI_Answer_Preference.csv")
semantic = load_csv("Semantic_Market_Share.csv")
comparisons = load_csv("Comparison_Dominance_Report.csv")

# Also load trust depth for the health matrix
trust_depth = []
trust_path = os.path.join(DATA_DIR, "Trust_Depth_Report.csv")
if os.path.exists(trust_path):
    trust_depth = load_csv("Trust_Depth_Report.csv")

# ---------------------------------------------------------------------------
# 2. Build per-cluster aggregation
# ---------------------------------------------------------------------------

# Cluster dominance from roadmaps
cluster_dom = {}
for r in roadmaps:
    c = r["cluster"].strip()
    if not c:
        continue
    cluster_dom[c] = {
        "dominance_score": float(r["dominance_score"]),
        "weakest_dim": r["weakest_dim"].strip(),
        "action_needed": r["action_needed"].strip(),
        "posts_to_modify": int(r["posts_to_modify"]),
    }

all_clusters = sorted(cluster_dom.keys())

# Per-cluster citation scores
cluster_citations = {c: [] for c in all_clusters}
for row in citations:
    c = row["cluster"].strip()
    if c in cluster_citations:
        cluster_citations[c].append(float(row["citation_score"]))

# Per-cluster moat scores
cluster_moats = {c: [] for c in all_clusters}
for row in moats:
    c = row["cluster"].strip()
    if c in cluster_moats:
        cluster_moats[c].append(float(row["moat_score"]))

# Per-cluster AI preference scores
cluster_ai = {c: [] for c in all_clusters}
for row in ai_prefs:
    c = row["cluster"].strip()
    if c in cluster_ai:
        cluster_ai[c].append(float(row["ai_preference_score"]))

# Per-cluster trust scores
cluster_trust = {c: [] for c in all_clusters}
for row in trust_depth:
    c = row["cluster"].strip()
    if c in cluster_trust:
        cluster_trust[c].append(float(row["trust_score"]))

# Semantic data (already cluster-level)
cluster_semantic = {}
for row in semantic:
    c = row["cluster"].strip()
    if c:
        cluster_semantic[c] = {
            "semantic_score": float(row["semantic_score"]),
            "owned_entities": int(row["owned_entities"]),
            "glossary_terms": int(row["glossary_terms"]),
            "faq_items": int(row["faq_items"]),
            "comparison_tables": int(row["comparison_tables"]),
            "practical_guides": int(row["practical_guides"]),
        }

# Comparison data (already cluster-level)
cluster_comparison = {}
for row in comparisons:
    c = row["cluster"].strip()
    if c:
        cluster_comparison[c] = {
            "avg_comparison_score": float(row["avg_comparison_score"]),
            "total_tables": int(row["total_tables"]),
            "posts_with_tables": int(row["posts_with_tables"]),
        }


def safe_mean(lst, default=0.0):
    return round(statistics.mean(lst), 1) if lst else default


# ---------------------------------------------------------------------------
# 3. Generate topic_ownership_status.csv
# ---------------------------------------------------------------------------

def ownership_status_label(score):
    if score >= 90:
        return "OWNED"
    elif score >= 75:
        return "CONTESTED"
    else:
        return "EMERGING"


def determine_priority_action(cluster_info, avg_citation, avg_moat, avg_ai, comp_info):
    """Determine the single highest-impact action to reach 90."""
    score = cluster_info["dominance_score"]
    if score >= 90:
        return "Maintain current position; strengthen comparison depth"

    weakest = cluster_info["weakest_dim"]
    gap = 90 - score

    # Check which dimension is weakest
    if "comparison" in weakest.lower():
        comp_score = comp_info.get("avg_comparison_score", 0) if comp_info else 0
        if comp_score < 70:
            return f"Add striped comparison tables (comparison at {comp_score}); need +{round(gap, 1)} overall"
        else:
            return f"Strengthen comparison depth to 85+ (currently {comp_score}); need +{round(gap, 1)} overall"
    elif "citation" in weakest.lower():
        return f"Improve reference quality and extractability; need +{round(gap, 1)} overall"
    elif "moat" in weakest.lower():
        return f"Add glossary terms and educational depth; need +{round(gap, 1)} overall"
    elif "trust" in weakest.lower():
        return f"Add named references and trust blocks; need +{round(gap, 1)} overall"
    elif "ai" in weakest.lower():
        return f"Improve AI answer superiority and extraction; need +{round(gap, 1)} overall"
    else:
        return f"Address weakest dimension ({weakest}); need +{round(gap, 1)} overall"


ownership_rows = []
for c in all_clusters:
    info = cluster_dom[c]
    score = info["dominance_score"]
    gap = max(0, round(90 - score, 1))
    status = ownership_status_label(score)
    post_count = len(cluster_citations[c])
    avg_cit = safe_mean(cluster_citations[c])
    avg_moat = safe_mean(cluster_moats[c])
    avg_ai = safe_mean(cluster_ai[c])
    comp = cluster_comparison.get(c)
    priority_action = determine_priority_action(info, avg_cit, avg_moat, avg_ai, comp)

    ownership_rows.append({
        "cluster": c,
        "dominance_score": score,
        "gap_to_90": gap,
        "ownership_status": status,
        "post_count": post_count,
        "avg_citation": avg_cit,
        "avg_moat": avg_moat,
        "avg_ai_pref": avg_ai,
        "weakest_dimension": info["weakest_dim"],
        "priority_action": priority_action,
    })

# Sort by dominance score ascending (weakest first)
ownership_rows.sort(key=lambda r: r["dominance_score"])

write_csv("topic_ownership_status.csv", ownership_rows, [
    "cluster", "dominance_score", "gap_to_90", "ownership_status",
    "post_count", "avg_citation", "avg_moat", "avg_ai_pref",
    "weakest_dimension", "priority_action",
])


# ---------------------------------------------------------------------------
# 4. Generate ownership_acceleration.csv
# ---------------------------------------------------------------------------

def generate_acceleration_actions(c, info, avg_cit, avg_moat, avg_ai, comp, sem):
    """Generate specific actions with estimated impact for each cluster."""
    actions = []
    score = info["dominance_score"]
    target = 90.0
    gap = max(0, round(target - score, 1))

    comp_score = comp.get("avg_comparison_score", 0) if comp else 0
    sem_score = sem.get("semantic_score", 0) if sem else 0

    # Action 1: Comparison tables (almost always the weakest)
    if comp_score < 85:
        impact = min(gap, round((85 - comp_score) * 0.15, 1))
        actions.append({
            "cluster": c,
            "current_score": score,
            "target_score": target,
            "gap": gap,
            "action_type": "comparison_enhancement",
            "specific_action": f"Add/improve striped comparison tables in all posts (current avg: {comp_score})",
            "estimated_impact": f"+{impact}",
            "priority": 1,
        })

    # Action 2: Educational depth / moat
    if avg_moat < 85:
        impact = min(gap, round((85 - avg_moat) * 0.1, 1))
        actions.append({
            "cluster": c,
            "current_score": score,
            "target_score": target,
            "gap": gap,
            "action_type": "moat_deepening",
            "specific_action": f"Add educational sections, glossary depth, and unique methodology (moat avg: {avg_moat})",
            "estimated_impact": f"+{impact}",
            "priority": 2,
        })

    # Action 3: Citation quality
    if avg_cit < 95:
        impact = min(gap, round((95 - avg_cit) * 0.08, 1))
        actions.append({
            "cluster": c,
            "current_score": score,
            "target_score": target,
            "gap": gap,
            "action_type": "citation_improvement",
            "specific_action": f"Improve extractability and reference quality (citation avg: {avg_cit})",
            "estimated_impact": f"+{impact}",
            "priority": 3,
        })

    # Action 4: AI preference boost
    if avg_ai < 92:
        impact = min(gap, round((92 - avg_ai) * 0.1, 1))
        actions.append({
            "cluster": c,
            "current_score": score,
            "target_score": target,
            "gap": gap,
            "action_type": "ai_optimization",
            "specific_action": f"Optimize for AI answer extraction with clear summaries (AI pref avg: {avg_ai})",
            "estimated_impact": f"+{impact}",
            "priority": 3,
        })

    # Action 5: New content to cover gaps
    post_count = len(cluster_citations[c])
    if post_count < 10:
        actions.append({
            "cluster": c,
            "current_score": score,
            "target_score": target,
            "gap": gap,
            "action_type": "content_expansion",
            "specific_action": f"Publish additional posts to strengthen cluster depth (currently {post_count} posts)",
            "estimated_impact": f"+{min(gap, 2.0)}",
            "priority": 2 if gap > 2 else 4,
        })

    # Action 6: Internal linking / semantic reinforcement
    if sem_score < 100:
        actions.append({
            "cluster": c,
            "current_score": score,
            "target_score": target,
            "gap": gap,
            "action_type": "semantic_reinforcement",
            "specific_action": f"Strengthen internal linking and entity coverage (semantic: {sem_score})",
            "estimated_impact": f"+{min(gap, 1.5)}",
            "priority": 4,
        })

    # If already owned, add maintenance action
    if score >= 90:
        actions.append({
            "cluster": c,
            "current_score": score,
            "target_score": 95.0,
            "gap": round(95 - score, 1),
            "action_type": "dominance_defense",
            "specific_action": "Maintain and defend position; update content quarterly; monitor competitor entries",
            "estimated_impact": "+0.5",
            "priority": 5,
        })

    return actions


accel_rows = []
for c in all_clusters:
    info = cluster_dom[c]
    avg_cit = safe_mean(cluster_citations[c])
    avg_moat = safe_mean(cluster_moats[c])
    avg_ai = safe_mean(cluster_ai[c])
    comp = cluster_comparison.get(c)
    sem = cluster_semantic.get(c)
    accel_rows.extend(generate_acceleration_actions(c, info, avg_cit, avg_moat, avg_ai, comp, sem))

# Sort by priority then by gap descending
accel_rows.sort(key=lambda r: (r["priority"], -float(r["gap"])))

write_csv("ownership_acceleration.csv", accel_rows, [
    "cluster", "current_score", "target_score", "gap",
    "action_type", "specific_action", "estimated_impact", "priority",
])


# ---------------------------------------------------------------------------
# 5. Generate cluster_health_matrix.csv
# ---------------------------------------------------------------------------

def health_label(score, thresholds=(90, 80, 70)):
    """Convert a numeric score to a health label."""
    if score >= thresholds[0]:
        return "STRONG"
    elif score >= thresholds[1]:
        return "GOOD"
    elif score >= thresholds[2]:
        return "MODERATE"
    else:
        return "WEAK"


def overall_health(labels):
    """Determine overall health from component labels."""
    counts = {"STRONG": 0, "GOOD": 0, "MODERATE": 0, "WEAK": 0}
    for l in labels:
        counts[l] = counts.get(l, 0) + 1
    if counts["WEAK"] >= 2:
        return "AT_RISK"
    elif counts["WEAK"] >= 1 or counts["MODERATE"] >= 3:
        return "NEEDS_ATTENTION"
    elif counts["MODERATE"] >= 1:
        return "HEALTHY"
    else:
        return "EXCELLENT"


health_rows = []
for c in all_clusters:
    avg_cit = safe_mean(cluster_citations[c])
    avg_moat = safe_mean(cluster_moats[c])
    avg_ai = safe_mean(cluster_ai[c])
    avg_trust = safe_mean(cluster_trust[c])
    sem = cluster_semantic.get(c, {})
    sem_score = sem.get("semantic_score", 0)
    comp = cluster_comparison.get(c, {})
    comp_score = comp.get("avg_comparison_score", 0)

    cit_health = health_label(avg_cit)
    moat_health = health_label(avg_moat)
    ai_health = health_label(avg_ai)
    sem_health = health_label(sem_score)
    comp_health = health_label(comp_score, thresholds=(85, 75, 65))
    trust_health = health_label(avg_trust)

    labels = [cit_health, moat_health, ai_health, sem_health, comp_health, trust_health]
    oh = overall_health(labels)

    health_rows.append({
        "cluster": c,
        "citation_health": f"{cit_health} ({avg_cit})",
        "moat_health": f"{moat_health} ({avg_moat})",
        "ai_health": f"{ai_health} ({avg_ai})",
        "semantic_health": f"{sem_health} ({sem_score})",
        "comparison_health": f"{comp_health} ({comp_score})",
        "trust_health": f"{trust_health} ({avg_trust})",
        "overall_health": oh,
    })

# Sort: worst overall health first
health_order = {"AT_RISK": 0, "NEEDS_ATTENTION": 1, "HEALTHY": 2, "EXCELLENT": 3}
health_rows.sort(key=lambda r: health_order.get(r["overall_health"], 99))

write_csv("cluster_health_matrix.csv", health_rows, [
    "cluster", "citation_health", "moat_health", "ai_health",
    "semantic_health", "comparison_health", "trust_health", "overall_health",
])


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print("\n=== TOPIC OWNERSHIP ENGINE COMPLETE ===")
print(f"Total clusters analyzed: {len(all_clusters)}")
owned = sum(1 for r in ownership_rows if r["ownership_status"] == "OWNED")
contested = sum(1 for r in ownership_rows if r["ownership_status"] == "CONTESTED")
emerging = sum(1 for r in ownership_rows if r["ownership_status"] == "EMERGING")
print(f"  OWNED (>=90):       {owned}")
print(f"  CONTESTED (75-90):  {contested}")
print(f"  EMERGING (<75):     {emerging}")
print(f"Total acceleration actions: {len(accel_rows)}")

# Show the contested clusters that need attention
print("\n--- Clusters needing push to 90 ---")
for r in ownership_rows:
    if r["ownership_status"] == "CONTESTED":
        print(f"  {r['cluster']}: {r['dominance_score']} (gap: {r['gap_to_90']}) | {r['weakest_dimension']}")
