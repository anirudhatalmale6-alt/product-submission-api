#!/usr/bin/env python3
"""Fetch all published posts and identify untreated Dog Toys + Uncategorized posts."""

import subprocess
import json
import time

WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"

ALREADY_TREATED = {3956, 3957, 3959, 5421, 5423, 5469, 5471, 5476, 5483, 5509,
                   3996, 4004, 4011, 4018, 4784, 4174, 4181, 4188, 4286, 4307,
                   4057, 4064, 4071, 4078, 4563, 4118, 4132, 4089, 4146, 5508}

DOG_TOYS_KEYWORDS = [
    "dog toy", "enrichment", "fetch", "tug", "chew", "puzzle", "boredom",
    "play style", "overstimulation", "pet toy safety", "cat toy safety",
    "cat enrichment", "cat toy rotation"
]

UNCATEGORIZED_KEYWORDS = [
    "seasonal pet", "first-time dog owner", "multi-pet", "pet hydration",
    "pet first aid", "confidence-building", "rotating puzzle",
    "where to place", "how to wash"
]

# Clusters that have their own treatment (should be excluded from Uncategorized)
OTHER_CLUSTER_KEYWORDS = [
    "dog bed", "orthopaedic", "cooling bed", "puppy bed", "bed material",
    "dog groom", "dog brush", "dog shampoo", "nail clip", "grooming basics",
    "dog train", "puppy train", "dog health", "dog bowl", "feeding",
    "cat scratch", "cat bed", "cat litter", "cat food", "cat health",
    "dog harness", "dog lead", "dog collar", "dog coat", "dog jacket",
    "puppy development"
]

def fetch_all_posts():
    """Fetch all published posts with pagination."""
    all_posts = []
    page = 1
    while True:
        url = f"{WP_API}/posts?status=publish&per_page=100&page={page}&_fields=id,title,slug,content&context=edit"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            print(f"Error on page {page}: {result.stderr}")
            break
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"JSON error on page {page}: {result.stdout[:200]}")
            break

        if not data or isinstance(data, dict):
            # API returns dict with error on empty pages
            if isinstance(data, dict):
                print(f"Page {page}: {data.get('message', 'unknown error')}")
            break

        all_posts.extend(data)
        print(f"Page {page}: fetched {len(data)} posts (total: {len(all_posts)})")

        if len(data) < 100:
            break
        page += 1
        time.sleep(0.5)

    return all_posts

def matches_keywords(text, keywords):
    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            return True
    return False

def has_humanization_blocks(content):
    """Check if post already has About this guide, Common Mistakes, or Quick Suitability."""
    markers = ["About this guide", "Common Mistakes to Avoid", "Quick Suitability Guide"]
    for m in markers:
        if m in content:
            return True
    return False

def main():
    print("Fetching all published posts...")
    posts = fetch_all_posts()
    print(f"\nTotal published posts: {len(posts)}")

    dog_toys_posts = []
    uncategorized_posts = []
    already_has_blocks = []
    already_treated = []

    for p in posts:
        pid = p["id"]
        title = p["title"]["raw"] if isinstance(p["title"], dict) else p["title"]
        slug = p.get("slug", "")
        content = p["content"]["raw"] if isinstance(p["content"], dict) else p.get("content", "")

        combined_text = f"{title} {slug} {content[:2000]}"

        if pid in ALREADY_TREATED:
            already_treated.append((pid, title))
            continue

        is_dog_toys = matches_keywords(combined_text, DOG_TOYS_KEYWORDS)
        is_uncategorized = matches_keywords(combined_text, UNCATEGORIZED_KEYWORDS)
        is_other_cluster = matches_keywords(combined_text, OTHER_CLUSTER_KEYWORDS)

        has_blocks = has_humanization_blocks(content)

        if has_blocks:
            already_has_blocks.append((pid, title, "dog_toys" if is_dog_toys else "uncategorized"))
            continue

        if is_dog_toys:
            dog_toys_posts.append((pid, title))
        elif not is_other_cluster:
            # Doesn't match any specific cluster = uncategorized
            uncategorized_posts.append((pid, title))
        elif is_uncategorized:
            uncategorized_posts.append((pid, title))

    print(f"\n{'='*70}")
    print(f"Already treated (skip): {len(already_treated)}")
    print(f"Already has blocks (skip): {len(already_has_blocks)}")
    print(f"Dog Toys cluster (to process): {len(dog_toys_posts)}")
    print(f"Uncategorized (to process): {len(uncategorized_posts)}")
    print(f"Total to process: {len(dog_toys_posts) + len(uncategorized_posts)}")

    print(f"\n--- DOG TOYS POSTS ---")
    for pid, title in sorted(dog_toys_posts, key=lambda x: x[0]):
        print(f"  {pid}: {title}")

    print(f"\n--- UNCATEGORIZED POSTS ---")
    for pid, title in sorted(uncategorized_posts, key=lambda x: x[0]):
        print(f"  {pid}: {title}")

    if already_has_blocks:
        print(f"\n--- ALREADY HAS BLOCKS (skipped) ---")
        for pid, title, cluster in already_has_blocks:
            print(f"  {pid}: {title} [{cluster}]")

if __name__ == "__main__":
    main()
