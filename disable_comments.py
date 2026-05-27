#!/usr/bin/env python3
"""
Script 2: Disable comments on non-blog pages on pethubonline.com
Targets specific page IDs + category hub pages.
"""

import requests
import json
import sys
from datetime import datetime

BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
LOG_FILE = "/var/lib/freelancer/projects/40416335/phase10d/disable_comments.log"

# Specific pages to disable comments on
TARGET_PAGES = {
    39: "About Us",
    300: "Affiliate Disclosure",
    4402: "How We Research Pet Products",
    4403: "Our Editorial Process",
    4405: "Corrections and Updates Policy",
    63: "Dog Supplies",
    1041: "Dog Toys",
    37: "Cat Supplies (verify)",
    38: "Unknown (verify)",
}

# Keywords to identify category/hub pages
HUB_KEYWORDS = [
    "supplies", "category", "hub", "products", "shop",
    "toys", "food", "health", "grooming", "training",
    "accessories", "beds", "bowls", "feeders", "treats",
    "collars", "leashes", "harnesses", "crates", "carriers"
]

results = []


def log(msg):
    print(msg)
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")


def get_session():
    s = requests.Session()
    s.auth = AUTH
    s.headers['Accept-Encoding'] = 'gzip, deflate'
    return s


def fetch_all_pages():
    """Fetch all published pages."""
    pages = []
    page_num = 1
    while True:
        s = get_session()
        resp = s.get(f"{BASE}/pages", params={
            "per_page": 100,
            "page": page_num,
            "status": "publish"
        })
        if resp.status_code == 400:
            break
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        pages.extend(data)
        total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
        if page_num >= total_pages:
            break
        page_num += 1
    return pages


def check_and_disable_comments(page_id, expected_title=None):
    """Check comment status and disable if open."""
    s = get_session()
    resp = s.get(f"{BASE}/pages/{page_id}", params={"context": "edit"})

    if resp.status_code == 404:
        log(f"  Page #{page_id}: NOT FOUND (404)")
        results.append({"id": page_id, "expected": expected_title, "status": "not_found"})
        return False

    if resp.status_code != 200:
        log(f"  Page #{page_id}: ERROR fetching - {resp.status_code}")
        results.append({"id": page_id, "expected": expected_title, "status": f"error_{resp.status_code}"})
        return False

    page = resp.json()
    actual_title = page["title"]["raw"]
    comment_status = page.get("comment_status", "unknown")

    if expected_title and expected_title not in ("Unknown (verify)", "Cat Supplies (verify)"):
        log(f"  Page #{page_id} '{actual_title}' (expected: {expected_title}) - comments: {comment_status}")
    else:
        log(f"  Page #{page_id} '{actual_title}' - comments: {comment_status}")

    if comment_status == "open":
        s2 = get_session()
        update_resp = s2.post(
            f"{BASE}/pages/{page_id}",
            json={"comment_status": "closed"}
        )
        if update_resp.status_code == 200:
            log(f"    -> CLOSED comments on page #{page_id} '{actual_title}'")
            results.append({
                "id": page_id,
                "title": actual_title,
                "action": "closed",
                "was": "open"
            })
            return True
        else:
            log(f"    -> ERROR closing comments: {update_resp.status_code} - {update_resp.text[:200]}")
            results.append({
                "id": page_id,
                "title": actual_title,
                "action": "error",
                "error": update_resp.text[:200]
            })
            return False
    else:
        log(f"    -> Already closed (no action needed)")
        results.append({
            "id": page_id,
            "title": actual_title,
            "action": "already_closed",
            "was": comment_status
        })
        return False


def is_hub_page(page):
    """Check if a page looks like a category/hub page based on title and slug."""
    title = page["title"]["rendered"].lower()
    slug = page["slug"].lower()
    combined = title + " " + slug

    for keyword in HUB_KEYWORDS:
        if keyword in combined:
            return True
    return False


def main():
    start = datetime.now()
    with open(LOG_FILE, "w") as f:
        f.write(f"=== Disable Comments Script - {start.isoformat()} ===\n\n")

    # Step 1: Process specific target pages
    log("=== Processing specific target pages ===\n")
    for page_id, expected_title in TARGET_PAGES.items():
        check_and_disable_comments(page_id, expected_title)

    # Step 2: Fetch all pages and find hub/category pages
    log("\n=== Fetching all pages to find category/hub pages ===\n")
    all_pages = fetch_all_pages()
    log(f"Total published pages: {len(all_pages)}\n")

    # Track IDs already processed
    processed_ids = set(TARGET_PAGES.keys())

    hub_pages_found = []
    for page in all_pages:
        if page["id"] in processed_ids:
            continue
        if is_hub_page(page):
            hub_pages_found.append(page)

    log(f"Found {len(hub_pages_found)} additional hub/category pages:\n")
    for page in hub_pages_found:
        log(f"  Candidate: #{page['id']} '{page['title']['rendered']}' (/{page['slug']})")

    log("\n=== Disabling comments on hub/category pages ===\n")
    for page in hub_pages_found:
        check_and_disable_comments(page["id"], page["title"]["rendered"])
        processed_ids.add(page["id"])

    # Summary
    log("\n" + "=" * 60)
    log("SUMMARY")
    log("=" * 60)
    closed_count = sum(1 for r in results if r.get("action") == "closed")
    already_closed = sum(1 for r in results if r.get("action") == "already_closed")
    not_found = sum(1 for r in results if r.get("status") == "not_found")
    errors = sum(1 for r in results if r.get("action") == "error" or (r.get("status", "").startswith("error")))

    log(f"Pages processed: {len(results)}")
    log(f"Comments closed: {closed_count}")
    log(f"Already closed: {already_closed}")
    log(f"Not found: {not_found}")
    log(f"Errors: {errors}")

    if closed_count > 0:
        log("\nPages where comments were closed:")
        for r in results:
            if r.get("action") == "closed":
                log(f"  #{r['id']} '{r.get('title', 'N/A')}'")

    end = datetime.now()
    log(f"\nCompleted in {(end - start).total_seconds():.1f}s")

    # Save structured results
    output = {
        "timestamp": start.isoformat(),
        "results": results,
        "summary": {
            "total_processed": len(results),
            "comments_closed": closed_count,
            "already_closed": already_closed,
            "not_found": not_found,
            "errors": errors
        }
    }
    json_file = LOG_FILE.replace(".log", ".json")
    with open(json_file, "w") as f:
        json.dump(output, f, indent=2)

    log(f"\nResults saved to {LOG_FILE} and {json_file}")


if __name__ == "__main__":
    main()
