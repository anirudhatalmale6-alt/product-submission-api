#!/usr/bin/env python3
"""Add cross-links and last-updated dates to the 4 trust/methodology pages."""

import requests, re, html as html_mod
from datetime import datetime, timezone
from gutenberg_utils import wrap_paragraph, wrap_heading, wrap_separator, validate_gutenberg, safe_update_content

WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"

s = requests.Session()
s.auth = (WP_USER, WP_PASS)
s.headers['Accept-Encoding'] = 'gzip, deflate'

TODAY = datetime.now(timezone.utc).strftime('%d %B %Y')

TRUST_PAGES = {
    4402: {
        'title': 'How We Research Pet Products',
        'slug': 'how-we-research-pet-products',
    },
    4403: {
        'title': 'Our Editorial Process',
        'slug': 'our-editorial-process',
    },
    300: {
        'title': 'Affiliate Disclosure',
        'slug': 'affiliate-disclosure',
    },
    4405: {
        'title': 'Corrections and Updates Policy',
        'slug': 'corrections-and-updates-policy',
    },
}

CROSS_LINK_BLOCK = '\n\n'.join([
    wrap_separator(),
    wrap_heading('Our Trust and Transparency Pages', level=2),
    wrap_paragraph(
        '<p>PetHub Online is committed to transparency in everything we publish. '
        'These pages explain how we work:</p>'
    ),
    '<!-- wp:list -->\n<ul>\n'
    '<li><a href="/how-we-research-pet-products">How We Research Pet Products</a> — Our research methodology and standards</li>\n'
    '<li><a href="/our-editorial-process">Our Editorial Process</a> — How content is created, reviewed, and maintained</li>\n'
    '<li><a href="/affiliate-disclosure">Affiliate Disclosure</a> — How affiliate relationships work and our commitment to honesty</li>\n'
    '<li><a href="/corrections-and-updates-policy">Corrections and Updates Policy</a> — How we handle errors and keep content current</li>\n'
    '</ul>\n<!-- /wp:list -->',
])


def add_last_updated(content, date_str):
    last_updated = wrap_paragraph(f'<p><em>Last updated: {date_str}</em></p>')
    return content.rstrip() + '\n\n' + last_updated


def remove_existing_cross_links(content):
    pattern = r'<!-- wp:separator -->.*?<!-- /wp:separator -->\s*<!-- wp:heading[^>]*-->\s*<h2[^>]*>Our Trust and Transparency Pages</h2>.*$'
    cleaned = re.sub(pattern, '', content, flags=re.DOTALL)
    return cleaned.rstrip()


def remove_existing_last_updated(content):
    content = re.sub(
        r'\n*<!-- wp:paragraph -->\s*<p><em>Last updated:.*?</em></p>\s*<!-- /wp:paragraph -->\s*$',
        '', content, flags=re.DOTALL
    )
    return content.rstrip()


print(f"Updating trust pages with cross-links and last-updated dates ({TODAY})")
print("=" * 60)

for pid, info in TRUST_PAGES.items():
    endpoint = 'pages'
    r = s.get(f"{WP_BASE}/{endpoint}/{pid}", params={'context': 'edit'})
    data = r.json()
    raw = data['content']['raw']
    title = html_mod.unescape(data['title'].get('raw', data['title'].get('rendered', '')))

    cleaned = remove_existing_cross_links(raw)
    cleaned = remove_existing_last_updated(cleaned)

    new_content = cleaned + '\n\n' + CROSS_LINK_BLOCK
    new_content = add_last_updated(new_content, TODAY)

    is_valid, issues = validate_gutenberg(new_content)
    if not is_valid:
        print(f"  VALIDATION FAILED {pid}: {title} — {issues}")
        continue

    ok, msg = safe_update_content(s, WP_BASE, endpoint, pid, new_content)
    if ok:
        print(f"  OK {pid}: {title}")
    else:
        print(f"  FAIL {pid}: {title} — {msg}")

print("\nDone.")
