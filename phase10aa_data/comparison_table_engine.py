#!/usr/bin/env python3
"""
Comparison Table Expansion Engine
Adds educational comparison tables to posts where they'd have highest citation impact.
Rules: no fake rankings, no unsupported 'best' claims, no Product/Review schema.
Only educational/feature/material/suitability comparisons.
"""

import subprocess, json, time, csv, re

WP_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"

TRUST_BLOCK = '''<!-- wp:separator {"className":"is-style-wide"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-wide"/>
<!-- /wp:separator -->
<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">About Our Editorial Standards</h3>
<!-- /wp:heading -->'''

COMPARISON_TABLES = {
    4784: {
        "title": "Dog Bed Materials Compared",
        "intro": "The following table compares common dog bed filling materials across key factors that affect comfort, durability, and suitability for different dogs.",
        "headers": ["Material", "Support Level", "Durability", "Best Suited For", "Washability"],
        "rows": [
            ["Memory foam", "High — moulds to body shape", "3–5 years typical", "Senior dogs, joint issues", "Cover removable; foam spot-clean only"],
            ["Egg-crate foam", "Medium — distributes pressure", "2–3 years typical", "Budget-friendly orthopaedic option", "Cover removable; foam degrades faster"],
            ["Polyester fibre fill", "Low to medium — compresses over time", "1–2 years before flattening", "Puppies, light dogs", "Fully machine washable"],
            ["Bolster/raised edge", "Medium — varies by fill", "2–4 years depending on fill", "Dogs who like to rest their head", "Depends on inner material"],
            ["Gel-infused foam", "High — temperature regulating", "3–5 years typical", "Dogs prone to overheating", "Cover removable; gel foam spot-clean"],
        ]
    },
    5416: {
        "title": "Dog Bed Types at a Glance",
        "intro": "This comparison summarises the main dog bed types, helping you match bed style to your dog's sleeping habits and needs.",
        "headers": ["Bed Type", "Shape", "Best For", "Common Sizes", "Key Consideration"],
        "rows": [
            ["Flat mat / cushion", "Rectangular, low profile", "Dogs who sprawl when sleeping", "Small to extra-large", "Easy to wash but offers less joint support"],
            ["Bolster bed", "Raised edges, sunken centre", "Dogs who curl up or rest chin", "Small to large", "Edges may compress with heavy use"],
            ["Orthopaedic bed", "Flat or bolster, memory foam", "Senior dogs, large breeds, joint problems", "Medium to extra-large", "Higher cost but longer-lasting support"],
            ["Elevated / raised cot", "Fabric stretched on frame", "Warm climates, outdoor use", "Small to extra-large", "Good airflow; not suitable for chewers"],
            ["Cave / hooded bed", "Enclosed, dome-shaped", "Anxious dogs, small breeds", "Small to medium", "Provides security; harder to clean"],
            ["Donut / calming bed", "Round, plush raised rim", "Dogs seeking nesting comfort", "Small to large", "Soft fill compresses over time"],
        ]
    },
    5510: {
        "title": "Dog Bed Size Guide by Weight",
        "intro": "Use this table as a starting point for matching your dog's weight to an appropriate bed size. Always measure your dog lying down for the most accurate fit.",
        "headers": ["Dog Weight", "Typical Bed Size", "Minimum Bed Dimensions", "Examples of Breeds"],
        "rows": [
            ["Under 10 kg", "Small", "45 cm x 35 cm", "Chihuahua, Yorkshire Terrier, Pomeranian"],
            ["10–25 kg", "Medium", "60 cm x 50 cm", "Cocker Spaniel, Beagle, Border Collie"],
            ["25–40 kg", "Large", "80 cm x 60 cm", "Labrador, Golden Retriever, Boxer"],
            ["Over 40 kg", "Extra-large", "100 cm x 75 cm or larger", "German Shepherd, Great Dane, Rottweiler"],
        ]
    },
    5418: {
        "title": "Dog Harness Types Compared",
        "intro": "Different harness designs serve different purposes. This table compares the main types to help you understand which suits your dog's needs.",
        "headers": ["Harness Type", "How It Works", "Best Suited For", "Potential Drawbacks"],
        "rows": [
            ["Back-clip", "Lead attaches at the back", "Calm walkers, small dogs", "Less steering control; may encourage pulling in some dogs"],
            ["Front-clip", "Lead attaches at the chest", "Dogs that pull; training purposes", "Can cause uneven gait if poorly fitted"],
            ["Dual-clip", "Attachment points front and back", "Versatile training and walking", "More complex to fit; heavier"],
            ["Step-in", "Dog steps into loops; clips at back", "Dogs uncomfortable with over-head fitting", "Less secure for strong pullers"],
            ["Head halter", "Loop around muzzle and behind ears", "Strong pullers needing redirection", "Requires careful introduction; may distress some dogs"],
        ]
    },
    4414: {
        "title": "Harness vs Collar: Key Differences",
        "intro": "Both harnesses and collars have valid uses. This comparison highlights the practical differences to help you choose based on your dog's behaviour and needs.",
        "headers": ["Factor", "Collar", "Harness"],
        "rows": [
            ["Pressure distribution", "Concentrated on neck and throat", "Spread across chest, shoulders, or back"],
            ["Control for pullers", "Limited; risk of choking", "Better control; reduces strain on neck"],
            ["Ease of fitting", "Quick and simple", "Takes longer; requires adjustment"],
            ["ID tag attachment", "Convenient — always visible", "Usually needs a separate collar for tags"],
            ["Risk of escape", "Higher for dogs with narrow heads", "Lower — wraps around body"],
            ["Suitability for puppies", "Lightweight options available", "Recommended for training; reduces neck strain"],
            ["Breeds at risk (flat-faced)", "Higher risk of breathing restriction", "Preferred — avoids throat pressure"],
        ]
    },
    5422: {
        "title": "Indoor vs Outdoor Dog Toys Compared",
        "intro": "Choosing between indoor and outdoor toys depends on space, play style, and safety considerations. This table highlights the key differences.",
        "headers": ["Factor", "Indoor Toys", "Outdoor Toys"],
        "rows": [
            ["Space needed", "Minimal — designed for confined areas", "Open space preferred"],
            ["Common types", "Puzzle toys, snuffle mats, chew toys", "Fetch toys, frisbees, tug ropes"],
            ["Noise level", "Generally quieter", "Can be noisy (squeakers, balls bouncing)"],
            ["Durability needs", "Moderate — less exposure to elements", "Higher — must withstand weather, dirt, impact"],
            ["Supervision level", "Can be used during quiet time", "Active supervision recommended"],
            ["Enrichment type", "Mental stimulation, calm focus", "Physical exercise, high energy"],
        ]
    },
    5420: {
        "title": "Dog Toy Cleaning Methods by Material",
        "intro": "Different toy materials require different cleaning approaches. Use this table to keep your dog's toys hygienic without damaging them.",
        "headers": ["Material", "Cleaning Method", "Frequency", "What to Avoid"],
        "rows": [
            ["Hard rubber (e.g. Kong-type)", "Warm soapy water; dishwasher safe (top rack)", "Weekly or after heavy use", "Bleach; abrasive scrubbers"],
            ["Rope toys", "Machine wash on gentle cycle; air dry fully", "Every 1–2 weeks", "Microwave drying (fire risk if metal present)"],
            ["Plush / fabric toys", "Machine wash in mesh bag; low heat dry", "Weekly; more if slobbered on", "High heat — can melt filling or squeakers"],
            ["Nylon / plastic", "Warm soapy water; rinse thoroughly", "Weekly", "Harsh chemicals that may leave residue"],
            ["Natural materials (antler, wood)", "Wipe with damp cloth; air dry", "After each use", "Submerging in water — causes splitting"],
        ]
    },
    5458: {
        "title": "Cat Scratching Surface Types Compared",
        "intro": "Cats have preferences for different scratching surfaces. Understanding the options helps you provide appropriate outlets for this natural behaviour.",
        "headers": ["Surface Type", "Texture Appeal", "Durability", "Best Placement", "Cost Range"],
        "rows": [
            ["Sisal rope (wrapped)", "High — satisfying shred resistance", "Medium to high (6–18 months)", "Vertical posts, door-mounted", "Moderate"],
            ["Sisal fabric (flat)", "High — similar to sisal rope", "High (resists fraying longer)", "Post wraps, wall-mounted panels", "Moderate"],
            ["Corrugated cardboard", "Very high — many cats prefer this", "Low (1–3 months)", "Floor pads, incline scratchers", "Low"],
            ["Carpet", "Medium — familiar texture", "Medium (frays over time)", "Cat trees, floor mats", "Low to moderate"],
            ["Wood / bark", "Medium — appeals to outdoor cats", "High (slow wear)", "Tree-trunk style posts", "Low to moderate"],
        ]
    },
    5523: {
        "title": "Dog Training Equipment Comparison",
        "intro": "Understanding what each piece of training equipment does — and does not do — helps you choose tools that match your training approach.",
        "headers": ["Equipment", "Primary Use", "Skill Level Needed", "Key Consideration"],
        "rows": [
            ["Flat collar", "ID tags, basic lead walking", "Beginner", "Not suitable for dogs that pull heavily"],
            ["Front-clip harness", "Reducing pulling during walks", "Beginner", "Must be fitted correctly to avoid chafing"],
            ["Long line (5–10 m)", "Recall training, controlled freedom", "Intermediate", "Use in open areas; avoid tangling"],
            ["Clicker", "Marking desired behaviours precisely", "Beginner to intermediate", "Requires consistent timing and follow-up reward"],
            ["Treat pouch", "Quick reward delivery during training", "Beginner", "Keep treats small and low-calorie"],
            ["Crate", "House training, safe space, travel", "Beginner (with guidance)", "Must never be used as punishment"],
        ]
    },
    4566: {
        "title": "Seasonal Risks and Precautions for Dogs",
        "intro": "Each season brings different hazards for dogs. This table summarises the key risks and simple precautions for each time of year.",
        "headers": ["Season", "Main Risks", "Signs to Watch For", "Basic Precautions"],
        "rows": [
            ["Spring", "Toxic plants, fertilisers, increased tick activity", "Vomiting, skin irritation, lethargy", "Check garden plants; start parasite prevention"],
            ["Summer", "Heatstroke, hot pavements, blue-green algae", "Excessive panting, drooling, collapse", "Walk early/late; always carry water; avoid stagnant water"],
            ["Autumn", "Conkers, acorns, darker walks, mushrooms", "Stomach upset, disorientation", "Keep on lead near fallen nuts; use reflective gear"],
            ["Winter", "Antifreeze, rock salt, hypothermia", "Shivering, cracked paws, lethargy", "Wipe paws after walks; avoid puddles near roads; provide coat if needed"],
        ]
    },
    5469: {
        "title": "Dog Toy Rotation Strategies Compared",
        "intro": "There is no single correct way to rotate toys. The best approach depends on your dog's play style and your household routine.",
        "headers": ["Strategy", "How It Works", "Best For", "Effort Level"],
        "rows": [
            ["Daily swap", "Change 2–3 toys each day", "Easily bored dogs, high-energy breeds", "High — requires organisation"],
            ["Weekly rotation", "Swap the full set every 7 days", "Most dogs; balanced novelty", "Moderate — manageable routine"],
            ["Category rotation", "Rotate by type (chew, puzzle, fetch)", "Dogs with varied play preferences", "Moderate — group by type"],
            ["Event-based", "Introduce toys for specific times (crate, walk, training)", "Structured households, training-focused", "Low — tied to routine events"],
        ]
    },
    5476: {
        "title": "Mental Stimulation Toy Types Compared",
        "intro": "Different puzzle and enrichment toys challenge dogs in different ways. Matching the toy type to your dog's experience level helps prevent frustration.",
        "headers": ["Toy Type", "How It Works", "Difficulty Level", "Best For"],
        "rows": [
            ["Snuffle mat", "Dog sniffs through fabric folds to find treats", "Beginner", "Scent-driven dogs, calm enrichment"],
            ["Treat-dispensing ball", "Rolls and releases treats through openings", "Beginner to intermediate", "Food-motivated dogs, independent play"],
            ["Slider puzzle", "Dog moves sliders or lifts lids to reveal treats", "Intermediate", "Problem-solvers, supervised play"],
            ["Multi-step puzzle", "Requires sequential actions to access reward", "Advanced", "Experienced puzzle dogs, high-drive breeds"],
            ["Frozen Kong / lick mat", "Dog works to lick out frozen filling", "Beginner to intermediate", "Calming sessions, crate enrichment, teething puppies"],
        ]
    },
    5467: {
        "title": "Pet Feeding Methods Compared",
        "intro": "How you feed your pet matters as much as what you feed. This table compares common feeding approaches and their suitability.",
        "headers": ["Feeding Method", "How It Works", "Advantages", "Disadvantages"],
        "rows": [
            ["Scheduled meals", "Set portions at fixed times (e.g. twice daily)", "Portion control; monitors appetite changes", "Requires consistent routine"],
            ["Free feeding", "Food available at all times", "Convenient; suits grazers", "Risk of overeating; harder to monitor intake"],
            ["Puzzle feeding", "Food dispensed through enrichment toys", "Mental stimulation; slows eating", "Not suitable for all food types; needs supervision initially"],
            ["Slow feeder bowls", "Bowl design forces slower eating", "Reduces bloat risk; easy to implement", "Some dogs may become frustrated"],
            ["Hand feeding", "Owner delivers food piece by piece", "Builds bond; useful for training", "Time-consuming; impractical for daily use"],
        ]
    },
    5509: {
        "title": "Common Toy Materials: Safety Overview",
        "intro": "Not all toy materials carry the same risks. This table provides an overview of common materials used in pet toys and their general safety profile.",
        "headers": ["Material", "Common Uses", "Safety Considerations", "Durability"],
        "rows": [
            ["Natural rubber", "Chew toys, fetch balls", "Generally safe; check for small pieces breaking off", "High for quality brands"],
            ["Thermoplastic rubber (TPR)", "Budget chew toys, balls", "Varies by manufacturer; avoid strong chemical odours", "Medium"],
            ["Nylon", "Chew bones, dental toys", "Hard surface may chip teeth in aggressive chewers", "High"],
            ["Cotton rope", "Tug toys, dental flossing toys", "Risk of ingesting fibres; supervise play", "Low to medium — frays with use"],
            ["Polyester plush", "Stuffed toys, comfort toys", "Squeakers and stuffing are choking hazards if torn", "Low — not for heavy chewers"],
            ["Felt / wool", "Quiet toys, cat toys", "Check for loose fibres; generally low risk", "Low to medium"],
        ]
    },
    4411: {
        "title": "Dog Harness Styles at a Glance",
        "intro": "Each harness style offers different benefits depending on your dog's size, behaviour, and walking needs.",
        "headers": ["Style", "Lead Attachment", "Best For", "Fitting Complexity"],
        "rows": [
            ["Back-clip Y-shape", "Single clip on back", "Everyday walking, small to medium dogs", "Simple — two adjustment points"],
            ["Front-clip anti-pull", "Single clip on chest", "Training, dogs that pull", "Moderate — chest strap must sit correctly"],
            ["Dual-clip", "Both front and back clips", "Versatile use, transitioning from pulling", "Moderate to complex"],
            ["Step-in", "Clip on back; dog steps into leg loops", "Dogs who dislike harnesses going over head", "Simple — but less adjustable"],
            ["Vest / padded", "Usually back clip; broad coverage", "Small breeds, dogs with sensitive skin", "Moderate — ensure snug but not restrictive"],
        ]
    },
    4570: {
        "title": "First-Time Dog Owner: Essential Categories",
        "intro": "New dog owners face many purchasing decisions. This table outlines the essential categories and what to prioritise when starting out.",
        "headers": ["Category", "What You Need First", "Can Wait", "Typical Budget Range"],
        "rows": [
            ["Feeding", "Bowls, age-appropriate food", "Slow feeders, puzzle feeders", "Low to moderate"],
            ["Walking", "Lead, collar or harness, poo bags", "Long lines, reflective gear", "Low"],
            ["Sleeping", "A bed or crate with bedding", "Orthopaedic bed, travel bed", "Low to moderate"],
            ["Safety", "ID tag, microchip (legal requirement), pet insurance review", "GPS tracker", "Low (tag); varies (insurance)"],
            ["Grooming", "Basic brush, nail clippers", "Professional grooming tools, shampoo", "Low"],
            ["Play & enrichment", "1–2 chew toys, 1 fetch toy", "Puzzle toys, rotation collection", "Low"],
        ]
    },
}

def build_table_block(table_data):
    """Build Gutenberg table block HTML."""
    d = table_data
    header_cells = "".join(f"<th>{h}</th>" for h in d["headers"])
    body_rows = ""
    for row in d["rows"]:
        cells = "".join(f"<td>{c}</td>" for c in row)
        body_rows += f"<tr>{cells}</tr>"

    block = f'''<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">{d["title"]}</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>{d["intro"]}</p>
<!-- /wp:paragraph -->

<!-- wp:table -->
<figure class="wp-block-table"><table><thead><tr>{header_cells}</tr></thead><tbody>{body_rows}</tbody></table></figure>
<!-- /wp:table -->'''
    return block

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

for post_id, table_data in COMPARISON_TABLES.items():
    print(f"\n--- Processing {post_id}: {table_data['title']} ---")
    try:
        post = fetch_post(post_id)
        if "id" not in post:
            print(f"  ERROR: Could not fetch post {post_id}")
            results.append({"post_id": post_id, "title": table_data["title"], "status": "fetch_error"})
            time.sleep(3)
            continue

        content = post["content"]["raw"]
        table_block = build_table_block(table_data)

        # Insert before trust editorial block if present
        if TRUST_BLOCK in content:
            new_content = content.replace(TRUST_BLOCK, f"\n{table_block}\n\n{TRUST_BLOCK}")
            print(f"  Inserted before trust block")
        # Try alternate trust block patterns
        elif '<!-- wp:separator {"className":"is-style-wide"} -->' in content:
            # Find the last separator (trust block is always last)
            sep_marker = '<!-- wp:separator {"className":"is-style-wide"} -->'
            last_idx = content.rfind(sep_marker)
            if last_idx > 0:
                new_content = content[:last_idx] + f"\n{table_block}\n\n" + content[last_idx:]
                print(f"  Inserted before last separator")
            else:
                new_content = content + f"\n\n{table_block}"
                print(f"  Appended to end")
        else:
            new_content = content + f"\n\n{table_block}"
            print(f"  Appended to end (no trust block found)")

        updated = update_post(post_id, new_content)
        if "id" in updated:
            print(f"  SUCCESS: Updated post {post_id}")
            results.append({
                "post_id": post_id,
                "title": post["title"]["raw"],
                "table_title": table_data["title"],
                "rows": len(table_data["rows"]),
                "columns": len(table_data["headers"]),
                "status": "updated"
            })
        else:
            print(f"  ERROR updating: {str(updated)[:200]}")
            results.append({"post_id": post_id, "title": table_data["title"], "status": "update_error"})

        time.sleep(3)
    except Exception as e:
        print(f"  EXCEPTION: {e}")
        results.append({"post_id": post_id, "title": table_data["title"], "status": f"error: {e}"})
        time.sleep(3)

# Write CSV
csv_path = "/var/lib/freelancer/projects/40416335/phase10aa_data/Comparison_Table_Expansion.csv"
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["post_id", "title", "table_title", "rows", "columns", "status"])
    w.writeheader()
    w.writerows(results)

success = sum(1 for r in results if r.get("status") == "updated")
print(f"\n=== COMPLETE: {success}/{len(results)} posts updated with comparison tables ===")
print(f"CSV saved to: {csv_path}")
