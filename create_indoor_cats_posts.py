#!/usr/bin/env python3
"""
Phase 23 - Indoor Cats Educational Posts Publisher
Publishes 21 Indoor Cats posts to PetHub Online (pethubonline.com)
"""

import requests
import json
import time
import os
import sys
import traceback
from datetime import datetime

# ─── Configuration ───
WP_URL = "https://pethubonline.com/wp-json/wp/v2"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_AUTH = (WP_USER, WP_PASS)
WP_HEADERS = {"Accept-Encoding": "gzip, deflate"}
CATEGORY_ID = 1413
AMAZON_TAG = "pethubonline-21"
PEXELS_KEY = "dmGyKrZqTlwukxWzOK1EkH4jbEv9EaIDpLGj7eL5MZ07bl6AR9OEoHlB"
RESULTS_PATH = "/var/lib/freelancer/projects/40416335/phase23_indoor_cats_results.json"
DELAY = 2  # seconds between API calls


def api_call(method, url, retries=3, **kwargs):
    """Make an API call with retry logic for rate limiting."""
    for attempt in range(retries):
        try:
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            kwargs['headers'].update(WP_HEADERS)
            resp = getattr(requests, method)(url, timeout=60, **kwargs)
            if resp.status_code == 429:
                wait = 10 * (attempt + 1)
                print(f"  Rate limited (429). Waiting {wait}s...")
                time.sleep(wait)
                continue
            return resp
        except Exception as e:
            print(f"  Request error (attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                time.sleep(5)
    return None


def fetch_pexels_image(query):
    """Fetch a landscape image URL from Pexels."""
    url = "https://api.pexels.com/v1/search"
    params = {"query": query, "orientation": "landscape", "per_page": 5}
    headers = {"Authorization": PEXELS_KEY}
    resp = api_call("get", url, headers=headers, params=params)
    if resp and resp.status_code == 200:
        data = resp.json()
        if data.get("photos"):
            photo = data["photos"][0]
            img_url = photo["src"].get("large2x") or photo["src"].get("large") or photo["src"]["original"]
            photographer = photo.get("photographer", "Pexels")
            return img_url, photographer
    return None, None


def download_image(img_url):
    """Download an image and return bytes + content type."""
    resp = api_call("get", img_url, headers={})
    if resp and resp.status_code == 200:
        content_type = resp.headers.get("Content-Type", "image/jpeg")
        return resp.content, content_type
    return None, None


def upload_media(image_bytes, content_type, filename, alt_text=""):
    """Upload image to WordPress media library."""
    url = f"{WP_URL}/media"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": content_type,
        "Accept-Encoding": "gzip, deflate",
    }
    resp = api_call("post", url, auth=WP_AUTH, headers=headers, data=image_bytes)
    if resp and resp.status_code == 201:
        media_id = resp.json().get("id")
        # Set alt text
        if media_id and alt_text:
            api_call("post", f"{url}/{media_id}", auth=WP_AUTH, json={"alt_text": alt_text})
        return media_id
    else:
        print(f"  Media upload failed: {resp.status_code if resp else 'No response'}")
        if resp:
            print(f"  Response: {resp.text[:300]}")
    return None


def create_post(title, content, slug, featured_image_id=None):
    """Create a WordPress post."""
    url = f"{WP_URL}/posts"
    payload = {
        "title": title,
        "content": content,
        "slug": slug,
        "status": "publish",
        "categories": [CATEGORY_ID],
    }
    if featured_image_id:
        payload["featured_media"] = featured_image_id
    resp = api_call("post", url, auth=WP_AUTH, json=payload)
    if resp and resp.status_code == 201:
        data = resp.json()
        return data.get("id"), data.get("link", "")
    else:
        print(f"  Post creation failed: {resp.status_code if resp else 'No response'}")
        if resp:
            print(f"  Response: {resp.text[:500]}")
    return None, None


# ─── Internal links pool ───
INTERNAL_LINKS = [
    ("https://pethubonline.com/how-to-keep-indoor-cats-mentally-stimulated/", "keeping indoor cats mentally stimulated"),
    ("https://pethubonline.com/best-window-perches-for-indoor-cats-uk/", "best window perches for indoor cats"),
    ("https://pethubonline.com/indoor-cat-exercise-creative-ways-to-keep-cats-active/", "indoor cat exercise ideas"),
    ("https://pethubonline.com/how-to-create-a-cat-safe-indoor-garden/", "creating a cat-safe indoor garden"),
    ("https://pethubonline.com/best-cat-trees-for-small-flats-uk/", "best cat trees for small flats"),
    ("https://pethubonline.com/indoor-cat-nutrition-do-indoor-cats-need-different-food/", "indoor cat nutrition guide"),
    ("https://pethubonline.com/how-to-prevent-obesity-in-indoor-cats/", "preventing obesity in indoor cats"),
    ("https://pethubonline.com/indoor-cat-litter-tray-guide-types-and-placement/", "indoor cat litter tray guide"),
    ("https://pethubonline.com/how-to-introduce-a-second-cat-to-an-indoor-home/", "introducing a second cat"),
    ("https://pethubonline.com/indoor-cat-safety-common-household-hazards/", "common household hazards for cats"),
    ("https://pethubonline.com/best-interactive-toys-for-indoor-cats-uk/", "best interactive toys for indoor cats"),
    ("https://pethubonline.com/how-to-help-indoor-cats-cope-with-boredom/", "helping indoor cats cope with boredom"),
    ("https://pethubonline.com/indoor-cat-grooming-routine-complete-guide/", "indoor cat grooming routine"),
    ("https://pethubonline.com/how-to-set-up-a-catio-for-your-indoor-cat/", "setting up a catio"),
    ("https://pethubonline.com/indoor-cat-behaviour-understanding-your-house-cat/", "understanding indoor cat behaviour"),
    ("https://pethubonline.com/best-scratching-posts-for-indoor-cats-uk/", "best scratching posts for indoor cats"),
    ("https://pethubonline.com/how-to-create-vertical-space-for-indoor-cats/", "creating vertical space for cats"),
    ("https://pethubonline.com/indoor-cat-health-checks-what-to-watch-for/", "indoor cat health checks"),
    ("https://pethubonline.com/how-to-transition-an-outdoor-cat-to-indoor-living/", "transitioning outdoor cats indoors"),
    ("https://pethubonline.com/indoor-cat-sleep-patterns-normal-vs-concerning/", "indoor cat sleep patterns"),
    ("https://pethubonline.com/best-harnesses-for-indoor-cats-who-want-to-explore/", "best harnesses for indoor cats"),
]


def get_internal_links(current_index, count=3):
    """Get internal links excluding the current post."""
    links = []
    candidates = [l for i, l in enumerate(INTERNAL_LINKS) if i != current_index]
    # Pick spread-out links
    step = max(1, len(candidates) // count)
    for i in range(0, len(candidates), step):
        if len(links) >= count:
            break
        links.append(candidates[i])
    return links


def amazon_link(asin, text):
    """Generate Amazon UK affiliate link."""
    return f'<a href="https://www.amazon.co.uk/dp/{asin}?tag={AMAZON_TAG}" target="_blank" rel="nofollow noopener">{text}</a>'


# ─── Post Content Generators ───

def generate_post_content(index, title, slug):
    """Generate full HTML content for each post."""
    links = get_internal_links(index)
    internal_html = "\n".join([f'<p>You might also enjoy our guide on <a href="{url}">{text}</a>.</p>' for url, text in links])

    # Each post generator returns (content, pexels_query)
    generators = {
        0: gen_mental_stimulation,
        1: gen_window_perches,
        2: gen_exercise,
        3: gen_indoor_garden,
        4: gen_cat_trees,
        5: gen_nutrition,
        6: gen_obesity,
        7: gen_litter_tray,
        8: gen_second_cat,
        9: gen_safety,
        10: gen_interactive_toys,
        11: gen_boredom,
        12: gen_grooming,
        13: gen_catio,
        14: gen_behaviour,
        15: gen_scratching_posts,
        16: gen_vertical_space,
        17: gen_health_checks,
        18: gen_transition,
        19: gen_sleep_patterns,
        20: gen_harnesses,
    }

    content, pexels_query = generators[index](title, slug, internal_html)
    return content, pexels_query


# ─── Shared HTML builders ───

def quick_answer_box(text):
    return f'''<div style="border-left: 4px solid #4CAF50; background: #f9fff9; padding: 16px 20px; margin-bottom: 24px; border-radius: 4px;">
<strong>Quick Answer:</strong> {text}
</div>'''

def toc_block(sections):
    items = "\n".join([f'<li><a href="#{s[0]}">{s[1]}</a></li>' for s in sections])
    return f'''<div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 28px;">
<strong>Table of Contents</strong>
<ol>{items}</ol>
</div>'''

def faq_section(faqs, slug):
    faq_html = ""
    schema_items = []
    for q, a in faqs:
        faq_html += f'''<div style="margin-bottom: 16px;">
<h3 style="margin-bottom: 6px;">{q}</h3>
<p>{a}</p>
</div>
'''
        schema_items.append(f'{{"@type":"Question","name":"{q.replace(chr(34), chr(39))}","acceptedAnswer":{{"@type":"Answer","text":"{a.replace(chr(34), chr(39))}"}}}}')

    schema = f'''<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{",".join(schema_items)}]}}
</script>'''

    return f'''<h2 id="faq">Frequently Asked Questions</h2>
{faq_html}
{schema}'''

def sources_section():
    return '''<h2 id="sources">Sources &amp; References</h2>
<ul>
<li><a href="https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/cats" target="_blank" rel="noopener">PDSA &ndash; Cat Care Advice</a></li>
<li><a href="https://www.rspca.org.uk/adviceandwelfare/pets/cats" target="_blank" rel="noopener">RSPCA &ndash; Cat Welfare</a></li>
<li><a href="https://www.bluecross.org.uk/pet-advice/cats" target="_blank" rel="noopener">Blue Cross &ndash; Cat Advice</a></li>
<li><a href="https://www.cats.org.uk/help-and-advice" target="_blank" rel="noopener">Cats Protection &ndash; Help &amp; Advice</a></li>
<li><a href="https://icatcare.org/advice/" target="_blank" rel="noopener">International Cat Care &ndash; Cat Advice</a></li>
</ul>'''

def author_box():
    return '''<div style="background: #f0f4f8; padding: 20px; border-radius: 8px; margin-top: 32px; margin-bottom: 20px;">
<strong>Written by the PetHub Online editorial team</strong> &mdash; Bringing you well-researched, practical pet care guides to help you and your feline companions thrive.
</div>'''

def cta_block():
    return '''<div style="background: #e8f5e9; padding: 20px; border-radius: 8px; text-align: center; margin: 24px 0;">
<strong>Explore more indoor cat guides on <a href="https://pethubonline.com/category/indoor-cats/">PetHub Online</a></strong>
</div>'''

def affiliate_disclosure():
    return '''<p style="font-size: 0.85em; color: #666; margin-top: 24px; padding: 12px; background: #fafafa; border-radius: 4px;"><em>Affiliate Disclosure: This post contains affiliate links. If you make a purchase through these links, we may earn a small commission at no extra cost to you. This helps support PetHub Online and allows us to continue creating helpful content for pet owners.</em></p>'''

def glossary_section(terms):
    items = "\n".join([f"<li><strong>{t}:</strong> {d}</li>" for t, d in terms])
    return f'''<h2 id="glossary">Key Terms / Glossary</h2>
<ul>{items}</ul>'''

def products_section(products, section_id="products"):
    """products: list of (asin, name, desc, price_approx)"""
    cards = ""
    for asin, name, desc, price in products:
        link = f"https://www.amazon.co.uk/dp/{asin}?tag={AMAZON_TAG}"
        cards += f'''<div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
<h3 style="margin-top: 0;"><a href="{link}" target="_blank" rel="nofollow noopener">{name}</a></h3>
<p>{desc}</p>
<p><strong>Approximate price:</strong> {price}</p>
<a href="{link}" target="_blank" rel="nofollow noopener" style="display: inline-block; background: #ff9900; color: #fff; padding: 10px 20px; border-radius: 4px; text-decoration: none; font-weight: bold;">Check Price on Amazon UK</a>
</div>
'''
    return f'''<h2 id="{section_id}">Recommended Products</h2>
{cards}'''

def comparison_table(headers, rows):
    """headers: list of strings. rows: list of lists."""
    th = "".join([f"<th style='padding: 10px; border: 1px solid #ddd; background: #f5f5f5;'>{h}</th>" for h in headers])
    body = ""
    for row in rows:
        cells = "".join([f"<td style='padding: 10px; border: 1px solid #ddd;'>{c}</td>" for c in row])
        body += f"<tr>{cells}</tr>\n"
    return f'''<h2 id="comparison">Product Comparison</h2>
<div style="overflow-x: auto;">
<table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
<thead><tr>{th}</tr></thead>
<tbody>{body}</tbody>
</table>
</div>'''


# ─── Individual Post Generators ───
# Each returns (html_content, pexels_search_query)

def gen_mental_stimulation(title, slug, internal_html):
    qa = quick_answer_box("Indoor cats need daily mental stimulation through puzzle feeders, interactive play sessions, window watching spots, and rotating toys. Aim for at least two 15-minute interactive play sessions per day to keep your indoor cat happy and healthy.")
    toc = toc_block([
        ("why-stimulation", "Why Do Indoor Cats Need Mental Stimulation?"),
        ("signs", "Signs Your Indoor Cat Is Understimulated"),
        ("enrichment-ideas", "10 Enrichment Ideas for Indoor Cats"),
        ("products", "Recommended Products"),
        ("comparison", "Product Comparison"),
        ("glossary", "Key Terms / Glossary"),
        ("faq", "Frequently Asked Questions"),
        ("sources", "Sources & References"),
    ])
    body = f'''{qa}
{toc}

<h2 id="why-stimulation">Why Do Indoor Cats Need Mental Stimulation?</h2>
<p>Indoor cats lack the natural stimulation that outdoor environments provide &mdash; hunting, exploring territory, climbing trees, and encountering new scents. Without adequate mental enrichment, indoor cats can develop behavioural problems including over-grooming, aggression, excessive vocalisation, and depression.</p>
<p>According to Cats Protection, environmental enrichment is one of the most important aspects of indoor cat care. A mentally stimulated cat is a healthier, calmer, and more contented companion.</p>

<h2 id="signs">What Are the Signs Your Indoor Cat Is Understimulated?</h2>
<ul>
<li><strong>Over-grooming</strong> &mdash; Excessive licking leading to bald patches</li>
<li><strong>Destructive behaviour</strong> &mdash; Scratching furniture, knocking items off surfaces</li>
<li><strong>Weight gain</strong> &mdash; Eating out of boredom rather than hunger</li>
<li><strong>Lethargy</strong> &mdash; Sleeping far more than the typical 12-16 hours</li>
<li><strong>Aggression</strong> &mdash; Biting or swatting at owners unprovoked</li>
<li><strong>Excessive meowing</strong> &mdash; Vocalising for attention or out of frustration</li>
</ul>

<h2 id="enrichment-ideas">What Are the Best Enrichment Ideas for Indoor Cats?</h2>
<h3>1. Puzzle Feeders</h3>
<p>Puzzle feeders make your cat work for their food, mimicking the mental challenge of hunting. Start with easy puzzles and gradually increase difficulty as your cat becomes more confident.</p>

<h3>2. Interactive Play Sessions</h3>
<p>Use wand toys, feather teasers, and laser pointers (always end with a physical toy to catch) for at least two 15-minute sessions daily. Vary the movements to simulate prey behaviour.</p>

<h3>3. Window Watching Stations</h3>
<p>Set up a comfortable perch near a window with a bird feeder outside. This provides hours of natural entertainment &mdash; often called &ldquo;cat TV.&rdquo;</p>

<h3>4. Rotation of Toys</h3>
<p>Keep 5-6 toys out at a time and rotate them weekly. Cats lose interest in familiar toys, so rotation keeps things fresh without constant spending.</p>

<h3>5. Cardboard Boxes and Paper Bags</h3>
<p>Simple and free enrichment. Cats love exploring enclosed spaces. Cut holes in boxes to create tunnels and hideaways.</p>

<h3>6. Catnip and Silver Vine</h3>
<p>About 50-70% of cats respond to catnip. Silver vine (Actinidia polygama) affects a broader range of cats and can provide 20-30 minutes of stimulated play.</p>

<h3>7. Training Sessions</h3>
<p>Yes, cats can be trained! Using positive reinforcement (treats and clicker training), you can teach your cat to sit, high-five, and even navigate agility courses.</p>

<h3>8. Cat-Safe Plants</h3>
<p>Cat grass (wheatgrass), catnip plants, and valerian provide safe sensory enrichment. Always check the ASPCA toxic plants list before introducing new plants.</p>

<h3>9. Elevated Spaces</h3>
<p>Cat shelves, tall cat trees, and wall-mounted walkways give cats vertical territory to explore and survey their domain from above.</p>

<h3>10. Scent Enrichment</h3>
<p>Hide treats around the house for your cat to sniff out. You can also bring in safe outdoor scents &mdash; a pinecone or a handful of leaves &mdash; for your cat to investigate.</p>

{products_section([
    ("B08GC4P4GP", "Catit Senses 2.0 Digger", "Interactive puzzle feeder that encourages natural pawing behaviour. Multiple difficulty levels suit beginners and experienced puzzle solvers.", "~£12"),
    ("B0006N9I68", "KONG Active Feather Teaser", "Classic wand toy with feathers that mimics bird movements. Durable and replaceable attachments.", "~£5"),
    ("B07V3CPFTM", "PetFusion Ambush Interactive Cat Toy", "Electronic toy with unpredictable feather movements that keeps cats engaged even when you are away.", "~£25"),
    ("B00D3NI2PG", "Trixie 5-in-1 Activity Centre", "Multi-function puzzle board with five different modules to challenge your cat mentally.", "~£15"),
])}

{comparison_table(
    ["Product", "Type", "Best For", "Difficulty", "Approx. Price"],
    [
        [f'<a href="https://www.amazon.co.uk/dp/B08GC4P4GP?tag={AMAZON_TAG}" rel="nofollow noopener">Catit Digger</a>', "Puzzle Feeder", "Meal times", "Beginner-Intermediate", "~£12"],
        [f'<a href="https://www.amazon.co.uk/dp/B0006N9I68?tag={AMAZON_TAG}" rel="nofollow noopener">KONG Feather Teaser</a>', "Wand Toy", "Interactive play", "N/A", "~£5"],
        [f'<a href="https://www.amazon.co.uk/dp/B07V3CPFTM?tag={AMAZON_TAG}" rel="nofollow noopener">PetFusion Ambush</a>', "Electronic Toy", "Solo play", "N/A", "~£25"],
        [f'<a href="https://www.amazon.co.uk/dp/B00D3NI2PG?tag={AMAZON_TAG}" rel="nofollow noopener">Trixie Activity Centre</a>', "Puzzle Board", "Problem solving", "Intermediate", "~£15"],
    ]
)}

{glossary_section([
    ("Environmental enrichment", "Modifications to an animal's environment that provide mental and physical stimulation"),
    ("Puzzle feeder", "A device that requires a cat to work or solve a problem to access food"),
    ("Silver vine", "A plant (Actinidia polygama) that produces a euphoric response in cats, similar to catnip"),
    ("Clicker training", "A positive reinforcement training method using a clicking sound to mark desired behaviour"),
    ("Vertical territory", "Elevated spaces such as shelves and cat trees that cats use for security and observation"),
])}

{faq_section([
    ("How many hours a day should I play with my indoor cat?", "Aim for at least 30 minutes of interactive play spread across two or more sessions. Some high-energy breeds may benefit from 45-60 minutes of daily play."),
    ("Do puzzle feeders really help indoor cats?", "Yes. Puzzle feeders engage your cat's natural hunting instincts and slow down eating, which reduces boredom, prevents obesity, and provides mental stimulation."),
    ("Can old cats benefit from mental stimulation?", "Absolutely. Senior cats still need mental enrichment, though you may need to adjust activities to suit their mobility. Gentle puzzle feeders and scent games work well for older cats."),
    ("Is it cruel to keep a cat indoors?", "Not if their environment is properly enriched. Many cat welfare organisations, including Cats Protection, state that indoor cats can live happy, healthy lives with appropriate stimulation and care."),
    ("What is the best toy for an indoor cat?", "Wand toys with feathers or string attachments are consistently rated as the most engaging interactive toys by cat behaviourists, as they best mimic prey movement."),
], slug)}

{sources_section()}

{internal_html}

{author_box()}
{cta_block()}
{affiliate_disclosure()}'''
    return body, "cat playing toy indoors"


def gen_window_perches(title, slug, internal_html):
    qa = quick_answer_box("The best window perches for indoor cats in the UK provide a sturdy, comfortable spot for your cat to watch the outside world. Look for perches with strong suction cups or bracket mounts rated for your cat's weight, with a washable cushion cover for easy cleaning.")
    toc = toc_block([
        ("why-perches", "Why Do Indoor Cats Need Window Perches?"),
        ("choosing", "How to Choose the Right Window Perch"),
        ("top-picks", "Top Window Perches for Indoor Cats UK"),
        ("products", "Recommended Products"),
        ("comparison", "Product Comparison"),
        ("installation", "Installation Tips"),
        ("glossary", "Key Terms / Glossary"),
        ("faq", "Frequently Asked Questions"),
        ("sources", "Sources & References"),
    ])
    body = f'''{qa}
{toc}

<h2 id="why-perches">Why Do Indoor Cats Need Window Perches?</h2>
<p>Window perches serve a dual purpose for indoor cats: they provide essential environmental enrichment through outdoor observation, and they offer a comfortable elevated resting spot that satisfies a cat's natural desire for vertical territory.</p>
<p>Cats Protection notes that watching birds, wildlife, and passing activity through windows can provide hours of mental stimulation for indoor cats. A dedicated window perch makes this activity comfortable and accessible.</p>

<h2 id="choosing">How Do You Choose the Right Window Perch?</h2>
<p>Consider these factors when selecting a window perch for your indoor cat:</p>
<ul>
<li><strong>Weight capacity</strong> &mdash; Ensure the perch supports your cat's weight with a safety margin. Most quality perches support 10-25 kg.</li>
<li><strong>Mounting type</strong> &mdash; Suction cup perches are easy to install but need smooth glass. Bracket-mounted or shelf-style perches are more permanent and often sturdier.</li>
<li><strong>Window size</strong> &mdash; Measure your window before purchasing. Some perches require specific minimum window widths.</li>
<li><strong>Comfort</strong> &mdash; Look for padded, machine-washable covers. Cats will use the perch more if it is genuinely comfortable.</li>
<li><strong>Durability</strong> &mdash; Read reviews regarding suction cup longevity. Temperature changes can affect suction over time.</li>
</ul>

<h2 id="top-picks">What Are the Top Window Perches for Indoor Cats in the UK?</h2>
<p>After researching the most popular options available to UK cat owners, here are our top picks based on customer reviews, weight capacity, and value for money:</p>

<h3>Suction Cup Perches</h3>
<p>These attach directly to glass with industrial-strength suction cups. Best for renters or anyone who does not want to drill into window frames.</p>

<h3>Bracket-Mounted Perches</h3>
<p>These screw into the wall or window frame. They are the most stable option and ideal for heavier cats or multi-cat households.</p>

<h3>Radiator Perches</h3>
<p>Popular in the UK where radiators are commonly positioned beneath windows. These hook onto your radiator and provide a warm, elevated viewing spot.</p>

{products_section([
    ("B073WBX7BM", "ZALALOVA Cat Window Perch", "Heavy-duty suction cup perch supporting up to 22 kg. Features a cosy fleece cover and reinforced cable for extra safety.", "~£18"),
    ("B0BLF4NHXT", "Pecute Cat Window Hammock", "Space-saving hammock design with four large suction cups. Machine-washable cover included. Supports up to 18 kg.", "~£16"),
    ("B01CQGZ074", "K&H Pet Products EZ Mount Window Bed", "Premium single-pane window perch with a quilted sleeping surface. Supports up to 22 kg with reinforced suction.", "~£35"),
    ("B09B28MKC3", "Zooplus Cat Radiator Bed", "Hooks onto standard UK radiators for a warm window-adjacent perch. Soft plush cover is removable and washable.", "~£15"),
])}

{comparison_table(
    ["Product", "Mount Type", "Weight Limit", "Washable Cover", "Approx. Price"],
    [
        [f'<a href="https://www.amazon.co.uk/dp/B073WBX7BM?tag={AMAZON_TAG}" rel="nofollow noopener">ZALALOVA Perch</a>', "Suction Cup", "22 kg", "Yes", "~£18"],
        [f'<a href="https://www.amazon.co.uk/dp/B0BLF4NHXT?tag={AMAZON_TAG}" rel="nofollow noopener">Pecute Hammock</a>', "Suction Cup", "18 kg", "Yes", "~£16"],
        [f'<a href="https://www.amazon.co.uk/dp/B01CQGZ074?tag={AMAZON_TAG}" rel="nofollow noopener">K&H EZ Mount</a>', "Suction Cup", "22 kg", "Yes", "~£35"],
        [f'<a href="https://www.amazon.co.uk/dp/B09B28MKC3?tag={AMAZON_TAG}" rel="nofollow noopener">Zooplus Radiator Bed</a>', "Radiator Hook", "8 kg", "Yes", "~£15"],
    ]
)}

<h2 id="installation">How Do You Install a Window Perch Safely?</h2>
<ul>
<li>Clean the window glass thoroughly with rubbing alcohol before applying suction cups</li>
<li>Test the perch with gentle weight before allowing your cat to use it</li>
<li>Re-press suction cups every few weeks to maintain grip</li>
<li>Avoid installing on double-glazed windows that flex under pressure</li>
<li>Place a soft landing zone below the perch just in case</li>
</ul>

{glossary_section([
    ("Window perch", "A cat bed or platform designed to attach to or near a window, giving cats an elevated viewing spot"),
    ("Suction cup mount", "An attachment method using vacuum-sealed cups on smooth glass surfaces"),
    ("Vertical territory", "Elevated spaces cats use for security, rest, and environmental observation"),
    ("Radiator perch", "A hammock-style bed that hooks onto household radiators near windows"),
    ("Environmental enrichment", "Modifications to an indoor space that improve an animal's quality of life"),
])}

{faq_section([
    ("Are suction cup cat perches safe?", "Quality suction cup perches are generally safe when properly installed on clean, smooth glass. Always check the weight rating exceeds your cat's weight and re-secure cups regularly."),
    ("Will a window perch damage my windows?", "Suction cup perches should not damage glass. Bracket-mounted perches may leave small screw holes in the frame or wall."),
    ("Can two cats share a window perch?", "Most standard perches are designed for one cat. For multi-cat households, install multiple perches or choose an extra-wide model rated for combined weight."),
    ("How do I get my cat to use a window perch?", "Place treats or catnip on the perch initially. Position it near a window with good outdoor views. Most cats will start using it within a few days once they feel it is stable."),
    ("Do window perches work on double glazing?", "Most suction cup perches work on double-glazed windows, but some thinner panes may flex. Test stability carefully before allowing your cat to use it."),
], slug)}

{sources_section()}

{internal_html}

{author_box()}
{cta_block()}
{affiliate_disclosure()}'''
    return body, "cat sitting window perch"


def gen_exercise(title, slug, internal_html):
    qa = quick_answer_box("Indoor cats need at least 30 minutes of active exercise daily to maintain a healthy weight and prevent behavioural issues. Use interactive wand toys, laser pointers, cat wheels, tunnel systems, and structured play sessions to keep your indoor cat physically fit.")
    toc = toc_block([
        ("why-exercise", "Why Is Exercise Important for Indoor Cats?"),
        ("how-much", "How Much Exercise Do Indoor Cats Need?"),
        ("creative-ideas", "Creative Exercise Ideas for Indoor Cats"),
        ("products", "Recommended Products"),
        ("comparison", "Product Comparison"),
        ("glossary", "Key Terms / Glossary"),
        ("faq", "Frequently Asked Questions"),
        ("sources", "Sources & References"),
    ])
    body = f'''{qa}
{toc}

<h2 id="why-exercise">Why Is Exercise Important for Indoor Cats?</h2>
<p>Indoor cats are at higher risk of obesity, with the PDSA estimating that around 46% of UK cats are overweight or obese. Without the natural exercise of hunting and territory patrol, indoor cats must have structured physical activity to stay healthy.</p>
<p>Regular exercise helps prevent obesity, reduces the risk of diabetes and joint problems, supports digestive health, and reduces stress-related behaviours such as over-grooming or aggression.</p>

<h2 id="how-much">How Much Exercise Do Indoor Cats Need Each Day?</h2>
<p>Most cat behaviourists recommend at least 30 minutes of active play per day, split into two or three shorter sessions. Kittens and young adults may need more &mdash; up to 45-60 minutes &mdash; while senior cats may do well with two gentle 10-minute sessions.</p>
<p>The key is consistency: daily short sessions are far better than occasional long play periods.</p>

<h2 id="creative-ideas">What Are the Best Creative Exercise Ideas for Indoor Cats?</h2>

<h3>1. Wand Toy Chase Games</h3>
<p>Drag wand toys along the floor, up walls, and over furniture to simulate prey behaviour. Vary speed and direction to keep your cat engaged. Always let your cat "catch" the toy periodically to prevent frustration.</p>

<h3>2. Cat Exercise Wheels</h3>
<p>Similar to hamster wheels but cat-sized, these allow cats to run at their own pace. They are particularly popular with active breeds like Bengals and Abyssinians.</p>

<h3>3. Tunnel Systems</h3>
<p>Crinkle tunnels and pop-up play tunnels encourage running, stalking, and pouncing. Connect multiple tunnels for a more complex circuit.</p>

<h3>4. Staircase Sprints</h3>
<p>If you have stairs, toss a toy up or down to encourage your cat to sprint between floors. This provides excellent cardiovascular exercise.</p>

<h3>5. Fetch (Yes, Really)</h3>
<p>Some cats naturally retrieve toys. If yours does, take advantage of it &mdash; scrunch up a paper ball or use a small soft toy and toss it down a hallway.</p>

<h3>6. Obstacle Courses</h3>
<p>Use cushions, boxes, and low furniture to create a mini agility course. Lead your cat through with a wand toy or treats.</p>

<h3>7. Food Scatter Games</h3>
<p>Scatter a portion of your cat's daily kibble across a room or hide it in puzzle feeders. This combines mental and physical exercise as your cat hunts for food.</p>

<h3>8. Laser Pointer Sessions</h3>
<p>Use a laser pointer to create fast, unpredictable movements across floors and walls. Always end the session by directing the laser to a physical toy or treat so your cat gets the satisfaction of a "catch."</p>

{products_section([
    ("B0CB7R41QC", "One Fast Cat Exercise Wheel", "Cat-sized running wheel with padded surface. Ideal for high-energy indoor cats. Diameter 120 cm for natural running posture.", "~£300"),
    ("B000IYSAIW", "Da Bird Cat Toy", "Premium feather wand that spins and sounds like a real bird in flight. Considered the gold standard of interactive cat toys by many owners.", "~£8"),
    ("B07QP8K94Y", "Catit Play Senses Circuit", "Ball-in-track toy that encourages batting and chasing. Modular design can be extended with add-on packs.", "~£10"),
    ("B07YJQHHGV", "SmartyKat Hot Pursuit", "Electronic concealed-motion toy that simulates prey hiding under fabric. Adjustable speed settings.", "~£18"),
])}

{comparison_table(
    ["Product", "Exercise Type", "Supervised?", "Best For", "Approx. Price"],
    [
        [f'<a href="https://www.amazon.co.uk/dp/B0CB7R41QC?tag={AMAZON_TAG}" rel="nofollow noopener">Cat Exercise Wheel</a>', "Cardio Running", "No", "High-energy breeds", "~£300"],
        [f'<a href="https://www.amazon.co.uk/dp/B000IYSAIW?tag={AMAZON_TAG}" rel="nofollow noopener">Da Bird</a>', "Chase/Pounce", "Yes", "All cats", "~£8"],
        [f'<a href="https://www.amazon.co.uk/dp/B07QP8K94Y?tag={AMAZON_TAG}" rel="nofollow noopener">Catit Circuit</a>', "Batting/Pawing", "No", "Gentle exercise", "~£10"],
        [f'<a href="https://www.amazon.co.uk/dp/B07YJQHHGV?tag={AMAZON_TAG}" rel="nofollow noopener">SmartyKat Hot Pursuit</a>', "Stalking/Pouncing", "No", "Solo play", "~£18"],
    ]
)}

{glossary_section([
    ("Interactive play", "Play sessions that involve direct human participation using toys to simulate prey behaviour"),
    ("Cat exercise wheel", "A large wheel that allows cats to walk or run at their own pace, similar to a hamster wheel"),
    ("Prey simulation", "Moving toys in patterns that mimic the movements of birds, mice, or insects to trigger hunting instincts"),
    ("Enrichment circuit", "A connected series of tunnels, obstacles, or tracks that encourage cats to move through a defined path"),
    ("Play-rest cycle", "The natural pattern of short bursts of intense activity followed by rest periods, typical of feline behaviour"),
])}

{faq_section([
    ("How do I know if my indoor cat is getting enough exercise?", "A well-exercised cat maintains a healthy weight, sleeps well at night, shows no destructive behaviours, and has regular, firm stools. Your vet can help assess your cat's body condition score."),
    ("Is a cat exercise wheel worth the money?", "For high-energy breeds or cats that enjoy running, an exercise wheel can be an excellent investment. However, not all cats will take to one, so look for sellers with a good return policy."),
    ("Can indoor cats exercise on their own?", "Cats can self-play with circuit toys, crinkle balls, and automated toys, but interactive play with a human provides the most effective exercise and strengthens your bond."),
    ("What time of day should I exercise my indoor cat?", "Cats are naturally crepuscular, meaning they are most active at dawn and dusk. Scheduling play sessions around these times aligns with their natural rhythm."),
    ("My cat is lazy. How do I motivate them to exercise?", "Start with very short sessions using high-value toys. Try different toy types to find what triggers your cat's prey drive. Slow, subtle movements often work better than fast, frantic ones for reluctant players."),
], slug)}

{sources_section()}

{internal_html}

{author_box()}
{cta_block()}
{affiliate_disclosure()}'''
    return body, "cat playing running indoors"


def gen_indoor_garden(title, slug, internal_html):
    qa = quick_answer_box("A cat-safe indoor garden uses only non-toxic plants such as cat grass, spider plants, Boston ferns, and catnip. Avoid lilies, aloe vera, and pothos, which are toxic to cats. Use elevated planters or hanging pots to control access to edible plants.")
    toc = toc_block([
        ("why-garden", "Why Create an Indoor Garden for Your Cat?"),
        ("safe-plants", "Which Plants Are Safe for Indoor Cats?"),
        ("toxic-plants", "Which Houseplants Are Toxic to Cats?"),
        ("setup", "How to Set Up a Cat-Safe Indoor Garden"),
        ("products", "Recommended Products"),
        ("comparison", "Product Comparison"),
        ("glossary", "Key Terms / Glossary"),
        ("faq", "Frequently Asked Questions"),
        ("sources", "Sources & References"),
    ])
    body = f'''{qa}
{toc}

<h2 id="why-garden">Why Create an Indoor Garden for Your Cat?</h2>
<p>Indoor gardens provide sensory enrichment for cats who lack access to the outdoors. Cats enjoy sniffing, nibbling, and rubbing against plants. Safe greenery can reduce stress, provide dietary fibre, and give cats a more natural-feeling environment.</p>
<p>The RSPCA recommends providing cat grass for indoor cats as it helps with digestion and hairball management, satisfying a natural grazing instinct.</p>

<h2 id="safe-plants">Which Plants Are Safe for Indoor Cats?</h2>
<ul>
<li><strong>Cat grass (wheatgrass)</strong> &mdash; Easy to grow, aids digestion, safe to nibble</li>
<li><strong>Catnip (Nepeta cataria)</strong> &mdash; Produces euphoric response in 50-70% of cats</li>
<li><strong>Spider plant (Chlorophytum comosum)</strong> &mdash; Non-toxic, resilient, and cats love the trailing leaves</li>
<li><strong>Boston fern (Nephrolepis exaltata)</strong> &mdash; Non-toxic and adds humidity to dry indoor air</li>
<li><strong>Parlour palm (Chamaedorea elegans)</strong> &mdash; Safe and adds a tropical feel</li>
<li><strong>African violet (Saintpaulia)</strong> &mdash; Non-toxic and adds colour</li>
<li><strong>Valerian (Valeriana officinalis)</strong> &mdash; Stimulating for cats, similar to catnip</li>
<li><strong>Silver vine (Actinidia polygama)</strong> &mdash; Strong response in cats, safe to grow indoors</li>
</ul>

<h2 id="toxic-plants">Which Houseplants Are Toxic to Cats?</h2>
<p>The following common houseplants are <strong>dangerous</strong> and should be completely avoided in homes with cats:</p>
<ul>
<li><strong>Lilies (Lilium spp.)</strong> &mdash; Extremely toxic; even small amounts can cause fatal kidney failure</li>
<li><strong>Aloe vera</strong> &mdash; Causes vomiting and diarrhoea</li>
<li><strong>Pothos (Devil's ivy)</strong> &mdash; Causes oral irritation and swelling</li>
<li><strong>Dieffenbachia (Dumb cane)</strong> &mdash; Causes intense oral pain and drooling</li>
<li><strong>Snake plant (Sansevieria)</strong> &mdash; Causes nausea and vomiting</li>
<li><strong>Peace lily (Spathiphyllum)</strong> &mdash; Causes oral irritation, drooling, vomiting</li>
<li><strong>Philodendron</strong> &mdash; Contains calcium oxalate crystals harmful to cats</li>
</ul>
<p>If you suspect your cat has ingested a toxic plant, contact your vet immediately. The Cats Protection and ASPCA both maintain comprehensive toxic plant lists.</p>

<h2 id="setup">How Do You Set Up a Cat-Safe Indoor Garden?</h2>
<ol>
<li><strong>Choose your space</strong> &mdash; A sunny windowsill, shelving unit, or dedicated corner works well</li>
<li><strong>Use organic soil</strong> &mdash; Avoid chemical fertilisers and pesticides that could harm your cat</li>
<li><strong>Elevate decorative plants</strong> &mdash; Use hanging planters or high shelves for plants you do not want chewed</li>
<li><strong>Make a cat grazing station</strong> &mdash; Place cat grass and catnip at cat height for easy access</li>
<li><strong>Protect soil</strong> &mdash; Cover soil with decorative stones to stop cats digging in pots</li>
<li><strong>Drainage trays</strong> &mdash; Ensure standing water in trays does not accumulate, as some cats drink from them</li>
</ol>

{products_section([
    ("B09BFYDSLX", "Cat Grass Growing Kit (3-Pack)", "Organic wheatgrass seeds with self-watering pots. Ready to nibble in 5-7 days. Perfect for indoor cats.", "~£10"),
    ("B07L3N7BLB", "Catit Senses 2.0 Grass Planter", "Designed specifically for cats with an integrated vermiculite growing medium. No soil mess.", "~£8"),
    ("B0CLLVZ8XJ", "Wall-Mounted Hanging Planters (Set of 3)", "Stylish ceramic wall planters that keep decorative plants safely out of reach while adding greenery to your home.", "~£20"),
    ("B08HCM6SJ4", "Organic Catnip Seeds", "Grow your own catnip from seed. Includes planting instructions. Multiple harvests from a single sowing.", "~£5"),
])}

{comparison_table(
    ["Product", "Type", "Cat Accessible", "Grow Time", "Approx. Price"],
    [
        [f'<a href="https://www.amazon.co.uk/dp/B09BFYDSLX?tag={AMAZON_TAG}" rel="nofollow noopener">Cat Grass Kit</a>', "Edible Grass", "Yes", "5-7 days", "~£10"],
        [f'<a href="https://www.amazon.co.uk/dp/B07L3N7BLB?tag={AMAZON_TAG}" rel="nofollow noopener">Catit Grass Planter</a>', "Edible Grass", "Yes", "5-7 days", "~£8"],
        [f'<a href="https://www.amazon.co.uk/dp/B0CLLVZ8XJ?tag={AMAZON_TAG}" rel="nofollow noopener">Wall Hanging Planters</a>', "Display Only", "No", "N/A", "~£20"],
        [f'<a href="https://www.amazon.co.uk/dp/B08HCM6SJ4?tag={AMAZON_TAG}" rel="nofollow noopener">Catnip Seeds</a>', "Edible/Stimulating", "Yes", "10-14 days", "~£5"],
    ]
)}

{glossary_section([
    ("Cat grass", "Typically wheatgrass or barley grass grown specifically for cats to nibble on, aiding digestion"),
    ("Catnip", "A herb from the mint family (Nepeta cataria) that produces a euphoric response in many cats"),
    ("ASPCA Toxic Plant List", "A comprehensive database maintained by the American Society for the Prevention of Cruelty to Animals listing plants harmful to pets"),
    ("Calcium oxalate", "A chemical compound found in many houseplants that causes pain and swelling when chewed by cats"),
    ("Silver vine", "A climbing plant native to East Asia that produces strong behavioural responses in cats"),
])}

{faq_section([
    ("Is cat grass the same as lawn grass?", "No. Cat grass typically refers to wheatgrass, barley grass, or oat grass grown specifically for cats. Lawn grass may contain pesticides and is not suitable."),
    ("Can cats eat spider plants?", "Spider plants are non-toxic to cats. Some cats enjoy chewing the leaves, which may cause mild stomach upset but is not dangerous."),
    ("How do I stop my cat eating my houseplants?", "Provide appealing alternatives like cat grass and catnip. Use citrus-scented sprays on plants you want to protect, as most cats dislike citrus. Move toxic plants out of reach entirely."),
    ("Are essential oils safe for cats in an indoor garden?", "No. Many essential oils are toxic to cats. Avoid using them near indoor gardens or in diffusers in rooms your cat frequents."),
    ("How often should I replace cat grass?", "Cat grass typically lasts 2-3 weeks before it starts to yellow. Keep a rotation of pots growing so fresh grass is always available."),
], slug)}

{sources_section()}

{internal_html}

{author_box()}
{cta_block()}
{affiliate_disclosure()}'''
    return body, "cat sitting near green plants indoors"


def gen_cat_trees(title, slug, internal_html):
    qa = quick_answer_box("The best cat trees for small UK flats are tall, narrow designs that maximise vertical space without taking up too much floor area. Look for floor-to-ceiling tension poles, wall-mounted modular systems, or slim multi-tier towers under 50 cm wide.")
    toc = toc_block([
        ("why-cat-trees", "Why Do Indoor Cats Need Cat Trees?"),
        ("choosing-small", "How to Choose a Cat Tree for a Small Flat"),
        ("best-types", "Best Cat Tree Types for Limited Space"),
        ("products", "Recommended Products"),
        ("comparison", "Product Comparison"),
        ("glossary", "Key Terms / Glossary"),
        ("faq", "Frequently Asked Questions"),
        ("sources", "Sources & References"),
    ])
    body = f'''{qa}
{toc}

<h2 id="why-cat-trees">Why Do Indoor Cats Need Cat Trees?</h2>
<p>Cat trees provide essential vertical territory for indoor cats. In the wild, cats climb to survey their territory, escape threats, and rest safely above ground level. Indoor cats retain these instincts, and a cat tree satisfies their need for height, scratching surfaces, and private retreats.</p>
<p>International Cat Care recommends providing vertical spaces as a key part of indoor cat environmental enrichment, particularly in multi-cat households where territory disputes can arise.</p>

<h2 id="choosing-small">How Do You Choose a Cat Tree for a Small Flat?</h2>
<ul>
<li><strong>Footprint</strong> &mdash; Measure the available floor space. Aim for designs under 50 cm x 50 cm base</li>
<li><strong>Height</strong> &mdash; Taller is better for small spaces. Floor-to-ceiling poles maximise vertical space</li>
<li><strong>Stability</strong> &mdash; Taller trees need a heavier base or ceiling mounting. Check weight ratings</li>
<li><strong>Materials</strong> &mdash; Sisal-wrapped posts last longest. Carpet-covered platforms collect fur but are comfortable</li>
<li><strong>Multi-function</strong> &mdash; Choose trees that combine scratching posts, perches, and hideaways to save buying separate items</li>
</ul>

<h2 id="best-types">What Are the Best Cat Tree Types for Small Spaces?</h2>
<h3>Floor-to-Ceiling Tension Poles</h3>
<p>These use spring tension against the ceiling to stay upright, requiring minimal floor space. They typically include multiple platforms, sisal-wrapped poles, and sometimes hammocks.</p>

<h3>Wall-Mounted Modular Systems</h3>
<p>Individual shelves, steps, and perches mounted directly to the wall. Take up zero floor space and can be customised to any room layout.</p>

<h3>Slim Multi-Tier Towers</h3>
<p>Traditional cat trees with a narrow profile. Good for corners and alcoves where a standard cat tree would not fit.</p>

<h3>Corner Cat Trees</h3>
<p>Designed specifically to fit into room corners, these make use of otherwise wasted space.</p>

{products_section([
    ("B08YNCLDDZ", "FEANDREA Slim Cat Tower (143 cm)", "Narrow profile cat tree with 3 perches, sisal posts, and a cosy cave. Base just 40 x 40 cm. Ideal for small flats.", "~£45"),
    ("B09BFHG6FD", "Catit Vesper High Base", "Elegant compact cat tree with walnut-finish frame. MDF cube base with memory foam cushion. Footprint 56 x 56 cm.", "~£90"),
    ("B0882WPWJ5", "Go Pet Club 188 cm Floor-to-Ceiling Tree", "Tall tension pole design with multiple platforms. Minimal floor space, maximum vertical territory.", "~£55"),
    ("B07D58KYFN", "FUKUMARU Cat Wall Shelves (Set of 5)", "Wall-mounted steps and perches. Zero floor space used. Natural wood finish suits modern interiors.", "~£40"),
])}

{comparison_table(
    ["Product", "Type", "Height", "Footprint", "Approx. Price"],
    [
        [f'<a href="https://www.amazon.co.uk/dp/B08YNCLDDZ?tag={AMAZON_TAG}" rel="nofollow noopener">FEANDREA Slim Tower</a>', "Multi-tier", "143 cm", "40 x 40 cm", "~£45"],
        [f'<a href="https://www.amazon.co.uk/dp/B09BFHG6FD?tag={AMAZON_TAG}" rel="nofollow noopener">Catit Vesper</a>', "Compact Premium", "121 cm", "56 x 56 cm", "~£90"],
        [f'<a href="https://www.amazon.co.uk/dp/B0882WPWJ5?tag={AMAZON_TAG}" rel="nofollow noopener">Go Pet Club Pole</a>', "Ceiling Tension", "188-274 cm", "36 x 36 cm", "~£55"],
        [f'<a href="https://www.amazon.co.uk/dp/B07D58KYFN?tag={AMAZON_TAG}" rel="nofollow noopener">FUKUMARU Shelves</a>', "Wall-mounted", "Custom", "Zero floor", "~£40"],
    ]
)}

{glossary_section([
    ("Vertical territory", "Elevated space that cats use for observation, rest, and feeling secure"),
    ("Tension pole", "A floor-to-ceiling post held in place by spring pressure, requiring no drilling"),
    ("Sisal", "A natural fibre wrapped around scratching posts that is durable and satisfying for cats to scratch"),
    ("Cat tree", "A multi-level structure providing climbing, scratching, and resting spaces for cats"),
    ("Modular system", "Individual components that can be arranged and reconfigured to suit different spaces"),
])}

{faq_section([
    ("How tall should a cat tree be for a flat?", "As tall as your ceiling allows. Cats feel most secure at height, so floor-to-ceiling designs are ideal. Minimum recommended height is 120 cm."),
    ("Are wall-mounted cat shelves stable enough?", "Yes, when properly installed into wall studs or with appropriate wall anchors. Each shelf typically supports 10-15 kg."),
    ("How do I stop my cat tree from wobbling?", "Ensure the base is on a flat surface. Use anti-slip pads underneath. For tall trees, consider ceiling anchoring or wall brackets for extra stability."),
    ("Can two cats share one cat tree?", "Yes, but ensure the tree has multiple perches at different heights so both cats can find their preferred level. In multi-cat homes, having more than one tree is ideal."),
    ("How often should I replace a cat tree?", "A quality cat tree should last 3-5 years. Replace sisal posts when they become frayed and loose. Whole replacement is needed when the structure becomes unstable."),
], slug)}

{sources_section()}

{internal_html}

{author_box()}
{cta_block()}
{affiliate_disclosure()}'''
    return body, "cat tree small apartment"


def gen_nutrition(title, slug, internal_html):
    qa = quick_answer_box("Yes, indoor cats generally benefit from specially formulated indoor cat food that has fewer calories, more fibre, and added hairball control ingredients. Indoor cats are less active than outdoor cats and need around 20% fewer calories to avoid weight gain.")
    toc = toc_block([
        ("differences", "How Does Indoor Cat Nutrition Differ?"),
        ("calorie-needs", "How Many Calories Does an Indoor Cat Need?"),
        ("what-to-look-for", "What to Look for in Indoor Cat Food"),
        ("wet-vs-dry", "Wet vs Dry Food for Indoor Cats"),
        ("products", "Recommended Products"),
        ("comparison", "Product Comparison"),
        ("glossary", "Key Terms / Glossary"),
        ("faq", "Frequently Asked Questions"),
        ("sources", "Sources & References"),
    ])
    body = f'''{qa}
{toc}

<h2 id="differences">How Does Indoor Cat Nutrition Differ from Outdoor Cat Nutrition?</h2>
<p>Indoor cats have different nutritional needs compared to their outdoor counterparts. They are less active, burn fewer calories, and spend more time grooming, which increases hairball formation. Indoor-specific cat foods are formulated to address these differences.</p>
<p>The PDSA highlights that one of the biggest health risks for indoor cats is obesity. Feeding an appropriate diet is the first line of defence against weight-related health problems.</p>

<h2 id="calorie-needs">How Many Calories Does an Indoor Cat Need Per Day?</h2>
<p>A typical adult indoor cat needs approximately 20 calories per pound of body weight per day. For a 4 kg (8.8 lb) indoor cat, this works out to roughly 175-200 kcal per day. This is around 20% less than a similarly sized outdoor cat.</p>
<p>Key factors affecting calorie requirements include:</p>
<ul>
<li><strong>Age</strong> &mdash; Kittens need more calories; senior cats need fewer</li>
<li><strong>Activity level</strong> &mdash; More active indoor cats may need slightly more</li>
<li><strong>Neutering status</strong> &mdash; Neutered cats have lower metabolic rates</li>
<li><strong>Body condition</strong> &mdash; Overweight cats need calorie restriction under vet guidance</li>
</ul>

<h2 id="what-to-look-for">What Should You Look for in Indoor Cat Food?</h2>
<ul>
<li><strong>Lower calorie density</strong> &mdash; Reduced fat content to prevent weight gain</li>
<li><strong>Higher fibre</strong> &mdash; Promotes satiety and aids hairball passage</li>
<li><strong>Hairball control</strong> &mdash; Added fibre or lubricants to reduce hairball formation</li>
<li><strong>High-quality protein</strong> &mdash; Named meat sources (chicken, salmon, turkey) as the first ingredient</li>
<li><strong>L-carnitine</strong> &mdash; An amino acid that supports fat metabolism</li>
<li><strong>Moderate portion sizes</strong> &mdash; Pre-measured portions help prevent overfeeding</li>
</ul>

<h2 id="wet-vs-dry">Is Wet or Dry Food Better for Indoor Cats?</h2>
<p>A combination of both is often ideal. Wet food provides hydration (important since indoor cats may drink less) and is typically lower in calories per gram. Dry food supports dental health and can be used in puzzle feeders for enrichment.</p>
<p>Blue Cross recommends offering fresh water alongside food at all times, and many cat behaviourists suggest a water fountain to encourage drinking.</p>

{products_section([
    ("B003YQMMCU", "Royal Canin Indoor Cat Dry Food", "Specifically formulated for indoor cats with reduced calories and enhanced fibre for hairball control. Available in 2 kg and 4 kg bags.", "~£16 (2 kg)"),
    ("B0BFVF4CVN", "James Wellbeloved Indoor Cat Turkey", "UK-made natural indoor cat food with single-source turkey protein. No artificial colours, flavours, or preservatives.", "~£12 (1.5 kg)"),
    ("B07BFLHLSX", "Purina ONE Indoor Cat Rich in Turkey", "High-protein indoor formula with added fibre and natural prebiotics for digestive health.", "~£8 (800 g)"),
    ("B003XV22HW", "Hill's Science Plan Indoor Cat Chicken", "Clinically proven nutrition with controlled calorie content and natural fibre blend for indoor cats.", "~£18 (1.5 kg)"),
])}

{comparison_table(
    ["Product", "Protein Source", "Hairball Control", "Calorie Controlled", "Approx. Price"],
    [
        [f'<a href="https://www.amazon.co.uk/dp/B003YQMMCU?tag={AMAZON_TAG}" rel="nofollow noopener">Royal Canin Indoor</a>', "Poultry", "Yes", "Yes", "~£16 (2 kg)"],
        [f'<a href="https://www.amazon.co.uk/dp/B0BFVF4CVN?tag={AMAZON_TAG}" rel="nofollow noopener">James Wellbeloved</a>', "Turkey", "Yes", "Yes", "~£12 (1.5 kg)"],
        [f'<a href="https://www.amazon.co.uk/dp/B07BFLHLSX?tag={AMAZON_TAG}" rel="nofollow noopener">Purina ONE Indoor</a>', "Turkey", "Yes", "Yes", "~£8 (800 g)"],
        [f'<a href="https://www.amazon.co.uk/dp/B003XV22HW?tag={AMAZON_TAG}" rel="nofollow noopener">Hill\'s Science Plan</a>', "Chicken", "Yes", "Yes", "~£18 (1.5 kg)"],
    ]
)}

{glossary_section([
    ("L-carnitine", "An amino acid that helps the body convert fat into energy, commonly added to weight management cat foods"),
    ("Body condition score", "A scale used by vets to assess whether a cat is underweight, ideal, or overweight (typically 1-9 scale)"),
    ("Hairball control formula", "Cat food with added fibre or lubricants that help ingested fur pass through the digestive system"),
    ("Metabolic rate", "The rate at which the body uses energy; lower in neutered and less active cats"),
    ("Prebiotics", "Non-digestible food ingredients that promote the growth of beneficial gut bacteria"),
])}

{faq_section([
    ("Do indoor cats really need special food?", "While not strictly essential, indoor cat food is formulated to address the specific challenges of indoor living &mdash; lower activity, more grooming, and potential weight gain. It can help prevent common health issues."),
    ("How often should I feed my indoor cat?", "Most vets recommend two measured meals per day for adult cats. Some owners use timed feeders to provide small meals throughout the day, which can better suit cats' natural grazing behaviour."),
    ("Can I mix indoor and regular cat food?", "Yes, mixing is fine. Many owners use indoor-formula dry food for puzzle feeders and regular wet food for meals. Just monitor total calorie intake."),
    ("Should indoor cats have access to food all day?", "Free-feeding (leaving food out all day) often leads to overeating in indoor cats. Measured portions are better for weight management."),
    ("Is grain-free food better for indoor cats?", "Not necessarily. Grain-free diets are only beneficial for cats with confirmed grain allergies, which are uncommon. Standard high-quality indoor formulas are suitable for most cats."),
], slug)}

{sources_section()}

{internal_html}

{author_box()}
{cta_block()}
{affiliate_disclosure()}'''
    return body, "cat eating food bowl indoors"


def gen_obesity(title, slug, internal_html):
    qa = quick_answer_box("Prevent obesity in indoor cats by measuring food portions, using puzzle feeders to slow eating, providing daily interactive play sessions, and scheduling regular weigh-ins. The PDSA estimates nearly half of UK cats are overweight, with indoor cats at particular risk.")
    toc = toc_block([
        ("risks", "Why Are Indoor Cats at Higher Risk of Obesity?"),
        ("how-to-tell", "How to Tell If Your Indoor Cat Is Overweight"),
        ("prevention", "How to Prevent Weight Gain in Indoor Cats"),
        ("feeding-guide", "Indoor Cat Feeding Guidelines"),
        ("products", "Recommended Products"),
        ("comparison", "Product Comparison"),
        ("glossary", "Key Terms / Glossary"),
        ("faq", "Frequently Asked Questions"),
        ("sources", "Sources & References"),
    ])
    body = f'''{qa}
{toc}

<h2 id="risks">Why Are Indoor Cats at Higher Risk of Obesity?</h2>
<p>Indoor cats face a perfect storm of obesity risk factors. They do not hunt, patrol territory, or climb trees. They have constant access to food and warm, comfortable resting spots. Many owners also show affection through treats. The result is that indoor cats can easily consume more calories than they burn.</p>
<p>The RSPCA notes that feline obesity is linked to diabetes, arthritis, urinary tract disease, liver problems, and a reduced lifespan of up to 2.5 years.</p>

<h2 id="how-to-tell">How Can You Tell If Your Indoor Cat Is Overweight?</h2>
<p>Use the body condition assessment method recommended by vets:</p>
<ul>
<li><strong>Ribs</strong> &mdash; You should be able to feel (but not see) your cat's ribs with light pressure</li>
<li><strong>Waist</strong> &mdash; Viewed from above, your cat should have a visible waist between ribs and hips</li>
<li><strong>Belly tuck</strong> &mdash; From the side, the abdomen should tuck up behind the rib cage, not hang down</li>
<li><strong>Weight</strong> &mdash; Average domestic cat: 3.5-5 kg. Breed-specific ranges vary</li>
</ul>
<p>If in doubt, ask your vet for a body condition score assessment at your next check-up.</p>

<h2 id="prevention">What Are the Best Ways to Prevent Weight Gain in Indoor Cats?</h2>
<h3>1. Measure Every Meal</h3>
<p>Use a kitchen scale or measuring scoop. Follow the feeding guidelines on your cat food packaging, adjusted for your cat's ideal weight (not current weight if overweight).</p>

<h3>2. Use Puzzle Feeders</h3>
<p>Puzzle feeders slow down eating and provide mental stimulation. They also turn mealtimes into an activity that burns calories.</p>

<h3>3. Schedule Interactive Play</h3>
<p>At least 30 minutes of active play daily, split into 2-3 sessions. Use wand toys, balls, and chase games.</p>

<h3>4. Limit Treats</h3>
<p>Treats should make up no more than 10% of your cat's daily calorie intake. Use tiny treats or break larger ones into smaller pieces.</p>

<h3>5. Regular Weigh-ins</h3>
<p>Weigh your cat monthly. Even 100 g of gain over time can indicate a trend towards obesity.</p>

<h2 id="feeding-guide">What Are the Feeding Guidelines for Indoor Cats?</h2>
<p>As a general guide for adult indoor cats fed a complete dry food:</p>
<ul>
<li><strong>3 kg cat:</strong> ~35-45 g per day</li>
<li><strong>4 kg cat:</strong> ~45-55 g per day</li>
<li><strong>5 kg cat:</strong> ~50-65 g per day</li>
</ul>
<p>Always check the specific recommendations on your chosen cat food, as calorie density varies between brands.</p>

{products_section([
    ("B08GC4P4GP", "Catit Senses 2.0 Digger", "Interactive puzzle feeder that slows eating and provides mental stimulation. Adjustable difficulty for gradual challenge.", "~£12"),
    ("B08CMX5BXS", "PetSafe SlimCat Interactive Ball Feeder", "Rolling ball that dispenses kibble as your cat plays. Combines feeding with exercise. Adjustable opening controls difficulty.", "~£6"),
    ("B01N4DYJ89", "Sure Petcare SureFeed Microchip Feeder", "Portion-controlled feeder that opens only for your cat's microchip. Prevents food stealing in multi-cat homes.", "~£70"),
    ("B07BFLHLSX", "Purina ONE Indoor Cat Rich in Turkey", "Calorie-controlled indoor formula with high protein to maintain lean muscle mass during weight management.", "~£8 (800 g)"),
])}

{comparison_table(
    ["Product", "Purpose", "Multi-Cat Suitable", "Best For", "Approx. Price"],
    [
        [f'<a href="https://www.amazon.co.uk/dp/B08GC4P4GP?tag={AMAZON_TAG}" rel="nofollow noopener">Catit Digger</a>', "Slow feeding", "Yes", "Puzzle feeders", "~£12"],
        [f'<a href="https://www.amazon.co.uk/dp/B08CMX5BXS?tag={AMAZON_TAG}" rel="nofollow noopener">PetSafe SlimCat</a>', "Exercise + feeding", "Yes", "Active cats", "~£6"],
        [f'<a href="https://www.amazon.co.uk/dp/B01N4DYJ89?tag={AMAZON_TAG}" rel="nofollow noopener">SureFeed Microchip</a>', "Portion control", "Essential", "Multi-cat homes", "~£70"],
        [f'<a href="https://www.amazon.co.uk/dp/B07BFLHLSX?tag={AMAZON_TAG}" rel="nofollow noopener">Purina ONE Indoor</a>', "Low-cal diet", "Yes", "Weight management", "~£8"],
    ]
)}

{glossary_section([
    ("Body condition score (BCS)", "A standardised scale (usually 1-9) used by veterinarians to assess body fat and overall condition"),
    ("Free-feeding", "Leaving food available for a cat to eat at will throughout the day, which can lead to overeating"),
    ("Calorie density", "The number of calories per gram of food; lower density foods allow larger portions with fewer calories"),
    ("Metabolic energy requirement", "The total calories a cat needs per day based on weight, age, activity level, and neutering status"),
    ("Lean body mass", "The weight of everything in the body except fat, including muscles, bones, and organs"),
])}

{faq_section([
    ("How much weight should an indoor cat lose per week?", "Safe weight loss for cats is 1-2% of body weight per week. For a 6 kg cat, this means losing 60-120 g per week. Rapid weight loss can cause fatty liver disease, so always consult your vet before starting a weight loss plan."),
    ("Why is my indoor cat always hungry?", "Constant hunger can indicate boredom-eating, an inadequate diet, diabetes, hyperthyroidism, or intestinal parasites. If your cat seems excessively hungry despite adequate portions, see your vet."),
    ("Do neutered cats gain weight more easily?", "Yes. Neutering reduces metabolic rate by approximately 20-30%. Adjusting food portions after neutering is important to prevent weight gain."),
    ("Can my indoor cat lose weight just by playing more?", "Exercise helps, but diet is the primary factor in feline weight management. A combination of portion control and increased activity is most effective."),
    ("Are diet cat foods effective?", "Veterinary diet foods are formulated to provide complete nutrition at lower calorie levels. They can be effective as part of a structured weight management plan supervised by your vet."),
], slug)}

{sources_section()}

{internal_html}

{author_box()}
{cta_block()}
{affiliate_disclosure()}'''
    return body, "overweight cat indoors"


def gen_litter_tray(title, slug, internal_html):
    qa = quick_answer_box("The general rule is one litter tray per cat plus one extra, placed in quiet, accessible locations away from food and water. For a single indoor cat, have at least two trays. Choose covered or uncovered based on your cat's preference, and scoop daily.")
    toc = toc_block([
        ("types", "What Types of Litter Trays Are Available?"),
        ("how-many", "How Many Litter Trays Does an Indoor Cat Need?"),
        ("placement", "Where Should You Place Litter Trays?"),
        ("litter-types", "What Type of Cat Litter Is Best?"),
        ("products", "Recommended Products"),
        ("comparison", "Product Comparison"),
        ("glossary", "Key Terms / Glossary"),
        ("faq", "Frequently Asked Questions"),
        ("sources", "Sources & References"),
    ])
    body = f'''{qa}
{toc}

<h2 id="types">What Types of Litter Trays Are Available?</h2>
<h3>Open Trays</h3>
<p>Simple, affordable, and easy to clean. Most cats prefer open trays as they allow easy escape routes and good ventilation. However, litter can be kicked outside the tray.</p>

<h3>Covered/Hooded Trays</h3>
<p>Contain mess and odour better. Some cats dislike the enclosed feeling, and odour can build up inside if not cleaned frequently. The RSPCA notes that many cats prefer uncovered trays.</p>

<h3>Top-Entry Trays</h3>
<p>Cats enter from the top, reducing litter tracking. Good for households with dogs who like to investigate the litter tray. May not suit elderly or mobility-impaired cats.</p>

<h3>Self-Cleaning Trays</h3>
<p>Automated systems that rake or rotate to separate clumps. Convenient but expensive, and some cats are frightened by the motor noise.</p>

<h2 id="how-many">How Many Litter Trays Does an Indoor Cat Need?</h2>
<p>The widely accepted formula is <strong>one tray per cat plus one extra</strong>. For a single indoor cat, this means two trays. For two cats, three trays. This is recommended by the RSPCA, Cats Protection, and International Cat Care.</p>
<p>Having multiple trays is important because cats may refuse to use a soiled tray, and some cats prefer to urinate in one location and defecate in another.</p>

<h2 id="placement">Where Should You Place Litter Trays in Your Home?</h2>
<ul>
<li><strong>Quiet locations</strong> &mdash; Away from washing machines, tumble dryers, and busy walkways</li>
<li><strong>Away from food and water</strong> &mdash; Cats instinctively separate their toilet area from eating areas</li>
<li><strong>Different rooms</strong> &mdash; Place trays in separate rooms so your cat always has a clean, accessible option</li>
<li><strong>Easy access</strong> &mdash; Avoid locations behind closed doors or up/down stairs for elderly cats</li>
<li><strong>Escape routes</strong> &mdash; Ensure your cat can see the room from the tray and is not cornered</li>
</ul>

<h2 id="litter-types">What Type of Cat Litter Is Best for Indoor Cats?</h2>
<ul>
<li><strong>Clumping clay</strong> &mdash; Most popular. Easy to scoop, good odour control. Heavier to dispose of.</li>
<li><strong>Non-clumping clay</strong> &mdash; Affordable but needs full replacement more often.</li>
<li><strong>Silica crystal</strong> &mdash; Excellent odour absorption, longer lasting, but some cats dislike the texture.</li>
<li><strong>Paper-based</strong> &mdash; Lightweight, eco-friendly, good for sensitive paws. Less effective at odour control.</li>
<li><strong>Wood pellet</strong> &mdash; Natural, good odour control, biodegradable. Can be tracked around the house.</li>
<li><strong>Tofu/corn-based</strong> &mdash; Biodegradable, flushable (check local regulations), and increasingly popular in the UK.</li>
</ul>

{products_section([
    ("B0BKLJWJY1", "Catit PIXI Top-Entry Litter Box", "Stylish top-entry design reduces litter tracking. Built-in scoop holder. Large enough for most adult cats.", "~£30"),
    ("B003XKRCPU", "Catit Jumbo Hooded Cat Pan", "Spacious covered tray with carbon filter for odour control. Swinging door for easy cat access.", "~£20"),
    ("B089G6N6YG", "Petsafe ScoopFree Self-Cleaning Litter Box", "Automatic raking system with disposable crystal trays. Hands-free cleaning for up to 30 days.", "~£130"),
    ("B08LKS6PYY", "World's Best Cat Litter (Clumping)", "Plant-based clumping litter made from whole-kernel corn. Quick clumping, easy to scoop, flushable.", "~£15 (3.18 kg)"),
])}

{comparison_table(
    ["Product", "Type", "Odour Control", "Easy to Clean", "Approx. Price"],
    [
        [f'<a href="https://www.amazon.co.uk/dp/B0BKLJWJY1?tag={AMAZON_TAG}" rel="nofollow noopener">Catit PIXI Top-Entry</a>', "Top-entry box", "Good", "Manual scoop", "~£30"],
        [f'<a href="https://www.amazon.co.uk/dp/B003XKRCPU?tag={AMAZON_TAG}" rel="nofollow noopener">Catit Jumbo Hooded</a>', "Covered box", "Carbon filter", "Manual scoop", "~£20"],
        [f'<a href="https://www.amazon.co.uk/dp/B089G6N6YG?tag={AMAZON_TAG}" rel="nofollow noopener">PetSafe ScoopFree</a>', "Self-cleaning", "Excellent", "Automatic", "~£130"],
        [f'<a href="https://www.amazon.co.uk/dp/B08LKS6PYY?tag={AMAZON_TAG}" rel="nofollow noopener">World\'s Best Cat Litter</a>', "Plant-based clumping", "Very good", "Easy scoop", "~£15"],
    ]
)}

{glossary_section([
    ("Litter tray", "A container filled with absorbent material where cats urinate and defecate indoors"),
    ("Clumping litter", "Cat litter that forms solid clumps when wet, making it easy to scoop out soiled sections"),
    ("Litter tracking", "When cats carry small pieces of litter on their paws and deposit them outside the tray"),
    ("Carbon filter", "An activated charcoal filter fitted to covered litter trays to absorb odour"),
    ("Substrate preference", "A cat's individual preference for the type and texture of litter material"),
])}

{faq_section([
    ("How often should I clean the litter tray?", "Scoop clumps and solids at least once daily. Completely empty, wash, and refill the tray with fresh litter every 1-2 weeks, or as recommended by the litter manufacturer."),
    ("Why does my indoor cat go outside the litter tray?", "Common reasons include a dirty tray, wrong litter type, stressful tray location, medical issues (UTIs, kidney disease), or not enough trays in a multi-cat home. If the behaviour starts suddenly, see your vet."),
    ("Is covered or uncovered better for indoor cats?", "Most cats prefer uncovered trays because they offer better ventilation and visibility. However, some cats like the privacy of a cover. Offer both initially and let your cat choose."),
    ("Can I use scented litter for my indoor cat?", "Most cats dislike scented litter. Unscented litter with good clumping or crystal absorption is better for odour control without deterring your cat from using the tray."),
    ("Where should I NOT place a litter tray?", "Avoid placing trays next to food bowls, in high-traffic areas, near noisy appliances, in dead-end corners with no escape route, or behind closed doors."),
], slug)}

{sources_section()}

{internal_html}

{author_box()}
{cta_block()}
{affiliate_disclosure()}'''
    return body, "cat litter tray indoors"


def gen_second_cat(title, slug, internal_html):
    qa = quick_answer_box("Introduce a second cat gradually over 1-2 weeks using scent swapping, visual introductions through a barrier, and supervised meetings. Never force face-to-face contact on the first day. Cats Protection recommends a minimum 7-day separation period for successful introductions.")
    toc = toc_block([
        ("before", "What to Consider Before Getting a Second Cat"),
        ("preparation", "How to Prepare Your Home"),
        ("step-by-step", "Step-by-Step Introduction Process"),
        ("signs", "Signs the Introduction Is Going Well"),
        ("products", "Recommended Products"),
        ("comparison", "Product Comparison"),
        ("glossary", "Key Terms / Glossary"),
        ("faq", "Frequently Asked Questions"),
        ("sources", "Sources & References"),
    ])
    body = f'''{qa}
{toc}

<h2 id="before">What Should You Consider Before Getting a Second Cat?</h2>
<p>Not all cats want or need feline companionship. Cats are naturally solitary hunters and do not require a social group to be happy. Before adding a second cat, consider:</p>
<ul>
<li><strong>Your current cat's personality</strong> &mdash; Sociable cats who have lived with others previously are better candidates</li>
<li><strong>Space</strong> &mdash; Indoor homes need enough room for separate resources (food, water, litter, sleeping areas) for each cat</li>
<li><strong>Age and energy matching</strong> &mdash; A kitten introduced to a senior cat can cause stress. Similar ages and energy levels work best</li>
<li><strong>Financial commitment</strong> &mdash; Double the food, litter, vet bills, and insurance</li>
</ul>

<h2 id="preparation">How Do You Prepare Your Home for a Second Cat?</h2>
<ul>
<li>Set up a <strong>separate room</strong> with food, water, litter tray, scratching post, hiding spots, and bedding</li>
<li>Add an <strong>extra litter tray</strong> (the new total should be one per cat plus one)</li>
<li>Install a <strong>Feliway Multicat diffuser</strong> to release calming pheromones</li>
<li>Create <strong>vertical escape routes</strong> such as cat shelves or tall cat trees</li>
<li>Ensure both cats have <strong>separate feeding stations</strong></li>
</ul>

<h2 id="step-by-step">What Is the Step-by-Step Process for Introducing Two Cats?</h2>
<h3>Days 1-3: Complete Separation</h3>
<p>Keep the new cat in their dedicated room. Allow your resident cat to continue their normal routine undisturbed. Both cats will be aware of each other's scent under the door.</p>

<h3>Days 3-5: Scent Swapping</h3>
<p>Swap bedding between the two cats so they become familiar with each other's scent. Rub a cloth on one cat's cheeks and place it near the other cat's food bowl.</p>

<h3>Days 5-7: Site Swapping</h3>
<p>Allow the new cat to explore the main living areas while the resident cat visits the new cat's room. This lets both cats investigate each other's scent in different spaces.</p>

<h3>Days 7-10: Visual Introduction</h3>
<p>Use a baby gate, mesh screen, or cracked door to allow the cats to see each other without direct contact. Feed both cats on their respective sides so they associate each other's presence with positive experiences.</p>

<h3>Days 10+: Supervised Meetings</h3>
<p>Allow brief, supervised face-to-face meetings. Have treats ready to reward calm behaviour. End sessions on a positive note before any tension develops. Gradually increase the length of meetings.</p>

<h2 id="signs">What Are the Signs the Introduction Is Going Well?</h2>
<ul>
<li>Both cats eating normally</li>
<li>Relaxed body language (slow blinking, lying down)</li>
<li>Curiosity without aggression (sniffing, watching)</li>
<li>Play behaviour without chasing or hissing</li>
<li>Both cats using communal areas at different times</li>
</ul>

{products_section([
    ("B003AKZL16", "Feliway Friends/Multicat Diffuser", "Releases cat appeasing pheromone to reduce tension between cats. Covers up to 70 m². Lasts 30 days per refill.", "~£20"),
    ("B07R35MN1B", "Lindam Easy Fit Baby Gate", "Pressure-fit gate ideal for separating rooms during cat introductions. Allows visual and scent contact while preventing direct access.", "~£25"),
    ("B08GC4P4GP", "Catit Senses 2.0 Digger", "Puzzle feeder that can be used to create positive mealtime associations during introductions. One per cat recommended.", "~£12"),
    ("B01N4DYJ89", "Sure Petcare SureFeed Microchip Feeder", "Prevents food stealing between cats. Opens only for the registered cat's microchip or collar tag.", "~£70"),
])}

{comparison_table(
    ["Product", "Purpose", "Duration/Type", "Essential?", "Approx. Price"],
    [
        [f'<a href="https://www.amazon.co.uk/dp/B003AKZL16?tag={AMAZON_TAG}" rel="nofollow noopener">Feliway Friends</a>', "Calming pheromone", "30-day refill", "Highly recommended", "~£20"],
        [f'<a href="https://www.amazon.co.uk/dp/B07R35MN1B?tag={AMAZON_TAG}" rel="nofollow noopener">Baby Gate</a>', "Visual barrier", "Reusable", "Very helpful", "~£25"],
        [f'<a href="https://www.amazon.co.uk/dp/B08GC4P4GP?tag={AMAZON_TAG}" rel="nofollow noopener">Catit Digger</a>', "Positive association", "Permanent", "Optional", "~£12"],
        [f'<a href="https://www.amazon.co.uk/dp/B01N4DYJ89?tag={AMAZON_TAG}" rel="nofollow noopener">SureFeed Microchip</a>', "Separate feeding", "Permanent", "Recommended", "~£70"],
    ]
)}

{glossary_section([
    ("Scent swapping", "The process of exchanging bedding or cloths between cats to familiarise them with each other's scent before meeting"),
    ("Site swapping", "Allowing each cat to explore the other's territory while the other cat is absent"),
    ("Feliway", "A synthetic version of feline facial pheromone that helps reduce stress and conflict in cats"),
    ("Resource guarding", "When a cat aggressively protects food, litter trays, or resting spots from another cat"),
    ("Solitary species", "Animals that naturally live and hunt alone, as domestic cats evolved to do"),
])}

{faq_section([
    ("How long does it take for two cats to get along?", "A successful introduction typically takes 1-4 weeks. Some cats become friends quickly, while others may take several months to tolerate each other. Some pairs never become close but can coexist peacefully."),
    ("What if the cats fight during introduction?", "Separate them immediately and go back to the previous stage of introduction. Fighting does not mean it will never work, but it does mean you are moving too fast."),
    ("Should I get a male or female cat as a companion?", "The individual personality matters more than sex. However, neutered opposite-sex pairs often have fewer territorial issues than same-sex pairs."),
    ("Is it better to get a kitten or an adult cat?", "An adult cat with a known history of living with other cats is often easier to introduce than a kitten, whose energy may stress an older resident cat. Match energy levels where possible."),
    ("Can indoor cats live happily in pairs?", "Many indoor cats thrive with a companion, especially if they are home alone during the day. The key is a careful, gradual introduction and adequate resources for both cats."),
], slug)}

{sources_section()}

{internal_html}

{author_box()}
{cta_block()}
{affiliate_disclosure()}'''
    return body, "two cats together indoors"


def gen_safety(title, slug, internal_html):
    qa = quick_answer_box("Common household hazards for indoor cats include toxic plants (lilies, poinsettia), open windows without screens, electrical cords, human medications, cleaning chemicals, small swallowable objects, and essential oil diffusers. Cat-proof your home room by room to keep your indoor cat safe.")
    toc = toc_block([
        ("common-hazards", "What Are the Most Common Household Hazards for Cats?"),
        ("room-by-room", "Room-by-Room Safety Checklist"),
        ("toxic-substances", "Which Household Substances Are Toxic to Cats?"),
        ("emergency", "What to Do in a Cat Emergency"),
        ("products", "Recommended Products"),
        ("comparison", "Product Comparison"),
        ("glossary", "Key Terms / Glossary"),
        ("faq", "Frequently Asked Questions"),
        ("sources", "Sources & References"),
    ])
    body = f'''{qa}
{toc}

<h2 id="common-hazards">What Are the Most Common Household Hazards for Cats?</h2>
<p>Indoor cats face numerous hidden dangers within the home. The Blue Cross receives thousands of calls each year about cats injured or poisoned by everyday household items. Awareness and prevention are key.</p>

<h3>Toxic Plants</h3>
<p>Lilies are the most dangerous &mdash; every part of the plant is toxic to cats and can cause fatal kidney failure. Other common toxic houseplants include poinsettia, aloe vera, pothos, and dieffenbachia.</p>

<h3>Open Windows and Balconies</h3>
<p>"High-rise syndrome" affects cats that fall from windows or balconies. Cats can squeeze through surprisingly narrow openings. Always use secure window screens or restrictors.</p>

<h3>Electrical Cords</h3>
<p>Kittens and young cats are particularly attracted to chewing electrical cords. This can cause burns, electrocution, or house fires.</p>

<h3>String and Small Objects</h3>
<p>String, ribbon, hair ties, rubber bands, and small toys can cause intestinal obstructions if swallowed. Linear foreign bodies (string) are particularly dangerous and often require surgery.</p>

<h2 id="room-by-room">What Does a Room-by-Room Safety Checklist Look Like?</h2>
<h3>Kitchen</h3>
<ul>
<li>Keep hob covers on when not in use (hot surfaces)</li>
<li>Secure bin lids (chicken bones, string from meat joints)</li>
<li>Store onions, garlic, grapes, and chocolate out of reach</li>
<li>Use child locks on cupboards containing chemicals</li>
</ul>

<h3>Bathroom</h3>
<ul>
<li>Keep toilet lids down (drowning risk for kittens, chemical exposure from cleaning products)</li>
<li>Store medications in locked cabinets</li>
<li>Remove bath mats with fraying edges (ingestion risk)</li>
</ul>

<h3>Living Room</h3>
<ul>
<li>Cover or hide electrical cords</li>
<li>Secure heavy bookcases and shelving to the wall</li>
<li>Use flameless candles instead of real ones</li>
<li>Check reclining chairs before closing them</li>
</ul>

<h3>Bedroom</h3>
<ul>
<li>Keep small items (hair ties, earrings, buttons) in closed containers</li>
<li>Check inside washing machines and tumble dryers before use</li>
<li>Secure window blinds cords out of reach</li>
</ul>

<h2 id="toxic-substances">Which Household Substances Are Toxic to Cats?</h2>
<ul>
<li><strong>Paracetamol</strong> &mdash; Extremely toxic to cats. A single tablet can be fatal</li>
<li><strong>Ibuprofen</strong> &mdash; Causes kidney failure in cats</li>
<li><strong>Essential oils</strong> &mdash; Tea tree, eucalyptus, peppermint, and citrus oils are toxic via ingestion, skin contact, or inhalation</li>
<li><strong>Antifreeze</strong> &mdash; Contains ethylene glycol, which is sweet-tasting and lethal even in tiny amounts</li>
<li><strong>Bleach and disinfectants</strong> &mdash; Phenol-based cleaners are particularly dangerous</li>
<li><strong>Human foods</strong> &mdash; Onions, garlic, grapes, raisins, chocolate, xylitol, alcohol</li>
</ul>

<h2 id="emergency">What Should You Do in a Cat Emergency?</h2>
<p>If your cat ingests something toxic or is injured:</p>
<ol>
<li>Stay calm and do not attempt to make your cat vomit (this can cause more harm)</li>
<li>Note what was ingested and approximately how much</li>
<li>Contact your vet or the VPIS (Veterinary Poisons Information Service) immediately</li>
<li>Keep your vet's emergency number and nearest out-of-hours clinic number saved in your phone</li>
</ol>

{products_section([
    ("B075N4DCLZ", "Flat Cats Window Screens", "Mesh window screens that allow fresh air while preventing cats from escaping or falling. Custom sizes available for UK window types.", "~£30"),
    ("B07DP8ZJZM", "Cable Tidy Tube (3-metre)", "Flexible split tubing that covers electrical cables and prevents chewing. Easy to install along skirting boards.", "~£8"),
    ("B00IONSAM0", "Child Safety Cabinet Locks (10 Pack)", "Adhesive cabinet locks that prevent cats from opening cupboards containing cleaning products or medication.", "~£8"),
    ("B08DJJWFBK", "Flameless LED Candles (Set of 6)", "Realistic flickering LED candles that eliminate fire risk from real candles. Timer and remote control included.", "~£15"),
])}

{comparison_table(
    ["Product", "Hazard Addressed", "Installation", "Cat-Proof Rating", "Approx. Price"],
    [
        [f'<a href="https://www.amazon.co.uk/dp/B075N4DCLZ?tag={AMAZON_TAG}" rel="nofollow noopener">Flat Cats Screens</a>', "Window falls", "Semi-permanent", "Excellent", "~£30"],
        [f'<a href="https://www.amazon.co.uk/dp/B07DP8ZJZM?tag={AMAZON_TAG}" rel="nofollow noopener">Cable Tidy Tube</a>', "Electrical cords", "Easy", "Good", "~£8"],
        [f'<a href="https://www.amazon.co.uk/dp/B00IONSAM0?tag={AMAZON_TAG}" rel="nofollow noopener">Cabinet Locks</a>', "Toxic chemicals", "Adhesive", "Good", "~£8"],
        [f'<a href="https://www.amazon.co.uk/dp/B08DJJWFBK?tag={AMAZON_TAG}" rel="nofollow noopener">LED Candles</a>', "Fire risk", "None needed", "Excellent", "~£15"],
    ]
)}

{glossary_section([
    ("High-rise syndrome", "Injuries sustained by cats falling from windows, balconies, or other heights"),
    ("Linear foreign body", "A string-like object (thread, ribbon, tinsel) ingested by a cat that can cause intestinal blockage or perforation"),
    ("VPIS", "Veterinary Poisons Information Service, a 24-hour UK helpline for animal poisoning emergencies"),
    ("Phenol", "A chemical found in some disinfectants that is highly toxic to cats due to their inability to metabolise it"),
    ("Ethylene glycol", "The toxic ingredient in antifreeze, lethal to cats in very small quantities"),
])}

{faq_section([
    ("What is the most dangerous household item for cats?", "Lilies and paracetamol are among the most dangerous. Even a small amount of lily pollen on a cat's fur (which they then groom off) can cause fatal kidney failure. A single paracetamol tablet can kill a cat."),
    ("Are essential oil diffusers safe around cats?", "No. Many essential oils are toxic to cats. If you use a diffuser, ensure your cat cannot access the room and has the choice to leave. Avoid tea tree, eucalyptus, peppermint, clove, and citrus oils entirely."),
    ("How do I cat-proof electrical cords?", "Use cable tidy tubes, cord covers, or run cables behind furniture. Apply bitter apple spray to cords as a deterrent. Unplug unused appliances."),
    ("Should I keep my toilet lid down?", "Yes, especially with kittens who could fall in and drown. Toilet water may also contain chemical residues from cleaning products."),
    ("Is tinsel dangerous for cats?", "Extremely dangerous. Tinsel is a classic linear foreign body that can cause life-threatening intestinal obstructions. Avoid using tinsel in homes with cats."),
], slug)}

{sources_section()}

{internal_html}

{author_box()}
{cta_block()}
{affiliate_disclosure()}'''
    return body, "cat safe home indoors"


def gen_interactive_toys(title, slug, internal_html):
    qa = quick_answer_box("The best interactive toys for indoor cats in the UK include wand toys like Da Bird, puzzle feeders like the Catit Digger, electronic motion toys, and treat-dispensing balls. Aim for toys that mimic prey behaviour to trigger your cat's natural hunting instincts.")
    toc = toc_block([
        ("why-interactive", "Why Are Interactive Toys Important for Indoor Cats?"),
        ("types", "Types of Interactive Cat Toys"),
        ("choosing", "How to Choose the Right Interactive Toy"),
        ("products", "Recommended Products"),
        ("comparison", "Product Comparison"),
        ("glossary", "Key Terms / Glossary"),
        ("faq", "Frequently Asked Questions"),
        ("sources", "Sources & References"),
    ])
    body = f'''{qa}
{toc}

<h2 id="why-interactive">Why Are Interactive Toys Important for Indoor Cats?</h2>
<p>Interactive toys are essential for indoor cats because they simulate the hunt-catch-kill-eat cycle that outdoor cats experience naturally. Without this stimulation, indoor cats can develop behavioural issues including aggression, anxiety, and destructive behaviour.</p>
<p>Cats Protection and the PDSA both emphasise that daily interactive play is one of the most important things you can do for an indoor cat's wellbeing.</p>

<h2 id="types">What Types of Interactive Cat Toys Are Available?</h2>
<h3>Wand and Teaser Toys</h3>
<p>Feather wands, string teasers, and ribbon wands allow you to control the prey. Vary speed, direction, and movement patterns to keep your cat engaged.</p>

<h3>Puzzle Feeders</h3>
<p>From simple treat balls to complex multi-stage puzzles, these engage your cat's problem-solving abilities and provide mental stimulation alongside physical activity.</p>

<h3>Electronic Motion Toys</h3>
<p>Battery-powered toys with unpredictable movements. Great for when you cannot play directly, though they should supplement, not replace, human-led play.</p>

<h3>Kick Toys</h3>
<p>Larger stuffed toys that cats can grab with their front paws and kick with their back legs, satisfying the "kill" instinct.</p>

<h3>Track and Ball Toys</h3>
<p>Enclosed tracks with balls that spin inside. Cats can bat at the ball without it rolling away and getting lost under furniture.</p>

<h2 id="choosing">How Do You Choose the Right Interactive Toy?</h2>
<ul>
<li>Match the toy to your cat's prey preference (birds, mice, insects)</li>
<li>Ensure size is appropriate &mdash; toys should not have small parts that can be swallowed</li>
<li>Rotate toys regularly to maintain novelty</li>
<li>Supervise play with wand toys to prevent string ingestion</li>
<li>Choose durable materials that withstand enthusiastic play</li>
</ul>

{products_section([
    ("B000IYSAIW", "Da Bird Cat Toy", "The gold standard of feather wands. The spinning feather attachment creates realistic bird-flight sounds and movements. Replacement feathers widely available.", "~£8"),
    ("B08GC4P4GP", "Catit Senses 2.0 Digger", "Five-tube puzzle feeder requiring cats to use different paw techniques. Adjustable difficulty suits kittens to adults.", "~£12"),
    ("B07V3CPFTM", "PetFusion Ambush Interactive Toy", "Electronic concealed-motion toy with rotating feather. Timer function and variable speed. Engages cats independently.", "~£25"),
    ("B0006N9I68", "KONG Active Feather Teaser", "Durable wand with replaceable feather attachment. Flexible rod creates unpredictable movements.", "~£5"),
    ("B07QP8K94Y", "Catit Play Senses Super Circuit", "Ball-in-track system that can be configured in different layouts. Includes peek-a-boo cover for added challenge.", "~£10"),
])}

{comparison_table(
    ["Product", "Type", "Supervised?", "Prey Mimicry", "Approx. Price"],
    [
        [f'<a href="https://www.amazon.co.uk/dp/B000IYSAIW?tag={AMAZON_TAG}" rel="nofollow noopener">Da Bird</a>', "Wand toy", "Yes", "Bird", "~£8"],
        [f'<a href="https://www.amazon.co.uk/dp/B08GC4P4GP?tag={AMAZON_TAG}" rel="nofollow noopener">Catit Digger</a>', "Puzzle feeder", "No", "Foraging", "~£12"],
        [f'<a href="https://www.amazon.co.uk/dp/B07V3CPFTM?tag={AMAZON_TAG}" rel="nofollow noopener">PetFusion Ambush</a>', "Electronic", "No", "Hidden prey", "~£25"],
        [f'<a href="https://www.amazon.co.uk/dp/B0006N9I68?tag={AMAZON_TAG}" rel="nofollow noopener">KONG Teaser</a>', "Wand toy", "Yes", "Bird/insect", "~£5"],
        [f'<a href="https://www.amazon.co.uk/dp/B07QP8K94Y?tag={AMAZON_TAG}" rel="nofollow noopener">Catit Circuit</a>', "Track toy", "No", "Small prey", "~£10"],
    ]
)}

{glossary_section([
    ("Prey drive", "A cat's innate motivation to stalk, chase, and catch prey-like objects"),
    ("Hunt-catch-kill-eat cycle", "The natural sequence of feline hunting behaviour that play should simulate"),
    ("Puzzle feeder", "A device requiring problem-solving to access food, combining mental stimulation with feeding"),
    ("Interactive play", "Play sessions involving direct participation from a human using toys"),
    ("Enrichment toy", "Any toy designed to improve an animal's quality of life by providing stimulation"),
])}

{faq_section([
    ("How many toys does an indoor cat need?", "Quality matters more than quantity. Have 5-6 toys available at a time and rotate them weekly. A good wand toy, a puzzle feeder, a kick toy, and a track toy provide variety."),
    ("Are laser pointers safe for cats?", "Laser pointers are safe if used correctly. Never shine the laser in your cat's eyes. Always end sessions by directing the laser to a physical toy or treat so your cat gets a satisfying catch."),
    ("How long should I play with my indoor cat each day?", "At least 30 minutes of interactive play, ideally split into 2-3 sessions. Schedule sessions around dawn and dusk when cats are naturally most active."),
    ("My cat ignores toys. What should I try?", "Try different toy types &mdash; some cats prefer feathers, others string or crinkle toys. Move toys slowly and subtly rather than fast. Rub catnip or silver vine on the toy. Some cats prefer chasing toys on the floor rather than in the air."),
    ("Should I leave toys out for my cat when I am at work?", "Leave a few safe solo toys out (track toys, puzzle feeders). Store wand toys out of reach to prevent string ingestion. Rotate the available toys regularly to maintain interest."),
], slug)}

{sources_section()}

{internal_html}

{author_box()}
{cta_block()}
{affiliate_disclosure()}'''
    return body, "cat playing interactive toy"


def gen_boredom(title, slug, internal_html):
    qa = quick_answer_box("Help indoor cats cope with boredom by providing puzzle feeders, rotating toys weekly, creating window watching stations, offering cat grass and catnip, scheduling daily interactive play, and creating vertical climbing spaces. A stimulated cat is a happy cat.")
    toc = toc_block([
        ("signs-boredom", "What Are the Signs of Boredom in Indoor Cats?"),
        ("causes", "Why Do Indoor Cats Get Bored?"),
        ("solutions", "10 Solutions for Bored Indoor Cats"),
        ("products", "Recommended Products"),
        ("comparison", "Product Comparison"),
        ("glossary", "Key Terms / Glossary"),
        ("faq", "Frequently Asked Questions"),
        ("sources", "Sources & References"),
    ])
    body = f'''{qa}
{toc}

<h2 id="signs-boredom">What Are the Signs of Boredom in Indoor Cats?</h2>
<p>Bored indoor cats often display behaviours that owners may mistakenly attribute to bad temperament. Recognising these signs early allows you to address the root cause:</p>
<ul>
<li><strong>Over-eating</strong> &mdash; Eating from boredom rather than genuine hunger</li>
<li><strong>Over-grooming</strong> &mdash; Excessive licking leading to bald patches or skin irritation</li>
<li><strong>Destructive scratching</strong> &mdash; Targeting furniture, carpets, and wallpaper</li>
<li><strong>Excessive sleeping</strong> &mdash; Beyond the normal 12-16 hours per day</li>
<li><strong>Aggression</strong> &mdash; Biting or ambushing ankles and hands</li>
<li><strong>Attention-seeking behaviour</strong> &mdash; Constant meowing, knocking things off surfaces</li>
<li><strong>Litter tray issues</strong> &mdash; Inappropriate elimination as a stress response</li>
</ul>

<h2 id="causes">Why Do Indoor Cats Get Bored?</h2>
<p>Outdoor cats spend a significant portion of their day hunting, patrolling territory, socialising with other cats, and exploring new environments. Indoor cats have none of these natural outlets. Their environment is predictable and unchanging, which does not suit an animal evolved for constant environmental interaction.</p>
<p>The RSPCA emphasises that environmental enrichment is not a luxury for indoor cats &mdash; it is essential for their welfare.</p>

<h2 id="solutions">What Are the Best Solutions for Bored Indoor Cats?</h2>

<h3>1. Structured Play Schedule</h3>
<p>Set aside specific times for interactive play. Cats thrive on routine, and knowing play time is coming can reduce anxiety.</p>

<h3>2. Puzzle Feeding</h3>
<p>Replace food bowls with puzzle feeders for at least one meal a day. This turns eating from a 30-second task into a 15-minute enrichment activity.</p>

<h3>3. Window Entertainment</h3>
<p>Position bird feeders outside windows and provide comfortable viewing perches. Some owners play &ldquo;cat TV&rdquo; YouTube videos of birds and squirrels.</p>

<h3>4. Rotation System</h3>
<p>Keep toys in a drawer and rotate 5-6 at a time weekly. The novelty of &ldquo;new&rdquo; toys re-engages interest without constant purchasing.</p>

<h3>5. Cat Grass and Herbs</h3>
<p>Growing cat grass, catnip, and silver vine provides sensory enrichment and satisfies nibbling instincts.</p>

<h3>6. Cardboard Box Forts</h3>
<p>Create tunnels and hideaways from cardboard boxes. Cut holes, connect boxes, and hide treats inside for exploration.</p>

<h3>7. Vertical Spaces</h3>
<p>Cat trees, wall shelves, and elevated walkways give cats territory to explore and a sense of security from height.</p>

<h3>8. Training Games</h3>
<p>Clicker training provides mental stimulation and strengthens your bond. Start with simple commands like &ldquo;sit&rdquo; and &ldquo;touch.&rdquo;</p>

<h3>9. Music and Sound</h3>
<p>Studies suggest cats respond positively to species-specific music with tempos matching purring frequencies. Some streaming services offer cat-specific playlists.</p>

<h3>10. Consider a Companion</h3>
<p>If your cat is sociable and you have the space and resources, a second cat can provide companionship during the day. This is not suitable for all cats, though.</p>

{products_section([
    ("B00D3NI2PG", "Trixie 5-in-1 Activity Centre", "Five different puzzle modules challenge your cat's problem-solving skills. Difficulty adjustable by adding or removing elements.", "~£15"),
    ("B073WBX7BM", "ZALALOVA Cat Window Perch", "Heavy-duty suction cup window bed for comfortable bird watching. Supports up to 22 kg.", "~£18"),
    ("B09BFYDSLX", "Cat Grass Growing Kit (3 Pack)", "Organic wheatgrass kit with self-watering containers. Fresh grass ready in 5-7 days.", "~£10"),
    ("B0CB7R41QC", "Cat Exercise Wheel", "Large running wheel for high-energy indoor cats. Padded running surface, silent bearings.", "~£300"),
])}

{comparison_table(
    ["Product", "Enrichment Type", "Engagement Time", "Solo Play?", "Approx. Price"],
    [
        [f'<a href="https://www.amazon.co.uk/dp/B00D3NI2PG?tag={AMAZON_TAG}" rel="nofollow noopener">Trixie Activity Centre</a>', "Mental", "15-30 min", "Yes", "~£15"],
        [f'<a href="https://www.amazon.co.uk/dp/B073WBX7BM?tag={AMAZON_TAG}" rel="nofollow noopener">Window Perch</a>', "Visual", "Hours", "Yes", "~£18"],
        [f'<a href="https://www.amazon.co.uk/dp/B09BFYDSLX?tag={AMAZON_TAG}" rel="nofollow noopener">Cat Grass Kit</a>', "Sensory", "Ongoing", "Yes", "~£10"],
        [f'<a href="https://www.amazon.co.uk/dp/B0CB7R41QC?tag={AMAZON_TAG}" rel="nofollow noopener">Exercise Wheel</a>', "Physical", "Variable", "Yes", "~£300"],
    ]
)}

{glossary_section([
    ("Environmental enrichment", "Modifications to an animal's environment designed to improve quality of life and reduce boredom"),
    ("Stereotypic behaviour", "Repetitive, apparently functionless behaviour patterns often indicating stress or boredom"),
    ("Clicker training", "Using a clicking sound paired with treats to mark and reinforce desired behaviour in cats"),
    ("Crepuscular", "Most active during dawn and dusk; the natural activity pattern of domestic cats"),
    ("Species-specific music", "Music composed at frequencies and tempos that research suggests appeal to cats"),
])}

{faq_section([
    ("Can a bored cat become depressed?", "Yes. Chronic boredom can lead to feline depression, characterised by withdrawal, loss of appetite, excessive sleeping, and loss of interest in play. If you suspect your cat is depressed, consult your vet."),
    ("How do I entertain my cat while I am at work?", "Leave out puzzle feeders, safe solo toys, a window perch with an outdoor bird feeder, and consider cat TV videos. Interactive electronic toys can also provide stimulation in your absence."),
    ("Is it normal for indoor cats to sleep all day?", "Cats naturally sleep 12-16 hours per day. However, if your cat sleeps significantly more and shows no interest in play or interaction when awake, boredom or depression may be a factor."),
    ("Do cats get bored of the same food?", "Some cats appreciate variety in flavours and textures, while others prefer consistency. If your cat seems disinterested in food, try rotating between 2-3 flavours of the same brand."),
    ("Will getting another cat fix my bored cat?", "It depends on your cat's personality. Some cats thrive with a companion, while others are happier alone. A careful, gradual introduction is essential if you decide to add a second cat."),
], slug)}

{sources_section()}

{internal_html}

{author_box()}
{cta_block()}
{affiliate_disclosure()}'''
    return body, "bored cat indoors lying down"


def gen_grooming(title, slug, internal_html):
    qa = quick_answer_box("A complete indoor cat grooming routine includes daily brushing for long-haired breeds (weekly for short-haired), regular nail trimming every 2-3 weeks, ear checks, dental care, and occasional baths only when necessary. Indoor cats especially need nail trims as they do not wear down claws naturally.")
    toc = toc_block([
        ("why-grooming", "Why Is Grooming Important for Indoor Cats?"),
        ("brushing", "How Often Should You Brush an Indoor Cat?"),
        ("nails", "How to Trim Indoor Cat Nails"),
        ("ears-teeth", "Ear and Dental Care for Indoor Cats"),
        ("products", "Recommended Products"),
        ("comparison", "Product Comparison"),
        ("glossary", "Key Terms / Glossary"),
        ("faq", "Frequently Asked Questions"),
        ("sources", "Sources & References"),
    ])
    body = f'''{qa}
{toc}

<h2 id="why-grooming">Why Is Grooming Especially Important for Indoor Cats?</h2>
<p>Indoor cats have specific grooming needs that differ from outdoor cats. They tend to groom themselves more frequently due to boredom, which increases hairball formation. Their nails do not wear down on rough outdoor surfaces, so regular trimming is essential. And because they spend all their time in a climate-controlled environment, they may shed more evenly throughout the year rather than seasonally.</p>

<h2 id="brushing">How Often Should You Brush an Indoor Cat?</h2>
<ul>
<li><strong>Long-haired breeds</strong> (Persian, Ragdoll, Maine Coon) &mdash; Daily brushing to prevent matting and reduce hairballs</li>
<li><strong>Medium-haired breeds</strong> (British Shorthair, Birman) &mdash; 2-3 times per week</li>
<li><strong>Short-haired breeds</strong> (Siamese, Burmese, domestic shorthair) &mdash; Weekly brushing, though more is beneficial</li>
</ul>
<p>Brushing removes loose fur, distributes natural oils, and gives you an opportunity to check for skin issues, lumps, or parasites.</p>

<h2 id="nails">How Do You Trim Indoor Cat Nails?</h2>
<p>Indoor cats need nail trims every 2-3 weeks. Without outdoor surfaces to wear them down, overgrown nails can curve into the paw pad, causing pain and infection.</p>
<ol>
<li>Choose a calm, quiet time when your cat is relaxed</li>
<li>Gently press the paw pad to extend the claws</li>
<li>Identify the pink &ldquo;quick&rdquo; &mdash; cut only the clear tip, 2 mm before the quick</li>
<li>Use sharp, cat-specific nail clippers for a clean cut</li>
<li>Reward with treats after each session to build positive associations</li>
</ol>

<h2 id="ears-teeth">How Do You Care for Indoor Cat Ears and Teeth?</h2>
<h3>Ear Care</h3>
<p>Check ears weekly for wax buildup, odour, or redness. Clean only the visible part with a cotton ball dampened with vet-approved ear cleaner. Never insert anything into the ear canal.</p>

<h3>Dental Care</h3>
<p>Dental disease affects an estimated 85% of cats over age 3. Brush your cat's teeth 2-3 times per week using cat-specific toothpaste (never human toothpaste). Dental treats and water additives can supplement brushing.</p>

{products_section([
    ("B006L2LHGE", "Furminator Short Hair Cat Deshedding Tool", "Stainless steel edge reaches through the topcoat to remove loose undercoat fur. Reduces shedding by up to 90% with regular use.", "~£18"),
    ("B0002AQMZQ", "JW Pet GripSoft Cat Nail Clipper", "Ergonomic scissor-style clippers with non-slip handles. Suitable for cats of all sizes. Clean, precise cuts.", "~£5"),
    ("B078JHCYMH", "Virbac C.E.T. Enzymatic Cat Toothpaste", "Poultry-flavoured enzymatic toothpaste formulated specifically for cats. No rinsing needed. Safe if swallowed.", "~£10"),
    ("B01GKKD52W", "Cat Grooming Glove", "Silicone-tipped glove that removes loose fur while petting. Ideal for cats who dislike traditional brushes.", "~£8"),
])}

{comparison_table(
    ["Product", "Purpose", "Frequency", "Cat Tolerance", "Approx. Price"],
    [
        [f'<a href="https://www.amazon.co.uk/dp/B006L2LHGE?tag={AMAZON_TAG}" rel="nofollow noopener">Furminator</a>', "Deshedding", "Weekly", "Moderate", "~£18"],
        [f'<a href="https://www.amazon.co.uk/dp/B0002AQMZQ?tag={AMAZON_TAG}" rel="nofollow noopener">JW Nail Clipper</a>', "Nail trimming", "Every 2-3 weeks", "Low initially", "~£5"],
        [f'<a href="https://www.amazon.co.uk/dp/B078JHCYMH?tag={AMAZON_TAG}" rel="nofollow noopener">Virbac Toothpaste</a>', "Dental care", "2-3x per week", "Variable", "~£10"],
        [f'<a href="https://www.amazon.co.uk/dp/B01GKKD52W?tag={AMAZON_TAG}" rel="nofollow noopener">Grooming Glove</a>', "Fur removal", "Daily-weekly", "High", "~£8"],
    ]
)}

{glossary_section([
    ("Quick", "The pink blood vessel inside a cat's nail; cutting into it causes pain and bleeding"),
    ("Deshedding", "The process of removing loose undercoat fur to reduce shedding and hairball formation"),
    ("Matting", "Tangled, clumped fur that can pull on the skin and cause discomfort, particularly in long-haired cats"),
    ("Enzymatic toothpaste", "Toothpaste containing enzymes that break down plaque without the need for vigorous brushing"),
    ("Hairball (trichobezoar)", "A ball of ingested fur that forms in the stomach, often vomited up or passed through the digestive system"),
])}

{faq_section([
    ("Do indoor cats need baths?", "Rarely. Most indoor cats keep themselves clean through self-grooming. Baths may be needed for cats with skin conditions, if they get into something messy, or for elderly cats who struggle to groom themselves."),
    ("How do I trim my cat's nails if they hate it?", "Start by handling their paws regularly without trimming, paired with treats. Trim one or two nails at a time rather than all at once. Consider a two-person approach or ask your vet for a demonstration."),
    ("Why does my indoor cat shed so much?", "Indoor cats often shed year-round due to constant indoor lighting and heating, unlike outdoor cats who shed seasonally. Regular brushing significantly reduces loose fur on furniture and clothing."),
    ("Can I use human toothpaste on my cat?", "Never. Human toothpaste contains fluoride and foaming agents that are toxic to cats. Always use toothpaste specifically formulated for cats."),
    ("How can I tell if my cat has dental problems?", "Signs include bad breath, drooling, dropping food, pawing at the mouth, red or swollen gums, and reluctance to eat. Regular vet dental check-ups are recommended annually."),
], slug)}

{sources_section()}

{internal_html}

{author_box()}
{cta_block()}
{affiliate_disclosure()}'''
    return body, "cat grooming brushing indoors"


def gen_catio(title, slug, internal_html):
    qa = quick_answer_box("A catio is a secure outdoor enclosure attached to your home that gives indoor cats safe access to fresh air, sunshine, and outdoor sights and sounds. You can build a simple window box catio for under £100 or invest in a full walk-in enclosure from £300-£1,000+.")
    toc = toc_block([
        ("what-is", "What Is a Catio?"),
        ("benefits", "What Are the Benefits of a Catio?"),
        ("types", "Types of Catios"),
        ("how-to-build", "How to Build a Simple Catio"),
        ("products", "Recommended Products"),
        ("comparison", "Product Comparison"),
        ("glossary", "Key Terms / Glossary"),
        ("faq", "Frequently Asked Questions"),
        ("sources", "Sources & References"),
    ])
    body = f'''{qa}
{toc}

<h2 id="what-is">What Is a Catio?</h2>
<p>A catio (cat + patio) is a screened outdoor enclosure that allows indoor cats to experience the outdoors safely. They range from small window boxes to large free-standing structures and can be attached to the house via a cat flap, window, or door.</p>
<p>Catios have grown increasingly popular in the UK as more owners choose to keep cats indoors for safety. They provide a compromise that gives cats outdoor enrichment without the risks of free-roaming.</p>

<h2 id="benefits">What Are the Benefits of a Catio?</h2>
<ul>
<li><strong>Fresh air and sunshine</strong> &mdash; Essential for vitamin D synthesis and overall wellbeing</li>
<li><strong>Sensory stimulation</strong> &mdash; Outdoor sounds, scents, and wildlife watching</li>
<li><strong>Exercise opportunities</strong> &mdash; Climbing, jumping, and exploring in a larger space</li>
<li><strong>Safety</strong> &mdash; Protection from traffic, predators, toxins, and fights with other cats</li>
<li><strong>Wildlife protection</strong> &mdash; Prevents cats from hunting birds and small mammals</li>
<li><strong>Reduced boredom</strong> &mdash; A new environment to explore reduces indoor monotony</li>
</ul>

<h2 id="types">What Types of Catios Are Available?</h2>
<h3>Window Box Catios</h3>
<p>Small enclosures that mount directly onto a window frame, projecting outward like a bay window. Affordable, easy to install, and suitable for flats.</p>

<h3>Lean-To Catios</h3>
<p>Larger enclosures that lean against an exterior wall, accessed via a cat flap or window. Good for ground-floor properties with a garden or yard.</p>

<h3>Free-Standing Catios</h3>
<p>Standalone structures connected to the house by a tunnel or placed independently in the garden. Offer the most space but require more investment.</p>

<h3>Balcony Catios</h3>
<p>Mesh netting or screening that encloses a balcony. Popular in flats and apartments (check your lease before installing).</p>

<h2 id="how-to-build">How Do You Build a Simple Catio?</h2>
<ol>
<li><strong>Plan the size and location</strong> &mdash; Choose a spot near a window or door with good natural light</li>
<li><strong>Build the frame</strong> &mdash; Use pressure-treated timber for outdoor durability</li>
<li><strong>Attach mesh</strong> &mdash; Use galvanised wire mesh (no larger than 25 mm gaps) or UV-resistant cat netting</li>
<li><strong>Add a roof</strong> &mdash; Include a solid or translucent roof section for weather protection</li>
<li><strong>Install shelves and perches</strong> &mdash; Give cats vertical climbing options inside the catio</li>
<li><strong>Add enrichment</strong> &mdash; Include scratching posts, cat grass, and safe plants</li>
<li><strong>Create access</strong> &mdash; Install a cat flap in a window or use a purpose-built tunnel</li>
</ol>

{products_section([
    ("B095PC82PP", "PawHut Outdoor Cat Enclosure with Shelter", "Large walk-in catio with multiple platforms, ramps, and a weatherproof shelter. Fir wood construction. 180 x 88 x 178 cm.", "~£200"),
    ("B0BSZKKFQM", "Elecwish Outdoor Cat House Enclosure", "Compact wooden catio with three tiers and mesh panels. Weather-resistant design. 71 x 39 x 131 cm.", "~£110"),
    ("B082YCQRHW", "ProtectaPet Cat Fence Barrier", "Rotating paddle barrier system that prevents cats from climbing over garden fences. Turns your entire garden into a safe cat enclosure.", "~£45 per metre"),
    ("B09B28MKC3", "SureFlap Microchip Cat Flap", "Selective entry cat flap that opens only for registered microchips. Ideal for catio access points.", "~£70"),
])}

{comparison_table(
    ["Product", "Type", "Size", "Assembly", "Approx. Price"],
    [
        [f'<a href="https://www.amazon.co.uk/dp/B095PC82PP?tag={AMAZON_TAG}" rel="nofollow noopener">PawHut Enclosure</a>', "Walk-in catio", "180x88x178 cm", "Self-assembly", "~£200"],
        [f'<a href="https://www.amazon.co.uk/dp/B0BSZKKFQM?tag={AMAZON_TAG}" rel="nofollow noopener">Elecwish Cat House</a>', "Compact catio", "71x39x131 cm", "Self-assembly", "~£110"],
        [f'<a href="https://www.amazon.co.uk/dp/B082YCQRHW?tag={AMAZON_TAG}" rel="nofollow noopener">ProtectaPet Barrier</a>', "Fence barrier", "Per metre", "DIY/Professional", "~£45/m"],
        [f'<a href="https://www.amazon.co.uk/dp/B09B28MKC3?tag={AMAZON_TAG}" rel="nofollow noopener">SureFlap Cat Flap</a>', "Access point", "N/A", "DIY install", "~£70"],
    ]
)}

{glossary_section([
    ("Catio", "A portmanteau of cat and patio; a secure outdoor enclosure for cats"),
    ("Cat-proof fencing", "Barrier systems fitted to existing garden fences that prevent cats from climbing over"),
    ("Galvanised mesh", "Wire mesh coated in zinc to prevent rust, commonly used for outdoor cat enclosures"),
    ("Cat flap", "A small hinged door set into a wall, window, or door allowing independent cat access"),
    ("Microchip cat flap", "A cat flap that reads a pet's microchip and only opens for registered animals"),
])}

{faq_section([
    ("Do I need planning permission for a catio in the UK?", "Most small catios fall under permitted development and do not require planning permission. However, if you live in a conservation area, listed building, or leasehold property, check with your local council or landlord first."),
    ("How much does a catio cost to build?", "A simple window box catio can be built for £50-£100 in materials. Pre-made walk-in catios range from £100-£500. Custom-built professional catios can cost £500-£2,000+."),
    ("Is a catio safe in winter?", "Yes, but provide a weatherproof shelter section, warm bedding, and allow your cat to come back inside freely. Most cats will self-regulate their outdoor time in cold weather."),
    ("Can I put a catio on a balcony?", "Yes, balcony catios are popular for flat dwellers. Use cat-safe mesh netting to enclose the space. Always check your lease or building regulations first."),
    ("How do I stop other cats getting into my catio?", "Use a microchip cat flap for the access point. Ensure all mesh joins are secure with no gaps. Add a solid base or bury mesh into the ground to prevent digging under."),
], slug)}

{sources_section()}

{internal_html}

{author_box()}
{cta_block()}
{affiliate_disclosure()}'''
    return body, "cat outdoor enclosure catio"


def gen_behaviour(title, slug, internal_html):
    qa = quick_answer_box("Indoor cat behaviour includes kneading, head bunting, slow blinking, zoomies, chattering at windows, and territorial marking. Understanding these behaviours helps you meet your indoor cat's needs and identify signs of stress or illness early.")
    toc = toc_block([
        ("common", "Common Indoor Cat Behaviours Explained"),
        ("body-language", "How to Read Your Indoor Cat's Body Language"),
        ("stress-signs", "Signs of Stress in Indoor Cats"),
        ("reducing-stress", "How to Reduce Stress in Indoor Cats"),
        ("products", "Recommended Products"),
        ("comparison", "Product Comparison"),
        ("glossary", "Key Terms / Glossary"),
        ("faq", "Frequently Asked Questions"),
        ("sources", "Sources & References"),
    ])
    body = f'''{qa}
{toc}

<h2 id="common">What Are Common Indoor Cat Behaviours and What Do They Mean?</h2>

<h3>Kneading</h3>
<p>When cats push their paws alternately against soft surfaces, it is called kneading. This behaviour originates from kittenhood (stimulating milk flow from the mother) and indicates contentment and comfort in adult cats.</p>

<h3>Head Bunting</h3>
<p>When your cat rubs their head against you or objects, they are depositing scent from glands on their cheeks and forehead. This marks you as part of their territory and is a sign of affection and trust.</p>

<h3>Slow Blinking</h3>
<p>A slow blink is often called a &ldquo;cat kiss.&rdquo; Research published in Scientific Reports (2020) confirmed that slow blinking is a positive communication signal between cats and humans.</p>

<h3>The Zoomies</h3>
<p>Sudden bursts of frantic running, usually at dawn or dusk, are normal for indoor cats. They release pent-up energy from a sedentary day. Regular play sessions can reduce the intensity.</p>

<h3>Chattering at Windows</h3>
<p>The rapid jaw chattering many cats do when watching birds through windows is thought to be a frustrated hunting response or a jaw-readying reflex for the killing bite.</p>

<h3>Bringing You &ldquo;Gifts&rdquo;</h3>
<p>Indoor cats may bring you toys, socks, or other items. This may be a leftover hunting instinct &mdash; sharing &ldquo;prey&rdquo; with family members.</p>

<h2 id="body-language">How Do You Read Your Indoor Cat's Body Language?</h2>
<ul>
<li><strong>Tail up</strong> &mdash; Happy, confident, greeting</li>
<li><strong>Tail puffed up</strong> &mdash; Frightened or agitated</li>
<li><strong>Ears forward</strong> &mdash; Alert, interested</li>
<li><strong>Ears flattened</strong> &mdash; Fearful, aggressive, or in pain</li>
<li><strong>Belly exposure</strong> &mdash; Trust (not always an invitation to touch)</li>
<li><strong>Dilated pupils</strong> &mdash; Excitement, fear, or low light conditions</li>
<li><strong>Arched back</strong> &mdash; Can indicate fear or playful excitement depending on context</li>
</ul>

<h2 id="stress-signs">What Are the Signs of Stress in Indoor Cats?</h2>
<p>Chronic stress in indoor cats can manifest as:</p>
<ul>
<li>Changes in eating habits (eating more or less)</li>
<li>Hiding more than usual</li>
<li>Over-grooming or under-grooming</li>
<li>Inappropriate urination or defecation</li>
<li>Increased aggression or irritability</li>
<li>Excessive vocalisation</li>
<li>Withdrawal from family interaction</li>
</ul>

<h2 id="reducing-stress">How Can You Reduce Stress in Indoor Cats?</h2>
<ul>
<li>Provide <strong>predictable routines</strong> for feeding and play</li>
<li>Ensure <strong>enough resources</strong> (one per cat plus one for litter trays, food stations, and resting areas)</li>
<li>Create <strong>hiding spots</strong> where your cat can retreat</li>
<li>Use <strong>Feliway diffusers</strong> to release calming pheromones</li>
<li>Minimise <strong>household disruption</strong> (loud noises, frequent visitors, renovations)</li>
<li>Provide <strong>vertical territory</strong> for a sense of security</li>
</ul>

{products_section([
    ("B003AKZL16", "Feliway Classic Diffuser", "Releases a synthetic copy of the feline facial pheromone that helps cats feel safe and secure. Covers up to 70 m². 30-day refills available.", "~£18"),
    ("B08GC4P4GP", "Catit Senses 2.0 Digger", "Reduces feeding-related stress by providing a calming, engaging feeding activity. Adjustable difficulty.", "~£12"),
    ("B07FDRG9YB", "PetFusion Cat Scratcher Lounge", "Curved cardboard scratcher that doubles as a lounger. Scratching releases stress and marks territory.", "~£25"),
    ("B0C6GRHYHP", "Cat Calming Treats (Licks)", "Calming paste treats with L-tryptophan and chamomile. Can help during stressful periods like house moves or vet visits.", "~£8"),
])}

{comparison_table(
    ["Product", "Stress Solution", "How It Works", "Duration", "Approx. Price"],
    [
        [f'<a href="https://www.amazon.co.uk/dp/B003AKZL16?tag={AMAZON_TAG}" rel="nofollow noopener">Feliway Classic</a>', "Pheromone", "Diffuses calming scent", "30 days per refill", "~£18"],
        [f'<a href="https://www.amazon.co.uk/dp/B08GC4P4GP?tag={AMAZON_TAG}" rel="nofollow noopener">Catit Digger</a>', "Enrichment", "Engages during feeding", "Permanent", "~£12"],
        [f'<a href="https://www.amazon.co.uk/dp/B07FDRG9YB?tag={AMAZON_TAG}" rel="nofollow noopener">PetFusion Scratcher</a>', "Scratching outlet", "Territory marking", "3-6 months", "~£25"],
        [f'<a href="https://www.amazon.co.uk/dp/B0C6GRHYHP?tag={AMAZON_TAG}" rel="nofollow noopener">Calming Treats</a>', "Supplement", "L-tryptophan + chamomile", "Per use", "~£8"],
    ]
)}

{glossary_section([
    ("Kneading", "A rhythmic paw-pushing behaviour on soft surfaces, indicating contentment"),
    ("Head bunting", "Rubbing the head against objects or people to deposit facial pheromones"),
    ("Crepuscular", "Active primarily during dawn and dusk; the natural activity pattern of cats"),
    ("Pheromone", "A chemical substance produced by an animal that affects the behaviour of other animals of the same species"),
    ("Redirected aggression", "When a cat becomes agitated by one stimulus but directs aggression toward a different target"),
])}

{faq_section([
    ("Why does my indoor cat meow at night?", "Night-time vocalisation can indicate boredom, hunger, or attention-seeking. Ensure your cat has adequate evening play and a late-night meal. If the behaviour starts suddenly, consult your vet to rule out medical causes."),
    ("Is it normal for indoor cats to have zoomies?", "Yes. Zoomies are a normal release of pent-up energy, especially common in indoor cats. Providing regular exercise and play sessions can reduce the frequency and intensity."),
    ("Why does my cat knock things off tables?", "This behaviour is often attention-seeking or investigatory. Cats are fascinated by the physics of falling objects. Providing interactive toys and play sessions can redirect this behaviour."),
    ("Why does my indoor cat spray?", "Spraying (urine marking on vertical surfaces) is territorial behaviour. In indoor cats, it often indicates stress &mdash; such as seeing outdoor cats through windows, household changes, or conflict with other household cats. Feliway diffusers and vet consultation can help."),
    ("Should I punish my cat for bad behaviour?", "Never. Cats do not understand punishment and it increases stress. Instead, redirect unwanted behaviour by providing appropriate outlets (scratching posts instead of furniture, toys instead of hands) and rewarding desired behaviour with treats and praise."),
], slug)}

{sources_section()}

{internal_html}

{author_box()}
{cta_block()}
{affiliate_disclosure()}'''
    return body, "cat behaviour indoors relaxed"


def gen_scratching_posts(title, slug, internal_html):
    qa = quick_answer_box("The best scratching posts for indoor cats in the UK are tall (at least 80 cm), sturdy, wrapped in sisal rope, and have a heavy, stable base. Cats need to stretch fully when scratching, so taller is better. Place posts near sleeping areas and furniture your cat currently scratches.")
    toc = toc_block([
        ("why-scratching", "Why Do Indoor Cats Need Scratching Posts?"),
        ("choosing", "How to Choose the Right Scratching Post"),
        ("types", "Types of Scratching Posts"),
        ("placement", "Where to Place Scratching Posts"),
        ("products", "Recommended Products"),
        ("comparison", "Product Comparison"),
        ("glossary", "Key Terms / Glossary"),
        ("faq", "Frequently Asked Questions"),
        ("sources", "Sources & References"),
    ])
    body = f'''{qa}
{toc}

<h2 id="why-scratching">Why Do Indoor Cats Need Scratching Posts?</h2>
<p>Scratching is a fundamental feline behaviour, not a destructive habit. Cats scratch to:</p>
<ul>
<li><strong>Maintain claws</strong> &mdash; Removes dead outer claw sheaths</li>
<li><strong>Mark territory</strong> &mdash; Leaves both visual marks and scent from paw glands</li>
<li><strong>Stretch muscles</strong> &mdash; Full-body stretch that exercises shoulder and leg muscles</li>
<li><strong>Relieve stress</strong> &mdash; Scratching is a displacement behaviour that reduces anxiety</li>
</ul>
<p>Without appropriate scratching surfaces, indoor cats will inevitably use furniture, carpets, and wallpaper. The RSPCA advises providing multiple scratching posts throughout the home.</p>

<h2 id="choosing">How Do You Choose the Right Scratching Post?</h2>
<ul>
<li><strong>Height</strong> &mdash; Minimum 80 cm tall so cats can stretch fully. Taller is better.</li>
<li><strong>Stability</strong> &mdash; Must not wobble or tip when used vigorously. Heavy base essential.</li>
<li><strong>Material</strong> &mdash; Sisal rope is most popular and durable. Some cats prefer sisal fabric, cardboard, or wood.</li>
<li><strong>Orientation</strong> &mdash; Most cats prefer vertical scratching, but some like horizontal or angled surfaces. Offer variety initially.</li>
</ul>

<h2 id="types">What Types of Scratching Posts Are Available?</h2>
<h3>Vertical Sisal Posts</h3>
<p>The classic tall post wrapped in sisal rope. Available freestanding or as part of cat trees.</p>
<h3>Cardboard Scratchers</h3>
<p>Flat or angled corrugated cardboard that cats shred. Affordable but needs replacing regularly.</p>
<h3>Wall-Mounted Scratchers</h3>
<p>Panels that attach directly to the wall, saving floor space and protecting walls.</p>
<h3>Scratching Mats and Pads</h3>
<p>Horizontal scratching surfaces placed on the floor. Some wrap around table legs.</p>

<h2 id="placement">Where Should You Place Scratching Posts?</h2>
<ul>
<li><strong>Near sleeping areas</strong> &mdash; Cats often scratch when they wake up</li>
<li><strong>Next to furniture</strong> your cat currently scratches &mdash; Provides an acceptable alternative</li>
<li><strong>Near entry points</strong> to rooms &mdash; Territory marking locations</li>
<li><strong>In social areas</strong> &mdash; Where the family spends time</li>
</ul>

{products_section([
    ("B07V45QFSD", "SmartCat Pioneer Pet Ultimate Scratching Post", "91 cm tall with heavy 40 x 40 cm base. Woven sisal fibre (not rope) provides excellent scratching texture. Extremely stable.", "~£45"),
    ("B07FDRG9YB", "PetFusion Ultimate Cat Scratcher Lounge", "Reversible curved cardboard scratcher that doubles as a lounger. Recycled cardboard, organic catnip included.", "~£25"),
    ("B08YNCLDDZ", "FEANDREA Cat Scratching Post with Platform", "Multi-function post with sisal-wrapped column and plush-covered platforms. 82 cm tall with stable base.", "~£30"),
    ("B07D58KYFN", "FUKUMARU Wall-Mounted Cat Scratcher", "Natural sisal wall pad that saves floor space. Mounts with included screws. Two-pack available.", "~£20"),
])}

{comparison_table(
    ["Product", "Material", "Height/Size", "Orientation", "Approx. Price"],
    [
        [f'<a href="https://www.amazon.co.uk/dp/B07V45QFSD?tag={AMAZON_TAG}" rel="nofollow noopener">SmartCat Ultimate</a>', "Woven sisal", "91 cm", "Vertical", "~£45"],
        [f'<a href="https://www.amazon.co.uk/dp/B07FDRG9YB?tag={AMAZON_TAG}" rel="nofollow noopener">PetFusion Lounge</a>', "Cardboard", "46 x 27 cm", "Horizontal/angled", "~£25"],
        [f'<a href="https://www.amazon.co.uk/dp/B08YNCLDDZ?tag={AMAZON_TAG}" rel="nofollow noopener">FEANDREA Post</a>', "Sisal rope", "82 cm", "Vertical", "~£30"],
        [f'<a href="https://www.amazon.co.uk/dp/B07D58KYFN?tag={AMAZON_TAG}" rel="nofollow noopener">FUKUMARU Wall</a>', "Sisal", "40 x 25 cm", "Vertical (wall)", "~£20"],
    ]
)}

{glossary_section([
    ("Sisal", "A natural plant fibre used to wrap scratching posts; durable and satisfying for cats to scratch"),
    ("Claw sheath", "The outer dead layer of a cat's claw that is removed through scratching"),
    ("Displacement behaviour", "An activity performed out of context, often during times of conflict or stress, such as scratching"),
    ("Territorial marking", "Behaviour including scratching, spraying, and rubbing that deposits scent to claim territory"),
    ("Corrugated cardboard scratcher", "A scratching surface made from layered ridged cardboard that cats shred during use"),
])}

{faq_section([
    ("How do I get my cat to use a scratching post instead of furniture?", "Place the post right next to the furniture being scratched. Rub catnip on the post. When your cat uses it, reward with treats. Cover the furniture temporarily with double-sided tape or tin foil, which cats dislike."),
    ("How many scratching posts does an indoor cat need?", "At least one per room your cat frequents. Multiple posts in different materials and orientations let your cat choose their preference. In multi-cat homes, provide one per cat plus extras."),
    ("Should I get a vertical or horizontal scratcher?", "Observe your cat. If they scratch walls and furniture legs, they prefer vertical. If they scratch carpets and rugs, they prefer horizontal. Many cats enjoy both, so offering variety is ideal."),
    ("How long does a sisal scratching post last?", "A quality sisal-wrapped post typically lasts 1-3 years depending on use. Replace when the sisal becomes shredded and loose. Some posts have replaceable sisal sleeves."),
    ("Is it normal for my cat to scratch after eating?", "Yes. Post-meal scratching is a common behaviour that may relate to territory marking around feeding areas. Place a scratching post near your cat's feeding station."),
], slug)}

{sources_section()}

{internal_html}

{author_box()}
{cta_block()}
{affiliate_disclosure()}'''
    return body, "cat scratching post indoors"


def gen_vertical_space(title, slug, internal_html):
    qa = quick_answer_box("Create vertical space for indoor cats using wall-mounted shelves, tall cat trees, floating walkways, ceiling-height climbing poles, and window perches. Vertical territory is essential for indoor cats' mental health, providing security, exercise, and environmental enrichment.")
    toc = toc_block([
        ("why-vertical", "Why Is Vertical Space Important for Indoor Cats?"),
        ("options", "Vertical Space Options for Every Budget"),
        ("planning", "How to Plan a Vertical Cat Space"),
        ("products", "Recommended Products"),
        ("comparison", "Product Comparison"),
        ("glossary", "Key Terms / Glossary"),
        ("faq", "Frequently Asked Questions"),
        ("sources", "Sources & References"),
    ])
    body = f'''{qa}
{toc}

<h2 id="why-vertical">Why Is Vertical Space Important for Indoor Cats?</h2>
<p>In nature, cats are both predators and prey. Height provides security &mdash; from an elevated position, a cat can survey their territory, spot potential threats, and rest safely. For indoor cats, vertical space is even more critical because horizontal floor space is limited.</p>
<p>International Cat Care identifies vertical territory as one of the five pillars of a healthy feline environment. In multi-cat homes, vertical space dramatically reduces conflict by allowing cats to establish hierarchy without direct confrontation.</p>

<h2 id="options">What Vertical Space Options Are Available for Indoor Cats?</h2>

<h3>Wall-Mounted Cat Shelves</h3>
<p>Individual shelves screwed into the wall at varying heights create a climbing route. Available in wood, carpet-covered, or sisal-wrapped designs. Cost-effective and customisable.</p>

<h3>Cat Walkways and Bridges</h3>
<p>Elevated pathways that run along walls at ceiling height. Give cats a highway around the room. Some include rope bridges for added fun.</p>

<h3>Floor-to-Ceiling Poles</h3>
<p>Tension-mounted poles with platforms at intervals. Minimal footprint, maximum height. Some include sisal-wrapped sections for scratching.</p>

<h3>Tall Cat Trees</h3>
<p>Traditional multi-platform structures. Choose the tallest your ceiling allows. Look for designs with staggered platforms for easy climbing.</p>

<h3>Window Perches</h3>
<p>Suction-cup or bracket-mounted beds on windows combine height with outdoor viewing enrichment.</p>

<h2 id="planning">How Do You Plan a Vertical Cat Space?</h2>
<ol>
<li><strong>Map the room</strong> &mdash; Identify walls, windows, and existing furniture that can serve as stepping stones</li>
<li><strong>Create routes</strong> &mdash; Cats need a way up and a way down. Ensure multiple paths to prevent territorial blocking</li>
<li><strong>Vary heights</strong> &mdash; Offer platforms at different levels to suit multiple cats or moods</li>
<li><strong>Include rest stops</strong> &mdash; At least one enclosed or semi-enclosed sleeping spot at height</li>
<li><strong>Test stability</strong> &mdash; Everything must be securely mounted. Use wall studs or appropriate anchors for plasterboard</li>
<li><strong>Add scratch surfaces</strong> &mdash; Include sisal sections along climbing routes</li>
</ol>

{products_section([
    ("B07D58KYFN", "FUKUMARU Cat Wall Shelves (Set of 5)", "Solid wood shelves with non-slip pads. Creates a climbing stairway on any wall. Weight limit 10 kg per shelf.", "~£40"),
    ("B0882WPWJ5", "Go Pet Club Floor-to-Ceiling Cat Tree", "Tension-mounted pole system reaching up to 274 cm. Multiple platforms and sisal scratching sections.", "~£55"),
    ("B08YNCLDDZ", "FEANDREA Cat Tower 143 cm", "Tall multi-tier cat tree with observation platform. Slim 40 x 40 cm footprint.", "~£45"),
    ("B073WBX7BM", "ZALALOVA Cat Window Perch", "Heavy-duty suction cup window bed. Adds an elevated resting spot with outdoor views.", "~£18"),
])}

{comparison_table(
    ["Product", "Type", "Height", "Floor Space", "Approx. Price"],
    [
        [f'<a href="https://www.amazon.co.uk/dp/B07D58KYFN?tag={AMAZON_TAG}" rel="nofollow noopener">FUKUMARU Shelves</a>', "Wall-mounted", "Custom", "Zero", "~£40"],
        [f'<a href="https://www.amazon.co.uk/dp/B0882WPWJ5?tag={AMAZON_TAG}" rel="nofollow noopener">Go Pet Club Pole</a>', "Ceiling tension", "Up to 274 cm", "36 x 36 cm", "~£55"],
        [f'<a href="https://www.amazon.co.uk/dp/B08YNCLDDZ?tag={AMAZON_TAG}" rel="nofollow noopener">FEANDREA Tower</a>', "Cat tree", "143 cm", "40 x 40 cm", "~£45"],
        [f'<a href="https://www.amazon.co.uk/dp/B073WBX7BM?tag={AMAZON_TAG}" rel="nofollow noopener">Window Perch</a>', "Suction cup", "Window height", "Zero", "~£18"],
    ]
)}

{glossary_section([
    ("Vertical territory", "Elevated spaces that cats use for observation, rest, and establishing hierarchy"),
    ("Five pillars of feline environment", "International Cat Care's framework: safe space, multiple resources, play/predation, positive human contact, and scent management"),
    ("Tension pole", "A floor-to-ceiling post held in place by spring tension, requiring no permanent fixings"),
    ("Cat highway", "An elevated walkway system that allows cats to traverse a room without touching the floor"),
    ("Resource blocking", "When one cat controls access to food, litter, or pathways, often causing stress to other cats in the home"),
])}

{faq_section([
    ("Will wall-mounted cat shelves damage my walls?", "Shelves require screws into the wall, which will leave holes if removed. Use wall plugs appropriate for your wall type (plasterboard, brick, etc.) to ensure secure mounting."),
    ("How high should cat shelves be mounted?", "Most cats enjoy heights of 1.5-2 metres above the floor. Ensure shelves are staggered so cats can reach them easily. Leave at least 30 cm between shelf levels for comfortable jumping."),
    ("Can old cats use vertical spaces?", "Yes, but provide easy access with closely spaced steps or ramps. Older cats may not jump as high, so lower platforms and gentle inclines are helpful."),
    ("Do I need vertical space for a single cat?", "Yes. Even single cats benefit greatly from vertical territory. It provides exercise, security, and enrichment that flat floor space alone cannot offer."),
    ("How do I encourage my cat to use wall shelves?", "Place treats on the shelves initially. Sprinkle catnip on platforms. Use a wand toy to lure your cat up the shelves. Position them near windows for added appeal."),
], slug)}

{sources_section()}

{internal_html}

{author_box()}
{cta_block()}
{affiliate_disclosure()}'''
    return body, "cat climbing shelves wall indoors"


def gen_health_checks(title, slug, internal_html):
    qa = quick_answer_box("Indoor cat health checks should include monitoring weight, teeth, eyes, ears, coat, litter habits, and behaviour. Schedule vet visits at least annually, and perform weekly home checks. Indoor cats are prone to obesity, dental disease, urinary issues, and stress-related conditions.")
    toc = toc_block([
        ("why-checks", "Why Do Indoor Cats Need Regular Health Checks?"),
        ("home-checklist", "Weekly Home Health Check Routine"),
        ("warning-signs", "Warning Signs to Watch For"),
        ("common-issues", "Common Health Issues in Indoor Cats"),
        ("products", "Recommended Products"),
        ("comparison", "Product Comparison"),
        ("glossary", "Key Terms / Glossary"),
        ("faq", "Frequently Asked Questions"),
        ("sources", "Sources & References"),
    ])
    body = f'''{qa}
{toc}

<h2 id="why-checks">Why Do Indoor Cats Need Regular Health Checks?</h2>
<p>Indoor cats are experts at hiding illness. In the wild, showing weakness makes animals vulnerable to predators, and domestic cats retain this instinct. By the time symptoms become obvious, a condition may be quite advanced.</p>
<p>The PDSA recommends annual vet check-ups for adult cats and twice-yearly visits for seniors (over 7 years). Between vet visits, regular home monitoring helps catch changes early.</p>

<h2 id="home-checklist">What Does a Weekly Home Health Check Look Like?</h2>
<ul>
<li><strong>Weight</strong> &mdash; Weigh monthly using a pet or kitchen scale. Note any gains or losses of more than 200 g</li>
<li><strong>Eyes</strong> &mdash; Should be clear and bright. Look for discharge, cloudiness, or squinting</li>
<li><strong>Ears</strong> &mdash; Check for excessive wax, redness, odour, or head shaking</li>
<li><strong>Mouth</strong> &mdash; Look for red gums, bad breath, drooling, or difficulty eating</li>
<li><strong>Coat</strong> &mdash; Should be glossy and even. Check for bald patches, excessive shedding, dandruff, or parasites</li>
<li><strong>Body</strong> &mdash; Run your hands over the body feeling for lumps, bumps, or areas of tenderness</li>
<li><strong>Litter habits</strong> &mdash; Monitor frequency, consistency, and any blood in urine or stool</li>
<li><strong>Behaviour</strong> &mdash; Note changes in activity, appetite, drinking, sleeping, or social interaction</li>
</ul>

<h2 id="warning-signs">What Warning Signs Should Indoor Cat Owners Watch For?</h2>
<p>Contact your vet if you notice any of the following:</p>
<ul>
<li>Increased or decreased water intake</li>
<li>Changes in appetite lasting more than 24 hours</li>
<li>Straining in the litter tray (especially male cats &mdash; can indicate urinary blockage, a life-threatening emergency)</li>
<li>Vomiting more than once in 24 hours</li>
<li>Lethargy or reluctance to move</li>
<li>Sudden weight loss or gain</li>
<li>Laboured or open-mouth breathing</li>
<li>Limping or difficulty jumping</li>
</ul>

<h2 id="common-issues">What Health Issues Are Most Common in Indoor Cats?</h2>
<h3>Obesity</h3>
<p>The number one health concern for indoor cats. Leads to diabetes, joint disease, and reduced lifespan. Prevention through portion control and exercise is key.</p>

<h3>Dental Disease</h3>
<p>Affects up to 85% of cats over 3. Indoor cats may develop plaque faster due to softer diets. Regular dental care is essential.</p>

<h3>Urinary Tract Issues</h3>
<p>Feline Lower Urinary Tract Disease (FLUTD) is more common in indoor cats, possibly due to reduced water intake and stress. Encourage water consumption with a pet fountain.</p>

<h3>Stress-Related Conditions</h3>
<p>Feline Idiopathic Cystitis (FIC), over-grooming, and anxiety-related behaviours are more prevalent in indoor cats. Environmental enrichment is the primary treatment.</p>

{products_section([
    ("B074N2MFZV", "PetSafe Drinkwell Water Fountain", "Encourages cats to drink more with flowing water. 1.8 litre capacity. Replaceable carbon filters keep water fresh.", "~£25"),
    ("B08CMX5BXS", "Digital Pet Scale", "Accurate to 10 g. Essential for monitoring your indoor cat's weight at home. Tray design helps cats sit still.", "~£20"),
    ("B078JHCYMH", "Virbac Enzymatic Cat Toothpaste", "Poultry-flavoured, safe-to-swallow toothpaste for regular dental care at home.", "~£10"),
    ("B003AKZL16", "Feliway Classic Diffuser", "Reduces stress that can trigger urinary and behavioural health problems in indoor cats.", "~£18"),
])}

{comparison_table(
    ["Product", "Health Area", "Frequency of Use", "Essential?", "Approx. Price"],
    [
        [f'<a href="https://www.amazon.co.uk/dp/B074N2MFZV?tag={AMAZON_TAG}" rel="nofollow noopener">Drinkwell Fountain</a>', "Hydration", "Continuous", "Highly recommended", "~£25"],
        [f'<a href="https://www.amazon.co.uk/dp/B08CMX5BXS?tag={AMAZON_TAG}" rel="nofollow noopener">Pet Scale</a>', "Weight monitoring", "Monthly", "Recommended", "~£20"],
        [f'<a href="https://www.amazon.co.uk/dp/B078JHCYMH?tag={AMAZON_TAG}" rel="nofollow noopener">Cat Toothpaste</a>', "Dental health", "2-3x per week", "Recommended", "~£10"],
        [f'<a href="https://www.amazon.co.uk/dp/B003AKZL16?tag={AMAZON_TAG}" rel="nofollow noopener">Feliway Diffuser</a>', "Stress management", "Continuous", "Helpful", "~£18"],
    ]
)}

{glossary_section([
    ("FLUTD", "Feline Lower Urinary Tract Disease, a group of conditions affecting the bladder and urethra"),
    ("Feline Idiopathic Cystitis (FIC)", "Bladder inflammation in cats with no identifiable cause, often linked to stress"),
    ("Body condition score", "A veterinary assessment tool rating body fat on a scale of 1-9"),
    ("Urinary blockage", "A life-threatening emergency where a cat cannot urinate, most common in male cats"),
    ("Dental prophylaxis", "Professional dental cleaning performed by a vet under anaesthesia"),
])}

{faq_section([
    ("How often should an indoor cat see the vet?", "Adult indoor cats should have an annual check-up including vaccination boosters and dental assessment. Senior cats (7+ years) benefit from twice-yearly visits. Kittens need visits at 8, 12, and 16 weeks for vaccinations."),
    ("Do indoor cats still need vaccinations?", "Yes. Even indoor cats should be vaccinated against feline panleukopenia (enteritis) and cat flu. These viruses can be brought into the home on shoes and clothing. Discuss with your vet which vaccines are appropriate."),
    ("Do indoor cats need flea and worm treatment?", "Indoor cats have a lower risk but can still get parasites from other pets, visitors, or even open windows. Discuss a preventive regime with your vet based on your specific circumstances."),
    ("How can I tell if my cat is in pain?", "Cats hide pain well. Signs include decreased appetite, hiding, reluctance to jump or climb, changes in grooming, vocalisation when touched, and altered facial expressions (squinting, flattened ears)."),
    ("What is the most important home health check I can do?", "Monitoring weight is arguably the most important. Gradual weight changes (gain or loss) are early indicators of many health conditions including diabetes, thyroid disease, and kidney disease."),
], slug)}

{sources_section()}

{internal_html}

{author_box()}
{cta_block()}
{affiliate_disclosure()}'''
    return body, "cat health check vet"


def gen_transition(title, slug, internal_html):
    qa = quick_answer_box("Transition an outdoor cat to indoor living gradually over 2-4 weeks by increasing indoor time, providing enrichment, blocking escape routes, and creating a stimulating indoor environment. Use puzzle feeders, window perches, and interactive play to replace outdoor stimulation.")
    toc = toc_block([
        ("why-transition", "Why Might You Need to Transition a Cat Indoors?"),
        ("preparation", "How to Prepare Your Home"),
        ("step-by-step", "Step-by-Step Transition Process"),
        ("challenges", "Common Challenges and Solutions"),
        ("products", "Recommended Products"),
        ("comparison", "Product Comparison"),
        ("glossary", "Key Terms / Glossary"),
        ("faq", "Frequently Asked Questions"),
        ("sources", "Sources & References"),
    ])
    body = f'''{qa}
{toc}

<h2 id="why-transition">Why Might You Need to Transition a Cat to Indoor Living?</h2>
<p>There are many valid reasons for transitioning an outdoor cat indoors:</p>
<ul>
<li><strong>Moving home</strong> &mdash; Particularly to a flat or busy road area</li>
<li><strong>Medical reasons</strong> &mdash; Post-surgery recovery, FIV-positive diagnosis, or chronic illness</li>
<li><strong>Safety concerns</strong> &mdash; Traffic, toxic neighbours' plants, aggressive animals in the area</li>
<li><strong>Age</strong> &mdash; Senior cats may benefit from the safety of indoor living</li>
<li><strong>Wildlife protection</strong> &mdash; Reducing predation on garden birds and small mammals</li>
</ul>
<p>Cats Protection advises that while the transition can be challenging, most outdoor cats can adapt to indoor living with patience and proper enrichment.</p>

<h2 id="preparation">How Do You Prepare Your Home for a Formerly Outdoor Cat?</h2>
<ul>
<li>Install <strong>multiple scratching posts</strong> to replace trees and fences</li>
<li>Set up <strong>window perches</strong> for outdoor observation</li>
<li>Create <strong>vertical spaces</strong> with cat trees and wall shelves</li>
<li>Provide <strong>hiding spots</strong> (boxes, igloos, covered beds)</li>
<li>Grow <strong>cat grass and catnip</strong> for natural sensory enrichment</li>
<li>Set up <strong>puzzle feeders</strong> to replace hunting</li>
<li>Install <strong>Feliway diffusers</strong> to reduce transition stress</li>
<li>Secure all windows and ensure doors have self-closers if needed</li>
</ul>

<h2 id="step-by-step">What Is the Best Step-by-Step Transition Process?</h2>
<h3>Week 1: Increase Indoor Time</h3>
<p>Begin keeping your cat indoors during the evening and night. Provide enrichment and play sessions during these indoor hours. Continue allowing supervised outdoor access during the day.</p>

<h3>Week 2: Reduce Outdoor Access</h3>
<p>Limit outdoor time to one or two supervised sessions. Increase indoor play to 2-3 interactive sessions daily. Begin using puzzle feeders for meals.</p>

<h3>Week 3: Indoor Only with Distraction</h3>
<p>Keep your cat fully indoors. This is typically the hardest week. Expect vocalisation, door-scratching, and attempts to escape. Stay patient, increase play frequency, and use Feliway.</p>

<h3>Week 4+: Establishing Routine</h3>
<p>Most cats begin to settle by the fourth week. Maintain enrichment, play schedules, and consider a catio for supervised outdoor access.</p>

<h2 id="challenges">What Are the Common Challenges When Transitioning?</h2>
<h3>Excessive Meowing</h3>
<p>Loud, persistent meowing at doors is the most common challenge. Do not give in &mdash; letting the cat out intermittently reinforces the behaviour. Instead, redirect with play and ignore the meowing.</p>

<h3>Escape Attempts</h3>
<p>Install draught excluders under doors, use window locks, and brief visitors to close doors quickly. Consider a double-door entry system (airlock).</p>

<h3>Spraying or Litter Avoidance</h3>
<p>Stress from the transition can cause litter tray issues. Provide extra trays, use Feliway, and maintain consistency in routine.</p>

{products_section([
    ("B003AKZL16", "Feliway Classic Diffuser", "Essential during the transition period. Releases calming pheromones to reduce stress and anxiety.", "~£18"),
    ("B073WBX7BM", "ZALALOVA Cat Window Perch", "Provides outdoor observation for a cat missing the outdoors. Suction cup mount, 22 kg capacity.", "~£18"),
    ("B00D3NI2PG", "Trixie 5-in-1 Activity Centre", "Replaces the mental stimulation of outdoor hunting with indoor puzzle challenges.", "~£15"),
    ("B000IYSAIW", "Da Bird Cat Toy", "Premium wand toy for intensive play sessions that tire out energetic ex-outdoor cats.", "~£8"),
])}

{comparison_table(
    ["Product", "Transition Purpose", "Replaces", "Priority", "Approx. Price"],
    [
        [f'<a href="https://www.amazon.co.uk/dp/B003AKZL16?tag={AMAZON_TAG}" rel="nofollow noopener">Feliway Diffuser</a>', "Stress reduction", "Outdoor territory confidence", "Essential", "~£18"],
        [f'<a href="https://www.amazon.co.uk/dp/B073WBX7BM?tag={AMAZON_TAG}" rel="nofollow noopener">Window Perch</a>', "Outdoor observation", "Garden sitting", "High", "~£18"],
        [f'<a href="https://www.amazon.co.uk/dp/B00D3NI2PG?tag={AMAZON_TAG}" rel="nofollow noopener">Activity Centre</a>', "Mental stimulation", "Hunting/exploring", "High", "~£15"],
        [f'<a href="https://www.amazon.co.uk/dp/B000IYSAIW?tag={AMAZON_TAG}" rel="nofollow noopener">Da Bird</a>', "Exercise/play", "Running/climbing outdoors", "Essential", "~£8"],
    ]
)}

{glossary_section([
    ("Transition period", "The adjustment time a cat needs when moving from outdoor to indoor living, typically 2-4 weeks"),
    ("Escape-proofing", "Securing doors, windows, and openings to prevent a cat from getting outside"),
    ("Displacement behaviour", "Behaviours like excessive grooming or eating that a cat performs in response to stress or frustration"),
    ("Environmental enrichment", "Modifications to the indoor environment that provide physical and mental stimulation"),
    ("Catio", "A secure outdoor enclosure that provides safe outdoor access for indoor cats"),
])}

{faq_section([
    ("How long does it take for an outdoor cat to adjust to living indoors?", "Most cats begin to settle within 2-4 weeks, though some may take several months. Younger cats and those with a calmer temperament tend to adjust faster."),
    ("Will my outdoor cat be unhappy living indoors?", "Not if the indoor environment is properly enriched. Research by International Cat Care shows that indoor cats with adequate enrichment can have equal or better welfare than outdoor cats."),
    ("Should I let my transitioning cat out if they seem really upset?", "No. Letting a distressed cat outside intermittently teaches them that persistent meowing/scratching works. Stay consistent and increase enrichment instead."),
    ("Can I build a catio to help the transition?", "A catio is an excellent compromise that provides outdoor sensory enrichment without the risks. It can significantly ease the transition for formerly outdoor cats."),
    ("What if my cat refuses to use the litter tray during transition?", "Ensure you have multiple trays in quiet, accessible locations with unscented litter. If problems persist beyond a week, consult your vet to rule out medical causes."),
], slug)}

{sources_section()}

{internal_html}

{author_box()}
{cta_block()}
{affiliate_disclosure()}'''
    return body, "cat looking out window indoors"


def gen_sleep_patterns(title, slug, internal_html):
    qa = quick_answer_box("Indoor cats typically sleep 12-16 hours per day, with peak activity at dawn and dusk. This is normal crepuscular behaviour. Concerning signs include sleeping more than 20 hours, sudden changes in sleep patterns, sleeping in unusual locations, or reluctance to wake for meals.")
    toc = toc_block([
        ("normal-sleep", "How Much Do Indoor Cats Normally Sleep?"),
        ("sleep-cycle", "Understanding the Indoor Cat Sleep Cycle"),
        ("concerning", "When Are Sleep Patterns Concerning?"),
        ("improving", "How to Improve Your Indoor Cat's Sleep Quality"),
        ("products", "Recommended Products"),
        ("comparison", "Product Comparison"),
        ("glossary", "Key Terms / Glossary"),
        ("faq", "Frequently Asked Questions"),
        ("sources", "Sources & References"),
    ])
    body = f'''{qa}
{toc}

<h2 id="normal-sleep">How Much Do Indoor Cats Normally Sleep?</h2>
<p>Indoor cats sleep an average of 12-16 hours per day, with some individuals sleeping up to 18 hours. This is normal feline behaviour. Cats are obligate predators, and in the wild, they conserve energy between hunts by sleeping extensively.</p>
<p>Age significantly affects sleep duration:</p>
<ul>
<li><strong>Kittens (under 1 year)</strong> &mdash; Up to 20 hours per day (growing requires enormous energy)</li>
<li><strong>Adult cats (1-7 years)</strong> &mdash; 12-16 hours per day</li>
<li><strong>Senior cats (7+ years)</strong> &mdash; 16-20 hours per day</li>
</ul>

<h2 id="sleep-cycle">What Does the Indoor Cat Sleep Cycle Look Like?</h2>
<p>Cats are crepuscular, meaning they are most active at dawn and dusk. A typical indoor cat's day looks like:</p>
<ul>
<li><strong>Early morning (4-7 am)</strong> &mdash; Peak activity: running, playing, demanding breakfast</li>
<li><strong>Morning (7-12 pm)</strong> &mdash; Light sleep and dozing</li>
<li><strong>Afternoon (12-5 pm)</strong> &mdash; Deep sleep, often in a sunny spot</li>
<li><strong>Evening (5-8 pm)</strong> &mdash; Second peak activity: play time, dinner</li>
<li><strong>Night (8 pm-4 am)</strong> &mdash; Mix of light sleep and brief active periods</li>
</ul>
<p>Cat sleep includes both light dozing (where ears remain alert to sounds) and deep REM sleep (where you may notice paw twitching and whisker movement).</p>

<h2 id="concerning">When Should Indoor Cat Sleep Patterns Concern You?</h2>
<p>While cats sleep a lot naturally, certain changes warrant veterinary attention:</p>
<ul>
<li><strong>Sudden increase in sleeping</strong> &mdash; Could indicate pain, illness, or depression</li>
<li><strong>Sleeping more than 20 hours</strong> (adult cat) &mdash; May suggest underlying health issues</li>
<li><strong>Sleeping in unusual locations</strong> &mdash; Cats in pain often hide in new spots</li>
<li><strong>Difficulty sleeping</strong> &mdash; Restlessness can indicate pain or hyperthyroidism</li>
<li><strong>Not waking for meals</strong> &mdash; A cat that does not respond to food may be unwell</li>
<li><strong>Excessive night-time activity</strong> in senior cats &mdash; Could indicate cognitive dysfunction</li>
</ul>

<h2 id="improving">How Can You Improve Your Indoor Cat's Sleep Quality?</h2>
<ul>
<li>Provide <strong>multiple comfortable sleeping spots</strong> at different heights and temperatures</li>
<li>Schedule <strong>evening play sessions</strong> to tire your cat before bedtime</li>
<li>Feed a <strong>late-night meal</strong> to prevent early-morning hunger waking</li>
<li>Create a <strong>quiet sleeping area</strong> away from household activity</li>
<li>Maintain <strong>consistent routines</strong> for feeding and play</li>
<li>Use <strong>blackout areas</strong> for daytime deep sleep if your home is very bright</li>
</ul>

{products_section([
    ("B09BFHG6FD", "Catit Vesper Cubo", "Enclosed sleeping pod with memory foam cushion. Elevated design gives security at height. Walnut-finish frame suits modern interiors.", "~£60"),
    ("B07FDRG9YB", "PetFusion Cat Scratcher Lounge", "Curved design doubles as a lounger for comfortable napping. Cats often sleep in it after a scratching session.", "~£25"),
    ("B0BLF4NHXT", "Pecute Self-Warming Cat Bed", "Thermal-reflective lining uses your cat's own body heat. No electricity needed. Machine washable.", "~£16"),
    ("B000IYSAIW", "Da Bird Cat Toy", "Intensive play sessions before bedtime can help reset your cat's sleep schedule and reduce night-time waking.", "~£8"),
])}

{comparison_table(
    ["Product", "Sleep Benefit", "Type", "Washable", "Approx. Price"],
    [
        [f'<a href="https://www.amazon.co.uk/dp/B09BFHG6FD?tag={AMAZON_TAG}" rel="nofollow noopener">Catit Vesper Cubo</a>', "Secure enclosed sleep", "Pod bed", "Cushion only", "~£60"],
        [f'<a href="https://www.amazon.co.uk/dp/B07FDRG9YB?tag={AMAZON_TAG}" rel="nofollow noopener">PetFusion Lounge</a>', "Relaxation post-scratch", "Scratcher/bed", "No (cardboard)", "~£25"],
        [f'<a href="https://www.amazon.co.uk/dp/B0BLF4NHXT?tag={AMAZON_TAG}" rel="nofollow noopener">Self-Warming Bed</a>', "Warmth without electricity", "Flat bed", "Yes", "~£16"],
        [f'<a href="https://www.amazon.co.uk/dp/B000IYSAIW?tag={AMAZON_TAG}" rel="nofollow noopener">Da Bird</a>', "Pre-bedtime exercise", "Wand toy", "N/A", "~£8"],
    ]
)}

{glossary_section([
    ("Crepuscular", "Most active during dawn and dusk, the natural activity pattern of domestic cats"),
    ("REM sleep", "Rapid Eye Movement sleep; the deep sleep stage where dreaming occurs, characterised by paw twitching and whisker movement"),
    ("Polyphasic sleep", "Sleeping in multiple short periods throughout the day rather than one long sleep, typical of cats"),
    ("Cognitive dysfunction syndrome", "Age-related decline in mental function in senior cats, similar to dementia in humans"),
    ("Circadian rhythm", "The internal biological clock regulating sleep-wake cycles over approximately 24 hours"),
])}

{faq_section([
    ("Is it normal for my indoor cat to sleep all day?", "Yes, 12-16 hours of sleep is normal for adult cats. Indoor cats may sleep slightly more due to reduced stimulation. If your cat is active and healthy during waking hours, excessive sleeping is usually not a concern."),
    ("Why does my indoor cat wake me up at 4 am?", "This is natural crepuscular behaviour. To reduce early waking, play vigorously before bedtime, feed a late meal, use timed feeders for an early morning portion, and avoid responding to early-morning demands."),
    ("Do cats dream?", "Research suggests cats do experience REM sleep and likely dream. You may notice paw twitching, whisker movements, and soft vocalisations during deep sleep."),
    ("Should I be worried if my cat's sleep patterns change suddenly?", "Yes. Sudden changes in sleep patterns can indicate pain, illness, or stress. If your cat suddenly sleeps much more or less than usual, or changes their preferred sleeping spots, consult your vet."),
    ("Is it okay to let my indoor cat sleep on my bed?", "There are no health concerns for most people sharing a bed with a healthy indoor cat. It can strengthen your bond. However, if your cat disrupts your sleep with night-time activity, consider providing an equally comfortable alternative nearby."),
], slug)}

{sources_section()}

{internal_html}

{author_box()}
{cta_block()}
{affiliate_disclosure()}'''
    return body, "cat sleeping indoors bed"


def gen_harnesses(title, slug, internal_html):
    qa = quick_answer_box("The best harnesses for indoor cats in the UK are escape-proof vest-style designs that distribute pressure evenly across the chest, not the neck. Start harness training indoors before venturing outside. Look for adjustable, lightweight designs with secure buckle closures.")
    toc = toc_block([
        ("why-harness", "Why Would an Indoor Cat Need a Harness?"),
        ("types", "Types of Cat Harnesses"),
        ("choosing", "How to Choose the Right Harness"),
        ("training", "How to Harness Train Your Indoor Cat"),
        ("products", "Recommended Products"),
        ("comparison", "Product Comparison"),
        ("glossary", "Key Terms / Glossary"),
        ("faq", "Frequently Asked Questions"),
        ("sources", "Sources & References"),
    ])
    body = f'''{qa}
{toc}

<h2 id="why-harness">Why Would an Indoor Cat Need a Harness?</h2>
<p>A harness allows indoor cats to safely experience the outdoors under supervision. Benefits include:</p>
<ul>
<li><strong>Fresh air and sunshine</strong> &mdash; Vitamin D and natural sensory stimulation</li>
<li><strong>Mental enrichment</strong> &mdash; New scents, sights, and sounds to explore</li>
<li><strong>Exercise</strong> &mdash; Walking and exploring at their own pace</li>
<li><strong>Bonding</strong> &mdash; Shared outdoor adventures strengthen the human-cat relationship</li>
<li><strong>Vet visits</strong> &mdash; A harness-trained cat is safer to transport and handle at the vet</li>
</ul>
<p>The Blue Cross notes that not all cats enjoy harness walking, but many indoor cats, especially younger ones, can be successfully trained with patience.</p>

<h2 id="types">What Types of Cat Harnesses Are Available?</h2>
<h3>Vest/Jacket Harnesses</h3>
<p>Full-coverage designs that wrap around the chest and secure with Velcro and/or buckles. Most escape-proof option and most comfortable for cats. Distributes pressure over a wide area.</p>

<h3>H-Style Harnesses</h3>
<p>Two loops connected by a bridge strap &mdash; one around the neck, one behind the front legs. Lightweight but easier for cats to wriggle out of.</p>

<h3>Figure-8 Harnesses</h3>
<p>A single strap that forms a figure-8 around the cat's neck and chest. Simple but less secure and can shift during movement.</p>

<h2 id="choosing">How Do You Choose the Right Cat Harness?</h2>
<ul>
<li><strong>Escape-proof design</strong> &mdash; The most important factor. Cats are remarkably flexible and can back out of poorly fitting harnesses</li>
<li><strong>Proper fit</strong> &mdash; You should be able to fit two fingers between the harness and your cat's body</li>
<li><strong>Lightweight material</strong> &mdash; Cats dislike heavy, bulky harnesses</li>
<li><strong>Secure closures</strong> &mdash; Buckles are more secure than Velcro alone</li>
<li><strong>Reflective elements</strong> &mdash; Useful for low-light visibility</li>
<li><strong>Leash attachment point</strong> &mdash; Should be on the back, not the chest or neck</li>
</ul>

<h2 id="training">How Do You Harness Train an Indoor Cat?</h2>
<ol>
<li><strong>Week 1: Familiarisation</strong> &mdash; Leave the harness near your cat's bed so they can sniff and investigate it. Reward interest with treats.</li>
<li><strong>Week 2: Wearing Indoors</strong> &mdash; Put the harness on loosely for a few minutes daily. Reward with treats and play. Gradually increase wearing time to 15-20 minutes.</li>
<li><strong>Week 3: Leash Indoors</strong> &mdash; Attach the leash and let your cat walk around the house, dragging the leash. Supervise to prevent tangling.</li>
<li><strong>Week 4: Outdoor Introduction</strong> &mdash; Start in a quiet, enclosed garden or patio. Let your cat set the pace. Keep first sessions to 5-10 minutes.</li>
<li><strong>Ongoing</strong> &mdash; Gradually increase outdoor time and explore new areas. Always let your cat lead the walk.</li>
</ol>

{products_section([
    ("B07FDRG8TT", "Rabbitgoo Escape-Proof Cat Harness", "Best-selling vest harness with adjustable chest and neck straps. Reflective strips for visibility. Available in multiple sizes and colours.", "~£12"),
    ("B07BGZYHM9", "Yizhi Miaow Cat Harness and Leash Set", "Soft mesh vest design with breathable fabric. Double security with Velcro and buckle closure. Comes with matching leash.", "~£14"),
    ("B0BG9Q7T5S", "Supakit Cat Harness", "Premium UK-designed harness with ultralight construction and anti-escape features. Developed specifically for cat anatomy.", "~£35"),
    ("B07V3CPFSY", "PetSafe Come With Me Kitty Harness", "H-style harness with bungee leash. Unique sliding chest strap adjusts to movement. Good for first-time harness users.", "~£15"),
])}

{comparison_table(
    ["Product", "Type", "Escape-Proof", "Weight", "Approx. Price"],
    [
        [f'<a href="https://www.amazon.co.uk/dp/B07FDRG8TT?tag={AMAZON_TAG}" rel="nofollow noopener">Rabbitgoo</a>', "Vest", "Excellent", "Light", "~£12"],
        [f'<a href="https://www.amazon.co.uk/dp/B07BGZYHM9?tag={AMAZON_TAG}" rel="nofollow noopener">Yizhi Miaow</a>', "Vest", "Very good", "Ultra-light", "~£14"],
        [f'<a href="https://www.amazon.co.uk/dp/B0BG9Q7T5S?tag={AMAZON_TAG}" rel="nofollow noopener">Supakit</a>', "Vest (premium)", "Excellent", "Ultra-light", "~£35"],
        [f'<a href="https://www.amazon.co.uk/dp/B07V3CPFSY?tag={AMAZON_TAG}" rel="nofollow noopener">PetSafe Kitty</a>', "H-style", "Good", "Very light", "~£15"],
    ]
)}

{glossary_section([
    ("Vest harness", "A full-coverage harness that wraps around the cat's chest and torso like a small vest"),
    ("H-style harness", "A harness design using two loops connected by a bridge strap, forming an H-shape when laid flat"),
    ("Escape-proof", "Designed with features (tight fit, multiple closures, wide coverage) that prevent a cat from wriggling free"),
    ("Bungee leash", "A leash with an elastic section that absorbs sudden pulls, reducing stress on the cat"),
    ("Positive reinforcement", "Training method using rewards (treats, praise) to encourage desired behaviour"),
])}

{faq_section([
    ("Can all cats be harness trained?", "Most cats can learn to accept a harness, but not all will enjoy walking outdoors. Older cats and very timid cats may find the experience stressful. Start training indoors and let your cat set the pace."),
    ("How tight should a cat harness be?", "You should be able to fit two fingers between the harness and your cat's body. Too loose and they can escape; too tight and it will be uncomfortable and restrictive."),
    ("What age can I start harness training?", "Kittens as young as 3-4 months can begin familiarisation with a harness. Early training generally leads to better acceptance of harness walking."),
    ("Should I use a retractable leash for cat walking?", "No. Retractable leashes give too much range and can be dangerous if a cat darts into a road or encounters a dog. Use a fixed 4-6 foot leash for cat walking."),
    ("What if my cat freezes when wearing a harness?", "Freezing is a common initial response. Place the harness on for just 1-2 minutes, reward with treats, and remove. Gradually increase wearing time over days. Most cats adapt within 1-2 weeks of daily practice."),
], slug)}

{sources_section()}

{internal_html}

{author_box()}
{cta_block()}
{affiliate_disclosure()}'''
    return body, "cat harness leash walking outdoors"


# ─── Topic Definitions ───
TOPICS = [
    ("How to Keep Indoor Cats Mentally Stimulated", "how-to-keep-indoor-cats-mentally-stimulated"),
    ("Best Window Perches for Indoor Cats UK", "best-window-perches-for-indoor-cats-uk"),
    ("Indoor Cat Exercise: Creative Ways to Keep Cats Active", "indoor-cat-exercise-creative-ways-to-keep-cats-active"),
    ("How to Create a Cat-Safe Indoor Garden", "how-to-create-a-cat-safe-indoor-garden"),
    ("Best Cat Trees for Small Flats UK", "best-cat-trees-for-small-flats-uk"),
    ("Indoor Cat Nutrition: Do Indoor Cats Need Different Food?", "indoor-cat-nutrition-do-indoor-cats-need-different-food"),
    ("How to Prevent Obesity in Indoor Cats", "how-to-prevent-obesity-in-indoor-cats"),
    ("Indoor Cat Litter Tray Guide: Types and Placement", "indoor-cat-litter-tray-guide-types-and-placement"),
    ("How to Introduce a Second Cat to an Indoor Home", "how-to-introduce-a-second-cat-to-an-indoor-home"),
    ("Indoor Cat Safety: Common Household Hazards", "indoor-cat-safety-common-household-hazards"),
    ("Best Interactive Toys for Indoor Cats UK", "best-interactive-toys-for-indoor-cats-uk"),
    ("How to Help Indoor Cats Cope with Boredom", "how-to-help-indoor-cats-cope-with-boredom"),
    ("Indoor Cat Grooming Routine: Complete Guide", "indoor-cat-grooming-routine-complete-guide"),
    ("How to Set Up a Catio for Your Indoor Cat", "how-to-set-up-a-catio-for-your-indoor-cat"),
    ("Indoor Cat Behaviour: Understanding Your House Cat", "indoor-cat-behaviour-understanding-your-house-cat"),
    ("Best Scratching Posts for Indoor Cats UK", "best-scratching-posts-for-indoor-cats-uk"),
    ("How to Create Vertical Space for Indoor Cats", "how-to-create-vertical-space-for-indoor-cats"),
    ("Indoor Cat Health Checks: What to Watch For", "indoor-cat-health-checks-what-to-watch-for"),
    ("How to Transition an Outdoor Cat to Indoor Living", "how-to-transition-an-outdoor-cat-to-indoor-living"),
    ("Indoor Cat Sleep Patterns: Normal vs Concerning", "indoor-cat-sleep-patterns-normal-vs-concerning"),
    ("Best Harnesses for Indoor Cats Who Want to Explore", "best-harnesses-for-indoor-cats-who-want-to-explore"),
]


def main():
    print(f"{'='*60}")
    print("Phase 23 - Indoor Cats Posts Publisher")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"{'='*60}\n")

    results = {
        "phase": "23_indoor_cats",
        "started": datetime.now().isoformat(),
        "total_attempted": 21,
        "total_published": 0,
        "posts": [],
        "errors": [],
    }

    for idx, (title, slug) in enumerate(TOPICS):
        post_num = idx + 1
        print(f"\n[{post_num}/21] Publishing: {title}")
        print("-" * 50)

        try:
            # 1. Generate content
            print("  Generating content...")
            content, pexels_query = generate_post_content(idx, title, slug)

            # 2. Fetch image from Pexels
            print(f"  Fetching Pexels image: '{pexels_query}'...")
            time.sleep(DELAY)
            img_url, photographer = fetch_pexels_image(pexels_query)
            featured_media_id = None

            if img_url:
                print(f"  Downloading image from Pexels (by {photographer})...")
                time.sleep(DELAY)
                img_bytes, content_type = download_image(img_url)

                if img_bytes:
                    ext = "jpg" if "jpeg" in (content_type or "") else "png"
                    filename = f"indoor-cats-{slug}.{ext}"
                    alt_text = f"{title} - Indoor cats guide by PetHub Online"
                    print(f"  Uploading to WordPress media library...")
                    time.sleep(DELAY)
                    featured_media_id = upload_media(img_bytes, content_type, filename, alt_text)
                    if featured_media_id:
                        print(f"  Media uploaded: ID {featured_media_id}")
                    else:
                        print("  Warning: Media upload failed, proceeding without featured image")
                else:
                    print("  Warning: Image download failed")
            else:
                print("  Warning: No Pexels image found")

            # 3. Create the post
            print("  Creating WordPress post...")
            time.sleep(DELAY)
            post_id, post_url = create_post(title, content, slug, featured_media_id)

            if post_id:
                print(f"  SUCCESS: Post ID {post_id}")
                print(f"  URL: {post_url}")
                results["total_published"] += 1
                results["posts"].append({
                    "number": post_num,
                    "title": title,
                    "slug": slug,
                    "post_id": post_id,
                    "url": post_url,
                    "featured_media_id": featured_media_id,
                    "status": "published",
                })
            else:
                error_msg = f"Failed to create post: {title}"
                print(f"  ERROR: {error_msg}")
                results["errors"].append({
                    "post_number": post_num,
                    "title": title,
                    "error": error_msg,
                })

        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            print(f"  ERROR: {error_msg}")
            traceback.print_exc()
            results["errors"].append({
                "post_number": post_num,
                "title": title,
                "error": error_msg,
            })

    # Save results
    results["completed"] = datetime.now().isoformat()
    results["success_rate"] = f"{results['total_published']}/21"

    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*60}")
    print(f"COMPLETED: {results['total_published']}/21 posts published")
    print(f"Results saved to: {RESULTS_PATH}")
    if results["errors"]:
        print(f"Errors: {len(results['errors'])}")
        for err in results["errors"]:
            print(f"  - Post {err['post_number']}: {err['error']}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
