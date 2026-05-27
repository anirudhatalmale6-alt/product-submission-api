#!/usr/bin/env python3
"""
Script 1: Fix placeholder bugs on pethubonline.com
Scans ALL published posts and pages for placeholder patterns and fixes them.
"""

import requests
import re
import json
import sys
from datetime import datetime

BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
LOG_FILE = "/var/lib/freelancer/projects/40416335/phase10d/fix_placeholders.log"

# Patterns to find
PLACEHOLDER_RE = re.compile(r'\{(\w+)\}')  # any {placeholder_name}
VENDOR_COUNT_RE = re.compile(r'\{vendor_count\}')
TITLE_RE = re.compile(r'\{title\}')
LOADING_COMMENTS_RE = re.compile(r'loading comments', re.IGNORECASE)
# Empty section: heading tag followed by whitespace/newlines then another heading tag with no real content
EMPTY_SECTION_RE = re.compile(
    r'(<h[1-6][^>]*>.*?</h[1-6]>)\s*(<h[1-6][^>]*>)',
    re.IGNORECASE | re.DOTALL
)

findings = []
fixes_applied = []


def log(msg):
    print(msg)
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")


def fetch_all(endpoint):
    """Fetch all items from a paginated WP REST endpoint."""
    items = []
    page = 1
    while True:
        params = {"per_page": 100, "page": page, "status": "publish"}
        s = requests.Session()
        s.auth = AUTH
        s.headers['Accept-Encoding'] = 'gzip, deflate'
        resp = s.get(f"{BASE}/{endpoint}", params=params)
        if resp.status_code == 400:
            # No more pages
            break
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        items.extend(data)
        total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
        if page >= total_pages:
            break
        page += 1
    return items


def scan_and_fix_content(item, item_type):
    """Scan a post/page content for placeholders and fix them."""
    item_id = item["id"]
    title = item["title"]["rendered"]
    content = item["content"]["rendered"]
    raw_content = None

    # We need the raw content to edit it - fetch with edit context
    s = requests.Session()
    s.auth = AUTH
    s.headers['Accept-Encoding'] = 'gzip, deflate'
    detail_resp = s.get(f"{BASE}/{item_type}/{item_id}", params={"context": "edit"})
    if detail_resp.status_code != 200:
        log(f"  WARNING: Could not fetch edit context for {item_type} {item_id}: {detail_resp.status_code}")
        return False

    detail = detail_resp.json()
    raw_content = detail["content"]["raw"]
    raw_title = detail["title"]["raw"]
    original_content = raw_content
    changed = False
    item_findings = []

    # Check for {vendor_count}
    if VENDOR_COUNT_RE.search(raw_content):
        item_findings.append("{vendor_count}")
        # Remove sentences containing {vendor_count} or replace with empty string
        raw_content = re.sub(r'[^.!?\n]*\{vendor_count\}[^.!?\n]*[.!?]?\s*', '', raw_content)
        # If still present (e.g., standalone), just remove it
        raw_content = VENDOR_COUNT_RE.sub('', raw_content)
        changed = True

    # Check for {title}
    if TITLE_RE.search(raw_content):
        item_findings.append("{title}")
        raw_content = TITLE_RE.sub(raw_title, raw_content)
        changed = True

    # Check for "loading comments"
    if LOADING_COMMENTS_RE.search(raw_content):
        item_findings.append('"loading comments"')
        # Remove elements containing "loading comments"
        raw_content = re.sub(
            r'<[^>]*>[\s]*loading comments[\s]*</[^>]*>', '', raw_content, flags=re.IGNORECASE
        )
        # If it's plain text without tags
        raw_content = LOADING_COMMENTS_RE.sub('', raw_content)
        changed = True

    # Check for other {placeholder} patterns
    other_placeholders = PLACEHOLDER_RE.findall(raw_content)
    # Filter out known non-placeholder patterns (CSS/JS curly braces, etc.)
    skip_names = {'vendor_count', 'title'}
    for ph in other_placeholders:
        if ph not in skip_names and not ph.startswith('0x') and len(ph) > 1:
            item_findings.append(f"{{{ph}}}")

    # Check for empty sections
    empty_matches = EMPTY_SECTION_RE.findall(raw_content)
    if empty_matches:
        item_findings.append(f"empty sections ({len(empty_matches)} found)")

    if item_findings:
        finding_str = ", ".join(item_findings)
        findings.append({
            "id": item_id,
            "type": item_type,
            "title": title,
            "findings": item_findings
        })
        log(f"  FOUND in {item_type} #{item_id} '{title}': {finding_str}")

    if changed:
        # Update the content via API
        s2 = requests.Session()
        s2.auth = AUTH
        s2.headers['Accept-Encoding'] = 'gzip, deflate'
        update_resp = s2.post(
            f"{BASE}/{item_type}/{item_id}",
            json={"content": raw_content}
        )
        if update_resp.status_code == 200:
            fixes_applied.append({
                "id": item_id,
                "type": item_type,
                "title": title,
                "fixed": [f for f in item_findings if f in ["{vendor_count}", "{title}", '"loading comments"']]
            })
            log(f"  FIXED {item_type} #{item_id} '{title}'")
            return True
        else:
            log(f"  ERROR updating {item_type} #{item_id}: {update_resp.status_code} - {update_resp.text[:200]}")
            return False

    return False


def main():
    start = datetime.now()
    # Clear log
    with open(LOG_FILE, "w") as f:
        f.write(f"=== Placeholder Fix Script - {start.isoformat()} ===\n\n")

    log("Fetching all published pages...")
    pages = fetch_all("pages")
    log(f"  Found {len(pages)} published pages")

    log("Fetching all published posts...")
    posts = fetch_all("posts")
    log(f"  Found {len(posts)} published posts")

    log(f"\nScanning {len(pages)} pages for placeholder bugs...")
    for page in pages:
        scan_and_fix_content(page, "pages")

    log(f"\nScanning {len(posts)} posts for placeholder bugs...")
    for post in posts:
        scan_and_fix_content(post, "posts")

    # Summary
    log("\n" + "=" * 60)
    log("SUMMARY")
    log("=" * 60)
    log(f"Total pages scanned: {len(pages)}")
    log(f"Total posts scanned: {len(posts)}")
    log(f"Total items with findings: {len(findings)}")
    log(f"Total items fixed: {len(fixes_applied)}")

    if findings:
        log("\nAll findings:")
        for f in findings:
            log(f"  {f['type']} #{f['id']} '{f['title']}': {', '.join(f['findings'])}")

    if fixes_applied:
        log("\nAll fixes applied:")
        for f in fixes_applied:
            log(f"  {f['type']} #{f['id']} '{f['title']}': fixed {', '.join(f['fixed'])}")

    end = datetime.now()
    log(f"\nCompleted in {(end - start).total_seconds():.1f}s")

    # Also save structured results
    results = {
        "timestamp": start.isoformat(),
        "pages_scanned": len(pages),
        "posts_scanned": len(posts),
        "findings": findings,
        "fixes_applied": fixes_applied
    }
    with open(LOG_FILE.replace(".log", ".json"), "w") as f:
        json.dump(results, f, indent=2)

    log(f"\nResults saved to {LOG_FILE} and {LOG_FILE.replace('.log', '.json')}")


if __name__ == "__main__":
    main()
