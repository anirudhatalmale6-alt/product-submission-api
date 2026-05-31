#!/usr/bin/env python3
"""
PetHub Image Compliance Audit
Audits all 168 published posts for image compliance standards.
"""

import subprocess
import json
import csv
import re
import time
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote


# WordPress credentials
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_API = "https://pethubonline.com/wp-json/wp/v2"


def wp_api_call(url):
    """Make a WordPress API call using curl via subprocess."""
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", f"{WP_USER}:{WP_PASS}", url],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"  [ERROR] curl failed for {url}: {result.stderr}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  [ERROR] JSON decode failed for {url}")
        print(f"  Response: {result.stdout[:200]}")
        return None


class ImageAnalyzer(HTMLParser):
    """Parse HTML content and extract image information."""

    def __init__(self):
        super().__init__()
        self.images = []
        self.current_position = 0
        self.total_length = 0
        self.heading_positions = []
        self.paragraph_count = 0
        self.first_paragraph_end = None
        self.in_paragraph = False
        self.broken_images = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == 'img':
            src = attrs_dict.get('src', '')
            alt = attrs_dict.get('alt', '')
            self.images.append({
                'src': src,
                'alt': alt,
                'position': self.getpos()[0],
                'has_alt': bool(alt and alt.strip()),
                'alt_text': alt.strip() if alt else '',
            })

        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.heading_positions.append(self.getpos()[0])

        if tag == 'p':
            self.paragraph_count += 1
            self.in_paragraph = True

    def handle_endtag(self, tag):
        if tag == 'p' and self.in_paragraph:
            self.in_paragraph = False
            if self.paragraph_count == 1 and self.first_paragraph_end is None:
                self.first_paragraph_end = self.getpos()[0]


def analyze_image_filename(src):
    """Check if an image filename is SEO-friendly (contains keywords, not just numbers)."""
    if not src:
        return False

    # Parse the URL to get the filename
    parsed = urlparse(src)
    path = unquote(parsed.path)
    filename = path.split('/')[-1] if '/' in path else path

    # Remove extension
    name_part = filename.rsplit('.', 1)[0] if '.' in filename else filename

    # Remove size suffixes like -300x200, -1024x768
    name_part = re.sub(r'-\d+x\d+$', '', name_part)

    # Check if it's just numbers/hex
    if re.match(r'^[0-9a-f\-_]+$', name_part, re.IGNORECASE):
        return False

    # Check if it has meaningful words (at least 2 chars of alpha)
    alpha_chars = re.sub(r'[^a-zA-Z]', '', name_part)
    if len(alpha_chars) < 3:
        return False

    # Check for common non-descriptive patterns
    non_descriptive = [
        r'^image\d*$', r'^img\d*$', r'^photo\d*$', r'^pic\d*$',
        r'^screenshot', r'^screen-shot', r'^untitled',
        r'^DSC', r'^IMG_', r'^DCIM', r'^P\d{7}',
    ]
    for pattern in non_descriptive:
        if re.match(pattern, name_part, re.IGNORECASE):
            return False

    return True


def check_broken_image(src):
    """Check if an image URL appears to be broken (basic heuristic checks)."""
    if not src:
        return True
    if src.startswith('data:'):
        return False  # Data URIs are inline, not broken
    if not src.startswith('http'):
        return True  # Relative URLs without proper base are suspect
    return False


def calculate_placement_score(images, heading_positions, first_paragraph_end, content):
    """
    Score image placement quality (0-100).
    Good placement: after introduction, before/after sections, spread throughout.
    """
    if not images:
        return 0

    score = 0
    content_lines = content.count('\n') + 1

    # Check if there's an image in the first third of the content
    first_third = content_lines / 3
    has_early_image = any(img['position'] <= first_third for img in images)
    if has_early_image:
        score += 25

    # Check if images are spread throughout the content (not all clustered)
    if len(images) >= 2:
        positions = [img['position'] for img in images]
        spread = (max(positions) - min(positions)) / max(content_lines, 1)
        if spread > 0.5:
            score += 30
        elif spread > 0.3:
            score += 20
        elif spread > 0.1:
            score += 10
    elif len(images) == 1:
        score += 15  # Single image, partial credit

    # Check if images appear near headings (within a few lines)
    near_heading_count = 0
    for img in images:
        for h_pos in heading_positions:
            if abs(img['position'] - h_pos) <= 5:
                near_heading_count += 1
                break

    if images:
        heading_proximity_ratio = near_heading_count / len(images)
        score += int(heading_proximity_ratio * 25)

    # Check if first image appears after introduction (not the very first element)
    if images and first_paragraph_end:
        if images[0]['position'] >= first_paragraph_end:
            score += 20
        else:
            score += 10  # Image before intro, partial credit
    elif images:
        score += 10  # No clear paragraph structure, partial credit

    return min(score, 100)


def calculate_compliance_score(total_images, images_with_alt, seo_filename_count,
                                placement_score, meets_minimum, broken_count):
    """Calculate overall compliance score (0-100)."""
    score = 0

    # Image count (25 points)
    if meets_minimum:
        score += 25
    elif total_images > 0:
        score += int(25 * min(total_images, 4) / 4)

    # Alt text coverage (30 points)
    if total_images > 0:
        alt_ratio = images_with_alt / total_images
        score += int(30 * alt_ratio)

    # SEO filenames (20 points)
    if total_images > 0:
        seo_ratio = seo_filename_count / total_images
        score += int(20 * seo_ratio)

    # Placement quality (15 points)
    score += int(15 * placement_score / 100)

    # No broken images (10 points)
    if broken_count == 0:
        score += 10
    elif total_images > 0:
        score += int(10 * max(0, 1 - broken_count / total_images))

    return min(score, 100)


def audit_post(post):
    """Audit a single post for image compliance."""
    post_id = post['id']
    title = post['title']['rendered'] if isinstance(post['title'], dict) else post['title']
    content = post['content']['rendered'] if isinstance(post['content'], dict) else post['content']

    # Clean title for CSV
    title = re.sub(r'<[^>]+>', '', title)
    title = title.replace('&#8211;', '-').replace('&#8217;', "'").replace('&amp;', '&')
    title = title.replace('&#8220;', '"').replace('&#8221;', '"')

    # Parse HTML for images
    analyzer = ImageAnalyzer()
    try:
        analyzer.feed(content)
    except Exception as e:
        print(f"  [WARN] HTML parse error for post {post_id}: {e}")

    images = analyzer.images
    total_images = len(images)
    images_with_alt = sum(1 for img in images if img['has_alt'])
    images_without_alt = total_images - images_with_alt

    # Check SEO filenames
    seo_filenames = sum(1 for img in images if analyze_image_filename(img['src']))

    # Check broken images
    broken = sum(1 for img in images if check_broken_image(img['src']))

    # Check 4-6 image minimum
    meets_minimum = total_images >= 4

    # Placement score
    placement_score = calculate_placement_score(
        images, analyzer.heading_positions,
        analyzer.first_paragraph_end, content
    )

    # Overall compliance score
    compliance_score = calculate_compliance_score(
        total_images, images_with_alt, seo_filenames,
        placement_score, meets_minimum, broken
    )

    # Identify issues
    issues = []
    if total_images == 0:
        issues.append("NO_IMAGES")
    elif total_images < 4:
        issues.append(f"BELOW_MINIMUM({total_images}/4)")
    if images_without_alt > 0:
        issues.append(f"MISSING_ALT({images_without_alt})")
    if total_images > 0 and seo_filenames < total_images:
        non_seo = total_images - seo_filenames
        issues.append(f"NON_SEO_FILENAMES({non_seo})")
    if broken > 0:
        issues.append(f"BROKEN_IMAGES({broken})")
    if placement_score < 50 and total_images > 0:
        issues.append("POOR_PLACEMENT")
    if not issues:
        issues.append("COMPLIANT")

    return {
        'post_id': post_id,
        'title': title,
        'total_images': total_images,
        'images_with_alt': images_with_alt,
        'images_without_alt': images_without_alt,
        'meets_4_6_minimum': 'Yes' if meets_minimum else 'No',
        'seo_filenames': f"{seo_filenames}/{total_images}",
        'placement_score': placement_score,
        'compliance_score': compliance_score,
        'issues': '; '.join(issues),
    }


def main():
    print("=" * 70)
    print("PetHub Image Compliance Audit")
    print("=" * 70)
    print()

    # Step 1: Fetch all published posts
    all_posts = []
    for page in range(1, 5):
        url = f"{WP_API}/posts?status=publish&per_page=50&page={page}&_fields=id,title,content"
        print(f"Fetching page {page}...")
        data = wp_api_call(url)

        if data is None:
            print(f"  [ERROR] Failed to fetch page {page}")
            continue

        if isinstance(data, dict) and 'code' in data:
            print(f"  [INFO] Page {page}: {data.get('message', 'No more posts')}")
            break

        if not isinstance(data, list):
            print(f"  [ERROR] Unexpected response type for page {page}: {type(data)}")
            break

        all_posts.extend(data)
        print(f"  Fetched {len(data)} posts (total: {len(all_posts)})")

        if len(data) < 50:
            break

        time.sleep(1)

    print(f"\nTotal posts fetched: {len(all_posts)}")
    print()

    # Step 2: Audit each post
    results = []
    for i, post in enumerate(all_posts, 1):
        post_id = post['id']
        title_raw = post['title']['rendered'] if isinstance(post['title'], dict) else str(post['title'])
        title_clean = re.sub(r'<[^>]+>', '', title_raw)[:60]
        print(f"[{i:3d}/{len(all_posts)}] Auditing post {post_id}: {title_clean}...")

        result = audit_post(post)
        results.append(result)

        # Brief status
        score = result['compliance_score']
        imgs = result['total_images']
        status = "PASS" if score >= 70 else "WARN" if score >= 40 else "FAIL"
        print(f"         Score: {score}/100 | Images: {imgs} | {status}")

    # Step 3: Write CSV report
    csv_path = "/var/lib/freelancer/projects/40416335/phase12_data/Image_Compliance_Report.csv"
    fieldnames = [
        'post_id', 'title', 'total_images', 'images_with_alt',
        'images_without_alt', 'meets_4_6_minimum', 'seo_filenames',
        'placement_score', 'compliance_score', 'issues'
    ]

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    print(f"\nReport saved to: {csv_path}")

    # Step 4: Print summary
    print()
    print("=" * 70)
    print("AUDIT SUMMARY")
    print("=" * 70)

    total_audited = len(results)
    passing = sum(1 for r in results if r['compliance_score'] >= 70)
    warning = sum(1 for r in results if 40 <= r['compliance_score'] < 70)
    failing = sum(1 for r in results if r['compliance_score'] < 40)

    avg_score = sum(r['compliance_score'] for r in results) / total_audited if total_audited else 0
    avg_images = sum(r['total_images'] for r in results) / total_audited if total_audited else 0

    meets_min = sum(1 for r in results if r['meets_4_6_minimum'] == 'Yes')
    no_images = sum(1 for r in results if r['total_images'] == 0)

    total_images_all = sum(r['total_images'] for r in results)
    total_with_alt = sum(r['images_with_alt'] for r in results)
    total_without_alt = sum(r['images_without_alt'] for r in results)

    print(f"\nTotal posts audited:        {total_audited}")
    print(f"Average compliance score:   {avg_score:.1f}/100")
    print(f"Average images per post:    {avg_images:.1f}")
    print()
    print(f"Posts PASSING (>=70):        {passing} ({passing/total_audited*100:.1f}%)")
    print(f"Posts WARNING (40-69):       {warning} ({warning/total_audited*100:.1f}%)")
    print(f"Posts FAILING (<40):         {failing} ({failing/total_audited*100:.1f}%)")
    print()
    print(f"Posts meeting 4+ images:     {meets_min} ({meets_min/total_audited*100:.1f}%)")
    print(f"Posts with NO images:        {no_images} ({no_images/total_audited*100:.1f}%)")
    print()
    print(f"Total images across all:     {total_images_all}")
    print(f"Images WITH alt text:        {total_with_alt} ({total_with_alt/total_images_all*100:.1f}%)" if total_images_all else "Images WITH alt text:        0")
    print(f"Images WITHOUT alt text:     {total_without_alt} ({total_without_alt/total_images_all*100:.1f}%)" if total_images_all else "Images WITHOUT alt text:     0")

    # Common issues breakdown
    print()
    print("COMMON ISSUES:")
    issue_counts = {}
    for r in results:
        for issue in r['issues'].split('; '):
            # Normalize issue name
            base_issue = re.sub(r'\(\d+[^)]*\)', '', issue).strip()
            if base_issue not in issue_counts:
                issue_counts[base_issue] = 0
            issue_counts[base_issue] += 1

    for issue, count in sorted(issue_counts.items(), key=lambda x: -x[1]):
        pct = count / total_audited * 100
        print(f"  {issue:<30s} {count:3d} posts ({pct:.1f}%)")

    # Top 10 lowest scoring posts
    print()
    print("LOWEST SCORING POSTS (Bottom 10):")
    sorted_results = sorted(results, key=lambda x: x['compliance_score'])
    for r in sorted_results[:10]:
        print(f"  Post {r['post_id']:5d} | Score: {r['compliance_score']:3d} | Images: {r['total_images']} | {r['title'][:50]}")

    # Top 10 highest scoring posts
    print()
    print("HIGHEST SCORING POSTS (Top 10):")
    sorted_desc = sorted(results, key=lambda x: -x['compliance_score'])
    for r in sorted_desc[:10]:
        print(f"  Post {r['post_id']:5d} | Score: {r['compliance_score']:3d} | Images: {r['total_images']} | {r['title'][:50]}")

    print()
    print("=" * 70)
    print("Audit complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
