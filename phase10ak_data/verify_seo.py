#!/usr/bin/env python3
"""
Phase 10AK Verification: Check SEO metadata was applied correctly.
Samples 10 posts and verifies meta titles/descriptions match what we set.
Uses XMLRPC (wp.getPost) since Jetpack SEO fields aren't exposed via REST API.
"""

import xmlrpc.client
import csv
import time
import random

XMLRPC_URL = "https://pethubonline.com/xmlrpc.php"
XMLRPC_USER = "jasonsarah2026"
XMLRPC_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
BLOG_ID = 1
LOG_FILE = "/var/lib/freelancer/projects/40416335/phase10ak_data/seo_metadata_log.csv"

def xmlrpc_get_post(post_id):
    """Fetch post via XMLRPC and return custom fields dict."""
    try:
        proxy = xmlrpc.client.ServerProxy(XMLRPC_URL)
        post = proxy.wp.getPost(BLOG_ID, XMLRPC_USER, XMLRPC_PASS, int(post_id))
        custom_fields = {f["key"]: f["value"] for f in post.get("custom_fields", [])}
        return custom_fields
    except Exception as e:
        print(f"  XMLRPC error: {e}")
        return None

def main():
    # Read the log
    rows = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["status"].startswith("updated"):
                rows.append(row)

    if not rows:
        print("No updated rows found in log!")
        return

    # Sample up to 10 posts
    sample = random.sample(rows, min(10, len(rows)))

    print(f"Verifying {len(sample)} posts out of {len(rows)} updated...")
    print("=" * 70)

    pass_count = 0
    fail_count = 0

    for row in sample:
        post_id = row["id"]
        expected_title = row["new_meta_title"]
        expected_desc = row["new_meta_desc"]

        print(f"\nPost {post_id}: {row['title'][:60]}")

        custom_fields = xmlrpc_get_post(post_id)
        time.sleep(2)

        if custom_fields is None:
            print(f"  FAIL: Could not fetch post via XMLRPC")
            fail_count += 1
            continue

        actual_title = custom_fields.get("jetpack_seo_html_title", "")
        actual_desc = custom_fields.get("advanced_seo_description", "")

        title_ok = True
        desc_ok = True

        if expected_title != "(unchanged)":
            if actual_title.strip() == expected_title.strip():
                print(f"  Meta title: PASS")
            else:
                print(f"  Meta title: FAIL")
                print(f"    Expected: {expected_title}")
                print(f"    Actual:   {actual_title}")
                title_ok = False
        else:
            print(f"  Meta title: skipped (unchanged)")

        if expected_desc != "(unchanged)":
            if actual_desc.strip() == expected_desc.strip():
                print(f"  Meta desc:  PASS")
            else:
                print(f"  Meta desc:  FAIL")
                print(f"    Expected: {expected_desc[:80]}")
                print(f"    Actual:   {actual_desc[:80]}")
                desc_ok = False
        else:
            print(f"  Meta desc:  skipped (unchanged)")

        if title_ok and desc_ok:
            pass_count += 1
        else:
            fail_count += 1

    print(f"\n{'=' * 70}")
    print(f"Results: {pass_count} PASS, {fail_count} FAIL out of {len(sample)} sampled")

if __name__ == "__main__":
    main()
