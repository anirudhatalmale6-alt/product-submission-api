#!/usr/bin/env python3
"""Phase 10AK - Phase 2 & 3: Insert cross-cluster links and complete corridor gaps."""

import subprocess, json, csv, re, time, os, tempfile, html
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

def api_update_post(post_id, data):
    """Update a post via WP REST API using temp file for JSON body."""
    url = f"{BASE}/posts/{post_id}"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        tmpfile = f.name
    try:
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-d", f"@{tmpfile}",
             "-H", "Content-Type: application/json",
             "-X", "POST", url],
            capture_output=True, text=True, timeout=60
        )
        resp = json.loads(result.stdout)
        if 'id' in resp:
            return True, resp
        else:
            return False, resp
    except Exception as e:
        return False, str(e)
    finally:
        os.unlink(tmpfile)

def decode_html(text):
    """Decode HTML entities."""
    return html.unescape(text)

def classify_topic(post):
    """Classify a post into a semantic topic based on title and content keywords."""
    title = decode_html(post['title']).lower()
    slug = post['slug'].lower()
    cat = post.get('cluster', '')

    # Direct category matches
    if cat in ['Dog Toys', 'Cat Toys']:
        return cat

    # Title/slug-based classification
    keywords = {
        'Dog Toys': ['dog toy', 'dog toys', 'chew toy', 'fetch', 'tug play', 'puzzle toy',
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
                     'bed sizing', 'bed material', 'elevated bed', 'dog bed type'],
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
        'Cat Toys': ['cat toy', 'cat toys', 'cat play', 'cat enrichment', 'kitten toy',
                     'cat personality', 'cat toy rotation', 'indoor cat toy'],
        'Pet Care': ['multi-pet', 'seasonal pet', 'pet hydration', 'pet first aid',
                     'seasonal dog care', 'pet enrichment explained', 'pet toy safety'],
    }

    for topic, kws in keywords.items():
        for kw in kws:
            if kw in title or kw in slug:
                return topic

    # Fallback to WP category
    return cat

def extract_internal_links(content):
    """Extract all internal link URLs from content."""
    pattern = r'href=["\']https?://pethubonline\.com/([^"\'#?]*)["\']'
    matches = re.findall(pattern, content, re.IGNORECASE)
    slugs = set()
    for m in matches:
        slug = m.strip('/').split('/')[-1] if m.strip('/') else ''
        if slug and slug not in ('', 'wp-json', 'wp-admin', 'wp-content', 'wp-includes'):
            slugs.add(slug)
    return slugs

def has_related_reading(content):
    """Check if post already has a Related Reading section."""
    return 'Related Reading' in content

def find_trust_footer_position(content):
    """Find where to insert Related Reading (before trust footer or at end)."""
    # Look for common trust footer patterns
    patterns = [
        r'<!-- wp:heading[^>]*-->\s*<h[23][^>]*>(?:Why Trust|Sources|References|Our Commitment)',
        r'<!-- wp:heading[^>]*-->\s*<h[23][^>]*>(?:Final Thoughts|Conclusion|The Bottom Line)',
        r'<h[23][^>]*>(?:Why Trust|Sources|References|Our Commitment)',
    ]
    for pat in patterns:
        match = re.search(pat, content, re.IGNORECASE)
        if match:
            return match.start()

    # Fallback: insert before last heading or at end
    last_h = None
    for m in re.finditer(r'<!-- wp:heading', content):
        last_h = m.start()
    if last_h:
        return last_h

    return len(content)

def build_related_reading_block(links):
    """Build a Related Reading HTML block."""
    items = []
    for link in links:
        url = f"https://pethubonline.com/{link['slug']}/"
        anchor = link['anchor']
        desc = link['description']
        items.append(f'<li><a href="{url}">{anchor}</a> -- {desc}</li>')

    items_html = "\n".join(items)
    block = f"""<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">Related Reading</h3>
<!-- /wp:heading -->
<!-- wp:list -->
<ul class="wp-block-list">
{items_html}
</ul>
<!-- /wp:list -->

"""
    return block

def generate_anchor_and_desc(target_post, source_topic, target_topic):
    """Generate descriptive anchor text and brief description for cross-cluster links."""
    title = decode_html(target_post['title'])
    slug = target_post['slug']

    # Create a shorter, more natural anchor text from the title
    anchor = title
    # Strip common suffixes
    for suffix in [' UK (2026)', ' (2026)', ' – Complete Guide', ' – Honest Reviews',
                   ': Complete Guide', ': A Complete Guide', ': A Practical Guide']:
        anchor = anchor.replace(suffix, '')

    # Generate description based on cross-cluster relationship
    topic_descriptions = {
        ('Dog Toys', 'Dog Health'): 'Understanding the health benefits of appropriate play.',
        ('Dog Toys', 'Dog Training'): 'How play supports training and behaviour development.',
        ('Dog Toys', 'Puppy Care'): 'Choosing age-appropriate toys for growing puppies.',
        ('Dog Toys', 'Dog Grooming'): 'Keeping toys and dogs clean for overall wellbeing.',
        ('Dog Health', 'Dog Toys'): 'Using play and enrichment to support your dog\'s health.',
        ('Dog Health', 'Dog Food'): 'How nutrition supports overall health and recovery.',
        ('Dog Health', 'Dog Beds'): 'Comfortable rest supports joint health and recovery.',
        ('Dog Health', 'Dog Grooming'): 'Regular grooming helps detect health issues early.',
        ('Dog Training', 'Dog Toys'): 'Enrichment toys that reinforce training outcomes.',
        ('Dog Training', 'Puppy Care'): 'Early training sets the foundation for good behaviour.',
        ('Dog Food', 'Dog Health'): 'Proper nutrition is the cornerstone of canine wellness.',
        ('Dog Beds', 'Dog Health'): 'Quality rest supports joint care and recovery.',
        ('Dog Grooming', 'Dog Health'): 'Grooming routines help maintain skin and coat health.',
        ('Puppy Care', 'Dog Training'): 'Structured training supports puppy development.',
        ('Puppy Care', 'Dog Toys'): 'Safe play is essential for puppy growth and confidence.',
        ('Cat Toys', 'Cat Supplies'): 'Essential supplies that complement your cat\'s play.',
        ('Cat Supplies', 'Cat Toys'): 'Interactive toys keep indoor cats engaged and healthy.',
    }

    key = (source_topic, target_topic)
    desc = topic_descriptions.get(key, f'A helpful guide covering {target_topic.lower()} essentials.')

    return anchor, desc

# ======== CORRIDOR DEFINITIONS ========
# Each corridor: (cluster_a, cluster_b, context_phrase_a_to_b, context_phrase_b_to_a)
CORRIDORS = [
    ('Dog Toys', 'Dog Health', 'play and safety', 'enrichment and physical health'),
    ('Dog Toys', 'Dog Training', 'enrichment and behaviour', 'training through play'),
    ('Dog Food', 'Dog Health', 'nutrition and wellness', 'health-driven nutrition'),
    ('Cat Toys', 'Cat Supplies', 'play and essentials', 'essentials for play'),
    ('Dog Beds', 'Dog Health', 'comfort and joint care', 'rest and recovery'),
    ('Dog Grooming', 'Dog Health', 'skin and coat', 'health and hygiene'),
    ('Puppy Care', 'Dog Training', 'development and learning', 'learning and growth'),
    ('Puppy Care', 'Dog Toys', 'appropriate toys by age', 'age-appropriate play'),
]


def main():
    print("=" * 70)
    print("PHASE 10AK - Phase 2 & 3: Cross-Cluster Link Insertion")
    print("=" * 70)

    # Load cached posts
    print("\n[1] Loading posts data...")
    posts = json.load(open(f"{DATA_DIR}/posts_cache.json"))
    print(f"  Loaded {len(posts)} posts")

    # Classify all posts by topic
    print("\n[2] Classifying posts by semantic topic...")
    for p in posts:
        p['topic'] = classify_topic(p)

    topic_counts = defaultdict(int)
    for p in posts:
        topic_counts[p['topic']] += 1

    for topic, count in sorted(topic_counts.items(), key=lambda x: -x[1]):
        print(f"    {topic}: {count} posts")

    # Build lookup maps
    slug_to_post = {p['slug']: p for p in posts}
    id_to_post = {p['id']: p for p in posts}
    topic_to_posts = defaultdict(list)
    for p in posts:
        topic_to_posts[p['topic']].append(p)

    # ========= PHASE 2: Related Reading for under-linked posts =========
    print("\n" + "=" * 70)
    print("PHASE 2: Related Reading Insertion for Under-Linked Posts")
    print("=" * 70)

    # Read audit to find under-linked posts
    audit_rows = []
    with open(f"{DATA_DIR}/internal_link_audit.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            audit_rows.append(row)

    # Also identify posts that could benefit from Related Reading
    # (those without it, even if they have enough links)
    candidates = []
    for row in audit_rows:
        pid = int(row['id'])
        post = id_to_post.get(pid)
        if not post:
            continue
        has_rr = row['has_related_reading'] == 'True'
        link_count = int(row['internal_link_count'])
        if not has_rr and link_count < 10:
            candidates.append({
                'id': pid,
                'title': decode_html(post['title']),
                'slug': post['slug'],
                'topic': post['topic'],
                'link_count': link_count,
                'content': post['content']
            })

    print(f"\n  Found {len(candidates)} posts without Related Reading (link count < 10)")

    # Sort by link count (most under-linked first)
    candidates.sort(key=lambda x: x['link_count'])

    # Limit to top 30 most in need
    candidates = candidates[:30]
    print(f"  Processing top {len(candidates)} posts")

    insertion_log = []
    updates_made = 0

    for i, cand in enumerate(candidates):
        pid = cand['id']
        slug = cand['slug']
        topic = cand['topic']
        content = cand['content']
        existing_slugs = extract_internal_links(content)

        print(f"\n  [{i+1}/{len(candidates)}] Post {pid}: {cand['title'][:60]}...")
        print(f"    Topic: {topic}, Current links: {cand['link_count']}")

        # Find posts from OTHER topics to link to
        related_links = []
        # Priority topics based on corridors
        priority_targets = []
        for c1, c2, _, _ in CORRIDORS:
            if topic == c1:
                priority_targets.append(c2)
            elif topic == c2:
                priority_targets.append(c1)

        # Add general cross-topic targets
        all_topics = list(topic_to_posts.keys())
        other_topics = [t for t in all_topics if t != topic and t != 'Uncategorized' and t != 'Pet Care']

        # Prioritize corridor partners, then other topics
        search_order = priority_targets + [t for t in other_topics if t not in priority_targets]

        for target_topic in search_order:
            if len(related_links) >= 5:
                break
            target_posts = topic_to_posts.get(target_topic, [])
            for tp in target_posts:
                if len(related_links) >= 5:
                    break
                if tp['slug'] in existing_slugs:
                    continue  # Already linked
                if tp['slug'] == slug:
                    continue  # Self-link
                anchor, desc = generate_anchor_and_desc(tp, topic, target_topic)
                related_links.append({
                    'slug': tp['slug'],
                    'anchor': anchor,
                    'description': desc,
                    'target_id': tp['id'],
                    'target_topic': target_topic
                })

        if not related_links:
            print(f"    No suitable cross-cluster links found, skipping")
            continue

        if len(related_links) < 3:
            print(f"    Only {len(related_links)} links found, skipping (need at least 3)")
            continue

        # Take 3-5 links
        related_links = related_links[:5]

        # Build Related Reading block
        rr_block = build_related_reading_block(related_links)

        # Find insertion point
        insert_pos = find_trust_footer_position(content)
        new_content = content[:insert_pos] + rr_block + content[insert_pos:]

        print(f"    Adding {len(related_links)} cross-cluster links:")
        for rl in related_links:
            print(f"      -> {rl['target_topic']}: {rl['anchor'][:50]}")

        # Update post
        time.sleep(2)
        success, resp = api_update_post(pid, {'content': new_content})

        if success:
            print(f"    SUCCESS - Updated post {pid}")
            updates_made += 1
            for rl in related_links:
                insertion_log.append({
                    'source_id': pid,
                    'source_title': cand['title'],
                    'source_topic': topic,
                    'target_id': rl['target_id'],
                    'target_slug': rl['slug'],
                    'target_topic': rl['target_topic'],
                    'anchor_text': rl['anchor'],
                    'link_type': 'related_reading',
                    'status': 'INSERTED'
                })
        else:
            print(f"    FAILED - {str(resp)[:100]}")
            for rl in related_links:
                insertion_log.append({
                    'source_id': pid,
                    'source_title': cand['title'],
                    'source_topic': topic,
                    'target_id': rl['target_id'],
                    'target_slug': rl['slug'],
                    'target_topic': rl['target_topic'],
                    'anchor_text': rl['anchor'],
                    'link_type': 'related_reading',
                    'status': 'FAILED'
                })

    print(f"\n  Phase 2 complete: {updates_made} posts updated with Related Reading")

    # ========= PHASE 3: Critical Corridor Links =========
    print("\n" + "=" * 70)
    print("PHASE 3: Cross-Cluster Corridor Completion")
    print("=" * 70)

    # Re-fetch posts that were updated to get fresh content
    print("\n  Re-fetching updated posts for corridor analysis...")
    time.sleep(2)
    fresh_posts = []
    page = 1
    while True:
        try:
            batch = api_get(f"posts?per_page=100&page={page}&status=publish")
            if not batch or isinstance(batch, dict):
                break
            for p in batch:
                fresh_posts.append({
                    'id': p['id'],
                    'title': p['title']['rendered'],
                    'slug': p['slug'],
                    'link': p['link'],
                    'content': p['content']['rendered'],
                    'categories': p['categories'],
                })
            if len(batch) < 100:
                break
            page += 1
            time.sleep(2)
        except Exception as e:
            print(f"  Error fetching: {e}")
            break

    # Re-classify
    for p in fresh_posts:
        p['cluster'] = ''  # Will be set by classify_topic
        p['topic'] = classify_topic(p)

    fresh_slug_map = {p['slug']: p for p in fresh_posts}
    fresh_id_map = {p['id']: p for p in fresh_posts}
    fresh_topic_map = defaultdict(list)
    for p in fresh_posts:
        fresh_topic_map[p['topic']].append(p)

    corridor_updates = []
    corridor_log = []

    for c1, c2, context_fwd, context_rev in CORRIDORS:
        print(f"\n  Corridor: {c1} <-> {c2}")

        # Check forward links (c1 -> c2)
        c1_posts = fresh_topic_map.get(c1, [])
        c2_posts = fresh_topic_map.get(c2, [])

        if not c1_posts or not c2_posts:
            print(f"    SKIP: {c1} has {len(c1_posts)} posts, {c2} has {len(c2_posts)} posts")
            corridor_log.append({
                'corridor': f"{c1} <-> {c2}",
                'direction': f"{c1} -> {c2}",
                'links_found': 0,
                'links_added': 0,
                'status': 'SKIP_NO_POSTS'
            })
            corridor_log.append({
                'corridor': f"{c1} <-> {c2}",
                'direction': f"{c2} -> {c1}",
                'links_found': 0,
                'links_added': 0,
                'status': 'SKIP_NO_POSTS'
            })
            continue

        c2_slugs = {p['slug'] for p in c2_posts}
        c1_slugs = {p['slug'] for p in c1_posts}

        # Count existing forward links
        fwd_links = 0
        for p in c1_posts:
            linked = extract_internal_links(p['content'])
            fwd_links += len(linked & c2_slugs)

        # Count existing reverse links
        rev_links = 0
        for p in c2_posts:
            linked = extract_internal_links(p['content'])
            rev_links += len(linked & c1_slugs)

        print(f"    {c1} -> {c2}: {fwd_links} existing links")
        print(f"    {c2} -> {c1}: {rev_links} existing links")

        # Add forward links if needed (c1 posts linking to c2)
        fwd_added = 0
        if fwd_links < 2:
            needed = 2 - fwd_links
            print(f"    Adding {needed} forward links ({c1} -> {c2})...")

            # Find best c1 posts to add links to (those with most content, fewest existing links to c2)
            for source in c1_posts:
                if fwd_added >= needed:
                    break
                existing = extract_internal_links(source['content'])
                already_links_to_c2 = existing & c2_slugs
                if already_links_to_c2:
                    continue  # This post already links to c2

                # Pick a c2 target
                target = None
                for t in c2_posts:
                    if t['slug'] not in existing:
                        target = t
                        break
                if not target:
                    continue

                # Build contextual inline link
                target_title = decode_html(target['title'])
                anchor = target_title
                for suffix in [' UK (2026)', ' (2026)', ' – Complete Guide', ' – Honest Reviews',
                               ': Complete Guide', ': A Complete Guide']:
                    anchor = anchor.replace(suffix, '')

                link_html = f'<a href="https://pethubonline.com/{target["slug"]}/">{anchor}</a>'

                # Try to insert into an existing paragraph near the end
                content = source['content']

                # Find a good paragraph to add the link to (look for last substantial paragraph)
                # Insert a contextual sentence before the trust footer
                insert_pos = find_trust_footer_position(content)

                context_sentence = f'\n<!-- wp:paragraph -->\n<p>For more on {context_fwd}, see our guide to {link_html}.</p>\n<!-- /wp:paragraph -->\n\n'
                new_content = content[:insert_pos] + context_sentence + content[insert_pos:]

                time.sleep(2)
                success, resp = api_update_post(source['id'], {'content': new_content})

                if success:
                    fwd_added += 1
                    print(f"      INSERTED: {decode_html(source['title'])[:40]}... -> {target_title[:40]}...")
                    insertion_log.append({
                        'source_id': source['id'],
                        'source_title': decode_html(source['title']),
                        'source_topic': c1,
                        'target_id': target['id'],
                        'target_slug': target['slug'],
                        'target_topic': c2,
                        'anchor_text': anchor,
                        'link_type': 'corridor_contextual',
                        'status': 'INSERTED'
                    })
                    # Update fresh content for this post
                    source['content'] = new_content
                else:
                    print(f"      FAILED: {str(resp)[:80]}")
                    insertion_log.append({
                        'source_id': source['id'],
                        'source_title': decode_html(source['title']),
                        'source_topic': c1,
                        'target_id': target['id'],
                        'target_slug': target['slug'],
                        'target_topic': c2,
                        'anchor_text': anchor,
                        'link_type': 'corridor_contextual',
                        'status': 'FAILED'
                    })

        corridor_log.append({
            'corridor': f"{c1} <-> {c2}",
            'direction': f"{c1} -> {c2}",
            'links_found': fwd_links,
            'links_added': fwd_added,
            'status': 'OK' if (fwd_links + fwd_added) >= 2 else 'PARTIAL'
        })

        # Add reverse links if needed (c2 posts linking to c1)
        rev_added = 0
        if rev_links < 2:
            needed = 2 - rev_links
            print(f"    Adding {needed} reverse links ({c2} -> {c1})...")

            for source in c2_posts:
                if rev_added >= needed:
                    break
                existing = extract_internal_links(source['content'])
                already_links_to_c1 = existing & c1_slugs
                if already_links_to_c1:
                    continue

                target = None
                for t in c1_posts:
                    if t['slug'] not in existing:
                        target = t
                        break
                if not target:
                    continue

                target_title = decode_html(target['title'])
                anchor = target_title
                for suffix in [' UK (2026)', ' (2026)', ' – Complete Guide', ' – Honest Reviews',
                               ': Complete Guide', ': A Complete Guide']:
                    anchor = anchor.replace(suffix, '')

                link_html = f'<a href="https://pethubonline.com/{target["slug"]}/">{anchor}</a>'
                content = source['content']
                insert_pos = find_trust_footer_position(content)
                context_sentence = f'\n<!-- wp:paragraph -->\n<p>For more on {context_rev}, see our guide to {link_html}.</p>\n<!-- /wp:paragraph -->\n\n'
                new_content = content[:insert_pos] + context_sentence + content[insert_pos:]

                time.sleep(2)
                success, resp = api_update_post(source['id'], {'content': new_content})

                if success:
                    rev_added += 1
                    print(f"      INSERTED: {decode_html(source['title'])[:40]}... -> {target_title[:40]}...")
                    insertion_log.append({
                        'source_id': source['id'],
                        'source_title': decode_html(source['title']),
                        'source_topic': c2,
                        'target_id': target['id'],
                        'target_slug': target['slug'],
                        'target_topic': c1,
                        'anchor_text': anchor,
                        'link_type': 'corridor_contextual',
                        'status': 'INSERTED'
                    })
                    source['content'] = new_content
                else:
                    print(f"      FAILED: {str(resp)[:80]}")
                    insertion_log.append({
                        'source_id': source['id'],
                        'source_title': decode_html(source['title']),
                        'source_topic': c2,
                        'target_id': target['id'],
                        'target_slug': target['slug'],
                        'target_topic': c1,
                        'anchor_text': anchor,
                        'link_type': 'corridor_contextual',
                        'status': 'FAILED'
                    })

        corridor_log.append({
            'corridor': f"{c1} <-> {c2}",
            'direction': f"{c2} -> {c1}",
            'links_found': rev_links,
            'links_added': rev_added,
            'status': 'OK' if (rev_links + rev_added) >= 2 else 'PARTIAL'
        })

    # ========= WRITE LOGS =========
    print("\n" + "=" * 70)
    print("Writing logs...")
    print("=" * 70)

    # Link insertions log
    log_file = f"{DATA_DIR}/link_insertions_log.csv"
    with open(log_file, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=[
            'source_id', 'source_title', 'source_topic',
            'target_id', 'target_slug', 'target_topic',
            'anchor_text', 'link_type', 'status'
        ])
        w.writeheader()
        w.writerows(insertion_log)
    print(f"  Link insertions log: {log_file} ({len(insertion_log)} entries)")

    # Corridor status log
    corr_file = f"{DATA_DIR}/corridor_status.csv"
    with open(corr_file, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=[
            'corridor', 'direction', 'links_found', 'links_added', 'status'
        ])
        w.writeheader()
        w.writerows(corridor_log)
    print(f"  Corridor status: {corr_file} ({len(corridor_log)} entries)")

    # Summary
    inserted = len([l for l in insertion_log if l['status'] == 'INSERTED'])
    failed = len([l for l in insertion_log if l['status'] == 'FAILED'])
    ok_corridors = len([c for c in corridor_log if c['status'] == 'OK'])
    partial_corridors = len([c for c in corridor_log if c['status'] == 'PARTIAL'])

    print(f"\n  FINAL SUMMARY:")
    print(f"  Links inserted: {inserted}")
    print(f"  Links failed: {failed}")
    print(f"  Corridor directions OK: {ok_corridors}/{len(corridor_log)}")
    print(f"  Corridor directions partial: {partial_corridors}/{len(corridor_log)}")


if __name__ == '__main__':
    main()
