#!/usr/bin/env python3
"""
Phase 10AK v2: SEO Metadata Optimization for PetHub Online
Uses XMLRPC to update jetpack_seo_html_title and advanced_seo_description
since the Rank Math REST API does not persist on this WordPress.com-hosted site.
"""

import subprocess
import json
import csv
import time
import re
import html
import xmlrpc.client

WP_API = "https://pethubonline.com/wp-json/wp/v2"
XMLRPC_URL = "https://pethubonline.com/xmlrpc.php"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
XMLRPC_USER = "jasonsarah2026"
XMLRPC_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
BLOG_ID = 1
LOG_FILE = "/var/lib/freelancer/projects/40416335/phase10ak_data/seo_metadata_log.csv"
DELAY = 2.0  # seconds between API calls

# XMLRPC proxy
proxy = xmlrpc.client.ServerProxy(XMLRPC_URL)

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

def is_buying_guide(title):
    """Check if the post is a buying guide / best-of list."""
    title_lower = title.lower()
    return any(kw in title_lower for kw in ["best ", "guide", "buying", "top ", "review"])

def has_year(text):
    """Check if text contains a year like 2026."""
    return bool(re.search(r'20\d{2}', text or ""))

def generate_meta_title(post_title):
    """Generate an optimized meta title under 60 chars."""
    title = clean_html(post_title)

    # Clean up the title for meta use
    meta = title

    # Remove " - PetHub Online" or similar site suffixes if present
    meta = re.sub(r'\s*[-–—|]\s*(PetHub|Pet Hub).*$', '', meta, flags=re.IGNORECASE)

    # Remove HTML entities leftovers
    meta = re.sub(r'&#\d+;', '', meta).strip()

    # Replace en-dash with hyphen for cleaner meta titles
    # (keeping original dashes as they are since they're already in the title)

    # If title is under 60, use it directly
    if len(meta) <= 60:
        return meta

    # Need to shorten. Remove parenthetical year first to re-add at end
    meta_no_year = re.sub(r'\s*\(?\d{4}\)?\s*', ' ', meta).strip()

    # Remove common suffixes
    for suffix in [" – Complete Guide & Honest Reviews", " - Complete Guide & Honest Reviews",
                   " – Complete Guide", " - Complete Guide", " – Comprehensive Guide",
                   " – Complete Buying Guide", " - A Complete Guide",
                   " – A Practical Guide", " - Honest Reviews",
                   " & Honest Reviews", " – Guide", " - Guide"]:
        if meta_no_year.endswith(suffix):
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
    words = candidate.split()
    result = ""
    for w in words:
        test = f"{result} {w}".strip() if result else w
        if len(test) > 57:
            break
        result = test
    return result if result else candidate[:57]

def generate_meta_description(post_title):
    """Generate an optimized meta description under 160 chars."""
    title = clean_html(post_title)
    title_lower = title.lower()

    # Build descriptions based on content type
    if "best " in title_lower and "uk" in title_lower:
        # Buying guide pattern - extract the subject
        subject = re.sub(r'Best\s+', '', title, flags=re.IGNORECASE)
        subject = re.sub(r'\s*UK\s*\(?20\d{2}\)?\s*', ' ', subject, flags=re.IGNORECASE)
        subject = re.sub(r'\s*[–—\-]\s*.*$', '', subject).strip()
        desc = f"Discover the best {subject.lower()} available in the UK for 2026. Expert-reviewed picks with honest ratings, pros, cons, and buying advice."
    elif "how to" in title_lower:
        subject = re.sub(r'How to\s+', '', title, flags=re.IGNORECASE)
        subject = re.sub(r'\s*[–—\-:]\s*.*$', '', subject).strip()
        desc = f"Learn how to {subject.lower()} with our step-by-step guide. Practical tips, expert advice, and common mistakes to avoid."
    elif "guide" in title_lower and "best" not in title_lower:
        subject = re.sub(r'\s*[–—\-:]\s*.*(?:Guide|guide).*$', '', title, flags=re.IGNORECASE)
        subject = re.sub(r'\s*\(?20\d{2}\)?\s*', ' ', subject).strip()
        desc = f"Your complete guide to {subject.lower()}. Evidence-based advice and practical tips for UK pet owners in 2026."
    elif "faq" in title_lower:
        subject = re.sub(r'\s*FAQ.*$', '', title, flags=re.IGNORECASE).strip()
        desc = f"Get answers to the most common questions about {subject.lower()}. Clear, expert-backed advice for UK pet owners."
    elif "explained" in title_lower:
        subject = re.sub(r'\s*Explained.*$', '', title, flags=re.IGNORECASE).strip()
        desc = f"Understand {subject.lower()} with this clear, jargon-free guide. Practical knowledge every UK pet owner should have."
    elif "vs " in title_lower or " vs." in title_lower:
        desc = f"An honest comparison: {title}. See the key differences, pros, cons, and which option suits your pet best."
    elif "glossary" in title_lower or "terminology" in title_lower:
        subject = re.sub(r'\s*(Glossary|Terminology).*$', '', title, flags=re.IGNORECASE).strip()
        desc = f"A clear glossary of {subject.lower()} terms. Simple definitions every pet owner can follow."
    elif "diy" in title_lower:
        subject = re.sub(r'DIY\s+', '', title, flags=re.IGNORECASE)
        subject = re.sub(r'\s*[–—\-:]\s*.*$', '', subject).strip()
        desc = f"Make safe, budget-friendly DIY {subject.lower()} at home. Step-by-step instructions with materials you already have."
    else:
        # Generic but still good
        desc = f"{title}. Practical advice, expert tips, and everything UK pet owners need to know."

    # Truncate to 160 chars if needed
    if len(desc) > 160:
        # Cut at last full sentence or phrase under 157
        if '. ' in desc:
            sentences = desc.split('. ')
            result = ""
            for s in sentences:
                test = f"{result}. {s}" if result else s
                if len(test) > 157:
                    break
                result = test
            desc = result.rstrip('.') + '.'
        else:
            desc = desc[:157].rsplit(' ', 1)[0] + '...'

    if len(desc) > 160:
        desc = desc[:157].rsplit(' ', 1)[0] + '...'

    return desc

def generate_alt_text(post_title):
    """Generate descriptive alt text for featured image."""
    title = clean_html(post_title)

    # Remove year, UK, and suffix decorations for a cleaner alt
    alt = re.sub(r'\s*\(?20\d{2}\)?\s*', ' ', title)
    alt = re.sub(r'\s*[–—\-]\s*(Complete|Comprehensive|Honest|Practical|Full).*$', '', alt, flags=re.IGNORECASE)
    alt = alt.strip()

    # Ensure it's descriptive
    if len(alt) < 10:
        alt = f"{title} guide for pet owners"

    return alt[:125]

def get_post_custom_fields(post_id):
    """Get custom fields for a post via XMLRPC."""
    try:
        post = proxy.wp.getPost(BLOG_ID, XMLRPC_USER, XMLRPC_PASS, post_id, ['custom_fields'])
        return post.get('custom_fields', [])
    except Exception as e:
        print(f"  [ERROR] XMLRPC getPost failed: {e}")
        return []

def update_seo_via_xmlrpc(post_id, custom_fields, new_title, new_desc):
    """Update SEO fields via XMLRPC."""
    # Find existing field IDs
    title_field_id = None
    desc_field_id = None

    for cf in custom_fields:
        if cf['key'] == 'jetpack_seo_html_title':
            title_field_id = cf['id']
        elif cf['key'] == 'advanced_seo_description':
            desc_field_id = cf['id']

    updates = []
    if title_field_id and new_title:
        updates.append({'id': str(title_field_id), 'key': 'jetpack_seo_html_title', 'value': new_title})
    elif new_title:
        updates.append({'key': 'jetpack_seo_html_title', 'value': new_title})

    if desc_field_id and new_desc:
        updates.append({'id': str(desc_field_id), 'key': 'advanced_seo_description', 'value': new_desc})
    elif new_desc:
        updates.append({'key': 'advanced_seo_description', 'value': new_desc})

    if not updates:
        return False

    try:
        result = proxy.wp.editPost(BLOG_ID, XMLRPC_USER, XMLRPC_PASS, post_id, {
            'custom_fields': updates
        })
        return result
    except Exception as e:
        print(f"  [ERROR] XMLRPC editPost failed: {e}")
        return False

def main():
    print("=" * 70)
    print("Phase 10AK v2: SEO Metadata Optimization (XMLRPC)")
    print("=" * 70)

    # Fetch all published posts
    all_posts = []
    for page in range(1, 5):
        url = f"{WP_API}/posts?per_page=100&page={page}&status=publish&_fields=id,title,featured_media,slug"
        print(f"\nFetching posts page {page}...")
        data = api_get(url)
        time.sleep(DELAY)

        if data is None:
            break
        if isinstance(data, dict) and data.get("code"):
            break
        if not data or len(data) == 0:
            break

        all_posts.extend(data)
        print(f"  Got {len(data)} posts (total: {len(all_posts)})")

        if len(data) < 100:
            break

    print(f"\nTotal published posts: {len(all_posts)}")

    if not all_posts:
        print("No posts found! Exiting.")
        return

    log_rows = []
    updated_count = 0
    skipped_count = 0
    error_count = 0

    for idx, post in enumerate(all_posts):
      try:
        post_id = post["id"]
        post_title = post["title"]["rendered"] if isinstance(post["title"], dict) else post["title"]
        featured_media = post.get("featured_media", 0)
        title_clean = clean_html(post_title)

        print(f"\n[{idx+1}/{len(all_posts)}] ID {post_id}: {title_clean[:60]}")

        # Fetch custom fields via XMLRPC
        custom_fields = get_post_custom_fields(post_id)
        time.sleep(DELAY)

        # Get current SEO values
        old_meta_title = ""
        old_meta_desc = ""
        for cf in custom_fields:
            if cf['key'] == 'jetpack_seo_html_title':
                old_meta_title = cf.get('value', '') or ''
            elif cf['key'] == 'advanced_seo_description':
                old_meta_desc = cf.get('value', '') or ''

        print(f"  Current SEO title ({len(old_meta_title)} chars): '{old_meta_title[:60]}'")
        print(f"  Current SEO desc ({len(old_meta_desc)} chars): '{old_meta_desc[:80]}'")

        # Generate new meta title
        new_meta_title = generate_meta_title(post_title)
        # Generate new meta description
        new_meta_desc = generate_meta_description(post_title)

        # Check if update is needed
        title_needs_update = True
        desc_needs_update = True

        if old_meta_title and len(old_meta_title) <= 60 and len(old_meta_title) > 10:
            title_needs_update = False
            new_meta_title = old_meta_title

        if old_meta_desc and 50 < len(old_meta_desc) <= 160:
            desc_needs_update = False
            new_meta_desc = old_meta_desc

        if title_needs_update:
            print(f"  -> New SEO title ({len(new_meta_title)} chars): '{new_meta_title}'")
        else:
            print(f"  -> SEO title: OK (keeping)")

        if desc_needs_update:
            print(f"  -> New SEO desc ({len(new_meta_desc)} chars): '{new_meta_desc}'")
        else:
            print(f"  -> SEO desc: OK (keeping)")

        # Update via XMLRPC
        meta_status = "no_change"
        update_title = new_meta_title if title_needs_update else None
        update_desc = new_meta_desc if desc_needs_update else None

        if update_title or update_desc:
            print(f"  Updating via XMLRPC...")
            result = update_seo_via_xmlrpc(post_id, custom_fields, update_title, update_desc)
            time.sleep(DELAY)

            if result:
                meta_status = "updated_xmlrpc"
                print(f"  -> XMLRPC update: success")
            else:
                meta_status = "error_update"
                print(f"  -> XMLRPC update: FAILED")
                error_count += 1

        # Handle featured image alt text
        alt_text_updated = "no"
        if featured_media and featured_media > 0:
            media = api_get(f"{WP_API}/media/{featured_media}")
            time.sleep(DELAY)

            if media and isinstance(media, dict) and not media.get("code"):
                current_alt = media.get("alt_text", "") or ""
                print(f"  Current alt text: '{current_alt[:60]}'")

                needs_alt_update = False
                if not current_alt or len(current_alt.strip()) < 5:
                    needs_alt_update = True
                elif current_alt.lower() in ["image", "photo", "picture", "img", "thumbnail",
                                               "featured image", "post image", "untitled"]:
                    needs_alt_update = True

                if needs_alt_update:
                    new_alt = generate_alt_text(post_title)
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
                    print(f"  -> Alt text: OK (keeping)")
            else:
                print(f"  -> Could not fetch media")
        else:
            print(f"  No featured media")

        # Track results
        if meta_status == "updated_xmlrpc" or alt_text_updated == "yes":
            updated_count += 1
        elif meta_status == "no_change" and alt_text_updated == "no":
            skipped_count += 1

        final_status = meta_status

        log_rows.append({
            "id": post_id,
            "title": title_clean,
            "old_meta_title": old_meta_title,
            "new_meta_title": new_meta_title if title_needs_update else "(unchanged)",
            "old_meta_desc": old_meta_desc,
            "new_meta_desc": new_meta_desc if desc_needs_update else "(unchanged)",
            "alt_text_updated": alt_text_updated,
            "status": final_status
        })
      except Exception as e:
        print(f"  [ERROR] Exception processing post {post.get('id','?')}: {e}")
        error_count += 1
        log_rows.append({
            "id": post.get("id", "?"),
            "title": clean_html(post.get("title", {}).get("rendered", "?") if isinstance(post.get("title"), dict) else str(post.get("title", "?"))),
            "old_meta_title": "", "new_meta_title": "",
            "old_meta_desc": "", "new_meta_desc": "",
            "alt_text_updated": "no", "status": f"error: {str(e)[:50]}"
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
    print(f"Phase 10AK v2 Complete!")
    print(f"{'=' * 70}")
    print(f"Total posts processed: {len(all_posts)}")
    print(f"Updated: {updated_count}")
    print(f"Skipped (already optimized): {skipped_count}")
    print(f"Errors: {error_count}")
    print(f"Log written to: {LOG_FILE}")

if __name__ == "__main__":
    main()
