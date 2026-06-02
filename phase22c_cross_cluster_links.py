#!/usr/bin/env python3
"""Phase 22C: Cross-Cluster Authority Transfer
Adds 'Explore More PetHub Guides' blocks at the end of strong cluster posts
linking to weaker clusters to transfer authority."""

import requests, json, time, re, random, html
from datetime import datetime

WP = "https://pethubonline.com/wp-json/wp/v2"
AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
HEADERS = {"Accept-Encoding": "gzip, deflate"}

LINK_BLOCK = """
<!-- wp:group {{"style":{{"border":{{"width":"1px"}},"spacing":{{"padding":{{"top":"20px","bottom":"20px","left":"24px","right":"24px"}}}}}},"borderColor":"cyan-bluish-gray"}} -->
<div class="wp-block-group has-border-color has-cyan-bluish-gray-border-color" style="border-width:1px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px">
<p><strong>Explore More PetHub Guides</strong></p>
<ul>
{links}
</ul>
</div>
<!-- /wp:group -->
"""

CLUSTER_MAP = {
    1391: "Pet Health",
    1474: "Training Supplies",
    1422: "Dog Harnesses",
    1467: "Dog Food",
    1489: "Dog Care",
    1413: "Indoor Cats",
    1443: "Enrichment Activities",
}

STRONG_CATS = [1376, 1397, 1450, 1377, 1442, 1401]


def fetch_posts(cat_id, per_page=100, status="publish"):
    posts = []
    page = 1
    while True:
        r = requests.get(f"{WP}/posts", params={
            "categories": cat_id, "status": status, "per_page": per_page,
            "page": page, "_fields": "id,title,link,content"
        }, auth=AUTH, headers=HEADERS)
        if r.status_code != 200:
            break
        batch = r.json()
        if not batch:
            break
        posts.extend(batch)
        page += 1
        time.sleep(0.5)
    return posts


def has_explore_block(content):
    return "Explore More PetHub Guides" in content


def build_link_block(target_posts, count=3):
    selected = random.sample(target_posts, min(count, len(target_posts)))
    links = ""
    for p in selected:
        title = html.unescape(p["title"]["rendered"])
        links += f'<li><a href="{p["link"]}">{title}</a></li>\n'
    return LINK_BLOCK.format(links=links)


def update_post(post_id, content):
    for attempt in range(3):
        r = requests.post(f"{WP}/posts/{post_id}",
            json={"content": content}, auth=AUTH, headers=HEADERS)
        if r.status_code == 200:
            return True
        if r.status_code == 429:
            time.sleep(10)
            continue
        print(f"    Error {r.status_code} updating {post_id}")
        return False
    return False


def main():
    print("=" * 60)
    print("PHASE 22C: CROSS-CLUSTER AUTHORITY TRANSFER")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    weak_posts = {}
    for cat_id, name in CLUSTER_MAP.items():
        posts = fetch_posts(cat_id)
        weak_posts[name] = posts
        print(f"  Weak cluster: {name} = {len(posts)} posts")

    all_weak = []
    for name, posts in weak_posts.items():
        all_weak.extend(posts)
    print(f"  Total weak cluster posts: {len(all_weak)}")

    if not all_weak:
        print("No weak cluster posts found. Exiting.")
        return

    results = {
        "phase": "22C",
        "timestamp": datetime.now().isoformat(),
        "posts_updated": 0,
        "posts_skipped": 0,
        "posts_already_linked": 0,
        "errors": 0,
        "transfers": [],
    }

    for cat_id in STRONG_CATS:
        strong = fetch_posts(cat_id, per_page=20)
        cat_name = {1376: "Dog Supplies", 1397: "Pet Care", 1450: "Dog Health",
                    1377: "Cat Supplies", 1442: "Puppy Care", 1401: "Dog Beds"}[cat_id]
        print(f"\nProcessing {cat_name} ({len(strong)} posts, using top 20)...")

        for i, post in enumerate(strong[:20]):
            pid = post["id"]
            title = html.unescape(post["title"]["rendered"])
            content = post["content"]["rendered"]

            if has_explore_block(content):
                results["posts_already_linked"] += 1
                continue

            link_block = build_link_block(all_weak, count=3)
            new_content = content + "\n" + link_block

            if update_post(pid, new_content):
                results["posts_updated"] += 1
                results["transfers"].append({
                    "source_id": pid,
                    "source_title": title,
                    "source_cluster": cat_name,
                })
                print(f"  [{i+1}] {title[:50]}... -> 3 cross-links added")
            else:
                results["errors"] += 1
                print(f"  [{i+1}] {title[:50]}... -> FAILED")
            time.sleep(1.5)

    print(f"\n{'=' * 60}")
    print(f"CROSS-CLUSTER TRANSFER COMPLETE")
    print(f"Posts updated: {results['posts_updated']}")
    print(f"Already linked: {results['posts_already_linked']}")
    print(f"Errors: {results['errors']}")

    with open("/var/lib/freelancer/projects/40416335/phase22c_cross_cluster_results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
