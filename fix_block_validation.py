#!/usr/bin/env python3
"""Fix Gutenberg 'Block contains invalid or unexpected content' errors.

ROOT CAUSES:
1. Older posts (3836-4335) are classic HTML. Our scripts appended block-format
   content (<!-- wp:heading --> etc.) to them, creating a hybrid Gutenberg can't parse.
2. AI visibility script injected raw HTML divs into classic posts.
3. Internal linking / FAQ / cross-link scripts appended block-marked content to classic posts.

FIX STRATEGY:
- Posts that are primarily classic HTML: strip ALL block markers so Gutenberg
  treats the entire post as a single Classic block (no validation errors).
- Posts created with proper blocks (Phase 10B/10C): verify block structure is correct.
- Pages with specific mismatches: fix individually.
"""

import requests, json, re, html, csv, os, time
from datetime import datetime, timezone

WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"

s = requests.Session()
s.auth = (WP_USER, WP_PASS)
s.headers['Accept-Encoding'] = 'gzip, deflate'

NOW = datetime.now(timezone.utc).isoformat()
OUT = '/var/lib/freelancer/projects/40416335/phase10c_expansion'
os.makedirs(OUT, exist_ok=True)

# Phase 10B/10C post IDs (created with proper blocks)
BLOCK_NATIVE_IDS = {
    4406, 4407, 4408, 4409, 4410, 4415,  # Cat Toys spokes
    4411, 4412, 4413, 4414,               # Dog Harness posts
    4563, 4566, 4568, 4570,               # Dog Care spokes
    4571, 4573, 4574, 4576,               # Pet Care spokes
}

def fetch_all_content():
    """Fetch all posts and pages with raw content."""
    items = []
    for endpoint in ['posts', 'pages']:
        for status in ['publish', 'draft']:
            page_num = 1
            while True:
                r = s.get(f"{WP_BASE}/{endpoint}",
                    params={'per_page': 100, 'page': page_num, 'status': status, 'context': 'edit'})
                if r.status_code != 200:
                    break
                batch = r.json()
                if not batch:
                    break
                for item in batch:
                    item['_endpoint'] = endpoint
                items.extend(batch)
                page_num += 1
    return items

def is_primarily_classic(raw):
    """Determine if content is primarily classic HTML (not block-native)."""
    if not raw.strip():
        return False
    block_markers = re.findall(r'<!-- wp:\S+', raw)
    total_lines = len([l for l in raw.split('\n') if l.strip()])
    if total_lines == 0:
        return False
    block_ratio = len(block_markers) / total_lines
    return block_ratio < 0.3

def strip_block_markers(raw):
    """Remove all block comment markers, leaving clean HTML."""
    cleaned = re.sub(r'<!-- wp:\S+[^>]*-->\s*\n?', '', raw)
    cleaned = re.sub(r'<!-- /wp:\S+ -->\s*\n?', '', cleaned)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()

def validate_block_structure(raw):
    """Check block structure and return list of issues."""
    issues = []
    opens = re.findall(r'<!-- wp:(\S+?)[\s{]', raw)
    closes = re.findall(r'<!-- /wp:(\S+?) -->', raw)

    open_counts = {}
    for o in opens:
        open_counts[o] = open_counts.get(o, 0) + 1
    close_counts = {}
    for c in closes:
        close_counts[c] = close_counts.get(c, 0) + 1

    for bt in set(list(open_counts.keys()) + list(close_counts.keys())):
        if bt in ('freeform',):
            continue
        oc = open_counts.get(bt, 0)
        cc = close_counts.get(bt, 0)
        if oc != cc:
            issues.append(f'mismatch:{bt}(open={oc},close={cc})')

    # Check for content between blocks that isn't block-wrapped
    has_blocks = '<!-- wp:' in raw
    if has_blocks:
        last_close = raw.rfind('<!-- /wp:')
        if last_close > -1:
            end = raw.find('-->', last_close)
            if end > -1:
                trailing = raw[end+3:].strip()
                if trailing and not trailing.startswith('<!-- wp:'):
                    issues.append(f'trailing_raw({len(trailing)})')

    return issues

def fix_block_native_post(raw):
    """Fix a block-native post — ensure all content is properly block-wrapped."""
    lines = raw.split('\n')
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # If this is a raw <h2>/<h3> not inside a block, wrap it
        if re.match(r'^<h([2-6])[^>]*>', stripped) and (i == 0 or '<!-- wp:heading' not in lines[max(0,i-1)]):
            level_match = re.match(r'^<h(\d)', stripped)
            level = level_match.group(1) if level_match else '2'
            fixed_lines.append(f'<!-- wp:heading {{"level":{level}}} -->')
            fixed_lines.append(line)
            fixed_lines.append(f'<!-- /wp:heading -->')
            i += 1
            continue

        # If this is a raw <p> not inside a block, wrap it
        if re.match(r'^<p[ >]', stripped) and (i == 0 or not any(
            lines[max(0,j)].strip().startswith('<!-- wp:paragraph')
            for j in range(max(0,i-2), i)
        )):
            fixed_lines.append('<!-- wp:paragraph -->')
            fixed_lines.append(line)
            fixed_lines.append('<!-- /wp:paragraph -->')
            i += 1
            continue

        # If this is a raw <ul>/<ol> not inside a block, wrap it
        if re.match(r'^<[uo]l', stripped) and (i == 0 or '<!-- wp:list' not in lines[max(0,i-1)]):
            is_ordered = stripped.startswith('<ol')
            fixed_lines.append(f'<!-- wp:list{" {\"ordered\":true}" if is_ordered else ""} -->')
            # Collect until closing tag
            fixed_lines.append(line)
            while i + 1 < len(lines):
                i += 1
                fixed_lines.append(lines[i])
                if re.match(r'^</[uo]l>', lines[i].strip()):
                    break
            fixed_lines.append('<!-- /wp:list -->')
            i += 1
            continue

        # If this is a raw <hr /> not inside a block
        if stripped in ('<hr />', '<hr/>', '<hr>') and (i == 0 or '<!-- wp:separator' not in lines[max(0,i-1)]):
            fixed_lines.append('<!-- wp:separator -->')
            fixed_lines.append('<hr class="wp-block-separator has-alpha-channel-opacity"/>')
            fixed_lines.append('<!-- /wp:separator -->')
            i += 1
            continue

        fixed_lines.append(line)
        i += 1

    return '\n'.join(fixed_lines)


print("=" * 70)
print("GUTENBERG BLOCK VALIDATION FIX")
print(f"Started: {NOW}")
print("=" * 70)

# Fetch all content
print("\nFetching all content...")
all_items = fetch_all_content()
print(f"Total items: {len(all_items)}")

# Backup before fixing
backups = {}
results = []
fixed_count = 0
skipped_count = 0

for item in all_items:
    pid = item['id']
    title = html.unescape(item['title'].get('raw', item['title'].get('rendered', '')))
    raw = item['content'].get('raw', '')
    endpoint = item['_endpoint']
    status = item['status']

    if not raw.strip():
        continue

    # Determine content type
    is_classic = is_primarily_classic(raw)
    is_block_native = pid in BLOCK_NATIVE_IDS

    # Check for issues
    block_issues = validate_block_structure(raw)
    has_issues = bool(block_issues) or (is_classic and '<!-- wp:' in raw)

    if not has_issues:
        continue

    # Backup
    backups[pid] = {'raw': raw, 'title': title, 'endpoint': endpoint}

    fix_type = None
    new_content = None

    if is_classic and not is_block_native:
        # CLASSIC POSTS: Strip all block markers to make them purely classic
        new_content = strip_block_markers(raw)
        fix_type = 'stripped_to_classic'
    elif is_block_native:
        # BLOCK-NATIVE POSTS: Fix block structure
        new_content = fix_block_native_post(raw)
        remaining = validate_block_structure(new_content)
        fix_type = 'block_structure_fixed' if not remaining else f'partial_fix({",".join(remaining)})'
    else:
        # Mixed/ambiguous — check which approach is cleaner
        stripped = strip_block_markers(raw)
        fixed_blocks = fix_block_native_post(raw)
        block_issues_after = validate_block_structure(fixed_blocks)
        if not block_issues_after:
            new_content = fixed_blocks
            fix_type = 'block_structure_fixed'
        else:
            new_content = stripped
            fix_type = 'stripped_to_classic'

    if new_content and new_content != raw:
        # Apply fix
        r = s.post(f"{WP_BASE}/{endpoint}/{pid}", json={"content": new_content})
        if r.status_code == 200:
            fixed_count += 1
            print(f"  FIXED {endpoint} {pid}: {title[:50]} [{fix_type}]")
        else:
            print(f"  FAILED {endpoint} {pid}: {r.status_code}")
            fix_type = f'update_failed_{r.status_code}'

        results.append({
            'id': pid, 'type': endpoint, 'title': title[:60], 'status': status,
            'fix_type': fix_type, 'had_issues': '; '.join(block_issues) if block_issues else 'hybrid_content',
            'content_was_classic': is_classic, 'is_block_native': is_block_native
        })
    else:
        skipped_count += 1

# Save backups
backup_path = os.path.join(OUT, 'block_fix_backups.json')
backup_data = {str(k): {'title': v['title'], 'endpoint': v['endpoint'], 'raw_length': len(v['raw'])} for k, v in backups.items()}
with open(backup_path, 'w') as f:
    json.dump(backup_data, f, indent=2)

# Save full raw backups separately (large file)
full_backup_path = os.path.join(OUT, 'block_fix_full_backups.json')
full_data = {str(k): v['raw'] for k, v in backups.items()}
with open(full_backup_path, 'w') as f:
    json.dump(full_data, f)

# Save results CSV
csv_path = os.path.join(OUT, 'Block_Validation_Fix_Log.csv')
with open(csv_path, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['id','type','title','status','fix_type','had_issues','content_was_classic','is_block_native'])
    w.writeheader()
    w.writerows(results)

print(f"\n{'='*70}")
print(f"FIX SUMMARY")
print(f"{'='*70}")
print(f"Total items scanned: {len(all_items)}")
print(f"Items fixed: {fixed_count}")
print(f"Items skipped (no change needed): {skipped_count}")
print(f"Backups saved: {backup_path}")
print(f"Fix log: {csv_path}")

# Categorize fixes
classic_fixes = sum(1 for r in results if r['fix_type'] == 'stripped_to_classic')
block_fixes = sum(1 for r in results if 'block_structure' in r['fix_type'])
print(f"\nFix breakdown:")
print(f"  Stripped to clean classic: {classic_fixes}")
print(f"  Block structure repaired: {block_fixes}")
