#!/usr/bin/env python3
"""Playwright tablet audit - tests 15 representative URLs across 3 key viewports."""
import json
import os
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = "/var/lib/freelancer/projects/40416335/phase13_data/tablet_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

VIEWPORTS = {
    'ipad_portrait': {'width': 768, 'height': 1024},
    'ipad_landscape': {'width': 1024, 'height': 768},
    'surface': {'width': 1366, 'height': 768},
}

URLS = [
    {'url': 'https://pethubonline.com/', 'type': 'homepage', 'title': 'Homepage'},
    {'url': 'https://pethubonline.com/best-cat-toys-uk/', 'type': 'post', 'title': 'Best Cat Toys UK'},
    {'url': 'https://pethubonline.com/best-dog-beds-uk/', 'type': 'post', 'title': 'Best Dog Beds UK'},
    {'url': 'https://pethubonline.com/best-dog-food-uk/', 'type': 'post', 'title': 'Best Dog Food UK'},
    {'url': 'https://pethubonline.com/best-cat-food-uk/', 'type': 'post', 'title': 'Best Cat Food UK'},
    {'url': 'https://pethubonline.com/indoor-cat-exercise/', 'type': 'post', 'title': 'Indoor Cat Exercise'},
    {'url': 'https://pethubonline.com/best-dog-harness-uk/', 'type': 'post', 'title': 'Best Dog Harness UK'},
    {'url': 'https://pethubonline.com/puppy-care-essentials-key-terms/', 'type': 'post', 'title': 'Puppy Care Essentials'},
    {'url': 'https://pethubonline.com/about-us/', 'type': 'page', 'title': 'About Us'},
    {'url': 'https://pethubonline.com/our-methodology/', 'type': 'page', 'title': 'Our Methodology'},
    {'url': 'https://pethubonline.com/category/cat-supplies/', 'type': 'category', 'title': 'Cat Supplies'},
    {'url': 'https://pethubonline.com/category/dog-supplies/', 'type': 'category', 'title': 'Dog Supplies'},
    {'url': 'https://pethubonline.com/best-interactive-cat-toys-uk/', 'type': 'post', 'title': 'Best Interactive Cat Toys'},
    {'url': 'https://pethubonline.com/best-orthopedic-dog-beds-uk/', 'type': 'post', 'title': 'Best Orthopedic Dog Beds'},
    {'url': 'https://pethubonline.com/seasonal-dog-care-keeping-your-dog-safe-year-round/', 'type': 'post', 'title': 'Seasonal Dog Care'},
]

results = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    for url_info in URLS:
        url = url_info['url']
        url_type = url_info['type']
        title = url_info.get('title', url)

        page_results = {
            'url': url,
            'type': url_type,
            'title': title,
            'viewport_scores': {},
            'issues': [],
        }

        for vp_name, vp_size in VIEWPORTS.items():
            context = browser.new_context(
                viewport=vp_size,
                user_agent='Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15'
            )
            page = context.new_page()

            try:
                page.goto(url, timeout=20000, wait_until='domcontentloaded')
                page.wait_for_timeout(1500)

                issues = []

                has_overflow = page.evaluate("() => document.body.scrollWidth > window.innerWidth")
                if has_overflow:
                    issues.append(f"horizontal-overflow@{vp_name}")

                small_text = page.evaluate("""() => {
                    const elements = document.querySelectorAll('p, li, td, span');
                    let smallCount = 0;
                    for (let el of elements) {
                        const style = window.getComputedStyle(el);
                        const size = parseFloat(style.fontSize);
                        if (size < 14 && el.textContent.trim().length > 10) smallCount++;
                    }
                    return smallCount;
                }""")
                if small_text > 5:
                    issues.append(f"small-text({small_text})@{vp_name}")

                img_overflow = page.evaluate("""() => {
                    const imgs = document.querySelectorAll('img');
                    let overflow = 0;
                    for (let img of imgs) {
                        if (img.naturalWidth > 0 && img.offsetWidth > window.innerWidth) overflow++;
                    }
                    return overflow;
                }""")
                if img_overflow > 0:
                    issues.append(f"img-overflow({img_overflow})@{vp_name}")

                small_targets = page.evaluate("""() => {
                    const targets = document.querySelectorAll('a, button, input[type=submit]');
                    let small = 0;
                    for (let t of targets) {
                        const rect = t.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            if (rect.height < 44 && rect.width < 44) small++;
                        }
                    }
                    return small;
                }""")
                if small_targets > 10:
                    issues.append(f"small-touch-targets({small_targets})@{vp_name}")

                content_width_pct = page.evaluate("""() => {
                    const main = document.querySelector('main, .entry-content, .post-content, article');
                    if (!main) return 100;
                    const rect = main.getBoundingClientRect();
                    return Math.round((rect.width / window.innerWidth) * 100);
                }""")
                if content_width_pct < 70:
                    issues.append(f"underutilized-width({content_width_pct}%)@{vp_name}")

                vp_score = 100
                vp_score -= 20 if has_overflow else 0
                vp_score -= min(15, small_text * 2)
                vp_score -= img_overflow * 10
                vp_score -= min(15, small_targets)
                vp_score -= max(0, (70 - content_width_pct)) // 3
                vp_score = max(0, vp_score)

                page_results['viewport_scores'][vp_name] = vp_score
                page_results['issues'].extend(issues)

                if vp_name == 'ipad_portrait':
                    safe_name = url.replace('https://pethubonline.com/', '').replace('/', '_') or 'home'
                    page.screenshot(path=f"{SCREENSHOT_DIR}/{safe_name}_tablet.png")

            except Exception as e:
                page_results['viewport_scores'][vp_name] = 0
                page_results['issues'].append(f"load-error@{vp_name}: {str(e)[:50]}")

            finally:
                context.close()

        results.append(page_results)

    browser.close()

print(json.dumps(results))
