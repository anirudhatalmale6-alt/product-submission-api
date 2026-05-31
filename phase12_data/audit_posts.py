#!/usr/bin/env python3
"""
AI Readiness Audit for PetHub Online (pethubonline.com)
Fetches all published posts, scores each for AI extractability,
and generates a remediation CSV.
"""

import subprocess
import json
import csv
import time
import re
import sys
from html.parser import HTMLParser

# WordPress API config
BASE_URL = "https://pethubonline.com/wp-json/wp/v2"
USER = "jasonsarah2026"
PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
PER_PAGE = 50

def wp_api_call(url):
    """Make authenticated WordPress API call using curl subprocess."""
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", f"{USER}:{PASS}", url],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"  curl error: {result.stderr}", file=sys.stderr)
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  JSON decode error for URL: {url}", file=sys.stderr)
        print(f"  Response: {result.stdout[:500]}", file=sys.stderr)
        return None

def fetch_all_posts():
    """Fetch all published posts with pagination."""
    all_posts = []
    page = 1
    while True:
        url = f"{BASE_URL}/posts?status=publish&per_page={PER_PAGE}&page={page}&_fields=id,title,content,link,slug,categories"
        print(f"Fetching page {page}...")
        data = wp_api_call(url)
        if data is None or (isinstance(data, dict) and data.get("code")):
            print(f"  API returned error or no data on page {page}: {data}")
            break
        if not isinstance(data, list) or len(data) == 0:
            break
        all_posts.extend(data)
        print(f"  Got {len(data)} posts (total: {len(all_posts)})")
        if len(data) < PER_PAGE:
            break
        page += 1
        time.sleep(1)
    return all_posts

class HTMLTextExtractor(HTMLParser):
    """Extract plain text from HTML."""
    def __init__(self):
        super().__init__()
        self.result = []
    def handle_data(self, data):
        self.result.append(data)
    def get_text(self):
        return ''.join(self.result)

def strip_html(html):
    """Remove HTML tags and return plain text."""
    extractor = HTMLTextExtractor()
    extractor.feed(html or "")
    return extractor.get_text()

def check_quick_answer(content):
    """Check for Quick Answer block."""
    patterns = [
        r'quick\s+answer',
        r'snippet[-_]answer',
        r'class="[^"]*quick[-_]?answer[^"]*"',
        r'class="[^"]*snippet[-_]?answer[^"]*"',
        r'<strong>\s*Quick\s+Answer',
        r'<b>\s*Quick\s+Answer',
        r'<h[2-4][^>]*>.*?Quick\s+Answer.*?</h[2-4]>',
    ]
    for p in patterns:
        if re.search(p, content, re.IGNORECASE):
            return True
    return False

def check_faq(content):
    """Check for FAQ section and count questions."""
    has_faq = False
    q_count = 0

    faq_patterns = [
        r'frequently\s+asked\s+questions',
        r'<h[2-4][^>]*>.*?FAQ.*?</h[2-4]>',
        r'class="[^"]*faq[^"]*"',
        r'wp-block-yoast-faq',
        r'schema-faq',
        r'rank-math-faq',
        r'<div[^>]*class="[^"]*faq[^"]*"',
    ]
    for p in faq_patterns:
        if re.search(p, content, re.IGNORECASE):
            has_faq = True
            break

    # Count Q&A pairs - look for strong/bold questions or FAQ schema questions
    q_patterns = [
        r'<strong>\s*Q[:\.]',
        r'<strong>[^<]{10,80}\?</strong>',
        r'<h[3-5][^>]*>[^<]{10,100}\?</h[3-5]>',
        r'class="[^"]*faq[-_]?question[^"]*"',
        r'"@type"\s*:\s*"Question"',
        r'rank-math-question',
    ]
    for p in q_patterns:
        matches = re.findall(p, content, re.IGNORECASE)
        q_count += len(matches)

    # Also check for FAQ-style heading followed by questions
    if not has_faq and q_count >= 3:
        has_faq = True

    return has_faq, q_count

def check_at_a_glance(content):
    """Check for At a Glance section."""
    patterns = [
        r'at\s+a\s+glance',
        r'class="[^"]*at[-_]?a[-_]?glance[^"]*"',
        r'<h[2-4][^>]*>.*?At\s+a\s+Glance.*?</h[2-4]>',
        r'<h[2-4][^>]*>.*?Overview.*?</h[2-4]>',
    ]
    for p in patterns:
        if re.search(p, content, re.IGNORECASE):
            return True
    return False

def check_key_takeaways(content):
    """Check for Key Takeaways section."""
    patterns = [
        r'key\s+takeaways?',
        r'class="[^"]*takeaway[^"]*"',
        r'<h[2-4][^>]*>.*?Key\s+Takeaways?.*?</h[2-4]>',
        r'<h[2-4][^>]*>.*?Main\s+Points?.*?</h[2-4]>',
        r'<h[2-4][^>]*>.*?Key\s+Points?.*?</h[2-4]>',
        r'<h[2-4][^>]*>.*?Summary.*?</h[2-4]>',
    ]
    for p in patterns:
        if re.search(p, content, re.IGNORECASE):
            return True
    return False

def check_toc(content):
    """Check for Table of Contents."""
    patterns = [
        r'table\s+of\s+contents',
        r'class="[^"]*toc[^"]*"',
        r'class="[^"]*table[-_]?of[-_]?contents[^"]*"',
        r'id="[^"]*toc[^"]*"',
        r'wp-block-table-of-contents',
        r'lwptoc',
        r'ez-toc',
        r'rank-math-toc',
        r'<div[^>]*class="[^"]*toc_',
    ]
    for p in patterns:
        if re.search(p, content, re.IGNORECASE):
            return True
    return False

def check_comparison_table(content):
    """Check for comparison tables."""
    has_table = bool(re.search(r'<table', content, re.IGNORECASE))

    comparison_patterns = [
        r'comparison',
        r'vs\.?\s',
        r'versus',
        r'<th[^>]*>.*?(?:pros?|cons?|feature|price|rating).*?</th>',
        r'class="[^"]*comparison[^"]*"',
    ]

    if has_table:
        for p in comparison_patterns:
            if re.search(p, content, re.IGNORECASE):
                return True

    # Also check for comparison-style content without tables
    if re.search(r'<h[2-4][^>]*>.*?(?:Comparison|vs\.|Versus).*?</h[2-4]>', content, re.IGNORECASE):
        return True

    return False

def check_key_terms(content):
    """Check for Key Terms/Glossary section."""
    patterns = [
        r'key\s+terms?',
        r'glossary',
        r'definitions?',
        r'<h[2-4][^>]*>.*?(?:Key\s+Terms?|Glossary|Definitions?).*?</h[2-4]>',
        r'class="[^"]*glossary[^"]*"',
    ]
    for p in patterns:
        if re.search(p, content, re.IGNORECASE):
            return True
    return False

def check_decision_pathway(content):
    """Check for Decision Pathway section."""
    patterns = [
        r'decision\s+pathway',
        r'decision\s+guide',
        r'decision\s+tree',
        r'how\s+to\s+choose',
        r'which\s+.*?\s+is\s+right\s+for',
        r'choosing\s+the\s+right',
        r'<h[2-4][^>]*>.*?(?:Decision|How\s+to\s+Choose|Which.*Right).*?</h[2-4]>',
        r'class="[^"]*decision[-_]?pathway[^"]*"',
    ]
    for p in patterns:
        if re.search(p, content, re.IGNORECASE):
            return True
    return False

def count_structured_headings(content):
    """Count H2 and H3 headings for structure analysis."""
    h2_count = len(re.findall(r'<h2', content, re.IGNORECASE))
    h3_count = len(re.findall(r'<h3', content, re.IGNORECASE))
    h4_count = len(re.findall(r'<h4', content, re.IGNORECASE))
    return h2_count + h3_count + h4_count

def check_extractable_summary(content):
    """Check if first paragraph provides a clear, extractable answer."""
    # Find first <p> tag content
    match = re.search(r'<p[^>]*>(.*?)</p>', content, re.IGNORECASE | re.DOTALL)
    if match:
        first_p = strip_html(match.group(1)).strip()
        # A good extractable summary should be 50-300 chars and not be a question
        if 50 <= len(first_p) <= 500 and not first_p.endswith('?'):
            return True
    return False

def calculate_ai_score(checks):
    """Calculate AI readiness score 0-100 based on checks."""
    score = 0
    weights = {
        'has_quick_answer': 15,        # Most important for AI extraction
        'has_faq': 12,                  # FAQ schema heavily used by AI
        'faq_quality': 5,              # Bonus for 5+ FAQ questions
        'has_at_a_glance': 8,          # Quick overview section
        'has_key_takeaways': 10,       # Key points section
        'has_toc': 8,                  # Navigation structure
        'has_comparison_table': 7,     # Data tables
        'has_key_terms': 5,            # Glossary/terms
        'has_decision_pathway': 5,     # Decision guidance
        'structured_headings': 10,     # Good heading hierarchy
        'extractable_summary': 15,     # Clear first-paragraph answer
    }

    if checks['has_quick_answer']:
        score += weights['has_quick_answer']
    if checks['has_faq']:
        score += weights['has_faq']
    if checks['faq_question_count'] >= 5:
        score += weights['faq_quality']
    elif checks['faq_question_count'] >= 3:
        score += weights['faq_quality'] * 0.6
    if checks['has_at_a_glance']:
        score += weights['has_at_a_glance']
    if checks['has_key_takeaways']:
        score += weights['has_key_takeaways']
    if checks['has_toc']:
        score += weights['has_toc']
    if checks['has_comparison_table']:
        score += weights['has_comparison_table']
    if checks['has_key_terms']:
        score += weights['has_key_terms']
    if checks['has_decision_pathway']:
        score += weights['has_decision_pathway']

    # Structured headings: 5+ headings = full score, scale linearly
    heading_count = checks['structured_headings_count']
    if heading_count >= 8:
        score += weights['structured_headings']
    elif heading_count >= 5:
        score += int(weights['structured_headings'] * 0.7)
    elif heading_count >= 3:
        score += int(weights['structured_headings'] * 0.4)
    elif heading_count >= 1:
        score += int(weights['structured_headings'] * 0.2)

    if checks['extractable_summary']:
        score += weights['extractable_summary']

    return score

def identify_issues(checks):
    """Identify missing elements."""
    issues = []
    if not checks['has_quick_answer']:
        issues.append("Missing Quick Answer block")
    if not checks['has_faq']:
        issues.append("Missing FAQ section")
    elif checks['faq_question_count'] < 3:
        issues.append(f"FAQ has only {checks['faq_question_count']} questions (need 3+)")
    if not checks['has_at_a_glance']:
        issues.append("Missing At a Glance section")
    if not checks['has_key_takeaways']:
        issues.append("Missing Key Takeaways section")
    if not checks['has_toc']:
        issues.append("Missing Table of Contents")
    if checks['structured_headings_count'] < 3:
        issues.append(f"Poor heading structure ({checks['structured_headings_count']} headings)")
    if not checks['extractable_summary']:
        issues.append("First paragraph not extractable as summary")
    if not checks['has_comparison_table']:
        issues.append("No comparison table")
    if not checks['has_key_terms']:
        issues.append("Missing Key Terms/Glossary section")
    if not checks['has_decision_pathway']:
        issues.append("Missing Decision Pathway section")
    return issues

def determine_remediation(checks):
    """Determine remediation actions needed."""
    actions = []
    if not checks['has_quick_answer']:
        actions.append("Add Quick Answer block at top with 2-3 sentence direct answer")
    if not checks['has_faq']:
        actions.append("Add FAQ section with 5+ relevant Q&A pairs using schema markup")
    elif checks['faq_question_count'] < 5:
        actions.append(f"Expand FAQ to 5+ questions (currently {checks['faq_question_count']})")
    if not checks['has_at_a_glance']:
        actions.append("Add At a Glance summary box with key facts")
    if not checks['has_key_takeaways']:
        actions.append("Add Key Takeaways bullet list before main content")
    if not checks['has_toc']:
        actions.append("Add Table of Contents with anchor links")
    if checks['structured_headings_count'] < 5:
        actions.append("Restructure with more H2/H3 headings for better hierarchy")
    if not checks['extractable_summary']:
        actions.append("Rewrite first paragraph as clear, direct answer to the topic")
    if not checks['has_comparison_table']:
        actions.append("Add comparison/data table where applicable")
    if not checks['has_key_terms']:
        actions.append("Add Key Terms section defining important vocabulary")
    if not checks['has_decision_pathway']:
        actions.append("Add Decision Pathway/How to Choose guide section")
    return actions

def audit_post(post):
    """Audit a single post for AI readiness."""
    content = post.get('content', {}).get('rendered', '')
    title = strip_html(post.get('title', {}).get('rendered', 'Untitled'))
    post_id = post.get('id', 0)

    checks = {
        'has_quick_answer': check_quick_answer(content),
        'has_faq': False,
        'faq_question_count': 0,
        'has_at_a_glance': check_at_a_glance(content),
        'has_key_takeaways': check_key_takeaways(content),
        'has_toc': check_toc(content),
        'has_comparison_table': check_comparison_table(content),
        'has_key_terms': check_key_terms(content),
        'has_decision_pathway': check_decision_pathway(content),
        'structured_headings_count': count_structured_headings(content),
        'extractable_summary': check_extractable_summary(content),
    }

    has_faq, faq_count = check_faq(content)
    checks['has_faq'] = has_faq
    checks['faq_question_count'] = faq_count

    ai_score = calculate_ai_score(checks)
    issues = identify_issues(checks)
    remediation = determine_remediation(checks)

    return {
        'post_id': post_id,
        'title': title,
        'ai_score': ai_score,
        'has_quick_answer': checks['has_quick_answer'],
        'has_faq': checks['has_faq'],
        'faq_question_count': checks['faq_question_count'],
        'has_at_a_glance': checks['has_at_a_glance'],
        'has_key_takeaways': checks['has_key_takeaways'],
        'has_toc': checks['has_toc'],
        'has_comparison_table': checks['has_comparison_table'],
        'has_key_terms': checks['has_key_terms'],
        'has_decision_pathway': checks['has_decision_pathway'],
        'structured_headings_count': checks['structured_headings_count'],
        'extractable_summary': checks['extractable_summary'],
        'issues': "; ".join(issues),
        'remediation_actions': "; ".join(remediation),
    }

def main():
    print("=" * 70)
    print("PetHub Online - AI Readiness Audit")
    print("=" * 70)
    print()

    # Step 1: Fetch all posts
    print("Step 1: Fetching all published posts...")
    posts = fetch_all_posts()
    print(f"\nTotal posts fetched: {len(posts)}")
    print()

    if not posts:
        print("ERROR: No posts fetched. Check API credentials and URL.")
        sys.exit(1)

    # Step 2: Audit each post
    print("Step 2: Auditing each post for AI readiness...")
    results = []
    for i, post in enumerate(posts):
        title = strip_html(post.get('title', {}).get('rendered', 'Untitled'))
        print(f"  [{i+1}/{len(posts)}] Auditing: {title[:60]}...")
        result = audit_post(post)
        results.append(result)

    # Step 3: Write CSV
    csv_path = "/var/lib/freelancer/projects/40416335/phase12_data/AI_Readiness_Remediation.csv"
    print(f"\nStep 3: Writing results to {csv_path}...")

    fieldnames = [
        'post_id', 'title', 'ai_score', 'has_quick_answer', 'has_faq',
        'faq_question_count', 'has_at_a_glance', 'has_key_takeaways',
        'has_toc', 'has_comparison_table', 'has_key_terms',
        'has_decision_pathway', 'structured_headings_count',
        'extractable_summary', 'issues', 'remediation_actions'
    ]

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        # Sort by score ascending (worst first for prioritized remediation)
        results.sort(key=lambda x: x['ai_score'])
        for row in results:
            writer.writerow(row)

    print(f"CSV saved with {len(results)} rows.")

    # Step 4: Summary statistics
    print()
    print("=" * 70)
    print("AI READINESS AUDIT SUMMARY")
    print("=" * 70)

    scores = [r['ai_score'] for r in results]
    avg_score = sum(scores) / len(scores) if scores else 0

    above_95 = [r for r in results if r['ai_score'] >= 95]
    between_90_95 = [r for r in results if 90 <= r['ai_score'] < 95]
    below_90 = [r for r in results if r['ai_score'] < 90]
    below_50 = [r for r in results if r['ai_score'] < 50]

    print(f"\nTotal posts audited:        {len(results)}")
    print(f"Average AI readiness score: {avg_score:.1f}%")
    print(f"Current platform score:     88% (reported)")
    print()
    print(f"Posts >= 95% (target):      {len(above_95)} ({len(above_95)*100//len(results)}%)")
    print(f"Posts 90-94%:               {len(between_90_95)} ({len(between_90_95)*100//len(results)}%)")
    print(f"Posts 50-89%:               {len([r for r in results if 50 <= r['ai_score'] < 90])} ({len([r for r in results if 50 <= r['ai_score'] < 90])*100//len(results)}%)")
    print(f"Posts < 50% (critical):     {len(below_50)} ({len(below_50)*100//len(results)}%)")

    # Most common missing elements
    print("\n--- Most Common Missing Elements ---")
    missing_counts = {}
    for r in results:
        if not r['has_quick_answer']:
            missing_counts['Quick Answer block'] = missing_counts.get('Quick Answer block', 0) + 1
        if not r['has_faq']:
            missing_counts['FAQ section'] = missing_counts.get('FAQ section', 0) + 1
        if not r['has_at_a_glance']:
            missing_counts['At a Glance section'] = missing_counts.get('At a Glance section', 0) + 1
        if not r['has_key_takeaways']:
            missing_counts['Key Takeaways section'] = missing_counts.get('Key Takeaways section', 0) + 1
        if not r['has_toc']:
            missing_counts['Table of Contents'] = missing_counts.get('Table of Contents', 0) + 1
        if not r['has_comparison_table']:
            missing_counts['Comparison table'] = missing_counts.get('Comparison table', 0) + 1
        if not r['has_key_terms']:
            missing_counts['Key Terms/Glossary'] = missing_counts.get('Key Terms/Glossary', 0) + 1
        if not r['has_decision_pathway']:
            missing_counts['Decision Pathway'] = missing_counts.get('Decision Pathway', 0) + 1
        if r['structured_headings_count'] < 5:
            missing_counts['Adequate heading structure'] = missing_counts.get('Adequate heading structure', 0) + 1
        if not r['extractable_summary']:
            missing_counts['Extractable first-paragraph summary'] = missing_counts.get('Extractable first-paragraph summary', 0) + 1

    sorted_missing = sorted(missing_counts.items(), key=lambda x: x[1], reverse=True)
    for element, count in sorted_missing:
        pct = count * 100 // len(results)
        print(f"  {element}: {count}/{len(results)} posts missing ({pct}%)")

    # Estimated score if all fixed
    print("\n--- Projected Score After Full Remediation ---")
    print(f"  If all posts reach 95%+: Platform AI Readiness = 95-100%")
    print(f"  Quick wins (add Quick Answer + FAQ to all): est. +15-27 points avg")
    print(f"  Medium effort (add TOC + Key Takeaways + At a Glance): est. +18-26 points avg")
    print(f"  Full remediation (all 10 dimensions): est. 95-100 per post")

    # Top 10 worst posts
    print("\n--- Top 10 Lowest-Scoring Posts (Priority Remediation) ---")
    for i, r in enumerate(results[:10]):
        print(f"  {i+1}. [{r['ai_score']}%] (ID:{r['post_id']}) {r['title'][:55]}")
        print(f"     Issues: {r['issues'][:100]}...")

    # Top 10 best posts
    print("\n--- Top 10 Highest-Scoring Posts ---")
    best = sorted(results, key=lambda x: x['ai_score'], reverse=True)
    for i, r in enumerate(best[:10]):
        print(f"  {i+1}. [{r['ai_score']}%] (ID:{r['post_id']}) {r['title'][:55]}")

    # Dimension coverage summary
    print("\n--- Dimension Coverage Summary ---")
    dims = {
        'Quick Answer': sum(1 for r in results if r['has_quick_answer']),
        'FAQ Section': sum(1 for r in results if r['has_faq']),
        'At a Glance': sum(1 for r in results if r['has_at_a_glance']),
        'Key Takeaways': sum(1 for r in results if r['has_key_takeaways']),
        'Table of Contents': sum(1 for r in results if r['has_toc']),
        'Comparison Table': sum(1 for r in results if r['has_comparison_table']),
        'Key Terms': sum(1 for r in results if r['has_key_terms']),
        'Decision Pathway': sum(1 for r in results if r['has_decision_pathway']),
        'Good Headings (5+)': sum(1 for r in results if r['structured_headings_count'] >= 5),
        'Extractable Summary': sum(1 for r in results if r['extractable_summary']),
    }
    for dim, count in dims.items():
        pct = count * 100 // len(results)
        bar = "#" * (pct // 2) + "." * (50 - pct // 2)
        print(f"  {dim:25s} {count:3d}/{len(results)} ({pct:3d}%) [{bar}]")

    print(f"\nCSV saved to: {csv_path}")
    print("Audit complete.")

if __name__ == '__main__':
    main()
