#!/usr/bin/env python3
"""Cross-cluster internal link insertion engine for underlinked posts.
Fetches all published posts, identifies underlinked ones (<10 internal links),
and inserts contextual cross-cluster links using keyword matching."""

import subprocess, json, time, re, csv, sys
from datetime import datetime

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
BASE = "https://pethubonline.com/wp-json/wp/v2"

CATEGORY_MAP = {
    1377: 'Cat Supplies', 1459: 'Cat Toys', 1413: 'Indoor Cats',
    1376: 'Dog Supplies', 1397: 'Pet Care', 1401: 'Dog Beds',
    1489: 'Dog Care', 1467: 'Dog Food', 1422: 'Dog Harnesses',
    1450: 'Dog Health', 1441: 'Dog Toys', 1442: 'Puppy Care',
    1474: 'Training Supplies', 1: 'Uncategorized'
}

CLUSTER_KEYWORDS = {
    'Cat Supplies': ['cat supply', 'cat litter', 'cat carrier', 'cat bowl', 'cat bed', 'scratching post', 'cat tree', 'cat supplies'],
    'Cat Toys': ['cat toy', 'cat play', 'feather wand', 'laser pointer cat', 'interactive cat', 'cat enrichment', 'cat puzzle'],
    'Indoor Cats': ['indoor cat', 'house cat', 'indoor environment', 'cat exercise indoor', 'cat behaviour', 'indoor diet'],
    'Dog Supplies': ['dog supply', 'dog lead', 'dog collar', 'dog bowl', 'dog crate', 'dog accessories'],
    'Pet Care': ['pet care', 'pet safety', 'pet health', 'vet visit', 'pet first aid', 'pet grooming', 'multi-pet', 'pet enrichment'],
    'Dog Beds': ['dog bed', 'orthopaedic bed', 'cooling bed', 'memory foam bed', 'dog sleeping', 'dog bed size'],
    'Dog Care': ['dog care', 'dog grooming', 'dog groom', 'nail trimming', 'dog bath', 'dental care dog'],
    'Dog Food': ['dog food', 'dog nutrition', 'dog diet', 'puppy food', 'dog feeding', 'dog ingredient'],
    'Dog Harnesses': ['dog harness', 'no-pull harness', 'harness vs collar', 'harness fitting', 'measure dog harness'],
    'Dog Health': ['dog health', 'dog joint', 'dog mobility', 'dog weight', 'dog exercise', 'senior dog health'],
    'Dog Toys': ['dog toy', 'chew toy', 'puzzle toy', 'tug toy', 'interactive toy', 'indestructible toy', 'fetch toy', 'enrichment toy'],
    'Puppy Care': ['puppy', 'puppy training', 'puppy socialisation', 'puppy teething', 'puppy crate', 'puppy development'],
    'Training Supplies': ['training', 'dog training', 'clicker', 'training treat', 'obedience', 'recall training'],
}

def wp_fetch(endpoint):
    url = f"{BASE}/{endpoint}"
    r = subprocess.run(["curl", "-s", "--compressed", "-u", AUTH, url],
                       capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout)

def wp_fetch_all(post_type="posts", status="publish"):
    all_items = []
    page = 1
    while True:
        time.sleep(2)
        url = f"{BASE}/{post_type}?status={status}&per_page=100&page={page}&context=edit"
        r = subprocess.run(["curl", "-s", "--compressed", "-u", AUTH, url],
                           capture_output=True, text=True, timeout=60)
        items = json.loads(r.stdout)
        if not items or isinstance(items, dict):
            break
        all_items.extend(items)
        if len(items) < 100:
            break
        page += 1
    return all_items

def wp_update(post_id, content):
    import tempfile
    payload = json.dumps({"content": {"raw": content}})
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(payload)
        tmppath = f.name
    time.sleep(3)
    url = f"{BASE}/posts/{post_id}"
    r = subprocess.run(["curl", "-s", "--compressed", "-u", AUTH, "-X", "POST",
                        "-H", "Content-Type: application/json",
                        "-d", f"@{tmppath}", url],
                       capture_output=True, text=True, timeout=60)
    import os
    os.unlink(tmppath)
    result = json.loads(r.stdout)
    return 'id' in result

def count_internal_links(content):
    return len(re.findall(r'href=["\']https?://pethubonline\.com/[^"\']*["\']', content, re.I))

def get_cluster(categories):
    for cat_id in categories:
        if cat_id in CATEGORY_MAP:
            return CATEGORY_MAP[cat_id]
    return 'Uncategorized'

def find_relevant_targets(source_content, source_cluster, all_posts, existing_links):
    """Find posts from OTHER clusters that are relevant to this content."""
    content_lower = source_content.lower()
    candidates = []

    for post in all_posts:
        post_cluster = get_cluster(post.get('categories', []))
        post_id = post['id']
        post_slug = post.get('slug', '')
        post_url = f"https://pethubonline.com/{post_slug}/"

        if post_url in existing_links or f"/{post_slug}/" in existing_links:
            continue
        if f"/{post_slug}" in source_content:
            continue

        title = post.get('title', {})
        if isinstance(title, dict):
            title = title.get('raw', title.get('rendered', ''))
        title_lower = title.lower()

        score = 0
        matched_phrase = None

        keywords = CLUSTER_KEYWORDS.get(post_cluster, [])
        for kw in keywords:
            if kw in content_lower:
                score += 2

        title_words = re.findall(r'\b[a-z]{4,}\b', title_lower)
        for tw in title_words:
            if tw in ['guide', 'best', 'complete', 'essential', 'ultimate', 'tips']:
                continue
            if tw in content_lower:
                score += 1
                if not matched_phrase:
                    matched_phrase = tw

        if score >= 3:
            candidates.append({
                'post_id': post_id,
                'title': title if isinstance(title, str) else str(title),
                'slug': post_slug,
                'url': post_url,
                'cluster': post_cluster,
                'score': score,
                'matched_phrase': matched_phrase
            })

    candidates.sort(key=lambda x: x['score'], reverse=True)
    same_cluster = [c for c in candidates if c['cluster'] == source_cluster]
    cross_cluster = [c for c in candidates if c['cluster'] != source_cluster]

    result = cross_cluster[:3]
    if len(result) < 3:
        result.extend(same_cluster[:3 - len(result)])

    return result

def build_link_block(targets):
    """Build a Gutenberg paragraph block with contextual cross-cluster links."""
    if not targets:
        return ""

    links_html = []
    for t in targets:
        title = t['title']
        url = t['url']
        links_html.append(f'<a href="{url}">{title}</a>')

    if len(links_html) == 1:
        line = f"For more guidance, see our {links_html[0]}."
    elif len(links_html) == 2:
        line = f"You might also find these helpful: {links_html[0]} and {links_html[1]}."
    else:
        line = f"Related reading: {', '.join(links_html[:-1])}, and {links_html[-1]}."

    block = f'\n\n<!-- wp:paragraph -->\n<p>{line}</p>\n<!-- /wp:paragraph -->'
    return block

def find_insertion_point(content):
    """Find a good spot to insert links — before Sources/References or FAQ, or at end."""
    patterns = [
        r'<!-- wp:heading[^>]*>\s*<h2[^>]*>Sources\s*(?:and|&amp;|&)\s*References',
        r'<!-- wp:heading[^>]*>\s*<h2[^>]*>(?:Sources|References)',
        r'<!-- wp:heading[^>]*>\s*<h2[^>]*>Key Terms',
        r'<!-- wp:heading[^>]*>\s*<h2[^>]*>Editorial Disclosure',
    ]

    for pat in patterns:
        m = re.search(pat, content, re.I)
        if m:
            return m.start()

    return len(content)

def main():
    print("Fetching all published posts...")
    posts = wp_fetch_all()
    print(f"Fetched {len(posts)} published posts")

    underlinked = []
    for p in posts:
        content = p.get('content', {})
        if isinstance(content, dict):
            content = content.get('raw', content.get('rendered', ''))
        link_count = count_internal_links(content)
        if link_count < 10:
            underlinked.append({
                'post': p,
                'content': content,
                'link_count': link_count,
                'cluster': get_cluster(p.get('categories', []))
            })

    underlinked.sort(key=lambda x: x['link_count'])
    print(f"Found {len(underlinked)} posts with <10 internal links")

    log = []
    updated = 0
    skipped = 0
    errors = 0

    for item in underlinked:
        post = item['post']
        content = item['content']
        post_id = post['id']
        title = post.get('title', {})
        if isinstance(title, dict):
            title = title.get('raw', title.get('rendered', ''))
        cluster = item['cluster']
        current_links = item['link_count']

        existing_links = ' '.join(re.findall(r'href=["\']([^"\']+)["\']', content))

        targets = find_relevant_targets(content, cluster, posts, existing_links)

        if not targets:
            print(f"  SKIP {post_id}: {title[:50]} — no relevant targets found")
            log.append({
                'post_id': post_id, 'title': title, 'cluster': cluster,
                'current_links': current_links, 'added': 0,
                'status': 'skipped', 'targets': ''
            })
            skipped += 1
            continue

        link_block = build_link_block(targets)
        insertion_point = find_insertion_point(content)
        new_content = content[:insertion_point] + link_block + content[insertion_point:]

        new_link_count = count_internal_links(new_content)
        added = new_link_count - current_links

        try:
            success = wp_update(post_id, new_content)
            if success:
                updated += 1
                target_names = '; '.join([f"{t['title'][:40]} ({t['cluster']})" for t in targets])
                print(f"  OK {post_id}: {title[:50]} — +{added} links (was {current_links}, now {new_link_count})")
                log.append({
                    'post_id': post_id, 'title': title, 'cluster': cluster,
                    'current_links': current_links, 'added': added,
                    'status': 'updated', 'targets': target_names
                })
            else:
                errors += 1
                print(f"  ERR {post_id}: {title[:50]} — API update failed")
                log.append({
                    'post_id': post_id, 'title': title, 'cluster': cluster,
                    'current_links': current_links, 'added': 0,
                    'status': 'error', 'targets': ''
                })
        except Exception as e:
            errors += 1
            print(f"  ERR {post_id}: {title[:50]} — {e}")
            log.append({
                'post_id': post_id, 'title': title, 'cluster': cluster,
                'current_links': current_links, 'added': 0,
                'status': 'error', 'targets': str(e)
            })

    with open('cross_cluster_link_log.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['post_id', 'title', 'cluster', 'current_links', 'added', 'status', 'targets'])
        w.writeheader()
        w.writerows(log)

    print(f"\nDone: {updated} updated, {skipped} skipped, {errors} errors")
    print(f"Log: cross_cluster_link_log.csv")

if __name__ == '__main__':
    main()
