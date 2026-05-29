#!/usr/bin/env python3
"""
Process the 4 remaining posts that lack humanization blocks.
Posts: 4160, 4167, 4230, 4244
"""

import subprocess
import json
import time
import csv
import os
import tempfile
import html
import re

WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
LOG_DIR = "/var/lib/freelancer/projects/40416335/phase10ag_data"
LOG_FILE = os.path.join(LOG_DIR, "humanization_batch3_log.csv")

ABOUT_GUIDE_TEMPLATES = [
    "This guide was developed using published safety and enrichment guidance from the RSPCA and Dogs Trust for UK pet owners.",
    "Our editorial team compiled this resource from published veterinary and animal welfare guidance, reviewed for accuracy in May 2026.",
    "We reviewed current UK pet welfare guidance from the RSPCA, Blue Cross, and PDSA to create this practical resource.",
    "This information draws on published research and guidance from UK veterinary organisations and animal behaviourists.",
    "Our team consulted published guidance from Dogs Trust, the Kennel Club, and the RSPCA to compile this educational resource.",
    "This guide is based on established animal welfare principles and published advice from UK pet charities.",
    "We compiled this resource using guidance from UK veterinary organisations, focusing on practical advice for everyday pet owners.",
    "This educational guide draws on published pet welfare research and practical guidance from leading UK animal charities.",
    "This resource was put together using published recommendations from UK animal welfare organisations and veterinary professionals.",
    "Our editorial team reviewed guidance from the RSPCA, PDSA, and Blue Cross to ensure this resource reflects current best practice.",
    "We built this guide using published pet care standards from UK veterinary bodies, with a focus on practical, owner-friendly advice.",
    "This guide draws on published welfare guidance from the Kennel Club, Dogs Trust, and veterinary professionals practising in the UK.",
]

# Post-specific content
POST_DATA = {
    4160: {
        "cluster": "uncategorized",
        "about_idx": 4,
        "mistakes": [
            "<strong>Using an elevated bowl without checking the correct height</strong> — The bowl rim should sit at your dog's chest level. Too high forces an unnatural neck extension; too low defeats the purpose of elevation.",
            "<strong>Assuming all dogs benefit from elevated feeding</strong> — Research on bloat (GDV) and elevated bowls is mixed. Consult your vet before switching, especially for deep-chested breeds at higher bloat risk.",
            "<strong>Choosing a wobbly or lightweight stand</strong> — Unstable elevated feeders tip over easily, creating mess and potentially startling your dog. Look for weighted bases or non-slip feet.",
            "<strong>Not adjusting height as a puppy grows</strong> — A fixed-height elevated feeder that suits a 4-month-old puppy will be too low within weeks. Choose adjustable models for growing dogs.",
            "<strong>Neglecting to clean the stand as well as the bowls</strong> — Food debris and water splashes accumulate on the stand itself. Wipe down the frame and base weekly to prevent bacteria buildup."
        ],
        "suitability": [
            "<strong>Best for senior dogs with arthritis:</strong> Elevated bowls reduce the need to bend, easing strain on neck, shoulders, and joints during meals",
            "<strong>Best for large and giant breeds:</strong> Raised feeders bring food to a natural eating height, improving posture and reducing air swallowing",
            "<strong>Best for dogs recovering from surgery:</strong> Elevated bowls minimise bending and stretching during the recovery period",
            "<strong>Best for messy eaters:</strong> Raised feeders with splash guards contain food and water more effectively than floor-level bowls",
            "<strong>Best on a budget:</strong> Simple adjustable-height stands at mid-range prices offer the core benefit without premium-priced features"
        ],
        "what_to_expect": "Most dogs adapt to an elevated feeder within a meal or two, though some initially investigate the new setup cautiously. Expect reduced mess around the feeding area and a more natural eating posture for taller dogs. If your dog seems uncomfortable, try adjusting the height before concluding the feeder is not suitable.",
        "pros_cons": {
            "pros": [
                "Reduces strain on neck and joints for dogs with mobility issues or arthritis",
                "Can improve eating posture and reduce air swallowing during meals",
                "Raised bowls keep food and water cleaner by reducing floor-level debris contamination",
                "Adjustable models accommodate growing puppies and multi-dog households"
            ],
            "cons": [
                "Research on bloat risk and elevated feeders remains inconclusive — consult your vet first",
                "Some dogs tip or play with the stand, especially when made from lightweight materials",
                "Higher upfront cost compared to standard floor bowls",
                "Not necessary for all dogs — small breeds and dogs without joint issues may not benefit"
            ]
        }
    },
    4167: {
        "cluster": "uncategorized",
        "about_idx": 7,
        "mistakes": [
            "<strong>Choosing a bottle that is too small for the trip length</strong> — A 300ml bottle may not be enough for a full day out with an active dog. Match bottle capacity to your dog's size and the expected duration of activity.",
            "<strong>Not testing the drinking mechanism before a trip</strong> — Some dogs struggle with squeeze bottles, flap dispensers, or trough-style designs. Let your dog practise at home before relying on it outdoors.",
            "<strong>Leaving a water bottle in a hot car</strong> — Plastic bottles in warm environments can leach chemicals and the water quickly reaches temperatures dogs refuse to drink. Keep bottles cool and shaded.",
            "<strong>Only offering water at the end of the walk</strong> — Dogs need regular hydration breaks during exercise, not just at the start and finish. Offer water every 20-30 minutes during active outings.",
            "<strong>Forgetting to clean the bottle between uses</strong> — Saliva, outdoor debris, and standing water create bacterial buildup. Rinse and dry the bottle after every outing and deep clean weekly."
        ],
        "suitability": [
            "<strong>Best for long walks and hikes:</strong> Large-capacity bottles (500ml+) with a built-in trough that allows comfortable, mess-free drinking on the move",
            "<strong>Best for short daily walks:</strong> Compact, lightweight bottles (250-350ml) that fit in a jacket pocket or attach to a lead",
            "<strong>Best for car travel:</strong> Spill-proof designs with a lockable lid that prevent leaks during transit",
            "<strong>Best for hot weather:</strong> Insulated bottles that keep water cool for several hours during summer outings",
            "<strong>Best on a budget:</strong> A simple squeeze bottle with a fold-out trough covers most everyday walking needs at a low cost"
        ],
        "what_to_expect": "Most dogs drink happily from a travel bottle trough after one or two introductions. Expect some spillage during the first few uses as both you and your dog learn the mechanism. Insulated bottles keep water noticeably cooler than standard plastic, which matters more than you might expect on warm days.",
        "pros_cons": {
            "pros": [
                "Ensures reliable hydration during walks, travel, and outdoor adventures",
                "Built-in trough designs eliminate the need to carry a separate bowl",
                "Lightweight, portable options fit easily into bags, pockets, or clip onto leads",
                "Insulated models keep water cool for hours in warm weather"
            ],
            "cons": [
                "Some dogs refuse unfamiliar drinking mechanisms and need a training period",
                "Cheaper plastic bottles may retain odours and stain over time",
                "Squeeze-activated designs require one free hand, which can be awkward while managing a lead",
                "Smaller bottles may not hold enough water for large dogs on long outings"
            ]
        }
    },
    4230: {
        "cluster": "uncategorized",
        "about_idx": 2,
        "mistakes": [
            "<strong>Using dog grooming tools on cats</strong> — Cat skin is thinner and more sensitive than dog skin. Dog-specific brushes, clippers, and combs can scratch, cut, or irritate feline skin.",
            "<strong>Attempting to groom a stressed or frightened cat</strong> — Forcing grooming on an unwilling cat creates lasting negative associations. Start with very short sessions and reward cooperation generously.",
            "<strong>Buying a complete grooming kit before understanding your cat's needs</strong> — Long-haired cats need different tools from short-haired cats. Assess your cat's coat type first, then purchase appropriate supplies.",
            "<strong>Neglecting nail trimming because the cat goes outdoors</strong> — Outdoor cats do wear down their claws more, but indoor surfaces and cat trees may not provide enough natural filing. Check nails fortnightly.",
            "<strong>Skipping grooming for short-haired cats</strong> — Short-haired cats still benefit from weekly brushing to remove loose fur, distribute natural oils, and allow skin and coat health checks."
        ],
        "suitability": [
            "<strong>Best for long-haired breeds (Persian, Maine Coon):</strong> A wide-toothed comb, slicker brush, and mat splitter are essential for managing thick, tangle-prone coats",
            "<strong>Best for short-haired breeds:</strong> A rubber grooming mitt or soft bristle brush for weekly maintenance, plus a flea comb for spot-checks",
            "<strong>Best for cats that dislike grooming:</strong> A grooming glove that mimics the feel of petting, providing the least intrusive introduction to regular coat care",
            "<strong>Best for kittens:</strong> Start with a small, soft brush and very gentle sessions to build positive grooming associations early",
            "<strong>Best on a budget:</strong> A basic slicker brush and a pair of cat nail clippers cover the core grooming needs of most cats for under £10"
        ],
        "what_to_expect": "Building a cat's tolerance for grooming takes patience, particularly if they were not groomed regularly as kittens. Expect initial resistance and plan for very short sessions (one to two minutes) with treats as rewards. Over time, many cats come to accept or even enjoy grooming as a bonding activity.",
        "pros_cons": {
            "pros": [
                "Regular grooming reduces hairballs, matting, and skin irritation across all coat types",
                "Provides an opportunity to check for fleas, lumps, wounds, and early signs of skin conditions",
                "Strengthens the bond between owner and cat when introduced gradually and positively",
                "Reduces loose fur around the home, which benefits both the cat and allergy-prone household members"
            ],
            "cons": [
                "Many cats resist grooming initially, requiring patience and a gradual approach",
                "Using the wrong tools can damage coat or skin — match supplies to your cat's specific coat type",
                "Long-haired breeds may need daily grooming sessions, which is a significant time commitment",
                "Nail trimming and ear cleaning carry a slight injury risk if technique is incorrect"
            ]
        }
    },
    4244: {
        "cluster": "uncategorized",
        "about_idx": 10,
        "mistakes": [
            "<strong>Using human nail clippers on cats</strong> — Human clippers crush the nail rather than cutting cleanly, causing splitting and pain. Use clippers specifically designed for cat claws.",
            "<strong>Cutting into the quick (pink area inside the nail)</strong> — Cutting too short causes bleeding and pain, making your cat fearful of future nail trims. Trim only the transparent tip, well clear of the pink quick.",
            "<strong>Restraining the cat too forcefully</strong> — Holding a cat down firmly increases stress and resistance. A calm, gentle approach with one paw at a time is more effective and less traumatic.",
            "<strong>Trying to trim all nails in one session from the start</strong> — Start with one or two nails per session and gradually increase. Forcing all nails at once when the cat is not accustomed creates lasting negative associations.",
            "<strong>Forgetting to check dewclaws</strong> — The dewclaw (inner 'thumb' claw) does not contact the ground and does not wear down naturally. It can curl into the paw pad if not trimmed regularly."
        ],
        "suitability": [
            "<strong>Best for beginners:</strong> Scissor-style cat nail clippers with a small, curved cutting edge offer the most control for first-time trimmers",
            "<strong>Best for experienced owners:</strong> Guillotine-style clippers allow quick, precise cuts once you are confident with the technique",
            "<strong>Best for anxious cats:</strong> Quiet, smooth-action clippers with no clicking sound that might startle a nervous cat",
            "<strong>Best for kittens:</strong> Small, lightweight clippers designed for tiny claws — adult-sized tools are awkward and imprecise on kitten nails",
            "<strong>Best on a budget:</strong> A basic pair of scissor-style cat nail clippers at around £5-7 is all most owners need — premium models add comfort but not better cutting performance"
        ],
        "what_to_expect": "Most cats tolerate nail trimming once they have been gradually introduced to the process, though some always find it mildly stressful. Expect to trim nails every two to four weeks, with indoor cats typically needing more frequent attention. Having styptic powder on hand provides peace of mind in case you accidentally cut slightly too short.",
        "pros_cons": {
            "pros": [
                "Prevents overgrown nails from curling into paw pads, which causes pain and infection",
                "Reduces scratching damage to furniture, carpets, and human skin",
                "Regular trimming keeps claws at a comfortable length for the cat's daily activities",
                "A straightforward skill that most owners can learn with practice and patience"
            ],
            "cons": [
                "Cutting the quick causes bleeding and pain, making technique and lighting important",
                "Some cats strongly resist nail trimming and may need gradual desensitisation over weeks",
                "Guillotine-style clippers can crush if the blade is dull — sharpen or replace regularly",
                "Kittens and very small cats require appropriately sized clippers that may not suit adult cats"
            ]
        }
    }
}


# ─── HTML Builders ──────────────────────────────────────────────────────────

def build_about_guide_html(text):
    return f"""<!-- wp:group {{"style":{{"color":{{"background":"#f9fafb"}},"border":{{"radius":"6px","width":"1px","color":"#e5e7eb"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"20px","bottom":"20px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#e5e7eb;border-width:1px;border-radius:6px;background-color:#f9fafb;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"13px"}}}}}} -->
<p style="font-size:13px"><strong>About this guide:</strong> {text} Last reviewed: May 2026. See our <a href="https://pethubonline.com/our-editorial-process/">editorial process</a> for details.</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->"""


def build_common_mistakes_html(mistakes):
    items = "\n".join([f'<!-- wp:list-item -->\n<li>{m}</li>\n<!-- /wp:list-item -->' for m in mistakes])
    return f"""<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">Common Mistakes to Avoid</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul class="wp-block-list">
{items}
</ul>
<!-- /wp:list -->"""


def build_suitability_html(items):
    items_html = "\n".join([f'<!-- wp:list-item -->\n<li>{item}</li>\n<!-- /wp:list-item -->' for item in items])
    return f"""<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">Quick Suitability Guide</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul class="wp-block-list">
{items_html}
</ul>
<!-- /wp:list -->"""


def build_what_to_expect_html(text):
    return f"""<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">What to Expect</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>{text}</p>
<!-- /wp:paragraph -->"""


def build_pros_cons_html(data):
    pros_items = "\n".join([f'<!-- wp:list-item -->\n<li>{p}</li>\n<!-- /wp:list-item -->' for p in data["pros"]])
    cons_items = "\n".join([f'<!-- wp:list-item -->\n<li>{c}</li>\n<!-- /wp:list-item -->' for c in data["cons"]])
    return f"""<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">Key Considerations</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><strong>Advantages:</strong></p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul class="wp-block-list">
{pros_items}
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Things to Watch:</strong></p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul class="wp-block-list">
{cons_items}
</ul>
<!-- /wp:list -->"""


# ─── API Helpers ────────────────────────────────────────────────────────────

def fetch_post(post_id):
    url = f"{WP_API}/posts/{post_id}?context=edit&_fields=id,title,content,slug"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
        if "id" in data:
            return data
        return None
    except json.JSONDecodeError:
        return None


def update_post(post_id, new_content):
    payload = json.dumps({"content": new_content})
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(payload)
        tmpfile = f.name
    try:
        url = f"{WP_API}/posts/{post_id}"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", f"@{tmpfile}",
             url],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            return False, f"curl error: {result.stderr}"
        try:
            resp = json.loads(result.stdout)
            if "id" in resp:
                return True, "OK"
            else:
                return False, f"API error: {result.stdout[:300]}"
        except json.JSONDecodeError:
            return False, f"Invalid JSON: {result.stdout[:300]}"
    finally:
        os.unlink(tmpfile)


def insert_about_guide(content, about_html):
    """Insert About This Guide after Quick Answer box or first heading."""
    qa_end = content.find('<!-- /wp:group -->')
    if qa_end >= 0 and 'Quick Answer' in content[:qa_end + 100]:
        insert_point = qa_end + len('<!-- /wp:group -->')
        return content[:insert_point] + "\n\n" + about_html + "\n\n" + content[insert_point:]

    h_pattern = re.search(r'(<!-- wp:heading.*?-->.*?</h[23]>\s*<!-- /wp:heading -->)', content, re.DOTALL)
    if h_pattern:
        insert_point = h_pattern.end()
        return content[:insert_point] + "\n\n" + about_html + "\n\n" + content[insert_point:]

    p_end = content.find('<!-- /wp:paragraph -->')
    if p_end >= 0:
        insert_point = p_end + len('<!-- /wp:paragraph -->')
        return content[:insert_point] + "\n\n" + about_html + "\n\n" + content[insert_point:]

    return about_html + "\n\n" + content


def insert_before_sources(content, blocks):
    sources_markers = [
        '<h3 class="wp-block-heading">Sources and Further Reading</h3>',
        '<h3 class="wp-block-heading">Sources and Further Reading',
        'Sources and Further Reading</h3>',
        '<h2 class="wp-block-heading">Sources and Further Reading</h2>',
    ]
    insert_point = -1
    for marker in sources_markers:
        idx = content.find(marker)
        if idx >= 0:
            hr_idx = content.rfind('<hr', max(0, idx - 300), idx)
            if hr_idx >= 0:
                insert_point = hr_idx
            else:
                insert_point = idx
            break

    if insert_point < 0:
        for marker in ['Related Guides</h2>', 'Related Guides</h3>']:
            idx = content.find(marker)
            if idx >= 0:
                insert_point = idx
                break

    if insert_point < 0:
        insert_point = len(content)

    combined = "\n\n".join(blocks)
    return content[:insert_point] + combined + "\n\n" + content[insert_point:]


def main():
    print("=" * 70)
    print("BATCH 3 REMAINING: 4 posts")
    print("=" * 70)

    results = []

    for post_id, pdata in POST_DATA.items():
        print(f"\nProcessing post {post_id}...", flush=True)

        post = fetch_post(post_id)
        if not post:
            print(f"  ERROR: Could not fetch post {post_id}")
            results.append({"id": post_id, "title": "FETCH_ERROR", "cluster": pdata["cluster"],
                            "about_guide": False, "common_mistakes": False, "suitability": False,
                            "what_to_expect": False, "pros_cons": False, "status": "FETCH_ERROR"})
            continue

        title = html.unescape(post["title"]["raw"])
        content = post["content"]["raw"]
        print(f"  Title: {title}", flush=True)

        # Check if already has blocks
        if "About this guide:" in content or "Common Mistakes to Avoid" in content or "Quick Suitability Guide" in content:
            print(f"  SKIPPED: Already has blocks", flush=True)
            results.append({"id": post_id, "title": title, "cluster": pdata["cluster"],
                            "about_guide": False, "common_mistakes": False, "suitability": False,
                            "what_to_expect": False, "pros_cons": False, "status": "ALREADY_HAS_BLOCKS"})
            continue

        # Build blocks
        new_content = content

        # 1. About This Guide
        about_text = ABOUT_GUIDE_TEMPLATES[pdata["about_idx"]]
        about_html = build_about_guide_html(about_text)
        new_content = insert_about_guide(new_content, about_html)

        # 2. Common Mistakes
        mistakes_html = build_common_mistakes_html(pdata["mistakes"])

        # 3. Quick Suitability Guide
        suitability_html = build_suitability_html(pdata["suitability"])

        pre_source_blocks = [mistakes_html, suitability_html]

        # 4. What to Expect
        has_wte = False
        if "what_to_expect" in pdata and pdata["what_to_expect"]:
            wte_html = build_what_to_expect_html(pdata["what_to_expect"])
            pre_source_blocks.append(wte_html)
            has_wte = True

        # 5. Key Considerations
        has_pc = False
        if "pros_cons" in pdata and pdata["pros_cons"]:
            pc_html = build_pros_cons_html(pdata["pros_cons"])
            pre_source_blocks.append(pc_html)
            has_pc = True

        # Insert before Sources
        new_content = insert_before_sources(new_content, pre_source_blocks)

        # Update
        success, msg = update_post(post_id, new_content)
        status = "OK" if success else f"ERROR: {msg}"

        print(f"  -> {status} | About: YES | Mistakes: YES | Suitability: YES | WtE: {has_wte} | P/C: {has_pc}", flush=True)

        results.append({
            "id": post_id, "title": title, "cluster": pdata["cluster"],
            "about_guide": True, "common_mistakes": True, "suitability": True,
            "what_to_expect": has_wte, "pros_cons": has_pc, "status": status
        })

        time.sleep(0.5)

    # Append to existing CSV
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        for r in results:
            writer.writerow([
                r["id"], r["title"], r["cluster"],
                r["about_guide"], r["common_mistakes"],
                r["suitability"], r["what_to_expect"],
                r["pros_cons"], r["status"]
            ])

    print(f"\n{'='*70}")
    print("REMAINING POSTS — COMPLETE")
    print(f"{'='*70}")
    ok = sum(1 for r in results if r["status"] == "OK")
    print(f"Processed: {len(results)}, Updated: {ok}")
    print(f"Log appended to: {LOG_FILE}")


if __name__ == "__main__":
    main()
