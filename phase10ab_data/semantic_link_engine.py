#!/usr/bin/env python3
"""
10AB-E: Semantic Link Prioritization Engine
Adds semantic reinforcement links (glossary, FAQ, trust, educational)
to posts with lowest semantic link quality scores.
"""

import subprocess, json, time, csv, re

WP_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
TRUST_BLOCK_MARKER = '<!-- wp:separator {"className":"is-style-wide"} -->'

SEMANTIC_LINK_BLOCKS = {
    4407: {
        "title": "DIY Cat Toys",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Related Guides</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>For more on cat play and safety, explore these related guides:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><a href="https://pethubonline.com/cat-toy-safety-guide/">Cat Toy Safety Guide</a> — materials and hazards to watch for</li>
<li><a href="https://pethubonline.com/cat-toy-types-explained/">Cat Toy Types Explained</a> — understanding different toy categories</li>
<li><a href="https://pethubonline.com/cat-enrichment-beyond-toys/">Cat Enrichment Beyond Toys</a> — creating a stimulating home environment</li>
<li><a href="https://pethubonline.com/how-often-replace-cat-toys/">How Often to Replace Cat Toys</a> — knowing when to retire old toys</li>
<li><a href="https://pethubonline.com/our-methodology/">Our Research Methodology</a> — how we produce our guides</li>
</ul>
<!-- /wp:list -->"""
    },
    4406: {
        "title": "Best Interactive Cat Toys for Indoor Cats",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Related Reading</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><a href="https://pethubonline.com/indoor-cat-care-guide/">Indoor Cat Care Guide</a> — comprehensive guide to keeping house cats healthy</li>
<li><a href="https://pethubonline.com/cat-enrichment-beyond-toys/">Cat Enrichment Beyond Toys</a> — additional stimulation ideas</li>
<li><a href="https://pethubonline.com/cat-toy-rotation-guide/">Cat Toy Rotation Guide</a> — keeping toys fresh and engaging</li>
<li><a href="https://pethubonline.com/kitten-vs-adult-cat-toys/">Kitten vs Adult Cat Toys</a> — age-appropriate toy choices</li>
<li><a href="https://pethubonline.com/pet-toy-safety-guide/">Pet Toy Safety Guide</a> — understanding materials and hazards</li>
</ul>
<!-- /wp:list -->"""
    },
    4408: {
        "title": "How Often to Replace Cat Toys",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Related Reading</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><a href="https://pethubonline.com/cat-toy-safety-guide/">Cat Toy Safety Guide</a> — safety checks and hazard awareness</li>
<li><a href="https://pethubonline.com/cat-toy-rotation-guide/">Cat Toy Rotation Guide</a> — maintaining interest through rotation</li>
<li><a href="https://pethubonline.com/diy-cat-toys-homemade/">DIY Cat Toys</a> — budget-friendly replacement options</li>
<li><a href="https://pethubonline.com/cat-toy-types-explained/">Cat Toy Types Explained</a> — understanding different categories</li>
<li><a href="https://pethubonline.com/corrections-policy/">Our Corrections Policy</a> — how we keep our guides accurate</li>
</ul>
<!-- /wp:list -->"""
    },
    4787: {
        "title": "Dog Toy Safety",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Related Reading</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><a href="https://pethubonline.com/dog-toy-materials-compared/">Dog Toy Materials Compared</a> — rubber, rope, plush, and nylon breakdown</li>
<li><a href="https://pethubonline.com/aggressive-chewer-dog-toys/">Aggressive Chewer Guide</a> — safe toys for power chewers</li>
<li><a href="https://pethubonline.com/dog-toy-lifespan-replacement/">Dog Toy Lifespan Guide</a> — when to replace toys</li>
<li><a href="https://pethubonline.com/dog-toy-safety-breed-size/">Dog Toy Safety by Breed Size</a> — size-appropriate toy selection</li>
<li><a href="https://pethubonline.com/dog-toy-cleaning-guide/">Dog Toy Cleaning Guide</a> — keeping toys hygienic</li>
</ul>
<!-- /wp:list -->"""
    },
    4786: {
        "title": "Where to Place Your Dog's Bed",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Related Reading</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><a href="https://pethubonline.com/dog-bed-sizing-guide/">Dog Bed Sizing Guide</a> — measuring and choosing the right size</li>
<li><a href="https://pethubonline.com/dog-bed-materials-explained/">Dog Bed Materials Explained</a> — foam, memory foam, and more</li>
<li><a href="https://pethubonline.com/dog-bed-types-explained/">Dog Bed Types Explained</a> — complete glossary of bed styles</li>
<li><a href="https://pethubonline.com/how-to-wash-dog-bed/">How to Wash Your Dog's Bed</a> — maintenance and hygiene</li>
<li><a href="https://pethubonline.com/our-methodology/">Our Research Methodology</a> — how we produce our guides</li>
</ul>
<!-- /wp:list -->"""
    },
    4785: {
        "title": "How to Wash Dog Bed",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Related Reading</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><a href="https://pethubonline.com/dog-bed-materials-explained/">Dog Bed Materials Explained</a> — understanding which materials need which care</li>
<li><a href="https://pethubonline.com/dog-bed-sizing-guide/">Dog Bed Sizing Guide</a> — choosing the right bed from the start</li>
<li><a href="https://pethubonline.com/where-to-place-dogs-bed/">Where to Place Your Dog's Bed</a> — location and comfort tips</li>
<li><a href="https://pethubonline.com/dog-toy-cleaning-guide/">Dog Toy Cleaning Guide</a> — keeping all your dog's items hygienic</li>
<li><a href="https://pethubonline.com/corrections-policy/">Our Corrections Policy</a> — how we handle updates</li>
</ul>
<!-- /wp:list -->"""
    },
    4576: {
        "title": "Multi-Pet Household Tips",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Related Reading</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><a href="https://pethubonline.com/indoor-cat-care-guide/">Indoor Cat Care Guide</a> — keeping house cats happy and healthy</li>
<li><a href="https://pethubonline.com/first-time-dog-owner-essentials/">First-Time Dog Owner Essentials</a> — what you need to know</li>
<li><a href="https://pethubonline.com/pet-enrichment-explained/">Pet Enrichment Explained</a> — types, benefits, and practical ideas</li>
<li><a href="https://pethubonline.com/pet-toy-safety-guide/">Pet Toy Safety Guide</a> — materials and hazard awareness</li>
<li><a href="https://pethubonline.com/our-methodology/">Our Research Methodology</a> — how we produce our guides</li>
</ul>
<!-- /wp:list -->"""
    },
    4571: {
        "title": "Pet First Aid Basics",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Related Reading</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><a href="https://pethubonline.com/dog-health-basics/">Dog Health Basics</a> — common conditions and when to see a vet</li>
<li><a href="https://pethubonline.com/seasonal-dog-care/">Seasonal Dog Care</a> — keeping your dog safe year-round</li>
<li><a href="https://pethubonline.com/pet-health-terminology/">Pet Health Terminology</a> — understanding veterinary terms</li>
<li><a href="https://pethubonline.com/dog-dental-health-guide/">Dog Dental Health</a> — a practical care guide</li>
<li><a href="https://pethubonline.com/our-methodology/">Our Research Methodology</a> — how we produce our guides</li>
</ul>
<!-- /wp:list -->"""
    },
    4573: {
        "title": "Seasonal Pet Safety",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Related Reading</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><a href="https://pethubonline.com/seasonal-dog-care/">Seasonal Dog Care</a> — detailed guide for dogs through the year</li>
<li><a href="https://pethubonline.com/indoor-cat-care-guide/">Indoor Cat Care Guide</a> — keeping house cats safe indoors</li>
<li><a href="https://pethubonline.com/pet-hydration-guide/">Pet Hydration Guide</a> — how much water your pet needs</li>
<li><a href="https://pethubonline.com/pet-health-terminology/">Pet Health Terminology</a> — understanding common vet terms</li>
<li><a href="https://pethubonline.com/corrections-policy/">Our Corrections Policy</a> — how we keep guides current</li>
</ul>
<!-- /wp:list -->"""
    },
    4789: {
        "title": "Best Types of Dog Toys for Different Play Styles",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Related Reading</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><a href="https://pethubonline.com/dog-play-styles-explained/">Dog Play Styles Explained</a> — understanding how your dog plays</li>
<li><a href="https://pethubonline.com/mental-stimulation-toys-dogs/">Mental Stimulation Toys for Dogs</a> — puzzles, games, and brain work</li>
<li><a href="https://pethubonline.com/dog-toy-enrichment-beyond-fetch/">Dog Toy Enrichment Beyond Fetch</a> — expanding your play repertoire</li>
<li><a href="https://pethubonline.com/dog-toy-materials-compared/">Dog Toy Materials Compared</a> — understanding material properties</li>
<li><a href="https://pethubonline.com/dog-toy-rotation-guide/">Dog Toy Rotation Guide</a> — keeping toys interesting</li>
</ul>
<!-- /wp:list -->"""
    },
    4791: {
        "title": "How to Choose Dog Training Treats",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Related Reading</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><a href="https://pethubonline.com/dog-training-equipment-explained/">Dog Training Equipment Explained</a> — tools, uses, and what to avoid</li>
<li><a href="https://pethubonline.com/puppy-socialisation-timeline/">Puppy Socialisation Guide</a> — a complete timeline</li>
<li><a href="https://pethubonline.com/dog-training-terminology/">Dog Training Terminology</a> — key concepts for new owners</li>
<li><a href="https://pethubonline.com/pet-feeding-guide/">Pet Feeding Guide</a> — portions, schedules, and methods</li>
<li><a href="https://pethubonline.com/pet-nutrition-terminology/">Pet Nutrition Terminology</a> — understanding food labels</li>
</ul>
<!-- /wp:list -->"""
    },
    5415: {
        "title": "Dog Play Styles Explained",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Related Reading</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><a href="https://pethubonline.com/dog-toy-enrichment-beyond-fetch/">Dog Toy Enrichment Beyond Fetch</a> — expanding play beyond the basics</li>
<li><a href="https://pethubonline.com/mental-stimulation-toys-dogs/">Mental Stimulation Toys</a> — puzzles and brain work for dogs</li>
<li><a href="https://pethubonline.com/safe-tug-play-dogs/">Safe Tug Play</a> — rules for safe tug games</li>
<li><a href="https://pethubonline.com/dog-behaviour-explained/">Dog Behaviour Explained</a> — understanding body language and actions</li>
<li><a href="https://pethubonline.com/dog-toy-rotation-guide/">Dog Toy Rotation</a> — keeping your dog interested</li>
</ul>
<!-- /wp:list -->"""
    },
}

def fetch_post(post_id):
    cmd = ["curl", "-s", "--compressed", "-u", AUTH,
           f"{WP_URL}/posts/{post_id}?context=edit"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout)

def update_post(post_id, content):
    cmd = ["curl", "-s", "--compressed", "-u", AUTH,
           "-X", "POST", f"{WP_URL}/posts/{post_id}",
           "-H", "Content-Type: application/json",
           "-d", json.dumps({"content": content})]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout)

results = []
for post_id, data in SEMANTIC_LINK_BLOCKS.items():
    print(f"\n--- {post_id}: {data['title']} ---")
    try:
        post = fetch_post(post_id)
        if "id" not in post:
            print(f"  ERROR fetching")
            results.append({"post_id": post_id, "title": data["title"], "links_added": 0, "status": "fetch_error"})
            time.sleep(3)
            continue

        content = post["content"]["raw"]

        # Don't add if already has Related Reading / Related Guides
        if "Related Reading" in content or "Related Guides" in content:
            print(f"  SKIP: already has related links section")
            results.append({"post_id": post_id, "title": post["title"]["raw"], "links_added": 0, "status": "already_present"})
            time.sleep(1)
            continue

        if TRUST_BLOCK_MARKER in content:
            last_idx = content.rfind(TRUST_BLOCK_MARKER)
            new_content = content[:last_idx] + f"\n{data['block']}\n\n" + content[last_idx:]
        else:
            new_content = content + f"\n\n{data['block']}"

        link_count = data["block"].count('href="https://pethubonline.com/')

        updated = update_post(post_id, new_content)
        if "id" in updated:
            print(f"  SUCCESS: +{link_count} semantic links")
            results.append({"post_id": post_id, "title": post["title"]["raw"], "links_added": link_count, "status": "updated"})
        else:
            print(f"  ERROR: {str(updated)[:150]}")
            results.append({"post_id": post_id, "title": data["title"], "links_added": 0, "status": "update_error"})
        time.sleep(3)
    except Exception as e:
        print(f"  EXCEPTION: {e}")
        results.append({"post_id": post_id, "title": data["title"], "links_added": 0, "status": f"error: {e}"})
        time.sleep(3)

csv_path = "/var/lib/freelancer/projects/40416335/phase10ab_data/Semantic_Link_Expansion.csv"
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["post_id", "title", "links_added", "status"])
    w.writeheader()
    w.writerows(results)

success = sum(1 for r in results if r.get("status") == "updated")
total_links = sum(r.get("links_added", 0) for r in results)
print(f"\n=== COMPLETE: {success}/{len(results)} posts updated, {total_links} semantic links added ===")
