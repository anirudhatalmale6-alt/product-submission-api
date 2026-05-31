#!/usr/bin/env python3
"""
Update author box on all published PetHub Online WordPress posts
to include a link to the About Jason page.
"""

import subprocess
import json
import re
import time
import os
import sys
from datetime import datetime

WP_API = "https://pethubonline.com/wp-json/wp/v2"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
LOG_PATH = "/var/lib/freelancer/projects/40416335/phase14_data/Author_Links_Log.txt"

# New author box paragraph (uses literal em dash U+2014, matching WP raw content format)
NEW_AUTHOR_PARA = '<p class="wp-block-paragraph"><strong><a href="/about-jason/">Jason Parr</a></strong> — Founder &amp; Lead Researcher at PetHub Online. Jason has been researching pet products and care practices for over 15 years, drawing on guidance from UK veterinary organisations and animal welfare charities. <a href="/about-jason/">Learn more about Jason and our editorial standards</a>.</p>'

log_lines = []

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    log_lines.append(line)

def curl_get(url, retries=2):
    """GET request using curl subprocess with retry."""
    for attempt in range(retries + 1):
        try:
            cmd = [
                "curl", "-s", "-S",
                "--connect-timeout", "15",
                "--max-time", "45",
                "-u", f"{WP_USER}:{WP_PASS}",
                "-H", "Content-Type: application/json",
                url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                log(f"  curl GET error (attempt {attempt+1}): {result.stderr}")
                if attempt < retries:
                    time.sleep(3)
                    continue
                return None
            return json.loads(result.stdout)
        except subprocess.TimeoutExpired:
            log(f"  curl GET timeout (attempt {attempt+1})")
            if attempt < retries:
                time.sleep(3)
                continue
            return None
        except json.JSONDecodeError as e:
            log(f"  JSON decode error: {e}")
            log(f"  Response (first 500 chars): {result.stdout[:500]}")
            return None
    return None

def curl_get_with_headers(url):
    """GET request that also returns headers (for pagination)."""
    cmd = [
        "curl", "-s", "-S", "-D", "-",
        "--connect-timeout", "15",
        "--max-time", "45",
        "-u", f"{WP_USER}:{WP_PASS}",
        "-H", "Content-Type: application/json",
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        log(f"  curl GET error: {result.stderr}")
        return None, {}

    # Split headers and body - curl -D - outputs headers then body
    # Headers end with blank line
    raw = result.stdout

    # Find the last occurrence of HTTP header block followed by body
    # With -D -, headers go to stdout before body
    # Split on double CRLF or double LF
    body = None
    headers = {}

    # Try CRLF first
    if "\r\n\r\n" in raw:
        parts = raw.split("\r\n\r\n")
        # Body is the last part, headers are everything before
        body = parts[-1]
        header_text = "\r\n\r\n".join(parts[:-1])
        for line in header_text.split("\r\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                headers[key.strip().lower()] = val.strip()
    elif "\n\n" in raw:
        parts = raw.split("\n\n")
        body = parts[-1]
        header_text = "\n\n".join(parts[:-1])
        for line in header_text.split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                headers[key.strip().lower()] = val.strip()
    else:
        body = raw

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        log(f"  JSON decode error: {e}")
        log(f"  Body (first 500 chars): {body[:500] if body else 'None'}")
        data = None

    return data, headers

def curl_post_update(post_id, content):
    """POST update using curl subprocess."""
    payload = json.dumps({"content": content})
    cmd = [
        "curl", "-s", "-S",
        "--connect-timeout", "15",
        "--max-time", "90",
        "-X", "POST",
        "-u", f"{WP_USER}:{WP_PASS}",
        "-H", "Content-Type: application/json",
        "-d", payload,
        f"{WP_API}/posts/{post_id}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        log(f"  curl POST error: {result.stderr}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        log(f"  JSON decode error: {e}")
        log(f"  Response (first 500 chars): {result.stdout[:500]}")
        return None

def fetch_all_published_posts():
    """Fetch all published posts with pagination."""
    all_posts = []
    page = 1

    while True:
        url = f"{WP_API}/posts?status=publish&per_page=100&page={page}&_fields=id,title,content,link"
        log(f"Fetching page {page}...")

        data, headers = curl_get_with_headers(url)

        if data is None:
            log(f"  Failed to fetch page {page}")
            break

        if isinstance(data, dict) and data.get("code"):
            if data.get("code") == "rest_post_invalid_page_number":
                log(f"  No more pages (page {page} beyond total)")
                break
            log(f"  API error: {data}")
            break

        if not isinstance(data, list) or len(data) == 0:
            log(f"  No posts on page {page}")
            break

        all_posts.extend(data)
        total_pages = headers.get("x-wp-totalpages", "1")
        total_posts = headers.get("x-wp-total", "?")
        log(f"  Got {len(data)} posts (total: {total_posts}, pages: {total_pages})")

        try:
            if page >= int(total_pages):
                break
        except (ValueError, TypeError):
            if len(data) < 100:
                break

        page += 1
        time.sleep(1)

    return all_posts

def has_about_jason_link_in_author_box(content):
    """Check if the author box already has /about-jason/ link."""
    # Find "About the Author" and check if /about-jason/ appears after it
    idx = content.lower().find('about the author')
    if idx == -1:
        return False
    after = content[idx:]
    if '/about-jason/' in after:
        return True
    return False

def update_author_box(content):
    """
    Replace the old author box paragraph with the new one.
    Returns (updated_content, was_changed).
    """
    if 'About the Author' not in content:
        return content, False

    # Strategy: Find the paragraph containing "<strong>Jason Parr</strong>"
    # that comes after "About the Author" heading

    # Find the "About the Author" heading position
    about_match = re.search(r'About the Author</h[23]>', content)
    if not about_match:
        # Try without closing tag specificity
        about_match = re.search(r'About the Author', content)

    if not about_match:
        return content, False

    about_pos = about_match.end()

    # In the content after the heading, find the paragraph with Jason Parr
    after_heading = content[about_pos:]

    # Match the paragraph - flexible pattern for different dash types and content
    # The paragraph starts with <p and contains <strong>Jason Parr</strong> followed by dash and bio text
    para_pattern = re.compile(
        r'<p[^>]*>\s*<strong>Jason Parr</strong>\s*(?:—|–|-|&mdash;|&ndash;)\s*.*?</p>',
        re.DOTALL | re.IGNORECASE
    )

    match = para_pattern.search(after_heading)
    if match:
        old_text = match.group(0)
        # Check it doesn't already have the link
        if '/about-jason/' in old_text:
            return content, False

        # Replace in the original content
        old_start = about_pos + match.start()
        old_end = about_pos + match.end()
        new_content = content[:old_start] + NEW_AUTHOR_PARA + content[old_end:]
        return new_content, True

    # Broader fallback: any <p> with "Jason Parr" after the heading
    para_pattern2 = re.compile(
        r'<p[^>]*>.*?Jason Parr.*?</p>',
        re.DOTALL | re.IGNORECASE
    )

    match = para_pattern2.search(after_heading[:2000])
    if match:
        old_text = match.group(0)
        if '/about-jason/' in old_text:
            return content, False

        old_start = about_pos + match.start()
        old_end = about_pos + match.end()
        new_content = content[:old_start] + NEW_AUTHOR_PARA + content[old_end:]
        return new_content, True

    return content, False

def main():
    log("=" * 70)
    log("PetHub Online - Author Box Update Script")
    log("Adding /about-jason/ links to author boxes on all published posts")
    log("=" * 70)

    # Step 1: Fetch all published posts
    log("")
    log("--- STEP 1: Fetching all published posts ---")
    posts = fetch_all_published_posts()
    log(f"Total published posts fetched: {len(posts)}")

    if not posts:
        log("No posts found. Exiting.")
        save_log()
        return

    # Step 2 & 3: Process each post
    log("")
    log("--- STEP 2: Processing posts ---")
    updated_count = 0
    skipped_already_linked = 0
    skipped_no_author_box = 0
    skipped_no_match = 0
    failed_count = 0

    for i, post in enumerate(posts):
        post_id = post["id"]
        title = post["title"]["rendered"] if isinstance(post["title"], dict) else post["title"]
        link = post.get("link", "N/A")
        content_rendered = post["content"]["rendered"] if isinstance(post["content"], dict) else post["content"]

        log(f"")
        log(f"[{i+1}/{len(posts)}] Post #{post_id}: {title}")
        log(f"  URL: {link}")

        # Quick check on rendered content
        if 'About the Author' not in content_rendered:
            log(f"  SKIP: No 'About the Author' section found")
            skipped_no_author_box += 1
            continue

        # Check if already has /about-jason/ link in author box
        if has_about_jason_link_in_author_box(content_rendered):
            log(f"  SKIP: Already has /about-jason/ link in author box")
            skipped_already_linked += 1
            continue

        # Fetch raw content for editing
        log(f"  Fetching raw (edit) content...")
        raw_post = curl_get(f"{WP_API}/posts/{post_id}?context=edit")
        if raw_post is None:
            log(f"  FAILED: Could not fetch raw content")
            failed_count += 1
            continue

        if isinstance(raw_post.get("content"), dict):
            raw_content = raw_post["content"]["raw"]
        else:
            raw_content = raw_post.get("content", "")

        # Check raw content
        if 'About the Author' not in raw_content:
            log(f"  SKIP: No 'About the Author' in raw content")
            skipped_no_author_box += 1
            continue

        if has_about_jason_link_in_author_box(raw_content):
            log(f"  SKIP: Already has /about-jason/ link in raw content")
            skipped_already_linked += 1
            continue

        # Perform the replacement
        new_content, was_changed = update_author_box(raw_content)

        if not was_changed:
            log(f"  SKIP: Author box pattern not matched for replacement")
            # Debug: show what's near "About the Author"
            about_idx = raw_content.find('About the Author')
            if about_idx >= 0:
                snippet = raw_content[about_idx:about_idx+400]
                log(f"  DEBUG snippet: {snippet[:300]}")
            skipped_no_match += 1
            continue

        # Wait 5 seconds before POST update
        log(f"  Waiting 5 seconds before updating...")
        time.sleep(5)

        # POST update
        log(f"  Updating post #{post_id}...")
        result = curl_post_update(post_id, new_content)

        if result and isinstance(result, dict) and "id" in result:
            log(f"  SUCCESS: Post #{post_id} updated successfully")
            updated_count += 1
        else:
            error_msg = "Unknown error"
            if isinstance(result, dict):
                error_msg = result.get("message", str(result))
            log(f"  FAILED: {error_msg}")
            failed_count += 1

    # Summary
    log("")
    log("=" * 70)
    log("SUMMARY")
    log("=" * 70)
    log(f"Total posts processed:         {len(posts)}")
    log(f"Posts updated:                  {updated_count}")
    log(f"Skipped (already linked):       {skipped_already_linked}")
    log(f"Skipped (no author box):        {skipped_no_author_box}")
    log(f"Skipped (no pattern match):     {skipped_no_match}")
    log(f"Failed:                         {failed_count}")
    log("=" * 70)

    save_log()

def save_log():
    """Save log to file."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "w") as f:
        f.write("\n".join(log_lines) + "\n")
    print(f"\nLog saved to: {LOG_PATH}", flush=True)

if __name__ == "__main__":
    main()
