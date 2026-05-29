#!/usr/bin/env python3
"""Check which posts still lack humanization blocks."""

import subprocess
import json
import time

WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"

def fetch_all_posts():
    all_posts = []
    page = 1
    while True:
        url = f"{WP_API}/posts?status=publish&per_page=100&page={page}&_fields=id,title,slug,content&context=edit"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            break
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            break
        if not data or isinstance(data, dict):
            break
        all_posts.extend(data)
        if len(data) < 100:
            break
        page += 1
        time.sleep(0.5)
    return all_posts

def main():
    posts = fetch_all_posts()
    print(f"Total published posts: {len(posts)}")

    missing = []
    has_blocks = []

    for p in posts:
        pid = p["id"]
        title = p["title"]["raw"] if isinstance(p["title"], dict) else p["title"]
        content = p["content"]["raw"] if isinstance(p["content"], dict) else p.get("content", "")

        has_about = "About this guide:" in content
        has_mistakes = "Common Mistakes to Avoid" in content
        has_suitability = "Quick Suitability Guide" in content
        # Also check for existing buyer-intent blocks
        has_quick_routine = any(m in content for m in [
            "Quick Routine", "Quick Grooming Routine", "Quick Brushing Routine",
            "Quick Bathing Routine", "Quick Nail Care Routine", "Quick Health Maintenance",
            "Quick Dental Care Routine", "Quick Flea Prevention", "Quick Joint Care Routine",
            "Quick Training Routine", "Quick Puppy Training Timeline", "Quick Play Routine",
            "Quick Scratching Post", "Quick Litter Tray", "Quick Litter Management",
            "Quick Waste Disposal"
        ])
        has_pros = "Advantages" in content or "Things to Watch" in content

        if has_about or has_mistakes or has_suitability or has_quick_routine or has_pros:
            has_blocks.append((pid, title, has_about, has_mistakes, has_suitability))
        else:
            missing.append((pid, title))

    print(f"\nPosts WITH humanization/buyer-intent blocks: {len(has_blocks)}")
    print(f"Posts WITHOUT any blocks: {len(missing)}")

    if missing:
        print(f"\n--- MISSING BLOCKS ---")
        for pid, title in sorted(missing, key=lambda x: x[0]):
            print(f"  {pid}: {title}")

if __name__ == "__main__":
    main()
