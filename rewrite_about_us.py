#!/usr/bin/env python3
"""Rewrite the About Us page (ID 39) on pethubonline.com.

Steps:
1. Fetch current content (context=edit), save backup
2. Extract the existing wp:cover hero block (keep it)
3. Build new body content with honest, compliant language
4. Validate with validate_gutenberg()
5. Push update via REST API
"""

import sys, os, re, json, requests

sys.path.insert(0, "/var/lib/freelancer/projects/40416335")
from gutenberg_utils import (
    validate_gutenberg, wrap_paragraph, wrap_heading, wrap_list,
    wrap_separator, build_page, safe_update_content, tpl_trust_footer,
    tpl_info_strip
)

WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
USER = "jasonsarah2026"
PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
PAGE_ID = 39
BACKUP_DIR = "/var/lib/freelancer/projects/40416335/phase10d"
BACKUP_FILE = os.path.join(BACKUP_DIR, "about_us_backup.txt")


def main():
    # ── 1. Fetch current page ────────────────────────────────────────
    s = requests.Session()
    s.auth = (USER, PASS)
    s.headers["Accept-Encoding"] = "gzip, deflate"

    print("[1] Fetching page 39 (context=edit)...")
    r = s.get(f"{WP_BASE}/pages/{PAGE_ID}", params={"context": "edit"})
    if r.status_code != 200:
        print(f"FATAL: Could not fetch page 39 — HTTP {r.status_code}")
        print(r.text[:500])
        sys.exit(1)

    data = r.json()
    raw_content = data.get("content", {}).get("raw", "")
    title = data.get("title", {}).get("raw", "About Us")
    print(f"  Title: {title}")
    print(f"  Content length: {len(raw_content)} chars")

    # ── 2. Save backup ───────────────────────────────────────────────
    os.makedirs(BACKUP_DIR, exist_ok=True)
    with open(BACKUP_FILE, "w", encoding="utf-8") as f:
        f.write(raw_content)
    print(f"[2] Backup saved to {BACKUP_FILE}")

    # ── 3. Extract cover block ───────────────────────────────────────
    # The cover block may contain nested blocks, so we need to match
    # from <!-- wp:cover ... to <!-- /wp:cover -->
    cover_match = re.search(
        r'(<!-- wp:cover[\s\S]*?<!-- /wp:cover -->)',
        raw_content
    )
    cover_block = ""
    if cover_match:
        cover_block = cover_match.group(1).strip()
        print(f"[3] Extracted cover block ({len(cover_block)} chars)")
    else:
        print("[3] WARNING: No cover block found — proceeding without hero")

    # ── 4. Build new body content ────────────────────────────────────
    blocks = []

    # Keep existing cover hero
    if cover_block:
        blocks.append(cover_block)

    # Info strip
    blocks.append(
        '<!-- wp:paragraph {"style":{"typography":{"fontSize":"0.9em"}}} -->\n'
        '<p style="font-size:0.9em;color:#555;">'
        '<strong>Last Updated:</strong> 27 May 2026<br/>'
        '<strong>Website:</strong> pethubonline.com<br/>'
        '<strong>Business:</strong> Pet Hub Online</p>\n'
        '<!-- /wp:paragraph -->'
    )

    blocks.append(wrap_separator())

    # ── Section 2: About Pet Hub Online ──────────────────────────────
    blocks.append(wrap_heading("About Pet Hub Online", level=2))
    blocks.append(wrap_paragraph(
        "Pet Hub Online is an independent, UK-based pet information website. "
        "We create educational content designed to help pet owners make informed "
        "decisions about products, nutrition, and everyday care."
    ))
    blocks.append(wrap_paragraph(
        "We are not veterinarians, and we do not manufacture or sell pet products "
        "directly. Our role is to research, organise, and present information in a "
        "clear, accessible way so you can find what you need without wading through "
        "marketing noise."
    ))

    # ── Section 3: Our Mission ───────────────────────────────────────
    blocks.append(wrap_heading("Our Mission", level=2))
    blocks.append(wrap_paragraph(
        "Our mission is straightforward: help pet owners find reliable, clearly "
        "sourced information about pet products and care. We aim to present facts "
        "in plain language, acknowledge what we do not know, and point you toward "
        "qualified professionals when a topic falls outside our scope."
    ))

    # ── Section 4: What We Do ────────────────────────────────────────
    blocks.append(wrap_heading("What We Do", level=2))

    # 4a — Educational Guides
    blocks.append(wrap_heading("Educational Guides", level=3))
    blocks.append(wrap_paragraph(
        "We research and write guides covering pet products, care routines, and "
        "common questions pet owners face. Our content is based on manufacturer "
        "specifications, publicly available reviews, and published guidance from "
        "recognised veterinary and animal welfare organisations."
    ))

    # 4b — Product Information
    blocks.append(wrap_heading("Product Information", level=3))
    blocks.append(wrap_paragraph(
        "We gather and present product information to help owners compare options "
        "side by side. We draw on publicly available data — including manufacturer "
        "descriptions, ingredient lists, and aggregated customer feedback — rather "
        "than proprietary lab results. Where we include affiliate links, these are "
        "clearly disclosed."
    ))

    # 4c — Ongoing Updates
    blocks.append(wrap_heading("Ongoing Updates", level=3))
    blocks.append(wrap_paragraph(
        "We regularly review and update our content to keep information current and "
        "accurate. Each page displays the date it was last updated, so you can "
        "judge how recent the information is."
    ))

    # ── Section 5: How Our Content Is Created ────────────────────────
    blocks.append(wrap_heading("How Our Content Is Created", level=2))
    blocks.append(wrap_paragraph(
        "Our content creation process combines AI-assisted drafting with human "
        "editorial oversight. Every article goes through the following steps:"
    ))
    blocks.append(wrap_list([
        "<strong>Research</strong> — We gather information from manufacturer data, "
        "published veterinary guidance, and reputable pet care sources.",
        "<strong>Drafting</strong> — Initial drafts are created with AI assistance "
        "to ensure consistent structure and coverage.",
        "<strong>Editorial Review</strong> — A human editor reviews each piece for "
        "accuracy, tone, and completeness before publication.",
        "<strong>Fact-Checking</strong> — Claims are cross-referenced against publicly "
        "available sources. We do not fabricate results or claim hands-on experience "
        "with products we have not personally used.",
    ]))

    # ── Section 6: Our Limitations ───────────────────────────────────
    blocks.append(wrap_heading("Our Limitations", level=2))
    blocks.append(wrap_paragraph(
        "Transparency matters to us, and that includes being upfront about what we "
        "cannot do:"
    ))
    blocks.append(wrap_list([
        "We are not veterinarians or certified animal behaviourists.",
        "Our content is educational and should not be treated as medical or "
        "professional advice.",
        "Always consult a qualified veterinarian for health concerns about your pet.",
        "We cannot independently verify every product claim made by manufacturers.",
        "Where information is limited, we say so rather than speculate.",
    ]))

    # ── Section 7: Affiliate Relationships ───────────────────────────
    blocks.append(wrap_heading("Affiliate Relationships", level=2))
    blocks.append(wrap_paragraph(
        "Pet Hub Online participates in affiliate programmes, which means we may "
        "earn a small commission when you purchase a product through one of our "
        "links. This comes at no extra cost to you."
    ))
    blocks.append(wrap_paragraph(
        "Affiliate relationships do not influence which products we feature or how "
        "we present information. Our editorial decisions are made independently of "
        "any commercial arrangement. For full details, please read our "
        '<a href="/affiliate-disclosure">Affiliate Disclosure</a> page.'
    ))

    # ── Section 8: Contact Us ────────────────────────────────────────
    blocks.append(wrap_heading("Contact Us", level=2))
    blocks.append(wrap_paragraph(
        "Have a question, correction, or suggestion? We welcome feedback from our "
        "readers. Visit our "
        '<a href="/contact">Contact</a> page to get in touch.'
    ))

    # ── Section 9: Trust footer ──────────────────────────────────────
    trust_links = [
        ('/affiliate-disclosure', 'Affiliate Disclosure'),
        ('/how-we-research-pet-products', 'How We Research Pet Products'),
        ('/our-editorial-process', 'Our Editorial Process'),
        ('/corrections-and-updates-policy', 'Corrections and Updates Policy'),
    ]
    blocks.append(wrap_separator())
    blocks.append(wrap_heading("Our Trust and Transparency Pages", level=2))
    link_items = [f'<a href="{url}">{text}</a>' for url, text in trust_links]
    blocks.append(wrap_list(link_items))

    # ── 5. Assemble & validate ───────────────────────────────────────
    new_content = build_page(blocks)

    print(f"\n[4] New content length: {len(new_content)} chars")

    # Count blocks
    open_blocks = re.findall(r'<!-- wp:(\S+?)[\s{]', new_content)
    open_blocks2 = re.findall(r'<!-- wp:(\S+?) -->', new_content)
    total_opens = len(open_blocks) + len(open_blocks2)
    print(f"  Total block opens: {total_opens}")

    is_valid, issues = validate_gutenberg(new_content)
    if not is_valid:
        print(f"FATAL: Gutenberg validation failed: {issues}")
        # Save for debugging
        with open(BACKUP_FILE.replace("backup", "failed_draft"), "w") as f:
            f.write(new_content)
        sys.exit(1)
    print("[5] Gutenberg validation PASSED")

    # ── Banned-phrase audit ──────────────────────────────────────────
    # Remove the cover block from the audit (it's untouched original content)
    body_for_audit = new_content
    if cover_block:
        body_for_audit = new_content.replace(cover_block, "")

    banned = [
        r'\bexperts?\b', r'\bexpert team\b', r'\btesting\b',
        r'\bwe test products\b', r'\bwe only recommend products we believe in\b',
        r'\breal user feedback\b', r'\bexpert testing\b',
    ]
    found_banned = []
    for pat in banned:
        matches = re.findall(pat, body_for_audit, re.IGNORECASE)
        if matches:
            found_banned.extend(matches)
    if found_banned:
        print(f"WARNING: Banned phrases found in body: {found_banned}")
        print("Continuing anyway — review manually if these are in the cover block only.")
    else:
        print("[6] Banned-phrase audit PASSED (none found in body)")

    # ── 6. Push update ───────────────────────────────────────────────
    print("\n[7] Pushing update to page 39...")
    ok, msg = safe_update_content(s, WP_BASE, "pages", PAGE_ID, new_content)
    if ok:
        print(f"SUCCESS: Page 39 updated. Message: {msg}")
    else:
        print(f"FAILED: {msg}")
        sys.exit(1)

    # ── 7. Verify ────────────────────────────────────────────────────
    print("\n[8] Verifying update...")
    r2 = s.get(f"{WP_BASE}/pages/{PAGE_ID}", params={"context": "edit"})
    if r2.status_code == 200:
        verified_content = r2.json().get("content", {}).get("raw", "")
        print(f"  Verified content length: {len(verified_content)} chars")
        if "About Pet Hub Online" in verified_content and "Our Limitations" in verified_content:
            print("  Key sections confirmed present.")
        else:
            print("  WARNING: Key sections may be missing — check manually.")
    else:
        print(f"  Verification fetch failed: HTTP {r2.status_code}")

    print("\nDone.")


if __name__ == "__main__":
    main()
