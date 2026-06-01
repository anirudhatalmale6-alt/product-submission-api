import requests, json, time, re, sys
from collections import defaultdict

WP_URL = 'https://pethubonline.com/wp-json/wp/v2'
AUTH = ('jasonsarah2026', 'yUmn Rngy EFE1 r7jr kjtm jmqx')

session = requests.Session()
session.auth = AUTH
session.headers.update({'Accept-Encoding': 'gzip, deflate'})

# Phase 1: Fetch ALL posts metadata only (no content - much faster)
print("Phase 1: Fetching post metadata (no content)...")
all_posts = []
page = 1
while True:
    r = session.get(f'{WP_URL}/posts', params={
        'per_page': 100, 'page': page, 'status': 'publish',
        '_fields': 'id,title,link,categories'
    })
    if r.status_code != 200:
        break
    posts = r.json()
    if not posts:
        break
    all_posts.extend(posts)
    page += 1
    time.sleep(0.5)

print(f"Total published posts: {len(all_posts)}")

# Build mappings
slug_to_post = {}
id_to_post = {}
for p in all_posts:
    slug = p['link'].replace('https://pethubonline.com/', '').rstrip('/')
    slug_to_post[slug] = p
    id_to_post[p['id']] = p

# Phase 2: Fetch content in batches to build link graph
print("Phase 2: Building link graph (fetching content in batches)...")
inbound = defaultdict(set)
outbound = defaultdict(set)

batch_size = 20
post_ids = [p['id'] for p in all_posts]

for batch_start in range(0, len(post_ids), batch_size):
    batch = post_ids[batch_start:batch_start + batch_size]
    for pid in batch:
        r = session.get(f'{WP_URL}/posts/{pid}', params={'_fields': 'id,content'})
        if r.status_code != 200:
            continue
        content = r.json()['content']['rendered']
        links = re.findall(r'href="https?://pethubonline\.com/([^"]+)"', content)
        for link in links:
            link = link.rstrip('/')
            if link in slug_to_post:
                target_id = slug_to_post[link]['id']
                if target_id != pid:
                    outbound[pid].add(target_id)
                    inbound[target_id].add(pid)
        time.sleep(0.3)

    done = min(batch_start + batch_size, len(post_ids))
    print(f"  Scanned {done}/{len(post_ids)} posts...")

# Find orphans
orphans = [p for p in all_posts if len(inbound.get(p['id'], set())) == 0]
print(f"\nOrphan posts (0 inbound links): {len(orphans)}")

# Group by category
posts_by_cat = defaultdict(list)
for p in all_posts:
    cat_id = p['categories'][0] if p['categories'] else 0
    posts_by_cat[cat_id].append(p)

# Phase 3: Fix orphans - add links from same-category posts
print("\nPhase 3: Fixing orphan posts...")
fixed = 0
links_added = 0
errors = 0

for i, orphan in enumerate(orphans):
    oid = orphan['id']
    otitle = orphan['title']['rendered']
    ourl = orphan['link']
    cat_id = orphan['categories'][0] if orphan['categories'] else 0

    # Find source posts in same category that don't already link to this orphan
    candidates = []
    for p in posts_by_cat[cat_id]:
        if p['id'] == oid:
            continue
        if oid in outbound.get(p['id'], set()):
            continue
        candidates.append(p)

    # Prefer posts with more outbound links (they're natural linkers)
    candidates.sort(key=lambda x: len(outbound.get(x['id'], set())), reverse=True)
    sources = candidates[:2]

    if not sources:
        print(f"  [{i+1}/{len(orphans)}] No candidates for: {otitle[:50]}")
        continue

    orphan_links = 0
    for src in sources:
        try:
            r = session.get(f'{WP_URL}/posts/{src["id"]}', params={'_fields': 'id,content'})
            if r.status_code != 200:
                errors += 1
                continue

            content = r.json()['content']['rendered']

            if ourl in content:
                continue

            link_html = f'\n<!-- wp:paragraph -->\n<p><strong>Related:</strong> <a href="{ourl}">{otitle}</a></p>\n<!-- /wp:paragraph -->'

            # Insert before FAQ if exists, otherwise append
            faq_pos = content.lower().find('<h2>frequently asked questions')
            if faq_pos == -1:
                faq_pos = content.lower().find('<h2>faq')

            if faq_pos > 0:
                new_content = content[:faq_pos] + link_html + '\n' + content[faq_pos:]
            else:
                new_content = content + link_html

            update_r = session.post(f'{WP_URL}/posts/{src["id"]}', json={'content': new_content})
            if update_r.status_code == 200:
                orphan_links += 1
                links_added += 1
                outbound[src['id']].add(oid)
                inbound[oid].add(src['id'])
            else:
                print(f"  ERROR updating {src['id']}: {update_r.status_code}")
                errors += 1

            time.sleep(2)
        except Exception as e:
            print(f"  Exception: {e}")
            errors += 1

    if orphan_links > 0:
        fixed += 1

    if (i + 1) % 25 == 0:
        print(f"  Progress: {i+1}/{len(orphans)} | Fixed: {fixed} | Links added: {links_added} | Errors: {errors}")

# Final summary
print(f"\n{'='*60}")
print(f"ORPHAN LINK FIX COMPLETE")
print(f"{'='*60}")
print(f"Total orphans found: {len(orphans)}")
print(f"Orphans fixed: {fixed}")
print(f"Total links added: {links_added}")
print(f"Errors: {errors}")
print(f"Remaining orphans: {len(orphans) - fixed}")

# Save results for dashboard
results = {
    'total_posts': len(all_posts),
    'total_orphans_found': len(orphans),
    'orphans_fixed': fixed,
    'links_added': links_added,
    'errors': errors,
    'remaining_orphans': len(orphans) - fixed,
    'orphan_ids': [p['id'] for p in orphans if p['id'] not in [oid for oid in inbound if len(inbound[oid]) > 0]]
}
with open('/var/lib/freelancer/projects/40416335/orphan_fix_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to orphan_fix_results.json")
