#!/usr/bin/env python3
"""
Phase 10AJ-G: HUB DOMINANCE ENGINE
Upgrades Dog Supplies (ID 3) and Cat Supplies (ID 696) hubs to authority destinations.
Adds: Cluster Overview, Quick Comparison Guide, FAQs, Editorial Note.
"""

import subprocess
import json
import tempfile
import csv
import re
import os

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
API = "https://pethubonline.com/wp-json/wp/v2/posts"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10aj_data"
LOG_FILE = os.path.join(DATA_DIR, "hub_dominance_log.csv")

# ─── NEW SECTIONS FOR DOG SUPPLIES HUB (ID 3) ───

DOG_NEW_SECTIONS = """
<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Understanding Dog Supplies: A Complete Overview</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Bringing a dog into your home is one of the most rewarding decisions you can make, but it also comes with a genuine responsibility to provide the right equipment, nutrition, and enrichment from day one. The UK dog supplies market has grown substantially in recent years, with the PDSA estimating that the average lifetime cost of owning a dog ranges from around seven thousand to thirty-three thousand pounds depending on breed and size. Understanding what your dog truly needs versus what is simply marketed well can save you both money and unnecessary clutter.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>For new owners, the essentials fall into clear categories: feeding equipment, sleeping arrangements, walking and training gear, grooming tools, and enrichment toys. The RSPCA recommends that owners focus first on safety and welfare basics before moving on to accessories. Seasonal considerations also matter significantly in the UK. Winter months require warmer bedding and possibly protective coats for short-haired breeds, while summer brings the need for cooling mats, increased water access, and awareness of hot pavement burns. Spring and autumn typically see increased parasite activity, making flea and tick prevention supplies essential.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Quality versus price is a persistent question for dog owners. In many cases, investing more upfront in durable, well-designed products such as orthopaedic beds, stainless steel bowls, and robust leads actually costs less over time than repeatedly replacing cheaper alternatives. However, this is not universal. Some budget-friendly options perform just as well as premium brands, particularly for items like basic grooming brushes and standard toys. The key is understanding which product categories genuinely benefit from higher spend and which do not. Our individual guides within this hub break down these trade-offs for each category.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>The British Veterinary Association (BVA) and PDSA both emphasise that the right supplies directly impact a dog's physical and mental wellbeing. Inadequate bedding contributes to joint problems, poor-quality food leads to digestive issues and coat deterioration, and a lack of enrichment toys can result in destructive behaviours born from boredom. This hub is designed to help you navigate every major product category with evidence-based guidance tailored to UK availability and standards.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Quick Comparison Guide</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The table below provides an at-a-glance summary of the major dog supply categories, helping you prioritise your purchases and understand what to look for in each area.</p>
<!-- /wp:paragraph -->

<!-- wp:table {"hasFixedLayout":true,"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Category</th><th>Best For</th><th>Key Consideration</th><th>Typical Price Range (UK)</th></tr></thead><tbody><tr><td>Dog Food</td><td>Daily nutrition and long-term health</td><td>Look for named meat sources and FEDIAF compliance</td><td>£30–£80/month</td></tr><tr><td>Dog Beds</td><td>Joint support and restful sleep</td><td>Size correctly; orthopaedic options for older or larger breeds</td><td>£25–£120</td></tr><tr><td>Leads and Harnesses</td><td>Safe walking and training</td><td>Harnesses reduce neck strain; avoid retractable leads near roads</td><td>£10–£45</td></tr><tr><td>Grooming Tools</td><td>Coat health and bonding</td><td>Match brush type to coat type; regular nail trimming is essential</td><td>£8–£35</td></tr><tr><td>Interactive Toys</td><td>Mental stimulation and boredom prevention</td><td>Rotate toys weekly; supervise with any new toy initially</td><td>£5–£25 each</td></tr><tr><td>Crates and Carriers</td><td>Travel safety and den training</td><td>Must be large enough for the dog to stand, turn, and lie down</td><td>£30–£90</td></tr><tr><td>Dental Care</td><td>Preventing periodontal disease</td><td>Daily brushing is the gold standard; dental chews supplement but do not replace</td><td>£5–£20/month</td></tr><tr><td>Seasonal Gear</td><td>Weather protection and comfort</td><td>Cooling mats in summer, insulated coats in winter for vulnerable breeds</td><td>£10–£40</td></tr></tbody></table></figure>
<!-- /wp:table -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Frequently Asked Questions</h3>
<!-- /wp:heading -->

<!-- wp:heading {"level":4} -->
<h4 class="wp-block-heading">How much should I budget for a new dog in the first year?</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The PDSA estimates first-year costs between one thousand and two thousand pounds for a medium-sized dog, covering vaccinations, neutering, microchipping, basic supplies, food, and insurance. This does not include the purchase or adoption fee. Setting aside a monthly amount of around one hundred to one hundred and fifty pounds covers ongoing food, insurance, and incidental supply replacements.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":4} -->
<h4 class="wp-block-heading">What are the essential supplies for a new puppy?</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>At minimum, a new puppy needs: appropriately sized food and water bowls, age-appropriate puppy food, a comfortable bed, a collar with ID tag (a legal requirement in the UK), a lead, puppy pads for house training, a crate or safe space, basic grooming tools, and a selection of safe chew toys. Our <a href="https://pethubonline.com/new-puppy-checklist-uk/">New Puppy Checklist</a> covers everything in detail.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":4} -->
<h4 class="wp-block-heading">Which dog food brands are most trusted by UK pet owners?</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Trust varies by what owners prioritise. Brands with strong veterinary backing include Royal Canin and Hills Science Plan. For owners seeking higher meat content, Forthglade, Lily's Kitchen, and Butternut Box are popular UK choices. The most important factor is not the brand name but whether the food meets FEDIAF nutritional guidelines and lists a named animal protein as its primary ingredient.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":4} -->
<h4 class="wp-block-heading">Are expensive dog beds worth the investment?</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>For puppies and young dogs that may chew their bedding, a mid-range bed is often more practical. However, for adult and senior dogs, particularly larger breeds prone to joint issues, investing in an orthopaedic bed with genuine memory foam or supportive filling is strongly recommended by veterinary professionals. A quality bed can last several years and contributes meaningfully to joint health and sleep quality.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":4} -->
<h4 class="wp-block-heading">How often should I replace my dog's toys?</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Inspect toys weekly for signs of damage such as loose squeakers, torn seams, or splintering. Replace immediately if any small parts could be swallowed. Soft toys typically last one to three months with regular use, while durable rubber toys can last a year or more. Rotating toys every week keeps them novel and engaging without constant replacement.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":4} -->
<h4 class="wp-block-heading">Do I need pet insurance, and does it count as a supply?</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>While not a physical supply, pet insurance is widely considered an essential part of responsible dog ownership in the UK. The BVA strongly recommends lifetime cover policies. Average premiums range from fifteen to fifty pounds per month depending on breed, age, and location. Without insurance, a single emergency vet visit can cost anywhere from five hundred to several thousand pounds.</p>
<!-- /wp:paragraph -->

<!-- wp:group {"style":{"color":{"background":"#f8fafb"},"border":{"radius":"8px","width":"1px","color":"#e2e8f0"},"spacing":{"padding":{"top":"16px","right":"20px","bottom":"16px","left":"20px"},"margin":{"top":"32px","bottom":"32px"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#e2e8f0;border-width:1px;border-radius:8px;background-color:#f8fafb;margin-top:32px;margin-bottom:32px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:paragraph {"style":{"typography":{"fontSize":"14px"}}} -->
<p style="font-size:14px"><strong>About this hub page:</strong> This page is regularly updated as we expand our guides. All recommendations are based on UK welfare standards and editorial research. We reference guidance from the RSPCA, PDSA, BVA, and The Kennel Club. Last reviewed: May 2026.</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->
"""

# ─── NEW SECTIONS FOR CAT SUPPLIES HUB (ID 696) ───

CAT_NEW_SECTIONS = """
<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator is-style-wide"/>
<!-- /wp:separator -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Understanding Cat Supplies: A Complete Overview</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Owning a cat in the UK has become increasingly popular, with an estimated eleven million cats living in British households according to the PDSA. Whether you are adopting your first kitten or welcoming a rescue cat, understanding the supplies landscape helps you make informed decisions rather than impulse purchases. The essentials have not changed dramatically over the years, but the quality, variety, and specialisation of products available to UK cat owners has grown enormously.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>At its core, cat ownership requires five non-negotiable supply categories: feeding equipment, a litter tray system, a scratching post, a secure carrier, and a comfortable sleeping area. Beyond these, enrichment items such as interactive toys, climbing structures, and puzzle feeders play a crucial role in preventing boredom-related behaviour, particularly for indoor cats. The RSPCA and Cats Protection both emphasise that mental stimulation is just as important as physical provisions for feline welfare.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Seasonal considerations affect cat owners differently than dog owners. Cats that go outdoors need reflective collars during darker months and increased parasite prevention in warmer seasons. Indoor cats benefit from seasonal enrichment changes such as window perches during summer and warmer bedding during winter. Since June 2024, microchipping has been compulsory for all cats in England, adding a one-off cost that owners must factor in.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>When it comes to quality versus price, cats can be particularly discerning. An expensive cat bed may go entirely unused if your cat prefers a cardboard box, while a cheap scratching post that topples over will be ignored in favour of your sofa. Understanding your individual cat's preferences before investing heavily is practical advice that the PDSA endorses. Our guides within this hub help you identify which product categories genuinely warrant higher spend and where budget options perform equally well.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Quick Comparison Guide</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Use this table to quickly understand the main cat supply categories, what each is best suited for, and what to consider before buying.</p>
<!-- /wp:paragraph -->

<!-- wp:table {"hasFixedLayout":true,"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Category</th><th>Best For</th><th>Key Consideration</th><th>Typical Price Range (UK)</th></tr></thead><tbody><tr><td>Cat Food</td><td>Daily nutrition and urinary health</td><td>Cats are obligate carnivores; high meat content is essential</td><td>£25–£60/month</td></tr><tr><td>Litter and Litter Trays</td><td>Hygiene and household odour control</td><td>One tray per cat plus one extra; clumping litter eases daily maintenance</td><td>£10–£30/month (litter), £8–£40 (tray)</td></tr><tr><td>Scratching Posts</td><td>Claw maintenance and territory marking</td><td>Must be tall enough for full stretch; stability is critical</td><td>£15–£80</td></tr><tr><td>Cat Beds</td><td>Security and warmth</td><td>Cats prefer enclosed or elevated options; washable covers are practical</td><td>£10–£50</td></tr><tr><td>Interactive Toys</td><td>Hunting instinct and mental stimulation</td><td>Wand toys for bonding; puzzle feeders for solo enrichment</td><td>£3–£20 each</td></tr><tr><td>Cat Carriers</td><td>Safe vet visits and travel</td><td>Top-opening carriers reduce stress; must meet airline size requirements if travelling</td><td>£15–£50</td></tr><tr><td>Grooming Tools</td><td>Coat health and hairball reduction</td><td>Long-haired breeds need daily brushing; short-haired cats benefit from weekly sessions</td><td>£5–£25</td></tr><tr><td>Cat Trees and Climbing Frames</td><td>Exercise, territory, and vertical space</td><td>Essential for indoor cats; must be stable and appropriately sized for the room</td><td>£30–£150</td></tr></tbody></table></figure>
<!-- /wp:table -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Frequently Asked Questions</h3>
<!-- /wp:heading -->

<!-- wp:heading {"level":4} -->
<h4 class="wp-block-heading">How much does it cost to own a cat per year in the UK?</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The PDSA estimates annual cat ownership costs between eight hundred and fifteen hundred pounds, covering food, litter, insurance, vaccinations, and flea and worming treatments. First-year costs are typically higher due to neutering, microchipping, and initial equipment purchases. Setting aside around seventy to one hundred and twenty pounds per month provides a reasonable ongoing budget.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":4} -->
<h4 class="wp-block-heading">What supplies do I need before bringing a cat home?</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>At minimum, you need: food and water bowls (ceramic or stainless steel preferred), age-appropriate cat food, a litter tray and litter, a scratching post, a secure carrier, a bed or blanket, and a collar with an ID tag. You should also have a safe room prepared where your new cat can acclimatise without being overwhelmed. Our cat supply guides cover each of these categories in detail.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":4} -->
<h4 class="wp-block-heading">Is wet or dry cat food better?</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Both have genuine advantages. Wet food provides additional hydration, which supports urinary tract health, a common concern in cats. Dry food helps with dental health through gentle abrasion and is more convenient for free-feeding. Many veterinary professionals, including those at International Cat Care, recommend a combination of both. The most important factor is that the food is nutritionally complete and lists a named animal protein as its primary ingredient.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":4} -->
<h4 class="wp-block-heading">Do indoor cats need different supplies than outdoor cats?</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Yes, indoor cats require more enrichment equipment to compensate for the lack of outdoor stimulation. Cat trees, climbing shelves, puzzle feeders, and a variety of interactive toys are considered essential rather than optional. Indoor cats also need more litter tray management attention since all waste is produced indoors. Our <a href="https://pethubonline.com/indoor-cat-care-guide/">Indoor Cat Care Guide</a> provides comprehensive advice.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":4} -->
<h4 class="wp-block-heading">Which cat litter type is best for odour control?</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Clumping clay litter and silica crystal litter generally offer the strongest odour control. However, many cats have preferences for texture and scent. Unscented clumping litter is the most widely accepted by cats and recommended by Cats Protection. Wood pellet litter is an eco-friendly alternative but requires more frequent full changes. The best approach is to trial a couple of types to see which your cat consistently uses without issue.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":4} -->
<h4 class="wp-block-heading">How many scratching posts does a cat need?</h4>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>At least one, but ideally two or more placed in different locations around the home. Cats scratch to mark territory, stretch muscles, and maintain claw health. Having both vertical and horizontal scratching surfaces increases the chance of your cat using them instead of furniture. In multi-cat households, provide at least one scratching option per cat.</p>
<!-- /wp:paragraph -->

<!-- wp:group {"style":{"color":{"background":"#f8fafb"},"border":{"radius":"8px","width":"1px","color":"#e2e8f0"},"spacing":{"padding":{"top":"16px","right":"20px","bottom":"16px","left":"20px"},"margin":{"top":"32px","bottom":"32px"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#e2e8f0;border-width:1px;border-radius:8px;background-color:#f8fafb;margin-top:32px;margin-bottom:32px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:paragraph {"style":{"typography":{"fontSize":"14px"}}} -->
<p style="font-size:14px"><strong>About this hub page:</strong> This page is regularly updated as we expand our guides. All recommendations are based on UK welfare standards and editorial research. We reference guidance from the RSPCA, PDSA, Cats Protection, and International Cat Care. Last reviewed: May 2026.</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->
"""


def fetch_content(post_id):
    """Fetch current post content."""
    url = f"{API}/{post_id}?context=edit"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    return data.get("content", {}).get("raw", "")


def update_content(post_id, new_content):
    """Update post content via WP REST API."""
    payload = {"content": new_content}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(payload, f)
        tmpfile = f.name

    url = f"{API}/{post_id}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH,
         "-d", f"@{tmpfile}",
         "-H", "Content-Type: application/json",
         "-X", "POST", url],
        capture_output=True, text=True
    )
    os.unlink(tmpfile)

    try:
        resp = json.loads(result.stdout)
        if "id" in resp:
            return True, resp["id"]
        else:
            return False, resp.get("message", "Unknown error")
    except json.JSONDecodeError:
        return False, result.stdout[:500]


def count_words(text):
    """Count words in HTML content (rough)."""
    clean = re.sub(r'<[^>]+>', '', text)
    clean = re.sub(r'<!--.*?-->', '', clean)
    return len(clean.split())


def process_hub(post_id, new_sections, label):
    """Fetch hub content, append new sections, update."""
    print(f"\n{'='*60}")
    print(f"Processing {label} Hub (ID {post_id})")
    print(f"{'='*60}")

    current = fetch_content(post_id)
    print(f"  Current content: {len(current)} chars, ~{count_words(current)} words")

    # Append new sections to the end
    updated = current.rstrip() + "\n" + new_sections.strip() + "\n"
    print(f"  Updated content: {len(updated)} chars, ~{count_words(updated)} words")

    new_words = count_words(new_sections)
    print(f"  New sections word count: ~{new_words}")

    success, info = update_content(post_id, updated)
    if success:
        print(f"  SUCCESS: Updated post {info}")
        return post_id, "cluster_overview,comparison_guide,faqs,editorial_note", new_words, "success"
    else:
        print(f"  FAILED: {info}")
        return post_id, "cluster_overview,comparison_guide,faqs,editorial_note", new_words, f"failed: {info}"


def main():
    results = []

    # Process Dog Supplies Hub
    r = process_hub(3, DOG_NEW_SECTIONS, "Dog Supplies")
    results.append(r)

    # Process Cat Supplies Hub
    r = process_hub(696, CAT_NEW_SECTIONS, "Cat Supplies")
    results.append(r)

    # Write log
    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["hub_id", "sections_added", "word_count_added", "status"])
        for row in results:
            writer.writerow(row)

    print(f"\nLog written to {LOG_FILE}")
    print("\n=== HUB DOMINANCE ENGINE COMPLETE ===")


if __name__ == "__main__":
    main()
