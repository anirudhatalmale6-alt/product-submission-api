#!/usr/bin/env python3
"""
Phase 10AV/10AY/10AW — Dog Toys Cluster
Comparison Dominance + Trust Depth + Decision Support

Adds missing: comparison tables, quick checklists, what-to-do-next blocks
to all published Dog Toys posts on pethubonline.com.
"""

import subprocess, json, time, csv, os, re, sys, tempfile
from datetime import datetime

# ── credentials ──────────────────────────────────────────────────────────────
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
BASE = "https://pethubonline.com/wp-json/wp/v2"
DELAY = 2
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10av_data"
CSV_PATH = os.path.join(DATA_DIR, "dog_toys_dominance.csv")

# ── helpers ──────────────────────────────────────────────────────────────────

def api_get(endpoint):
    """GET from WP REST API."""
    url = f"{BASE}/{endpoint}"
    r = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    if r.returncode != 0:
        print(f"  [CURL ERROR] {r.stderr[:200]}")
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        print(f"  [JSON ERROR] {r.stdout[:300]}")
        return None


def api_update(post_id, payload):
    """POST update to WP REST API using temp file."""
    url = f"{BASE}/posts/{post_id}"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        tmp = f.name
    try:
        r = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-X", "POST", "-H", "Content-Type: application/json",
             "-d", f"@{tmp}", url],
            capture_output=True, text=True, timeout=90
        )
        if r.returncode != 0:
            print(f"  [UPDATE CURL ERROR] {r.stderr[:200]}")
            return None
        data = json.loads(r.stdout)
        if "id" in data:
            return data
        else:
            print(f"  [UPDATE ERROR] {json.dumps(data)[:300]}")
            return None
    finally:
        os.unlink(tmp)


def fetch_all_dog_toy_posts():
    """Search multiple terms to find all dog-toy-related published posts."""
    search_terms = [
        "dog+toy", "dog+toys", "enrichment", "puzzle+toy",
        "chew+toy", "tug+play", "tug+toy", "interactive+toy",
        "fetch+toy", "rope+toy", "squeaky+toy", "plush+toy",
        "treat+dispensing", "kong", "dog+ball", "puppy+toy",
        "indestructible+toy", "dog+play", "mental+stimulation+dog",
        "boredom+dog", "teething+toy", "dental+toy",
        "aggressive+chewer", "power+chewer", "toy+safety+dog",
        "toy+rotation", "snuffle+mat", "lick+mat"
    ]

    seen_ids = set()
    posts = []

    for term in search_terms:
        page = 1
        while True:
            data = api_get(
                f"posts?search={term}&per_page=50&status=publish"
                f"&page={page}&_fields=id,title,link"
            )
            if not data or not isinstance(data, list) or len(data) == 0:
                break
            for p in data:
                pid = p["id"]
                if pid not in seen_ids:
                    seen_ids.add(pid)
                    title = p["title"]["rendered"] if isinstance(p["title"], dict) else p["title"]
                    posts.append({"id": pid, "title": title, "link": p.get("link", "")})
            if len(data) < 50:
                break
            page += 1
            time.sleep(0.5)
        time.sleep(0.3)

    # Also ensure posts 3 and 5420 are included
    for must_id in [3, 5420]:
        if must_id not in seen_ids:
            data = api_get(f"posts/{must_id}?_fields=id,title,link,status")
            if data and isinstance(data, dict) and data.get("status") == "publish":
                title = data["title"]["rendered"] if isinstance(data["title"], dict) else data["title"]
                posts.append({"id": must_id, "title": title, "link": data.get("link", "")})
                seen_ids.add(must_id)

    return posts


def is_dog_toy_post(title, content):
    """Filter: only keep posts genuinely about dog toys / enrichment / play."""
    text = (title + " " + content).lower()
    # Must mention dog/puppy AND toy/play/enrichment/chew
    dog_words = ["dog", "puppy", "pup", "canine"]
    toy_words = [
        "toy", "toys", "chew", "tug", "fetch", "play", "enrichment",
        "puzzle", "kong", "squeaky", "plush", "rope", "ball",
        "treat-dispensing", "treat dispensing", "snuffle", "lick mat",
        "interactive", "indestructible", "teething", "dental chew",
        "mental stimulation", "boredom buster", "toy rotation"
    ]
    has_dog = any(w in text for w in dog_words)
    has_toy = any(w in text for w in toy_words)
    return has_dog and has_toy


# ── block detectors ──────────────────────────────────────────────────────────

def has_comparison_table(content):
    return "is-style-stripes" in content and "<table" in content

def has_quick_checklist(content):
    return "Quick Checklist" in content and "#f5f3ff" in content

def has_what_to_do_next(content):
    return "What to Do Next" in content and "#f0fdfa" in content

def has_common_mistakes(content):
    return "Common Mistakes" in content

def has_key_terms(content):
    return "Key Terms" in content

def has_key_takeaways(content):
    return "Key Takeaways" in content


# ── content generators ───────────────────────────────────────────────────────

# A library of comparison tables for different subtopics
COMPARISON_TABLES = {
    "default_play_style": {
        "headers": ["Type", "Best For", "Considerations", "Suitability"],
        "rows": [
            ["Fetch toys (balls, frisbees)", "High-energy breeds needing aerobic exercise", "Check size to prevent choking; avoid tennis balls long-term (abrasive felt)", "Most dogs; supervise outdoors"],
            ["Tug toys (rope, rubber)", "Bonding through interactive play; jaw exercise", "Choose appropriate length; replace when frayed or unravelling", "Strong pullers; not ideal for resource-guarding dogs without training"],
            ["Puzzle / treat-dispensing", "Mental stimulation; slowing fast eaters", "Difficulty level should match dog's experience; clean regularly", "All ages; especially high-intelligence breeds"],
            ["Chew toys (rubber, nylon)", "Teething puppies; dogs who love to gnaw", "Match hardness to chew strength; discard once small enough to swallow", "Puppies through seniors; match to jaw power"],
            ["Plush / squeaky toys", "Comfort play; gentle mouthing breeds", "Supervise destuffers; remove squeaker if swallowed risk exists", "Light chewers; comfort-seeking dogs"],
            ["Snuffle mats / lick mats", "Calming enrichment; scent-work stimulation", "Wash frequently to prevent mould; supervise initially", "Anxious dogs; post-walk wind-down"],
        ]
    },
    "material_safety": {
        "headers": ["Material", "Best For", "Safety Considerations", "Durability"],
        "rows": [
            ["Natural rubber (latex-free)", "General chewing; fetch toys", "Non-toxic; ensure no small breakable pieces", "High — withstands heavy chewing"],
            ["Thermoplastic rubber (TPR)", "Bouncy fetch toys; teething", "BPA-free options preferred; check for chemical odours", "Moderate to high"],
            ["Nylon / polyamide", "Power chewers; long-lasting gnaw toys", "Can splinter if low quality; choose veterinary-grade", "Very high — resists aggressive chewing"],
            ["Cotton rope", "Tug games; dental flossing effect", "Fibres can cause intestinal blockage if ingested in quantity", "Moderate — replace when fraying"],
            ["Plush / fleece fabric", "Comfort toys; light play", "Remove stuffing and squeakers for destuffers", "Low — not for aggressive chewers"],
            ["Silicone (food-grade)", "Lick mats; treat moulds", "Dishwasher safe; ensure food-grade certification", "High — heat and cold resistant"],
        ]
    },
    "durability": {
        "headers": ["Chew Strength", "Recommended Material", "Toy Examples", "Replacement Frequency"],
        "rows": [
            ["Light chewer", "Plush, soft rubber, fleece", "Stuffed animals, soft balls, comfort toys", "When visibly worn or destuffed"],
            ["Moderate chewer", "Natural rubber, TPR, cotton rope", "Standard Kongs, rubber rings, braided ropes", "Every 2–4 weeks or when damaged"],
            ["Power chewer", "Nylon, hard rubber, reinforced stitching", "Heavy-duty chew bones, thick rubber toys", "Every 1–2 weeks; inspect daily"],
            ["Aggressive destroyer", "Veterinary-grade nylon, solid rubber", "Indestructible-rated toys only; avoid plush entirely", "Replace immediately when any piece breaks off"],
            ["Senior / gentle mouth", "Soft rubber, plush, silicone", "Gentle-chew range, lick mats, soft fetch balls", "When misshapen; prioritise comfort"],
        ]
    },
    "enrichment_type": {
        "headers": ["Enrichment Type", "How It Works", "Benefits", "Best Suited For"],
        "rows": [
            ["Food puzzles", "Dog manipulates toy to release treats", "Reduces boredom; slows eating; builds problem-solving skills", "Food-motivated dogs; fast eaters"],
            ["Scent work (snuffle mats)", "Treats hidden in fabric folds for nose-led foraging", "Engages natural foraging instinct; calming effect", "All breeds; especially scent hounds"],
            ["Lick mats", "Spreadable food licked from textured surface", "Releases calming endorphins; great for anxiety", "Anxious dogs; bath-time distraction"],
            ["Interactive / motorised toys", "Battery-powered movement triggers chase instinct", "Physical exercise without owner involvement", "Home-alone dogs; high-energy breeds"],
            ["Frozen enrichment", "Treats frozen inside toys or ice blocks", "Extended engagement; cooling in warm weather", "Teething puppies; summer enrichment"],
            ["DIY enrichment (cardboard, muffin tins)", "Household items repurposed as puzzle feeders", "Zero cost; easily varied; reduces waste", "Budget-conscious owners; creative play"],
        ]
    },
    "age_appropriate": {
        "headers": ["Life Stage", "Recommended Toy Types", "Key Considerations", "Avoid"],
        "rows": [
            ["Puppy (8–16 weeks)", "Soft rubber teethers, small plush, frozen cloths", "Gentle on developing teeth; small enough for tiny mouths", "Hard nylon; toys with small detachable parts"],
            ["Adolescent (4–12 months)", "Medium rubber chews, rope toys, beginner puzzles", "Teething intensifies; rotate toys to maintain interest", "Toys sized for adult dogs (choking risk)"],
            ["Adult (1–7 years)", "Full range based on chew strength and play style", "Match toy to energy level and breed tendencies", "Worn-out or damaged toys; undersized items"],
            ["Senior (7+ years)", "Soft chews, gentle puzzles, comfort plush", "Dental sensitivity; joint considerations for fetch", "Hard chews that may crack ageing teeth"],
            ["Multi-dog household", "Duplicates to prevent guarding; varied types", "Supervise shared play; separate high-value items", "Single high-value toy that triggers conflict"],
        ]
    },
}

def pick_comparison_table(title, content):
    """Choose the best comparison table based on post content."""
    text = (title + " " + content).lower()

    if any(w in text for w in ["material", "rubber", "nylon", "cotton", "safe", "toxic", "bpa"]):
        return "material_safety"
    if any(w in text for w in ["durability", "indestructible", "power chewer", "aggressive chewer", "destroy", "tough"]):
        return "durability"
    if any(w in text for w in ["enrichment", "puzzle", "snuffle", "lick mat", "boredom", "mental stimulation", "brain"]):
        return "enrichment_type"
    if any(w in text for w in ["puppy", "senior", "age", "teething", "old dog", "life stage", "adolescent"]):
        return "age_appropriate"
    # Default: play style
    return "default_play_style"


def build_comparison_html(table_key):
    """Build WordPress table block HTML."""
    tbl = COMPARISON_TABLES[table_key]
    headers = tbl["headers"]
    rows = tbl["rows"]

    thead = "<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>"
    tbody_rows = []
    for row in rows:
        tbody_rows.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
    tbody = "".join(tbody_rows)

    return (
        '<!-- wp:table {"className":"is-style-stripes"} -->\n'
        '<figure class="wp-block-table is-style-stripes"><table><thead>'
        f'{thead}</thead><tbody>{tbody}</tbody></table></figure>\n'
        '<!-- /wp:table -->'
    )


# Checklist items by topic
CHECKLIST_LIBRARY = {
    "default_play_style": [
        "Choose toys sized appropriately for your dog's breed — too small risks choking",
        "Rotate toys every few days to maintain novelty and interest",
        "Inspect toys daily for cracks, loose pieces, or fraying",
        "Supervise all play sessions, especially with new toys",
        "Match toy type to your dog's natural play preference (fetch, tug, chew, or puzzle)",
        "Remove and discard any toy that shows signs of breaking apart",
        "Wash fabric and rubber toys weekly to prevent bacteria buildup",
    ],
    "material_safety": [
        "Check labels for BPA-free, phthalate-free, and non-toxic certifications",
        "Avoid toys with strong chemical odours — off-gassing can indicate harmful substances",
        "Choose natural rubber over PVC whenever possible",
        "Inspect rope toys for loose fibres that could cause intestinal blockage",
        "Remove stuffing from plush toys if your dog is a destuffer",
        "Verify the toy is appropriately sized — it should not fit entirely in your dog's mouth",
        "Replace silicone and rubber toys when they show bite marks or tearing",
    ],
    "durability": [
        "Assess your dog's chew strength honestly before purchasing",
        "Start with a medium-durability toy and adjust based on how quickly it wears",
        "Inspect toys after every play session for cracks or missing pieces",
        "Power chewers should avoid plush, thin rubber, and rope toys",
        "Replace any toy that can be compressed to fit in your dog's mouth",
        "Keep a rotation of 4–6 toys to reduce wear on any single item",
        "Budget for regular replacement — even 'indestructible' toys eventually wear out",
    ],
    "enrichment_type": [
        "Start with easy puzzle difficulty and increase gradually",
        "Clean food-dispensing toys after every use to prevent mould",
        "Vary enrichment types throughout the week (puzzle, scent, lick, frozen)",
        "Supervise first use of any new enrichment toy",
        "Freeze treats inside toys for longer-lasting engagement",
        "Use your dog's daily food allowance in puzzles to prevent overfeeding",
        "Rotate enrichment activities to prevent boredom with any single type",
    ],
    "age_appropriate": [
        "Match toy hardness to your dog's life stage and dental condition",
        "Puppies need softer toys — hard nylon can damage developing teeth",
        "Senior dogs benefit from gentle-chew toys that do not stress ageing jaws",
        "Supervise adolescent dogs closely — teething increases destructive chewing",
        "Replace puppy toys as your dog grows to prevent choking on undersized items",
        "Introduce puzzle toys early to build problem-solving confidence",
        "Consult your veterinarian if your dog's chewing habits change suddenly",
    ],
}

def build_checklist_html(table_key):
    items = CHECKLIST_LIBRARY.get(table_key, CHECKLIST_LIBRARY["default_play_style"])
    li = "".join(f"<li>{item}</li>" for item in items)
    return (
        '<!-- wp:group {"style":{"color":{"background":"#f5f3ff"},"border":{"radius":"6px","width":"1px","color":"#ddd6fe"},"spacing":{"padding":{"top":"16px","bottom":"16px","left":"20px","right":"20px"},"margin":{"top":"24px","bottom":"24px"}}},"layout":{"type":"constrained"}} -->\n'
        '<div class="wp-block-group has-border-color has-background" style="border-color:#ddd6fe;border-width:1px;border-radius:6px;background-color:#f5f3ff;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<!-- wp:heading {"level":4} --><h4 class="wp-block-heading">Quick Checklist</h4><!-- /wp:heading -->\n'
        f'<!-- wp:list --><ul class="wp-block-list">{li}</ul><!-- /wp:list -->\n'
        '</div><!-- /wp:group -->'
    )


# Next steps by topic
NEXT_STEPS_LIBRARY = {
    "default_play_style": [
        "Observe which play style your dog naturally gravitates towards over the next week",
        "Select two or three toy types that match your dog's preference and chew strength",
        "Set up a toy rotation schedule, swapping available toys every 2–3 days",
        "Book a veterinary dental check if you are unsure about appropriate chew hardness",
    ],
    "material_safety": [
        "Audit your dog's current toy collection and remove anything with visible damage or strong odours",
        "Check remaining toys for safety certifications (non-toxic, BPA-free labels)",
        "Replace any PVC-based toys with natural rubber or TPR alternatives",
        "Establish a weekly toy-cleaning routine using pet-safe soap and warm water",
    ],
    "durability": [
        "Test your dog's chew strength by offering a medium-durability toy and observing for 30 minutes",
        "Remove any toy that shows damage within the first session — your dog needs a tougher option",
        "Create a weekly inspection habit: check every toy for cracks, tears, or missing pieces",
        "Set a monthly budget for toy replacement based on your dog's chew intensity",
    ],
    "enrichment_type": [
        "Try one new enrichment type this week (puzzle feeder, snuffle mat, or frozen treat toy)",
        "Start at the easiest difficulty level and increase only when your dog solves it consistently",
        "Track which enrichment activities your dog engages with longest — double down on those",
        "Schedule enrichment sessions before periods your dog is typically home alone",
        "Gradually replace a portion of bowl feeding with puzzle-based feeding",
    ],
    "age_appropriate": [
        "Assess your dog's current life stage and review whether their toys still match",
        "Replace any toys your puppy has outgrown — undersized toys become choking hazards",
        "For senior dogs, swap hard chews for softer alternatives and consult your vet about dental health",
        "Introduce one age-appropriate new toy this week and observe your dog's response",
    ],
}

def build_next_steps_html(table_key):
    items = NEXT_STEPS_LIBRARY.get(table_key, NEXT_STEPS_LIBRARY["default_play_style"])
    li = "".join(f"<li>{item}</li>" for item in items)
    return (
        '<!-- wp:group {"style":{"color":{"background":"#f0fdfa"},"border":{"radius":"6px","width":"1px","color":"#99f6e4"},"spacing":{"padding":{"top":"16px","bottom":"16px","left":"20px","right":"20px"},"margin":{"top":"24px","bottom":"24px"}}},"layout":{"type":"constrained"}} -->\n'
        '<div class="wp-block-group has-border-color has-background" style="border-color:#99f6e4;border-width:1px;border-radius:6px;background-color:#f0fdfa;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<!-- wp:heading {"level":4} --><h4 class="wp-block-heading">What to Do Next</h4><!-- /wp:heading -->\n'
        f'<!-- wp:list {{"ordered":true}} --><ol class="wp-block-list">{li}</ol><!-- /wp:list -->\n'
        '</div><!-- /wp:group -->'
    )


# ── insertion logic ──────────────────────────────────────────────────────────

def find_insertion_point(content, block_name, anchor_blocks):
    """
    Find where to insert a new block, respecting the ordering:
    ... Quick Checklist ... What to Do Next ... Common Mistakes ... Key Terms ... Key Takeaways ... [trust footer]

    Returns index position in content string, or -1 if can't determine.
    """
    # For each anchor that should come AFTER the block, insert before the first one found
    for anchor in anchor_blocks:
        idx = content.find(anchor)
        if idx != -1:
            # Go back to start of line
            while idx > 0 and content[idx-1] != '\n':
                idx -= 1
            return idx
    # Fallback: insert before the last <!-- /wp: closing, or at end
    return len(content)


def insert_blocks(content, title, table_key):
    """Insert missing blocks into content. Returns (new_content, comp_added, check_added, next_added)."""
    comp_added = False
    check_added = False
    next_added = False

    # Determine what's missing
    need_comp = not has_comparison_table(content)
    need_check = not has_quick_checklist(content)
    need_next = not has_what_to_do_next(content)

    if not need_comp and not need_check and not need_next:
        return content, False, False, False

    # Build blocks
    comp_html = build_comparison_html(table_key) if need_comp else ""
    check_html = build_checklist_html(table_key) if need_check else ""
    next_html = build_next_steps_html(table_key) if need_next else ""

    # Insertion strategy:
    # Desired order: ... [comparison table] ... Quick Checklist ... What to Do Next ... Common Mistakes ... Key Terms ... Key Takeaways ... [footer]

    # Insert What to Do Next first (goes before Common Mistakes / Key Terms / Key Takeaways / footer)
    if need_next:
        anchors_after_next = ["Common Mistakes", "Key Terms", "Key Takeaways", "trust-signals", "wp-block-group has-border-color has-background\" style=\"border-color:#fed7aa"]
        pos = find_insertion_point(content, "What to Do Next", anchors_after_next)
        content = content[:pos] + "\n\n" + next_html + "\n\n" + content[pos:]
        next_added = True

    # Insert Quick Checklist (goes before What to Do Next)
    if need_check:
        anchors_after_check = ["What to Do Next", "Common Mistakes", "Key Terms", "Key Takeaways", "trust-signals"]
        pos = find_insertion_point(content, "Quick Checklist", anchors_after_check)
        content = content[:pos] + "\n\n" + check_html + "\n\n" + content[pos:]
        check_added = True

    # Insert Comparison Table (goes before Quick Checklist)
    if need_comp:
        anchors_after_comp = ["Quick Checklist", "What to Do Next", "Common Mistakes", "Key Terms", "Key Takeaways", "trust-signals"]
        pos = find_insertion_point(content, "comparison table", anchors_after_comp)
        content = content[:pos] + "\n\n" + comp_html + "\n\n" + content[pos:]
        comp_added = True

    return content, comp_added, check_added, next_added


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("Phase 10AV/10AY/10AW — Dog Toys Cluster")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)

    # 1. Discover all dog toy posts
    print("\n[1] Discovering dog toy posts...")
    candidates = fetch_all_dog_toy_posts()
    print(f"    Found {len(candidates)} candidate posts from search")

    # 2. Fetch full content and filter
    dog_toy_posts = []
    print("\n[2] Fetching content & filtering to genuine dog toy posts...")
    for i, p in enumerate(candidates):
        data = api_get(f"posts/{p['id']}?_fields=id,title,content,status")
        if not data or data.get("status") != "publish":
            continue
        title = data["title"]["rendered"] if isinstance(data["title"], dict) else data["title"]
        content = data["content"]["rendered"] if isinstance(data["content"], dict) else data["content"]
        if is_dog_toy_post(title, content):
            dog_toy_posts.append({"id": p["id"], "title": title})
        time.sleep(0.3)

    print(f"    Confirmed {len(dog_toy_posts)} dog toy posts")
    for p in dog_toy_posts:
        print(f"      - [{p['id']}] {p['title']}")

    # 3. Process each post
    print(f"\n[3] Processing {len(dog_toy_posts)} posts...")
    results = []

    for idx, post in enumerate(dog_toy_posts):
        pid = post["id"]
        title = post["title"]
        print(f"\n  [{idx+1}/{len(dog_toy_posts)}] Post {pid}: {title[:60]}...")

        # Fetch raw content
        data = api_get(f"posts/{pid}?context=edit&_fields=id,content")
        if not data:
            print(f"    SKIP — could not fetch raw content")
            results.append({"id": pid, "title": title, "comparison_added": "error",
                           "checklist_added": "error", "next_steps_added": "error",
                           "status": "fetch_error"})
            continue

        raw_content = data["content"]["raw"] if isinstance(data["content"], dict) else data["content"]

        # Pick table type
        table_key = pick_comparison_table(title, raw_content)
        print(f"    Table type: {table_key}")

        # Check existing blocks
        has_comp = has_comparison_table(raw_content)
        has_check = has_quick_checklist(raw_content)
        has_next = has_what_to_do_next(raw_content)
        print(f"    Existing — comparison: {has_comp}, checklist: {has_check}, next_steps: {has_next}")

        if has_comp and has_check and has_next:
            print(f"    SKIP — all blocks already present")
            results.append({"id": pid, "title": title, "comparison_added": "already_present",
                           "checklist_added": "already_present", "next_steps_added": "already_present",
                           "status": "skipped"})
            time.sleep(DELAY)
            continue

        # Insert missing blocks
        new_content, comp_added, check_added, next_added = insert_blocks(
            raw_content, title, table_key
        )

        if not comp_added and not check_added and not next_added:
            print(f"    SKIP — nothing new to add")
            results.append({"id": pid, "title": title, "comparison_added": "already_present",
                           "checklist_added": "already_present", "next_steps_added": "already_present",
                           "status": "skipped"})
            time.sleep(DELAY)
            continue

        # Update post
        resp = api_update(pid, {"content": new_content})
        if resp:
            status = "updated"
            print(f"    UPDATED — comp:{comp_added} check:{check_added} next:{next_added}")
        else:
            status = "update_failed"
            print(f"    FAILED to update")

        results.append({
            "id": pid,
            "title": title,
            "comparison_added": "yes" if comp_added else ("already_present" if has_comp else "no"),
            "checklist_added": "yes" if check_added else ("already_present" if has_check else "no"),
            "next_steps_added": "yes" if next_added else ("already_present" if has_next else "no"),
            "status": status,
        })

        time.sleep(DELAY)

    # 4. Write CSV log
    print(f"\n[4] Writing CSV log to {CSV_PATH}")
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "title", "comparison_added", "checklist_added",
            "next_steps_added", "status"
        ])
        writer.writeheader()
        writer.writerows(results)

    # 5. Summary
    updated = sum(1 for r in results if r["status"] == "updated")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    failed = sum(1 for r in results if "error" in r["status"] or "failed" in r["status"])
    comp_count = sum(1 for r in results if r["comparison_added"] == "yes")
    check_count = sum(1 for r in results if r["checklist_added"] == "yes")
    next_count = sum(1 for r in results if r["next_steps_added"] == "yes")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total dog toy posts processed: {len(results)}")
    print(f"  Updated: {updated}")
    print(f"  Skipped (all blocks present): {skipped}")
    print(f"  Failed: {failed}")
    print(f"  Comparison tables added: {comp_count}")
    print(f"  Quick checklists added: {check_count}")
    print(f"  What to Do Next added: {next_count}")
    print(f"\n  CSV log: {CSV_PATH}")
    print(f"  Completed: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
