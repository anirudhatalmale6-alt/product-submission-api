#!/usr/bin/env python3
"""Phase 10D: Add cross-links between new and existing posts + add FAQs to posts lacking them."""

import requests, re, html as html_mod, time
from gutenberg_utils import (
    wrap_paragraph, wrap_heading, wrap_list, wrap_separator,
    validate_gutenberg, safe_update_content
)

WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
s = requests.Session()
s.auth = ('jasonsarah2026', 'yUmn Rngy EFE1 r7jr kjtm jmqx')
s.headers['Accept-Encoding'] = 'gzip, deflate'

CROSS_LINKS = {
    3996: [
        ('/how-to-choose-dog-bed-size', 'How to Choose the Right Dog Bed Size'),
        ('/dog-bed-materials-guide', 'Dog Bed Materials Explained'),
        ('/how-to-wash-dog-bed', 'How to Wash and Maintain Your Dog\'s Bed'),
        ('/where-to-place-dog-bed', 'Where to Place Your Dog\'s Bed'),
    ],
    4004: [
        ('/dog-bed-materials-guide', 'Dog Bed Materials Explained'),
        ('/how-to-choose-dog-bed-size', 'How to Choose the Right Dog Bed Size'),
    ],
    4011: [
        ('/where-to-place-dog-bed', 'Where to Place Your Dog\'s Bed'),
        ('/dog-bed-materials-guide', 'Dog Bed Materials Explained'),
    ],
    4018: [
        ('/how-to-choose-dog-bed-size', 'How to Choose the Right Dog Bed Size'),
        ('/how-to-wash-dog-bed', 'How to Wash and Maintain Your Dog\'s Bed'),
    ],
    3956: [
        ('/dog-toy-safety-guide', 'Dog Toy Safety Guide'),
        ('/mental-stimulation-for-dogs', 'Mental Stimulation for Dogs'),
        ('/dog-toys-for-different-play-styles', 'Dog Toys by Play Style'),
        ('/diy-dog-toys-homemade', 'DIY Dog Toys'),
    ],
    3957: [
        ('/dog-toy-safety-guide', 'Dog Toy Safety Guide'),
        ('/dog-toys-for-different-play-styles', 'Dog Toys by Play Style'),
    ],
    3959: [
        ('/mental-stimulation-for-dogs', 'Mental Stimulation for Dogs'),
        ('/dog-toys-for-different-play-styles', 'Dog Toys by Play Style'),
    ],
    3960: [
        ('/dog-toy-safety-guide', 'Dog Toy Safety Guide'),
        ('/diy-dog-toys-homemade', 'DIY Dog Toys'),
    ],
    4118: [
        ('/how-to-choose-dog-training-treats', 'How to Choose Dog Training Treats'),
        ('/puppy-socialisation-guide', 'Puppy Socialisation Guide'),
    ],
    4125: [
        ('/how-to-choose-dog-training-treats', 'How to Choose Dog Training Treats'),
    ],
    4132: [
        ('/puppy-socialisation-guide', 'Puppy Socialisation Guide'),
        ('/how-to-choose-dog-training-treats', 'How to Choose Dog Training Treats'),
    ],
}

link_count = 0

for pid, links in CROSS_LINKS.items():
    r = s.get(f"{WP_BASE}/posts/{pid}", params={'context': 'edit'})
    if r.status_code != 200:
        print(f"  SKIP {pid}: fetch failed {r.status_code}")
        continue

    data = r.json()
    raw = data['content']['raw']
    title = html_mod.unescape(data['title'].get('raw', ''))

    new_links = []
    for url, text in links:
        if url not in raw:
            new_links.append((url, text))

    if not new_links:
        print(f"  SKIP {pid}: all links already present")
        continue

    related_section = re.search(r'(<!-- wp:heading[^>]*-->\s*<h2[^>]*>Related Reading</h2>.*?<!-- /wp:list -->)', raw, re.DOTALL)
    if related_section:
        old_list = related_section.group(0)
        insert_point = old_list.rfind('</ul>')
        new_li = '\n'.join(f'<li><a href="{url}">{text}</a></li>' for url, text in new_links)
        updated_list = old_list[:insert_point] + new_li + '\n' + old_list[insert_point:]
        new_content = raw.replace(old_list, updated_list)
    else:
        link_items = [f'<a href="{url}">{text}</a>' for _, (url, text) in enumerate(new_links)]
        related_block = '\n\n'.join([
            wrap_separator(),
            wrap_heading('Related Reading', level=2),
            wrap_list(link_items),
        ])
        new_content = raw.rstrip() + '\n\n' + related_block

    is_valid, issues = validate_gutenberg(new_content)
    if not is_valid:
        print(f"  VALIDATION FAIL {pid}: {issues}")
        continue

    ok, msg = safe_update_content(s, WP_BASE, 'posts', pid, new_content)
    if ok:
        link_count += len(new_links)
        print(f"  OK {pid}: {title[:50]} (+{len(new_links)} links)")
    else:
        print(f"  FAIL {pid}: {msg}")

    time.sleep(0.3)

print(f"\nTotal cross-links added: {link_count}")
