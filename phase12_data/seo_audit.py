#!/usr/bin/env python3
"""
PetHub SEO Remediation Audit - Complete Version
Fetches all published posts from pethubonline.com, extracts SEO data from
multiple sources (REST API + Rank Math API + front-end scraping), and generates
a comprehensive SEO remediation plan.
"""

import subprocess
import json
import csv
import re
import sys
import time
from html import unescape
from html.parser import HTMLParser

# WordPress credentials
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_API = "https://pethubonline.com/wp-json/wp/v2"
RM_API = "https://pethubonline.com/wp-json/rankmath/v1"
AUTH = f"{WP_USER}:{WP_PASS}"

OUTPUT_CSV = "/var/lib/freelancer/projects/40416335/phase12_data/SEO_Remediation_Plan.csv"


class HTMLStripper(HTMLParser):
    """Strip HTML tags and extract plain text."""
    def __init__(self):
        super().__init__()
        self.result = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip = True

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip = False

    def handle_data(self, data):
        if not self.skip:
            self.result.append(data)

    def get_text(self):
        return ' '.join(self.result)


def strip_html(html_str):
    """Remove HTML tags and return plain text."""
    if not html_str:
        return ""
    s = HTMLStripper()
    try:
        s.feed(unescape(html_str))
    except Exception:
        return re.sub(r'<[^>]+>', '', html_str)
    return s.get_text().strip()


def curl_fetch(url, auth=True, timeout_sec=30):
    """Fetch a URL using curl subprocess."""
    cmd = ["curl", "-s", "--compressed"]
    if auth:
        cmd.extend(["-u", AUTH])
    cmd.append(url)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        return None

    if result.returncode != 0:
        return None
    return result.stdout


def curl_fetch_json(url, auth=True):
    """Fetch URL and parse as JSON."""
    raw = curl_fetch(url, auth=auth)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def fetch_all_posts():
    """Fetch all published posts with pagination."""
    all_posts = []
    page = 1
    per_page = 50

    while True:
        url = f"{WP_API}/posts?status=publish&per_page={per_page}&page={page}"
        print(f"  Fetching page {page}...")
        data = curl_fetch_json(url)

        if data is None or isinstance(data, dict):
            if isinstance(data, dict) and 'code' in data:
                print(f"    API error: {data.get('message', 'Unknown')}")
            break

        if not data:
            break

        all_posts.extend(data)
        print(f"    Got {len(data)} posts (total: {len(all_posts)})")

        if len(data) < per_page:
            break
        page += 1

    return all_posts


def fetch_rank_math_scores():
    """Fetch SEO scores and link stats from Rank Math API."""
    rm_data = {}
    page = 1

    while True:
        url = f"{RM_API}/links/posts?per_page=100&page={page}"
        print(f"  Fetching Rank Math page {page}...")
        data = curl_fetch_json(url)

        if not data or not isinstance(data, dict):
            break

        posts = data.get('posts', [])
        for p in posts:
            pid = str(p.get('post_id', ''))
            rm_data[pid] = {
                'rm_seo_score': int(p.get('seo_score', 0)),
                'rm_internal_links': int(p.get('internal_link_count', 0)),
                'rm_external_links': int(p.get('external_link_count', 0)),
                'rm_incoming_links': int(p.get('incoming_link_count', 0)),
                'is_orphan': p.get('is_orphan', False),
            }

        total_pages = int(data.get('pages', 1))
        if page >= total_pages:
            break
        page += 1

    print(f"    Rank Math data for {len(rm_data)} posts/pages")
    return rm_data


def scrape_front_end_meta(url):
    """Scrape a post's front-end HTML to extract SEO meta from Rank Math output."""
    raw = curl_fetch(url, auth=False, timeout_sec=20)
    if not raw:
        return {}

    meta = {}

    # Extract <title>
    title_match = re.search(r'<title>([^<]+)</title>', raw)
    if title_match:
        meta['seo_title'] = unescape(title_match.group(1)).strip()

    # Extract meta description
    desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']', raw)
    if desc_match:
        meta['meta_desc'] = unescape(desc_match.group(1)).strip()

    # Extract focus keyword from schema JSON-LD
    schema_match = re.search(r'<script[^>]+class="rank-math-schema"[^>]*>(.*?)</script>', raw, re.DOTALL)
    if schema_match:
        try:
            schema = json.loads(schema_match.group(1))
            graph = schema.get('@graph', [])
            for item in graph:
                if item.get('@type') == 'Article' or (isinstance(item.get('@type'), list) and 'Article' in item.get('@type', [])):
                    kw = item.get('keywords', '')
                    if kw:
                        meta['focus_keyword'] = kw
                    break
        except (json.JSONDecodeError, AttributeError):
            pass

    # Fallback: check article:tag meta
    if not meta.get('focus_keyword'):
        tags = re.findall(r'<meta\s+property=["\']article:tag["\']\s+content=["\']([^"\']*)["\']', raw)
        if tags:
            meta['article_tags'] = tags

    return meta


def analyze_content(content_html):
    """Analyze post content for SEO factors."""
    if not content_html:
        return {
            'word_count': 0,
            'h2_count': 0,
            'total_images': 0,
            'images_without_alt': 0,
            'internal_link_count': 0,
            'first_paragraph': '',
        }

    analysis = {}

    # Word count
    plain_text = strip_html(content_html)
    words = plain_text.split()
    analysis['word_count'] = len(words)

    # H2 headings
    h2_matches = re.findall(r'<h2[^>]*>', content_html, re.IGNORECASE)
    analysis['h2_count'] = len(h2_matches)

    # Images analysis
    img_tags = re.findall(r'<img[^>]*>', content_html, re.IGNORECASE)
    analysis['total_images'] = len(img_tags)
    images_without_alt = 0
    for img in img_tags:
        alt_match = re.search(r'alt=["\']([^"\']*)["\']', img, re.IGNORECASE)
        if not alt_match or not alt_match.group(1).strip():
            images_without_alt += 1
    analysis['images_without_alt'] = images_without_alt

    # Internal links
    internal_links = re.findall(
        r'<a[^>]+href=["\']https?://(?:www\.)?pethubonline\.com[^"\']*["\']',
        content_html, re.IGNORECASE
    )
    analysis['internal_link_count'] = len(internal_links)

    # First paragraph for suggested meta description
    first_p_match = re.search(r'<p[^>]*>(.*?)</p>', content_html, re.DOTALL | re.IGNORECASE)
    if first_p_match:
        first_p = strip_html(first_p_match.group(1)).strip()
        if len(first_p) > 155:
            first_p = first_p[:155].rsplit(' ', 1)[0] + '...'
        analysis['first_paragraph'] = first_p
    else:
        analysis['first_paragraph'] = plain_text[:155].rsplit(' ', 1)[0] + '...' if len(plain_text) > 155 else plain_text

    return analysis


def score_post(title_text, meta, analysis, rm_data):
    """Score a post 0-100 based on SEO factors. Uses our own scoring aligned with Rank Math criteria."""
    score = 0
    issues = []
    actions = []

    title_len = len(title_text)
    meta_desc = meta.get('meta_desc', '')
    meta_desc_len = len(meta_desc)
    seo_title = meta.get('seo_title', '')
    focus_kw = meta.get('focus_keyword', '')

    # 1. Focus keyword (15 pts)
    if focus_kw:
        score += 15
    else:
        issues.append("No focus keyword")
        actions.append("Set focus keyword in Rank Math")

    # 2. SEO title set and different from post title (10 pts)
    if seo_title and seo_title != title_text:
        score += 10
    elif seo_title:
        score += 5
        issues.append("SEO title same as post title")
        actions.append("Customize SEO title with keyword + brand")
    else:
        issues.append("No SEO title")
        actions.append("Set SEO title in Rank Math")

    # 3. Title length (10 pts)
    if 50 <= title_len <= 60:
        score += 10
    elif 40 <= title_len <= 70:
        score += 6
        issues.append(f"Title length {title_len} (ideal 50-60)")
        if title_len < 50:
            actions.append(f"Expand title (+{50 - title_len} chars)")
        else:
            actions.append(f"Shorten title (-{title_len - 60} chars)")
    else:
        score += 2
        issues.append(f"Title length {title_len} (ideal 50-60)")
        if title_len < 40:
            actions.append(f"Title too short (+{50 - title_len} chars needed)")
        else:
            actions.append(f"Title too long (-{title_len - 60} chars)")

    # 4. Meta description (10 pts total: 5 for existing + 5 for proper length)
    if meta_desc:
        score += 5
        if 120 <= meta_desc_len <= 160:
            score += 5
        elif 100 <= meta_desc_len <= 170:
            score += 3
            issues.append(f"Meta desc length {meta_desc_len} (ideal 120-160)")
            actions.append("Adjust meta description length to 120-160 chars")
        else:
            score += 1
            issues.append(f"Meta desc length {meta_desc_len} (ideal 120-160)")
            actions.append("Rewrite meta description to 120-160 chars")
    else:
        issues.append("No meta description")
        suggested = analysis.get('first_paragraph', '')[:155]
        actions.append(f"Add meta desc: \"{suggested}\"")

    # 5. Images with alt text (10 pts)
    total_imgs = analysis.get('total_images', 0)
    imgs_no_alt = analysis.get('images_without_alt', 0)
    if total_imgs == 0:
        score += 5
        issues.append("No images in content")
        actions.append("Add relevant images with descriptive alt text")
    elif imgs_no_alt == 0:
        score += 10
    elif imgs_no_alt < total_imgs:
        score += 5
        issues.append(f"{imgs_no_alt}/{total_imgs} images missing alt text")
        actions.append(f"Add alt text to {imgs_no_alt} images")
    else:
        issues.append(f"All {total_imgs} images missing alt text")
        actions.append(f"Add descriptive alt text to all {total_imgs} images")

    # 6. Internal links (10 pts)
    ilinks = analysis.get('internal_link_count', 0)
    # Also consider Rank Math's count
    rm_ilinks = rm_data.get('rm_internal_links', 0)
    effective_ilinks = max(ilinks, rm_ilinks)

    if effective_ilinks >= 3:
        score += 10
    elif effective_ilinks >= 1:
        score += 5
        issues.append(f"Only {effective_ilinks} internal link(s) (aim for 3+)")
        actions.append(f"Add {3 - effective_ilinks} more internal links to related posts")
    else:
        issues.append("No internal links")
        actions.append("Add 3+ internal links to related posts")

    # 7. H2 headings (10 pts)
    h2s = analysis.get('h2_count', 0)
    if h2s >= 3:
        score += 10
    elif h2s >= 1:
        score += 5
        issues.append(f"Only {h2s} H2 heading(s) (aim for 3+)")
        actions.append(f"Add {3 - h2s} more H2 subheadings for structure")
    else:
        issues.append("No H2 headings")
        actions.append("Add H2 subheadings for content structure")

    # 8. Content length (20 pts)
    wc = analysis.get('word_count', 0)
    if wc >= 1500:
        score += 20
    elif wc >= 1000:
        score += 15
    elif wc >= 600:
        score += 10
        issues.append(f"Content {wc} words (aim 1000+)")
        actions.append(f"Expand content by {1000 - wc}+ words")
    elif wc >= 300:
        score += 5
        issues.append(f"Thin content: {wc} words (aim 1000+)")
        actions.append(f"Expand content significantly ({1000 - wc}+ more words)")
    else:
        issues.append(f"Very thin content: {wc} words")
        actions.append("Rewrite/expand content to 1000+ words")

    # 9. Focus keyword in title (5 pts bonus check)
    if focus_kw and title_text:
        if focus_kw.lower() in title_text.lower():
            score += 5
        else:
            issues.append("Focus keyword not in title")
            actions.append(f"Include '{focus_kw}' in post title")

    # Cap at 100
    score = min(100, score)

    return score, issues, actions


def main():
    print("=" * 70)
    print("PetHub SEO Remediation Audit - Complete Analysis")
    print("=" * 70)
    print()

    # Step 1: Fetch all posts from WP REST API
    print("[1/4] Fetching all published posts from WP REST API...")
    posts = fetch_all_posts()
    total = len(posts)
    print(f"  Total posts fetched: {total}")
    print()

    if not posts:
        print("ERROR: No posts fetched. Exiting.")
        sys.exit(1)

    # Step 2: Fetch Rank Math SEO scores
    print("[2/4] Fetching Rank Math SEO scores and link data...")
    rm_scores = fetch_rank_math_scores()
    print()

    # Step 3: Scrape front-end pages for SEO meta
    print("[3/4] Scraping front-end pages for SEO meta (title, desc, focus kw)...")
    print("  This will take ~2-3 minutes for 168 posts...")

    front_end_data = {}
    for i, post in enumerate(posts, 1):
        post_id = post.get('id', 0)
        link = post.get('link', '')

        if i % 25 == 0 or i == 1:
            print(f"  Scraping post {i}/{total}...")

        if link:
            meta = scrape_front_end_meta(link)
            front_end_data[str(post_id)] = meta
            # Small delay to be nice to the server
            if i % 10 == 0:
                time.sleep(0.5)

    print(f"  Scraped {len(front_end_data)} posts")
    print()

    # Step 4: Analyze and score each post
    print("[4/4] Analyzing and scoring all posts...")
    results = []
    issue_counts = {
        'no_focus_keyword': 0,
        'no_seo_title': 0,
        'no_meta_desc': 0,
        'title_length_issue': 0,
        'meta_desc_length_issue': 0,
        'images_without_alt': 0,
        'no_images': 0,
        'low_internal_links': 0,
        'low_h2': 0,
        'thin_content': 0,
        'kw_not_in_title': 0,
    }

    total_score = 0
    total_rm_score = 0
    rm_score_count = 0

    for i, post in enumerate(posts, 1):
        post_id = post.get('id', 0)
        pid_str = str(post_id)

        title_data = post.get('title', {})
        if isinstance(title_data, dict):
            title = title_data.get('rendered', '')
        else:
            title = str(title_data)
        title_text = strip_html(title)

        content_data = post.get('content', {})
        if isinstance(content_data, dict):
            content_html = content_data.get('rendered', '')
        else:
            content_html = str(content_data)

        link = post.get('link', '')

        if i % 40 == 0 or i == 1:
            print(f"  Scoring post {i}/{total}: {title_text[:50]}...")

        # Get front-end SEO meta
        fe_meta = front_end_data.get(pid_str, {})

        # Get Rank Math link/score data
        rm_data = rm_scores.get(pid_str, {})
        rm_seo_score = rm_data.get('rm_seo_score', 0)
        if rm_seo_score > 0:
            total_rm_score += rm_seo_score
            rm_score_count += 1

        # Build unified meta
        meta = {
            'focus_keyword': fe_meta.get('focus_keyword', ''),
            'seo_title': fe_meta.get('seo_title', ''),
            'meta_desc': fe_meta.get('meta_desc', ''),
        }

        # Analyze content
        analysis = analyze_content(content_html)

        # Score
        score, issues, actions = score_post(title_text, meta, analysis, rm_data)
        total_score += score

        # Count issues
        if not meta['focus_keyword']:
            issue_counts['no_focus_keyword'] += 1
        if not meta['seo_title'] or meta['seo_title'] == title_text:
            issue_counts['no_seo_title'] += 1
        if not meta['meta_desc']:
            issue_counts['no_meta_desc'] += 1
        if len(title_text) < 50 or len(title_text) > 60:
            issue_counts['title_length_issue'] += 1
        if meta['meta_desc'] and (len(meta['meta_desc']) < 120 or len(meta['meta_desc']) > 160):
            issue_counts['meta_desc_length_issue'] += 1
        if analysis['images_without_alt'] > 0:
            issue_counts['images_without_alt'] += 1
        if analysis['total_images'] == 0:
            issue_counts['no_images'] += 1
        effective_ilinks = max(analysis['internal_link_count'], rm_data.get('rm_internal_links', 0))
        if effective_ilinks < 3:
            issue_counts['low_internal_links'] += 1
        if analysis['h2_count'] < 3:
            issue_counts['low_h2'] += 1
        if analysis['word_count'] < 1000:
            issue_counts['thin_content'] += 1
        if meta['focus_keyword'] and meta['focus_keyword'].lower() not in title_text.lower():
            issue_counts['kw_not_in_title'] += 1

        # Statuses
        fk_status = "SET" if meta['focus_keyword'] else "MISSING"
        st_status = "SET" if meta['seo_title'] and meta['seo_title'] != title_text else "MISSING"
        md_status = "SET" if meta['meta_desc'] else "MISSING"

        # Suggested meta desc if missing
        suggested_meta = ""
        if not meta['meta_desc'] and analysis.get('first_paragraph'):
            suggested_meta = analysis['first_paragraph']

        results.append({
            'post_id': post_id,
            'title': title_text,
            'url': link,
            'seo_score': score,
            'rm_seo_score': rm_seo_score,
            'focus_keyword_status': fk_status,
            'focus_keyword': meta['focus_keyword'],
            'seo_title_status': st_status,
            'seo_title': meta['seo_title'],
            'meta_desc_status': md_status,
            'title_length': len(title_text),
            'meta_desc_length': len(meta['meta_desc']) if meta['meta_desc'] else 0,
            'images_without_alt': analysis['images_without_alt'],
            'total_images': analysis['total_images'],
            'internal_link_count': effective_ilinks,
            'h2_count': analysis['h2_count'],
            'word_count': analysis['word_count'],
            'issues': '; '.join(issues) if issues else 'None',
            'remediation_actions': '; '.join(actions) if actions else 'None needed',
            'suggested_meta_desc': suggested_meta,
        })

    # Sort by score ascending (worst first)
    results.sort(key=lambda x: x['seo_score'])

    # Write CSV
    print(f"\n  Writing CSV to {OUTPUT_CSV}...")
    fieldnames = [
        'post_id', 'title', 'url', 'seo_score', 'rm_seo_score',
        'focus_keyword_status', 'focus_keyword',
        'seo_title_status', 'seo_title',
        'meta_desc_status', 'title_length', 'meta_desc_length',
        'images_without_alt', 'total_images', 'internal_link_count', 'h2_count',
        'word_count', 'issues', 'remediation_actions', 'suggested_meta_desc'
    ]

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print(f"  CSV written with {len(results)} rows.")

    # Calculate statistics
    avg_score = total_score / total if total else 0
    avg_rm_score = total_rm_score / rm_score_count if rm_score_count else 0
    posts_above_90 = sum(1 for r in results if r['seo_score'] >= 90)
    posts_70_89 = sum(1 for r in results if 70 <= r['seo_score'] < 90)
    posts_50_69 = sum(1 for r in results if 50 <= r['seo_score'] < 70)
    posts_below_50 = sum(1 for r in results if r['seo_score'] < 50)

    total_issues = sum(issue_counts.values())

    # Estimate improvement from fixing top issues
    # Focus keyword fix: 15pts * posts missing it / total
    kw_impact = (15 * issue_counts['no_focus_keyword']) / total
    # Meta desc fix: 10pts * posts missing it / total
    md_impact = (10 * issue_counts['no_meta_desc']) / total
    # SEO title fix: 10pts * posts missing it / total (5pts if just same as title)
    st_impact = (7 * issue_counts['no_seo_title']) / total
    # Internal links fix
    il_impact = (5 * issue_counts['low_internal_links']) / total

    estimated_new_avg = avg_score + kw_impact + md_impact + st_impact + il_impact

    print()
    print("=" * 70)
    print("SEO REMEDIATION AUDIT SUMMARY")
    print("=" * 70)
    print()
    print(f"Total Posts Analyzed: {total}")
    print(f"Current Average SEO Score (our audit): {avg_score:.1f}/100")
    print(f"Current Average Rank Math Score:       {avg_rm_score:.1f}/100")
    print()
    print("Score Distribution (audit score):")
    print(f"  90-100 (Excellent):  {posts_above_90:>4} posts ({posts_above_90/total*100:.1f}%)")
    print(f"  70-89  (Good):       {posts_70_89:>4} posts ({posts_70_89/total*100:.1f}%)")
    print(f"  50-69  (Needs Work): {posts_50_69:>4} posts ({posts_50_69/total*100:.1f}%)")
    print(f"  0-49   (Critical):   {posts_below_50:>4} posts ({posts_below_50/total*100:.1f}%)")
    print()
    print("ISSUES BY TYPE:")
    print(f"  Missing focus keyword:         {issue_counts['no_focus_keyword']:>4} posts")
    print(f"  Missing/default SEO title:     {issue_counts['no_seo_title']:>4} posts")
    print(f"  Missing meta description:      {issue_counts['no_meta_desc']:>4} posts")
    print(f"  Non-ideal title length:        {issue_counts['title_length_issue']:>4} posts")
    print(f"  Non-ideal meta desc length:    {issue_counts['meta_desc_length_issue']:>4} posts")
    print(f"  Images without alt text:       {issue_counts['images_without_alt']:>4} posts")
    print(f"  No images in content:          {issue_counts['no_images']:>4} posts")
    print(f"  Low internal links (<3):       {issue_counts['low_internal_links']:>4} posts")
    print(f"  Low H2 headings (<3):          {issue_counts['low_h2']:>4} posts")
    print(f"  Thin content (<1000 words):    {issue_counts['thin_content']:>4} posts")
    print(f"  Focus kw not in title:         {issue_counts['kw_not_in_title']:>4} posts")
    print(f"  -------------------------------------------")
    print(f"  TOTAL ISSUES:                  {total_issues:>4}")
    print()
    print("ESTIMATED IMPACT OF REMEDIATION:")
    print(f"  Current average audit score:   {avg_score:.1f}/100")
    print(f"  After fixing focus keywords:   +{kw_impact:.1f} pts avg")
    print(f"  After fixing meta descriptions:+{md_impact:.1f} pts avg")
    print(f"  After fixing SEO titles:       +{st_impact:.1f} pts avg")
    print(f"  After fixing internal links:   +{il_impact:.1f} pts avg")
    print(f"  Projected new average:         {estimated_new_avg:.1f}/100")
    print(f"  Gap to 90% target:             {max(0, 90 - estimated_new_avg):.1f} pts remaining")
    print()

    # Priority fixes
    print("TOP PRIORITY FIXES (ordered by impact):")
    print("  1. Set focus keywords (15 pts/post) - Bulk: research & assign primary keyword")
    print("  2. Add meta descriptions (10 pts/post) - Can auto-generate from first paragraph")
    print("  3. Optimize SEO titles (5-10 pts/post) - Add keyword + brand suffix")
    print("  4. Add internal links (5-10 pts/post) - Cross-link related content")
    print("  5. Fix title lengths (4-8 pts/post) - Adjust to 50-60 char range")
    print("  6. Add alt text to images (5-10 pts/post) - Include keywords in alt")
    print("  7. Expand thin content (5-15 pts/post) - Add depth to short articles")
    print()

    # 15 worst posts
    print("15 LOWEST-SCORING POSTS (fix first):")
    print(f"  {'ID':>6} | {'Score':>5} | {'RM':>3} | {'WC':>5} | {'FK':>3} | {'MD':>3} | Title")
    print(f"  {'------':>6} | {'-----':>5} | {'---':>3} | {'-----':>5} | {'---':>3} | {'---':>3} | {'---'*17}")
    for r in results[:15]:
        fk = 'Y' if r['focus_keyword_status'] == 'SET' else 'N'
        md = 'Y' if r['meta_desc_status'] == 'SET' else 'N'
        print(f"  {r['post_id']:>6} | {r['seo_score']:>4}% | {r['rm_seo_score']:>3} | {r['word_count']:>5} | {fk:>3} | {md:>3} | {r['title'][:45]}")
    print()

    # 10 best posts
    print("10 HIGHEST-SCORING POSTS (reference examples):")
    print(f"  {'ID':>6} | {'Score':>5} | {'RM':>3} | {'WC':>5} | {'FK':>3} | {'MD':>3} | Title")
    print(f"  {'------':>6} | {'-----':>5} | {'---':>3} | {'-----':>5} | {'---':>3} | {'---':>3} | {'---'*17}")
    for r in results[-10:]:
        fk = 'Y' if r['focus_keyword_status'] == 'SET' else 'N'
        md = 'Y' if r['meta_desc_status'] == 'SET' else 'N'
        print(f"  {r['post_id']:>6} | {r['seo_score']:>4}% | {r['rm_seo_score']:>3} | {r['word_count']:>5} | {fk:>3} | {md:>3} | {r['title'][:45]}")
    print()

    print(f"Full CSV report: {OUTPUT_CSV}")
    print("=" * 70)


if __name__ == '__main__':
    main()
