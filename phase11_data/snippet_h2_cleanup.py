#!/usr/bin/env python3
"""
Phase 11R-fix: Clean up bad H2 rewrites from snippet capture engine.

Issues found:
1. "Compared: Compared:" double prefix (147 instances)
2. "What X Is Best for Y?" grammar errors (52 instances)
3. Other nonsensical rewrites (4 instances)

Strategy: For each bad rewrite, replace the bad new_h2 with a fixed version.
- Double "Compared:" → strip to "Compared: X vs Y" (proper single prefix)
- Grammar "Is Best for" → revert to original H2
- Other bad → revert to original H2
"""
import csv, json, os, re, subprocess, sys, tempfile, time
from collections import defaultdict

WP_API = "https://pethubonline.com/wp-json/wp/v2/posts"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
SLEEP_POST = 3
MAX_RETRIES = 3
BACKOFF_BASE = 5
CSV_PATH = "/var/lib/freelancer/projects/40416335/phase11_data/snippet_optimizations.csv"


def fetch_post(post_id):
    time.sleep(2)
    url = f"{WP_API}/{post_id}?context=edit&_fields=id,content"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def update_post(post_id, content_raw):
    url = f"{WP_API}/{post_id}"
    payload = json.dumps({"content": content_raw})
    for attempt in range(MAX_RETRIES):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            tmp.write(payload)
            tmp_path = tmp.name
        try:
            time.sleep(SLEEP_POST)
            result = subprocess.run(
                ["curl", "-s", "-X", "POST", "--compressed",
                 "-u", AUTH, "-H", "Content-Type: application/json",
                 "-d", f"@{tmp_path}", url],
                capture_output=True, text=True, timeout=120
            )
            try:
                resp = json.loads(result.stdout)
            except json.JSONDecodeError:
                continue
            if isinstance(resp, dict) and "id" in resp:
                return True
            if isinstance(resp, dict) and resp.get("data", {}).get("status") == 429:
                wait = BACKOFF_BASE * (attempt + 1)
                print(f"    [429] Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
    return False


def classify_bad_rewrite(original_h2, new_h2):
    """Returns (is_bad, fix_h2) or (False, None) if OK."""
    # Double Compared: prefix
    if "Compared: Compared:" in new_h2:
        # Fix: clean up the double prefix in original too, then keep as statement
        fixed = original_h2.replace("Compared: Compared:", "Compared:")
        return True, fixed

    # "What X Is Best for Y?" grammar
    if " Is Best for " in new_h2:
        return True, original_h2

    # Nonsensical "How to Feed Schedule"
    if re.search(r"How to Feed .+ and ", new_h2) and "Schedule" in new_h2:
        return True, original_h2

    # "What Hiding Spots: The Need Is Best for"
    if ": The Need Is Best" in new_h2:
        return True, original_h2

    # "What Is X Needs?" / "What Is X Behaviour?" / "What Is X Teething?"
    if re.match(r"What Is .+(Needs|Behaviour|Teething)\?$", new_h2):
        return True, original_h2

    return False, None


def html_escape_h2(text):
    """Escape for matching in HTML H2 tags."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    print("=" * 70)
    print("Phase 11R-fix: Cleaning up bad H2 rewrites")
    print("=" * 70)

    # Read CSV and identify bad rewrites
    bad_rewrites = defaultdict(list)  # post_id -> [(bad_h2, fix_h2), ...]
    total_bad = 0
    total_good = 0

    with open(CSV_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['action_taken'] != 'h2_rewrite':
                continue
            original = row['original_h2']
            new = row['new_h2']
            is_bad, fix = classify_bad_rewrite(original, new)
            if is_bad:
                bad_rewrites[row['post_id']].append((new, fix))
                total_bad += 1
            else:
                total_good += 1

    print(f"\nBad rewrites to fix: {total_bad}")
    print(f"Good rewrites (keeping): {total_good}")
    print(f"Posts affected: {len(bad_rewrites)}\n")

    if not bad_rewrites:
        print("Nothing to fix!")
        return

    # Process each affected post
    fixed_count = 0
    failed_count = 0
    posts_updated = 0
    posts_failed = 0

    for i, (post_id, fixes) in enumerate(sorted(bad_rewrites.items(), key=lambda x: int(x[0]), reverse=True)):
        print(f"  [{i+1}/{len(bad_rewrites)}] Processing post {post_id} ({len(fixes)} fixes)...")

        post = fetch_post(int(post_id))
        if not post or "content" not in post:
            print(f"    [ERROR] Could not fetch post {post_id}")
            posts_failed += 1
            continue

        content = post["content"]["raw"]
        content_changed = False

        for bad_h2, fix_h2 in fixes:
            # Try to find and replace in Gutenberg H2 blocks
            # Match: <h2 ...>BAD_TEXT</h2>
            bad_escaped = re.escape(bad_h2)
            pattern = f"(<h2[^>]*>){bad_escaped}(</h2>)"
            replacement = f"\\g<1>{fix_h2}\\g<2>"
            new_content, count = re.subn(pattern, replacement, content)
            if count > 0:
                content = new_content
                content_changed = True
                fixed_count += count
            else:
                # Try HTML-escaped version
                bad_html = html_escape_h2(bad_h2)
                bad_escaped2 = re.escape(bad_html)
                pattern2 = f"(<h2[^>]*>){bad_escaped2}(</h2>)"
                new_content2, count2 = re.subn(pattern2, replacement, content)
                if count2 > 0:
                    content = new_content2
                    content_changed = True
                    fixed_count += count2
                else:
                    print(f"    [WARN] Could not find H2: {bad_h2[:60]}...")
                    failed_count += 1

        if content_changed:
            # Also clean up any remaining double "Compared: Compared:" in the whole content
            content = content.replace("Compared: Compared:", "Compared:")

            success = update_post(int(post_id), content)
            if success:
                posts_updated += 1
                print(f"    [OK] Updated ({len(fixes)} H2s fixed)")
            else:
                posts_failed += 1
                print(f"    [FAIL] Update failed")
        else:
            print(f"    [SKIP] No matching H2s found in content")

    # Summary
    print(f"\n{'='*70}")
    print(f"CLEANUP SUMMARY")
    print(f"{'='*70}")
    print(f"  H2s fixed: {fixed_count}")
    print(f"  H2s not found: {failed_count}")
    print(f"  Posts updated: {posts_updated}")
    print(f"  Posts failed: {posts_failed}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
