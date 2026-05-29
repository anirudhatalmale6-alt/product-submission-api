#!/usr/bin/env python3
"""
Fix 5 posts with broken meta titles/descriptions from v2 run.
"""

import xmlrpc.client
import subprocess
import json
import time
import csv

XMLRPC_URL = "https://pethubonline.com/xmlrpc.php"
XMLRPC_USER = "jasonsarah2026"
XMLRPC_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
BLOG_ID = 1

FIXES = [
    {
        "id": 5464,
        "title": "Pet Grooming Glossary: Understanding Grooming Terms",
        "desc": "Your complete glossary of pet grooming terms and techniques. Simple definitions, practical explanations, and everything UK pet owners need to know.",
    },
    {
        "id": 5419,
        "title": "Cat Care Basics: A Glossary for New Cat Owners",
        "desc": "Your complete glossary of cat care basics for new cat owners. Simple definitions, practical tips, and everything UK pet owners need to know in 2026.",
    },
    {
        "id": 5296,
        "title": "Best Indoor Cat Toys UK (2026) – Guide for House Cats",
        "desc": "Discover the best indoor cat toys available in the UK for 2026. Expert-reviewed picks with honest ratings, pros, cons, and practical buying advice.",
    },
    {
        "id": 4412,
        "title": "No-Pull Dog Harness Guide: How They Work and When to Use",
        "desc": "Your complete guide to no-pull dog harnesses. Evidence-based advice on how they work, when to use one, and practical tips for UK pet owners in 2026.",
    },
    {
        "id": 4034,
        "title": "Best No-Pull Dog Harnesses UK (2026) – Comfort Guide",
        "desc": "Discover the best no-pull dog harnesses available in the UK for 2026. Expert-reviewed picks with honest ratings, pros, cons, and buying advice.",
    },
]

def xmlrpc_update(post_id, seo_title, seo_desc):
    """Update SEO meta via XMLRPC."""
    proxy = xmlrpc.client.ServerProxy(XMLRPC_URL)
    # First get current custom fields
    post = proxy.wp.getPost(BLOG_ID, XMLRPC_USER, XMLRPC_PASS, post_id)
    custom_fields = post.get("custom_fields", [])

    updates = []
    title_found = False
    desc_found = False

    for cf in custom_fields:
        if cf["key"] == "jetpack_seo_html_title":
            updates.append({"id": cf["id"], "key": "jetpack_seo_html_title", "value": seo_title})
            title_found = True
        elif cf["key"] == "advanced_seo_description":
            updates.append({"id": cf["id"], "key": "advanced_seo_description", "value": seo_desc})
            desc_found = True

    if not title_found:
        updates.append({"key": "jetpack_seo_html_title", "value": seo_title})
    if not desc_found:
        updates.append({"key": "advanced_seo_description", "value": seo_desc})

    result = proxy.wp.editPost(BLOG_ID, XMLRPC_USER, XMLRPC_PASS, post_id, {
        "custom_fields": updates
    })
    return result

def main():
    print(f"Fixing {len(FIXES)} posts with broken meta...")
    print("=" * 70)

    for fix in FIXES:
        post_id = fix["id"]
        new_title = fix["title"]
        new_desc = fix["desc"]

        print(f"\nPost {post_id}:")
        print(f"  New title ({len(new_title)} chars): {new_title}")
        print(f"  New desc  ({len(new_desc)} chars): {new_desc}")

        assert len(new_title) <= 60, f"Title too long: {len(new_title)}"
        assert len(new_desc) <= 160, f"Desc too long: {len(new_desc)}"

        try:
            result = xmlrpc_update(post_id, new_title, new_desc)
            print(f"  -> XMLRPC: {'success' if result else 'FAILED'}")
        except Exception as e:
            print(f"  -> ERROR: {e}")

        time.sleep(2)

    # Verify
    print(f"\n{'=' * 70}")
    print("Verifying fixes...")
    time.sleep(3)

    all_ok = True
    for fix in FIXES:
        post_id = fix["id"]
        proxy = xmlrpc.client.ServerProxy(XMLRPC_URL)
        post = proxy.wp.getPost(BLOG_ID, XMLRPC_USER, XMLRPC_PASS, post_id)
        cf = {f["key"]: f["value"] for f in post.get("custom_fields", [])}

        actual_title = cf.get("jetpack_seo_html_title", "")
        actual_desc = cf.get("advanced_seo_description", "")

        title_ok = actual_title.strip() == fix["title"].strip()
        desc_ok = actual_desc.strip() == fix["desc"].strip()

        print(f"\nPost {post_id}:")
        print(f"  Title: {'PASS' if title_ok else 'FAIL'}")
        print(f"  Desc:  {'PASS' if desc_ok else 'FAIL'}")

        if not title_ok:
            print(f"    Expected: {fix['title']}")
            print(f"    Actual:   {actual_title}")
            all_ok = False
        if not desc_ok:
            print(f"    Expected: {fix['desc']}")
            print(f"    Actual:   {actual_desc}")
            all_ok = False

        time.sleep(2)

    print(f"\n{'=' * 70}")
    print(f"All fixes verified: {'YES' if all_ok else 'NO'}")

if __name__ == "__main__":
    main()
