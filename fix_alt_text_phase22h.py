#!/usr/bin/env python3
"""
Phase 22H - Fix all remaining images missing alt text on PetHub Online.
Scans all media items, generates descriptive alt text, and updates via WP REST API.
"""

import sys
import requests
import json
import time
import re
import os
from datetime import datetime
from urllib.parse import unquote

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# ── Configuration ──────────────────────────────────────────────────────────────
WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
HEADERS = {"Accept-Encoding": "gzip, deflate"}
RESULTS_PATH = "/var/lib/freelancer/projects/40416335/phase22h_alt_text_results.json"
DELAY_BETWEEN_UPDATES = 1  # seconds
RETRY_WAIT = 10  # seconds on 429


# ── Helper Functions ───────────────────────────────────────────────────────────

def clean_filename(filename):
    """Extract meaningful words from a filename."""
    # Remove extension
    name = os.path.splitext(filename)[0]
    # URL decode
    name = unquote(name)
    # Remove common prefixes like dates, IDs, dimensions
    name = re.sub(r'^\d{4}[-/]\d{2}[-/]\d{2}[-_]?', '', name)
    name = re.sub(r'[-_]\d+x\d+$', '', name)
    name = re.sub(r'^IMG[-_]\d+', '', name)
    name = re.sub(r'^DSC[-_]?\d+', '', name)
    name = re.sub(r'^\d+[-_]', '', name)
    # Replace separators with spaces
    name = re.sub(r'[-_]+', ' ', name)
    # Remove excess whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def clean_title(title):
    """Clean up a WordPress media title."""
    if not title:
        return ""
    # Strip HTML entities and tags
    title = re.sub(r'<[^>]+>', '', title)
    title = re.sub(r'&[a-zA-Z]+;', ' ', title)
    # Remove trailing dimensions like 1200x800
    title = re.sub(r'\s*\d+\s*[xX]\s*\d+\s*$', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title


def generate_alt_text(media_item, post_title=None):
    """
    Generate descriptive alt text from available metadata.
    Priority: post context > title > filename
    """
    title = clean_title(media_item.get("title", {}).get("rendered", ""))
    filename = media_item.get("source_url", "").split("/")[-1] if media_item.get("source_url") else ""
    filename_words = clean_filename(filename)
    caption = ""
    if media_item.get("caption", {}).get("rendered"):
        caption = re.sub(r'<[^>]+>', '', media_item["caption"]["rendered"]).strip()

    # Determine the best subject description
    subject = ""
    context = ""

    # Use caption if available and meaningful
    if caption and len(caption) > 5 and caption.lower() not in ("image", "photo", "picture", "untitled"):
        subject = caption

    # Use title if it's meaningful
    elif title and len(title) > 2 and title.lower() not in ("image", "photo", "picture", "untitled", "img"):
        subject = title

    # Fall back to filename
    elif filename_words and len(filename_words) > 2:
        subject = filename_words

    # If we have a post title, use it as context
    if post_title:
        post_title_clean = re.sub(r'<[^>]+>', '', post_title).strip()
        if post_title_clean and post_title_clean.lower() != subject.lower():
            context = post_title_clean

    # Build alt text
    if subject and context:
        alt = f"{subject.capitalize()} - {context}"
    elif subject:
        alt = subject.capitalize()
    elif context:
        alt = f"Image for {context}"
    else:
        # Last resort: use any available info
        mime = media_item.get("mime_type", "image/jpeg")
        media_id = media_item.get("id", "unknown")
        alt = f"Pet product image {media_id}"

    # Ensure pet-relevant context if none detected
    pet_keywords = ["pet", "dog", "cat", "puppy", "kitten", "animal", "food", "treat",
                     "toy", "collar", "leash", "bowl", "bed", "groom", "vet", "health",
                     "nutrition", "supplement", "accessory", "aquarium", "fish", "bird",
                     "hamster", "rabbit", "reptile", "pethub"]
    has_pet_context = any(kw in alt.lower() for kw in pet_keywords)

    if not has_pet_context and context:
        # Check if context has pet keywords
        if any(kw in context.lower() for kw in pet_keywords):
            has_pet_context = True

    # Trim to 125 characters max
    if len(alt) > 125:
        alt = alt[:122] + "..."

    return alt


def fetch_all_media():
    """Fetch all media items from WordPress, paginating through all pages."""
    all_media = []
    page = 1
    per_page = 100

    while True:
        print(f"  Fetching media page {page}...")
        try:
            resp = requests.get(
                f"{WP_BASE}/media",
                params={"per_page": per_page, "page": page},
                auth=AUTH,
                headers=HEADERS,
                timeout=30
            )
            if resp.status_code == 400:
                # Past last page
                break
            resp.raise_for_status()
            items = resp.json()
            if not items:
                break
            all_media.extend(items)
            total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
            total_items = int(resp.headers.get("X-WP-Total", len(all_media)))
            print(f"    Got {len(items)} items (total so far: {len(all_media)}/{total_items})")
            if page >= total_pages:
                break
            page += 1
            time.sleep(0.5)
        except requests.exceptions.RequestException as e:
            print(f"    ERROR fetching page {page}: {e}")
            if "429" in str(e):
                print(f"    Rate limited, waiting {RETRY_WAIT}s...")
                time.sleep(RETRY_WAIT)
                continue
            break

    return all_media


def fetch_post_title(post_id):
    """Fetch a post's title by ID."""
    if not post_id or post_id == 0:
        return None
    try:
        resp = requests.get(
            f"{WP_BASE}/posts/{post_id}",
            auth=AUTH,
            headers=HEADERS,
            timeout=15
        )
        if resp.status_code == 200:
            return resp.json().get("title", {}).get("rendered", "")
        # Try pages endpoint
        resp = requests.get(
            f"{WP_BASE}/pages/{post_id}",
            auth=AUTH,
            headers=HEADERS,
            timeout=15
        )
        if resp.status_code == 200:
            return resp.json().get("title", {}).get("rendered", "")
    except:
        pass
    return None


def update_alt_text(media_id, alt_text):
    """Update the alt_text for a media item. Returns (success, error_msg)."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                f"{WP_BASE}/media/{media_id}",
                json={"alt_text": alt_text},
                auth=AUTH,
                headers=HEADERS,
                timeout=20
            )
            if resp.status_code == 429:
                print(f"    Rate limited on media {media_id}, waiting {RETRY_WAIT}s...")
                time.sleep(RETRY_WAIT)
                continue
            if resp.status_code in (200, 201):
                return True, None
            else:
                return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(3)
                continue
            return False, str(e)
    return False, "Max retries exceeded"


# ── Main Execution ─────────────────────────────────────────────────────────────

def main():
    start_time = datetime.now()
    print("=" * 70)
    print("Phase 22H - PetHub Online Alt Text Fix")
    print(f"Started: {start_time.isoformat()}")
    print("=" * 70)

    # Step 1: SCAN - Fetch all media
    print("\n[1/4] SCANNING all media items...")
    all_media = fetch_all_media()
    total_scanned = len(all_media)
    print(f"\n  Total media items found: {total_scanned}")

    # Step 2: Identify missing alt text
    print("\n[2/4] IDENTIFYING media with missing alt text...")
    missing_alt = []
    for item in all_media:
        alt = item.get("alt_text", "").strip()
        if not alt:
            info = {
                "id": item["id"],
                "title": item.get("title", {}).get("rendered", ""),
                "filename": item.get("source_url", "").split("/")[-1] if item.get("source_url") else "unknown",
                "source_url": item.get("source_url", ""),
                "post": item.get("post", 0),
                "mime_type": item.get("mime_type", ""),
                "caption": re.sub(r'<[^>]+>', '', item.get("caption", {}).get("rendered", "")).strip(),
                "_raw": item
            }
            missing_alt.append(info)

    print(f"  Media with missing alt text: {len(missing_alt)}")
    print(f"  Media with existing alt text: {total_scanned - len(missing_alt)}")

    if not missing_alt:
        print("\n  All media items already have alt text. Nothing to fix!")
        results = {
            "phase": "22H",
            "timestamp": start_time.isoformat(),
            "total_scanned": total_scanned,
            "missing_alt_text_found": 0,
            "fixed_count": 0,
            "errors": [],
            "samples": []
        }
        with open(RESULTS_PATH, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n  Results saved to {RESULTS_PATH}")
        return

    # Log first 10 missing items
    print("\n  Sample of media missing alt text:")
    for item in missing_alt[:10]:
        print(f"    ID: {item['id']} | Title: {item['title'][:50]} | File: {item['filename'][:40]} | Post: {item['post']}")

    # Step 3: GENERATE & UPDATE alt text
    print(f"\n[3/4] GENERATING alt text and UPDATING {len(missing_alt)} media items...")

    # Pre-fetch post titles for associated posts
    post_ids = set(item["post"] for item in missing_alt if item["post"] and item["post"] != 0)
    post_titles = {}
    if post_ids:
        print(f"  Pre-fetching titles for {len(post_ids)} associated posts...")
        for pid in post_ids:
            title = fetch_post_title(pid)
            if title:
                post_titles[pid] = title
            time.sleep(0.3)
        print(f"  Fetched {len(post_titles)} post titles")

    fixed_count = 0
    errors = []
    samples = []

    for idx, item in enumerate(missing_alt):
        media_id = item["id"]
        post_title = post_titles.get(item["post"])

        # Generate alt text
        alt_text = generate_alt_text(item["_raw"], post_title)

        # Update via API
        success, error_msg = update_alt_text(media_id, alt_text)

        if success:
            fixed_count += 1
            if len(samples) < 20:
                samples.append({
                    "id": media_id,
                    "title": item["title"][:60],
                    "filename": item["filename"][:40],
                    "alt_text_generated": alt_text,
                    "post_title": post_title[:60] if post_title else None
                })
        else:
            errors.append({
                "id": media_id,
                "title": item["title"][:60],
                "error": error_msg
            })

        # Progress logging every 20 items
        if (idx + 1) % 20 == 0 or (idx + 1) == len(missing_alt):
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"  Progress: {idx + 1}/{len(missing_alt)} | Fixed: {fixed_count} | Errors: {len(errors)} | Elapsed: {elapsed:.0f}s")

        # Delay between updates
        time.sleep(DELAY_BETWEEN_UPDATES)

    # Step 4: REPORT
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"\n[4/4] GENERATING REPORT...")
    print("=" * 70)
    print(f"  Total scanned:        {total_scanned}")
    print(f"  Missing alt text:     {len(missing_alt)}")
    print(f"  Successfully fixed:   {fixed_count}")
    print(f"  Errors:               {len(errors)}")
    print(f"  Duration:             {duration:.0f}s")
    print(f"  Success rate:         {(fixed_count/len(missing_alt)*100):.1f}%")
    print("=" * 70)

    if errors:
        print(f"\n  Errors encountered:")
        for err in errors[:10]:
            print(f"    ID {err['id']}: {err['error'][:80]}")

    print(f"\n  Sample alt texts generated:")
    for s in samples[:10]:
        print(f"    ID {s['id']}: \"{s['alt_text_generated']}\"")

    results = {
        "phase": "22H",
        "timestamp_start": start_time.isoformat(),
        "timestamp_end": end_time.isoformat(),
        "duration_seconds": round(duration, 1),
        "total_scanned": total_scanned,
        "already_have_alt_text": total_scanned - len(missing_alt),
        "missing_alt_text_found": len(missing_alt),
        "fixed_count": fixed_count,
        "error_count": len(errors),
        "success_rate_percent": round(fixed_count / len(missing_alt) * 100, 1) if missing_alt else 100,
        "errors": errors,
        "samples": samples
    }

    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to {RESULTS_PATH}")
    print(f"\n  Phase 22H complete.")


if __name__ == "__main__":
    main()
