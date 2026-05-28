#!/usr/bin/env python3
"""
10AE-H: Momentum Prioritization Engine
pethubonline.com — WordPress pet supplies blog (144 published posts)

PURPOSE: Automatically prioritize the highest-ROI quality accelerations across
all dimensions. This is the master priority engine that ranks ALL possible
improvements by expected impact.

Priority Order (from client directive):
1. References (highest ROI)
2. Comparisons
3. Practical guidance
4. Citation confidence
5. Trust depth
6. Semantic reinforcement
7. Cross-cluster flow

Output CSVs:
1. Momentum_Priority_Queue.csv       — Every action ranked by ROI
2. ROI_Rankings_By_Cluster.csv        — Per-cluster aggregated priorities
3. Acceleration_Roadmap.csv           — Phased execution roadmap
"""

import subprocess
import json
import csv
import re
import os
import sys
from collections import defaultdict
from html import unescape
from datetime import datetime

# ── Configuration ──────────────────────────────────────────────────────────
WP_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase10ae_data"

# UK Authority references for Reference scoring
AUTHORITY_SOURCES = [
    "rspca", "bva", "pdsa", "gov.uk", "battersea", "blue cross",
    "bluecross", "fediaf", "defra", "pfma", "kennel club",
    "cats protection", "british veterinary"
]

# ── WordPress API ──────────────────────────────────────────────────────────

def wp_api_get(endpoint):
    """GET request to WP REST API using curl."""
    url = f"{WP_URL}{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"  [ERROR] curl failed: {result.stderr[:200]}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  [ERROR] JSON decode failed: {result.stdout[:200]}")
        return None


def fetch_all_posts():
    """Fetch all published posts via WP REST API."""
    all_posts = []
    page = 1
    while True:
        data = wp_api_get(f"/posts?status=publish&per_page=100&page={page}&context=edit")
        if not isinstance(data, list) or len(data) == 0:
            break
        all_posts.extend(data)
        print(f"  Fetched page {page}: {len(data)} posts (total: {len(all_posts)})")
        if len(data) < 100:
            break
        page += 1
    return all_posts


# ── HTML / Content Utilities ──────────────────────────────────────────────

def strip_html(html_str):
    """Strip HTML tags and decode entities."""
    if not html_str:
        return ""
    text = re.sub(r'<[^>]+>', ' ', html_str)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_rendered(post, field):
    """Get rendered content from a post field."""
    val = post.get(field, "")
    if isinstance(val, dict):
        return val.get("rendered", "")
    return val or ""


# ── Cluster Classification ────────────────────────────────────────────────

def classify_post(title):
    """Classify a post into a content cluster based on title keywords."""
    t = title.lower()

    # Dog Toys
    if any(kw in t for kw in ["dog toy", "tug", "fetch", "chew toy"]):
        return "Dog Toys"
    if "enrichment" in t and "dog" in t:
        return "Dog Toys"
    if "mental stimulation" in t and "dog" in t:
        return "Dog Toys"

    # Dog Food
    if any(kw in t for kw in ["dog food", "puppy food", "dry food", "dry vs wet"]):
        return "Dog Food"

    # Dog Beds
    if "dog bed" in t:
        return "Dog Beds"

    # Dog Harnesses
    if "harness" in t and "cat" not in t:
        return "Dog Harnesses"

    # Dog Health
    if any(kw in t for kw in ["flea", "joint supplement", "dental care", "dog health"]):
        return "Dog Health"

    # Dog Care
    if any(kw in t for kw in ["grooming", "seasonal dog", "first-time dog",
                               "dental health", "measure your dog"]):
        return "Dog Care"

    # Cat Toys
    if any(kw in t for kw in ["cat toy", "cat play"]):
        return "Cat Toys"

    # Puppy Care
    if any(kw in t for kw in ["puppy", "socialisation"]):
        return "Puppy Care"

    # Dog Supplies
    if any(kw in t for kw in ["collar", "lead", "bowl", "training treat",
                               "interactive dog", "indestructible"]):
        return "Dog Supplies"

    # Cat Supplies
    if "cat " in t and "dog" not in t:
        return "Cat Supplies"

    # Educational
    if any(kw in t for kw in ["terminology", "glossary", "explained",
                               "enrichment", "behaviour"]):
        return "Educational"

    # Pet Care General
    if any(kw in t for kw in ["pet ", "multi-pet", "first aid", "seasonal pet"]):
        return "Pet Care General"

    # Fallback
    if "dog" in t:
        return "Dog Care"
    if "cat" in t:
        return "Cat Supplies"
    if "pet" in t:
        return "Pet Care General"

    return "Uncategorized"


# ── 7 Scoring Dimensions (aligned to priority order) ─────────────────────

def score_references(content_raw, content_text):
    """D1: Reference Score — count of UK authority mentions/links."""
    score = 0
    content_lower = (content_raw + " " + content_text).lower()

    # Count authority source mentions
    authority_count = 0
    for src in AUTHORITY_SOURCES:
        mentions = len(re.findall(re.escape(src), content_lower))
        authority_count += mentions

    # Score based on number of unique authorities referenced
    unique_auths = sum(1 for src in AUTHORITY_SOURCES if src in content_lower)
    score += min(unique_auths * 12, 48)

    # Score based on total mention count
    score += min(authority_count * 4, 20)

    # External links to authority domains
    auth_links = len(re.findall(
        r'href=["\'][^"\']*(?:rspca\.org|bva\.co\.uk|pdsa\.org|gov\.uk|battersea\.org|'
        r'bluecross\.org|fediaf\.org|pfma\.org|thekennelclub\.org|cats\.org)',
        content_raw, re.IGNORECASE
    ))
    score += min(auth_links * 8, 32)

    return min(score, 100)


def score_comparisons(content_raw, content_text):
    """D2: Comparison Score — tables, vs-content, pro/con sections."""
    score = 0

    # Tables
    tables = len(re.findall(r'wp-block-table|<table', content_raw))
    score += min(tables * 15, 30)

    # "vs" comparisons
    vs_count = len(re.findall(r'(?i)\bvs\.?\b', content_text))
    score += min(vs_count * 5, 25)

    # Pro/Con sections
    procon = len(re.findall(
        r'(?i)(pros?\s*(and|&)\s*cons?|advantages?\s*(and|&)\s*disadvantages?)',
        content_text
    ))
    score += min(procon * 15, 30)

    # Comparison headings
    comp_headings = len(re.findall(
        r'(?i)<h[2-4][^>]*>[^<]*(compar|vs\.|versus|differ)[^<]*</h[2-4]>',
        content_raw
    ))
    score += min(comp_headings * 10, 15)

    return min(score, 100)


def score_practical(content_raw, content_text):
    """D3: Practical Score — checklists, step-by-step, tips, troubleshooting, examples."""
    score = 0

    # Checklists / bullet lists
    list_items = len(re.findall(r'<li[^>]*>', content_raw))
    score += min(list_items * 2, 25)

    # Step-by-step / numbered
    steps = len(re.findall(r'(?i)(step\s+\d|step-by-step|how\s+to)', content_text))
    score += min(steps * 8, 25)

    # Tips
    tips = len(re.findall(r'(?i)(top\s+tip|pro\s+tip|quick\s+tip|tip\s*:|\btips?\b)', content_text))
    score += min(tips * 5, 20)

    # Troubleshooting
    troubleshoot = len(re.findall(
        r'(?i)(troubleshoot|common\s+problem|common\s+mistake|what\s+to\s+do\s+if|warning\s+sign)',
        content_text
    ))
    score += min(troubleshoot * 8, 15)

    # Examples
    examples = len(re.findall(r'(?i)(for\s+example|e\.g\.|such\s+as|example\s*:)', content_text))
    score += min(examples * 5, 15)

    return min(score, 100)


def score_citations(content_raw, content_text):
    """D4: Citation Score — extractability, trust, comparison, glossary, educational clarity."""
    score = 0

    # Quick answer / summary blocks (extractability)
    quick = len(re.findall(
        r'(?i)(quick\s+answer|tl;?\s*dr|in\s+short|at\s+a\s+glance|summary|key\s+takeaway)',
        content_text
    ))
    score += min(quick * 10, 25)

    # "According to" / citation phrases
    citations = len(re.findall(
        r'(?i)(according\s+to|studies?\s+(show|suggest|indicate|found)|research\s+(shows?|suggests?))',
        content_text
    ))
    score += min(citations * 6, 25)

    # Source/reference attributions
    sources = len(re.findall(r'(?i)(source[sd]?\s*:|reference[sd]?\s*:|cited\s+from)', content_text))
    score += min(sources * 10, 20)

    # Clear definitions (bold-dash patterns)
    bold_defs = len(re.findall(r'<strong>[^<]+</strong>\s*[–—\-]\s*\w', content_raw))
    score += min(bold_defs * 4, 15)

    # FAQ schema / structured Q&A
    faq = len(re.findall(r'(?i)(faq|frequently\s+asked)', content_raw))
    score += min(faq * 8, 15)

    return min(score, 100)


def score_trust(content_raw, content_text):
    """D5: Trust Score — editorial standards, methodology, corrections, AI transparency, disclosure."""
    score = 0

    trust_signals = [
        (r'(?i)editorial\s+standards?', 10),
        (r'(?i)methodology', 8),
        (r'(?i)fact[\s-]?check', 10),
        (r'(?i)reviewed\s+by', 8),
        (r'(?i)veterinar', 6),
        (r'(?i)expert[\s-]?reviewed', 10),
        (r'(?i)evidence[\s-]?based', 8),
        (r'(?i)peer[\s-]?reviewed', 8),
        (r'(?i)disclaimer', 6),
        (r'(?i)last\s+updated', 5),
        (r'(?i)written\s+by', 5),
        (r'(?i)certified', 6),
        (r'(?i)qualified', 5),
        (r'(?i)correction|erratum', 8),
        (r'(?i)ai[\s-]?(generated|assisted|written)', 6),
        (r'(?i)transparency', 6),
        (r'(?i)disclosure', 6),
    ]

    for pattern, pts in trust_signals:
        matches = len(re.findall(pattern, content_text))
        if matches > 0:
            score += min(matches * pts, pts + 2)

    return min(score, 100)


def score_semantic(content_raw, content_text):
    """D6: Semantic Score — glossary blocks, inline definitions, terminology depth."""
    score = 0

    # Key Terms / Glossary blocks
    key_terms = len(re.findall(r'(?i)(key\s+terms?|glossary|definitions?)\s*[:\-]', content_raw))
    score += min(key_terms * 20, 40)

    # Bold-dash definitions
    bold_dash = len(re.findall(r'<strong>[^<]+</strong>\s*[–—\-]\s*\w', content_raw))
    score += min(bold_dash * 5, 30)

    # Definition list items
    dl_items = len(re.findall(r'<dt[^>]*>', content_raw))
    score += min(dl_items * 5, 15)

    # Inline definitions (parenthetical explanations)
    inline_defs = len(re.findall(r'\([^)]{10,80}(?:meaning|i\.e\.|also\s+known|refers\s+to)[^)]*\)', content_text))
    score += min(inline_defs * 8, 15)

    return min(score, 100)


def score_flow(content_raw, all_posts_slugs):
    """D7: Flow Score — outbound internal links, cross-cluster potential."""
    score = 0

    # Count internal links to pethubonline.com
    internal_links = re.findall(
        r'href=["\'][^"\']*pethubonline\.com[^"\']*["\']',
        content_raw, re.IGNORECASE
    )
    outbound_internal = len(internal_links)
    score += min(outbound_internal * 8, 40)

    # Check if linking to other posts by slug
    linked_slugs = 0
    for slug in all_posts_slugs:
        if slug and len(slug) > 3 and slug in content_raw.lower():
            linked_slugs += 1
    score += min(linked_slugs * 6, 30)

    # Cross-reference / "related posts" / "see also" signals
    cross_refs = len(re.findall(
        r'(?i)(related\s+(?:posts?|articles?|guides?)|see\s+also|you\s+might\s+also|read\s+more)',
        content_raw
    ))
    score += min(cross_refs * 10, 30)

    return min(score, 100)


# ── Action Definitions ────────────────────────────────────────────────────

# Each action: (name, dimension, base_effort, priority_weight)
# Priority weights from client directive (1=highest priority)
ACTION_DEFINITIONS = [
    {
        "name": "Add external references (UK authorities)",
        "dimension": "References",
        "base_effort": 1,
        "priority_weight": 7,  # Highest priority = highest weight
        "score_fn_idx": 0,
    },
    {
        "name": "Add comparison table",
        "dimension": "Comparisons",
        "base_effort": 2,
        "priority_weight": 6,
        "score_fn_idx": 1,
    },
    {
        "name": "Add checklist/troubleshooting guide",
        "dimension": "Practical",
        "base_effort": 2,
        "priority_weight": 5,
        "score_fn_idx": 2,
    },
    {
        "name": "Add summary/at-a-glance block",
        "dimension": "Citations",
        "base_effort": 1,
        "priority_weight": 4,
        "score_fn_idx": 3,
    },
    {
        "name": "Add trust editorial block",
        "dimension": "Trust",
        "base_effort": 1,
        "priority_weight": 3,
        "score_fn_idx": 4,
    },
    {
        "name": "Expand glossary definitions",
        "dimension": "Semantic",
        "base_effort": 1,
        "priority_weight": 2,
        "score_fn_idx": 5,
    },
    {
        "name": "Add cross-cluster links",
        "dimension": "Flow",
        "base_effort": 1,
        "priority_weight": 1,
        "score_fn_idx": 6,
    },
]


def calculate_impact(current_score, dimension_priority_weight):
    """
    Calculate estimated impact of an improvement action.
    Lower current scores = higher impact potential.
    Higher priority weight = more important dimension.
    """
    # Gap from perfect (0-100 scale)
    gap = 100 - current_score

    # Base impact: proportional to the gap
    if gap >= 80:
        base_impact = 9
    elif gap >= 60:
        base_impact = 8
    elif gap >= 40:
        base_impact = 6
    elif gap >= 20:
        base_impact = 4
    else:
        base_impact = 2

    # Weight by dimension priority (1-7 scale -> multiplier 0.7-1.3)
    priority_multiplier = 0.7 + (dimension_priority_weight / 7.0) * 0.6

    impact = min(round(base_impact * priority_multiplier, 1), 10)
    return impact


def calculate_estimated_gain(current_score, impact):
    """Estimate how many points the dimension score would increase."""
    gap = 100 - current_score
    # Gain is proportional to impact and available headroom
    gain = min(round(gap * (impact / 10.0) * 0.4), gap)
    return max(gain, 1)


def determine_priority_tier(roi_score):
    """Classify ROI into priority tiers."""
    if roi_score >= 7:
        return "P0-Critical"
    elif roi_score >= 5:
        return "P1-High"
    elif roi_score >= 3:
        return "P2-Medium"
    else:
        return "P3-Low"


# ── Main Engine ───────────────────────────────────────────────────────────

def main():
    print("=" * 80)
    print("10AE-H: MOMENTUM PRIORITIZATION ENGINE")
    print(f"pethubonline.com | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # ── Step 1: Fetch all posts ───────────────────────────────────────────
    print("\n[1/5] Fetching all published posts...")
    posts = fetch_all_posts()
    if not posts:
        print("  FATAL: No posts fetched. Aborting.")
        sys.exit(1)
    print(f"  Total posts fetched: {len(posts)}")

    # Build slug list for flow scoring
    all_slugs = [p.get("slug", "") for p in posts]

    # ── Step 2: Score every post on all 7 dimensions ──────────────────────
    print("\n[2/5] Scoring all posts on 7 dimensions...")

    scored_posts = []
    for i, post in enumerate(posts):
        pid = post.get("id", 0)
        title_raw = get_rendered(post, "title")
        title = strip_html(title_raw)
        content_raw = get_rendered(post, "content")
        content_text = strip_html(content_raw)
        cluster = classify_post(title)

        scores = [
            score_references(content_raw, content_text),    # D0: References
            score_comparisons(content_raw, content_text),    # D1: Comparisons
            score_practical(content_raw, content_text),      # D2: Practical
            score_citations(content_raw, content_text),      # D3: Citations
            score_trust(content_raw, content_text),          # D4: Trust
            score_semantic(content_raw, content_text),       # D5: Semantic
            score_flow(content_raw, all_slugs),              # D6: Flow
        ]

        scored_posts.append({
            "post_id": pid,
            "title": title,
            "cluster": cluster,
            "scores": scores,
            "avg_score": round(sum(scores) / len(scores), 1),
        })

        if (i + 1) % 25 == 0:
            print(f"    Scored {i+1}/{len(posts)} posts...")

    print(f"  Scoring complete: {len(scored_posts)} posts scored")

    # ── Step 3: Generate all possible actions & rank by ROI ───────────────
    print("\n[3/5] Generating improvement actions & calculating ROI...")

    all_actions = []
    for sp in scored_posts:
        for action_def in ACTION_DEFINITIONS:
            idx = action_def["score_fn_idx"]
            current_score = sp["scores"][idx]
            priority_weight = action_def["priority_weight"]
            effort = action_def["base_effort"]

            impact = calculate_impact(current_score, priority_weight)
            estimated_gain = calculate_estimated_gain(current_score, impact)

            # ROI = impact / effort, boosted by priority weight
            roi = round((impact / effort) * (1 + priority_weight * 0.05), 2)

            all_actions.append({
                "post_id": sp["post_id"],
                "title": sp["title"],
                "cluster": sp["cluster"],
                "action": action_def["name"],
                "dimension": action_def["dimension"],
                "current_score": current_score,
                "estimated_gain": estimated_gain,
                "effort": effort,
                "impact": impact,
                "roi_score": roi,
                "priority_tier": determine_priority_tier(roi),
            })

    # Sort by ROI descending, then by priority weight descending
    dimension_priority = {d["dimension"]: d["priority_weight"] for d in ACTION_DEFINITIONS}
    all_actions.sort(key=lambda x: (
        -x["roi_score"],
        -dimension_priority.get(x["dimension"], 0),
        x["current_score"]
    ))

    # Assign ranks
    for rank, action in enumerate(all_actions, 1):
        action["rank"] = rank

    print(f"  Generated {len(all_actions)} improvement actions")

    # ── Step 4: Write output CSVs ─────────────────────────────────────────
    print("\n[4/5] Writing output CSVs...")

    # CSV 1: Momentum_Priority_Queue.csv
    csv1_path = os.path.join(OUTPUT_DIR, "Momentum_Priority_Queue.csv")
    with open(csv1_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "rank", "post_id", "title", "cluster", "action", "dimension",
            "current_score", "estimated_gain", "effort", "roi_score", "priority_tier"
        ])
        for a in all_actions:
            writer.writerow([
                a["rank"], a["post_id"], a["title"], a["cluster"],
                a["action"], a["dimension"], a["current_score"],
                a["estimated_gain"], a["effort"], a["roi_score"],
                a["priority_tier"]
            ])
    print(f"  [OK] {csv1_path}")
    print(f"       {len(all_actions)} rows written")

    # CSV 2: ROI_Rankings_By_Cluster.csv
    csv2_path = os.path.join(OUTPUT_DIR, "ROI_Rankings_By_Cluster.csv")
    cluster_stats = defaultdict(lambda: {
        "actions": [], "roi_sum": 0, "gain_sum": 0, "count": 0, "posts": set()
    })
    for a in all_actions:
        cl = a["cluster"]
        cluster_stats[cl]["actions"].append(a)
        cluster_stats[cl]["roi_sum"] += a["roi_score"]
        cluster_stats[cl]["gain_sum"] += a["estimated_gain"]
        cluster_stats[cl]["count"] += 1
        cluster_stats[cl]["posts"].add(a["post_id"])

    cluster_rows = []
    for cluster, stats in cluster_stats.items():
        # Find the top action for this cluster
        top_action = max(stats["actions"], key=lambda x: x["roi_score"])
        avg_roi = round(stats["roi_sum"] / stats["count"], 2) if stats["count"] > 0 else 0
        cluster_rows.append({
            "cluster": cluster,
            "top_action": top_action["action"],
            "avg_roi": avg_roi,
            "total_improvement_potential": stats["gain_sum"],
            "posts_affected": len(stats["posts"]),
            "priority": determine_priority_tier(avg_roi),
        })

    cluster_rows.sort(key=lambda x: -x["avg_roi"])

    with open(csv2_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "cluster", "top_action", "avg_roi", "total_improvement_potential",
            "posts_affected", "priority"
        ])
        for r in cluster_rows:
            writer.writerow([
                r["cluster"], r["top_action"], r["avg_roi"],
                r["total_improvement_potential"], r["posts_affected"],
                r["priority"]
            ])
    print(f"  [OK] {csv2_path}")
    print(f"       {len(cluster_rows)} clusters ranked")

    # CSV 3: Acceleration_Roadmap.csv
    csv3_path = os.path.join(OUTPUT_DIR, "Acceleration_Roadmap.csv")

    # Group actions by dimension for phased roadmap
    dimension_groups = defaultdict(list)
    for a in all_actions:
        dimension_groups[a["dimension"]].append(a)

    # Build roadmap phases based on priority order
    phase_order = [
        ("References", "Phase 1: Authority References", "1-2 days"),
        ("Comparisons", "Phase 2: Comparison Content", "2-3 days"),
        ("Practical", "Phase 3: Practical Guides", "2-3 days"),
        ("Citations", "Phase 4: Citation Confidence", "1-2 days"),
        ("Trust", "Phase 5: Trust Signals", "1 day"),
        ("Semantic", "Phase 6: Semantic Enrichment", "1 day"),
        ("Flow", "Phase 7: Cross-Cluster Flow", "1 day"),
    ]

    roadmap_rows = []
    for dimension, phase_name, timeline in phase_order:
        actions_in_dim = dimension_groups.get(dimension, [])
        if not actions_in_dim:
            continue

        # Split into effort tiers
        effort_1 = [a for a in actions_in_dim if a["effort"] == 1]
        effort_2 = [a for a in actions_in_dim if a["effort"] == 2]
        effort_3 = [a for a in actions_in_dim if a["effort"] == 3]

        posts_targeted = len(set(a["post_id"] for a in actions_in_dim))
        total_gain = sum(a["estimated_gain"] for a in actions_in_dim)

        # Calculate average effort
        if actions_in_dim:
            avg_effort = sum(a["effort"] for a in actions_in_dim) / len(actions_in_dim)
            if avg_effort <= 1.3:
                effort_label = "Low (quick wins)"
            elif avg_effort <= 2.0:
                effort_label = "Medium (focused work)"
            else:
                effort_label = "High (deep rewrite)"
        else:
            effort_label = "N/A"

        roadmap_rows.append({
            "phase": phase_name,
            "action_category": dimension,
            "posts_targeted": posts_targeted,
            "estimated_total_gain": total_gain,
            "effort_level": effort_label,
            "timeline_suggestion": timeline,
        })

    with open(csv3_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "phase", "action_category", "posts_targeted",
            "estimated_total_gain", "effort_level", "timeline_suggestion"
        ])
        for r in roadmap_rows:
            writer.writerow([
                r["phase"], r["action_category"], r["posts_targeted"],
                r["estimated_total_gain"], r["effort_level"],
                r["timeline_suggestion"]
            ])
    print(f"  [OK] {csv3_path}")
    print(f"       {len(roadmap_rows)} phases defined")

    # ── Step 5: Print Summary ─────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("MOMENTUM PRIORITIZATION SUMMARY")
    print("=" * 80)

    # Overall stats
    all_scores = [sp["avg_score"] for sp in scored_posts]
    site_avg = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0
    print(f"\nSite-wide average quality score: {site_avg}/100")
    print(f"Total posts analyzed: {len(scored_posts)}")
    print(f"Total improvement actions ranked: {len(all_actions)}")

    # Dimension averages
    dim_names = ["References", "Comparisons", "Practical", "Citations", "Trust", "Semantic", "Flow"]
    print(f"\n{'Dimension':<20} {'Avg Score':>10} {'Gap from 100':>14}")
    print("-" * 46)
    for idx, dim in enumerate(dim_names):
        dim_scores = [sp["scores"][idx] for sp in scored_posts]
        avg = round(sum(dim_scores) / len(dim_scores), 1)
        gap = round(100 - avg, 1)
        print(f"{dim:<20} {avg:>10.1f} {gap:>14.1f}")

    # Top 20 highest-ROI actions
    print(f"\n{'─' * 80}")
    print("TOP 20 HIGHEST-ROI ACTIONS")
    print(f"{'─' * 80}")
    print(f"{'#':>3} {'ROI':>6} {'Tier':<13} {'Dimension':<13} {'Score':>5} {'Gain':>5} {'Post Title'}")
    print(f"{'':>3} {'':>6} {'':>13} {'':>13} {'':>5} {'':>5} {'Action'}")
    print("-" * 80)

    for a in all_actions[:20]:
        title_short = a["title"][:42] + "..." if len(a["title"]) > 45 else a["title"]
        print(f"{a['rank']:>3} {a['roi_score']:>6.2f} {a['priority_tier']:<13} "
              f"{a['dimension']:<13} {a['current_score']:>5} {a['estimated_gain']:>5} {title_short}")
        action_short = a["action"][:70]
        print(f"{'':>3} {'':>6} {'':>13} {'':>13} {'':>5} {'':>5} -> {action_short}")

    # Per-cluster priorities
    print(f"\n{'─' * 80}")
    print("PER-CLUSTER PRIORITIES")
    print(f"{'─' * 80}")
    print(f"{'Cluster':<22} {'Avg ROI':>8} {'Posts':>6} {'Total Gain':>11} {'Top Action'}")
    print("-" * 80)

    for r in cluster_rows:
        cluster_short = r["cluster"][:20]
        action_short = r["top_action"][:35]
        print(f"{cluster_short:<22} {r['avg_roi']:>8.2f} {r['posts_affected']:>6} "
              f"{r['total_improvement_potential']:>11} {action_short}")

    # Execution roadmap summary
    print(f"\n{'─' * 80}")
    print("RECOMMENDED EXECUTION ORDER")
    print(f"{'─' * 80}")

    for r in roadmap_rows:
        print(f"\n  {r['phase']}")
        print(f"    Category:  {r['action_category']}")
        print(f"    Posts:     {r['posts_targeted']}")
        print(f"    Est Gain:  {r['estimated_total_gain']} points total")
        print(f"    Effort:    {r['effort_level']}")
        print(f"    Timeline:  {r['timeline_suggestion']}")

    # P0 action count
    p0_count = sum(1 for a in all_actions if a["priority_tier"] == "P0-Critical")
    p1_count = sum(1 for a in all_actions if a["priority_tier"] == "P1-High")
    p2_count = sum(1 for a in all_actions if a["priority_tier"] == "P2-Medium")
    p3_count = sum(1 for a in all_actions if a["priority_tier"] == "P3-Low")

    print(f"\n{'─' * 80}")
    print("PRIORITY TIER BREAKDOWN")
    print(f"{'─' * 80}")
    print(f"  P0-Critical:  {p0_count:>4} actions (ROI >= 7.0)")
    print(f"  P1-High:      {p1_count:>4} actions (ROI 5.0-6.9)")
    print(f"  P2-Medium:    {p2_count:>4} actions (ROI 3.0-4.9)")
    print(f"  P3-Low:       {p3_count:>4} actions (ROI < 3.0)")
    total_gain_all = sum(a["estimated_gain"] for a in all_actions)
    print(f"\n  Total improvement potential: {total_gain_all} quality points across all actions")

    print(f"\n{'=' * 80}")
    print(f"Engine complete. {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Output: {OUTPUT_DIR}/")
    print(f"  1. Momentum_Priority_Queue.csv    ({len(all_actions)} actions ranked)")
    print(f"  2. ROI_Rankings_By_Cluster.csv     ({len(cluster_rows)} clusters)")
    print(f"  3. Acceleration_Roadmap.csv        ({len(roadmap_rows)} phases)")
    print("=" * 80)


if __name__ == "__main__":
    main()
