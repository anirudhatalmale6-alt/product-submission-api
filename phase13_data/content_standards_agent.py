#!/usr/bin/env python3
"""
Phase 13D: Content Standards Agent
Mandatory pre-publication validation for all content.
Validates 12 quality gates before any post can be published.
"""

import subprocess
import json
import re
import time
from html.parser import HTMLParser
from datetime import datetime

WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_API = "https://pethubonline.com/wp-json/wp/v2"

PASS_THRESHOLD = 10  # Must pass 10/12 gates minimum
HARD_FAIL_GATES = ['trust_lint', 'no_fake_authority', 'evidence_check']


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            self.text_parts.append(data)

    def get_text(self):
        return ' '.join(self.text_parts)


def strip_html(html):
    ext = HTMLTextExtractor()
    try:
        ext.feed(html or '')
    except:
        pass
    return ext.get_text()


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


def gate_1_word_count(content, plain_text):
    """Gate 1: Minimum word count (1000+ words for posts)"""
    wc = len(plain_text.split())
    passed = wc >= 1000
    return {
        'gate': 'word_count',
        'passed': passed,
        'score': min(100, int(wc / 10)),
        'detail': f'{wc} words' + ('' if passed else ' (minimum 1000 required)'),
    }


def gate_2_heading_structure(content):
    """Gate 2: Proper heading hierarchy (H2s with logical structure)"""
    h2_count = len(re.findall(r'<h2', content or '', re.IGNORECASE))
    h3_count = len(re.findall(r'<h3', content or '', re.IGNORECASE))
    has_h1_in_body = bool(re.search(r'<h1', content or '', re.IGNORECASE))

    issues = []
    if h2_count < 3:
        issues.append(f'only {h2_count} H2s (need 3+)')
    if has_h1_in_body:
        issues.append('H1 in body (Astra handles H1)')

    passed = h2_count >= 3 and not has_h1_in_body
    return {
        'gate': 'heading_structure',
        'passed': passed,
        'score': min(100, h2_count * 15 + h3_count * 5),
        'detail': f'{h2_count} H2s, {h3_count} H3s' + (f' | Issues: {"; ".join(issues)}' if issues else ''),
    }


def gate_3_internal_links(content):
    """Gate 3: Internal linking (3+ internal links)"""
    pattern = r'href=["\']https?://(www\.)?pethubonline\.com[^"\']*["\']'
    count = len(re.findall(pattern, content or '', re.IGNORECASE))
    passed = count >= 3
    return {
        'gate': 'internal_links',
        'passed': passed,
        'score': min(100, count * 20),
        'detail': f'{count} internal links' + ('' if passed else ' (minimum 3 required)'),
    }


def gate_4_external_citations(content):
    """Gate 4: External citations (3+ authoritative references)"""
    all_links = re.findall(r'href=["\']https?://([^"\']+)["\']', content or '', re.IGNORECASE)
    external = [l for l in all_links if 'pethubonline.com' not in l.lower()]
    count = len(external)
    passed = count >= 3
    return {
        'gate': 'external_citations',
        'passed': passed,
        'score': min(100, count * 20),
        'detail': f'{count} external citations' + ('' if passed else ' (minimum 3 required)'),
    }


def gate_5_sources_section(content):
    """Gate 5: Sources/References section present"""
    pattern = r'<h[2-4][^>]*>[^<]*(Sources|References|Citations|Bibliography)[^<]*</h[2-4]>'
    has_sources = bool(re.search(pattern, content or '', re.IGNORECASE))
    return {
        'gate': 'sources_section',
        'passed': has_sources,
        'score': 100 if has_sources else 0,
        'detail': 'Sources section present' if has_sources else 'No Sources/References section found',
    }


def gate_6_faq_section(content):
    """Gate 6: FAQ section with structured Q&A"""
    patterns = [
        r'<h[2-4][^>]*>\s*(FAQ|Frequently Asked Questions)[^<]*</h[2-4]>',
        r'wp-block-yoast-faq',
        r'class=["\'][^"\']*faq[^"\']*["\']',
    ]
    has_faq = any(re.search(p, content or '', re.IGNORECASE) for p in patterns)
    return {
        'gate': 'faq_section',
        'passed': has_faq,
        'score': 100 if has_faq else 0,
        'detail': 'FAQ section present' if has_faq else 'No FAQ section found',
    }


def gate_7_trust_lint(content, plain_text):
    """Gate 7: Trust lint - no fake authority claims (HARD FAIL)"""
    violations = []

    fake_patterns = [
        (r'(our team of|our experts|our veterinarians)\s+(have|has)\s+(tested|reviewed|verified)',
         'Claims team testing without evidence'),
        (r'(we tested|we reviewed|we tried)\s+\d+',
         'Claims product testing without evidence'),
        (r'(Dr\.|Professor|Veterinarian)\s+[A-Z][a-z]+\s+(recommends|says|confirms)',
         'Names fake expert'),
        (r'clinically (proven|tested|verified)',
         'Clinical claims without citation'),
    ]

    for pattern, desc in fake_patterns:
        if re.search(pattern, plain_text, re.IGNORECASE):
            violations.append(desc)

    passed = len(violations) == 0
    return {
        'gate': 'trust_lint',
        'passed': passed,
        'score': 100 if passed else 0,
        'detail': 'No trust violations' if passed else f'VIOLATIONS: {"; ".join(violations)}',
        'hard_fail': not passed,
    }


def gate_8_no_fake_authority(content, plain_text):
    """Gate 8: No fake credentials/authors/reviewers (HARD FAIL)"""
    violations = []

    fake_signals = [
        (r'reviewed by [A-Z][a-z]+ [A-Z][a-z]+,?\s*(DVM|PhD|MRCVS|BVSc)',
         'Names specific expert reviewer'),
        (r'(medically|scientifically|fact)\s*-?\s*checked by',
         'Claims fact-checking by person'),
        (r'(award-winning|certified|licensed)\s+(team|staff|experts)',
         'Claims certified team'),
    ]

    for pattern, desc in fake_signals:
        if re.search(pattern, plain_text, re.IGNORECASE):
            violations.append(desc)

    passed = len(violations) == 0
    return {
        'gate': 'no_fake_authority',
        'passed': passed,
        'score': 100 if passed else 0,
        'detail': 'No fake authority signals' if passed else f'VIOLATIONS: {"; ".join(violations)}',
        'hard_fail': not passed,
    }


def gate_9_evidence_check(content, plain_text):
    """Gate 9: Claims backed by evidence/citations (HARD FAIL for strong claims)"""
    strong_claims = re.findall(
        r'(studies show|research proves|scientifically proven|statistics indicate|data shows)',
        plain_text, re.IGNORECASE
    )

    has_citations = bool(re.search(
        r'href=["\']https?://(?!.*pethubonline\.com)',
        content or '', re.IGNORECASE
    ))

    if strong_claims and not has_citations:
        return {
            'gate': 'evidence_check',
            'passed': False,
            'score': 0,
            'detail': f'Strong claims ({len(strong_claims)}) without external citations',
            'hard_fail': True,
        }

    return {
        'gate': 'evidence_check',
        'passed': True,
        'score': 100,
        'detail': 'Evidence coverage adequate',
    }


def gate_10_meta_seo(post_id):
    """Gate 10: SEO metadata (focus keyword, meta description via Rank Math)"""
    data = wp_api_call(f"posts/{post_id}?_fields=meta")
    if not data or not isinstance(data, dict):
        return {
            'gate': 'meta_seo',
            'passed': False,
            'score': 0,
            'detail': 'Could not fetch meta',
        }

    meta = data.get('meta', {})
    has_focus_kw = bool(meta.get('rank_math_focus_keyword', ''))
    has_desc = bool(meta.get('rank_math_description', ''))
    has_title = bool(meta.get('rank_math_title', ''))

    score = (has_focus_kw * 40) + (has_desc * 30) + (has_title * 30)
    passed = score >= 70

    details = []
    if not has_focus_kw:
        details.append('no focus keyword')
    if not has_desc:
        details.append('no meta description')
    if not has_title:
        details.append('no SEO title')

    return {
        'gate': 'meta_seo',
        'passed': passed,
        'score': score,
        'detail': 'SEO metadata complete' if passed else f'Missing: {", ".join(details)}',
    }


def gate_11_image_compliance(content):
    """Gate 11: Images with alt text, reasonable count"""
    images = re.findall(r'<img[^>]*>', content or '', re.IGNORECASE)
    img_count = len(images)
    imgs_with_alt = sum(1 for img in images if re.search(r'alt=["\'][^"\']+["\']', img))

    if img_count == 0:
        return {
            'gate': 'image_compliance',
            'passed': False,
            'score': 0,
            'detail': 'No images found (minimum 2 required)',
        }

    alt_pct = imgs_with_alt / img_count * 100 if img_count > 0 else 0
    passed = img_count >= 2 and alt_pct >= 80

    return {
        'gate': 'image_compliance',
        'passed': passed,
        'score': int(min(100, alt_pct)),
        'detail': f'{img_count} images, {imgs_with_alt} with alt text ({alt_pct:.0f}%)',
    }


def gate_12_snippet_readiness(content):
    """Gate 12: Featured snippet optimization (list/table/definition)"""
    signals = 0
    if re.search(r'<ol', content or '', re.IGNORECASE):
        signals += 1
    if re.search(r'<ul', content or '', re.IGNORECASE):
        signals += 1
    if re.search(r'<table', content or '', re.IGNORECASE):
        signals += 1
    if re.search(r'<h[2-4][^>]*>[^<]*(What|How|Why|When)', content or '', re.IGNORECASE):
        signals += 1
    if re.search(r'Key Takeaway', content or '', re.IGNORECASE):
        signals += 1

    passed = signals >= 3
    return {
        'gate': 'snippet_readiness',
        'passed': passed,
        'score': min(100, signals * 25),
        'detail': f'{signals}/5 snippet signals' + ('' if passed else ' (need 3+)'),
    }


def validate_post(post_id, title=None, content=None):
    """Run all 12 gates on a post. Returns validation result."""
    if content is None:
        data = wp_api_call(f"posts/{post_id}?_fields=id,title,content,status")
        if not data:
            return {'post_id': post_id, 'error': 'Could not fetch post'}
        title = data['title']['rendered'] if isinstance(data['title'], dict) else data['title']
        content = data['content']['rendered'] if isinstance(data['content'], dict) else ''

    plain_text = strip_html(content)

    gates = [
        gate_1_word_count(content, plain_text),
        gate_2_heading_structure(content),
        gate_3_internal_links(content),
        gate_4_external_citations(content),
        gate_5_sources_section(content),
        gate_6_faq_section(content),
        gate_7_trust_lint(content, plain_text),
        gate_8_no_fake_authority(content, plain_text),
        gate_9_evidence_check(content, plain_text),
        gate_10_meta_seo(post_id),
        gate_11_image_compliance(content),
        gate_12_snippet_readiness(content),
    ]

    passed_count = sum(1 for g in gates if g['passed'])
    hard_fails = [g for g in gates if g.get('hard_fail')]
    avg_score = sum(g['score'] for g in gates) / len(gates)

    # Publication decision
    can_publish = passed_count >= PASS_THRESHOLD and len(hard_fails) == 0

    return {
        'post_id': post_id,
        'title': title,
        'gates_passed': passed_count,
        'gates_total': 12,
        'hard_fails': len(hard_fails),
        'average_score': round(avg_score, 1),
        'can_publish': can_publish,
        'gate_results': gates,
        'timestamp': datetime.utcnow().isoformat(),
    }


def validate_all_drafts():
    """Validate all draft posts."""
    print("Fetching draft posts...")
    drafts = []
    for page in range(1, 5):
        data = wp_api_call(f"posts?status=draft&per_page=50&page={page}&_fields=id,title,content")
        if not data or (isinstance(data, dict) and data.get('code')):
            break
        drafts.extend(data)
        if len(data) < 50:
            break
        time.sleep(1)

    print(f"  Found {len(drafts)} drafts")
    results = []

    for i, post in enumerate(drafts):
        post_id = post['id']
        title = post['title']['rendered'] if isinstance(post['title'], dict) else post['title']
        content = post['content']['rendered'] if isinstance(post['content'], dict) else ''

        result = validate_post(post_id, title, content)
        results.append(result)

        if (i + 1) % 20 == 0:
            print(f"  Validated {i+1}/{len(drafts)}...")

    return results


def validate_all_published():
    """Validate all published posts (regression check)."""
    print("Fetching published posts...")
    posts = []
    for page in range(1, 5):
        data = wp_api_call(f"posts?status=publish&per_page=50&page={page}&_fields=id,title,content")
        if not data or (isinstance(data, dict) and data.get('code')):
            break
        posts.extend(data)
        if len(data) < 50:
            break
        time.sleep(1)

    print(f"  Found {len(posts)} published posts")
    results = []

    for i, post in enumerate(posts):
        post_id = post['id']
        title = post['title']['rendered'] if isinstance(post['title'], dict) else post['title']
        content = post['content']['rendered'] if isinstance(post['content'], dict) else ''

        result = validate_post(post_id, title, content)
        results.append(result)

        if (i + 1) % 25 == 0:
            print(f"  Validated {i+1}/{len(posts)}...")

    return results


def main():
    print("=" * 70)
    print("PHASE 13D: CONTENT STANDARDS AGENT - VALIDATION RUN")
    print("=" * 70)
    print()

    # Validate published posts
    print("[1/2] Validating published posts (regression check)...")
    published_results = validate_all_published()
    print(f"  Validated {len(published_results)} published posts")
    print()

    # Validate draft posts
    print("[2/2] Validating draft posts (publication readiness)...")
    draft_results = validate_all_drafts()
    print(f"  Validated {len(draft_results)} draft posts")
    print()

    # Summary
    print("=" * 70)
    print("PUBLISHED POSTS - REGRESSION CHECK")
    print("=" * 70)

    pub_passing = sum(1 for r in published_results if r.get('can_publish'))
    pub_avg = sum(r.get('average_score', 0) for r in published_results) / len(published_results) if published_results else 0

    print(f"  Total: {len(published_results)}")
    print(f"  Meeting standards: {pub_passing} ({pub_passing/len(published_results)*100:.1f}%)")
    print(f"  Average gate score: {pub_avg:.1f}/100")
    print()

    # Gate-by-gate breakdown for published
    gate_pass_rates = {}
    for r in published_results:
        for g in r.get('gate_results', []):
            gate_name = g['gate']
            if gate_name not in gate_pass_rates:
                gate_pass_rates[gate_name] = {'passed': 0, 'total': 0}
            gate_pass_rates[gate_name]['total'] += 1
            if g['passed']:
                gate_pass_rates[gate_name]['passed'] += 1

    print("  GATE PASS RATES (Published):")
    print("  " + "-" * 50)
    for gate, stats in sorted(gate_pass_rates.items(), key=lambda x: x[1]['passed']/max(x[1]['total'],1)):
        rate = stats['passed'] / stats['total'] * 100 if stats['total'] > 0 else 0
        bar = '#' * int(rate / 5) + '.' * (20 - int(rate / 5))
        print(f"    {gate:<22} [{bar}] {rate:5.1f}% ({stats['passed']}/{stats['total']})")

    print()
    print("=" * 70)
    print("DRAFT POSTS - PUBLICATION READINESS")
    print("=" * 70)

    if draft_results:
        draft_ready = sum(1 for r in draft_results if r.get('can_publish'))
        draft_avg = sum(r.get('average_score', 0) for r in draft_results) / len(draft_results)

        print(f"  Total drafts: {len(draft_results)}")
        print(f"  Ready to publish: {draft_ready}")
        print(f"  Need work: {len(draft_results) - draft_ready}")
        print(f"  Average gate score: {draft_avg:.1f}/100")
        print()

        # Show drafts that are close to publishable
        almost_ready = [r for r in draft_results if r.get('gates_passed', 0) >= 8 and not r.get('can_publish')]
        if almost_ready:
            print("  ALMOST READY (8-9 gates passing):")
            for r in almost_ready[:10]:
                title_short = r['title'][:50] + "..." if len(r['title']) > 50 else r['title']
                failing = [g['gate'] for g in r.get('gate_results', []) if not g['passed']]
                print(f"    ID {r['post_id']} | {r['gates_passed']}/12 | {title_short}")
                print(f"      Failing: {', '.join(failing)}")

        # Hard fails
        hard_fail_posts = [r for r in draft_results if r.get('hard_fails', 0) > 0]
        if hard_fail_posts:
            print()
            print("  HARD FAIL POSTS (trust/authority violations):")
            for r in hard_fail_posts[:5]:
                title_short = r['title'][:50] + "..." if len(r['title']) > 50 else r['title']
                violations = [g['detail'] for g in r.get('gate_results', []) if g.get('hard_fail')]
                print(f"    ID {r['post_id']} | {title_short}")
                for v in violations:
                    print(f"      VIOLATION: {v}")
    else:
        print("  No draft posts found.")

    print()
    print("=" * 70)

    # Write results to JSON for agent consumption
    output = {
        'timestamp': datetime.utcnow().isoformat(),
        'published': {
            'total': len(published_results),
            'passing': pub_passing,
            'average_score': round(pub_avg, 1),
        },
        'drafts': {
            'total': len(draft_results),
            'ready': sum(1 for r in draft_results if r.get('can_publish')),
            'average_score': round(sum(r.get('average_score', 0) for r in draft_results) / max(len(draft_results), 1), 1),
        },
        'gate_pass_rates': {k: round(v['passed']/max(v['total'],1)*100, 1) for k, v in gate_pass_rates.items()},
    }

    output_json = "/var/lib/freelancer/projects/40416335/phase13_data/content_standards_results.json"
    with open(output_json, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"Results JSON: {output_json}")
    print("=" * 70)


if __name__ == "__main__":
    main()
