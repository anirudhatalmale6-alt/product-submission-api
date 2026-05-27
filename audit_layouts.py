#!/usr/bin/env python3
"""
PetHub Online - Layout Audit Script
Fetches raw Gutenberg block content from WP REST API (context=edit)
and analyzes block structure patterns for template library planning.
"""

import requests
import re
import json
import os
from datetime import datetime
from collections import OrderedDict

# WordPress REST API config
BASE_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
HEADERS = {"Accept-Encoding": "gzip, deflate"}

# Items to audit
PAGES = [
    {"id": 39, "label": "Main page"},
    {"id": 63, "label": "Restored from revision"},
    {"id": 4402, "label": "About Us trust page (draft)"},
    {"id": 4403, "label": "Trust page (draft)"},
    {"id": 300, "label": "Privacy Policy / Affiliate Disclosure (live)"},
    {"id": 1041, "label": "Category/hub page"},
]

POSTS = [
    {"id": 4783, "label": "Phase 10D - Dog Bed Size (new educational)"},
    {"id": 4563, "label": "Phase 10C - Dog Care post"},
    {"id": 3996, "label": "Older pillar post - Dog Beds"},
]


def fetch_item(item_type, item_id):
    """Fetch a page or post with context=edit to get raw block content."""
    endpoint = f"{BASE_URL}/{item_type}/{item_id}"
    params = {"context": "edit"}
    try:
        resp = requests.get(endpoint, auth=AUTH, headers=HEADERS, params=params, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": f"HTTP {resp.status_code}", "message": resp.text[:500]}
    except Exception as e:
        return {"error": str(e)}


def extract_blocks(raw_content):
    """Parse Gutenberg block comments from raw HTML content."""
    # Match block open/close comments: <!-- wp:blocktype {"attrs"} --> or <!-- wp:blocktype -->
    block_pattern = re.compile(r'<!-- wp:([a-zA-Z0-9\-/]+)(?:\s+(\{[^}]*\}))?\s*(/?)\s*-->')

    blocks = []
    for match in block_pattern.finditer(raw_content):
        block_type = match.group(1)
        attrs_str = match.group(2)
        self_closing = match.group(3) == '/'
        attrs = {}
        if attrs_str:
            try:
                attrs = json.loads(attrs_str)
            except json.JSONDecodeError:
                attrs = {"raw": attrs_str}
        blocks.append({
            "type": f"wp:{block_type}",
            "attrs": attrs,
            "self_closing": self_closing,
        })
    return blocks


def get_unique_block_types(blocks):
    """Return sorted unique block types."""
    return sorted(set(b["type"] for b in blocks))


def check_hero_image(raw_content, blocks):
    """Check if there's a hero/featured image at the top."""
    # Check for wp:image or wp:cover near the start
    first_1000 = raw_content[:1500]
    has_cover = "<!-- wp:cover" in first_1000
    has_image_top = "<!-- wp:image" in first_1000
    has_media_text = "<!-- wp:media-text" in first_1000

    # Also check for featured image in data (featured_media field)
    return {
        "cover_block_at_top": has_cover,
        "image_block_at_top": has_image_top,
        "media_text_at_top": has_media_text,
        "any_hero": has_cover or has_image_top or has_media_text,
    }


def check_info_strip(raw_content):
    """Check for top info strip (date, site name, business name)."""
    first_2000 = raw_content[:2000].lower()
    patterns = {
        "has_date_reference": bool(re.search(r'(updated|published|date|last modified)', first_2000)),
        "has_site_name": "pethub" in first_2000 or "pet hub" in first_2000,
        "has_business_name": "hubxonline" in first_2000 or "hub x online" in first_2000,
        "has_info_box_top": bool(re.search(r'(info-strip|info-box|meta-strip|article-meta|post-meta)', first_2000)),
    }
    return patterns


def check_heading_hierarchy(raw_content):
    """Check heading levels in body content (H2/H3 only, no H1)."""
    # Find all heading blocks and HTML headings
    heading_block_pattern = re.compile(r'<!-- wp:heading\s*(\{[^}]*\})?\s*-->\s*<h(\d)', re.IGNORECASE)
    html_heading_pattern = re.compile(r'<h(\d)[^>]*>', re.IGNORECASE)

    levels_found = set()
    h1_in_body = False

    # Check wp:heading blocks
    for match in heading_block_pattern.finditer(raw_content):
        level = int(match.group(2))
        levels_found.add(level)
        if level == 1:
            h1_in_body = True

    # Check raw HTML headings
    for match in html_heading_pattern.finditer(raw_content):
        level = int(match.group(1))
        levels_found.add(level)
        if level == 1:
            h1_in_body = True

    return {
        "levels_found": sorted(levels_found),
        "has_h1_in_body": h1_in_body,
        "correct_hierarchy": not h1_in_body and levels_found.issubset({2, 3, 4, 5, 6}),
    }


def check_faq_section(raw_content):
    """Check for FAQ section."""
    lower = raw_content.lower()
    return {
        "has_faq_heading": bool(re.search(r'<h[23][^>]*>.*?(faq|frequently asked|common questions).*?</h[23]>', lower)),
        "has_faq_block": "wp:yoast/faq-block" in lower or "wp:rank-math/faq" in lower or "wp:generateblocks" in lower and "faq" in lower,
        "has_faq_schema": "faqpage" in lower or '"@type":"faq' in lower,
        "has_details_element": "<details" in lower or "wp:details" in lower,
        "has_qa_pattern": bool(re.search(r'<strong>.*?\?.*?</strong>', lower)),
    }


def check_related_reading(raw_content):
    """Check for Related Reading / Related Posts section."""
    lower = raw_content.lower()
    return {
        "has_related_heading": bool(re.search(r'<h[23][^>]*>.*?(related|further reading|you may also|keep reading|more from|explore more).*?</h[23]>', lower)),
        "has_internal_links_section": bool(re.search(r'(related-reading|related-posts|further-reading|keep-reading)', lower)),
        "internal_link_count": len(re.findall(r'href="https?://pethubonline\.com/[^"]*"', raw_content)),
    }


def check_affiliate_disclosure(raw_content):
    """Check for affiliate disclosure and info-box styled divs."""
    lower = raw_content.lower()
    results = {
        "has_affiliate_disclosure": bool(re.search(r'(affiliate|commission|earn a commission|disclosure|compensated)', lower)),
        "has_info_box_class": bool(re.search(r'class="[^"]*info-box[^"]*"', lower)),
        "has_wp_html_blocks": "<!-- wp:html" in raw_content,
        "wp_html_block_count": raw_content.count("<!-- wp:html"),
        "has_styled_divs": bool(re.search(r'<div[^>]*style="[^"]*background[^"]*"[^>]*>', lower)),
        "has_custom_css_classes": [],
    }

    # Find custom CSS classes in wp:html blocks or wp:group blocks
    class_matches = re.findall(r'class="([^"]*(?:info|disclosure|trust|box|notice|alert|callout)[^"]*)"', lower)
    results["has_custom_css_classes"] = list(set(class_matches))

    return results


def analyze_structure_pattern(raw_content, blocks):
    """Determine the general structure pattern of the content."""
    sections = []

    # Split into rough sections by headings
    heading_positions = [(m.start(), m.group()) for m in re.finditer(r'<h([23])[^>]*>(.*?)</h\1>', raw_content, re.IGNORECASE)]

    # Check for intro paragraph before first heading
    first_heading_pos = heading_positions[0][0] if heading_positions else len(raw_content)
    intro_content = raw_content[:first_heading_pos]
    if len(intro_content.strip()) > 50:
        sections.append("INTRO")

    # Categorize sections by heading content
    for pos, heading_html in heading_positions:
        heading_text = re.sub(r'<[^>]+>', '', heading_html).lower().strip()

        if any(kw in heading_text for kw in ['faq', 'frequently asked', 'common question']):
            sections.append("FAQ")
        elif any(kw in heading_text for kw in ['related', 'further reading', 'keep reading', 'you may also', 'explore']):
            sections.append("RELATED_READING")
        elif any(kw in heading_text for kw in ['trust', 'why trust', 'about us', 'our commitment']):
            sections.append("TRUST")
        elif any(kw in heading_text for kw in ['disclosure', 'affiliate']):
            sections.append("DISCLOSURE")
        elif any(kw in heading_text for kw in ['conclusion', 'final', 'summary', 'bottom line', 'verdict']):
            sections.append("CONCLUSION")
        elif any(kw in heading_text for kw in ['table of contents', 'toc', 'what you']):
            sections.append("TOC")
        else:
            sections.append("BODY")

    return sections


def format_report(item_type, item_info, data, analysis):
    """Format a single item's analysis into readable text."""
    lines = []
    lines.append(f"{'='*80}")
    lines.append(f"  {item_type.upper()} ID {item_info['id']}: {item_info['label']}")
    lines.append(f"{'='*80}")

    if "error" in data:
        lines.append(f"  ERROR: {data['error']}")
        if "message" in data:
            lines.append(f"  Message: {data['message'][:200]}")
        lines.append("")
        return "\n".join(lines)

    # Basic info
    title = data.get("title", {}).get("raw", data.get("title", {}).get("rendered", "N/A"))
    status = data.get("status", "N/A")
    slug = data.get("slug", "N/A")
    content_raw = data.get("content", {}).get("raw", "")
    content_len = len(content_raw)

    lines.append(f"  Title: {title}")
    lines.append(f"  Status: {status}")
    lines.append(f"  Slug: {slug}")
    lines.append(f"  Raw content length: {content_len} chars")
    lines.append("")

    if content_len == 0:
        lines.append("  [NO CONTENT - empty page/post]")
        lines.append("")
        return "\n".join(lines)

    # 1. Block types
    lines.append("  1. BLOCK TYPES PRESENT:")
    block_types = analysis["block_types"]
    if block_types:
        for bt in block_types:
            lines.append(f"     - {bt}")
    else:
        lines.append("     [No Gutenberg blocks detected - likely Classic Editor or raw HTML]")
    lines.append("")

    # 2. Hero/featured image
    lines.append("  2. HERO/FEATURED IMAGE:")
    hero = analysis["hero"]
    featured_media = data.get("featured_media", 0)
    lines.append(f"     Featured media ID: {featured_media}")
    lines.append(f"     Cover block at top: {hero['cover_block_at_top']}")
    lines.append(f"     Image block at top: {hero['image_block_at_top']}")
    lines.append(f"     Media-text at top: {hero['media_text_at_top']}")
    lines.append(f"     Any hero element: {hero['any_hero']}")
    lines.append("")

    # 3. Info strip
    lines.append("  3. TOP INFO STRIP:")
    info = analysis["info_strip"]
    for k, v in info.items():
        lines.append(f"     {k}: {v}")
    lines.append("")

    # 4. Heading hierarchy
    lines.append("  4. HEADING HIERARCHY:")
    headings = analysis["headings"]
    lines.append(f"     Levels found: {headings['levels_found']}")
    lines.append(f"     H1 in body: {headings['has_h1_in_body']}")
    lines.append(f"     Correct (no H1, only H2-H6): {headings['correct_hierarchy']}")
    lines.append("")

    # 5. FAQ section
    lines.append("  5. FAQ SECTION:")
    faq = analysis["faq"]
    for k, v in faq.items():
        lines.append(f"     {k}: {v}")
    lines.append("")

    # 6. Related reading
    lines.append("  6. RELATED READING:")
    related = analysis["related"]
    for k, v in related.items():
        lines.append(f"     {k}: {v}")
    lines.append("")

    # 7. Affiliate disclosure / info-box divs
    lines.append("  7. AFFILIATE DISCLOSURE / INFO-BOX DIVS:")
    disclosure = analysis["disclosure"]
    lines.append(f"     Has affiliate disclosure text: {disclosure['has_affiliate_disclosure']}")
    lines.append(f"     Has info-box class: {disclosure['has_info_box_class']}")
    lines.append(f"     Has wp:html blocks: {disclosure['has_wp_html_blocks']}")
    lines.append(f"     wp:html block count: {disclosure['wp_html_block_count']}")
    lines.append(f"     Has styled divs (inline bg): {disclosure['has_styled_divs']}")
    lines.append(f"     Custom CSS classes found: {disclosure['has_custom_css_classes']}")
    lines.append("")

    # 8. Structure pattern
    lines.append("  8. STRUCTURE PATTERN:")
    pattern = analysis["structure"]
    if pattern:
        lines.append(f"     Detected sections: {' -> '.join(pattern)}")
    else:
        lines.append("     [Could not detect structure pattern]")
    lines.append("")

    # First 300 chars of raw content for manual inspection
    lines.append("  RAW CONTENT PREVIEW (first 500 chars):")
    preview = content_raw[:500].replace("\n", "\n     ")
    lines.append(f"     {preview}")
    lines.append("")

    # Count of all headings with text
    heading_texts = re.findall(r'<h([2-6])[^>]*>(.*?)</h\1>', content_raw, re.IGNORECASE)
    if heading_texts:
        lines.append("  ALL HEADINGS IN CONTENT:")
        for level, text in heading_texts:
            clean_text = re.sub(r'<[^>]+>', '', text).strip()
            lines.append(f"     H{level}: {clean_text}")
        lines.append("")

    return "\n".join(lines)


def main():
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("  PETHUB ONLINE - PAGE/POST LAYOUT AUDIT REPORT")
    report_lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report_lines.append(f"  Site: https://pethubonline.com")
    report_lines.append("=" * 80)
    report_lines.append("")

    all_block_types = set()
    items_with_h1 = []
    items_without_faq = []
    items_without_related = []
    items_with_wp_html = []

    # Process pages
    report_lines.append("\n" + "#" * 80)
    report_lines.append("  SECTION 1: PAGES")
    report_lines.append("#" * 80 + "\n")

    for page_info in PAGES:
        print(f"Fetching page {page_info['id']}...")
        data = fetch_item("pages", page_info["id"])

        content_raw = data.get("content", {}).get("raw", "") if "error" not in data else ""
        blocks = extract_blocks(content_raw)

        analysis = {
            "block_types": get_unique_block_types(blocks),
            "hero": check_hero_image(content_raw, blocks),
            "info_strip": check_info_strip(content_raw),
            "headings": check_heading_hierarchy(content_raw),
            "faq": check_faq_section(content_raw),
            "related": check_related_reading(content_raw),
            "disclosure": check_affiliate_disclosure(content_raw),
            "structure": analyze_structure_pattern(content_raw, blocks),
        }

        # Track summary stats
        all_block_types.update(analysis["block_types"])
        if analysis["headings"]["has_h1_in_body"]:
            items_with_h1.append(f"Page {page_info['id']}")
        if not any(analysis["faq"].values()):
            items_without_faq.append(f"Page {page_info['id']}")
        if not analysis["related"]["has_related_heading"]:
            items_without_related.append(f"Page {page_info['id']}")
        if analysis["disclosure"]["has_wp_html_blocks"]:
            items_with_wp_html.append(f"Page {page_info['id']} ({analysis['disclosure']['wp_html_block_count']} blocks)")

        report_lines.append(format_report("Page", page_info, data, analysis))

    # Process posts
    report_lines.append("\n" + "#" * 80)
    report_lines.append("  SECTION 2: POSTS")
    report_lines.append("#" * 80 + "\n")

    for post_info in POSTS:
        print(f"Fetching post {post_info['id']}...")
        data = fetch_item("posts", post_info["id"])

        content_raw = data.get("content", {}).get("raw", "") if "error" not in data else ""
        blocks = extract_blocks(content_raw)

        analysis = {
            "block_types": get_unique_block_types(blocks),
            "hero": check_hero_image(content_raw, blocks),
            "info_strip": check_info_strip(content_raw),
            "headings": check_heading_hierarchy(content_raw),
            "faq": check_faq_section(content_raw),
            "related": check_related_reading(content_raw),
            "disclosure": check_affiliate_disclosure(content_raw),
            "structure": analyze_structure_pattern(content_raw, blocks),
        }

        # Track summary stats
        all_block_types.update(analysis["block_types"])
        if analysis["headings"]["has_h1_in_body"]:
            items_with_h1.append(f"Post {post_info['id']}")
        if not any(analysis["faq"].values()):
            items_without_faq.append(f"Post {post_info['id']}")
        if not analysis["related"]["has_related_heading"]:
            items_without_related.append(f"Post {post_info['id']}")
        if analysis["disclosure"]["has_wp_html_blocks"]:
            items_with_wp_html.append(f"Post {post_info['id']} ({analysis['disclosure']['wp_html_block_count']} blocks)")

        report_lines.append(format_report("Post", post_info, data, analysis))

    # Summary section
    report_lines.append("\n" + "#" * 80)
    report_lines.append("  SECTION 3: CROSS-ITEM SUMMARY & FINDINGS")
    report_lines.append("#" * 80 + "\n")

    report_lines.append("  ALL UNIQUE BLOCK TYPES ACROSS ALL ITEMS:")
    for bt in sorted(all_block_types):
        report_lines.append(f"    - {bt}")
    report_lines.append("")

    report_lines.append("  ITEMS WITH H1 IN BODY (should be fixed):")
    if items_with_h1:
        for item in items_with_h1:
            report_lines.append(f"    - {item}")
    else:
        report_lines.append("    [None - all clean]")
    report_lines.append("")

    report_lines.append("  ITEMS WITHOUT FAQ SECTION:")
    if items_without_faq:
        for item in items_without_faq:
            report_lines.append(f"    - {item}")
    else:
        report_lines.append("    [All have FAQ sections]")
    report_lines.append("")

    report_lines.append("  ITEMS WITHOUT RELATED READING SECTION:")
    if items_without_related:
        for item in items_without_related:
            report_lines.append(f"    - {item}")
    else:
        report_lines.append("    [All have related reading]")
    report_lines.append("")

    report_lines.append("  ITEMS WITH wp:html BLOCKS (legacy/non-Gutenberg):")
    if items_with_wp_html:
        for item in items_with_wp_html:
            report_lines.append(f"    - {item}")
    else:
        report_lines.append("    [None - all using native Gutenberg blocks]")
    report_lines.append("")

    report_lines.append("  TEMPLATE LIBRARY RECOMMENDATIONS:")
    report_lines.append("    Based on the audit, the following reusable patterns should be templated:")
    report_lines.append("    1. Educational Post Template (intro -> body -> FAQ -> related -> trust)")
    report_lines.append("    2. Hub/Category Page Template (intro -> subcategory grid -> links)")
    report_lines.append("    3. Trust/About Page Template (hero -> mission -> trust signals)")
    report_lines.append("    4. Pillar Post Template (ToC -> deep sections -> FAQ -> related)")
    report_lines.append("    5. Standard Info-Box / Disclosure Block Pattern")
    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("  END OF AUDIT REPORT")
    report_lines.append("=" * 80)

    full_report = "\n".join(report_lines)

    # Save report
    output_path = "/var/lib/freelancer/projects/40416335/phase10d/layout_audit_report.txt"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(full_report)

    print("\n" + full_report)
    print(f"\n\nReport saved to: {output_path}")


if __name__ == "__main__":
    main()
