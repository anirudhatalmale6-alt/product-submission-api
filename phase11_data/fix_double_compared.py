#!/usr/bin/env python3
"""
Fix remaining "Compared: Compared:" double prefixes across all posts.
Runs after snippet_h2_cleanup.py — catches any posts that weren't covered
by the H2 rewrite cleanup.
"""
import json, os, subprocess, sys, tempfile, time

WP_API = "https://pethubonline.com/wp-json/wp/v2/posts"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
SLEEP_GET = 2
SLEEP_POST = 3
MAX_RETRIES = 3
BACKOFF_BASE = 5


def fetch_all_posts():
    posts = []
    page = 1
    while True:
        time.sleep(SLEEP_GET)
        url = f"{WP_API}?per_page=100&page={page}&context=edit&_fields=id,title,content&status=publish"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True, timeout=60
        )
        try:
            batch = json.loads(result.stdout)
        except json.JSONDecodeError:
            break
        if not isinstance(batch, list) or len(batch) == 0:
            break
        posts.extend(batch)
        print(f"  Page {page}: {len(batch)} posts (total: {len(posts)})")
        if len(batch) < 100:
            break
        page += 1
    return posts


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


def main():
    print("=" * 70)
    print("Fix remaining 'Compared: Compared:' double prefixes")
    print("=" * 70)

    print("\nFetching all published posts...")
    posts = fetch_all_posts()
    print(f"Total: {len(posts)} posts\n")

    affected = []
    for p in posts:
        content = p.get("content", {}).get("raw", "")
        if "Compared: Compared:" in content:
            title = p.get("title", {}).get("raw", p.get("title", {}).get("rendered", ""))
            affected.append({"id": p["id"], "title": title, "content": content})

    print(f"Posts still containing 'Compared: Compared:': {len(affected)}\n")

    if not affected:
        print("All clean! Nothing to fix.")
        return

    fixed = 0
    failed = 0
    for i, post in enumerate(affected):
        print(f"  [{i+1}/{len(affected)}] Fixing post {post['id']}: {post['title'][:60]}...")
        new_content = post["content"].replace("Compared: Compared:", "Compared:")
        success = update_post(post["id"], new_content)
        if success:
            fixed += 1
            print(f"    [OK] Fixed")
        else:
            failed += 1
            print(f"    [FAIL]")

    print(f"\n{'='*70}")
    print(f"  Fixed: {fixed}, Failed: {failed}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
