#!/usr/bin/env python3
"""
10AC-H: Live Authority Telemetry
Comprehensive authority measurement combining all scoring dimensions
into a single live telemetry report. Tracks authority momentum across
cluster replication, trust density, semantic saturation, and quality.
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

def classify_cluster(post):
    title = post["title"]["raw"].lower()
    cats = post.get("categories", [])
    if 1344 in cats or "dog toy" in title or ("toy" in title and "cat" not in title and "dog" in post["content"]["raw"].lower()[:300]):
        return "Dog Toys"
    if any(kw in title for kw in ["dog food", "puppy food", "dry food", "dry vs wet"]):
        return "Dog Food"
    if "dog bed" in title or ("bed" in title and "cat" not in title):
        return "Dog Beds"
    if "harness" in title and "cat" not in title:
        return "Dog Harnesses"
    if any(kw in title for kw in ["flea", "joint supplement", "dental care", "dog health"]):
        return "Dog Health"
    if any(kw in title for kw in ["grooming", "seasonal dog", "first-time dog", "dental health", "measure your dog"]):
        return "Dog Care"
    if "cat toy" in title or "cat play" in title:
        return "Cat Toys"
    if "cat " in title:
        return "Cat Supplies"
    if "puppy" in title or "socialisation" in title:
        return "Puppy Care"
    if any(kw in title for kw in ["collar", "lead", "bowl", "training treat", "interactive dog", "indestructible"]):
        return "Dog Supplies"
    if any(kw in title for kw in ["pet ", "multi-pet", "first aid", "seasonal pet"]):
        return "Pet Care General"
    if any(kw in title for kw in ["terminology", "glossary", "explained", "enrichment", "behaviour"]):
        return "Educational"
    return "Other"

def measure_authority(post):
    content = post["content"]["raw"]
    word_count = len(content.split())

    return {
        "trust_complete": 1 if ("Editorial Standards" in content or "editorial methodology" in content) else 0,
        "has_faq": 1 if ("FAQ" in content or len(re.findall(r'<!-- wp:heading {"level":3}', content)) >= 3) else 0,
        "has_glossary": 1 if "Key Terms" in content else 0,
        "has_comparison": 1 if "wp-block-table" in content else 0,
        "has_practical": 1 if (bool(re.search(r'<li><strong>[^<]+:</strong>', content)) or "Practical Example" in content) else 0,
        "has_external_ref": 1 if any(ref in content for ref in KNOWN_REFS) else 0,
        "has_related": 1 if ("Related Reading" in content or "Related Guides" in content) else 0,
        "has_checklist": 1 if bool(re.search(r'<li><strong>[^<]+:</strong>', content)) else 0,
        "internal_links": len(re.findall(r'href="https://pethubonline\.com/', content)),
        "external_refs": sum(1 for ref in KNOWN_REFS if ref in content),
        "glossary_terms": len(re.findall(r'<strong>[^<]+</strong>\s*[—–-]', content)),
        "word_count": word_count,
        "heading_count": len(re.findall(r'<!-- wp:heading', content)),
    }

print("Fetching all published posts for authority telemetry...")
posts = fetch_all_posts()
print(f"Analyzing {len(posts)} posts\n")

clusters = defaultdict(list)
all_metrics = []

for post in posts:
    cluster = classify_cluster(post)
    metrics = measure_authority(post)
    metrics["cluster"] = cluster
    metrics["post_id"] = post["id"]
    metrics["title"] = post["title"]["raw"][:60]
    clusters[cluster].append(metrics)
    all_metrics.append(metrics)

# Site-wide telemetry
total = len(all_metrics)
site_telemetry = {
    "total_posts": total,
    "trust_coverage": sum(m["trust_complete"] for m in all_metrics) / total * 100,
    "faq_coverage": sum(m["has_faq"] for m in all_metrics) / total * 100,
    "glossary_coverage": sum(m["has_glossary"] for m in all_metrics) / total * 100,
    "comparison_coverage": sum(m["has_comparison"] for m in all_metrics) / total * 100,
    "practical_coverage": sum(m["has_practical"] for m in all_metrics) / total * 100,
    "external_ref_coverage": sum(m["has_external_ref"] for m in all_metrics) / total * 100,
    "related_coverage": sum(m["has_related"] for m in all_metrics) / total * 100,
    "checklist_coverage": sum(m["has_checklist"] for m in all_metrics) / total * 100,
    "avg_internal_links": sum(m["internal_links"] for m in all_metrics) / total,
    "avg_external_refs": sum(m["external_refs"] for m in all_metrics) / total,
    "avg_glossary_terms": sum(m["glossary_terms"] for m in all_metrics) / total,
    "avg_word_count": sum(m["word_count"] for m in all_metrics) / total,
    "total_internal_links": sum(m["internal_links"] for m in all_metrics),
    "total_external_refs": sum(m["external_refs"] for m in all_metrics),
    "total_glossary_terms": sum(m["glossary_terms"] for m in all_metrics),
}

# Cluster telemetry
cluster_telemetry = []
for cluster_name, posts_list in sorted(clusters.items()):
    n = len(posts_list)
    if n == 0:
        continue

    authority_score = (
        (sum(m["trust_complete"] for m in posts_list) / n * 15) +
        (sum(m["has_faq"] for m in posts_list) / n * 10) +
        (sum(m["has_glossary"] for m in posts_list) / n * 10) +
        (sum(m["has_comparison"] for m in posts_list) / n * 10) +
        (sum(m["has_practical"] for m in posts_list) / n * 10) +
        (sum(m["has_external_ref"] for m in posts_list) / n * 10) +
        (sum(m["has_related"] for m in posts_list) / n * 10) +
        (sum(m["has_checklist"] for m in posts_list) / n * 5) +
        (min(1, sum(m["internal_links"] for m in posts_list) / n / 8) * 10) +
        (min(1, sum(m["word_count"] for m in posts_list) / n / 1200) * 10)
    )

    cluster_telemetry.append({
        "cluster": cluster_name,
        "posts": n,
        "authority_score": round(authority_score, 1),
        "trust_pct": round(sum(m["trust_complete"] for m in posts_list) / n * 100, 1),
        "faq_pct": round(sum(m["has_faq"] for m in posts_list) / n * 100, 1),
        "glossary_pct": round(sum(m["has_glossary"] for m in posts_list) / n * 100, 1),
        "comparison_pct": round(sum(m["has_comparison"] for m in posts_list) / n * 100, 1),
        "practical_pct": round(sum(m["has_practical"] for m in posts_list) / n * 100, 1),
        "extref_pct": round(sum(m["has_external_ref"] for m in posts_list) / n * 100, 1),
        "related_pct": round(sum(m["has_related"] for m in posts_list) / n * 100, 1),
        "avg_links": round(sum(m["internal_links"] for m in posts_list) / n, 1),
        "avg_words": round(sum(m["word_count"] for m in posts_list) / n, 0),
    })

cluster_telemetry.sort(key=lambda x: -x["authority_score"])

# Save CSVs
base = "/var/lib/freelancer/projects/40416335/phase10ac_data"

csv1 = f"{base}/Authority_Telemetry_Clusters.csv"
fields1 = ["cluster", "posts", "authority_score", "trust_pct", "faq_pct", "glossary_pct",
           "comparison_pct", "practical_pct", "extref_pct", "related_pct", "avg_links", "avg_words"]
with open(csv1, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields1)
    w.writeheader()
    w.writerows(cluster_telemetry)

csv2 = f"{base}/Authority_Telemetry_Posts.csv"
fields2 = ["post_id", "title", "cluster", "trust_complete", "has_faq", "has_glossary",
           "has_comparison", "has_practical", "has_external_ref", "has_related", "has_checklist",
           "internal_links", "external_refs", "glossary_terms", "word_count", "heading_count"]
with open(csv2, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields2)
    w.writeheader()
    w.writerows(sorted(all_metrics, key=lambda x: x["post_id"]))

# Print telemetry report
print(f"{'='*70}")
print(f"LIVE AUTHORITY TELEMETRY — {total} posts")
print(f"{'='*70}")

print(f"\nSITE-WIDE AUTHORITY METRICS:")
print(f"  Trust coverage:        {site_telemetry['trust_coverage']:.1f}%")
print(f"  FAQ coverage:          {site_telemetry['faq_coverage']:.1f}%")
print(f"  Glossary coverage:     {site_telemetry['glossary_coverage']:.1f}%")
print(f"  Comparison tables:     {site_telemetry['comparison_coverage']:.1f}%")
print(f"  Practical guidance:    {site_telemetry['practical_coverage']:.1f}%")
print(f"  External references:   {site_telemetry['external_ref_coverage']:.1f}%")
print(f"  Related links:         {site_telemetry['related_coverage']:.1f}%")
print(f"  Checklists:            {site_telemetry['checklist_coverage']:.1f}%")
print(f"  Avg internal links:    {site_telemetry['avg_internal_links']:.1f}")
print(f"  Avg external refs:     {site_telemetry['avg_external_refs']:.1f}")
print(f"  Avg glossary terms:    {site_telemetry['avg_glossary_terms']:.1f}")
print(f"  Avg word count:        {site_telemetry['avg_word_count']:.0f}")
print(f"  Total internal links:  {site_telemetry['total_internal_links']}")
print(f"  Total external refs:   {site_telemetry['total_external_refs']}")

print(f"\nCLUSTER AUTHORITY RANKINGS:")
for ct in cluster_telemetry:
    print(f"\n  {ct['cluster']} ({ct['posts']} posts) — Authority: {ct['authority_score']}/100")
    print(f"    Trust: {ct['trust_pct']}% | FAQ: {ct['faq_pct']}% | Glossary: {ct['glossary_pct']}%")
    print(f"    Comparison: {ct['comparison_pct']}% | Practical: {ct['practical_pct']}% | ExtRef: {ct['extref_pct']}%")
    print(f"    Related: {ct['related_pct']}% | Links: {ct['avg_links']} | Words: {ct['avg_words']}")

weighted_authority = sum(ct["authority_score"] * ct["posts"] for ct in cluster_telemetry) / total if total else 0
print(f"\nWEIGHTED SITE AUTHORITY: {weighted_authority:.1f}/100")
print(f"\nCSVs saved: {csv1}, {csv2}")
