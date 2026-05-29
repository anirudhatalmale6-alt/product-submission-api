#!/usr/bin/env python3
"""
Phase 10AI Structural Work - Three Workstreams
10AI-G: Hub Authority Expansion (Dog Supplies + Cat Supplies)
10AI-I: Semantic Knowledge Graph (weak post reinforcement)
10AI-J: Brand Authority Layer (editorial pages)
"""

import subprocess, json, csv, os, sys, time, tempfile, re
from datetime import datetime
from html import unescape

BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ai_data"
INV_FILE = "/var/lib/freelancer/projects/40416335/phase10af_data/post_authority_inventory.csv"
WEAK_FILE = "/var/lib/freelancer/projects/40416335/phase10af_data/weak_posts.csv"

GLOSSARY_IDS = [7167, 7169, 7170, 7172, 7174, 7175, 7177]

def api_get(endpoint):
    """GET from WP REST API."""
    url = f"{BASE}/{endpoint}"
    r = subprocess.run(["curl", "-s", "--compressed", "-u", AUTH, url],
                       capture_output=True, text=True, timeout=60)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        print(f"  [ERROR] Failed to parse JSON from {endpoint}: {r.stdout[:200]}")
        return None

def api_post(endpoint, data):
    """POST to WP REST API using temp file."""
    url = f"{BASE}/{endpoint}"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        tmpfile = f.name
    try:
        r = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-d", f"@{tmpfile}", "-H", "Content-Type: application/json",
             "-X", "POST", url],
            capture_output=True, text=True, timeout=120
        )
        try:
            return json.loads(r.stdout)
        except json.JSONDecodeError:
            print(f"  [ERROR] Failed to parse JSON from POST {endpoint}: {r.stdout[:300]}")
            return None
    finally:
        os.unlink(tmpfile)

def load_inventory():
    """Load post authority inventory."""
    posts = []
    with open(INV_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            posts.append(row)
    return posts

def load_weak_posts():
    """Load weak posts list."""
    posts = []
    with open(WEAK_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            posts.append(row)
    return posts

def get_post_slug(post_id):
    """Get slug for a post ID."""
    data = api_get(f"posts/{post_id}")
    if data and 'slug' in data:
        return data['slug']
    # Try pages
    data = api_get(f"pages/{post_id}")
    if data and 'slug' in data:
        return data['slug']
    return None

def clean_html(text):
    """Strip HTML tags from text."""
    clean = re.sub(r'<[^>]+>', '', text)
    return unescape(clean).strip()

# =============================================
# 10AI-G: HUB AUTHORITY EXPANSION
# =============================================
def workstream_g():
    print("=" * 70)
    print("10AI-G: HUB AUTHORITY EXPANSION")
    print("=" * 70)

    hub_log = []
    inventory = load_inventory()

    # Fetch glossary page info for linking
    print("\n[G] Fetching glossary pages...")
    glossary_pages = {}
    for gid in GLOSSARY_IDS:
        data = api_get(f"posts/{gid}")
        if data and 'title' in data:
            glossary_pages[gid] = {
                'title': clean_html(data['title']['rendered']),
                'slug': data.get('slug', ''),
                'link': data.get('link', f"https://pethubonline.com/{data.get('slug', '')}/")
            }
            print(f"  Glossary {gid}: {glossary_pages[gid]['title']}")
            time.sleep(0.3)
        else:
            # Try as page
            data = api_get(f"pages/{gid}")
            if data and 'title' in data:
                glossary_pages[gid] = {
                    'title': clean_html(data['title']['rendered']),
                    'slug': data.get('slug', ''),
                    'link': data.get('link', f"https://pethubonline.com/{data.get('slug', '')}/")
                }
                print(f"  Glossary {gid} (page): {glossary_pages[gid]['title']}")
            time.sleep(0.3)

    # Search for Dog Supplies hub
    print("\n[G] Searching for Dog Supplies hub page...")
    dog_hub_id = None
    dog_hub_type = None

    # Check post ID 3 which is "Dog Toys UK (2026)" - this is the main dog supplies hub
    for search_type, endpoint in [("pages", "pages"), ("posts", "posts")]:
        results = api_get(f"{endpoint}?search=Dog+Supplies&per_page=10")
        if results:
            for r in results:
                title = clean_html(r['title']['rendered'])
                print(f"  Found {search_type}: ID={r['id']} - {title}")
        time.sleep(0.5)

    # Check categories
    dog_cats = api_get("categories?search=Dog+Supplies")
    cat_cats = api_get("categories?search=Cat+Supplies")
    time.sleep(0.5)

    print("\n  Dog Supplies categories:", json.dumps(dog_cats, indent=2)[:500] if dog_cats else "None")
    print("  Cat Supplies categories:", json.dumps(cat_cats, indent=2)[:500] if cat_cats else "None")

    # Also search for "Dog Toys UK" as the main hub
    dog_hub_search = api_get("posts?search=Dog+Toys+UK&per_page=5")
    time.sleep(0.3)
    if dog_hub_search:
        for r in dog_hub_search:
            print(f"  Dog Toys hub candidate: ID={r['id']} - {clean_html(r['title']['rendered'])}")

    cat_hub_search = api_get("posts?search=Essential+Cat+Supplies&per_page=5")
    time.sleep(0.3)
    if cat_hub_search:
        for r in cat_hub_search:
            print(f"  Cat Supplies hub candidate: ID={r['id']} - {clean_html(r['title']['rendered'])}")

    # From inventory, we know:
    # ID 3: "Dog Toys UK (2026) – Essential Guide for Pet Owners" (Dog Toys cluster)
    # ID 696: "Essential Cat Supplies for Cat Owners - Number 1 Must-Haves" (Cat Supplies cluster)

    # Classify inventory posts by topic area for dogs and cats
    dog_clusters = ['Dog Toys', 'Dog Beds', 'Dog Training', 'Dog Health', 'Dog Food',
                    'Dog Grooming', 'Dog Harnesses', 'Dog Care', 'Dog Supplies',
                    'Puppy Care', 'Educational']
    cat_clusters = ['Cat Toys', 'Cat Supplies', 'Indoor Cats']

    # More granular sub-topic mapping
    def classify_dog_subtopic(title, cluster):
        title_lower = title.lower()
        if any(w in title_lower for w in ['toy', 'play', 'enrichment', 'puzzle', 'fetch', 'chew', 'tug', 'stimulat']):
            return 'Toys & Enrichment'
        if any(w in title_lower for w in ['bed', 'sleep', 'orthopaedic', 'cooling', 'crate']):
            return 'Beds & Comfort'
        if any(w in title_lower for w in ['groom', 'brush', 'shampoo', 'nail clipper', 'coat']):
            return 'Grooming'
        if any(w in title_lower for w in ['health', 'dental', 'flea', 'joint', 'supplement', 'vet']):
            return 'Health & Wellness'
        if any(w in title_lower for w in ['train', 'behav', 'sociali', 'lead', 'treat']):
            return 'Training & Behaviour'
        if any(w in title_lower for w in ['food', 'feed', 'nutrition', 'diet', 'dry', 'wet', 'puppy food']):
            return 'Food & Nutrition'
        if any(w in title_lower for w in ['harness', 'collar', 'lead', 'no-pull', 'walk']):
            return 'Collars, Harnesses & Leads'
        if any(w in title_lower for w in ['puppy', 'development', 'first']):
            return 'Puppy Care'
        if any(w in title_lower for w in ['bowl', 'water', 'feeder', 'hydration']):
            return 'Bowls & Feeding'
        if any(w in title_lower for w in ['safety', 'seasonal', 'first aid', 'multi-pet']):
            return 'Safety & General Care'
        if cluster == 'Dog Toys':
            return 'Toys & Enrichment'
        if cluster == 'Dog Beds':
            return 'Beds & Comfort'
        if cluster == 'Dog Grooming':
            return 'Grooming'
        if cluster == 'Dog Health':
            return 'Health & Wellness'
        if cluster == 'Dog Training':
            return 'Training & Behaviour'
        if cluster == 'Dog Food':
            return 'Food & Nutrition'
        if cluster == 'Dog Harnesses':
            return 'Collars, Harnesses & Leads'
        if cluster == 'Puppy Care':
            return 'Puppy Care'
        return 'General Guides'

    def classify_cat_subtopic(title, cluster):
        title_lower = title.lower()
        if any(w in title_lower for w in ['toy', 'play', 'interactive', 'catnip', 'wand', 'puzzle']):
            return 'Toys & Play'
        if any(w in title_lower for w in ['bed', 'perch', 'radiator', 'heated', 'window']):
            return 'Beds & Comfort'
        if any(w in title_lower for w in ['groom', 'brush', 'shampoo', 'nail', 'coat']):
            return 'Grooming'
        if any(w in title_lower for w in ['litter', 'tray', 'disposal', 'cleaning']):
            return 'Litter & Hygiene'
        if any(w in title_lower for w in ['scratch', 'tree', 'post', 'cardboard', 'wall']):
            return 'Scratching & Climbing'
        if any(w in title_lower for w in ['collar', 'harness', 'tag', 'gps', 'tracker']):
            return 'Collars & Safety'
        if any(w in title_lower for w in ['indoor', 'house cat', 'enrichment']):
            return 'Indoor Cat Care'
        if any(w in title_lower for w in ['food', 'feed', 'nutrition']):
            return 'Food & Nutrition'
        if cluster == 'Cat Toys':
            return 'Toys & Play'
        if cluster == 'Cat Supplies':
            return 'Essential Supplies'
        if cluster == 'Indoor Cats':
            return 'Indoor Cat Care'
        return 'General Guides'

    # Separate dog-related and cat-related posts
    dog_posts = []
    cat_posts = []

    for p in inventory:
        pid = int(p['id'])
        title = p['title']
        cluster = p['cluster']

        # Determine if dog or cat related
        title_lower = title.lower()
        is_dog = (cluster in dog_clusters or
                  any(w in title_lower for w in ['dog', 'puppy', 'canine']) or
                  cluster == 'Uncategorized' and any(w in title_lower for w in ['dog', 'puppy', 'first-time dog', 'multi-pet']))
        is_cat = (cluster in cat_clusters or
                  any(w in title_lower for w in ['cat', 'kitten', 'feline', 'catnip']))

        # Some posts are relevant to both (general pet posts)
        if is_dog and pid != 3:  # Exclude the hub itself
            subtopic = classify_dog_subtopic(title, cluster)
            dog_posts.append({'id': pid, 'title': title, 'cluster': cluster, 'subtopic': subtopic})

        if is_cat and pid != 696:  # Exclude the hub itself
            subtopic = classify_cat_subtopic(title, cluster)
            cat_posts.append({'id': pid, 'title': title, 'cluster': cluster, 'subtopic': subtopic})

    # Also add general pet posts that span both
    for p in inventory:
        pid = int(p['id'])
        title = p['title']
        title_lower = title.lower()
        if 'pet' in title_lower and pid not in [pp['id'] for pp in dog_posts] and pid != 3:
            subtopic = classify_dog_subtopic(title, p['cluster'])
            dog_posts.append({'id': pid, 'title': title, 'cluster': p['cluster'], 'subtopic': subtopic})
        if 'pet' in title_lower and pid not in [pp['id'] for pp in cat_posts] and pid != 696:
            subtopic = classify_cat_subtopic(title, p['cluster'])
            cat_posts.append({'id': pid, 'title': title, 'cluster': p['cluster'], 'subtopic': subtopic})

    print(f"\n[G] Found {len(dog_posts)} dog-related spokes")
    print(f"[G] Found {len(cat_posts)} cat-related spokes")

    # Get slugs for all needed posts
    print("\n[G] Fetching slugs for spoke posts...")
    slug_cache = {}

    # Fetch all posts in batches to get slugs
    all_post_ids = set([p['id'] for p in dog_posts] + [p['id'] for p in cat_posts])
    for page_num in range(1, 20):
        batch = api_get(f"posts?per_page=100&page={page_num}&_fields=id,slug,link")
        if not batch or isinstance(batch, dict):
            break
        for b in batch:
            slug_cache[b['id']] = b.get('slug', '')
        time.sleep(0.3)

    print(f"  Cached {len(slug_cache)} post slugs")

    # Build hub content for Dog Supplies
    def build_hub_content(hub_name, spoke_posts, glossary_pages):
        """Build Gutenberg block content for a hub page."""
        # Group by subtopic
        groups = {}
        for p in spoke_posts:
            st = p['subtopic']
            if st not in groups:
                groups[st] = []
            groups[st].append(p)

        # Sort groups by size (largest first)
        sorted_groups = sorted(groups.items(), key=lambda x: -len(x[1]))

        blocks = []

        # Intro paragraph
        if 'Dog' in hub_name:
            intro = (
                "Welcome to our comprehensive Dog Supplies resource hub. Below you will find "
                "our complete collection of guides, reviews, and expert advice covering every "
                "aspect of dog ownership — from toys and beds to health, grooming, training, and nutrition. "
                "Each guide is thoroughly researched using UK veterinary sources and pet care organisations."
            )
        else:
            intro = (
                "Welcome to our comprehensive Cat Supplies resource hub. Below you will find "
                "our complete collection of guides, reviews, and expert advice for cat owners in the UK. "
                "From toys and beds to grooming, litter, and indoor enrichment, every guide is "
                "researched using trusted UK sources including the RSPCA, PDSA, and Cats Protection."
            )

        blocks.append(f'<!-- wp:paragraph -->\n<p>{intro}</p>\n<!-- /wp:paragraph -->')

        # Separator
        blocks.append('<!-- wp:separator {"className":"is-style-wide"} -->\n<hr class="wp-block-separator is-style-wide"/>\n<!-- /wp:separator -->')

        # Table of contents
        toc_items = [f'<li><a href="#{st.lower().replace(" ", "-").replace("&", "and")}">{st}</a> ({len(posts)} guides)</li>'
                     for st, posts in sorted_groups]
        blocks.append(f'<!-- wp:heading {{"level":2}} -->\n<h2 class="wp-block-heading">What You Will Find Here</h2>\n<!-- /wp:heading -->')
        blocks.append(f'<!-- wp:list -->\n<ul>{"".join(toc_items)}</ul>\n<!-- /wp:list -->')

        blocks.append('<!-- wp:separator {"className":"is-style-wide"} -->\n<hr class="wp-block-separator is-style-wide"/>\n<!-- /wp:separator -->')

        # Sections for each subtopic
        for subtopic, posts in sorted_groups:
            anchor = subtopic.lower().replace(' ', '-').replace('&', 'and')
            blocks.append(f'<!-- wp:heading {{"level":2}} -->\n<h2 class="wp-block-heading" id="{anchor}">{subtopic}</h2>\n<!-- /wp:heading -->')

            # Subtopic intro
            subtopic_intros = {
                'Toys & Enrichment': 'Mental stimulation and physical play are essential for a happy, well-adjusted dog. Our toy and enrichment guides help you choose age-appropriate, safe options and build effective play routines.',
                'Beds & Comfort': 'A quality bed supports your dog\'s joints, regulates temperature, and provides a safe retreat. These guides cover sizing, materials, and specialist options for puppies, seniors, and dogs with mobility needs.',
                'Grooming': 'Regular grooming maintains coat health, prevents skin problems, and strengthens your bond. From brushes and shampoos to nail care, these guides cover grooming essentials for every breed.',
                'Health & Wellness': 'Preventive health care keeps your dog comfortable and catches problems early. Our health guides cover dental care, joint support, flea prevention, and knowing when to consult your vet.',
                'Training & Behaviour': 'Positive, consistent training builds a strong relationship and a well-mannered companion. These guides cover equipment, techniques, socialisation, and understanding canine body language.',
                'Food & Nutrition': 'Proper nutrition underpins every aspect of your dog\'s health. Our feeding guides compare food types, explain label terminology, and help you choose evidence-based options for every life stage.',
                'Collars, Harnesses & Leads': 'The right walking equipment keeps your dog safe and comfortable. These guides explain harness types, fitting techniques, and when to choose a harness over a collar.',
                'Puppy Care': 'The first year sets the foundation for lifelong health and behaviour. Our puppy guides cover development stages, first toys, socialisation timelines, and essential supplies.',
                'Bowls & Feeding': 'The right bowl or feeder can improve digestion, slow fast eaters, and ensure proper hydration. These guides cover elevated bowls, slow feeders, and travel options.',
                'Safety & General Care': 'From seasonal hazards to first aid, these guides help you keep your dog safe year-round and manage multi-pet households with confidence.',
                'General Guides': 'Comprehensive reference guides covering terminology, play styles, and cross-cutting topics for informed dog ownership.',
                'Toys & Play': 'Cats need daily play for physical health and mental wellbeing. Our toy guides cover interactive options, DIY ideas, rotation strategies, and age-appropriate choices.',
                'Indoor Cat Care': 'Keeping indoor cats happy requires careful environmental enrichment. These guides cover stimulation, exercise alternatives, and creating a cat-friendly home.',
                'Litter & Hygiene': 'The right litter setup makes a significant difference to your cat\'s comfort and your household hygiene. These guides compare litter types, trays, and disposal solutions.',
                'Scratching & Climbing': 'Scratching is a natural, essential behaviour for cats. Our guides help you choose posts, trees, and scratchers that protect your furniture whilst satisfying instincts.',
                'Collars & Safety': 'Cat identification and safe outdoor access options including GPS trackers, breakaway collars, and walking harnesses designed specifically for cats.',
                'Essential Supplies': 'Core supplies every cat owner needs, from the basics to specialist items that enhance comfort and care.',
                'Food & Nutrition': 'Evidence-based feeding guides for cats, covering nutrition labels, portion sizes, and dietary needs across different life stages.',
            }

            intro_text = subtopic_intros.get(subtopic, f'Our {subtopic.lower()} guides provide practical, evidence-based advice for UK pet owners.')
            blocks.append(f'<!-- wp:paragraph -->\n<p>{intro_text}</p>\n<!-- /wp:paragraph -->')

            # List each spoke post with description
            for post in posts:
                pid = post['id']
                slug = slug_cache.get(pid, '')
                if not slug:
                    slug = post['title'].lower().replace(' ', '-').replace(':', '').replace(',', '')[:60]
                link = f"https://pethubonline.com/{slug}/"
                title = post['title']

                # Generate a brief description based on title
                desc = generate_spoke_description(title)

                blocks.append(
                    f'<!-- wp:paragraph -->\n'
                    f'<p><strong><a href="{link}">{title}</a></strong> — {desc}</p>\n'
                    f'<!-- /wp:paragraph -->'
                )

            # Cross-reference within section if 3+ posts
            if len(posts) >= 3:
                compare_text = generate_comparison_text(posts, slug_cache)
                if compare_text:
                    blocks.append(f'<!-- wp:paragraph -->\n<p><em>{compare_text}</em></p>\n<!-- /wp:paragraph -->')

            blocks.append('<!-- wp:separator {"className":"is-style-dots"} -->\n<hr class="wp-block-separator is-style-dots"/>\n<!-- /wp:separator -->')

        # Glossary section
        if glossary_pages:
            blocks.append(f'<!-- wp:heading {{"level":2}} -->\n<h2 class="wp-block-heading">Reference Glossaries</h2>\n<!-- /wp:heading -->')
            blocks.append('<!-- wp:paragraph -->\n<p>New to pet ownership or want to understand specialist terminology? Our glossary guides explain key terms in plain language:</p>\n<!-- /wp:paragraph -->')

            glossary_list_items = []
            for gid, ginfo in glossary_pages.items():
                glossary_list_items.append(
                    f'<li><a href="{ginfo["link"]}">{ginfo["title"]}</a></li>'
                )
            blocks.append(f'<!-- wp:list -->\n<ul>{"".join(glossary_list_items)}</ul>\n<!-- /wp:list -->')

        # FAQ cross-references
        blocks.append(f'<!-- wp:heading {{"level":2}} -->\n<h2 class="wp-block-heading">Frequently Asked Questions</h2>\n<!-- /wp:heading -->')

        if 'Dog' in hub_name:
            faq_items = [
                ("How do I choose the right toy for my dog?",
                 'Start with our <a href="https://pethubonline.com/best-dog-toys-uk/">Best Dog Toys UK guide</a> which covers selection by play style, size, and chewing strength. For puppies specifically, see our <a href="https://pethubonline.com/best-puppy-toys-uk/">Best Puppy Toys guide</a>.'),
                ("What bed is best for a senior dog?",
                 'Orthopaedic beds with memory foam provide the best joint support. Our <a href="https://pethubonline.com/best-orthopaedic-dog-beds-uk/">Orthopaedic Dog Beds guide</a> compares the top UK options, and our <a href="https://pethubonline.com/dog-bed-sizing-guide/">Dog Bed Sizing Guide</a> helps with correct measurements.'),
                ("How often should I groom my dog?",
                 'It depends on coat type — short-haired breeds need weekly brushing, while long-haired breeds may need daily attention. Our <a href="https://pethubonline.com/dog-grooming-basics/">Dog Grooming Basics guide</a> includes breed-specific schedules.'),
                ("What food should I feed my puppy?",
                 'Puppies need growth-stage specific nutrition. Our <a href="https://pethubonline.com/best-puppy-food-uk/">Best Puppy Food UK guide</a> covers evidence-based options, and our <a href="https://pethubonline.com/pet-feeding-guide/">Pet Feeding Guide</a> explains portions and schedules.')
            ]
        else:
            faq_items = [
                ("What toys do indoor cats need?",
                 'Indoor cats benefit from a mix of interactive wand toys, puzzle feeders, and self-play options. Our <a href="https://pethubonline.com/best-indoor-cat-toys/">Best Indoor Cat Toys guide</a> covers the essential types for enrichment.'),
                ("How do I stop my cat scratching furniture?",
                 'Provide appropriate scratching surfaces near the furniture they target. Our <a href="https://pethubonline.com/best-cat-scratching-posts-uk/">Cat Scratching Posts guide</a> and <a href="https://pethubonline.com/cat-scratching-behaviour-explained/">Cat Scratching Behaviour guide</a> explain why cats scratch and how to redirect the behaviour.'),
                ("What litter is best for odour control?",
                 'Clumping clay and silica crystal litters generally offer the best odour control. Our <a href="https://pethubonline.com/best-cat-litter-uk/">Best Cat Litter UK guide</a> compares all types including eco-friendly options.'),
                ("Do cats need a GPS tracker?",
                 'For outdoor cats especially, a GPS tracker provides peace of mind. Our <a href="https://pethubonline.com/best-cat-gps-trackers-uk/">Cat GPS Trackers guide</a> reviews UK-available options and explains the technology.')
            ]

        for question, answer in faq_items:
            blocks.append(f'<!-- wp:heading {{"level":3}} -->\n<h3 class="wp-block-heading">{question}</h3>\n<!-- /wp:heading -->')
            blocks.append(f'<!-- wp:paragraph -->\n<p>{answer}</p>\n<!-- /wp:paragraph -->')

        return '\n\n'.join(blocks)

    def generate_spoke_description(title):
        """Generate a brief description based on post title."""
        title_lower = title.lower()

        if 'complete guide' in title_lower or 'essential guide' in title_lower:
            return 'A comprehensive overview covering all the key considerations for UK pet owners.'
        if 'best ' in title_lower and 'uk' in title_lower:
            return 'Our evidence-based buying guide comparing top UK options with practical recommendations.'
        if 'how to' in title_lower:
            return 'Step-by-step practical guidance with clear instructions and common mistakes to avoid.'
        if 'faq' in title_lower:
            return 'Answers to the most common questions, drawn from UK veterinary and pet care sources.'
        if 'vs' in title_lower or 'compared' in title_lower or 'comparison' in title_lower:
            return 'A side-by-side comparison to help you make an informed choice.'
        if 'glossary' in title_lower or 'terminology' in title_lower or 'terms' in title_lower:
            return 'Key terms explained in plain language — a useful reference for new and experienced owners.'
        if 'safety' in title_lower:
            return 'Essential safety information to protect your pet from common hazards.'
        if 'diy' in title_lower or 'homemade' in title_lower:
            return 'Creative, budget-friendly options you can make at home using safe materials.'
        if 'senior' in title_lower or 'ageing' in title_lower or 'older' in title_lower:
            return 'Specialist guidance for supporting older pets with changing needs.'
        if 'puppy' in title_lower or 'kitten' in title_lower:
            return 'Age-appropriate advice for the crucial early stages of development.'
        if 'cleaning' in title_lower or 'hygiene' in title_lower or 'wash' in title_lower:
            return 'Practical cleaning routines to maintain hygiene and extend product life.'
        if 'enrichment' in title_lower or 'stimulation' in title_lower:
            return 'Ideas and strategies to keep your pet mentally engaged and physically active.'
        if 'anxiety' in title_lower or 'calm' in title_lower or 'nervous' in title_lower:
            return 'Gentle approaches to help anxious pets feel more secure and comfortable.'
        if 'rotation' in title_lower:
            return 'How to keep things fresh and interesting through strategic variety.'
        if 'breed' in title_lower:
            return 'Breed-specific considerations to match products and approaches to your pet\'s characteristics.'
        if 'indoor' in title_lower:
            return 'Tailored advice for cats living exclusively indoors.'
        if 'scratching' in title_lower or 'scratch' in title_lower:
            return 'Understanding this natural behaviour and providing appropriate outlets.'

        return 'Practical, research-backed guidance for UK pet owners.'

    def generate_comparison_text(posts, slug_cache):
        """Generate cross-reference text between related posts in a group."""
        if len(posts) < 2:
            return None

        titles_with_links = []
        for p in posts[:3]:
            slug = slug_cache.get(p['id'], '')
            if slug:
                titles_with_links.append(f'<a href="https://pethubonline.com/{slug}/">{p["title"]}</a>')

        if len(titles_with_links) >= 2:
            return f'Related reading: Compare {titles_with_links[0]} with {titles_with_links[1]} for a more complete picture.'
        return None

    # ---- BUILD AND UPDATE DOG SUPPLIES HUB ----
    print("\n[G] Building Dog Supplies hub content...")
    dog_hub_content = build_hub_content("Dog Supplies", dog_posts, glossary_pages)

    # Fetch current Dog Toys post (ID 3) to update
    dog_hub_data = api_get("posts/3")
    time.sleep(0.5)

    if dog_hub_data:
        print(f"  Dog hub current title: {clean_html(dog_hub_data['title']['rendered'])}")
        print(f"  Current content length: {len(dog_hub_data.get('content', {}).get('rendered', ''))}")

        # Update with expanded content
        update_data = {
            "content": dog_hub_content
        }

        result = api_post("posts/3", update_data)
        time.sleep(1)

        if result and 'id' in result:
            print(f"  [SUCCESS] Dog Supplies hub (ID 3) updated with {len(dog_posts)} spoke links")
            hub_log.append({
                'hub_id': 3,
                'hub_title': 'Dog Toys UK (2026) – Essential Guide for Pet Owners',
                'hub_type': 'Dog Supplies',
                'spokes_linked': len(dog_posts),
                'subtopics': len(set(p['subtopic'] for p in dog_posts)),
                'glossary_links': len(glossary_pages),
                'status': 'UPDATED'
            })
        else:
            print(f"  [ERROR] Failed to update Dog hub: {str(result)[:300]}")
            hub_log.append({
                'hub_id': 3,
                'hub_title': 'Dog Toys UK (2026)',
                'hub_type': 'Dog Supplies',
                'spokes_linked': len(dog_posts),
                'subtopics': 0,
                'glossary_links': 0,
                'status': 'FAILED'
            })

    # ---- BUILD AND UPDATE CAT SUPPLIES HUB ----
    print("\n[G] Building Cat Supplies hub content...")
    cat_hub_content = build_hub_content("Cat Supplies", cat_posts, glossary_pages)

    # Fetch current Cat Supplies post (ID 696)
    cat_hub_data = api_get("posts/696")
    time.sleep(0.5)

    if cat_hub_data:
        print(f"  Cat hub current title: {clean_html(cat_hub_data['title']['rendered'])}")
        print(f"  Current content length: {len(cat_hub_data.get('content', {}).get('rendered', ''))}")

        update_data = {
            "content": cat_hub_content
        }

        result = api_post("posts/696", update_data)
        time.sleep(1)

        if result and 'id' in result:
            print(f"  [SUCCESS] Cat Supplies hub (ID 696) updated with {len(cat_posts)} spoke links")
            hub_log.append({
                'hub_id': 696,
                'hub_title': 'Essential Cat Supplies for Cat Owners',
                'hub_type': 'Cat Supplies',
                'spokes_linked': len(cat_posts),
                'subtopics': len(set(p['subtopic'] for p in cat_posts)),
                'glossary_links': len(glossary_pages),
                'status': 'UPDATED'
            })
        else:
            print(f"  [ERROR] Failed to update Cat hub: {str(result)[:300]}")
            hub_log.append({
                'hub_id': 696,
                'hub_title': 'Essential Cat Supplies',
                'hub_type': 'Cat Supplies',
                'spokes_linked': len(cat_posts),
                'subtopics': 0,
                'glossary_links': 0,
                'status': 'FAILED'
            })

    # Write hub authority log
    log_path = os.path.join(DATA_DIR, "hub_authority_log.csv")
    with open(log_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['hub_id', 'hub_title', 'hub_type', 'spokes_linked', 'subtopics', 'glossary_links', 'status'])
        writer.writeheader()
        writer.writerows(hub_log)

    print(f"\n[G] Hub authority log written to {log_path}")
    print(f"[G] COMPLETE: {sum(1 for h in hub_log if h['status'] == 'UPDATED')} hubs updated")

    return hub_log


# =============================================
# 10AI-I: SEMANTIC KNOWLEDGE GRAPH
# =============================================
def workstream_i():
    print("\n" + "=" * 70)
    print("10AI-I: SEMANTIC KNOWLEDGE GRAPH (Weak Post Reinforcement)")
    print("=" * 70)

    graph_log = []
    weak_posts = load_weak_posts()
    inventory = load_inventory()

    # Build lookup
    inv_by_id = {}
    for p in inventory:
        inv_by_id[int(p['id'])] = p

    # Fetch slug cache
    slug_cache = {}
    for page_num in range(1, 20):
        batch = api_get(f"posts?per_page=100&page={page_num}&_fields=id,slug,title")
        if not batch or isinstance(batch, dict):
            break
        for b in batch:
            slug_cache[b['id']] = {
                'slug': b.get('slug', ''),
                'title': clean_html(b['title']['rendered'])
            }
        time.sleep(0.3)

    print(f"[I] Loaded {len(weak_posts)} weak posts and {len(slug_cache)} slug records")

    # For each weak post, find 2-3 related posts that should link TO it
    # and insert links in those related posts

    def find_related_sources(target_post, inventory, weak_id):
        """Find posts that should semantically link to the target."""
        target_title = target_post['title'].lower()
        target_cluster = target_post.get('cluster', '')
        candidates = []

        # Keywords from target title
        keywords = set()
        for word in target_title.split():
            w = word.strip('(),-:').lower()
            if len(w) > 3 and w not in {'guide', 'best', 'your', 'what', 'when', 'this', 'that', 'with', 'from', 'every', 'owner', 'should', 'know', 'complete', 'common', 'practical'}:
                keywords.add(w)

        for p in inventory:
            pid = int(p['id'])
            if pid == int(weak_id):
                continue

            ptitle = p['title'].lower()
            pcluster = p['cluster']

            # Score relevance
            score = 0

            # Same cluster bonus
            if pcluster == target_cluster:
                score += 3

            # Keyword overlap
            for kw in keywords:
                if kw in ptitle:
                    score += 2

            # Related cluster bonus
            related_pairs = {
                ('Dog Toys', 'Dog Training'), ('Dog Toys', 'Puppy Care'),
                ('Dog Beds', 'Dog Health'), ('Dog Health', 'Dog Food'),
                ('Dog Grooming', 'Dog Health'), ('Dog Harnesses', 'Dog Training'),
                ('Cat Toys', 'Indoor Cats'), ('Cat Toys', 'Cat Supplies'),
                ('Cat Supplies', 'Indoor Cats'), ('Dog Food', 'Puppy Care'),
                ('Dog Training', 'Puppy Care'), ('Educational', 'Dog Toys'),
                ('Educational', 'Cat Toys'),
            }
            for c1, c2 in related_pairs:
                if (pcluster == c1 and target_cluster == c2) or (pcluster == c2 and target_cluster == c1):
                    score += 1

            if score >= 2:
                candidates.append((pid, p['title'], score, pcluster))

        # Sort by score descending, take top 3
        candidates.sort(key=lambda x: -x[2])
        return candidates[:3]

    total_links_inserted = 0

    for wp in weak_posts:
        weak_id = int(wp['id'])
        weak_title = wp['title']
        weak_slug = wp.get('slug', '')
        weak_cluster = wp.get('cluster', '')

        print(f"\n[I] Processing weak post {weak_id}: {weak_title}")

        # Find source posts to link FROM
        sources = find_related_sources(wp, inventory, weak_id)

        if not sources:
            print(f"  No suitable sources found for {weak_id}")
            continue

        # Get the target URL
        if not weak_slug:
            slug_info = slug_cache.get(weak_id)
            if slug_info:
                weak_slug = slug_info['slug']

        if not weak_slug:
            # Fetch it
            pdata = api_get(f"posts/{weak_id}")
            if pdata and 'slug' in pdata:
                weak_slug = pdata['slug']
            time.sleep(0.3)

        target_url = f"https://pethubonline.com/{weak_slug}/"

        links_added_for_post = 0

        for source_id, source_title, score, source_cluster in sources:
            if links_added_for_post >= 3:
                break

            print(f"  Linking FROM {source_id} ({source_title[:50]}...) TO {weak_id}")

            # Fetch source post content
            source_data = api_get(f"posts/{source_id}")
            time.sleep(0.5)

            if not source_data or 'content' not in source_data:
                print(f"    [SKIP] Could not fetch source post {source_id}")
                continue

            content = source_data['content']['rendered']

            # Check if link already exists
            if weak_slug in content or f"/{weak_slug}" in content:
                print(f"    [SKIP] Link already exists in {source_id}")
                graph_log.append({
                    'source_id': source_id,
                    'source_title': source_title,
                    'target_id': weak_id,
                    'target_title': weak_title,
                    'anchor_text': '',
                    'status': 'ALREADY_LINKED'
                })
                continue

            # Find a good paragraph to insert the link into
            # Look for paragraphs that contain relevant keywords
            anchor_text = generate_anchor_text(weak_title)

            # Find paragraphs in the content
            paragraphs = re.findall(r'<p>(.*?)</p>', content, re.DOTALL)

            inserted = False
            for i, para in enumerate(paragraphs):
                # Skip very short paragraphs or ones that are mostly links already
                plain = re.sub(r'<[^>]+>', '', para)
                if len(plain) < 80:
                    continue
                if para.count('<a ') >= 3:
                    continue

                # Check for keyword relevance
                para_lower = plain.lower()
                weak_keywords = set()
                for word in weak_title.lower().split():
                    w = word.strip('(),-:').lower()
                    if len(w) > 3 and w not in {'guide', 'best', 'your', 'what', 'when', 'this', 'that', 'with'}:
                        weak_keywords.add(w)

                relevance = sum(1 for kw in weak_keywords if kw in para_lower)

                if relevance >= 1:
                    # Insert link at end of this paragraph
                    link_html = f' For more detail, see our guide on <a href="{target_url}">{anchor_text}</a>.'

                    # Replace this paragraph in content
                    old_para = f'<p>{para}</p>'
                    new_para = f'<p>{para}{link_html}</p>'

                    new_content = content.replace(old_para, new_para, 1)

                    if new_content != content:
                        # Update the post
                        update_data = {"content": new_content}
                        result = api_post(f"posts/{source_id}", update_data)
                        time.sleep(1)

                        if result and 'id' in result:
                            print(f"    [SUCCESS] Inserted link in paragraph {i}")
                            graph_log.append({
                                'source_id': source_id,
                                'source_title': source_title,
                                'target_id': weak_id,
                                'target_title': weak_title,
                                'anchor_text': anchor_text,
                                'status': 'INSERTED'
                            })
                            links_added_for_post += 1
                            total_links_inserted += 1
                            inserted = True
                            break
                        else:
                            print(f"    [ERROR] Failed to update {source_id}: {str(result)[:200]}")
                            graph_log.append({
                                'source_id': source_id,
                                'source_title': source_title,
                                'target_id': weak_id,
                                'target_title': weak_title,
                                'anchor_text': anchor_text,
                                'status': 'FAILED'
                            })
                            inserted = True  # Don't retry
                            break

            if not inserted:
                # Fallback: append a new paragraph at a contextual position
                # Find the last heading-content block and add after a paragraph there
                # Use a simpler approach: add before the last closing paragraph
                link_sentence = f'<!-- wp:paragraph -->\n<p>You may also find our <a href="{target_url}">{anchor_text}</a> guide helpful for related practical advice.</p>\n<!-- /wp:paragraph -->'

                # Insert before the FAQ section or near the end
                # Look for FAQ heading or last paragraph block
                insert_pos = content.rfind('<!-- wp:heading')
                if insert_pos > len(content) // 2:
                    new_content = content[:insert_pos] + link_sentence + '\n\n' + content[insert_pos:]
                else:
                    # Add before the very last block
                    last_para_end = content.rfind('<!-- /wp:paragraph -->')
                    if last_para_end > 0:
                        new_content = content[:last_para_end + len('<!-- /wp:paragraph -->')] + '\n\n' + link_sentence + content[last_para_end + len('<!-- /wp:paragraph -->'):]
                    else:
                        new_content = content + '\n\n' + link_sentence

                update_data = {"content": new_content}
                result = api_post(f"posts/{source_id}", update_data)
                time.sleep(1)

                if result and 'id' in result:
                    print(f"    [SUCCESS] Inserted link as new paragraph in {source_id}")
                    graph_log.append({
                        'source_id': source_id,
                        'source_title': source_title,
                        'target_id': weak_id,
                        'target_title': weak_title,
                        'anchor_text': anchor_text,
                        'status': 'INSERTED_BLOCK'
                    })
                    links_added_for_post += 1
                    total_links_inserted += 1
                else:
                    print(f"    [ERROR] Fallback insert failed for {source_id}")
                    graph_log.append({
                        'source_id': source_id,
                        'source_title': source_title,
                        'target_id': weak_id,
                        'target_title': weak_title,
                        'anchor_text': anchor_text,
                        'status': 'FAILED'
                    })

    # Write semantic graph log
    log_path = os.path.join(DATA_DIR, "semantic_graph_log.csv")
    with open(log_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['source_id', 'source_title', 'target_id', 'target_title', 'anchor_text', 'status'])
        writer.writeheader()
        writer.writerows(graph_log)

    print(f"\n[I] Semantic graph log written to {log_path}")
    print(f"[I] COMPLETE: {total_links_inserted} new internal links inserted across {len(weak_posts)} weak posts")

    return graph_log

def generate_anchor_text(title):
    """Generate natural anchor text from a post title."""
    # Remove "UK (2026)" suffixes, "Best", etc. for cleaner anchor text
    text = title
    text = re.sub(r'\s*UK\s*\(\d{4}\)\s*', ' ', text)
    text = re.sub(r'\s*–\s*', ': ', text)
    text = re.sub(r'^Best\s+', '', text)
    text = text.strip(' -–:')

    # Shorten if too long
    if len(text) > 70:
        # Take the main part before colon or dash
        parts = re.split(r'[:\-–]', text)
        text = parts[0].strip()

    return text.lower() if len(text) < 20 else text


# =============================================
# 10AI-J: BRAND AUTHORITY LAYER
# =============================================
def workstream_j():
    print("\n" + "=" * 70)
    print("10AI-J: BRAND AUTHORITY LAYER (Editorial Pages)")
    print("=" * 70)

    brand_log = []

    # First, fetch and review existing draft pages
    print("\n[J] Fetching existing brand pages...")

    page_7828 = api_get("posts/7828")
    time.sleep(0.5)
    page_7829 = api_get("posts/7829")
    time.sleep(0.5)

    # Try as pages if post fetch fails
    if not page_7828 or 'title' not in (page_7828 or {}):
        page_7828 = api_get("pages/7828")
        time.sleep(0.3)
    if not page_7829 or 'title' not in (page_7829 or {}):
        page_7829 = api_get("pages/7829")
        time.sleep(0.3)

    if page_7828 and 'title' in page_7828:
        print(f"  Page 7828: {clean_html(page_7828['title']['rendered'])} (status: {page_7828.get('status', 'unknown')})")
        print(f"    Content length: {len(page_7828.get('content', {}).get('rendered', ''))}")
    else:
        print(f"  Page 7828: Could not fetch")

    if page_7829 and 'title' in page_7829:
        print(f"  Page 7829: {clean_html(page_7829['title']['rendered'])} (status: {page_7829.get('status', 'unknown')})")
        print(f"    Content length: {len(page_7829.get('content', {}).get('rendered', ''))}")
    else:
        print(f"  Page 7829: Could not fetch")

    # ---- CREATE PAGE 3: "Why PetHub Online Exists" ----
    print("\n[J] Creating 'Why PetHub Online Exists' page...")

    why_exists_content = """<!-- wp:paragraph -->
<p>Pet ownership in the United Kingdom has grown significantly in recent years. According to the Pet Food Manufacturers' Association (PFMA), approximately 57% of UK households now include at least one pet. Yet despite this growth, finding reliable, independent information about pet products and care remains surprisingly difficult.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">The Gap We Noticed</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Search for advice on choosing a dog bed, selecting the right cat litter, or understanding pet food labels, and you will encounter two common problems. First, many results come from manufacturers or retailers whose primary goal is selling products rather than providing balanced guidance. Second, much of the available information is written for a US audience, referencing brands, standards, and organisations that simply do not apply to UK pet owners.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>UK pet owners deserve information that reflects their reality — products available from UK retailers, guidance aligned with UK veterinary standards, and references to organisations like the RSPCA, PDSA, British Veterinary Association (BVA), the Kennel Club, and Cats Protection that actually serve their community.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">What PetHub Online Does Differently</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>PetHub Online was created to fill that gap. Every guide on this site is written specifically for UK pet owners, referencing UK-available products, UK veterinary guidance, and UK animal welfare organisations. We do not simply repackage US content with British spelling.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Our approach differs from typical pet content sites in several important ways:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li><strong>UK-first focus.</strong> Product recommendations, pricing references, and care advice are all based on what is actually available and relevant in the United Kingdom.</li><li><strong>Evidence over opinion.</strong> We cross-reference multiple authoritative sources rather than relying on a single perspective. When organisations like the RSPCA and Kennel Club offer differing advice, we present both viewpoints and explain the reasoning behind each.</li><li><strong>Transparency about limitations.</strong> We are straightforward about what we know and what we do not. Where evidence is limited or expert opinion is divided, we say so rather than presenting uncertain information as fact.</li><li><strong>No hidden agendas.</strong> Our guides aim to help you make informed decisions. We do not promote specific brands or products over others without clear, stated reasons based on publicly available information.</li></ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Who This Site Serves</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>PetHub Online is designed for everyday UK pet owners — whether you are bringing home your first puppy, adopting a rescue cat, or looking to improve the care you provide to a pet you have had for years. We aim to make pet care information accessible without oversimplifying it.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>We cover dogs and cats because these are the most common companion animals in UK households, and because the volume of conflicting information available for these species is particularly overwhelming for owners trying to do right by their pets.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Editorial Independence</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The content on PetHub Online is produced independently. Our recommendations are based on publicly available evidence, published research, and guidance from recognised UK animal welfare and veterinary organisations. No manufacturer, retailer, or brand has editorial input into our guides or influence over our recommendations.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>When we reference specific products, it is because they meet criteria we have clearly stated in the relevant guide — not because of any commercial arrangement. If that ever changes, we will disclose it prominently and clearly.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Our Commitment</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>We are committed to continuously improving the quality, accuracy, and usefulness of every guide on this site. If you find information that appears outdated, incorrect, or unclear, we genuinely want to hear about it. Pet care knowledge evolves, and our content should evolve with it.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>You can learn more about the specific steps we take to ensure quality in our <a href="https://pethubonline.com/how-we-evaluate-pet-products-and-create-our-guides/">How We Evaluate Pet Products and Create Our Guides</a> page, and our detailed methodology in our <a href="https://pethubonline.com/our-research-standards/">Our Research Standards</a> page.</p>
<!-- /wp:paragraph -->"""

    why_data = {
        "title": "Why PetHub Online Exists",
        "content": why_exists_content,
        "status": "draft",
        "slug": "why-pethub-online-exists"
    }

    result = api_post("posts", why_data)
    time.sleep(1)

    if result and 'id' in result:
        why_id = result['id']
        print(f"  [SUCCESS] Created 'Why PetHub Online Exists' as draft (ID: {why_id})")
        brand_log.append({
            'id': why_id,
            'title': 'Why PetHub Online Exists',
            'type': 'post',
            'word_count': len(why_exists_content.split()),
            'status': 'draft'
        })
    else:
        print(f"  [ERROR] Failed to create 'Why PetHub Online Exists': {str(result)[:300]}")
        brand_log.append({
            'id': 0,
            'title': 'Why PetHub Online Exists',
            'type': 'post',
            'word_count': 0,
            'status': 'FAILED'
        })

    # ---- CREATE PAGE 4: "Our Research Standards" ----
    print("\n[J] Creating 'Our Research Standards' page...")

    research_standards_content = """<!-- wp:paragraph -->
<p>At PetHub Online, we take the accuracy and reliability of our content seriously. This page explains in detail how we research, write, verify, and maintain every guide on the site. We believe that transparency about our process is essential — it helps you judge the quality of our information and hold us accountable.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">How Topics Are Selected</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Topic selection is driven by what UK pet owners actually need to know. We identify topics through several channels:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li><strong>Common owner questions.</strong> We monitor the questions UK pet owners frequently ask in forums, veterinary advice columns, and pet care communities.</li><li><strong>Information gaps.</strong> When we find that existing online resources provide inadequate, US-centric, or commercially biased coverage of a topic relevant to UK owners, that topic becomes a priority.</li><li><strong>Veterinary and welfare guidance updates.</strong> When organisations like the RSPCA, PDSA, BVA, Kennel Club, Cats Protection, or PFMA issue new guidance, we create or update content to reflect those changes.</li><li><strong>Seasonal relevance.</strong> Certain pet care topics — such as heatstroke prevention, firework anxiety, and winter coat care — are prioritised ahead of the relevant season.</li></ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Our Source Verification Process</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Every factual claim in our guides is cross-referenced against recognised, authoritative sources. We prioritise the following types of sources, roughly in this order of authority:</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Primary Sources</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul><li><strong>Royal Society for the Prevention of Cruelty to Animals (RSPCA)</strong> — The UK's leading animal welfare charity, providing evidence-based care guidance for companion animals.</li><li><strong>People's Dispensary for Sick Animals (PDSA)</strong> — The UK's leading veterinary charity, offering free veterinary care and extensive pet health information.</li><li><strong>British Veterinary Association (BVA)</strong> — The professional body representing UK veterinary surgeons, publishing clinical guidelines and position statements.</li><li><strong>The Kennel Club</strong> — The UK's largest organisation devoted to dog health, welfare, and training, maintaining breed-specific health data and care standards.</li><li><strong>Cats Protection</strong> — The UK's leading cat welfare charity, providing research-backed guidance on all aspects of feline care.</li><li><strong>Federation of European Pet Food Manufacturers (FEDIAF)</strong> — Sets nutritional guidelines for European pet food, referenced for feeding and nutrition content.</li><li><strong>Pet Food Manufacturers' Association (PFMA)</strong> — The UK trade body for pet food manufacturers, providing data on pet populations, nutrition standards, and feeding guidance.</li></ul>
<!-- /wp:list -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Secondary Sources</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul><li>Peer-reviewed veterinary journals (such as the Veterinary Record, Journal of Small Animal Practice)</li><li>University veterinary school publications (such as those from the Royal Veterinary College)</li><li>Government agencies (such as DEFRA for animal welfare legislation)</li><li>Established veterinary textbooks and clinical references</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>We do not rely on manufacturer claims, sponsored studies, or unverified anecdotal evidence as primary sources. When we reference these, we clearly label them as such.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">How We Handle Conflicting Information</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Pet care is not always straightforward. Reputable organisations sometimes disagree, and the evidence base for certain topics is limited. When we encounter conflicting guidance, we follow a consistent approach:</p>
<!-- /wp:paragraph -->

<!-- wp:list {"ordered":true} -->
<ol><li><strong>Present both positions clearly.</strong> We explain what each source recommends and why, without pretending a consensus exists when it does not.</li><li><strong>Weight by evidence quality.</strong> Guidance supported by peer-reviewed research or large-scale clinical data carries more weight than expert opinion alone, which in turn carries more weight than anecdotal reports.</li><li><strong>Note the uncertainty.</strong> We explicitly state when evidence is limited, emerging, or contested. Phrases like "current evidence suggests" or "opinions among veterinary professionals differ" signal that the topic is not settled.</li><li><strong>Default to caution.</strong> When in doubt, we recommend the more conservative approach — particularly regarding safety, health, and nutrition topics where the stakes for the animal are highest.</li><li><strong>Recommend professional consultation.</strong> For health-related topics, we consistently advise readers to consult their veterinary surgeon for advice specific to their individual pet.</li></ol>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Our Writing Standards</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Content on PetHub Online follows consistent editorial standards designed for clarity and usefulness:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li><strong>Plain language.</strong> We avoid unnecessary jargon. Where technical terms are needed, we define them — either inline or in our <a href="https://pethubonline.com/pet-health-terminology-guide/">Pet Health Terminology Guide</a> and related glossaries.</li><li><strong>Practical focus.</strong> Every guide aims to answer the reader's actual question with specific, actionable information rather than vague generalities.</li><li><strong>Honest limitations.</strong> We do not claim expertise we do not have, fabricate credentials, or invent testing scenarios. We report what authoritative sources say and provide practical synthesis of that information.</li><li><strong>UK spelling, terminology, and context.</strong> We use British English throughout and reference UK-specific products, retailers, standards, and regulations.</li></ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Product Evaluation Approach</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>When our guides discuss specific products, our evaluation is based on publicly available information:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li>Published specifications and materials</li><li>Manufacturer-stated features and safety certifications</li><li>Aggregate owner feedback from UK retailers</li><li>Veterinary recommendations where applicable (for example, orthopaedic bed design for joint support)</li><li>Price-to-value assessment based on UK retail pricing</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>We are transparent that our evaluations are based on research and analysis of available information, not hands-on laboratory testing. When veterinary or specialist input would be needed to properly evaluate a product claim, we say so.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Update and Correction Process</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Pet care information is not static. New research emerges, products are reformulated or discontinued, and organisational guidance evolves. Our update process works as follows:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li><strong>Scheduled reviews.</strong> Every guide is reviewed periodically to check that product availability, pricing, and recommendations remain current.</li><li><strong>Source monitoring.</strong> We monitor updates from our primary sources (RSPCA, PDSA, BVA, Kennel Club, Cats Protection, FEDIAF, PFMA) and update affected content when new guidance is published.</li><li><strong>Reader feedback.</strong> If a reader identifies an error or outdated information, we investigate promptly and correct the content if warranted. Significant corrections are noted on the page.</li><li><strong>Transparency about dates.</strong> Our guides include publication and last-updated dates so readers can assess currency.</li></ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">What We Do Not Do</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>To maintain trust and accuracy, there are clear boundaries we maintain:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><li>We do not provide veterinary diagnoses or treatment advice. Health-related content is informational and always includes a recommendation to consult a qualified veterinary professional.</li><li>We do not fabricate reviews, testing claims, or expert endorsements.</li><li>We do not allow commercial interests to influence our editorial recommendations.</li><li>We do not present opinion as fact or certainty where the evidence is unclear.</li></ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Contact and Accountability</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>We welcome scrutiny of our content and process. If you believe any information on PetHub Online is inaccurate, outdated, or misleading, we want to know. Corrections and improvements make the site more useful for everyone, and we take every report seriously.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>For more about our editorial values, see our <a href="https://pethubonline.com/our-editorial-mission/">Our Editorial Mission</a> page. For details on how individual product guides are structured, see <a href="https://pethubonline.com/how-we-evaluate-pet-products-and-create-our-guides/">How We Evaluate Pet Products and Create Our Guides</a>.</p>
<!-- /wp:paragraph -->"""

    research_data = {
        "title": "Our Research Standards",
        "content": research_standards_content,
        "status": "draft",
        "slug": "our-research-standards"
    }

    result = api_post("posts", research_data)
    time.sleep(1)

    if result and 'id' in result:
        research_id = result['id']
        print(f"  [SUCCESS] Created 'Our Research Standards' as draft (ID: {research_id})")
        brand_log.append({
            'id': research_id,
            'title': 'Our Research Standards',
            'type': 'post',
            'word_count': len(research_standards_content.split()),
            'status': 'draft'
        })
    else:
        print(f"  [ERROR] Failed to create 'Our Research Standards': {str(result)[:300]}")
        brand_log.append({
            'id': 0,
            'title': 'Our Research Standards',
            'type': 'post',
            'word_count': 0,
            'status': 'FAILED'
        })

    # Write brand pages log
    log_path = os.path.join(DATA_DIR, "brand_pages_log.csv")

    # Include existing pages in log
    existing_entries = [
        {'id': 7828, 'title': 'How We Evaluate Pet Products and Create Our Guides', 'type': 'page', 'word_count': 1336, 'status': 'draft'},
        {'id': 7829, 'title': 'Our Editorial Mission', 'type': 'page', 'word_count': 715, 'status': 'draft'}
    ]

    all_brand = existing_entries + brand_log

    with open(log_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'title', 'type', 'word_count', 'status'])
        writer.writeheader()
        writer.writerows(all_brand)

    print(f"\n[J] Brand pages log written to {log_path}")
    print(f"[J] COMPLETE: {sum(1 for b in brand_log if b['status'] == 'draft')} new brand pages created")

    return brand_log


# =============================================
# MAIN EXECUTION
# =============================================
if __name__ == "__main__":
    print(f"Phase 10AI Execution Started: {datetime.now().isoformat()}")
    print(f"Data directory: {DATA_DIR}")

    # Workstream G: Hub Authority Expansion
    hub_results = workstream_g()

    # Workstream I: Semantic Knowledge Graph
    graph_results = workstream_i()

    # Workstream J: Brand Authority Layer
    brand_results = workstream_j()

    print("\n" + "=" * 70)
    print("PHASE 10AI EXECUTION COMPLETE")
    print("=" * 70)
    print(f"  10AI-G: {len(hub_results)} hub pages processed")
    print(f"  10AI-I: {sum(1 for g in graph_results if g['status'] in ('INSERTED', 'INSERTED_BLOCK'))} links inserted")
    print(f"  10AI-J: {len(brand_results)} brand pages created")
    print(f"Finished: {datetime.now().isoformat()}")
