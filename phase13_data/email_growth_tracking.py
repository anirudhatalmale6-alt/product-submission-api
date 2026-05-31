#!/usr/bin/env python3
"""
Phase 13K: Email List Growth Tracking
Audits newsletter/email infrastructure and generates tracking dashboard data.
"""

import subprocess
import json
import csv
import re
import time
from html.parser import HTMLParser
from collections import defaultdict

WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_API = "https://pethubonline.com/wp-json/wp/v2"

OUTPUT_CSV = "/var/lib/freelancer/projects/40416335/phase13_data/Email_Growth_Dashboard.csv"


def wp_api_call(endpoint):
    url = f"{WP_API}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", f"{WP_USER}:{WP_PASS}", url],
        capture_output=True, text=True
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def check_newsletter_pages():
    """Check for newsletter/signup pages."""
    pages = wp_api_call("pages?status=publish&per_page=100&_fields=id,title,slug,content")
    newsletter_pages = []

    if pages and isinstance(pages, list):
        for page in pages:
            title = page['title']['rendered'] if isinstance(page['title'], dict) else page['title']
            content = page['content']['rendered'] if isinstance(page['content'], dict) else ''
            slug = page.get('slug', '')

            # Check for newsletter/signup signals
            signals = []
            if re.search(r'newsletter|subscribe|sign.?up|email.?list|mailing.?list', title, re.IGNORECASE):
                signals.append('title_match')
            if re.search(r'newsletter|subscribe|sign.?up|email.?list', content, re.IGNORECASE):
                signals.append('content_match')
            if re.search(r'<form|<input[^>]*type=["\']email', content, re.IGNORECASE):
                signals.append('has_form')
            if re.search(r'mailchimp|convertkit|mailerlite|sendinblue|brevo', content, re.IGNORECASE):
                signals.append('esp_detected')

            if signals:
                newsletter_pages.append({
                    'id': page['id'],
                    'title': title,
                    'slug': slug,
                    'signals': signals,
                    'url': f'https://pethubonline.com/{slug}/',
                })

    return newsletter_pages


def check_signup_forms_in_posts():
    """Check how many posts have email signup forms/CTAs."""
    posts_with_signup = 0
    posts_without_signup = 0
    total_posts = 0

    for page_num in range(1, 5):
        data = wp_api_call(f"posts?status=publish&per_page=50&page={page_num}&_fields=id,content")
        if not data or (isinstance(data, dict) and data.get('code')):
            break

        for post in data:
            total_posts += 1
            content = post['content']['rendered'] if isinstance(post['content'], dict) else ''

            has_signup = bool(re.search(
                r'newsletter|subscribe|sign.?up|<input[^>]*type=["\']email|mailchimp|convertkit',
                content, re.IGNORECASE
            ))

            if has_signup:
                posts_with_signup += 1
            else:
                posts_without_signup += 1

        if len(data) < 50:
            break
        time.sleep(1)

    return {
        'total_posts': total_posts,
        'with_signup': posts_with_signup,
        'without_signup': posts_without_signup,
        'coverage_pct': round(posts_with_signup / max(total_posts, 1) * 100, 1),
    }


def check_lead_magnets():
    """Check for lead magnets (downloads, guides, checklists)."""
    # Check posts and pages for lead magnet signals
    lead_magnets = []

    pages = wp_api_call("pages?status=publish&per_page=100&_fields=id,title,content,slug")
    posts = wp_api_call("posts?status=publish&per_page=50&_fields=id,title,content,slug")

    all_content = (pages or []) + (posts or [])

    for item in all_content:
        title = item['title']['rendered'] if isinstance(item['title'], dict) else item['title']
        content = item['content']['rendered'] if isinstance(item['content'], dict) else ''
        slug = item.get('slug', '')

        # Lead magnet signals
        if re.search(r'(free download|free guide|free checklist|free template|lead magnet|opt.?in|gated content)', content, re.IGNORECASE):
            lead_magnets.append({
                'title': title,
                'slug': slug,
                'type': 'lead_magnet_page',
            })
        elif re.search(r'(download.+free|get.+free|claim.+free).+(guide|checklist|template|ebook)', content, re.IGNORECASE):
            lead_magnets.append({
                'title': title,
                'slug': slug,
                'type': 'download_offer',
            })

    return lead_magnets


def check_popup_plugins():
    """Check for popup/optin plugins via WP API."""
    plugins = wp_api_call("plugins?_fields=plugin,name,status")
    popup_plugins = []

    optin_plugin_names = [
        'optinmonster', 'sumo', 'bloom', 'mailchimp', 'convertkit',
        'popup', 'optin', 'hustle', 'newsletter', 'mailerlite',
        'brevo', 'sendinblue', 'fluentcrm', 'wp-mail-smtp'
    ]

    if plugins and isinstance(plugins, list):
        for plugin in plugins:
            name = (plugin.get('name', '') or '').lower()
            plugin_slug = (plugin.get('plugin', '') or '').lower()
            status = plugin.get('status', '')

            for optin_name in optin_plugin_names:
                if optin_name in name or optin_name in plugin_slug:
                    popup_plugins.append({
                        'name': plugin.get('name', ''),
                        'slug': plugin.get('plugin', ''),
                        'status': status,
                    })
                    break

    return popup_plugins


def main():
    print("=" * 70)
    print("PHASE 13K: EMAIL LIST GROWTH - INFRASTRUCTURE AUDIT")
    print("=" * 70)
    print()

    print("[1/4] Checking newsletter pages...")
    newsletter_pages = check_newsletter_pages()
    print(f"  Newsletter pages found: {len(newsletter_pages)}")
    for np in newsletter_pages:
        print(f"    - {np['title']} ({', '.join(np['signals'])})")
    print()

    print("[2/4] Checking signup form coverage across posts...")
    signup_coverage = check_signup_forms_in_posts()
    print(f"  Total posts: {signup_coverage['total_posts']}")
    print(f"  With signup form/CTA: {signup_coverage['with_signup']}")
    print(f"  Without signup: {signup_coverage['without_signup']}")
    print(f"  Coverage: {signup_coverage['coverage_pct']}%")
    print()

    print("[3/4] Checking lead magnets...")
    lead_magnets = check_lead_magnets()
    print(f"  Lead magnets found: {len(lead_magnets)}")
    for lm in lead_magnets:
        print(f"    - {lm['title']} ({lm['type']})")
    print()

    print("[4/4] Checking optin/popup plugins...")
    popup_plugins = check_popup_plugins()
    print(f"  Email/popup plugins: {len(popup_plugins)}")
    for pp in popup_plugins:
        print(f"    - {pp['name']} (status: {pp['status']})")
    print()

    # Generate dashboard CSV
    rows = []

    # Infrastructure status
    rows.append({
        'metric': 'Newsletter Pages',
        'value': str(len(newsletter_pages)),
        'status': 'active' if newsletter_pages else 'missing',
        'action_needed': '' if newsletter_pages else 'Create dedicated newsletter signup page',
    })
    rows.append({
        'metric': 'Signup Form Coverage',
        'value': f"{signup_coverage['coverage_pct']}%",
        'status': 'good' if signup_coverage['coverage_pct'] > 50 else 'needs_work',
        'action_needed': '' if signup_coverage['coverage_pct'] > 50 else f"Add signup CTAs to {signup_coverage['without_signup']} posts",
    })
    rows.append({
        'metric': 'Lead Magnets',
        'value': str(len(lead_magnets)),
        'status': 'active' if lead_magnets else 'missing',
        'action_needed': '' if lead_magnets else 'Create 3-5 cluster-specific lead magnets (checklists, guides)',
    })
    rows.append({
        'metric': 'Email Plugins',
        'value': str(len(popup_plugins)),
        'status': 'active' if popup_plugins else 'missing',
        'action_needed': '' if popup_plugins else 'Install email marketing plugin (MailerLite/ConvertKit recommended)',
    })
    rows.append({
        'metric': 'Posts with Email CTA',
        'value': str(signup_coverage['with_signup']),
        'status': 'tracking',
        'action_needed': 'Target: 80%+ posts should have email CTA',
    })
    rows.append({
        'metric': 'Conversion Tracking',
        'value': 'Not configured',
        'status': 'missing',
        'action_needed': 'Set up GA4 event tracking for form submissions',
    })

    fieldnames = ['metric', 'value', 'status', 'action_needed']
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Dashboard CSV: {OUTPUT_CSV}")
    print()

    # Summary
    print("=" * 70)
    print("EMAIL GROWTH INFRASTRUCTURE STATUS")
    print("=" * 70)
    print()

    infra_score = 0
    if newsletter_pages:
        infra_score += 25
    if signup_coverage['coverage_pct'] > 20:
        infra_score += 25
    if lead_magnets:
        infra_score += 25
    if popup_plugins:
        infra_score += 25

    print(f"  Infrastructure readiness: {infra_score}/100")
    print()
    print("  RECOMMENDATIONS:")
    if not newsletter_pages:
        print("  1. Create a dedicated /newsletter/ page with compelling signup copy")
    if signup_coverage['coverage_pct'] < 50:
        print(f"  2. Add email signup CTAs to remaining {signup_coverage['without_signup']} posts")
    if not lead_magnets:
        print("  3. Create lead magnets:")
        print("     - 'Complete Indoor Cat Care Checklist' (PDF)")
        print("     - 'UK Dog Food Comparison Chart' (PDF)")
        print("     - 'New Puppy Essentials Guide' (PDF)")
    if not popup_plugins:
        print("  4. Install email marketing integration (MailerLite free tier recommended)")
    print("  5. Set up GA4 conversion tracking for email signups")
    print("  6. Create welcome email sequence (5 emails)")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
