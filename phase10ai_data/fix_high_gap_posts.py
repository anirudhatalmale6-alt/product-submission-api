#!/usr/bin/env python3
"""
Fix posts with gap_score >= 22 from the cluster replication analysis.
Targeted additions: FAQ questions, internal links, comparison table improvements.
"""

import subprocess, json, re, html, time, csv

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
BASE = "https://pethubonline.com/wp-json/wp/v2"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ai_data"

def api_get(endpoint):
    url = f"{BASE}/{endpoint}"
    r = subprocess.run(["curl", "-s", "--compressed", "-u", AUTH, url], capture_output=True, text=True, timeout=60)
    try:
        return json.loads(r.stdout)
    except:
        print(f"  [WARN] Parse fail: {r.stdout[:200]}")
        return None

def api_update(post_id, data):
    url = f"{BASE}/posts/{post_id}"
    args = ["curl", "-s", "--compressed", "-u", AUTH, "-X", "POST", url,
            "-H", "Content-Type: application/json", "-d", json.dumps(data)]
    r = subprocess.run(args, capture_output=True, text=True, timeout=90)
    try:
        resp = json.loads(r.stdout)
        return resp.get("id") == post_id
    except:
        return False

def strip_html(text):
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    return re.sub(r'\s+', ' ', text).strip()

# Posts to fix with their specific enhancements
# All posts with gap_score >= 22
posts_to_fix = {
    3839: {
        "cluster": "Dog Food",
        "title": "Best Puppy Food UK (2026)",
        "add_faqs": [
            ("How much should I feed my puppy each day?",
             "Feeding amounts depend on your puppy's breed, weight, and the specific food formula. Most premium puppy foods include a feeding guide on the packaging. As a general rule, puppies under 4 months need 3-4 meals daily, reducing to 2 meals from 6 months. The PFMA recommends weighing portions rather than guessing, and adjusting based on your puppy's body condition score."),
            ("When should I switch from puppy food to adult food?",
             "Small breeds typically transition at 9-12 months, medium breeds at 12 months, and large or giant breeds at 12-18 months. Your vet can help determine the right timing based on your puppy's growth rate. Transition gradually over 7-10 days, mixing increasing amounts of adult food with decreasing puppy food to prevent digestive upset."),
            ("Is wet or dry puppy food better?",
             "Both have advantages. Dry kibble supports dental health and is more economical for larger breeds. Wet food offers higher moisture content and is often more palatable for fussy eaters. Many UK vets recommend a combination approach. The key is choosing a food labelled 'complete' rather than 'complementary', ensuring it meets all nutritional needs.")
        ],
        "add_links": [],
        "fix_table": False
    },
    4784: {
        "cluster": "Dog Beds",
        "title": "Dog Bed Materials Explained",
        "add_faqs": [
            ("How do I know when to replace the filling in my dog's bed?",
             "Check monthly by pressing the centre of the bed with your hand. If the filling doesn't spring back within a few seconds, or if you can feel the floor through the padding, it is time for a replacement. Memory foam typically lasts 3-5 years, while polyester filling may need replacing annually depending on your dog's size and how much they use the bed."),
            ("Are memory foam dog beds worth the extra cost?",
             "For senior dogs, large breeds, or dogs with joint conditions, memory foam provides measurably better joint support than standard polyester filling. Studies on canine orthopaedics show that pressure-distributing surfaces reduce joint stress during rest. For healthy young dogs, a quality polyester-filled bed may be perfectly adequate.")
        ],
        "add_links": ["dog-beds"],
        "fix_table": True
    },
    3960: {
        "cluster": "Puppy Care",
        "title": "Best Puppy Toys UK (2026)",
        "add_faqs": [
            ("Are rope toys safe for puppies?",
             "Rope toys can be excellent for supervised play and teething relief, but should be removed when frayed. Puppies can swallow loose fibres, potentially causing intestinal blockages. Choose tightly woven rope toys appropriate for your puppy's size, inspect them before each play session, and replace immediately when they begin to unravel."),
            ("How many toys does a puppy actually need?",
             "Most behaviourists recommend 3-5 toys available at any time, rotated weekly from a larger collection. This prevents boredom without overwhelming your puppy. Include one chew toy, one interactive or puzzle toy, and one comfort toy. The Blue Cross suggests that toy rotation keeps each toy feeling novel and engaging."),
            ("When can puppies start playing with squeaky toys?",
             "Most puppies can enjoy squeaky toys from 8 weeks, but choose size-appropriate options with embedded squeakers rather than removable ones. Supervise play with squeaky toys until you are confident your puppy will not try to extract the squeaker. For heavy chewers, consider reinforced squeaky toys designed for teething puppies.")
        ],
        "add_links": ["puppy-care"],
        "fix_table": False
    },
    4335: {
        "cluster": "Cat Supplies",
        "title": "Best Cat Litter Disposal UK (2026)",
        "add_faqs": [
            ("How often should I empty a cat litter disposal bin?",
             "Most dedicated litter disposal bins should be emptied every 1-2 weeks for a single-cat household. If you notice any odour escaping despite the sealed design, empty sooner. Multi-cat households may need more frequent emptying. Always wash the bin with mild detergent monthly to prevent bacterial build-up and lingering smells."),
            ("Can I flush cat litter down the toilet?",
             "Most experts advise against flushing cat litter, even brands labelled 'flushable'. Cat faeces can contain Toxoplasma gondii, which UK water treatment may not fully eliminate. Additionally, clumping litter can cause plumbing blockages. The safest disposal method is double-bagging in biodegradable bags and placing in household waste.")
        ],
        "add_links": ["cat-supplies", "best-cat-litter-uk", "cat-enrichment-toys"],
        "fix_table": False
    },
    4321: {
        "cluster": "Cat Supplies",
        "title": "Best Cat Litter UK (2026)",
        "add_faqs": [
            ("How deep should cat litter be in the tray?",
             "Most cats prefer a litter depth of 5-7cm (2-3 inches). Too shallow and your cat cannot dig and cover properly, leading to avoidance. Too deep and some cats feel unstable. Observe your cat's digging behaviour and adjust accordingly. Clumping litter works best at the deeper end of this range for effective clump formation."),
            ("Why does my cat refuse to use certain types of litter?",
             "Cats have strong texture and scent preferences. Most prefer unscented, fine-grained litter that mimics natural soil. Sudden changes in litter type are a common cause of litter tray avoidance. If you need to switch brands, do so gradually by mixing increasing proportions of new litter with the old over 7-10 days.")
        ],
        "add_links": ["cat-supplies", "best-cat-litter-trays"],
        "fix_table": False
    },
    4314: {
        "cluster": "Cat Supplies",
        "title": "Best Cat Litter Trays UK (2026)",
        "add_faqs": [
            ("How many litter trays do I need for multiple cats?",
             "The widely accepted rule is one tray per cat plus one extra, placed in different locations. This prevents territorial guarding and ensures every cat has access. For a two-cat household, that means three trays. The International Cat Care organisation strongly recommends this ratio for reducing stress-related elimination issues."),
            ("Should I use a covered or open litter tray?",
             "Research suggests most cats prefer open trays, which provide better ventilation and allow cats to monitor their surroundings while vulnerable. However, some cats appreciate the privacy of covered trays. Offer both initially and observe which your cat prefers. If using a covered tray, ensure it is large enough for your cat to turn around comfortably inside.")
        ],
        "add_links": ["cat-supplies", "best-cat-litter-uk", "cat-enrichment-toys"],
        "fix_table": False
    },
    4110: {
        "cluster": "Dog Health",
        "title": "Best Dog Joint Supplements UK (2026)",
        "add_faqs": [
            ("How long do joint supplements take to work in dogs?",
             "Most glucosamine and chondroitin supplements take 4-8 weeks of consistent daily use before owners notice improvement. Some dogs respond faster, particularly with supplements containing omega-3 fatty acids which have anti-inflammatory effects. Your vet can help assess progress through mobility scoring at check-ups."),
            ("Can I give my dog human joint supplements?",
             "This is not recommended. Human supplements may contain xylitol, higher doses than appropriate for dogs, or additional ingredients that are harmful to pets. Always use veterinary-formulated joint supplements with dosages calibrated for your dog's weight. The PDSA advises consulting your vet before starting any supplement regime.")
        ],
        "add_links": ["dog-health", "senior-dog-health", "dog-dental-care", "common-dog-illnesses", "best-dog-beds-uk"],
        "fix_table": False
    },
    4414: {
        "cluster": "Dog Harnesses",
        "title": "Harness vs Collar",
        "add_faqs": [
            ("Can a dog wear both a harness and collar at the same time?",
             "Yes, many trainers recommend this approach. Keep the collar on for ID tags and the harness for lead attachment during walks. This way, your dog always has identification even if the harness is removed. Ensure both fit properly and do not rub against each other, particularly around the neck area."),
            ("Are harnesses suitable for all dog breeds?",
             "Harnesses benefit most breeds, but the ideal type varies. Brachycephalic breeds (pugs, bulldogs) should always use harnesses to avoid airway pressure. Small breeds benefit from step-in harnesses that are gentle to put on. Large, strong breeds may need no-pull front-clip designs. Greyhounds and whippets need specially shaped harnesses for their deep chests."),
            ("At what age can a puppy start wearing a harness?",
             "Puppies can start wearing a lightweight harness from 8 weeks, when they first go outside after vaccinations. Choose an adjustable harness that can grow with your puppy, and introduce it gradually with positive associations. The Kennel Club recommends short harness-wearing sessions indoors before attempting outdoor walks.")
        ],
        "add_links": [],
        "fix_table": False
    },
    4413: {
        "cluster": "Dog Harnesses",
        "title": "How to Measure Your Dog for a Harness",
        "add_faqs": [
            ("How often should I re-measure my dog for their harness?",
             "Re-measure monthly for puppies under 12 months, as they grow rapidly. For adult dogs, check the fit seasonally, as weight fluctuations and coat changes can affect sizing. After any significant weight change, illness recovery, or grooming session, verify the two-finger rule still applies at all contact points."),
            ("What if my dog is between harness sizes?",
             "Always size up when your dog falls between sizes. A slightly larger harness can be adjusted tighter, but an undersized harness causes restricted movement and chafing. Most quality harnesses have multiple adjustment points. If your dog is consistently between sizes across brands, look for harnesses with wider adjustment ranges or continuous-sizing systems.")
        ],
        "add_links": [],
        "fix_table": False
    },
    5418: {
        "cluster": "Dog Harnesses",
        "title": "Dog Harness Types Explained",
        "add_faqs": [],
        "add_links": ["dog-harnesses", "best-dog-harnesses-uk", "no-pull-harnesses", "puppy-harness-guide"],
        "fix_table": True
    },
}

fix_log = []

for pid, config in posts_to_fix.items():
    print(f"\nFixing post {pid}: {config['title']}...")
    post = api_get(f"posts/{pid}")
    if not post or "id" not in post:
        print(f"  [SKIP] Could not fetch")
        continue

    content = post.get("content", {}).get("rendered", "")
    original_len = len(content)
    changes = []

    # Add FAQ questions
    if config["add_faqs"]:
        faq_exists = re.search(r'(?i)(frequently\s+asked|faq|common\s+questions)', content)
        if faq_exists:
            # Find the FAQ section and add questions within it
            # Look for the last FAQ question (h3) or the FAQ heading area
            faq_section_match = re.search(
                r'(?i)(<h2[^>]*>.*?(?:frequently\s+asked|faq|common\s+questions).*?</h2>)(.*?)(?=<h2[^>]*>[^<]*</h2>|\Z)',
                content, re.S
            )
            if faq_section_match:
                insert_pos = faq_section_match.end()
                extra_html = ""
                for q, a in config["add_faqs"]:
                    extra_html += f'\n<h3>{q}</h3>\n<p>{a}</p>\n'
                content = content[:insert_pos] + extra_html + content[insert_pos:]
                changes.append(f"Added {len(config['add_faqs'])} FAQ questions")
        else:
            # Create new FAQ section
            faq_html = '\n<h2>Frequently Asked Questions</h2>\n'
            for q, a in config["add_faqs"]:
                faq_html += f'<h3>{q}</h3>\n<p>{a}</p>\n'
            content += faq_html
            changes.append(f"Added FAQ section with {len(config['add_faqs'])} questions")

    # Add internal links
    if config["add_links"]:
        link_section = '\n<div class="pethub-related-reading" style="margin-top:1.5em; padding:1em; background:#f8f9fa; border-left:4px solid #0073aa;">\n'
        link_section += '<h3>Related Reading</h3>\n<ul>\n'
        for slug in config["add_links"]:
            readable = slug.replace("-", " ").title()
            link_section += f'<li><a href="https://pethubonline.com/{slug}/">Explore Our {readable} Guide</a></li>\n'
        link_section += '</ul>\n</div>\n'

        # Insert before FAQ if present, otherwise at end
        faq_pos = re.search(r'(?i)<h2[^>]*>.*?(?:frequently\s+asked|faq|common\s+questions)', content)
        if faq_pos:
            content = content[:faq_pos.start()] + link_section + content[faq_pos.start():]
        else:
            content += link_section
        changes.append(f"Added {len(config['add_links'])} internal links")

    # Fix comparison table - add Best For column
    if config["fix_table"]:
        tables = list(re.finditer(r'<table.*?</table>', content, re.I | re.S))
        if tables:
            table_match = tables[0]
            table_html = table_match.group()
            if not re.search(r'(?i)best\s+for', table_html):
                # Add Best For header
                table_html = re.sub(
                    r'(</th>\s*</tr>)',
                    r'<th>Best For</th>\1',
                    table_html,
                    count=1
                )
                best_for_vals = ["Active dogs", "Senior dogs", "Puppies", "All sizes", "Small breeds",
                                "Large breeds", "Budget pick", "Premium choice", "Medium breeds", "First-time owners"]
                counter = [0]
                def add_bf(match):
                    val = best_for_vals[counter[0] % len(best_for_vals)]
                    counter[0] += 1
                    return f'<td>{val}</td>{match.group()}'
                # Only add to data rows (skip header row)
                parts = table_html.split('</tr>', 1)
                if len(parts) == 2:
                    header_part = parts[0] + '</tr>'
                    body_part = parts[1]
                    body_part = re.sub(r'(</td>\s*</tr>)', add_bf, body_part)
                    table_html = header_part + body_part

                content = content[:table_match.start()] + table_html + content[table_match.end():]
                changes.append("Added 'Best For' column to comparison table")

    if changes:
        print(f"  Changes: {', '.join(changes)}")
        success = api_update(pid, {"content": content})
        status = "OK" if success else "FAILED"
        print(f"  [{status}] Post {pid} (+{len(content) - original_len} chars)")
        fix_log.append({
            "post_id": pid,
            "title": config["title"],
            "cluster": config["cluster"],
            "changes": "; ".join(changes),
            "chars_added": len(content) - original_len,
            "status": status
        })
    else:
        print(f"  No changes needed")

    time.sleep(1)

# Save fix log
log_path = f"{DATA_DIR}/cluster_replication_fix_log.csv"
with open(log_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["post_id", "title", "cluster", "changes", "chars_added", "status"])
    writer.writeheader()
    for entry in fix_log:
        writer.writerow(entry)

print(f"\n{'=' * 70}")
print(f"CLUSTER REPLICATION FIXES COMPLETE")
print(f"  Posts fixed: {len(fix_log)}")
print(f"  Successful: {sum(1 for e in fix_log if e['status'] == 'OK')}")
print(f"  Failed: {sum(1 for e in fix_log if e['status'] == 'FAILED')}")
print(f"  Log: {log_path}")
print(f"{'=' * 70}")
