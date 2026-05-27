#!/usr/bin/env python3
"""
Phase 10D: Fix broken internal links across pethubonline.com content.
Fetches all published posts/pages, identifies broken links, replaces with correct URLs.
"""

import requests
import time
import re
import json
import os
from datetime import datetime

# ── Config ──────────────────────────────────────────────────────────────────
BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
LOG_DIR = "/var/lib/freelancer/projects/40416335/phase10d"
LOG_FILE = os.path.join(LOG_DIR, "broken_links_fix_log.txt")
DELAY = 0.3

os.makedirs(LOG_DIR, exist_ok=True)

log_lines = []

def log(msg):
    print(msg)
    log_lines.append(msg)

def save_log():
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    log(f"[LOG] Saved to {LOG_FILE}")

# ── Helpers ─────────────────────────────────────────────────────────────────
def get_session():
    s = requests.Session()
    s.auth = AUTH
    s.headers["Accept-Encoding"] = "gzip, deflate"
    s.headers["User-Agent"] = "PetHubLinkFixer/1.0"
    return s

def fetch_all(s, endpoint, params=None):
    """Fetch all items from a paginated WP REST endpoint."""
    items = []
    page = 1
    base_params = {"per_page": 100, "status": "publish"}
    if params:
        base_params.update(params)
    while True:
        base_params["page"] = page
        r = s.get(f"{BASE}/{endpoint}", params=base_params, timeout=30)
        if r.status_code == 400:
            # past last page
            break
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        items.extend(data)
        total_pages = int(r.headers.get("X-WP-TotalPages", 1))
        log(f"  Fetched {endpoint} page {page}/{total_pages} ({len(data)} items)")
        if page >= total_pages:
            break
        page += 1
        time.sleep(DELAY)
    return items

def fetch_single(s, endpoint, item_id, params=None):
    """Fetch a single item by ID (any status)."""
    base_params = {}
    if params:
        base_params.update(params)
    r = s.get(f"{BASE}/{endpoint}/{item_id}", params=base_params, timeout=30)
    if r.status_code == 200:
        return r.json()
    # Try with context=edit for drafts
    base_params["context"] = "edit"
    r = s.get(f"{BASE}/{endpoint}/{item_id}", params=base_params, timeout=30)
    if r.status_code == 200:
        return r.json()
    log(f"  [WARN] Could not fetch {endpoint}/{item_id}: {r.status_code}")
    return None

def update_content(s, endpoint, item_id, new_content, title=""):
    """Update a post/page content via REST API."""
    r = s.post(
        f"{BASE}/{endpoint}/{item_id}",
        json={"content": new_content},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()

# ── Main ────────────────────────────────────────────────────────────────────
def main():
    log("=" * 70)
    log(f"Phase 10D: Fix Broken Internal Links — {datetime.now().isoformat()}")
    log("=" * 70)

    s = get_session()

    # ── Step 1: Fetch all published posts and pages ─────────────────────
    log("\n[1] Fetching all published posts...")
    posts = fetch_all(s, "posts")
    log(f"    Total posts: {len(posts)}")

    log("\n[2] Fetching all published pages...")
    pages = fetch_all(s, "pages")
    log(f"    Total pages: {len(pages)}")

    all_items = posts + pages

    # ── Step 2: Build slug-to-URL map ───────────────────────────────────
    log("\n[3] Building slug-to-URL map...")
    slug_map = {}
    id_map = {}
    for item in all_items:
        slug = item.get("slug", "")
        url = item.get("link", "")
        iid = item.get("id")
        title = item.get("title", {})
        if isinstance(title, dict):
            title = title.get("rendered", "")
        slug_map[slug] = url
        id_map[iid] = {"slug": slug, "url": url, "title": title}

    # Log some key slugs for debugging
    log(f"    Total slugs indexed: {len(slug_map)}")

    # ── Step 3: Look up specific pages we need ──────────────────────────
    log("\n[4] Looking up specific pages for correct URLs...")

    # Page 1956 = Dog Training
    dog_training_page = fetch_single(s, "pages", 1956)
    if dog_training_page:
        dt_slug = dog_training_page.get("slug", "")
        dt_link = dog_training_page.get("link", "")
        log(f"    Page 1956 (Dog Training): slug='{dt_slug}', link='{dt_link}'")
    else:
        dt_link = None
        log("    Page 1956 (Dog Training): NOT FOUND")

    # Page 1146 = Dog Harnesses hub
    dog_harness_page = fetch_single(s, "pages", 1146)
    if dog_harness_page:
        dh_slug = dog_harness_page.get("slug", "")
        dh_link = dog_harness_page.get("link", "")
        log(f"    Page 1146 (Dog Harnesses): slug='{dh_slug}', link='{dh_link}'")
    else:
        dh_link = None
        log("    Page 1146 (Dog Harnesses): NOT FOUND")

    # Page 4405 = Corrections and Updates Policy (draft)
    corrections_page = fetch_single(s, "pages", 4405)
    if corrections_page:
        cp_slug = corrections_page.get("slug", "")
        cp_link = corrections_page.get("link", "")
        cp_status = corrections_page.get("status", "")
        log(f"    Page 4405 (Corrections Policy): slug='{cp_slug}', status='{cp_status}', link='{cp_link}'")
    else:
        cp_slug = None
        log("    Page 4405 (Corrections Policy): NOT FOUND")

    # Page 4402 = How We Research (draft) - leave as-is
    research_page = fetch_single(s, "pages", 4402)
    if research_page:
        rp_slug = research_page.get("slug", "")
        rp_status = research_page.get("status", "")
        log(f"    Page 4402 (How We Research): slug='{rp_slug}', status='{rp_status}' — LEAVE AS-IS")

    # Page 4403 = Our Editorial Process (draft) - leave as-is
    editorial_page = fetch_single(s, "pages", 4403)
    if editorial_page:
        ep_slug = editorial_page.get("slug", "")
        ep_status = editorial_page.get("status", "")
        log(f"    Page 4403 (Editorial Process): slug='{ep_slug}', status='{ep_status}' — LEAVE AS-IS")

    # ── Search for Dog Care hub page ────────────────────────────────────
    log("\n[5] Searching for hub pages by slug keywords...")

    # Search slug map for dog-care, dog-health, pet-care variations
    care_candidates = {k: v for k, v in slug_map.items() if "dog-care" in k or "dog-health" in k}
    log(f"    Dog care candidates: {care_candidates}")

    pet_care_candidates = {k: v for k, v in slug_map.items() if "pet-care" in k}
    log(f"    Pet care candidates: {pet_care_candidates}")

    harness_candidates = {k: v for k, v in slug_map.items() if "harness" in k}
    log(f"    Harness candidates: {harness_candidates}")

    training_candidates = {k: v for k, v in slug_map.items() if "training" in k or "train" in k}
    log(f"    Training candidates: {training_candidates}")

    contact_candidates = {k: v for k, v in slug_map.items() if "contact" in k}
    log(f"    Contact candidates: {contact_candidates}")

    # Also search for category pages that might match
    log("\n[6] Fetching categories for fallback URLs...")
    categories = fetch_all(s, "categories")
    cat_slug_map = {}
    for cat in categories:
        cat_slug_map[cat.get("slug", "")] = cat.get("link", "")
    care_cats = {k: v for k, v in cat_slug_map.items() if "dog" in k or "care" in k or "pet" in k or "train" in k}
    log(f"    Relevant categories: {care_cats}")

    # ── Step 4: Build replacement rules ─────────────────────────────────
    log("\n[7] Building replacement rules...")

    replacements = {}

    # 1. /best-dog-harness -> correct harness hub URL
    if dh_link:
        # Extract path from full URL
        from urllib.parse import urlparse
        dh_path = urlparse(dh_link).path
        replacements["/best-dog-harness"] = dh_path.rstrip("/") if not dh_path.endswith("/") else dh_path
        # Also handle with trailing slash
        log(f"    /best-dog-harness -> {dh_path}")
    elif harness_candidates:
        # Use first harness candidate
        first_slug = list(harness_candidates.keys())[0]
        first_url = harness_candidates[first_slug]
        harness_path = urlparse(first_url).path
        replacements["/best-dog-harness"] = harness_path
        log(f"    /best-dog-harness -> {harness_path} (from slug '{first_slug}')")
    else:
        log("    [SKIP] /best-dog-harness: No harness hub page found")

    # 2. /dog-care/ -> correct dog care hub URL
    from urllib.parse import urlparse
    if care_candidates:
        # Prefer exact or closest match
        if "dog-health-care" in care_candidates:
            dc_path = urlparse(care_candidates["dog-health-care"]).path
        elif "dog-care" in care_candidates:
            dc_path = urlparse(care_candidates["dog-care"]).path
        else:
            first = list(care_candidates.values())[0]
            dc_path = urlparse(first).path
        replacements["/dog-care/"] = dc_path
        replacements["/dog-care"] = dc_path.rstrip("/")
        log(f"    /dog-care/ -> {dc_path}")
    elif "dog-care" in cat_slug_map:
        dc_path = urlparse(cat_slug_map["dog-care"]).path
        replacements["/dog-care/"] = dc_path
        replacements["/dog-care"] = dc_path.rstrip("/")
        log(f"    /dog-care/ -> {dc_path} (from category)")
    else:
        log("    [SKIP] /dog-care/: No dog care hub page found")

    # 3. /pet-care-tips/ -> correct pet care hub URL
    if pet_care_candidates:
        if "pet-care-tips" in pet_care_candidates:
            pc_path = urlparse(pet_care_candidates["pet-care-tips"]).path
            log(f"    /pet-care-tips/ -> {pc_path} (exact slug exists!)")
            # If it exists, no need to replace
            replacements.pop("/pet-care-tips/", None)
            replacements.pop("/pet-care-tips", None)
            log("    [SKIP] /pet-care-tips/ — page exists with this slug")
        else:
            first = list(pet_care_candidates.values())[0]
            pc_path = urlparse(first).path
            replacements["/pet-care-tips/"] = pc_path
            replacements["/pet-care-tips"] = pc_path.rstrip("/")
            log(f"    /pet-care-tips/ -> {pc_path}")
    elif "pet-care" in cat_slug_map:
        pc_path = urlparse(cat_slug_map["pet-care"]).path
        replacements["/pet-care-tips/"] = pc_path
        replacements["/pet-care-tips"] = pc_path.rstrip("/")
        log(f"    /pet-care-tips/ -> {pc_path} (from category)")
    else:
        log("    [SKIP] /pet-care-tips/: No pet care hub page found")

    # 4. /dog-training/ -> correct training hub URL
    if dt_link:
        dt_path = urlparse(dt_link).path
        replacements["/dog-training/"] = dt_path
        replacements["/dog-training"] = dt_path.rstrip("/")
        log(f"    /dog-training/ -> {dt_path}")
    elif training_candidates:
        first = list(training_candidates.values())[0]
        t_path = urlparse(first).path
        replacements["/dog-training/"] = t_path
        replacements["/dog-training"] = t_path.rstrip("/")
        log(f"    /dog-training/ -> {t_path}")
    else:
        log("    [SKIP] /dog-training/: No training hub page found")

    # 5. /corrections-and-updates-policy -> check if slug is different
    if corrections_page:
        if cp_slug and cp_slug != "corrections-and-updates-policy":
            replacements["/corrections-and-updates-policy"] = f"/{cp_slug}"
            log(f"    /corrections-and-updates-policy -> /{cp_slug}")
        else:
            log(f"    [SKIP] /corrections-and-updates-policy — slug matches ('{cp_slug}'), page just needs publishing")

    # 6 & 7. /how-we-research-pet-products and /our-editorial-process — LEAVE AS-IS
    log("    [SKIP] /how-we-research-pet-products — draft, will be published soon")
    log("    [SKIP] /our-editorial-process — draft, will be published soon")

    # 8. /contact -> /contact-pet-hub-online
    replacements["_CONTACT_FIX_"] = True  # Special flag — handled separately
    log("    /contact -> /contact-pet-hub-online (on About Us page only)")

    # 9. Dog food sub-pages — LEAVE AS-IS
    log("    [SKIP] Dog food sub-pages (grain-free, raw, senior, wet) — future phases")

    log(f"\n    Total replacement rules: {len(replacements) - 1} (plus contact fix)")

    # ── Step 5: Scan all content and apply fixes ────────────────────────
    log("\n[8] Scanning all content for broken links...")

    # We need to fetch content with context=edit to get raw HTML
    changes_made = []
    items_updated = 0
    total_replacements = 0

    # Refetch all items with edit context for raw content
    log("    Refetching posts with edit context...")
    posts_edit = fetch_all(s, "posts", {"context": "edit"})
    log("    Refetching pages with edit context...")
    pages_edit = fetch_all(s, "pages", {"context": "edit"})

    all_edit = []
    for p in posts_edit:
        p["_type"] = "posts"
        all_edit.append(p)
    for p in pages_edit:
        p["_type"] = "pages"
        all_edit.append(p)

    log(f"    Total items to scan: {len(all_edit)}")

    for item in all_edit:
        iid = item["id"]
        itype = item["_type"]
        title = item.get("title", {})
        if isinstance(title, dict):
            title = title.get("rendered", title.get("raw", ""))

        content = item.get("content", {})
        if isinstance(content, dict):
            content = content.get("raw", content.get("rendered", ""))

        if not content:
            continue

        original_content = content
        item_changes = []

        # Apply URL replacements
        for broken, fixed in replacements.items():
            if broken == "_CONTACT_FIX_":
                continue
            if broken in content:
                # Use precise href matching to avoid false positives
                # Match href="/broken-url" or href="https://pethubonline.com/broken-url"
                patterns = [
                    (f'href="{broken}"', f'href="{fixed}"'),
                    (f'href="{broken}/"', f'href="{fixed}/"' if not fixed.endswith("/") else f'href="{fixed}"'),
                    (f'href="https://pethubonline.com{broken}"', f'href="https://pethubonline.com{fixed}"'),
                    (f'href="https://pethubonline.com{broken}/"', f'href="https://pethubonline.com{fixed}/"' if not fixed.endswith("/") else f'href="https://pethubonline.com{fixed}"'),
                    (f'href="http://pethubonline.com{broken}"', f'href="https://pethubonline.com{fixed}"'),
                ]
                for old, new in patterns:
                    if old in content:
                        count = content.count(old)
                        content = content.replace(old, new)
                        item_changes.append(f"  Replaced {count}x: {old} -> {new}")
                        total_replacements += count

        # Special: /contact -> /contact-pet-hub-online (About Us page 39 specifically, but scan all)
        # Only fix exact /contact links (not /contact-pet-hub-online which is already correct)
        contact_patterns = [
            ('href="/contact"', 'href="/contact-pet-hub-online"'),
            ('href="https://pethubonline.com/contact"', 'href="https://pethubonline.com/contact-pet-hub-online"'),
            ('href="http://pethubonline.com/contact"', 'href="https://pethubonline.com/contact-pet-hub-online"'),
            ('href="/contact/"', 'href="/contact-pet-hub-online/"'),
            ('href="https://pethubonline.com/contact/"', 'href="https://pethubonline.com/contact-pet-hub-online/"'),
        ]
        for old, new in contact_patterns:
            if old in content:
                count = content.count(old)
                content = content.replace(old, new)
                item_changes.append(f"  Replaced {count}x: {old} -> {new}")
                total_replacements += count

        # Fix generic "Learn more" anchor text on affiliate disclosure links
        # Pattern: <a href="...affiliate-disclosure...">Learn more</a>
        aff_pattern = re.compile(
            r'(<a\s[^>]*href="[^"]*affiliate-disclosure[^"]*"[^>]*>)\s*Learn\s+more\s*(</a>)',
            re.IGNORECASE
        )
        aff_matches = aff_pattern.findall(content)
        if aff_matches:
            count = len(aff_matches)
            content = aff_pattern.sub(r'\1Read our affiliate disclosure\2', content)
            item_changes.append(f"  Fixed {count}x: 'Learn more' -> 'Read our affiliate disclosure' (affiliate links)")
            total_replacements += count

        # If changes were made, update the item
        if content != original_content:
            items_updated += 1
            change_entry = {
                "id": iid,
                "type": itype,
                "title": title,
                "changes": item_changes,
            }
            changes_made.append(change_entry)
            log(f"\n  [{items_updated}] Updating {itype[:-1]} #{iid}: {title}")
            for c in item_changes:
                log(c)

            try:
                update_content(s, itype, iid, content, title)
                log(f"    -> Updated successfully")
            except Exception as e:
                log(f"    -> ERROR: {e}")

            time.sleep(DELAY)

    # ── Summary ─────────────────────────────────────────────────────────
    log("\n" + "=" * 70)
    log("SUMMARY")
    log("=" * 70)
    log(f"Total items scanned: {len(all_edit)}")
    log(f"Items updated: {items_updated}")
    log(f"Total link replacements: {total_replacements}")
    log(f"\nReplacement rules applied:")
    for broken, fixed in replacements.items():
        if broken != "_CONTACT_FIX_":
            log(f"  {broken} -> {fixed}")
    log(f"  /contact -> /contact-pet-hub-online")
    log(f"  'Learn more' (affiliate) -> 'Read our affiliate disclosure'")

    log(f"\nSkipped (leave as-is):")
    log(f"  /how-we-research-pet-products — draft page, will be published")
    log(f"  /our-editorial-process — draft page, will be published")
    log(f"  Dog food sub-pages — future phase content")

    log(f"\nDetailed changes:")
    for entry in changes_made:
        log(f"  {entry['type'][:-1]} #{entry['id']}: {entry['title']}")
        for c in entry["changes"]:
            log(f"    {c}")

    save_log()
    log(f"\nDone! Log saved to {LOG_FILE}")


if __name__ == "__main__":
    main()
