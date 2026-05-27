#!/usr/bin/env python3
"""
fix_internal_links.py - Add bidirectional internal links between hub pages and related posts.

Each hub page gets a "Related Articles" section at the bottom linking to its related posts.
Each post gets a "Part of our [Hub] guide" link after the first paragraph or Quick Summary.
"""

import requests
import re
import time
import json

# WordPress API credentials
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_API = "https://pethubonline.com/wp-json/wp/v2"

# Hub page definitions: page_id -> (hub_name, category_ids, title_keywords)
HUB_PAGES = {
    1149: {
        "name": "Cat Toys",
        "slug": "cat-toys",
        "category_ids": [1459],
        "title_keywords": ["cat toy"],
    },
    1041: {
        "name": "Dog Toys",
        "slug": "dog-toys",
        "category_ids": [1441],
        "title_keywords": ["dog toy"],
    },
    1141: {
        "name": "Dog Beds",
        "slug": "dog-beds",
        "category_ids": [1401],
        "title_keywords": ["dog bed"],
    },
    1146: {
        "name": "Dog Collars & Leashes",
        "slug": "dog-collars-leashes",
        "category_ids": [1422],
        "title_keywords": ["dog collar", "dog lead", "dog harness", "harness vs collar"],
    },
    1951: {
        "name": "Dog Bowls & Feeding",
        "slug": "dog-bowls-feeding",
        "category_ids": [],
        "title_keywords": ["dog bowl", "dog water bottle", "slow feeder"],
    },
    3107: {
        "name": "Cat Beds",
        "slug": "cat-beds",
        "category_ids": [],
        "title_keywords": ["cat bed", "cat radiator", "cat window perch", "heated cat"],
    },
    3109: {
        "name": "Cat Grooming",
        "slug": "cat-grooming",
        "category_ids": [],
        "title_keywords": ["cat groom", "cat brush", "cat nail", "cat shampoo"],
    },
    3111: {
        "name": "Cat Collars",
        "slug": "cat-collars",
        "category_ids": [],
        "title_keywords": ["cat collar", "cat tag", "cat gps", "cat harness"],
    },
    3113: {
        "name": "Cat Scratching Posts",
        "slug": "cat-scratching-posts",
        "category_ids": [],
        "title_keywords": ["cat scratch", "cat tree", "cardboard cat", "wall-mounted cat"],
    },
    3115: {
        "name": "Cat Litter Trays",
        "slug": "cat-litter-trays",
        "category_ids": [],
        "title_keywords": ["cat litter", "litter tray", "self-cleaning litter", "litter disposal"],
    },
    1144: {
        "name": "Dog Grooming",
        "slug": "dog-grooming",
        "category_ids": [],
        "title_keywords": ["dog groom", "dog brush", "dog shampoo", "dog nail"],
    },
    1956: {
        "name": "Dog Training & Behaviour",
        "slug": "dog-training-behaviour",
        "category_ids": [1474],
        "title_keywords": ["dog train", "puppy train", "toilet train"],
    },
    1960: {
        "name": "Dog Health & Care",
        "slug": "dog-health-care",
        "category_ids": [1450],
        "title_keywords": ["dog health", "dog dental", "dog flea", "dog joint"],
    },
    3892: {
        "name": "Best Dog Food & Puppy Food UK",
        "slug": "best-dog-food-puppy-food-uk",
        "category_ids": [1467],
        "title_keywords": ["dog food", "puppy food", "dry vs wet"],
    },
}

# Specificity ordering: more specific hubs should win over general ones
# Higher number = more specific
SPECIFICITY = {
    1149: 5,  # Cat Toys
    1041: 5,  # Dog Toys
    1141: 5,  # Dog Beds
    1146: 5,  # Dog Collars & Leashes
    1951: 5,  # Dog Bowls & Feeding
    3107: 5,  # Cat Beds
    3109: 5,  # Cat Grooming
    3111: 5,  # Cat Collars
    3113: 6,  # Cat Scratching Posts (more specific)
    3115: 6,  # Cat Litter Trays (more specific)
    1144: 5,  # Dog Grooming
    1956: 5,  # Dog Training & Behaviour
    1960: 5,  # Dog Health & Care
    3892: 5,  # Best Dog Food & Puppy Food UK
}


def create_session():
    """Create an authenticated requests session."""
    s = requests.Session()
    s.auth = (WP_USER, WP_PASS)
    s.headers["Accept-Encoding"] = "gzip, deflate"
    s.headers["User-Agent"] = "PetHub-Internal-Links/1.0"
    return s


def fetch_all_paginated(session, url, params=None):
    """Fetch all items from a paginated WP REST API endpoint."""
    if params is None:
        params = {}
    params.setdefault("per_page", 100)
    params.setdefault("page", 1)

    all_items = []
    while True:
        resp = session.get(url, params=params)
        if resp.status_code != 200:
            print(f"  Error fetching {url} page {params['page']}: {resp.status_code}")
            break
        items = resp.json()
        if not items:
            break
        all_items.extend(items)
        total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
        if params["page"] >= total_pages:
            break
        params["page"] += 1
        time.sleep(0.3)

    return all_items


def fetch_pages(session):
    """Fetch all published pages with raw content."""
    print("Fetching all published pages (context=edit)...")
    pages = fetch_all_paginated(
        session,
        f"{WP_API}/pages",
        {"status": "publish", "context": "edit", "per_page": 100},
    )
    print(f"  Fetched {len(pages)} published pages")
    return pages


def fetch_posts(session):
    """Fetch all published + draft posts with raw content."""
    print("Fetching all published posts (context=edit)...")
    published = fetch_all_paginated(
        session,
        f"{WP_API}/posts",
        {"status": "publish", "context": "edit", "per_page": 100},
    )
    print(f"  Fetched {len(published)} published posts")

    print("Fetching all draft posts (context=edit)...")
    drafts = fetch_all_paginated(
        session,
        f"{WP_API}/posts",
        {"status": "draft", "context": "edit", "per_page": 100},
    )
    print(f"  Fetched {len(drafts)} draft posts")

    return published, drafts


def match_post_to_hub(post, all_hubs):
    """Determine which hub page a post belongs to. Returns hub_page_id or None."""
    title_lower = post["title"]["raw"].lower()
    post_categories = post.get("categories", [])

    matches = []

    for page_id, hub in all_hubs.items():
        matched = False

        # Check category match
        for cat_id in hub["category_ids"]:
            if cat_id in post_categories:
                matched = True
                break

        # Check title keyword match
        if not matched:
            for keyword in hub["title_keywords"]:
                if keyword in title_lower:
                    matched = True
                    break

        if matched:
            matches.append(page_id)

    if not matches:
        return None

    if len(matches) == 1:
        return matches[0]

    # Multiple matches - pick most specific
    best = max(matches, key=lambda pid: SPECIFICITY.get(pid, 0))
    return best


def has_related_articles_section(content):
    """Check if page content already has a Related Articles section."""
    return "Related Articles" in content


def has_hub_backlink(content, hub_url):
    """Check if post content already links to the hub page."""
    return hub_url in content


def build_related_articles_block(posts_for_hub):
    """Build Gutenberg blocks for Related Articles section."""
    list_items = []
    for post in posts_for_hub:
        title = post["title"]["raw"]
        url = post["link"]
        list_items.append(f'<li><a href="{url}">{title}</a></li>')

    items_html = "\n".join(list_items)

    block = f"""

<!-- wp:heading {{"level":2}} -->
<h2 class="wp-block-heading">Related Articles</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul class="wp-block-list">
{items_html}
</ul>
<!-- /wp:list -->"""

    return block


def build_hub_backlink_block(hub_name, hub_url):
    """Build Gutenberg block for the hub backlink in posts."""
    block = f"""
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"0.95em"}}}}}} -->
<p style="font-size:0.95em"><strong>Part of our <a href="{hub_url}">{hub_name}</a> guide.</strong></p>
<!-- /wp:paragraph -->
"""
    return block


def insert_backlink_after_first_para_or_summary(content, backlink_block):
    """Insert backlink after Quick Summary or first paragraph."""
    # Check for Quick Summary block end
    summary_pattern = r'(<!-- /wp:group -->)'
    # Check for a "Quick Summary" heading followed by a group block
    quick_summary_match = re.search(
        r'(?i)(quick\s+summary|key\s+takeaway|at\s+a\s+glance)',
        content[:2000]
    )

    if quick_summary_match:
        # Find the closing of the group block or details block after the summary
        # Try to find <!-- /wp:group --> after the summary heading
        summary_pos = quick_summary_match.end()
        # Look for the next <!-- /wp:group --> after the summary
        group_end = content.find("<!-- /wp:group -->", summary_pos)
        if group_end != -1:
            insert_pos = group_end + len("<!-- /wp:group -->")
            return content[:insert_pos] + "\n" + backlink_block + content[insert_pos:]

    # Otherwise insert after first <!-- /wp:paragraph -->
    first_para_end = content.find("<!-- /wp:paragraph -->")
    if first_para_end != -1:
        insert_pos = first_para_end + len("<!-- /wp:paragraph -->")
        return content[:insert_pos] + "\n" + backlink_block + content[insert_pos:]

    # Fallback: prepend
    return backlink_block + "\n" + content


def update_page_content(session, page_id, new_content):
    """Update a page's content via the WP REST API."""
    resp = session.post(
        f"{WP_API}/pages/{page_id}",
        json={"content": new_content},
    )
    return resp.status_code, resp.text


def update_post_content(session, post_id, new_content):
    """Update a post's content via the WP REST API."""
    resp = session.post(
        f"{WP_API}/posts/{post_id}",
        json={"content": new_content},
    )
    return resp.status_code, resp.text


def main():
    session = create_session()

    # Step 1: Fetch all pages and posts
    pages = fetch_pages(session)
    published_posts, draft_posts = fetch_posts(session)
    all_posts = published_posts + draft_posts

    # Build lookup dictionaries
    pages_by_id = {p["id"]: p for p in pages}
    published_posts_by_id = {p["id"]: p for p in published_posts}

    # Step 2: Map posts to hub pages
    print("\n--- Mapping posts to hub pages ---")
    hub_to_posts = {pid: [] for pid in HUB_PAGES}
    post_to_hub = {}
    unmatched_posts = []

    for post in all_posts:
        hub_id = match_post_to_hub(post, HUB_PAGES)
        if hub_id:
            hub_to_posts[hub_id].append(post)
            post_to_hub[post["id"]] = hub_id
        else:
            unmatched_posts.append(post)

    for hub_id, posts in hub_to_posts.items():
        hub_name = HUB_PAGES[hub_id]["name"]
        pub_count = sum(1 for p in posts if p["status"] == "publish")
        draft_count = sum(1 for p in posts if p["status"] == "draft")
        print(f"  {hub_name} (page {hub_id}): {pub_count} published, {draft_count} draft posts")

    print(f"  Unmatched posts: {len(unmatched_posts)}")
    for p in unmatched_posts:
        print(f"    - [{p['id']}] {p['title']['raw']} (status: {p['status']})")

    # Step 3: Update hub pages with Related Articles sections
    print("\n--- Updating hub pages with Related Articles ---")
    pages_updated = 0
    pages_skipped_already = []
    pages_skipped_no_posts = []
    pages_skipped_not_found = []
    hub_link_counts = {}

    for hub_id, hub_info in HUB_PAGES.items():
        hub_name = hub_info["name"]

        # Only link to published posts
        published_related = [p for p in hub_to_posts[hub_id] if p["status"] == "publish"]

        if not published_related:
            pages_skipped_no_posts.append(f"{hub_name} (page {hub_id})")
            print(f"  SKIP {hub_name}: no published related posts")
            continue

        if hub_id not in pages_by_id:
            pages_skipped_not_found.append(f"{hub_name} (page {hub_id})")
            print(f"  SKIP {hub_name}: page {hub_id} not found in fetched pages")
            continue

        page = pages_by_id[hub_id]
        content = page["content"]["raw"]

        if has_related_articles_section(content):
            pages_skipped_already.append(f"{hub_name} (page {hub_id})")
            print(f"  SKIP {hub_name}: already has Related Articles section")
            continue

        # Build and append Related Articles section
        related_block = build_related_articles_block(published_related)
        new_content = content + related_block

        status_code, resp_text = update_page_content(session, hub_id, new_content)
        if status_code == 200:
            pages_updated += 1
            hub_link_counts[hub_name] = len(published_related)
            print(f"  UPDATED {hub_name} (page {hub_id}): added {len(published_related)} article links")
        else:
            print(f"  ERROR updating {hub_name} (page {hub_id}): HTTP {status_code}")
            try:
                err = json.loads(resp_text)
                print(f"    {err.get('message', resp_text[:200])}")
            except:
                print(f"    {resp_text[:200]}")

        time.sleep(0.5)

    # Step 4: Update posts with hub backlinks
    print("\n--- Updating posts with hub backlinks ---")
    posts_updated = 0
    posts_skipped_already = []
    posts_skipped_draft = []
    posts_skipped_no_page = []

    for post in all_posts:
        post_id = post["id"]

        if post_id not in post_to_hub:
            continue

        hub_id = post_to_hub[post_id]

        if post["status"] != "publish":
            posts_skipped_draft.append(f"[{post_id}] {post['title']['raw']}")
            continue

        if hub_id not in pages_by_id:
            posts_skipped_no_page.append(f"[{post_id}] {post['title']['raw']} -> hub {hub_id}")
            continue

        hub_page = pages_by_id[hub_id]
        hub_name = HUB_PAGES[hub_id]["name"]
        hub_url = hub_page["link"]

        content = post["content"]["raw"]

        if has_hub_backlink(content, hub_url):
            posts_skipped_already.append(f"[{post_id}] {post['title']['raw']}")
            continue

        # Also check for hub name in a "Part of our" pattern
        if f"Part of our" in content and hub_name in content:
            posts_skipped_already.append(f"[{post_id}] {post['title']['raw']}")
            continue

        backlink_block = build_hub_backlink_block(hub_name, hub_url)
        new_content = insert_backlink_after_first_para_or_summary(content, backlink_block)

        status_code, resp_text = update_post_content(session, post_id, new_content)
        if status_code == 200:
            posts_updated += 1
            print(f"  UPDATED [{post_id}] {post['title']['raw']} -> {hub_name}")
        else:
            print(f"  ERROR [{post_id}] {post['title']['raw']}: HTTP {status_code}")
            try:
                err = json.loads(resp_text)
                print(f"    {err.get('message', resp_text[:200])}")
            except:
                print(f"    {resp_text[:200]}")

        time.sleep(0.5)

    # Step 6: Print comprehensive summary
    print("\n" + "=" * 70)
    print("COMPREHENSIVE SUMMARY")
    print("=" * 70)

    print(f"\n--- Hub Pages Updated: {pages_updated} ---")
    for hub_name, count in hub_link_counts.items():
        print(f"  {hub_name}: {count} article links added")

    print(f"\n--- Hub Pages Skipped ---")
    if pages_skipped_already:
        print(f"  Already had Related Articles ({len(pages_skipped_already)}):")
        for s in pages_skipped_already:
            print(f"    - {s}")
    if pages_skipped_no_posts:
        print(f"  No published related posts ({len(pages_skipped_no_posts)}):")
        for s in pages_skipped_no_posts:
            print(f"    - {s}")
    if pages_skipped_not_found:
        print(f"  Page not found ({len(pages_skipped_not_found)}):")
        for s in pages_skipped_not_found:
            print(f"    - {s}")

    print(f"\n--- Posts Updated with Backlinks: {posts_updated} ---")

    print(f"\n--- Posts Skipped ---")
    if posts_skipped_already:
        print(f"  Already had hub backlink ({len(posts_skipped_already)}):")
        for s in posts_skipped_already:
            print(f"    - {s}")
    if posts_skipped_draft:
        print(f"  Draft posts not modified ({len(posts_skipped_draft)}):")
        for s in posts_skipped_draft:
            print(f"    - {s}")
    if posts_skipped_no_page:
        print(f"  Hub page not found ({len(posts_skipped_no_page)}):")
        for s in posts_skipped_no_page:
            print(f"    - {s}")

    total_hub_links = sum(hub_link_counts.values())
    total_backlinks = posts_updated
    print(f"\n--- TOTALS ---")
    print(f"  Hub pages updated: {pages_updated}")
    print(f"  Total article links added to hub pages: {total_hub_links}")
    print(f"  Posts updated with backlinks: {total_backlinks}")
    print(f"  Total links added (both directions): {total_hub_links + total_backlinks}")
    print(f"  Unmatched posts: {len(unmatched_posts)}")


if __name__ == "__main__":
    main()
