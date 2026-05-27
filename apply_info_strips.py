#!/usr/bin/env python3
"""Add standardized info strip to educational posts that lack one.
Phase 10C + 10D posts on pethubonline.com."""

import sys
import time
import requests
from datetime import datetime

sys.path.insert(0, '/var/lib/freelancer/projects/40416335')
from gutenberg_utils import validate_gutenberg

# ── Config ──────────────────────────────────────────────────────────────
WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")

TARGET_IDS = [
    4563, 4566, 4568, 4570, 4571, 4573, 4574, 4576,
    4406, 4407, 4408, 4409, 4410, 4415, 4411, 4412, 4413, 4414,
    4783, 4784, 4785, 4786, 4787, 4788, 4789, 4790, 4791, 4792,
]


def format_date(iso_str):
    """Convert ISO date string to '27 May 2026' format."""
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        return dt.strftime('%-d %B %Y')
    except Exception:
        return "27 May 2026"


def build_info_strip(last_updated_str):
    """Build the info strip paragraph block + separator."""
    strip = (
        f'<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"0.9em"}}}}}} -->\n'
        f'<p style="font-size:0.9em;color:#555;"><strong>Last Updated:</strong> {last_updated_str}'
        f'<br/><strong>Website:</strong> pethubonline.com'
        f'<br/><strong>Business:</strong> Pet Hub Online</p>\n'
        f'<!-- /wp:paragraph -->'
    )
    sep = (
        '<!-- wp:separator -->\n'
        '<hr class="wp-block-separator has-alpha-channel-opacity"/>\n'
        '<!-- /wp:separator -->'
    )
    return strip + '\n\n' + sep


def has_info_strip(content):
    """Check if the first 500 chars already contain an info strip."""
    first_500 = content[:500] if content else ""
    return "Last Updated:" in first_500 or "Business:" in first_500


def main():
    session = requests.Session()
    session.auth = AUTH
    session.headers['Accept-Encoding'] = 'gzip, deflate'

    updated = []
    skipped = []
    errors = []

    for pid in TARGET_IDS:
        print(f"\n--- Post {pid} ---")

        # 1. GET the post
        r = session.get(f"{WP_BASE}/posts/{pid}", params={"context": "edit"})
        if r.status_code != 200:
            msg = f"GET failed: HTTP {r.status_code}"
            print(f"  ERROR: {msg}")
            errors.append((pid, msg))
            time.sleep(0.3)
            continue

        post = r.json()
        title = post.get("title", {}).get("raw", post.get("title", ""))
        content = post.get("content", {}).get("raw", post.get("content", ""))
        modified = post.get("modified", "")

        print(f"  Title: {title}")
        print(f"  Modified: {modified}")
        print(f"  Content length: {len(content)} chars")

        # 2. Check if already has info strip
        if has_info_strip(content):
            print(f"  SKIP: already has info strip")
            skipped.append((pid, title))
            time.sleep(0.3)
            continue

        # 3. Determine the date
        if modified:
            last_updated_str = format_date(modified)
        else:
            last_updated_str = "27 May 2026"
        print(f"  Last Updated date: {last_updated_str}")

        # 4. Build the info strip
        info_block = build_info_strip(last_updated_str)

        # 5. Prepend before existing content
        new_content = info_block + '\n\n' + content

        # 6. Validate Gutenberg blocks
        is_valid, issues = validate_gutenberg(new_content)
        if not is_valid:
            msg = f"Validation failed: {'; '.join(issues)}"
            print(f"  ERROR: {msg}")
            errors.append((pid, msg))
            time.sleep(0.3)
            continue

        print(f"  Validation: PASS")

        # 7. Update the post
        r2 = session.post(f"{WP_BASE}/posts/{pid}", json={"content": new_content})
        if r2.status_code == 200:
            print(f"  UPDATED successfully")
            updated.append((pid, title))
        else:
            msg = f"POST failed: HTTP {r2.status_code}"
            print(f"  ERROR: {msg}")
            errors.append((pid, msg))

        time.sleep(0.3)

    # ── Summary ─────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Updated: {len(updated)}")
    for pid, title in updated:
        print(f"  {pid}: {title}")

    print(f"\nSkipped (already had strip): {len(skipped)}")
    for pid, title in skipped:
        print(f"  {pid}: {title}")

    print(f"\nErrors: {len(errors)}")
    for pid, msg in errors:
        print(f"  {pid}: {msg}")

    print(f"\nTotal processed: {len(TARGET_IDS)}")


if __name__ == "__main__":
    main()
