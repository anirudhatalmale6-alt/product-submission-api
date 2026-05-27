#!/usr/bin/env python3
"""
PetHub Online - Image & Alt Text Audit
Audits all published posts and pages for image issues.
"""

import requests
import re
import sys
from html import unescape
from urllib.parse import urlparse, unquote
from datetime import datetime

BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")

# Educational post IDs to specifically track
EDUCATIONAL_IDS = {
    4563, 4566, 4568, 4570, 4571, 4573, 4574, 4576,
    4406, 4407, 4408, 4409, 4410, 4415,
    4411, 4412, 4413, 4414,
    4783, 4784, 4785, 4786,
    4787, 4788, 4789, 4790,
    4791, 4792,
}

WEAK_ALT_PATTERNS = [
    r'^image\d*$',
    r'^photo\d*$',
    r'^screenshot\d*$',
    r'^picture\d*$',
    r'^img[_\-]?\d+',
    r'^DSC[_\-]?\d+',
    r'^IMG[_\-]?\d+',
    r'^DCIM',
    r'^untitled',
    r'^placeholder',
    r'^\d+$',
    r'^[a-f0-9\-]{20,}$',  # UUID-like filenames used as alt
    r'^\S+\.\w{3,4}$',     # Just a filename with extension
]


def fetch_all(endpoint, params=None):
    """Fetch all items from a paginated WP REST endpoint."""
    if params is None:
        params = {}
    items = []
    page = 1
    while True:
        params_page = {**params, "page": page, "per_page": 100, "status": "publish", "context": "edit"}
        s = requests.Session()
        s.auth = AUTH
        s.headers['Accept-Encoding'] = 'gzip, deflate'
        try:
            r = s.get(f"{BASE}/{endpoint}", params=params_page, timeout=60)
            if r.status_code == 400:
                # No more pages
                break
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if r.status_code == 400:
                break
            print(f"  HTTP error on page {page}: {e}", file=sys.stderr)
            break
        except Exception as e:
            print(f"  Error on page {page}: {e}", file=sys.stderr)
            break
        data = r.json()
        if not data:
            break
        items.extend(data)
        total_pages = int(r.headers.get("X-WP-TotalPages", 1))
        print(f"  Fetched page {page}/{total_pages} ({len(data)} items)", file=sys.stderr)
        if page >= total_pages:
            break
        page += 1
    return items


def extract_images(html_content):
    """Extract all <img> tags from HTML content, returning list of dicts."""
    if not html_content:
        return []
    images = []
    img_pattern = re.compile(r'<img\s[^>]*?>', re.IGNORECASE | re.DOTALL)
    for match in img_pattern.finditer(html_content):
        tag = match.group(0)
        # Extract src
        src_match = re.search(r'src=["\']([^"\']+)["\']', tag, re.IGNORECASE)
        src = unescape(src_match.group(1)) if src_match else ""
        # Extract alt
        alt_match = re.search(r'alt=["\']([^"\']*)["\']', tag, re.IGNORECASE)
        if alt_match is None:
            alt = None  # alt attribute missing entirely
        else:
            alt = unescape(alt_match.group(1)).strip()
        images.append({"src": src, "alt": alt, "tag": tag, "position": match.start()})
    return images


def is_weak_alt(alt_text):
    """Check if alt text is generic/weak."""
    if not alt_text:
        return False  # Empty handled separately
    text = alt_text.strip().lower()
    for pattern in WEAK_ALT_PATTERNS:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    return False


def has_chatgpt_filename(src):
    """Check if image filename contains chatgpt."""
    if not src:
        return False
    filename = unquote(urlparse(src).path.split("/")[-1]).lower()
    return "chatgpt" in filename


def get_content_raw(item):
    """Get raw content from a WP item (handles both dict formats)."""
    content = item.get("content", {})
    if isinstance(content, dict):
        return content.get("raw", content.get("rendered", ""))
    return str(content)


def get_title(item):
    """Get title from a WP item."""
    title = item.get("title", {})
    if isinstance(title, dict):
        return unescape(title.get("raw", title.get("rendered", "(no title)")))
    return str(title)


def run_audit():
    print("=" * 70, file=sys.stderr)
    print("PetHub Online - Image & Alt Text Audit", file=sys.stderr)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", file=sys.stderr)
    print("=" * 70, file=sys.stderr)

    # Fetch all published posts and pages
    print("\nFetching posts...", file=sys.stderr)
    posts = fetch_all("posts")
    print(f"  Total posts: {len(posts)}", file=sys.stderr)

    print("\nFetching pages...", file=sys.stderr)
    pages = fetch_all("pages")
    print(f"  Total pages: {len(pages)}", file=sys.stderr)

    all_items = []
    for p in posts:
        p["_type"] = "post"
        all_items.append(p)
    for p in pages:
        p["_type"] = "page"
        all_items.append(p)

    print(f"\nTotal items to audit: {len(all_items)}", file=sys.stderr)

    # Audit categories
    missing_featured = []       # 1
    missing_alt = []            # 2
    weak_alt = []               # 3
    chatgpt_filenames = []      # 4
    missing_hero = []           # 5
    image_counts = []           # 6
    edu_zero_images = []        # Educational posts with zero body images

    for item in all_items:
        item_id = item["id"]
        item_type = item["_type"]
        title = get_title(item)
        content = get_content_raw(item)
        featured_media = item.get("featured_media", 0)
        slug = item.get("slug", "")
        link = item.get("link", f"https://pethubonline.com/?p={item_id}")

        images = extract_images(content)
        img_count = len(images)

        label = f"[{item_type.upper()} #{item_id}] {title}"

        # 1. Missing featured image
        if not featured_media:
            missing_featured.append({
                "id": item_id, "type": item_type, "title": title, "link": link
            })

        # 2. Missing alt text
        for img in images:
            if img["alt"] is None or img["alt"] == "":
                missing_alt.append({
                    "id": item_id, "type": item_type, "title": title,
                    "src": img["src"], "alt_raw": img["alt"], "link": link
                })

        # 3. Weak alt text
        for img in images:
            if img["alt"] and is_weak_alt(img["alt"]):
                weak_alt.append({
                    "id": item_id, "type": item_type, "title": title,
                    "src": img["src"], "alt": img["alt"], "link": link
                })

        # 4. ChatGPT filenames
        for img in images:
            if has_chatgpt_filename(img["src"]):
                chatgpt_filenames.append({
                    "id": item_id, "type": item_type, "title": title,
                    "src": img["src"], "alt": img.get("alt", ""), "link": link
                })

        # 5. Missing hero image (no image in first 1000 chars)
        if item_type == "post":
            first_1000 = content[:1000] if content else ""
            hero_imgs = extract_images(first_1000)
            if not hero_imgs:
                missing_hero.append({
                    "id": item_id, "type": item_type, "title": title,
                    "total_images": img_count, "link": link
                })

        # 6. Image count
        image_counts.append({
            "id": item_id, "type": item_type, "title": title,
            "count": img_count, "link": link
        })

        # Educational posts with zero images
        if item_id in EDUCATIONAL_IDS and img_count == 0:
            edu_zero_images.append({
                "id": item_id, "type": item_type, "title": title, "link": link
            })

    # Generate report
    lines = []
    lines.append("=" * 75)
    lines.append("PETHUB ONLINE - IMAGE & ALT TEXT AUDIT REPORT")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"Total items audited: {len(all_items)} ({len(posts)} posts, {len(pages)} pages)")
    lines.append("=" * 75)

    # Summary
    total_images = sum(ic["count"] for ic in image_counts)
    lines.append("")
    lines.append("EXECUTIVE SUMMARY")
    lines.append("-" * 40)
    lines.append(f"  Total images found in content:   {total_images}")
    lines.append(f"  Missing featured images:         {len(missing_featured)}")
    lines.append(f"  Missing alt text instances:       {len(missing_alt)}")
    lines.append(f"  Weak/generic alt text instances:  {len(weak_alt)}")
    lines.append(f"  ChatGPT filename images:         {len(chatgpt_filenames)}")
    lines.append(f"  Posts missing hero image:         {len(missing_hero)}")
    lines.append(f"  Educational posts with 0 images:  {len(edu_zero_images)}")

    # 1. Missing Featured Images
    lines.append("")
    lines.append("=" * 75)
    lines.append(f"1. MISSING FEATURED IMAGES ({len(missing_featured)} items)")
    lines.append("=" * 75)
    if missing_featured:
        for item in sorted(missing_featured, key=lambda x: x["id"]):
            lines.append(f"  [{item['type'].upper()} #{item['id']}] {item['title']}")
            lines.append(f"    URL: {item['link']}")
    else:
        lines.append("  None found - all items have featured images.")

    # 2. Missing Alt Text
    lines.append("")
    lines.append("=" * 75)
    lines.append(f"2. MISSING ALT TEXT ({len(missing_alt)} images)")
    lines.append("=" * 75)
    if missing_alt:
        # Group by post
        by_post = {}
        for item in missing_alt:
            key = item["id"]
            if key not in by_post:
                by_post[key] = {"title": item["title"], "type": item["type"], "link": item["link"], "images": []}
            by_post[key]["images"].append(item["src"])
        for pid in sorted(by_post.keys()):
            info = by_post[pid]
            lines.append(f"  [{info['type'].upper()} #{pid}] {info['title']}")
            for src in info["images"]:
                fname = unquote(urlparse(src).path.split("/")[-1]) if src else "(no src)"
                lines.append(f"    - {fname}")
    else:
        lines.append("  None found - all images have alt text.")

    # 3. Weak Alt Text
    lines.append("")
    lines.append("=" * 75)
    lines.append(f"3. WEAK/GENERIC ALT TEXT ({len(weak_alt)} images)")
    lines.append("=" * 75)
    if weak_alt:
        for item in sorted(weak_alt, key=lambda x: x["id"]):
            fname = unquote(urlparse(item["src"]).path.split("/")[-1]) if item["src"] else "(no src)"
            lines.append(f"  [{item['type'].upper()} #{item['id']}] {item['title']}")
            lines.append(f"    Alt: \"{item['alt']}\"  |  File: {fname}")
    else:
        lines.append("  None found - all alt text appears descriptive.")

    # 4. ChatGPT Image Filenames
    lines.append("")
    lines.append("=" * 75)
    lines.append(f"4. CHATGPT IMAGE FILENAMES ({len(chatgpt_filenames)} images)")
    lines.append("=" * 75)
    if chatgpt_filenames:
        for item in sorted(chatgpt_filenames, key=lambda x: x["id"]):
            fname = unquote(urlparse(item["src"]).path.split("/")[-1]) if item["src"] else "(no src)"
            lines.append(f"  [{item['type'].upper()} #{item['id']}] {item['title']}")
            lines.append(f"    File: {fname}")
            lines.append(f"    URL: {item['link']}")
    else:
        lines.append("  None found - no ChatGPT-named images detected.")

    # 5. Missing Hero Images
    lines.append("")
    lines.append("=" * 75)
    lines.append(f"5. POSTS MISSING HERO IMAGE (first 1000 chars) ({len(missing_hero)} posts)")
    lines.append("=" * 75)
    if missing_hero:
        for item in sorted(missing_hero, key=lambda x: x["id"]):
            img_note = f"({item['total_images']} images total)" if item['total_images'] > 0 else "(NO images at all)"
            lines.append(f"  [POST #{item['id']}] {item['title']}  {img_note}")
    else:
        lines.append("  None found - all posts have hero images.")

    # 6. Image Count Per Item
    lines.append("")
    lines.append("=" * 75)
    lines.append("6. IMAGE COUNT PER ITEM")
    lines.append("=" * 75)
    # Sort by count ascending so zero-image items are at top
    for item in sorted(image_counts, key=lambda x: (x["count"], x["id"])):
        lines.append(f"  {item['count']:3d} images  [{item['type'].upper()} #{item['id']}] {item['title']}")

    # Educational Posts with Zero Images
    lines.append("")
    lines.append("=" * 75)
    lines.append(f"7. EDUCATIONAL POSTS WITH ZERO BODY IMAGES ({len(edu_zero_images)} of {len(EDUCATIONAL_IDS)} tracked)")
    lines.append("=" * 75)
    if edu_zero_images:
        for item in sorted(edu_zero_images, key=lambda x: x["id"]):
            lines.append(f"  [{item['type'].upper()} #{item['id']}] {item['title']}")
            lines.append(f"    URL: {item['link']}")
    else:
        lines.append("  All tracked educational posts have at least one image.")

    # Educational posts found vs expected
    found_edu_ids = {ic["id"] for ic in image_counts if ic["id"] in EDUCATIONAL_IDS}
    missing_edu_ids = EDUCATIONAL_IDS - found_edu_ids
    if missing_edu_ids:
        lines.append("")
        lines.append(f"  NOTE: {len(missing_edu_ids)} educational IDs not found as published content:")
        for mid in sorted(missing_edu_ids):
            lines.append(f"    - ID {mid}")

    # Educational posts image summary
    lines.append("")
    lines.append("  EDUCATIONAL POSTS IMAGE SUMMARY:")
    edu_items = [ic for ic in image_counts if ic["id"] in EDUCATIONAL_IDS]
    for item in sorted(edu_items, key=lambda x: x["id"]):
        status = "OK" if item["count"] > 0 else "** ZERO IMAGES **"
        lines.append(f"    #{item['id']:5d}  {item['count']:2d} images  {item['title'][:50]}  {status}")

    lines.append("")
    lines.append("=" * 75)
    lines.append("END OF REPORT")
    lines.append("=" * 75)

    report = "\n".join(lines)
    return report


if __name__ == "__main__":
    report = run_audit()

    # Save report
    report_path = "/var/lib/freelancer/projects/40416335/phase10d/image_audit_report.txt"
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\nReport saved to: {report_path}", file=sys.stderr)

    # Also print to stdout
    print(report)
