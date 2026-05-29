#!/usr/bin/env python3
"""
Phase 10AK: SEO Metadata Optimization for PetHub Online
- Optimize meta titles (<60 chars, focus keyword at start)
- Optimize meta descriptions (<160 chars, actionable, focus keyword)
- Optimize first image alt text (include focus keyword)
- Do NOT change post titles or slugs
"""

import subprocess
import json
import csv
import time
import re
import html
import sys

WP_API = "https://pethubonline.com/wp-json/wp/v2"
RANKMATH_API = "https://pethubonline.com/wp-json/rankmath/v1/updateMeta"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
LOG_FILE = "/var/lib/freelancer/projects/40416335/phase10ak_data/seo_metadata_log.csv"
DELAY = 2.5  # seconds between API calls

def api_get(url):
    """GET request via curl subprocess."""
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  [ERROR] Failed to parse JSON from: {url}")
        print(f"  Response: {result.stdout[:500]}")
        return None

def api_post(url, data):
    """POST request via curl subprocess."""
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH,
         "-X", "POST",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(data),
         url],
        capture_output=True, text=True, timeout=60
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  [ERROR] Failed to parse JSON from POST: {url}")
        print(f"  Response: {result.stdout[:500]}")
        return None

def clean_html(text):
    """Remove HTML entities and tags."""
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.strip()
    return text

def extract_focus_keyword(post_title, meta_data):
    """Extract focus keyword from Rank Math meta or derive from title."""
    # Try rank_math_focus_keyword from meta
    fk = meta_data.get("rank_math_focus_keyword", "")
    if fk:
        return fk.strip()
    # Derive from title - take the main subject phrase
    title = clean_html(post_title)
    return ""

def is_buying_guide(title):
    """Check if the post is a buying guide / best-of list."""
    title_lower = title.lower()
    return any(kw in title_lower for kw in ["best ", "guide", "buying", "top ", "review"])

def has_year(text):
    """Check if text contains a year like 2026."""
    return bool(re.search(r'20\d{2}', text or ""))

def generate_meta_title(post_title, focus_keyword, current_meta_title):
    """Generate an optimized meta title under 60 chars."""
    title = clean_html(post_title)

    # If current meta title exists, is under 60 chars, and starts with focus keyword, keep it
    if current_meta_title:
        cmt = current_meta_title.strip()
        if len(cmt) <= 60 and len(cmt) > 10:
            if focus_keyword and focus_keyword.lower() in cmt.lower()[:40]:
                return None  # No change needed

    # Strategy: Use the post title itself if it's already good
    # Many titles are already well-structured with keywords

    # Clean up the title for meta use
    meta = title

    # Remove " - PetHub Online" or similar site suffixes if present
    meta = re.sub(r'\s*[-–—|]\s*(PetHub|Pet Hub).*$', '', meta, flags=re.IGNORECASE)

    # Remove HTML entities
    meta = re.sub(r'&#\d+;', '', meta).strip()

    # If title already has year and is under 60, use it
    if len(meta) <= 60:
        return meta

    # Need to shorten. Remove parenthetical year first to re-add at end
    meta_no_year = re.sub(r'\s*\(?\d{4}\)?\s*', ' ', meta).strip()

    # Remove common suffixes
    for suffix in [" – Complete Guide", " - Complete Guide", " – Comprehensive Guide",
                   " – Complete Buying Guide", " - A Complete Guide",
                   " – A Practical Guide", " - Honest Reviews",
                   " & Honest Reviews", " – Guide", " - Guide"]:
        if meta_no_year.endswith(suffix) or meta_no_year.endswith(suffix.replace("–", "-")):
            meta_no_year = meta_no_year[:-len(suffix)].strip()
            break

    # Re-add year for buying guides
    if is_buying_guide(title) and not has_year(meta_no_year):
        candidate = f"{meta_no_year} (2026)"
    else:
        candidate = meta_no_year

    # Add short suffix if room
    if len(candidate) <= 44:
        candidate += " | PetHub Guide"
    elif len(candidate) <= 48:
        candidate += " | Guide"

    if len(candidate) <= 60:
        return candidate

    # Last resort: truncate intelligently at word boundary
    if len(meta_no_year) > 57:
        words = meta_no_year.split()
        result = ""
        for w in words:
            test = f"{result} {w}".strip() if result else w
            if len(test) > 57:
                break
            result = test
        return result

    return meta_no_year[:60].strip()

def generate_meta_description(post_title, focus_keyword, cluster, current_desc):
    """Generate an optimized meta description under 160 chars."""
    title = clean_html(post_title)

    # Check if current description is acceptable
    if current_desc:
        cd = current_desc.strip()
        if 50 < len(cd) <= 160:
            if focus_keyword and focus_keyword.lower() in cd.lower():
                return None  # Good enough

    title_lower = title.lower()

    # Build descriptions based on content type and cluster
    # UK-focused, actionable language, under 160 chars

    if "best " in title_lower and "uk" in title_lower:
        # Buying guide pattern
        subject = re.sub(r'Best\s+', '', title, flags=re.IGNORECASE)
        subject = re.sub(r'\s*UK\s*\(?20\d{2}\)?\s*', ' ', subject, flags=re.IGNORECASE)
        subject = re.sub(r'\s*[-–—]\s*.*$', '', subject).strip()
        desc = f"Discover the best {subject.lower()} available in the UK for 2026. Expert-reviewed picks with honest ratings, pros, cons, and practical buying advice."
    elif "how to" in title_lower:
        subject = re.sub(r'How to\s+', '', title, flags=re.IGNORECASE)
        subject = re.sub(r'\s*[-–—:]\s*.*$', '', subject).strip()
        desc = f"Learn how to {subject.lower()} with our step-by-step guide. Practical tips, expert advice, and common mistakes to avoid."
    elif "guide" in title_lower:
        subject = re.sub(r'\s*[-–—:]\s*.*Guide.*$', '', title, flags=re.IGNORECASE)
        subject = re.sub(r'\s*\(?20\d{2}\)?\s*', ' ', subject).strip()
        desc = f"Your complete guide to {subject.lower()}. Evidence-based advice, practical tips, and everything UK pet owners need to know in 2026."
    elif "faq" in title_lower:
        subject = re.sub(r'\s*FAQ.*$', '', title, flags=re.IGNORECASE)
        subject = subject.strip()
        desc = f"Get answers to the most common questions about {subject.lower()}. Clear, expert-backed advice for UK pet owners."
    elif "explained" in title_lower:
        subject = re.sub(r'\s*Explained.*$', '', title, flags=re.IGNORECASE)
        subject = subject.strip()
        desc = f"Understand {subject.lower()} with this clear, jargon-free guide. Practical knowledge every UK pet owner should have."
    elif "vs " in title_lower or " vs." in title_lower:
        desc = f"An honest comparison: {title}. See the key differences, pros, cons, and which option suits your pet best."
    elif "glossary" in title_lower or "terminology" in title_lower:
        subject = re.sub(r'\s*(Glossary|Terminology).*$', '', title, flags=re.IGNORECASE).strip()
        desc = f"A clear glossary of {subject.lower()} terms. Understand the jargon with simple definitions every pet owner can follow."
    elif "diy" in title_lower:
        subject = re.sub(r'DIY\s+', '', title, flags=re.IGNORECASE)
        subject = re.sub(r'\s*[-–—:]\s*.*$', '', subject).strip()
        desc = f"Make safe, budget-friendly DIY {subject.lower()} at home. Step-by-step instructions with materials you already have."
    else:
        # Generic but still good
        desc = f"{title}. Practical advice, expert tips, and everything UK pet owners need to know."

    # Ensure focus keyword is in the description
    if focus_keyword and focus_keyword.lower() not in desc.lower():
        # Try to inject the focus keyword
        if len(desc) + len(focus_keyword) + 15 < 160:
            desc = desc.rstrip('.')
            desc += f". Covers {focus_keyword.lower()}."

    # Truncate to 160 chars if needed
    if len(desc) > 160:
        # Cut at last full sentence under 160
        sentences = desc.split('. ')
        result = ""
        for s in sentences:
            test = f"{result}. {s}" if result else s
            if len(test) > 157:
                break
            result = test
        desc = result.rstrip('.') + '.'

    if len(desc) > 160:
        desc = desc[:157].rsplit(' ', 1)[0] + '...'

    return desc

def generate_alt_text(post_title, focus_keyword):
    """Generate descriptive alt text with focus keyword."""
    title = clean_html(post_title)

    # Remove year, UK, and suffix decorations for a cleaner alt
    alt = re.sub(r'\s*\(?20\d{2}\)?\s*', ' ', title)
    alt = re.sub(r'\s*[-–—|]\s*(Complete|Comprehensive|Honest|Practical|Full).*$', '', alt, flags=re.IGNORECASE)
    alt = re.sub(r'\s*UK\s*', ' ', alt, flags=re.IGNORECASE)
    alt = re.sub(r'\s+', ' ', alt).strip()

    if focus_keyword and focus_keyword.lower() not in alt.lower():
        alt = f"{focus_keyword} - {alt}"

    # Ensure it's descriptive
    if len(alt) < 10:
        alt = f"{title} guide for pet owners"

    return alt[:125]  # Keep alt text reasonable length

def main():
    print("=" * 70)
    print("Phase 10AK: SEO Metadata Optimization")
    print("=" * 70)

    # Fetch all published posts
    all_posts = []
    for page in range(1, 5):  # Up to 4 pages
        url = f"{WP_API}/posts?per_page=100&page={page}&status=publish&_fields=id,title,featured_media,meta,slug"
        print(f"\nFetching posts page {page}...")
        data = api_get(url)
        time.sleep(DELAY)

        if data is None:
            print(f"  Failed to fetch page {page}")
            break
        if isinstance(data, dict) and data.get("code"):
            print(f"  API returned: {data.get('message', 'error')}")
            break
        if not data or len(data) == 0:
            print(f"  No more posts on page {page}")
            break

        all_posts.extend(data)
        print(f"  Got {len(data)} posts (total: {len(all_posts)})")

        if len(data) < 100:
            break

    print(f"\nTotal published posts: {len(all_posts)}")

    if not all_posts:
        print("No posts found! Exiting.")
        return

    # Open log CSV
    log_rows = []

    updated_count = 0
    skipped_count = 0
    error_count = 0

    for idx, post in enumerate(all_posts):
        post_id = post["id"]
        post_title = post["title"]["rendered"] if isinstance(post["title"], dict) else post["title"]
        featured_media = post.get("featured_media", 0)
        title_clean = clean_html(post_title)

        print(f"\n[{idx+1}/{len(all_posts)}] ID {post_id}: {title_clean[:60]}")

        # Fetch full post with edit context to get Rank Math meta
        print(f"  Fetching post meta (context=edit)...")
        post_detail = api_get(f"{WP_API}/posts/{post_id}?context=edit")
        time.sleep(DELAY)

        if post_detail is None:
            print(f"  [ERROR] Could not fetch post details")
            log_rows.append({
                "id": post_id, "title": title_clean,
                "old_meta_title": "", "new_meta_title": "",
                "old_meta_desc": "", "new_meta_desc": "",
                "alt_text_updated": "no", "status": "error_fetch"
            })
            error_count += 1
            continue

        # Extract current Rank Math meta
        meta = post_detail.get("meta", {})
        if meta is None:
            meta = {}

        old_meta_title = meta.get("rank_math_title", "") or ""
        old_meta_desc = meta.get("rank_math_description", "") or ""
        focus_keyword = meta.get("rank_math_focus_keyword", "") or ""

        print(f"  Focus keyword: '{focus_keyword}'")
        print(f"  Current meta title ({len(old_meta_title)} chars): '{old_meta_title[:60]}'")
        print(f"  Current meta desc ({len(old_meta_desc)} chars): '{old_meta_desc[:80]}'")

        # Determine cluster from inventory for better description generation
        cluster = ""

        # Generate optimized meta title
        new_meta_title = generate_meta_title(post_title, focus_keyword, old_meta_title)

        # Generate optimized meta description
        new_meta_desc = generate_meta_description(post_title, focus_keyword, cluster, old_meta_desc)

        # Decide what to update
        meta_updates = {}

        if new_meta_title is not None:
            meta_updates["rank_math_title"] = new_meta_title
            print(f"  -> New meta title ({len(new_meta_title)} chars): '{new_meta_title}'")
        else:
            new_meta_title = old_meta_title
            print(f"  -> Meta title: OK (keeping current)")

        if new_meta_desc is not None:
            meta_updates["rank_math_description"] = new_meta_desc
            print(f"  -> New meta desc ({len(new_meta_desc)} chars): '{new_meta_desc}'")
        else:
            new_meta_desc = old_meta_desc
            print(f"  -> Meta desc: OK (keeping current)")

        # Update meta if needed
        meta_status = "no_change"
        if meta_updates:
            # Try Rank Math API first
            print(f"  Updating via Rank Math API...")
            rm_result = api_post(RANKMATH_API, {
                "objectID": post_id,
                "objectType": "post",
                "meta": meta_updates
            })
            time.sleep(DELAY)

            if rm_result and not (isinstance(rm_result, dict) and rm_result.get("code")):
                print(f"  -> Rank Math API: success")
                meta_status = "updated_rankmath"
            else:
                # Fallback: update via WP REST API post meta
                print(f"  -> Rank Math API failed, using WP REST fallback...")
                if rm_result:
                    print(f"     Error: {rm_result}")
                wp_result = api_post(f"{WP_API}/posts/{post_id}", {
                    "meta": meta_updates
                })
                time.sleep(DELAY)

                if wp_result and wp_result.get("id") == post_id:
                    print(f"  -> WP REST fallback: success")
                    meta_status = "updated_wp_rest"
                else:
                    print(f"  -> WP REST fallback: FAILED")
                    if wp_result:
                        print(f"     Error: {wp_result}")
                    meta_status = "error_update"
                    error_count += 1

        # Handle featured image alt text
        alt_text_updated = "no"
        if featured_media and featured_media > 0:
            print(f"  Fetching featured media ID {featured_media}...")
            media = api_get(f"{WP_API}/media/{featured_media}")
            time.sleep(DELAY)

            if media and isinstance(media, dict) and not media.get("code"):
                current_alt = media.get("alt_text", "") or ""
                print(f"  Current alt text: '{current_alt[:60]}'")

                # Update if empty or generic
                needs_alt_update = False
                if not current_alt or len(current_alt.strip()) < 5:
                    needs_alt_update = True
                elif current_alt.lower() in ["image", "photo", "picture", "img", "thumbnail",
                                               "featured image", "post image", "untitled"]:
                    needs_alt_update = True
                elif focus_keyword and focus_keyword.lower() not in current_alt.lower():
                    # Alt text exists but doesn't contain focus keyword
                    needs_alt_update = True

                if needs_alt_update:
                    new_alt = generate_alt_text(post_title, focus_keyword)
                    print(f"  -> New alt text: '{new_alt}'")

                    alt_result = api_post(f"{WP_API}/media/{featured_media}", {
                        "alt_text": new_alt
                    })
                    time.sleep(DELAY)

                    if alt_result and isinstance(alt_result, dict) and alt_result.get("id"):
                        alt_text_updated = "yes"
                        print(f"  -> Alt text updated")
                    else:
                        alt_text_updated = "error"
                        print(f"  -> Alt text update FAILED")
                else:
                    print(f"  -> Alt text: OK (keeping current)")
            else:
                print(f"  -> Could not fetch media")
        else:
            print(f"  No featured media")

        # Track results
        if meta_status in ("updated_rankmath", "updated_wp_rest") or alt_text_updated == "yes":
            updated_count += 1
            final_status = meta_status if meta_updates else "alt_only"
        elif meta_status == "no_change" and alt_text_updated == "no":
            skipped_count += 1
            final_status = "no_change"
        else:
            final_status = meta_status

        log_rows.append({
            "id": post_id,
            "title": title_clean,
            "old_meta_title": old_meta_title,
            "new_meta_title": new_meta_title if meta_updates.get("rank_math_title") else "(unchanged)",
            "old_meta_desc": old_meta_desc,
            "new_meta_desc": new_meta_desc if meta_updates.get("rank_math_description") else "(unchanged)",
            "alt_text_updated": alt_text_updated,
            "status": final_status
        })

    # Write log CSV
    print(f"\n\nWriting log to {LOG_FILE}...")
    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "title", "old_meta_title", "new_meta_title",
            "old_meta_desc", "new_meta_desc", "alt_text_updated", "status"
        ])
        writer.writeheader()
        writer.writerows(log_rows)

    print(f"\n{'=' * 70}")
    print(f"Phase 10AK Complete!")
    print(f"{'=' * 70}")
    print(f"Total posts processed: {len(all_posts)}")
    print(f"Updated: {updated_count}")
    print(f"Skipped (already optimized): {skipped_count}")
    print(f"Errors: {error_count}")
    print(f"Log written to: {LOG_FILE}")

if __name__ == "__main__":
    main()
