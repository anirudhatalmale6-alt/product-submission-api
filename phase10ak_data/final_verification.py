#!/usr/bin/env python3
"""Phase 10AK - Final Verification: Re-audit all posts after link insertions."""

import subprocess, json, csv, re, time, html
from collections import defaultdict

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
BASE = "https://pethubonline.com/wp-json/wp/v2"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ak_data"

def api_get(endpoint):
    url = f"{BASE}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    return json.loads(result.stdout)

def count_internal_links(content):
    pattern = r'href=["\']https?://pethubonline\.com/[^"\']*["\']'
    return len(re.findall(pattern, content, re.IGNORECASE))

def extract_internal_slugs(content):
    pattern = r'href=["\']https?://pethubonline\.com/([^"\'#?]*)["\']'
    matches = re.findall(pattern, content, re.IGNORECASE)
    slugs = set()
    for m in matches:
        slug = m.strip('/').split('/')[-1] if m.strip('/') else ''
        if slug and slug not in ('', 'wp-json', 'wp-admin', 'wp-content'):
            slugs.add(slug)
    return slugs

def classify_topic(title, slug):
    title_l = title.lower()
    slug_l = slug.lower()
    keywords = {
        'Dog Toys': ['dog toy', 'chew toy', 'fetch', 'tug play', 'puzzle toy',
                      'enrichment for dog', 'dog play', 'mental stimulation toy', 'toy rotation',
                      'toy safety', 'toy durability', 'toy cleaning', 'toy hygiene', 'toy storage',
                      'toy lifespan', 'interactive dog toy', 'indestructible', 'boredom',
                      'overstimulation', 'sensory enrichment', 'confidence-building play',
                      'play recovery', 'multi-dog toy', 'rotating puzzle', 'enrichment by breed',
                      'toy anxiety', 'scent-game', 'crate and play', 'indoor vs outdoor dog toy',
                      'aggressive chewer', 'puppy-safe dog toy', 'low-mobility enrichment',
                      'play style', 'diy dog toy', 'brain work', 'senior dog toy',
                      'toy material', 'rubber, rope, plush'],
        'Dog Health': ['dog health', 'joint supplement', 'flea treatment', 'dental care',
                       'orthopaedic care', 'joint health', 'mobility', 'common condition',
                       'prevention', 'veterinary', 'pet health'],
        'Dog Training': ['dog training', 'training treat', 'training lead', 'training equipment',
                         'behaviour', 'body language', 'training terminology',
                         'puppy training guide', 'training and behaviour'],
        'Dog Food': ['dog food', 'puppy food', 'dry vs wet', 'nutrition', 'pet feeding',
                     'pet nutrition', 'food label'],
        'Dog Beds': ['dog bed', 'orthopaedic bed', 'cooling bed', 'puppy bed',
                     'bed sizing', 'bed material', 'elevated bed'],
        'Dog Grooming': ['dog grooming', 'dog brush', 'dog shampoo', 'dog nail', 'grooming glossary',
                         'pet grooming', 'coat type'],
        'Dog Harnesses': ['dog harness', 'no-pull', 'collar and harness', 'harness vs collar',
                          'measure your dog for a harness', 'dog collar', 'puppy collar', 'dog lead'],
        'Puppy Care': ['puppy care', 'puppy socialisation', 'puppy development',
                       'first-time dog owner', 'new owner', 'first year'],
        'Cat Supplies': ['cat supply', 'cat supplies', 'cat bed', 'cat brush', 'cat nail',
                         'cat shampoo', 'cat collar', 'cat harness', 'cat gps', 'cat id tag',
                         'cat scratching', 'cat scratcher', 'cat tree', 'cat litter',
                         'cat grooming', 'cat window', 'cat radiator', 'heated cat',
                         'catnip', 'cat care basic', 'indoor cat'],
        'Cat Toys': ['cat toy', 'cat play', 'cat enrichment', 'kitten toy',
                     'cat personality', 'cat toy rotation', 'indoor cat toy'],
        'Pet Care': ['multi-pet', 'seasonal pet', 'pet hydration', 'pet first aid',
                     'seasonal dog care', 'pet enrichment explained', 'pet toy safety'],
    }
    for topic, kws in keywords.items():
        for kw in kws:
            if kw in title_l or kw in slug_l:
                return topic
    return 'Other'


def main():
    print("=" * 70)
    print("PHASE 10AK - Final Verification Audit")
    print("=" * 70)

    # Fetch all posts fresh
    print("\n[1] Fetching all published posts...")
    all_posts = []
    page = 1
    while True:
        posts = api_get(f"posts?per_page=100&page={page}&status=publish")
        if not posts or isinstance(posts, dict):
            break
        all_posts.extend(posts)
        if len(posts) < 100:
            break
        page += 1
        time.sleep(2)
    print(f"  Fetched {len(all_posts)} posts")

    # Build slug map
    slug_map = {}
    for p in all_posts:
        slug_map[p['slug']] = {
            'id': p['id'],
            'title': html.unescape(p['title']['rendered']),
            'topic': classify_topic(html.unescape(p['title']['rendered']), p['slug'])
        }

    # Re-audit
    print("\n[2] Re-auditing internal links...")
    audit_rows = []
    topic_to_posts = defaultdict(list)
    cluster_cross_links = defaultdict(lambda: defaultdict(int))

    for p in all_posts:
        pid = p['id']
        title = html.unescape(p['title']['rendered'])
        content = p['content']['rendered']
        slug = p['slug']
        topic = classify_topic(title, slug)
        link_count = count_internal_links(content)
        has_rr = 'Related Reading' in content
        linked_slugs = extract_internal_slugs(content)

        topic_to_posts[topic].append(p)

        # Count cross-cluster links
        for ls in linked_slugs:
            if ls in slug_map:
                target_topic = slug_map[ls]['topic']
                if target_topic != topic:
                    cluster_cross_links[topic][target_topic] += 1

        audit_rows.append({
            'id': pid,
            'title': title,
            'slug': slug,
            'cluster': topic,
            'internal_link_count': link_count,
            'has_related_reading': has_rr,
            'needs_reinforcement': link_count < 5
        })

    # Write updated audit
    audit_file = f"{DATA_DIR}/internal_link_audit.csv"
    with open(audit_file, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['id', 'title', 'slug', 'cluster', 'internal_link_count', 'has_related_reading', 'needs_reinforcement'])
        w.writeheader()
        w.writerows(audit_rows)

    # Statistics
    total = len(audit_rows)
    under5 = len([r for r in audit_rows if r['needs_reinforcement']])
    with_rr = len([r for r in audit_rows if r['has_related_reading']])
    avg_links = sum(r['internal_link_count'] for r in audit_rows) / total if total else 0

    print(f"\n  FINAL AUDIT SUMMARY:")
    print(f"  Total posts: {total}")
    print(f"  Posts with < 5 internal links: {under5}")
    print(f"  Posts with Related Reading: {with_rr}")
    print(f"  Average internal links per post: {avg_links:.1f}")

    print(f"\n  Topic breakdown:")
    topic_stats = defaultdict(lambda: {'count': 0, 'total_links': 0, 'under5': 0, 'with_rr': 0})
    for r in audit_rows:
        t = r['cluster']
        topic_stats[t]['count'] += 1
        topic_stats[t]['total_links'] += r['internal_link_count']
        if r['needs_reinforcement']:
            topic_stats[t]['under5'] += 1
        if r['has_related_reading']:
            topic_stats[t]['with_rr'] += 1

    for t, s in sorted(topic_stats.items(), key=lambda x: -x[1]['count']):
        avg = s['total_links'] / s['count'] if s['count'] else 0
        print(f"    {t}: {s['count']} posts, avg {avg:.1f} links, {s['with_rr']} with RR, {s['under5']} under-linked")

    # Corridor verification
    print(f"\n  Cross-cluster corridor verification:")
    corridors = [
        ('Dog Toys', 'Dog Health'),
        ('Dog Toys', 'Dog Training'),
        ('Dog Food', 'Dog Health'),
        ('Cat Toys', 'Cat Supplies'),
        ('Dog Beds', 'Dog Health'),
        ('Dog Grooming', 'Dog Health'),
        ('Puppy Care', 'Dog Training'),
        ('Puppy Care', 'Dog Toys'),
    ]

    corridor_final = []
    all_ok = True
    for c1, c2 in corridors:
        fwd = cluster_cross_links[c1][c2]
        rev = cluster_cross_links[c2][c1]
        fwd_status = "OK" if fwd >= 2 else "NEEDS_WORK"
        rev_status = "OK" if rev >= 2 else "NEEDS_WORK"
        if fwd < 2 or rev < 2:
            all_ok = False
        print(f"    {c1} -> {c2}: {fwd} links ({fwd_status})")
        print(f"    {c2} -> {c1}: {rev} links ({rev_status})")
        corridor_final.append({
            'corridor': f"{c1} <-> {c2}",
            'direction': f"{c1} -> {c2}",
            'links_found': fwd,
            'links_added': 0,
            'status': fwd_status
        })
        corridor_final.append({
            'corridor': f"{c1} <-> {c2}",
            'direction': f"{c2} -> {c1}",
            'links_found': rev,
            'links_added': 0,
            'status': rev_status
        })

    # Write final corridor status
    with open(f"{DATA_DIR}/corridor_status.csv", 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['corridor', 'direction', 'links_found', 'links_added', 'status'])
        w.writeheader()
        w.writerows(corridor_final)

    if all_ok:
        print(f"\n  ALL CORRIDORS COMPLETE - All 8 bidirectional corridors have >= 2 links each way")
    else:
        print(f"\n  SOME CORRIDORS INCOMPLETE - Review corridor_status.csv for details")

    print(f"\n  Files written:")
    print(f"    {DATA_DIR}/internal_link_audit.csv")
    print(f"    {DATA_DIR}/corridor_status.csv")
    print(f"    {DATA_DIR}/link_insertions_log.csv (from Phase 2/3)")


if __name__ == '__main__':
    main()
