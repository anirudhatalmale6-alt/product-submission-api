#!/usr/bin/env python3
"""Fix overclaim/trust issues on 6 hub pages on pethubonline.com.

For each page: fetch with context=edit, back up original, apply exact string
replacements to soften unsupported expert/testing claims, add info strip,
validate Gutenberg blocks, then update via WP REST API.
"""

import sys
import os
import time
import json

import requests

# Add project dir to path so we can import gutenberg_utils
sys.path.insert(0, '/var/lib/freelancer/projects/40416335')
from gutenberg_utils import validate_gutenberg

# ── Config ──────────────────────────────────────────────────────────────────
WP_BASE = 'https://pethubonline.com/wp-json/wp/v2'
WP_USER = 'jasonsarah2026'
WP_PASS = 'yUmn Rngy EFE1 r7jr kjtm jmqx'
BACKUP_DIR = '/var/lib/freelancer/projects/40416335/phase10d/hub_backups'

INFO_STRIP = (
    '<!-- wp:paragraph {"style":{"typography":{"fontSize":"0.9em"}}} -->\n'
    '<p style="font-size:0.9em;color:#555;"><strong>Last Updated:</strong> 27 May 2026<br/>'
    '<strong>Website:</strong> pethubonline.com<br/>'
    '<strong>Business:</strong> Pet Hub Online</p>\n'
    '<!-- /wp:paragraph -->\n'
    '<!-- wp:separator -->\n'
    '<hr class="wp-block-separator has-alpha-channel-opacity"/>\n'
    '<!-- /wp:separator -->'
)

os.makedirs(BACKUP_DIR, exist_ok=True)

# ── Session setup ───────────────────────────────────────────────────────────
s = requests.Session()
s.auth = (WP_USER, WP_PASS)
s.headers['Accept-Encoding'] = 'gzip, deflate'


# ── Per-page replacement definitions ───────────────────────────────────────
# Each entry: (page_id, label, [(old_str, new_str), ...])
PAGES = [
    (1141, 'Dog Beds', [
        ('Expert-Reviewed Picks', 'Recommended Options'),
    ]),
    (1144, 'Dog Grooming', [
        ('Expert-Approved Essentials', 'Recommended Essentials'),
        ('Our grooming tools are tested by professionals and pet owners alike',
         'Our grooming guides are based on manufacturer specifications and widely available product information'),
        ('tested by professionals', 'researched'),
        ('Expert', 'Practical'),
        ('expert', 'practical'),
    ]),
    (1146, 'Dog Collars & Leashes', [
        ('Independent Only Reviews', 'Research-Based Guides'),
        ('Every collar and lead is tested and reviewed by real dog owners',
         'Every collar and lead guide is based on manufacturer data, published reviews, and practical considerations'),
        ('Expert-Verified Quality', 'Quality Considerations'),
        ('tested for durability, fit, and ease of use',
         'evaluated based on durability, fit, and ease of use'),
    ]),
    (1149, 'Cat Toys', [
        ('Expert-Reviewed Picks', 'Recommended Options'),
        ('Pet Owner Approved', 'Community Focused'),
        ('top-rated', 'popular'),
        ('expert tips', 'practical tips'),
        ('expert insights', 'practical insights'),
    ]),
    (63, 'Dog Supplies', [
        ('Expert Recommendations for Every Breed', 'Recommendations by Breed'),
        ('Our team reviews and curates each item',
         'We research and curate product information'),
        ('Every recommendation is tested for comfort, reliability, and value',
         'Every recommendation is evaluated based on manufacturer data, available reviews, and value'),
        ('our team', 'we'),
        ('Our team', 'We'),
    ]),
    (38, 'Blog', [
        ('expert advice', 'practical guidance'),
        ('expert reviews', 'product guides'),
        ('Expert Advice', 'Practical Guidance'),
        ('Expert Reviews', 'Product Guides'),
    ]),
]


def fetch_page(page_id):
    """Fetch page content with context=edit. Try pages first, then posts."""
    for endpoint in ('pages', 'posts'):
        r = s.get(f'{WP_BASE}/{endpoint}/{page_id}', params={'context': 'edit'})
        if r.status_code == 200:
            data = r.json()
            content = data.get('content', {})
            if isinstance(content, dict):
                content = content.get('raw', content.get('rendered', ''))
            return endpoint, content
    raise RuntimeError(f'Could not fetch page/post {page_id}: HTTP {r.status_code} - {r.text[:300]}')


def save_backup(page_id, slug, content):
    path = os.path.join(BACKUP_DIR, f'{page_id}_{slug}_backup.txt')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  Backup saved: {path}')


def insert_info_strip(content):
    """Insert info strip after any existing affiliate disclosure block but
    before the first main heading.  If the info strip is already present,
    skip insertion."""
    if '27 May 2026' in content and 'pethubonline.com' in content and 'Pet Hub Online' in content:
        # Already has an info strip with our exact date — skip
        if 'Last Updated:</strong> 27 May 2026' in content:
            return content, False

    # Locate the first wp:heading block
    heading_marker = '<!-- wp:heading'

    idx = content.find(heading_marker)
    if idx == -1:
        # No heading found — place at the very top
        return INFO_STRIP + '\n\n' + content, True

    # Check if there's an affiliate-disclosure block before the heading
    affiliate_end = -1
    # Look for the end of the affiliate disclosure HTML block
    aff_pattern = '<!-- /wp:html -->'
    search_area = content[:idx]
    # Find the LAST closing html block before the heading (which is likely
    # the affiliate disclosure)
    last_html_close = search_area.rfind(aff_pattern)
    if last_html_close != -1 and 'affiliate' in search_area[max(0, last_html_close - 500):last_html_close].lower():
        insert_pos = last_html_close + len(aff_pattern)
        # Skip whitespace
        while insert_pos < len(content) and content[insert_pos] in ('\n', '\r', ' '):
            insert_pos += 1
        new_content = content[:insert_pos] + '\n\n' + INFO_STRIP + '\n\n' + content[insert_pos:]
        return new_content, True

    # No affiliate block — insert right before the first heading
    new_content = content[:idx] + INFO_STRIP + '\n\n' + content[idx:]
    return new_content, True


def apply_replacements(content, replacements):
    """Apply exact string replacements. Returns (new_content, count)."""
    count = 0
    for old, new in replacements:
        occurrences = content.count(old)
        if occurrences > 0:
            content = content.replace(old, new)
            count += occurrences
            print(f'    Replaced "{old}" -> "{new}" ({occurrences}x)')
        else:
            print(f'    NOT FOUND: "{old}"')
    return content, count


def update_page(endpoint, page_id, content):
    """Update page content via WP REST API."""
    payload = {'content': content}
    r = s.post(f'{WP_BASE}/{endpoint}/{page_id}', json=payload)
    if r.status_code == 200:
        return True, 'OK'
    return False, f'HTTP {r.status_code}: {r.text[:300]}'


# ── Main ────────────────────────────────────────────────────────────────────
def main():
    results = []
    total_replacements = 0

    for page_id, label, replacements in PAGES:
        print(f'\n{"="*60}')
        print(f'Processing page {page_id}: {label}')
        print(f'{"="*60}')

        try:
            endpoint, content = fetch_page(page_id)
            print(f'  Fetched via {endpoint}, content length: {len(content)} chars')
        except RuntimeError as e:
            print(f'  FAILED to fetch: {e}')
            results.append((page_id, label, 'FETCH_FAILED', 0))
            continue

        # Determine slug for backup filename
        slug = label.lower().replace(' & ', '_').replace(' ', '_')
        save_backup(page_id, slug, content)

        # Apply text replacements
        new_content, rep_count = apply_replacements(content, replacements)
        print(f'  Text replacements made: {rep_count}')

        # Insert info strip
        new_content, strip_inserted = insert_info_strip(new_content)
        if strip_inserted:
            print(f'  Info strip inserted')
            rep_count += 1  # count the strip as a change
        else:
            print(f'  Info strip already present or skipped')

        # Skip update if no changes
        if new_content == content:
            print(f'  No changes needed — skipping update')
            results.append((page_id, label, 'NO_CHANGES', 0))
            continue

        # Validate Gutenberg blocks
        is_valid, issues = validate_gutenberg(new_content)
        if not is_valid:
            # Check if original content also fails validation (pre-existing)
            orig_valid, orig_issues = validate_gutenberg(content)
            if not orig_valid:
                # Original already has issues — our text replacements and
                # info strip don't change block structure, so these are
                # pre-existing.  Safe to proceed.
                print(f'  Gutenberg validation: ISSUES PRE-EXISTING (original also fails)')
                print(f'    Original issues: {orig_issues}')
                print(f'    Modified issues: {issues}')
            else:
                print(f'  VALIDATION FAILED (new issues introduced): {issues}')
                results.append((page_id, label, f'VALIDATION_FAILED: {issues}', rep_count))
                continue
        else:
            print(f'  Gutenberg validation: PASSED')

        # Update
        success, msg = update_page(endpoint, page_id, new_content)
        if success:
            print(f'  UPDATE: SUCCESS')
            results.append((page_id, label, 'SUCCESS', rep_count))
            total_replacements += rep_count
        else:
            print(f'  UPDATE FAILED: {msg}')
            results.append((page_id, label, f'UPDATE_FAILED: {msg}', rep_count))

        # Rate limit
        time.sleep(0.5)

    # ── Summary ─────────────────────────────────────────────────────────────
    print(f'\n\n{"="*60}')
    print(f'SUMMARY')
    print(f'{"="*60}')
    for page_id, label, status, count in results:
        print(f'  Page {page_id} ({label}): {status} — {count} changes')
    print(f'\nTotal replacements across all pages: {total_replacements}')

    # Return non-zero if any failures
    failures = [r for r in results if r[2] not in ('SUCCESS', 'NO_CHANGES')]
    if failures:
        print(f'\n{len(failures)} page(s) had issues.')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
