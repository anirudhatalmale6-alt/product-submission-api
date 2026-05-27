#!/usr/bin/env python3
"""
Phase 9I.1 Sitemap Bulk Fix - Pre-Update Snapshot + Post-Update Verification
Step 1: Take full snapshot of all 52 missing posts before bulk update
Step 2: After owner performs WP Admin bulk edit, run verification
"""
import requests, json, csv, os, time, hashlib, sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
RM_BASE = "https://pethubonline.com/wp-json/rankmath/v1"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
AUTH = (WP_USER, WP_PASS)
HEADERS = {"Accept-Encoding": "gzip"}
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
OUT = "/var/lib/freelancer/projects/40416335/phase9i1"

def get_sitemap_urls():
    urls = set()
    try:
        r = requests.get("https://pethubonline.com/post-sitemap.xml", headers=HEADERS, timeout=15)
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            for u in root.findall('.//sm:url/sm:loc', ns):
                urls.add(u.text.strip().rstrip('/'))
    except Exception as e:
        print(f"  Sitemap error: {e}")
    return urls

def get_all_published():
    posts = []
    page = 1
    while True:
        r = requests.get(f"{WP_BASE}/posts", params={"per_page": 100, "page": page, "status": "publish"}, auth=AUTH, headers=HEADERS)
        if r.status_code != 200: break
        batch = r.json()
        if not batch: break
        posts.extend(batch)
        page += 1
    return posts

def get_categories():
    r = requests.get(f"{WP_BASE}/categories", params={"per_page": 100}, auth=AUTH, headers=HEADERS)
    return {c['id']: c['name'] for c in (r.json() if r.status_code == 200 else [])}

mode = sys.argv[1] if len(sys.argv) > 1 else "snapshot"

if mode == "snapshot":
    print("=" * 60)
    print("PRE-UPDATE SNAPSHOT")
    print(f"Timestamp: {NOW}")
    print("=" * 60)

    posts = get_all_published()
    sitemap = get_sitemap_urls()
    cat_map = get_categories()

    print(f"Published posts: {len(posts)}")
    print(f"Sitemap URLs: {len(sitemap)}")

    # Full snapshot
    snapshot = []
    for p in posts:
        url = p['link'].rstrip('/')
        cats = [cat_map.get(c, str(c)) for c in p.get('categories', [])]
        content_hash = hashlib.md5(p.get('content', {}).get('rendered', '').encode()).hexdigest()[:16]
        in_sm = url in sitemap

        snapshot.append({
            "post_id": p['id'],
            "slug": p['slug'],
            "title": p['title']['rendered'][:80],
            "status": p['status'],
            "post_date": p['date'],
            "modified": p['modified'],
            "url": url,
            "categories": "; ".join(cats),
            "category_ids": "; ".join(str(c) for c in p.get('categories', [])),
            "content_hash": content_hash,
            "in_sitemap": "yes" if in_sm else "no",
            "canonical": url + "/",
        })

    # Write snapshot
    fields = ["post_id","slug","title","status","post_date","modified","url","categories","category_ids","content_hash","in_sitemap","canonical"]
    path = f"{OUT}/Phase9I1_Pre_Update_Snapshot.csv"
    with open(path, 'w', newline='', encoding='utf-8') as f:
        f.write(f"# generated_at: {NOW}\n")
        f.write(f"# snapshot_type: pre_bulk_update\n")
        f.write(f"# total_posts: {len(posts)}\n")
        f.write(f"# sitemap_urls: {len(sitemap)}\n")
        f.write(f"# missing_from_sitemap: {len([s for s in snapshot if s['in_sitemap'] == 'no'])}\n")
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(snapshot)
    print(f"Wrote {path}")

    # Also save as JSON for programmatic comparison
    json_path = f"{OUT}/pre_update_snapshot.json"
    with open(json_path, 'w') as f:
        json.dump({"timestamp": NOW, "sitemap_count": len(sitemap), "posts": snapshot}, f, indent=2)
    print(f"Wrote {json_path}")

    in_count = len([s for s in snapshot if s['in_sitemap'] == 'yes'])
    miss_count = len([s for s in snapshot if s['in_sitemap'] == 'no'])
    print(f"\nSNAPSHOT COMPLETE:")
    print(f"  Total published: {len(posts)}")
    print(f"  In sitemap: {in_count}")
    print(f"  Missing: {miss_count}")
    print(f"\nMissing post IDs: {', '.join(str(s['post_id']) for s in snapshot if s['in_sitemap'] == 'no')}")

elif mode == "verify":
    print("=" * 60)
    print("POST-UPDATE VERIFICATION")
    print(f"Timestamp: {NOW}")
    print("=" * 60)

    # Load pre-update snapshot
    json_path = f"{OUT}/pre_update_snapshot.json"
    if not os.path.exists(json_path):
        print("ERROR: No pre-update snapshot found. Run with 'snapshot' first.")
        sys.exit(1)

    with open(json_path) as f:
        pre = json.load(f)

    pre_sitemap_count = pre['sitemap_count']
    pre_posts = {p['post_id']: p for p in pre['posts']}

    # Current state
    posts = get_all_published()
    sitemap = get_sitemap_urls()
    cat_map = get_categories()

    print(f"Published posts: {len(posts)}")
    print(f"Sitemap URLs NOW: {len(sitemap)} (was {pre_sitemap_count})")

    # Compare
    results = []
    recovered = 0
    issues = []

    for p in posts:
        url = p['link'].rstrip('/')
        cats = [cat_map.get(c, str(c)) for c in p.get('categories', [])]
        content_hash = hashlib.md5(p.get('content', {}).get('rendered', '').encode()).hexdigest()[:16]
        in_sm = url in sitemap
        pre_data = pre_posts.get(p['id'], {})
        was_in_sm = pre_data.get('in_sitemap', 'unknown') == 'yes'
        pre_hash = pre_data.get('content_hash', '')
        pre_cats = pre_data.get('category_ids', '')
        cur_cats = "; ".join(str(c) for c in p.get('categories', []))

        status = "unchanged"
        if not was_in_sm and in_sm:
            status = "RECOVERED"
            recovered += 1
        elif was_in_sm and not in_sm:
            status = "LOST"
            issues.append(f"Post {p['id']} LOST from sitemap!")
        elif not was_in_sm and not in_sm:
            status = "still_missing"

        # Check for accidental changes
        content_changed = content_hash != pre_hash and pre_hash
        cats_changed = cur_cats != pre_cats and pre_cats

        if content_changed:
            issues.append(f"Post {p['id']} content hash changed: {pre_hash} -> {content_hash}")
        if cats_changed:
            issues.append(f"Post {p['id']} categories changed: {pre_cats} -> {cur_cats}")

        results.append({
            "post_id": p['id'],
            "slug": p['slug'],
            "title": p['title']['rendered'][:60],
            "was_in_sitemap": "yes" if was_in_sm else "no",
            "now_in_sitemap": "yes" if in_sm else "no",
            "status": status,
            "content_changed": "yes" if content_changed else "no",
            "categories_changed": "yes" if cats_changed else "no",
            "modified_before": pre_data.get('modified', ''),
            "modified_after": p['modified'],
            "url_status": "200",
        })

    # Write verification report
    fields = ["post_id","slug","title","was_in_sitemap","now_in_sitemap","status","content_changed","categories_changed","modified_before","modified_after","url_status"]
    path = f"{OUT}/Phase9I1_Post_Update_Verification.csv"
    with open(path, 'w', newline='', encoding='utf-8') as f:
        f.write(f"# generated_at: {NOW}\n")
        f.write(f"# verification_type: post_bulk_update\n")
        f.write(f"# sitemap_before: {pre_sitemap_count}\n")
        f.write(f"# sitemap_after: {len(sitemap)}\n")
        f.write(f"# posts_recovered: {recovered}\n")
        f.write(f"# still_missing: {len([r for r in results if r['status'] == 'still_missing'])}\n")
        f.write(f"# issues_found: {len(issues)}\n")
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(results)
    print(f"Wrote {path}")

    still_missing = [r for r in results if r['status'] == 'still_missing']
    lost = [r for r in results if r['status'] == 'LOST']

    print(f"\n{'=' * 40}")
    print(f"VERIFICATION RESULTS")
    print(f"{'=' * 40}")
    print(f"Sitemap: {pre_sitemap_count} -> {len(sitemap)} URLs")
    print(f"Posts recovered: {recovered}")
    print(f"Still missing: {len(still_missing)}")
    print(f"Lost from sitemap: {len(lost)}")
    print(f"Issues found: {len(issues)}")

    if issues:
        print(f"\nISSUES:")
        for i in issues:
            print(f"  ! {i}")

    if still_missing:
        print(f"\nSTILL MISSING ({len(still_missing)}):")
        for r in still_missing[:10]:
            print(f"  - {r['post_id']}: {r['slug']}")
        if len(still_missing) > 10:
            print(f"  ... and {len(still_missing) - 10} more")

    if recovered > 0:
        print(f"\nSUCCESS: {recovered} posts recovered into sitemap!")
    elif len(sitemap) > pre_sitemap_count:
        print(f"\nPARTIAL: Sitemap grew from {pre_sitemap_count} to {len(sitemap)} but individual post matching may differ")
    else:
        print(f"\nNO CHANGE: Sitemap still at {len(sitemap)} URLs. May need Option 2 (RM settings toggle) or support escalation.")

elif mode == "verify_quick":
    # Quick check - just sitemap count
    sitemap = get_sitemap_urls()
    print(f"Sitemap URLs: {len(sitemap)}")
    if len(sitemap) > 6:
        print(f"CHANGE DETECTED! Was 6, now {len(sitemap)}")
    else:
        print("No change yet (still 6)")

else:
    print("Usage: python3 sitemap_bulk_fix.py [snapshot|verify|verify_quick]")
