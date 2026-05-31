#!/usr/bin/env python3
"""
Phase 13 - Reclassify 45 Uncategorized WordPress Posts on pethubonline.com
into strategic content clusters.

This script:
1. Fetches all published posts in category "Uncategorized" (ID 1)
2. Fetches all available categories
3. Analyzes each post title+content to determine best category
4. Generates a CSV reclassification plan
5. Executes reclassification via WP REST API (adds new category, keeps Uncategorized)
6. Prints summary
"""

import requests
import csv
import time
import re
import os
from html import unescape

# WordPress credentials
WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
AUTH = (WP_USER, WP_PASS)

# Target categories with IDs (from live site)
CATEGORIES = {
    "Cat Supplies": 1377,
    "Cat Toys": 1459,
    "Indoor Cats": 1413,
    "Dog Supplies": 1376,
    "Dog Beds": 1401,
    "Dog Food": 1467,
    "Dog Health": 1450,
    "Dog Care": 1489,
    "Dog Toys": 1441,
    "Dog Harnesses": 1422,
    "Buying Guides": 1380,
    "Pet Care": 1397,
    "Pet Health": 1391,
    "Pet Beds": 1396,
    "Product Reviews": 1379,
    "Puppy Care": 1442,
    "Training Supplies": 1474,
    "Enrichment Activities": 1443,
    "Interactive Toys": 1460,
    "Orthopaedic Care": 1455,
}

# Output paths
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase13_data"
CSV_PATH = os.path.join(OUTPUT_DIR, "Cluster_Reclassification_Plan.csv")


def strip_html(html_text):
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', ' ', html_text)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def classify_post(title, content_text):
    """
    Rule-based classification using keyword matching on title and content.
    Returns (category_name, category_id, confidence, reasoning).
    """
    title_lower = title.lower()
    content_lower = content_text[:3000].lower()  # First 3000 chars for efficiency
    combined = title_lower + " " + content_lower

    # === SITE META / ABOUT PAGES ===
    if any(kw in title_lower for kw in ["research standards", "why pethub", "about us"]):
        return ("Pet Care", 1397, "high",
                "Site meta/about content - general Pet Care category")

    # === CAT-SPECIFIC ===
    if "cat toy" in title_lower or "cat toys" in title_lower:
        return ("Cat Toys", 1459, "high",
                "Title explicitly mentions cat toys")

    if "indoor cat" in title_lower:
        if "toy" in title_lower:
            return ("Cat Toys", 1459, "high",
                    "Indoor cat toys - primary focus is toys for indoor cats")
        return ("Indoor Cats", 1413, "high",
                "Title explicitly about indoor cats")

    if "cat scratch" in title_lower or "cat scratching" in title_lower:
        return ("Cat Supplies", 1377, "high",
                "Cat scratching behaviour relates to cat supplies (scratching posts)")

    if "cat" in title_lower and "toy" not in title_lower:
        return ("Cat Supplies", 1377, "medium",
                "Cat-related content best fits Cat Supplies")

    # === DOG TOYS (specific patterns) ===
    dog_toy_keywords = [
        "dog toy", "toy rotation", "toy safety", "toy lifespan",
        "toy overstimulation", "toy hygiene", "toy durability",
        "toy materials", "tug play", "puzzle", "mental stimulation toy",
        "senior dog toy", "play style", "multi-dog toy", "toy storage",
        "dog play", "play recovery", "enrichment for dogs",
        "scent-game", "scent game", "confidence-building play",
        "sensory enrichment", "boredom prevention", "crate and play",
        "rotating puzzle"
    ]
    if any(kw in title_lower for kw in dog_toy_keywords):
        return ("Dog Toys", 1441, "high",
                "Title directly relates to dog toys/play/enrichment activities")

    if "enrichment" in title_lower and "dog" in combined:
        # Check if it's specifically about toys/play
        if any(w in combined for w in ["toy", "play", "puzzle", "game"]):
            return ("Dog Toys", 1441, "high",
                    "Dog enrichment content focused on toys and play")
        return ("Dog Care", 1489, "medium",
                "General dog enrichment fits Dog Care")

    # === DOG BEDS ===
    if "dog bed" in title_lower or "bed sizing" in title_lower:
        return ("Dog Beds", 1401, "high",
                "Title explicitly about dog beds")

    # === DOG HEALTH ===
    dog_health_keywords = [
        "dog health", "orthopaedic", "orthopedic", "joint health",
        "mobility", "low-mobility", "arthritis", "healing dog"
    ]
    if any(kw in title_lower for kw in dog_health_keywords):
        return ("Dog Health", 1450, "high",
                "Title relates to dog health/orthopaedic/mobility topics")

    # === DOG FOOD / NUTRITION ===
    if "dog food" in title_lower or ("nutrition" in title_lower and "dog" in combined):
        return ("Dog Food", 1467, "high",
                "Title explicitly about dog food/nutrition")

    if "pet nutrition" in title_lower or "food label" in title_lower:
        return ("Dog Food", 1467, "medium",
                "Pet nutrition/food labels content - fits Dog Food category")

    if "pet feeding" in title_lower or "feeding guide" in title_lower:
        return ("Dog Food", 1467, "medium",
                "Feeding guide content fits Dog Food category")

    # === DOG TRAINING ===
    if "training" in title_lower and "dog" in combined:
        return ("Training Supplies", 1474, "high",
                "Dog training content fits Training Supplies")

    if "training terminology" in title_lower or "training equipment" in title_lower:
        return ("Training Supplies", 1474, "high",
                "Training-focused content")

    # === PUPPY CARE ===
    if "puppy" in title_lower:
        return ("Puppy Care", 1442, "high",
                "Title explicitly about puppies")

    # === DOG BEHAVIOUR ===
    if "dog behaviour" in title_lower or "dog behavior" in title_lower:
        return ("Dog Care", 1489, "high",
                "Dog behaviour content fits Dog Care")

    # === PET TOY SAFETY (general) ===
    if "pet toy safety" in title_lower:
        return ("Dog Toys", 1441, "medium",
                "Pet toy safety - majority of toy content is dog-focused")

    # === PET ENRICHMENT (general) ===
    if "pet enrichment" in title_lower:
        if "dog" in content_lower[:500]:
            return ("Dog Toys", 1441, "medium",
                    "Pet enrichment with dog focus relates to Dog Toys")
        return ("Pet Care", 1397, "medium",
                "General pet enrichment content")

    # === PET HEALTH ===
    if "pet health" in title_lower or "veterinary" in title_lower:
        return ("Pet Health", 1391, "high",
                "Pet health terminology/content")

    # === PET GROOMING ===
    if "grooming" in title_lower:
        return ("Pet Care", 1397, "medium",
                "Pet grooming fits general Pet Care")

    # === BUYING GUIDES ===
    if "buying guide" in title_lower or "best " in title_lower:
        if "cat" in title_lower:
            return ("Cat Toys", 1459, "high",
                    "Best cat toys buying guide")
        if "dog bed" in title_lower:
            return ("Dog Beds", 1401, "high",
                    "Best dog beds buying guide")
        return ("Buying Guides", 1380, "medium",
                "Buying guide content")

    # === FALLBACK: Check content for primary animal ===
    dog_signals = sum(1 for w in ["dog", "canine", "puppy", "pup"] if w in content_lower[:1000])
    cat_signals = sum(1 for w in ["cat", "feline", "kitten"] if w in content_lower[:1000])

    if dog_signals > cat_signals:
        if "toy" in combined or "play" in combined or "enrichment" in combined:
            return ("Dog Toys", 1441, "medium",
                    "Content primarily dog-focused with toy/play/enrichment themes")
        return ("Dog Care", 1489, "low",
                "Content primarily dog-focused, general care")
    elif cat_signals > dog_signals:
        return ("Cat Supplies", 1377, "low",
                "Content primarily cat-focused")
    else:
        return ("Pet Care", 1397, "low",
                "General pet content, no clear primary category")


def fetch_uncategorized_posts():
    """Fetch all posts in Uncategorized category (ID 1)."""
    posts = []
    page = 1
    headers = {"Accept-Encoding": "gzip, deflate"}
    while True:
        resp = requests.get(
            f"{WP_BASE}/posts",
            params={
                "categories": 1,
                "per_page": 50,
                "page": page,
                "status": "publish",
                "_fields": "id,title,categories,content"
            },
            auth=AUTH,
            headers=headers,
            timeout=30
        )
        if resp.status_code != 200:
            print(f"Error fetching posts page {page}: {resp.status_code}")
            break
        data = resp.json()
        if not data:
            break
        posts.extend(data)
        if len(data) < 50:
            break
        page += 1
    return posts


def main():
    print("=" * 70)
    print("PHASE 13 - PETHUBONLINE.COM POST RECLASSIFICATION")
    print("=" * 70)
    print()

    # Step 1: Fetch uncategorized posts
    print("[1/5] Fetching uncategorized posts...")
    posts = fetch_uncategorized_posts()
    print(f"  Found {len(posts)} uncategorized posts")
    print()

    # Step 2: Classify each post
    print("[2/5] Analyzing and classifying posts...")
    classifications = []
    for post in posts:
        post_id = post["id"]
        title = unescape(post["title"]["rendered"])
        content_text = strip_html(post["content"]["rendered"])
        current_cats = post["categories"]

        cat_name, cat_id, confidence, reasoning = classify_post(title, content_text)

        classifications.append({
            "post_id": post_id,
            "title": title,
            "current_category": "Uncategorized",
            "recommended_category": cat_name,
            "recommended_category_id": cat_id,
            "confidence": confidence,
            "reasoning": reasoning,
            "current_categories": current_cats
        })
        print(f"  [{confidence:6s}] {post_id:6d} -> {cat_name:<20s} | {title[:60]}")

    print()

    # Step 3: Generate CSV
    print(f"[3/5] Writing CSV to {CSV_PATH}...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "post_id", "title", "current_category",
            "recommended_category", "recommended_category_id",
            "confidence", "reasoning"
        ])
        writer.writeheader()
        for c in classifications:
            writer.writerow({
                "post_id": c["post_id"],
                "title": c["title"],
                "current_category": c["current_category"],
                "recommended_category": c["recommended_category"],
                "recommended_category_id": c["recommended_category_id"],
                "confidence": c["confidence"],
                "reasoning": c["reasoning"]
            })
    print(f"  CSV saved with {len(classifications)} rows")
    print()

    # Step 4: Execute reclassification via WP REST API
    print("[4/5] Executing reclassification (5s delay between updates)...")
    success_count = 0
    fail_count = 0
    category_counts = {}

    for i, c in enumerate(classifications, 1):
        post_id = c["post_id"]
        new_cat_id = c["recommended_category_id"]
        cat_name = c["recommended_category"]

        # Keep Uncategorized (1) AND add new category
        new_categories = list(set(c["current_categories"] + [new_cat_id]))

        try:
            resp = requests.post(
                f"{WP_BASE}/posts/{post_id}",
                json={"categories": new_categories},
                auth=AUTH,
                headers={"Content-Type": "application/json", "Accept-Encoding": "gzip, deflate"},
                timeout=30
            )

            if resp.status_code == 200:
                success_count += 1
                category_counts[cat_name] = category_counts.get(cat_name, 0) + 1
                print(f"  [{i:2d}/45] OK   Post {post_id} -> +{cat_name} (ID {new_cat_id})")
            else:
                fail_count += 1
                print(f"  [{i:2d}/45] FAIL Post {post_id} - HTTP {resp.status_code}: {resp.text[:100]}")
        except Exception as e:
            fail_count += 1
            print(f"  [{i:2d}/45] ERR  Post {post_id} - {str(e)}")

        # 5-second delay between updates
        if i < len(classifications):
            time.sleep(5)

    print()

    # Step 5: Summary
    print("=" * 70)
    print("[5/5] RECLASSIFICATION SUMMARY")
    print("=" * 70)
    print(f"  Total posts processed: {len(classifications)}")
    print(f"  Successfully updated:  {success_count}")
    print(f"  Failed:                {fail_count}")
    print()
    print("  Category Distribution:")
    print("  " + "-" * 50)
    for cat_name, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        cat_id = CATEGORIES.get(cat_name, "?")
        print(f"    {cat_name:<25s} (ID {cat_id:>5}) : {count:2d} posts")
    print("  " + "-" * 50)
    print(f"    {'TOTAL':<25s}              : {success_count:2d} posts")
    print()
    print("  NOTE: Uncategorized (ID 1) was KEPT on all posts.")
    print("  Client can remove it after confirming the new assignments.")
    print()
    print("  CSV plan saved to:")
    print(f"    {CSV_PATH}")
    print()


if __name__ == "__main__":
    main()
