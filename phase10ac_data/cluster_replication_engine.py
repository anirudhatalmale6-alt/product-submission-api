#!/usr/bin/env python3
"""
10AC-A: Cluster Replication Engine
Compares all clusters against the Dog Toys reference model (86.3 dominance)
and generates specific replication plans per cluster.
"""

import subprocess, json, time, csv, re
from collections import defaultdict

WP_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"

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
    content = post["content"]["raw"].lower()
    cats = post.get("categories", [])

    rules = [
        ("Dog Toys", lambda: 1344 in cats or "dog toy" in title or ("toy" in title and "cat" not in title and "dog" in content[:300])),
        ("Dog Food", lambda: any(kw in title for kw in ["dog food", "puppy food", "dry food", "dry vs wet"])),
        ("Dog Beds", lambda: "dog bed" in title or ("bed" in title and "cat" not in title)),
        ("Dog Harnesses", lambda: "harness" in title and "cat" not in title),
        ("Dog Health", lambda: any(kw in title for kw in ["flea", "joint supplement", "dental care", "dog health"])),
        ("Dog Care", lambda: any(kw in title for kw in ["grooming", "seasonal dog", "first-time dog", "dental health", "measure your dog for"])),
        ("Cat Toys", lambda: ("cat toy" in title or "cat play" in title) and 1344 not in cats),
        ("Cat Supplies", lambda: "cat " in title and not any(kw in title for kw in ["cat toy", "cat play"])),
        ("Puppy Care", lambda: "puppy" in title or "socialisation" in title),
        ("Dog Supplies", lambda: 205 in cats or any(kw in title for kw in ["collar", "lead", "bowl", "training treat", "interactive dog", "indestructible"])),
        ("Pet Care General", lambda: any(kw in title for kw in ["pet ", "multi-pet", "first aid", "seasonal pet"])),
    ]

    for name, check in rules:
        try:
            if check():
                return name
        except:
            pass

    # Educational/glossary posts
    if any(kw in title for kw in ["terminology", "glossary", "explained", "enrichment", "behaviour"]):
        if "cat" in title:
            return "Cat Supplies"
        if "dog" in title:
            return "Dog Care"
        return "Pet Care General"

    return "Uncategorized"

def analyze_post(post):
    content = post["content"]["raw"]
    return {
        "has_faq": "FAQ" in content or "Common Questions" in content or content.count("<!-- wp:heading {\"level\":3}") >= 3,
        "has_glossary": "Key Terms" in content,
        "has_trust": "Editorial Standards" in content,
        "has_comparison": "wp-block-table" in content,
        "has_practical": "Practical Example" in content or "<ol>" in content,
        "has_external_ref": any(r in content for r in ["rspca.org", "bva.co.uk", "fediaf.org", "battersea.org", "cats.org.uk", "gov.uk", "pdsa.org", "bluecross.org"]),
        "has_related": "Related Reading" in content or "Related Guides" in content,
        "has_inline_defs": len(re.findall(r'meaning\s|refers to\s|defined as\s', content.lower())) > 0,
        "has_checklist": bool(re.search(r'<li><strong>[^<]+:</strong>', content)),
        "word_count": len(content.split()),
        "internal_links": len(re.findall(r'href="https://pethubonline\.com/', content)),
        "glossary_terms": len(re.findall(r'<strong>[^<]+</strong>\s*[—–-]', content)),
        "faq_count": len(re.findall(r'<!-- wp:heading {"level":3}', content)),
    }

print("Fetching all published posts...")
posts = fetch_all_posts()
print(f"Found {len(posts)} posts\n")

clusters = defaultdict(list)
for p in posts:
    cluster = classify_cluster(p)
    analysis = analyze_post(p)
    clusters[cluster].append({"id": p["id"], "title": p["title"]["raw"], **analysis})

# Reference model: Dog Toys
ref = clusters.get("Dog Toys", [])
ref_metrics = {
    "post_count": len(ref),
    "faq_rate": sum(1 for p in ref if p["has_faq"]) / max(1, len(ref)) * 100,
    "glossary_rate": sum(1 for p in ref if p["has_glossary"]) / max(1, len(ref)) * 100,
    "trust_rate": sum(1 for p in ref if p["has_trust"]) / max(1, len(ref)) * 100,
    "comparison_rate": sum(1 for p in ref if p["has_comparison"]) / max(1, len(ref)) * 100,
    "practical_rate": sum(1 for p in ref if p["has_practical"]) / max(1, len(ref)) * 100,
    "external_ref_rate": sum(1 for p in ref if p["has_external_ref"]) / max(1, len(ref)) * 100,
    "related_rate": sum(1 for p in ref if p["has_related"]) / max(1, len(ref)) * 100,
    "avg_glossary_terms": sum(p["glossary_terms"] for p in ref) / max(1, len(ref)),
    "avg_faq_count": sum(p["faq_count"] for p in ref) / max(1, len(ref)),
    "avg_internal_links": sum(p["internal_links"] for p in ref) / max(1, len(ref)),
}

print(f"REFERENCE MODEL: Dog Toys ({ref_metrics['post_count']} posts)")
for k, v in ref_metrics.items():
    print(f"  {k}: {v:.1f}")

replication_plans = []
gap_details = []

for cluster_name, posts_list in sorted(clusters.items()):
    if cluster_name == "Dog Toys" or cluster_name == "Uncategorized":
        continue

    n = len(posts_list)
    if n == 0:
        continue

    metrics = {
        "faq_rate": sum(1 for p in posts_list if p["has_faq"]) / n * 100,
        "glossary_rate": sum(1 for p in posts_list if p["has_glossary"]) / n * 100,
        "trust_rate": sum(1 for p in posts_list if p["has_trust"]) / n * 100,
        "comparison_rate": sum(1 for p in posts_list if p["has_comparison"]) / n * 100,
        "practical_rate": sum(1 for p in posts_list if p["has_practical"]) / n * 100,
        "external_ref_rate": sum(1 for p in posts_list if p["has_external_ref"]) / n * 100,
        "related_rate": sum(1 for p in posts_list if p["has_related"]) / n * 100,
        "avg_glossary_terms": sum(p["glossary_terms"] for p in posts_list) / n,
        "avg_faq_count": sum(p["faq_count"] for p in posts_list) / n,
        "avg_internal_links": sum(p["internal_links"] for p in posts_list) / n,
    }

    gaps = []
    gap_scores = {}

    # Post count gap
    post_gap = max(0, 15 - n)
    if post_gap > 0:
        gaps.append(f"Need {post_gap} more posts to reach 15-post baseline")
        gap_scores["post_count"] = post_gap

    # Dimension gaps
    dims = [
        ("comparison_rate", "comparison tables", 20),
        ("practical_rate", "practical examples", 20),
        ("external_ref_rate", "external references", 15),
        ("trust_rate", "trust editorial blocks", 15),
        ("glossary_rate", "glossary Key Terms", 10),
        ("faq_rate", "FAQ sections", 10),
        ("related_rate", "Related Reading sections", 10),
    ]

    for dim_key, dim_name, weight in dims:
        gap = ref_metrics[dim_key] - metrics[dim_key]
        if gap > 10:
            posts_needing = [p for p in posts_list if not p[f"has_{dim_key.replace('_rate', '')}".replace("has_comparison", "has_comparison").replace("has_practical", "has_practical")]
                           ] if dim_key != "comparison_rate" else [p for p in posts_list if not p["has_comparison"]]

            # Fix the has_ mapping
            has_key_map = {
                "comparison_rate": "has_comparison",
                "practical_rate": "has_practical",
                "external_ref_rate": "has_external_ref",
                "trust_rate": "has_trust",
                "glossary_rate": "has_glossary",
                "faq_rate": "has_faq",
                "related_rate": "has_related",
            }
            has_key = has_key_map[dim_key]
            missing_posts = [p for p in posts_list if not p[has_key]]
            missing_count = len(missing_posts)

            gaps.append(f"{dim_name}: {metrics[dim_key]:.0f}% vs ref {ref_metrics[dim_key]:.0f}% ({missing_count} posts missing)")
            gap_scores[dim_key] = gap * weight / 100

            for mp in missing_posts:
                gap_details.append({
                    "cluster": cluster_name,
                    "post_id": mp["id"],
                    "title": mp["title"][:60],
                    "missing_dimension": dim_name,
                    "priority": "high" if gap > 50 else "medium" if gap > 25 else "low"
                })

    overall_gap = sum(gap_scores.values())
    replication_readiness = max(0, 100 - overall_gap)

    replication_plans.append({
        "cluster": cluster_name,
        "posts": n,
        "replication_readiness": round(replication_readiness, 1),
        "faq_rate": round(metrics["faq_rate"], 1),
        "glossary_rate": round(metrics["glossary_rate"], 1),
        "trust_rate": round(metrics["trust_rate"], 1),
        "comparison_rate": round(metrics["comparison_rate"], 1),
        "practical_rate": round(metrics["practical_rate"], 1),
        "external_ref_rate": round(metrics["external_ref_rate"], 1),
        "related_rate": round(metrics["related_rate"], 1),
        "post_gap": post_gap,
        "top_gaps": " | ".join(gaps[:3]) if gaps else "None",
    })

replication_plans.sort(key=lambda x: x["replication_readiness"])

# Save CSVs
base = "/var/lib/freelancer/projects/40416335/phase10ac_data"

csv1 = f"{base}/Cluster_Replication_Plans.csv"
fields1 = ["cluster", "posts", "replication_readiness", "faq_rate", "glossary_rate",
           "trust_rate", "comparison_rate", "practical_rate", "external_ref_rate",
           "related_rate", "post_gap", "top_gaps"]
with open(csv1, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields1)
    w.writeheader()
    w.writerows(replication_plans)

csv2 = f"{base}/Cluster_Gap_Details.csv"
fields2 = ["cluster", "post_id", "title", "missing_dimension", "priority"]
with open(csv2, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields2)
    w.writeheader()
    w.writerows(sorted(gap_details, key=lambda x: (x["cluster"], x["priority"])))

print(f"\n{'='*60}")
print("CLUSTER REPLICATION PLANS (vs Dog Toys Reference)")
print(f"{'='*60}")
for r in replication_plans:
    print(f"\n{r['cluster']} ({r['posts']} posts) — Readiness: {r['replication_readiness']}%")
    print(f"  FAQ: {r['faq_rate']}% | Glossary: {r['glossary_rate']}% | Trust: {r['trust_rate']}%")
    print(f"  Comparison: {r['comparison_rate']}% | Practical: {r['practical_rate']}% | ExtRef: {r['external_ref_rate']}%")
    print(f"  Post gap: {r['post_gap']} | Top gaps: {r['top_gaps'][:80]}")

high_gaps = sum(1 for g in gap_details if g["priority"] == "high")
med_gaps = sum(1 for g in gap_details if g["priority"] == "medium")
print(f"\nTotal gap items: {len(gap_details)} ({high_gaps} high, {med_gaps} medium)")
print(f"CSVs saved to: {csv1}, {csv2}")
