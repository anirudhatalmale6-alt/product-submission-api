#!/usr/bin/env python3
"""Add internal links between Phase 21X posts and existing content."""

import requests
import json
import time
import re

WP_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
HEADERS = {"Accept-Encoding": "gzip, deflate"}

LINK_MAP = {
    1450: {  # Dog Health
        "label": "Dog Health",
        "related_cats": [1376, 1489, 1442, 1391, 1487],  # Dog Supplies, Dog Care, Puppy Care, Pet Health, Health & Wellness
        "hub_text": "Browse all Dog Health guides",
    },
    1376: {  # Dog Supplies
        "label": "Dog Supplies",
        "related_cats": [1450, 1401, 1422, 1489, 1510],  # Dog Health, Dog Beds, Dog Harnesses, Dog Care, Dog Accessories
        "hub_text": "Browse all Dog Supplies guides",
    },
    1377: {  # Cat Supplies
        "label": "Cat Supplies",
        "related_cats": [1459, 1413, 1397],  # Cat Toys, Indoor Cats, Pet Care
        "hub_text": "Browse all Cat Supplies guides",
    },
}

def fetch_posts_by_category(session, cat_id, per_page=100):
    """Fetch all posts in a category."""
    posts = []
    page = 1
    while True:
        r = session.get(f"{WP_URL}/posts", params={
            "categories": cat_id, "per_page": per_page, "page": page,
            "_fields": "id,title,link,categories", "status": "publish"
        })
        if r.status_code != 200:
            break
        batch = r.json()
        if not batch:
            break
        posts.extend(batch)
        if len(batch) < per_page:
            break
        page += 1
    return posts

def fetch_related_posts(session, cat_ids, limit=5):
    """Fetch a few posts from related categories for cross-linking."""
    related = []
    for cat_id in cat_ids[:3]:
        r = session.get(f"{WP_URL}/posts", params={
            "categories": cat_id, "per_page": limit, "orderby": "date", "order": "desc",
            "_fields": "id,title,link", "status": "publish"
        })
        if r.status_code == 200:
            related.extend(r.json())
        time.sleep(0.5)
    return related

def add_internal_links(session, post_id, same_cat_posts, related_posts):
    """Add internal links block to a post's content."""
    r = session.get(f"{WP_URL}/posts/{post_id}", params={"_fields": "id,content,categories"})
    if r.status_code != 200:
        return False
    post = r.json()
    content = post["content"]["rendered"]

    # Skip if already has internal links section
    if "Related Guides" in content or "You May Also Like" in content:
        return True

    # Pick 3 same-category links and 2 cross-category links
    same_links = [p for p in same_cat_posts if p["id"] != post_id][:3]
    cross_links = related_posts[:2]

    if not same_links and not cross_links:
        return True

    links_html = '\n<!-- wp:heading -->\n<h2 class="wp-block-heading">Related Guides</h2>\n<!-- /wp:heading -->\n\n<!-- wp:list -->\n<ul class="wp-block-list">\n'

    for p in same_links:
        title = p["title"]["rendered"] if isinstance(p["title"], dict) else p["title"]
        links_html += f'<li><a href="{p["link"]}">{title}</a></li>\n'

    for p in cross_links:
        title = p["title"]["rendered"] if isinstance(p["title"], dict) else p["title"]
        links_html += f'<li><a href="{p["link"]}">{title}</a></li>\n'

    links_html += '</ul>\n<!-- /wp:list -->\n'

    # Insert before the Author Box / CTA section
    insertion_point = content.find("Written by the PetHub Online editorial team")
    if insertion_point == -1:
        insertion_point = content.find("Explore more")

    if insertion_point > 0:
        # Find the start of the wp:group containing the author box
        search_back = content[:insertion_point].rfind("<!-- wp:group")
        if search_back > 0:
            new_content = content[:search_back] + links_html + "\n" + content[search_back:]
        else:
            new_content = content + "\n" + links_html
    else:
        new_content = content + "\n" + links_html

    # Get raw content for API update
    r2 = session.get(f"{WP_URL}/posts/{post_id}", params={"_fields": "id,content", "context": "edit"})
    if r2.status_code != 200:
        return False
    raw_content = r2.json()["content"]["raw"]

    insertion_point_raw = raw_content.find("Written by the PetHub Online editorial team")
    if insertion_point_raw == -1:
        insertion_point_raw = raw_content.find("Explore more")

    if insertion_point_raw > 0:
        search_back = raw_content[:insertion_point_raw].rfind("<!-- wp:group")
        if search_back > 0:
            new_raw = raw_content[:search_back] + links_html + "\n" + raw_content[search_back:]
        else:
            new_raw = raw_content + "\n" + links_html
    else:
        new_raw = raw_content + "\n" + links_html

    r3 = session.post(f"{WP_URL}/posts/{post_id}", json={"content": new_raw})
    return r3.status_code == 200


def main():
    session = requests.Session()
    session.auth = AUTH
    session.headers.update(HEADERS)

    # Load Phase 21X post IDs
    new_post_ids = set()
    for fname in ["dog_health_expansion_results.json", "dog_supplies_expansion_results.json", "cat_supplies_expansion_results.json"]:
        fpath = f"/var/lib/freelancer/projects/40416335/{fname}"
        try:
            data = json.load(open(fpath))
            for p in data["posts"]:
                new_post_ids.add(p["id"])
        except:
            pass

    print(f"Phase 21X posts to link: {len(new_post_ids)}")

    results = {"linked": 0, "skipped": 0, "errors": 0}

    for cat_id, cat_info in LINK_MAP.items():
        print(f"\nProcessing category: {cat_info['label']} (ID={cat_id})")

        same_cat_posts = fetch_posts_by_category(session, cat_id)
        print(f"  Posts in category: {len(same_cat_posts)}")

        related_posts = fetch_related_posts(session, cat_info["related_cats"], limit=3)
        print(f"  Related posts found: {len(related_posts)}")

        # Only link new Phase 21X posts
        new_in_cat = [p for p in same_cat_posts if p["id"] in new_post_ids]
        print(f"  New Phase 21X posts to link: {len(new_in_cat)}")

        for i, post in enumerate(new_in_cat):
            try:
                pid = post["id"]
                title = post["title"]["rendered"] if isinstance(post["title"], dict) else post["title"]
                print(f"  [{i+1}/{len(new_in_cat)}] Linking ID={pid}: {title[:50]}...")

                if add_internal_links(session, pid, same_cat_posts, related_posts):
                    results["linked"] += 1
                else:
                    results["errors"] += 1

                time.sleep(2)
            except Exception as e:
                print(f"    ERROR: {e}")
                results["errors"] += 1
                time.sleep(3)

    print(f"\nResults: {results['linked']} linked, {results['errors']} errors")

    with open("/var/lib/freelancer/projects/40416335/phase21x_internal_links_results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
