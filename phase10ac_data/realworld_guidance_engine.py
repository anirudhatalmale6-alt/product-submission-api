#!/usr/bin/env python3
"""
10AC-D: Real-World Guidance Engine
Adds checklists, measurable guidance, timelines, safety warnings,
and troubleshooting sections to thin posts lacking practical guidance.
"""

import subprocess, json, time, csv, re

WP_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"

TRUST_BLOCK_MARKER = '<!-- wp:separator {"className":"is-style-wide"} -->'

GUIDANCE_TEMPLATES = {
    "dog_toy": {
        "title": "Quick Safety Checklist",
        "items": [
            ("Inspect daily:", "check for loose threads, cracked rubber, torn seams, or small pieces that could be swallowed"),
            ("Size check:", "the toy should be too large to fit entirely in your dog's mouth — if it can, it is a choking hazard"),
            ("Supervise first use:", "watch how your dog interacts with any new toy for at least 15 minutes before leaving them alone with it"),
            ("Replace immediately:", "discard any toy showing deep puncture marks, exposed stuffing, or detached squeakers"),
            ("Material match:", "heavy chewers need solid rubber or nylon; plush toys suit gentle dogs only"),
        ]
    },
    "dog_food": {
        "title": "Feeding Quick-Check Guide",
        "items": [
            ("Transition gradually:", "when switching food, mix 25% new food with 75% old for 3 days, then 50/50 for 3 days, then 75/25 for 3 days before going fully new"),
            ("Check the label:", "the first ingredient should be a named protein source (e.g. 'chicken' not 'meat derivatives')"),
            ("Watch weight monthly:", "run your hands along your dog's ribs — you should feel them easily without pressing hard"),
            ("Fresh water always:", "change water at least twice daily and clean the bowl every day"),
            ("Portion control:", "follow the feeding guide on the packet as a starting point, then adjust based on your dog's body condition"),
        ]
    },
    "dog_bed": {
        "title": "Bed Selection Checklist",
        "items": [
            ("Measure your dog:", "measure from nose to base of tail while lying flat, then add 15–20 cm to get the minimum bed length"),
            ("Washing test:", "choose a bed with a removable, machine-washable cover — you will need to wash it at least fortnightly"),
            ("Support check:", "for dogs over 7 years old or with joint issues, memory foam at least 7 cm thick provides meaningful support"),
            ("Location matters:", "place the bed away from draughts, direct heat sources, and high-traffic doorways"),
            ("Non-slip base:", "check the bed has a non-slip bottom, especially on hard floors, to prevent sliding when the dog gets in and out"),
        ]
    },
    "dog_harness": {
        "title": "Harness Fit Checklist",
        "items": [
            ("Two-finger rule:", "you should be able to slide two fingers flat between the harness and your dog's body at every strap point"),
            ("Check the chest plate:", "the front panel should sit centred on the breastbone, not pressing against the throat or restricting shoulder movement"),
            ("Movement test:", "with the harness fitted, watch your dog walk — there should be no chafing, limping, or altered gait"),
            ("Re-measure monthly:", "puppies and young dogs grow rapidly; re-check fit every 2–4 weeks and after any weight change"),
            ("Remove after walks:", "unless your vet advises otherwise, remove the harness indoors to prevent skin irritation from prolonged wear"),
        ]
    },
    "dog_health": {
        "title": "When to Contact Your Vet",
        "items": [
            ("Immediately:", "difficulty breathing, seizures, suspected poisoning, bloated abdomen with distress, or inability to stand"),
            ("Within 24 hours:", "persistent vomiting or diarrhoea lasting more than 12 hours, refusal to eat for more than a day, or sudden lethargy"),
            ("At your next appointment:", "gradual weight changes, mild skin irritation, slightly loose stools, or minor behavioural changes"),
            ("Track symptoms:", "note the start date, frequency, and severity of any symptom before calling your vet — this speeds up diagnosis"),
            ("Keep records:", "maintain a simple health log with vaccination dates, weight checks, and any medication given — your vet will appreciate it"),
        ]
    },
    "puppy_care": {
        "title": "Puppy Development Timeline",
        "items": [
            ("Weeks 3–12 (socialisation window):", "expose your puppy to at least 100 different positive experiences including people, sounds, surfaces, and other vaccinated dogs"),
            ("Weeks 8–16 (fear period):", "avoid overwhelming experiences; keep new introductions gentle and reward calm behaviour"),
            ("Months 3–6 (teething):", "provide appropriate chew toys; frozen washcloths or rubber teething rings help soothe sore gums"),
            ("Months 6–12 (adolescence):", "expect some regression in training; stay consistent with commands and increase exercise gradually"),
            ("Training sessions:", "keep sessions to 5 minutes for puppies under 4 months, 10 minutes for 4–6 months, building to 15 minutes for older puppies"),
        ]
    },
    "cat_supplies": {
        "title": "Cat Environment Checklist",
        "items": [
            ("Vertical space:", "provide at least one elevated resting spot per cat, ideally 1.5 metres or higher — cats feel safer with a high vantage point"),
            ("Litter box rule:", "one litter box per cat plus one extra, placed in quiet, accessible locations away from food and water"),
            ("Scratching provision:", "offer both vertical and horizontal scratching surfaces near resting areas and room entrances"),
            ("Play daily:", "aim for two 10–15 minute interactive play sessions per day to prevent obesity and behavioural issues"),
            ("Safe retreat:", "every cat needs at least one quiet hiding spot where they will not be disturbed by other pets or children"),
        ]
    },
    "dog_care": {
        "title": "Weekly Care Routine",
        "items": [
            ("Dental check:", "lift your dog's lips and check for red gums, tartar buildup, or broken teeth — brush teeth at least 3 times per week"),
            ("Coat inspection:", "run your hands through the coat checking for lumps, ticks, matting, or skin irritation"),
            ("Ear check:", "look inside both ears for redness, discharge, or odour — clean with a vet-approved ear cleaner if waxy"),
            ("Nail length:", "if you can hear nails clicking on hard floors, they need trimming — overgrown nails affect gait and can cause pain"),
            ("Weight monitoring:", "weigh your dog monthly and compare against the breed-standard healthy range — a 10% change warrants a vet check"),
        ]
    },
    "pet_care_general": {
        "title": "Essential Pet Safety Checklist",
        "items": [
            ("Toxic foods:", "keep chocolate, grapes, raisins, onions, garlic, xylitol, and macadamia nuts completely out of reach"),
            ("Medication safety:", "never give human medication to pets unless specifically directed by your vet — paracetamol is lethal to cats"),
            ("ID and microchip:", "ensure your pet's microchip details are up to date and they wear a collar with an ID tag showing your current phone number"),
            ("Emergency plan:", "know your nearest emergency vet's address and opening hours — save their number in your phone now"),
            ("Seasonal hazards:", "antifreeze in winter, heatstroke in summer, fireworks in autumn — prepare for each season's specific risks"),
        ]
    },
}

def fetch_all_posts():
    posts = []
    page = 1
    while True:
        cmd = ["curl", "-s", "--compressed", "-u", AUTH,
               f"{WP_URL}/posts?status=publish&per_page=100&page={page}&context=edit"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        batch = json.loads(r.stdout)
        if not batch or isinstance(batch, dict):
            break
        posts.extend(batch)
        if len(batch) < 100:
            break
        page += 1
        time.sleep(2)
    return posts

def update_post(post_id, content):
    cmd = ["curl", "-s", "--compressed", "-u", AUTH,
           "-X", "POST", f"{WP_URL}/posts/{post_id}",
           "-H", "Content-Type: application/json",
           "-d", json.dumps({"content": content})]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout)

def classify_cluster(post):
    title = post["title"]["raw"].lower()
    cats = post.get("categories", [])
    if 1344 in cats or "dog toy" in title or ("toy" in title and "cat" not in title):
        return "dog_toy"
    if any(kw in title for kw in ["dog food", "puppy food", "dry food", "dry vs wet"]):
        return "dog_food"
    if "dog bed" in title or ("bed" in title and "cat" not in title):
        return "dog_bed"
    if "harness" in title and "cat" not in title:
        return "dog_harness"
    if any(kw in title for kw in ["flea", "joint supplement", "dental care", "dog health"]):
        return "dog_health"
    if any(kw in title for kw in ["grooming", "seasonal dog", "first-time dog", "dental health", "measure your dog"]):
        return "dog_care"
    if "cat toy" in title or "cat play" in title:
        return "cat_supplies"
    if "cat " in title:
        return "cat_supplies"
    if "puppy" in title or "socialisation" in title:
        return "puppy_care"
    if any(kw in title for kw in ["collar", "lead", "bowl", "training treat", "interactive dog", "indestructible"]):
        return "dog_care"
    return "pet_care_general"

def has_checklist(content):
    return bool(re.search(r'<li><strong>[^<]+:</strong>', content))

def build_checklist_block(cluster_key):
    template = GUIDANCE_TEMPLATES.get(cluster_key)
    if not template:
        template = GUIDANCE_TEMPLATES["pet_care_general"]

    items_html = ""
    for label, detail in template["items"]:
        items_html += f"<li><strong>{label}</strong> {detail}</li>\n"

    return f"""<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">{template['title']}</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
{items_html.rstrip()}
</ul>
<!-- /wp:list -->"""

print("Fetching all published posts...")
posts = fetch_all_posts()
print(f"Found {len(posts)} posts\n")

candidates = []
for post in posts:
    content = post["content"]["raw"]
    if has_checklist(content):
        continue
    if "Quick Safety Checklist" in content or "Quick-Check" in content:
        continue
    if "Checklist" in content and "Care Routine" in content:
        continue

    cluster = classify_cluster(post)
    word_count = len(content.split())
    if word_count < 300:
        continue

    candidates.append({
        "post": post,
        "cluster": cluster,
        "word_count": word_count
    })

candidates.sort(key=lambda x: x["word_count"])
targets = candidates[:30]

print(f"Found {len(candidates)} posts without checklists, targeting {len(targets)}\n")

results = []
updated_count = 0

for item in targets:
    post = item["post"]
    pid = post["id"]
    title = post["title"]["raw"]
    content = post["content"]["raw"]
    cluster = item["cluster"]

    block = build_checklist_block(cluster)

    if TRUST_BLOCK_MARKER in content:
        last_idx = content.rfind(TRUST_BLOCK_MARKER)
        new_content = content[:last_idx] + f"\n{block}\n\n" + content[last_idx:]
    else:
        new_content = content + f"\n\n{block}"

    result = update_post(pid, new_content)
    if "id" in result:
        updated_count += 1
        results.append({
            "post_id": pid,
            "title": title[:60],
            "cluster": cluster,
            "checklist_type": GUIDANCE_TEMPLATES.get(cluster, GUIDANCE_TEMPLATES["pet_care_general"])["title"],
            "status": "updated"
        })
        print(f"  {pid}: {cluster} checklist — {title[:50]}")
    else:
        results.append({
            "post_id": pid,
            "title": title[:60],
            "cluster": cluster,
            "checklist_type": "",
            "status": "error"
        })
    time.sleep(2)

csv_path = "/var/lib/freelancer/projects/40416335/phase10ac_data/RealWorld_Guidance_Expansion.csv"
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["post_id", "title", "cluster", "checklist_type", "status"])
    w.writeheader()
    w.writerows(results)

print(f"\n=== REAL-WORLD GUIDANCE: {updated_count} posts updated with checklists ===")
