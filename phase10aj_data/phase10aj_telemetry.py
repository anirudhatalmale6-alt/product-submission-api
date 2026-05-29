#!/usr/bin/env python3
"""
Phase 10AJ Telemetry & Scoring for PetHub Online WordPress site.
Fetches 30 posts (3 from each of 10 clusters) and scores on 7 dimensions.
"""

import subprocess
import json
import csv
import re
import time
import random
import os
import sys
from collections import defaultdict
from html import unescape

# ── Config ──────────────────────────────────────────────────────────────────
WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10aj_data"

# Cluster keywords for categorisation
CLUSTER_KEYWORDS = {
    "Dog Toys":       ["dog toy", "dog toys", "chew toy", "fetch toy", "tug toy", "interactive toy for dog", "puzzle toy for dog"],
    "Dog Food":       ["dog food", "dog diet", "dog nutrition", "best food for dog", "dry dog food", "wet dog food", "grain-free dog", "puppy food"],
    "Dog Health":     ["dog health", "dog supplement", "dog vitamin", "joint support dog", "dog dental", "flea", "tick", "worming", "dog allergy", "dog immune"],
    "Dog Training":   ["dog training", "dog lead", "dog leash", "training treat", "clicker", "dog whistle", "obedience", "recall training"],
    "Cat Toys":       ["cat toy", "cat toys", "cat wand", "cat laser", "cat puzzle", "interactive cat", "feather toy"],
    "Cat Supplies":   ["cat litter", "cat bed", "cat tree", "cat scratching", "cat carrier", "cat bowl", "cat fountain", "cat supply", "cat supplies", "cat brush"],
    "Dog Grooming":   ["dog grooming", "dog shampoo", "dog brush", "dog nail", "dog clipper", "dog coat", "deshedding", "dog bath"],
    "Dog Harnesses":  ["dog harness", "no-pull harness", "front-clip harness", "dog vest", "walking harness"],
    "Dog Beds":       ["dog bed", "dog crate", "dog mat", "orthopaedic dog", "orthopedic dog", "dog blanket", "dog sleeping", "memory foam dog"],
    "Puppy Care":     ["puppy", "puppies", "new puppy", "puppy training", "puppy socialisation", "puppy socialization", "puppy teething", "puppy crate"],
}

# Phase 10AI baselines
BASELINES = {
    "E-E-A-T Depth": 28.0,
    "Humanization": 0.0,
    "Conversion Sophistication": 76.0,
    "Comparison Quality": 73.0,
    "Trust Intensity": 62.0,
    "Citation Readiness": 90.7,
    "Practical Usefulness": 71.4,
}


def api_call(endpoint):
    """Make a WP REST API call using curl subprocess."""
    url = f"{WP_API}/{endpoint}"
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
        print(f"  [WARN] JSON decode error for {url}: {result.stdout[:200]}")
        return None


def strip_html(html_text):
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', ' ', html_text)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def classify_post(title, content_text):
    """Classify a post into one of the 10 clusters based on title and content."""
    combined = (title + " " + content_text[:2000]).lower()
    best_cluster = None
    best_score = 0
    for cluster, keywords in CLUSTER_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        # Weight title matches more heavily
        title_lower = title.lower()
        score += sum(3 for kw in keywords if kw in title_lower)
        if score > best_score:
            best_score = score
            best_cluster = cluster
    return best_cluster if best_cluster else "Uncategorized"


def score_eeat_depth(content):
    """Score E-E-A-T Depth (0-100)."""
    c_lower = content.lower()
    blocks = {
        "About this guide": 12,
        "How we evaluated": 15,
        "Why this matters": 12,
        "What we considered": 12,
        "What to realistically expect": 15,
        "When advice may differ": 12,
        "What pet owners commonly overlook": 12,
        "Questions we considered": 10,
    }
    total = 0
    found = []
    for block, pts in blocks.items():
        if block.lower() in c_lower:
            total += pts
            found.append(block)
    return min(total, 100), "|".join(found) if found else "none"


def score_humanization(content):
    """Score Humanization Intensity (0-100)."""
    c_lower = content.lower()
    score = 0
    found = []

    # Real-world scenario language (15pts)
    scenario_terms = ["realistically expect", "adjustment period", "normal", "frustrating"]
    if any(t in c_lower for t in scenario_terms):
        score += 15
        found.append("real-world-scenarios")

    # Honest caveats (15pts)
    caveat_terms = ["not ideal if", "won't work", "doesn't mean", "that's normal", "that is normal"]
    if any(t in c_lower for t in caveat_terms):
        score += 15
        found.append("honest-caveats")

    # Common Mistakes section (15pts)
    if "common mistake" in c_lower or "mistakes to avoid" in c_lower:
        score += 15
        found.append("common-mistakes")

    # Troubleshooting section (15pts)
    if "troubleshoot" in c_lower:
        score += 15
        found.append("troubleshooting")

    # When to Seek Help (15pts)
    if "when to seek" in c_lower or "see your vet" in c_lower or "consult your vet" in c_lower:
        score += 15
        found.append("when-to-seek-help")

    # Personal/relatable tone (10pts)
    personal_terms = ["your dog", "your cat", "your puppy"]
    if any(t in c_lower for t in personal_terms):
        score += 10
        found.append("personal-tone")

    # Absence of AI patterns (15pts) - more AI patterns = lower score
    ai_patterns = ["designed to", "it's important to note", "comprehensive guide", "when it comes to",
                   "it is important to note", "in conclusion"]
    ai_count = sum(1 for p in ai_patterns if p in c_lower)
    if ai_count == 0:
        score += 15
        found.append("no-ai-patterns")
    elif ai_count == 1:
        score += 10
        found.append("minimal-ai-patterns")
    elif ai_count == 2:
        score += 5
        found.append("some-ai-patterns")
    else:
        found.append(f"ai-patterns({ai_count})")

    return min(score, 100), "|".join(found) if found else "none"


def score_conversion(content):
    """Score Conversion Sophistication (0-100)."""
    c_lower = content.lower()
    score = 0
    found = []

    # Quick Suitability Guide (15pts)
    if "suitability" in c_lower or "quick suitability" in c_lower or "is this right for" in c_lower:
        score += 15
        found.append("suitability-guide")

    # Good choice if / Not ideal if (20pts)
    if ("good choice if" in c_lower or "great choice if" in c_lower) and ("not ideal if" in c_lower or "not suitable if" in c_lower):
        score += 20
        found.append("good-notideal")
    elif "good choice if" in c_lower or "great choice if" in c_lower or "not ideal if" in c_lower:
        score += 10
        found.append("partial-good-notideal")

    # Best For sections (15pts)
    if "best for" in c_lower:
        score += 15
        found.append("best-for")

    # Decision Summary (20pts)
    if "decision summary" in c_lower or "final verdict" in c_lower or "our verdict" in c_lower or "the verdict" in c_lower:
        score += 20
        found.append("decision-summary")

    # Comparison table (15pts)
    if "<table" in content.lower() or "comparison" in c_lower:
        score += 15
        found.append("comparison-table")

    # Budget/Premium guidance (15pts)
    if ("budget" in c_lower and ("premium" in c_lower or "mid-range" in c_lower)) or "price range" in c_lower:
        score += 15
        found.append("budget-premium")

    return min(score, 100), "|".join(found) if found else "none"


def score_comparison(content):
    """Score Comparison Quality (0-100)."""
    c_lower = content.lower()
    score = 0
    found = []

    has_table = "<table" in content.lower()

    # Has comparison table (20pts)
    if has_table:
        score += 20
        found.append("has-table")

    # Has "Best For" column (20pts)
    if has_table and "best for" in c_lower:
        score += 20
        found.append("best-for-column")

    # Has 4+ rows (15pts)
    if has_table:
        tr_count = content.lower().count("<tr")
        if tr_count >= 5:  # 1 header + 4 data rows
            score += 15
            found.append(f"rows({tr_count})")

    # Has suitability info (20pts)
    if "suitable for" in c_lower or "suitability" in c_lower or "good choice if" in c_lower or "best for" in c_lower:
        score += 20
        found.append("suitability-info")

    # Multiple comparison dimensions (15pts)
    dimensions = ["price", "size", "durability", "material", "weight", "rating", "quality", "comfort", "value"]
    dim_count = sum(1 for d in dimensions if d in c_lower)
    if dim_count >= 3:
        score += 15
        found.append(f"dimensions({dim_count})")

    # Table uses proper HTML formatting (10pts)
    if has_table and "<th" in content.lower():
        score += 10
        found.append("proper-html-table")

    return min(score, 100), "|".join(found) if found else "none"


def score_trust(content):
    """Score Trust Intensity (0-100)."""
    c_lower = content.lower()
    score = 0
    found = []

    # Trust footer present (15pts)
    if "trust" in c_lower and ("footer" in c_lower or "editorial" in c_lower or "our commitment" in c_lower):
        score += 15
        found.append("trust-footer")
    elif "you can trust" in c_lower or "why trust" in c_lower:
        score += 15
        found.append("trust-statement")

    # UK authority links (RSPCA, PDSA, BVA etc) (15pts)
    uk_authorities = ["rspca", "pdsa", "bva", "kennel club", "blue cross", "cats protection",
                      "battersea", "dogs trust", "royal veterinary"]
    if any(a in c_lower for a in uk_authorities):
        score += 15
        found.append("uk-authority-links")

    # "Why we reference these sources" block (20pts)
    if "why we reference" in c_lower or "our sources" in c_lower or "sources we reference" in c_lower:
        score += 20
        found.append("source-reference-block")

    # "How we evaluated" methodology (15pts)
    if "how we evaluated" in c_lower or "our evaluation" in c_lower or "our methodology" in c_lower:
        score += 15
        found.append("evaluation-methodology")

    # AI transparency disclosure (15pts)
    if "ai" in c_lower and ("transparen" in c_lower or "assisted" in c_lower or "generated" in c_lower or "disclosure" in c_lower):
        score += 15
        found.append("ai-transparency")
    elif "artificial intelligence" in c_lower:
        score += 15
        found.append("ai-mention")

    # Editorial process link (10pts)
    if "editorial process" in c_lower or "editorial policy" in c_lower or "editorial standard" in c_lower:
        score += 10
        found.append("editorial-process")

    # Corrections policy link (10pts)
    if "correction" in c_lower and "policy" in c_lower:
        score += 10
        found.append("corrections-policy")

    return min(score, 100), "|".join(found) if found else "none"


def score_citation(content):
    """Score Citation Readiness (0-100)."""
    c_lower = content.lower()
    score = 0
    found = []

    # At a Glance box (15pts)
    if "at a glance" in c_lower:
        score += 15
        found.append("at-a-glance")

    # Key Takeaways (15pts)
    if "key takeaway" in c_lower or "quick takeaway" in c_lower:
        score += 15
        found.append("key-takeaways")

    # Decision Summary (20pts)
    if "decision summary" in c_lower or "final verdict" in c_lower or "our verdict" in c_lower or "the verdict" in c_lower:
        score += 20
        found.append("decision-summary")

    # FAQ section (15pts)
    if "frequently asked" in c_lower or "faq" in c_lower or "common questions" in c_lower:
        score += 15
        found.append("faq")

    # Quick Answer block (10pts)
    if "quick answer" in c_lower or "short answer" in c_lower or "in short" in c_lower:
        score += 10
        found.append("quick-answer")

    # Source references (15pts)
    if "source" in c_lower or "reference" in c_lower or "cited" in c_lower or "according to" in c_lower:
        score += 15
        found.append("source-references")

    # Glossary terms (10pts)
    if "glossary" in c_lower or "definition" in c_lower or "what does" in c_lower:
        score += 10
        found.append("glossary")

    return min(score, 100), "|".join(found) if found else "none"


def score_practical(content):
    """Score Practical Usefulness (0-100)."""
    c_lower = content.lower()
    score = 0
    found = []

    # Troubleshooting section (15pts)
    if "troubleshoot" in c_lower:
        score += 15
        found.append("troubleshooting")

    # When to Seek Help (15pts)
    if "when to seek" in c_lower or "see your vet" in c_lower or "consult your vet" in c_lower or "visit your vet" in c_lower:
        score += 15
        found.append("when-to-seek-help")

    # Warning Signs (10pts)
    if "warning sign" in c_lower or "red flag" in c_lower or "watch out for" in c_lower:
        score += 10
        found.append("warning-signs")

    # Common Mistakes (15pts)
    if "common mistake" in c_lower or "mistakes to avoid" in c_lower:
        score += 15
        found.append("common-mistakes")

    # What to Realistically Expect (15pts)
    if "realistically expect" in c_lower or "realistic expect" in c_lower or "what to expect" in c_lower:
        score += 15
        found.append("realistic-expectations")

    # Routine/schedule guidance (10pts)
    if "routine" in c_lower or "schedule" in c_lower or "daily" in c_lower or "weekly" in c_lower:
        score += 10
        found.append("routine-guidance")

    # Is This Right for You (10pts)
    if "is this right" in c_lower or "right for you" in c_lower or "right for your" in c_lower:
        score += 10
        found.append("right-for-you")

    # Decision trees/pathways (10pts)
    if "decision" in c_lower or "pathway" in c_lower or "flow" in c_lower or "choose" in c_lower:
        score += 10
        found.append("decision-pathways")

    return min(score, 100), "|".join(found) if found else "none"


def fetch_all_posts():
    """Fetch all published posts from the WP API (paginated)."""
    all_posts = []
    page = 1
    while True:
        print(f"  Fetching posts page {page}...")
        data = api_call(f"posts?per_page=100&page={page}&status=publish&_fields=id,title,content,slug,categories")
        if not data or not isinstance(data, list) or len(data) == 0:
            break
        all_posts.extend(data)
        print(f"    Got {len(data)} posts (total: {len(all_posts)})")
        if len(data) < 100:
            break
        page += 1
        time.sleep(1)
    return all_posts


def main():
    print("=" * 70)
    print("Phase 10AJ Telemetry & Scoring - PetHub Online")
    print("=" * 70)

    # Step 1: Wait for content agents
    print("\n[1/5] Waiting 240 seconds for content agents to land their batches...")
    time.sleep(240)
    print("  Wait complete. Starting telemetry.")

    # Step 2: Fetch all posts
    print("\n[2/5] Fetching all published posts...")
    all_posts = fetch_all_posts()
    print(f"  Total posts fetched: {len(all_posts)}")

    if not all_posts:
        print("  ERROR: No posts found. Exiting.")
        sys.exit(1)

    # Step 3: Classify posts into clusters and select 3 from each
    print("\n[3/5] Classifying posts into clusters...")
    cluster_posts = defaultdict(list)

    for post in all_posts:
        title = strip_html(post.get("title", {}).get("rendered", ""))
        content_raw = post.get("content", {}).get("rendered", "")
        content_text = strip_html(content_raw)
        cluster = classify_post(title, content_text)
        cluster_posts[cluster].append({
            "id": post["id"],
            "title": title,
            "content_raw": content_raw,
            "content_text": content_text,
            "cluster": cluster,
        })

    print(f"  Clusters found: {len(cluster_posts)}")
    for c, posts in sorted(cluster_posts.items()):
        print(f"    {c}: {len(posts)} posts")

    # Select 3 from each target cluster
    target_clusters = list(CLUSTER_KEYWORDS.keys())
    selected_posts = []

    for cluster in target_clusters:
        posts = cluster_posts.get(cluster, [])
        if len(posts) >= 3:
            chosen = random.sample(posts, 3)
        elif len(posts) > 0:
            chosen = posts[:]
            # Pad from uncategorized or other clusters if needed
            print(f"  [WARN] Only {len(posts)} posts in '{cluster}', using all available")
        else:
            print(f"  [WARN] No posts in '{cluster}', will try Uncategorized")
            chosen = []

        for p in chosen:
            p["cluster"] = cluster  # Ensure correct cluster assignment
        selected_posts.extend(chosen)

    print(f"\n  Selected {len(selected_posts)} posts for scoring")

    # If we have fewer than 30, try to fill from uncategorized
    if len(selected_posts) < 30:
        uncategorized = cluster_posts.get("Uncategorized", [])
        needed = 30 - len(selected_posts)
        if uncategorized:
            extra = random.sample(uncategorized, min(needed, len(uncategorized)))
            # Distribute extras across clusters that need them
            deficit_clusters = [c for c in target_clusters if len(cluster_posts.get(c, [])) < 3]
            for i, p in enumerate(extra):
                if deficit_clusters:
                    p["cluster"] = deficit_clusters[i % len(deficit_clusters)]
                else:
                    p["cluster"] = "Uncategorized"
            selected_posts.extend(extra)
            print(f"  Added {len(extra)} from uncategorized. Total: {len(selected_posts)}")

    # Step 4: Score each post
    print("\n[4/5] Scoring posts on 7 dimensions...")

    eeat_rows = []
    human_rows = []
    conv_rows = []
    comp_rows = []
    trust_rows = []
    cite_rows = []
    pract_rows = []

    for i, post in enumerate(selected_posts):
        pid = post["id"]
        title = post["title"]
        cluster = post["cluster"]
        content = post["content_raw"]
        print(f"  [{i+1}/{len(selected_posts)}] Scoring: {title[:60]}... (cluster: {cluster})")

        e_score, e_found = score_eeat_depth(content)
        h_score, h_found = score_humanization(content)
        c_score, c_found = score_conversion(content)
        cmp_score, cmp_found = score_comparison(content)
        t_score, t_found = score_trust(content)
        ci_score, ci_found = score_citation(content)
        p_score, p_found = score_practical(content)

        eeat_rows.append([pid, title, cluster, e_score, e_found])
        human_rows.append([pid, title, cluster, h_score, h_found])
        conv_rows.append([pid, title, cluster, c_score, c_found])
        comp_rows.append([pid, title, cluster, cmp_score, cmp_found])
        trust_rows.append([pid, title, cluster, t_score, t_found])
        cite_rows.append([pid, title, cluster, ci_score, ci_found])
        pract_rows.append([pid, title, cluster, p_score, p_found])

        print(f"    EEAT={e_score} HUM={h_score} CONV={c_score} COMP={cmp_score} TRUST={t_score} CITE={ci_score} PRACT={p_score}")

    # Step 5: Write CSV files
    print("\n[5/5] Writing output files...")

    csv_files = {
        "eeat_depth_scores.csv": (["id", "title", "cluster", "score", "blocks_found"], eeat_rows),
        "humanization_scores.csv": (["id", "title", "cluster", "score", "signals_found"], human_rows),
        "conversion_scores.csv": (["id", "title", "cluster", "score", "elements_found"], conv_rows),
        "comparison_scores.csv": (["id", "title", "cluster", "score", "elements_found"], comp_rows),
        "trust_intensity_scores.csv": (["id", "title", "cluster", "score", "elements_found"], trust_rows),
        "citation_scores.csv": (["id", "title", "cluster", "score", "elements_found"], cite_rows),
        "practical_scores.csv": (["id", "title", "cluster", "score", "elements_found"], pract_rows),
    }

    for fname, (headers, rows) in csv_files.items():
        fpath = os.path.join(DATA_DIR, fname)
        with open(fpath, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(headers)
            w.writerows(rows)
        print(f"  Written: {fname}")

    # Dashboard: cluster averages
    print("\n  Computing cluster averages...")
    cluster_data = defaultdict(lambda: {"count": 0, "eeat": [], "human": [], "conv": [], "comp": [], "trust": [], "cite": [], "pract": []})

    for i in range(len(selected_posts)):
        cl = selected_posts[i]["cluster"]
        cluster_data[cl]["count"] += 1
        cluster_data[cl]["eeat"].append(eeat_rows[i][3])
        cluster_data[cl]["human"].append(human_rows[i][3])
        cluster_data[cl]["conv"].append(conv_rows[i][3])
        cluster_data[cl]["comp"].append(comp_rows[i][3])
        cluster_data[cl]["trust"].append(trust_rows[i][3])
        cluster_data[cl]["cite"].append(cite_rows[i][3])
        cluster_data[cl]["pract"].append(pract_rows[i][3])

    dashboard_path = os.path.join(DATA_DIR, "phase10aj_dashboard.csv")
    with open(dashboard_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cluster", "posts_scored", "avg_eeat_depth", "avg_humanization", "avg_conversion",
                     "avg_comparison", "avg_trust", "avg_citation", "avg_practical", "composite_score"])

        all_composites = []
        for cl in target_clusters:
            d = cluster_data.get(cl)
            if not d or d["count"] == 0:
                w.writerow([cl, 0, 0, 0, 0, 0, 0, 0, 0, 0])
                continue
            n = d["count"]
            avgs = {
                "eeat": sum(d["eeat"]) / n,
                "human": sum(d["human"]) / n,
                "conv": sum(d["conv"]) / n,
                "comp": sum(d["comp"]) / n,
                "trust": sum(d["trust"]) / n,
                "cite": sum(d["cite"]) / n,
                "pract": sum(d["pract"]) / n,
            }
            composite = sum(avgs.values()) / 7
            all_composites.append(composite)
            w.writerow([cl, n,
                        f"{avgs['eeat']:.1f}", f"{avgs['human']:.1f}", f"{avgs['conv']:.1f}",
                        f"{avgs['comp']:.1f}", f"{avgs['trust']:.1f}", f"{avgs['cite']:.1f}",
                        f"{avgs['pract']:.1f}", f"{composite:.1f}"])

        # Overall row
        total_n = len(selected_posts)
        if total_n > 0:
            overall_eeat = sum(r[3] for r in eeat_rows) / total_n
            overall_human = sum(r[3] for r in human_rows) / total_n
            overall_conv = sum(r[3] for r in conv_rows) / total_n
            overall_comp = sum(r[3] for r in comp_rows) / total_n
            overall_trust = sum(r[3] for r in trust_rows) / total_n
            overall_cite = sum(r[3] for r in cite_rows) / total_n
            overall_pract = sum(r[3] for r in pract_rows) / total_n
            overall_composite = (overall_eeat + overall_human + overall_conv + overall_comp +
                                 overall_trust + overall_cite + overall_pract) / 7
            w.writerow(["OVERALL", total_n,
                        f"{overall_eeat:.1f}", f"{overall_human:.1f}", f"{overall_conv:.1f}",
                        f"{overall_comp:.1f}", f"{overall_trust:.1f}", f"{overall_cite:.1f}",
                        f"{overall_pract:.1f}", f"{overall_composite:.1f}"])

    print(f"  Written: phase10aj_dashboard.csv")

    # Before/After comparison
    before_after_path = os.path.join(DATA_DIR, "phase10aj_before_after.csv")
    dimension_scores = {
        "E-E-A-T Depth": overall_eeat if total_n > 0 else 0,
        "Humanization": overall_human if total_n > 0 else 0,
        "Conversion Sophistication": overall_conv if total_n > 0 else 0,
        "Comparison Quality": overall_comp if total_n > 0 else 0,
        "Trust Intensity": overall_trust if total_n > 0 else 0,
        "Citation Readiness": overall_cite if total_n > 0 else 0,
        "Practical Usefulness": overall_pract if total_n > 0 else 0,
    }

    with open(before_after_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["dimension", "phase10ai_baseline", "phase10aj_score", "improvement_pct"])
        for dim in BASELINES:
            baseline = BASELINES[dim]
            current = dimension_scores.get(dim, 0)
            if baseline > 0:
                improvement = ((current - baseline) / baseline) * 100
            else:
                improvement = current  # From 0 baseline, just show current score as improvement
            w.writerow([dim, f"{baseline:.1f}", f"{current:.1f}", f"{improvement:.1f}"])

    print(f"  Written: phase10aj_before_after.csv")

    # ── Summary ─────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("PHASE 10AJ TELEMETRY SUMMARY")
    print("=" * 70)
    print(f"Posts scored: {total_n}")
    print(f"\nDimension Averages:")
    for dim, score in dimension_scores.items():
        baseline = BASELINES.get(dim, 0)
        delta = score - baseline
        arrow = "+" if delta >= 0 else ""
        print(f"  {dim:30s}: {score:5.1f}  (baseline {baseline:.1f}, {arrow}{delta:.1f})")
    if total_n > 0:
        print(f"\n  Composite Score: {overall_composite:.1f}")
    print("=" * 70)
    print("Phase 10AJ telemetry complete.")


if __name__ == "__main__":
    main()
