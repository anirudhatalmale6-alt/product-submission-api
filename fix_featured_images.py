#!/usr/bin/env python3
"""
Fix Featured Images - Phase 19 Image Compliance
Adds featured images to all 224 posts missing them on pethubonline.com
Uses Pexels API for sourcing relevant landscape images.
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
import base64
import gzip
import io
from datetime import datetime, timezone

# ── Configuration ──────────────────────────────────────────────────────────
WP_API = "https://pethubonline.com/wp-json/wp/v2"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
PEXELS_KEY = "dmGyKrZqTlwukxWzOK1EkH4jbEv9EaIDpLGj7eL5MZ07bl6AR9OEoHlB"

BASE_DIR = "/var/lib/freelancer/projects/40416335"
AUDIT_FILE = os.path.join(BASE_DIR, "phase19_image_audit.json")
RESULTS_FILE = os.path.join(BASE_DIR, "featured_image_fix_results.json")

AUTH_STRING = base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()
DELAY_BETWEEN_POSTS = 2  # seconds

# ── Category-level fallback search terms ───────────────────────────────────
CATEGORY_QUERIES = {
    "Fish Supplies": ["aquarium fish", "tropical fish tank"],
    "Cat Toys": ["cat playing", "cat toy"],
    "Indoor Cats": ["indoor cat", "cat home"],
    "Dog Beds": ["dog bed", "dog sleeping"],
    "Puppy Care": ["puppy", "cute puppy"],
    "Pet Care": ["pet care", "pet owner"],
    "Dog Supplies": ["dog supplies", "dog owner"],
    "Dog Health": ["dog health", "veterinarian dog"],
    "Cat Supplies": ["cat supplies", "cat owner"],
    "Enrichment Activities": ["pet enrichment", "cat playing"],
    "Dog Accessories": ["dog accessories", "dog collar"],
    "Dog Toys": ["dog toy", "dog playing fetch"],
    "Dog Care": ["dog grooming", "dog care"],
    "Dog Food": ["dog food bowl", "dog eating"],
    "Training Supplies": ["dog training", "pet training"],
    "Dog Harnesses": ["dog harness", "dog walking"],
    "Health &amp; Wellness": ["pet wellness", "veterinarian"],
    "Health & Wellness": ["pet wellness", "veterinarian"],
    "Pet Health": ["pet health", "veterinarian"],
    "Uncategorized": ["happy pet", "pet owner"],
}

# ── Stop words for title-based query extraction ────────────────────────────
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "need", "must",
    "your", "our", "their", "his", "her", "its", "my", "this", "that",
    "these", "those", "what", "which", "who", "whom", "how", "when",
    "where", "why", "all", "each", "every", "both", "few", "more", "most",
    "other", "some", "such", "no", "not", "only", "own", "same", "so",
    "than", "too", "very", "just", "about", "above", "after", "again",
    "also", "any", "because", "before", "between", "during", "into",
    "through", "under", "until", "up", "while", "guide", "uk", "best",
    "top", "complete", "ultimate", "essential", "tips", "review", "reviews",
    "buying", "choose", "choosing", "right", "find", "finding", "keep",
    "keeping", "help", "new", "2024", "2025", "2026",
}

# Pet-related high-value terms to prioritize
PET_TERMS = {
    "dog", "cat", "puppy", "kitten", "fish", "aquarium", "pet", "canine",
    "feline", "goldfish", "betta", "tropical", "hamster", "rabbit", "bird",
    "parrot", "turtle", "reptile", "guinea", "ferret",
}

PRODUCT_TERMS = {
    "bed", "toy", "toys", "food", "bowl", "collar", "leash", "harness",
    "crate", "kennel", "brush", "shampoo", "treat", "treats", "feeder",
    "fountain", "litter", "scratching", "post", "carrier", "cage", "tank",
    "filter", "heater", "supplement", "vitamin", "chew", "ball", "puzzle",
    "training", "pad", "gate", "fence", "jacket", "coat", "boots",
    "grooming", "nail", "clipper", "dental",
}


USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"


def make_request(url, method="GET", data=None, headers=None, content_type=None):
    """Make an HTTP request with gzip support and error handling."""
    if headers is None:
        headers = {}
    headers["Accept-Encoding"] = "gzip, deflate"
    headers["User-Agent"] = USER_AGENT

    if data is not None and isinstance(data, dict):
        data = json.dumps(data).encode("utf-8")
        if content_type is None:
            content_type = "application/json"

    if content_type:
        headers["Content-Type"] = content_type

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        body = e.read()
        if e.headers.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
        raise Exception(f"HTTP {e.code}: {body.decode('utf-8', errors='replace')[:500]}")


def make_raw_request(url, headers=None):
    """Download raw bytes (for images)."""
    if headers is None:
        headers = {}
    headers["Accept-Encoding"] = "gzip, deflate"
    headers["User-Agent"] = USER_AGENT
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return raw


def extract_search_query(title, category):
    """Extract 2-3 key search terms from a post title."""
    # Clean the title
    clean = re.sub(r"[^a-zA-Z0-9\s]", " ", title.lower())
    words = clean.split()

    # Separate pet terms and product terms found in title
    found_pet = [w for w in words if w in PET_TERMS]
    found_product = [w for w in words if w in PRODUCT_TERMS]
    found_other = [w for w in words if w not in STOP_WORDS and w not in PET_TERMS
                   and w not in PRODUCT_TERMS and len(w) > 2]

    # Build query: prioritise pet term + product/descriptive term
    query_parts = []
    if found_pet:
        query_parts.append(found_pet[0])
    if found_product:
        query_parts.append(found_product[0])
    # Fill up to 3 terms with other meaningful words
    for w in found_other:
        if len(query_parts) >= 3:
            break
        if w not in query_parts:
            query_parts.append(w)

    # If we still have fewer than 2 terms, add more pet/product terms
    for w in found_pet[1:] + found_product[1:]:
        if len(query_parts) >= 3:
            break
        if w not in query_parts:
            query_parts.append(w)

    if len(query_parts) >= 2:
        return " ".join(query_parts)

    # Fallback: use first few non-stop words
    fallback = [w for w in words if w not in STOP_WORDS and len(w) > 2][:3]
    if fallback:
        return " ".join(fallback)

    return None


def search_pexels(query, api_key):
    """Search Pexels for a landscape image. Returns (image_url, photographer) or (None, None)."""
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.pexels.com/v1/search?query={encoded_query}&orientation=landscape&per_page=1"
    headers = {
        "Authorization": api_key,
        "Accept-Encoding": "gzip, deflate",
        "User-Agent": USER_AGENT,
    }

    try:
        data = make_request(url, headers=headers)
        photos = data.get("photos", [])
        if photos:
            photo = photos[0]
            img_url = photo["src"]["medium"]
            photographer = photo.get("photographer", "Pexels")
            return img_url, photographer
    except Exception as e:
        print(f"    [Pexels error] {e}", flush=True)
    return None, None


def upload_to_wordpress(image_data, filename, alt_text):
    """Upload image to WordPress media library. Returns media ID or None."""
    url = f"{WP_API}/media"
    headers = {
        "Authorization": f"Basic {AUTH_STRING}",
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "image/jpeg",
        "Accept-Encoding": "gzip, deflate",
        "User-Agent": USER_AGENT,
    }

    req = urllib.request.Request(url, data=image_data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            result = json.loads(raw)
            media_id = result.get("id")

            # Update alt text
            if media_id and alt_text:
                update_url = f"{WP_API}/media/{media_id}"
                update_data = json.dumps({"alt_text": alt_text}).encode("utf-8")
                update_headers = {
                    "Authorization": f"Basic {AUTH_STRING}",
                    "Content-Type": "application/json",
                    "Accept-Encoding": "gzip, deflate",
                    "User-Agent": USER_AGENT,
                }
                update_req = urllib.request.Request(
                    update_url, data=update_data, headers=update_headers, method="POST"
                )
                urllib.request.urlopen(update_req, timeout=30)

            return media_id
    except urllib.error.HTTPError as e:
        body = e.read()
        if e.headers.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
        print(f"    [WP upload error] HTTP {e.code}: {body.decode('utf-8', errors='replace')[:300]}", flush=True)
    except Exception as e:
        print(f"    [WP upload error] {e}", flush=True)
    return None


def set_featured_image(post_id, media_id):
    """Set the featured_media for a WordPress post. Returns True/False."""
    url = f"{WP_API}/posts/{post_id}"
    data = json.dumps({"featured_media": media_id}).encode("utf-8")
    headers = {
        "Authorization": f"Basic {AUTH_STRING}",
        "Content-Type": "application/json",
        "Accept-Encoding": "gzip, deflate",
        "User-Agent": USER_AGENT,
    }
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            result = json.loads(raw)
            return result.get("featured_media") == media_id
    except urllib.error.HTTPError as e:
        body = e.read()
        if e.headers.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
        print(f"    [WP set featured error] HTTP {e.code}: {body.decode('utf-8', errors='replace')[:300]}", flush=True)
    except Exception as e:
        print(f"    [WP set featured error] {e}", flush=True)
    return False


def generate_alt_text(title):
    """Generate descriptive alt text from post title."""
    # Remove common suffixes and clean up
    alt = re.sub(r"\s*[-|:]\s*(Guide|Review|Tips|Best|Top|UK|2024|2025|2026).*$", "", title, flags=re.IGNORECASE)
    alt = alt.strip()
    if not alt:
        alt = title
    return alt


def sanitize_filename(title):
    """Create a URL-safe filename from a post title."""
    clean = re.sub(r"[^a-zA-Z0-9\s-]", "", title.lower())
    clean = re.sub(r"\s+", "-", clean.strip())
    clean = clean[:60]
    return f"{clean}.jpg"


def main():
    start_time = datetime.now(timezone.utc)
    print(f"{'='*70}", flush=True)
    print(f"Phase 19 Featured Image Fix - pethubonline.com", flush=True)
    print(f"Started: {start_time.isoformat()}", flush=True)
    print(f"{'='*70}\n", flush=True)

    # Load the audit data
    with open(AUDIT_FILE) as f:
        audit = json.load(f)

    posts = audit["missing_featured"]
    total = len(posts)
    print(f"Loaded {total} posts missing featured images\n", flush=True)

    # Test WordPress connectivity
    print("Testing WordPress API connectivity...", flush=True)
    try:
        test_url = f"{WP_API}/posts?per_page=1&_fields=id"
        test_headers = {
            "Authorization": f"Basic {AUTH_STRING}",
            "Accept-Encoding": "gzip, deflate",
        }
        make_request(test_url, headers=test_headers)
        print("  WordPress API: OK\n", flush=True)
    except Exception as e:
        print(f"  WordPress API FAILED: {e}", flush=True)
        print("Aborting.", flush=True)
        sys.exit(1)

    # Test Pexels API
    print("Testing Pexels API connectivity...", flush=True)
    try:
        test_url = "https://api.pexels.com/v1/search?query=cat&per_page=1"
        test_headers = {
            "Authorization": PEXELS_KEY,
            "Accept-Encoding": "gzip, deflate",
        }
        result = make_request(test_url, headers=test_headers)
        if result.get("photos"):
            print("  Pexels API: OK\n", flush=True)
        else:
            print("  Pexels API returned no results for test query", flush=True)
    except Exception as e:
        print(f"  Pexels API FAILED: {e}", flush=True)
        print("Aborting.", flush=True)
        sys.exit(1)

    # Process each post
    results = {
        "started": start_time.isoformat(),
        "total_posts": total,
        "success": [],
        "failed": [],
        "skipped": [],
    }

    success_count = 0
    fail_count = 0
    skip_count = 0

    for idx, post in enumerate(posts, 1):
        post_id = post["id"]
        title = post["title"]
        category = post["category"]

        if idx % 20 == 1 or idx == 1:
            print(f"\n{'─'*70}", flush=True)
            print(f"  Progress: {idx-1}/{total} done | {success_count} OK | {fail_count} failed | {skip_count} skipped", flush=True)
            print(f"{'─'*70}\n", flush=True)

        print(f"[{idx}/{total}] Post {post_id}: {title[:65]}...", flush=True) if len(title) > 65 else print(f"[{idx}/{total}] Post {post_id}: {title}", flush=True)

        # Step 1: Generate search query from title
        query = extract_search_query(title, category)
        print(f"  Search query: \"{query}\"", flush=True)

        # Step 2: Search Pexels
        img_url = None
        photographer = None

        if query:
            img_url, photographer = search_pexels(query, PEXELS_KEY)

        # Fallback to category-level query if no results
        if not img_url:
            cat_queries = CATEGORY_QUERIES.get(category, ["pet", "animal"])
            for cq in cat_queries:
                print(f"  Fallback search: \"{cq}\"", flush=True)
                img_url, photographer = search_pexels(cq, PEXELS_KEY)
                if img_url:
                    break

        # Ultimate fallback
        if not img_url:
            print(f"  Trying ultimate fallback: \"pet animal\"", flush=True)
            img_url, photographer = search_pexels("pet animal", PEXELS_KEY)

        if not img_url:
            print(f"  SKIP: No image found for any query", flush=True)
            skip_count += 1
            results["skipped"].append({
                "id": post_id,
                "title": title,
                "reason": "No Pexels image found",
            })
            time.sleep(DELAY_BETWEEN_POSTS)
            continue

        # Step 3: Download the image
        print(f"  Downloading from Pexels (by {photographer})...", flush=True)
        try:
            image_data = make_raw_request(img_url)
            print(f"  Downloaded {len(image_data):,} bytes", flush=True)
        except Exception as e:
            print(f"  FAIL: Download error: {e}", flush=True)
            fail_count += 1
            results["failed"].append({
                "id": post_id,
                "title": title,
                "reason": f"Image download failed: {str(e)[:200]}",
            })
            time.sleep(DELAY_BETWEEN_POSTS)
            continue

        # Step 4: Upload to WordPress
        filename = sanitize_filename(title)
        alt_text = generate_alt_text(title)
        print(f"  Uploading to WordPress as \"{filename}\"...", flush=True)

        media_id = upload_to_wordpress(image_data, filename, alt_text)
        if not media_id:
            print(f"  FAIL: Upload to WordPress failed", flush=True)
            fail_count += 1
            results["failed"].append({
                "id": post_id,
                "title": title,
                "reason": "WordPress media upload failed",
            })
            time.sleep(DELAY_BETWEEN_POSTS)
            continue

        print(f"  Uploaded: media ID {media_id}", flush=True)

        # Step 5: Set as featured image
        print(f"  Setting featured_media on post {post_id}...", flush=True)
        success = set_featured_image(post_id, media_id)

        if success:
            print(f"  SUCCESS: Featured image set!", flush=True)
            success_count += 1
            results["success"].append({
                "id": post_id,
                "title": title,
                "media_id": media_id,
                "photographer": photographer,
                "pexels_url": img_url,
            })
        else:
            print(f"  FAIL: Could not set featured_media", flush=True)
            fail_count += 1
            results["failed"].append({
                "id": post_id,
                "title": title,
                "media_id": media_id,
                "reason": "Failed to set featured_media on post",
            })

        # Rate limiting
        time.sleep(DELAY_BETWEEN_POSTS)

    # Final summary
    end_time = datetime.now(timezone.utc)
    elapsed = (end_time - start_time).total_seconds()

    results["completed"] = end_time.isoformat()
    results["elapsed_seconds"] = round(elapsed, 1)
    results["summary"] = {
        "total": total,
        "success": success_count,
        "failed": fail_count,
        "skipped": skip_count,
    }

    # Save results
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*70}", flush=True)
    print(f"COMPLETED - Phase 19 Featured Image Fix", flush=True)
    print(f"{'='*70}", flush=True)
    print(f"Total posts:  {total}", flush=True)
    print(f"Success:      {success_count}", flush=True)
    print(f"Failed:       {fail_count}", flush=True)
    print(f"Skipped:      {skip_count}", flush=True)
    print(f"Duration:     {elapsed:.0f}s ({elapsed/60:.1f} min)", flush=True)
    print(f"Results:      {RESULTS_FILE}", flush=True)
    print(f"{'='*70}", flush=True)


if __name__ == "__main__":
    main()
