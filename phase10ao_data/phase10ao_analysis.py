#!/usr/bin/env python3
"""
Phase 10AO - Cluster Dominance Replication Analysis
READ-ONLY analysis of PetHub Online WordPress posts.
Profiles Dog Toys as reference cluster, compares all others, generates gap/replication CSVs.
"""

import subprocess
import json
import csv
import re
import time
import html
import os
from collections import defaultdict

# --- Config ---
WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ao_data"

# Clusters and their search queries
CLUSTERS = {
    "Dog Toys": ["dog toy"],
    "Dog Food": ["dog food"],
    "Dog Beds": ["dog bed"],
    "Puppy Care": ["puppy"],
    "Dog Health": ["dog health"],
    "Cat Supplies": ["cat supplies", "cat litter", "cat bed"],
    "Cat Toys": ["cat toy"],
    "Dog Grooming": ["dog grooming", "dog brush", "dog shampoo"],
    "Dog Harnesses": ["dog harness", "dog collar", "dog lead"],
    "Dog Training": ["dog training"],
}

REFERENCE_CLUSTER = "Dog Toys"

# Element importance weights for priority scoring
IMPORTANCE_WEIGHTS = {
    "faq": 10,
    "comparison_table": 9,
    "trust_footer": 9,
    "at_a_glance": 8,
    "key_takeaways": 8,
    "uk_authority_refs": 8,
    "how_we_evaluated": 7,
    "why_we_reference": 7,
    "common_mistakes": 6,
    "when_to_seek_help": 6,
    "beginner_recs": 6,
    "budget_premium": 5,
    "glossary": 5,
}

ELEMENTS = list(IMPORTANCE_WEIGHTS.keys())


def api_call(url):
    """Make a curl call to WP REST API and return parsed JSON."""
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        print(f"  [ERROR] curl failed: {result.stderr}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  [ERROR] JSON decode failed for {url[:80]}...")
        return None


def fetch_posts_for_search(query, per_page=50):
    """Fetch all published posts matching a search query, paginating."""
    all_posts = []
    page = 1
    while True:
        url = f"{WP_BASE}/posts?search={query.replace(' ', '+')}&status=publish&per_page={per_page}&page={page}&_fields=id,title,content,link"
        data = api_call(url)
        if data is None or not isinstance(data, list) or len(data) == 0:
            break
        all_posts.extend(data)
        if len(data) < per_page:
            break
        page += 1
        time.sleep(1)
    return all_posts


def strip_html(html_str):
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', ' ', html_str)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def count_internal_links(content_html):
    """Count links pointing to pethubonline.com."""
    links = re.findall(r'href=["\']([^"\']+)["\']', content_html, re.IGNORECASE)
    return sum(1 for l in links if 'pethubonline.com' in l)


def count_words(text):
    """Count words in plain text."""
    return len(text.split())


def analyze_post(post):
    """Analyze a single post for all content elements. Returns dict of booleans + metrics."""
    raw = post.get("content", {}).get("rendered", "")
    title_raw = post.get("title", {}).get("rendered", "")
    title = strip_html(title_raw)
    text = strip_html(raw)
    lower = raw.lower()
    text_lower = text.lower()

    result = {
        "id": post["id"],
        "title": title,
        "word_count": count_words(text),
        "internal_links": count_internal_links(raw),
    }

    # FAQ section - look for heading or schema FAQ markers
    result["faq"] = bool(
        re.search(r'(frequently\s+asked\s+questions|faq)', lower)
        or re.search(r'<h[2-4][^>]*>.*?(faq|frequently)', lower)
    )

    # Quick Answer / At a Glance
    result["at_a_glance"] = bool(
        re.search(r'(at\s+a\s+glance|quick\s+answer|the\s+quick\s+answer|our\s+quick\s+answer|bottom\s+line\s+up\s+front)', lower)
    )

    # Comparison table
    result["comparison_table"] = bool(
        re.search(r'<table', lower)
        or re.search(r'(comparison|compare|versus|vs\.)', lower)
        and re.search(r'(table|chart)', lower)
    )

    # Glossary terms/links
    result["glossary"] = bool(
        re.search(r'(glossary|key\s+terms|definitions|terminology)', lower)
    )

    # Trust footer
    result["trust_footer"] = bool(
        re.search(r'(trust|editorial\s+standards|editorial\s+policy|our\s+commitment|transparency)', lower)
        and re.search(r'(footer|bottom|policy|standard)', lower)
    ) or bool(
        re.search(r'(we\s+are\s+committed|our\s+promise|built\s+on\s+trust|trust\s+signal)', lower)
    ) or bool(
        re.search(r'(independently\s+researched|editorially\s+independent|no\s+sponsored|unbiased)', lower)
    )

    # UK authority references (RSPCA, PDSA, Kennel Club, Blue Cross, BVA, DEFRA, etc.)
    uk_refs = re.findall(
        r'(rspca|pdsa|kennel\s+club|blue\s+cross|british\s+veterinary|bva|defra|uk\s+government|nhs|pet\s+food\s+manufacturers|pfma|battersea)',
        lower
    )
    result["uk_authority_refs"] = len(uk_refs) > 0

    # "How We Evaluated" section
    result["how_we_evaluated"] = bool(
        re.search(r'(how\s+we\s+(evaluated|tested|assessed|reviewed|chose|selected|ranked))', lower)
    )

    # "Why We Reference Sources" section
    result["why_we_reference"] = bool(
        re.search(r'(why\s+we\s+reference|why\s+we\s+cite|our\s+sources|source\s+methodology|why\s+sources\s+matter)', lower)
    )

    # "Key Takeaways" section
    result["key_takeaways"] = bool(
        re.search(r'(key\s+takeaway|main\s+takeaway|what\s+to\s+remember|summary\s+of\s+key|quick\s+summary)', lower)
    )

    # "Common Mistakes" section
    result["common_mistakes"] = bool(
        re.search(r'(common\s+mistake|mistake.*to\s+avoid|pitfall|what\s+not\s+to|avoid\s+these|errors?\s+to\s+avoid)', lower)
    )

    # "When to Seek Help" section
    result["when_to_seek_help"] = bool(
        re.search(r'(when\s+to\s+(see|consult|visit|seek|contact)\s+(a\s+)?(vet|veterinarian|professional|behaviourist|behaviorist|expert|help))', lower)
    )

    # Beginner recommendations
    result["beginner_recs"] = bool(
        re.search(r'(beginner|first[\s-]time|new\s+(dog|cat|pet)\s+owner|starter|getting\s+started|if\s+you.*re\s+new)', lower)
    )

    # Budget vs Premium guidance
    result["budget_premium"] = bool(
        re.search(r'(budget|affordable|cheap|premium|luxury|splurge|high[\s-]end|value\s+for\s+money|price\s+range|worth\s+the\s+(price|cost|money))', lower)
    )

    return result


def fetch_cluster_posts(cluster_name, queries):
    """Fetch and deduplicate posts for a cluster across multiple search queries."""
    seen_ids = set()
    posts = []
    for q in queries:
        print(f"  Searching: '{q}'...")
        results = fetch_posts_for_search(q)
        for p in results:
            pid = p["id"]
            if pid not in seen_ids:
                seen_ids.add(pid)
                posts.append(p)
        time.sleep(1)
    print(f"  -> {len(posts)} unique posts for {cluster_name}")
    return posts


def profile_cluster(posts):
    """Analyze all posts in a cluster, return list of analysis dicts + aggregate profile."""
    analyses = []
    for p in posts:
        a = analyze_post(p)
        analyses.append(a)

    total = len(analyses)
    if total == 0:
        return analyses, {}

    profile = {}
    for elem in ELEMENTS:
        count = sum(1 for a in analyses if a.get(elem))
        profile[elem] = {
            "count": count,
            "total": total,
            "pct": round(100 * count / total, 1)
        }

    # Also compute averages for word_count and internal_links
    profile["avg_word_count"] = round(sum(a["word_count"] for a in analyses) / total, 0)
    profile["avg_internal_links"] = round(sum(a["internal_links"] for a in analyses) / total, 1)

    return analyses, profile


def compute_gaps(ref_profile, cluster_profile):
    """Compute gap and priority score for each element."""
    gaps = {}
    for elem in ELEMENTS:
        ref_pct = ref_profile.get(elem, {}).get("pct", 0)
        cl_pct = cluster_profile.get(elem, {}).get("pct", 0)
        gap = round(ref_pct - cl_pct, 1)
        weight = IMPORTANCE_WEIGHTS.get(elem, 5)
        priority = round(gap * weight / 100, 2)  # normalize
        gaps[elem] = {
            "gap": gap,
            "priority": priority,
            "ref_pct": ref_pct,
            "cl_pct": cl_pct,
        }
    return gaps


def generate_replication_plans(cluster_name, analyses, gaps, ref_profile):
    """Generate actionable replication plan rows for a cluster."""
    plans = []
    total = len(analyses)
    if total == 0:
        return plans

    for elem in ELEMENTS:
        g = gaps[elem]
        if g["gap"] <= 0:
            continue  # No gap

        posts_missing = [a for a in analyses if not a.get(elem)]
        n_missing = len(posts_missing)
        if n_missing == 0:
            continue

        # Nice element name
        nice = elem.replace("_", " ").title()
        ref_pct = g["ref_pct"]

        plan = {
            "cluster": cluster_name,
            "gap_type": f"Missing {nice}",
            "posts_affected": n_missing,
            "gap_description": f"{n_missing}/{total} posts lack {nice} (cluster {g['cl_pct']}% vs reference {ref_pct}%)",
            "priority": g["priority"],
            "recommended_action": f"Add {nice} section to {n_missing} posts to match Dog Toys reference ({ref_pct}% coverage)",
        }
        plans.append(plan)

    # Missing spokes analysis: if cluster has fewer posts than reference
    # (handled separately in missing_spokes output)

    return plans


def generate_missing_spokes(cluster_name, analyses, ref_analyses):
    """Suggest missing spoke topics based on reference cluster depth."""
    spokes = []
    ref_count = len(ref_analyses)
    cl_count = len(analyses)

    if cl_count >= ref_count:
        return spokes

    deficit = ref_count - cl_count

    # Generic spoke suggestions based on cluster type
    spoke_templates = {
        "Dog Food": [
            ("Grain-Free Dog Food Guide", "Reference cluster covers niche subtopics comprehensively"),
            ("Senior Dog Nutrition Guide", "Age-specific content matches reference depth pattern"),
            ("Puppy Food Transition Guide", "Life-stage guidance mirrors reference's completeness"),
            ("Raw vs Kibble Comparison", "Comparison content matches reference's table-heavy style"),
            ("Dog Food Allergy Guide", "Health-adjacent content expands cluster authority"),
        ],
        "Dog Beds": [
            ("Orthopaedic Dog Beds for Older Dogs", "Age-specific subtopic matches reference depth"),
            ("Outdoor & Waterproof Dog Beds", "Environment-specific guide fills cluster gap"),
            ("Anxiety-Relief Dog Beds (Calming Beds)", "Behavioural-crossover content adds authority"),
            ("Dog Bed Size Guide by Breed", "Practical guide matches reference's helpful-content pattern"),
            ("Heated Dog Beds for Winter", "Seasonal content expands cluster coverage"),
        ],
        "Puppy Care": [
            ("Puppy Socialisation Timeline", "Developmental stages content adds depth"),
            ("Puppy-Proofing Your Home Guide", "Practical safety content matches reference style"),
            ("Puppy Vaccination Schedule UK", "UK-specific authority content fills gap"),
            ("Puppy Sleep Training Guide", "Behavioural guidance matches reference completeness"),
            ("First 30 Days With Your Puppy", "Comprehensive onboarding guide adds cluster depth"),
        ],
        "Dog Health": [
            ("Common Dog Illnesses Symptoms Guide", "Health reference content builds authority"),
            ("Dog Dental Care Complete Guide", "Specific health subtopic expands cluster"),
            ("Dog Weight Management Guide", "Practical health guidance matches reference pattern"),
            ("Seasonal Dog Health Hazards UK", "UK-specific seasonal content adds authority"),
            ("Dog First Aid Kit Essentials", "Practical safety content fills cluster gap"),
        ],
        "Cat Supplies": [
            ("Best Self-Cleaning Litter Boxes UK", "Product-specific guide adds cluster depth"),
            ("Cat Bed Buying Guide by Cat Size", "Practical guide matches reference style"),
            ("Eco-Friendly Cat Litter Options", "Niche subtopic expands cluster coverage"),
            ("Indoor Cat Enrichment Supplies", "Behavioural-crossover content adds authority"),
            ("Cat Carrier Guide for Vet Visits", "Practical supply guide fills cluster gap"),
        ],
        "Cat Toys": [
            ("Interactive Cat Toys for Indoor Cats", "Environment-specific guide adds depth"),
            ("Cat Puzzle Feeders & Food Toys", "Enrichment content matches reference pattern"),
            ("DIY Cat Toys Safe Materials Guide", "Budget-friendly content fills practical gap"),
            ("Senior Cat Toy Recommendations", "Age-specific content matches reference depth"),
            ("Kitten Play Safety Guide", "Safety-focused content builds authority"),
        ],
        "Dog Grooming": [
            ("Dog Grooming Schedule by Coat Type", "Breed-specific practical guide adds depth"),
            ("Dog Nail Trimming Complete Guide", "Specific grooming subtopic expands cluster"),
            ("Dog Ear Cleaning Guide", "Health-adjacent grooming content adds authority"),
            ("Hypoallergenic Dog Shampoo Guide", "Niche product guide fills cluster gap"),
            ("Professional vs Home Dog Grooming", "Comparison content matches reference style"),
        ],
        "Dog Harnesses": [
            ("No-Pull Harness Training Guide", "Training-crossover content adds depth"),
            ("Dog Collar vs Harness Decision Guide", "Comparison content matches reference pattern"),
            ("Dog Lead Length & Material Guide", "Practical buying guide fills cluster gap"),
            ("Puppy Harness Size & Fitting Guide", "Age-specific guide adds cluster depth"),
            ("Reflective & Night Walk Gear Guide", "Safety-focused content builds authority"),
        ],
        "Dog Training": [
            ("Recall Training Step-by-Step Guide", "Core skill guide adds cluster depth"),
            ("Crate Training Complete Guide", "Comprehensive subtopic matches reference pattern"),
            ("Lead Reactivity Training Guide", "Behavioural subtopic expands cluster"),
            ("Puppy Training Timeline by Age", "Age-specific training guide adds depth"),
            ("Positive Reinforcement Methods Guide", "Methodology content builds authority"),
        ],
    }

    templates = spoke_templates.get(cluster_name, [])
    for i, (topic, rationale) in enumerate(templates):
        if i >= deficit:
            break
        priority = round(10 - (i * 0.5), 1)
        spokes.append({
            "cluster": cluster_name,
            "suggested_spoke_topic": topic,
            "rationale": rationale,
            "priority": priority,
        })

    return spokes


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    # =========================================
    # STEP 1: Profile Reference Cluster (Dog Toys)
    # =========================================
    print("=" * 60)
    print("STEP 1: Profiling Reference Cluster - Dog Toys")
    print("=" * 60)

    ref_queries = CLUSTERS[REFERENCE_CLUSTER]
    ref_posts = fetch_cluster_posts(REFERENCE_CLUSTER, ref_queries)
    time.sleep(1)
    ref_analyses, ref_profile = profile_cluster(ref_posts)

    print(f"\nReference Profile ({len(ref_analyses)} posts):")
    for elem in ELEMENTS:
        p = ref_profile.get(elem, {})
        print(f"  {elem}: {p.get('count',0)}/{p.get('total',0)} = {p.get('pct',0)}%")
    print(f"  Avg word count: {ref_profile.get('avg_word_count', 0)}")
    print(f"  Avg internal links: {ref_profile.get('avg_internal_links', 0)}")

    # Write reference_profile.csv
    ref_csv = os.path.join(DATA_DIR, "reference_profile.csv")
    with open(ref_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["element", "dog_toys_count", "dog_toys_total", "dog_toys_pct"])
        for elem in ELEMENTS:
            p = ref_profile.get(elem, {})
            w.writerow([elem, p.get("count", 0), p.get("total", 0), p.get("pct", 0)])
        # Also include word count and internal links as supplementary rows
        w.writerow(["avg_word_count", ref_profile.get("avg_word_count", 0), len(ref_analyses), ""])
        w.writerow(["avg_internal_links", ref_profile.get("avg_internal_links", 0), len(ref_analyses), ""])
    print(f"\n[SAVED] {ref_csv}")

    # =========================================
    # STEP 2: Profile Each Target Cluster
    # =========================================
    print("\n" + "=" * 60)
    print("STEP 2: Profiling Target Clusters")
    print("=" * 60)

    all_cluster_data = {REFERENCE_CLUSTER: {"analyses": ref_analyses, "profile": ref_profile}}

    for cluster_name, queries in CLUSTERS.items():
        if cluster_name == REFERENCE_CLUSTER:
            continue
        print(f"\n--- {cluster_name} ---")
        posts = fetch_cluster_posts(cluster_name, queries)
        time.sleep(1)
        analyses, profile = profile_cluster(posts)
        all_cluster_data[cluster_name] = {"analyses": analyses, "profile": profile}

        print(f"  Profile ({len(analyses)} posts):")
        for elem in ELEMENTS:
            p = profile.get(elem, {})
            print(f"    {elem}: {p.get('count',0)}/{p.get('total',0)} = {p.get('pct',0)}%")

    # Write cluster_profiles.csv
    profiles_csv = os.path.join(DATA_DIR, "cluster_profiles.csv")
    with open(profiles_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cluster", "element", "count", "total", "pct", "gap_vs_reference", "priority_score"])
        for cluster_name in CLUSTERS:
            data = all_cluster_data.get(cluster_name)
            if not data or not data["profile"]:
                continue
            profile = data["profile"]
            gaps = compute_gaps(ref_profile, profile) if cluster_name != REFERENCE_CLUSTER else {}
            for elem in ELEMENTS:
                p = profile.get(elem, {})
                gap = gaps.get(elem, {}).get("gap", 0) if gaps else 0
                pri = gaps.get(elem, {}).get("priority", 0) if gaps else 0
                w.writerow([cluster_name, elem, p.get("count", 0), p.get("total", 0),
                            p.get("pct", 0), gap, pri])
    print(f"\n[SAVED] {profiles_csv}")

    # =========================================
    # STEP 3: Compute Gaps & Generate Plans
    # =========================================
    print("\n" + "=" * 60)
    print("STEP 3: Computing Gaps & Generating Replication Plans")
    print("=" * 60)

    all_plans = []
    all_spokes = []

    for cluster_name in CLUSTERS:
        if cluster_name == REFERENCE_CLUSTER:
            continue
        data = all_cluster_data.get(cluster_name)
        if not data or not data["profile"]:
            continue

        gaps = compute_gaps(ref_profile, data["profile"])
        plans = generate_replication_plans(cluster_name, data["analyses"], gaps, ref_profile)
        all_plans.extend(plans)

        spokes = generate_missing_spokes(cluster_name, data["analyses"], ref_analyses)
        all_spokes.extend(spokes)

        print(f"\n{cluster_name}: {len(plans)} gap items, {len(spokes)} spoke suggestions")

    # Sort plans by priority descending
    all_plans.sort(key=lambda x: x["priority"], reverse=True)

    # Write replication_plans.csv
    plans_csv = os.path.join(DATA_DIR, "replication_plans.csv")
    with open(plans_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cluster", "gap_type", "posts_affected", "gap_description", "priority", "recommended_action"])
        for plan in all_plans:
            w.writerow([plan["cluster"], plan["gap_type"], plan["posts_affected"],
                         plan["gap_description"], plan["priority"], plan["recommended_action"]])
    print(f"\n[SAVED] {plans_csv}")

    # Write missing_spokes.csv
    spokes_csv = os.path.join(DATA_DIR, "missing_spokes.csv")
    with open(spokes_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cluster", "suggested_spoke_topic", "rationale", "priority"])
        for s in all_spokes:
            w.writerow([s["cluster"], s["suggested_spoke_topic"], s["rationale"], s["priority"]])
    print(f"\n[SAVED] {spokes_csv}")

    # =========================================
    # STEP 4: Cluster Rankings
    # =========================================
    print("\n" + "=" * 60)
    print("STEP 4: Generating Cluster Rankings")
    print("=" * 60)

    rankings = []
    for cluster_name in CLUSTERS:
        data = all_cluster_data.get(cluster_name)
        if not data or not data["profile"]:
            rankings.append({
                "cluster": cluster_name, "posts": 0, "avg_word_count": 0,
                "faq_pct": 0, "comparison_pct": 0, "trust_pct": 0, "authority_pct": 0,
                "at_a_glance_pct": 0, "key_takeaways_pct": 0, "dominance_score": 0, "rank": 0
            })
            continue

        profile = data["profile"]
        analyses = data["analyses"]
        total = len(analyses)

        faq_pct = profile.get("faq", {}).get("pct", 0)
        comparison_pct = profile.get("comparison_table", {}).get("pct", 0)
        trust_pct = profile.get("trust_footer", {}).get("pct", 0)
        authority_pct = profile.get("uk_authority_refs", {}).get("pct", 0)
        at_a_glance_pct = profile.get("at_a_glance", {}).get("pct", 0)
        key_takeaways_pct = profile.get("key_takeaways", {}).get("pct", 0)

        # Dominance score: weighted average of key metrics + post count bonus
        dominance = (
            faq_pct * 0.20 +
            comparison_pct * 0.15 +
            trust_pct * 0.15 +
            authority_pct * 0.15 +
            at_a_glance_pct * 0.10 +
            key_takeaways_pct * 0.10 +
            min(total * 2, 15)  # post count bonus, capped at 15
        )

        rankings.append({
            "cluster": cluster_name,
            "posts": total,
            "avg_word_count": profile.get("avg_word_count", 0),
            "faq_pct": faq_pct,
            "comparison_pct": comparison_pct,
            "trust_pct": trust_pct,
            "authority_pct": authority_pct,
            "at_a_glance_pct": at_a_glance_pct,
            "key_takeaways_pct": key_takeaways_pct,
            "dominance_score": round(dominance, 1),
            "rank": 0,  # filled after sorting
        })

    # Sort by dominance score descending
    rankings.sort(key=lambda x: x["dominance_score"], reverse=True)
    for i, r in enumerate(rankings):
        r["rank"] = i + 1

    # Write cluster_rankings.csv
    rankings_csv = os.path.join(DATA_DIR, "cluster_rankings.csv")
    with open(rankings_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cluster", "posts", "avg_word_count", "faq_pct", "comparison_pct",
                     "trust_pct", "authority_pct", "at_a_glance_pct", "key_takeaways_pct",
                     "dominance_score", "rank"])
        for r in rankings:
            w.writerow([r["cluster"], r["posts"], r["avg_word_count"],
                         r["faq_pct"], r["comparison_pct"], r["trust_pct"],
                         r["authority_pct"], r["at_a_glance_pct"], r["key_takeaways_pct"],
                         r["dominance_score"], r["rank"]])
    print(f"\n[SAVED] {rankings_csv}")

    # =========================================
    # Summary
    # =========================================
    print("\n" + "=" * 60)
    print("PHASE 10AO COMPLETE - SUMMARY")
    print("=" * 60)
    print(f"\nReference cluster: {REFERENCE_CLUSTER} ({len(ref_analyses)} posts)")
    print(f"Target clusters profiled: {len(CLUSTERS) - 1}")
    print(f"Total replication plan items: {len(all_plans)}")
    print(f"Total missing spoke suggestions: {len(all_spokes)}")
    print(f"\nCluster Rankings:")
    for r in rankings:
        print(f"  #{r['rank']} {r['cluster']}: {r['dominance_score']} dominance ({r['posts']} posts)")
    print(f"\nAll output files in: {DATA_DIR}/")
    print("  - reference_profile.csv")
    print("  - cluster_profiles.csv")
    print("  - replication_plans.csv")
    print("  - cluster_rankings.csv")
    print("  - missing_spokes.csv")


if __name__ == "__main__":
    main()
