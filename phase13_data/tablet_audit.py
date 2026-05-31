#!/usr/bin/env python3
"""
Phase 13H: Tablet & iPad Optimization Audit
Tests all critical pages at tablet viewport sizes using Playwright.
Generates Tablet_Optimization_Report.csv
"""

import subprocess
import json
import time
import csv
import re

WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_API = "https://pethubonline.com/wp-json/wp/v2"

OUTPUT_CSV = "/var/lib/freelancer/projects/40416335/phase13_data/Tablet_Optimization_Report.csv"
SCREENSHOT_DIR = "/var/lib/freelancer/projects/40416335/phase13_data/tablet_screenshots"

# Tablet viewports to test
VIEWPORTS = {
    'ipad_portrait': {'width': 768, 'height': 1024},
    'ipad_landscape': {'width': 1024, 'height': 768},
    'ipad_pro_portrait': {'width': 1024, 'height': 1366},
    'android_tablet': {'width': 800, 'height': 1280},
    'surface': {'width': 1366, 'height': 768},
}


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


def fetch_test_urls():
    """Fetch a representative set of URLs to test."""
    urls = []

    # Homepage
    urls.append({'url': 'https://pethubonline.com/', 'type': 'homepage'})

    # Get published posts (sample of 20)
    for page in range(1, 3):
        data = wp_api_call(f"posts?status=publish&per_page=10&page={page}&_fields=id,slug,title")
        if data and isinstance(data, list):
            for post in data:
                slug = post.get('slug', '')
                title = post['title']['rendered'] if isinstance(post['title'], dict) else post['title']
                urls.append({
                    'url': f'https://pethubonline.com/{slug}/',
                    'type': 'post',
                    'title': title
                })
        time.sleep(1)

    # Get pages
    data = wp_api_call("pages?status=publish&per_page=10&_fields=id,slug,title")
    if data and isinstance(data, list):
        for page in data:
            slug = page.get('slug', '')
            title = page['title']['rendered'] if isinstance(page['title'], dict) else page['title']
            urls.append({
                'url': f'https://pethubonline.com/{slug}/',
                'type': 'page',
                'title': title
            })

    # Category pages
    data = wp_api_call("categories?per_page=10&_fields=id,slug,name")
    if data and isinstance(data, list):
        for cat in data:
            slug = cat.get('slug', '')
            if slug and slug != 'uncategorized':
                urls.append({
                    'url': f'https://pethubonline.com/category/{slug}/',
                    'type': 'category',
                    'title': cat.get('name', slug)
                })

    return urls


def run_tablet_audit(urls):
    """Run Playwright-based tablet audit."""
    # Build Playwright script
    script = f'''
import json
import os
from playwright.sync_api import sync_playwright

URLS = {json.dumps(urls)}
VIEWPORTS = {json.dumps(VIEWPORTS)}
SCREENSHOT_DIR = "{SCREENSHOT_DIR}"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

results = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    for url_info in URLS:
        url = url_info['url']
        url_type = url_info['type']
        title = url_info.get('title', url)

        page_results = {{
            'url': url,
            'type': url_type,
            'title': title,
            'viewport_scores': {{}},
            'issues': [],
        }}

        for vp_name, vp_size in VIEWPORTS.items():
            context = browser.new_context(
                viewport=vp_size,
                user_agent='Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15'
            )
            page = context.new_page()

            try:
                page.goto(url, timeout=30000, wait_until='domcontentloaded')
                page.wait_for_timeout(2000)

                # Check for layout issues
                issues = []

                # 1. Check horizontal overflow
                has_overflow = page.evaluate("""
                    () => document.body.scrollWidth > window.innerWidth
                """)
                if has_overflow:
                    issues.append(f"horizontal-overflow@{{vp_name}}")

                # 2. Check if text is readable (font-size >= 14px on mobile)
                small_text = page.evaluate("""
                    () => {{
                        const elements = document.querySelectorAll('p, li, td, span');
                        let smallCount = 0;
                        for (let el of elements) {{
                            const style = window.getComputedStyle(el);
                            const size = parseFloat(style.fontSize);
                            if (size < 14 && el.textContent.trim().length > 10) smallCount++;
                        }}
                        return smallCount;
                    }}
                """)
                if small_text > 5:
                    issues.append(f"small-text({{small_text}})@{{vp_name}}")

                # 3. Check if images overflow container
                img_overflow = page.evaluate("""
                    () => {{
                        const imgs = document.querySelectorAll('img');
                        let overflow = 0;
                        for (let img of imgs) {{
                            if (img.naturalWidth > 0 && img.offsetWidth > window.innerWidth) overflow++;
                        }}
                        return overflow;
                    }}
                """)
                if img_overflow > 0:
                    issues.append(f"img-overflow({{img_overflow}})@{{vp_name}}")

                # 4. Check touch target sizes (buttons/links >= 44px)
                small_targets = page.evaluate("""
                    () => {{
                        const targets = document.querySelectorAll('a, button, input[type=submit]');
                        let small = 0;
                        for (let t of targets) {{
                            const rect = t.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {{
                                if (rect.height < 44 && rect.width < 44) small++;
                            }}
                        }}
                        return small;
                    }}
                """)
                if small_targets > 10:
                    issues.append(f"small-touch-targets({{small_targets}})@{{vp_name}}")

                # 5. Check navigation is accessible
                nav_visible = page.evaluate("""
                    () => {{
                        const nav = document.querySelector('nav, .main-navigation, .site-navigation, #primary-menu');
                        if (!nav) return true;
                        const style = window.getComputedStyle(nav);
                        return style.display !== 'none' && style.visibility !== 'hidden';
                    }}
                """)
                if not nav_visible:
                    has_hamburger = page.evaluate("""
                        () => {{
                            const toggles = document.querySelectorAll('.menu-toggle, .hamburger, [class*=toggle], [aria-label*=menu]');
                            return toggles.length > 0;
                        }}
                    """)
                    if not has_hamburger:
                        issues.append(f"nav-hidden-no-toggle@{{vp_name}}")

                # 6. Check content width utilization
                content_width_pct = page.evaluate("""
                    () => {{
                        const main = document.querySelector('main, .entry-content, .post-content, article');
                        if (!main) return 100;
                        const rect = main.getBoundingClientRect();
                        return Math.round((rect.width / window.innerWidth) * 100);
                    }}
                """)
                if content_width_pct < 70:
                    issues.append(f"underutilized-width({{content_width_pct}}%)@{{vp_name}}")

                # Calculate viewport score
                vp_score = 100
                vp_score -= 20 if has_overflow else 0
                vp_score -= min(15, small_text * 2)
                vp_score -= img_overflow * 10
                vp_score -= min(15, small_targets)
                vp_score -= 10 if (not nav_visible and not has_hamburger if not nav_visible else False) else 0
                vp_score -= max(0, (70 - content_width_pct)) // 3
                vp_score = max(0, vp_score)

                page_results['viewport_scores'][vp_name] = vp_score
                page_results['issues'].extend(issues)

            except Exception as e:
                page_results['viewport_scores'][vp_name] = 0
                page_results['issues'].append(f"load-error@{{vp_name}}: {{str(e)[:50]}}")

            finally:
                context.close()

        results.append(page_results)

    browser.close()

print(json.dumps(results))
'''

    # Write and run the script
    script_path = "/var/lib/freelancer/projects/40416335/phase13_data/tablet_playwright.py"
    with open(script_path, 'w') as f:
        f.write(script)

    print("  Running Playwright tablet audit (this may take a few minutes)...")
    result = subprocess.run(
        ["python3", script_path],
        capture_output=True, text=True, timeout=300
    )

    if result.returncode != 0:
        print(f"  Playwright error: {result.stderr[:500]}")
        return []

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  Parse error: {result.stdout[:500]}")
        return []


def main():
    print("=" * 70)
    print("PHASE 13H: TABLET & iPAD OPTIMIZATION AUDIT")
    print("=" * 70)
    print()

    print("[1/3] Fetching test URLs...")
    urls = fetch_test_urls()
    print(f"  URLs to test: {len(urls)}")
    print()

    print("[2/3] Running tablet viewport audit...")
    results = run_tablet_audit(urls)
    print(f"  Pages audited: {len(results)}")
    print()

    if not results:
        print("  ERROR: No results from audit. Check Playwright installation.")
        return

    # Process results for CSV
    print("[3/3] Generating report...")
    csv_rows = []
    for r in results:
        avg_score = sum(r['viewport_scores'].values()) / len(r['viewport_scores']) if r['viewport_scores'] else 0
        issues_str = "; ".join(r['issues']) if r['issues'] else "none"

        csv_rows.append({
            'url': r['url'],
            'type': r['type'],
            'title': r.get('title', ''),
            'ipad_portrait_score': r['viewport_scores'].get('ipad_portrait', 0),
            'ipad_landscape_score': r['viewport_scores'].get('ipad_landscape', 0),
            'ipad_pro_score': r['viewport_scores'].get('ipad_pro_portrait', 0),
            'android_tablet_score': r['viewport_scores'].get('android_tablet', 0),
            'surface_score': r['viewport_scores'].get('surface', 0),
            'average_score': round(avg_score, 1),
            'issues': issues_str,
            'issue_count': len(r['issues']),
        })

    csv_rows.sort(key=lambda x: x['average_score'])

    fieldnames = ['url', 'type', 'title', 'ipad_portrait_score', 'ipad_landscape_score',
                  'ipad_pro_score', 'android_tablet_score', 'surface_score',
                  'average_score', 'issues', 'issue_count']

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"  CSV written: {OUTPUT_CSV}")
    print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()

    avg_all = sum(r['average_score'] for r in csv_rows) / len(csv_rows) if csv_rows else 0
    above_95 = sum(1 for r in csv_rows if r['average_score'] >= 95)
    above_80 = sum(1 for r in csv_rows if r['average_score'] >= 80)
    below_70 = sum(1 for r in csv_rows if r['average_score'] < 70)

    print(f"  Pages tested: {len(csv_rows)}")
    print(f"  Average tablet score: {avg_all:.1f}/100")
    print(f"  Above 95% (excellent): {above_95}")
    print(f"  Above 80% (good): {above_80}")
    print(f"  Below 70% (needs work): {below_70}")
    print()

    # Issue frequency
    from collections import defaultdict
    issue_types = defaultdict(int)
    for r in csv_rows:
        if r['issues'] != 'none':
            for issue in r['issues'].split('; '):
                base_issue = issue.split('@')[0] if '@' in issue else issue
                issue_types[base_issue] += 1

    if issue_types:
        print("COMMON ISSUES:")
        print("-" * 50)
        for issue, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  [{count:3}] {issue}")

    print()
    print("WORST PERFORMING PAGES:")
    print("-" * 50)
    for r in csv_rows[:10]:
        title_short = r['title'][:45] + "..." if len(r['title']) > 45 else r['title']
        print(f"  Avg:{r['average_score']:5.1f} | {title_short}")
        if r['issues'] != 'none':
            print(f"         Issues: {r['issues'][:80]}")
        print()

    print("=" * 70)


if __name__ == "__main__":
    main()
