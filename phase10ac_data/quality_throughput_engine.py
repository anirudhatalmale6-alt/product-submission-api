#!/usr/bin/env python3
"""
10AC-G: Quality Throughput Engine
Comprehensive quality scoring across all 144+ posts.
Generates per-post quality scores across 10 dimensions, identifies
the posts with lowest overall quality, and produces actionable reports.
"""

import subprocess, json, time, csv, re
from collections import defaultdict

WP_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"

KNOWN_REFS = ["rspca.org", "bva.co.uk", "fediaf.org", "battersea.org", "cats.org.uk",
              "gov.uk", "pdsa.org", "bluecross.org"]

def fetch_all_posts():
    posts = []
    page = 1
    while True:
        cmd = ["curl", "-s", "--compressed", "-u", AUTH,
               f"{WP_URL}/posts?status=publish&per_page=100&page={page}&context=edit"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        batch = json.loads(r.stdout)
        if not batch or isinstance(batch, dict):
            break
        posts.extend(batch)
        if len(batch) < 100:
            break
        page += 1
        time.sleep(2)
    return posts

def score_post(post):
    content = post["content"]["raw"]
    title = post["title"]["raw"]
    word_count = len(content.split())

    # 1. Content Depth (0-100)
    depth = min(100, word_count / 12)

    # 2. FAQ Coverage (0-100)
    faq_headings = len(re.findall(r'<!-- wp:heading {"level":3}', content))
    has_faq_marker = "FAQ" in content or "Common Questions" in content or "Frequently Asked" in content
    faq_score = min(100, faq_headings * 15 + (30 if has_faq_marker else 0))

    # 3. Glossary/Definition Coverage (0-100)
    glossary_terms = len(re.findall(r'<strong>[^<]+</strong>\s*[—–-]', content))
    has_key_terms = "Key Terms" in content
    glossary_score = min(100, glossary_terms * 12 + (25 if has_key_terms else 0))

    # 4. Trust Signals (0-100)
    has_trust = "Editorial Standards" in content or "editorial methodology" in content
    has_methodology_link = "our-methodology" in content
    has_corrections_link = "corrections-policy" in content
    has_ai_transparency = "ai-transparency" in content
    trust_score = (30 if has_trust else 0) + (25 if has_methodology_link else 0) + \
                  (25 if has_corrections_link else 0) + (20 if has_ai_transparency else 0)

    # 5. Comparison Tables (0-100)
    has_table = "wp-block-table" in content
    table_count = content.count("wp-block-table")
    comparison_score = min(100, table_count * 40 + (20 if has_table else 0))

    # 6. Practical Guidance (0-100)
    has_checklist = bool(re.search(r'<li><strong>[^<]+:</strong>', content))
    has_ordered_list = "<ol>" in content
    has_practical = "Practical Example" in content or "Step-by-Step" in content
    practical_items = len(re.findall(r'<li><strong>[^<]+:</strong>', content))
    practical_score = min(100, practical_items * 15 + (25 if has_checklist else 0) + \
                         (15 if has_ordered_list else 0) + (15 if has_practical else 0))

    # 7. External References (0-100)
    ext_refs = sum(1 for ref in KNOWN_REFS if ref in content)
    ext_score = min(100, ext_refs * 30)

    # 8. Internal Links (0-100)
    internal_links = len(re.findall(r'href="https://pethubonline\.com/', content))
    has_related = "Related Reading" in content or "Related Guides" in content
    internal_score = min(100, internal_links * 8 + (20 if has_related else 0))

    # 9. Semantic Richness (0-100)
    inline_defs = len(re.findall(r'meaning\s|refers to\s|defined as\s|— a |— an |— the ', content.lower()))
    heading_count = len(re.findall(r'<!-- wp:heading', content))
    list_count = content.count("<!-- wp:list -->")
    semantic_score = min(100, inline_defs * 10 + heading_count * 5 + list_count * 8)

    # 10. Freshness Indicators (0-100)
    has_year = bool(re.search(r'202[456]', content))
    has_updated = "Updated" in content or "updated" in content
    freshness_score = (50 if has_year else 0) + (50 if has_updated else 0)

    overall = (
        depth * 0.15 +
        faq_score * 0.10 +
        glossary_score * 0.10 +
        trust_score * 0.15 +
        comparison_score * 0.10 +
        practical_score * 0.10 +
        ext_score * 0.10 +
        internal_score * 0.10 +
        semantic_score * 0.05 +
        freshness_score * 0.05
    )

    return {
        "post_id": post["id"],
        "title": title[:60],
        "word_count": word_count,
        "depth_score": round(depth, 1),
        "faq_score": round(faq_score, 1),
        "glossary_score": round(glossary_score, 1),
        "trust_score": round(trust_score, 1),
        "comparison_score": round(comparison_score, 1),
        "practical_score": round(practical_score, 1),
        "external_ref_score": round(ext_score, 1),
        "internal_link_score": round(internal_score, 1),
        "semantic_score": round(semantic_score, 1),
        "freshness_score": round(freshness_score, 1),
        "overall_quality": round(overall, 1),
        "quality_tier": "S" if overall >= 85 else "A" if overall >= 70 else "B" if overall >= 55 else "C" if overall >= 40 else "D"
    }

print("Fetching all published posts...")
posts = fetch_all_posts()
print(f"Found {len(posts)} posts\n")

scores = []
for post in posts:
    score = score_post(post)
    scores.append(score)

scores.sort(key=lambda x: -x["overall_quality"])

csv_path = "/var/lib/freelancer/projects/40416335/phase10ac_data/Quality_Throughput_Index.csv"
fields = ["post_id", "title", "word_count", "depth_score", "faq_score", "glossary_score",
          "trust_score", "comparison_score", "practical_score", "external_ref_score",
          "internal_link_score", "semantic_score", "freshness_score", "overall_quality", "quality_tier"]

with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(scores)

tier_counts = defaultdict(int)
for s in scores:
    tier_counts[s["quality_tier"]] += 1

avg_overall = sum(s["overall_quality"] for s in scores) / len(scores) if scores else 0
avg_dims = {}
for dim in ["depth_score", "faq_score", "glossary_score", "trust_score", "comparison_score",
            "practical_score", "external_ref_score", "internal_link_score", "semantic_score", "freshness_score"]:
    avg_dims[dim] = sum(s[dim] for s in scores) / len(scores) if scores else 0

print(f"{'='*60}")
print(f"QUALITY THROUGHPUT INDEX — {len(scores)} posts scored")
print(f"{'='*60}")
print(f"\nOverall Average: {avg_overall:.1f}/100")
print(f"\nDimension Averages:")
for dim, val in sorted(avg_dims.items(), key=lambda x: -x[1]):
    print(f"  {dim.replace('_score', ''):20s}: {val:.1f}")
print(f"\nTier Distribution:")
for tier in ["S", "A", "B", "C", "D"]:
    count = tier_counts.get(tier, 0)
    pct = count / len(scores) * 100 if scores else 0
    bar = "#" * int(pct / 2)
    print(f"  {tier}: {count:3d} ({pct:.0f}%) {bar}")

print(f"\nTop 10 Posts:")
for s in scores[:10]:
    print(f"  {s['post_id']:5d} ({s['quality_tier']}) {s['overall_quality']:5.1f} — {s['title']}")

print(f"\nBottom 10 Posts:")
for s in scores[-10:]:
    print(f"  {s['post_id']:5d} ({s['quality_tier']}) {s['overall_quality']:5.1f} — {s['title']}")

print(f"\nCSV saved to {csv_path}")
