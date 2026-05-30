#!/usr/bin/env python3
"""Re-run gate checks on all 18 expanded drafts."""

import subprocess, json, time, re, csv

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
BASE = "https://pethubonline.com/wp-json/wp/v2"

CATEGORY_MAP = {
    1377: 'Cat Supplies', 1459: 'Cat Toys', 1413: 'Indoor Cats',
    1376: 'Dog Supplies', 1397: 'Pet Care', 1401: 'Dog Beds',
    1489: 'Dog Care', 1467: 'Dog Food', 1422: 'Dog Harnesses',
    1450: 'Dog Health', 1441: 'Dog Toys', 1442: 'Puppy Care',
    1474: 'Training Supplies', 1: 'Uncategorized'
}

def wp_fetch(post_id):
    time.sleep(2)
    url = f"{BASE}/posts/{post_id}?context=edit"
    r = subprocess.run(["curl", "-s", "--compressed", "-u", AUTH, url],
                       capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout)

def count_words(content):
    text = re.sub(r'<[^>]+>', ' ', content)
    text = re.sub(r'<!--[^>]+-->', ' ', text)
    return len(text.split())

def check_gates(post_id):
    post = wp_fetch(post_id)
    title = post.get('title', {})
    if isinstance(title, dict):
        title = title.get('raw', title.get('rendered', ''))
    content = post.get('content', {})
    if isinstance(content, dict):
        content = content.get('raw', content.get('rendered', ''))
    cats = post.get('categories', [])
    cluster = 'Uncategorized'
    for c in cats:
        if c in CATEGORY_MAP:
            cluster = CATEGORY_MAP[c]
            break

    words = count_words(content)
    has_qa = 'quick-answer' in content
    has_faq = 'at-a-glance' in content or 'Frequently Asked Questions' in content
    has_sources = 'sources-heading' in content or 'Sources and References' in content
    has_glossary = 'key-terms' in content
    has_disclosure = 'editorial-disclosure' in content
    internal_links = len(re.findall(r'href=["\']https?://pethubonline\.com/[^"\']*["\']', content, re.I))
    has_h2_questions = len(re.findall(r'<h2[^>]*>[^<]*\?</h2>', content)) > 0

    fails = []
    if words < 1500:
        fails.append(f'Word count {words} < 1500')
    if not has_qa:
        fails.append('Missing Quick Answer')
    if not has_faq:
        fails.append('Missing FAQ')
    if not has_sources:
        fails.append('Missing Sources')
    if not has_glossary:
        fails.append('Missing Key Terms')
    if not has_disclosure:
        fails.append('Missing Disclosure')
    if internal_links < 3:
        fails.append(f'Only {internal_links} internal links')

    gate_status = 'PASS' if not fails else 'FAIL'

    return {
        'post_id': post_id,
        'title': title,
        'cluster': cluster,
        'word_count': words,
        'has_quick_answer': has_qa,
        'has_faq': has_faq,
        'has_sources': has_sources,
        'has_glossary': has_glossary,
        'has_disclosure': has_disclosure,
        'internal_links': internal_links,
        'gate_status': gate_status,
        'fail_reasons': '; '.join(fails) if fails else 'None'
    }

draft_ids = [10028, 12823, 12820, 12817, 12816, 12813,
             12767, 12766, 12765, 12764, 12763, 12762,
             12761, 12760, 12759, 12758, 12757, 12756]

results = []
passed = 0
failed = 0

for pid in draft_ids:
    r = check_gates(pid)
    results.append(r)
    status = r['gate_status']
    if status == 'PASS':
        passed += 1
        print(f"  PASS {pid}: {r['title'][:50]} ({r['word_count']}w, {r['internal_links']} links)")
    else:
        failed += 1
        print(f"  FAIL {pid}: {r['title'][:50]} — {r['fail_reasons']}")

with open('Draft_Gate_Check_v2.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
    w.writeheader()
    w.writerows(results)

print(f"\nResults: {passed} PASS, {failed} FAIL")
print("Log: Draft_Gate_Check_v2.csv")
