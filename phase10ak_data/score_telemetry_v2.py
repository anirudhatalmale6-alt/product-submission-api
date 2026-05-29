#!/usr/bin/env python3
"""
Phase 10AK Full Telemetry Re-Score for PetHub Online - v2
Scores 50 posts (5 per cluster) across 8 dimensions.
Uses multiple search strategies and category/tag lookups to fill all clusters.
"""

import subprocess
import json
import csv
import re
import sys
import time
import html
import urllib.parse
from collections import defaultdict

# --- Config ---
WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ak_data"

CLUSTERS = [
    "Dog Toys", "Dog Food", "Dog Health", "Dog Training",
    "Cat Toys", "Cat Supplies", "Dog Grooming", "Dog Harnesses",
    "Dog Beds", "Puppy Care"
]

POSTS_PER_CLUSTER = 5

# Multiple search terms per cluster (tried in order)
CLUSTER_SEARCHES = {
    "Dog Toys": ["dog toy", "dog toys", "chew toy", "puzzle toy", "tug toy", "fetch toy"],
    "Dog Food": ["dog food", "feeding", "nutrition dog", "diet dog", "kibble", "raw food dog"],
    "Dog Health": ["dog health", "vet", "veterinary", "illness dog", "dog care health", "pet health"],
    "Dog Training": ["dog training", "training", "obedience", "behaviour dog", "recall", "leash training"],
    "Cat Toys": ["cat toy", "cat toys", "cat play", "interactive cat", "feather toy", "laser cat"],
    "Cat Supplies": ["cat supplies", "cat care", "cat litter", "cat food", "cat scratching", "indoor cat"],
    "Dog Grooming": ["dog grooming", "grooming", "bathing dog", "dog coat", "nail trimming", "brushing dog"],
    "Dog Harnesses": ["dog harness", "harness", "lead dog", "collar", "walking equipment", "dog equipment"],
    "Dog Beds": ["dog bed", "dog beds", "dog sleeping", "crate", "den dog", "resting dog", "orthopedic dog"],
    "Puppy Care": ["puppy", "puppy care", "new puppy", "puppy training", "puppy development", "young dog"],
}

# Baselines
BASELINES_10AI = {
    "E-E-A-T Depth": 28.0,
    "Trust Intensity": 62.0,
    "Conversion": 76.0,
    "Practical Usefulness": 71.4,
    "Comparison Quality": 73.0,
    "Citation Readiness": 90.7,
}
BASELINES_10AJ = {
    "E-E-A-T Depth": 26.8,
    "Humanization": 68.3,
    "Conversion": 39.8,
    "Comparison Quality": 74.3,
    "Trust Intensity": 60.0,
    "Citation Readiness": 72.0,
    "Practical Usefulness": 62.3,
}


def api_call(url):
    """Make WP REST API call via subprocess curl."""
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def strip_html(raw_html):
    """Strip HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', ' ', raw_html)
    text = html.unescape(text)
    return text


def count_internal_links(content):
    """Count links to pethubonline.com in content."""
    links = re.findall(r'href=["\']([^"\']+)["\']', content, re.IGNORECASE)
    internal = [l for l in links if 'pethubonline.com' in l or (l.startswith('/') and not l.startswith('//'))]
    return len(internal)


def word_count(text):
    """Count words in plain text."""
    return len(text.split())


def ci(text, phrase):
    """Case-insensitive search for phrase in text."""
    return phrase.lower() in text.lower()


def ci_count(text, phrase):
    """Case-insensitive count of phrase in text."""
    return len(re.findall(re.escape(phrase.lower()), text.lower()))


def score_eeat(content, text):
    score = 0
    if ci(text, "about this guide"): score += 10
    if ci(text, "how we evaluated"): score += 15
    if ci(text, "why this matters"): score += 10
    if ci(text, "what we considered"): score += 10
    if ci(text, "what to realistically expect"): score += 15
    if ci(text, "is this right for you") or ci(text, "good choice if"): score += 10
    if ci(text, "why we reference these sources"): score += 15
    if ci(text, "decision summary"): score += 15
    return score


def score_humanization(content, text):
    score = 0
    if ci(text, "realistically expect"): score += 15
    if ci(text, "not ideal if"): score += 15
    if ci(text, "common mistakes") or ci(text, "common mistake"): score += 15
    if ci(text, "troubleshooting"): score += 15
    if ci(text, "when to seek"): score += 15
    if ci(text, "your dog") or ci(text, "your cat") or ci(text, "your puppy"): score += 10
    ai_phrases = ["designed to", "it's important to note", "comprehensive guide"]
    ai_count = sum(ci_count(text, p) for p in ai_phrases)
    ai_score = max(0, 15 - (ai_count * 5))
    score += ai_score
    return score


def score_conversion(content, text):
    score = 0
    if ci(text, "good choice if") or ci(text, "not ideal if"): score += 20
    if ci(text, "suitability"): score += 15
    if ci(text, "decision summary"): score += 15
    if "<table" in content.lower(): score += 15
    if ci(text, "best for"): score += 15
    if ci(text, "beginner"): score += 10
    if ci(text, "budget") or ci(text, "premium"): score += 10
    return score


def score_comparison(content, text):
    score = 0
    has_table = "<table" in content.lower()
    if has_table: score += 25
    row_count = len(re.findall(r'<tr', content, re.IGNORECASE))
    if row_count >= 5: score += 15
    if has_table and ci(content, "best for"): score += 20
    if has_table and (ci(content, "suitability") or ci(content, "suitable") or ci(content, "ideal for")): score += 15
    headers = re.findall(r'<th[^>]*>(.*?)</th>', content, re.IGNORECASE | re.DOTALL)
    if len(headers) >= 3: score += 15
    if has_table and "<thead" in content.lower(): score += 10
    return score


def score_trust(content, text):
    score = 0
    if ci(text, "trust") and (ci(text, "editorial") or ci(text, "transparency")): score += 10
    uk_authorities = ["rspca", "pdsa", "bva", "kennel club", "blue cross", "cats protection", "rcvs"]
    if any(ci(text, auth) for auth in uk_authorities): score += 15
    if ci(text, "why we reference these sources"): score += 15
    if ci(text, "how we evaluated"): score += 15
    if ci(text, "ai") and (ci(text, "transparency") or ci(text, "disclosure") or ci(text, "assisted")): score += 10
    if ci(text, "editorial process") or ci(text, "editorial policy"): score += 10
    if ci(text, "corrections") or ci(text, "correction policy"): score += 10
    if ci(text, "about this guide"): score += 10
    if ci(text, "affiliate") or ci(text, "commission"): score += 5
    return score


def score_citation(content, text):
    score = 0
    if ci(text, "at a glance"): score += 15
    if ci(text, "key takeaways") or ci(text, "key takeaway"): score += 15
    if ci(text, "decision summary"): score += 15
    if ci(text, "frequently asked") or ci(text, "faq") or ci(text, "common questions"): score += 15
    if ci(text, "sources") or ci(text, "references") or ci(text, "bibliography"): score += 15
    if ci(text, "glossary") or ci(text, "terminology"): score += 10
    if "<table" in content.lower(): score += 15
    return score


def score_practical(content, text):
    score = 0
    if ci(text, "troubleshooting"): score += 15
    if ci(text, "when to seek"): score += 15
    if ci(text, "warning sign") or ci(text, "red flag"): score += 10
    if ci(text, "common mistakes") or ci(text, "common mistake"): score += 15
    if ci(text, "what to realistically expect") or ci(text, "realistically expect"): score += 15
    if ci(text, "routine") or ci(text, "schedule") or ci(text, "checklist"): score += 10
    if ci(text, "good choice if") or ci(text, "not ideal if"): score += 10
    if ci(text, "beginner"): score += 10
    return score


def fetch_posts_search(search_term, count=10):
    """Fetch posts via search."""
    encoded = urllib.parse.quote(search_term)
    url = f"{WP_BASE}/posts?search={encoded}&per_page={count}&status=publish&_fields=id,title,content,link"
    data = api_call(url)
    if not data or not isinstance(data, list):
        return []
    return data


def fetch_all_posts_paginated(page=1, per_page=50):
    """Fetch all posts paginated."""
    url = f"{WP_BASE}/posts?per_page={per_page}&page={page}&status=publish&_fields=id,title,content,link&orderby=date&order=desc"
    data = api_call(url)
    if not data or not isinstance(data, list):
        return []
    return data


def classify_post_to_cluster(title, text):
    """Classify a post to its best-fitting cluster based on content."""
    title_lower = title.lower()
    text_lower = text.lower()
    combined = title_lower + " " + text_lower[:500]

    scores = {}
    scores["Dog Toys"] = sum(1 for t in ["dog toy", "chew toy", "puzzle toy", "tug toy", "fetch", "enrichment toy", "play toy"] if t in combined)
    scores["Dog Food"] = sum(1 for t in ["dog food", "feeding", "nutrition", "kibble", "raw food", "diet", "meal", "eating"] if t in combined)
    scores["Dog Health"] = sum(1 for t in ["dog health", "veterinary", "vet visit", "illness", "disease", "symptoms", "medication", "health check"] if t in combined)
    scores["Dog Training"] = sum(1 for t in ["training", "obedience", "behaviour", "recall", "command", "positive reinforcement", "leash"] if t in combined)
    scores["Cat Toys"] = sum(1 for t in ["cat toy", "cat play", "feather", "laser", "interactive cat"] if t in combined)
    scores["Cat Supplies"] = sum(1 for t in ["cat", "feline", "kitten", "litter", "scratching", "indoor cat"] if t in combined)
    scores["Dog Grooming"] = sum(1 for t in ["grooming", "bathing", "coat", "nail", "brushing", "shedding", "fur"] if t in combined)
    scores["Dog Harnesses"] = sum(1 for t in ["harness", "lead", "collar", "walking equipment", "no-pull"] if t in combined)
    scores["Dog Beds"] = sum(1 for t in ["bed", "sleeping", "crate", "den", "resting", "orthopedic"] if t in combined)
    scores["Puppy Care"] = sum(1 for t in ["puppy", "puppies", "young dog", "puppy care", "new puppy", "whelp"] if t in combined)

    # Prefer dog-specific clusters if "dog" is present
    if "cat" in combined and "dog" not in combined:
        # Boost cat clusters
        scores["Cat Toys"] += 2
        scores["Cat Supplies"] += 2

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return None  # Can't classify
    return best


def main():
    print("=" * 70)
    print("Phase 10AK Full Telemetry Re-Score v2 - PetHub Online")
    print("=" * 70)

    # First, gather a large pool of posts
    print("\nStep 1: Building post pool...")

    all_posts = {}  # id -> post dict

    # Fetch recent pages of posts
    for page in range(1, 8):
        print(f"  Fetching page {page}...")
        posts = fetch_all_posts_paginated(page=page, per_page=50)
        for p in posts:
            pid = p.get("id")
            if pid:
                all_posts[pid] = p
        time.sleep(0.3)
        if len(posts) < 50:
            break

    # Also search by cluster terms
    for cluster, terms in CLUSTER_SEARCHES.items():
        for term in terms[:3]:  # First 3 terms per cluster
            results = fetch_posts_search(term, count=10)
            for p in results:
                pid = p.get("id")
                if pid and pid not in all_posts:
                    all_posts[pid] = p
            time.sleep(0.3)

    print(f"  Total unique posts in pool: {len(all_posts)}")

    # Step 2: Classify posts into clusters
    print("\nStep 2: Classifying posts into clusters...")
    cluster_posts = defaultdict(list)

    for pid, post in all_posts.items():
        title_raw = post.get("title", {}).get("rendered", "Untitled")
        title = strip_html(title_raw)
        content_raw = post.get("content", {}).get("rendered", "")
        text = strip_html(content_raw)

        cluster = classify_post_to_cluster(title, text)
        if cluster:
            cluster_posts[cluster].append(post)

    for cl in CLUSTERS:
        print(f"  {cl}: {len(cluster_posts[cl])} posts")

    # Step 3: Score 5 posts per cluster
    print("\nStep 3: Scoring posts...")
    all_scores = []
    cluster_score_agg = defaultdict(lambda: defaultdict(list))
    dimension_totals = defaultdict(list)
    seen_ids = set()

    dims = ["E-E-A-T Depth", "Humanization", "Conversion", "Comparison Quality",
            "Trust Intensity", "Citation Readiness", "Practical Usefulness", "Overall Authority"]

    for cluster in CLUSTERS:
        posts = cluster_posts[cluster]
        print(f"\n--- Cluster: {cluster} ({len(posts)} available) ---")

        scored = 0
        for post in posts:
            if scored >= POSTS_PER_CLUSTER:
                break

            post_id = post.get("id")
            if post_id in seen_ids:
                continue
            seen_ids.add(post_id)

            title_raw = post.get("title", {}).get("rendered", "Untitled")
            title = strip_html(title_raw)
            content_raw = post.get("content", {}).get("rendered", "")
            text = strip_html(content_raw)
            link = post.get("link", "")

            wc = word_count(text)
            il = count_internal_links(content_raw)

            eeat = score_eeat(content_raw, text)
            human = score_humanization(content_raw, text)
            conv = score_conversion(content_raw, text)
            comp = score_comparison(content_raw, text)
            trust = score_trust(content_raw, text)
            cite = score_citation(content_raw, text)
            prac = score_practical(content_raw, text)
            overall = round((eeat + human + conv + comp + trust + cite + prac) / 7, 1)

            if wc > 2000 and il > 3:
                crawl_priority = "High"
            elif wc > 1000 and il > 1:
                crawl_priority = "Medium"
            else:
                crawl_priority = "Low"

            row = {
                "Post ID": post_id,
                "Title": title[:80],
                "Cluster": cluster,
                "URL": link,
                "Word Count": wc,
                "Internal Links": il,
                "Crawl Priority": crawl_priority,
                "E-E-A-T Depth": eeat,
                "Humanization": human,
                "Conversion": conv,
                "Comparison Quality": comp,
                "Trust Intensity": trust,
                "Citation Readiness": cite,
                "Practical Usefulness": prac,
                "Overall Authority": overall,
            }
            all_scores.append(row)

            for dim in dims:
                cluster_score_agg[cluster][dim].append(row[dim])
                dimension_totals[dim].append(row[dim])

            print(f"  [{post_id}] {title[:55]}... | WC={wc} IL={il} | EEAT={eeat} HUM={human} CONV={conv} COMP={comp} TRUST={trust} CITE={cite} PRAC={prac} OA={overall}")
            scored += 1

        if scored < POSTS_PER_CLUSTER:
            print(f"  [NOTE] Only {scored} unique posts scored for {cluster}")

    # --- Write full_telemetry_scores.csv ---
    csv_path = f"{DATA_DIR}/full_telemetry_scores.csv"
    fieldnames = ["Post ID", "Title", "Cluster", "URL", "Word Count", "Internal Links",
                  "Crawl Priority", "E-E-A-T Depth", "Humanization", "Conversion",
                  "Comparison Quality", "Trust Intensity", "Citation Readiness",
                  "Practical Usefulness", "Overall Authority"]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_scores)
    print(f"\n[OK] Wrote {csv_path} ({len(all_scores)} posts)")

    # --- Write cluster_dashboard.csv ---
    cluster_csv = f"{DATA_DIR}/cluster_dashboard.csv"
    with open(cluster_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Cluster", "Posts"] + dims)
        for cl in CLUSTERS:
            if cl in cluster_score_agg:
                n = len(cluster_score_agg[cl].get("Overall Authority", []))
                row = [cl, n]
                for d in dims:
                    vals = cluster_score_agg[cl].get(d, [])
                    avg = round(sum(vals) / len(vals), 1) if vals else 0
                    row.append(avg)
                writer.writerow(row)
            else:
                writer.writerow([cl, 0] + [0] * len(dims))
    print(f"[OK] Wrote {cluster_csv}")

    # --- Write dimension_summary.csv ---
    dim_csv = f"{DATA_DIR}/dimension_summary.csv"
    with open(dim_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Dimension", "10AK Average", "10AI Baseline", "10AJ Baseline",
                         "Delta vs 10AI", "Delta vs 10AJ"])
        for d in dims:
            vals = dimension_totals.get(d, [])
            avg = round(sum(vals) / len(vals), 1) if vals else 0
            b_ai = BASELINES_10AI.get(d, "N/A")
            b_aj = BASELINES_10AJ.get(d, "N/A")
            d_ai = round(avg - b_ai, 1) if isinstance(b_ai, (int, float)) else "N/A"
            d_aj = round(avg - b_aj, 1) if isinstance(b_aj, (int, float)) else "N/A"
            writer.writerow([d, avg, b_ai, b_aj, d_ai, d_aj])
    print(f"[OK] Wrote {dim_csv}")

    # --- Write before_after_all_phases.csv ---
    ba_csv = f"{DATA_DIR}/before_after_all_phases.csv"
    with open(ba_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Dimension", "Phase 10AI", "Phase 10AJ", "Phase 10AK", "Total Lift (10AI->10AK)"])
        for d in dims:
            vals = dimension_totals.get(d, [])
            ak = round(sum(vals) / len(vals), 1) if vals else 0
            ai = BASELINES_10AI.get(d, "N/A")
            aj = BASELINES_10AJ.get(d, "N/A")
            lift = round(ak - ai, 1) if isinstance(ai, (int, float)) else "N/A"
            writer.writerow([d, ai, aj, ak, lift])
    print(f"[OK] Wrote {ba_csv}")

    # --- Summary ---
    print("\n" + "=" * 70)
    print("PHASE 10AK TELEMETRY SUMMARY")
    print("=" * 70)
    print(f"Total posts scored: {len(all_scores)}")
    print(f"Clusters covered: {len([c for c in CLUSTERS if c in cluster_score_agg])}/{len(CLUSTERS)}")
    print()
    print(f"{'Dimension':<25} {'10AK Avg':>10} {'10AI Base':>10} {'10AJ Base':>10} {'vs 10AI':>10} {'vs 10AJ':>10}")
    print("-" * 75)
    for d in dims:
        vals = dimension_totals.get(d, [])
        avg = round(sum(vals) / len(vals), 1) if vals else 0
        b_ai = BASELINES_10AI.get(d, "-")
        b_aj = BASELINES_10AJ.get(d, "-")
        d_ai = f"{avg - b_ai:+.1f}" if isinstance(b_ai, (int, float)) else "-"
        d_aj = f"{avg - b_aj:+.1f}" if isinstance(b_aj, (int, float)) else "-"
        b_ai_s = f"{b_ai}" if isinstance(b_ai, (int, float)) else "-"
        b_aj_s = f"{b_aj}" if isinstance(b_aj, (int, float)) else "-"
        print(f"{d:<25} {avg:>10.1f} {b_ai_s:>10} {b_aj_s:>10} {d_ai:>10} {d_aj:>10}")

    print("\nCluster Breakdown:")
    print(f"{'Cluster':<20} {'Posts':>5} {'EEAT':>6} {'HUM':>6} {'CONV':>6} {'COMP':>6} {'TRUST':>6} {'CITE':>6} {'PRAC':>6} {'OA':>6}")
    print("-" * 85)
    for cl in CLUSTERS:
        if cl in cluster_score_agg:
            n = len(cluster_score_agg[cl].get("Overall Authority", []))
            avgs = []
            for d in dims:
                vals = cluster_score_agg[cl].get(d, [])
                avgs.append(round(sum(vals) / len(vals), 1) if vals else 0)
            print(f"{cl:<20} {n:>5} " + " ".join(f"{a:>6.1f}" for a in avgs))
        else:
            print(f"{cl:<20}     0 " + " ".join(f"{'N/A':>6}" for _ in dims))

    # Top/bottom posts
    print("\nTop 5 Posts by Overall Authority:")
    sorted_posts = sorted(all_scores, key=lambda x: x["Overall Authority"], reverse=True)
    for i, p in enumerate(sorted_posts[:5], 1):
        print(f"  {i}. [{p['Post ID']}] {p['Title'][:50]}... OA={p['Overall Authority']} ({p['Cluster']})")

    print("\nBottom 5 Posts by Overall Authority:")
    for i, p in enumerate(sorted_posts[-5:], 1):
        print(f"  {i}. [{p['Post ID']}] {p['Title'][:50]}... OA={p['Overall Authority']} ({p['Cluster']})")

    print("\n[DONE] Phase 10AK scoring complete.")


if __name__ == "__main__":
    main()
