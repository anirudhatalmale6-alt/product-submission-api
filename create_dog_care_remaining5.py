#!/usr/bin/env python3
"""
Phase 23 - Remaining 5 Dog Care Posts (Posts 6-10 that were missed)
Publishes the 5 missing posts to reach 23 total new posts.
"""

import requests
import json
import time
import os
import sys
import random
from datetime import datetime, timezone

# ── Configuration ────────────────────────────────────────────────────────────
WP_URL = "https://pethubonline.com/wp-json/wp/v2"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_AUTH = (WP_USER, WP_PASS)
WP_HEADERS = {"Accept-Encoding": "gzip, deflate"}
PEXELS_KEY = "dmGyKrZqTlwukxWzOK1EkH4jbEv9EaIDpLGj7eL5MZ07bl6AR9OEoHlB"
AMAZON_TAG = "pethubonline-21"
DOG_CARE_CAT = 1489
RESULTS_FILE = "/var/lib/freelancer/projects/40416335/phase23_dog_care_results.json"
DELAY = 2

# All existing + newly created posts for internal linking
ALL_POSTS = [
    {"title": "First Week with a New Puppy", "url": "https://pethubonline.com/first-week-new-puppy-guide/"},
    {"title": "Puppy Sleep Guide", "url": "https://pethubonline.com/puppy-sleep-guide-by-age/"},
    {"title": "Dog Behaviour Explained", "url": "https://pethubonline.com/dog-behaviour-explained/"},
    {"title": "Dog Dental Health Care Guide", "url": "https://pethubonline.com/dog-dental-health-care-guide/"},
    {"title": "Seasonal Dog Care Guide", "url": "https://pethubonline.com/seasonal-dog-care-guide/"},
    {"title": "Dog Grooming Basics", "url": "https://pethubonline.com/dog-grooming-basics-guide/"},
    {"title": "Best Dog Nail Clippers UK", "url": "https://pethubonline.com/best-dog-nail-clippers-uk/"},
    {"title": "Best Dog Shampoo UK", "url": "https://pethubonline.com/best-dog-shampoo-uk/"},
    {"title": "Best Dog Brushes UK", "url": "https://pethubonline.com/best-dog-brushes-uk/"},
    {"title": "How Often Should You Bathe Your Dog?", "url": "https://pethubonline.com/how-often-bathe-your-dog-uk-guide/"},
    {"title": "Dog Nail Trimming at Home", "url": "https://pethubonline.com/dog-nail-trimming-at-home-guide/"},
    {"title": "How to Brush Your Dog's Teeth", "url": "https://pethubonline.com/how-to-brush-dogs-teeth-properly/"},
    {"title": "Dog Coat Care by Season", "url": "https://pethubonline.com/dog-coat-care-by-season-guide/"},
    {"title": "How to Clean Your Dog's Ears", "url": "https://pethubonline.com/how-to-clean-dogs-ears-safely/"},
    {"title": "How to Keep Your Dog Cool in Summer", "url": "https://pethubonline.com/how-to-keep-dog-cool-summer-uk/"},
    {"title": "Winter Dog Care Guide", "url": "https://pethubonline.com/winter-dog-care-keeping-warm-safe/"},
    {"title": "Dog Skin Care Routine", "url": "https://pethubonline.com/dog-skin-care-routine-dryness-irritation/"},
    {"title": "How to Choose Dog Shampoo UK", "url": "https://pethubonline.com/how-to-choose-right-dog-shampoo-uk/"},
    {"title": "Dog Eye Cleaning Guide", "url": "https://pethubonline.com/dog-eye-cleaning-safe-gentle-methods/"},
    {"title": "How to Detangle Matted Dog Fur", "url": "https://pethubonline.com/how-to-detangle-matted-dog-fur/"},
    {"title": "Dog Bathing Supplies", "url": "https://pethubonline.com/dog-bathing-supplies-everything-you-need/"},
    {"title": "Dog Care After Neutering or Spaying", "url": "https://pethubonline.com/how-to-care-for-dog-after-neutering-spaying/"},
    {"title": "Dog Care Checklist", "url": "https://pethubonline.com/dog-care-checklist-daily-weekly-monthly/"},
    {"title": "Travel Safely with Your Dog UK", "url": "https://pethubonline.com/how-to-travel-safely-with-dog-uk/"},
    {"title": "Dog Care in Rainy Weather", "url": "https://pethubonline.com/dog-care-rainy-weather-happy-dry/"},
    {"title": "How to Care for a Rescue Dog", "url": "https://pethubonline.com/how-to-care-for-rescue-dog-first-30-days/"},
    {"title": "Dog Care on a Budget UK", "url": "https://pethubonline.com/dog-care-on-a-budget-affordable-uk-tips/"},
]


def api_call(method, url, retries=3, **kwargs):
    for attempt in range(retries):
        try:
            resp = method(url, **kwargs)
            if resp.status_code == 429:
                print(f"  Rate limited (429), waiting 10s...")
                time.sleep(10)
                continue
            return resp
        except Exception as e:
            print(f"  Request error: {e}")
            if attempt < retries - 1:
                time.sleep(5)
    return None


def fetch_pexels_image(query):
    resp = api_call(
        requests.get,
        "https://api.pexels.com/v1/search",
        params={"query": query, "orientation": "landscape", "per_page": 5},
        headers={"Authorization": PEXELS_KEY}
    )
    if resp and resp.status_code == 200:
        photos = resp.json().get("photos", [])
        if photos:
            photo = random.choice(photos[:3])
            return photo["src"]["large2x"], photo["photographer"], photo["url"]
    return None, None, None


def upload_image_to_wp(image_url, filename, alt_text=""):
    resp = api_call(requests.get, image_url, headers={"Accept-Encoding": "gzip, deflate"})
    if not resp or resp.status_code != 200:
        return None
    image_data = resp.content
    content_type = resp.headers.get("Content-Type", "image/jpeg")
    if not filename.endswith((".jpg", ".jpeg", ".png", ".webp")):
        filename += ".jpg"
    upload_resp = api_call(
        requests.post,
        f"{WP_URL}/media",
        auth=WP_AUTH,
        headers={
            "Accept-Encoding": "gzip, deflate",
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": content_type,
        },
        data=image_data
    )
    if upload_resp and upload_resp.status_code == 201:
        media = upload_resp.json()
        media_id = media["id"]
        if alt_text:
            api_call(requests.post, f"{WP_URL}/media/{media_id}", auth=WP_AUTH, headers=WP_HEADERS, json={"alt_text": alt_text})
        return media_id
    return None


def build_faq_schema(faqs):
    entities = []
    for faq in faqs:
        entities.append({
            "@type": "Question",
            "name": faq["q"],
            "acceptedAnswer": {"@type": "Answer", "text": faq["a"]}
        })
    schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": entities}
    return f'<script type="application/ld+json">\n{json.dumps(schema, indent=2)}\n</script>'


def get_internal_links(count=3):
    return random.sample(ALL_POSTS, min(count, len(ALL_POSTS)))


def build_internal_links_html(links):
    items = "".join(f'<li><a href="{l["url"]}">{l["title"]}</a></li>\n' for l in links)
    return f"""
<div style="background:#f0f7f0;border-left:4px solid #2e7d32;padding:15px 20px;margin:25px 0;border-radius:4px;">
<h3 style="margin-top:0;color:#2e7d32;">Related Dog Care Guides</h3>
<ul style="margin-bottom:0;">{items}</ul>
</div>"""


def build_post_html(post):
    parts = []
    # Quick Answer
    parts.append(f"""
<div style="border-left:4px solid #2e7d32;background:#f1f8e9;padding:18px 22px;margin:0 0 28px 0;border-radius:4px;">
<strong style="color:#2e7d32;font-size:1.1em;">Quick Answer</strong><br>
<p style="margin:8px 0 0 0;">{post['quick_answer']}</p>
</div>""")

    # TOC
    toc = ""
    section_ids = []
    for i, (title, _) in enumerate(post["sections"]):
        sid = f"section-{i+1}"
        section_ids.append(sid)
        toc += f'<li><a href="#{sid}">{title}</a></li>\n'
    toc += '<li><a href="#recommended-products">Recommended Products</a></li>\n'
    toc += '<li><a href="#product-comparison">Product Comparison</a></li>\n'
    toc += '<li><a href="#glossary">Key Terms / Glossary</a></li>\n'
    toc += '<li><a href="#faq">Frequently Asked Questions</a></li>\n'
    toc += '<li><a href="#sources">Sources &amp; References</a></li>\n'
    parts.append(f"""
<div style="background:#f5f5f5;border:1px solid #e0e0e0;padding:18px 22px;margin:0 0 28px 0;border-radius:4px;">
<strong style="font-size:1.1em;">Table of Contents</strong>
<ol style="margin:10px 0 0 0;">{toc}</ol>
</div>""")

    # Sections
    for i, (title, content) in enumerate(post["sections"]):
        parts.append(f'<h2 id="{section_ids[i]}">{title}</h2>')
        parts.append(content)

    # Internal links
    links = get_internal_links(3)
    parts.append(build_internal_links_html(links))

    # Products
    parts.append('<h2 id="recommended-products">Recommended Products</h2>')
    parts.append('<p>These products may help with the topics covered in this guide. Links are affiliate links to Amazon UK — if you purchase through them, we may earn a small commission at no extra cost to you.</p>')
    for prod in post["products"]:
        link = f'https://www.amazon.co.uk/dp/{prod["asin"]}?tag={AMAZON_TAG}'
        parts.append(f"""
<div style="border:1px solid #e0e0e0;padding:15px 20px;margin:12px 0;border-radius:4px;background:#fafafa;">
<h3 style="margin-top:0;">{prod['name']}</h3>
<p>{prod['desc']}</p>
<p><a href="{link}" target="_blank" rel="nofollow noopener" style="background:#ff9900;color:#fff;padding:8px 18px;text-decoration:none;border-radius:4px;display:inline-block;">View on Amazon UK</a></p>
</div>""")

    # Comparison Table
    parts.append('<h2 id="product-comparison">Product Comparison</h2>')
    hdr = "".join(f'<th style="padding:10px 14px;text-align:left;background:#2e7d32;color:#fff;">{h}</th>' for h in post["comparison_headers"])
    rows = ""
    for row in post["comparison_rows"]:
        cells = "".join(f'<td style="padding:10px 14px;border-bottom:1px solid #e0e0e0;">{c}</td>' for c in row)
        rows += f"<tr>{cells}</tr>\n"
    parts.append(f"""
<div style="overflow-x:auto;">
<table style="width:100%;border-collapse:collapse;border:1px solid #e0e0e0;margin:15px 0;">
<thead><tr>{hdr}</tr></thead>
<tbody>{rows}</tbody>
</table>
</div>""")

    # Glossary
    parts.append('<h2 id="glossary">Key Terms / Glossary</h2>')
    parts.append('<dl style="margin:15px 0;">')
    for term, defn in post["glossary"]:
        parts.append(f'<dt style="font-weight:bold;margin-top:12px;">{term}</dt>')
        parts.append(f'<dd style="margin-left:20px;margin-bottom:8px;">{defn}</dd>')
    parts.append('</dl>')

    # FAQ
    parts.append('<h2 id="faq">Frequently Asked Questions</h2>')
    for faq in post["faqs"]:
        parts.append(f"""
<div style="border:1px solid #e0e0e0;padding:15px 20px;margin:10px 0;border-radius:4px;">
<h3 style="margin-top:0;color:#1a5276;">{faq['q']}</h3>
<p>{faq['a']}</p>
</div>""")
    parts.append(build_faq_schema(post["faqs"]))

    # Sources
    parts.append('<h2 id="sources">Sources &amp; References</h2><ul>')
    for name, url in post["sources"]:
        parts.append(f'<li><a href="{url}" target="_blank" rel="noopener">{name}</a></li>')
    parts.append('</ul>')

    # Author Box
    parts.append("""
<div style="background:#f5f5f5;border:1px solid #e0e0e0;padding:18px 22px;margin:25px 0;border-radius:4px;">
<strong>About the Author</strong><br>
<p style="margin:8px 0 0 0;">Written by the PetHub Online editorial team. Our writers research and compile information from leading UK animal welfare organisations including the PDSA, RSPCA, Blue Cross, BVA, and RCVS to provide accurate, helpful guides for dog owners.</p>
</div>""")

    # CTA
    parts.append("""
<div style="background:#e8f5e9;border:1px solid #a5d6a7;padding:18px 22px;margin:25px 0;border-radius:4px;text-align:center;">
<strong style="font-size:1.1em;color:#2e7d32;">Explore More Dog Care Guides</strong><br>
<p style="margin:8px 0 0 0;">Visit <a href="https://pethubonline.com/category/dogs/dog-care/">PetHub Online</a> for more expert dog care guides, product recommendations, and advice for UK dog owners.</p>
</div>""")

    # Affiliate Disclosure
    parts.append("""
<div style="background:#fff8e1;border:1px solid #ffe082;padding:14px 18px;margin:25px 0;border-radius:4px;font-size:0.9em;">
<strong>Affiliate Disclosure:</strong> PetHub Online is a participant in the Amazon Services LLC Associates Programme, an affiliate advertising programme designed to provide a means for sites to earn advertising fees by advertising and linking to Amazon.co.uk. When you purchase through links on this page, we may earn a small commission at no additional cost to you. We only recommend products we believe offer genuine value.
</div>""")

    return "\n".join(parts)


# ── The 5 Missing Posts ──────────────────────────────────────────────────────
MISSING_POSTS = [
    {
        "title": "Dog Paw Care: Protecting Paws in All Weather",
        "slug": "dog-paw-care-protecting-paws-all-weather",
        "pexels_query": "dog paw close up",
        "meta_description": "Complete guide to dog paw care in the UK. Learn how to protect your dog's paws from hot pavements, ice, salt, and thorns throughout every season.",
        "quick_answer": "Check your dog's paws daily for cuts, cracks, and foreign objects. Apply paw balm before walks in extreme weather. In summer, test pavement temperature with the back of your hand — if it is too hot for you, it is too hot for your dog. In winter, rinse paws after walks to remove road salt.",
        "sections": [
            ("Why Is Paw Care Important for Dogs?", "<p>A dog's paws are their primary point of contact with the world. They endure hot surfaces, cold ground, rough terrain, and chemical exposure daily. The <a href=\"https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs/walking-your-dog\" target=\"_blank\" rel=\"noopener\">PDSA</a> highlights that paw injuries are common but largely preventable with regular care.</p><p>Paw pads contain sweat glands (one of the few places dogs can sweat), provide cushioning, and offer traction. Damage to paw pads can cause significant pain and lameness.</p>"),
            ("How to Check Your Dog's Paws", "<p>Make paw checks a daily habit, especially after walks:</p><ul><li>Look between the toes for grass seeds, thorns, or small stones</li><li>Check paw pads for cuts, cracks, blisters, or swelling</li><li>Examine nails for damage, splitting, or excessive length</li><li>Feel for lumps, bumps, or areas of tenderness</li><li>Check for redness or signs of irritation between the toes</li></ul>"),
            ("Summer Paw Care: Hot Pavement Protection", "<p>Pavement can reach temperatures exceeding 50°C in direct summer sun — hot enough to cause burns within seconds.</p><ul><li><strong>The 7-second test:</strong> Place the back of your hand on the pavement. If you cannot hold it there for 7 seconds, it is too hot for your dog's paws.</li><li><strong>Walk during cooler hours:</strong> Early morning and late evening walks avoid the worst heat.</li><li><strong>Stick to grass and shade:</strong> Natural surfaces stay much cooler than tarmac or concrete.</li><li><strong>Paw balm:</strong> Apply a wax-based paw balm before walks to add a protective layer.</li></ul>"),
            ("Winter Paw Care: Cold, Ice, and Road Salt", "<p>Winter presents several hazards for dog paws:</p><ul><li><strong>Road salt:</strong> Sodium chloride irritates paw pads and is toxic if licked. Rinse paws after every walk on gritted surfaces.</li><li><strong>Ice and snow:</strong> Ice balls can form between toes, especially in long-haired breeds. Trim the fur between paw pads to prevent this.</li><li><strong>Cracking:</strong> Cold, dry air causes paw pads to crack. Regular application of paw balm keeps pads supple.</li><li><strong>Antifreeze:</strong> Ethylene glycol is extremely toxic and attractive to dogs. Avoid areas where puddles of antifreeze may be present.</li></ul><p>The <a href=\"https://www.rspca.org.uk/adviceandwelfare/pets/dogs/health\" target=\"_blank\" rel=\"noopener\">RSPCA</a> provides additional winter safety advice for dog owners.</p>"),
            ("First Aid for Paw Injuries", "<p>For minor paw injuries:</p><ol><li>Clean the wound gently with lukewarm water</li><li>Remove any visible debris with tweezers</li><li>Apply an antiseptic solution safe for dogs</li><li>Cover with a clean bandage if the wound is bleeding</li><li>Prevent licking with an Elizabethan collar if needed</li></ol><p>Seek veterinary attention for deep cuts, persistent bleeding, embedded objects, or if your dog is refusing to put weight on the paw.</p>"),
            ("Seasonal Paw Care Calendar", "<p><strong>Spring:</strong> Watch for grass seeds in meadows and parks. Check between toes after every walk. Allergens may cause itchy paws — contact your vet if your dog licks paws excessively.</p><p><strong>Summer:</strong> Hot pavement check before every walk. Paw balm application. Check for burns after walks.</p><p><strong>Autumn:</strong> Harvest mites can affect paws. Trim fur between pads as conditions get muddier. Watch for fallen conkers and acorns which are mildly toxic.</p><p><strong>Winter:</strong> Paw wax before walks. Rinse salt after walks. Check for cracking daily. Keep paw fur trimmed to prevent ice balls.</p>"),
        ],
        "products": [
            {"name": "Musher's Secret Paw Wax", "asin": "B0002IJQDC", "desc": "All-season paw protection wax. Forms breathable, semi-permeable barrier against heat, cold, and salt."},
            {"name": "Ruff Wear Grip Trex Dog Boots", "asin": "B07FK24Q2D", "desc": "Durable, weather-resistant dog boots with Vibram outsole for extreme conditions."},
            {"name": "Natural Dog Company PawTection Balm", "asin": "B01MTBBFAM", "desc": "Organic paw balm with SPF protection for summer heat and winter cold."},
            {"name": "PawZ Rubber Dog Boots", "asin": "B003E2XLQG", "desc": "Disposable, waterproof rubber boots for wet weather and post-surgery paw protection."},
        ],
        "comparison_headers": ["Product", "Type", "Best For", "Price Range"],
        "comparison_rows": [
            ["Musher's Secret", "Paw wax", "All-season protection", "£12–£18"],
            ["Ruff Wear Grip Trex", "Dog boots", "Extreme conditions", "£50–£70"],
            ["PawTection Balm", "Organic balm", "Daily maintenance", "£10–£16"],
            ["PawZ Rubber Boots", "Disposable boots", "Wet weather", "£10–£15"],
        ],
        "glossary": [
            ("Paw pad", "The tough, cushioned area on the underside of a dog's foot that provides shock absorption and traction."),
            ("Interdigital cyst", "A painful, fluid-filled swelling between a dog's toes, often caused by infection, foreign bodies, or allergies."),
            ("Hyperkeratosis", "Excessive growth of keratin on the paw pads, causing a rough, crusty appearance."),
            ("Grass seed", "The seed head of certain grasses that can pierce a dog's skin and migrate, causing infection. Most common in summer."),
            ("Dew claw", "An extra digit on the inner side of a dog's leg, located higher than the other toes."),
        ],
        "faqs": [
            {"q": "How do I know if pavement is too hot for my dog?", "a": "Use the 7-second rule: place the back of your hand flat on the pavement. If you cannot comfortably hold it there for 7 seconds, the surface is too hot for your dog's paws. Pavement can be 20–30°C hotter than the air temperature on sunny days."},
            {"q": "Should my dog wear boots?", "a": "Dog boots are not necessary for most dogs in normal conditions, but they can be helpful in extreme heat, deep snow, icy terrain, or after paw injuries. Some dogs need time to adjust to wearing them."},
            {"q": "How do I remove a grass seed from my dog's paw?", "a": "If the grass seed is visible, gently remove it with tweezers and clean the area. If the seed has burrowed into the skin, do not attempt to remove it yourself as this can push it deeper. Veterinary attention is needed as embedded grass seeds can migrate and cause serious infections."},
            {"q": "Why are my dog's paw pads cracked?", "a": "Cracked paw pads can result from walking on hot or rough surfaces, exposure to road salt, dry weather, allergies, or nutritional deficiencies. Regular application of paw balm helps prevent and heal cracks."},
            {"q": "Is road salt dangerous for dogs?", "a": "Yes. Road salt irritates paw pads and can be toxic if ingested in significant quantities through paw licking. Symptoms of salt ingestion include vomiting, diarrhoea, excessive thirst, and lethargy. Always rinse paws after walks on gritted roads."},
        ],
        "sources": [
            ("PDSA - Walking Your Dog", "https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs/walking-your-dog"),
            ("RSPCA - Dog Health", "https://www.rspca.org.uk/adviceandwelfare/pets/dogs/health"),
            ("Blue Cross - Dog Care", "https://www.bluecross.org.uk/advice/dog"),
            ("BVA - Animal Welfare", "https://www.bva.co.uk/"),
        ],
    },
    {
        "title": "How to Remove Ticks from Dogs Safely",
        "slug": "how-to-remove-ticks-from-dogs-safely",
        "pexels_query": "dog in tall grass field",
        "meta_description": "Learn how to safely remove ticks from your dog using a tick removal tool. UK guide covering tick-borne diseases, prevention, and when to see a vet.",
        "quick_answer": "Use a tick removal tool (twist-and-pull hook) to remove ticks from your dog. Slide the tool under the tick close to the skin, twist slowly 2-3 turns, and pull gently upward. Never squeeze, burn, or apply substances to an attached tick as this can cause the tick to regurgitate harmful bacteria into your dog.",
        "sections": [
            ("Why Are Ticks Dangerous for Dogs in the UK?", "<p>Ticks are blood-sucking parasites found throughout the UK, especially in areas with long grass, woodland, heathland, and deer populations. While the bite itself is usually painless, ticks can transmit serious diseases including Lyme disease (Borrelia burgdorferi), babesiosis, and ehrlichiosis.</p><p>The <a href=\"https://www.rspca.org.uk/adviceandwelfare/pets/dogs/health/ticks\" target=\"_blank\" rel=\"noopener\">RSPCA</a> reports that tick activity in the UK has increased in recent years, partly due to milder winters and expanding deer populations. Ticks are most active from March to October but can be found year-round in milder regions.</p>"),
            ("How to Find Ticks on Your Dog", "<p>Check your dog thoroughly after every walk, especially in tick-prone areas:</p><ul><li>Run your hands over your dog's entire body, feeling for small bumps</li><li>Pay special attention to the head, ears, neck, armpits, groin, and between toes</li><li>Use a fine-toothed comb on long-haired dogs</li><li>Check around the collar area</li><li>Look inside and behind the ears</li></ul><p>Ticks start very small (the size of a pinhead) and swell as they feed, eventually reaching the size of a small pea.</p>"),
            ("Step-by-Step Tick Removal", "<ol><li><strong>Use a tick removal tool:</strong> O'Tom Tick Twisters or similar hook-style tools are the safest option.</li><li><strong>Slide the tool under the tick:</strong> Position the prongs on either side of the tick, as close to your dog's skin as possible.</li><li><strong>Twist slowly:</strong> Rotate the tool 2–3 full turns in either direction. This detaches the tick's mouthparts from the skin.</li><li><strong>Pull gently upward:</strong> The tick should release cleanly. Do not yank.</li><li><strong>Check the tick:</strong> Ensure the head and mouthparts have been removed completely.</li><li><strong>Clean the area:</strong> Wipe the bite site with antiseptic.</li><li><strong>Dispose of the tick:</strong> Place it in a sealed container or tissue and dispose of it. Do not crush it with bare fingers.</li><li><strong>Monitor the site:</strong> Watch for redness, swelling, or signs of infection over the next few weeks.</li></ol>"),
            ("What NOT to Do When Removing Ticks", "<ul><li><strong>Do not squeeze the tick's body:</strong> This can force infected fluids back into your dog.</li><li><strong>Do not use petroleum jelly, nail polish, or alcohol on the tick:</strong> These old remedies can cause the tick to regurgitate bacteria.</li><li><strong>Do not burn the tick:</strong> This is dangerous and ineffective.</li><li><strong>Do not pull the tick straight out without twisting:</strong> The mouthparts may remain embedded in the skin.</li><li><strong>Do not use fingers alone:</strong> You risk squeezing the tick's body and incomplete removal.</li></ul>"),
            ("Tick Prevention for Dogs", "<p>Prevention is always better than removal:</p><ul><li><strong>Prescription treatments:</strong> Speak to your vet about tick prevention treatments (spot-on, tablets, or collars).</li><li><strong>Regular checks:</strong> Make post-walk tick checks a daily habit.</li><li><strong>Avoid high-risk areas:</strong> Be aware of tick hotspots in your local area, especially during spring and summer.</li><li><strong>Keep grass short:</strong> In your garden, regular mowing reduces tick habitat.</li></ul><p>The <a href=\"https://www.bva.co.uk/\" target=\"_blank\" rel=\"noopener\">BVA</a> recommends discussing tick prevention with your vet, as the appropriate product depends on your dog's lifestyle and your local tick risk.</p>"),
            ("Understanding Lyme Disease in Dogs", "<p>Lyme disease is the most significant tick-borne disease in the UK. It is caused by the bacterium Borrelia burgdorferi, carried by Ixodes ricinus (the sheep tick or deer tick).</p><p><strong>Symptoms in dogs</strong> may not appear for weeks or months after the bite:</p><ul><li>Fever and lethargy</li><li>Lameness that may shift between legs</li><li>Swollen joints</li><li>Loss of appetite</li><li>Swollen lymph nodes</li></ul><p>If you suspect Lyme disease, contact your veterinary practice immediately. Early treatment with antibiotics is usually effective. The <a href=\"https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs/ticks-on-dogs\" target=\"_blank\" rel=\"noopener\">PDSA</a> provides detailed information on tick-borne diseases in the UK.</p>"),
        ],
        "products": [
            {"name": "O'Tom Tick Twister Set", "asin": "B0171PAVQW", "desc": "Two-size set of tick removal hooks. Simple twist-and-pull action removes ticks cleanly."},
            {"name": "MHKBD Tick Remover Kit", "asin": "B0DKBK1L3T", "desc": "Three-size tick removal tool set with magnifying glass for spotting small ticks."},
            {"name": "Beaphar FIPROtec Spot-On for Dogs", "asin": "B07B6M5VRH", "desc": "Fipronil-based spot-on treatment that kills ticks for up to 4 weeks."},
            {"name": "Tick Identification Card", "asin": "B07G9R37Q6", "desc": "Credit card-sized tick removal tool. Keep in your wallet for walks."},
        ],
        "comparison_headers": ["Product", "Type", "Best For", "Price Range"],
        "comparison_rows": [
            ["O'Tom Tick Twister", "Removal tool", "Safe tick removal", "£3–£6"],
            ["MHKBD Tick Kit", "Removal kit", "Multiple tick sizes", "£5–£8"],
            ["Beaphar FIPROtec", "Spot-on treatment", "Prevention", "£8–£15"],
            ["Tick ID Card", "Portable tool", "On-the-go removal", "£3–£5"],
        ],
        "glossary": [
            ("Lyme disease", "A bacterial infection caused by Borrelia burgdorferi, transmitted by ticks. Symptoms in dogs include fever, lameness, and joint swelling."),
            ("Ixodes ricinus", "The sheep tick or deer tick, the most common tick species in the UK and the primary vector for Lyme disease."),
            ("Engorged tick", "A tick that has been feeding for several hours to days and is visibly swollen with blood."),
            ("Mouthparts", "The tick's feeding apparatus that embeds into the host's skin. If left behind during removal, they can cause infection."),
            ("Vector", "An organism that transmits a pathogen from one host to another, such as a tick transmitting Lyme disease bacteria."),
        ],
        "faqs": [
            {"q": "How quickly can a tick transmit disease?", "a": "Most tick-borne diseases require the tick to be attached for 24–48 hours before transmission occurs. This is why prompt removal is so important. Checking your dog after every walk and removing ticks quickly significantly reduces disease risk."},
            {"q": "Can I catch Lyme disease from my dog?", "a": "You cannot catch Lyme disease directly from your dog, but an infected tick that falls off your dog could attach to you. Dogs can bring ticks into the home on their coat, so checking your dog also protects your family."},
            {"q": "What are the signs of Lyme disease in dogs?", "a": "Signs include fever, lethargy, joint swelling and lameness, loss of appetite, and swollen lymph nodes. Symptoms may not appear for weeks or months after the tick bite. If you notice these signs, especially after removing a tick, consult your vet."},
            {"q": "The tick's head is stuck in my dog's skin. What should I do?", "a": "If a small piece of mouthpart remains after removal, the body will usually expel it naturally, similar to a splinter. Clean the area with antiseptic and monitor for signs of infection. If infection develops, see your vet."},
            {"q": "Can ticks be found year-round in the UK?", "a": "While tick activity peaks between March and October, ticks can be active year-round in milder areas of the UK, especially in the south and west. Any day above 3–4°C can see tick activity, so vigilance is important even in winter."},
        ],
        "sources": [
            ("RSPCA - Ticks on Dogs", "https://www.rspca.org.uk/adviceandwelfare/pets/dogs/health/ticks"),
            ("PDSA - Ticks on Dogs", "https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs/ticks-on-dogs"),
            ("Blue Cross - Ticks on Dogs", "https://www.bluecross.org.uk/advice/dog/ticks-on-dogs"),
            ("BVA - Parasite Prevention", "https://www.bva.co.uk/"),
        ],
    },
    {
        "title": "Dog Shedding Solutions: Managing Excessive Hair Loss",
        "slug": "dog-shedding-solutions-managing-hair-loss",
        "pexels_query": "fluffy dog golden retriever",
        "meta_description": "Manage your dog's shedding with proven UK solutions. Learn why dogs shed, when it is excessive, and the best tools and diet changes to reduce loose hair.",
        "quick_answer": "Shedding is normal for most dogs but can be managed with regular brushing (daily during heavy shedding seasons), a high-quality diet rich in omega-3 fatty acids, and proper bathing. Excessive shedding beyond normal seasonal patterns may indicate allergies, parasites, hormonal issues, or stress and should be discussed with a vet.",
        "sections": [
            ("Why Do Dogs Shed?", "<p>Shedding is a natural process by which dogs replace old or damaged hair. Most dogs shed year-round to some degree, with heavier periods in spring and autumn as they transition between seasonal coats.</p><p>The amount of shedding depends on breed, coat type, health, and environment. Dogs kept primarily indoors may shed more evenly throughout the year as they are less affected by seasonal daylight changes that trigger shedding cycles.</p><p>According to the <a href=\"https://www.rspca.org.uk/adviceandwelfare/pets/dogs/health/grooming\" target=\"_blank\" rel=\"noopener\">RSPCA</a>, regular grooming is essential for all dogs regardless of coat type.</p>"),
            ("Which Dog Breeds Shed the Most?", "<p><strong>Heavy shedders:</strong> Siberian Huskies, German Shepherds, Labrador Retrievers, Golden Retrievers, Alaskan Malamutes, Chow Chows, Border Collies, Akitas, Saint Bernards.</p><p><strong>Moderate shedders:</strong> Boxers, Dalmatians, Beagles, Pugs, Bulldogs, Corgis.</p><p><strong>Low shedders:</strong> Poodles, Bichon Frises, Yorkshire Terriers, Maltese, Portuguese Water Dogs, Shih Tzus.</p><p>No dog is truly 'hypoallergenic' — low-shedding breeds still produce dander, saliva, and urine proteins that can trigger allergies in sensitive individuals.</p>"),
            ("When Is Dog Shedding a Problem?", "<p>While shedding is normal, certain patterns may indicate an underlying health issue. The <a href=\"https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs/itchy-skin-in-dogs\" target=\"_blank\" rel=\"noopener\">PDSA</a> recommends consulting a vet if you notice:</p><ul><li>Bald patches or thinning areas</li><li>Shedding accompanied by excessive scratching</li><li>Dull, dry, or brittle coat</li><li>Skin redness, sores, or scabs</li><li>Sudden increase in shedding unrelated to season</li></ul><p>Possible medical causes include allergies (food or environmental), parasites (fleas, mites), fungal infections (ringworm), hormonal disorders (hypothyroidism, Cushing's disease), and stress.</p>"),
            ("How to Reduce Dog Shedding: Proven Methods", "<ul><li><strong>Brush regularly:</strong> Daily brushing during heavy shedding season and 2–3 times weekly otherwise removes loose hair before it falls.</li><li><strong>Use the right brush:</strong> Deshedding tools for double coats, slicker brushes for medium coats, bristle brushes for short coats.</li><li><strong>Bathe with deshedding shampoo:</strong> Specialised shampoos help release dead undercoat during baths.</li><li><strong>Feed a quality diet:</strong> Food rich in omega-3 and omega-6 fatty acids promotes a healthy coat and reduces excessive shedding.</li><li><strong>Ensure adequate hydration:</strong> Dehydrated skin leads to increased shedding.</li><li><strong>Manage stress:</strong> Stress-related shedding is common. Maintain routines and provide enrichment.</li><li><strong>Treat parasites promptly:</strong> Flea infestations cause excessive scratching and hair loss.</li></ul>"),
            ("Best Brushing Tools by Coat Type", "<p>Choosing the right tool makes shedding management much more effective:</p><ul><li><strong>Deshedding tools</strong> (FURminator): Stainless steel edge reaches through topcoat to remove loose undercoat. Best for double-coated breeds like Huskies, Labs, and Shepherds.</li><li><strong>Slicker brushes:</strong> Fine wire pins remove tangles and loose fur from medium and long coats. Ideal for Spaniels, Setters, and mixed breeds.</li><li><strong>Rubber curry brushes:</strong> Perfect for short-coated breeds like Boxers, Dalmatians, and Staffies. Massage the skin and attract loose hair through static.</li><li><strong>Undercoat rakes:</strong> Long teeth reach deep into thick double coats to remove matted undercoat. Essential during spring and autumn shedding seasons.</li><li><strong>Pin brushes:</strong> Gentle on sensitive skin. Good for silky-coated breeds like Yorkies and Maltese.</li></ul>"),
            ("Diet and Supplements for Coat Health", "<p>A dog's diet has a direct impact on coat condition and shedding levels:</p><ul><li><strong>Protein:</strong> Hair is primarily composed of protein (keratin). A diet with adequate high-quality protein supports healthy coat growth.</li><li><strong>Omega-3 fatty acids:</strong> Found in fish oil, these reduce inflammation and support the skin barrier. Fish-based foods or supplements are excellent sources.</li><li><strong>Omega-6 fatty acids:</strong> Found in chicken fat and vegetable oils, these help maintain coat sheen.</li><li><strong>Biotin:</strong> A B vitamin that supports healthy skin and coat.</li><li><strong>Zinc:</strong> Essential for skin repair and immune function.</li></ul><p>The <a href=\"https://www.bluecross.org.uk/advice/dog/grooming-your-dog\" target=\"_blank\" rel=\"noopener\">Blue Cross</a> emphasises that a balanced, complete diet is the foundation of coat health.</p>"),
        ],
        "products": [
            {"name": "FURminator Undercoat Deshedding Tool", "asin": "B0040QQ07C", "desc": "Stainless steel deshedding edge removes loose undercoat without damaging the topcoat."},
            {"name": "King Komb Deshedding Tool", "asin": "B072BY5J9K", "desc": "Retractable rubber bristle design. Captures loose hair during grooming."},
            {"name": "YuMOVE Skin & Coat Care", "asin": "B0932H3PT4", "desc": "Omega-3 and omega-6 fatty acid supplement supporting healthy skin and coat."},
            {"name": "Grizzly Salmon Oil for Dogs", "asin": "B0013LXGK4", "desc": "Wild Alaskan salmon oil pump. Rich in omega-3 for reducing shedding and improving coat shine."},
        ],
        "comparison_headers": ["Product", "Type", "Best For", "Price Range"],
        "comparison_rows": [
            ["FURminator Deshedding", "Deshedding tool", "Double-coated breeds", "£20–£30"],
            ["King Komb", "Deshedding tool", "Short to medium coats", "£15–£25"],
            ["YuMOVE Skin & Coat", "Supplement", "Coat health from inside", "£15–£20"],
            ["Grizzly Salmon Oil", "Oil supplement", "Omega-3 boost", "£12–£18"],
        ],
        "glossary": [
            ("Shedding cycle", "The natural process by which dogs lose old or damaged hair, typically increasing in spring and autumn."),
            ("Guard hairs", "The longer, coarser outer hairs of the topcoat that protect against the elements."),
            ("Undercoat", "The dense, soft inner layer of fur that provides insulation against heat and cold."),
            ("Alopecia", "Abnormal hair loss in dogs that may indicate an underlying medical condition requiring veterinary attention."),
            ("Omega fatty acids", "Essential fats (omega-3 and omega-6) that support skin barrier function and coat health. Cannot be produced by the body and must come from diet."),
        ],
        "faqs": [
            {"q": "Is it normal for my dog to shed a lot in spring?", "a": "Yes. Spring shedding is normal for most breeds, especially double-coated dogs. They are losing their thick winter undercoat to prepare for warmer weather. Daily brushing during this period helps manage the loose fur and keeps your home cleaner."},
            {"q": "Can diet affect how much my dog sheds?", "a": "Absolutely. A high-quality diet rich in omega-3 and omega-6 fatty acids, quality protein, and adequate vitamins supports healthy skin and coat, reducing excessive shedding. Fish oil supplements can also make a noticeable difference within 4–6 weeks."},
            {"q": "Does shaving a dog reduce shedding?", "a": "Shaving does not reduce shedding — the dog will still shed shorter hairs. For double-coated breeds, shaving can actually damage the coat permanently, disrupt its insulating properties, and may lead to irregular or patchy regrowth. Regular brushing is always preferable."},
            {"q": "My dog sheds year-round. Is that normal?", "a": "Dogs kept primarily indoors are less affected by seasonal daylight changes that trigger natural shedding cycles, so they tend to shed more evenly throughout the year. This is generally normal, but if shedding seems excessive or is accompanied by skin problems, consult your vet."},
            {"q": "Can stress cause a dog to shed more?", "a": "Yes. Stress-related shedding is well-documented in dogs. Anxiety, changes in routine, new environments, and visits to the vet can all trigger temporary increases in shedding. Addressing the source of stress and maintaining consistent routines can help reduce it."},
        ],
        "sources": [
            ("PDSA - Itchy Skin in Dogs", "https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs/itchy-skin-in-dogs"),
            ("RSPCA - Dog Grooming", "https://www.rspca.org.uk/adviceandwelfare/pets/dogs/health/grooming"),
            ("Blue Cross - Grooming Your Dog", "https://www.bluecross.org.uk/advice/dog/grooming-your-dog"),
            ("BVA - Pet Health", "https://www.bva.co.uk/"),
        ],
    },
    {
        "title": "How to Give Your Dog a Professional-Looking Groom at Home",
        "slug": "professional-dog-groom-at-home-guide",
        "pexels_query": "dog grooming scissors trimming",
        "meta_description": "Learn how to groom your dog at home like a professional. Complete UK guide with step-by-step instructions for bathing, brushing, trimming, and finishing.",
        "quick_answer": "For a professional-looking home groom, start with a thorough brush-out to remove tangles, then bathe with a quality dog shampoo. Towel-dry and blow-dry on low heat. Trim around the face, paws, and sanitary areas with rounded-tip scissors. Finish with ear cleaning, nail trimming, and a final brush to fluff the coat.",
        "sections": [
            ("Why Groom Your Dog at Home?", "<p>Professional grooming in the UK typically costs between £25 and £60 per session depending on breed and size. With the right tools and technique, you can achieve great results at home between professional appointments — or handle the entire grooming routine yourself.</p><p>Home grooming also strengthens your bond with your dog, allows you to spot health issues early, and reduces stress for dogs that find salon visits overwhelming. The <a href=\"https://www.bluecross.org.uk/advice/dog/grooming-your-dog\" target=\"_blank\" rel=\"noopener\">Blue Cross</a> encourages regular home grooming as part of good dog care.</p>"),
            ("Essential Grooming Tools for Home Use", "<ul><li><strong>Slicker brush:</strong> For detangling and removing loose fur</li><li><strong>Metal comb:</strong> For checking for remaining tangles after brushing</li><li><strong>Dog shampoo and conditioner:</strong> pH-balanced for dogs</li><li><strong>Rounded-tip scissors:</strong> For trimming around face, feet, and sensitive areas</li><li><strong>Thinning shears:</strong> For blending and reducing bulk without harsh lines</li><li><strong>Nail clippers or grinder:</strong> For nail maintenance</li><li><strong>Ear cleaner:</strong> Veterinary-approved solution</li><li><strong>Towels and dryer:</strong> Absorbent towels and a low-heat dryer</li><li><strong>Non-slip mat:</strong> For stability during bathing</li><li><strong>Treats:</strong> For positive reinforcement throughout the session</li></ul>"),
            ("Step-by-Step Home Grooming Routine", "<ol><li><strong>Pre-groom brush:</strong> Remove all tangles, mats, and loose fur before bathing. Wet mats tighten and become harder to remove.</li><li><strong>Bath time:</strong> Use lukewarm water. Wet thoroughly, apply shampoo from neck to tail, massage into the coat. Rinse completely — shampoo residue causes irritation.</li><li><strong>Condition (optional):</strong> Apply conditioner for long-coated breeds. Leave for 2–3 minutes, then rinse thoroughly.</li><li><strong>Towel dry:</strong> Press (do not rub) with an absorbent towel to remove excess water.</li><li><strong>Blow dry:</strong> Use a dryer on low heat, keeping it moving. Brush simultaneously for a fluffier finish.</li><li><strong>Trim carefully:</strong> Use rounded-tip scissors for face, paw, and sanitary areas. Work slowly and carefully.</li><li><strong>Clean ears:</strong> Apply ear cleaner, massage the base, let the dog shake, and wipe clean with cotton wool.</li><li><strong>Trim nails:</strong> Clip or grind to an appropriate length. Stop before the quick.</li><li><strong>Final brush:</strong> A finish brush distributes natural oils and adds shine.</li></ol>"),
            ("Trimming Tips for Different Areas", "<p><strong>Face:</strong> Use rounded-tip scissors. Trim carefully around eyes to maintain visibility. Cut in the direction of hair growth. For breeds with facial furnishings (Schnauzers, Westies), shape the beard and eyebrows according to breed standard.</p><p><strong>Paws:</strong> Trim fur between paw pads level with the pads using small, rounded scissors. Neaten the outline of the foot for a clean, rounded look.</p><p><strong>Ears:</strong> Trim long ear feathering to reduce matting. For breeds with hairy ear canals, discuss hair removal with your vet — some recent veterinary opinion suggests routine plucking may cause inflammation.</p><p><strong>Sanitary area:</strong> Keep the area around the rear end trimmed short for hygiene. Take extra care as this is a sensitive area. Small, rounded scissors are safest.</p><p><strong>Body:</strong> For breeds that need body trimming, use clippers with an appropriate guard length. Always clip in the direction of hair growth for a natural look.</p>"),
            ("Common Home Grooming Mistakes to Avoid", "<ul><li><strong>Bathing before brushing out mats:</strong> Mats tighten when wet, making them painful and nearly impossible to remove.</li><li><strong>Using dull scissors or clippers:</strong> Increases risk of injury and pulls hair rather than cutting cleanly.</li><li><strong>Cutting too close to the skin:</strong> Leaves no margin for error and can cause razor burns or nicks.</li><li><strong>Rushing the process:</strong> Accidents happen when you hurry. Take your time, especially around sensitive areas.</li><li><strong>Forgetting to reward your dog:</strong> Treats and praise throughout make future sessions easier.</li><li><strong>Using human products:</strong> Human shampoos, conditioners, and scissors are not designed for dog coats.</li><li><strong>Neglecting tool maintenance:</strong> Dull blades and dirty brushes are less effective and less hygienic.</li></ul>"),
            ("Grooming Schedules by Breed Type", "<p><strong>Short-coated breeds</strong> (Labradors, Beagles, Boxers): Bath every 6–8 weeks, brush weekly with rubber curry brush, regular nail trims.</p><p><strong>Medium-coated breeds</strong> (Border Collies, Spaniels): Bath every 4–6 weeks, brush 2–3 times weekly with slicker brush, trim feathering as needed.</p><p><strong>Long-coated breeds</strong> (Shih Tzus, Yorkshire Terriers): Bath every 3–4 weeks, brush daily with pin/slicker brush, professional-style trim every 6–8 weeks.</p><p><strong>Wire-coated breeds</strong> (Terriers, Schnauzers): Bath every 4–6 weeks, hand-stripping or clipping every 8–12 weeks, regular brushing with slicker brush.</p><p>The <a href=\"https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs/grooming-your-dog\" target=\"_blank\" rel=\"noopener\">PDSA</a> provides breed-specific grooming advice.</p>"),
        ],
        "products": [
            {"name": "Wahl Dog Grooming Clippers Kit", "asin": "B0B2DC3J9D", "desc": "Complete grooming kit with quiet-running clippers, 4 guide combs, scissors, and comb."},
            {"name": "Pettom Grooming Scissors Set", "asin": "B08RYSNFNV", "desc": "Stainless steel set including straight, curved, thinning shears and comb."},
            {"name": "Chris Christensen Big G Slicker Brush", "asin": "B0064ECGS6", "desc": "Professional-quality slicker brush with flexible pad and fine pins for thorough detangling."},
            {"name": "Andis Ultra Edge Detachable Blade Clipper", "asin": "B002DZOYFC", "desc": "Professional single-speed clipper. Quiet operation with detachable blades."},
        ],
        "comparison_headers": ["Product", "Type", "Best For", "Price Range"],
        "comparison_rows": [
            ["Wahl Grooming Kit", "Clipper kit", "Beginners", "£25–£40"],
            ["Pettom Scissors Set", "Scissors", "Detail work", "£10–£18"],
            ["Chris Christensen Brush", "Slicker brush", "All coat types", "£20–£30"],
            ["Andis Ultra Edge", "Professional clipper", "Regular grooming", "£70–£100"],
        ],
        "glossary": [
            ("Slicker brush", "A grooming brush with fine, short wire pins set on a flat or slightly curved pad, used for detangling and removing loose fur."),
            ("Thinning shears", "Scissors with one or two serrated blades that remove some hair while leaving the rest, creating a natural-looking finish."),
            ("Guard comb", "An attachment for electric clippers that determines the length of hair left after clipping."),
            ("Sanitary trim", "Trimming fur around a dog's rear end and genital area for hygiene purposes."),
            ("Hand stripping", "A grooming technique for wire-coated breeds where dead hair is plucked by hand rather than clipped, maintaining the coat's natural texture."),
        ],
        "faqs": [
            {"q": "How often should I groom my dog at home?", "a": "Brushing should be done 2–3 times per week for most breeds, daily for long-coated dogs. Full grooming sessions (bath, trim, nails, ears) every 4–8 weeks depending on breed and coat type."},
            {"q": "Can I use human clippers on my dog?", "a": "Human hair clippers are not recommended as they are designed for finer human hair, may overheat on thicker dog coats, and are often too loud. Purpose-built dog clippers have appropriate blade teeth spacing, are designed for thicker animal hair, and tend to run more quietly."},
            {"q": "How do I keep my dog calm during grooming?", "a": "Start grooming routines early in your dog's life. Use plenty of treats and positive reinforcement. Keep sessions short initially and gradually increase duration. A non-slip surface helps your dog feel secure. Taking breaks when your dog becomes restless is better than forcing the issue."},
            {"q": "What if I accidentally cut my dog while grooming?", "a": "Stay calm. For minor nicks, apply gentle pressure with a clean cloth and use styptic powder or cornflour to stop bleeding. Clean the wound with antiseptic. For deeper cuts or persistent bleeding, contact your veterinary practice."},
            {"q": "Should I groom my dog myself or use a professional?", "a": "Basic grooming (brushing, bathing, nail trimming, ear cleaning) can be done at home by most owners. Professional groomers are recommended for breed-specific cuts, heavily matted coats, anxious dogs that may bite, and owners uncomfortable with clippers near sensitive areas."},
        ],
        "sources": [
            ("Blue Cross - Grooming Your Dog", "https://www.bluecross.org.uk/advice/dog/grooming-your-dog"),
            ("PDSA - Grooming Your Dog", "https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs/grooming-your-dog"),
            ("RSPCA - Dog Grooming", "https://www.rspca.org.uk/adviceandwelfare/pets/dogs/health/grooming"),
            ("RCVS - Find a Vet", "https://www.rcvs.org.uk/find-a-vet/"),
        ],
    },
    {
        "title": "Dog Claw Care: When to Clip and When to See a Vet",
        "slug": "dog-claw-care-when-to-clip-see-vet",
        "pexels_query": "dog paws nails close",
        "meta_description": "Know when to clip your dog's claws at home and when to visit a vet. UK guide to recognising nail problems, proper trimming, and maintaining healthy claws.",
        "quick_answer": "Clip your dog's claws when they touch the ground while standing or you hear clicking on hard floors. Trim every 2–4 weeks using dog-specific clippers. See a vet if a nail is broken and bleeding heavily, growing into the paw pad, discoloured, swollen, or if your dog shows signs of pain when the paw is touched.",
        "sections": [
            ("How Do You Know When Your Dog's Claws Need Trimming?", "<p>The simplest test: when your dog stands on a flat, hard surface, their nails should not touch the ground. If you can hear a clicking sound when your dog walks on tiles or hard flooring, the nails are too long.</p><p>According to the <a href=\"https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs/grooming-your-dog\" target=\"_blank\" rel=\"noopener\">PDSA</a>, overgrown nails are one of the most overlooked aspects of dog care, yet they can cause significant discomfort and long-term joint problems if neglected.</p><p>The ideal nail length allows your dog to stand and walk comfortably, with the nails just clearing the ground when standing on a flat surface.</p>"),
            ("How to Clip Your Dog's Claws Safely at Home", "<ol><li>Choose sharp, dog-specific nail clippers (guillotine for small dogs, scissor-style for larger dogs)</li><li>Have styptic powder ready in case of accidental quick cuts</li><li>Work in good lighting — natural daylight is best</li><li>Choose a calm moment, ideally after exercise when your dog is relaxed</li><li>Hold the paw firmly but gently — do not squeeze</li><li>Identify the quick (pink area in light nails; trim small amounts on dark nails and watch for the chalky white ring)</li><li>Cut at a 45-degree angle, removing small amounts at a time</li><li>Smooth edges with a nail file or grinder</li><li>Do not forget dewclaws — they do not wear naturally</li><li>Reward with treats after each paw to build positive association</li></ol>"),
            ("When Should You See a Vet About Your Dog's Claws?", "<p>Seek veterinary attention for:</p><ul><li><strong>Broken nails with heavy bleeding:</strong> A nail torn at the base may need professional treatment, potentially under sedation. The exposed quick is painful and prone to infection.</li><li><strong>Ingrown nails:</strong> Nails growing into the paw pad cause pain and infection risk. This most commonly affects dewclaws that do not wear naturally.</li><li><strong>Discoloured nails:</strong> A single nail that changes colour may indicate a fungal infection, tumour, or immune-mediated disease. Changes in multiple nails warrant investigation.</li><li><strong>Swelling around the nail bed:</strong> This may indicate infection (paronychia) requiring antibiotics.</li><li><strong>Crumbling or brittle nails:</strong> Symmetric lupoid onychodystrophy and other conditions cause nail deterioration across multiple nails.</li><li><strong>Pain when touching the paw:</strong> Reluctance to have paws handled may indicate hidden injury or infection.</li><li><strong>Bleeding that won't stop:</strong> If styptic powder does not stop bleeding within 10 minutes, veterinary help is needed.</li></ul>"),
            ("Common Dog Nail Problems Explained", "<p><strong>Split nails:</strong> Can result from trauma, dry nails, or nutritional deficiencies. Minor splits can be filed smooth; deep splits that reach the quick need veterinary attention.</p><p><strong>Overgrown dewclaws:</strong> Because dewclaws do not contact the ground, they grow continuously and can curl in a full circle, piercing the paw pad if neglected. Check them every 2 weeks.</p><p><strong>Nail bed infections (paronychia):</strong> Red, swollen tissue around the nail base, often with discharge. Can be caused by trauma, allergies, or immune issues. Requires veterinary treatment with antibiotics.</p><p><strong>Symmetric lupoid onychodystrophy (SLO):</strong> An immune-mediated condition where multiple nails become brittle, split, and eventually fall off. Breeds like German Shepherds and Rottweilers may be predisposed. Requires long-term veterinary management with supplements and sometimes immunosuppressive medication.</p><p><strong>Nail tumours:</strong> Squamous cell carcinoma can affect the nail bed, causing swelling and nail loss in a single digit. Early veterinary assessment is important.</p>"),
            ("Tips for Maintaining Healthy Dog Claws", "<ul><li>Trim every 2–4 weeks to maintain appropriate length</li><li>Walk regularly on hard surfaces (pavement, concrete) to encourage natural nail wear</li><li>Keep the quick receded by trimming small amounts frequently — the quick retreats with regular maintenance trimming</li><li>If nails are very overgrown, trim small amounts every 5–7 days to gradually shorten them rather than cutting drastically in one session</li><li>Ensure a balanced diet with adequate biotin, zinc, and protein for nail strength</li><li>Inspect claws during regular grooming sessions for early detection of problems</li><li>Use a nail grinder between clips to smooth edges and maintain length</li></ul><p>The <a href=\"https://www.rspca.org.uk/adviceandwelfare/pets/dogs/health/grooming\" target=\"_blank\" rel=\"noopener\">RSPCA</a> recommends incorporating nail checks into your regular grooming routine.</p>"),
            ("Understanding the Quick and How to Avoid It", "<p>The quick is the blood vessel and nerve that runs through the centre of each nail. Cutting into it causes pain and bleeding.</p><p><strong>On light/clear nails:</strong> The quick is visible as a pink area inside the nail. Cut 2mm below where the pink ends.</p><p><strong>On dark/black nails:</strong> The quick is not visible from outside. Trim small amounts and examine the cut surface after each snip:</p><ul><li>White, dry, flaky — safe to continue trimming</li><li>Pale pink, slightly moist — the quick is very close, stop here</li><li>Dark dot in centre — this is the quick itself, stop immediately</li></ul><p>With regular trimming, the quick gradually recedes, allowing you to achieve a shorter nail length over time. If nails have been neglected, expect to need 4–6 weeks of weekly trimming to achieve the optimal length.</p><p>The <a href=\"https://www.bluecross.org.uk/advice/dog/grooming-your-dog\" target=\"_blank\" rel=\"noopener\">Blue Cross</a> recommends having styptic powder on hand for every trimming session, even for experienced owners.</p>"),
        ],
        "products": [
            {"name": "Thunderpaws Professional Nail Clippers", "asin": "B01COKOSX4", "desc": "Stainless steel scissor-style clippers with safety stop guard and ergonomic handles."},
            {"name": "Dremel PawControl Nail Grinder", "asin": "B09GFMLZ6P", "desc": "Quiet rotary grinder with LED light and 4 speed settings. Rechargeable."},
            {"name": "Mikki Nail Clipper for Dogs", "asin": "B000WFHRPQ", "desc": "Compact guillotine-style clipper ideal for small to medium breeds."},
            {"name": "Pogi's Styptic Powder", "asin": "B0C2C4FJNM", "desc": "Fast-acting powder to stop bleeding from accidental quick cuts. Benzocaine-free."},
        ],
        "comparison_headers": ["Product", "Type", "Best For", "Price Range"],
        "comparison_rows": [
            ["Thunderpaws Clippers", "Scissor clipper", "Medium to large dogs", "£8–£13"],
            ["Dremel PawControl", "Nail grinder", "Nervous dogs / precision", "£30–£40"],
            ["Mikki Nail Clipper", "Guillotine clipper", "Small to medium dogs", "£5–£9"],
            ["Pogi's Styptic Powder", "First aid", "Quick cut emergencies", "£5–£8"],
        ],
        "glossary": [
            ("Quick", "The blood vessel and nerve inside a dog's nail. Cutting into it causes pain and bleeding."),
            ("Dewclaw", "An extra digit located higher on the inner leg, not touching the ground. Present on front legs of most dogs; some breeds have rear dewclaws."),
            ("Paronychia", "Infection of the tissue surrounding the nail, causing swelling, redness, pain, and sometimes discharge."),
            ("Lupoid onychodystrophy", "An immune-mediated condition causing brittle, splitting, and shedding nails across multiple digits."),
            ("Guillotine clipper", "A nail trimming tool where the nail is inserted through a ring and cut by a single blade sliding across."),
        ],
        "faqs": [
            {"q": "How far back should I cut my dog's nails?", "a": "Cut to just before the quick. The nail should not touch the ground when your dog is standing. On dark nails, trim small amounts and stop when you see a chalky white or pale pink centre on the cut surface. A good rule is that you should be able to slide a piece of paper between the nail tip and the floor."},
            {"q": "My dog's nails are very long. Can I cut them short in one go?", "a": "No. If nails have been neglected, the quick will have grown longer too. Trim small amounts every 5–7 days to gradually encourage the quick to recede. Attempting to cut to the ideal length in one session risks cutting the quick and causing pain and bleeding. The process typically takes 4–6 weeks."},
            {"q": "How do I stop my dog's nail bleeding after cutting too short?", "a": "Apply styptic powder or cornflour directly to the nail tip with gentle pressure for 30–60 seconds. Keep your dog calm and off dirty surfaces for 15–20 minutes. If bleeding does not stop within 10 minutes, contact your vet."},
            {"q": "Can a broken nail heal on its own?", "a": "Minor cracks at the tip may smooth out with filing. However, a nail broken at or near the base often requires veterinary treatment including pain relief, possible removal of the damaged nail under sedation, and antibiotics to prevent or treat infection. The exposed quick is very painful."},
            {"q": "Do dogs need their dewclaws trimmed?", "a": "Yes. Dewclaws do not touch the ground and cannot wear down naturally through walking. They need regular trimming — typically every 2–3 weeks — to prevent them from curling and growing into the paw pad, which causes pain and infection."},
        ],
        "sources": [
            ("PDSA - Grooming Your Dog", "https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs/grooming-your-dog"),
            ("RSPCA - Dog Grooming", "https://www.rspca.org.uk/adviceandwelfare/pets/dogs/health/grooming"),
            ("Blue Cross - Dog Care", "https://www.bluecross.org.uk/advice/dog/grooming-your-dog"),
            ("BVA - Pet Health", "https://www.bva.co.uk/"),
        ],
    },
]


def main():
    print("=" * 60)
    print("PHASE 23 - Remaining 5 Dog Care Posts")
    print(f"Publishing posts 6-10 (Paw Care, Ticks, Shedding, Home Groom, Claw Care)")
    print("=" * 60)

    results = []
    success = 0

    for i, post in enumerate(MISSING_POSTS):
        print(f"\n{'='*60}")
        print(f"POST {i+1}/5: {post['title']}")
        print(f"{'='*60}")

        # Build HTML
        html = build_post_html(post)

        # Create post
        print(f"  Creating post...")
        resp = api_call(
            requests.post,
            f"{WP_URL}/posts",
            auth=WP_AUTH,
            headers=WP_HEADERS,
            json={
                "title": post["title"],
                "slug": post["slug"],
                "content": html,
                "status": "publish",
                "categories": [DOG_CARE_CAT],
                "meta": {"_yoast_wpseo_metadesc": post.get("meta_description", "")},
            }
        )

        if not resp or resp.status_code not in (200, 201):
            status = resp.status_code if resp else "none"
            print(f"  FAILED: {status}")
            results.append({"title": post["title"], "status": "FAILED", "error": str(status)})
            continue

        wp_post = resp.json()
        post_id = wp_post["id"]
        post_url = wp_post["link"]
        print(f"  Published: ID={post_id} | {post_url}")
        time.sleep(DELAY)

        # Fetch and upload image
        print(f"  Fetching image: '{post['pexels_query']}'")
        img_url, photographer, _ = fetch_pexels_image(post["pexels_query"])
        media_id = None

        if img_url:
            time.sleep(DELAY)
            filename = f"dog-care-{post['slug']}.jpg"
            print(f"  Uploading image...")
            media_id = upload_image_to_wp(img_url, filename, post["title"])

            if media_id:
                print(f"  Image uploaded: {media_id}")
                time.sleep(DELAY)
                feat_resp = api_call(
                    requests.post,
                    f"{WP_URL}/posts/{post_id}",
                    auth=WP_AUTH,
                    headers=WP_HEADERS,
                    json={"featured_media": media_id}
                )
                if feat_resp and feat_resp.status_code == 200:
                    print(f"  Featured image set")
            else:
                print(f"  Image upload failed")
        else:
            print(f"  No Pexels image found")

        time.sleep(DELAY)
        results.append({
            "title": post["title"],
            "post_id": post_id,
            "url": post_url,
            "slug": post["slug"],
            "media_id": media_id,
            "status": "PUBLISHED",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        success += 1

    # Merge with existing results
    try:
        with open(RESULTS_FILE, "r") as f:
            existing = json.load(f)
        existing["results"].extend(results)
        existing["published"] = existing.get("published", 0) + success
        existing["total_posts"] = existing.get("total_posts", 0) + len(MISSING_POSTS)
    except Exception:
        existing = {
            "phase": "23",
            "task": "Dog Care Educational Posts (remaining 5)",
            "total_posts": len(MISSING_POSTS),
            "published": success,
            "results": results,
        }

    with open(RESULTS_FILE, "w") as f:
        json.dump(existing, f, indent=2)

    print(f"\n{'='*60}")
    print(f"SUMMARY: {success}/5 published")
    print(f"Results merged into {RESULTS_FILE}")
    print(f"{'='*60}")

    for r in results:
        if r.get("status") == "PUBLISHED":
            print(f"  {r['url']}")

    return 0 if success == 5 else 1


if __name__ == "__main__":
    sys.exit(main())
