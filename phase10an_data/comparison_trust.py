#!/usr/bin/env python3
"""
Phase 10AN: Comparison Saturation + Trust for PetHub Online
Clusters: Cat Toys, Cat Supplies, Dog Grooming, Dog Harnesses, Dog Health, Indoor Cats, Uncategorized
"""

import subprocess, json, time, csv, os, re, tempfile

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
BASE = "https://pethubonline.com/wp-json/wp/v2"
LOG_FILE = "/var/lib/freelancer/projects/40416335/phase10an_data/comparison_trust_log.csv"
DELAY = 2

# ── Cluster definitions ──
CLUSTERS = {
    "Cat Toys": [5033, 5032, 4409, 4408, 4407, 4406, 4307, 4300, 4286, 4188, 4181, 4174],
    "Cat Supplies": [4335, 4321, 4314, 4209, 4202, 696, 7175],
    "Dog Grooming": [5464, 4563, 4251, 4244, 4237, 4230, 4078, 4071, 4064, 4057],
    "Dog Harnesses": [5418, 4414, 4413, 4412, 4411, 4279, 4258, 4139, 4049, 4042, 4034, 4027],
    "Dog Health": [5520, 4568, 4110, 4103, 4096, 4089],
    "Indoor Cats": [5519, 5296, 7342, 7343, 7344, 7345, 7346, 7167],
    "Uncategorized": [6048, 6044, 4786, 4785, 4573, 4570, 4576, 4574, 4571, 4328, 4293, 4223, 4153],
}

# Column headers per cluster
CLUSTER_COLUMNS = {
    "Cat Toys": ("Type", "Best For", "Play Style", "Durability", "Indoor/Outdoor"),
    "Cat Supplies": ("Product Type", "Best For", "Key Feature", "Maintenance", "Value"),
    "Dog Grooming": ("Tool Type", "Best For", "Coat Type", "Frequency", "Skill Level"),
    "Dog Harnesses": ("Style", "Best For", "Pull Control", "Comfort", "Ease of Use"),
    "Dog Health": ("Approach", "Best For", "When to Use", "Effectiveness", "Vet Input Needed"),
    "Indoor Cats": ("Activity", "Best For", "Space Needed", "Engagement Level", "Safety"),
    "Uncategorized": ("Option", "Best For", "Key Benefit", "Difficulty", "Suitability"),
}

# ── Topic-specific comparison table rows ──
# Each post that might need a table gets contextually relevant rows
TABLE_ROWS = {
    # Cat Supplies glossary
    7175: [
        ("Food Bowls", "All cats", "Whisker-friendly design", "Dishwasher safe options", "Budget-friendly"),
        ("Water Fountains", "Cats who avoid still water", "Encourages hydration", "Filter replacement monthly", "Mid-range"),
        ("Litter Trays", "Indoor cats", "Odour control features", "Daily scooping needed", "Varies by type"),
        ("Scratching Posts", "All cats", "Protects furniture", "Replace when worn", "Good long-term value"),
        ("Grooming Brushes", "Medium to long-haired cats", "Reduces shedding", "Clean after each use", "Budget-friendly"),
        ("Cat Carriers", "Vet visits and travel", "Stress-reducing design", "Wipe clean after use", "Worth investing in"),
    ],
    # Dog Grooming - shampoo guide (missing table)
    4071: [
        ("General Purpose", "Healthy coats, routine bathing", "All coat types", "Every 4–8 weeks", "Beginner"),
        ("Sensitive/Hypoallergenic", "Itchy or reactive skin", "Short to medium coats", "As needed", "Beginner"),
        ("De-shedding Formula", "Heavy seasonal shedding", "Double coats", "During moult cycles", "Intermediate"),
        ("Puppy Shampoo", "Dogs under 12 months", "All puppy coats", "Monthly or as needed", "Beginner"),
        ("Medicated Shampoo", "Skin conditions (vet-directed)", "Any coat type", "Per vet schedule", "Vet-guided"),
        ("Dry/Waterless Shampoo", "Between-bath freshening", "All coat types", "Weekly if needed", "Beginner"),
    ],
    # Dog Harnesses - complete guide (missing key takeaways only, but adding table if missing)
    4411: [],  # has table already
    # Indoor Cats - new posts
    7342: [
        ("Wand/Feather Teaser Play", "Active cats of all ages", "Minimal", "Very High", "Low risk with supervision"),
        ("Climbing and Cat Trees", "Agile, curious cats", "Moderate vertical space", "High", "Secure to wall for stability"),
        ("Laser Pointer Chase", "High-energy cats", "Open floor space", "High (short bursts)", "End with tangible reward"),
        ("Puzzle Feeders", "Food-motivated cats", "Minimal", "Moderate to High", "Very safe"),
        ("Solo Ball/Track Toys", "Cats home alone", "Minimal", "Moderate", "Choose size-safe toys"),
        ("Cat Wheel/Treadmill", "Very active breeds", "Moderate floor space", "Very High", "Supervise initial use"),
    ],
    7343: [
        ("Toxic Plant Removal", "Homes with any indoor cat", "Minimal", "High", "Replace with cat-safe plants"),
        ("Window Safety Screens", "Homes above ground floor", "Window areas", "High", "Use purpose-built cat mesh"),
        ("String/Ribbon Storage", "Cats that swallow linear items", "Minimal", "Very High", "Vet emergency if ingested"),
        ("Chemical Storage", "All cat households", "Under-sink areas", "High", "Use child-proof latches"),
        ("Small Object Tidying", "Kittens and playful cats", "All rooms", "Moderate", "Daily habit recommended"),
        ("Electrical Cord Covers", "Kittens and chewers", "Near electronics", "Moderate", "Use cord protectors"),
    ],
    7344: [
        ("Cat Trees and Towers", "All indoor cats", "Moderate floor space", "High", "Secure to wall"),
        ("Wall-Mounted Shelves", "Agile climbers", "Vertical wall space", "High", "Professional fitting advised"),
        ("Window Perches", "Curious, observation-loving cats", "Window sill area", "Moderate", "Check weight capacity"),
        ("Hiding Boxes and Tunnels", "Shy or anxious cats", "Minimal", "Moderate", "Very safe"),
        ("Scratching Stations", "All indoor cats", "Small floor/wall area", "High", "Essential for claw health"),
        ("Puzzle and Foraging Toys", "Food-motivated cats", "Minimal", "Moderate to High", "Supervise initially"),
    ],
    7345: [
        ("Urine Spraying Management", "Cats marking territory", "Minimal", "High with consistency", "Vet check recommended"),
        ("Litter Tray Troubleshooting", "Cats avoiding the tray", "Tray placement areas", "High", "Rule out medical causes"),
        ("Destructive Scratching Redirect", "Furniture-scratching cats", "Near scratch targets", "Moderate", "Very safe approach"),
        ("Overgrooming Intervention", "Stressed or anxious cats", "Minimal", "Moderate", "Vet input essential"),
        ("Night-Time Activity Reduction", "Nocturnal-active cats", "Minimal", "Moderate", "Adjust routine gradually"),
        ("Multi-Cat Conflict Resolution", "Households with 2+ cats", "Multiple resource stations", "High", "Separate then reintroduce"),
    ],
    7346: [
        ("Wet Food (Primary)", "Most indoor cats", "Minimal", "High", "Supports hydration"),
        ("Dry Food (Complementary)", "Grazing supplementation", "Minimal", "Moderate", "Monitor calorie intake"),
        ("Indoor-Formula Kibble", "Less active house cats", "Minimal", "Moderate", "Lower calorie density"),
        ("Weight Management Diet", "Overweight indoor cats", "Minimal", "High with consistency", "Vet assessment first"),
        ("Raw/BFCR Diet", "With veterinary guidance only", "Preparation space", "Variable", "Vet supervision essential"),
        ("Treat and Snack Limits", "All indoor cats", "Minimal", "Moderate", "Keep under 10% of calories"),
    ],
    7167: [
        ("Basic Indoor Cat Terms", "New cat owners", "Minimal", "High", "Start here first"),
        ("Health and Veterinary Terms", "All cat owners", "Minimal", "High", "Essential knowledge"),
        ("Behaviour and Body Language", "Understanding your cat", "Observation space", "Very High", "Builds bond with cat"),
        ("Enrichment Vocabulary", "Improving cat wellbeing", "Minimal", "High", "Apply concepts at home"),
        ("Nutrition and Diet Terms", "Feeding decisions", "Minimal", "Moderate", "Discuss with vet"),
        ("Legal and Compliance Terms", "UK cat owners", "Minimal", "Moderate", "Know your obligations"),
    ],
}


def api_get(endpoint):
    """GET from WP REST API."""
    url = f"{BASE}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    return json.loads(result.stdout)


def api_post(endpoint, data):
    """POST to WP REST API using temp file."""
    url = f"{BASE}/{endpoint}"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        tmp = f.name
    try:
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-d", f"@{tmp}", "-H", "Content-Type: application/json",
             "-X", "POST", url],
            capture_output=True, text=True, timeout=60
        )
        return json.loads(result.stdout)
    finally:
        os.unlink(tmp)


def has_table(content):
    return "<table" in content.lower()


def has_at_a_glance(content):
    return "at a glance" in content.lower()


def has_key_takeaways(content):
    return "key takeaway" in content.lower()


def has_source_ref(content):
    return "why we reference" in content.lower()


def has_editorial_footer(content):
    return "our editorial standards" in content.lower()


def build_comparison_table(post_id, cluster, title):
    """Build a comparison table block for the post."""
    cols = CLUSTER_COLUMNS[cluster]
    rows = TABLE_ROWS.get(post_id, [])

    if not rows:
        # Generate generic educational rows based on cluster and title
        rows = generate_generic_rows(cluster, title)

    header = "".join(f"<th>{c}</th>" for c in cols)
    body_rows = ""
    for row in rows:
        cells = "".join(f"<td>{cell}</td>" for cell in row)
        body_rows += f"<tr>{cells}</tr>\n"

    return f"""<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">Quick Comparison</h3>
<!-- /wp:heading -->
<!-- wp:table {{"className":"is-style-stripes"}} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr>{header}</tr></thead><tbody>
{body_rows}</tbody></table></figure>
<!-- /wp:table -->"""


def generate_generic_rows(cluster, title):
    """Generate educational comparison rows when no specific rows are defined."""
    # This should not be called for posts that already have tables
    # Fallback generic rows per cluster
    generic = {
        "Cat Toys": [
            ("Wand Toys", "Interactive play sessions", "Mimics prey movement", "Moderate", "Indoor"),
            ("Puzzle Feeders", "Mental stimulation", "Problem-solving", "High", "Indoor"),
            ("Ball Toys", "Solo play", "Chase and bat", "High", "Indoor/Outdoor"),
            ("Catnip Toys", "Relaxation and excitement", "Roll and rub", "Moderate", "Indoor"),
            ("Scratching Toys", "Claw maintenance", "Scratch and stretch", "Moderate to High", "Indoor"),
        ],
        "Cat Supplies": [
            ("Feeding Essentials", "Daily nutrition", "Ergonomic design", "Low maintenance", "Good value"),
            ("Litter Supplies", "Hygiene management", "Odour control", "Regular cleaning", "Mid-range"),
            ("Grooming Tools", "Coat maintenance", "Reduces shedding", "Weekly use", "Budget-friendly"),
            ("Carriers", "Vet visits and travel", "Stress reduction", "Occasional cleaning", "Worth investing"),
            ("Bedding", "Rest and comfort", "Washable materials", "Weekly washing", "Mid-range"),
        ],
        "Dog Grooming": [
            ("Slicker Brush", "Removing tangles", "Medium to long coats", "2–3 times weekly", "Beginner"),
            ("Undercoat Rake", "De-shedding", "Double coats", "Weekly during moult", "Intermediate"),
            ("Nail Clippers", "Claw maintenance", "All coat types", "Every 2–4 weeks", "Beginner to Intermediate"),
            ("Ear Cleaner", "Ear hygiene", "Floppy-eared breeds", "Weekly checks", "Beginner"),
            ("Detangling Spray", "Mat prevention", "Long, silky coats", "Before brushing", "Beginner"),
        ],
        "Dog Harnesses": [
            ("Back-Clip", "Calm walkers", "Minimal", "High", "Very Easy"),
            ("Front-Clip", "Moderate pullers", "Good redirect", "Moderate", "Easy"),
            ("Dual-Clip", "Training versatility", "Adjustable", "Good", "Moderate"),
            ("Head Halter", "Strong pullers", "Excellent control", "Takes adjustment", "Moderate"),
            ("Step-In", "Small/anxious dogs", "Minimal", "Good", "Very Easy"),
        ],
        "Dog Health": [
            ("Preventive Vet Checks", "All dogs", "Annually minimum", "High", "Yes – essential"),
            ("Dental Care Routine", "All breeds", "Daily ideal", "High over time", "Vet assessment first"),
            ("Joint Supplements", "Senior or large breeds", "Daily with food", "Moderate to High", "Discuss with vet"),
            ("Parasite Prevention", "All dogs", "Monthly or seasonal", "Very High", "Vet-prescribed"),
            ("Weight Management", "Overweight dogs", "Ongoing", "High with commitment", "Initial vet plan"),
        ],
        "Indoor Cats": [
            ("Interactive Play", "Active cats", "Minimal", "Very High", "Supervise wand toys"),
            ("Climbing Structures", "Agile cats", "Vertical space", "High", "Secure installations"),
            ("Puzzle Feeders", "Food-motivated cats", "Minimal", "Moderate", "Very safe"),
            ("Window Watching", "Curious cats", "Window access", "Low to Moderate", "Use window locks"),
            ("Hiding Spots", "Shy or anxious cats", "Minimal", "Moderate", "Very safe"),
        ],
        "Uncategorized": [
            ("Research First", "All pet decisions", "Informed choices", "Low", "All pet owners"),
            ("Vet Consultation", "Health concerns", "Professional guidance", "Moderate", "Essential first step"),
            ("Gradual Introduction", "New products/routines", "Reduces stress", "Low", "Most situations"),
            ("Quality Over Quantity", "Equipment choices", "Better durability", "Low once purchased", "Budget-conscious owners"),
            ("Regular Review", "Ongoing care", "Keeps things current", "Low", "All pet owners"),
        ],
    }
    return generic.get(cluster, generic["Uncategorized"])


def build_at_a_glance(title, cluster):
    """Build an At a Glance box tailored to the post topic."""
    # Generate contextual bullet points
    topic = title.lower()

    if "glossary" in topic or "terminology" in topic:
        bullets = [
            "This glossary covers essential terms every cat owner should understand",
            "Terms are explained in plain language with UK-specific context where relevant",
            "Bookmark this page as a quick reference when researching cat care topics",
            "Each term includes practical relevance to help you make informed decisions",
        ]
    elif "exercise" in topic:
        bullets = [
            "Indoor cats need 15–30 minutes of active play daily for physical and mental health",
            "Interactive play with wand toys is the most effective form of cat exercise",
            "Vertical climbing opportunities count as valuable exercise for cats",
            "Adjust activity levels based on your cat's age, breed, and health status",
        ]
    elif "safety" in topic or "hazard" in topic:
        bullets = [
            "Common household items like lilies, string, and open windows pose serious risks to cats",
            "Prevention is always more effective and less costly than emergency treatment",
            "Conduct a room-by-room safety audit at least twice a year",
            "Keep your vet's emergency number and the nearest out-of-hours clinic details accessible",
        ]
    elif "cat-friendly home" in topic or "enrichment" in topic:
        bullets = [
            "Environmental enrichment reduces stress-related behaviours in indoor cats",
            "Vertical space is just as important as floor space for feline wellbeing",
            "Every indoor cat needs dedicated scratching surfaces, hiding spots, and window access",
            "Rotate and refresh enrichment items regularly to maintain your cat's interest",
        ]
    elif "behaviour" in topic:
        bullets = [
            "Most indoor cat behaviour issues stem from unmet environmental or social needs",
            "Punishment is ineffective and damages the bond between you and your cat",
            "Medical causes should always be ruled out before addressing behavioural concerns",
            "Patience and consistency are essential when modifying feline behaviour",
        ]
    elif "diet" in topic or "nutrition" in topic or "feeding" in topic:
        bullets = [
            "Indoor cats typically need 15–20% fewer calories than outdoor cats",
            "Protein should remain the primary component of any indoor cat's diet",
            "Wet food supports hydration, which is especially important for cats who drink little water",
            "Regular weight monitoring helps catch gradual changes early",
        ]
    elif "shampoo" in topic:
        bullets = [
            "Human shampoo disrupts a dog's skin pH and should never be used",
            "Most healthy dogs only need bathing every 4–8 weeks with a suitable product",
            "Sensitive and medicated shampoos serve very different purposes – choose based on need",
            "Always rinse thoroughly – leftover product causes irritation and flaking",
        ]
    elif "harness" in topic:
        bullets = [
            "A well-fitted harness distributes pressure safely across the chest, not the neck",
            "Front-clip designs help redirect pulling without causing discomfort",
            "Correct sizing is essential – you should fit two fingers under every strap",
            "Introduce any new harness gradually with positive reinforcement",
        ]
    elif "cat supply" in topic or "cat supplies" in topic:
        bullets = [
            "Understanding what each cat care product does helps you choose wisely",
            "Quality essentials reduce long-term costs and improve your cat's wellbeing",
            "This guide covers the core vocabulary around cat supplies in the UK market",
            "Consult your vet for recommendations specific to your cat's needs",
        ]
    else:
        bullets = [
            "This guide provides practical, evidence-based information for UK pet owners",
            "All recommendations focus on your pet's safety and wellbeing",
            "Consult your vet for advice specific to your individual pet's needs",
            "Bookmark this page for easy reference when making pet care decisions",
        ]

    bullet_html = "\n".join(f"<li>{b}</li>" for b in bullets)

    return f"""<!-- wp:group {{"style":{{"border":{{"width":"1px","color":"#c7d2fe","radius":"8px"}},"color":{{"background":"#eef2ff"}},"spacing":{{"padding":{{"top":"16px","right":"20px","bottom":"16px","left":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}}}} -->
<div class="wp-block-group has-border-color" style="border-color:#c7d2fe;border-width:1px;border-radius:8px;background-color:#eef2ff;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">At a Glance</h4>
<!-- /wp:heading -->
<!-- wp:list -->
<ul class="wp-block-list">
{bullet_html}
</ul>
<!-- /wp:list -->
</div>
<!-- /wp:group -->"""


def build_key_takeaways(title, cluster):
    """Build Key Takeaways box tailored to the post topic."""
    topic = title.lower()

    if "glossary" in topic or "terminology" in topic:
        items = [
            "Knowing the correct terminology helps you communicate effectively with your vet",
            "Many cat care terms have specific UK legal or regulatory meanings",
            "Understanding product descriptions helps you compare options confidently",
        ]
    elif "exercise" in topic:
        items = [
            "Consistent daily play sessions matter more than occasional long ones",
            "Rotate toy types to prevent boredom and maintain engagement",
            "Watch for signs of overexertion, especially in older or overweight cats",
        ]
    elif "safety" in topic or "hazard" in topic:
        items = [
            "Remove or secure toxic plants, chemicals, and small swallowable objects",
            "Fit window restrictors and secure balcony access before allowing unsupervised time",
            "Know the signs of poisoning and have emergency contact numbers readily available",
        ]
    elif "cat-friendly home" in topic or "enrichment" in topic:
        items = [
            "Provide resources in multiple locations to reduce competition in multi-cat homes",
            "Cat trees, shelves, and window perches create essential vertical territory",
            "Change enrichment regularly – novelty drives feline curiosity and exploration",
        ]
    elif "behaviour" in topic:
        items = [
            "Address the root cause of unwanted behaviour rather than just the symptoms",
            "Environmental changes often resolve issues faster than direct behavioural intervention",
            "Seek professional help from a certified animal behaviourist for persistent problems",
        ]
    elif "diet" in topic or "nutrition" in topic or "feeding" in topic:
        items = [
            "Measure portions accurately – even small daily overfeeding accumulates quickly",
            "Transition between foods gradually over 7–10 days to avoid digestive upset",
            "Treats should make up no more than 10% of your cat's daily calorie intake",
        ]
    elif "shampoo" in topic:
        items = [
            "Match the shampoo type to your dog's specific coat and skin needs",
            "Introduce bathing gradually with positive associations for anxious dogs",
            "Consult your vet before using medicated shampoos – incorrect use can worsen conditions",
        ]
    elif "harness" in topic:
        items = [
            "Choose a harness style based on your dog's size, behaviour, and walking habits",
            "Recheck the fit regularly – dogs' bodies change with age, season, and condition",
            "A harness complements training but does not replace it",
        ]
    elif "cat supply" in topic or "cat supplies" in topic:
        items = [
            "Start with the essentials and build your cat care kit over time",
            "Invest more in items your cat uses daily – food bowls, litter trays, and scratchers",
            "Replace worn items promptly to maintain hygiene and safety standards",
        ]
    else:
        items = [
            "Always prioritise your pet's safety and comfort when trying new approaches",
            "Consult your vet for personalised advice tailored to your pet's specific needs",
            "Small, consistent changes are more effective than dramatic overnight adjustments",
        ]

    bullet_html = "\n".join(f"<li>{b}</li>" for b in items)

    return f"""<!-- wp:group {{"style":{{"border":{{"width":"1px","color":"#bbf7d0","radius":"8px"}},"color":{{"background":"#f0fdf4"}},"spacing":{{"padding":{{"top":"16px","right":"20px","bottom":"16px","left":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}}}} -->
<div class="wp-block-group has-border-color" style="border-color:#bbf7d0;border-width:1px;border-radius:8px;background-color:#f0fdf4;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">Key Takeaways</h4>
<!-- /wp:heading -->
<!-- wp:list -->
<ul class="wp-block-list">
{bullet_html}
</ul>
<!-- /wp:list -->
</div>
<!-- /wp:group -->"""


def build_source_ref():
    """Build 'Why We Reference These Sources' block."""
    return """<!-- wp:group {"style":{"border":{"width":"1px","color":"#bae6fd","radius":"8px"},"color":{"background":"#f0f9ff"},"spacing":{"padding":{"top":"16px","right":"20px","bottom":"16px","left":"20px"},"margin":{"top":"24px","bottom":"24px"}}}} -->
<div class="wp-block-group has-border-color" style="border-color:#bae6fd;border-width:1px;border-radius:8px;background-color:#f0f9ff;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {"level":4} -->
<h4 class="wp-block-heading">Why We Reference These Sources</h4>
<!-- /wp:heading -->
<!-- wp:paragraph {"style":{"typography":{"fontSize":"14px"}}} -->
<p class="wp-block-paragraph" style="font-size:14px">We reference veterinary organisations, peer-reviewed research, and established animal welfare bodies to ensure our content is accurate and trustworthy. Our editorial team cross-checks claims against multiple sources and updates articles when new evidence emerges. This approach helps you make informed decisions based on the best available information rather than anecdotal claims or marketing material.</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->"""


def insert_before_editorial_footer(content, blocks_to_insert):
    """Insert new blocks before the 'Our Editorial Standards' footer."""
    # Find the editorial footer - look for the group block containing it
    # The footer starts with a wp:group block that contains "Our Editorial Standards"
    editorial_pattern = r'(<!-- wp:group \{[^}]*\} -->\s*<div[^>]*>[\s\S]*?Our Editorial Standards[\s\S]*?<!-- /wp:group -->)'

    match = re.search(editorial_pattern, content)
    if match:
        insert_point = match.start()
        new_content = content[:insert_point] + blocks_to_insert + "\n\n" + content[insert_point:]
        return new_content

    # Fallback: look for simpler pattern
    idx = content.find("Our Editorial Standards")
    if idx > 0:
        # Walk back to find the start of the containing group block
        # Look for the nearest <!-- wp:group before this
        search_area = content[:idx]
        last_group = search_area.rfind("<!-- wp:group")
        if last_group > 0:
            new_content = content[:last_group] + blocks_to_insert + "\n\n" + content[last_group:]
            return new_content

    # Last fallback: append before end
    return content + "\n\n" + blocks_to_insert


def process_post(post_id, cluster):
    """Process a single post, adding missing elements."""
    print(f"  Fetching post {post_id}...")
    data = api_get(f"posts/{post_id}?context=edit")

    if "id" not in data:
        print(f"    ERROR: Could not fetch post {post_id}: {data}")
        return post_id, "Unknown", cluster, False, False, False, False, "fetch_error"

    title = data.get("title", {}).get("raw", "Unknown")
    content = data.get("content", {}).get("raw", "")

    print(f"    Title: {title[:70]}")

    # Check what's missing
    needs_table = not has_table(content)
    needs_at_a_glance = not has_at_a_glance(content)
    needs_key_takeaways = not has_key_takeaways(content)
    needs_source_ref = not has_source_ref(content)

    if not needs_table and not needs_at_a_glance and not needs_key_takeaways and not needs_source_ref:
        print(f"    All elements present - SKIP")
        return post_id, title, cluster, False, False, False, False, "already_complete"

    missing = []
    if needs_table: missing.append("table")
    if needs_at_a_glance: missing.append("at_a_glance")
    if needs_key_takeaways: missing.append("key_takeaways")
    if needs_source_ref: missing.append("source_ref")
    print(f"    Missing: {', '.join(missing)}")

    # Build all blocks to insert
    blocks = []

    if needs_at_a_glance:
        blocks.append(build_at_a_glance(title, cluster))

    if needs_table:
        blocks.append(build_comparison_table(post_id, cluster, title))

    if needs_key_takeaways:
        blocks.append(build_key_takeaways(title, cluster))

    if needs_source_ref:
        blocks.append(build_source_ref())

    combined_blocks = "\n\n".join(blocks)

    # Insert before editorial footer
    if has_editorial_footer(content):
        new_content = insert_before_editorial_footer(content, combined_blocks)
    else:
        # No footer? Append at end
        new_content = content + "\n\n" + combined_blocks

    # Update the post
    print(f"    Updating post {post_id}...")
    update_data = {"content": new_content}
    result = api_post(f"posts/{post_id}", update_data)

    if "id" in result:
        print(f"    SUCCESS - updated post {post_id}")
        status = "updated"
    else:
        print(f"    ERROR updating: {str(result)[:200]}")
        status = "update_error"

    return post_id, title, cluster, needs_table, needs_at_a_glance, needs_key_takeaways, needs_source_ref, status


def main():
    print("=" * 70)
    print("Phase 10AN: Comparison Saturation + Trust")
    print("=" * 70)

    # Prepare log
    log_rows = []

    # Build flat list of (post_id, cluster) in order
    all_posts = []
    for cluster, ids in CLUSTERS.items():
        for pid in ids:
            all_posts.append((pid, cluster))

    total = len(all_posts)
    updated = 0
    skipped = 0
    errors = 0

    for i, (post_id, cluster) in enumerate(all_posts, 1):
        print(f"\n[{i}/{total}] Post {post_id} ({cluster})")

        try:
            pid, title, clust, tbl, aag, kt, sr, status = process_post(post_id, cluster)
            log_rows.append({
                "id": pid,
                "title": title,
                "cluster": clust,
                "table_added": tbl,
                "at_a_glance_added": aag,
                "key_takeaways_added": kt,
                "source_ref_added": sr,
                "status": status,
            })
            if status == "updated":
                updated += 1
            elif status == "already_complete":
                skipped += 1
            else:
                errors += 1
        except Exception as e:
            print(f"    EXCEPTION: {e}")
            log_rows.append({
                "id": post_id,
                "title": "ERROR",
                "cluster": cluster,
                "table_added": False,
                "at_a_glance_added": False,
                "key_takeaways_added": False,
                "source_ref_added": False,
                "status": f"exception: {str(e)[:100]}",
            })
            errors += 1

        time.sleep(DELAY)

    # Write log
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "title", "cluster", "table_added",
            "at_a_glance_added", "key_takeaways_added",
            "source_ref_added", "status"
        ])
        writer.writeheader()
        writer.writerows(log_rows)

    print("\n" + "=" * 70)
    print(f"COMPLETE: {updated} updated, {skipped} skipped, {errors} errors")
    print(f"Log: {LOG_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
