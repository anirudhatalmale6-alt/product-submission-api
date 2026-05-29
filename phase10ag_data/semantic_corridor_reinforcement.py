#!/usr/bin/env python3
"""
Semantic Corridor Reinforcement & Hub-Spoke Internal Link Architecture
PetHub Online (pethubonline.com)
Phase 10AG - Internal Link Audit & Reinforcement
"""

import json
import csv
import re
import time
import subprocess
import os
import sys
import tempfile
from html.parser import HTMLParser
from collections import defaultdict

# ── Config ──────────────────────────────────────────────────────────────
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
BASE = "https://pethubonline.com/wp-json/wp/v2"
DOMAIN = "pethubonline.com"
OUT_DIR = "/var/lib/freelancer/projects/40416335/phase10ag_data"
DELAY = 0.5

# ── API Helper ──────────────────────────────────────────────────────────
def api_get(endpoint, params=None):
    """GET request via curl subprocess."""
    url = f"{BASE}/{endpoint}"
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"  [ERROR] curl failed for {url}: {result.stderr}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  [ERROR] JSON decode failed for {url}: {result.stdout[:200]}")
        return None

def api_post(endpoint, data):
    """POST request via curl subprocess, writing JSON to temp file."""
    url = f"{BASE}/{endpoint}"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        tmpfile = f.name
    try:
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", f"@{tmpfile}",
             url],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"  [ERROR] POST failed for {url}: {result.stderr}")
            return None
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"  [ERROR] JSON decode failed: {result.stdout[:300]}")
            return None
    finally:
        os.unlink(tmpfile)


# ── HTML Link Extractor ─────────────────────────────────────────────────
class LinkExtractor(HTMLParser):
    """Extract all <a href="...">anchor text</a> from HTML content."""
    def __init__(self):
        super().__init__()
        self.links = []  # list of (href, anchor_text)
        self._current_href = None
        self._current_text = ""

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            href = dict(attrs).get('href', '')
            self._current_href = href
            self._current_text = ""

    def handle_data(self, data):
        if self._current_href is not None:
            self._current_text += data

    def handle_endtag(self, tag):
        if tag == 'a' and self._current_href is not None:
            self.links.append((self._current_href, self._current_text.strip()))
            self._current_href = None
            self._current_text = ""


def extract_internal_links(html_content):
    """Extract all internal links from HTML content."""
    parser = LinkExtractor()
    try:
        parser.feed(html_content or "")
    except Exception:
        pass
    internal = []
    for href, anchor in parser.links:
        if DOMAIN in href or (href.startswith('/') and not href.startswith('//')):
            internal.append((href, anchor))
    return internal


def slug_from_url(url):
    """Extract slug from a pethubonline.com URL."""
    url = url.rstrip('/')
    # Remove query string and fragment
    url = url.split('?')[0].split('#')[0]
    parts = url.split('/')
    return parts[-1] if parts else ""


# ── Cluster Detection ────────────────────────────────────────────────────
CLUSTER_KEYWORDS = {
    "Dog Toys": ["dog-toy", "dog-toys", "chew-toy", "fetch", "tug-toy", "puzzle-toy", "squeaky", "plush-toy"],
    "Cat Toys": ["cat-toy", "cat-toys", "feather-toy", "laser", "catnip", "interactive-cat"],
    "Dog Beds": ["dog-bed", "dog-beds", "orthopaedic", "orthopedic", "elevated-bed", "crate-bed", "calming-bed", "memory-foam-bed", "cooling-bed", "heated-bed", "bolster-bed", "nest-bed"],
    "Dog Food": ["dog-food", "puppy-food", "dog-nutrition", "dog-diet", "kibble", "raw-diet-dog", "grain-free-dog", "senior-dog-food"],
    "Cat Food": ["cat-food", "kitten-food", "cat-nutrition", "cat-diet", "wet-cat-food", "dry-cat-food"],
    "Dog Health": ["dog-health", "dog-vet", "dog-vaccination", "flea-tick-dog", "heartworm", "dog-dental", "dog-arthritis", "dog-allergy"],
    "Cat Health": ["cat-health", "cat-vet", "cat-vaccination", "flea-tick-cat", "cat-dental", "cat-allergy"],
    "Dog Grooming": ["dog-grooming", "dog-bath", "dog-brush", "dog-nail", "dog-shampoo", "dog-haircut", "grooming-tool"],
    "Cat Grooming": ["cat-grooming", "cat-brush", "cat-nail", "cat-bath"],
    "Dog Training": ["dog-training", "puppy-training", "obedience", "crate-training", "leash-training", "clicker", "potty-training"],
    "Puppy Care": ["puppy-care", "new-puppy", "puppy-proof", "puppy-socializ", "puppy-feeding", "puppy-sleep", "puppy-checklist"],
    "Cat Supplies": ["cat-supplies", "cat-litter", "cat-carrier", "cat-scratch", "cat-tree", "cat-harness", "cat-collar", "cat-bed"],
    "Indoor Cats": ["indoor-cat", "indoor-cats", "apartment-cat", "cat-enrichment", "window-perch"],
    "Dog Supplies": ["dog-supplies", "dog-collar", "dog-leash", "dog-harness", "dog-crate", "dog-bowl", "dog-carrier"],
    "Pet Safety": ["pet-safety", "pet-proof", "toxic", "poison", "emergency-vet", "first-aid-pet"],
    "Glossary": ["glossary", "define", "terminology", "what-is", "meaning-of"],
}

def detect_cluster(slug, title=""):
    """Detect which cluster a post belongs to based on slug and title."""
    combined = (slug + " " + title).lower()
    best_match = "Other"
    best_score = 0
    for cluster, keywords in CLUSTER_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > best_score:
            best_score = score
            best_match = cluster
    # Fallback heuristics
    if best_score == 0:
        if "dog" in combined and "toy" in combined:
            return "Dog Toys"
        elif "cat" in combined and "toy" in combined:
            return "Cat Toys"
        elif "dog" in combined and "bed" in combined:
            return "Dog Beds"
        elif "dog" in combined and ("food" in combined or "nutrition" in combined or "diet" in combined):
            return "Dog Food"
        elif "cat" in combined and ("food" in combined or "nutrition" in combined or "diet" in combined):
            return "Cat Food"
        elif "dog" in combined and ("health" in combined or "vet" in combined):
            return "Dog Health"
        elif "cat" in combined and ("health" in combined or "vet" in combined):
            return "Cat Health"
        elif "dog" in combined and "groom" in combined:
            return "Dog Grooming"
        elif "cat" in combined and "groom" in combined:
            return "Cat Grooming"
        elif "dog" in combined and "train" in combined:
            return "Dog Training"
        elif "puppy" in combined:
            return "Puppy Care"
        elif "cat" in combined and ("suppli" in combined or "litter" in combined or "scratch" in combined):
            return "Cat Supplies"
        elif "indoor" in combined and "cat" in combined:
            return "Indoor Cats"
        elif "dog" in combined:
            return "Dog Supplies"
        elif "cat" in combined:
            return "Cat Supplies"
    return best_match


# ═══════════════════════════════════════════════════════════════════════
# STEP 1: FULL LINK AUDIT - Fetch all posts and extract links
# ═══════════════════════════════════════════════════════════════════════
def fetch_all_posts():
    """Fetch all published posts with pagination."""
    all_posts = []
    page = 1
    while True:
        print(f"  Fetching posts page {page}...")
        data = api_get("posts", {
            "per_page": 100,
            "page": page,
            "status": "publish",
            "_fields": "id,title,slug,link,content,categories"
        })
        if not data or not isinstance(data, list) or len(data) == 0:
            break
        all_posts.extend(data)
        print(f"    Got {len(data)} posts (total: {len(all_posts)})")
        if len(data) < 100:
            break
        page += 1
        time.sleep(DELAY)
    return all_posts


def build_link_matrix(posts):
    """Build the complete internal link matrix."""
    # Build slug -> post mapping
    slug_map = {}
    id_map = {}
    for p in posts:
        title = p.get('title', {}).get('rendered', '') if isinstance(p.get('title'), dict) else str(p.get('title', ''))
        slug = p.get('slug', '')
        pid = p.get('id')
        slug_map[slug] = p
        id_map[pid] = p

    link_matrix = []  # (source_id, source_title, source_cluster, target_id, target_title, target_cluster, anchor_text, is_cross_cluster)
    outgoing = defaultdict(list)  # pid -> [(target_slug, anchor)]
    incoming = defaultdict(int)    # pid -> count

    for p in posts:
        pid = p.get('id')
        title = p.get('title', {}).get('rendered', '') if isinstance(p.get('title'), dict) else str(p.get('title', ''))
        slug = p.get('slug', '')
        content = p.get('content', {}).get('rendered', '') if isinstance(p.get('content'), dict) else str(p.get('content', ''))
        source_cluster = detect_cluster(slug, title)

        links = extract_internal_links(content)
        for href, anchor in links:
            target_slug = slug_from_url(href)
            if target_slug and target_slug in slug_map:
                tp = slug_map[target_slug]
                tid = tp.get('id')
                ttitle = tp.get('title', {}).get('rendered', '') if isinstance(tp.get('title'), dict) else str(tp.get('title', ''))
                tslug = tp.get('slug', '')
                target_cluster = detect_cluster(tslug, ttitle)
                is_cross = source_cluster != target_cluster

                link_matrix.append({
                    'source_id': pid,
                    'source_title': title,
                    'source_cluster': source_cluster,
                    'target_id': tid,
                    'target_title': ttitle,
                    'target_cluster': target_cluster,
                    'anchor_text': anchor,
                    'is_cross_cluster': is_cross
                })

                outgoing[pid].append((target_slug, anchor))
                incoming[tid] = incoming.get(tid, 0) + 1

    return link_matrix, outgoing, incoming, slug_map, id_map


# ═══════════════════════════════════════════════════════════════════════
# STEP 2: IDENTIFY WEAK CORRIDORS
# ═══════════════════════════════════════════════════════════════════════
def identify_weak_corridors(posts, link_matrix, outgoing, incoming, slug_map):
    """Find posts and cross-cluster corridors that need reinforcement."""

    # Build cluster membership
    cluster_posts = defaultdict(list)
    for p in posts:
        title = p.get('title', {}).get('rendered', '') if isinstance(p.get('title'), dict) else str(p.get('title', ''))
        slug = p.get('slug', '')
        cluster = detect_cluster(slug, title)
        cluster_posts[cluster].append(p)

    # Cross-cluster link counts
    cross_cluster_counts = defaultdict(int)
    for entry in link_matrix:
        if entry['is_cross_cluster']:
            key = tuple(sorted([entry['source_cluster'], entry['target_cluster']]))
            cross_cluster_counts[key] += 1

    # All unique cluster pairs
    clusters = list(cluster_posts.keys())
    weak_corridors = []
    for i in range(len(clusters)):
        for j in range(i+1, len(clusters)):
            pair = tuple(sorted([clusters[i], clusters[j]]))
            count = cross_cluster_counts.get(pair, 0)
            if count < 3:
                weak_corridors.append((pair[0], pair[1], count))

    # Posts with fewer than 3 outgoing internal links
    low_outgoing = []
    for p in posts:
        pid = p.get('id')
        if len(outgoing.get(pid, [])) < 3:
            title = p.get('title', {}).get('rendered', '') if isinstance(p.get('title'), dict) else str(p.get('title', ''))
            low_outgoing.append((pid, title, len(outgoing.get(pid, []))))

    # Posts with 0 incoming links
    orphans = []
    for p in posts:
        pid = p.get('id')
        if incoming.get(pid, 0) == 0:
            title = p.get('title', {}).get('rendered', '') if isinstance(p.get('title'), dict) else str(p.get('title', ''))
            orphans.append((pid, title))

    return weak_corridors, low_outgoing, orphans, cluster_posts


# ═══════════════════════════════════════════════════════════════════════
# STEP 3: INSERT CONTEXTUAL LINKS
# ═══════════════════════════════════════════════════════════════════════

# Known weak corridors to prioritize
PRIORITY_CORRIDORS = [
    ("Cat Supplies", "Dog Grooming", "grooming"),
    ("Dog Food", "Dog Health", "nutrition-health"),
    ("Puppy Care", "Dog Training", "puppy-training"),
    ("Indoor Cats", "Cat Supplies", "indoor-supplies"),
    ("Dog Beds", "Dog Health", "orthopaedic-health"),
]

# Sentence templates for variety
LINK_TEMPLATES = [
    'For related guidance on {topic}, see our complete guide to <a href="https://pethubonline.com/{slug}/">{anchor}</a>, which covers {description}.',
    'If you\'re exploring {topic}, our article on <a href="https://pethubonline.com/{slug}/">{anchor}</a> provides helpful insights into {description}.',
    'Pet owners looking into {topic} will also benefit from reading about <a href="https://pethubonline.com/{slug}/">{anchor}</a>, where we discuss {description}.',
    'To learn more about {topic}, check out our guide on <a href="https://pethubonline.com/{slug}/">{anchor}</a> for practical advice on {description}.',
    'Understanding {topic} goes hand in hand with <a href="https://pethubonline.com/{slug}/">{anchor}</a>, which explains {description}.',
    'Our detailed resource on <a href="https://pethubonline.com/{slug}/">{anchor}</a> complements this guide with expert advice on {description}.',
    'You might also find our guide to <a href="https://pethubonline.com/{slug}/">{anchor}</a> useful, as it covers {description} in depth.',
    'For a broader perspective on {topic}, explore <a href="https://pethubonline.com/{slug}/">{anchor}</a>, which addresses {description}.',
]

def build_link_paragraph(template_idx, topic, slug, anchor, description):
    """Build a WordPress paragraph block with a contextual link."""
    template = LINK_TEMPLATES[template_idx % len(LINK_TEMPLATES)]
    sentence = template.format(
        topic=topic,
        slug=slug,
        anchor=anchor,
        description=description
    )
    return f'<!-- wp:paragraph -->\n<p>{sentence}</p>\n<!-- /wp:paragraph -->'


def find_sources_section(content):
    """Find the position of Sources/References section to insert before it."""
    patterns = [
        r'<!--\s*wp:heading\s*.*?-->\s*<h[23][^>]*>\s*(?:Sources|References|Further Reading|Bibliography)',
        r'<h[23][^>]*>\s*(?:Sources|References|Further Reading|Bibliography)',
        r'<!--\s*wp:heading\s*-->\s*<h2>\s*Sources',
    ]
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.start()
    return None


def insert_link_into_post(post, link_paragraph, slug_map, existing_slugs_in_content):
    """Insert a link paragraph into a post's content before the Sources section.
    Returns updated content or None if insertion not needed."""
    content = post.get('content', {}).get('rendered', '') if isinstance(post.get('content'), dict) else str(post.get('content', ''))

    # Find where to insert - before Sources section or at end
    insert_pos = find_sources_section(content)
    if insert_pos is not None:
        new_content = content[:insert_pos] + link_paragraph + "\n\n" + content[insert_pos:]
    else:
        new_content = content + "\n\n" + link_paragraph

    return new_content


def generate_corridor_links(posts, cluster_posts, link_matrix, outgoing, slug_map):
    """Generate contextual link insertions for weak corridors."""
    insertions = []  # (source_id, source_title, target_id, target_title, corridor, anchor_text, paragraph)
    template_idx = 0

    # Build a quick lookup: existing links per post (by target slug)
    existing_links = defaultdict(set)
    for entry in link_matrix:
        source_id = entry['source_id']
        target_slug = slug_map_by_id = None
        for s, p in slug_map.items():
            if p.get('id') == entry['target_id']:
                target_slug = s
                break
        if target_slug:
            existing_links[source_id].add(target_slug)

    # Define corridor-specific link mappings
    # Each entry: (source_cluster, target_cluster, topic, anchor_desc_pairs)
    corridor_configs = [
        {
            "source_cluster": "Cat Supplies",
            "target_cluster": "Dog Grooming",
            "topic": "pet grooming essentials",
            "rationale": "grooming tools and techniques overlap between cats and dogs"
        },
        {
            "source_cluster": "Dog Grooming",
            "target_cluster": "Cat Supplies",
            "topic": "essential cat care supplies",
            "rationale": "grooming is a key part of overall pet supply needs"
        },
        {
            "source_cluster": "Dog Food",
            "target_cluster": "Dog Health",
            "topic": "how nutrition impacts your dog's health",
            "rationale": "proper nutrition is foundational to preventing common health issues"
        },
        {
            "source_cluster": "Dog Health",
            "target_cluster": "Dog Food",
            "topic": "optimal canine nutrition",
            "rationale": "diet adjustments can help manage and prevent many health conditions"
        },
        {
            "source_cluster": "Puppy Care",
            "target_cluster": "Dog Training",
            "topic": "early training for puppies",
            "rationale": "establishing good habits during puppyhood sets the foundation for a well-behaved adult dog"
        },
        {
            "source_cluster": "Dog Training",
            "target_cluster": "Puppy Care",
            "topic": "comprehensive puppy care",
            "rationale": "understanding puppy development stages helps you tailor your training approach"
        },
        {
            "source_cluster": "Indoor Cats",
            "target_cluster": "Cat Supplies",
            "topic": "supplies designed for indoor cats",
            "rationale": "indoor cats have specific environmental enrichment needs"
        },
        {
            "source_cluster": "Cat Supplies",
            "target_cluster": "Indoor Cats",
            "topic": "keeping indoor cats happy and stimulated",
            "rationale": "the right supplies make all the difference for an indoor cat's wellbeing"
        },
        {
            "source_cluster": "Dog Beds",
            "target_cluster": "Dog Health",
            "topic": "how sleep quality affects your dog's health",
            "rationale": "proper rest and joint support are crucial for dogs of all ages"
        },
        {
            "source_cluster": "Dog Health",
            "target_cluster": "Dog Beds",
            "topic": "choosing the right bed for your dog's health needs",
            "rationale": "orthopaedic and supportive beds can help manage joint pain and arthritis"
        },
        # Additional corridors to strengthen
        {
            "source_cluster": "Dog Toys",
            "target_cluster": "Dog Training",
            "topic": "using toys as training rewards",
            "rationale": "interactive toys can reinforce positive training behaviours"
        },
        {
            "source_cluster": "Cat Toys",
            "target_cluster": "Indoor Cats",
            "topic": "enrichment for indoor cats",
            "rationale": "the right toys are essential for keeping indoor cats mentally stimulated"
        },
        {
            "source_cluster": "Dog Food",
            "target_cluster": "Puppy Care",
            "topic": "feeding your new puppy",
            "rationale": "nutritional needs differ significantly between puppies and adult dogs"
        },
        {
            "source_cluster": "Cat Health",
            "target_cluster": "Cat Food",
            "topic": "feline nutrition and health",
            "rationale": "a balanced diet is the cornerstone of preventive feline healthcare"
        },
    ]

    for config in corridor_configs:
        src_cluster = config["source_cluster"]
        tgt_cluster = config["target_cluster"]
        topic = config["topic"]
        rationale = config["rationale"]

        src_posts = cluster_posts.get(src_cluster, [])
        tgt_posts = cluster_posts.get(tgt_cluster, [])

        if not src_posts or not tgt_posts:
            continue

        # Pick source posts that have fewer outgoing links first
        src_sorted = sorted(src_posts, key=lambda p: len(outgoing.get(p.get('id'), [])))

        links_added = 0
        for sp in src_sorted:
            if links_added >= 3:  # 3 links per corridor direction
                break
            sid = sp.get('id')
            stitle = sp.get('title', {}).get('rendered', '') if isinstance(sp.get('title'), dict) else str(sp.get('title', ''))
            sslug = sp.get('slug', '')

            # Pick a target post that this source doesn't already link to
            for tp in tgt_posts:
                tid = tp.get('id')
                ttitle = tp.get('title', {}).get('rendered', '') if isinstance(tp.get('title'), dict) else str(tp.get('title', ''))
                tslug = tp.get('slug', '')

                if tslug in existing_links.get(sid, set()):
                    continue  # Already linked

                # Build anchor text from target title (clean HTML entities)
                anchor = re.sub(r'<[^>]+>', '', ttitle)
                anchor = anchor.replace('&#8211;', '–').replace('&#8217;', "'").replace('&amp;', '&')
                if len(anchor) > 80:
                    anchor = anchor[:77] + "..."

                description = rationale
                paragraph = build_link_paragraph(template_idx, topic, tslug, anchor, description)
                template_idx += 1

                corridor_name = f"{src_cluster} -> {tgt_cluster}"
                insertions.append({
                    'source_id': sid,
                    'source_title': stitle,
                    'source_slug': sslug,
                    'target_id': tid,
                    'target_title': ttitle,
                    'target_slug': tslug,
                    'corridor': corridor_name,
                    'anchor_text': anchor,
                    'paragraph': paragraph
                })

                # Mark as linked now
                existing_links[sid].add(tslug)
                links_added += 1
                break

    return insertions


def generate_low_outgoing_links(posts, cluster_posts, outgoing, slug_map, link_matrix, existing_insertions):
    """Generate links for posts with fewer than 3 outgoing internal links."""
    insertions = []
    template_idx = 20  # offset to vary templates

    # Build existing links per post
    existing_links = defaultdict(set)
    for entry in link_matrix:
        source_id = entry['source_id']
        for s, p in slug_map.items():
            if p.get('id') == entry['target_id']:
                existing_links[source_id].add(s)
                break

    # Also account for already-planned insertions
    for ins in existing_insertions:
        existing_links[ins['source_id']].add(ins['target_slug'])

    # Posts with < 3 outgoing links
    low_posts = []
    for p in posts:
        pid = p.get('id')
        current_outgoing = len(outgoing.get(pid, [])) + sum(1 for ins in existing_insertions if ins['source_id'] == pid)
        if current_outgoing < 3:
            title = p.get('title', {}).get('rendered', '') if isinstance(p.get('title'), dict) else str(p.get('title', ''))
            slug = p.get('slug', '')
            cluster = detect_cluster(slug, title)
            low_posts.append((p, cluster, current_outgoing))

    # Sort by fewest links first
    low_posts.sort(key=lambda x: x[2])

    for (sp, src_cluster, count) in low_posts[:15]:  # Cap at 15 posts
        sid = sp.get('id')
        stitle = sp.get('title', {}).get('rendered', '') if isinstance(sp.get('title'), dict) else str(sp.get('title', ''))
        sslug = sp.get('slug', '')
        needed = 3 - count - sum(1 for ins in insertions if ins['source_id'] == sid)

        if needed <= 0:
            continue

        # Find same-cluster posts to link to
        same_cluster_posts = [p for p in cluster_posts.get(src_cluster, []) if p.get('id') != sid]
        for tp in same_cluster_posts:
            if needed <= 0:
                break
            tslug = tp.get('slug', '')
            if tslug in existing_links.get(sid, set()):
                continue

            tid = tp.get('id')
            ttitle = tp.get('title', {}).get('rendered', '') if isinstance(tp.get('title'), dict) else str(tp.get('title', ''))
            anchor = re.sub(r'<[^>]+>', '', ttitle).replace('&#8211;', '–').replace('&#8217;', "'").replace('&amp;', '&')
            if len(anchor) > 80:
                anchor = anchor[:77] + "..."

            topic = f"{src_cluster.lower()} essentials"
            description = f"everything you need to know about {src_cluster.lower()}"
            paragraph = build_link_paragraph(template_idx, topic, tslug, anchor, description)
            template_idx += 1

            insertions.append({
                'source_id': sid,
                'source_title': stitle,
                'source_slug': sslug,
                'target_id': tid,
                'target_title': ttitle,
                'target_slug': tslug,
                'corridor': f"{src_cluster} (same-cluster)",
                'anchor_text': anchor,
                'paragraph': paragraph
            })
            existing_links[sid].add(tslug)
            needed -= 1

    return insertions


# ═══════════════════════════════════════════════════════════════════════
# STEP 4: HUB-SPOKE REINFORCEMENT
# ═══════════════════════════════════════════════════════════════════════
def audit_hub_spokes(posts, cluster_posts, link_matrix, slug_map):
    """Audit hub pages and ensure they link to all their spokes."""
    # Identify hub pages - typically posts with "hub" indicators or known IDs
    # Hub pages often have short slugs or are the main category landing pages
    hub_audit = []

    # Build outgoing link map per post
    hub_outgoing = defaultdict(set)
    for entry in link_matrix:
        for s, p in slug_map.items():
            if p.get('id') == entry['target_id']:
                hub_outgoing[entry['source_id']].add(s)
                break

    for cluster_name, cposts in cluster_posts.items():
        if len(cposts) < 2:
            continue

        # The "hub" is typically the post with the most outgoing links in the cluster
        # or a known hub page
        best_hub = None
        best_score = -1
        for p in cposts:
            pid = p.get('id')
            # Score: outgoing links within cluster
            score = sum(1 for s in hub_outgoing.get(pid, set()) if s in [pp.get('slug', '') for pp in cposts])
            if score > best_score:
                best_score = score
                best_hub = p

        if not best_hub:
            continue

        hub_id = best_hub.get('id')
        hub_title = best_hub.get('title', {}).get('rendered', '') if isinstance(best_hub.get('title'), dict) else str(best_hub.get('title', ''))
        hub_slug = best_hub.get('slug', '')

        # Spokes = all other posts in the cluster
        spokes = [p for p in cposts if p.get('id') != hub_id]
        spoke_slugs = set(p.get('slug', '') for p in spokes)
        linked_slugs = hub_outgoing.get(hub_id, set()) & spoke_slugs
        missing = spoke_slugs - linked_slugs

        hub_audit.append({
            'hub_id': hub_id,
            'hub_title': hub_title,
            'hub_slug': hub_slug,
            'cluster': cluster_name,
            'total_spokes': len(spokes),
            'linked_spokes': len(linked_slugs),
            'missing_slugs': list(missing),
            'missing_links': ", ".join(list(missing)[:10])
        })

    return hub_audit


def generate_hub_spoke_links(hub_audit, slug_map, link_matrix, existing_insertions):
    """Generate link insertions for hubs missing spoke links."""
    insertions = []
    template_idx = 40

    # Account for planned insertions
    planned = defaultdict(set)
    for ins in existing_insertions:
        planned[ins['source_id']].add(ins['target_slug'])

    for hub in hub_audit:
        hub_id = hub['hub_id']
        hub_title = hub['hub_title']
        hub_slug = hub['hub_slug']
        cluster = hub['cluster']

        missing = [s for s in hub['missing_slugs'] if s not in planned.get(hub_id, set())]
        # Add up to 5 missing spoke links per hub
        for tslug in missing[:5]:
            if tslug not in slug_map:
                continue
            tp = slug_map[tslug]
            tid = tp.get('id')
            ttitle = tp.get('title', {}).get('rendered', '') if isinstance(tp.get('title'), dict) else str(tp.get('title', ''))

            anchor = re.sub(r'<[^>]+>', '', ttitle).replace('&#8211;', '–').replace('&#8217;', "'").replace('&amp;', '&')
            if len(anchor) > 80:
                anchor = anchor[:77] + "..."

            topic = f"{cluster.lower()} guides"
            description = f"a comprehensive look at this important {cluster.lower()} topic"
            paragraph = build_link_paragraph(template_idx, topic, tslug, anchor, description)
            template_idx += 1

            insertions.append({
                'source_id': hub_id,
                'source_title': hub_title,
                'source_slug': hub_slug,
                'target_id': tid,
                'target_title': ttitle,
                'target_slug': tslug,
                'corridor': f"Hub-Spoke ({cluster})",
                'anchor_text': anchor,
                'paragraph': paragraph
            })
            planned[hub_id].add(tslug)

    return insertions


# ═══════════════════════════════════════════════════════════════════════
# STEP 5: GLOSSARY CROSS-LINKING
# ═══════════════════════════════════════════════════════════════════════
def generate_glossary_links(posts, cluster_posts, link_matrix, slug_map, existing_insertions):
    """Ensure glossary pages link to their hub and related posts."""
    insertions = []
    template_idx = 60

    # Find glossary posts
    glossary_posts = []
    for p in posts:
        slug = p.get('slug', '')
        title = p.get('title', {}).get('rendered', '') if isinstance(p.get('title'), dict) else str(p.get('title', ''))
        if 'glossary' in slug.lower() or 'glossary' in title.lower():
            glossary_posts.append(p)

    # Build existing links
    existing_links = defaultdict(set)
    for entry in link_matrix:
        source_id = entry['source_id']
        for s, p in slug_map.items():
            if p.get('id') == entry['target_id']:
                existing_links[source_id].add(s)
                break

    for ins in existing_insertions:
        existing_links[ins['source_id']].add(ins['target_slug'])

    for gp in glossary_posts:
        gid = gp.get('id')
        gtitle = gp.get('title', {}).get('rendered', '') if isinstance(gp.get('title'), dict) else str(gp.get('title', ''))
        gslug = gp.get('slug', '')

        # Determine which cluster the glossary relates to
        gcluster = detect_cluster(gslug, gtitle)

        # Find same-cluster educational posts to link to
        same_cluster = [p for p in cluster_posts.get(gcluster, []) if p.get('id') != gid]
        added = 0
        for tp in same_cluster[:5]:
            tslug = tp.get('slug', '')
            if tslug in existing_links.get(gid, set()):
                continue
            tid = tp.get('id')
            ttitle = tp.get('title', {}).get('rendered', '') if isinstance(tp.get('title'), dict) else str(tp.get('title', ''))

            anchor = re.sub(r'<[^>]+>', '', ttitle).replace('&#8211;', '–').replace('&#8217;', "'").replace('&amp;', '&')
            if len(anchor) > 80:
                anchor = anchor[:77] + "..."

            topic = f"{gcluster.lower()} terminology and care"
            description = f"practical application of these {gcluster.lower()} concepts"
            paragraph = build_link_paragraph(template_idx, topic, tslug, anchor, description)
            template_idx += 1

            insertions.append({
                'source_id': gid,
                'source_title': gtitle,
                'source_slug': gslug,
                'target_id': tid,
                'target_title': ttitle,
                'target_slug': tslug,
                'corridor': f"Glossary ({gcluster})",
                'anchor_text': anchor,
                'paragraph': paragraph
            })
            existing_links[gid].add(tslug)
            added += 1
            if added >= 4:
                break

        # Cross-cluster link (1 per glossary)
        other_clusters = [c for c in cluster_posts.keys() if c != gcluster and c != "Other"]
        if other_clusters:
            cross_cluster = other_clusters[template_idx % len(other_clusters)]
            cross_posts = cluster_posts.get(cross_cluster, [])
            for tp in cross_posts[:3]:
                tslug = tp.get('slug', '')
                if tslug in existing_links.get(gid, set()):
                    continue
                tid = tp.get('id')
                ttitle = tp.get('title', {}).get('rendered', '') if isinstance(tp.get('title'), dict) else str(tp.get('title', ''))

                anchor = re.sub(r'<[^>]+>', '', ttitle).replace('&#8211;', '–').replace('&#8217;', "'").replace('&amp;', '&')
                if len(anchor) > 80:
                    anchor = anchor[:77] + "..."

                topic = "related pet care topics"
                description = f"a complementary perspective from our {cross_cluster.lower()} guides"
                paragraph = build_link_paragraph(template_idx, topic, tslug, anchor, description)
                template_idx += 1

                insertions.append({
                    'source_id': gid,
                    'source_title': gtitle,
                    'source_slug': gslug,
                    'target_id': tid,
                    'target_title': ttitle,
                    'target_slug': tslug,
                    'corridor': f"Glossary cross-cluster ({gcluster} -> {cross_cluster})",
                    'anchor_text': anchor,
                    'paragraph': paragraph
                })
                existing_links[gid].add(tslug)
                break

    return insertions


# ═══════════════════════════════════════════════════════════════════════
# APPLY INSERTIONS - Batch update posts via WP API
# ═══════════════════════════════════════════════════════════════════════
def apply_insertions(all_insertions, slug_map):
    """Group insertions by source post and apply them in batches."""
    # Group by source_id
    by_source = defaultdict(list)
    for ins in all_insertions:
        by_source[ins['source_id']].append(ins)

    results = []
    batch_count = 0
    total = len(by_source)

    for idx, (sid, ins_list) in enumerate(by_source.items()):
        print(f"\n  [{idx+1}/{total}] Updating post {sid} ({ins_list[0]['source_title'][:50]}...)  +{len(ins_list)} links")

        # Fetch current content
        post_data = api_get(f"posts/{sid}", {"_fields": "id,content"})
        if not post_data:
            for ins in ins_list:
                results.append({**ins, 'status': 'FAILED - could not fetch'})
            continue

        content = post_data.get('content', {}).get('rendered', '') if isinstance(post_data.get('content'), dict) else str(post_data.get('content', ''))

        # Double check: skip if target slug already in content
        paragraphs_to_insert = []
        for ins in ins_list:
            tslug = ins['target_slug']
            if f'pethubonline.com/{tslug}/' in content or f'pethubonline.com/{tslug}"' in content:
                print(f"    SKIP: {tslug} already linked in this post")
                results.append({**ins, 'status': 'SKIPPED - already linked'})
                continue
            paragraphs_to_insert.append(ins)

        if not paragraphs_to_insert:
            continue

        # Build combined insertion block
        combined_paragraphs = "\n\n".join(ins['paragraph'] for ins in paragraphs_to_insert)

        # Insert before Sources section or at end
        insert_pos = find_sources_section(content)
        if insert_pos is not None:
            new_content = content[:insert_pos] + combined_paragraphs + "\n\n" + content[insert_pos:]
        else:
            new_content = content + "\n\n" + combined_paragraphs

        # Update via API
        update_result = api_post(f"posts/{sid}", {"content": new_content})
        time.sleep(DELAY)

        if update_result and update_result.get('id'):
            for ins in paragraphs_to_insert:
                results.append({**ins, 'status': 'INSERTED'})
                print(f"    OK: -> {ins['target_slug']} ({ins['corridor']})")
        else:
            error_msg = "FAILED"
            if update_result and isinstance(update_result, dict):
                error_msg = f"FAILED - {update_result.get('message', 'unknown error')}"
            for ins in paragraphs_to_insert:
                results.append({**ins, 'status': error_msg})
                print(f"    FAIL: -> {ins['target_slug']}")

        batch_count += 1
        if batch_count % 10 == 0:
            print(f"\n  --- Batch checkpoint: {batch_count} posts updated ---\n")

    return results


# ═══════════════════════════════════════════════════════════════════════
# CSV OUTPUT
# ═══════════════════════════════════════════════════════════════════════
def save_link_audit_csv(link_matrix, filepath):
    """Save the full link audit matrix to CSV."""
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'source_id', 'source_title', 'source_cluster',
            'target_id', 'target_title', 'target_cluster',
            'anchor_text', 'is_cross_cluster'
        ])
        writer.writeheader()
        for entry in link_matrix:
            writer.writerow(entry)
    print(f"  Saved link audit: {filepath} ({len(link_matrix)} rows)")


def save_reinforcement_log_csv(results, filepath):
    """Save the corridor reinforcement log to CSV."""
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'source_id', 'source_title', 'target_id', 'target_title',
            'corridor', 'anchor_text', 'status'
        ])
        writer.writeheader()
        for r in results:
            writer.writerow({
                'source_id': r.get('source_id'),
                'source_title': r.get('source_title'),
                'target_id': r.get('target_id'),
                'target_title': r.get('target_title'),
                'corridor': r.get('corridor'),
                'anchor_text': r.get('anchor_text'),
                'status': r.get('status')
            })
    print(f"  Saved reinforcement log: {filepath} ({len(results)} rows)")


def save_hub_spoke_csv(hub_audit, filepath):
    """Save the hub-spoke audit to CSV."""
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'hub_id', 'hub_title', 'cluster', 'total_spokes',
            'linked_spokes', 'missing_links'
        ])
        writer.writeheader()
        for h in hub_audit:
            writer.writerow({
                'hub_id': h['hub_id'],
                'hub_title': h['hub_title'],
                'cluster': h['cluster'],
                'total_spokes': h['total_spokes'],
                'linked_spokes': h['linked_spokes'],
                'missing_links': h['missing_links']
            })
    print(f"  Saved hub-spoke audit: {filepath} ({len(hub_audit)} rows)")


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════
def main():
    print("=" * 70)
    print("PetHub Online - Semantic Corridor Reinforcement")
    print("Phase 10AG: Internal Link Architecture Audit & Strengthening")
    print("=" * 70)

    # ── Step 1: Fetch all posts ──
    print("\n[STEP 1] Fetching all published posts...")
    posts = fetch_all_posts()
    print(f"  Total posts fetched: {len(posts)}")

    if not posts:
        print("ERROR: No posts fetched. Aborting.")
        return

    # ── Step 1b: Build link matrix ──
    print("\n[STEP 1b] Building internal link matrix...")
    link_matrix, outgoing, incoming, slug_map, id_map = build_link_matrix(posts)
    print(f"  Total internal links found: {len(link_matrix)}")
    print(f"  Unique source posts with outgoing links: {len(set(e['source_id'] for e in link_matrix))}")
    print(f"  Cross-cluster links: {sum(1 for e in link_matrix if e['is_cross_cluster'])}")

    # ── Step 2: Identify weak corridors ──
    print("\n[STEP 2] Identifying weak corridors...")
    weak_corridors, low_outgoing, orphans, cluster_posts = identify_weak_corridors(
        posts, link_matrix, outgoing, incoming, slug_map
    )

    print(f"  Cluster distribution:")
    for cluster, cposts in sorted(cluster_posts.items(), key=lambda x: -len(x[1])):
        print(f"    {cluster}: {len(cposts)} posts")

    print(f"\n  Weak cross-cluster corridors (< 3 links): {len(weak_corridors)}")
    for c1, c2, count in sorted(weak_corridors, key=lambda x: x[2])[:15]:
        print(f"    {c1} <-> {c2}: {count} links")

    print(f"\n  Posts with < 3 outgoing links: {len(low_outgoing)}")
    print(f"  Orphan posts (0 incoming links): {len(orphans)}")

    # ── Step 3: Generate corridor links ──
    print("\n[STEP 3] Generating contextual corridor links...")
    corridor_insertions = generate_corridor_links(posts, cluster_posts, link_matrix, outgoing, slug_map)
    print(f"  Corridor links planned: {len(corridor_insertions)}")

    # Low-outgoing reinforcement
    print("\n[STEP 3b] Generating links for low-outgoing posts...")
    low_outgoing_insertions = generate_low_outgoing_links(
        posts, cluster_posts, outgoing, slug_map, link_matrix, corridor_insertions
    )
    print(f"  Low-outgoing links planned: {len(low_outgoing_insertions)}")

    # ── Step 4: Hub-spoke audit ──
    print("\n[STEP 4] Auditing hub-spoke architecture...")
    hub_audit = audit_hub_spokes(posts, cluster_posts, link_matrix, slug_map)
    for h in hub_audit:
        if h['total_spokes'] > 0:
            pct = (h['linked_spokes'] / h['total_spokes']) * 100
            print(f"  {h['cluster']}: {h['hub_title'][:50]} - {h['linked_spokes']}/{h['total_spokes']} spokes linked ({pct:.0f}%)")

    hub_spoke_insertions = generate_hub_spoke_links(hub_audit, slug_map, link_matrix, corridor_insertions + low_outgoing_insertions)
    print(f"  Hub-spoke links planned: {len(hub_spoke_insertions)}")

    # ── Step 5: Glossary cross-linking ──
    print("\n[STEP 5] Generating glossary cross-links...")
    glossary_insertions = generate_glossary_links(
        posts, cluster_posts, link_matrix, slug_map,
        corridor_insertions + low_outgoing_insertions + hub_spoke_insertions
    )
    print(f"  Glossary links planned: {len(glossary_insertions)}")

    # ── Combine and cap at ~45 total insertions ──
    all_insertions = corridor_insertions + low_outgoing_insertions + hub_spoke_insertions + glossary_insertions
    print(f"\n  TOTAL links planned: {len(all_insertions)}")

    # Cap if needed (target ~40, allow up to 50)
    if len(all_insertions) > 50:
        print(f"  Capping at 50 insertions (was {len(all_insertions)})")
        all_insertions = all_insertions[:50]

    # ── Save pre-insertion audit CSVs ──
    print("\n[OUTPUT] Saving audit CSVs...")
    save_link_audit_csv(link_matrix, os.path.join(OUT_DIR, "semantic_corridor_audit.csv"))
    save_hub_spoke_csv(hub_audit, os.path.join(OUT_DIR, "hub_spoke_audit.csv"))

    # ── Apply insertions ──
    print(f"\n[APPLYING] Inserting {len(all_insertions)} contextual links...")
    results = apply_insertions(all_insertions, slug_map)

    # ── Save reinforcement log ──
    save_reinforcement_log_csv(results, os.path.join(OUT_DIR, "corridor_reinforcement_log.csv"))

    # ── Final Summary ──
    inserted = sum(1 for r in results if r.get('status') == 'INSERTED')
    skipped = sum(1 for r in results if 'SKIPPED' in r.get('status', ''))
    failed = sum(1 for r in results if 'FAILED' in r.get('status', ''))

    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"  Total posts analyzed: {len(posts)}")
    print(f"  Existing internal links: {len(link_matrix)}")
    print(f"  Cross-cluster links (existing): {sum(1 for e in link_matrix if e['is_cross_cluster'])}")
    print(f"  Links inserted: {inserted}")
    print(f"  Links skipped (already present): {skipped}")
    print(f"  Links failed: {failed}")
    print(f"\n  Output files:")
    print(f"    {OUT_DIR}/semantic_corridor_audit.csv")
    print(f"    {OUT_DIR}/corridor_reinforcement_log.csv")
    print(f"    {OUT_DIR}/hub_spoke_audit.csv")
    print("=" * 70)


if __name__ == "__main__":
    main()
