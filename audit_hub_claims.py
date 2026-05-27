#!/usr/bin/env python3
"""
Hub/Category Page Overclaim & Trust Discipline Audit
=====================================================
Fetches hub/category pages from pethubonline.com via WP REST API (context=edit)
and audits for overclaims, trust signal issues, affiliate disclosure, info strips,
media, and comment status.
"""

import requests
import re
import json
import html
import os
from datetime import datetime

# --- Config ---
BASE_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
PAGE_IDS = [63, 1041, 37, 38, 1141, 1144, 1146, 1149]

OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase10d"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "hub_claims_audit.txt")

# Overclaim patterns: (label, regex_pattern)
OVERCLAIM_PATTERNS = [
    ("expert/experts", r'\bexperts?\b'),
    ("tested/testing/we test", r'\b(?:tested|testing|we\s+test)\b'),
    ("vet-backed/vet-approved/veterinary approved", r'\b(?:vet[\-\s]?backed|vet[\-\s]?approved|veterinary\s+approved)\b'),
    ("top rated/top-rated", r'\btop[\-\s]rated\b'),
    ("best (ranking context)", r'\bbest\b'),
    ("number one / #1", r'(?:\bnumber\s+one\b|#1)'),
    ("proven/clinically proven", r'\b(?:clinically\s+)?proven\b'),
    ("guaranteed", r'\bguaranteed\b'),
    ("we recommend", r'\bwe\s+recommend\b'),
    ("our team", r'\bour\s+team\b'),
    ("real user feedback / owner-approved", r'\b(?:real\s+user\s+feedback|owner[\-\s]approved)\b'),
    ("independently reviewed", r'\bindependently\s+reviewed\b'),
]

# Trust block phrases to flag
TRUST_BLOCK_PHRASES = [
    "expert testing",
    "updated reviews",
    "pet owner approved",
    "owner approved",
    "owner-approved",
    "expert-tested",
    "expert tested",
    "independently reviewed",
    "vet-backed",
    "vet backed",
    "real user feedback",
]


def strip_html(raw_html):
    """Remove HTML tags and decode entities for readable context."""
    text = re.sub(r'<[^>]+>', ' ', raw_html)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_surrounding_context(text, match_start, match_end, chars=120):
    """Get surrounding context around a match."""
    start = max(0, match_start - chars)
    end = min(len(text), match_end + chars)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{text[start:end]}{suffix}"


def check_overclaims(raw_content, plain_text):
    """Check for overclaim phrases. Returns list of findings."""
    findings = []
    for label, pattern in OVERCLAIM_PATTERNS:
        matches = list(re.finditer(pattern, plain_text, re.IGNORECASE))
        if matches:
            for m in matches:
                context = get_surrounding_context(plain_text, m.start(), m.end())
                # For "best", filter out non-ranking uses
                if label == "best (ranking context)":
                    # Skip "best friend", "best practice", "do your best" etc.
                    surrounding = plain_text[max(0, m.start()-30):min(len(plain_text), m.end()+30)].lower()
                    if any(x in surrounding for x in ['best friend', 'best practice', 'do your best', 'best of luck', "pet's best"]):
                        continue
                findings.append({
                    'pattern': label,
                    'matched': m.group(),
                    'context': context,
                })
    return findings


def check_trust_blocks(raw_content, plain_text):
    """Check for trust signal blocks and flag overclaims within them."""
    findings = []

    # Look for trust block headings
    trust_block_patterns = [
        r'why\s+pet\s+owners?\s+trust',
        r'why\s+trust\s+(?:pet\s+hub|pethub)',
        r'trusted\s+by\s+pet\s+owners',
        r'our\s+trust\s+promise',
    ]

    has_trust_block = False
    for pat in trust_block_patterns:
        if re.search(pat, plain_text, re.IGNORECASE):
            has_trust_block = True
            match = re.search(pat, plain_text, re.IGNORECASE)
            findings.append({
                'type': 'trust_block_found',
                'heading': match.group(),
                'context': get_surrounding_context(plain_text, match.start(), match.end(), 200),
            })

    # Check for specific trust-block overclaim phrases
    trust_overclaims = []
    for phrase in TRUST_BLOCK_PHRASES:
        if re.search(re.escape(phrase), plain_text, re.IGNORECASE):
            match = re.search(re.escape(phrase), plain_text, re.IGNORECASE)
            trust_overclaims.append({
                'phrase': phrase,
                'context': get_surrounding_context(plain_text, match.start(), match.end(), 150),
            })

    if trust_overclaims:
        findings.append({
            'type': 'trust_block_overclaims',
            'items': trust_overclaims,
        })

    return has_trust_block, findings


def check_info_strip(raw_content):
    """Check for a top info strip (Last Updated, Website, Business)."""
    # Look in raw HTML for info strip patterns
    has_info_strip = False
    details = []

    info_patterns = [
        (r'last\s+updated', 'Last Updated'),
        (r'website\s*:', 'Website'),
        (r'business\s*:', 'Business'),
        (r'info[\-_]?strip', 'Info Strip class/id'),
        (r'wp-block-columns.*?last\s+updated', 'Columns block with Last Updated'),
    ]

    for pat, label in info_patterns:
        if re.search(pat, raw_content, re.IGNORECASE):
            has_info_strip = True
            details.append(label)

    return has_info_strip, details


def check_affiliate_disclosure(raw_content):
    """Check for affiliate disclosure and whether it's a wp:html block."""
    has_disclosure = False
    is_wp_html_block = False
    disclosure_text = ""

    # Check for affiliate/disclosure keywords
    disclosure_patterns = [
        r'affiliate\s+(?:disclosure|notice|disclaimer)',
        r'commission',
        r'we\s+(?:may\s+)?earn\s+(?:a\s+)?commission',
        r'affiliate\s+links?',
        r'paid\s+(?:commission|referral)',
    ]

    for pat in disclosure_patterns:
        match = re.search(pat, raw_content, re.IGNORECASE)
        if match:
            has_disclosure = True
            # Get surrounding context from raw HTML
            start = max(0, match.start() - 200)
            end = min(len(raw_content), match.end() + 200)
            disclosure_text = raw_content[start:end]
            break

    # Check if it's inside a wp:html block
    if has_disclosure:
        # Look for <!-- wp:html --> blocks containing affiliate language
        wp_html_blocks = re.findall(r'<!-- wp:html -->(.*?)<!-- /wp:html -->', raw_content, re.DOTALL | re.IGNORECASE)
        for block in wp_html_blocks:
            for pat in disclosure_patterns:
                if re.search(pat, block, re.IGNORECASE):
                    is_wp_html_block = True
                    break

    return has_disclosure, is_wp_html_block, disclosure_text


def check_media(page_data, raw_content):
    """Check for hero/cover image and featured media."""
    featured_media_id = page_data.get('featured_media', 0)
    has_featured = featured_media_id > 0

    # Check for cover block or hero image in content
    has_cover = bool(re.search(r'wp:cover|wp:image|<img\s', raw_content, re.IGNORECASE))
    cover_details = []
    if re.search(r'wp:cover', raw_content, re.IGNORECASE):
        cover_details.append('wp:cover block')
    if re.search(r'wp:image', raw_content, re.IGNORECASE):
        cover_details.append('wp:image block(s)')

    return has_featured, featured_media_id, has_cover, cover_details


def fetch_page(session, page_id):
    """Fetch a single page with context=edit."""
    url = f"{BASE_URL}/pages/{page_id}"
    params = {'context': 'edit'}
    resp = session.get(url, params=params, auth=AUTH, timeout=30)
    resp.raise_for_status()
    return resp.json()


def audit_page(session, page_id):
    """Run full audit on a single page."""
    result = {
        'page_id': page_id,
        'errors': [],
    }

    try:
        page_data = fetch_page(session, page_id)
    except Exception as e:
        result['errors'].append(f"FETCH ERROR: {e}")
        return result

    title = page_data.get('title', {})
    if isinstance(title, dict):
        title = title.get('raw', title.get('rendered', f'Page {page_id}'))
    result['title'] = title

    slug = page_data.get('slug', '')
    result['slug'] = slug
    result['status'] = page_data.get('status', 'unknown')
    result['link'] = page_data.get('link', '')

    # Get raw content
    content = page_data.get('content', {})
    if isinstance(content, dict):
        raw_content = content.get('raw', content.get('rendered', ''))
    else:
        raw_content = str(content)

    result['content_length'] = len(raw_content)
    plain_text = strip_html(raw_content)
    result['plain_text_length'] = len(plain_text)

    # Comment status
    result['comment_status'] = page_data.get('comment_status', 'unknown')

    # 1. Overclaim audit
    result['overclaims'] = check_overclaims(raw_content, plain_text)

    # 2. Trust signal audit
    has_trust_block, trust_findings = check_trust_blocks(raw_content, plain_text)
    result['has_trust_block'] = has_trust_block
    result['trust_findings'] = trust_findings

    # 3. Info strip check
    has_info_strip, info_details = check_info_strip(raw_content)
    result['has_info_strip'] = has_info_strip
    result['info_strip_details'] = info_details

    # 4. Affiliate disclosure
    has_disclosure, is_wp_html, disclosure_text = check_affiliate_disclosure(raw_content)
    result['has_affiliate_disclosure'] = has_disclosure
    result['disclosure_is_wp_html_block'] = is_wp_html
    result['disclosure_snippet'] = disclosure_text[:300] if disclosure_text else ""

    # 5. Media
    has_featured, featured_id, has_cover, cover_details = check_media(page_data, raw_content)
    result['has_featured_media'] = has_featured
    result['featured_media_id'] = featured_id
    result['has_cover_image'] = has_cover
    result['cover_details'] = cover_details

    return result


def format_report(results):
    """Format results into a readable report."""
    lines = []
    lines.append("=" * 80)
    lines.append("PET HUB ONLINE - HUB/CATEGORY PAGE OVERCLAIM & TRUST AUDIT")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 80)
    lines.append("")

    # Summary
    total_overclaims = sum(len(r.get('overclaims', [])) for r in results)
    pages_with_overclaims = sum(1 for r in results if r.get('overclaims'))
    pages_with_trust_issues = sum(1 for r in results
                                   if any(f.get('type') == 'trust_block_overclaims'
                                          for f in r.get('trust_findings', [])))

    lines.append("EXECUTIVE SUMMARY")
    lines.append("-" * 40)
    lines.append(f"Pages audited:            {len(results)}")
    lines.append(f"Total overclaim instances: {total_overclaims}")
    lines.append(f"Pages with overclaims:    {pages_with_overclaims}/{len(results)}")
    lines.append(f"Pages with trust issues:  {pages_with_trust_issues}/{len(results)}")
    lines.append("")

    # Per-page details
    for r in results:
        lines.append("=" * 80)
        page_id = r.get('page_id', '?')
        title = r.get('title', 'Unknown')
        lines.append(f"PAGE {page_id}: {title}")
        lines.append(f"  Slug: {r.get('slug', '?')}")
        lines.append(f"  Status: {r.get('status', '?')}")
        lines.append(f"  URL: {r.get('link', '?')}")
        lines.append(f"  Content length: {r.get('content_length', 0)} chars (raw), {r.get('plain_text_length', 0)} chars (plain)")
        lines.append(f"  Comment status: {r.get('comment_status', '?')}")
        lines.append("")

        if r.get('errors'):
            for err in r['errors']:
                lines.append(f"  ** ERROR: {err}")
            lines.append("")
            continue

        # --- OVERCLAIM AUDIT ---
        overclaims = r.get('overclaims', [])
        lines.append(f"  [1] OVERCLAIM AUDIT: {len(overclaims)} instance(s) found")
        if overclaims:
            lines.append("  " + "-" * 60)
            for i, oc in enumerate(overclaims, 1):
                lines.append(f"    ({i}) Pattern: {oc['pattern']}")
                lines.append(f"        Matched: \"{oc['matched']}\"")
                lines.append(f"        Context: {oc['context']}")
                lines.append("")
        else:
            lines.append("      CLEAN - No overclaim phrases detected.")
            lines.append("")

        # --- TRUST SIGNAL AUDIT ---
        lines.append(f"  [2] TRUST SIGNAL AUDIT:")
        if r.get('has_trust_block'):
            lines.append("      Trust block FOUND on this page.")
        else:
            lines.append("      No trust block heading detected.")

        trust_findings = r.get('trust_findings', [])
        for tf in trust_findings:
            if tf.get('type') == 'trust_block_found':
                lines.append(f"      Heading: \"{tf['heading']}\"")
                lines.append(f"      Context: {tf['context'][:200]}")
            elif tf.get('type') == 'trust_block_overclaims':
                lines.append(f"      ** TRUST BLOCK OVERCLAIMS ({len(tf['items'])} found):")
                for item in tf['items']:
                    lines.append(f"         - \"{item['phrase']}\"")
                    lines.append(f"           Context: {item['context'][:200]}")
        lines.append("")

        # --- INFO STRIP ---
        lines.append(f"  [3] INFO STRIP CHECK:")
        if r.get('has_info_strip'):
            lines.append(f"      Present. Elements: {', '.join(r.get('info_strip_details', []))}")
        else:
            lines.append("      NOT FOUND - No info strip detected.")
        lines.append("")

        # --- AFFILIATE DISCLOSURE ---
        lines.append(f"  [4] AFFILIATE DISCLOSURE CHECK:")
        if r.get('has_affiliate_disclosure'):
            lines.append(f"      Present.")
            lines.append(f"      Is wp:html block: {'YES' if r.get('disclosure_is_wp_html_block') else 'NO'}")
            if r.get('disclosure_snippet'):
                snippet = strip_html(r['disclosure_snippet'])[:200]
                lines.append(f"      Snippet: {snippet}")
        else:
            lines.append("      NOT FOUND - No affiliate disclosure detected.")
        lines.append("")

        # --- IMAGE/MEDIA ---
        lines.append(f"  [5] IMAGE/MEDIA:")
        lines.append(f"      Featured media: {'YES (ID: ' + str(r.get('featured_media_id')) + ')' if r.get('has_featured_media') else 'NO'}")
        lines.append(f"      Cover/hero image in content: {'YES' if r.get('has_cover_image') else 'NO'}")
        if r.get('cover_details'):
            lines.append(f"      Details: {', '.join(r['cover_details'])}")
        lines.append("")

        # --- COMMENT STATUS ---
        lines.append(f"  [6] COMMENT STATUS: {r.get('comment_status', 'unknown').upper()}")
        lines.append("")

    # === ACTIONABLE SUMMARY ===
    lines.append("=" * 80)
    lines.append("ACTIONABLE FINDINGS - PAGES NEEDING FIXES")
    lines.append("=" * 80)
    lines.append("")

    for r in results:
        if r.get('errors'):
            continue
        page_id = r.get('page_id', '?')
        title = r.get('title', 'Unknown')
        issues = []

        if r.get('overclaims'):
            patterns_found = list(set(oc['pattern'] for oc in r['overclaims']))
            issues.append(f"OVERCLAIMS ({len(r['overclaims'])} instances): {', '.join(patterns_found)}")

        trust_findings = r.get('trust_findings', [])
        for tf in trust_findings:
            if tf.get('type') == 'trust_block_overclaims':
                phrases = [item['phrase'] for item in tf['items']]
                issues.append(f"TRUST BLOCK OVERCLAIMS: {', '.join(phrases)}")

        if not r.get('has_info_strip'):
            issues.append("MISSING info strip")

        if not r.get('has_affiliate_disclosure'):
            issues.append("MISSING affiliate disclosure")
        elif not r.get('disclosure_is_wp_html_block'):
            issues.append("Affiliate disclosure is NOT a wp:html block")

        if not r.get('has_featured_media') and not r.get('has_cover_image'):
            issues.append("MISSING hero/cover image and featured media")

        if r.get('comment_status') == 'open':
            issues.append("Comments are OPEN (should likely be closed for hub pages)")

        if issues:
            lines.append(f"PAGE {page_id} ({title}):")
            for issue in issues:
                lines.append(f"  - {issue}")
            lines.append("")
        else:
            lines.append(f"PAGE {page_id} ({title}): ALL CLEAN")
            lines.append("")

    return "\n".join(lines)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    s = requests.Session()
    s.headers['Accept-Encoding'] = 'gzip, deflate'
    s.headers['User-Agent'] = 'PetHub-Audit/1.0'

    results = []
    for page_id in PAGE_IDS:
        print(f"Auditing page {page_id}...")
        result = audit_page(s, page_id)
        title = result.get('title', 'Unknown')
        overclaims = len(result.get('overclaims', []))
        print(f"  -> {title} | {overclaims} overclaim(s)")
        results.append(result)

    report = format_report(results)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\nReport saved to: {OUTPUT_FILE}")
    print("\n" + report)


if __name__ == '__main__':
    main()
