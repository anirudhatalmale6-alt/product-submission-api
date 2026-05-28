#!/usr/bin/env python3
"""
10AC-F: Semantic Reinforcement Graph
Maps the full internal link graph between posts, identifies orphan posts
and weak link clusters, then adds cross-cluster semantic links.
"""

import subprocess, json, time, csv, re
from collections import defaultdict

WP_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
TRUST_BLOCK_MARKER = '<!-- wp:separator {"className":"is-style-wide"} -->'

CROSS_CLUSTER_LINKS = {
    "dog_toy_to_dog_care": [
        ("dog-toy-safety-what-every-owner-needs-to-know", "seasonal-dog-care", "seasonal dog care", "Safety concerns change seasonally"),
        ("mental-stimulation-toys-dogs", "first-time-dog-owner-essentials", "first-time dog owner essentials", "Beginners need enrichment guidance"),
        ("dog-toy-enrichment-beyond-fetch", "dog-grooming-basics", "dog grooming basics", "Well-groomed dogs are happier play partners"),
    ],
    "dog_toy_to_dog_food": [
        ("dog-toy-enrichment-beyond-fetch", "puppy-food-guide-uk", "puppy food guide", "Nutrition fuels play energy"),
        ("mental-stimulation-toys-dogs", "best-dry-dog-food-uk", "dry dog food guide", "Kibble dispensing toys combine feeding and play"),
    ],
    "dog_toy_to_dog_health": [
        ("senior-dog-toys-gentle-play", "best-dog-joint-supplements-uk", "joint supplements guide", "Joint health affects play ability in older dogs"),
        ("dog-toy-safety-what-every-owner-needs-to-know", "best-dog-flea-treatment-uk", "flea treatment guide", "Flea infestations can transfer between toys"),
    ],
    "dog_toy_to_harness": [
        ("dog-toy-enrichment-beyond-fetch", "dog-harnesses-complete-guide", "dog harness guide", "Outdoor enrichment needs proper walking gear"),
        ("safe-tug-play-dogs", "no-pull-dog-harness-guide", "no-pull harness guide", "Tug play can overlap with lead-pulling habits"),
    ],
    "cat_to_general": [
        ("cat-enrichment-beyond-toys", "pet-enrichment-explained", "pet enrichment explained", "Cross-species enrichment principles"),
        ("cat-toy-safety-guide", "pet-first-aid-basics", "pet first aid basics", "Toy accidents need first aid knowledge"),
        ("indoor-cat-care-guide", "seasonal-pet-safety", "seasonal pet safety", "Indoor cats face seasonal hazards too"),
    ],
    "dog_bed_to_care": [
        ("dog-bed-types-explained", "dog-grooming-basics", "dog grooming basics", "Clean dogs keep beds hygienic longer"),
        ("how-to-wash-dog-bed", "seasonal-dog-care", "seasonal dog care", "Washing frequency changes with seasons"),
    ],
    "puppy_to_training": [
        ("puppy-socialisation-timeline", "dog-training-terminology", "dog training terminology", "Understanding training terms helps socialisation"),
        ("puppy-food-guide-uk", "how-to-choose-dog-training-treats", "training treats guide", "Training treats should complement main diet"),
    ],
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

def update_post(post_id, content):
    cmd = ["curl", "-s", "--compressed", "-u", AUTH,
           "-X", "POST", f"{WP_URL}/posts/{post_id}",
           "-H", "Content-Type: application/json",
           "-d", json.dumps({"content": content})]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout)

print("Fetching all published posts...")
posts = fetch_all_posts()
print(f"Found {len(posts)} posts\n")

slug_to_post = {}
link_graph = defaultdict(set)
inbound_count = defaultdict(int)

for post in posts:
    slug = post["slug"]
    slug_to_post[slug] = post

    content = post["content"]["raw"]
    links = re.findall(r'href="https://pethubonline\.com/([^"/?]+)/?', content)
    for link_slug in links:
        if link_slug != slug and link_slug in [p["slug"] for p in posts]:
            link_graph[slug].add(link_slug)
            inbound_count[link_slug] += 1

all_slugs = set(p["slug"] for p in posts)
orphans = [s for s in all_slugs if inbound_count.get(s, 0) == 0 and s in slug_to_post]
weak = [s for s in all_slugs if inbound_count.get(s, 0) == 1 and s in slug_to_post]

print(f"Link graph: {sum(len(v) for v in link_graph.values())} total internal links")
print(f"Orphan posts (0 inbound): {len(orphans)}")
print(f"Weak posts (1 inbound): {len(weak)}")

graph_csv = "/var/lib/freelancer/projects/40416335/phase10ac_data/Semantic_Link_Graph.csv"
rows = []
for post in posts:
    slug = post["slug"]
    outbound = len(link_graph.get(slug, set()))
    inbound = inbound_count.get(slug, 0)
    rows.append({
        "post_id": post["id"],
        "title": post["title"]["raw"][:60],
        "slug": slug,
        "outbound_links": outbound,
        "inbound_links": inbound,
        "link_health": "orphan" if inbound == 0 else "weak" if inbound == 1 else "healthy" if inbound <= 5 else "strong"
    })

rows.sort(key=lambda x: x["inbound_links"])

with open(graph_csv, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["post_id", "title", "slug", "outbound_links", "inbound_links", "link_health"])
    w.writeheader()
    w.writerows(rows)

print(f"\nSemantic graph saved to {graph_csv}")

results = []
updated_count = 0
links_added = 0

for cross_type, links_list in CROSS_CLUSTER_LINKS.items():
    for source_slug, target_slug, anchor_text, reason in links_list:
        if source_slug not in slug_to_post:
            continue
        if target_slug not in slug_to_post:
            continue

        source = slug_to_post[source_slug]
        content = source["content"]["raw"]

        target_url = f"https://pethubonline.com/{target_slug}/"
        if target_url in content:
            continue

        link_html = f'<a href="{target_url}">{anchor_text}</a>'

        see_also = f"""<!-- wp:paragraph -->
<p>See also: {link_html} — {reason.lower()}.</p>
<!-- /wp:paragraph -->"""

        if TRUST_BLOCK_MARKER in content:
            last_idx = content.rfind(TRUST_BLOCK_MARKER)
            new_content = content[:last_idx] + f"\n{see_also}\n\n" + content[last_idx:]
        else:
            new_content = content + f"\n\n{see_also}"

        result = update_post(source["id"], new_content)
        if "id" in result:
            updated_count += 1
            links_added += 1
            results.append({
                "source_id": source["id"],
                "source_slug": source_slug[:40],
                "target_slug": target_slug[:40],
                "anchor_text": anchor_text,
                "cross_type": cross_type,
                "status": "inserted"
            })
            print(f"  {source['id']}: {source_slug[:30]} -> {target_slug[:30]}")
        else:
            results.append({
                "source_id": source["id"],
                "source_slug": source_slug[:40],
                "target_slug": target_slug[:40],
                "anchor_text": anchor_text,
                "cross_type": cross_type,
                "status": "error"
            })
        time.sleep(2)

cross_csv = "/var/lib/freelancer/projects/40416335/phase10ac_data/Cross_Cluster_Links.csv"
with open(cross_csv, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["source_id", "source_slug", "target_slug", "anchor_text", "cross_type", "status"])
    w.writeheader()
    w.writerows(results)

print(f"\n=== SEMANTIC GRAPH: {links_added} cross-cluster links inserted across {updated_count} posts ===")
print(f"=== Graph: {len(orphans)} orphans, {len(weak)} weak, {len(all_slugs) - len(orphans) - len(weak)} healthy ===")
