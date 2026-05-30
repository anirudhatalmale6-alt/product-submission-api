#!/usr/bin/env python3
"""
Phase 12: Full Cluster Re-Score Engine
Scores every published post and aggregates by cluster:
- Trust link coverage
- FAQ/glossary/key-terms presence
- Comparison table presence
- Snippet readiness (question-format H2s, answer blocks)
- Quick-answer blocks
- Internal links (to hub, from hub)
- Sources/references section
- Overall authority density score
"""
import json, subprocess, time, csv, re, sys
from collections import defaultdict

WP_API = "https://pethubonline.com/wp-json/wp/v2/posts"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
SLEEP_GET = 2

CATEGORY_MAP = {
    1377: "Cat Supplies", 1459: "Cat Toys", 1413: "Indoor Cats",
    1376: "Dog Supplies", 1397: "Pet Care", 1401: "Dog Beds",
    1489: "Dog Care", 1467: "Dog Food", 1422: "Dog Harnesses",
    1450: "Dog Health", 1441: "Dog Toys", 1442: "Puppy Care",
    1474: "Training Supplies", 1: "Uncategorized"
}

TRUST_URLS = [
    "how-we-research-pet-products",
    "our-editorial-process",
    "corrections-and-updates-policy",
    "affiliate-disclosure"
]


def fetch_all_posts():
    posts = []
    page = 1
    while True:
        time.sleep(SLEEP_GET)
        url = f"{WP_API}?per_page=100&page={page}&context=edit&_fields=id,title,content,categories&status=publish"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True, timeout=60
        )
        try:
            batch = json.loads(result.stdout)
        except json.JSONDecodeError:
            break
        if not isinstance(batch, list) or len(batch) == 0:
            break
        posts.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return posts


def score_post(post):
    content = post.get("content", {}).get("raw", "")
    title = post.get("title", {}).get("raw", "")
    content_lower = content.lower()
    cats = post.get("categories", [])
    cluster = "Unknown"
    for c in cats:
        if c in CATEGORY_MAP:
            cluster = CATEGORY_MAP[c]
            break

    scores = {}

    # Trust links (4 links = 100%)
    trust_count = sum(1 for url in TRUST_URLS if url in content_lower)
    scores["trust_links"] = min(trust_count / 4 * 100, 100)

    # FAQ section
    scores["has_faq"] = 100 if ("Frequently Asked Questions" in content or "FAQ" in content) else 0

    # Glossary/Key Terms
    scores["has_glossary"] = 100 if ("Key Terms" in content or "Glossary" in content or
                                      "At a Glance" in content or "Terminology" in title) else 0

    # Comparison table
    scores["has_comparison"] = 100 if ("wp-block-table" in content and "Compared:" in content) else (
        50 if "wp-block-table" in content else 0)

    # Question-format H2s (snippet ready)
    h2_matches = re.findall(r'<h2[^>]*>([^<]+)</h2>', content)
    question_h2s = sum(1 for h in h2_matches if h.strip().endswith("?"))
    total_h2s = len(h2_matches)
    scores["snippet_h2_pct"] = (question_h2s / total_h2s * 100) if total_h2s > 0 else 0
    scores["total_h2s"] = total_h2s
    scores["question_h2s"] = question_h2s

    # Quick-answer block
    scores["has_quick_answer"] = 100 if ("quick-answer" in content_lower or
                                          "wp-block-group" in content and "answer" in content_lower[:1000]) else 0

    # Sources and References
    scores["has_sources"] = 100 if "Sources and References" in content else 0

    # Internal links count
    internal_links = len(re.findall(r'href="https?://pethubonline\.com/', content))
    scores["internal_links"] = min(internal_links, 20)

    # Word count (rough)
    text_only = re.sub(r'<[^>]+>', '', content)
    word_count = len(text_only.split())
    scores["word_count"] = word_count

    # Overall authority density (weighted average)
    authority_density = (
        scores["trust_links"] * 0.20 +
        scores["has_faq"] * 0.15 +
        scores["has_glossary"] * 0.10 +
        scores["has_comparison"] * 0.15 +
        scores["snippet_h2_pct"] * 0.15 +
        scores["has_sources"] * 0.10 +
        min(scores["internal_links"] / 10 * 100, 100) * 0.10 +
        scores["has_quick_answer"] * 0.05
    )
    scores["authority_density"] = round(authority_density, 1)

    return {
        "post_id": post["id"],
        "title": title,
        "cluster": cluster,
        **{k: (round(v, 1) if isinstance(v, float) else v) for k, v in scores.items()}
    }


def main():
    print("=" * 70)
    print("Phase 12: Full Cluster Re-Score Engine")
    print("=" * 70)

    print("\nFetching all published posts...")
    posts = fetch_all_posts()
    print(f"Total: {len(posts)} posts\n")

    # Score each post
    results = []
    for p in posts:
        results.append(score_post(p))

    # Aggregate by cluster
    cluster_agg = defaultdict(lambda: {
        "posts": 0, "trust_avg": 0, "faq_pct": 0, "glossary_pct": 0,
        "comparison_pct": 0, "snippet_pct": 0, "sources_pct": 0,
        "avg_internal_links": 0, "avg_word_count": 0, "authority_avg": 0,
        "quick_answer_pct": 0
    })

    for r in results:
        c = r["cluster"]
        cluster_agg[c]["posts"] += 1
        cluster_agg[c]["trust_avg"] += r["trust_links"]
        cluster_agg[c]["faq_pct"] += (1 if r["has_faq"] == 100 else 0)
        cluster_agg[c]["glossary_pct"] += (1 if r["has_glossary"] == 100 else 0)
        cluster_agg[c]["comparison_pct"] += (1 if r["has_comparison"] >= 50 else 0)
        cluster_agg[c]["snippet_pct"] += r["snippet_h2_pct"]
        cluster_agg[c]["sources_pct"] += (1 if r["has_sources"] == 100 else 0)
        cluster_agg[c]["avg_internal_links"] += r["internal_links"]
        cluster_agg[c]["avg_word_count"] += r["word_count"]
        cluster_agg[c]["authority_avg"] += r["authority_density"]
        cluster_agg[c]["quick_answer_pct"] += (1 if r["has_quick_answer"] == 100 else 0)

    # Compute averages
    cluster_summary = []
    for cluster, agg in sorted(cluster_agg.items()):
        n = agg["posts"]
        cluster_summary.append({
            "cluster": cluster,
            "posts": n,
            "trust_coverage": round(agg["trust_avg"] / n, 1),
            "faq_coverage": round(agg["faq_pct"] / n * 100, 1),
            "glossary_coverage": round(agg["glossary_pct"] / n * 100, 1),
            "comparison_coverage": round(agg["comparison_pct"] / n * 100, 1),
            "snippet_readiness": round(agg["snippet_pct"] / n, 1),
            "sources_coverage": round(agg["sources_pct"] / n * 100, 1),
            "quick_answer_coverage": round(agg["quick_answer_pct"] / n * 100, 1),
            "avg_internal_links": round(agg["avg_internal_links"] / n, 1),
            "avg_word_count": round(agg["avg_word_count"] / n),
            "authority_density": round(agg["authority_avg"] / n, 1),
        })

    # Print summary
    print("CLUSTER AUTHORITY DENSITY SCORECARD")
    print("=" * 90)
    print(f"{'Cluster':20s} {'Posts':>5} {'Trust':>6} {'FAQ':>5} {'Gloss':>6} {'Comp':>5} {'Snip':>5} {'Src':>5} {'QA':>5} {'Links':>5} {'Words':>6} {'SCORE':>6}")
    print("-" * 90)
    total_score = 0
    for cs in cluster_summary:
        print(f"{cs['cluster']:20s} {cs['posts']:5d} {cs['trust_coverage']:5.0f}% {cs['faq_coverage']:4.0f}% {cs['glossary_coverage']:5.0f}% {cs['comparison_coverage']:4.0f}% {cs['snippet_readiness']:4.0f}% {cs['sources_coverage']:4.0f}% {cs['quick_answer_coverage']:4.0f}% {cs['avg_internal_links']:5.1f} {cs['avg_word_count']:6d} {cs['authority_density']:5.1f}")
        total_score += cs['authority_density'] * cs['posts']

    overall = total_score / len(results) if results else 0
    print("-" * 90)
    print(f"{'OVERALL':20s} {len(results):5d} {'':>6} {'':>5} {'':>6} {'':>5} {'':>5} {'':>5} {'':>5} {'':>5} {'':>6} {overall:5.1f}")
    print("=" * 90)

    # Write per-post CSV
    post_csv = "/var/lib/freelancer/projects/40416335/phase11_data/authority_density_posts.csv"
    fields = ["post_id", "title", "cluster", "trust_links", "has_faq", "has_glossary",
              "has_comparison", "snippet_h2_pct", "total_h2s", "question_h2s",
              "has_quick_answer", "has_sources", "internal_links", "word_count", "authority_density"]
    with open(post_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in results:
            writer.writerow({k: r[k] for k in fields})
    print(f"\nWrote: {post_csv} ({len(results)} rows)")

    # Write cluster summary CSV
    summary_csv = "/var/lib/freelancer/projects/40416335/phase11_data/authority_density_clusters.csv"
    with open(summary_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(cluster_summary[0].keys()))
        writer.writeheader()
        writer.writerows(cluster_summary)
    print(f"Wrote: {summary_csv} ({len(cluster_summary)} rows)")

    print(f"\nOVERALL SITE AUTHORITY DENSITY: {overall:.1f}/100")


if __name__ == "__main__":
    main()
