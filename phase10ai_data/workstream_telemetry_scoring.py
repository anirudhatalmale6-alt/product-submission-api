#!/usr/bin/env python3
"""
TELEMETRY: Full Phase 10AI Scoring
Score 20 posts across clusters on 7 dimensions.
"""

import subprocess, json, csv, re, html, sys, time
from datetime import datetime

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
BASE = "https://pethubonline.com/wp-json/wp/v2"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ai_data"
INVENTORY = "/var/lib/freelancer/projects/40416335/phase10af_data/post_authority_inventory.csv"

def api_get(endpoint):
    url = f"{BASE}/{endpoint}"
    r = subprocess.run(["curl", "-s", "--compressed", "-u", AUTH, url], capture_output=True, text=True, timeout=60)
    try:
        return json.loads(r.stdout)
    except:
        print(f"  [WARN] Failed to parse: {r.stdout[:200]}")
        return None

def strip_html(text):
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    return re.sub(r'\s+', ' ', text).strip()

# Load inventory for cluster assignments
cluster_map = {}  # id -> cluster
with open(INVENTORY) as f:
    reader = csv.DictReader(f)
    for row in reader:
        cluster_map[int(row["id"])] = row["cluster"]

# Select 20 posts spread across clusters
print("=" * 70)
print("TELEMETRY: Phase 10AI Full Scoring")
print("=" * 70)

# Get posts by cluster from inventory
cluster_posts = {}
with open(INVENTORY) as f:
    reader = csv.DictReader(f)
    for row in reader:
        c = row["cluster"]
        cluster_posts.setdefault(c, []).append(int(row["id"]))

# Pick ~20 posts spread across clusters
target_clusters = ["Dog Toys", "Dog Food", "Dog Beds", "Puppy Care", "Cat Supplies",
                   "Dog Health", "Dog Harnesses", "Dog Training", "Dog Grooming",
                   "Cat Toys", "Educational"]
sample_ids = []
for cluster in target_clusters:
    ids = cluster_posts.get(cluster, [])
    # Take 2 from each, but fill to 20
    sample_ids.extend(ids[:2])

# Trim to 20
sample_ids = sample_ids[:20]
print(f"\nSampling {len(sample_ids)} posts across {len(target_clusters)} clusters")

# Fetch and score each post
scores_trust = []
scores_eeat = []
scores_conversion = []
scores_practical = []
scores_comparison = []
scores_citation = []
scores_hub = []

for pid in sample_ids:
    print(f"\n  Scoring post {pid}...")
    post = api_get(f"posts/{pid}")
    if not post or "id" not in post:
        print(f"    [SKIP] Could not fetch")
        continue

    content = post.get("content", {}).get("rendered", "")
    title = strip_html(post.get("title", {}).get("rendered", ""))
    cluster = cluster_map.get(pid, "Unknown")
    content_lower = content.lower()

    # ============================
    # 1. Trust Intensity Score (0-100)
    # ============================
    trust_signals = {
        "methodology_ref": bool(re.search(r'(?i)(methodology|our\s+method|how\s+we\s+(test|evaluate|review|assess))', content)),
        "source_citation": bool(re.search(r'(?i)(source|according\s+to|research\s+(show|suggest|indicate|find)|stud(y|ies)\s+(show|suggest|find))', content)),
        "correction_policy": bool(re.search(r'(?i)(correction\s+policy|we\s+correct|update\s+policy)', content)),
        "ai_disclosure": bool(re.search(r'(?i)(ai[\s-]assist|artificial\s+intelligence|machine\s+learning|ai\s+disclosure)', content)),
        "evidence_statement": bool(re.search(r'(?i)(evidence\s+(suggest|show|indicate|support)|based\s+on\s+evidence|clinical\s+evidence|scientific\s+evidence)', content)),
        "editorial_process": bool(re.search(r'(?i)(editorial\s+process|reviewed\s+by|fact[\s-]check|editor|peer[\s-]review)', content)),
        "transparency_note": bool(re.search(r'(?i)(transparency|affiliate\s+disclosure|sponsored|we\s+may\s+earn)', content)),
        "last_updated": bool(re.search(r'(?i)(last\s+updated|reviewed\s+on|updated\s+on|current\s+as\s+of)', content)),
    }
    trust_count = sum(trust_signals.values())
    trust_score = int((trust_count / 8) * 100)

    scores_trust.append({
        "post_id": pid, "title": title, "cluster": cluster,
        "trust_intensity_score": trust_score,
        **{f"has_{k}": v for k, v in trust_signals.items()}
    })

    # ============================
    # 2. E-E-A-T Depth Score (0-100)
    # ============================
    eeat_blocks = {
        "about_this_guide": bool(re.search(r'(?i)about\s+this\s+guide', content)),
        "why_this_matters": bool(re.search(r'(?i)why\s+this\s+matters', content)),
        "what_we_considered": bool(re.search(r'(?i)what\s+we\s+considered', content)),
        "how_we_evaluated": bool(re.search(r'(?i)how\s+we\s+evaluated', content)),
        "what_pet_owners_know": bool(re.search(r'(?i)what\s+pet\s+owners\s+should\s+know', content)),
        "when_advice_differ": bool(re.search(r'(?i)when\s+advice\s+may\s+differ', content)),
    }
    eeat_count = sum(eeat_blocks.values())
    eeat_score = int((eeat_count / 6) * 100)

    scores_eeat.append({
        "post_id": pid, "title": title, "cluster": cluster,
        "eeat_depth_score": eeat_score,
        **{f"has_{k}": v for k, v in eeat_blocks.items()}
    })

    # ============================
    # 3. Conversion Sophistication Score (0-100)
    # ============================
    conv_elements = {
        "best_for_sections": bool(re.search(r'(?i)best\s+for', content)),
        "suitability_guides": bool(re.search(r'(?i)(suitab|ideal\s+for|recommended\s+for|good\s+for|perfect\s+for)', content)),
        "decision_trees": bool(re.search(r'(?i)(decision|choose|choosing|how\s+to\s+pick|which.*right\s+for)', content)),
        "budget_vs_premium": bool(re.search(r'(?i)(budget|premium|price\s+range|afford|value\s+for\s+money)', content)),
        "beginner_recommendations": bool(re.search(r'(?i)(beginner|first[\s-]time|new\s+(owner|parent|to\s+))', content)),
    }
    conv_count = sum(conv_elements.values())
    conv_score = int((conv_count / 5) * 100)

    scores_conversion.append({
        "post_id": pid, "title": title, "cluster": cluster,
        "conversion_sophistication_score": conv_score,
        **{f"has_{k}": v for k, v in conv_elements.items()}
    })

    # ============================
    # 4. Practical Usefulness Score (0-100)
    # ============================
    practical_blocks = {
        "troubleshooting": bool(re.search(r'(?i)(troubleshoot|common\s+(problem|issue|failure|mistake))', content)),
        "routines_schedules": bool(re.search(r'(?i)(routine|schedule|daily|weekly|morning|evening)', content)),
        "warning_signs": bool(re.search(r'(?i)(warning\s+sign|red\s+flag|watch\s+for|danger|caution)', content)),
        "measurable_checks": bool(re.search(r'(?i)(measure|check\s+for|test\s+for|indicator|monitor)', content)),
        "what_to_do_next": bool(re.search(r'(?i)(what\s+to\s+do\s+next|next\s+step|action\s+plan|getting\s+started)', content)),
        "when_to_seek_help": bool(re.search(r'(?i)(when\s+to\s+(seek|consult|see|visit)|consult\s+(a\s+)?vet|professional\s+help)', content)),
        "common_failures": bool(re.search(r'(?i)(common\s+(mistake|failure|error|pitfall)|avoid\s+these|don.t\s+make)', content)),
    }
    practical_count = sum(practical_blocks.values())
    practical_score = int((practical_count / 7) * 100)

    scores_practical.append({
        "post_id": pid, "title": title, "cluster": cluster,
        "practical_usefulness_score": practical_score,
        **{f"has_{k}": v for k, v in practical_blocks.items()}
    })

    # ============================
    # 5. Comparison Quality Score (0-100)
    # ============================
    has_table = bool(re.search(r'<table', content, re.I))
    has_best_for_col = False
    has_4_plus_rows = False
    has_suitability_info = False
    has_multi_dimensions = False

    if has_table:
        tables = re.findall(r'<table.*?</table>', content, re.I | re.S)
        if tables:
            main_table = tables[0]
            has_best_for_col = bool(re.search(r'(?i)best\s+for', main_table))
            rows = re.findall(r'<tr', main_table, re.I)
            has_4_plus_rows = len(rows) >= 5  # 1 header + 4 data
            has_suitability_info = bool(re.search(r'(?i)(suitab|ideal|recommend)', main_table))
            # Multiple dimensions = 4+ columns
            first_row = main_table.split('</tr>')[0] if '</tr>' in main_table else ""
            cols = re.findall(r'<t[hd]', first_row, re.I)
            has_multi_dimensions = len(cols) >= 4

    comp_score = 0
    if has_table: comp_score += 20
    if has_best_for_col: comp_score += 20
    if has_4_plus_rows: comp_score += 20
    if has_suitability_info: comp_score += 20
    if has_multi_dimensions: comp_score += 20

    scores_comparison.append({
        "post_id": pid, "title": title, "cluster": cluster,
        "comparison_quality_score": comp_score,
        "has_table": has_table,
        "has_best_for_column": has_best_for_col,
        "has_4plus_rows": has_4_plus_rows,
        "has_suitability_info": has_suitability_info,
        "has_multiple_dimensions": has_multi_dimensions,
    })

    # ============================
    # 6. Citation Readiness Score (0-100)
    # ============================
    citation_elements = {
        "at_a_glance": bool(re.search(r'(?i)(at\s+a\s+glance|overview|summary\s+box|quick\s+summary)', content)),
        "key_takeaways": bool(re.search(r'(?i)key\s+takeaway', content)),
        "faq_section": bool(re.search(r'(?i)(frequently\s+asked|faq|common\s+questions)', content)),
        "quick_answer": bool(re.search(r'(?i)(quick\s+answer|short\s+answer|in\s+brief|tldr|tl;dr)', content)),
        "source_references": bool(re.search(r'(?i)(source|reference|citation|according\s+to|research)', content)),
        "uk_authority_citations": bool(re.search(r'(?i)(rspca|kennel\s+club|blue\s+cross|pdsa|uk\s+vet|british|bva)', content)),
    }
    citation_count = sum(citation_elements.values())
    citation_score = int((citation_count / 6) * 100)

    scores_citation.append({
        "post_id": pid, "title": title, "cluster": cluster,
        "citation_readiness_score": citation_score,
        **{f"has_{k}": v for k, v in citation_elements.items()}
    })

    # ============================
    # 7. Hub Authority Score (0-100) - only for hub-like pages
    # ============================
    # Detect if this is a hub page (contains multiple spoke links)
    internal_links = re.findall(r'href=["\']https?://pethubonline\.com/([^"\'#]+)', content, re.I)
    unique_internal = list(set(internal_links))
    is_hub = len(unique_internal) >= 5  # Hubs typically link to many spokes

    if is_hub:
        # Spoke coverage: how many unique internal pages linked
        spoke_coverage = min(100, len(unique_internal) * 5)  # 20 links = 100%

        # Spoke descriptions: do internal links have surrounding descriptive text?
        links_with_context = 0
        for link_match in re.finditer(r'<a[^>]*href=["\']https?://pethubonline\.com/[^"\']+["\'][^>]*>.*?</a>', content, re.I | re.S):
            # Check if link is within a paragraph or list item with 50+ chars
            start = max(0, link_match.start() - 200)
            context = content[start:link_match.end() + 200]
            clean_context = strip_html(context)
            if len(clean_context) > 80:
                links_with_context += 1
        desc_coverage = min(100, int((links_with_context / max(len(unique_internal), 1)) * 100))

        # Cross-reference density
        cross_ref = min(100, len(unique_internal) * 4)

        hub_score = int((spoke_coverage * 0.4 + desc_coverage * 0.3 + cross_ref * 0.3))
    else:
        hub_score = 0
        spoke_coverage = 0
        desc_coverage = 0
        cross_ref = 0

    scores_hub.append({
        "post_id": pid, "title": title, "cluster": cluster,
        "is_hub": is_hub,
        "hub_authority_score": hub_score,
        "spoke_coverage_pct": spoke_coverage if is_hub else "",
        "spoke_description_pct": desc_coverage if is_hub else "",
        "cross_reference_density": cross_ref if is_hub else "",
    })

    print(f"    '{title[:50]}' [{cluster}] Trust:{trust_score} EEAT:{eeat_score} Conv:{conv_score} Pract:{practical_score} Comp:{comp_score} Cite:{citation_score} Hub:{hub_score}")
    time.sleep(0.5)

# Save all CSV files
def save_csv(filename, data, fieldnames):
    path = f"{DATA_DIR}/{filename}"
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    print(f"  Saved {len(data)} rows to {path}")
    return path

print("\n[SAVING SCORE FILES]")

save_csv("trust_intensity_scores.csv", scores_trust,
         ["post_id", "title", "cluster", "trust_intensity_score",
          "has_methodology_ref", "has_source_citation", "has_correction_policy",
          "has_ai_disclosure", "has_evidence_statement", "has_editorial_process",
          "has_transparency_note", "has_last_updated"])

save_csv("eeat_depth_scores.csv", scores_eeat,
         ["post_id", "title", "cluster", "eeat_depth_score",
          "has_about_this_guide", "has_why_this_matters", "has_what_we_considered",
          "has_how_we_evaluated", "has_what_pet_owners_know", "has_when_advice_differ"])

save_csv("conversion_sophistication_scores.csv", scores_conversion,
         ["post_id", "title", "cluster", "conversion_sophistication_score",
          "has_best_for_sections", "has_suitability_guides", "has_decision_trees",
          "has_budget_vs_premium", "has_beginner_recommendations"])

save_csv("practical_usefulness_scores.csv", scores_practical,
         ["post_id", "title", "cluster", "practical_usefulness_score",
          "has_troubleshooting", "has_routines_schedules", "has_warning_signs",
          "has_measurable_checks", "has_what_to_do_next", "has_when_to_seek_help",
          "has_common_failures"])

save_csv("comparison_quality_scores.csv", scores_comparison,
         ["post_id", "title", "cluster", "comparison_quality_score",
          "has_table", "has_best_for_column", "has_4plus_rows",
          "has_suitability_info", "has_multiple_dimensions"])

save_csv("citation_readiness_scores.csv", scores_citation,
         ["post_id", "title", "cluster", "citation_readiness_score",
          "has_at_a_glance", "has_key_takeaways", "has_faq_section",
          "has_quick_answer", "has_source_references", "has_uk_authority_citations"])

# Hub authority scores only for hub posts
hub_csv_data = [{k: v for k, v in s.items() if k != "is_hub"} for s in scores_hub if s["is_hub"]]
if hub_csv_data:
    save_csv("hub_authority_scores.csv", hub_csv_data,
             ["post_id", "title", "cluster", "hub_authority_score",
              "spoke_coverage_pct", "spoke_description_pct", "cross_reference_density"])

# ============================
# DASHBOARD: Summary per cluster
# ============================
print("\n[CREATING DASHBOARD]")

# Aggregate by cluster
cluster_scores = {}
for i, pid in enumerate([s["post_id"] for s in scores_trust]):
    cluster = scores_trust[i]["cluster"]
    if cluster not in cluster_scores:
        cluster_scores[cluster] = {
            "trust": [], "eeat": [], "conversion": [], "practical": [],
            "comparison": [], "citation": [], "hub": [], "count": 0
        }
    cluster_scores[cluster]["trust"].append(scores_trust[i]["trust_intensity_score"])
    cluster_scores[cluster]["eeat"].append(scores_eeat[i]["eeat_depth_score"])
    cluster_scores[cluster]["conversion"].append(scores_conversion[i]["conversion_sophistication_score"])
    cluster_scores[cluster]["practical"].append(scores_practical[i]["practical_usefulness_score"])
    cluster_scores[cluster]["comparison"].append(scores_comparison[i]["comparison_quality_score"])
    cluster_scores[cluster]["citation"].append(scores_citation[i]["citation_readiness_score"])
    cluster_scores[cluster]["hub"].append(scores_hub[i]["hub_authority_score"])
    cluster_scores[cluster]["count"] += 1

dashboard_rows = []
for cluster, data in sorted(cluster_scores.items()):
    n = data["count"]
    avg = lambda lst: sum(lst) / len(lst) if lst else 0
    composite = (avg(data["trust"]) + avg(data["eeat"]) + avg(data["conversion"]) +
                 avg(data["practical"]) + avg(data["comparison"]) + avg(data["citation"])) / 6

    dashboard_rows.append({
        "cluster": cluster,
        "posts_scored": n,
        "avg_trust_intensity": round(avg(data["trust"]), 1),
        "avg_eeat_depth": round(avg(data["eeat"]), 1),
        "avg_conversion_sophistication": round(avg(data["conversion"]), 1),
        "avg_practical_usefulness": round(avg(data["practical"]), 1),
        "avg_comparison_quality": round(avg(data["comparison"]), 1),
        "avg_citation_readiness": round(avg(data["citation"]), 1),
        "avg_hub_authority": round(avg(data["hub"]), 1),
        "composite_score": round(composite, 1),
    })

dash_path = f"{DATA_DIR}/phase10ai_dashboard.csv"
with open(dash_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "cluster", "posts_scored", "avg_trust_intensity", "avg_eeat_depth",
        "avg_conversion_sophistication", "avg_practical_usefulness",
        "avg_comparison_quality", "avg_citation_readiness", "avg_hub_authority",
        "composite_score"
    ])
    writer.writeheader()
    for row in dashboard_rows:
        writer.writerow(row)
print(f"  Dashboard saved to {dash_path}")

# Print dashboard
print(f"\n{'=' * 90}")
print(f"PHASE 10AI SCORING DASHBOARD")
print(f"{'=' * 90}")
print(f"{'Cluster':<18} {'N':>3} {'Trust':>6} {'EEAT':>6} {'Conv':>6} {'Pract':>6} {'Comp':>6} {'Cite':>6} {'Hub':>5} {'TOTAL':>7}")
print("-" * 90)
for row in dashboard_rows:
    print(f"{row['cluster']:<18} {row['posts_scored']:>3} {row['avg_trust_intensity']:>6.1f} {row['avg_eeat_depth']:>6.1f} "
          f"{row['avg_conversion_sophistication']:>6.1f} {row['avg_practical_usefulness']:>6.1f} "
          f"{row['avg_comparison_quality']:>6.1f} {row['avg_citation_readiness']:>6.1f} "
          f"{row['avg_hub_authority']:>5.1f} {row['composite_score']:>7.1f}")
print("-" * 90)

# Overall averages
if dashboard_rows:
    overall_composite = sum(r["composite_score"] for r in dashboard_rows) / len(dashboard_rows)
    print(f"{'OVERALL':<18} {sum(r['posts_scored'] for r in dashboard_rows):>3} "
          f"{sum(r['avg_trust_intensity'] for r in dashboard_rows)/len(dashboard_rows):>6.1f} "
          f"{sum(r['avg_eeat_depth'] for r in dashboard_rows)/len(dashboard_rows):>6.1f} "
          f"{sum(r['avg_conversion_sophistication'] for r in dashboard_rows)/len(dashboard_rows):>6.1f} "
          f"{sum(r['avg_practical_usefulness'] for r in dashboard_rows)/len(dashboard_rows):>6.1f} "
          f"{sum(r['avg_comparison_quality'] for r in dashboard_rows)/len(dashboard_rows):>6.1f} "
          f"{sum(r['avg_citation_readiness'] for r in dashboard_rows)/len(dashboard_rows):>6.1f} "
          f"{sum(r['avg_hub_authority'] for r in dashboard_rows)/len(dashboard_rows):>5.1f} "
          f"{overall_composite:>7.1f}")

print(f"\n{'=' * 70}")
print(f"TELEMETRY SCORING COMPLETE")
print(f"{'=' * 70}")
