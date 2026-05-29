#!/usr/bin/env python3
"""Phase 10AK - Phase 1: Audit current internal link state for all published posts."""

import subprocess, json, csv, re, time, sys

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
BASE = "https://pethubonline.com/wp-json/wp/v2"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ak_data"

def api_get(endpoint):
    """GET request via curl subprocess."""
    url = f"{BASE}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    return json.loads(result.stdout)

def fetch_all_posts():
    """Fetch all published posts with pagination."""
    all_posts = []
    page = 1
    while True:
        print(f"  Fetching page {page}...")
        try:
            posts = api_get(f"posts?per_page=100&page={page}&status=publish")
            if not posts or isinstance(posts, dict):
                break
            all_posts.extend(posts)
            if len(posts) < 100:
                break
            page += 1
            time.sleep(2)
        except Exception as e:
            print(f"  Error on page {page}: {e}")
            break
    return all_posts

def fetch_all_categories():
    """Fetch all categories."""
    all_cats = []
    page = 1
    while True:
        try:
            cats = api_get(f"categories?per_page=100&page={page}")
            if not cats or isinstance(cats, dict):
                break
            all_cats.extend(cats)
            if len(cats) < 100:
                break
            page += 1
            time.sleep(2)
        except Exception as e:
            break
    return {c['id']: c['name'] for c in all_cats}

def count_internal_links(content):
    """Count internal links to pethubonline.com in post content."""
    pattern = r'href=["\']https?://pethubonline\.com/[^"\']*["\']'
    matches = re.findall(pattern, content, re.IGNORECASE)
    return len(matches)

def extract_internal_link_targets(content):
    """Extract all internal link target slugs from content."""
    pattern = r'href=["\']https?://pethubonline\.com/([^"\'#?]*)["\']'
    matches = re.findall(pattern, content, re.IGNORECASE)
    # Clean up slugs
    slugs = []
    for m in matches:
        slug = m.strip('/').split('/')[-1] if m.strip('/') else ''
        if slug and slug not in ('', 'wp-json', 'wp-admin', 'wp-content'):
            slugs.append(slug)
    return slugs

def determine_cluster(post, cat_map):
    """Determine post cluster from categories."""
    cats = post.get('categories', [])
    for cid in cats:
        name = cat_map.get(cid, '')
        if name and name != 'Uncategorized':
            return name
    return 'Uncategorized'

# Cluster groupings for corridor analysis
CLUSTER_GROUPS = {
    'Dog Toys': ['Dog Toys'],
    'Dog Health': ['Dog Health'],
    'Dog Training': ['Dog Training'],
    'Dog Food': ['Dog Food'],
    'Cat Toys': ['Cat Toys'],
    'Cat Supplies': ['Cat Supplies'],
    'Dog Beds': ['Dog Beds'],
    'Dog Grooming': ['Dog Grooming'],
    'Puppy Care': ['Puppy Care'],
    'Dog Supplies': ['Dog Supplies'],
    'Dog Harnesses': ['Dog Harnesses'],
    'Cat Food': ['Cat Food'],
    'Cat Health': ['Cat Health'],
}

def normalize_cluster(cluster):
    """Map cluster to its group."""
    for group, members in CLUSTER_GROUPS.items():
        if cluster in members:
            return group
    return cluster

def main():
    print("=" * 60)
    print("PHASE 10AK - Phase 1: Internal Link Audit")
    print("=" * 60)

    # Fetch categories
    print("\n[1] Fetching categories...")
    cat_map = fetch_all_categories()
    print(f"  Found {len(cat_map)} categories")
    for cid, name in sorted(cat_map.items()):
        print(f"    {cid}: {name}")

    # Fetch all posts
    print("\n[2] Fetching all published posts...")
    posts = fetch_all_posts()
    print(f"  Found {len(posts)} published posts")

    # Build slug-to-post map
    slug_to_post = {}
    id_to_post = {}
    for p in posts:
        slug_to_post[p['slug']] = p
        id_to_post[p['id']] = p

    # Audit each post
    print("\n[3] Auditing internal links...")
    audit_rows = []
    cluster_links = {}  # cluster -> set of linked clusters
    post_link_targets = {}  # post_id -> list of target slugs

    for i, post in enumerate(posts):
        pid = post['id']
        title = post['title']['rendered']
        content = post['content']['rendered']
        cluster = determine_cluster(post, cat_map)
        slug = post['slug']

        internal_count = count_internal_links(content)
        target_slugs = extract_internal_link_targets(content)
        needs_reinforcement = internal_count < 5
        has_related_reading = 'Related Reading' in content

        # Track cross-cluster links
        norm_cluster = normalize_cluster(cluster)
        if norm_cluster not in cluster_links:
            cluster_links[norm_cluster] = {}

        for ts in target_slugs:
            if ts in slug_to_post:
                target_cluster = determine_cluster(slug_to_post[ts], cat_map)
                target_norm = normalize_cluster(target_cluster)
                if target_norm != norm_cluster:
                    if target_norm not in cluster_links[norm_cluster]:
                        cluster_links[norm_cluster][target_norm] = []
                    cluster_links[norm_cluster][target_norm].append({
                        'source_id': pid,
                        'source_slug': slug,
                        'target_slug': ts
                    })

        post_link_targets[pid] = target_slugs

        audit_rows.append({
            'id': pid,
            'title': title,
            'slug': slug,
            'cluster': cluster,
            'internal_link_count': internal_count,
            'has_related_reading': has_related_reading,
            'needs_reinforcement': needs_reinforcement
        })

        if (i + 1) % 20 == 0:
            print(f"  Audited {i+1}/{len(posts)} posts...")

    # Write audit CSV
    audit_file = f"{DATA_DIR}/internal_link_audit.csv"
    with open(audit_file, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['id', 'title', 'slug', 'cluster', 'internal_link_count', 'has_related_reading', 'needs_reinforcement'])
        w.writeheader()
        w.writerows(audit_rows)
    print(f"\n  Audit written to {audit_file}")

    # Summary
    needs_work = [r for r in audit_rows if r['needs_reinforcement']]
    has_related = [r for r in audit_rows if r['has_related_reading']]
    print(f"\n  SUMMARY:")
    print(f"  Total posts: {len(audit_rows)}")
    print(f"  Posts with < 5 internal links: {len(needs_work)}")
    print(f"  Posts already with Related Reading: {len(has_related)}")

    # Cluster distribution
    cluster_counts = {}
    for r in audit_rows:
        c = r['cluster']
        if c not in cluster_counts:
            cluster_counts[c] = {'total': 0, 'under_linked': 0, 'avg_links': 0}
        cluster_counts[c]['total'] += 1
        cluster_counts[c]['avg_links'] += r['internal_link_count']
        if r['needs_reinforcement']:
            cluster_counts[c]['under_linked'] += 1

    print(f"\n  Cluster breakdown:")
    for c, stats in sorted(cluster_counts.items()):
        avg = stats['avg_links'] / stats['total'] if stats['total'] > 0 else 0
        print(f"    {c}: {stats['total']} posts, {stats['under_linked']} under-linked, avg {avg:.1f} links")

    # Corridor analysis
    print(f"\n  Cross-cluster corridor analysis:")
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

    corridor_status = []
    for c1, c2 in corridors:
        fwd = len(cluster_links.get(c1, {}).get(c2, []))
        rev = len(cluster_links.get(c2, {}).get(c1, []))
        fwd_ok = "OK" if fwd >= 2 else "NEEDS_LINKS"
        rev_ok = "OK" if rev >= 2 else "NEEDS_LINKS"
        print(f"    {c1} -> {c2}: {fwd} links ({fwd_ok})")
        print(f"    {c2} -> {c1}: {rev} links ({rev_ok})")

        corridor_status.append({
            'corridor': f"{c1} <-> {c2}",
            'direction': f"{c1} -> {c2}",
            'links_found': fwd,
            'links_added': 0,
            'status': fwd_ok
        })
        corridor_status.append({
            'corridor': f"{c1} <-> {c2}",
            'direction': f"{c2} -> {c1}",
            'links_found': rev,
            'links_added': 0,
            'status': rev_ok
        })

    # Write corridor status
    corridor_file = f"{DATA_DIR}/corridor_status.csv"
    with open(corridor_file, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['corridor', 'direction', 'links_found', 'links_added', 'status'])
        w.writeheader()
        w.writerows(corridor_status)
    print(f"\n  Corridor status written to {corridor_file}")

    # Save posts data for phase 2
    posts_cache = f"{DATA_DIR}/posts_cache.json"
    post_data = []
    for p in posts:
        post_data.append({
            'id': p['id'],
            'title': p['title']['rendered'],
            'slug': p['slug'],
            'link': p['link'],
            'content': p['content']['rendered'],
            'categories': p['categories'],
            'cluster': determine_cluster(p, cat_map)
        })
    with open(posts_cache, 'w') as f:
        json.dump(post_data, f)
    print(f"  Posts cache saved to {posts_cache}")

    # Save cluster links for corridor work
    cl_cache = f"{DATA_DIR}/cluster_links_cache.json"
    # Convert sets to lists for JSON
    cl_serializable = {}
    for c, targets in cluster_links.items():
        cl_serializable[c] = {}
        for t, links in targets.items():
            cl_serializable[c][t] = links
    with open(cl_cache, 'w') as f:
        json.dump(cl_serializable, f)
    print(f"  Cluster links cache saved to {cl_cache}")

    return needs_work, corridor_status

if __name__ == '__main__':
    main()
