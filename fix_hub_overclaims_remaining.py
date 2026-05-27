#!/usr/bin/env python3
"""
Fix overclaim issues and add info strips to 10 remaining hub pages on pethubonline.com.
Phase 10d - Hub page overclaim cleanup.
"""

import requests
import time
import os
import sys
import re

# ---------- Config ----------
BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
BACKUP_DIR = "/var/lib/freelancer/projects/40416335/phase10d/hub_backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

INFO_STRIP = """<!-- wp:paragraph {"style":{"typography":{"fontSize":"0.9em"}}} -->
<p style="font-size:0.9em;color:#555;"><strong>Last Updated:</strong> 27 May 2026<br/><strong>Website:</strong> pethubonline.com<br/><strong>Business:</strong> Pet Hub Online</p>
<!-- /wp:paragraph -->

<!-- wp:separator -->
<hr class="wp-block-separator has-alpha-channel-opacity"/>
<!-- /wp:separator -->"""

# All dash variants to try for "Expert-Reviewed" / "Expert-Approved" style strings
DASHES = ["-", "–", "—", "‑"]  # hyphen, en-dash, em-dash, non-breaking hyphen


def multi_dash_replace(content, before_dash, after_dash_old, after_dash_new):
    """Replace 'before_dash{ANY_DASH}after_dash_old' with 'before_dash-after_dash_new'
    trying all dash variants. Returns (new_content, count)."""
    total = 0
    for d in DASHES:
        old = f"{before_dash}{d}{after_dash_old}"
        if old in content:
            # Use simple hyphen in the replacement
            new = f"{before_dash}-{after_dash_new}" if after_dash_new else before_dash
            # But we actually want the replacement as specified by caller
            content = content.replace(old, f"{before_dash.replace('Expert','Recommended').replace('expert','recommended') if 'Expert' in before_dash or 'expert' in before_dash else before_dash}{'' if not after_dash_new else after_dash_new}")
            total += 1
    return content, total


def replace_all_dashes(content, old_pattern, new_pattern):
    """Replace old_pattern with new_pattern, trying all dash variants in old_pattern."""
    total = 0
    for d in DASHES:
        variant = old_pattern.replace("{D}", d)
        if variant in content:
            count = content.count(variant)
            content = content.replace(variant, new_pattern)
            total += count
    return content, total


def add_info_strip(content):
    """Add info strip after affiliate disclosure block (if present), before first main heading/cover.
    Returns (new_content, was_added)."""
    # Check if info strip already present
    if "pethubonline.com" in content and "Pet Hub Online" in content and "Last Updated" in content:
        return content, False

    # Strategy: find the right insertion point
    # Look for affiliate disclosure block first - it's typically a wp:group or wp:paragraph
    # with text about affiliate/commission/earn
    # Then insert after it, before the first cover/heading block.

    # Common patterns for affiliate disclosure:
    # <!-- wp:group ... --> ... affiliate ... <!-- /wp:group -->
    # Or a standalone paragraph with affiliate text

    # Let's find the best insertion point:
    # 1. After affiliate disclosure block (if any)
    # 2. Before first wp:cover or wp:heading

    # Try to find affiliate disclosure block end
    affiliate_end = -1
    # Look for common affiliate disclosure patterns
    aff_patterns = [
        "affiliate",
        "commission",
        "As an Amazon Associate",
        "earn from qualifying",
        "Affiliate Disclosure",
        "affiliate link",
    ]

    lines = content.split("\n")
    # Find if there's an affiliate block in the first ~30 lines
    for i, line in enumerate(lines[:50]):
        line_lower = line.lower()
        if any(p.lower() in line_lower for p in aff_patterns):
            # Found affiliate text. Now find the end of this block.
            # Look for the closing block comment after this line
            for j in range(i, min(i + 20, len(lines))):
                if "<!-- /wp:group -->" in lines[j] or "<!-- /wp:paragraph -->" in lines[j]:
                    affiliate_end = j
                    break
            if affiliate_end == -1:
                affiliate_end = i  # fallback: right after the affiliate line
            break

    if affiliate_end >= 0:
        # Insert after affiliate disclosure block
        insert_pos = affiliate_end + 1
        lines.insert(insert_pos, "")
        lines.insert(insert_pos + 1, INFO_STRIP)
        lines.insert(insert_pos + 2, "")
        return "\n".join(lines), True

    # No affiliate block found. Insert before first wp:cover or wp:heading
    for i, line in enumerate(lines):
        if "<!-- wp:cover" in line or "<!-- wp:heading" in line:
            lines.insert(i, "")
            lines.insert(i, INFO_STRIP)
            lines.insert(i, "")
            return "\n".join(lines), True

    # Fallback: insert at the very top
    return INFO_STRIP + "\n\n" + content, True


# ---------- Page definitions ----------
# Each entry: (page_id, list of (old, new) replacements)
# For dashed patterns, use {D} as placeholder for any dash type

PAGES = [
    {
        "id": 1176,
        "name": "Cat Supplies",
        "replacements": [
            ("Expert Reviewed Products", "Recommended Products"),
            ("our team", "we"),
        ],
    },
    {
        "id": 3107,
        "name": "Cat Beds",
        "replacements": [
            ("Expert{D}Reviewed Picks", "Recommended Picks"),
        ],
    },
    {
        "id": 3109,
        "name": "Cat Grooming",
        "replacements": [
            ("Expert{D}Reviewed Picks", "Recommended Picks"),
        ],
    },
    {
        "id": 3111,
        "name": "Cat Collars",
        "replacements": [
            ("Expert{D}Reviewed Picks", "Recommended Picks"),
        ],
    },
    {
        "id": 3113,
        "name": "Cat Scratching Posts",
        "replacements": [
            ("Expert{D}Reviewed Picks", "Recommended Picks"),
            # NOTE: keep "cat behaviour experts recommend" as is
        ],
    },
    {
        "id": 3115,
        "name": "Cat Litter Trays",
        "replacements": [
            ("Expert{D}Reviewed Picks", "Recommended Picks"),
        ],
    },
    {
        "id": 1951,
        "name": "Dog Bowls & Feeding",
        "replacements": [
            ("Expert{D}Reviewed Feeding Essentials", "Recommended Feeding Essentials"),
            # NOTE: keep "70 years of petware expertise" as is
        ],
    },
    {
        "id": 1956,
        "name": "Dog Training & Behaviour",
        "replacements": [
            ("Expert{D}Approved Essentials", "Recommended Essentials"),
            ("expert{D}backed training cards", "practical training cards"),
            (
                "Our training tools are tested by professionals and pet owners alike",
                "Our training guides are based on manufacturer specifications and widely available product information",
            ),
        ],
    },
    {
        "id": 1960,
        "name": "Dog Health & Care",
        "replacements": [
            ("Expert{D}Approved Essentials", "Recommended Essentials"),
            (
                "Our health products are tested by professionals and pet owners alike",
                "Our health product guides are based on manufacturer data and widely available information",
            ),
            # NOTE: keep "VET-APPROVED" as is (manufacturer claim)
        ],
    },
    {
        "id": 3892,
        "name": "Best Dog Food & Puppy Food UK",
        "replacements": [
            # NOTE: keep "with veterinary and nutrition experts" as-is (goal statement)
            # No text replacements needed, just info strip
        ],
    },
]


def fetch_page(session, page_id):
    """Fetch page content with context=edit."""
    url = f"{BASE}/pages/{page_id}?context=edit"
    resp = session.get(url, auth=AUTH)
    resp.raise_for_status()
    return resp.json()


def update_page(session, page_id, content):
    """Update page content."""
    url = f"{BASE}/pages/{page_id}"
    resp = session.post(url, auth=AUTH, json={"content": content})
    resp.raise_for_status()
    return resp.json()


def save_backup(page_id, slug, content):
    """Save backup of original content."""
    path = os.path.join(BACKUP_DIR, f"{page_id}_{slug}_backup.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def apply_replacements(content, replacements):
    """Apply all replacements, handling dash variants."""
    changes = []
    for old_pat, new_text in replacements:
        if "{D}" in old_pat:
            content, count = replace_all_dashes(content, old_pat, new_text)
            if count:
                changes.append(f"  Replaced '{old_pat}' -> '{new_text}' ({count}x)")
        else:
            count = content.count(old_pat)
            if count:
                content = content.replace(old_pat, new_text)
                changes.append(f"  Replaced '{old_pat}' -> '{new_text}' ({count}x)")
            else:
                changes.append(f"  WARNING: '{old_pat}' not found!")
    return content, changes


def main():
    s = requests.Session()
    s.headers["Accept-Encoding"] = "gzip, deflate"
    s.headers["User-Agent"] = "PetHub-OverclaimFix/1.0"

    results = []
    errors = []

    print("=" * 70)
    print("Hub Page Overclaim Fix + Info Strip - 10 Pages")
    print("=" * 70)

    for i, page_def in enumerate(PAGES):
        pid = page_def["id"]
        name = page_def["name"]
        replacements = page_def["replacements"]

        print(f"\n[{i+1}/10] Page {pid} ({name})")
        print("-" * 50)

        try:
            # 1. Fetch current content
            data = fetch_page(s, pid)
            slug = data.get("slug", f"page-{pid}")
            raw_content = data["content"]["raw"]
            print(f"  Fetched: {len(raw_content)} chars, slug='{slug}'")

            # 2. Save backup
            backup_path = save_backup(pid, slug, raw_content)
            print(f"  Backup saved: {backup_path}")

            # 3. Apply text replacements
            new_content, change_log = apply_replacements(raw_content, replacements)
            for c in change_log:
                print(c)

            # 4. Add info strip if missing
            new_content, strip_added = add_info_strip(new_content)
            if strip_added:
                print("  Added info strip at top")
            else:
                print("  Info strip already present - skipped")

            # 5. Check if anything changed
            if new_content == raw_content:
                print("  No changes needed - skipping update")
                results.append((pid, name, "NO CHANGES"))
                continue

            # 6. Update page
            update_page(s, pid, new_content)
            print(f"  UPDATED successfully!")
            results.append((pid, name, "UPDATED"))

        except Exception as e:
            err_msg = f"ERROR on page {pid} ({name}): {e}"
            print(f"  {err_msg}")
            errors.append(err_msg)
            results.append((pid, name, f"ERROR: {e}"))

        # 7. Sleep between updates
        if i < len(PAGES) - 1:
            time.sleep(0.5)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for pid, name, status in results:
        print(f"  Page {pid:5d} ({name:40s}) -> {status}")

    if errors:
        print(f"\n  ERRORS: {len(errors)}")
        for e in errors:
            print(f"    {e}")
    else:
        print(f"\n  All {len(results)} pages processed successfully!")

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
