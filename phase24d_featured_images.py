#!/usr/bin/env python3
"""
Phase 24D - Featured Images Audit & Fix for PetHub Online
Fetches all published posts, identifies missing featured images,
sources images from Pexels, uploads to WordPress, and sets as featured.
"""

import requests
import json
import time
import re
import os
import sys
from datetime import datetime
from requests.auth import HTTPBasicAuth

# ── Configuration ──────────────────────────────────────────────────────
WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_AUTH = HTTPBasicAuth(WP_USER, WP_PASS)
WP_HEADERS = {"Accept-Encoding": "gzip, deflate"}

PEXELS_KEY = "dmGyKrZqTlwukxWzOK1EkH4jbEv9EaIDpLGj7eL5MZ07bl6AR9OEoHlB"
PEXELS_HEADERS = {
    "Authorization": PEXELS_KEY,
    "Accept-Encoding": "gzip, deflate"
}

RESULTS_PATH = "/var/lib/freelancer/projects/40416335/phase24d_featured_images_results.json"
DELAY = 2          # seconds between API calls
RETRY_DELAY = 10   # seconds on 429

# Stop words to filter from search queries
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "need", "must",
    "it", "its", "this", "that", "these", "those", "i", "you", "he", "she",
    "we", "they", "me", "him", "her", "us", "them", "my", "your", "his",
    "our", "their", "what", "which", "who", "whom", "how", "when", "where",
    "why", "not", "no", "nor", "so", "if", "then", "than", "too", "very",
    "just", "about", "up", "out", "all", "also", "as", "into", "over",
    "after", "before", "between", "under", "above", "below", "each",
    "every", "both", "few", "more", "most", "other", "some", "such",
    "only", "own", "same", "here", "there", "again", "further",
    "why", "top", "best", "guide", "tips", "ultimate", "complete",
    "essential", "everything", "know", "things", "ways"
}


def api_call(method, url, retries=3, **kwargs):
    """Make an API call with retry on 429."""
    for attempt in range(retries):
        try:
            resp = method(url, timeout=30, **kwargs)
            if resp.status_code == 429:
                print(f"    [429] Rate limited, waiting {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
                continue
            return resp
        except requests.exceptions.RequestException as e:
            print(f"    [ERROR] Request failed (attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                time.sleep(5)
    return None


def fetch_all_posts():
    """Fetch all published posts with pagination."""
    all_posts = []
    page = 1
    while True:
        print(f"  Fetching posts page {page}...")
        resp = api_call(
            requests.get,
            f"{WP_BASE}/posts",
            params={
                "per_page": 100,
                "page": page,
                "status": "publish",
                "_fields": "id,title,featured_media"
            },
            headers=WP_HEADERS,
            auth=WP_AUTH
        )
        if resp is None or resp.status_code != 200:
            print(f"    Failed to fetch page {page}: {resp.status_code if resp else 'no response'}")
            break
        posts = resp.json()
        if not posts:
            break
        all_posts.extend(posts)
        total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
        print(f"    Got {len(posts)} posts (page {page}/{total_pages})")
        if page >= total_pages:
            break
        page += 1
        time.sleep(DELAY)
    return all_posts


def make_search_query(title):
    """Extract key topic words from a post title for Pexels search."""
    # Decode HTML entities
    title = title.replace("&#8217;", "'").replace("&amp;", "&")
    title = re.sub(r"&#\d+;", "", title)
    title = re.sub(r"&\w+;", "", title)
    # Remove special characters, keep letters/spaces
    clean = re.sub(r"[^a-zA-Z\s]", " ", title.lower())
    words = clean.split()
    # Filter stop words
    keywords = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    # Take up to 4 keywords for a focused search
    query = " ".join(keywords[:4])
    # If no keywords remain, use cleaned title
    if not query:
        query = " ".join(words[:3])
    # Always add "pet" context if not present
    pet_words = {"pet", "pets", "dog", "dogs", "cat", "cats", "puppy", "kitten",
                 "animal", "animals", "fish", "bird", "rabbit", "hamster", "parrot",
                 "turtle", "reptile", "guinea", "ferret", "horse", "pony", "vet",
                 "veterinary", "grooming", "aquarium", "terrarium"}
    if not any(w in pet_words for w in keywords):
        query = query + " pet"
    return query


def search_pexels(query):
    """Search Pexels for a landscape image matching the query."""
    resp = api_call(
        requests.get,
        "https://api.pexels.com/v1/search",
        params={
            "query": query,
            "orientation": "landscape",
            "per_page": 3
        },
        headers=PEXELS_HEADERS
    )
    if resp is None or resp.status_code != 200:
        print(f"    Pexels search failed: {resp.status_code if resp else 'no response'}")
        return None
    data = resp.json()
    photos = data.get("photos", [])
    if not photos:
        print(f"    No Pexels results for '{query}'")
        return None
    # Return the first photo's large image URL and photographer info
    photo = photos[0]
    return {
        "url": photo["src"]["large"],
        "photographer": photo.get("photographer", "Unknown"),
        "pexels_url": photo.get("url", ""),
        "alt": photo.get("alt", query)
    }


def download_image(url):
    """Download an image and return the bytes."""
    resp = api_call(
        requests.get,
        url,
        headers={"Accept-Encoding": "gzip, deflate"}
    )
    if resp is None or resp.status_code != 200:
        print(f"    Image download failed: {resp.status_code if resp else 'no response'}")
        return None
    return resp.content


def upload_to_wordpress(image_data, filename, alt_text="", caption=""):
    """Upload an image to WordPress media library."""
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "image/jpeg",
        "Accept-Encoding": "gzip, deflate"
    }
    resp = api_call(
        requests.post,
        f"{WP_BASE}/media",
        headers=headers,
        auth=WP_AUTH,
        data=image_data
    )
    if resp is None or resp.status_code not in (200, 201):
        print(f"    Upload failed: {resp.status_code if resp else 'no response'}")
        if resp:
            print(f"    Response: {resp.text[:300]}")
        return None
    media = resp.json()
    media_id = media.get("id")
    # Update alt text and caption
    if media_id and (alt_text or caption):
        time.sleep(DELAY)
        update_data = {}
        if alt_text:
            update_data["alt_text"] = alt_text
        if caption:
            update_data["caption"] = caption
        api_call(
            requests.post,
            f"{WP_BASE}/media/{media_id}",
            headers=WP_HEADERS,
            auth=WP_AUTH,
            json=update_data
        )
    return media_id


def set_featured_image(post_id, media_id):
    """Set the featured image on a post."""
    resp = api_call(
        requests.post,
        f"{WP_BASE}/posts/{post_id}",
        headers=WP_HEADERS,
        auth=WP_AUTH,
        json={"featured_media": media_id}
    )
    if resp is None or resp.status_code != 200:
        print(f"    Set featured image failed: {resp.status_code if resp else 'no response'}")
        if resp:
            print(f"    Response: {resp.text[:300]}")
        return False
    return True


def main():
    print("=" * 70)
    print("Phase 24D - Featured Images Audit & Fix for PetHub Online")
    print(f"Started: {datetime.utcnow().isoformat()}Z")
    print("=" * 70)

    # Results tracking
    results = {
        "started": datetime.utcnow().isoformat() + "Z",
        "total_posts": 0,
        "already_have_image": 0,
        "missing_image": 0,
        "fixed": 0,
        "failed": 0,
        "skipped": 0,
        "details": []
    }

    # Step 1: Fetch all published posts
    print("\n[1] Fetching all published posts...")
    posts = fetch_all_posts()
    results["total_posts"] = len(posts)
    print(f"  Total published posts: {len(posts)}")

    # Step 2: Identify posts missing featured images
    missing = [p for p in posts if p.get("featured_media", 0) == 0]
    have = [p for p in posts if p.get("featured_media", 0) > 0]
    results["already_have_image"] = len(have)
    results["missing_image"] = len(missing)

    print(f"\n[2] Audit Results:")
    print(f"  Posts WITH featured image: {len(have)}")
    print(f"  Posts MISSING featured image: {len(missing)}")

    if not missing:
        print("\n  All posts already have featured images! Nothing to fix.")
        results["completed"] = datetime.utcnow().isoformat() + "Z"
        with open(RESULTS_PATH, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n  Results saved to {RESULTS_PATH}")
        return

    # Step 3: Fix each post missing a featured image
    print(f"\n[3] Fixing {len(missing)} posts...")
    for idx, post in enumerate(missing, 1):
        post_id = post["id"]
        title = post["title"]["rendered"] if isinstance(post["title"], dict) else post["title"]
        print(f"\n  [{idx}/{len(missing)}] Post #{post_id}: {title}")

        detail = {
            "post_id": post_id,
            "title": title,
            "status": "pending",
            "search_query": None,
            "pexels_photo": None,
            "media_id": None
        }

        # 3a: Generate search query
        query = make_search_query(title)
        detail["search_query"] = query
        print(f"    Search query: '{query}'")
        time.sleep(DELAY)

        # 3b: Search Pexels
        photo = search_pexels(query)
        if not photo:
            # Try a broader fallback query
            fallback = query.split()
            if len(fallback) > 2:
                fallback_query = " ".join(fallback[:2])
                print(f"    Retrying with fallback query: '{fallback_query}'")
                time.sleep(DELAY)
                photo = search_pexels(fallback_query)
            if not photo:
                # Last resort: generic pet image
                print(f"    Using generic 'happy pet' fallback")
                time.sleep(DELAY)
                photo = search_pexels("happy pet animal")
            if not photo:
                detail["status"] = "failed"
                detail["error"] = "No Pexels results found"
                results["failed"] += 1
                results["details"].append(detail)
                print(f"    FAILED: No image found")
                continue

        detail["pexels_photo"] = {
            "photographer": photo["photographer"],
            "pexels_url": photo["pexels_url"]
        }
        print(f"    Found image by {photo['photographer']}")
        time.sleep(DELAY)

        # 3c: Download the image
        print(f"    Downloading image...")
        image_data = download_image(photo["url"])
        if not image_data:
            detail["status"] = "failed"
            detail["error"] = "Image download failed"
            results["failed"] += 1
            results["details"].append(detail)
            print(f"    FAILED: Download failed")
            continue
        print(f"    Downloaded {len(image_data) / 1024:.1f} KB")
        time.sleep(DELAY)

        # 3d: Upload to WordPress
        # Create a sanitized filename
        safe_title = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")[:50]
        filename = f"pethub-{safe_title}.jpg"
        alt_text = f"{title} - PetHub Online"
        caption = f"Photo by {photo['photographer']} on Pexels"

        print(f"    Uploading to WordPress as '{filename}'...")
        media_id = upload_to_wordpress(image_data, filename, alt_text, caption)
        if not media_id:
            detail["status"] = "failed"
            detail["error"] = "WordPress upload failed"
            results["failed"] += 1
            results["details"].append(detail)
            print(f"    FAILED: Upload failed")
            continue
        detail["media_id"] = media_id
        print(f"    Uploaded as media #{media_id}")
        time.sleep(DELAY)

        # 3e: Set as featured image
        print(f"    Setting featured image on post #{post_id}...")
        success = set_featured_image(post_id, media_id)
        if success:
            detail["status"] = "fixed"
            results["fixed"] += 1
            print(f"    SUCCESS: Featured image set!")
        else:
            detail["status"] = "failed"
            detail["error"] = "Failed to set featured image"
            results["failed"] += 1
            print(f"    FAILED: Could not set featured image")

        results["details"].append(detail)
        time.sleep(DELAY)

        # Save intermediate results every 5 posts
        if idx % 5 == 0:
            with open(RESULTS_PATH, "w") as f:
                json.dump(results, f, indent=2)
            print(f"    [Checkpoint saved]")

    # Final summary
    results["completed"] = datetime.utcnow().isoformat() + "Z"
    coverage = ((results["already_have_image"] + results["fixed"]) / results["total_posts"] * 100) if results["total_posts"] > 0 else 0

    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"  Total posts:          {results['total_posts']}")
    print(f"  Already had image:    {results['already_have_image']}")
    print(f"  Were missing:         {results['missing_image']}")
    print(f"  Fixed:                {results['fixed']}")
    print(f"  Failed:               {results['failed']}")
    print(f"  Coverage:             {coverage:.1f}%")
    results["final_coverage_pct"] = round(coverage, 1)

    # Save results
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
