#!/usr/bin/env python3
"""
Phase 11P — Revenue Readiness Analysis Engine for PetHub Online
===============================================================
ANALYSIS ONLY. Does NOT insert affiliate links, add Product/Review/Offer
schema, activate any monetization, or modify any WordPress content.

Assesses every published post across six dimensions and classifies into
revenue-readiness tiers. Outputs four CSV reports plus a terminal summary.
"""

import csv
import json
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from statistics import mean

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_API = "https://pethubonline.com/wp-json/wp/v2/posts"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase11_data"
SCORE_DIR = "/var/lib/freelancer/projects/40416335/phase10cc_data"

# Blocked clusters — never flag as monetization-ready
BLOCKED_CLUSTERS = {"Dog Food", "Dog Harnesses"}

# Thresholds for readiness tiers
READY_THRESHOLD = 75          # overall readiness >= 75
NEAR_READY_THRESHOLD = 55     # overall readiness >= 55
DEVELOPING_THRESHOLD = 35     # overall readiness >= 35
# Below DEVELOPING_THRESHOLD → NOT-APPLICABLE

COMMERCIAL_HIGH = 70          # commercial intent considered "high"
COMMERCIAL_MED = 40           # commercial intent considered "medium"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def wp_curl(url):
    """Fetch from WP REST API using subprocess curl."""
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"  [WARN] curl failed for {url}: {result.stderr[:200]}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  [WARN] JSON decode failed for {url}")
        return None


def load_csv_scores(filepath, id_col="id", score_cols=None):
    """Load a scoring CSV into a dict keyed by post id."""
    data = {}
    if not os.path.exists(filepath):
        print(f"  [WARN] Missing: {filepath}")
        return data
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row.get(id_col, "").strip()
            if not pid:
                continue
            entry = {}
            if score_cols:
                for col in score_cols:
                    val = row.get(col, "0").strip()
                    try:
                        entry[col] = float(val)
                    except ValueError:
                        entry[col] = 0.0
            else:
                for k, v in row.items():
                    entry[k] = v.strip() if isinstance(v, str) else v
            data[pid] = entry
    return data


def parse_health_value(cell):
    """Extract numeric value from cells like 'STRONG (92.8)'."""
    m = re.search(r"\(([\d.]+)\)", str(cell))
    return float(m.group(1)) if m else 0.0


def load_cluster_health():
    """Load cluster_health_matrix.csv."""
    path = os.path.join(DATA_DIR, "cluster_health_matrix.csv")
    data = {}
    if not os.path.exists(path):
        return data
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cluster = row.get("cluster", "").strip()
            if not cluster:
                continue
            data[cluster] = {
                "citation_health": parse_health_value(row.get("citation_health", "")),
                "moat_health": parse_health_value(row.get("moat_health", "")),
                "ai_health": parse_health_value(row.get("ai_health", "")),
                "semantic_health": parse_health_value(row.get("semantic_health", "")),
                "comparison_health": parse_health_value(row.get("comparison_health", "")),
                "trust_health": parse_health_value(row.get("trust_health", "")),
                "overall_health": row.get("overall_health", "").strip(),
            }
    return data


def load_ownership():
    """Load topic_ownership_status.csv."""
    path = os.path.join(DATA_DIR, "topic_ownership_status.csv")
    data = {}
    if not os.path.exists(path):
        return data
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cluster = row.get("cluster", "").strip()
            if not cluster:
                continue
            data[cluster] = {
                "dominance_score": float(row.get("dominance_score", 0)),
                "ownership_status": row.get("ownership_status", "").strip(),
                "post_count": int(row.get("post_count", 0)),
                "avg_citation": float(row.get("avg_citation", 0)),
                "avg_moat": float(row.get("avg_moat", 0)),
                "avg_ai_pref": float(row.get("avg_ai_pref", 0)),
                "weakest_dimension": row.get("weakest_dimension", "").strip(),
            }
    return data


# ---------------------------------------------------------------------------
# Commercial intent scoring
# ---------------------------------------------------------------------------

BUYING_KEYWORDS = [
    "best", "top", "review", "comparison", "vs", "versus", "guide",
    "buy", "buying", "choose", "choosing", "recommended", "recommendation",
    "worth", "price", "cost", "budget", "affordable", "premium",
    "uk", "2026", "2025"
]

PRODUCT_CATEGORY_KEYWORDS = [
    "bed", "beds", "toy", "toys", "food", "treats", "shampoo", "brush",
    "clipper", "clippers", "harness", "harnesses", "collar", "collars",
    "leash", "lead", "crate", "carrier", "feeder", "bowl", "tag", "tags",
    "supplies", "grooming", "nail", "catnip"
]

COMPARISON_KEYWORDS = [
    "vs", "versus", "compared", "comparison", "difference", "differences",
    "better", "which", "types", "kinds"
]

EDUCATIONAL_KEYWORDS = [
    "how to", "why", "what is", "when to", "socialisation", "training",
    "behaviour", "behavior", "health", "tips", "guide", "first-time",
    "timeline", "stages", "signs", "symptoms"
]


def compute_commercial_intent(title, content_html, cluster):
    """Score 0-100 how commercially oriented a post is."""
    title_lower = title.lower()
    content_lower = (content_html or "").lower()

    score = 0.0

    # Title-level signals (up to 50 points)
    buying_hits = sum(1 for kw in BUYING_KEYWORDS if kw in title_lower)
    score += min(buying_hits * 6, 30)

    product_hits = sum(1 for kw in PRODUCT_CATEGORY_KEYWORDS if kw in title_lower)
    score += min(product_hits * 8, 16)

    # "Best X UK (2026)" pattern — very strong buying intent
    if re.search(r"best\s+.+uk.*20\d{2}", title_lower):
        score += 20
    elif re.search(r"best\s+", title_lower):
        score += 10

    # Comparison signals (up to 15 points)
    comp_hits = sum(1 for kw in COMPARISON_KEYWORDS if kw in title_lower)
    score += min(comp_hits * 5, 15)

    # Content-level signals (up to 25 points)
    # Product mentions in body
    product_body_hits = sum(1 for kw in PRODUCT_CATEGORY_KEYWORDS if kw in content_lower)
    score += min(product_body_hits * 0.3, 10)

    # Comparison tables (structured buying guidance)
    table_count = content_lower.count("<table")
    score += min(table_count * 3, 9)

    # FAQ sections (answer purchase questions)
    if "faq" in content_lower or "frequently asked" in content_lower:
        score += 3

    # Pros/cons pattern
    if "pros" in content_lower and "cons" in content_lower:
        score += 3

    # Cluster-level boost for product clusters
    product_clusters = {
        "Cat Supplies": 15, "Dog Care": 10, "Cat Toys": 12,
        "Dog Toys": 12, "Dog Beds": 14, "Training Supplies": 10,
        "Dog Supplies": 12, "Dog Harnesses": 14, "Dog Food": 10,
        "Indoor Cats": 5
    }
    score += product_clusters.get(cluster, 0)

    # Educational dampener — pure educational content scores lower
    edu_hits = sum(1 for kw in EDUCATIONAL_KEYWORDS if kw in title_lower)
    if edu_hits >= 2 and product_hits == 0:
        score *= 0.5

    return min(round(score, 1), 100)


# ---------------------------------------------------------------------------
# Content maturity scoring
# ---------------------------------------------------------------------------

def compute_content_maturity(post_id, comparison_data, practical_data, trust_data):
    """Score 0-100 based on enrichment completeness."""
    scores = []

    # Comparison coverage
    comp = comparison_data.get(str(post_id), {})
    comp_score = comp.get("comparison_score", 0)
    if isinstance(comp_score, str):
        try:
            comp_score = float(comp_score)
        except ValueError:
            comp_score = 0
    scores.append(float(comp_score))

    # Practical guidance
    prac = practical_data.get(str(post_id), {})
    prac_score = prac.get("practical_score", 0)
    if isinstance(prac_score, str):
        try:
            prac_score = float(prac_score)
        except ValueError:
            prac_score = 0
    scores.append(float(prac_score))

    # Trust depth
    trust = trust_data.get(str(post_id), {})
    trust_score = trust.get("trust_score", 0)
    if isinstance(trust_score, str):
        try:
            trust_score = float(trust_score)
        except ValueError:
            trust_score = 0
    scores.append(float(trust_score))

    # Enrichment completeness bonuses
    has_practical = prac.get("has_practical_guide", "").lower() == "yes"
    has_decision = prac.get("has_decision_pathway", "").lower() == "yes"
    has_troubleshooting = prac.get("has_troubleshooting", "").lower() == "yes"

    enrichment_count = sum([has_practical, has_decision, has_troubleshooting])
    enrichment_bonus = enrichment_count * 2  # up to 6 points

    if scores:
        base = mean(scores)
    else:
        base = 50  # default for posts without scoring data

    return min(round(base + enrichment_bonus, 1), 100)


# ---------------------------------------------------------------------------
# Overall readiness + tier classification
# ---------------------------------------------------------------------------

def compute_overall_readiness(commercial_intent, citation_score, moat_score,
                               ownership_score, ai_readiness, content_maturity):
    """Weighted composite readiness score 0-100."""
    # Weights: commercial intent is key, but authority dimensions matter
    weights = {
        "commercial_intent": 0.30,
        "citation_score": 0.15,
        "moat_score": 0.15,
        "ownership_score": 0.10,
        "ai_readiness": 0.15,
        "content_maturity": 0.15,
    }
    raw = (
        commercial_intent * weights["commercial_intent"]
        + citation_score * weights["citation_score"]
        + moat_score * weights["moat_score"]
        + ownership_score * weights["ownership_score"]
        + ai_readiness * weights["ai_readiness"]
        + content_maturity * weights["content_maturity"]
    )
    return round(raw, 1)


def classify_tier(overall, commercial_intent, cluster):
    """Classify into readiness tier."""
    # Blocked clusters can never be READY
    if cluster in BLOCKED_CLUSTERS:
        if overall >= NEAR_READY_THRESHOLD:
            return "NEAR-READY (BLOCKED)"
        elif overall >= DEVELOPING_THRESHOLD:
            return "DEVELOPING"
        else:
            return "NOT-APPLICABLE"

    if overall >= READY_THRESHOLD and commercial_intent >= COMMERCIAL_HIGH:
        return "READY"
    elif overall >= NEAR_READY_THRESHOLD and commercial_intent >= COMMERCIAL_MED:
        return "NEAR-READY"
    elif overall >= DEVELOPING_THRESHOLD:
        return "DEVELOPING"
    else:
        return "NOT-APPLICABLE"


def determine_monetization_fit(title, commercial_intent, cluster, tier):
    """Suggest monetization type based on content characteristics."""
    title_lower = title.lower()

    if tier in ("NOT-APPLICABLE",):
        return "None (educational)"

    if cluster in BLOCKED_CLUSTERS:
        return "Blocked (pending evidence)"

    fits = []
    if re.search(r"best\s+.+uk", title_lower) or "review" in title_lower:
        fits.append("Affiliate")
    if "guide" in title_lower or "comparison" in title_lower:
        fits.append("Affiliate")
    if commercial_intent >= 60:
        fits.append("Sponsored")
    if commercial_intent >= 40:
        fits.append("Display Ads")

    # Deduplicate
    seen = set()
    unique_fits = []
    for f in fits:
        if f not in seen:
            seen.add(f)
            unique_fits.append(f)

    return "; ".join(unique_fits) if unique_fits else "Display Ads"


# ---------------------------------------------------------------------------
# Fetch all published posts
# ---------------------------------------------------------------------------

def fetch_all_posts():
    """Fetch all published posts from WordPress REST API."""
    all_posts = []
    page = 1
    while True:
        url = f"{WP_API}?per_page=100&page={page}&context=edit"
        print(f"  Fetching page {page}: {url}")
        data = wp_curl(url)
        if data is None or not isinstance(data, list) or len(data) == 0:
            break
        all_posts.extend(data)
        print(f"    Got {len(data)} posts (total so far: {len(all_posts)})")
        if len(data) < 100:
            break
        page += 1
        time.sleep(2)
    return all_posts


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("Phase 11P — Revenue Readiness Analysis Engine")
    print("ANALYSIS ONLY — No monetization activation")
    print("=" * 70)
    print()

    # ------------------------------------------------------------------
    # 1. Load scoring data
    # ------------------------------------------------------------------
    print("[1/6] Loading scoring data from Phase 10CC...")
    citation_data = load_csv_scores(
        os.path.join(SCORE_DIR, "Citation_Dominance_Report.csv"),
        score_cols=["citation_score"]
    )
    moat_data = load_csv_scores(
        os.path.join(SCORE_DIR, "Authority_Moat_Report.csv"),
        score_cols=["moat_score"]
    )
    ai_pref_data = load_csv_scores(
        os.path.join(SCORE_DIR, "AI_Answer_Preference.csv"),
        score_cols=["ai_preference_score"]
    )
    comparison_data = load_csv_scores(
        os.path.join(SCORE_DIR, "Comparison_Coverage.csv"),
        score_cols=["comparison_table_count", "comparison_score"]
    )
    practical_data = load_csv_scores(
        os.path.join(SCORE_DIR, "Practical_Guidance_Scores.csv"),
    )
    trust_data = load_csv_scores(
        os.path.join(SCORE_DIR, "Trust_Depth_Report.csv"),
        score_cols=["trust_blocks_count", "named_refs_count", "trust_score"]
    )

    print(f"  Citation scores: {len(citation_data)} posts")
    print(f"  Moat scores: {len(moat_data)} posts")
    print(f"  AI preference scores: {len(ai_pref_data)} posts")
    print(f"  Comparison coverage: {len(comparison_data)} posts")
    print(f"  Practical guidance: {len(practical_data)} posts")
    print(f"  Trust depth: {len(trust_data)} posts")
    print()

    # ------------------------------------------------------------------
    # 2. Load cluster-level data
    # ------------------------------------------------------------------
    print("[2/6] Loading cluster health & ownership data...")
    cluster_health = load_cluster_health()
    ownership_data = load_ownership()
    print(f"  Cluster health: {len(cluster_health)} clusters")
    print(f"  Ownership data: {len(ownership_data)} clusters")
    print()

    # ------------------------------------------------------------------
    # 3. Fetch all posts from WordPress
    # ------------------------------------------------------------------
    print("[3/6] Fetching published posts from WordPress REST API...")
    posts = fetch_all_posts()
    print(f"  Total posts fetched: {len(posts)}")
    print()

    if not posts:
        print("[ERROR] No posts fetched. Falling back to scoring data posts.")
        # Build a minimal post list from scoring data
        posts = []
        # Use citation data as the base since it has id, title, cluster
        cit_path = os.path.join(SCORE_DIR, "Citation_Dominance_Report.csv")
        with open(cit_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row.get("id", "").strip()
                if pid:
                    posts.append({
                        "id": int(pid),
                        "title": {"rendered": row.get("title", "")},
                        "content": {"rendered": ""},
                        "_cluster_override": row.get("cluster", "Uncategorized"),
                    })
        print(f"  Fallback posts from scoring data: {len(posts)}")
        print()

    # ------------------------------------------------------------------
    # 4. Build cluster map from scoring data (canonical source)
    # ------------------------------------------------------------------
    # The scoring CSVs have the authoritative cluster assignment
    cluster_map = {}  # post_id -> cluster
    cit_path = os.path.join(SCORE_DIR, "Citation_Dominance_Report.csv")
    if os.path.exists(cit_path):
        with open(cit_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row.get("id", "").strip()
                cluster = row.get("cluster", "Uncategorized").strip()
                if pid:
                    cluster_map[pid] = cluster

    # ------------------------------------------------------------------
    # 5. Analyze each post
    # ------------------------------------------------------------------
    print("[4/6] Analyzing revenue readiness per post...")
    post_results = []

    for post in posts:
        pid = str(post["id"])
        title_raw = post.get("title", {})
        if isinstance(title_raw, dict):
            title = title_raw.get("rendered", title_raw.get("raw", ""))
        else:
            title = str(title_raw)

        content_raw = post.get("content", {})
        if isinstance(content_raw, dict):
            content_html = content_raw.get("rendered", content_raw.get("raw", ""))
        else:
            content_html = str(content_raw)

        # Cluster from scoring data (preferred) or override
        cluster = cluster_map.get(pid, post.get("_cluster_override", "Uncategorized"))

        # Dimension scores
        citation_score = citation_data.get(pid, {}).get("citation_score", 0)
        moat_score = moat_data.get(pid, {}).get("moat_score", 0)
        ai_readiness = ai_pref_data.get(pid, {}).get("ai_preference_score", 0)

        # Ownership score: 100 if OWNED, 60 if CONTESTED, 0 otherwise
        own = ownership_data.get(cluster, {})
        own_status = own.get("ownership_status", "")
        if own_status == "OWNED":
            ownership_score = 100.0
        elif own_status == "CONTESTED":
            ownership_score = 60.0
        else:
            ownership_score = 30.0

        # Commercial intent
        commercial_intent = compute_commercial_intent(title, content_html, cluster)

        # Content maturity
        content_maturity = compute_content_maturity(pid, comparison_data, practical_data, trust_data)

        # Overall readiness
        overall = compute_overall_readiness(
            commercial_intent, citation_score, moat_score,
            ownership_score, ai_readiness, content_maturity
        )

        # Tier
        tier = classify_tier(overall, commercial_intent, cluster)

        # Monetization fit
        monetization_fit = determine_monetization_fit(title, commercial_intent, cluster, tier)

        post_results.append({
            "post_id": pid,
            "title": title,
            "cluster": cluster,
            "commercial_intent": commercial_intent,
            "citation_score": citation_score,
            "moat_score": moat_score,
            "ownership_score": ownership_score,
            "ai_readiness": ai_readiness,
            "content_maturity": content_maturity,
            "overall_readiness": overall,
            "readiness_tier": tier,
            "monetization_fit": monetization_fit,
        })

    print(f"  Analyzed {len(post_results)} posts")
    print()

    # ------------------------------------------------------------------
    # 6. Cluster-level aggregation
    # ------------------------------------------------------------------
    print("[5/6] Aggregating cluster-level readiness...")
    cluster_agg = defaultdict(lambda: {
        "posts": [],
        "readiness_scores": [],
        "commercial_intents": [],
        "tiers": defaultdict(int),
    })

    for pr in post_results:
        c = pr["cluster"]
        cluster_agg[c]["posts"].append(pr)
        cluster_agg[c]["readiness_scores"].append(pr["overall_readiness"])
        cluster_agg[c]["commercial_intents"].append(pr["commercial_intent"])
        cluster_agg[c]["tiers"][pr["readiness_tier"]] += 1

    cluster_results = []
    for cluster_name, agg in sorted(cluster_agg.items(), key=lambda x: -mean(x[1]["readiness_scores"])):
        posts_in_cluster = agg["posts"]
        avg_readiness = round(mean(agg["readiness_scores"]), 1)

        # Top commercial intent post
        top_ci = max(posts_in_cluster, key=lambda p: p["commercial_intent"])

        # Strongest and weakest dimensions (average across cluster)
        dim_avgs = {
            "commercial_intent": round(mean([p["commercial_intent"] for p in posts_in_cluster]), 1),
            "citation_score": round(mean([p["citation_score"] for p in posts_in_cluster]), 1),
            "moat_score": round(mean([p["moat_score"] for p in posts_in_cluster]), 1),
            "ownership_score": round(mean([p["ownership_score"] for p in posts_in_cluster]), 1),
            "ai_readiness": round(mean([p["ai_readiness"] for p in posts_in_cluster]), 1),
            "content_maturity": round(mean([p["content_maturity"] for p in posts_in_cluster]), 1),
        }
        strongest = max(dim_avgs, key=dim_avgs.get)
        weakest = min(dim_avgs, key=dim_avgs.get)

        # Count tiers — handle both exact and substring matches for blocked tiers
        ready_count = sum(1 for p in posts_in_cluster if p["readiness_tier"] == "READY")
        near_ready_count = sum(1 for p in posts_in_cluster if "NEAR-READY" in p["readiness_tier"])
        developing_count = sum(1 for p in posts_in_cluster if p["readiness_tier"] == "DEVELOPING")
        na_count = sum(1 for p in posts_in_cluster if p["readiness_tier"] == "NOT-APPLICABLE")

        cluster_results.append({
            "cluster": cluster_name,
            "post_count": len(posts_in_cluster),
            "avg_readiness": avg_readiness,
            "ready_count": ready_count,
            "near_ready_count": near_ready_count,
            "developing_count": developing_count,
            "not_applicable_count": na_count,
            "top_commercial_intent_post": f"{top_ci['title']} ({top_ci['commercial_intent']})",
            "strongest_dimension": f"{strongest} ({dim_avgs[strongest]})",
            "weakest_dimension": f"{weakest} ({dim_avgs[weakest]})",
        })

    print(f"  Aggregated {len(cluster_results)} clusters")
    print()

    # ------------------------------------------------------------------
    # 7. Revenue opportunity map
    # ------------------------------------------------------------------
    print("[6/6] Building revenue opportunity map...")
    opportunity_map = []

    for cr in cluster_results:
        cluster_name = cr["cluster"]
        is_blocked = cluster_name in BLOCKED_CLUSTERS

        # Determine opportunity type and description
        if is_blocked:
            opportunity_map.append({
                "cluster": cluster_name,
                "opportunity_type": "BLOCKED",
                "description": f"Commercial content blocked pending evidence build. {cr['post_count']} posts with avg readiness {cr['avg_readiness']}.",
                "readiness_score": cr["avg_readiness"],
                "blockers": "Evidence gap; authority evidence needed before commercial activation",
                "priority": "HOLD",
            })
            continue

        if cr["ready_count"] > 0:
            opportunity_map.append({
                "cluster": cluster_name,
                "opportunity_type": "Affiliate Revenue",
                "description": f"{cr['ready_count']} posts ready for affiliate monetization. Strong commercial intent with owned authority position.",
                "readiness_score": cr["avg_readiness"],
                "blockers": "None — awaiting activation approval",
                "priority": "HIGH",
            })

        if cr["near_ready_count"] > 0:
            weakest = cr["weakest_dimension"]
            opportunity_map.append({
                "cluster": cluster_name,
                "opportunity_type": "Near-Ready Upgrade",
                "description": f"{cr['near_ready_count']} posts approaching readiness. Weakest: {weakest}.",
                "readiness_score": cr["avg_readiness"],
                "blockers": f"Improve {weakest} to cross threshold",
                "priority": "MEDIUM",
            })

        if cr["ready_count"] >= 3:
            opportunity_map.append({
                "cluster": cluster_name,
                "opportunity_type": "Sponsored Content",
                "description": f"Cluster has {cr['ready_count']} ready posts — sufficient density for sponsored partnerships.",
                "readiness_score": cr["avg_readiness"],
                "blockers": "Requires brand partnership outreach",
                "priority": "MEDIUM",
            })

        if cr["post_count"] >= 5 and cr["avg_readiness"] >= 50:
            opportunity_map.append({
                "cluster": cluster_name,
                "opportunity_type": "Display Advertising",
                "description": f"{cr['post_count']} posts with {cr['avg_readiness']} avg readiness — viable for display ad placement.",
                "readiness_score": cr["avg_readiness"],
                "blockers": "Traffic volume threshold needed",
                "priority": "LOW",
            })

    print(f"  Identified {len(opportunity_map)} opportunities")
    print()

    # ------------------------------------------------------------------
    # 8. Write CSVs
    # ------------------------------------------------------------------
    print("Writing output CSVs...")

    # a) revenue_readiness_by_post.csv
    post_csv = os.path.join(DATA_DIR, "revenue_readiness_by_post.csv")
    with open(post_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "post_id", "title", "cluster", "commercial_intent", "citation_score",
            "moat_score", "ownership_score", "ai_readiness", "content_maturity",
            "overall_readiness", "readiness_tier", "monetization_fit"
        ])
        writer.writeheader()
        for pr in sorted(post_results, key=lambda x: -x["overall_readiness"]):
            writer.writerow(pr)
    print(f"  -> {post_csv}")

    # b) revenue_readiness_by_cluster.csv
    cluster_csv = os.path.join(DATA_DIR, "revenue_readiness_by_cluster.csv")
    with open(cluster_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "cluster", "post_count", "avg_readiness", "ready_count",
            "near_ready_count", "developing_count", "not_applicable_count",
            "top_commercial_intent_post", "strongest_dimension", "weakest_dimension"
        ])
        writer.writeheader()
        for cr in cluster_results:
            writer.writerow(cr)
    print(f"  -> {cluster_csv}")

    # c) revenue_opportunity_map.csv
    opp_csv = os.path.join(DATA_DIR, "revenue_opportunity_map.csv")
    with open(opp_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "cluster", "opportunity_type", "description", "readiness_score",
            "blockers", "priority"
        ])
        writer.writeheader()
        for opp in sorted(opportunity_map, key=lambda x: {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "HOLD": 3}.get(x["priority"], 4)):
            writer.writerow(opp)
    print(f"  -> {opp_csv}")

    # d) revenue_readiness_summary.csv
    summary_csv = os.path.join(DATA_DIR, "revenue_readiness_summary.csv")

    total_posts = len(post_results)
    ready_posts = sum(1 for p in post_results if p["readiness_tier"] == "READY")
    near_ready_posts = sum(1 for p in post_results if "NEAR-READY" in p["readiness_tier"])
    developing_posts = sum(1 for p in post_results if p["readiness_tier"] == "DEVELOPING")
    na_posts = sum(1 for p in post_results if p["readiness_tier"] == "NOT-APPLICABLE")
    blocked_posts = sum(1 for p in post_results if "BLOCKED" in p["readiness_tier"])

    avg_overall = round(mean([p["overall_readiness"] for p in post_results]), 1) if post_results else 0
    avg_commercial = round(mean([p["commercial_intent"] for p in post_results]), 1) if post_results else 0
    max_readiness = max([p["overall_readiness"] for p in post_results]) if post_results else 0
    min_readiness = min([p["overall_readiness"] for p in post_results]) if post_results else 0

    top_ready = sorted(post_results, key=lambda x: -x["overall_readiness"])[:5]
    top_ready_str = "; ".join([f"{p['title'][:50]} ({p['overall_readiness']})" for p in top_ready])

    top_cluster = cluster_results[0] if cluster_results else None
    top_cluster_str = f"{top_cluster['cluster']} ({top_cluster['avg_readiness']})" if top_cluster else "N/A"

    # Count high-priority opportunities
    high_opps = sum(1 for o in opportunity_map if o["priority"] == "HIGH")
    medium_opps = sum(1 for o in opportunity_map if o["priority"] == "MEDIUM")

    summary_rows = [
        ("total_posts_analyzed", total_posts),
        ("ready_tier_count", ready_posts),
        ("near_ready_tier_count", near_ready_posts),
        ("developing_tier_count", developing_posts),
        ("not_applicable_tier_count", na_posts),
        ("blocked_tier_count", blocked_posts),
        ("average_overall_readiness", avg_overall),
        ("average_commercial_intent", avg_commercial),
        ("max_readiness_score", max_readiness),
        ("min_readiness_score", min_readiness),
        ("total_clusters", len(cluster_results)),
        ("top_cluster", top_cluster_str),
        ("high_priority_opportunities", high_opps),
        ("medium_priority_opportunities", medium_opps),
        ("top_5_ready_posts", top_ready_str),
        ("blocked_clusters", "; ".join(BLOCKED_CLUSTERS)),
        ("analysis_date", time.strftime("%Y-%m-%d")),
        ("phase", "11P — Revenue Readiness Analysis ONLY"),
    ]

    with open(summary_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        for row in summary_rows:
            writer.writerow(row)
    print(f"  -> {summary_csv}")
    print()

    # ------------------------------------------------------------------
    # 9. Terminal summary
    # ------------------------------------------------------------------
    print("=" * 70)
    print("REVENUE READINESS SUMMARY — Phase 11P")
    print("=" * 70)
    print()
    print(f"  Total Posts Analyzed:    {total_posts}")
    print(f"  Average Readiness Score: {avg_overall}")
    print(f"  Average Commercial Intent: {avg_commercial}")
    print()
    print("  READINESS DISTRIBUTION:")
    print(f"    READY:          {ready_posts:>4} posts ({round(ready_posts/total_posts*100, 1) if total_posts else 0}%)")
    print(f"    NEAR-READY:     {near_ready_posts:>4} posts ({round(near_ready_posts/total_posts*100, 1) if total_posts else 0}%)")
    print(f"    DEVELOPING:     {developing_posts:>4} posts ({round(developing_posts/total_posts*100, 1) if total_posts else 0}%)")
    print(f"    NOT-APPLICABLE: {na_posts:>4} posts ({round(na_posts/total_posts*100, 1) if total_posts else 0}%)")
    if blocked_posts > 0:
        print(f"    BLOCKED:        {blocked_posts:>4} posts ({round(blocked_posts/total_posts*100, 1) if total_posts else 0}%)")
    print()

    print("  BLOCKED CLUSTERS (no monetization):")
    for bc in BLOCKED_CLUSTERS:
        bc_posts = [p for p in post_results if p["cluster"] == bc]
        if bc_posts:
            bc_avg = round(mean([p["overall_readiness"] for p in bc_posts]), 1)
            print(f"    - {bc}: {len(bc_posts)} posts, avg readiness {bc_avg} (HELD)")
        else:
            print(f"    - {bc}: 0 posts in analysis")
    print()

    print("  TOP 5 HIGHEST-READINESS POSTS:")
    for i, p in enumerate(top_ready, 1):
        blocked_tag = " [BLOCKED]" if p["cluster"] in BLOCKED_CLUSTERS else ""
        print(f"    {i}. [{p['readiness_tier']}] {p['title'][:60]}")
        print(f"       Readiness: {p['overall_readiness']} | Commercial: {p['commercial_intent']} | Cluster: {p['cluster']}{blocked_tag}")
    print()

    print("  CLUSTER READINESS RANKING:")
    for cr in cluster_results[:10]:
        blocked_tag = " [BLOCKED]" if cr["cluster"] in BLOCKED_CLUSTERS else ""
        print(f"    {cr['cluster']:25s} | Avg: {cr['avg_readiness']:5.1f} | Ready: {cr['ready_count']:2d} | Near: {cr['near_ready_count']:2d}{blocked_tag}")
    print()

    print("  HIGH-PRIORITY OPPORTUNITIES:")
    for opp in opportunity_map:
        if opp["priority"] == "HIGH":
            print(f"    [{opp['priority']}] {opp['cluster']}: {opp['opportunity_type']}")
            print(f"       {opp['description'][:80]}")
    print()

    if not any(o["priority"] == "HIGH" for o in opportunity_map):
        print("    (No high-priority opportunities yet)")
        print()

    print("  REVENUE PATH SUMMARY:")
    print(f"    - {ready_posts} posts could monetize today if activation approved")
    print(f"    - {near_ready_posts} posts are 1 dimension away from readiness")
    print(f"    - {blocked_posts} posts in blocked clusters (awaiting evidence)")
    print(f"    - {high_opps} high-priority cluster opportunities identified")
    print(f"    - {medium_opps} medium-priority cluster opportunities identified")
    print()
    print("  REMINDER: This is ANALYSIS ONLY. No monetization has been activated.")
    print("=" * 70)


if __name__ == "__main__":
    main()
