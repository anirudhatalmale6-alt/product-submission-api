#!/usr/bin/env python3
"""
PetHub Online: Phase 10AZ (Semantic Corridor Analysis),
Phase 10BA (Cluster Dominance Roadmaps), Phase 10BB (AI Citation Readiness Scoring)

READ-ONLY analysis — generates CSV recommendations, does NOT modify WordPress posts.
"""

import csv
import json
import subprocess
import os
import re
import time
import html
from collections import defaultdict
from urllib.parse import quote

# ── Config ──────────────────────────────────────────────────────────────────
WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"

DIR_AZ = "/var/lib/freelancer/projects/40416335/phase10az_data"
DIR_BA = "/var/lib/freelancer/projects/40416335/phase10ba_data"
DIR_BB = "/var/lib/freelancer/projects/40416335/phase10bb_data"
DIR_AQ = "/var/lib/freelancer/projects/40416335/phase10aq_data"
DIR_AO = "/var/lib/freelancer/projects/40416335/phase10ao_data"

os.makedirs(DIR_AZ, exist_ok=True)
os.makedirs(DIR_BA, exist_ok=True)
os.makedirs(DIR_BB, exist_ok=True)

# ── Helpers ─────────────────────────────────────────────────────────────────

def wp_api(endpoint, per_page=100):
    """Fetch all pages from WP REST API endpoint."""
    results = []
    page = 1
    while True:
        sep = "&" if "?" in endpoint else "?"
        url = f"{WP_BASE}/{endpoint}{sep}per_page={per_page}&page={page}"
        proc = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True, timeout=60
        )
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            print(f"  [WARN] JSON decode failed for page {page} of {endpoint}")
            break
        if isinstance(data, dict) and "code" in data:
            break
        if not data:
            break
        results.extend(data)
        if len(data) < per_page:
            break
        page += 1
        time.sleep(0.3)
    return results


def strip_html(text):
    """Remove HTML tags and decode entities."""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def load_csv(path):
    """Load a CSV file into a list of dicts."""
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def write_csv(path, fieldnames, rows):
    """Write a list of dicts to CSV."""
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  -> Wrote {len(rows)} rows to {path}")


# ── Load prior data ────────────────────────────────────────────────────────

print("Loading prior analytics data...")
all_post_scores = load_csv(f"{DIR_AQ}/all_post_scores.csv")
cluster_dominance = load_csv(f"{DIR_AQ}/cluster_dominance.csv")
missing_spokes = load_csv(f"{DIR_AO}/missing_spokes.csv")
replication_plans = load_csv(f"{DIR_AO}/replication_plans.csv")

# Index posts by cluster
posts_by_cluster = defaultdict(list)
posts_by_id = {}
for p in all_post_scores:
    posts_by_cluster[p['cluster']].append(p)
    posts_by_id[p['id']] = p

print(f"  Loaded {len(all_post_scores)} posts across {len(posts_by_cluster)} clusters")

# ── Fetch all published posts with content ──────────────────────────────────

print("\nFetching all published posts from WordPress API...")
raw_posts = wp_api("posts?status=publish&_fields=id,title,content,categories,link")
print(f"  Fetched {len(raw_posts)} posts")

# Also fetch categories to map IDs to names
print("Fetching categories...")
categories_raw = wp_api("categories?_fields=id,name,slug")
cat_id_to_name = {}
for c in categories_raw:
    cat_id_to_name[c['id']] = c.get('name', c.get('slug', ''))
print(f"  Fetched {len(cat_id_to_name)} categories")

# Build content index
posts_content = {}
for rp in raw_posts:
    pid = str(rp['id'])
    title = rp.get('title', {}).get('rendered', '')
    content_html = rp.get('content', {}).get('rendered', '')
    content_text = strip_html(content_html)
    link = rp.get('link', '')
    cats = rp.get('categories', [])
    cat_names = [cat_id_to_name.get(cid, '') for cid in cats]

    # Find cluster from our scores data
    cluster = ''
    if pid in posts_by_id:
        cluster = posts_by_id[pid]['cluster']
    else:
        # Try to infer from category names
        for cn in cat_names:
            cn_lower = cn.lower()
            for cl in posts_by_cluster.keys():
                if cl.lower() in cn_lower or cn_lower in cl.lower():
                    cluster = cl
                    break
            if cluster:
                break

    posts_content[pid] = {
        'id': pid,
        'title': strip_html(title),
        'content_html': content_html,
        'content_text': content_text,
        'link': link,
        'cluster': cluster,
        'categories': cat_names,
        'word_count': len(content_text.split())
    }

print(f"  Indexed content for {len(posts_content)} posts")


# ══════════════════════════════════════════════════════════════════════════════
# TASK 1: SEMANTIC CORRIDOR ANALYSIS (Phase 10AZ)
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("TASK 1: SEMANTIC CORRIDOR ANALYSIS (Phase 10AZ)")
print("="*80)

# Define corridor pairs
CORRIDORS = [
    ("Dog Food", "Dog Health"),
    ("Dog Toys", "Puppy Care"),
    ("Dog Beds", "Dog Health"),
    ("Cat Toys", "Cat Supplies"),
    ("Dog Harnesses", "Dog Training"),
    ("Educational", "Dog Food"),
    ("Educational", "Dog Health"),
    ("Educational", "Dog Toys"),
    ("Educational", "Cat Toys"),
    ("Educational", "Dog Beds"),
    ("Educational", "Dog Training"),
    ("Educational", "Dog Harnesses"),
    ("Educational", "Cat Supplies"),
    ("Educational", "Puppy Care"),
    ("Educational", "Dog Grooming"),
    ("Educational", "Indoor Cats"),
]

# Glossary/terminology keywords by cluster
CLUSTER_GLOSSARY_TERMS = {
    "Dog Food": ["nutrition", "kibble", "protein", "grain-free", "hypoallergenic", "raw food", "wet food", "dry food", "feeding", "ingredients", "calories", "portions", "diet", "supplements", "digestive", "appetite", "food allergy", "meal"],
    "Dog Health": ["veterinary", "vaccination", "parasite", "flea", "tick", "joint", "dental", "orthopaedic", "neutering", "spaying", "arthritis", "hip dysplasia", "allergy", "inflammation", "medication", "symptoms", "diagnosis", "prevention"],
    "Dog Toys": ["enrichment", "puzzle", "fetch", "tug", "chew", "interactive", "squeaky", "rope toy", "plush", "rubber", "durability", "indestructible", "mental stimulation", "boredom", "play style", "rotation", "safety", "overstimulation"],
    "Puppy Care": ["teething", "socialisation", "crate training", "house training", "vaccination schedule", "puppy-proofing", "development stages", "first year", "puppy food", "growth", "potty training", "puppy bed", "first toys", "biting"],
    "Dog Beds": ["orthopaedic", "memory foam", "cooling", "elevated", "crate bed", "waterproof", "washable", "bolster", "donut bed", "sizing", "placement", "heated", "calming bed", "nesting", "bed materials"],
    "Cat Toys": ["wand toy", "laser", "feather", "catnip", "scratching post", "cat tree", "puzzle feeder", "interactive", "mouse toy", "crinkle", "bell toy", "enrichment", "indoor play", "hunting instinct", "prey drive"],
    "Cat Supplies": ["litter", "litter tray", "cat bed", "cat collar", "cat harness", "food bowl", "water fountain", "carrier", "grooming", "scratching", "self-cleaning", "cat flap", "cat tag"],
    "Dog Harnesses": ["no-pull", "front-clip", "back-clip", "fitting", "measuring", "collar vs harness", "lead", "walking", "training harness", "padded", "reflective", "step-in", "overhead"],
    "Dog Training": ["positive reinforcement", "recall", "lead training", "reactivity", "body language", "behaviour", "obedience", "socialisation", "clicker", "treats", "crate training", "separation anxiety", "command"],
    "Educational": ["glossary", "terminology", "guide", "explained", "basics", "understanding", "key terms", "definitions", "overview", "comparison"],
    "Dog Grooming": ["brushing", "bathing", "shampoo", "nail trimming", "ear cleaning", "coat type", "shedding", "deshedding", "grooming schedule", "professional grooming", "hypoallergenic", "clippers"],
    "Indoor Cats": ["indoor cat", "house cat", "enrichment", "exercise", "window perch", "cat safety", "household hazards", "indoor play", "mental stimulation", "boredom prevention"],
    "Uncategorized": [],
}

# FAQ topic keywords by cluster
CLUSTER_FAQ_TOPICS = {
    "Dog Food": ["how much to feed", "best food brand", "grain free safe", "wet vs dry", "raw diet", "food transition", "puppy food switch", "senior dog food", "food allergies", "treats vs food"],
    "Dog Health": ["when to see vet", "vaccination schedule", "flea prevention", "dental care", "joint supplements", "common symptoms", "pet insurance", "neutering age", "first aid", "medication side effects"],
    "Dog Toys": ["safest toys", "how many toys", "toy rotation", "clean toys", "indestructible toys", "best for chewers", "puzzle difficulty", "toy size", "when to replace", "fetch alternatives"],
    "Puppy Care": ["first night home", "potty training", "teething relief", "socialisation window", "puppy vaccinations", "feeding schedule", "sleep training", "biting", "crate training", "first vet visit"],
    "Dog Beds": ["best bed type", "bed size guide", "washing frequency", "orthopaedic benefits", "crate bed fit", "bed placement", "memory foam vs standard", "cooling beds", "puppy bed", "senior bed"],
    "Cat Toys": ["best toys for indoor cats", "catnip safe", "laser pointer safe", "how often play", "DIY cat toys", "toy rotation", "kitten toys", "senior cat toys", "interactive toys", "scratching alternatives"],
    "Cat Supplies": ["best litter type", "litter box placement", "cat bed vs human bed", "cat collar safety", "harness training", "water fountain benefits", "carrier selection", "grooming frequency"],
    "Dog Harnesses": ["harness vs collar", "no-pull harness", "measuring for harness", "puppy harness", "front vs back clip", "harness training", "walking equipment", "lead length"],
    "Dog Training": ["positive reinforcement", "recall tips", "lead pulling", "puppy training age", "separation anxiety", "reactive dog", "training treats", "clicker training", "obedience basics"],
    "Educational": ["pet terminology", "beginner guide", "key terms", "understanding labels", "pet care basics", "glossary use"],
    "Dog Grooming": ["brushing frequency", "bathing schedule", "nail trimming", "ear cleaning", "best shampoo", "coat types", "professional vs home", "shedding control"],
    "Indoor Cats": ["keeping cats happy indoors", "exercise ideas", "safety hazards", "enrichment tips", "window perch", "cat-proofing home"],
    "Uncategorized": [],
}


def find_cross_links(source_cluster, target_cluster):
    """Find existing hyperlinks from source cluster posts to target cluster posts."""
    source_posts = [(pid, pc) for pid, pc in posts_content.items() if pc['cluster'] == source_cluster]
    target_posts = [(pid, pc) for pid, pc in posts_content.items() if pc['cluster'] == target_cluster]

    links_found = []
    for spid, spc in source_posts:
        html_content = spc['content_html']
        for tpid, tpc in target_posts:
            # Check if source links to target URL
            target_url = tpc.get('link', '')
            target_slug = target_url.split('/')[-2] if target_url.endswith('/') else target_url.split('/')[-1]
            if target_slug and target_slug in html_content:
                links_found.append({
                    'source_id': spid,
                    'source_title': spc['title'],
                    'target_id': tpid,
                    'target_title': tpc['title'],
                })
    return links_found


def compute_glossary_overlap(cluster_a, cluster_b):
    """Compute glossary/terminology overlap between two clusters."""
    terms_a = set(t.lower() for t in CLUSTER_GLOSSARY_TERMS.get(cluster_a, []))
    terms_b = set(t.lower() for t in CLUSTER_GLOSSARY_TERMS.get(cluster_b, []))

    if not terms_a or not terms_b:
        return 0.0, set()

    overlap = terms_a & terms_b
    # Also check for partial overlaps (one term contains another)
    partial_overlap = set()
    for ta in terms_a:
        for tb in terms_b:
            if ta in tb or tb in ta:
                partial_overlap.add(f"{ta}/{tb}")

    # Check actual content overlap: terms from cluster A found in cluster B's content
    content_overlap_count = 0
    posts_b = [pc for pc in posts_content.values() if pc['cluster'] == cluster_b]
    content_b_combined = " ".join(pc['content_text'].lower() for pc in posts_b)

    for term in terms_a:
        if term.lower() in content_b_combined:
            content_overlap_count += 1

    posts_a = [pc for pc in posts_content.values() if pc['cluster'] == cluster_a]
    content_a_combined = " ".join(pc['content_text'].lower() for pc in posts_a)

    for term in terms_b:
        if term.lower() in content_a_combined:
            content_overlap_count += 1

    total_terms = len(terms_a) + len(terms_b)
    if total_terms == 0:
        return 0.0, set()

    # Weighted: direct overlap counts double, content mentions count single
    score = min(100, ((len(overlap) * 3 + len(partial_overlap) * 2 + content_overlap_count) / total_terms) * 100)
    return round(score, 1), overlap | partial_overlap


def compute_faq_overlap(cluster_a, cluster_b):
    """Compute FAQ topic overlap between two clusters."""
    topics_a = set(t.lower() for t in CLUSTER_FAQ_TOPICS.get(cluster_a, []))
    topics_b = set(t.lower() for t in CLUSTER_FAQ_TOPICS.get(cluster_b, []))

    if not topics_a or not topics_b:
        return 0.0

    # Direct overlap
    overlap = topics_a & topics_b

    # Semantic proximity: topics that share keywords
    shared_keyword_count = 0
    for ta in topics_a:
        ta_words = set(ta.split())
        for tb in topics_b:
            tb_words = set(tb.split())
            if len(ta_words & tb_words) >= 1:
                shared_keyword_count += 1

    total_topics = len(topics_a) + len(topics_b)
    score = min(100, ((len(overlap) * 4 + shared_keyword_count) / total_topics) * 100)
    return round(score, 1)


def identify_missing_links(source_cluster, target_cluster, existing_links):
    """Identify high-value missing link opportunities between clusters."""
    existing_pairs = set()
    for link in existing_links:
        existing_pairs.add((link['source_id'], link['target_id']))

    source_posts = [p for p in all_post_scores if p['cluster'] == source_cluster]
    target_posts = [p for p in all_post_scores if p['cluster'] == target_cluster]

    # Sort by dominance score descending (best pages first)
    source_posts.sort(key=lambda x: float(x.get('topical_dominance_score', 0)), reverse=True)
    target_posts.sort(key=lambda x: float(x.get('topical_dominance_score', 0)), reverse=True)

    missing = []
    for sp in source_posts[:15]:  # Top 15 source pages
        for tp in target_posts[:15]:  # Top 15 target pages
            if (sp['id'], tp['id']) not in existing_pairs:
                # Score relevance based on content overlap potential
                s_text = posts_content.get(sp['id'], {}).get('content_text', '').lower()
                t_title_words = strip_html(tp['title']).lower().split()

                relevance = sum(1 for w in t_title_words if len(w) > 3 and w in s_text)
                combined_score = float(sp.get('topical_dominance_score', 0)) + float(tp.get('topical_dominance_score', 0))

                missing.append({
                    'source_id': sp['id'],
                    'source_title': sp['title'],
                    'target_id': tp['id'],
                    'target_title': tp['title'],
                    'relevance': relevance,
                    'combined_score': combined_score,
                })

    # Sort by relevance then combined score
    missing.sort(key=lambda x: (x['relevance'], x['combined_score']), reverse=True)
    return missing[:20]


def generate_anchor_text(source_title, target_title, target_cluster):
    """Generate a natural anchor text suggestion."""
    t_lower = target_title.lower()

    # Try to extract the core topic
    # Remove common prefixes
    for prefix in ["best ", "how to ", "a guide to ", "understanding ", "the "]:
        if t_lower.startswith(prefix):
            t_lower = t_lower[len(prefix):]

    # Remove year references
    t_lower = re.sub(r'\(?\d{4}\)?', '', t_lower)
    # Remove UK references for cleaner anchor
    t_lower = re.sub(r'\s*uk\s*', ' ', t_lower, flags=re.IGNORECASE)
    # Clean up separators
    t_lower = re.sub(r'\s*[–—-]\s*', ' ', t_lower)
    t_lower = re.sub(r'\s+', ' ', t_lower).strip()

    # Truncate if too long
    words = t_lower.split()
    if len(words) > 6:
        t_lower = " ".join(words[:6])

    return t_lower


# Run corridor analysis
print("\nAnalyzing semantic corridors...")
corridor_results = []
all_link_plans = []

for source_cluster, target_cluster in CORRIDORS:
    corridor_name = f"{source_cluster} <-> {target_cluster}"
    print(f"  Analyzing: {corridor_name}")

    # Count existing cross-links (both directions)
    links_s_to_t = find_cross_links(source_cluster, target_cluster)
    links_t_to_s = find_cross_links(target_cluster, source_cluster)
    all_existing = links_s_to_t + links_t_to_s
    existing_count = len(all_existing)

    # Glossary overlap
    glossary_score, glossary_terms = compute_glossary_overlap(source_cluster, target_cluster)

    # FAQ overlap
    faq_score = compute_faq_overlap(source_cluster, target_cluster)

    # Missing links
    missing_s_to_t = identify_missing_links(source_cluster, target_cluster, links_s_to_t)
    missing_t_to_s = identify_missing_links(target_cluster, source_cluster, links_t_to_s)
    all_missing = missing_s_to_t + missing_t_to_s

    # Calculate corridor strength (0-100)
    # Components: link density (40%), glossary overlap (30%), FAQ overlap (30%)
    source_count = len(posts_by_cluster.get(source_cluster, []))
    target_count = len(posts_by_cluster.get(target_cluster, []))
    max_possible_links = max(1, source_count * target_count)
    link_density = min(100, (existing_count / max(1, min(source_count, target_count))) * 100)

    corridor_strength = round(
        link_density * 0.40 +
        glossary_score * 0.30 +
        faq_score * 0.30,
        1
    )

    # Top missing links as string
    top_missing_str = "; ".join(
        f"{m['source_title'][:40]} -> {m['target_title'][:40]}"
        for m in all_missing[:5]
    )

    corridor_results.append({
        'corridor': corridor_name,
        'source_cluster': source_cluster,
        'target_cluster': target_cluster,
        'existing_links': existing_count,
        'glossary_overlap': glossary_score,
        'faq_overlap': faq_score,
        'corridor_strength': corridor_strength,
        'missing_link_count': len(all_missing),
        'top_missing_links': top_missing_str,
    })

    # Build link plan entries
    priority_rank = 0
    for m in all_missing[:10]:
        priority_rank += 1
        anchor = generate_anchor_text(m['source_title'], m['target_title'], target_cluster)
        all_link_plans.append({
            'source_id': m['source_id'],
            'source_title': m['source_title'],
            'target_id': m['target_id'],
            'target_title': m['target_title'],
            'suggested_anchor_text': anchor,
            'corridor': corridor_name,
            'priority': priority_rank,
        })

# Write corridor analysis CSV
write_csv(
    f"{DIR_AZ}/corridor_analysis.csv",
    ['corridor', 'source_cluster', 'target_cluster', 'existing_links', 'glossary_overlap',
     'faq_overlap', 'corridor_strength', 'missing_link_count', 'top_missing_links'],
    corridor_results
)

# Write corridor link plan CSV
write_csv(
    f"{DIR_AZ}/corridor_link_plan.csv",
    ['source_id', 'source_title', 'target_id', 'target_title', 'suggested_anchor_text', 'corridor', 'priority'],
    all_link_plans
)


# ══════════════════════════════════════════════════════════════════════════════
# TASK 2: CLUSTER DOMINANCE ROADMAPS (Phase 10BA)
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("TASK 2: CLUSTER DOMINANCE ROADMAPS (Phase 10BA)")
print("="*80)

PRIORITY_CLUSTERS = ["Indoor Cats", "Puppy Care", "Dog Beds", "Dog Grooming", "Cat Supplies"]
TARGET_SCORE = 75

# Dimension names in cluster_dominance CSV
DIMENSIONS = {
    'avg_saturation': 'Content Saturation',
    'avg_authority': 'Authority Density',
    'avg_semantic': 'Semantic Coverage',
    'avg_glossary': 'Glossary Density',
    'avg_trust': 'Trust Intensity',
    'avg_citation': 'Citation Confidence',
    'avg_practical': 'Practical Usefulness',
    'avg_comparison': 'Comparison Usefulness',
    'avg_ai_readiness': 'AI Readiness',
    'avg_indexing': 'Indexing Momentum',
}

# Build cluster data index
cluster_data = {}
for cd in cluster_dominance:
    cluster_data[cd['cluster']] = cd

# Index replication plans by cluster
repl_by_cluster = defaultdict(list)
for rp in replication_plans:
    repl_by_cluster[rp['cluster']].append(rp)

# Index missing spokes by cluster
spokes_by_cluster = defaultdict(list)
for ms in missing_spokes:
    spokes_by_cluster[ms['cluster']].append(ms)

print("\nGenerating dominance roadmaps for 5 priority clusters...")
roadmap_rows = []

for cluster in PRIORITY_CLUSTERS:
    print(f"\n  Cluster: {cluster}")
    cd = cluster_data.get(cluster, {})
    current_score = float(cd.get('topical_dominance_score', 0))
    print(f"    Current score: {current_score}, Target: {TARGET_SCORE}")

    # Find weakest dimensions
    dim_scores = {}
    for dim_key, dim_name in DIMENSIONS.items():
        val = float(cd.get(dim_key, 0))
        dim_scores[dim_key] = (dim_name, val)

    # Sort by score ascending (weakest first)
    sorted_dims = sorted(dim_scores.items(), key=lambda x: x[1][1])

    # Get cluster posts sorted by score ascending (weakest posts first)
    cluster_posts = posts_by_cluster.get(cluster, [])
    cluster_posts_sorted = sorted(cluster_posts, key=lambda x: float(x.get('topical_dominance_score', 0)))

    # Get replication gaps
    cluster_repl = repl_by_cluster.get(cluster, [])
    cluster_repl_sorted = sorted(cluster_repl, key=lambda x: float(x.get('priority', 0)), reverse=True)

    # Get missing spokes
    cluster_spokes = spokes_by_cluster.get(cluster, [])

    # Generate roadmap actions
    action_priority = 0

    # ACTION SET 1: Address weakest dimensions
    for dim_key, (dim_name, dim_val) in sorted_dims[:4]:  # Top 4 weakest
        if dim_val >= 90:
            continue  # Already strong

        action_priority += 1
        gap = TARGET_SCORE - current_score
        # Estimate lift: improving weakest dimension has ~10% weight on overall
        estimated_lift = round(min(10, (90 - dim_val) * 0.1), 1)

        # Identify which posts need improvement on this dimension
        # Map dimension key to post score columns
        dim_to_post_col = {
            'avg_saturation': 'saturation',
            'avg_authority': 'authority_density',
            'avg_semantic': 'semantic_coverage',
            'avg_glossary': 'glossary_density',
            'avg_trust': 'trust_intensity',
            'avg_citation': 'citation_confidence',
            'avg_practical': 'practical_usefulness',
            'avg_comparison': 'comparison_usefulness',
            'avg_ai_readiness': 'ai_readiness',
            'avg_indexing': 'indexing_momentum',
        }

        post_col = dim_to_post_col.get(dim_key, '')
        weak_posts = []
        for p in cluster_posts:
            if post_col and float(p.get(post_col, 0)) < 70:
                weak_posts.append(p['id'])

        posts_str = "; ".join(weak_posts[:10])
        if len(weak_posts) > 10:
            posts_str += f" (+{len(weak_posts)-10} more)"

        # Determine action based on dimension
        if dim_key == 'avg_glossary':
            action = f"Add glossary/terminology sections to {len(weak_posts)} posts lacking definitions (cluster avg {dim_val})"
        elif dim_key == 'avg_practical':
            action = f"Add practical UK-specific guidance, measurement tables, cost breakdowns to {len(weak_posts)} posts (cluster avg {dim_val})"
        elif dim_key == 'avg_comparison':
            action = f"Add comparison tables and side-by-side analysis to {len(weak_posts)} posts (cluster avg {dim_val})"
        elif dim_key == 'avg_citation':
            action = f"Add extractable facts, statistics, clear answers to {len(weak_posts)} posts (cluster avg {dim_val})"
        elif dim_key == 'avg_ai_readiness':
            action = f"Add FAQ sections, At a Glance, Key Takeaways to {len(weak_posts)} posts (cluster avg {dim_val})"
        elif dim_key == 'avg_saturation':
            action = f"Expand thin content — increase word count and depth on {len(weak_posts)} posts below 2000 words (cluster avg {dim_val})"
        elif dim_key == 'avg_authority':
            action = f"Add How We Evaluated, Why We Reference, editorial methodology to {len(weak_posts)} posts (cluster avg {dim_val})"
        elif dim_key == 'avg_trust':
            action = f"Add trust signals: methodology notes, correction policies, expert references to {len(weak_posts)} posts (cluster avg {dim_val})"
        elif dim_key == 'avg_indexing':
            action = f"Improve indexing signals: add internal links, schema markup, breadcrumbs to {len(weak_posts)} posts (cluster avg {dim_val})"
        else:
            action = f"Improve {dim_name} across {len(weak_posts)} posts (cluster avg {dim_val})"

        roadmap_rows.append({
            'cluster': cluster,
            'current_score': current_score,
            'target_score': TARGET_SCORE,
            'weakest_dimension': dim_name,
            'dimension_score': dim_val,
            'action_required': action,
            'posts_affected': posts_str if posts_str else "All cluster posts",
            'priority': action_priority,
            'estimated_lift': estimated_lift,
        })

    # ACTION SET 2: Fix replication gaps (from replication_plans.csv)
    for rp in cluster_repl_sorted[:3]:
        action_priority += 1
        rp_priority = float(rp.get('priority', 0))
        estimated_lift = round(min(5, rp_priority * 2), 1)

        roadmap_rows.append({
            'cluster': cluster,
            'current_score': current_score,
            'target_score': TARGET_SCORE,
            'weakest_dimension': 'Replication Gap',
            'dimension_score': round(100 - rp_priority * 10, 1),
            'action_required': rp.get('recommended_action', rp.get('gap_description', '')),
            'posts_affected': f"{rp.get('posts_affected', 'N/A')} posts",
            'priority': action_priority,
            'estimated_lift': estimated_lift,
        })

    # ACTION SET 3: Publish missing spoke topics
    for spoke in cluster_spokes[:3]:
        action_priority += 1
        estimated_lift = round(min(4, float(spoke.get('priority', 0)) * 0.4), 1)

        roadmap_rows.append({
            'cluster': cluster,
            'current_score': current_score,
            'target_score': TARGET_SCORE,
            'weakest_dimension': 'Missing Spoke Topic',
            'dimension_score': 0,
            'action_required': f"Publish new spoke: {spoke['suggested_spoke_topic']} — {spoke['rationale']}",
            'posts_affected': "New post required",
            'priority': action_priority,
            'estimated_lift': estimated_lift,
        })

    # ACTION SET 4: Upgrade weakest individual posts
    for wp in cluster_posts_sorted[:3]:
        if float(wp.get('topical_dominance_score', 0)) < 60:
            action_priority += 1
            roadmap_rows.append({
                'cluster': cluster,
                'current_score': current_score,
                'target_score': TARGET_SCORE,
                'weakest_dimension': 'Weak Post Upgrade',
                'dimension_score': float(wp.get('topical_dominance_score', 0)),
                'action_required': f"Major upgrade needed: '{wp['title']}' (score {wp['topical_dominance_score']}) — expand content, add all standard sections, improve trust depth",
                'posts_affected': wp['id'],
                'priority': action_priority,
                'estimated_lift': round(min(3, (60 - float(wp.get('topical_dominance_score', 0))) * 0.05), 1),
            })

# Write roadmaps CSV
write_csv(
    f"{DIR_BA}/dominance_roadmaps.csv",
    ['cluster', 'current_score', 'target_score', 'weakest_dimension', 'dimension_score',
     'action_required', 'posts_affected', 'priority', 'estimated_lift'],
    roadmap_rows
)


# ══════════════════════════════════════════════════════════════════════════════
# TASK 3: AI CITATION READINESS SCORING (Phase 10BB)
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("TASK 3: AI CITATION READINESS SCORING (Phase 10BB)")
print("="*80)

def score_citation_confidence(content_text, content_html, word_count):
    """Score 0-100: Has extractable facts, clear answers, statistics."""
    score = 0
    text_lower = content_text.lower()

    # Has statistics/numbers
    numbers = re.findall(r'\d+\.?\d*\s*(?:%|percent|£|kg|mg|ml|grams|months|weeks|years|times|hours|minutes)', text_lower)
    score += min(25, len(numbers) * 3)

    # Has clear definitive statements ("is", "are", "should", "recommended")
    definitive = len(re.findall(r'\b(?:recommended|is best|you should|ideal for|suitable for|designed for|proven|evidence)\b', text_lower))
    score += min(20, definitive * 2)

    # Has lists (enumerated or bullet)
    lists = content_html.count('<li>') + content_html.count('<li ')
    score += min(20, lists * 1.5)

    # Has headings with clear topics
    headings = len(re.findall(r'<h[2-4][^>]*>', content_html))
    score += min(15, headings * 2)

    # Word count factor (longer = more citable)
    if word_count >= 2500:
        score += 20
    elif word_count >= 1500:
        score += 15
    elif word_count >= 800:
        score += 10
    else:
        score += 5

    return min(100, round(score))


def score_extractability(content_text, content_html, word_count):
    """Score 0-100: Has structured data — tables, lists, definitions."""
    score = 0
    text_lower = content_text.lower()

    # Tables
    tables = content_html.count('<table')
    score += min(30, tables * 15)

    # Lists
    lists = content_html.count('<ul') + content_html.count('<ol')
    score += min(25, lists * 5)

    # Definition-like structures
    definitions = len(re.findall(r'\b(?:means|defined as|refers to|is when|is a|are a)\b', text_lower))
    score += min(15, definitions * 3)

    # Bold/strong text (key points)
    bold = content_html.count('<strong') + content_html.count('<b>')
    score += min(15, bold * 1)

    # Structured headings
    h2_count = len(re.findall(r'<h2[^>]*>', content_html))
    h3_count = len(re.findall(r'<h3[^>]*>', content_html))
    score += min(15, (h2_count + h3_count) * 2)

    return min(100, round(score))


def score_practical_specificity(content_text, content_html, word_count):
    """Score 0-100: UK-specific, actionable, measurable guidance."""
    score = 0
    text_lower = content_text.lower()

    # UK-specific references
    uk_refs = len(re.findall(r'\b(?:uk|united kingdom|british|england|scotland|wales|nhs|rspca|bva|defra|kennel club|£)\b', text_lower))
    score += min(25, uk_refs * 3)

    # Actionable language
    actionable = len(re.findall(r'\b(?:step \d|how to|guide|follow|ensure|check|measure|apply|choose|avoid|consider|tip|recommendation)\b', text_lower))
    score += min(25, actionable * 2)

    # Measurable guidance (specific quantities)
    measurable = len(re.findall(r'\d+\s*(?:cm|mm|inches|kg|lbs|grams|ml|litres|times|days|weeks|months|minutes|hours|£)', text_lower))
    score += min(25, measurable * 3)

    # Product recommendations
    products = len(re.findall(r'\b(?:best|top|recommended|our pick|editor\'s choice|budget|premium|affordable)\b', text_lower))
    score += min(15, products * 2)

    # Pricing information
    if '£' in text_lower or 'price' in text_lower or 'cost' in text_lower:
        score += 10

    return min(100, round(score))


def score_trust_depth(content_text, content_html, word_count):
    """Score 0-100: Methodology, editorial, corrections visible."""
    score = 0
    text_lower = content_text.lower()

    # Methodology indicators
    methodology = len(re.findall(r'\b(?:how we evaluated|methodology|our process|research|tested|reviewed|assessed|criteria|editorial|standards)\b', text_lower))
    score += min(25, methodology * 5)

    # Trust signals
    trust = len(re.findall(r'\b(?:why we reference|correction|updated|last reviewed|fact.?check|verified|evidence.?based|peer|source|study|journal|published)\b', text_lower))
    score += min(25, trust * 4)

    # Date/update references
    dates = len(re.findall(r'\b(?:2024|2025|2026|last updated|reviewed on|published|updated)\b', text_lower))
    score += min(15, dates * 3)

    # Author/expert references
    author = len(re.findall(r'\b(?:expert|veterinarian|vet|specialist|qualified|certified|professional)\b', text_lower))
    score += min(20, author * 4)

    # Word count trust bonus
    if word_count >= 2000:
        score += 15
    elif word_count >= 1000:
        score += 10

    return min(100, round(score))


def score_comparison_usefulness(content_text, content_html, word_count):
    """Score 0-100: Has educational comparison tables."""
    score = 0
    text_lower = content_text.lower()

    # Comparison tables
    tables = content_html.count('<table')
    score += min(35, tables * 18)

    # Comparison language
    comparisons = len(re.findall(r'\b(?:vs|versus|compared|comparison|difference|better than|worse than|pros|cons|advantages|disadvantages|alternative)\b', text_lower))
    score += min(25, comparisons * 3)

    # Side-by-side indicators
    side_by_side = len(re.findall(r'\b(?:side by side|head to head|at a glance|quick comparison|feature comparison|which is)\b', text_lower))
    score += min(20, side_by_side * 5)

    # Rating or scoring
    ratings = len(re.findall(r'\b(?:rating|score|rank|star|out of \d|\/10|\/5)\b', text_lower))
    score += min(20, ratings * 4)

    return min(100, round(score))


def score_glossary_usefulness(content_text, content_html, word_count):
    """Score 0-100: Has definitions, key terms."""
    score = 0
    text_lower = content_text.lower()

    # Glossary section presence
    if 'glossary' in text_lower or 'key terms' in text_lower or 'terminology' in text_lower:
        score += 25

    # Definition patterns
    definitions = len(re.findall(r'\b(?:means|defined as|refers to|is a term|is when|also known as|abbreviated|stands for)\b', text_lower))
    score += min(30, definitions * 4)

    # Bold terms (likely definitions)
    bold_terms = re.findall(r'<strong[^>]*>([^<]+)</strong>', content_html)
    score += min(25, len(bold_terms) * 2)

    # Term-definition list structures (dt/dd)
    dl_items = content_html.count('<dt') + content_html.count('<dd')
    score += min(20, dl_items * 5)

    # Heading-based term definitions
    if re.search(r'<h[23][^>]*>[^<]*(?:glossary|terms|terminology|definitions)', content_html, re.IGNORECASE):
        score += 15

    return min(100, round(score))


def score_answer_usefulness(content_text, content_html, word_count):
    """Score 0-100: Has FAQ, quick answers, direct responses."""
    score = 0
    text_lower = content_text.lower()

    # FAQ section
    if 'faq' in text_lower or 'frequently asked' in text_lower or 'common questions' in text_lower:
        score += 25

    # Question patterns
    questions = len(re.findall(r'\?', content_text))
    score += min(25, questions * 2)

    # Direct answer patterns
    answers = len(re.findall(r'\b(?:the answer is|short answer|in summary|simply put|to summarise|the reason|this means|this is because)\b', text_lower))
    score += min(20, answers * 5)

    # Q&A heading patterns
    qa_headings = len(re.findall(r'<h[2-4][^>]*>[^<]*\?', content_html))
    score += min(20, qa_headings * 4)

    # List-based answers
    if content_html.count('<li>') >= 5:
        score += 10

    return min(100, round(score))


def score_summary_usefulness(content_text, content_html, word_count):
    """Score 0-100: Has At a Glance, Key Takeaways."""
    score = 0
    text_lower = content_text.lower()

    # At a Glance
    if 'at a glance' in text_lower or 'at-a-glance' in text_lower:
        score += 25

    # Key Takeaways
    if 'key takeaway' in text_lower or 'main takeaway' in text_lower:
        score += 25

    # Summary sections
    if 'summary' in text_lower or 'conclusion' in text_lower or 'final thoughts' in text_lower:
        score += 15

    # Quick reference
    if 'quick reference' in text_lower or 'cheat sheet' in text_lower or 'quick guide' in text_lower:
        score += 15

    # TL;DR or overview
    if 'tldr' in text_lower or 'tl;dr' in text_lower or 'overview' in text_lower:
        score += 10

    # Bullet point summaries near top (first 500 chars)
    first_500 = content_html[:2000].lower()
    if '<ul' in first_500 or '<ol' in first_500:
        score += 10

    return min(100, round(score))


print("\nScoring all posts on 8 AI citation readiness dimensions...")
ai_citation_rows = []

for pid, pc in posts_content.items():
    content_text = pc['content_text']
    content_html = pc['content_html']
    word_count = pc['word_count']
    cluster = pc['cluster']
    title = pc['title']

    # Skip if no meaningful content
    if word_count < 50:
        continue

    cit_conf = score_citation_confidence(content_text, content_html, word_count)
    extractability = score_extractability(content_text, content_html, word_count)
    practical_spec = score_practical_specificity(content_text, content_html, word_count)
    trust_depth = score_trust_depth(content_text, content_html, word_count)
    comparison_use = score_comparison_usefulness(content_text, content_html, word_count)
    glossary_use = score_glossary_usefulness(content_text, content_html, word_count)
    answer_use = score_answer_usefulness(content_text, content_html, word_count)
    summary_use = score_summary_usefulness(content_text, content_html, word_count)

    # Overall AI citation readiness (weighted average)
    overall = round(
        cit_conf * 0.20 +
        extractability * 0.15 +
        practical_spec * 0.15 +
        trust_depth * 0.10 +
        comparison_use * 0.10 +
        glossary_use * 0.10 +
        answer_use * 0.10 +
        summary_use * 0.10,
        1
    )

    ai_citation_rows.append({
        'id': pid,
        'title': title,
        'cluster': cluster if cluster else 'Unknown',
        'citation_conf': cit_conf,
        'extractability': extractability,
        'practical_spec': practical_spec,
        'trust_depth': trust_depth,
        'comparison_use': comparison_use,
        'glossary_use': glossary_use,
        'answer_use': answer_use,
        'summary_use': summary_use,
        'overall_ai_readiness': overall,
    })

# Sort by overall score descending
ai_citation_rows.sort(key=lambda x: x['overall_ai_readiness'], reverse=True)

print(f"  Scored {len(ai_citation_rows)} posts")

# Write AI citation readiness CSV
write_csv(
    f"{DIR_BB}/ai_citation_readiness.csv",
    ['id', 'title', 'cluster', 'citation_conf', 'extractability', 'practical_spec',
     'trust_depth', 'comparison_use', 'glossary_use', 'answer_use', 'summary_use', 'overall_ai_readiness'],
    ai_citation_rows
)

# Generate leaderboard
print("\nGenerating AI citation leaderboard...")
pages_above_70 = sum(1 for r in ai_citation_rows if r['overall_ai_readiness'] >= 70)
pages_above_80 = sum(1 for r in ai_citation_rows if r['overall_ai_readiness'] >= 80)

leaderboard_rows = []
for rank, row in enumerate(ai_citation_rows, 1):
    leaderboard_rows.append({
        'rank': rank,
        'id': row['id'],
        'title': row['title'],
        'cluster': row['cluster'],
        'overall_score': row['overall_ai_readiness'],
        'pages_above_70_count': pages_above_70,
        'pages_above_80_count': pages_above_80,
    })

write_csv(
    f"{DIR_BB}/ai_citation_leaderboard.csv",
    ['rank', 'id', 'title', 'cluster', 'overall_score', 'pages_above_70_count', 'pages_above_80_count'],
    leaderboard_rows
)

# Generate first_25_above_70 CSV
print("\nIdentifying 25 posts closest to or above 70 AI citation readiness...")
# Sort by distance to 70 (closest first, prioritize those just below)
sorted_by_proximity = sorted(
    ai_citation_rows,
    key=lambda x: (0 if x['overall_ai_readiness'] >= 70 else 1, abs(x['overall_ai_readiness'] - 70))
)

first_25_rows = []
for row in sorted_by_proximity[:25]:
    score = row['overall_ai_readiness']
    actions = []

    # Identify specific weaknesses
    if row['citation_conf'] < 70:
        actions.append(f"Boost citation confidence ({row['citation_conf']}->70+): add statistics, specific facts, definitive statements")
    if row['extractability'] < 70:
        actions.append(f"Improve extractability ({row['extractability']}->70+): add tables, structured lists, bold key terms")
    if row['practical_spec'] < 70:
        actions.append(f"Add practical specificity ({row['practical_spec']}->70+): UK-specific guidance, measurements, pricing")
    if row['trust_depth'] < 70:
        actions.append(f"Deepen trust signals ({row['trust_depth']}->70+): add methodology, expert references, update dates")
    if row['comparison_use'] < 70:
        actions.append(f"Add comparisons ({row['comparison_use']}->70+): create comparison tables, pros/cons, ratings")
    if row['glossary_use'] < 70:
        actions.append(f"Add glossary ({row['glossary_use']}->70+): define key terms, add terminology section")
    if row['answer_use'] < 70:
        actions.append(f"Add FAQ/answers ({row['answer_use']}->70+): add FAQ section, direct answers to common questions")
    if row['summary_use'] < 70:
        actions.append(f"Add summaries ({row['summary_use']}->70+): add At a Glance, Key Takeaways sections")

    first_25_rows.append({
        'id': row['id'],
        'title': row['title'],
        'cluster': row['cluster'],
        'overall_ai_readiness': score,
        'gap_to_70': round(max(0, 70 - score), 1),
        'weakest_dimension': min(
            ['citation_conf', 'extractability', 'practical_spec', 'trust_depth',
             'comparison_use', 'glossary_use', 'answer_use', 'summary_use'],
            key=lambda d: row[d]
        ),
        'weakest_score': min(row['citation_conf'], row['extractability'], row['practical_spec'],
                           row['trust_depth'], row['comparison_use'], row['glossary_use'],
                           row['answer_use'], row['summary_use']),
        'actions_to_reach_70': " | ".join(actions[:4]),
    })

write_csv(
    f"{DIR_BB}/first_25_above_70.csv",
    ['id', 'title', 'cluster', 'overall_ai_readiness', 'gap_to_70', 'weakest_dimension',
     'weakest_score', 'actions_to_reach_70'],
    first_25_rows
)


# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("GENERATION COMPLETE — SUMMARY")
print("="*80)

print(f"\nPhase 10AZ (Semantic Corridors):")
print(f"  - {DIR_AZ}/corridor_analysis.csv ({len(corridor_results)} corridors analyzed)")
print(f"  - {DIR_AZ}/corridor_link_plan.csv ({len(all_link_plans)} link opportunities)")
avg_strength = round(sum(r['corridor_strength'] for r in corridor_results) / len(corridor_results), 1) if corridor_results else 0
print(f"  - Average corridor strength: {avg_strength}/100")
strongest = max(corridor_results, key=lambda x: x['corridor_strength']) if corridor_results else {}
weakest = min(corridor_results, key=lambda x: x['corridor_strength']) if corridor_results else {}
print(f"  - Strongest: {strongest.get('corridor', 'N/A')} ({strongest.get('corridor_strength', 0)})")
print(f"  - Weakest: {weakest.get('corridor', 'N/A')} ({weakest.get('corridor_strength', 0)})")

print(f"\nPhase 10BA (Dominance Roadmaps):")
print(f"  - {DIR_BA}/dominance_roadmaps.csv ({len(roadmap_rows)} action items)")
for cluster in PRIORITY_CLUSTERS:
    cd = cluster_data.get(cluster, {})
    actions = sum(1 for r in roadmap_rows if r['cluster'] == cluster)
    print(f"  - {cluster}: {cd.get('topical_dominance_score', '?')} -> 75 target ({actions} actions)")

print(f"\nPhase 10BB (AI Citation Readiness):")
print(f"  - {DIR_BB}/ai_citation_readiness.csv ({len(ai_citation_rows)} posts scored)")
print(f"  - {DIR_BB}/ai_citation_leaderboard.csv ({len(leaderboard_rows)} rankings)")
print(f"  - {DIR_BB}/first_25_above_70.csv ({len(first_25_rows)} priority posts)")
print(f"  - Posts above 70: {pages_above_70}/{len(ai_citation_rows)}")
print(f"  - Posts above 80: {pages_above_80}/{len(ai_citation_rows)}")
if ai_citation_rows:
    print(f"  - Top score: {ai_citation_rows[0]['title']} ({ai_citation_rows[0]['overall_ai_readiness']})")
    avg_ai = round(sum(r['overall_ai_readiness'] for r in ai_citation_rows) / len(ai_citation_rows), 1)
    print(f"  - Average AI readiness: {avg_ai}/100")

print("\nAll CSVs generated successfully.")
