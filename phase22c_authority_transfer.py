#!/usr/bin/env python3
"""Phase 22C: Authority Transfer Engine
Links from top 50 authority pages to weak cluster pages to transfer link equity."""

import requests, json, time, re, random
from datetime import datetime

WP = "https://pethubonline.com/wp-json/wp/v2"
AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
HEADERS = {"Accept-Encoding": "gzip, deflate"}

STRONG_CATS = {
    1450: "Dog Health",
    1449: "Dog Supplies",
    1448: "Cat Supplies",
}

WEAK_CATS = {
    1456: "Dog Harnesses",
    1457: "Dog Food",
    1458: "Pet Health",
    1455: "Fish Supplies",
}

TOPIC_LINKS = {
    "Dog Harnesses": [
        ("dog harness", "best dog harness"),
        ("harness for dogs", "dog harnesses"),
        ("walking harness", "harness guide"),
        ("no-pull harness", "harness fitting"),
    ],
    "Dog Food": [
        ("dog food", "best dog food"),
        ("dog nutrition", "feeding your dog"),
        ("dog diet", "raw dog food"),
    ],
    "Pet Health": [
        ("pet health", "pet wellness"),
        ("veterinary care", "vet visits"),
        ("pet insurance", "health check"),
    ],
    "Fish Supplies": [
        ("fish tank", "aquarium"),
        ("fish food", "fish supplies"),
        ("fish care", "fishkeeping"),
    ],
}


def fetch_all_posts(cat_id, status="publish"):
    posts = []
    page = 1
    while True:
        r = requests.get(
            f"{WP}/posts",
            params={"categories": cat_id, "status": status, "per_page": 100, "page": page,
                    "_fields": "id,title,link,content"},
            auth=AUTH, headers=HEADERS
        )
        if r.status_code != 200:
            break
        batch = r.json()
        if not batch:
            break
        posts.extend(batch)
        page += 1
        time.sleep(0.5)
    return posts


def fetch_weak_cluster_targets():
    targets = {}
    for cat_id, name in WEAK_CATS.items():
        posts = fetch_all_posts(cat_id)
        targets[name] = [(p["id"], p["title"]["rendered"], p["link"]) for p in posts]
        print(f"  {name}: {len(posts)} posts")
    return targets


def find_link_opportunities(content, target_url, target_title, keywords):
    content_lower = content.lower()
    if target_url in content:
        return None
    for kw in keywords:
        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        matches = list(pattern.finditer(content))
        valid = []
        for m in matches:
            start = max(0, m.start() - 50)
            context = content[start:m.end() + 50]
            if '<a ' not in context or '</a>' not in context:
                valid.append(m)
        if valid:
            match = valid[0]
            original = content[match.start():match.end()]
            link_html = f'<a href="{target_url}" title="{target_title}">{original}</a>'
            new_content = content[:match.start()] + link_html + content[match.end():]
            return new_content
    return None


def update_post(post_id, content):
    for attempt in range(3):
        r = requests.post(
            f"{WP}/posts/{post_id}",
            json={"content": content},
            auth=AUTH, headers=HEADERS
        )
        if r.status_code == 200:
            return True
        if r.status_code == 429:
            time.sleep(10)
            continue
        print(f"    Error {r.status_code} updating post {post_id}")
        return False
    return False


def main():
    print("=" * 60)
    print("PHASE 22C: AUTHORITY TRANSFER ENGINE")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    print("\nFetching weak cluster targets...")
    targets = fetch_weak_cluster_targets()

    print("\nFetching strong cluster posts (top 50 by authority)...")
    strong_posts = []
    for cat_id, name in STRONG_CATS.items():
        posts = fetch_all_posts(cat_id)
        for p in posts:
            p["_cluster"] = name
        strong_posts.extend(posts)
        print(f"  {name}: {len(posts)} posts")

    strong_posts.sort(key=lambda p: len(p.get("content", {}).get("rendered", "")), reverse=True)
    top50 = strong_posts[:50]
    print(f"\nSelected top 50 authority pages (by content length)")

    results = {
        "phase": "22C",
        "timestamp": datetime.now().isoformat(),
        "transfers": [],
        "total_links_added": 0,
        "posts_updated": 0,
        "errors": 0,
    }

    for i, post in enumerate(top50):
        pid = post["id"]
        title = post["title"]["rendered"]
        content = post["content"]["rendered"]
        cluster = post["_cluster"]
        links_added = 0

        for weak_name, weak_posts in targets.items():
            if not weak_posts:
                continue
            keywords = []
            for kw_pair in TOPIC_LINKS.get(weak_name, []):
                keywords.extend(kw_pair)

            target = random.choice(weak_posts)
            target_id, target_title, target_url = target

            new_content = find_link_opportunities(content, target_url, target_title, keywords)
            if new_content:
                content = new_content
                links_added += 1

        if links_added > 0:
            if update_post(pid, content):
                results["transfers"].append({
                    "source_id": pid,
                    "source_title": title,
                    "source_cluster": cluster,
                    "links_added": links_added,
                })
                results["total_links_added"] += links_added
                results["posts_updated"] += 1
                print(f"  [{i+1}/50] {title[:50]}... -> {links_added} links added")
            else:
                results["errors"] += 1
                print(f"  [{i+1}/50] {title[:50]}... -> UPDATE FAILED")
        else:
            print(f"  [{i+1}/50] {title[:50]}... -> no keyword matches")

        time.sleep(1)

    print(f"\n{'=' * 60}")
    print(f"AUTHORITY TRANSFER COMPLETE")
    print(f"Posts updated: {results['posts_updated']}")
    print(f"Total links added: {results['total_links_added']}")
    print(f"Errors: {results['errors']}")
    print(f"{'=' * 60}")

    with open("/var/lib/freelancer/projects/40416335/phase22c_authority_transfer_results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
