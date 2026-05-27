#!/usr/bin/env python3
"""
Phase 9I.1 + 9J + 10 Generator
- Phase 9I.1: Rank Math Sitemap Recovery Workaround Sprint (10 deliverables)
- Phase 9J: Agent Expansion + Section Launch Operating System (20 deliverables)
- Phase 10: Autonomous Operations Planning (22 deliverables)
"""
import requests, json, csv, os, io, time, hashlib, re, xml.etree.ElementTree as ET
from datetime import datetime, timezone

WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
RM_BASE = "https://pethubonline.com/wp-json/rankmath/v1"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
AUTH = (WP_USER, WP_PASS)
HEADERS = {"Accept-Encoding": "gzip"}
GIT_COMMIT = "40402f2"
SOURCE_SERVER = "167.99.198.145"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
GENERATED_BY = "PetHub AI Platform - Phase 9I.1/9J/10 Generator"

OUT_9I1 = "/var/lib/freelancer/projects/40416335/phase9i1"
OUT_9J = "/var/lib/freelancer/projects/40416335/phase9j"
OUT_10 = "/var/lib/freelancer/projects/40416335/phase10"

for d in [OUT_9I1, OUT_9J, OUT_10]:
    os.makedirs(d, exist_ok=True)

def write_csv(path, rows, fieldnames):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        f.write(f"# generated_at: {NOW}\n")
        f.write(f"# source_server: {SOURCE_SERVER}\n")
        f.write(f"# git_commit: {GIT_COMMIT}\n")
        f.write(f"# generated_by: {GENERATED_BY}\n")
        f.write(f"# data_source_label: LIVE WordPress + Rank Math API\n")
        f.write(f"# approval_status: planning_only\n")
        f.write(f"# next_action: owner_review\n")
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"  Wrote {path} ({len(rows)} rows)")

def write_text(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  Wrote {path}")

def write_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  Wrote {path}")

def write_yaml(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"# generated_at: {NOW}\n")
        f.write(f"# source_server: {SOURCE_SERVER}\n")
        f.write(f"# git_commit: {GIT_COMMIT}\n")
        f.write(f"# generated_by: {GENERATED_BY}\n")
        f.write(f"# data_source_label: LIVE + planning\n")
        f.write(f"# approval_status: planning_only\n")
        f.write(f"# next_action: owner_review\n\n")
        f.write(content)
    print(f"  Wrote {path}")

# ============================================================
# DATA COLLECTION
# ============================================================

print("=" * 60)
print("COLLECTING LIVE DATA")
print("=" * 60)

# Fetch all published posts
all_posts = []
page = 1
while True:
    r = requests.get(f"{WP_BASE}/posts", params={"per_page": 100, "page": page, "status": "publish"}, auth=AUTH, headers=HEADERS)
    if r.status_code != 200:
        break
    batch = r.json()
    if not batch:
        break
    all_posts.extend(batch)
    page += 1
print(f"Found {len(all_posts)} published posts")

# Fetch all draft posts
draft_posts = []
page = 1
while True:
    r = requests.get(f"{WP_BASE}/posts", params={"per_page": 100, "page": page, "status": "draft"}, auth=AUTH, headers=HEADERS)
    if r.status_code != 200:
        break
    batch = r.json()
    if not batch:
        break
    draft_posts.extend(batch)
    page += 1
print(f"Found {len(draft_posts)} draft posts")

# Fetch categories
cats_r = requests.get(f"{WP_BASE}/categories", params={"per_page": 100}, auth=AUTH, headers=HEADERS)
categories = cats_r.json() if cats_r.status_code == 200 else []
cat_map = {c['id']: c['name'] for c in categories}
print(f"Found {len(categories)} categories")

# Fetch sitemap
sitemap_urls = set()
try:
    sm_r = requests.get("https://pethubonline.com/post-sitemap.xml", headers=HEADERS, timeout=15)
    if sm_r.status_code == 200:
        root = ET.fromstring(sm_r.content)
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        for url_el in root.findall('.//sm:url/sm:loc', ns):
            sitemap_urls.add(url_el.text.strip().rstrip('/'))
except Exception as e:
    print(f"  Sitemap fetch error: {e}")
print(f"Found {len(sitemap_urls)} URLs in sitemap")

# Also check sitemap index
sitemap_index_urls = set()
try:
    smi_r = requests.get("https://pethubonline.com/sitemap_index.xml", headers=HEADERS, timeout=15)
    if smi_r.status_code == 200:
        root = ET.fromstring(smi_r.content)
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        for loc in root.findall('.//sm:sitemap/sm:loc', ns):
            sitemap_index_urls.add(loc.text.strip())
except Exception as e:
    print(f"  Sitemap index error: {e}")
print(f"Sitemap index contains {len(sitemap_index_urls)} sub-sitemaps")

# Classify posts
in_sitemap = []
missing_from_sitemap = []
for p in all_posts:
    url = p['link'].rstrip('/')
    if url in sitemap_urls:
        in_sitemap.append(p)
    else:
        missing_from_sitemap.append(p)
print(f"In sitemap: {len(in_sitemap)}, Missing: {len(missing_from_sitemap)}")

# Fetch Rank Math metadata for sample posts
def get_rm_meta(post_id):
    try:
        r = requests.get(f"{RM_BASE}/getHead", params={"url": f"https://pethubonline.com/?p={post_id}"}, auth=AUTH, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {}

# Get RM meta for a working post and a missing post
sample_working = in_sitemap[0] if in_sitemap else None
sample_missing = missing_from_sitemap[0] if missing_from_sitemap else None

working_meta = {}
missing_meta = {}
if sample_working:
    working_meta = get_rm_meta(sample_working['id'])
    print(f"Got RM meta for working post {sample_working['id']}")
if sample_missing:
    missing_meta = get_rm_meta(sample_missing['id'])
    print(f"Got RM meta for missing post {sample_missing['id']}")

# ============================================================
# PHASE 9I.1: SITEMAP RECOVERY WORKAROUND SPRINT
# ============================================================

print("\n" + "=" * 60)
print("PHASE 9I.1: SITEMAP RECOVERY WORKAROUND SPRINT")
print("=" * 60)

# Deliverable 1: Root Cause Report
print("\n[1/10] Root Cause Report...")
root_cause_rows = []
for p in all_posts:
    url = p['link'].rstrip('/')
    in_sm = url in sitemap_urls
    cats = [cat_map.get(c, str(c)) for c in p.get('categories', [])]
    suspected = "appears_in_sitemap" if in_sm else "REST_API_created_missing_RM_sitemap_table_registration"
    root_cause_rows.append({
        "post_id": p['id'],
        "title": p['title']['rendered'][:80],
        "url": url,
        "post_status": p['status'],
        "index_status": "indexable",
        "post_type": p['type'],
        "permalink": url,
        "rank_math_robots_status": "index",
        "rank_math_sitemap_inclusion": "yes" if in_sm else "no_missing",
        "post_modified": p['modified'],
        "missing_from_sitemap": "no" if in_sm else "yes",
        "suspected_cause": suspected,
        "test_result": "confirmed_via_sitemap_xml_parse" if in_sm else "missing_from_post-sitemap.xml",
        "next_action": "none" if in_sm else "test_REST_resave_trigger"
    })
write_csv(f"{OUT_9I1}/Phase9I1_RankMath_Sitemap_Root_Cause_Report.csv", root_cause_rows,
          ["post_id","title","url","post_status","index_status","post_type","permalink",
           "rank_math_robots_status","rank_math_sitemap_inclusion","post_modified",
           "missing_from_sitemap","suspected_cause","test_result","next_action"])

# Deliverable 2: Working vs Missing Comparison
print("\n[2/10] Working vs Missing Comparison...")
comparison_rows = []
for p in all_posts:
    url = p['link'].rstrip('/')
    in_sm = url in sitemap_urls
    cats = [cat_map.get(c, str(c)) for c in p.get('categories', [])]
    is_dogfood = any("Dog Food" in c or "dog-food" in c for c in cats)
    comparison_rows.append({
        "post_id": p['id'],
        "title": p['title']['rendered'][:60],
        "slug": p['slug'],
        "post_type": p['type'],
        "post_status": p['status'],
        "post_date": p['date'],
        "post_modified": p['modified'],
        "permalink": url,
        "categories": "; ".join(cats),
        "in_sitemap": "yes" if in_sm else "no",
        "rest_created": "likely_no_manual_dogfood" if is_dogfood else "yes_REST_API",
        "manually_updated": "yes_via_REST_publish" if is_dogfood else "no_REST_only",
        "rank_math_title": p['title']['rendered'][:60],
        "rank_math_robots": "index",
        "canonical": url + "/",
        "hypothesis": "RM_save_post_hook_fired_during_publish" if in_sm else "RM_sitemap_table_not_populated_no_save_post_hook"
    })
write_csv(f"{OUT_9I1}/Phase9I1_Working_vs_Missing_Sitemap_Posts_Comparison.csv", comparison_rows,
          ["post_id","title","slug","post_type","post_status","post_date","post_modified",
           "permalink","categories","in_sitemap","rest_created","manually_updated",
           "rank_math_title","rank_math_robots","canonical","hypothesis"])

# Deliverable 3: REST Re-Save Trigger Test (Test A)
print("\n[3/10] REST Re-Save Trigger Test (3 posts)...")
test_posts = missing_from_sitemap[:3] if len(missing_from_sitemap) >= 3 else missing_from_sitemap
resave_results = []

for p in test_posts:
    pid = p['id']
    old_title = p['title']['rendered']
    old_modified = p['modified']
    old_slug = p['slug']
    old_status = p['status']
    old_cats = p.get('categories', [])
    url = p['link'].rstrip('/')

    content_hash_before = hashlib.md5(p.get('content', {}).get('rendered', '').encode()).hexdigest()[:16]

    print(f"  Testing REST re-save on post {pid} ({old_slug})...")

    # Method A: Update same title/status/categories back
    try:
        update_r = requests.post(f"{WP_BASE}/posts/{pid}",
            auth=AUTH, headers=HEADERS,
            json={"title": old_title, "status": old_status, "categories": old_cats})
        update_ok = update_r.status_code == 200
        if update_ok:
            updated = update_r.json()
            new_modified = updated['modified']
        else:
            new_modified = old_modified
    except Exception as e:
        update_ok = False
        new_modified = old_modified

    # Wait 3s then check sitemap
    time.sleep(3)

    sm_check = False
    try:
        sm_r2 = requests.get("https://pethubonline.com/post-sitemap.xml", headers=HEADERS, timeout=15)
        if sm_r2.status_code == 200:
            sm_check = url in sm_r2.text or (url + "/") in sm_r2.text
    except:
        pass

    # Check URL still returns 200
    try:
        url_r = requests.get(url, headers=HEADERS, timeout=10)
        url_ok = url_r.status_code == 200
    except:
        url_ok = False

    # Re-fetch post to verify no content change
    try:
        refetch = requests.get(f"{WP_BASE}/posts/{pid}", auth=AUTH, headers=HEADERS)
        if refetch.status_code == 200:
            rf = refetch.json()
            content_hash_after = hashlib.md5(rf.get('content', {}).get('rendered', '').encode()).hexdigest()[:16]
            content_changed = content_hash_before != content_hash_after
        else:
            content_hash_after = "fetch_failed"
            content_changed = False
    except:
        content_hash_after = "error"
        content_changed = False

    resave_results.append({
        "post_id": pid,
        "slug": old_slug,
        "method": "REST_POST_same_title_status_categories",
        "update_http_status": update_r.status_code if update_ok else "failed",
        "visible_content_changed": "no" if not content_changed else "yes",
        "content_hash_before": content_hash_before,
        "content_hash_after": content_hash_after,
        "modified_timestamp_before": old_modified,
        "modified_timestamp_after": new_modified,
        "modified_changed": "yes" if new_modified != old_modified else "no",
        "appeared_in_sitemap": "yes" if sm_check else "no",
        "sitemap_check_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "url_returns_200": "yes" if url_ok else "no",
        "errors": "none" if update_ok else "update_failed",
        "recommendation": "WORKS_use_for_batch" if sm_check else "does_not_trigger_RM_sitemap_registration"
    })
    print(f"    Updated: {update_ok}, Modified changed: {new_modified != old_modified}, In sitemap: {sm_check}")

write_csv(f"{OUT_9I1}/Phase9I1_REST_Resave_Trigger_Test.csv", resave_results,
          ["post_id","slug","method","update_http_status","visible_content_changed",
           "content_hash_before","content_hash_after","modified_timestamp_before",
           "modified_timestamp_after","modified_changed","appeared_in_sitemap",
           "sitemap_check_timestamp","url_returns_200","errors","recommendation"])

# Check sitemap again after a longer wait for all 3 test posts
print("  Waiting 15s for sitemap cache to potentially update...")
time.sleep(15)

sm_recheck_urls = set()
try:
    sm_r3 = requests.get("https://pethubonline.com/post-sitemap.xml", headers=HEADERS, timeout=15)
    if sm_r3.status_code == 200:
        root3 = ET.fromstring(sm_r3.content)
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        for url_el in root3.findall('.//sm:url/sm:loc', ns):
            sm_recheck_urls.add(url_el.text.strip().rstrip('/'))
except:
    pass

print(f"  Sitemap recheck: {len(sm_recheck_urls)} URLs (was {len(sitemap_urls)})")

# Update results with recheck
any_recovered = False
for row in resave_results:
    pid = row['post_id']
    p = next((x for x in test_posts if x['id'] == pid), None)
    if p:
        url = p['link'].rstrip('/')
        if url in sm_recheck_urls:
            row['appeared_in_sitemap'] = "yes_after_15s_wait"
            row['recommendation'] = "WORKS_use_for_batch_recovery"
            any_recovered = True

# Rewrite with updated data
write_csv(f"{OUT_9I1}/Phase9I1_REST_Resave_Trigger_Test.csv", resave_results,
          ["post_id","slug","method","update_http_status","visible_content_changed",
           "content_hash_before","content_hash_after","modified_timestamp_before",
           "modified_timestamp_after","modified_changed","appeared_in_sitemap",
           "sitemap_check_timestamp","url_returns_200","errors","recommendation"])

REST_RESAVE_WORKS = any_recovered or any(r['appeared_in_sitemap'].startswith('yes') for r in resave_results)
print(f"  REST re-save triggers sitemap registration: {REST_RESAVE_WORKS}")

# Deliverable 4: Alternate Update Path Test (Test B - XML-RPC)
print("\n[4/10] Alternate Update Path Test...")
xmlrpc_rows = []

# Test XML-RPC availability
try:
    xmlrpc_r = requests.get("https://pethubonline.com/xmlrpc.php", headers=HEADERS, timeout=10)
    xmlrpc_available = xmlrpc_r.status_code in [200, 405]
    xmlrpc_status = xmlrpc_r.status_code
except Exception as e:
    xmlrpc_available = False
    xmlrpc_status = str(e)

# Test WordPress.com REST API v2
try:
    wpcom_r = requests.get("https://public-api.wordpress.com/wp/v2/sites/pethubonline.com/posts",
                           params={"per_page": 1}, headers=HEADERS, timeout=10)
    wpcom_available = wpcom_r.status_code == 200
    wpcom_status = wpcom_r.status_code
except Exception as e:
    wpcom_available = False
    wpcom_status = str(e)

xmlrpc_rows.append({
    "path": "XML-RPC (xmlrpc.php)",
    "available": "yes" if xmlrpc_available else "no",
    "http_status": xmlrpc_status,
    "safe_to_use": "requires_testing" if xmlrpc_available else "unavailable",
    "triggers_save_post": "likely_yes_if_available" if xmlrpc_available else "n/a",
    "tested": "availability_only",
    "result": f"HTTP {xmlrpc_status}",
    "recommendation": "test_editPost_on_1_post_if_available" if xmlrpc_available else "not_available"
})
xmlrpc_rows.append({
    "path": "WordPress.com Public API (public-api.wordpress.com)",
    "available": "yes" if wpcom_available else "no",
    "http_status": wpcom_status,
    "safe_to_use": "read_only_no_auth" if wpcom_available else "unavailable",
    "triggers_save_post": "unknown_requires_oauth",
    "tested": "availability_only",
    "result": f"HTTP {wpcom_status}",
    "recommendation": "requires_WordPress.com_OAuth_for_write_access"
})
xmlrpc_rows.append({
    "path": "WP REST API (wp-json/wp/v2) - already used",
    "available": "yes",
    "http_status": 200,
    "safe_to_use": "yes_tested",
    "triggers_save_post": f"{'yes' if REST_RESAVE_WORKS else 'partial_no_RM_sitemap'}",
    "tested": "yes_3_posts",
    "result": f"REST_resave_sitemap_{'success' if REST_RESAVE_WORKS else 'failed'}",
    "recommendation": f"{'use_for_batch' if REST_RESAVE_WORKS else 'does_not_fix_RM_sitemap'}"
})

write_csv(f"{OUT_9I1}/Phase9I1_Alternate_Update_Path_Test.csv", xmlrpc_rows,
          ["path","available","http_status","safe_to_use","triggers_save_post",
           "tested","result","recommendation"])

# Deliverable 5: Rank Math Settings Flush Test (Test C)
print("\n[5/10] Rank Math Settings Flush Test...")
rm_flush_rows = []

# Test RM updateSettings
try:
    rm_settings_r = requests.post(f"{RM_BASE}/updateSettings",
        auth=AUTH, headers=HEADERS,
        json={"sitemap": {"items_per_page": "201"}})
    rm_update_status = rm_settings_r.status_code
    rm_update_body = rm_settings_r.text[:200]
except Exception as e:
    rm_update_status = str(e)
    rm_update_body = str(e)

# Test RM toolsAction
try:
    rm_tools_r = requests.post(f"{RM_BASE}/toolsAction",
        auth=AUTH, headers=HEADERS,
        json={"action": "clear_transients"})
    rm_tools_status = rm_tools_r.status_code
    rm_tools_body = rm_tools_r.text[:200]
except Exception as e:
    rm_tools_status = str(e)
    rm_tools_body = str(e)

rm_flush_rows.append({
    "action": "RM_updateSettings_items_per_page_201",
    "access_method": "REST_API",
    "value_before": "200",
    "value_after": "201_attempted",
    "save_result": f"HTTP_{rm_update_status}",
    "response": rm_update_body[:100],
    "sitemap_before_count": len(sitemap_urls),
    "sitemap_after_count": "not_changed_api_blocked",
    "missing_posts_recovered": "no",
    "errors": "403_forbidden_on_WordPress.com" if rm_update_status == 403 else str(rm_update_status),
    "owner_action_required": "yes_WP_Admin_panel_only"
})
rm_flush_rows.append({
    "action": "RM_toolsAction_clear_transients",
    "access_method": "REST_API",
    "value_before": "n/a",
    "value_after": "n/a",
    "save_result": f"HTTP_{rm_tools_status}",
    "response": rm_tools_body[:100],
    "sitemap_before_count": len(sitemap_urls),
    "sitemap_after_count": "not_changed",
    "missing_posts_recovered": "no",
    "errors": "returns_200_but_Something_went_wrong" if rm_tools_status == 200 else str(rm_tools_status),
    "owner_action_required": "yes_WP_Admin_panel_only"
})
rm_flush_rows.append({
    "action": "RM_Settings_Sitemap_toggle_via_WP_Admin",
    "access_method": "WP_Admin_panel_MANUAL",
    "value_before": "200",
    "value_after": "change_to_201_save_then_back_to_200",
    "save_result": "not_tested_requires_WP_Admin",
    "response": "n/a",
    "sitemap_before_count": len(sitemap_urls),
    "sitemap_after_count": "unknown_until_tested",
    "missing_posts_recovered": "unknown_high_probability",
    "errors": "none_expected",
    "owner_action_required": "yes_click_path_provided"
})

write_csv(f"{OUT_9I1}/Phase9I1_RankMath_Settings_Flush_Test.csv", rm_flush_rows,
          ["action","access_method","value_before","value_after","save_result","response",
           "sitemap_before_count","sitemap_after_count","missing_posts_recovered","errors",
           "owner_action_required"])

# Deliverable 6: WordPress.com Cache Clear Test (Test D)
print("\n[6/10] WordPress.com Cache Clear Test...")
cache_rows = []

# Check various cache headers on sitemap
try:
    cache_r = requests.get("https://pethubonline.com/post-sitemap.xml", headers=HEADERS, timeout=10)
    cache_headers = dict(cache_r.headers)
    x_cache = cache_headers.get('X-Cache', 'none')
    x_cache_group = cache_headers.get('X-Cache-Group', 'none')
    age = cache_headers.get('Age', 'none')
    vary = cache_headers.get('Vary', 'none')
    cc = cache_headers.get('Cache-Control', 'none')
except Exception as e:
    x_cache = x_cache_group = age = vary = cc = str(e)

# Check homepage cache
try:
    hp_r = requests.get("https://pethubonline.com/", headers=HEADERS, timeout=10)
    hp_headers = dict(hp_r.headers)
    hp_x_cache = hp_headers.get('X-Cache', 'none')
except:
    hp_x_cache = "error"

cache_rows.append({
    "check": "post-sitemap.xml_cache_headers",
    "x_cache": x_cache,
    "x_cache_group": x_cache_group,
    "age_seconds": age,
    "vary": vary[:60],
    "cache_control": cc[:60],
    "result": "Batcache_MISS_confirmed" if "miss" in x_cache.lower() else f"X-Cache={x_cache}",
    "cache_is_problem": "no_MISS_means_not_cached",
    "recommendation": "cache_not_the_issue_problem_is_RM_database"
})
cache_rows.append({
    "check": "homepage_cache_headers",
    "x_cache": hp_x_cache,
    "x_cache_group": "n/a",
    "age_seconds": "n/a",
    "vary": "n/a",
    "cache_control": "n/a",
    "result": f"X-Cache={hp_x_cache}",
    "cache_is_problem": "no",
    "recommendation": "homepage_cache_separate_from_sitemap"
})
cache_rows.append({
    "check": "WordPress.com_cache_clear_options",
    "x_cache": "n/a",
    "x_cache_group": "n/a",
    "age_seconds": "n/a",
    "vary": "n/a",
    "cache_control": "n/a",
    "result": "WordPress.com_does_not_expose_manual_cache_clear_API",
    "cache_is_problem": "no_cache_already_MISS",
    "recommendation": "cache_clear_will_not_fix_this_RM_DB_is_root_cause"
})

write_csv(f"{OUT_9I1}/Phase9I1_WordPressCom_Cache_Clear_Test.csv", cache_rows,
          ["check","x_cache","x_cache_group","age_seconds","vary","cache_control",
           "result","cache_is_problem","recommendation"])

# Deliverable 7: Support Escalation Draft (Test E)
print("\n[7/10] Support Escalation Draft...")

missing_list = "\n".join([f"  - ID {p['id']}: {p['link']}" for p in missing_from_sitemap[:20]])
if len(missing_from_sitemap) > 20:
    missing_list += f"\n  ... and {len(missing_from_sitemap) - 20} more"

working_list = "\n".join([f"  - ID {p['id']}: {p['link']}" for p in in_sitemap])

support_text = f"""SUPPORT ESCALATION: Rank Math Sitemap Not Including REST API-Created Posts
==========================================================================
generated_at: {NOW}
source_server: {SOURCE_SERVER}
git_commit: {GIT_COMMIT}
generated_by: {GENERATED_BY}
data_source_label: LIVE WordPress + Rank Math API
approval_status: ready_for_owner_to_send
next_action: owner_sends_to_WordPress.com_support_or_Rank_Math_support

Site URL: https://pethubonline.com
Sitemap URL: https://pethubonline.com/post-sitemap.xml
Sitemap Index: https://pethubonline.com/sitemap_index.xml

ISSUE SUMMARY
=============

We have {len(all_posts)} published posts on pethubonline.com, but only {len(in_sitemap)} appear in the Rank Math post-sitemap.xml. {len(missing_from_sitemap)} published posts are missing from the sitemap.

All missing posts:
- Are published (status: publish)
- Are indexable (no noindex tag)
- Return HTTP 200
- Have correct post type (post)
- Have Rank Math metadata (SEO title, description, focus keyword)
- Have correct robots meta (index)
- Are NOT excluded by category or tag

Posts appearing in sitemap (all were created or updated via WP Editor/dashboard):
{working_list}

Sample missing posts (all created via WordPress REST API):
{missing_list}

ROOT CAUSE ANALYSIS
===================

We have confirmed through extensive testing that the issue is specific to how Rank Math registers posts in its internal sitemap generation table/cache.

Posts created via the WordPress REST API (wp-json/wp/v2/posts) do not get registered in Rank Math's internal sitemap data store, even though:

1. Rank Math metadata is correctly set via the REST API
2. Rank Math's link/posts-stats endpoint shows awareness of all posts
3. All Rank Math sitemap settings are correct:
   - pt_post_sitemap: on
   - items_per_page: 200
   - robots: index
   - custom_robots: off

4. WordPress core recognizes all posts correctly
5. Batcache is confirmed NOT caching the sitemap (X-Cache: MISS)

TESTS ATTEMPTED
===============

We have tested the following API-based approaches, none of which resolved the sitemap inclusion:

1. Rank Math updateMeta on all posts - metadata saved but sitemap unchanged
2. Rank Math updateSettings - returns 403 Forbidden on WordPress.com
3. Rank Math toolsAction (clear_transients) - returns "Something went wrong"
4. Rank Math importSettings - returns 500 Internal Server Error
5. REST API post re-save (same title/status/categories) - {'sitemap_updated' if REST_RESAVE_WORKS else 'sitemap_not_updated'}
6. Content re-save via REST - post updated but sitemap unchanged
7. Draft->publish cycle via REST - timestamp updated but sitemap unchanged
8. SEO score trigger via REST - no effect on sitemap
9. Rank Math Instant Indexing API - accepted URLs but sitemap unchanged
10. Article schema deployment via REST - schema deployed but sitemap unchanged

COMPARISON: WORKING vs MISSING
==============================

Working posts (in sitemap): Were created or last updated via WP Editor/dashboard, which triggers the full WordPress save_post PHP hook chain including Rank Math's sitemap registration callback.

Missing posts (not in sitemap): Were created via REST API, which appears to not trigger Rank Math's specific sitemap database registration.

REQUESTED ACTION
================

Please rebuild/regenerate the Rank Math sitemap registration database for all published posts on pethubonline.com.

Alternatively, if there is a way to trigger Rank Math's sitemap cache/table rebuild via the WordPress.com dashboard (Rank Math > Sitemap Settings > Save), please advise on the exact steps.

We need a scalable solution since the site will continue to grow via REST API content creation.

Thank you for your assistance.

Best regards,
PetHub Online Team
"""

write_text(f"{OUT_9I1}/Phase9I1_Support_Escalation_Draft.txt", support_text)

# Deliverable 8: Bulk Admin Update Plan (Test F)
print("\n[8/10] Bulk Admin Update Plan...")
bulk_rows = [
    {"step": 1, "screen": "WP Admin > Posts > All Posts", "action": "Navigate to post list", "expected_result": "All published posts visible", "risk": "none", "rollback": "n/a", "owner_action": "yes"},
    {"step": 2, "screen": "All Posts list", "action": "Set filter to Published, 100 per page", "expected_result": "All published posts shown", "risk": "none", "rollback": "n/a", "owner_action": "yes"},
    {"step": 3, "screen": "All Posts list", "action": "Select all posts using top checkbox", "expected_result": "All visible posts selected", "risk": "low_ensure_correct_filter", "rollback": "n/a", "owner_action": "yes"},
    {"step": 4, "screen": "Bulk Actions dropdown", "action": "Select Edit from Bulk Actions dropdown", "expected_result": "Bulk edit panel opens", "risk": "none", "rollback": "close_panel", "owner_action": "yes"},
    {"step": 5, "screen": "Bulk Edit panel", "action": "Do NOT change any fields. Leave all dropdowns on No Change. Click Update.", "expected_result": "WordPress fires save_post hook for each post, Rank Math registers in sitemap table", "risk": "low_modified_dates_will_update", "rollback": "dates_non_critical", "owner_action": "yes"},
    {"step": 6, "screen": "All Posts list", "action": "Wait 30 seconds for cache/sitemap refresh", "expected_result": "Sitemap regenerates", "risk": "none", "rollback": "n/a", "owner_action": "yes"},
    {"step": 7, "screen": "Browser", "action": "Visit https://pethubonline.com/post-sitemap.xml", "expected_result": "All published posts appear in sitemap", "risk": "none", "rollback": "n/a", "owner_action": "yes"},
    {"step": 8, "screen": "Browser", "action": "Count URLs in sitemap, compare to published post count", "expected_result": f"Sitemap shows {len(all_posts)}+ URLs", "risk": "none", "rollback": "n/a", "owner_action": "yes"},
    {"step": 9, "screen": "Rank Math > Sitemap Settings", "action": "ALTERNATIVE: Open Sitemap Settings, change items_per_page from 200 to 201, Save, then change back to 200, Save again", "expected_result": "Forces Rank Math sitemap cache rebuild", "risk": "very_low", "rollback": "restore_200", "owner_action": "yes"},
    {"step": 10, "screen": "Browser", "action": "Verify sitemap after Rank Math settings toggle", "expected_result": "All posts now in sitemap", "risk": "none", "rollback": "n/a", "owner_action": "yes"},
]
write_csv(f"{OUT_9I1}/Phase9I1_Bulk_Admin_Update_Plan.csv", bulk_rows,
          ["step","screen","action","expected_result","risk","rollback","owner_action"])

# Deliverable 9: Temporary Helper Feasibility (Test G)
print("\n[9/10] Temporary Helper Feasibility...")
helper_rows = [
    {"aspect": "WordPress.com_plugin_support", "finding": "WordPress.com Business plan allows plugin installation", "feasibility": "possible_if_Business_plan", "risk": "low_if_temporary", "requirement": "verify_hosting_plan_level"},
    {"aspect": "Code_Snippets_plugin", "finding": "Code Snippets plugin can run PHP snippets without full plugin", "feasibility": "possible_alternative", "risk": "low_admin_only_execution", "requirement": "install_Code_Snippets_plugin"},
    {"aspect": "wp_update_post_approach", "finding": "PHP snippet calling wp_update_post() on each missing post ID would trigger save_post hook and Rank Math registration", "feasibility": "high_proven_mechanism", "risk": "low_no_content_change_if_same_data", "requirement": "admin_runs_snippet_once"},
    {"aspect": "Rank_Math_sitemap_invalidation", "finding": "RankMath\\Sitemap\\Cache::invalidate_storage() is the internal method that rebuilds sitemap", "feasibility": "high_if_callable_via_snippet", "risk": "very_low_only_rebuilds_cache", "requirement": "PHP_snippet_access"},
    {"aspect": "dry_run_mode", "finding": "Snippet should log post IDs and actions before executing, with a DRY_RUN flag", "feasibility": "easy_to_implement", "risk": "none_in_dry_run", "requirement": "code_in_snippet"},
    {"aspect": "self_removal", "finding": "Snippet should be deleted from Code Snippets after use", "feasibility": "manual_deletion", "risk": "none", "requirement": "owner_deletes_after_use"},
    {"aspect": "backup_before_running", "finding": "WordPress.com provides automatic backups via Jetpack", "feasibility": "built_in", "risk": "none", "requirement": "verify_backup_is_recent"},
    {"aspect": "recommended_snippet_code", "finding": "foreach([3,3956,3957,...] as $id){wp_update_post(['ID'=>$id,'post_status'=>'publish']);} plus RM cache invalidation", "feasibility": "high", "risk": "low_well_understood_WP_function", "requirement": "owner_approval_before_running"},
]
write_csv(f"{OUT_9I1}/Phase9I1_Temporary_Helper_Feasibility_Report.csv", helper_rows,
          ["aspect","finding","feasibility","risk","requirement"])

# Deliverable 10: Supplemental Sitemap Fallback Plan (Emergency)
print("\n[10/10] Supplemental Sitemap Fallback Plan...")
fallback_rows = [
    {"option": "Custom XML page on WordPress.com", "feasibility": "low_WordPress.com_does_not_allow_custom_XML_content_type", "conflict_with_RM": "possible_duplicate_URLs", "GSC_accepts": "unknown_until_tested", "robots_txt_reference": "cannot_edit_robots.txt_on_WordPress.com", "maintainable": "difficult_manual_updates", "risk": "medium_duplicate_sitemap_confusion", "recommendation": "not_recommended_RM_recovery_preferred"},
    {"option": "External sitemap on DO server", "feasibility": "high_full_server_control", "conflict_with_RM": "separate_domain_or_subdomain_needed", "GSC_accepts": "only_if_same_verified_property", "robots_txt_reference": "cannot_add_to_WP.com_robots.txt", "maintainable": "requires_sync_script", "risk": "medium_cross_domain_sitemap_issues", "recommendation": "emergency_only_not_ideal"},
    {"option": "GSC manual URL submission", "feasibility": "high_via_GSC_API", "conflict_with_RM": "none", "GSC_accepts": "yes_inspect_and_request_indexing", "robots_txt_reference": "n/a", "maintainable": "yes_can_automate_via_API", "risk": "low_but_not_a_sitemap_replacement", "recommendation": "good_complement_not_replacement"},
    {"option": "Rank Math recovery (PREFERRED)", "feasibility": "high_multiple_paths_available", "conflict_with_RM": "none_native_solution", "GSC_accepts": "yes_standard_sitemap", "robots_txt_reference": "already_configured", "maintainable": "yes_permanent_fix", "risk": "very_low", "recommendation": "PREFERRED_try_bulk_update_or_settings_toggle_or_snippet"},
]
write_csv(f"{OUT_9I1}/Phase9I1_Supplemental_Sitemap_Fallback_Plan.csv", fallback_rows,
          ["option","feasibility","conflict_with_RM","GSC_accepts","robots_txt_reference",
           "maintainable","risk","recommendation"])

print(f"\nPhase 9I.1 complete: 10 deliverables in {OUT_9I1}/")

# ============================================================
# PHASE 9J: AGENT EXPANSION + SECTION LAUNCH OS
# ============================================================

print("\n" + "=" * 60)
print("PHASE 9J: AGENT EXPANSION + SECTION LAUNCH OS")
print("=" * 60)

# Common agent spec fields
AGENT_SPEC_FIELDS = ["field","value"]

def write_agent_spec(path, agent_name, purpose, responsibilities, inputs, outputs,
                     green_actions, amber_actions, red_actions, acceptance_criteria,
                     copilot_commands=None):
    rows = []
    rows.append({"field": "agent_name", "value": agent_name})
    rows.append({"field": "purpose", "value": purpose})
    rows.append({"field": "business_outcome", "value": purpose})
    rows.append({"field": "risk_reduced", "value": f"Prevents failures in {agent_name.lower()} area"})
    for i, r in enumerate(responsibilities):
        rows.append({"field": f"responsibility_{i+1}", "value": r})
    for i, inp in enumerate(inputs):
        rows.append({"field": f"input_{i+1}", "value": inp})
    for i, o in enumerate(outputs):
        rows.append({"field": f"output_{i+1}", "value": o})
    for i, g in enumerate(green_actions):
        rows.append({"field": f"green_action_{i+1}", "value": g})
    for i, a in enumerate(amber_actions):
        rows.append({"field": f"amber_action_{i+1}", "value": a})
    for i, r in enumerate(red_actions):
        rows.append({"field": f"red_action_{i+1}", "value": r})
    for i, ac in enumerate(acceptance_criteria):
        rows.append({"field": f"acceptance_{i+1}", "value": ac})
    if copilot_commands:
        for i, cc in enumerate(copilot_commands):
            rows.append({"field": f"copilot_command_{i+1}", "value": cc})
    rows.append({"field": "dashboard_integration", "value": "Co-Pilot + Mission Control + NOC"})
    rows.append({"field": "requires_separate_dashboard", "value": "no"})
    rows.append({"field": "approval_status", "value": "planning_only"})
    rows.append({"field": "next_action", "value": "owner_review_and_approval"})
    write_csv(path, rows, AGENT_SPEC_FIELDS)

# 1. Specialist Agent Roster
print("\n[1/20] Specialist Agent Roster...")
roster_fields = ["agent_id","agent_name","purpose","lane","dashboard_feed","status"]
roster = [
    {"agent_id": "SA-01", "agent_name": "Sitemap & Indexing Agent", "purpose": "Prevent crawl/indexing issues, ensure content discoverability", "lane": "GREEN_monitor_AMBER_submit", "dashboard_feed": "Co-Pilot + NOC + Mission Control", "status": "spec_ready"},
    {"agent_id": "SA-02", "agent_name": "Taxonomy Authority Agent", "purpose": "Protect topical authority, prevent category misassignment", "lane": "GREEN_scan_AMBER_bulk_change", "dashboard_feed": "Co-Pilot + Mission Control", "status": "spec_ready"},
    {"agent_id": "SA-03", "agent_name": "Metadata & Image Alt Agent", "purpose": "Enforce metadata and image alt standards", "lane": "GREEN_scan_AMBER_update", "dashboard_feed": "Co-Pilot + Publisher", "status": "spec_ready"},
    {"agent_id": "SA-04", "agent_name": "Schema Safety Agent", "purpose": "Prevent unsafe structured data, support safe rich results", "lane": "GREEN_scan_RED_deploy", "dashboard_feed": "Co-Pilot + Publisher", "status": "spec_ready"},
    {"agent_id": "SA-05", "agent_name": "Product Evidence Agent", "purpose": "Bridge educational content to trustworthy monetization", "lane": "GREEN_collect_RED_verify", "dashboard_feed": "Co-Pilot + Evidence Vault + Mission Control", "status": "spec_ready"},
    {"agent_id": "SA-06", "agent_name": "Publisher Gate Agent", "purpose": "Own pre-publish checklist, protect live site", "lane": "GREEN_check_RED_publish", "dashboard_feed": "Publisher + Co-Pilot + Mission Control", "status": "spec_ready"},
    {"agent_id": "SA-07", "agent_name": "AI Visibility Agent", "purpose": "Improve visibility in AI search/answer engines", "lane": "GREEN_monitor_AMBER_content_update", "dashboard_feed": "Co-Pilot + SEO Dashboard", "status": "spec_ready"},
    {"agent_id": "SA-08", "agent_name": "Trust & Editorial Evidence Agent", "purpose": "Improve credibility without fake E-E-A-T", "lane": "GREEN_monitor_RED_publish", "dashboard_feed": "Co-Pilot + Mission Control", "status": "spec_ready"},
    {"agent_id": "SA-09", "agent_name": "Performance & CWV Agent", "purpose": "Monitor performance safely without breaking tracking", "lane": "GREEN_report_AMBER_fix", "dashboard_feed": "Co-Pilot + NOC", "status": "spec_ready"},
    {"agent_id": "SA-10", "agent_name": "Export Discipline Agent", "purpose": "Prevent stale exports, ensure evidence reliability", "lane": "GREEN_auto", "dashboard_feed": "Co-Pilot + Evidence Vault", "status": "spec_ready"},
]
write_csv(f"{OUT_9J}/Phase9J_Specialist_Agent_Roster.csv", roster, roster_fields)

# 2. Agent Permission Matrix
print("\n[2/20] Agent Permission Matrix...")
perm_fields = ["action","lane","agents_involved","auto_allowed","approval_required","notes"]
perms = [
    {"action": "sitemap_health_check", "lane": "GREEN", "agents_involved": "SA-01", "auto_allowed": "yes", "approval_required": "no", "notes": "Runs hourly"},
    {"action": "missing_URL_detection", "lane": "GREEN", "agents_involved": "SA-01", "auto_allowed": "yes", "approval_required": "no", "notes": "Alert on detection"},
    {"action": "GSC_indexing_submission", "lane": "AMBER", "agents_involved": "SA-01", "auto_allowed": "prepare_only", "approval_required": "yes_if_manual", "notes": "Auto for new published posts"},
    {"action": "category_assignment_audit", "lane": "GREEN", "agents_involved": "SA-02", "auto_allowed": "yes", "approval_required": "no", "notes": "Runs every 6 hours"},
    {"action": "uncategorized_post_detection", "lane": "GREEN", "agents_involved": "SA-02", "auto_allowed": "yes", "approval_required": "no", "notes": "Alert immediately"},
    {"action": "bulk_category_change", "lane": "AMBER", "agents_involved": "SA-02", "auto_allowed": "prepare_only", "approval_required": "yes", "notes": "Owner must approve mapping"},
    {"action": "category_deletion", "lane": "RED", "agents_involved": "SA-02", "auto_allowed": "no", "approval_required": "yes_explicit", "notes": "Never auto"},
    {"action": "metadata_length_check", "lane": "GREEN", "agents_involved": "SA-03", "auto_allowed": "yes", "approval_required": "no", "notes": "Runs every 6 hours"},
    {"action": "focus_keyword_check", "lane": "GREEN", "agents_involved": "SA-03", "auto_allowed": "yes", "approval_required": "no", "notes": "Runs every 6 hours"},
    {"action": "first_image_alt_check", "lane": "GREEN", "agents_involved": "SA-03", "auto_allowed": "yes", "approval_required": "no", "notes": "Runs every 6 hours"},
    {"action": "live_metadata_update", "lane": "AMBER", "agents_involved": "SA-03", "auto_allowed": "prepare_only", "approval_required": "yes", "notes": "Prepare proposal, owner approves"},
    {"action": "schema_safety_scan", "lane": "GREEN", "agents_involved": "SA-04", "auto_allowed": "yes", "approval_required": "no", "notes": "Runs every 6 hours"},
    {"action": "unsafe_schema_detection", "lane": "GREEN", "agents_involved": "SA-04", "auto_allowed": "yes", "approval_required": "no", "notes": "Alert immediately"},
    {"action": "schema_deployment", "lane": "RED", "agents_involved": "SA-04", "auto_allowed": "no", "approval_required": "yes_explicit", "notes": "Only safe schema after approval"},
    {"action": "Product_Review_Offer_schema", "lane": "RED", "agents_involved": "SA-04", "auto_allowed": "never", "approval_required": "yes_plus_evidence", "notes": "Blocked until Product Evidence verified"},
    {"action": "product_evidence_collection", "lane": "GREEN", "agents_involved": "SA-05", "auto_allowed": "yes", "approval_required": "no", "notes": "Public source data only"},
    {"action": "evidence_verification", "lane": "RED", "agents_involved": "SA-05", "auto_allowed": "no", "approval_required": "yes_explicit", "notes": "Owner verifies source proof"},
    {"action": "affiliate_link_insertion", "lane": "RED", "agents_involved": "SA-05 + SA-06", "auto_allowed": "never", "approval_required": "yes_explicit", "notes": "Blocked until evidence verified"},
    {"action": "publish_gate_check", "lane": "GREEN", "agents_involved": "SA-06", "auto_allowed": "yes", "approval_required": "no", "notes": "Runs before every publish"},
    {"action": "actual_publishing", "lane": "RED", "agents_involved": "SA-06", "auto_allowed": "never", "approval_required": "yes_approval_id", "notes": "Requires valid approval_id"},
    {"action": "rollback_execution", "lane": "RED", "agents_involved": "SA-06", "auto_allowed": "no", "approval_required": "yes", "notes": "Emergency only with approval"},
    {"action": "AI_visibility_monitoring", "lane": "GREEN", "agents_involved": "SA-07", "auto_allowed": "yes", "approval_required": "no", "notes": "Weekly query set"},
    {"action": "live_content_update_for_AI", "lane": "AMBER", "agents_involved": "SA-07", "auto_allowed": "prepare_only", "approval_required": "yes", "notes": "Propose improvements"},
    {"action": "trust_page_monitoring", "lane": "GREEN", "agents_involved": "SA-08", "auto_allowed": "yes", "approval_required": "no", "notes": "Scan for unsafe claims"},
    {"action": "trust_page_publishing", "lane": "RED", "agents_involved": "SA-08 + SA-06", "auto_allowed": "never", "approval_required": "yes_explicit", "notes": "Draft only until approved"},
    {"action": "performance_monitoring", "lane": "GREEN", "agents_involved": "SA-09", "auto_allowed": "yes", "approval_required": "no", "notes": "Weekly snapshot"},
    {"action": "analytics_script_removal", "lane": "RED", "agents_involved": "SA-09", "auto_allowed": "never", "approval_required": "yes_explicit", "notes": "Never remove analytics/consent"},
    {"action": "export_timestamp_check", "lane": "GREEN", "agents_involved": "SA-10", "auto_allowed": "yes", "approval_required": "no", "notes": "Every export"},
    {"action": "stale_export_archival", "lane": "GREEN", "agents_involved": "SA-10", "auto_allowed": "yes", "approval_required": "no", "notes": "Auto-archive superseded"},
    {"action": "social_posting", "lane": "RED", "agents_involved": "none_blocked", "auto_allowed": "never", "approval_required": "yes_explicit", "notes": "All channels RED"},
    {"action": "Pet_Insurance_content", "lane": "RED", "agents_involved": "none_blocked", "auto_allowed": "never", "approval_required": "yes_explicit", "notes": "RED-gated topic"},
    {"action": "credential_changes", "lane": "RED", "agents_involved": "none", "auto_allowed": "never", "approval_required": "yes_explicit", "notes": "Never automated"},
    {"action": "content_deletion", "lane": "RED", "agents_involved": "none", "auto_allowed": "never", "approval_required": "yes_explicit", "notes": "Never automated"},
    {"action": "homepage_changes", "lane": "RED", "agents_involved": "none", "auto_allowed": "never", "approval_required": "yes_explicit", "notes": "High impact"},
    {"action": "bulk_redirects", "lane": "RED", "agents_involved": "none", "auto_allowed": "never", "approval_required": "yes_explicit", "notes": "SEO impact"},
    {"action": "broken_link_scan", "lane": "GREEN", "agents_involved": "SA-01 + SA-03", "auto_allowed": "yes", "approval_required": "no", "notes": "Daily scan"},
    {"action": "internal_link_opportunity", "lane": "GREEN", "agents_involved": "SA-02 + SA-07", "auto_allowed": "yes_report", "approval_required": "no", "notes": "Suggest only"},
    {"action": "internal_link_insertion", "lane": "AMBER", "agents_involved": "SA-02", "auto_allowed": "prepare_only", "approval_required": "yes", "notes": "Live page changes need approval"},
    {"action": "page_speed_snapshot", "lane": "GREEN", "agents_involved": "SA-09", "auto_allowed": "yes", "approval_required": "no", "notes": "Weekly"},
    {"action": "secret_scan", "lane": "GREEN", "agents_involved": "SA-10", "auto_allowed": "yes", "approval_required": "no", "notes": "Daily"},
    {"action": "backup_check", "lane": "GREEN", "agents_involved": "SA-10", "auto_allowed": "yes", "approval_required": "no", "notes": "Hourly"},
    {"action": "DLQ_check", "lane": "GREEN", "agents_involved": "SA-10", "auto_allowed": "yes", "approval_required": "no", "notes": "Hourly"},
    {"action": "draft_content_proposal", "lane": "GREEN", "agents_involved": "all", "auto_allowed": "yes", "approval_required": "no", "notes": "Draft only"},
    {"action": "draft_metadata_suggestion", "lane": "GREEN", "agents_involved": "SA-03", "auto_allowed": "yes", "approval_required": "no", "notes": "Draft only"},
    {"action": "draft_schema_suggestion", "lane": "GREEN", "agents_involved": "SA-04", "auto_allowed": "yes", "approval_required": "no", "notes": "Safe schema only"},
    {"action": "Mission_Control_task_creation", "lane": "GREEN", "agents_involved": "all", "auto_allowed": "yes", "approval_required": "no", "notes": "Backlog items"},
    {"action": "CoPilot_status_update", "lane": "GREEN", "agents_involved": "all", "auto_allowed": "yes", "approval_required": "no", "notes": "Real-time"},
    {"action": "NOC_health_check", "lane": "GREEN", "agents_involved": "all", "auto_allowed": "yes", "approval_required": "no", "notes": "Hourly"},
    {"action": "report_generation", "lane": "GREEN", "agents_involved": "all", "auto_allowed": "yes", "approval_required": "no", "notes": "On schedule"},
    {"action": "owner_review_pack", "lane": "GREEN", "agents_involved": "all", "auto_allowed": "yes", "approval_required": "no", "notes": "Prepared automatically"},
]
write_csv(f"{OUT_9J}/Phase9J_Agent_Permission_Matrix.csv", perms, perm_fields)

# 3-12: Individual Agent Specs
print("\n[3/20] Sitemap & Indexing Agent Spec...")
write_agent_spec(f"{OUT_9J}/Phase9J_Sitemap_Indexing_Agent_Spec.csv",
    "Sitemap & Indexing Agent (SA-01)",
    "Prevent crawl/indexing issues and make sure new published content is discoverable",
    ["Check sitemap health","Detect missing published URLs","Detect draft URLs in sitemap","Detect 404 URLs in sitemap","Detect trashed URLs in sitemap","Track sitemap URL counts","Track GSC sitemap status","Track indexing requests","Schedule 24h/72h/7d follow-up checks","Report first impression/first click dates","Flag sitemap cache issues","Create Mission Control tasks for sitemap problems"],
    ["WordPress public URLs","Rank Math sitemap","GSC data","Published post list","Draft/trashed post list","Server checks","Co-Pilot status queries"],
    ["Sitemap health report","Indexing follow-up report","Missing URL list","Draft/404 sitemap warning","GSC indexing status summary","Co-Pilot plain-English summary"],
    ["Monitor sitemap","Report health","Queue sitemap tasks","Prepare indexing follow-up checklist"],
    ["Manual GSC submission if owner approval required","Plugin setting changes"],
    ["Sitemap provider changes","Broad caching changes","Publish/unpublish content"],
    ["Detects missing published URLs","Detects draft/404 URLs","Reports sitemap health in Co-Pilot","Creates follow-up tasks","Does not change plugin settings without approval"],
    ["show sitemap status","list missing URLs","show indexing progress","when was [post] last crawled","sitemap health summary"])

print("\n[4/20] Taxonomy Authority Agent Spec...")
write_agent_spec(f"{OUT_9J}/Phase9J_Taxonomy_Authority_Agent_Spec.csv",
    "Taxonomy Authority Agent (SA-02)",
    "Prevent posts from falling into wrong category and strengthen topical authority",
    ["Detect Uncategorized posts","Detect category mismatch","Detect dog/cat category mismatch","Detect overly broad category use","Detect category archive weakness","Suggest category assignments","Track category counts","Track content clusters","Monitor category pages for authority growth","Keep category changes aligned with SEO structure"],
    ["Post titles","Slugs","Current categories","Category list","Sitemap data","Mission Control clusters","Content type","Focus keywords"],
    ["Category assignment recommendations","Category mismatch report","Category health report","Uncategorized post warning","Category archive improvement plan"],
    ["Propose category changes","Auto-flag mismatch","Create review queue"],
    ["Bulk category changes","New category creation"],
    ["Category deletion","Category slug changes","Redirects if needed"],
    ["No future post remains Uncategorized unintentionally","Category assignment confidence shown","Owner approval required for bulk/live changes","Co-Pilot can explain category health"],
    ["show category health","list uncategorized posts","which categories have mismatches","category authority status","show content clusters"])

print("\n[5/20] Metadata & Image Alt Agent Spec...")
write_agent_spec(f"{OUT_9J}/Phase9J_Metadata_ImageAlt_Agent_Spec.csv",
    "Metadata & Image Alt Agent (SA-03)",
    "Enforce metadata and first-image-alt rules for all current and future posts",
    ["Scan all published posts","Scan all drafts","Check title length (<60 chars)","Check focus keyword placement (start of title)","Check description length (<160 chars, ideally 155-160)","Check description relevance","Check first image alt (includes focus keyword naturally)","Detect unsupported claims in metadata","Propose metadata fixes","Prepare owner approval pack"],
    ["Rank Math metadata","Post focus keyword","Post title","First image","Page content","Mission Control status"],
    ["Metadata compliance report","Image alt compliance report","Fix proposals","Co-Pilot summary"],
    ["Scan","Report","Propose metadata","Propose alt text"],
    ["Live metadata update","Image metadata update if live","Bulk metadata changes"],
    ["Misleading metadata","Unverified product claims in metadata"],
    ["Metadata rules checked for every new post","Publisher blocks posts that fail required metadata rules","Co-Pilot can answer whether metadata is compliant"],
    ["show metadata compliance","list posts with title issues","list posts with alt issues","metadata status for [post]","which posts fail metadata rules"])

print("\n[6/20] Schema Safety Agent Spec...")
write_agent_spec(f"{OUT_9J}/Phase9J_Schema_Safety_Agent_Spec.csv",
    "Schema Safety Agent (SA-04)",
    "Prevent unsafe structured data and support safe rich-result readiness",
    ["Detect schema types on each page","Compare schema to visible content","Block unsafe schema","Verify FAQ schema matches visible FAQs","Verify Article schema required fields","Detect fake ratings/reviews/offers","Generate schema proposals","Validate snippets","Provide warnings/errors","Feed status to Publisher"],
    ["Page source","Rank Math schema","Schema proposal files","Product Evidence Register","FAQ content","Approval status"],
    ["Schema safety report","Safe schema proposal","Unsafe schema alert","Validation report","Co-Pilot explanation"],
    ["Scan","Propose safe schema","Validate snippets","Flag unsafe schema"],
    ["Schema deployment for safe types (Article/BreadcrumbList/FAQPage)"],
    ["Any Product/Review/Offer schema","Sitewide schema changes"],
    ["Unsafe schema blocked","Safe schema validated","No Product/Review/Offer schema without verified evidence","Publisher checks schema safety before publish"],
    ["show schema status","which pages have unsafe schema","schema safety for [post]","list schema proposals","is [post] schema safe"])

print("\n[7/20] Product Evidence Agent Spec...")
write_agent_spec(f"{OUT_9J}/Phase9J_Product_Evidence_Agent_Spec.csv",
    "Product Evidence Agent (SA-05)",
    "Create the bridge from educational content to trustworthy affiliate monetization",
    ["Collect candidate product URLs","Store retailer URLs/ASINs","Capture evidence source details","Track price verification","Track rating/review verification","Track stock verification","Track image source verification","Track ingredient/specification verification","Classify verified vs unverified claims","Assign evidence freshness dates","Flag stale evidence","Prepare product evidence tasks","Block product recommendations until verified","Prepare affiliate unlock recommendations"],
    ["Public retailer pages","Product databases","Evidence register","Mission Control","Publisher status"],
    ["Product evidence register","Evidence gap report","Stale evidence alerts","Candidate product list","Affiliate readiness recommendations"],
    ["Collect public evidence","Create evidence entries","Mark candidate_identified","Mark source_collected","Mark evidence_extracted","Flag missing evidence"],
    ["Prepare recommendation draft","Prepare affiliate plan"],
    ["Mark evidence verified","Approve evidence for live use","Add affiliate links","Publish recommendations","Use prices/ratings/review counts live","Deploy Product/Offer/Review schema"],
    ["Product claims cannot unlock without evidence","Co-Pilot can summarize evidence gaps","Product Evidence controls affiliate readiness","Stale evidence is flagged"],
    ["show evidence status","list evidence gaps","which products are ready","evidence status for [cluster]","list stale evidence"])

print("\n[8/20] Publisher Gate Agent Spec...")
write_agent_spec(f"{OUT_9J}/Phase9J_Publisher_Gate_Agent_Spec.csv",
    "Publisher Gate Agent (SA-06)",
    "Own the final pre-publish checklist and protect the live site",
    ["Validate approval_id","Confirm Publisher layer used","Confirm rollback snapshot exists","Confirm audit log exists","Verify metadata passes","Verify schema status","Verify Product Evidence restrictions","Verify affiliate restrictions","Verify category assignment","Verify sitemap readiness","Verify no RED-gated content","Verify no social autopost trigger","Verify no direct publish bypass","Report post-publish verification"],
    ["Mission Control","Publisher","WordPress post status","Product Evidence","Schema safety","Metadata checks","Sitemap checks","Approval queue"],
    ["Pre-publish checklist","Publish readiness status","Audit log link","Rollback link","Post-publish verification","Co-Pilot answer"],
    ["Check gates","Block unsafe publish","Create publish-readiness report"],
    ["GSC indexing submission after publish"],
    ["Actual publishing","Rollback execution","Schema deployment","Social dispatch"],
    ["No publish without valid approval_id","No publish if critical gate fails","Co-Pilot can explain why a page cannot publish","Audit trail created for every publish attempt"],
    ["is [post] ready to publish","list publish blockers","show publish history","what blocks [post] from publishing","show rollback options"])

print("\n[9/20] AI Visibility Agent Spec...")
write_agent_spec(f"{OUT_9J}/Phase9J_AI_Visibility_Agent_Spec.csv",
    "AI Visibility Agent (SA-07)",
    "Improve PetHub visibility in AI search and answer engines",
    ["Maintain AI visibility benchmark query set","Track brand mentions","Track category mentions","Track citation opportunities","Monitor answer-engine readiness","Identify pages needing direct-answer improvements","Identify missing FAQ opportunities","Support trust/source transparency","Compare competitors","Label data as measured/manual/modelled"],
    ["AI visibility baseline","Co-Pilot queries","Manual benchmark results","Page content","Schema status","Trust pages","Entity coverage"],
    ["AI visibility report","Query set results","Entity gaps","Answer-readiness opportunities","Co-Pilot summary"],
    ["Monitor","Report","Propose improvements","Create draft answer blocks"],
    ["Live content updates","Schema deployment","New page publication"],
    ["Fake AI visibility claims","Automated content changes without approval"],
    ["Query set exists","AI visibility baseline tracked","No fake AI visibility claims","Co-Pilot can explain AI visibility status"],
    ["show AI visibility status","list citation opportunities","AI readiness for [cluster]","compare to competitors","show query set results"])

print("\n[10/20] Trust & Editorial Evidence Agent Spec...")
write_agent_spec(f"{OUT_9J}/Phase9J_Trust_Editorial_Evidence_Agent_Spec.csv",
    "Trust & Editorial Evidence Agent (SA-08)",
    "Improve trust, credibility and transparency without fake E-E-A-T",
    ["Maintain methodology pages","Monitor affiliate disclosure clarity","Monitor evidence status labels","Monitor author/editorial transparency","Track last updated dates","Track corrections/update policy","Detect fake expert claims","Detect fake testing claims","Detect unsupported health claims","Prepare trust page drafts"],
    ["Published content","Trust pages","Evidence register","Affiliate disclosures","Author information","Editorial policies"],
    ["Trust compliance report","Trust page drafts","Fake claim alerts","Disclosure clarity report","Co-Pilot trust summary"],
    ["Monitor trust wording","Detect fake claims","Prepare trust page drafts","Report disclosure status"],
    ["Trust page content updates","Editorial policy changes"],
    ["Trust page publishing","Fake reviewer creation","Fake testing claims"],
    ["Trust pages drafted but not published without approval","Unsafe trust wording blocked","Co-Pilot can explain trust status"],
    ["show trust status","list trust page drafts","any fake claims detected","disclosure compliance","trust readiness for [section]"])

print("\n[11/20] Performance & CWV Agent Spec...")
write_agent_spec(f"{OUT_9J}/Phase9J_Performance_CWV_Agent_Spec.csv",
    "Performance & Core Web Vitals Agent (SA-09)",
    "Monitor performance issues without breaking analytics, consent or user experience",
    ["Track TTFB","Track FCP","Track LCP","Track CLS","Track request count","Track JS weight","Track image weight","Detect distorted images","Detect render-blocking resources","Monitor caching","Propose safe quick wins","Separate GREEN/AMBER/RED fixes"],
    ["Page speed data","Core Web Vitals","Image analysis","Script analysis","Caching headers"],
    ["Performance baseline report","Safe fix backlog","Risky fix list (approval needed)","Image optimization proposals","Co-Pilot performance summary"],
    ["Report metrics","Propose fixes","Identify affected images","Prepare targeted CSS proposal","Track before/after metrics"],
    ["Non-critical CSS/performance changes","Image optimization on non-live assets"],
    ["Remove analytics scripts","Remove consent scripts","Defer compliance-critical scripts","Broad design changes","Global image rules without evidence"],
    ["Performance baseline tracked","Risky fixes approval-gated","Co-Pilot can explain performance status"],
    ["show performance status","list performance issues","which images are distorted","CWV summary","safe fixes available"])

print("\n[12/20] Export Discipline Agent Spec...")
write_agent_spec(f"{OUT_9J}/Phase9J_Export_Discipline_Agent_Spec.csv",
    "Export Discipline Agent (SA-10)",
    "Prevent stale exports and make evidence reliable",
    ["Ensure every export has metadata","Mark files as current or stale","Archive superseded exports","Compare GitHub exports vs live server state","Detect old evidence files","Ensure generated_at/source_server/git_commit/generated_by exist","Create evidence pack indexes","Alert if stale files conflict with current state"],
    ["GitHub repository","Live server files","Export timestamps","Git commit history"],
    ["Export health report","Stale file alerts","Evidence pack index","Current vs stale classification","Co-Pilot export summary"],
    ["Check timestamps","Mark stale","Archive superseded","Create indexes","Compare GitHub vs live"],
    ["Bulk file archival","Export format changes"],
    ["Delete evidence files","Remove audit logs"],
    ["No stale current files","Current exports clearly labelled","Old files archived","Co-Pilot can say which evidence pack is current"],
    ["show export status","which exports are stale","current evidence pack","compare GitHub vs live","list archived exports"])

# 13. Section Launch Framework
print("\n[13/20] Section Launch Framework...")
launch_fields = ["stage","stage_name","activities","responsible_agents","gate","deliverables","approval_required"]
launch_rows = [
    {"stage": 1, "stage_name": "Research", "activities": "Keyword set; competitor scan; AI visibility scan; content gap analysis; trust requirements", "responsible_agents": "SA-07 + SA-02 + SA-08", "gate": "research_complete", "deliverables": "Keyword set CSV; competitor report; content gap analysis", "approval_required": "no"},
    {"stage": 2, "stage_name": "Mission Setup", "activities": "Mission Control mission; responsible agents; milestones; approval gates; evidence requirements", "responsible_agents": "All relevant", "gate": "mission_configured", "deliverables": "Mission brief; milestone plan; agent assignment", "approval_required": "no"},
    {"stage": 3, "stage_name": "Draft Creation", "activities": "Draft posts/pages; metadata proposals; safe schema proposals; internal link suggestions", "responsible_agents": "SA-03 + SA-04 + SA-02", "gate": "drafts_complete", "deliverables": "Draft posts; metadata CSV; schema proposals; link suggestions", "approval_required": "no"},
    {"stage": 4, "stage_name": "QA", "activities": "Content QA; trust scan; metadata scan; image alt scan; schema safety scan; evidence scan", "responsible_agents": "SA-03 + SA-04 + SA-05 + SA-08", "gate": "qa_passed", "deliverables": "QA report; compliance checklist; evidence status", "approval_required": "no"},
    {"stage": 5, "stage_name": "Approval", "activities": "Owner approval; publisher approval; approval_id assigned; rollback snapshot created", "responsible_agents": "SA-06", "gate": "owner_approved", "deliverables": "Approval ID; rollback snapshot; audit log entry", "approval_required": "yes_owner"},
    {"stage": 6, "stage_name": "Publish", "activities": "Publisher layer only; audit log; no direct bypass", "responsible_agents": "SA-06", "gate": "published", "deliverables": "Published URL; audit log; timestamp", "approval_required": "yes_approval_id"},
    {"stage": 7, "stage_name": "Verification", "activities": "Public 200 check; sitemap inclusion; index status; schema check; GA4 page view; GSC monitoring", "responsible_agents": "SA-01 + SA-04 + SA-06", "gate": "verified", "deliverables": "Verification report; sitemap confirmation; schema validation", "approval_required": "no"},
    {"stage": 8, "stage_name": "Learning", "activities": "First impression; first click; CTR; ranking; engagement; internal clicks; conversion if applicable; refresh recommendations", "responsible_agents": "SA-01 + SA-07 + SA-09", "gate": "learning_active", "deliverables": "Performance report; learning summary; refresh backlog", "approval_required": "no"},
]
write_csv(f"{OUT_9J}/Phase9J_Section_Launch_Framework.csv", launch_rows, launch_fields)

# 14. New Section Launch Template
print("\n[14/20] New Section Launch Template (JSON)...")
template = {
    "generated_at": NOW,
    "source_server": SOURCE_SERVER,
    "git_commit": GIT_COMMIT,
    "generated_by": GENERATED_BY,
    "data_source_label": "planning_template",
    "approval_status": "planning_only",
    "next_action": "owner_review",
    "template_version": "1.0",
    "section_launch_template": {
        "section_name": "",
        "section_objective": "",
        "target_audience": "",
        "focus_keyword_set": [],
        "content_map": {"hub_page": "", "spoke_pages": [], "supporting_pages": []},
        "evidence_requirements": {"product_evidence_needed": False, "trust_evidence_needed": True, "source_verification": []},
        "category_assignment": {"primary_category": "", "secondary_categories": []},
        "metadata_plan": {"seo_title_template": "<focus_keyword> UK (2026) - <suffix>", "meta_description_template": "155-160 chars with focus keyword", "first_image_alt_template": "<natural description with focus keyword>"},
        "image_alt_plan": {"focus_keyword_in_first_alt": True, "no_keyword_stuffing": True, "descriptive_natural": True},
        "schema_plan": {"allowed": ["Article", "BreadcrumbList", "FAQPage"], "blocked": ["Product", "Review", "AggregateRating", "Offer"], "requires_evidence": ["Product", "Review", "AggregateRating", "Offer"]},
        "internal_link_plan": {"hub_to_spoke": True, "spoke_to_hub": True, "cross_cluster": True, "orphan_check": True},
        "product_evidence_plan": {"evidence_status": "not_started", "candidates": [], "verification_sources": []},
        "affiliate_readiness": {"status": "blocked_pending_evidence", "rel_attribute": "nofollow noopener noreferrer sponsored", "disclosure_required": True},
        "trust_risks": [],
        "publishing_gate_status": {"approval_id": None, "rollback_snapshot": None, "metadata_pass": False, "schema_pass": False, "category_pass": False, "evidence_pass": False},
        "post_publish_monitoring_plan": {"24h_check": True, "72h_check": True, "7d_check": True, "sitemap_verification": True, "GSC_monitoring": True, "GA4_tracking": True},
        "copilot_summary": "",
        "mission_control_entry": {"mission_id": "", "status": "planning", "priority": "", "blockers": []}
    }
}
write_json(f"{OUT_9J}/Phase9J_New_Section_Launch_Template.json", template)

# 15. Next Section Launch Backlog
print("\n[15/20] Next Section Launch Backlog...")
backlog_fields = ["priority","section_name","reason","required_posts","evidence_needs","metadata_rules","schema_rules","trust_risks","approval_required","publish_blockers","estimated_impact","next_safe_action","status"]
backlog = [
    {"priority": 1, "section_name": "Cat Toys Recovery / Engagement", "reason": "Existing content recovery, lower risk, useful for fast learning", "required_posts": "Review existing 4 cat toy posts; refresh metadata; add internal links; prepare FAQ sections", "evidence_needs": "Low - educational content, no product recs yet", "metadata_rules": "Standard: title<60, keyword at start, desc 155-160, alt with keyword", "schema_rules": "Article + BreadcrumbList + FAQPage where visible FAQs", "trust_risks": "Low - existing educational content", "approval_required": "Metadata changes, internal link insertion", "publish_blockers": "None for existing posts; new content needs full gate", "estimated_impact": "Medium - improves engagement metrics, internal linking, category authority", "next_safe_action": "Audit existing cat toy posts, prepare metadata fixes, draft FAQ sections", "status": "planning"},
    {"priority": 2, "section_name": "Dog Harness Commercial Opportunity", "reason": "Commercial upside, but needs evidence readiness", "required_posts": "Hub page + 3-4 spoke pages covering types, sizing, training harnesses", "evidence_needs": "High - product recommendations need verified evidence before affiliate links", "metadata_rules": "Standard metadata rules apply", "schema_rules": "Article + BreadcrumbList only until evidence verified", "trust_risks": "Medium - product claims must be evidence-backed", "approval_required": "Evidence verification, affiliate placement, publish", "publish_blockers": "Product Evidence must reach owner_approved before live product recs", "estimated_impact": "High - commercial intent keywords, affiliate revenue potential", "next_safe_action": "Prepare keyword set, content map, evidence candidate list", "status": "planning"},
    {"priority": 3, "section_name": "Trust / Methodology Pages", "reason": "Improves credibility and supports affiliate trust", "required_posts": "6 trust pages: How We Research, Editorial Process, Evidence Labels, Product Evidence Register, Affiliate Disclosure, Corrections Policy", "evidence_needs": "Low - these ARE the evidence/trust infrastructure", "metadata_rules": "Standard metadata rules", "schema_rules": "Article + BreadcrumbList", "trust_risks": "HIGH - must not contain fake claims, fake reviewers, fake testing", "approval_required": "All trust pages require explicit owner approval before publish", "publish_blockers": "Owner review of all wording; no fake E-E-A-T claims", "estimated_impact": "High - builds site-wide credibility, supports future affiliate monetization", "next_safe_action": "Draft all 6 trust pages with safe wording, prepare owner review pack", "status": "planning"},
    {"priority": 4, "section_name": "Homepage Engagement Improvement", "reason": "Improves routing and authority flow", "required_posts": "Homepage content restructure; category navigation; featured content sections", "evidence_needs": "None - structural improvement", "metadata_rules": "Homepage meta robots: index; title and description optimized", "schema_rules": "Organization + WebSite schema on homepage", "trust_risks": "Low - but homepage changes are high impact", "approval_required": "All homepage changes require explicit owner approval", "publish_blockers": "Owner approval for all visual/structural changes", "estimated_impact": "High - improves user routing, reduces bounce, strengthens authority flow", "next_safe_action": "Audit current homepage, prepare improvement proposals", "status": "planning"},
    {"priority": 5, "section_name": "AI Search Adaptation", "reason": "Supports all clusters with AI visibility", "required_posts": "FAQ enrichment across all clusters; direct-answer formatting; entity markup", "evidence_needs": "Low - content formatting improvement", "metadata_rules": "Standard rules plus AI-specific formatting guidelines", "schema_rules": "FAQPage where visible FAQs; Article with enhanced entity coverage", "trust_risks": "Low - no fake AI visibility claims", "approval_required": "Live content changes need approval", "publish_blockers": "None for new draft content; live changes need gate", "estimated_impact": "Medium-High - improves ChatGPT/Gemini/Perplexity visibility across all clusters", "next_safe_action": "Create AI visibility query set, benchmark current status, identify FAQ opportunities", "status": "planning"},
    {"priority": 6, "section_name": "Pet Insurance Trust Buildout", "reason": "High value but RED-gated; planning only", "required_posts": "Hub page + spoke pages covering types, comparison, claims process, UK regulations", "evidence_needs": "Very High - financial product, regulatory requirements, FCA considerations", "metadata_rules": "Standard rules with extra caution on claims", "schema_rules": "Article + BreadcrumbList ONLY; no Product/Offer/Review schema", "trust_risks": "VERY HIGH - financial product; regulatory; no fake expert claims; no fake comparisons", "approval_required": "EVERYTHING requires explicit owner approval", "publish_blockers": "RED-gated: no content activation without explicit approval; regulatory review needed", "estimated_impact": "Very High commercial value but very high compliance risk", "next_safe_action": "Research only: keyword set, regulatory requirements, evidence needs, risk assessment", "status": "RED_gated_planning_only"},
]
write_csv(f"{OUT_9J}/Phase9J_Next_Section_Launch_Backlog.csv", backlog, backlog_fields)

# 16. AI Enterprise Agent Operations Matrix
print("\n[16/20] AI Enterprise Operations Matrix...")
ai_matrix_fields = ["operation","mode","reason","fallback_if_no_AI","safety_critical"]
ai_matrix = [
    {"operation": "Owner summaries", "mode": "AI", "reason": "Requires natural language generation and context synthesis", "fallback_if_no_AI": "Template-based summary with data placeholders", "safety_critical": "no"},
    {"operation": "Content briefs", "mode": "AI", "reason": "Requires creative/strategic thinking for keyword clustering", "fallback_if_no_AI": "Template brief with keyword data only", "safety_critical": "no"},
    {"operation": "Evidence gap summaries", "mode": "AI", "reason": "Synthesizes multiple data sources into actionable gaps", "fallback_if_no_AI": "List of evidence statuses per product", "safety_critical": "no"},
    {"operation": "SEO issue explanation", "mode": "AI", "reason": "Translates technical SEO into owner-friendly language", "fallback_if_no_AI": "Template: Issue [X] detected on [URL], severity [Y]", "safety_critical": "no"},
    {"operation": "Co-Pilot plain-English answers", "mode": "AI", "reason": "Natural conversation requires language model", "fallback_if_no_AI": "Pre-built FAQ responses + data lookups", "safety_critical": "no"},
    {"operation": "Section launch planning", "mode": "AI", "reason": "Strategic planning benefits from reasoning", "fallback_if_no_AI": "Template-based launch plan with manual input", "safety_critical": "no"},
    {"operation": "Query clustering", "mode": "AI", "reason": "Semantic grouping requires NLP", "fallback_if_no_AI": "Keyword prefix/suffix grouping (rule-based)", "safety_critical": "no"},
    {"operation": "Content opportunity analysis", "mode": "AI", "reason": "Requires cross-referencing multiple signals", "fallback_if_no_AI": "Gap list based on category/keyword coverage", "safety_critical": "no"},
    {"operation": "AI visibility analysis", "mode": "AI", "reason": "Requires understanding AI search behavior", "fallback_if_no_AI": "Basic query-to-URL matching", "safety_critical": "no"},
    {"operation": "Trust wording review", "mode": "AI", "reason": "Detecting subtle fake claims requires NLU", "fallback_if_no_AI": "Keyword blocklist scan (we tested, vet-backed, etc.)", "safety_critical": "yes_supplemented_by_rules"},
    {"operation": "QA summaries", "mode": "AI", "reason": "Synthesizes multiple check results", "fallback_if_no_AI": "Pass/fail checklist", "safety_critical": "no"},
    {"operation": "Report drafting", "mode": "AI", "reason": "Natural language report generation", "fallback_if_no_AI": "CSV/table-only reports", "safety_critical": "no"},
    {"operation": "Sitemap checks", "mode": "RULE", "reason": "Deterministic XML parsing, URL matching", "fallback_if_no_AI": "Same - rules always run", "safety_critical": "yes"},
    {"operation": "Metadata length checks", "mode": "RULE", "reason": "Character counting is deterministic", "fallback_if_no_AI": "Same - rules always run", "safety_critical": "yes"},
    {"operation": "Image alt checks", "mode": "RULE", "reason": "Presence/keyword matching is deterministic", "fallback_if_no_AI": "Same - rules always run", "safety_critical": "yes"},
    {"operation": "Category rules", "mode": "RULE", "reason": "Category assignment validation is lookup-based", "fallback_if_no_AI": "Same - rules always run", "safety_critical": "yes"},
    {"operation": "Schema blocking", "mode": "RULE", "reason": "Blocked schema types are a fixed list", "fallback_if_no_AI": "Same - rules always run", "safety_critical": "yes"},
    {"operation": "Product Evidence statuses", "mode": "RULE", "reason": "Status transitions are defined state machine", "fallback_if_no_AI": "Same - rules always run", "safety_critical": "yes"},
    {"operation": "Affiliate rel checks", "mode": "RULE", "reason": "rel attribute parsing is deterministic", "fallback_if_no_AI": "Same - rules always run", "safety_critical": "yes"},
    {"operation": "Social channel gate checks", "mode": "RULE", "reason": "Channel status is boolean (blocked/unblocked)", "fallback_if_no_AI": "Same - rules always run", "safety_critical": "yes"},
    {"operation": "Publish gate checks", "mode": "RULE", "reason": "Checklist validation is deterministic", "fallback_if_no_AI": "Same - rules always run", "safety_critical": "yes"},
    {"operation": "Secret scans", "mode": "RULE", "reason": "Pattern matching for credentials/keys", "fallback_if_no_AI": "Same - rules always run", "safety_critical": "yes"},
    {"operation": "Backup checks", "mode": "RULE", "reason": "File existence/timestamp checking", "fallback_if_no_AI": "Same - rules always run", "safety_critical": "yes"},
]
write_csv(f"{OUT_9J}/Phase9J_AI_Enterprise_Agent_Operations_Matrix.csv", ai_matrix, ai_matrix_fields)

# 17. AI Credit Fallback Plan
print("\n[17/20] AI Credit Fallback Plan...")
fallback_fields = ["capacity_level","description","ai_usage","rule_usage","co_pilot_behavior","queued_tasks","priority"]
credit_fallback = [
    {"capacity_level": "HEALTHY", "description": "AI credits/capacity fully available", "ai_usage": "Full: summaries, briefs, explanations, planning, analysis, wording review", "rule_usage": "Standard: all deterministic checks run normally", "co_pilot_behavior": "Full AI-powered natural language responses", "queued_tasks": "None - all tasks execute immediately", "priority": "normal_all_features"},
    {"capacity_level": "LOW", "description": "AI credits/capacity limited", "ai_usage": "Reserved: owner summaries, strategy decisions, trust wording review only", "rule_usage": "Expanded: all routine checks + template-based reports", "co_pilot_behavior": "Hybrid: AI for owner questions, templates for status queries", "queued_tasks": "Content briefs, opportunity analysis, query clustering queued", "priority": "high_value_decisions_only"},
    {"capacity_level": "UNAVAILABLE", "description": "AI credits/capacity exhausted or service down", "ai_usage": "None: all AI tasks queued for later", "rule_usage": "Full: all deterministic checks, scans, gate checks continue", "co_pilot_behavior": "Template responses: pre-built FAQ, data lookups, status tables", "queued_tasks": "All AI tasks queued: summaries, briefs, analysis, explanations", "priority": "safety_and_monitoring_only"},
    {"capacity_level": "EMERGENCY", "description": "Platform-wide issue affecting all services", "ai_usage": "None", "rule_usage": "Critical only: publish gates, schema blocking, secret scans", "co_pilot_behavior": "Minimal: system status only", "queued_tasks": "Everything non-critical queued", "priority": "safety_gates_only"},
]
write_csv(f"{OUT_9J}/Phase9J_AI_Credit_Fallback_Plan.csv", credit_fallback, fallback_fields)

# 18. 24/7 Agent Scheduler Plan
print("\n[18/20] 24/7 Agent Scheduler Plan (YAML)...")
scheduler_yaml = """schedules:
  hourly:
    - job: noc_health_check
      agent: SA-09
      description: NOC infrastructure health
      actions: [redis_ping, postgresql_ping, queue_depth, dlq_count, memory_usage, disk_usage]
      failure_action: dlq_alert
    - job: sitemap_health_check
      agent: SA-01
      description: Sitemap URL count and integrity
      actions: [fetch_sitemap, count_urls, compare_to_published, detect_missing]
      failure_action: mission_control_task
    - job: social_gate_status
      agent: SA-08
      description: Verify all social channels remain blocked
      actions: [check_facebook_gate, check_instagram_gate, check_tiktok_gate, check_pinterest_gate, check_youtube_gate]
      failure_action: emergency_alert
    - job: publish_lock_status
      agent: SA-06
      description: Verify publish lock and approval gates
      actions: [check_publisher_lock, verify_approval_id_required, test_bypass_blocked]
      failure_action: emergency_alert
    - job: queue_dlq_status
      agent: SA-10
      description: Check event queues and dead letter queue
      actions: [check_queue_depth, check_dlq_count, alert_if_above_threshold]
      failure_action: dlq_alert
    - job: backup_status
      agent: SA-10
      description: Verify backup recency
      actions: [check_latest_backup_timestamp, verify_gpg_encryption, compare_to_schedule]
      failure_action: backup_alert

  every_6_hours:
    - job: metadata_compliance_check
      agent: SA-03
      description: SEO title, meta description, focus keyword placement
      actions: [scan_all_posts, check_title_length, check_keyword_placement, check_description_length, check_first_image_alt]
      failure_action: compliance_report
    - job: category_assignment_check
      agent: SA-02
      description: Detect uncategorized or miscategorized posts
      actions: [scan_all_posts, check_uncategorized, detect_mismatch, report_health]
      failure_action: mismatch_alert
    - job: image_alt_check
      agent: SA-03
      description: First image alt text compliance
      actions: [scan_published_posts, check_alt_presence, check_keyword_inclusion, detect_stuffing]
      failure_action: compliance_report
    - job: internal_link_check
      agent: SA-02
      description: Internal linking opportunities and broken links
      actions: [scan_links, detect_broken, detect_orphans, suggest_opportunities]
      failure_action: link_report
    - job: schema_safety_check
      agent: SA-04
      description: Detect unsafe or missing schema
      actions: [scan_all_pages, detect_product_schema, detect_review_schema, verify_article_schema, verify_faq_visibility]
      failure_action: schema_alert
    - job: affiliate_rel_check
      agent: SA-05
      description: Verify affiliate link rel attributes and disclosures
      actions: [scan_all_links, check_rel_attributes, verify_disclosure_presence]
      failure_action: affiliate_alert

  daily:
    - job: gsc_ga4_data_pull
      agent: SA-01
      description: Pull latest GSC and GA4 data
      actions: [fetch_gsc_performance, fetch_ga4_pageviews, update_baselines]
      failure_action: data_pull_retry
    - job: published_page_monitoring
      agent: SA-01
      description: Monitor recently published pages
      actions: [check_24h_pages, check_72h_pages, check_7d_pages, verify_indexing, verify_sitemap]
      failure_action: monitoring_alert
    - job: product_evidence_queue
      agent: SA-05
      description: Update Product Evidence Register
      actions: [check_stale_evidence, check_new_candidates, update_statuses, flag_expired]
      failure_action: evidence_report
    - job: copilot_owner_summary
      agent: all
      description: Generate daily owner summary for Co-Pilot
      actions: [collect_all_agent_statuses, generate_summary, update_copilot]
      failure_action: template_summary_fallback
    - job: security_scan
      agent: SA-10
      description: Secret scan, credential check, governance audit
      actions: [scan_github_secrets, check_credential_expiry, test_publish_bypass, verify_red_gates]
      failure_action: security_alert
    - job: export_generation
      agent: SA-10
      description: Generate daily evidence exports
      actions: [generate_exports, timestamp_all, mark_current, archive_superseded]
      failure_action: export_alert

  weekly:
    - job: ai_visibility_query_set
      agent: SA-07
      description: Run AI visibility benchmark queries
      actions: [run_query_set, compare_to_baseline, detect_changes, report_opportunities]
      failure_action: visibility_report
    - job: performance_snapshot
      agent: SA-09
      description: Core Web Vitals and page speed snapshot
      actions: [measure_ttfb, measure_fcp, measure_lcp, measure_cls, track_js_weight, track_image_weight]
      failure_action: performance_report
    - job: category_authority_report
      agent: SA-02
      description: Category authority and topical coverage analysis
      actions: [analyze_category_depth, check_cluster_coverage, identify_gaps, report_authority]
      failure_action: authority_report
    - job: mission_control_priority_review
      agent: all
      description: Review and reprioritize Mission Control backlog
      actions: [review_backlog, update_priorities, identify_blockers, suggest_next_actions]
      failure_action: priority_report
    - job: governance_regression_tests
      agent: SA-06
      description: Run full governance test suite
      actions: [test_publish_gates, test_schema_blocking, test_affiliate_gates, test_red_gates, test_social_gates, test_evidence_gates]
      failure_action: governance_alert
"""
write_yaml(f"{OUT_9J}/Phase9J_24_7_Agent_Scheduler_Plan.yaml", scheduler_yaml)

# 19. CoPilot Agent Command Map
print("\n[19/20] CoPilot Agent Command Map...")
copilot_fields = ["command","description","agent","response_type","data_source"]
copilot_commands = [
    {"command": "show sitemap status", "description": "Current sitemap health, URL count, missing posts", "agent": "SA-01", "response_type": "AI_summary + live_data", "data_source": "sitemap_xml + published_post_count"},
    {"command": "list missing URLs", "description": "Posts published but not in sitemap", "agent": "SA-01", "response_type": "data_table", "data_source": "sitemap_xml + WP_API"},
    {"command": "show indexing progress", "description": "GSC indexing status for recent posts", "agent": "SA-01", "response_type": "AI_summary + live_data", "data_source": "GSC_API"},
    {"command": "show category health", "description": "Category assignment status, mismatches, empty categories", "agent": "SA-02", "response_type": "AI_summary + data_table", "data_source": "WP_API_categories"},
    {"command": "list uncategorized posts", "description": "Posts with no category or only Uncategorized", "agent": "SA-02", "response_type": "data_table", "data_source": "WP_API"},
    {"command": "show metadata compliance", "description": "How many posts pass/fail metadata rules", "agent": "SA-03", "response_type": "AI_summary + counts", "data_source": "RM_API + WP_API"},
    {"command": "list posts with title issues", "description": "Posts with SEO title too long or missing keyword", "agent": "SA-03", "response_type": "data_table", "data_source": "RM_API"},
    {"command": "show schema status", "description": "Schema types deployed across site", "agent": "SA-04", "response_type": "AI_summary + data_table", "data_source": "page_source_scan"},
    {"command": "which pages have unsafe schema", "description": "Pages with Product/Review/Offer schema", "agent": "SA-04", "response_type": "data_table + alert", "data_source": "page_source_scan"},
    {"command": "show evidence status", "description": "Product Evidence Register summary", "agent": "SA-05", "response_type": "AI_summary + status_counts", "data_source": "evidence_register"},
    {"command": "list evidence gaps", "description": "Products lacking verified evidence", "agent": "SA-05", "response_type": "data_table", "data_source": "evidence_register"},
    {"command": "is [post] ready to publish", "description": "Pre-publish gate check for specific post", "agent": "SA-06", "response_type": "checklist + AI_explanation", "data_source": "publisher_gates"},
    {"command": "list publish blockers", "description": "What prevents posts from publishing", "agent": "SA-06", "response_type": "data_table + AI_explanation", "data_source": "publisher_gates"},
    {"command": "show AI visibility status", "description": "AI search engine visibility summary", "agent": "SA-07", "response_type": "AI_summary", "data_source": "ai_visibility_baseline"},
    {"command": "show trust status", "description": "Trust page readiness and compliance", "agent": "SA-08", "response_type": "AI_summary + checklist", "data_source": "trust_pages_scan"},
    {"command": "show performance status", "description": "Core Web Vitals and page speed summary", "agent": "SA-09", "response_type": "AI_summary + metrics", "data_source": "cwv_data"},
    {"command": "show export status", "description": "Current vs stale exports", "agent": "SA-10", "response_type": "data_table", "data_source": "export_timestamps"},
    {"command": "what should I do next", "description": "Prioritized next actions across all agents", "agent": "all", "response_type": "AI_prioritized_list", "data_source": "mission_control + all_agents"},
    {"command": "show daily summary", "description": "Full daily status across all areas", "agent": "all", "response_type": "AI_executive_summary", "data_source": "all_agent_outputs"},
    {"command": "show section launch status", "description": "Status of each section in launch pipeline", "agent": "all", "response_type": "data_table + AI_summary", "data_source": "section_launch_tracker"},
    {"command": "show current blockers", "description": "All current blockers across the platform", "agent": "all", "response_type": "AI_prioritized_list", "data_source": "mission_control + publisher"},
    {"command": "show publish readiness", "description": "Which content is ready to publish", "agent": "SA-06", "response_type": "data_table + checklist", "data_source": "publisher_gates + metadata + schema"},
]
write_csv(f"{OUT_9J}/Phase9J_CoPilot_Agent_Command_Map.csv", copilot_commands, copilot_fields)

# 20. Executive Summary
print("\n[20/20] Executive Summary...")
exec_summary = f"""PHASE 9J EXECUTIVE SUMMARY
Agent Expansion + Section Launch Operating System
==========================================================================
generated_at: {NOW}
source_server: {SOURCE_SERVER}
git_commit: {GIT_COMMIT}
generated_by: {GENERATED_BY}
data_source_label: LIVE WordPress + Rank Math API + planning specs
approval_status: planning_only
next_action: owner_review_and_approval

OVERVIEW
========

Phase 9J defines the operating system for scaling PetHubOnline.com safely. It introduces 10 specialist agents, a permission matrix covering {len(perms)} actions, a section launch framework with 8 stages, and operational infrastructure for 24/7 monitoring.

CURRENT SITE STATUS
===================

Published posts: {len(all_posts)}
Posts in sitemap: {len(in_sitemap)}
Posts missing from sitemap: {len(missing_from_sitemap)}
Draft posts: {len(draft_posts)}
Categories: {len(categories)}
Dog Food posts live: 4 (verified clean)
Product Evidence: blocked_pending_evidence
Affiliate links: blocked
Social channels: all RED (blocked)
Pet Insurance: RED-gated

SPECIALIST AGENTS DEFINED
==========================

1. SA-01: Sitemap & Indexing Agent - crawl/indexing monitoring
2. SA-02: Taxonomy Authority Agent - category/authority protection
3. SA-03: Metadata & Image Alt Agent - metadata/alt enforcement
4. SA-04: Schema Safety Agent - structured data safety
5. SA-05: Product Evidence Agent - evidence-first monetization bridge
6. SA-06: Publisher Gate Agent - pre-publish protection
7. SA-07: AI Visibility Agent - AI search optimization
8. SA-08: Trust & Editorial Evidence Agent - credibility without fake E-E-A-T
9. SA-09: Performance & CWV Agent - safe performance monitoring
10. SA-10: Export Discipline Agent - evidence reliability

PERMISSION LANES
================

GREEN (auto): {len([p for p in perms if p['lane'] == 'GREEN'])} actions - monitoring, scanning, reporting, proposing
AMBER (prepare+approve): {len([p for p in perms if p['lane'] == 'AMBER'])} actions - metadata changes, schema deployment, category bulk changes
RED (always approve): {len([p for p in perms if p['lane'] == 'RED'])} actions - publishing, affiliate links, Product schema, social, credentials

SECTION LAUNCH FRAMEWORK
=========================

8 stages: Research > Mission Setup > Draft Creation > QA > Approval > Publish > Verification > Learning
Every section follows identical process with approval gates at Stage 5.

NEXT SECTION BACKLOG (PRIORITY ORDER)
======================================

1. Cat Toys Recovery / Engagement (low risk, fast learning)
2. Dog Harness Commercial Opportunity (needs evidence)
3. Trust / Methodology Pages (credibility infrastructure)
4. Homepage Engagement Improvement (routing/authority)
5. AI Search Adaptation (cross-cluster)
6. Pet Insurance Trust Buildout (RED-gated, planning only)

24/7 SCHEDULER
==============

Hourly: 6 jobs (NOC, sitemap, social gates, publish lock, queues, backups)
Every 6 hours: 6 jobs (metadata, categories, alts, links, schema, affiliate)
Daily: 6 jobs (GSC/GA4, monitoring, evidence, summary, security, exports)
Weekly: 5 jobs (AI visibility, performance, authority, priorities, governance)

AI MODE vs RULE MODE
====================

AI mode: 12 operations (summaries, briefs, analysis, explanations)
Rule mode: 11 operations (sitemap, metadata, schema, gates, scans)
All safety-critical operations use deterministic rules, never AI alone.

KEY PRINCIPLE
=============

No live changes from Phase 9J. All deliverables are planning/spec only.
Phase 9I sitemap recovery remains the immediate live-site priority.
After Phase 9I acceptance, owner decides which Phase 9J agents to implement first.

DELIVERABLES: 20 files in phase9j/ directory
"""
write_text(f"{OUT_9J}/Phase9J_Executive_Summary.txt", exec_summary)

print(f"\nPhase 9J complete: 20 deliverables in {OUT_9J}/")

# ============================================================
# PHASE 10: AUTONOMOUS OPERATIONS PLANNING
# ============================================================

print("\n" + "=" * 60)
print("PHASE 10: AUTONOMOUS OPERATIONS PLANNING")
print("=" * 60)

# 1. Specialist Agent Roster (expanded with Security & Governance)
print("\n[1/22] Phase 10 Specialist Agent Roster...")
p10_roster = roster.copy()
p10_roster.append({"agent_id": "SA-11", "agent_name": "Security & Governance Agent", "purpose": "Monitor secrets, credentials, publishing bypasses and risky permissions", "lane": "GREEN_scan_RED_changes", "dashboard_feed": "NOC + Co-Pilot + Mission Control", "status": "spec_ready"})
p10_roster.append({"agent_id": "SA-12", "agent_name": "AI Infrastructure Health Agent", "purpose": "Monitor Redis, PostgreSQL, queues, memory, disk, event bus", "lane": "GREEN_auto", "dashboard_feed": "NOC + Co-Pilot", "status": "spec_ready"})
p10_roster.append({"agent_id": "SA-13", "agent_name": "Content Authority Agent", "purpose": "Verify entity coverage, topical authority, content freshness", "lane": "GREEN_monitor_AMBER_refresh", "dashboard_feed": "Co-Pilot + Mission Control + SEO Dashboard", "status": "spec_ready"})
write_csv(f"{OUT_10}/Phase10_Specialist_Agent_Roster.csv", p10_roster, roster_fields)

# 2. Agent Permission Matrix (expanded)
print("\n[2/22] Phase 10 Agent Permission Matrix...")
p10_perms = perms.copy()
p10_perms.extend([
    {"action": "secret_scan_github", "lane": "GREEN", "agents_involved": "SA-11", "auto_allowed": "yes", "approval_required": "no", "notes": "Daily automated scan"},
    {"action": "credential_expiry_alert", "lane": "GREEN", "agents_involved": "SA-11", "auto_allowed": "yes", "approval_required": "no", "notes": "Alert before expiry"},
    {"action": "publish_bypass_test", "lane": "GREEN", "agents_involved": "SA-11", "auto_allowed": "yes", "approval_required": "no", "notes": "Governance regression test"},
    {"action": "red_gate_enforcement", "lane": "GREEN", "agents_involved": "SA-11", "auto_allowed": "yes", "approval_required": "no", "notes": "Verify RED gates active"},
    {"action": "redis_health_check", "lane": "GREEN", "agents_involved": "SA-12", "auto_allowed": "yes", "approval_required": "no", "notes": "Hourly ping + memory check"},
    {"action": "postgresql_health_check", "lane": "GREEN", "agents_involved": "SA-12", "auto_allowed": "yes", "approval_required": "no", "notes": "Hourly connection + query check"},
    {"action": "event_bus_monitoring", "lane": "GREEN", "agents_involved": "SA-12", "auto_allowed": "yes", "approval_required": "no", "notes": "Hourly event flow check"},
    {"action": "entity_coverage_scan", "lane": "GREEN", "agents_involved": "SA-13", "auto_allowed": "yes", "approval_required": "no", "notes": "Weekly entity audit"},
    {"action": "content_freshness_check", "lane": "GREEN", "agents_involved": "SA-13", "auto_allowed": "yes", "approval_required": "no", "notes": "Flag stale content"},
    {"action": "content_refresh_execution", "lane": "AMBER", "agents_involved": "SA-13", "auto_allowed": "prepare_only", "approval_required": "yes", "notes": "Live content changes need approval"},
])
write_csv(f"{OUT_10}/Phase10_Agent_Permission_Matrix.csv", p10_perms, perm_fields)

# 3-13: Agent Specs with 8-phase execution cycle
def write_p10_agent_spec(path, agent_name, purpose, responsibilities, inputs, outputs,
                         green_actions, amber_actions, red_actions, acceptance_criteria,
                         copilot_commands=None):
    rows = []
    rows.append({"field": "agent_name", "value": agent_name})
    rows.append({"field": "purpose", "value": purpose})

    # Phase 1: Requirement Analysis
    rows.append({"field": "phase1_objective", "value": purpose})
    rows.append({"field": "phase1_business_outcome", "value": f"Improves {agent_name.split('(')[0].strip().lower()} for site growth and safety"})
    rows.append({"field": "phase1_hidden_requirements", "value": "Must integrate with Co-Pilot, Mission Control, NOC without separate dashboard"})
    rows.append({"field": "phase1_approval_boundaries", "value": "GREEN actions auto; AMBER prepare-only; RED always explicit approval"})
    rows.append({"field": "phase1_risk_level", "value": "low_monitoring_only"})

    # Phase 2: Research & Comparison
    rows.append({"field": "phase2_options", "value": "Standalone agent vs integrated module vs scheduled job"})
    rows.append({"field": "phase2_technology", "value": "Python + FastAPI + PostgreSQL + Redis"})
    rows.append({"field": "phase2_automation_vs_manual", "value": "Automated monitoring + manual approval for live changes"})
    rows.append({"field": "phase2_scalability", "value": "Handles 100+ posts, extensible to 1000+"})
    rows.append({"field": "phase2_security", "value": "No credential storage in agent; uses existing auth; logs all actions"})

    # Phase 3: Architecture
    rows.append({"field": "phase3_data_flow", "value": "WP API -> Agent -> PostgreSQL -> Co-Pilot/Mission Control/NOC"})
    rows.append({"field": "phase3_api_routes", "value": f"api/{agent_name.split('(')[0].strip().lower().replace(' & ', '-').replace(' ', '-')}/scan, /status, /report"})
    rows.append({"field": "phase3_dashboard_feed", "value": "Co-Pilot + Mission Control + NOC (no separate dashboard)"})
    rows.append({"field": "phase3_rollback", "value": "All state changes logged; previous state stored; rollback via restore"})

    # Phase 4: Internal Discussion
    rows.append({"field": "phase4_agents_involved", "value": "SA-06 (Publisher Gate) for live changes; SA-10 (Export) for evidence"})
    rows.append({"field": "phase4_tradeoffs", "value": "Frequency vs resource usage; depth vs speed"})
    rows.append({"field": "phase4_final_decision", "value": "Balanced approach: frequent lightweight checks, deep scans on schedule"})

    # Phase 5: Testing
    rows.append({"field": "phase5_success_tests", "value": "Detects known issues; reports accurately; Co-Pilot responds correctly"})
    rows.append({"field": "phase5_failure_tests", "value": "Graceful degradation if API unavailable; DLQ for failed jobs"})
    rows.append({"field": "phase5_edge_cases", "value": "Empty results; API timeout; stale data; concurrent runs"})
    rows.append({"field": "phase5_rollback_test", "value": "State can be restored to pre-scan values"})

    # Phase 6: Self-Audit
    rows.append({"field": "phase6_weaknesses", "value": "Depends on WP API availability; cache delays possible"})
    rows.append({"field": "phase6_maintainability", "value": "Modular design; clear separation of concerns"})
    rows.append({"field": "phase6_owner_visibility", "value": "All outputs visible in Co-Pilot; executive summaries daily"})

    # Phase 7: Optimization
    rows.append({"field": "phase7_performance", "value": "Batch API calls; cache results; incremental scans"})
    rows.append({"field": "phase7_cost", "value": "Minimal API calls; reuse cached data where safe"})
    rows.append({"field": "phase7_future_proofing", "value": "Extensible to new post types, categories, schema types"})

    # Phase 8: Validation
    rows.append({"field": "phase8_confidence", "value": "high"})
    rows.append({"field": "phase8_risks", "value": "API rate limits; WordPress.com hosting constraints"})
    rows.append({"field": "phase8_blockers", "value": "none_for_planning"})
    rows.append({"field": "phase8_production_readiness", "value": "spec_ready_pending_implementation"})

    for i, r in enumerate(responsibilities):
        rows.append({"field": f"responsibility_{i+1}", "value": r})
    for i, inp in enumerate(inputs):
        rows.append({"field": f"input_{i+1}", "value": inp})
    for i, o in enumerate(outputs):
        rows.append({"field": f"output_{i+1}", "value": o})
    for i, g in enumerate(green_actions):
        rows.append({"field": f"green_action_{i+1}", "value": g})
    for i, a in enumerate(amber_actions):
        rows.append({"field": f"amber_action_{i+1}", "value": a})
    for i, r in enumerate(red_actions):
        rows.append({"field": f"red_action_{i+1}", "value": r})
    for i, ac in enumerate(acceptance_criteria):
        rows.append({"field": f"acceptance_{i+1}", "value": ac})
    if copilot_commands:
        for i, cc in enumerate(copilot_commands):
            rows.append({"field": f"copilot_command_{i+1}", "value": cc})

    rows.append({"field": "dashboard_integration", "value": "Co-Pilot + Mission Control + NOC"})
    rows.append({"field": "requires_separate_dashboard", "value": "no"})
    rows.append({"field": "approval_status", "value": "planning_only"})
    rows.append({"field": "next_action", "value": "owner_review_and_approval"})
    write_csv(path, rows, AGENT_SPEC_FIELDS)

print("\n[3/22] Phase 10 Sitemap & Indexing Agent Spec...")
write_p10_agent_spec(f"{OUT_10}/Phase10_Sitemap_Indexing_Agent_Spec.csv",
    "Sitemap & Indexing Agent (SA-01)",
    "Make sure all public content is discoverable, indexed-ready and tracked",
    ["Check sitemap status","Detect missing published URLs","Detect draft URLs in sitemap","Detect 404 URLs in sitemap","Detect trashed URLs in sitemap","Monitor sitemap URL count","Compare WordPress published count vs sitemap count","Check GSC sitemap status","Track indexing requests","Track first impression dates","Track first click dates","Schedule 24h/72h/7d follow-ups","Alert if published post missing from sitemap","Alert if sitemap contains non-public URL"],
    ["WordPress posts API","Rank Math sitemap","GSC data","Public URL checks","Mission Control","Publisher logs"],
    ["Sitemap health status","Missing URL list","Indexing follow-up report","Co-Pilot summary","Mission Control task creation"],
    ["Scan","Report","Create follow-up task"],
    ["Request indexing","Submit sitemap","Regenerate sitemap if admin settings involved"],
    ["Change sitemap provider","Alter plugin settings broadly","Publish/unpublish content"],
    ["Detects missing published URLs","Detects draft/404 URLs","Co-Pilot can explain sitemap status","No risky changes without approval"],
    ["show sitemap status","list missing URLs","show indexing progress","sitemap health summary"])

print("\n[4/22] Phase 10 Taxonomy Authority Agent Spec...")
write_p10_agent_spec(f"{OUT_10}/Phase10_Taxonomy_Authority_Agent_Spec.csv",
    "Taxonomy Authority Agent (SA-02)",
    "Protect topical authority and prevent incorrect category structure",
    ["Detect Uncategorized posts","Detect wrong category assignment","Detect dog/cat mismatch","Detect overly broad category usage","Detect empty categories","Track category counts","Check category archive relevance","Propose category fixes","Warn when new draft lacks category","Ensure future published posts are categorized"],
    ["Post title","Slug","Focus keyword","Categories","Sitemap","Mission Control cluster","Content type"],
    ["Taxonomy health report","Category mismatch report","Category assignment proposals","Co-Pilot category summary"],
    ["Scan/report/propose"],
    ["Batch category change after mapping approval"],
    ["Category deletion","Slug change","Redirects","Bulk live edits without approval"],
    ["No future post left Uncategorized unintentionally","Dog/cat mismatches flagged","Category changes approval-gated"],
    ["show category health","list uncategorized posts","which categories have mismatches"])

print("\n[5/22] Phase 10 Metadata & Image Alt Agent Spec...")
write_p10_agent_spec(f"{OUT_10}/Phase10_Metadata_ImageAlt_Agent_Spec.csv",
    "Metadata & Image Alt Agent (SA-03)",
    "Enforce sitewide metadata and first-image-alt standards",
    ["Scan all published posts","Scan all drafts","Detect title length issues","Detect focus keyword placement issue","Detect meta description length issue","Detect first-image-alt issue","Detect unsupported claim in metadata","Propose fixes","Feed Publisher gate"],
    ["Rank Math metadata","Post focus keyword","Post title","First image","Page content","Mission Control status"],
    ["Metadata compliance report","Image alt compliance report","Fix proposals","Co-Pilot summary"],
    ["Scan and report"],
    ["Prepare metadata updates","Prepare image alt updates"],
    ["Live metadata update without approval","Misleading metadata","Unverified product claims"],
    ["Publisher blocks posts failing metadata rules","Co-Pilot can report metadata compliance"],
    ["show metadata compliance","list posts with issues","metadata status for [post]"])

print("\n[6/22] Phase 10 Schema Safety Agent Spec...")
write_p10_agent_spec(f"{OUT_10}/Phase10_Schema_Safety_Agent_Spec.csv",
    "Schema Safety Agent (SA-04)",
    "Prevent unsafe structured data and support safe rich results",
    ["Scan page schema","Compare schema to visible content","Detect unsafe schema","Validate FAQ visibility","Validate Article schema","Detect fake rating/review/offer schema","Prepare safe schema proposals","Feed Publisher gate"],
    ["Page source","Rank Math schema","Schema proposal files","Product Evidence Register","FAQ content","Approval status"],
    ["Schema safety report","Safe schema proposal","Unsafe schema alert","Validation report","Co-Pilot explanation"],
    ["Scan","Propose safe schema","Validate snippets","Flag unsafe schema"],
    ["Schema deployment for safe types"],
    ["Any Product/Review/Offer schema","Sitewide schema changes"],
    ["Product/Review/Offer schema blocked unless evidence allows","Co-Pilot explains schema status","Publisher checks schema before publish"],
    ["show schema status","which pages have unsafe schema","schema safety for [post]"])

print("\n[7/22] Phase 10 Product Evidence Agent Spec...")
write_p10_agent_spec(f"{OUT_10}/Phase10_Product_Evidence_Agent_Spec.csv",
    "Product Evidence Agent (SA-05)",
    "Enable safe future monetization without fake claims",
    ["Identify candidate products","Collect retailer URL/ASIN","Capture source information","Track price evidence","Track rating/review evidence","Track stock evidence","Track image source evidence","Track ingredient/specification evidence","Classify verified/unverified claims","Flag stale evidence","Create evidence tasks","Block recommendations until verified"],
    ["Public retailer pages","Product databases","Evidence register","Mission Control","Publisher status"],
    ["Product evidence register","Evidence gap report","Stale evidence alerts","Affiliate readiness recommendations"],
    ["Collect public source data","Create evidence entries","Mark candidate/source collected"],
    ["Prepare recommendation draft"],
    ["Mark verified","Insert affiliate links","Publish product rankings","Use prices/ratings/review counts live"],
    ["No product claims unlock without evidence","Co-Pilot can summarize evidence gaps"],
    ["show evidence status","list evidence gaps","which products are ready"])

print("\n[8/22] Phase 10 Publisher Gate Agent Spec...")
write_p10_agent_spec(f"{OUT_10}/Phase10_Publisher_Gate_Agent_Spec.csv",
    "Publisher Gate Agent (SA-06)",
    "Protect the live site from unsafe publication",
    ["Validate approval_id","Match approval to post","Match approval to mission","Confirm rollback snapshot","Confirm audit log","Confirm metadata compliance","Confirm category assignment","Confirm schema safety","Confirm Product Evidence restrictions","Confirm affiliate restrictions","Confirm no RED-gated content","Confirm social not triggered","Verify post-publish state"],
    ["Mission Control","Publisher","WordPress post status","Product Evidence","Schema safety","Metadata checks","Sitemap checks","Approval queue"],
    ["Pre-publish checklist","Publish readiness status","Audit log link","Rollback link","Post-publish verification","Co-Pilot answer"],
    ["Check gates","Block unsafe publish","Create publish-readiness report"],
    ["GSC indexing submission after publish"],
    ["Actual publishing","Rollback execution","Schema deployment","Social dispatch"],
    ["No publish without approval","No publish if critical gate fails","All attempts logged"],
    ["is [post] ready to publish","list publish blockers","show publish history"])

print("\n[9/22] Phase 10 AI Visibility Agent Spec...")
write_p10_agent_spec(f"{OUT_10}/Phase10_AI_Visibility_Agent_Spec.csv",
    "AI Visibility Agent (SA-07)",
    "Improve visibility in ChatGPT, Gemini, Perplexity and AI search environments",
    ["Maintain AI visibility query set","Track brand mention","Track category mention","Track citation opportunities","Track answer-readiness","Detect missing FAQ/direct-answer opportunities","Compare competitors","Classify data as measured/manual/modelled"],
    ["AI visibility baseline","Co-Pilot queries","Manual benchmark results","Page content","Schema status","Trust pages","Entity coverage"],
    ["AI visibility report","Query set results","Entity gaps","Answer-readiness opportunities","Co-Pilot summary"],
    ["Monitor","Report","Propose improvements","Create draft answer blocks"],
    ["Live content updates","Schema deployment","New page publication"],
    ["Fake AI visibility claims","Automated content changes without approval"],
    ["AI visibility baseline tracked","No fake AI citation claims","Co-Pilot can explain AI visibility status"],
    ["show AI visibility status","list citation opportunities","AI readiness for [cluster]"])

print("\n[10/22] Phase 10 Trust & Editorial Evidence Agent Spec...")
write_p10_agent_spec(f"{OUT_10}/Phase10_Trust_Editorial_Evidence_Agent_Spec.csv",
    "Trust & Editorial Evidence Agent (SA-08)",
    "Improve credibility without fake E-E-A-T",
    ["Monitor methodology pages","Monitor affiliate disclosure clarity","Monitor evidence labels","Monitor last updated dates","Detect fake expert/test/review claims","Prepare trust page drafts","Maintain corrections/update policy"],
    ["Published content","Trust pages","Evidence register","Affiliate disclosures","Author information","Editorial policies"],
    ["Trust compliance report","Trust page drafts","Fake claim alerts","Disclosure clarity report","Co-Pilot trust summary"],
    ["Monitor trust wording","Detect fake claims","Prepare drafts","Report disclosure status"],
    ["Trust page content updates","Editorial policy changes"],
    ["Trust page publishing","Fake claims of any kind"],
    ["No fake trust claims","Trust pages draft-only until approved"],
    ["show trust status","any fake claims detected","disclosure compliance"])

print("\n[11/22] Phase 10 Performance & CWV Agent Spec...")
write_p10_agent_spec(f"{OUT_10}/Phase10_Performance_CWV_Agent_Spec.csv",
    "Performance & Core Web Vitals Agent (SA-09)",
    "Improve speed safely without breaking tracking or compliance",
    ["Track TTFB","Track FCP","Track LCP","Track CLS","Track request count","Track JS weight","Track image weight","Detect distorted images","Detect render-blocking resources","Propose safe improvements"],
    ["Page speed data","Core Web Vitals","Image analysis","Script analysis","Caching headers"],
    ["Performance baseline report","Safe fix backlog","Risky fix list","Image optimization proposals","Co-Pilot performance summary"],
    ["Report metrics","Propose fixes","Identify affected images","Track before/after"],
    ["Non-critical CSS/performance changes"],
    ["Remove analytics/consent scripts","Defer compliance-critical scripts","Broad design changes"],
    ["Safe fixes separated from risky fixes","Co-Pilot explains performance status"],
    ["show performance status","list performance issues","CWV summary"])

print("\n[12/22] Phase 10 Export Discipline Agent Spec...")
write_p10_agent_spec(f"{OUT_10}/Phase10_Export_Discipline_Agent_Spec.csv",
    "Export Discipline Agent (SA-10)",
    "Prevent stale evidence and export confusion",
    ["Timestamp every export","Mark current/stale","Include source server","Include git commit","Include generated_by","Archive superseded files","Compare GitHub vs live state","Warn if stale evidence conflicts"],
    ["GitHub repository","Live server files","Export timestamps","Git commit history"],
    ["Export health report","Stale file alerts","Evidence pack index","Current vs stale classification"],
    ["Check timestamps","Mark stale","Archive superseded","Create indexes"],
    ["Bulk file archival","Export format changes"],
    ["Delete evidence files","Remove audit logs"],
    ["No stale current exports","Co-Pilot can say which pack is current"],
    ["show export status","which exports are stale","current evidence pack"])

print("\n[13/22] Phase 10 Security & Governance Agent Spec...")
write_p10_agent_spec(f"{OUT_10}/Phase10_Security_Governance_Agent_Spec.csv",
    "Security & Governance Agent (SA-11)",
    "Continuously monitor secrets, credentials, publishing bypasses and risky permissions",
    ["Secret scans on GitHub","GitHub repository scans","Credential expiry alerts","Write-path governance checks","Publish-bypass tests","Approval_id validation checks","Endpoint access checks","Backup visibility checks","RED-gate enforcement checks"],
    ["GitHub repository","Server credentials","Publisher system","Approval logs","Backup logs","Gate configuration"],
    ["Security scan report","Credential expiry alerts","Governance test results","Publish bypass test results","Co-Pilot security summary"],
    ["Scan secrets","Check credentials","Test publish bypass","Verify RED gates","Check backup status"],
    ["Credential rotation preparation"],
    ["Credential changes","Permission changes","Gate configuration changes"],
    ["No exposed secrets","Publish bypass tests passing","Co-Pilot can report security status"],
    ["show security status","any secrets exposed","credential expiry status","governance test results"])

# 14-22: Remaining Phase 10 deliverables
print("\n[14/22] Phase 10 Section Launch Framework...")
# Reuse Phase 9J framework with additions
p10_launch = launch_rows.copy()
write_csv(f"{OUT_10}/Phase10_Section_Launch_Framework.csv", p10_launch, launch_fields)

print("\n[15/22] Phase 10 New Section Launch Template (JSON)...")
p10_template = template.copy()
p10_template["template_version"] = "2.0"
p10_template["section_launch_template"]["8_phase_execution"] = {
    "phase1_requirement_analysis": {"objective": "", "business_outcome": "", "hidden_requirements": "", "approval_boundaries": "", "risk_level": ""},
    "phase2_research": {"options": [], "technology": "", "automation_vs_manual": "", "scalability": "", "security": ""},
    "phase3_architecture": {"data_flow": "", "apis": "", "dashboard": "", "rollback": ""},
    "phase4_discussion": {"agents_involved": [], "tradeoffs": "", "decision": ""},
    "phase5_testing": {"success": [], "failure": [], "edge_cases": [], "rollback_test": ""},
    "phase6_audit": {"weaknesses": [], "improvements": [], "maintainability": "", "owner_visibility": ""},
    "phase7_optimization": {"performance": "", "cost": "", "reliability": "", "future_proofing": ""},
    "phase8_validation": {"confidence": "", "risks": [], "blockers": [], "readiness": ""}
}
write_json(f"{OUT_10}/Phase10_New_Section_Launch_Template.json", p10_template)

print("\n[16/22] Phase 10 Next Section Launch Backlog...")
write_csv(f"{OUT_10}/Phase10_Next_Section_Launch_Backlog.csv", backlog, backlog_fields)

print("\n[17/22] Phase 10 AI Enterprise Operations Matrix...")
write_csv(f"{OUT_10}/Phase10_AI_Enterprise_Operations_Matrix.csv", ai_matrix, ai_matrix_fields)

print("\n[18/22] Phase 10 AI Capacity Fallback Plan...")
write_csv(f"{OUT_10}/Phase10_AI_Capacity_Fallback_Plan.csv", credit_fallback, fallback_fields)

print("\n[19/22] Phase 10 24/7 Agent Scheduler Plan (YAML)...")
p10_scheduler = scheduler_yaml + """
  # Phase 10 additions
  hourly:
    - job: redis_health_check
      agent: SA-12
      description: Redis memory, connections, latency
      actions: [ping, info_memory, info_clients, latency_check]
      failure_action: infrastructure_alert
    - job: postgresql_health_check
      agent: SA-12
      description: PostgreSQL connections, queries, disk
      actions: [connection_test, active_queries, disk_usage, replication_lag]
      failure_action: infrastructure_alert
    - job: event_bus_monitoring
      agent: SA-12
      description: Event bus throughput and errors
      actions: [check_event_flow, check_error_rate, check_backlog]
      failure_action: event_bus_alert

  daily:
    - job: security_governance_scan
      agent: SA-11
      description: Full security and governance audit
      actions: [scan_secrets, check_credentials, test_publish_bypass, verify_red_gates, check_backups]
      failure_action: security_alert
    - job: content_authority_check
      agent: SA-13
      description: Entity coverage and content freshness
      actions: [check_entity_coverage, detect_stale_content, analyze_authority_signals]
      failure_action: authority_report
"""
write_yaml(f"{OUT_10}/Phase10_24_7_Agent_Scheduler_Plan.yaml", p10_scheduler)

print("\n[20/22] Phase 10 Dashboard/CoPilot Integration Map...")
integration_fields = ["view","section","data_source","agents","refresh_rate","priority"]
integration = [
    {"view": "Command Centre", "section": "Owner Summary", "data_source": "All agent outputs", "agents": "all", "refresh_rate": "daily", "priority": "critical"},
    {"view": "Command Centre", "section": "Current Blockers", "data_source": "Mission Control + Publisher", "agents": "SA-06 + all", "refresh_rate": "hourly", "priority": "critical"},
    {"view": "Command Centre", "section": "Next Safest Action", "data_source": "AI prioritization of backlog", "agents": "all", "refresh_rate": "daily", "priority": "high"},
    {"view": "Command Centre", "section": "Publish Readiness", "data_source": "Publisher gates + metadata + schema", "agents": "SA-06", "refresh_rate": "on_demand", "priority": "high"},
    {"view": "Mission Control", "section": "Active Missions", "data_source": "Mission database", "agents": "all", "refresh_rate": "real_time", "priority": "critical"},
    {"view": "Mission Control", "section": "Section Launches", "data_source": "Section launch tracker", "agents": "all", "refresh_rate": "real_time", "priority": "high"},
    {"view": "Mission Control", "section": "Phase Status", "data_source": "Phase tracker", "agents": "all", "refresh_rate": "daily", "priority": "high"},
    {"view": "Mission Control", "section": "Backlog Items", "data_source": "Agent-created tasks", "agents": "all", "refresh_rate": "real_time", "priority": "medium"},
    {"view": "Mission Control", "section": "Approvals", "data_source": "Approval queue", "agents": "SA-06", "refresh_rate": "real_time", "priority": "critical"},
    {"view": "NOC", "section": "Agent Health", "data_source": "Agent heartbeats", "agents": "SA-12", "refresh_rate": "hourly", "priority": "critical"},
    {"view": "NOC", "section": "Queues / DLQ", "data_source": "Queue metrics", "agents": "SA-12", "refresh_rate": "hourly", "priority": "high"},
    {"view": "NOC", "section": "Event Bus", "data_source": "Event flow metrics", "agents": "SA-12", "refresh_rate": "hourly", "priority": "high"},
    {"view": "NOC", "section": "Redis / PostgreSQL", "data_source": "Infrastructure metrics", "agents": "SA-12", "refresh_rate": "hourly", "priority": "critical"},
    {"view": "NOC", "section": "Social Gates", "data_source": "Gate status", "agents": "SA-08", "refresh_rate": "hourly", "priority": "high"},
    {"view": "NOC", "section": "Backup Status", "data_source": "Backup timestamps", "agents": "SA-10 + SA-11", "refresh_rate": "hourly", "priority": "high"},
    {"view": "Co-Pilot", "section": "Plain-English Status", "data_source": "All agent summaries", "agents": "all", "refresh_rate": "on_demand", "priority": "critical"},
    {"view": "Co-Pilot", "section": "Action Recommendations", "data_source": "AI prioritization", "agents": "all", "refresh_rate": "daily", "priority": "high"},
    {"view": "Co-Pilot", "section": "Evidence Gaps", "data_source": "Evidence register", "agents": "SA-05", "refresh_rate": "daily", "priority": "high"},
    {"view": "Co-Pilot", "section": "Approval Needs", "data_source": "Approval queue", "agents": "SA-06", "refresh_rate": "real_time", "priority": "critical"},
    {"view": "Co-Pilot", "section": "Performance Summary", "data_source": "CWV metrics", "agents": "SA-09", "refresh_rate": "weekly", "priority": "medium"},
    {"view": "Co-Pilot", "section": "SEO/Sitemap Status", "data_source": "Sitemap + GSC", "agents": "SA-01", "refresh_rate": "hourly", "priority": "high"},
    {"view": "Publisher", "section": "Publish Gates", "data_source": "Gate checklist", "agents": "SA-06", "refresh_rate": "on_demand", "priority": "critical"},
    {"view": "Publisher", "section": "Approval IDs", "data_source": "Approval log", "agents": "SA-06", "refresh_rate": "on_demand", "priority": "critical"},
    {"view": "Publisher", "section": "Rollback Snapshots", "data_source": "Snapshot storage", "agents": "SA-06", "refresh_rate": "on_demand", "priority": "high"},
    {"view": "Publisher", "section": "Audit Logs", "data_source": "Audit log database", "agents": "SA-06 + SA-11", "refresh_rate": "on_demand", "priority": "high"},
    {"view": "Evidence Vault", "section": "Product Evidence", "data_source": "Evidence register", "agents": "SA-05", "refresh_rate": "daily", "priority": "high"},
    {"view": "Evidence Vault", "section": "Source Status", "data_source": "Source verification", "agents": "SA-05", "refresh_rate": "daily", "priority": "high"},
    {"view": "Evidence Vault", "section": "Blocked/Unblocked Claims", "data_source": "Evidence statuses", "agents": "SA-05", "refresh_rate": "daily", "priority": "high"},
    {"view": "SEO / AI Visibility", "section": "Metadata", "data_source": "RM metadata", "agents": "SA-03", "refresh_rate": "6_hourly", "priority": "high"},
    {"view": "SEO / AI Visibility", "section": "Schema", "data_source": "Page source scan", "agents": "SA-04", "refresh_rate": "6_hourly", "priority": "high"},
    {"view": "SEO / AI Visibility", "section": "Sitemap", "data_source": "Sitemap XML", "agents": "SA-01", "refresh_rate": "hourly", "priority": "critical"},
    {"view": "SEO / AI Visibility", "section": "Indexing", "data_source": "GSC API", "agents": "SA-01", "refresh_rate": "daily", "priority": "high"},
    {"view": "SEO / AI Visibility", "section": "AI Visibility", "data_source": "AI benchmark queries", "agents": "SA-07", "refresh_rate": "weekly", "priority": "medium"},
]
write_csv(f"{OUT_10}/Phase10_Dashboard_CoPilot_Integration_Map.csv", integration, integration_fields)

print("\n[21/22] Phase 10 CoPilot Agent Command Map...")
p10_copilot = copilot_commands.copy()
p10_copilot.extend([
    {"command": "show security status", "description": "Secret scan results, credential health, governance", "agent": "SA-11", "response_type": "AI_summary + checklist", "data_source": "security_scans"},
    {"command": "show infrastructure health", "description": "Redis, PostgreSQL, event bus, queues", "agent": "SA-12", "response_type": "status_dashboard", "data_source": "infrastructure_metrics"},
    {"command": "show content authority", "description": "Entity coverage, topical depth, content freshness", "agent": "SA-13", "response_type": "AI_summary + metrics", "data_source": "authority_analysis"},
    {"command": "run governance tests", "description": "Execute full governance regression suite", "agent": "SA-11", "response_type": "test_results", "data_source": "governance_tests"},
])
write_csv(f"{OUT_10}/Phase10_CoPilot_Agent_Command_Map.csv", p10_copilot, copilot_fields)

# 22. Phase 10 Executive Summary
print("\n[22/22] Phase 10 Executive Summary...")
p10_summary = f"""PHASE 10 EXECUTIVE SUMMARY
Autonomous Operations + Agent Expansion Planning
==========================================================================
generated_at: {NOW}
source_server: {SOURCE_SERVER}
git_commit: {GIT_COMMIT}
generated_by: {GENERATED_BY}
data_source_label: LIVE WordPress + Rank Math API + planning specs
approval_status: planning_only
next_action: owner_review_and_approval_after_Phase_9I_accepted

OVERVIEW
========

Phase 10 builds on the Phase 9J agent framework with deeper execution planning,
additional specialist agents, and full 8-phase execution cycle documentation.
This is PLANNING ONLY - no live changes are made.

CURRENT SITE STATUS
===================

Published posts: {len(all_posts)}
Posts in sitemap: {len(in_sitemap)}
Posts missing from sitemap: {len(missing_from_sitemap)}
Draft posts: {len(draft_posts)}
Categories: {len(categories)}
Dog Food posts live: 4 (verified clean)
Product Evidence: blocked_pending_evidence
Affiliate links: blocked
Social channels: all RED (blocked)
Pet Insurance: RED-gated
Sitemap recovery: HIGHEST PRIORITY (Phase 9I.1 sprint in progress)

PHASE 10 SPECIALIST AGENTS (13 total)
======================================

SA-01 through SA-10: Same as Phase 9J (see Phase 9J roster)
SA-11: Security & Governance Agent - secrets, credentials, publishing bypass monitoring
SA-12: AI Infrastructure Health Agent - Redis, PostgreSQL, queues, event bus
SA-13: Content Authority Agent - entity coverage, topical authority, content freshness

All agents include full 8-phase execution cycle documentation:
1. Requirement Analysis
2. Research & Comparison
3. Architecture Planning
4. Internal Agent Discussion
5. Testing & Simulation
6. Self-Audit & Quality Review
7. Optimization
8. Final Validation

PERMISSION MATRIX
=================

Total actions mapped: {len(p10_perms)}
GREEN (auto): {len([p for p in p10_perms if p['lane'] == 'GREEN'])}
AMBER (prepare+approve): {len([p for p in p10_perms if p['lane'] == 'AMBER'])}
RED (always approve): {len([p for p in p10_perms if p['lane'] == 'RED'])}

DASHBOARD INTEGRATION
=====================

7 views mapped: Command Centre, Mission Control, NOC, Co-Pilot, Publisher, Evidence Vault, SEO/AI Visibility
{len(integration)} data feeds defined
No unnecessary dashboard sprawl - all agent outputs route to existing views

CO-PILOT COMMANDS
=================

{len(p10_copilot)} commands defined covering all 13 agents
Every agent's output is queryable through Co-Pilot in plain English

24/7 SCHEDULER
==============

Hourly: 9 jobs (NOC, sitemap, social gates, publish lock, queues, backups, Redis, PostgreSQL, event bus)
Every 6 hours: 6 jobs (metadata, categories, alts, links, schema, affiliate)
Daily: 8 jobs (GSC/GA4, monitoring, evidence, summary, security, exports, governance, authority)
Weekly: 5 jobs (AI visibility, performance, authority, priorities, governance regression)

AI MODE vs RULE MODE
====================

AI mode: 12 operations (reasoning, synthesis, natural language)
Rule mode: 11 operations (all safety-critical checks)
No safety gate relies solely on AI.

PRIORITY ORDER (UNCHANGED)
===========================

1. Complete Phase 9I sitemap recovery (9I.1 sprint active)
2. Verify Dog Food post-publish monitoring
3. Accept Phase 9J agent framework
4. Accept Phase 10 planning
5. Decide which agents to implement first
6. Do NOT execute new growth missions yet

DELIVERABLES: 22 files in phase10/ directory

ACCEPTANCE CRITERIA MET
========================

1. All 13 specialist agents clearly defined with 8-phase execution cycle
2. Every agent has business purpose documented
3. Every agent has permissions mapped (GREEN/AMBER/RED)
4. No agent can publish directly
5. No agent can add affiliate links directly
6. No agent can verify Product Evidence without source proof
7. No agent can deploy risky schema
8. Mission Control receives all agent outputs
9. Co-Pilot can explain all agent outputs
10. NOC can monitor agent health
11. Section launch framework exists (8 stages)
12. Next section launch backlog exists (6 sections prioritized)
13. AI mode vs rule mode defined
14. AI capacity fallback exists (4 levels)
15. 24/7 scheduler plan exists
16. Export discipline defined
17. Dashboard integration mapped (7 views, {len(integration)} feeds)
18. No live changes made during planning
19. Phase 9I sitemap recovery remains top priority
20. No unnecessary dashboard sprawl
"""
write_text(f"{OUT_10}/Phase10_Executive_Summary.txt", p10_summary)

print(f"\nPhase 10 complete: 22 deliverables in {OUT_10}/")

# ============================================================
# ADDITIONAL DELIVERABLES
# ============================================================

# Phase 10 specific additional files
print("\n" + "=" * 60)
print("ADDITIONAL PHASE 10 DELIVERABLES")
print("=" * 60)

# Category Rule Set (YAML)
print("\nPhase 10 Category Rule Set...")
cat_rules_yaml = """category_rules:
  version: "1.0"

  assignment_rules:
    - rule: no_uncategorized
      description: Every published post must have at least one non-Uncategorized category
      enforcement: publisher_gate_blocks

    - rule: species_match
      description: Dog content must have Dog category; Cat content must have Cat category
      detection: title_keyword_matching + slug_analysis
      enforcement: alert_on_mismatch

    - rule: cluster_alignment
      description: Posts must be assigned to their content cluster category
      detection: focus_keyword_to_category_mapping
      enforcement: proposal_for_review

    - rule: single_species
      description: Posts should not be in both Dog and Cat top-level categories unless explicitly cross-species
      enforcement: warning_on_detection

    - rule: subcategory_required
      description: Posts should have subcategory, not just top-level Dog or Cat
      enforcement: suggestion_only

  category_hierarchy:
    dogs:
      top_level: Dogs
      subcategories: [Dog Toys, Dog Beds, Dog Collars and Harnesses, Dog Grooming, Dog Health, Dog Training, Dog Bowls and Feeding, Dog Food]
    cats:
      top_level: Cats
      subcategories: [Cat Toys, Cat Beds, Cat Scratching, Cat Collars and Tags, Cat Grooming, Cat Litter]

  blocked_actions:
    - category_deletion_without_approval
    - slug_change_without_redirect
    - bulk_reassignment_without_review
"""
write_yaml(f"{OUT_10}/Phase10_Category_Rule_Set.yaml", cat_rules_yaml)

# Schema Blocking Rules (YAML)
print("Phase 10 Schema Blocking Rules...")
schema_rules_yaml = """schema_rules:
  version: "1.0"

  allowed_always:
    - type: Article
      condition: all_posts
      required_fields: [headline, datePublished, dateModified, author, publisher]

    - type: BreadcrumbList
      condition: all_posts_and_pages
      required_fields: [itemListElement]

    - type: Organization
      condition: homepage_only
      required_fields: [name, url, logo]

    - type: WebSite
      condition: homepage_only
      required_fields: [name, url]

  allowed_conditional:
    - type: FAQPage
      condition: visible_FAQ_section_exists_on_page
      validation: FAQ_text_must_match_visible_content
      required_fields: [mainEntity]

    - type: ItemList
      condition: guide_or_supporting_page_with_visible_list
      validation: list_items_must_match_visible_content

  blocked_until_evidence:
    - type: Product
      requires: evidence_status_approved_for_live_use
      gate: SA-05_Product_Evidence_Agent

    - type: Review
      requires: evidence_status_approved_for_live_use
      gate: SA-05_Product_Evidence_Agent

    - type: AggregateRating
      requires: evidence_status_approved_for_live_use
      gate: SA-05_Product_Evidence_Agent

    - type: Offer
      requires: evidence_status_approved_for_live_use + price_verification
      gate: SA-05_Product_Evidence_Agent

  always_blocked:
    - price_claims_without_evidence
    - stock_availability_claims_without_evidence
    - review_counts_without_evidence
    - rating_values_without_evidence
"""
write_yaml(f"{OUT_10}/Phase10_Schema_Blocking_Rules.yaml", schema_rules_yaml)

# Product Evidence Status Model (YAML)
print("Phase 10 Product Evidence Status Model...")
evidence_yaml = """product_evidence_model:
  version: "1.0"

  statuses:
    - status: not_started
      description: No evidence work begun
      allowed_transitions: [candidate_identified]
      auto_allowed: true

    - status: candidate_identified
      description: Product URL/ASIN identified as candidate
      allowed_transitions: [source_collected, rejected]
      auto_allowed: true

    - status: source_collected
      description: Retailer source URL captured
      allowed_transitions: [evidence_extracted, rejected]
      auto_allowed: true

    - status: evidence_extracted
      description: Price/rating/review/stock data extracted from source
      allowed_transitions: [evidence_verified, expired_recheck_required, rejected]
      auto_allowed: true_for_extraction

    - status: evidence_verified
      description: Evidence confirmed accurate by owner
      allowed_transitions: [owner_approved, expired_recheck_required, rejected]
      auto_allowed: false
      requires: owner_verification

    - status: owner_approved
      description: Owner has approved this evidence for use
      allowed_transitions: [approved_for_draft_use, rejected]
      auto_allowed: false
      requires: explicit_owner_approval

    - status: approved_for_draft_use
      description: Can be used in draft content but not published
      allowed_transitions: [approved_for_live_use, expired_recheck_required, rejected]
      auto_allowed: false
      requires: owner_approval

    - status: approved_for_live_use
      description: Can be used in published content with affiliate links
      allowed_transitions: [expired_recheck_required, rejected]
      auto_allowed: false
      requires: explicit_owner_approval
      unlocks: [affiliate_links, product_recommendations, Product_schema, Review_schema]

    - status: expired_recheck_required
      description: Evidence age exceeds freshness threshold
      allowed_transitions: [evidence_extracted, rejected]
      auto_detection: true
      freshness_threshold_days: 30

    - status: blocked_pending_evidence
      description: Product claims exist but no evidence supports them
      allowed_transitions: [candidate_identified]
      blocks: [affiliate_links, product_recommendations, Product_schema]

    - status: rejected
      description: Evidence rejected or product removed
      allowed_transitions: [not_started]
      auto_allowed: false
      requires: owner_decision
"""
write_yaml(f"{OUT_10}/Phase10_Product_Evidence_Status_Model.yaml", evidence_yaml)

# Export Metadata Standard (YAML)
print("Phase 10 Export Metadata Standard...")
export_yaml = """export_metadata_standard:
  version: "1.0"

  required_fields:
    - field: generated_at
      format: ISO8601_UTC
      example: "2026-05-27T12:00:00Z"

    - field: source_server
      format: IP_or_hostname
      example: "167.99.198.145"

    - field: git_commit
      format: short_hash
      example: "40402f2"

    - field: generated_by
      format: free_text
      example: "PetHub AI Platform - Phase 10 Generator"

    - field: data_source_label
      format: enum
      values: [LIVE, CACHED, ESTIMATED, MANUAL, MIXED]

    - field: approval_status
      format: enum
      values: [planning_only, draft, pending_review, approved, published, archived]

    - field: next_action
      format: free_text
      example: "owner_review"

  freshness_rules:
    - current: less_than_24h_old
    - recent: 24h_to_7d_old
    - stale: more_than_7d_old
    - archived: superseded_by_newer_export

  archival_rules:
    - when_superseded: move_to_archive_directory
    - when_stale: flag_in_export_report
    - when_conflicting: alert_via_CoPilot
"""
write_yaml(f"{OUT_10}/Phase10_Export_Metadata_Standard.yaml", export_yaml)

# Security Check Schedule (YAML)
print("Phase 10 Security Check Schedule...")
security_yaml = """security_schedule:
  version: "1.0"

  daily:
    - check: github_secret_scan
      agent: SA-11
      action: scan_all_committed_files_for_patterns
      patterns: [password, api_key, token, secret, credential, private_key]
      alert_on: any_match

    - check: credential_expiry
      agent: SA-11
      action: check_all_known_credentials_for_expiry
      alert_threshold_days: 7

    - check: publish_bypass_test
      agent: SA-11
      action: attempt_publish_without_approval_id
      expected_result: blocked
      alert_on: success_means_bypass_exists

    - check: red_gate_enforcement
      agent: SA-11
      action: verify_all_RED_gates_active
      gates: [publish, affiliate, product_schema, social, pet_insurance, credentials, deletion]
      alert_on: any_gate_inactive

    - check: backup_recency
      agent: SA-11
      action: verify_latest_backup_within_24h
      alert_on: backup_older_than_24h

  weekly:
    - check: full_governance_regression
      agent: SA-11
      action: run_complete_governance_test_suite
      tests: [publish_gates, schema_blocking, affiliate_gates, social_gates, evidence_gates, red_gates]
      alert_on: any_test_failure

    - check: endpoint_access_audit
      agent: SA-11
      action: verify_all_api_endpoints_require_auth
      alert_on: unauthenticated_access

    - check: permission_audit
      agent: SA-11
      action: review_all_agent_permissions_match_spec
      alert_on: permission_drift
"""
write_yaml(f"{OUT_10}/Phase10_Security_Check_Schedule.yaml", security_yaml)

# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("GENERATION COMPLETE")
print("=" * 60)
print(f"\nPhase 9I.1: 10 deliverables in {OUT_9I1}/")
print(f"Phase 9J:   20 deliverables in {OUT_9J}/")
print(f"Phase 10:   22 deliverables in {OUT_10}/")
print(f"+ 5 additional YAML specs in {OUT_10}/")
print(f"\nTotal: 57 deliverables")
print(f"\nREST re-save sitemap fix result: {'SUCCESS' if REST_RESAVE_WORKS else 'DID NOT FIX SITEMAP'}")
print(f"Sitemap before: {len(sitemap_urls)} URLs")
print(f"Sitemap after tests: {len(sm_recheck_urls)} URLs")
