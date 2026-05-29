#!/usr/bin/env python3
"""
Phase 10AK Full Telemetry Re-Score for PetHub Online
Scores 50 posts (5 per cluster) across 8 dimensions.
"""

import subprocess
import json
import csv
import re
import sys
import time
import html
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

# Search terms for each cluster
CLUSTER_SEARCH = {
    "Dog Toys": "dog toy",
    "Dog Food": "dog food",
    "Dog Health": "dog health",
    "Dog Training": "dog training",
    "Cat Toys": "cat toy",
    "Cat Supplies": "cat supplies",
    "Dog Grooming": "dog grooming",
    "Dog Harnesses": "dog harness",
    "Dog Beds": "dog bed",
    "Puppy Care": "puppy",
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
        print(f"  [WARN] curl error for {url}: {result.stderr[:200]}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  [WARN] JSON decode error for {url}: {result.stdout[:200]}")
        return None


def strip_html(raw_html):
    """Strip HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', ' ', raw_html)
    text = html.unescape(text)
    return text


def count_internal_links(content):
    """Count links to pethubonline.com in content."""
    links = re.findall(r'href=["\']([^"\']+)["\']', content, re.IGNORECASE)
    internal = [l for l in links if 'pethubonline.com' in l or l.startswith('/')]
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
    """E-E-A-T Depth Score (0-100)."""
    score = 0
    # "About this guide" / "About This Guide" (10pts)
    if ci(text, "about this guide"):
        score += 10
    # "How we evaluated" / "How We Evaluated" (15pts)
    if ci(text, "how we evaluated"):
        score += 15
    # "Why this matters" / "Why This Matters" (10pts)
    if ci(text, "why this matters"):
        score += 10
    # "What we considered" / "What We Considered" (10pts)
    if ci(text, "what we considered"):
        score += 10
    # "What to realistically expect" (15pts)
    if ci(text, "what to realistically expect"):
        score += 15
    # "Is this right for you" / "Good choice if" (10pts)
    if ci(text, "is this right for you") or ci(text, "good choice if"):
        score += 10
    # "Why we reference these sources" (15pts)
    if ci(text, "why we reference these sources"):
        score += 15
    # "Decision summary" (15pts)
    if ci(text, "decision summary"):
        score += 15
    return score


def score_humanization(content, text):
    """Humanization Score (0-100)."""
    score = 0
    # "realistically expect" language (15pts)
    if ci(text, "realistically expect"):
        score += 15
    # "not ideal if" / honest caveats (15pts)
    if ci(text, "not ideal if"):
        score += 15
    # "Common Mistakes" section (15pts)
    if ci(text, "common mistakes"):
        score += 15
    # "Troubleshooting" section (15pts)
    if ci(text, "troubleshooting"):
        score += 15
    # "When to seek" help section (15pts)
    if ci(text, "when to seek"):
        score += 15
    # "your dog"/"your cat"/"your puppy" (personal tone) (10pts)
    if ci(text, "your dog") or ci(text, "your cat") or ci(text, "your puppy"):
        score += 10
    # Low AI pattern count: 15pts base minus 5 per AI phrase found
    ai_phrases = ["designed to", "it's important to note", "comprehensive guide"]
    ai_count = sum(ci_count(text, p) for p in ai_phrases)
    ai_score = max(0, 15 - (ai_count * 5))
    score += ai_score
    return score


def score_conversion(content, text):
    """Conversion Score (0-100)."""
    score = 0
    # "Good choice if" / "Not ideal if" (20pts)
    if ci(text, "good choice if") or ci(text, "not ideal if"):
        score += 20
    # "Suitability" guide (15pts)
    if ci(text, "suitability"):
        score += 15
    # "Decision summary" (15pts)
    if ci(text, "decision summary"):
        score += 15
    # Comparison table present (15pts)
    if "<table" in content.lower():
        score += 15
    # "Best For" info (15pts)
    if ci(text, "best for"):
        score += 15
    # "beginner" recommendation (10pts)
    if ci(text, "beginner"):
        score += 10
    # "Budget" / "Premium" guidance (10pts)
    if ci(text, "budget") or ci(text, "premium"):
        score += 10
    return score


def score_comparison(content, text):
    """Comparison Quality Score (0-100)."""
    score = 0
    has_table = "<table" in content.lower()
    # Has comparison table (25pts)
    if has_table:
        score += 25
    # Table has 4+ rows (15pts)
    row_count = len(re.findall(r'<tr', content, re.IGNORECASE))
    if row_count >= 5:  # 4 data rows + 1 header
        score += 15
    # Table has "Best For" column (20pts)
    if has_table and ci(content, "best for"):
        score += 20
    # Table has suitability info (15pts)
    if has_table and (ci(content, "suitability") or ci(content, "suitable") or ci(content, "ideal for")):
        score += 15
    # Multiple comparison dimensions (15pts) - check for multiple th/td headers
    headers = re.findall(r'<th[^>]*>(.*?)</th>', content, re.IGNORECASE | re.DOTALL)
    if len(headers) >= 3:
        score += 15
    # Table uses proper HTML (10pts)
    if has_table and "<thead" in content.lower():
        score += 10
    return score


def score_trust(content, text):
    """Trust Intensity Score (0-100)."""
    score = 0
    # Trust footer present (10pts) - look for trust-related sections at end
    if ci(text, "trust") and (ci(text, "editorial") or ci(text, "transparency")):
        score += 10
    # UK authority links (RSPCA/PDSA/BVA etc) (15pts)
    uk_authorities = ["rspca", "pdsa", "bva", "kennel club", "blue cross", "cats protection", "rcvs"]
    if any(ci(text, auth) for auth in uk_authorities):
        score += 15
    # "Why we reference these sources" (15pts)
    if ci(text, "why we reference these sources"):
        score += 15
    # "How we evaluated" (15pts)
    if ci(text, "how we evaluated"):
        score += 15
    # AI transparency disclosure (10pts)
    if ci(text, "ai") and (ci(text, "transparency") or ci(text, "disclosure") or ci(text, "assisted")):
        score += 10
    # Editorial process link (10pts)
    if ci(text, "editorial process") or ci(text, "editorial policy"):
        score += 10
    # Corrections policy link (10pts)
    if ci(text, "corrections") or ci(text, "correction policy"):
        score += 10
    # "About this guide" (10pts)
    if ci(text, "about this guide"):
        score += 10
    # Affiliate disclosure (5pts)
    if ci(text, "affiliate") or ci(text, "commission"):
        score += 5
    return score


def score_citation(content, text):
    """Citation Readiness Score (0-100)."""
    score = 0
    # "At a Glance" box (15pts)
    if ci(text, "at a glance"):
        score += 15
    # "Key Takeaways" (15pts)
    if ci(text, "key takeaways") or ci(text, "key takeaway"):
        score += 15
    # "Decision Summary" (15pts)
    if ci(text, "decision summary"):
        score += 15
    # FAQ section (15pts)
    if ci(text, "frequently asked") or ci(text, "faq") or ci(text, "common questions"):
        score += 15
    # Source references (15pts)
    if ci(text, "sources") or ci(text, "references") or ci(text, "bibliography"):
        score += 15
    # Glossary terms/links (10pts)
    if ci(text, "glossary") or ci(text, "terminology"):
        score += 10
    # Comparison table (15pts)
    if "<table" in content.lower():
        score += 15
    return score


def score_practical(content, text):
    """Practical Usefulness Score (0-100)."""
    score = 0
    # "Troubleshooting" section (15pts)
    if ci(text, "troubleshooting"):
        score += 15
    # "When to seek" help (15pts)
    if ci(text, "when to seek"):
        score += 15
    # "Warning signs" (10pts)
    if ci(text, "warning sign") or ci(text, "red flag"):
        score += 10
    # "Common Mistakes" (15pts)
    if ci(text, "common mistakes") or ci(text, "common mistake"):
        score += 15
    # "What to realistically expect" (15pts)
    if ci(text, "what to realistically expect") or ci(text, "realistically expect"):
        score += 15
    # "Routine"/"schedule"/"checklist" (10pts)
    if ci(text, "routine") or ci(text, "schedule") or ci(text, "checklist"):
        score += 10
    # "Good choice if / Not ideal if" (10pts)
    if ci(text, "good choice if") or ci(text, "not ideal if"):
        score += 10
    # "beginner" guidance (10pts)
    if ci(text, "beginner"):
        score += 10
    return score


def fetch_cluster_posts(cluster_name, search_term, count=5):
    """Fetch posts for a cluster via search."""
    url = f"{WP_BASE}/posts?search={search_term.replace(' ', '+')}&per_page={count}&status=publish&_fields=id,title,content,link"
    data = api_call(url)
    if not data or not isinstance(data, list):
        print(f"  [WARN] No posts found for cluster '{cluster_name}' with search '{search_term}'")
        return []
    return data[:count]


def main():
    print("=" * 70)
    print("Phase 10AK Full Telemetry Re-Score - PetHub Online")
    print("=" * 70)

    all_scores = []
    cluster_scores = defaultdict(lambda: defaultdict(list))
    dimension_totals = defaultdict(list)

    seen_ids = set()

    for cluster in CLUSTERS:
        search_term = CLUSTER_SEARCH[cluster]
        print(f"\n--- Cluster: {cluster} (search: '{search_term}') ---")
        posts = fetch_cluster_posts(cluster, search_term)

        if not posts:
            print(f"  No posts found, trying broader search...")
            # Try just the first word
            broader = search_term.split()[0]
            posts = fetch_cluster_posts(cluster, broader)

        fetched = 0
        for post in posts:
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

            # Score all dimensions
            eeat = score_eeat(content_raw, text)
            human = score_humanization(content_raw, text)
            conv = score_conversion(content_raw, text)
            comp = score_comparison(content_raw, text)
            trust = score_trust(content_raw, text)
            cite = score_citation(content_raw, text)
            prac = score_practical(content_raw, text)

            # Overall = average of 7
            overall = round((eeat + human + conv + comp + trust + cite + prac) / 7, 1)

            # Crawl priority estimate
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

            # Track for cluster/dimension aggregation
            for dim in ["E-E-A-T Depth", "Humanization", "Conversion", "Comparison Quality",
                        "Trust Intensity", "Citation Readiness", "Practical Usefulness", "Overall Authority"]:
                cluster_scores[cluster][dim].append(row[dim])
                dimension_totals[dim].append(row[dim])

            print(f"  [{post_id}] {title[:60]}... | WC={wc} IL={il} | EEAT={eeat} HUM={human} CONV={conv} COMP={comp} TRUST={trust} CITE={cite} PRAC={prac} OA={overall}")
            fetched += 1
            if fetched >= POSTS_PER_CLUSTER:
                break

            # Brief pause to avoid rate limits
            time.sleep(0.5)

        if fetched < POSTS_PER_CLUSTER:
            print(f"  [NOTE] Only {fetched} unique posts scored for {cluster}")

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
    dims = ["E-E-A-T Depth", "Humanization", "Conversion", "Comparison Quality",
            "Trust Intensity", "Citation Readiness", "Practical Usefulness", "Overall Authority"]
    with open(cluster_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Cluster", "Posts"] + dims)
        for cl in CLUSTERS:
            if cl in cluster_scores:
                n = len(cluster_scores[cl].get("Overall Authority", []))
                row = [cl, n]
                for d in dims:
                    vals = cluster_scores[cl].get(d, [])
                    avg = round(sum(vals) / len(vals), 1) if vals else 0
                    row.append(avg)
                writer.writerow(row)
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
    print(f"Clusters covered: {len(cluster_scores)}")
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
        if cl in cluster_scores:
            n = len(cluster_scores[cl].get("Overall Authority", []))
            avgs = []
            for d in dims:
                vals = cluster_scores[cl].get(d, [])
                avgs.append(round(sum(vals) / len(vals), 1) if vals else 0)
            print(f"{cl:<20} {n:>5} " + " ".join(f"{a:>6.1f}" for a in avgs))

    print("\n[DONE] Phase 10AK scoring complete.")


if __name__ == "__main__":
    main()
