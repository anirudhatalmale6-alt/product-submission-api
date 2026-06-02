#!/usr/bin/env python3
"""Fix orphan posts by adding inbound links from same-category posts."""

import requests
import json
import time
import re

WP_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
HEADERS = {"Accept-Encoding": "gzip, deflate"}

def main():
    s = requests.Session()
    s.auth = AUTH
    s.headers.update(HEADERS)

    # Load orphan data
    orphans = json.load(open("orphan_scan_phase21y.json"))["orphans"]
    print(f"Orphans to fix: {len(orphans)}")

    # Fetch all posts with categories
    all_posts = []
    page = 1
    while True:
        r = s.get(f"{WP_URL}/posts", params={
            "per_page": 100, "page": page, "status": "publish",
            "_fields": "id,title,link,categories"
        })
        if r.status_code != 200:
            break
        posts = r.json()
        if not posts:
            break
        all_posts.extend(posts)
        page += 1
        time.sleep(0.5)

    print(f"Total posts: {len(all_posts)}")

    # Group posts by category
    cat_posts = {}
    for p in all_posts:
        for cat in p["categories"]:
            cat_posts.setdefault(cat, []).append(p)

    orphan_ids = {o["id"] for o in orphans}
    fixed = 0
    links_added = 0
    errors = []

    for orphan in orphans:
        oid = orphan["id"]
        ocats = orphan["categories"]
        otitle = orphan["title"]

        # Find same-category non-orphan posts to add links FROM
        candidates = []
        for cat in ocats:
            for p in cat_posts.get(cat, []):
                if p["id"] != oid and p["id"] not in orphan_ids:
                    candidates.append(p)

        if not candidates:
            # Fallback: use any post from same category even if orphan
            for cat in ocats:
                for p in cat_posts.get(cat, []):
                    if p["id"] != oid:
                        candidates.append(p)

        if not candidates:
            print(f"  {oid}: No candidates found")
            errors.append(f"No candidates for {oid}")
            continue

        # Pick up to 2 candidates to add links from
        selected = candidates[:2]

        for source in selected:
            try:
                # Fetch source post raw content
                r = s.get(f"{WP_URL}/posts/{source['id']}", params={
                    "_fields": "id,content", "context": "edit"
                })
                if r.status_code != 200:
                    continue

                content = r.json()["content"]["raw"]

                # Check if already links to orphan
                orphan_post = next((p for p in all_posts if p["id"] == oid), None)
                if orphan_post and orphan_post["link"] in content:
                    continue

                # Add link in Related Guides section if exists, or before Author Box
                link_html = f'<li><a href="{orphan_post["link"]}">{otitle}</a></li>\n'

                if "Related Guides" in content:
                    # Add to existing Related Guides list
                    idx = content.find("Related Guides")
                    ul_start = content.find("<ul", idx)
                    ul_close = content.find("</ul>", ul_start)
                    if ul_close > 0:
                        content = content[:ul_close] + link_html + content[ul_close:]
                else:
                    # Add a Related Guides section before Author Box
                    related_block = f'\n<!-- wp:heading -->\n<h2 class="wp-block-heading">Related Guides</h2>\n<!-- /wp:heading -->\n\n<!-- wp:list -->\n<ul class="wp-block-list">\n{link_html}</ul>\n<!-- /wp:list -->\n\n'

                    inserted = False
                    for marker in ["Written by the PetHub Online", "Explore more", "Amazon Services"]:
                        idx = content.find(marker)
                        if idx > 0:
                            search_back = content[:idx].rfind("<!-- wp:")
                            if search_back > 0:
                                content = content[:search_back] + related_block + content[search_back:]
                                inserted = True
                                break

                    if not inserted:
                        content += related_block

                r2 = s.post(f"{WP_URL}/posts/{source['id']}", json={"content": content})
                if r2.status_code == 200:
                    links_added += 1
                else:
                    errors.append(f"Update {source['id']} failed: {r2.status_code}")

                time.sleep(2)

            except Exception as e:
                errors.append(f"Error linking to {oid} from {source['id']}: {str(e)}")
                time.sleep(3)

        fixed += 1
        if fixed % 10 == 0:
            print(f"  Progress: {fixed}/{len(orphans)} orphans processed, {links_added} links added")

    print(f"\nResults: {fixed}/{len(orphans)} orphans processed, {links_added} links added, {len(errors)} errors")

    with open("orphan_remediation_phase21y.json", "w") as f:
        json.dump({
            "total_orphans": len(orphans),
            "orphans_processed": fixed,
            "links_added": links_added,
            "errors_count": len(errors),
            "errors": errors[:20],
        }, f, indent=2)


if __name__ == "__main__":
    main()
