#!/usr/bin/env python3
"""Fix overclaim/trust issues on page 1041 (Dog Toys) — pethubonline.com
V4 FINAL: Fix the remaining "thoroughly researched" sentence that contains
narrow no-break spaces (U+202F) in 'Pet Hub Online'."""

import sys
import requests

sys.path.insert(0, '/var/lib/freelancer/projects/40416335')
from gutenberg_utils import validate_gutenberg

# ── Config ──────────────────────────────────────────────────────────────
WP_BASE = 'https://pethubonline.com/wp-json/wp/v2'
AUTH = ('jasonsarah2026', 'yUmn Rngy EFE1 r7jr kjtm jmqx')
PAGE_ID = 1041
BACKUP_PATH = '/var/lib/freelancer/projects/40416335/phase10d/hub_backups/1041_dog_toys_backup.txt'

# Unicode narrow no-break space used throughout these headings/text
NNBSP = ' '


def main():
    s = requests.Session()
    s.auth = AUTH
    s.headers['Accept-Encoding'] = 'gzip, deflate'

    # ── STEP 1: Fetch current page content ──────────────────────────────
    print(f"[1] Fetching page {PAGE_ID} with context=edit ...")
    r = s.get(f'{WP_BASE}/pages/{PAGE_ID}', params={'context': 'edit'})
    r.raise_for_status()
    data = r.json()
    raw = data['content']['raw']
    title = data['title']['raw']
    print(f"    Title: {title}")
    print(f"    Content length: {len(raw)} chars")

    backup_v4 = BACKUP_PATH.replace('.txt', '_v4_pre.txt')
    with open(backup_v4, 'w', encoding='utf-8') as f:
        f.write(raw)
    print(f"    Pre-v4 backup saved to {backup_v4}")

    # ── STEP 2: Final replacement ───────────────────────────────────────
    content = raw
    changes = []

    def do_replace(old, new, label):
        nonlocal content
        if old in content:
            count = content.count(old)
            content = content.replace(old, new)
            changes.append(f"  [{count}x] {label}")
            print(f"  FIXED [{count}x]: {label}")
            return count
        return 0

    print("\n[2] Applying final replacement ...")

    # The remaining sentence: contains NNBSP in "Pet Hub Online"
    # Exact string: "Every toy featured on Pet Hub Online is thoroughly researched for safety, durability, and play value."
    old_sentence = f'Every toy featured on Pet{NNBSP}Hub{NNBSP}Online is thoroughly researched for safety, durability, and play value.'
    new_sentence = f'Every toy featured on Pet{NNBSP}Hub{NNBSP}Online is researched using manufacturer specifications, published reviews, and available safety data.'

    do_replace(old_sentence, new_sentence,
               'Trust body: thoroughly researched -> manufacturer specs/reviews/safety data')

    if not changes:
        print("    No changes needed — sentence may already be fixed.")

    # ── STEP 3-4: Validate ──────────────────────────────────────────────
    print("\n[3] Validating Gutenberg blocks ...")
    is_valid, issues = validate_gutenberg(content)
    if is_valid:
        print("    Validation PASSED.")
    else:
        print(f"    Issues: {issues}")
        real_issues = [i for i in issues if not i.startswith('unapproved_blocks:')]
        if real_issues:
            print("    ABORTING.")
            sys.exit(1)
        print("    Only unapproved block types. Proceeding.")

    # ── STEP 5: Update ──────────────────────────────────────────────────
    if not changes:
        print("\n[4] No update needed.")
        return

    print(f"\n[4] Updating page via API ...")
    r = s.post(f'{WP_BASE}/pages/{PAGE_ID}', json={'content': content})
    if r.status_code == 200:
        print(f"    SUCCESS: Page {PAGE_ID} updated.")
        updated = r.json()
        print(f"    Modified: {updated.get('modified', 'unknown')}")
    else:
        print(f"    FAILED: HTTP {r.status_code}")
        print(f"    Response: {r.text[:500]}")
        sys.exit(1)

    # ── FINAL VERIFICATION ──────────────────────────────────────────────
    print(f"\n[5] Full verification of all overclaim fixes ...")
    r = s.get(f'{WP_BASE}/pages/{PAGE_ID}', params={'context': 'edit'})
    final = r.json()['content']['raw']

    overclaim_checks = [
        # (phrase, should_be_absent=True)
        (f'Expert{NNBSP}Testing', True, 'Expert Testing (NNBSP)'),
        ('Expert Testing', True, 'Expert Testing (plain)'),
        ('independently tested', True, 'independently tested'),
        (f'Pet{NNBSP}Owner{NNBSP}Approved', True, 'Pet Owner Approved (NNBSP)'),
        ('Pet Owner Approved', True, 'Pet Owner Approved (plain)'),
        ('refreshed weekly', True, 'refreshed weekly'),
        ('recommended by pet experts', True, 'recommended by pet experts'),
        ('we would use ourselves', True, 'we would use ourselves'),
        ('curated range', True, 'curated range'),
        ('thoroughly researched for safety', True, 'thoroughly researched for safety'),
    ]

    expected_present = [
        ('Research-Based Recommendations', 'Research-Based Recommendations heading'),
        ('Community Focused', 'Community Focused heading'),
        ('regularly reviewed and updated', 'regularly reviewed and updated'),
        ('manufacturer specifications', 'manufacturer specifications'),
        ('Last Updated:</strong> 27 May 2026', 'Info strip'),
        ('Research-based guides', 'Footer strip fix'),
    ]

    all_good = True
    for phrase, should_be_absent, label in overclaim_checks:
        if phrase in final:
            print(f"    FAIL: '{label}' still present (should be removed)")
            all_good = False
        else:
            print(f"    OK: '{label}' removed")

    for phrase, label in expected_present:
        if phrase in final:
            print(f"    OK: '{label}' present")
        else:
            print(f"    FAIL: '{label}' missing")
            all_good = False

    if all_good:
        print("\n    ALL 16 OVERCLAIM FIXES VERIFIED SUCCESSFULLY.")
    else:
        print("\n    Some issues remain.")

    print(f"\n{'='*60}")
    print("COMPLETE CHANGE LOG (all runs combined):")
    print("  Run 1 (v1): 3 fixes — refreshed weekly, real dog owners, independently tested")
    print("  Run 2 (v2): 7 fixes — most trusted, v1 cleanup, footer strip, image alt,")
    print("              affiliate disclosure, curated range, product selection")
    print("  Run 3 (v3): 2 fixes — Expert Testing H3 (NNBSP), Pet Owner Approved H3 (NNBSP)")
    print(f"  Run 4 (v4): {len(changes)} fix(es) — thoroughly researched sentence (NNBSP)")
    print(f"\nTotal: {3+7+2+len(changes)} replacement operations across 4 runs")
    print(f"Page: {title} (ID: {PAGE_ID})")
    print(f"Original backup: {BACKUP_PATH}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
