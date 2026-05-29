#!/usr/bin/env python3
"""
Phase 10AG Telemetry & Scoring CSVs Generator
Fetches all published posts from pethubonline.com and generates 10 CSV reports
covering E-E-A-T depth, humanization, comparison usefulness, buyer-intent,
practical guidance, citation readiness, brand authority, cluster analysis,
conversion readiness, and AI answer ownership.
"""

import subprocess
import json
import csv
import re
import os
import sys
from collections import defaultdict

# ─── Configuration ───────────────────────────────────────────────────────────
WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase10ag_data"

# ─── Cluster classification rules ────────────────────────────────────────────
CLUSTER_RULES = [
    ("Cat Toys", [
        "cat toy", "catnip", "interactive cat", "cat scratching", "cat tree",
        "cat enrichment", "cat toy rotation", "cat toy safety"
    ]),
    ("Cat Supplies", [
        "cat litter", "cat bed", "cat supplies", "cat collar", "cat harness",
        "heated cat", "cat radiator", "cat window"
    ]),
    ("Dog Toys", [
        "dog toy", "enrichment", "fetch", "tug", "chew", "puzzle", "boredom",
        "play style", "overstimulation", "pet toy safety"
    ]),
    ("Dog Beds", [
        "dog bed", "orthopaedic", "cooling bed", "puppy bed"
    ]),
    ("Dog Food", [
        "dog food", "nutrition", "feeding", "dry vs wet", "puppy food"
    ]),
    ("Dog Grooming", [
        "grooming", "brush", "shampoo", "nail clip", "cat brush", "cat shampoo",
        "cat nail", "cat grooming"
    ]),
    ("Dog Harnesses", [
        "harness", "collar", "lead", "no-pull", "puppy collar", "cat harness",
        "cat collar"
    ]),
    ("Dog Health", [
        "health", "flea", "dental", "joint supplement"
    ]),
    ("Dog Training", [
        "training", "behaviour", "socialisation", "treat", "scratching behaviour"
    ]),
    ("Educational", [
        "glossary", "explained", "guide"
    ]),
    ("Indoor Cats", [
        "indoor cat"
    ]),
    ("Puppy Care", [
        "puppy"
    ]),
    ("Dog Care", [
        "seasonal dog", "seasonal pet"
    ]),
]


def fetch_all_posts():
    """Fetch all published posts using curl with pagination."""
    all_posts = []
    page = 1
    while True:
        url = f"{WP_API}/posts?per_page=100&page={page}&status=publish&_fields=id,title,content,link"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"  curl error on page {page}: {result.stderr}")
            break
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"  JSON decode error on page {page}: {result.stdout[:200]}")
            break
        if isinstance(data, dict) and data.get("code"):
            # e.g. {"code":"rest_post_invalid_page_number",...}
            break
        if not isinstance(data, list) or len(data) == 0:
            break
        all_posts.extend(data)
        print(f"  Fetched page {page}: {len(data)} posts (total: {len(all_posts)})")
        if len(data) < 100:
            break
        page += 1
    return all_posts


def classify_cluster(title):
    """Classify a post into a cluster based on title keywords."""
    title_lower = title.lower()
    for cluster_name, keywords in CLUSTER_RULES:
        for kw in keywords:
            if kw in title_lower:
                return cluster_name
    return "Uncategorised"


def analyze_post(post):
    """Analyze a single post for all content signals."""
    title = post.get("title", {}).get("rendered", "") or ""
    content = post.get("content", {}).get("rendered", "") or ""
    content_lower = content.lower()
    title_lower = title.lower()

    # ─── Boolean content signals ─────────────────────────────────────────
    has_about_guide = "about this guide" in content_lower
    has_common_mistakes = "common mistakes" in content_lower
    has_what_to_expect = "what to expect" in content_lower

    # Suitability: "Quick Suitability" or "Best for" section
    has_suitability_guide = (
        "quick suitability" in content_lower or
        bool(re.search(r'best\s+for\b', content_lower))
    )

    # Pros/Cons: ("Advantages" AND "Things to Watch") OR "Key Considerations"
    has_pros_cons = (
        ("advantages" in content_lower and "things to watch" in content_lower) or
        "key considerations" in content_lower
    )

    # Routine checklist: "Quick Routine" or ("Daily:" AND "Weekly:")
    has_routine_checklist = (
        "quick routine" in content_lower or
        ("daily:" in content_lower and "weekly:" in content_lower)
    )

    # Comparison table: wp:table block or <table in rendered HTML
    has_comparison_table = "wp:table" in content_lower or "<table" in content_lower

    # FAQ
    has_faq = (
        "faq" in content_lower or
        "frequently asked" in content_lower
    )

    # Quick Answer
    has_quick_answer = "quick answer" in content_lower

    # Sources and Further Reading
    has_sources = "sources and further reading" in content_lower

    # Trust footer: "Our Editorial Standards"
    has_trust_footer = "our editorial standards" in content_lower

    # Editorial link
    has_editorial_link = "/our-editorial-process/" in content_lower

    # Methodology link
    has_methodology_link = "/how-we-research-pet-products/" in content_lower

    # Corrections link
    has_corrections_link = "/corrections-and-updates-policy/" in content_lower

    # Affiliate disclosure link
    has_affiliate_disclosure = "/affiliate-disclosure/" in content_lower

    # Practical tips (has_practical_tips used for humanization)
    # Check for practical tip patterns: "tip:", "pro tip", "practical tip", list items with actionable verbs
    has_practical_tips = bool(re.search(
        r'(practical\s+tip|pro\s+tip|our\s+tip|top\s+tip|quick\s+tip|handy\s+tip)',
        content_lower
    ))

    # ─── Counts ──────────────────────────────────────────────────────────

    # Internal links: hrefs containing pethubonline.com
    internal_links = re.findall(r'href=["\']([^"\']*pethubonline\.com[^"\']*)["\']', content, re.IGNORECASE)
    internal_link_count = len(internal_links)

    # External links: hrefs NOT containing pethubonline.com (but still http)
    all_links = re.findall(r'href=["\'](https?://[^"\']+)["\']', content, re.IGNORECASE)
    external_link_count = len([l for l in all_links if "pethubonline.com" not in l.lower()])

    # Word count (approximate from stripped content)
    text_only = re.sub(r'<[^>]+>', ' ', content)
    text_only = re.sub(r'\s+', ' ', text_only).strip()
    word_count = len(text_only.split()) if text_only else 0

    # Heading count (wp:heading blocks OR rendered <h2>-<h6> tags)
    heading_count = len(re.findall(r'wp:heading', content, re.IGNORECASE))
    if heading_count == 0:
        heading_count = len(re.findall(r'<h[2-6]\b', content, re.IGNORECASE))

    # List count (wp:list blocks OR rendered <ul>/<ol> tags)
    list_count = len(re.findall(r'wp:list\b', content, re.IGNORECASE))
    if list_count == 0:
        list_count = len(re.findall(r'<(?:ul|ol)\b', content, re.IGNORECASE))

    # Image count (wp:image blocks OR rendered <img> tags)
    image_count = len(re.findall(r'wp:image', content, re.IGNORECASE))
    if image_count == 0:
        image_count = len(re.findall(r'<img\b', content, re.IGNORECASE))

    cluster = classify_cluster(title)

    return {
        "id": post["id"],
        "title": title,
        "cluster": cluster,
        "has_about_guide": has_about_guide,
        "has_common_mistakes": has_common_mistakes,
        "has_what_to_expect": has_what_to_expect,
        "has_suitability_guide": has_suitability_guide,
        "has_pros_cons": has_pros_cons,
        "has_routine_checklist": has_routine_checklist,
        "has_comparison_table": has_comparison_table,
        "has_faq": has_faq,
        "has_quick_answer": has_quick_answer,
        "has_sources": has_sources,
        "has_trust_footer": has_trust_footer,
        "has_editorial_link": has_editorial_link,
        "has_methodology_link": has_methodology_link,
        "has_corrections_link": has_corrections_link,
        "has_affiliate_disclosure": has_affiliate_disclosure,
        "has_practical_tips": has_practical_tips,
        "internal_link_count": internal_link_count,
        "external_link_count": external_link_count,
        "word_count": word_count,
        "heading_count": heading_count,
        "list_count": list_count,
        "image_count": image_count,
    }


def bool_to_int(val):
    return 1 if val else 0


def compute_scores(a):
    """Compute all scoring dimensions from analyzed data."""
    b = bool_to_int

    # 1. E-E-A-T depth score (max 100)
    eeat = (
        b(a["has_about_guide"]) * 20 +
        b(a["has_editorial_link"]) * 15 +
        b(a["has_methodology_link"]) * 15 +
        b(a["has_corrections_link"]) * 10 +
        b(a["has_common_mistakes"]) * 20 +
        b(a["has_what_to_expect"]) * 20
    )

    # 2. Humanization score (max 100)
    humanization = (
        b(a["has_common_mistakes"]) * 25 +
        b(a["has_what_to_expect"]) * 25 +
        b(a["has_routine_checklist"]) * 25 +
        b(a["has_practical_tips"]) * 25
    )

    # 3. Comparison usefulness score (max 100)
    comparison = (
        b(a["has_comparison_table"]) * 40 +
        b(a["has_suitability_guide"]) * 30 +
        b(a["has_pros_cons"]) * 30
    )

    # 4. Buyer intent score (max 100)
    buyer_intent = (
        b(a["has_suitability_guide"]) * 30 +
        b(a["has_pros_cons"]) * 25 +
        b(a["has_routine_checklist"]) * 20 +
        b(a["has_comparison_table"]) * 25
    )

    # 5. Practical guidance score (max 100)
    # Weighted: mistakes(25) + what_to_expect(25) + routine(25) + lists(25 scaled)
    list_score = min(25, a["list_count"] * 3)  # ~8+ lists = full marks
    practical = (
        b(a["has_common_mistakes"]) * 25 +
        b(a["has_what_to_expect"]) * 25 +
        b(a["has_routine_checklist"]) * 25 +
        list_score
    )

    # 6. Citation readiness score (max 100)
    # sources(25) + external_links(20 scaled) + trust_footer(15) + faq(20) + quick_answer(20)
    ext_link_score = min(20, a["external_link_count"] * 4)  # 5+ external links = full
    citation = (
        b(a["has_sources"]) * 25 +
        ext_link_score +
        b(a["has_trust_footer"]) * 15 +
        b(a["has_faq"]) * 20 +
        b(a["has_quick_answer"]) * 20
    )

    # 9. Conversion readiness score (max 100)
    # suitability(25) + comparison_table(25) + pros_cons(20) + routine(15) + internal_links(15 scaled)
    int_link_score = min(15, a["internal_link_count"] * 2)  # 7-8+ internal links = full
    conversion = (
        b(a["has_suitability_guide"]) * 25 +
        b(a["has_comparison_table"]) * 25 +
        b(a["has_pros_cons"]) * 20 +
        b(a["has_routine_checklist"]) * 15 +
        int_link_score
    )

    # 10. AI answer ownership score (max 100)
    # faq(20) + quick_answer(20) + comparison_table(15) + suitability(15) + headings(15 scaled) + lists(15 scaled)
    heading_score = min(15, a["heading_count"] * 1)  # 15+ headings = full
    list_ai_score = min(15, a["list_count"] * 2)     # 7-8+ lists = full
    ai_ownership = (
        b(a["has_faq"]) * 20 +
        b(a["has_quick_answer"]) * 20 +
        b(a["has_comparison_table"]) * 15 +
        b(a["has_suitability_guide"]) * 15 +
        heading_score +
        list_ai_score
    )

    # 7. Brand authority total (average of 5 main dimensions)
    brand_authority = round((eeat + humanization + comparison + buyer_intent + citation) / 5, 1)

    return {
        "eeat_depth_score": eeat,
        "humanization_score": humanization,
        "comparison_usefulness_score": comparison,
        "buyer_intent_score": buyer_intent,
        "practical_guidance_score": practical,
        "citation_readiness_score": citation,
        "brand_authority_total": brand_authority,
        "conversion_readiness_score": conversion,
        "ai_answer_ownership_score": ai_ownership,
    }


def write_csv(filepath, rows, fieldnames):
    """Write a CSV file with given rows and fieldnames."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"  Written: {os.path.basename(filepath)} ({len(rows)} rows)")


def main():
    print("=" * 70)
    print("Phase 10AG Telemetry & Scoring CSV Generator")
    print("=" * 70)

    # Step 1: Fetch all published posts
    print("\n[1/3] Fetching all published posts...")
    posts = fetch_all_posts()
    print(f"  Total posts fetched: {len(posts)}")
    if not posts:
        print("ERROR: No posts fetched. Exiting.")
        sys.exit(1)

    # Step 2: Analyze all posts
    print("\n[2/3] Analyzing content signals...")
    analyzed = []
    for post in posts:
        a = analyze_post(post)
        s = compute_scores(a)
        analyzed.append({**a, **s})
    print(f"  Analyzed {len(analyzed)} posts")

    # Step 3: Generate all 10 CSVs
    print("\n[3/3] Generating CSV reports...")

    # --- CSV 1: E-E-A-T Depth Scores ---
    csv1_fields = [
        "id", "title", "cluster", "has_about_guide", "has_editorial_link",
        "has_methodology_link", "has_corrections_link", "has_common_mistakes",
        "has_what_to_expect", "eeat_depth_score"
    ]
    csv1_rows = [{k: (bool_to_int(v) if isinstance(v, bool) else v) for k, v in row.items() if k in csv1_fields} for row in analyzed]
    write_csv(os.path.join(OUTPUT_DIR, "eeat_depth_scores.csv"), csv1_rows, csv1_fields)

    # --- CSV 2: Humanization Scores ---
    csv2_fields = [
        "id", "title", "cluster", "has_common_mistakes", "has_what_to_expect",
        "has_routine_checklist", "has_practical_tips", "humanization_score"
    ]
    csv2_rows = [{k: (bool_to_int(v) if isinstance(v, bool) else v) for k, v in row.items() if k in csv2_fields} for row in analyzed]
    write_csv(os.path.join(OUTPUT_DIR, "humanization_scores.csv"), csv2_rows, csv2_fields)

    # --- CSV 3: Comparison Usefulness Scores ---
    csv3_fields = [
        "id", "title", "cluster", "has_comparison_table", "has_suitability_guide",
        "has_pros_cons", "comparison_usefulness_score"
    ]
    csv3_rows = [{k: (bool_to_int(v) if isinstance(v, bool) else v) for k, v in row.items() if k in csv3_fields} for row in analyzed]
    write_csv(os.path.join(OUTPUT_DIR, "comparison_usefulness_scores.csv"), csv3_rows, csv3_fields)

    # --- CSV 4: Buyer Intent Scores ---
    csv4_fields = [
        "id", "title", "cluster", "has_suitability_guide", "has_pros_cons",
        "has_routine_checklist", "has_comparison_table", "buyer_intent_score"
    ]
    csv4_rows = [{k: (bool_to_int(v) if isinstance(v, bool) else v) for k, v in row.items() if k in csv4_fields} for row in analyzed]
    write_csv(os.path.join(OUTPUT_DIR, "buyer_intent_scores.csv"), csv4_rows, csv4_fields)

    # --- CSV 5: Practical Guidance Scores ---
    csv5_fields = [
        "id", "title", "cluster", "has_common_mistakes", "has_what_to_expect",
        "has_routine_checklist", "list_count", "practical_guidance_score"
    ]
    csv5_rows = [{k: (bool_to_int(v) if isinstance(v, bool) else v) for k, v in row.items() if k in csv5_fields} for row in analyzed]
    write_csv(os.path.join(OUTPUT_DIR, "practical_guidance_scores.csv"), csv5_rows, csv5_fields)

    # --- CSV 6: Citation Readiness Scores ---
    csv6_fields = [
        "id", "title", "cluster", "has_sources", "external_link_count",
        "has_trust_footer", "has_faq", "has_quick_answer", "citation_readiness_score"
    ]
    csv6_rows = [{k: (bool_to_int(v) if isinstance(v, bool) else v) for k, v in row.items() if k in csv6_fields} for row in analyzed]
    write_csv(os.path.join(OUTPUT_DIR, "citation_readiness_scores.csv"), csv6_rows, csv6_fields)

    # --- CSV 7: Brand Authority Scores ---
    csv7_fields = [
        "id", "title", "cluster", "eeat_score", "humanization_score",
        "comparison_score", "buyer_intent_score", "citation_score",
        "brand_authority_total"
    ]
    csv7_rows = []
    for row in analyzed:
        csv7_rows.append({
            "id": row["id"],
            "title": row["title"],
            "cluster": row["cluster"],
            "eeat_score": row["eeat_depth_score"],
            "humanization_score": row["humanization_score"],
            "comparison_score": row["comparison_usefulness_score"],
            "buyer_intent_score": row["buyer_intent_score"],
            "citation_score": row["citation_readiness_score"],
            "brand_authority_total": row["brand_authority_total"],
        })
    write_csv(os.path.join(OUTPUT_DIR, "brand_authority_scores.csv"), csv7_rows, csv7_fields)

    # --- CSV 8: Cluster Brand Authority (aggregated) ---
    csv8_fields = [
        "cluster", "post_count", "avg_eeat", "avg_humanization", "avg_comparison",
        "avg_buyer_intent", "avg_citation", "avg_brand_authority", "weakest_dimension"
    ]
    cluster_data = defaultdict(lambda: {
        "eeat": [], "humanization": [], "comparison": [],
        "buyer_intent": [], "citation": [], "brand_authority": []
    })
    for row in analyzed:
        c = row["cluster"]
        cluster_data[c]["eeat"].append(row["eeat_depth_score"])
        cluster_data[c]["humanization"].append(row["humanization_score"])
        cluster_data[c]["comparison"].append(row["comparison_usefulness_score"])
        cluster_data[c]["buyer_intent"].append(row["buyer_intent_score"])
        cluster_data[c]["citation"].append(row["citation_readiness_score"])
        cluster_data[c]["brand_authority"].append(row["brand_authority_total"])

    csv8_rows = []
    for cluster_name in sorted(cluster_data.keys()):
        cd = cluster_data[cluster_name]
        count = len(cd["eeat"])
        avgs = {
            "avg_eeat": round(sum(cd["eeat"]) / count, 1),
            "avg_humanization": round(sum(cd["humanization"]) / count, 1),
            "avg_comparison": round(sum(cd["comparison"]) / count, 1),
            "avg_buyer_intent": round(sum(cd["buyer_intent"]) / count, 1),
            "avg_citation": round(sum(cd["citation"]) / count, 1),
            "avg_brand_authority": round(sum(cd["brand_authority"]) / count, 1),
        }
        # Find weakest dimension
        dim_map = {
            "E-E-A-T": avgs["avg_eeat"],
            "Humanization": avgs["avg_humanization"],
            "Comparison": avgs["avg_comparison"],
            "Buyer Intent": avgs["avg_buyer_intent"],
            "Citation": avgs["avg_citation"],
        }
        weakest = min(dim_map, key=dim_map.get)

        csv8_rows.append({
            "cluster": cluster_name,
            "post_count": count,
            **avgs,
            "weakest_dimension": weakest,
        })
    write_csv(os.path.join(OUTPUT_DIR, "cluster_brand_authority.csv"), csv8_rows, csv8_fields)

    # --- CSV 9: Conversion Readiness Scores ---
    csv9_fields = [
        "id", "title", "cluster", "has_suitability_guide", "has_comparison_table",
        "has_pros_cons", "has_routine_checklist", "internal_link_count",
        "conversion_readiness_score"
    ]
    csv9_rows = [{k: (bool_to_int(v) if isinstance(v, bool) else v) for k, v in row.items() if k in csv9_fields} for row in analyzed]
    write_csv(os.path.join(OUTPUT_DIR, "conversion_readiness_scores.csv"), csv9_rows, csv9_fields)

    # --- CSV 10: AI Answer Ownership Scores ---
    csv10_fields = [
        "id", "title", "cluster", "has_faq", "has_quick_answer",
        "has_comparison_table", "has_suitability_guide", "heading_count",
        "list_count", "ai_answer_ownership_score"
    ]
    csv10_rows = [{k: (bool_to_int(v) if isinstance(v, bool) else v) for k, v in row.items() if k in csv10_fields} for row in analyzed]
    write_csv(os.path.join(OUTPUT_DIR, "ai_answer_ownership_scores.csv"), csv10_rows, csv10_fields)

    # ─── Summary Statistics ──────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("SUMMARY STATISTICS")
    print("=" * 70)

    total = len(analyzed)
    print(f"\nTotal posts analyzed: {total}")

    # Cluster breakdown
    print(f"\nCluster distribution:")
    cluster_counts = defaultdict(int)
    for row in analyzed:
        cluster_counts[row["cluster"]] += 1
    for c in sorted(cluster_counts.keys()):
        print(f"  {c}: {cluster_counts[c]} posts")

    # Average scores across all posts
    score_keys = [
        ("E-E-A-T Depth", "eeat_depth_score"),
        ("Humanization", "humanization_score"),
        ("Comparison Usefulness", "comparison_usefulness_score"),
        ("Buyer Intent", "buyer_intent_score"),
        ("Practical Guidance", "practical_guidance_score"),
        ("Citation Readiness", "citation_readiness_score"),
        ("Brand Authority", "brand_authority_total"),
        ("Conversion Readiness", "conversion_readiness_score"),
        ("AI Answer Ownership", "ai_answer_ownership_score"),
    ]

    print(f"\nGlobal average scores (out of 100):")
    for label, key in score_keys:
        vals = [row[key] for row in analyzed]
        avg = sum(vals) / len(vals) if vals else 0
        max_val = max(vals) if vals else 0
        min_val = min(vals) if vals else 0
        print(f"  {label:30s}: avg={avg:5.1f}  min={min_val:5.1f}  max={max_val:5.1f}")

    # Content signal adoption rates
    bool_signals = [
        "has_about_guide", "has_common_mistakes", "has_what_to_expect",
        "has_suitability_guide", "has_pros_cons", "has_routine_checklist",
        "has_comparison_table", "has_faq", "has_quick_answer", "has_sources",
        "has_trust_footer", "has_editorial_link", "has_methodology_link",
        "has_corrections_link", "has_affiliate_disclosure", "has_practical_tips"
    ]

    print(f"\nContent signal adoption rates:")
    for sig in bool_signals:
        count = sum(1 for row in analyzed if row[sig])
        pct = (count / total * 100) if total else 0
        print(f"  {sig:35s}: {count:3d}/{total} ({pct:5.1f}%)")

    # Average counts
    count_signals = [
        "internal_link_count", "external_link_count", "word_count",
        "heading_count", "list_count", "image_count"
    ]
    print(f"\nAverage content metrics:")
    for sig in count_signals:
        vals = [row[sig] for row in analyzed]
        avg = sum(vals) / len(vals) if vals else 0
        print(f"  {sig:30s}: avg={avg:6.1f}  total={sum(vals)}")

    # Posts with zero brand authority
    zero_ba = sum(1 for row in analyzed if row["brand_authority_total"] == 0)
    print(f"\nPosts with zero brand authority: {zero_ba}/{total}")

    # Top 5 and bottom 5 by brand authority
    sorted_by_ba = sorted(analyzed, key=lambda x: x["brand_authority_total"], reverse=True)
    print(f"\nTop 5 posts by brand authority:")
    for row in sorted_by_ba[:5]:
        print(f"  [{row['id']}] {row['title'][:60]:60s} BA={row['brand_authority_total']}")

    print(f"\nBottom 5 posts by brand authority:")
    for row in sorted_by_ba[-5:]:
        print(f"  [{row['id']}] {row['title'][:60]:60s} BA={row['brand_authority_total']}")

    print(f"\nAll 10 CSVs written to: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
