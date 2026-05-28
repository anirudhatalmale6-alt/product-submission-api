#!/usr/bin/env python3
"""
10AB-F: Cluster Dominance Scoring Engine
Tracks cluster leadership across 10 dimensions to create a strategic KPI per cluster.
"""

import subprocess, json, time, csv, re
from collections import defaultdict

WP_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"

CLUSTERS = {
    "Dog Toys": {"cat_id": 1344, "keywords": ["dog toy", "dog toys", "chew", "fetch", "puzzle toy", "enrichment", "play"]},
    "Dog Food": {"cat_id": 1330, "keywords": ["dog food", "puppy food", "dry food", "wet food", "nutrition"]},
    "Dog Beds": {"cat_id": 1338, "keywords": ["dog bed", "orthopaedic", "cooling bed", "puppy bed"]},
    "Dog Care": {"cat_id": 1330, "keywords": ["grooming", "dental", "seasonal care", "first-time owner"]},
    "Dog Health": {"cat_id": 1337, "keywords": ["flea", "joint", "dental health", "supplement"]},
    "Dog Supplies": {"cat_id": 205, "keywords": ["collar", "lead", "harness", "bowl", "training"]},
    "Dog Harnesses": {"cat_id": 1342, "keywords": ["harness", "no-pull", "front-clip"]},
    "Cat Supplies": {"cat_id": 204, "keywords": ["cat toy", "cat bed", "scratching", "litter", "cat collar"]},
    "Cat Toys": {"cat_id": 1344, "keywords": ["cat toy", "interactive cat", "catnip", "indoor cat"]},
    "Puppy Care": {"cat_id": None, "keywords": ["puppy", "socialisation", "teething", "first year"]},
    "Pet Care General": {"cat_id": None, "keywords": ["pet safety", "multi-pet", "first aid", "hydration"]},
}

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

def assign_cluster(post):
    title = post["title"]["raw"].lower()
    content = post["content"]["raw"].lower()
    cats = [c for c in post.get("categories", [])]

    scores = {}
    for cluster, info in CLUSTERS.items():
        score = 0
        for kw in info["keywords"]:
            if kw in title:
                score += 3
            if kw in content[:500]:
                score += 1
        if info["cat_id"] and info["cat_id"] in cats:
            score += 5
        scores[cluster] = score

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Uncategorized"

def score_post(post):
    content = post["content"]["raw"]
    title = post["title"]["raw"]
    word_count = len(content.split())

    has_faq = content.count("<h3") >= 3
    has_glossary = "Key Terms" in content or "Glossary" in content or "<strong>" in content and "—" in content
    has_trust = "Editorial Standards" in content or "editorial methodology" in content
    has_comparison = "wp-block-table" in content
    has_practical = "Practical Example" in content or "Step-by-Step" in content or "step 1" in content.lower()
    has_related = "Related Reading" in content or "Further Reading" in content
    has_external_ref = any(ref in content for ref in ["rspca.org", "bva.co.uk", "fediaf.org", "battersea.org", "gov.uk"])

    internal_links = len(re.findall(r'href="https://pethubonline\.com/[^"]*"', content))

    faq_count = len(re.findall(r'<!-- wp:heading {"level":3}', content))
    glossary_terms = len(re.findall(r'<strong>[^<]+</strong>\s*[—–-]', content))

    return {
        "word_count": word_count,
        "has_faq": has_faq,
        "faq_count": faq_count,
        "has_glossary": has_glossary,
        "glossary_terms": glossary_terms,
        "has_trust": has_trust,
        "has_comparison": has_comparison,
        "has_practical": has_practical,
        "has_related": has_related,
        "has_external_ref": has_external_ref,
        "internal_links": internal_links,
    }

print("Fetching all published posts...")
posts = fetch_all_posts()
print(f"Found {len(posts)} published posts")

cluster_data = defaultdict(lambda: {
    "posts": [], "total_words": 0, "faq_posts": 0, "glossary_posts": 0,
    "trust_posts": 0, "comparison_posts": 0, "practical_posts": 0,
    "external_ref_posts": 0, "total_internal_links": 0, "total_faq_count": 0,
    "total_glossary_terms": 0, "related_reading_posts": 0
})

post_details = []

for post in posts:
    cluster = assign_cluster(post)
    scores = score_post(post)

    cd = cluster_data[cluster]
    cd["posts"].append(post["id"])
    cd["total_words"] += scores["word_count"]
    cd["faq_posts"] += 1 if scores["has_faq"] else 0
    cd["glossary_posts"] += 1 if scores["has_glossary"] else 0
    cd["trust_posts"] += 1 if scores["has_trust"] else 0
    cd["comparison_posts"] += 1 if scores["has_comparison"] else 0
    cd["practical_posts"] += 1 if scores["has_practical"] else 0
    cd["external_ref_posts"] += 1 if scores["has_external_ref"] else 0
    cd["total_internal_links"] += scores["internal_links"]
    cd["total_faq_count"] += scores["faq_count"]
    cd["total_glossary_terms"] += scores["glossary_terms"]
    cd["related_reading_posts"] += 1 if scores["has_related"] else 0

    post_details.append({
        "post_id": post["id"],
        "title": post["title"]["raw"],
        "cluster": cluster,
        **scores
    })

# Calculate dominance scores per cluster
results = []
for cluster_name, cd in sorted(cluster_data.items()):
    n = len(cd["posts"])
    if n == 0:
        continue

    semantic_saturation = min(100, (n / 15) * 100)  # 15 posts = full saturation
    publication_depth = min(100, (cd["total_words"] / (n * 1500)) * 100)  # 1500 words avg target
    educational_breadth = min(100, (n * 10))  # Each post adds breadth
    faq_dominance = (cd["faq_posts"] / n) * 100
    glossary_dominance = (cd["glossary_posts"] / n) * 100
    trust_reinforcement = (cd["trust_posts"] / n) * 100
    ai_answer_readiness = ((cd["faq_posts"] + cd["glossary_posts"] + cd["comparison_posts"]) / (n * 3)) * 100
    crawl_reinforcement = min(100, (cd["total_internal_links"] / (n * 5)) * 100)  # 5 links per post target
    comparison_usefulness = (cd["comparison_posts"] / n) * 100
    authority_momentum = min(100, (cd["related_reading_posts"] / n) * 100)

    overall = (
        semantic_saturation * 0.15 +
        publication_depth * 0.10 +
        educational_breadth * 0.05 +
        faq_dominance * 0.15 +
        glossary_dominance * 0.10 +
        trust_reinforcement * 0.10 +
        ai_answer_readiness * 0.15 +
        crawl_reinforcement * 0.05 +
        comparison_usefulness * 0.10 +
        authority_momentum * 0.05
    )

    results.append({
        "cluster": cluster_name,
        "posts": n,
        "total_words": cd["total_words"],
        "semantic_saturation": round(semantic_saturation, 1),
        "publication_depth": round(publication_depth, 1),
        "educational_breadth": round(educational_breadth, 1),
        "faq_dominance": round(faq_dominance, 1),
        "glossary_dominance": round(glossary_dominance, 1),
        "trust_reinforcement": round(trust_reinforcement, 1),
        "ai_answer_readiness": round(ai_answer_readiness, 1),
        "crawl_reinforcement": round(crawl_reinforcement, 1),
        "comparison_usefulness": round(comparison_usefulness, 1),
        "authority_momentum": round(authority_momentum, 1),
        "overall_dominance": round(overall, 1),
    })

results.sort(key=lambda x: x["overall_dominance"], reverse=True)

csv_path = "/var/lib/freelancer/projects/40416335/phase10ab_data/Cluster_Dominance_Index.csv"
fields = ["cluster", "posts", "total_words", "semantic_saturation", "publication_depth",
          "educational_breadth", "faq_dominance", "glossary_dominance", "trust_reinforcement",
          "ai_answer_readiness", "crawl_reinforcement", "comparison_usefulness",
          "authority_momentum", "overall_dominance"]
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(results)

# Summary
print(f"\n{'='*60}")
print("CLUSTER DOMINANCE INDEX")
print(f"{'='*60}")
for r in results:
    print(f"\n{r['cluster']} ({r['posts']} posts)")
    print(f"  Overall Dominance: {r['overall_dominance']}/100")
    print(f"  Semantic Saturation: {r['semantic_saturation']}  |  FAQ: {r['faq_dominance']}  |  Glossary: {r['glossary_dominance']}")
    print(f"  Trust: {r['trust_reinforcement']}  |  Comparison: {r['comparison_usefulness']}  |  AI Ready: {r['ai_answer_readiness']}")
    print(f"  Crawl: {r['crawl_reinforcement']}  |  Authority: {r['authority_momentum']}  |  Depth: {r['publication_depth']}")

# Also save per-post details
post_csv = "/var/lib/freelancer/projects/40416335/phase10ab_data/Cluster_Post_Details.csv"
post_fields = ["post_id", "title", "cluster", "word_count", "has_faq", "faq_count",
               "has_glossary", "glossary_terms", "has_trust", "has_comparison",
               "has_practical", "has_related", "has_external_ref", "internal_links"]
with open(post_csv, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=post_fields)
    w.writeheader()
    w.writerows(post_details)

print(f"\nCSVs saved to: {csv_path} and {post_csv}")
