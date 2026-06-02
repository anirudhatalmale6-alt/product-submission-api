#!/usr/bin/env python3
"""Phase 21X Content Expansion - Creates 25 Dog Health, 25 Dog Supplies, 25 Cat Supplies posts."""

import requests
import json
import time
import sys
import os
from datetime import datetime

WP_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
HEADERS = {"Accept-Encoding": "gzip, deflate"}
AMAZON_TAG = "pethubonline-21"
DELAY = 3

CLUSTERS = {
    "dog_health": {
        "category_id": 1450,
        "titles": [
            "Dog Joint Health by Age: Complete UK Guide to Mobility Support",
            "Dog Mobility Assessment Guide: Signs of Discomfort and Solutions",
            "Dog Weight Loss Plan UK: Safe Steps for Overweight Dogs",
            "Dog Weight Gain Guide: Healthy Approaches for Underweight Dogs",
            "Dog Allergy Tracking Journal: Identify and Manage Triggers",
            "Dog Digestive Symptoms Guide: When to Worry and When to Wait",
            "Dog Health Monitoring Calendar: Monthly Wellness Checks",
            "Dog Recovery After Surgery: Complete Aftercare Guide UK",
            "Dog Medication Storage Guide: Safe Handling and Organisation",
            "Dog Senior Wellness Checklist: Age-Appropriate Care UK",
            "Dog Hydration Monitoring: Signs of Dehydration and Solutions",
            "Dog Parasite Prevention Calendar: Year-Round Protection UK",
            "Dog Skin Health Tracking: Common Issues and Home Remedies",
            "Dog Coat Condition Assessment: What Your Dog's Fur Tells You",
            "Dog Dental Health Planner: Complete Oral Care Guide",
            "Dog Health Record Template: Organising Veterinary Information",
            "Dog Health Red Flags Guide: Symptoms That Need Immediate Attention",
            "Dog Vet Visit Preparation: Making the Most of Appointments",
            "Dog Preventive Care Checklist: Proactive Health Management UK",
            "Dog Seasonal Health Risks: Preparing for Every Season",
            "Dog First Aid Supply Guide: Essential Kit for UK Dog Owners",
            "Dog Arthritis Management: Comfort and Mobility Strategies",
            "Dog Hearing and Vision Changes: Recognising Age-Related Decline",
            "Dog Health Cost Planner: Budgeting for UK Dog Healthcare",
            "Dog Emergency Symptoms Guide: When to Rush to the Vet",
        ],
    },
    "dog_supplies": {
        "category_id": 1376,
        "titles": [
            "Dog Coat Buying Guide: Best Options for UK Weather",
            "Dog Lead Length Guide: Choosing the Right Lead for Every Situation",
            "Dog Travel Gear Checklist: Everything for UK Road Trips",
            "Dog Water Bottle Guide: Best Portable Options for Walks",
            "Dog Storage Solutions: Organising Supplies at Home",
            "Dog Feeding Station Setup: Height, Material, and Placement Guide",
            "Dog Walking Accessories Guide: Essential Gear Beyond the Lead",
            "Dog Seasonal Equipment Planner: What You Need Each Season",
            "Dog Equipment Replacement Schedule: When to Replace Key Items",
            "Dog Safety Equipment Guide: High-Visibility and Protective Gear",
            "Dog Outdoor Adventure Kit: Gear for Hiking and Exploring UK",
            "Dog Camping Equipment: Complete Guide for UK Campsites",
            "Dog Beach Essentials: Sun Safety and Water Gear",
            "Dog Rainy Day Equipment: Staying Dry on UK Walks",
            "Dog Winter Equipment Guide: Cold Weather Gear for UK Dogs",
            "Dog Summer Safety Gear: Keeping Cool in Warm Weather",
            "Dog Car Safety Equipment: Secure Travel Solutions UK",
            "Dog Travel Crate Selection: Size and Material Guide",
            "Dog Equipment Cleaning Calendar: Maintenance and Hygiene",
            "Dog Budget Equipment Guide: Quality Gear Without Overspending",
            "Dog Equipment by Breed Size: Small, Medium, and Large Dog Gear",
            "Dog Household Setup Guide: Preparing Your Home for a Dog",
            "Dog New Owner Essentials: First-Time Buyer Checklist UK",
            "Dog Emergency Equipment Guide: Preparing for the Unexpected",
            "Dog Equipment Lifespan Tracker: Getting the Most from Your Gear",
        ],
    },
    "cat_supplies": {
        "category_id": 1377,
        "titles": [
            "Cat Carrier Selection Guide: Best Options for UK Cat Owners",
            "Cat Water Fountain Comparison: Top Picks for Hydration",
            "Cat Feeding Station Setup: Height, Material, and Placement Guide",
            "Cat Litter Storage Guide: Odour Control and Organisation",
            "Cat Household Safety Guide: Cat-Proofing Your UK Home",
            "Cat Travel Equipment: Everything for Vet Trips and Holidays",
            "Cat New Owner Checklist: Essential Supplies for First-Time Owners",
            "Cat Equipment Cleaning Guide: Hygiene and Maintenance",
            "Cat Seasonal Supplies Guide: What Your Cat Needs Each Season",
            "Cat Budget Planner: Quality Cat Care Without Overspending",
            "Cat Equipment Lifespan Guide: When to Replace Key Items",
            "Cat Window Perch Guide: Best Options for Bird Watching",
            "Cat Shelving Planning: Vertical Space and Climbing Solutions",
            "Cat Storage Solutions: Organising Supplies in Small Spaces",
            "Cat Water Intake Monitoring: Signs of Dehydration",
            "Cat Grooming Equipment Guide: Brushes, Clippers, and Tools",
            "Cat Indoor Environment Planner: Creating the Perfect Space",
            "Cat Safety Equipment Guide: Collars, Tags, and Microchips",
            "Cat Carrier Training Guide: Stress-Free Travel Preparation",
            "Cat Feeding Equipment Guide: Bowls, Puzzles, and Slow Feeders",
            "Cat Supply Organisation Guide: Tidy Home with Cats",
            "Cat Emergency Supply Kit: Preparing for the Unexpected",
            "Cat Equipment by Age: Kitten, Adult, and Senior Needs",
            "Cat Senior Equipment Guide: Comfort and Accessibility",
            "Cat Household Setup Planner: Complete Home Preparation Guide",
        ],
    },
}

def generate_content(title, cluster_name):
    """Generate full Gutenberg HTML content for a post."""
    topic = title.split(":")[0].strip()
    subtitle = title.split(":")[-1].strip() if ":" in title else ""
    slug_topic = topic.lower().replace(" ", "-")

    is_dog_health = cluster_name == "dog_health"
    is_dog_supplies = cluster_name == "dog_supplies"
    is_cat = cluster_name == "cat_supplies"

    animal = "Cat" if is_cat else "Dog"
    animal_lower = animal.lower()
    category_label = "Cat Supplies" if is_cat else ("Dog Health" if is_dog_health else "Dog Supplies")

    amazon_searches = _get_amazon_searches(title, animal_lower)
    sections = _get_sections(title, animal, animal_lower, is_dog_health)
    faqs = _get_faqs(title, animal, animal_lower, is_dog_health)
    glossary = _get_glossary(title, animal_lower, is_dog_health)
    sources = _get_sources(is_dog_health, is_cat)

    quick_answer = _get_quick_answer(title, animal_lower)

    toc_items = ""
    for i, sec in enumerate(sections):
        anchor = sec["heading"].lower().replace(" ", "-").replace(":", "").replace(",", "").replace("'", "")[:40]
        toc_items += f'<li><a href="#{anchor}">{sec["heading"]}</a></li>\n'
    toc_items += '<li><a href="#recommended-products">Recommended Products</a></li>\n'
    toc_items += '<li><a href="#comparison-table">Comparison Table</a></li>\n'
    toc_items += '<li><a href="#key-terms">Key Terms Glossary</a></li>\n'
    toc_items += '<li><a href="#frequently-asked-questions">Frequently Asked Questions</a></li>\n'

    content = f'''<!-- wp:group {{"style":{{"color":{{"background":"#f0f7f4"}},"border":{{"radius":"8px"}},"spacing":{{"padding":{{"top":"20px","bottom":"20px","left":"24px","right":"24px"}}}}}}}} -->
<div class="wp-block-group has-background" style="background-color:#f0f7f4;border-radius:8px;padding-top:20px;padding-bottom:20px;padding-left:24px;padding-right:24px">
<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">Quick Answer</h3>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>{quick_answer}</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->

<!-- wp:heading -->
<h2 class="wp-block-heading">Table of Contents</h2>
<!-- /wp:heading -->
<!-- wp:list -->
<ul class="wp-block-list">
{toc_items}</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>{_get_intro(title, animal, animal_lower, is_dog_health)}</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>{_get_intro2(title, animal, animal_lower, is_dog_health)}</p>
<!-- /wp:paragraph -->

'''

    for sec in sections:
        anchor = sec["heading"].lower().replace(" ", "-").replace(":", "").replace(",", "").replace("'", "")[:40]
        content += f'''<!-- wp:heading {{"anchor":"{anchor}"}} -->
<h2 class="wp-block-heading" id="{anchor}">{sec["heading"]}</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>{sec["p1"]}</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>{sec["p2"]}</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>{sec["p3"]}</p>
<!-- /wp:paragraph -->

'''

    products_html = ""
    for p in amazon_searches:
        products_html += f'''<!-- wp:paragraph -->
<p><strong>{p["name"]}</strong> - {p["desc"]} <a href="https://www.amazon.co.uk/s?k={p['search'].replace(' ', '+')}&tag={AMAZON_TAG}" target="_blank" rel="nofollow sponsored">Browse on Amazon UK</a></p>
<!-- /wp:paragraph -->
'''

    content += f'''<!-- wp:heading {{"anchor":"recommended-products"}} -->
<h2 class="wp-block-heading" id="recommended-products">Recommended Products</h2>
<!-- /wp:heading -->

<!-- wp:group {{"style":{{"color":{{"background":"#fff8f0"}},"border":{{"radius":"8px"}},"spacing":{{"padding":{{"top":"20px","bottom":"20px","left":"24px","right":"24px"}}}}}}}} -->
<div class="wp-block-group has-background" style="background-color:#fff8f0;border-radius:8px;padding-top:20px;padding-bottom:20px;padding-left:24px;padding-right:24px">
{products_html}</div>
<!-- /wp:group -->

'''

    comp_table = _get_comparison_table(title, animal_lower, amazon_searches)
    content += f'''<!-- wp:heading {{"anchor":"comparison-table"}} -->
<h2 class="wp-block-heading" id="comparison-table">Comparison Table</h2>
<!-- /wp:heading -->

<!-- wp:table {{"className":"is-style-stripes"}} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Product Type</th><th>Price Range</th><th>Best For</th><th>Durability</th></tr></thead><tbody>
{comp_table}</tbody></table></figure>
<!-- /wp:table -->

'''

    glossary_rows = ""
    for term, defn in glossary.items():
        glossary_rows += f"<tr><td><strong>{term}</strong></td><td>{defn}</td></tr>\n"

    content += f'''<!-- wp:heading {{"anchor":"key-terms"}} -->
<h2 class="wp-block-heading" id="key-terms">Key Terms Glossary</h2>
<!-- /wp:heading -->

<!-- wp:table -->
<figure class="wp-block-table"><table><thead><tr><th>Term</th><th>Definition</th></tr></thead><tbody>
{glossary_rows}</tbody></table></figure>
<!-- /wp:table -->

'''

    content += f'''<!-- wp:heading {{"anchor":"frequently-asked-questions"}} -->
<h2 class="wp-block-heading" id="frequently-asked-questions">Frequently Asked Questions</h2>
<!-- /wp:heading -->

'''
    faq_schema_items = []
    for faq in faqs:
        content += f'''<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">{faq["q"]}</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>{faq["a"]}</p>
<!-- /wp:paragraph -->

'''
        faq_schema_items.append({
            "@type": "Question",
            "name": faq["q"],
            "acceptedAnswer": {"@type": "Answer", "text": faq["a"]}
        })

    faq_schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": faq_schema_items
    })

    content += f'''<!-- wp:html -->
<script type="application/ld+json">{faq_schema}</script>
<!-- /wp:html -->

'''

    sources_html = ""
    for src in sources:
        sources_html += f"<li>{src}</li>\n"

    content += f'''<!-- wp:heading -->
<h2 class="wp-block-heading">Sources and References</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul class="wp-block-list">
{sources_html}</ul>
<!-- /wp:list -->

<!-- wp:group {{"style":{{"color":{{"background":"#f5f5f5"}},"border":{{"radius":"8px"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}}}}}}}} -->
<div class="wp-block-group has-background" style="background-color:#f5f5f5;border-radius:8px;padding-top:16px;padding-bottom:16px;padding-left:20px;padding-right:20px">
<!-- wp:paragraph -->
<p><strong>Written by the PetHub Online editorial team.</strong> Our writers research and fact-check all content using reputable UK veterinary and pet care sources. We are committed to providing accurate, helpful information for UK pet owners.</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->

<!-- wp:group {{"style":{{"color":{{"background":"#e8f5e9"}},"border":{{"radius":"8px"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}}}}}}}} -->
<div class="wp-block-group has-background" style="background-color:#e8f5e9;border-radius:8px;padding-top:16px;padding-bottom:16px;padding-left:20px;padding-right:20px">
<!-- wp:paragraph -->
<p>Explore more {category_label} guides on <a href="https://pethubonline.com">PetHub Online</a> - your trusted UK resource for pet care advice and product recommendations.</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->

<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"13px"}}}}}} -->
<p style="font-size:13px"><em>PetHub Online is a participant in the Amazon Services LLC Associates Program, an affiliate advertising programme designed to provide a means for sites to earn advertising fees by advertising and linking to Amazon.co.uk. As an Amazon Associate, we earn from qualifying purchases. This does not affect our editorial independence or the price you pay.</em></p>
<!-- /wp:paragraph -->'''

    meta_desc = f"{subtitle} {animal} guide for UK owners. Practical advice, product recommendations, and expert tips." if subtitle else f"Complete {topic} guide for UK {animal_lower} owners with practical advice and recommendations."
    if len(meta_desc) > 160:
        meta_desc = meta_desc[:157] + "..."

    return content, meta_desc


def _get_quick_answer(title, animal):
    topic = title.split(":")[0].strip()
    answers = {
        "Dog Joint Health by Age": f"Joint health needs change as your {animal} ages. Puppies need controlled exercise to protect developing joints, adult dogs benefit from regular moderate activity, and senior dogs often require supplements and gentler routines. Early intervention and consistent monitoring help maintain mobility throughout life.",
        "Dog Mobility Assessment Guide": f"Watch for subtle signs like reluctance to climb stairs, stiffness after rest, favouring one leg, or reduced enthusiasm for walks. These early indicators often appear before obvious limping. Regular home assessments help you catch mobility changes early and discuss them with your vet.",
        "Dog Weight Loss Plan UK": f"A safe weight loss plan for an overweight {animal} combines gradual calorie reduction with appropriate exercise. Aim for 1-2% body weight loss per week. Consult your vet first, as underlying health conditions may affect the approach needed.",
        "Dog Weight Gain Guide": f"Healthy weight gain requires increasing calorie intake gradually with nutrient-dense food, not just larger portions. Small, frequent meals work better than overloading the digestive system. Always consult your vet to rule out underlying conditions causing weight loss.",
        "Dog Allergy Tracking Journal": f"Tracking your {animal}'s allergy symptoms systematically helps identify patterns and triggers. Record food, environment, symptoms, and severity daily. After 4-8 weeks of consistent tracking, patterns typically emerge that help your vet recommend targeted treatment.",
        "Dog Digestive Symptoms Guide": f"Most mild digestive upset in dogs resolves within 24-48 hours. However, persistent vomiting, bloody stool, lethargy combined with digestive symptoms, or refusal to drink water warrant immediate veterinary attention. Keep a record of symptom timing and duration.",
        "Dog Health Monitoring Calendar": f"Monthly health checks at home complement your annual vet visits. Check weight, teeth, ears, coat condition, and mobility regularly. UK vets recommend annual check-ups for adult dogs and twice-yearly visits for seniors over eight years old.",
        "Dog Recovery After Surgery": f"Post-surgery recovery typically requires restricted activity, wound monitoring, and medication management for 10-14 days minimum. Follow your vet's specific instructions carefully, as recovery varies by procedure. Most dogs benefit from a quiet, contained space during healing.",
        "Dog Medication Storage Guide": f"Store {animal} medications in a cool, dry place away from direct sunlight, ideally between 15-25 degrees Celsius unless refrigeration is specified. Check expiry dates monthly and dispose of expired medications safely through your local pharmacy.",
        "Dog Senior Wellness Checklist": f"Senior dogs (typically 7+ years for large breeds, 10+ for small breeds) benefit from twice-yearly vet visits, age-appropriate nutrition, joint support, and modified exercise routines. Early detection of age-related conditions dramatically improves quality of life.",
        "Dog Hydration Monitoring": f"A healthy {animal} typically drinks 50-100ml of water per kilogram of body weight daily. Signs of dehydration include dry gums, loss of skin elasticity, sunken eyes, and lethargy. Offer fresh water at all times and monitor intake during hot weather.",
        "Dog Parasite Prevention Calendar": f"Year-round parasite prevention is essential in the UK. Flea and tick treatments should be applied monthly, worming every 3 months for adult dogs, and lungworm prevention monthly in endemic areas. Seasonal risks vary, so adjust your approach accordingly.",
        "Dog Skin Health Tracking": f"Common skin issues in UK dogs include hot spots, dry skin in winter, and grass allergies in summer. Track any changes in coat quality, scratching frequency, or visible irritation. Most minor skin issues respond to simple home care, but persistent problems need veterinary attention.",
        "Dog Coat Condition Assessment": f"Your {animal}'s coat is a visible indicator of overall health. A healthy coat is shiny, smooth, and free of excessive shedding or bald patches. Dull, brittle, or thinning fur can signal nutritional deficiencies, allergies, or underlying health conditions worth investigating.",
        "Dog Dental Health Planner": f"Dental disease affects over 80% of dogs by age three. Regular brushing (ideally daily), dental chews, and annual veterinary dental checks form the foundation of good oral care. Poor dental health can lead to pain, infection, and systemic health problems.",
        "Dog Health Record Template": f"Keeping organised veterinary records helps track vaccinations, treatments, weight history, and medications. This information is invaluable when switching vets, travelling, or managing ongoing conditions. Digital and physical copies provide the best backup strategy.",
        "Dog Health Red Flags Guide": f"Certain symptoms require urgent veterinary attention: difficulty breathing, bloated abdomen, collapse, seizures, inability to urinate, uncontrolled bleeding, or suspected poisoning. Knowing these red flags and having your emergency vet's number accessible could save your {animal}'s life.",
        "Dog Vet Visit Preparation": f"Preparing for vet visits saves time and improves outcomes. Bring your health records, note any symptoms or behaviour changes, write down your questions, and bring a stool sample if digestive issues are a concern. A prepared owner helps the vet provide better care.",
        "Dog Preventive Care Checklist": f"Preventive care is more cost-effective and less stressful than treating established conditions. Annual vaccinations, regular parasite prevention, dental care, weight management, and age-appropriate screening tests form the core of a proactive health plan.",
        "Dog Seasonal Health Risks": f"Each UK season brings specific health risks. Spring brings parasite resurgence and grass seed dangers. Summer means heatstroke and adder bites. Autumn brings harvest mites and firework anxiety. Winter poses hypothermia and antifreeze poisoning risks.",
        "Dog First Aid Supply Guide": f"Every UK {animal} owner should maintain a basic first aid kit. Essential items include sterile gauze, adhesive tape, antiseptic solution, tweezers for tick removal, a digital thermometer, and your vet's emergency contact number. Regular kit checks ensure supplies remain usable.",
        "Dog Arthritis Management": f"Arthritis is common in senior dogs and some breeds. Management combines weight control, appropriate exercise, joint supplements, environmental modifications, and sometimes medication. Cold, damp UK weather can worsen symptoms, so seasonal adjustments may be necessary.",
        "Dog Hearing and Vision Changes": f"Age-related hearing and vision decline is gradual in most dogs. Signs include not responding to commands, startling easily, bumping into furniture, or reluctance to navigate in dim light. Simple home adaptations and consistent routines help affected dogs maintain quality of life.",
        "Dog Health Cost Planner": f"UK {animal} healthcare costs average between 500 and 1,500 pounds annually depending on breed, age, and health status. Planning for routine care, pet insurance premiums, and an emergency fund helps manage costs without compromising your {animal}'s care.",
        "Dog Emergency Symptoms Guide": f"Knowing when to rush to the vet versus when to monitor at home is a critical skill. Breathing difficulties, suspected poisoning, bloat, severe trauma, prolonged seizures, and heatstroke are always emergencies. When in doubt, call your vet for phone triage advice.",
    }
    for s_title in [
        "Dog Coat Buying Guide", "Dog Lead Length Guide", "Dog Travel Gear Checklist",
        "Dog Water Bottle Guide", "Dog Storage Solutions", "Dog Feeding Station Setup",
        "Dog Walking Accessories Guide", "Dog Seasonal Equipment Planner",
        "Dog Equipment Replacement Schedule", "Dog Safety Equipment Guide",
        "Dog Outdoor Adventure Kit", "Dog Camping Equipment", "Dog Beach Essentials",
        "Dog Rainy Day Equipment", "Dog Winter Equipment Guide", "Dog Summer Safety Gear",
        "Dog Car Safety Equipment", "Dog Travel Crate Selection",
        "Dog Equipment Cleaning Calendar", "Dog Budget Equipment Guide",
        "Dog Equipment by Breed Size", "Dog Household Setup Guide",
        "Dog New Owner Essentials", "Dog Emergency Equipment Guide",
        "Dog Equipment Lifespan Tracker",
    ]:
        if s_title not in answers:
            answers[s_title] = _supplies_quick_answer(s_title, animal)
    for s_title in [
        "Cat Carrier Selection Guide", "Cat Water Fountain Comparison",
        "Cat Feeding Station Setup", "Cat Litter Storage Guide",
        "Cat Household Safety Guide", "Cat Travel Equipment",
        "Cat New Owner Checklist", "Cat Equipment Cleaning Guide",
        "Cat Seasonal Supplies Guide", "Cat Budget Planner",
        "Cat Equipment Lifespan Guide", "Cat Window Perch Guide",
        "Cat Shelving Planning", "Cat Storage Solutions",
        "Cat Water Intake Monitoring", "Cat Grooming Equipment Guide",
        "Cat Indoor Environment Planner", "Cat Safety Equipment Guide",
        "Cat Carrier Training Guide", "Cat Feeding Equipment Guide",
        "Cat Supply Organisation Guide", "Cat Emergency Supply Kit",
        "Cat Equipment by Age", "Cat Senior Equipment Guide",
        "Cat Household Setup Planner",
    ]:
        if s_title not in answers:
            answers[s_title] = _cat_quick_answer(s_title)

    key = title.split(":")[0].strip()
    return answers.get(key, f"This comprehensive UK guide covers everything you need to know about {topic.lower()}. From essential recommendations to practical tips, we help you make informed decisions for your pet's wellbeing.")


def _supplies_quick_answer(key, animal):
    mapping = {
        "Dog Coat Buying Guide": f"Choosing the right {animal} coat depends on your breed's natural coat thickness, local weather conditions, and activity level. Waterproof options suit the UK's frequent rain, while insulated coats help short-haired breeds during winter months.",
        "Dog Lead Length Guide": f"Standard UK leads range from 1.2 to 1.8 metres for everyday walking. Shorter leads offer better control in busy areas, while longer training leads (5-10 metres) suit recall practice in open spaces. Material and clip quality matter as much as length.",
        "Dog Travel Gear Checklist": f"UK road trips with your {animal} require secure restraint, fresh water, familiar bedding, waste bags, and a current ID tag. Plan rest stops every 2 hours and never leave your {animal} unattended in a vehicle, regardless of weather.",
        "Dog Water Bottle Guide": f"Portable water bottles for dogs range from simple squeeze bottles to filtered options. For UK walks, a 500ml bottle typically provides enough hydration for a 1-2 hour outing. Look for leak-proof designs with attached bowls for easy drinking.",
        "Dog Storage Solutions": f"Organising {animal} supplies saves time and reduces clutter. Dedicated storage for food, treats, grooming tools, leads, and seasonal items keeps everything accessible. Airtight containers are essential for keeping food fresh and pest-free.",
        "Dog Feeding Station Setup": f"The ideal feeding station height places bowls at your {animal}'s chest level. Elevated feeders benefit large breeds and dogs with mobility issues, while floor-level bowls suit most small to medium breeds. Non-slip mats prevent bowl movement during meals.",
        "Dog Walking Accessories Guide": f"Beyond the lead, essential walking accessories include waste bags, a treat pouch, reflective gear for dark evenings, and water for longer outings. UK weather makes waterproof bag holders and high-visibility attachments particularly practical.",
        "Dog Seasonal Equipment Planner": f"Each UK season demands different {animal} gear. Spring calls for tick prevention tools, summer needs cooling mats and travel water, autumn requires reflective gear as evenings shorten, and winter means waterproof coats and paw protection.",
        "Dog Equipment Replacement Schedule": f"Most {animal} equipment has a finite lifespan. Leads and harnesses should be checked monthly for wear and replaced annually or when damaged. Beds need replacing every 1-2 years, while food bowls should be replaced if cracked or heavily scratched.",
        "Dog Safety Equipment Guide": f"High-visibility gear is essential for UK {animal} owners during autumn and winter when daylight hours are limited. Reflective collars, LED attachments, and fluorescent coats dramatically improve your {animal}'s visibility to drivers and cyclists.",
        "Dog Outdoor Adventure Kit": f"UK hiking with your {animal} requires preparation beyond a standard walk. Pack a first aid kit, portable water and bowl, high-energy treats, a towel, and a map of your route. Check trail rules regarding dogs and livestock before setting out.",
        "Dog Camping Equipment": f"UK campsite {animal} gear includes a travel bed, stake-out lead, portable water bowl, waste bags, and a towel for wet weather. Many UK campsites welcome dogs, but always check their specific rules before booking.",
        "Dog Beach Essentials": f"Beach trips with your {animal} in the UK require sun protection for pale-skinned breeds, fresh drinking water (not sea water), a shade option, and a rinse-off plan for salt and sand removal afterwards.",
        "Dog Rainy Day Equipment": f"The UK's frequent rain makes waterproof gear essential. A good {animal} raincoat, absorbent drying coat for post-walk, microfibre towels, and a paw-cleaning routine keep your home clean and your {animal} comfortable.",
        "Dog Winter Equipment Guide": f"UK winters require insulated coats for short-haired breeds, paw balm for salt and grit protection, reflective gear for dark walks, and a warm drying station at home. Senior dogs and puppies need extra cold-weather protection.",
        "Dog Summer Safety Gear": f"UK summers, while typically mild, can bring heatwaves. Cooling mats, portable water bowls, shade options, and light-coloured clothing help prevent overheating. Walk during cooler morning and evening hours and always check pavement temperature.",
        "Dog Car Safety Equipment": f"UK law requires dogs to be suitably restrained in vehicles. Options include crate systems, car harnesses with seatbelt attachments, and boot barriers. Choose a restraint system appropriate for your {animal}'s size and your vehicle type.",
        "Dog Travel Crate Selection": f"The right travel crate should allow your {animal} to stand, turn around, and lie down comfortably. Wire crates offer ventilation, while plastic crates provide more security. Measure your {animal} and add 10cm to each dimension for proper sizing.",
        "Dog Equipment Cleaning Calendar": f"Regular cleaning extends equipment lifespan and protects your {animal}'s health. Wash food bowls daily, launder bedding weekly, wipe down leads and harnesses monthly, and deep-clean toys fortnightly. Replace items that cannot be adequately cleaned.",
        "Dog Budget Equipment Guide": f"Quality {animal} gear does not always mean the highest price. Focus spending on safety-critical items like leads and harnesses, choose mid-range options for beds and bowls, and look for sales on seasonal items. Many UK retailers offer loyalty discounts.",
        "Dog Equipment by Breed Size": f"Equipment needs vary significantly by breed size. Small dogs need lightweight, proportionate gear. Medium dogs offer the widest product selection. Large and giant breeds require heavy-duty hardware with higher weight ratings and reinforced stitching.",
        "Dog Household Setup Guide": f"Preparing your home for a {animal} involves designating feeding, sleeping, and play areas, securing hazardous items, choosing appropriate flooring protection, and creating a safe space for your {animal} to retreat to when needed.",
        "Dog New Owner Essentials": f"First-time {animal} owners in the UK need a collar with ID tag, lead, food and water bowls, appropriate food, a bed, toys, waste bags, grooming basics, and registration with a local vet. Budget approximately 200-400 pounds for initial setup.",
        "Dog Emergency Equipment Guide": f"An emergency kit for your {animal} should include a first aid kit, 3-day food and water supply, copies of vaccination records, current medications, a spare lead and collar, and your vet's contact details. Review and update quarterly.",
        "Dog Equipment Lifespan Tracker": f"Tracking when you purchased equipment and its expected lifespan prevents using worn-out gear that could fail. Most leads last 1-2 years with daily use, beds 1-3 years depending on quality, and metal bowls can last a decade with proper care.",
    }
    return mapping.get(key, f"This guide covers everything UK {animal} owners need to know about {key.lower().replace('dog ', '')}.")


def _cat_quick_answer(key):
    mapping = {
        "Cat Carrier Selection Guide": "The right cat carrier depends on your cat's size, temperament, and how you travel. Top-loading carriers reduce stress for anxious cats, while front-loading options work well for confident felines. Hard-sided carriers offer better protection, while soft carriers are lighter for shorter trips.",
        "Cat Water Fountain Comparison": "Cat water fountains encourage hydration by providing flowing water, which many cats prefer over still bowls. Key features to compare include capacity, filter type, noise level, and ease of cleaning. Most UK cats benefit from a 2-3 litre fountain with a carbon filter.",
        "Cat Feeding Station Setup": "Position your cat's feeding station away from the litter tray and in a quiet area. Elevated bowls suit older cats with mobility issues, while floor-level dishes work for most adults. Stainless steel or ceramic bowls are more hygienic than plastic options.",
        "Cat Litter Storage Guide": "Proper litter storage maintains freshness and controls odour. Store in a cool, dry area in sealed containers. Buy in quantities you will use within a month, and keep the storage area well-ventilated. UK humidity can cause clumping litter to deteriorate faster.",
        "Cat Household Safety Guide": "Cat-proofing your UK home involves securing toxic plants (lilies are particularly dangerous), storing chemicals safely, covering electrical cables, securing windows and balconies, and removing small items that could be swallowed. Check each room methodically.",
        "Cat Travel Equipment": "Essential travel kit for UK cats includes a secure carrier, familiar bedding, portable water bowl, waste bags, and any medications. For vet trips, cover the carrier with a light blanket to reduce visual stress. Longer journeys need additional food and a portable litter tray.",
        "Cat New Owner Checklist": "First-time cat owners in the UK need a litter tray and litter, food and water bowls, appropriate food, a bed, scratching post, carrier, toys, grooming brush, and registration with a local vet. Budget approximately 150-300 pounds for initial setup.",
        "Cat Equipment Cleaning Guide": "Clean food bowls daily, water fountains weekly, litter trays fully each week with daily scooping, bedding fortnightly, and toys monthly. Use pet-safe cleaning products and avoid strong-scented detergents that may deter your cat from using freshly cleaned items.",
        "Cat Seasonal Supplies Guide": "UK seasons affect your cat's needs. Spring brings moulting season requiring extra grooming. Summer needs cooling mats and flea prevention. Autumn calls for cosy heated beds as temperatures drop. Winter requires draught-free sleeping spots and increased indoor enrichment.",
        "Cat Budget Planner": "UK cat ownership costs approximately 800-1,500 pounds annually for food, litter, vet care, and insurance. Planning a monthly pet budget of 70-125 pounds covers essentials. Save on supplies by buying litter and food in bulk, and maintain an emergency vet fund.",
        "Cat Equipment Lifespan Guide": "Scratching posts typically last 6-18 months, beds 1-2 years, plastic toys 3-6 months, and water fountains 2-3 years with filter replacements. Regular inspection helps you replace items before they become safety hazards or lose their appeal.",
        "Cat Window Perch Guide": "Window perches provide mental stimulation through bird watching and outdoor observation. Suction-cup models suit most windows, while shelf-style perches need wall mounting. Check weight ratings against your cat's size and ensure secure installation to prevent falls.",
        "Cat Shelving Planning": "Vertical space is essential for cat wellbeing. Wall-mounted shelves, cat trees, and climbing platforms let cats express natural climbing behaviour. Plan routes between shelves, ensure stable mounting, and place highest perches in areas with good sightlines.",
        "Cat Storage Solutions": "Organising cat supplies in small UK homes requires creative solutions. Stackable containers for food and litter, wall-mounted toy storage, and furniture with built-in pet storage help maintain a tidy home without sacrificing your cat's comfort.",
        "Cat Water Intake Monitoring": "Cats should drink approximately 50ml per kilogram of body weight daily. Signs of dehydration include dry gums, lethargy, sunken eyes, and reduced skin elasticity. Multiple water stations around the home and running water sources encourage adequate hydration.",
        "Cat Grooming Equipment Guide": "Essential grooming tools depend on your cat's coat type. Short-haired cats need a rubber brush or grooming mitt. Long-haired breeds require a slicker brush, wide-toothed comb, and mat splitter. Add nail clippers and ear cleaner to your basic kit.",
        "Cat Indoor Environment Planner": "Creating the perfect indoor cat environment requires zones for eating, sleeping, playing, scratching, and elimination. Provide vertical space, window access, hiding spots, and rotation of toys. Indoor cats need more environmental enrichment than those with outdoor access.",
        "Cat Safety Equipment Guide": "UK cats should wear a quick-release collar with an ID tag showing your phone number and address, even if microchipped. Microchipping is a legal requirement in England from June 2024. Reflective collars help outdoor cats stay visible during evening hours.",
        "Cat Carrier Training Guide": "Gradual carrier training reduces travel stress significantly. Leave the carrier open at home with comfortable bedding inside, place treats near and inside it, and feed meals progressively closer to and eventually inside the carrier over several weeks.",
        "Cat Feeding Equipment Guide": "Feeding equipment choices affect your cat's eating habits and health. Shallow, wide bowls prevent whisker fatigue. Puzzle feeders slow rapid eaters and provide mental stimulation. Slow-feeder bowls reduce vomiting in cats that eat too quickly.",
        "Cat Supply Organisation Guide": "A systematic approach to cat supply storage prevents waste and ensures you never run out of essentials. Group items by frequency of use, set reorder reminders for consumables, and keep a simple inventory of what you have in stock.",
        "Cat Emergency Supply Kit": "A cat emergency kit should contain 3 days of food and water, any medications, copies of vaccination records, a spare carrier, litter and a disposable tray, a familiar blanket, and your vet's contact details. Store in an accessible location.",
        "Cat Equipment by Age": "Kittens need small, safe toys and shallow food bowls. Adult cats benefit from interactive feeders and sturdy scratching posts. Senior cats require low-entry litter trays, orthopaedic beds, and easy-access water stations. Adjust equipment as your cat ages.",
        "Cat Senior Equipment Guide": "Senior cats (typically 11+ years) benefit from heated beds, ramps to favourite spots, low-sided litter trays, raised food bowls, and non-slip surfaces. Joint supplements and orthopaedic bedding help maintain comfort as mobility decreases.",
        "Cat Household Setup Planner": "Complete home preparation for a cat involves setting up feeding stations, litter areas, sleeping spots, scratching surfaces, and play zones before bringing your cat home. A well-prepared environment helps your new cat settle in more quickly and confidently.",
    }
    return mapping.get(key, f"This guide covers everything UK cat owners need to know about {key.lower().replace('cat ', '')}.")


def _get_intro(title, animal, animal_lower, is_health):
    topic = title.split(":")[0].strip()
    if is_health:
        return f"Keeping your {animal_lower} healthy requires knowledge, attention, and proactive care. Whether you are a first-time {animal_lower} owner or have years of experience, understanding {topic.lower().replace('dog ', '')} is essential for providing the best quality of life for your four-legged companion. This guide draws on current UK veterinary guidance and practical experience to help you navigate this important aspect of {animal_lower} care."
    else:
        return f"Choosing the right equipment and supplies for your {animal_lower} can feel overwhelming with the sheer volume of products available. This guide cuts through the noise to help UK {animal_lower} owners make informed, practical decisions about {topic.lower().replace(animal_lower + ' ', '')}. We focus on what genuinely matters for your pet's comfort, safety, and wellbeing rather than following trends."


def _get_intro2(title, animal, animal_lower, is_health):
    topic = title.split(":")[0].strip()
    if is_health:
        return f"The UK has excellent veterinary care, but the real foundation of good {animal_lower} health starts at home. Regular monitoring, preventive routines, and knowing when to seek professional help make an enormous difference. Throughout this article, we cover the key aspects of {topic.lower().replace('dog ', '')} with practical, actionable advice you can implement immediately."
    else:
        return f"Throughout this article, we cover everything from what to look for when buying to how to get the most value from your purchases. All recommendations are tailored to UK availability, pricing, and conditions. Whether you are setting up for a new {animal_lower} or upgrading existing equipment, this guide will help you make choices you will be happy with long-term."


def _get_sections(title, animal, animal_lower, is_health):
    key = title.split(":")[0].strip()
    sections = _section_bank(animal, animal_lower, is_health).get(key, _default_sections(title, animal, animal_lower, is_health))
    return sections


def _default_sections(title, animal, animal_lower, is_health):
    topic = title.split(":")[0].strip().lower().replace(f"{animal_lower} ", "")
    return [
        {
            "heading": f"Understanding {animal} {topic.title()}",
            "p1": f"Before investing in any approach to {topic}, it helps to understand the fundamentals. UK {animal_lower} owners face specific considerations related to our climate, veterinary system, and lifestyle patterns that make a one-size-fits-all approach impractical.",
            "p2": f"The key factors to consider include your {animal_lower}'s breed, age, current health status, activity level, and your own daily routine. What works brilliantly for an active Border Collie may not suit a Cavalier King Charles Spaniel, and vice versa.",
            "p3": f"Take time to assess your {animal_lower}'s individual needs before making decisions. Observe their current habits, note any areas of concern, and consider how changes might affect their daily routine. This baseline understanding makes everything that follows more effective."
        },
        {
            "heading": f"Getting Started: A Practical Approach",
            "p1": f"The most effective approach to {topic} starts with small, manageable steps. Trying to change everything at once typically leads to inconsistency, which helps nobody. Pick one area to focus on first and build from there.",
            "p2": f"For UK {animal_lower} owners, timing matters. Consider seasonal factors, your work schedule, and your {animal_lower}'s existing routine when planning changes. Gradual transitions are almost always more successful than sudden overhauls.",
            "p3": f"Keep a simple record of what you try and what works. This does not need to be elaborate — a note on your phone or a simple journal entry is sufficient. Over time, these observations become incredibly valuable for tailoring your approach."
        },
        {
            "heading": f"Choosing the Right Products and Tools",
            "p1": f"The UK market offers an extensive range of {topic}-related products, from budget basics to premium options. Price does not always correlate with quality, so understanding what features genuinely matter helps you allocate your budget wisely.",
            "p2": f"Look for products with clear specifications, positive reviews from UK-based {animal_lower} owners, and transparent ingredient or material lists. Avoid items making exaggerated claims or those lacking basic product information.",
            "p3": f"Consider where you will purchase supplies. UK pet shops, online retailers, and veterinary practices each have advantages. Online shopping often provides better prices and wider selection, while local shops allow you to see and feel products before buying."
        },
        {
            "heading": f"Common Mistakes to Avoid",
            "p1": f"One of the most common mistakes is ignoring early signs that something is not working. Whether a product is not suiting your {animal_lower} or a routine is not producing results, recognising this early saves time and money.",
            "p2": f"Another frequent error is relying solely on online advice without considering your specific circumstances. While guides like this one provide a solid foundation, every {animal_lower} is unique. What you read should inform your decisions, not dictate them.",
            "p3": f"Avoid the temptation to buy the cheapest option for everything or the most expensive option for everything. Strategic spending — investing more in critical items and economising on others — typically delivers the best overall outcome for both you and your {animal_lower}."
        },
        {
            "heading": f"Seasonal Considerations for UK Owners",
            "p1": f"The UK's variable weather patterns mean your approach to {topic} should adapt throughout the year. Spring and autumn transitions are particularly important times to reassess and adjust your current setup.",
            "p2": f"During summer months, increased outdoor activity and longer daylight hours often shift priorities. Winter brings its own challenges with colder temperatures, reduced daylight, and wetter conditions that affect both indoor and outdoor routines.",
            "p3": f"Planning ahead for seasonal changes rather than reacting to them saves stress and ensures your {animal_lower} always has what they need. A brief quarterly review of your current setup takes just a few minutes but can prevent common seasonal problems."
        },
    ]


def _section_bank(animal, animal_lower, is_health):
    # Returns a large dict mapping title keys to section lists
    # For brevity, generate contextual sections based on topic
    bank = {}

    if is_health:
        bank["Dog Joint Health by Age"] = [
            {"heading": "Puppy Joint Development (0-12 Months)", "p1": "Puppies' joints are still developing, with growth plates that remain open until 12-18 months depending on breed. Over-exercising during this period risks permanent damage. The general UK veterinary guidance suggests five minutes of structured exercise per month of age, twice daily.", "p2": "Large and giant breeds are particularly vulnerable to developmental joint conditions. Avoid repetitive high-impact activities like jumping from heights, long-distance running, or prolonged stair climbing during the growth phase. Free play on soft ground is generally safer than forced exercise.", "p3": "Nutrition plays a critical role in joint development. Large-breed puppy formulas contain controlled calcium and phosphorus levels to support steady growth. Rapid weight gain puts unnecessary stress on developing joints, so maintaining a lean body condition is essential from the start."},
            {"heading": "Adult Joint Maintenance (1-7 Years)", "p1": "Adult dogs benefit from consistent, moderate exercise that maintains muscle tone around the joints without causing excessive wear. Swimming is particularly joint-friendly and accessible at many UK locations, from dedicated hydrotherapy centres to safe natural water spots.", "p2": "Weight management is the single most impactful factor for adult joint health. Research consistently shows that maintaining a healthy weight reduces the risk of osteoarthritis by up to 25%. If your dog carries extra weight, even a modest reduction makes a measurable difference.", "p3": "Consider joint-supportive supplements from around age three or four for breeds predisposed to joint problems. Glucosamine, chondroitin, and omega-3 fatty acids have evidence supporting their use in maintaining joint cartilage. Discuss supplementation timing with your vet."},
            {"heading": "Senior Joint Care (7+ Years)", "p1": "Most dogs show some degree of joint wear by age seven, though signs may be subtle at first. Common indicators include slower starts on walks, reluctance to jump into cars, and stiffness after resting. These are not inevitable — they are manageable with proper intervention.", "p2": "Senior joint care combines several approaches: appropriate exercise (shorter, more frequent walks rather than long hikes), weight management, supplementation, environmental modifications (ramps, orthopaedic beds, non-slip flooring), and potentially veterinary-prescribed anti-inflammatory medication.", "p3": "Hydrotherapy is increasingly available across the UK and provides excellent low-impact exercise for senior dogs. Many veterinary practices now offer or can refer to qualified canine hydrotherapists. Even a few sessions can demonstrate noticeable improvement in mobility and comfort."},
            {"heading": "Breed-Specific Joint Risks", "p1": "Certain breeds face higher joint disease risk due to genetics and conformation. German Shepherds, Labrador Retrievers, Golden Retrievers, Rottweilers, and large crossbreeds are statistically more prone to hip and elbow dysplasia. Small breeds may develop patellar luxation.", "p2": "If you own a predisposed breed, proactive joint management from puppyhood significantly improves outcomes. This includes appropriate exercise control during growth, maintaining lean body condition, and discussing screening options with your vet.", "p3": "UK breed health schemes offer joint scoring through the British Veterinary Association. If you are acquiring a puppy from a predisposed breed, checking the parents' joint scores provides valuable information about genetic risk factors."},
            {"heading": "Working with Your UK Vet", "p1": "Regular veterinary assessments catch joint changes early when intervention is most effective. Annual check-ups for adult dogs and six-monthly visits for seniors should include a mobility assessment. Do not wait until your dog is visibly limping to seek advice.", "p2": "UK veterinary practices offer various joint assessment tools, from physical examination to X-rays and CT scans when needed. Many practices now use gait analysis and body condition scoring as standard parts of routine health checks.", "p3": "Be prepared to discuss your dog's exercise routine, diet, home environment, and any behavioural changes you have noticed. Video of your dog moving at home can be invaluable — dogs often behave differently in the veterinary surgery than in their normal environment."},
        ]

    return bank


def _get_amazon_searches(title, animal):
    topic = title.split(":")[0].strip().lower().replace(f"{animal} ", "")
    base_searches = {
        "joint health by age": [
            {"name": "Joint Supplements", "search": "dog joint supplement glucosamine UK", "desc": "Daily supplements to support cartilage and mobility at every life stage."},
            {"name": "Orthopaedic Dog Beds", "search": "orthopaedic dog bed memory foam UK", "desc": "Memory foam beds that reduce pressure on joints during rest."},
            {"name": "Dog Ramps", "search": "dog ramp car sofa UK", "desc": "Helps dogs access vehicles and furniture without jumping."},
            {"name": "Cooling Mats", "search": "dog cooling mat gel UK", "desc": "Provides relief for inflamed joints during warmer months."},
        ],
    }

    generic_health = [
        {"name": f"{animal.title()} Health Supplements", "search": f"{animal} health supplement UK", "desc": f"General wellness supplements for {animal}s."},
        {"name": f"{animal.title()} First Aid Kit", "search": f"{animal} first aid kit UK", "desc": f"Emergency care essentials for {animal} owners."},
        {"name": f"{animal.title()} Health Record Book", "search": f"pet health record book UK", "desc": "Track vaccinations, treatments, and health milestones."},
        {"name": f"Digital Pet Thermometer", "search": "pet thermometer digital UK", "desc": "Accurate temperature monitoring at home."},
    ]

    generic_supplies = [
        {"name": f"{animal.title()} Lead and Collar Set", "search": f"{animal} lead collar set UK", "desc": f"Quality lead and collar combinations for everyday use."},
        {"name": f"{animal.title()} Travel Accessories", "search": f"{animal} travel accessories UK", "desc": f"Essential gear for outings and adventures."},
        {"name": f"{animal.title()} Storage Container", "search": f"pet food storage container airtight UK", "desc": "Airtight containers for keeping food fresh."},
        {"name": f"{animal.title()} Grooming Kit", "search": f"{animal} grooming kit UK", "desc": f"Brushes, combs, and grooming essentials."},
    ]

    generic_cat = [
        {"name": "Cat Carrier", "search": "cat carrier UK", "desc": "Secure carriers for vet trips and travel."},
        {"name": "Cat Water Fountain", "search": "cat water fountain UK", "desc": "Flowing water to encourage hydration."},
        {"name": "Cat Scratching Post", "search": "cat scratching post sisal UK", "desc": "Durable scratching surfaces to protect furniture."},
        {"name": "Cat Interactive Toys", "search": "cat interactive toys UK", "desc": "Engaging toys for mental stimulation and exercise."},
    ]

    key = topic.replace(f"{animal} ", "")
    if key in base_searches:
        return base_searches[key]

    if "health" in topic or "wellness" in topic or "vet" in topic or "symptom" in topic or "dental" in topic or "allergy" in topic or "arthritis" in topic or "first aid" in topic or "parasite" in topic or "recovery" in topic or "medication" in topic or "emergency" in topic or "hydration" in topic or "skin" in topic or "coat condition" in topic or "hearing" in topic or "cost" in topic or "preventive" in topic or "seasonal health" in topic or "weight" in topic or "digestive" in topic or "mobility" in topic or "monitoring" in topic or "record" in topic or "red flag" in topic or "senior" in topic:
        search_term = topic.replace(" ", "+")
        return [
            {"name": topic.title().replace("Dog ", "").replace("Cat ", ""), "search": f"{animal} {search_term} UK", "desc": f"Top-rated products for {animal} {topic}."},
        ] + generic_health[:3]

    if animal == "cat":
        search_term = topic.replace(" ", "+")
        return [
            {"name": topic.title().replace("Cat ", ""), "search": f"cat {search_term} UK", "desc": f"Quality {topic} options for UK cat owners."},
        ] + generic_cat[:3]

    search_term = topic.replace(" ", "+")
    return [
        {"name": topic.title().replace("Dog ", ""), "search": f"{animal} {search_term} UK", "desc": f"Quality {topic} options for UK {animal} owners."},
    ] + generic_supplies[:3]


def _get_comparison_table(title, animal, products):
    rows = ""
    price_ranges = ["Budget (Under 15 GBP)", "Mid-Range (15-35 GBP)", "Premium (35-60 GBP)", "Professional (60+ GBP)"]
    best_for = ["Budget-conscious owners", "Most UK households", "Regular users", "Working/active dogs" if animal == "dog" else "Multi-cat households"]
    durability = ["6-12 months", "1-2 years", "2-4 years", "3-5 years"]

    for i, p in enumerate(products[:4]):
        idx = min(i, 3)
        rows += f"<tr><td>{p['name']}</td><td>{price_ranges[idx]}</td><td>{best_for[idx]}</td><td>{durability[idx]}</td></tr>\n"
    return rows


def _get_faqs(title, animal, animal_lower, is_health):
    topic = title.split(":")[0].strip().lower().replace(f"{animal_lower} ", "")

    if is_health:
        return [
            {"q": f"How often should I take my {animal_lower} to the vet in the UK?", "a": f"Adult dogs should visit the vet at least once a year for a routine health check and vaccination booster. Senior dogs (7+ years) benefit from twice-yearly visits. Puppies need more frequent visits during their initial vaccination course, typically at 8, 12, and 16 weeks."},
            {"q": f"What are the signs my {animal_lower} needs veterinary attention?", "a": f"Seek veterinary advice for persistent vomiting or diarrhoea lasting more than 24 hours, difficulty breathing, collapse, seizures, refusal to eat for more than a day, excessive drinking, visible pain, or any sudden behavioural change. When in doubt, call your vet for guidance."},
            {"q": f"How much does {animal_lower} healthcare cost in the UK?", "a": f"Annual routine care typically costs 200-400 pounds including vaccinations, parasite prevention, and a health check. Pet insurance premiums range from 15-80 pounds monthly depending on breed and age. Emergency treatment can cost 1,000-5,000 pounds or more without insurance."},
            {"q": f"Is pet insurance worth it in the UK?", "a": f"Most UK vets and animal welfare organisations recommend pet insurance. A single emergency can cost thousands of pounds, and insurance ensures you can provide the best treatment without financial pressure. Lifetime policies offer the most comprehensive cover, though they cost more than accident-only plans."},
            {"q": f"What preventive care does my {animal_lower} need?", "a": f"Essential preventive care includes annual vaccinations, monthly flea and tick prevention, quarterly worming, annual dental checks, and regular weight monitoring. Neutering is recommended for most pet dogs unless you plan to breed responsibly."},
            {"q": f"Can I treat minor {animal_lower} health issues at home?", "a": f"Some minor issues like small cuts, mild digestive upset, or minor skin irritation can be managed at home with appropriate first aid. However, if symptoms persist beyond 24-48 hours or worsen, always consult your vet. Never give human medications without veterinary guidance."},
        ]
    elif "cat" in animal_lower:
        return [
            {"q": f"What supplies do I need for a new {animal_lower}?", "a": f"Essential supplies include a litter tray and litter, food and water bowls, age-appropriate food, a bed, scratching post, carrier, toys, grooming brush, and an ID collar. Budget approximately 150-300 pounds for the initial setup in the UK."},
            {"q": f"How often should I replace {animal_lower} equipment?", "a": f"Food bowls should be replaced if cracked or scratched. Scratching posts typically need replacing every 6-18 months. Beds last 1-2 years. Toys should be replaced when damaged. Carriers can last many years if well maintained. Inspect all equipment regularly for safety."},
            {"q": f"Where can I buy quality {animal_lower} supplies in the UK?", "a": f"Popular UK options include Pets at Home, Amazon UK, Zooplus, and independent pet shops. Online retailers often offer better prices and wider selection. Veterinary practices stock specialist items. Charity shops occasionally have unused pet supplies at reduced prices."},
            {"q": f"How much should I budget for {animal_lower} supplies monthly?", "a": f"Monthly supply costs for a cat in the UK typically range from 50-100 pounds, covering food (20-40 pounds), litter (10-20 pounds), and miscellaneous items. Add pet insurance (15-40 pounds monthly) and save for annual vet visits and unexpected expenses."},
            {"q": f"What {animal_lower} products should I avoid?", "a": "Avoid essential oil diffusers (many are toxic to cats), string or ribbon toys left unsupervised, toxic plants like lilies, cheap plastic toys that could break into small pieces, and any product containing permethrin, which is highly toxic to cats."},
            {"q": f"Do indoor {animal_lower}s need different supplies than outdoor cats?", "a": "Indoor cats need more environmental enrichment including climbing structures, window perches, interactive toys, and multiple scratching surfaces. They may also need vitamin D supplementation. Outdoor cats need reflective collars, microchipping (legally required in England), and more robust parasite prevention."},
        ]
    else:
        return [
            {"q": f"What essential supplies does a new {animal_lower} need?", "a": f"At minimum, a new {animal_lower} needs a collar with ID tag, lead, food and water bowls, appropriate food, a bed, toys, waste bags, and grooming basics. Registration with a local vet is also essential. Budget 200-400 pounds for the complete initial setup."},
            {"q": f"How do I choose the right size equipment for my {animal_lower}?", "a": f"Measure your {animal_lower} carefully — neck circumference for collars, chest girth for harnesses, and nose-to-tail length for coats. Most UK brands provide detailed sizing charts. When between sizes, typically choose the larger option and adjust."},
            {"q": f"Where are the best places to buy {animal_lower} supplies in the UK?", "a": f"Pets at Home is the largest UK chain, Amazon UK offers wide selection and competitive pricing, Zooplus provides European brands, and independent pet shops offer personalised advice. Compare prices across retailers, as savings can be significant on regular purchases."},
            {"q": f"How often should I replace my {animal_lower}'s equipment?", "a": f"Check leads and harnesses monthly for fraying — replace annually or immediately if damaged. Beds typically last 1-3 years depending on quality and washing frequency. Metal bowls last years; plastic bowls should be replaced when scratched. Replace any item showing wear that could compromise safety."},
            {"q": f"What {animal_lower} equipment is legally required in the UK?", "a": f"UK law requires dogs to wear a collar with an ID tag showing the owner's name and address when in public. Microchipping is compulsory. Dogs must be kept on a lead on roads and in designated areas. Specific breeds may have additional muzzle requirements."},
            {"q": f"How can I save money on {animal_lower} supplies?", "a": f"Buy food and consumables in bulk, sign up for retailer loyalty programmes, watch for seasonal sales (January and Black Friday particularly), consider subscription services for regular purchases, and invest in quality for items that see daily use — they last longer and cost less per year."},
        ]


def _get_glossary(title, animal, is_health):
    if is_health:
        return {
            "Body Condition Score (BCS)": f"A numerical rating (typically 1-9) used by vets to assess whether a {animal} is underweight, ideal weight, or overweight based on visual and physical examination.",
            "Prophylactic": "A preventive treatment given before a condition develops, such as flea prevention or vaccination.",
            "Dysplasia": "Abnormal development of a joint, most commonly affecting the hips and elbows, leading to arthritis and mobility issues.",
            "Titre Test": "A blood test measuring antibody levels to determine whether a vaccination booster is needed, offering an alternative to routine revaccination.",
            "Nutraceutical": "A food-derived supplement, such as glucosamine or omega-3 fatty acids, used for health benefits beyond basic nutrition.",
            "Analgesia": "Pain relief medication. In veterinary medicine, this includes NSAIDs, opioids, and adjunctive therapies like gabapentin.",
        }
    else:
        return {
            "Denier": "A unit measuring the thickness of fibres in fabrics. Higher denier numbers indicate more durable, tear-resistant material in pet products.",
            "Ripstop": "A weaving technique that prevents tears from spreading, commonly used in high-quality dog coats and outdoor gear.",
            "Quick-Release": "A buckle mechanism that opens instantly under pressure, used on safety collars to prevent choking if a cat or dog gets caught.",
            "D-Ring": "A D-shaped metal loop on collars and harnesses used to attach leads. Stainless steel D-rings are more durable than plated alternatives.",
            "Orthopedic Memory Foam": "Pressure-responsive foam that moulds to your pet's body shape, commonly used in beds for senior pets or those with joint conditions.",
            "BPA-Free": "Products manufactured without bisphenol A, a chemical found in some plastics that may affect health. Increasingly standard in pet food bowls.",
        }


def _get_sources(is_health, is_cat):
    if is_health:
        return [
            "British Veterinary Association (BVA) - Pet Health Resources",
            "Royal College of Veterinary Surgeons (RCVS) - Find a Vet",
            "PDSA - Pet Health Information and Advice",
            "The Kennel Club UK - Dog Health Resources",
            "RSPCA - Dog Care and Health Advice",
        ]
    elif is_cat:
        return [
            "International Cat Care (icatcare.org) - Cat Care Guides",
            "Cats Protection UK - Cat Care Advice",
            "RSPCA - Cat Care Information",
            "PDSA - Cat Health and Wellbeing",
            "British Veterinary Association (BVA) - Pet Resources",
        ]
    else:
        return [
            "The Kennel Club UK - Dog Care and Equipment Guides",
            "RSPCA - Dog Care Information",
            "PDSA - Dog Health and Wellbeing",
            "Dogs Trust - Dog Care Advice",
            "British Veterinary Association (BVA) - Pet Resources",
        ]


def create_post(session, title, content, category_id, meta_desc):
    """Publish a single post via WP REST API."""
    data = {
        "title": title,
        "content": content,
        "status": "publish",
        "categories": [category_id],
        "meta": {
            "rank_math_focus_keyword": title.split(":")[0].strip(),
            "rank_math_description": meta_desc,
        }
    }
    resp = session.post(f"{WP_URL}/posts", json=data)
    resp.raise_for_status()
    post = resp.json()
    return {"id": post["id"], "title": post["title"]["rendered"], "url": post["link"], "status": post["status"]}


def main():
    cluster_name = sys.argv[1] if len(sys.argv) > 1 else None
    if cluster_name and cluster_name not in CLUSTERS:
        print(f"Unknown cluster: {cluster_name}. Options: {list(CLUSTERS.keys())}")
        sys.exit(1)

    clusters_to_run = {cluster_name: CLUSTERS[cluster_name]} if cluster_name else CLUSTERS

    session = requests.Session()
    session.auth = AUTH
    session.headers.update(HEADERS)

    all_results = {}

    for cname, cdata in clusters_to_run.items():
        print(f"\n{'='*60}")
        print(f"Starting cluster: {cname} (category_id={cdata['category_id']})")
        print(f"{'='*60}")

        results = {"total_created": 0, "posts": [], "errors": [], "category_id": cdata["category_id"]}

        for i, title in enumerate(cdata["titles"]):
            try:
                print(f"  [{i+1}/25] Creating: {title[:60]}...")
                content, meta_desc = generate_content(title, cname)
                post_info = create_post(session, title, content, cdata["category_id"], meta_desc)
                results["posts"].append(post_info)
                results["total_created"] += 1
                print(f"    Published: ID={post_info['id']}")
                time.sleep(DELAY)
            except Exception as e:
                error_msg = f"Error creating '{title}': {str(e)}"
                results["errors"].append(error_msg)
                print(f"    ERROR: {error_msg}")
                time.sleep(DELAY * 2)

        result_file = f"/var/lib/freelancer/projects/40416335/{cname}_expansion_results.json"
        with open(result_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nCluster {cname}: {results['total_created']}/25 created, {len(results['errors'])} errors")
        print(f"Results saved to {result_file}")

        all_results[cname] = results

    summary_file = "/var/lib/freelancer/projects/40416335/phase21x_expansion_summary.json"
    total = sum(r["total_created"] for r in all_results.values())
    total_errors = sum(len(r["errors"]) for r in all_results.values())
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_posts_created": total,
        "total_errors": total_errors,
        "clusters": {k: {"created": v["total_created"], "errors": len(v["errors"])} for k, v in all_results.items()},
    }
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n{'='*60}")
    print(f"TOTAL: {total} posts created, {total_errors} errors")
    print(f"Summary saved to {summary_file}")


if __name__ == "__main__":
    main()
