#!/usr/bin/env python3
"""URGENT: Repair Gutenberg migration — fix Group blocks with raw HTML.

ROOT CAUSE:
The HTMLToBlocks converter wrapped ALL <div> elements in Group blocks.
Group blocks require inner content to also be valid inner blocks.
Raw HTML inside a Group's wrapper div is opaque to the editor — content
appears hidden/missing in the Gutenberg editing view.

REPAIR STRATEGY:
1. Pages with block_fix backup: Restore original proper Gutenberg content
2. Posts with affiliate/info-box Group blocks: Convert to HTML blocks
3. Pages without backup: Restore from WordPress revisions
"""

import requests, json, re, html as html_mod, csv, os, time
from datetime import datetime, timezone

WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
s = requests.Session()
s.auth = ('jasonsarah2026', 'yUmn Rngy EFE1 r7jr kjtm jmqx')
s.headers['Accept-Encoding'] = 'gzip, deflate'

OUT = '/var/lib/freelancer/projects/40416335/phase10d'
NOW = datetime.now(timezone.utc).isoformat()

# Load backups
with open('/var/lib/freelancer/projects/40416335/phase10c_expansion/block_fix_full_backups.json') as f:
    BLOCK_FIX_BACKUPS = json.load(f)

print("=" * 70)
print("GUTENBERG MIGRATION REPAIR")
print(f"Started: {NOW}")
print("=" * 70)

# =====================================================================
# STEP 1: Restore pages from block_fix backup (proper Gutenberg blocks)
# =====================================================================
print("\n--- STEP 1: Restoring pages from block_fix backup ---")

# Pages that have proper block structure in the backup
PAGES_WITH_BACKUP = [
    4, 37, 38, 39,
    1041, 1141, 1144, 1146, 1149,
    1951, 1956, 1960,
    3107, 3109, 3111, 3113, 3115,
]

restored_pages = 0
page_results = []

for pid in PAGES_WITH_BACKUP:
    pid_str = str(pid)
    if pid_str not in BLOCK_FIX_BACKUPS:
        print(f"  SKIP page {pid}: not in backup")
        page_results.append({'id': pid, 'type': 'pages', 'action': 'skip_no_backup'})
        continue

    backup_content = BLOCK_FIX_BACKUPS[pid_str]

    # Verify backup has proper blocks
    if '<!-- wp:' not in backup_content:
        print(f"  SKIP page {pid}: backup has no block markers")
        page_results.append({'id': pid, 'type': 'pages', 'action': 'skip_no_blocks_in_backup'})
        continue

    r = s.post(f"{WP_BASE}/pages/{pid}", json={"content": backup_content})
    if r.status_code == 200:
        restored_pages += 1
        title = html_mod.unescape(r.json()['title'].get('raw', ''))[:50]
        print(f"  RESTORED page {pid}: {title}")
        page_results.append({'id': pid, 'type': 'pages', 'action': 'restored_from_backup', 'title': title})
    else:
        print(f"  FAIL page {pid}: HTTP {r.status_code}")
        page_results.append({'id': pid, 'type': 'pages', 'action': f'restore_failed_{r.status_code}'})

    time.sleep(0.3)

print(f"\nPages restored from backup: {restored_pages}")


# =====================================================================
# STEP 2: Restore pages 63 and 1176 from WordPress revisions
# =====================================================================
print("\n--- STEP 2: Restoring pages 63 and 1176 from revisions ---")

PAGES_NEED_REVISIONS = [63, 1176]

for pid in PAGES_NEED_REVISIONS:
    # Fetch revisions for this page
    r = s.get(f"{WP_BASE}/pages/{pid}/revisions", params={'per_page': 50, 'context': 'edit'})
    if r.status_code != 200:
        print(f"  FAIL page {pid}: cannot fetch revisions ({r.status_code})")
        page_results.append({'id': pid, 'type': 'pages', 'action': 'revisions_failed'})
        continue

    revisions = r.json()
    print(f"  Page {pid}: {len(revisions)} revisions found")

    # Find a revision with proper block content (cover/columns blocks)
    best_revision = None
    for rev in revisions:
        raw = rev.get('content', {}).get('raw', '')
        if not raw:
            continue
        has_cover = '<!-- wp:cover' in raw
        has_columns = '<!-- wp:columns' in raw
        has_group_raw = bool(re.search(r'<!-- wp:group -->\s*<div class="wp-block-group"><div class="wp-block-', raw))

        if (has_cover or has_columns) and not has_group_raw:
            best_revision = rev
            print(f"    Found good revision {rev['id']} (date: {rev.get('date', 'unknown')})")
            break

    if best_revision:
        restore_content = best_revision['content']['raw']
        r = s.post(f"{WP_BASE}/pages/{pid}", json={"content": restore_content})
        if r.status_code == 200:
            restored_pages += 1
            title = html_mod.unescape(r.json()['title'].get('raw', ''))[:50]
            print(f"  RESTORED page {pid}: {title} (from revision {best_revision['id']})")
            page_results.append({'id': pid, 'type': 'pages', 'action': 'restored_from_revision', 'title': title})
        else:
            print(f"  FAIL page {pid}: HTTP {r.status_code}")
            page_results.append({'id': pid, 'type': 'pages', 'action': f'revision_restore_failed_{r.status_code}'})
    else:
        # No good revision found — convert Group blocks intelligently
        print(f"  No clean revision for page {pid}, applying block-type detection fix")

        r = s.get(f"{WP_BASE}/pages/{pid}", params={'context': 'edit'})
        raw = r.json()['content']['raw']

        # Replace Group blocks wrapping known Gutenberg-class divs
        def fix_group_block(match):
            inner_html = match.group(1).strip()

            # Detect the actual block type from CSS classes
            if 'wp-block-cover' in inner_html:
                return f'<!-- wp:cover -->\n{inner_html}\n<!-- /wp:cover -->'
            elif 'wp-block-columns' in inner_html:
                return f'<!-- wp:columns -->\n{inner_html}\n<!-- /wp:columns -->'
            elif 'wp-block-column' in inner_html:
                return f'<!-- wp:column -->\n{inner_html}\n<!-- /wp:column -->'
            elif 'wp-block-group' in inner_html:
                return f'<!-- wp:group -->\n{inner_html}\n<!-- /wp:group -->'
            elif 'affiliate-disclosure' in inner_html or ('style=' in inner_html and '<strong>' in inner_html):
                return f'<!-- wp:html -->\n{inner_html}\n<!-- /wp:html -->'
            else:
                return f'<!-- wp:html -->\n{inner_html}\n<!-- /wp:html -->'

        fixed = re.sub(
            r'<!-- wp:group -->\s*<div class="wp-block-group">(.*?)</div>\s*<!-- /wp:group -->',
            fix_group_block,
            raw,
            flags=re.DOTALL
        )

        r2 = s.post(f"{WP_BASE}/pages/{pid}", json={"content": fixed})
        if r2.status_code == 200:
            restored_pages += 1
            title = html_mod.unescape(r2.json()['title'].get('raw', ''))[:50]
            print(f"  FIXED page {pid}: {title} (block-type detection)")
            page_results.append({'id': pid, 'type': 'pages', 'action': 'fixed_block_types', 'title': title})
        else:
            print(f"  FAIL page {pid}: HTTP {r2.status_code}")
            page_results.append({'id': pid, 'type': 'pages', 'action': f'fix_failed_{r2.status_code}'})

    time.sleep(0.3)


# =====================================================================
# STEP 3: Fix posts — convert affiliate/info-box Group blocks to HTML blocks
# =====================================================================
print("\n--- STEP 3: Fixing posts — Group→HTML for affiliate/info boxes ---")

# Fetch all posts
all_posts = []
for status in ['publish', 'draft']:
    page_num = 1
    while True:
        r = s.get(f"{WP_BASE}/posts",
            params={'per_page': 100, 'page': page_num, 'status': status, 'context': 'edit'})
        if r.status_code != 200:
            break
        batch = r.json()
        if not batch:
            break
        all_posts.extend(batch)
        page_num += 1

fixed_posts = 0
post_results = []

# Pattern: Group block wrapping a styled div (affiliate-box or info-box)
GROUP_RAW_PATTERN = re.compile(
    r'<!-- wp:group -->\s*<div class="wp-block-group">(<div[^>]*(?:affiliate-disclosure|style=)[^>]*>.*?</div>)</div>\s*<!-- /wp:group -->',
    re.DOTALL
)

for post in all_posts:
    pid = post['id']
    raw = post['content'].get('raw', '')
    title = html_mod.unescape(post['title'].get('raw', post['title'].get('rendered', '')))[:50]

    if not raw.strip():
        continue

    # Check for problematic Group blocks
    matches = GROUP_RAW_PATTERN.findall(raw)
    if not matches:
        continue

    # Replace Group wrappers with HTML blocks
    new_content = GROUP_RAW_PATTERN.sub(
        lambda m: f'<!-- wp:html -->\n{m.group(1)}\n<!-- /wp:html -->',
        raw
    )

    if new_content == raw:
        continue

    r = s.post(f"{WP_BASE}/posts/{pid}", json={"content": new_content})
    if r.status_code == 200:
        fixed_posts += 1
        print(f"  FIXED post {pid}: {title} ({len(matches)} Group→HTML)")
        post_results.append({'id': pid, 'type': 'posts', 'action': 'group_to_html', 'fixes': len(matches), 'title': title})
    else:
        print(f"  FAIL post {pid}: HTTP {r.status_code}")
        post_results.append({'id': pid, 'type': 'posts', 'action': f'fix_failed_{r.status_code}', 'title': title})

    time.sleep(0.2)

print(f"\nPosts fixed: {fixed_posts}")


# =====================================================================
# STEP 4: Verify — check all items for remaining Group blocks with raw HTML
# =====================================================================
print("\n--- STEP 4: Full verification scan ---")

all_items = list(all_posts)
for status in ['publish', 'draft']:
    page_num = 1
    while True:
        r = s.get(f"{WP_BASE}/pages",
            params={'per_page': 100, 'page': page_num, 'status': status, 'context': 'edit'})
        if r.status_code != 200:
            break
        batch = r.json()
        if not batch:
            break
        all_items.extend([{**p, '_endpoint': 'pages'} for p in batch])
        page_num += 1

remaining_issues = []
clean_items = 0

for item in all_items:
    raw = item.get('content', {}).get('raw', '')
    if not raw.strip():
        continue

    endpoint = item.get('_endpoint', 'posts')
    pid = item['id']

    # Check for Group blocks with raw HTML inside (no inner blocks)
    group_sections = re.findall(
        r'<!-- wp:group -->\s*<div class="wp-block-group">(.*?)</div>\s*<!-- /wp:group -->',
        raw, re.DOTALL
    )

    bad_groups = 0
    for gs in group_sections:
        if '<!-- wp:' not in gs.strip():
            bad_groups += 1

    if bad_groups > 0:
        title = html_mod.unescape(item.get('title', {}).get('raw', item.get('title', {}).get('rendered', '')))[:50]
        remaining_issues.append(f"{endpoint}/{pid}: {title} ({bad_groups} bad Group blocks)")
    else:
        clean_items += 1

print(f"Clean items: {clean_items}")
print(f"Items with remaining issues: {len(remaining_issues)}")
if remaining_issues:
    for issue in remaining_issues:
        print(f"  REMAINING: {issue}")


# =====================================================================
# Save repair log
# =====================================================================
csv_path = os.path.join(OUT, 'Gutenberg_Repair_Log.csv')
all_results = page_results + post_results
fieldnames = ['id', 'type', 'action', 'title', 'fixes']
with open(csv_path, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    w.writeheader()
    w.writerows(all_results)

print(f"\n{'='*70}")
print("REPAIR SUMMARY")
print(f"{'='*70}")
print(f"Pages restored from backup: {restored_pages}")
print(f"Posts fixed (Group→HTML): {fixed_posts}")
print(f"Total repairs: {restored_pages + fixed_posts}")
print(f"Remaining issues: {len(remaining_issues)}")
print(f"Repair log: {csv_path}")
