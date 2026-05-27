#!/usr/bin/env python3
"""Refine 4 trust/policy pages on pethubonline.com — Phase 10D trust page polish."""

import json
import re
import sys
import time

import requests

sys.path.insert(0, "/var/lib/freelancer/projects/40416335")
from gutenberg_utils import (
    validate_gutenberg,
    wrap_paragraph,
    wrap_heading,
    wrap_list,
    wrap_separator,
    tpl_info_strip,
    build_page,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
BACKUP_PATH = "/var/lib/freelancer/projects/40416335/phase10d/trust_page_backups.json"

PAGE_IDS = [4402, 4403, 4405, 300]

# The canonical trust footer block
TRUST_FOOTER_LINKS = [
    ("/about-us", "About Us"),
    ("/affiliate-disclosure", "Affiliate Disclosure"),
    ("/how-we-research-pet-products", "How We Research Pet Products"),
    ("/our-editorial-process", "Our Editorial Process"),
    ("/corrections-and-updates-policy", "Corrections and Updates Policy"),
]

INFO_STRIP_TEXT = tpl_info_strip(
    last_updated="27 May 2026",
    website="pethubonline.com",
    business="Pet Hub Online",
)

SEPARATOR_BLOCK = wrap_separator()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_session():
    s = requests.Session()
    s.auth = AUTH
    s.headers["Accept-Encoding"] = "gzip, deflate"
    s.headers["User-Agent"] = "PetHub-TrustPageRefiner/1.0"
    return s


def fetch_page(session, page_id):
    """Fetch a page by ID. Returns dict or None."""
    url = f"{WP_BASE}/pages/{page_id}?context=edit"
    r = session.get(url)
    if r.status_code == 200:
        return r.json()
    print(f"  [WARN] Page {page_id} fetch returned {r.status_code}")
    return None


def search_page_by_slug(session, slug):
    """Search for a page by slug."""
    url = f"{WP_BASE}/pages?slug={slug}&status=draft,publish,private&context=edit"
    r = session.get(url)
    if r.status_code == 200 and r.json():
        return r.json()[0]
    return None


def build_trust_footer():
    """Build the canonical trust footer with all 5 pages."""
    links = [f'<a href="{url}">{text}</a>' for url, text in TRUST_FOOTER_LINKS]
    return "\n\n".join([
        SEPARATOR_BLOCK,
        wrap_heading("Our Trust and Transparency Pages", level=2),
        wrap_list(links),
    ])


def has_info_strip(content):
    """Check if page already has an info-strip-like block at the top."""
    # Look for "Last Updated" or "Effective Date" near the top
    first_500 = content[:500] if content else ""
    return bool(re.search(r"(Last Updated|Effective Date)", first_500))


def has_trust_footer(content):
    """Check if page has a trust footer section."""
    return "Our Trust and Transparency Pages" in (content or "")


def has_corrections_link(content):
    """Check if the corrections policy link exists in the trust footer."""
    return "corrections-and-updates-policy" in (content or "")


def remove_existing_trust_footer(content):
    """Remove the existing trust footer so we can replace it with the canonical one."""
    # Pattern: from the separator before "Our Trust and Transparency Pages" to end
    # Find the heading first
    marker = "Our Trust and Transparency Pages"
    idx = content.find(marker)
    if idx == -1:
        return content

    # Walk backwards from the heading to find the separator before it
    before_heading = content[:idx]
    # Find the last separator before the heading
    sep_pattern = '<!-- wp:separator -->'
    last_sep_idx = before_heading.rfind(sep_pattern)
    if last_sep_idx != -1:
        # Check it's reasonably close (within 200 chars)
        if idx - last_sep_idx < 300:
            return content[:last_sep_idx].rstrip()

    # Fallback: just cut from the heading block opener
    heading_block = "<!-- wp:heading -->"
    # Find the heading block just before the marker text
    search_start = max(0, idx - 100)
    heading_idx = content.rfind(heading_block, search_start, idx)
    if heading_idx != -1:
        return content[:heading_idx].rstrip()

    return content


def add_info_strip_to_top(content):
    """Prepend the info strip + separator to the top of the content."""
    return INFO_STRIP_TEXT + "\n\n" + SEPARATOR_BLOCK + "\n\n" + content


def check_fake_testing(content):
    """Check for any fake testing implications and report them."""
    suspicious = []
    patterns = [
        r"(we\s+test(ed)?|our\s+testing|hands[- ]on\s+test|lab\s+test)",
        r"(our\s+experts?\s+test|we\s+tried|we\s+evaluated\s+each)",
    ]
    for p in patterns:
        matches = re.findall(p, content or "", re.IGNORECASE)
        if matches:
            suspicious.extend(matches)
    return suspicious


def update_page(session, page_id, content, status=None):
    """Update page content via WP REST API after validation."""
    is_valid, issues = validate_gutenberg(content)
    if not is_valid:
        print(f"  [ERROR] Validation failed for page {page_id}: {issues}")
        return False

    payload = {"content": content}
    if status:
        payload["status"] = status

    r = session.post(f"{WP_BASE}/pages/{page_id}", json=payload)
    if r.status_code == 200:
        return True
    print(f"  [ERROR] Update failed for page {page_id}: {r.status_code} - {r.text[:300]}")
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    session = get_session()
    backups = {}
    pages_data = {}

    # -----------------------------------------------------------------------
    # Step 1: Fetch all pages and save backups
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("STEP 1: Fetching current page content and saving backups")
    print("=" * 60)

    for pid in PAGE_IDS:
        print(f"\nFetching page {pid}...")
        data = fetch_page(session, pid)
        if data:
            pages_data[pid] = data
            backups[str(pid)] = {
                "id": pid,
                "title": data.get("title", {}).get("raw", ""),
                "slug": data.get("slug", ""),
                "status": data.get("status", ""),
                "content": data.get("content", {}).get("raw", ""),
            }
            print(f"  Title: {backups[str(pid)]['title']}")
            print(f"  Status: {backups[str(pid)]['status']}")
            print(f"  Content length: {len(backups[str(pid)]['content'])} chars")
        else:
            print(f"  Page {pid} not found by ID, searching by slug...")
            if pid == 4405:
                for slug in ["corrections-and-updates-policy", "corrections-updates-policy"]:
                    data = search_page_by_slug(session, slug)
                    if data:
                        real_id = data["id"]
                        print(f"  Found as page {real_id} with slug '{slug}'")
                        pages_data[pid] = data
                        backups[str(pid)] = {
                            "id": real_id,
                            "title": data.get("title", {}).get("raw", ""),
                            "slug": data.get("slug", ""),
                            "status": data.get("status", ""),
                            "content": data.get("content", {}).get("raw", ""),
                            "actual_id": real_id,
                        }
                        print(f"  Title: {backups[str(pid)]['title']}")
                        print(f"  Status: {backups[str(pid)]['status']}")
                        break

    # Save backups
    with open(BACKUP_PATH, "w") as f:
        json.dump(backups, f, indent=2)
    print(f"\nBackups saved to {BACKUP_PATH}")

    # -----------------------------------------------------------------------
    # Step 2: Refine each page
    # -----------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("STEP 2: Refining pages")
    print("=" * 60)

    results = {}

    for pid in PAGE_IDS:
        if pid not in pages_data:
            print(f"\n--- Page {pid}: SKIPPED (not found) ---")
            results[pid] = "skipped - not found"
            continue

        data = pages_data[pid]
        actual_id = backups[str(pid)].get("actual_id", pid)
        title = backups[str(pid)]["title"]
        content = backups[str(pid)]["content"]
        changes = []

        print(f"\n--- Page {pid} ({actual_id}): {title} ---")

        # Check existing features
        has_strip = has_info_strip(content)
        has_footer = has_trust_footer(content)
        has_corr = has_corrections_link(content)

        print(f"  Has info strip: {has_strip}")
        print(f"  Has trust footer: {has_footer}")
        print(f"  Has corrections link: {has_corr}")

        # --- Info strip ---
        if not has_strip:
            content = add_info_strip_to_top(content)
            changes.append("Added info strip at top")
        else:
            # For page 300 (Affiliate Disclosure), check if it has all fields
            if pid == 300:
                first_block_end = content.find("<!-- /wp:paragraph -->")
                if first_block_end != -1:
                    first_block = content[:first_block_end + len("<!-- /wp:paragraph -->")]
                    needs_update = False
                    if "Last Updated" not in first_block:
                        needs_update = True
                    if "Business" not in first_block:
                        needs_update = True
                    if needs_update:
                        # Replace the first paragraph block with our full info strip
                        rest = content[first_block_end + len("<!-- /wp:paragraph -->"):].lstrip("\n")
                        # Preserve effective date if present
                        eff_match = re.search(r"Effective Date:</strong>\s*([^<]+)", first_block)
                        eff_date = eff_match.group(1).strip() if eff_match else ""
                        new_strip = tpl_info_strip(
                            effective_date=eff_date,
                            last_updated="27 May 2026",
                            website="pethubonline.com",
                            business="Pet Hub Online",
                        )
                        # Check if there's already a separator after
                        if rest.lstrip().startswith("<!-- wp:separator"):
                            content = new_strip + "\n\n" + rest
                        else:
                            content = new_strip + "\n\n" + SEPARATOR_BLOCK + "\n\n" + rest
                        changes.append("Updated info strip with all fields (preserved Effective Date)")

        # --- Check for fake testing implications (page 4402) ---
        if pid == 4402:
            suspicious = check_fake_testing(content)
            if suspicious:
                print(f"  [NOTE] Found potential testing language: {suspicious[:5]}")
                print(f"  (Review manually — not auto-removing to preserve context)")

        # --- Trust footer ---
        if has_footer:
            if not has_corr:
                # Remove old footer and add canonical one with corrections link
                content = remove_existing_trust_footer(content)
                content = content.rstrip() + "\n\n" + build_trust_footer()
                changes.append("Replaced trust footer (added corrections policy link)")
            else:
                # Footer exists with corrections link — verify all 5 links present
                all_links_present = True
                for url, _ in TRUST_FOOTER_LINKS:
                    if url not in content:
                        all_links_present = False
                        break
                if not all_links_present:
                    content = remove_existing_trust_footer(content)
                    content = content.rstrip() + "\n\n" + build_trust_footer()
                    changes.append("Rebuilt trust footer (ensured all 5 links)")
                else:
                    print("  Trust footer already complete with all 5 links")
        else:
            # No footer at all — add it
            content = content.rstrip() + "\n\n" + build_trust_footer()
            changes.append("Added trust footer with all 5 trust page links")

        # --- Validate and update ---
        if not changes:
            print("  No changes needed")
            results[pid] = "no changes needed"
            continue

        print(f"  Changes: {changes}")

        is_valid, issues = validate_gutenberg(content)
        if not is_valid:
            print(f"  [ERROR] Validation failed: {issues}")
            results[pid] = f"validation failed: {issues}"
            continue

        print(f"  Validation: PASSED")

        success = update_page(session, actual_id, content)
        if success:
            print(f"  Updated successfully!")
            results[pid] = f"updated ({', '.join(changes)})"
        else:
            results[pid] = "update failed"

        time.sleep(0.3)

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for pid in PAGE_IDS:
        title = backups.get(str(pid), {}).get("title", "unknown")
        result = results.get(pid, "not processed")
        print(f"  Page {pid} ({title}): {result}")

    print(f"\nBackups: {BACKUP_PATH}")
    print("Done!")


if __name__ == "__main__":
    main()
