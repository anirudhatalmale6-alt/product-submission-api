#!/usr/bin/env python3
"""
Comparison Enhancement Engine for PetHub Online
================================================
Pushes 7 CONTESTED clusters above 90 dominance by adding/strengthening
comparison tables in WordPress posts.

Clusters (priority order):
1. Indoor Cats   - comparison 75.0, needs +3.1
2. Dog Supplies  - comparison 60.0, needs +2.2
3. Uncategorized - comparison 62.3, needs +1.9
4. Cat Toys      - comparison 63.4, needs +1.1
5. Pet Care      - comparison 60.0, needs +0.8
6. Cat Supplies  - comparison 63.7, needs +0.7
7. Dog Health    - comparison 80.0, needs +0.5
"""

import json
import subprocess
import sys
import time
import csv
import os
import re
import tempfile
from datetime import datetime

# ─── Configuration ───────────────────────────────────────────────────────────
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_API = "https://pethubonline.com/wp-json/wp/v2"
SLEEP_GET = 2
SLEEP_POST = 3
MAX_RETRIES = 3
BACKOFF_BASE = 5

OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase11_data"
CSV_PATH = os.path.join(OUTPUT_DIR, "comparison_enhancement_log.csv")

# Category IDs from WordPress
CATEGORY_MAP = {
    "Indoor Cats": 1413,
    "Dog Supplies": 1376,
    "Uncategorized": 1,
    "Cat Toys": 1459,
    "Pet Care": 1397,
    "Cat Supplies": 1377,
    "Dog Health": 1450,
}

# BLOCKED clusters - never touch
BLOCKED_CATEGORIES = {
    "Dog Food": 1467,
    "Dog Harnesses": 1422,
}

# Priority order for processing
CLUSTER_PRIORITY = [
    "Indoor Cats",
    "Dog Supplies",
    "Uncategorized",
    "Cat Toys",
    "Pet Care",
    "Cat Supplies",
    "Dog Health",
]

# ─── Cluster-Specific Comparison Templates ───────────────────────────────────
# Each template: (heading_topic, col_a, col_b, rows[])
# rows = [(feature, val_a, val_b), ...]

COMPARISON_TEMPLATES = {
    "Indoor Cats": [
        (
            "Indoor Enrichment vs Outdoor Stimulation for Cats",
            "Indoor Enrichment",
            "Outdoor Stimulation",
            [
                ("Safety level", "High — controlled environment with no predators or traffic", "Variable — exposure to cars, wildlife, and toxins"),
                ("Exercise variety", "Climbing trees, tunnels, interactive feeders", "Free roaming, climbing real trees, hunting"),
                ("Mental stimulation", "Puzzle feeders, rotating toys, window perches", "Natural exploration, scent trails, varied terrain"),
                ("Parasite exposure", "Minimal with regular indoor cleaning", "Higher risk of fleas, ticks, and worms"),
                ("Owner involvement", "Requires scheduled play sessions daily", "Less structured but monitoring still needed"),
                ("Cost", "One-time investment in furniture and toys", "Ongoing costs for flea prevention and vet checks"),
            ],
        ),
        (
            "Wet Food vs Dry Food for Indoor Cats",
            "Wet Food",
            "Dry Food",
            [
                ("Moisture content", "70–80% water, aids hydration", "6–10% water, cats may need separate water source"),
                ("Calorie density", "Lower per volume, helps manage weight", "Higher per volume, easier to overfeed"),
                ("Dental effect", "Minimal abrasion on teeth", "Some kibble shapes help reduce tartar buildup"),
                ("Shelf life after opening", "1–2 days refrigerated", "Several weeks in sealed container"),
                ("Protein concentration", "Typically higher animal protein per serving", "May include more plant-based fillers"),
                ("Cost per serving", "Generally higher per meal", "More economical for multi-cat households"),
            ],
        ),
        (
            "Cat Tree Styles for Indoor Spaces",
            "Floor-to-Ceiling Trees",
            "Compact Cat Trees",
            [
                ("Height range", "Typically 200–280 cm, reaches ceiling", "Usually 60–130 cm, fits under shelves"),
                ("Stability", "Ceiling tension rod adds extra support", "Base-weighted, can wobble for large cats"),
                ("Space required", "60×60 cm floor footprint minimum", "40×40 cm footprint, fits in corners"),
                ("Number of platforms", "4–8 levels with multiple perches", "2–4 levels with 1–2 perches"),
                ("Best for", "Active cats, multi-cat homes", "Kittens, senior cats, small apartments"),
            ],
        ),
        (
            "Interactive Play vs Solo Play for Indoor Cats",
            "Interactive (Owner-Led) Play",
            "Solo (Self-Directed) Play",
            [
                ("Bonding benefit", "Strengthens cat-owner relationship", "Minimal bonding, encourages independence"),
                ("Exercise intensity", "High — owner controls pace and movement", "Moderate — depends on toy design"),
                ("Mental engagement", "Very high — mimics prey behaviour", "Moderate — repetitive patterns possible"),
                ("Time commitment", "15–20 min sessions twice daily recommended", "Cats engage at will throughout the day"),
                ("Recommended toys", "Wand toys, laser pointers (with treat reward), feather teasers", "Ball tracks, battery-powered mice, treat dispensers"),
            ],
        ),
    ],
    "Dog Supplies": [
        (
            "Slow Feeder Types for Dogs",
            "Maze-Style Feeders",
            "Lick Mat Feeders",
            [
                ("Feeding speed reduction", "Slows eating by 5–10× with channelled ridges", "Slows eating by 3–5× through spreading and licking"),
                ("Best food type", "Dry kibble and small treats", "Wet food, yoghurt, peanut butter"),
                ("Cleaning difficulty", "Moderate — grooves need brush cleaning", "Easy — most are dishwasher safe"),
                ("Mental stimulation", "High — dogs must navigate patterns", "Moderate — licking is calming, less problem-solving"),
                ("Durability", "Plastic or stainless, lasts 1–3 years", "Silicone, lasts 6–18 months with chewers"),
                ("Best for", "Fast eaters, food-motivated breeds", "Anxious dogs, post-surgery calming"),
            ],
        ),
        (
            "Elevated Bowls vs Floor Bowls for Dogs",
            "Elevated Bowls",
            "Floor-Level Bowls",
            [
                ("Posture support", "Reduces neck strain for tall and senior dogs", "Natural eating position for most breeds"),
                ("Bloat risk consideration", "Debated — some studies suggest higher risk for deep-chested breeds", "Traditional position, widely studied as safe baseline"),
                ("Mess control", "Raised lip catches spills, less floor splatter", "Water and food can spread on floor easily"),
                ("Accessibility", "Easier for dogs with arthritis or mobility issues", "Requires bending which may strain older dogs"),
                ("Cost range", "£15–£50 for adjustable stands", "£5–£20 for standard bowls"),
            ],
        ),
        (
            "Dog Bowl Materials Compared",
            "Stainless Steel Bowls",
            "Ceramic Bowls",
            [
                ("Durability", "Very high — dent-resistant, lasts years", "Moderate — can chip or crack if dropped"),
                ("Bacterial resistance", "Non-porous surface, easy to sanitise", "Glazed surface resists bacteria when intact"),
                ("Weight and stability", "Lightweight, may slide on smooth floors", "Heavy, stays in place during eating"),
                ("Chemical safety", "No leaching, food-grade steel", "Safe if lead-free glaze; check certifications"),
                ("Dishwasher safe", "Yes — handles high temperatures well", "Usually yes, but check manufacturer guidelines"),
                ("Allergen concern", "Hypoallergenic for most dogs", "Hypoallergenic; good for dogs with plastic sensitivity"),
            ],
        ),
        (
            "Travel Water Solutions for Dogs",
            "Portable Water Bottles",
            "Collapsible Travel Bowls",
            [
                ("Portability", "Compact, clips to leash or bag", "Folds flat, fits in pocket"),
                ("Water control", "Dispensed in measured amounts, less waste", "Dog drinks freely, may waste water"),
                ("Capacity", "Typically 350–550 ml", "Holds 250–500 ml when unfolded"),
                ("Ease of use on walks", "One-handed operation, trough attached", "Requires stopping to pour and hold bowl"),
                ("Cleaning", "Bottle and trough need separate washing", "Simple rinse, most are dishwasher safe"),
            ],
        ),
    ],
    "Cat Toys": [
        (
            "Wand Toys vs Ball Toys vs Puzzle Toys for Cats",
            "Wand Toys",
            "Puzzle Feeders",
            [
                ("Play style", "Mimics prey — flying, darting movements", "Problem-solving — cats work to extract treats"),
                ("Exercise level", "High — jumping, pouncing, running", "Low to moderate — pawing, nudging"),
                ("Mental stimulation", "Moderate — focuses on hunting instinct", "Very high — engages cognitive skills"),
                ("Owner involvement", "Required — owner controls the wand", "Minimal — cat works independently"),
                ("Session duration", "10–15 minutes of active play", "15–30 minutes of focused engagement"),
                ("Safety when unsupervised", "Store away — string and feather hazards", "Generally safe for solo use"),
            ],
        ),
        (
            "Battery-Powered vs Manual Interactive Cat Toys",
            "Battery-Powered Toys",
            "Manual Interactive Toys",
            [
                ("Consistency of movement", "Automated patterns, runs without owner", "Varied, depends on owner creativity"),
                ("Novelty duration", "Cats may lose interest in predictable patterns", "Owner can change movements to maintain interest"),
                ("Cost", "£10–£40 plus battery replacement", "£3–£15, no ongoing costs"),
                ("Noise level", "Motor noise may startle timid cats", "Silent operation"),
                ("Bonding opportunity", "Low — designed for solo play", "High — requires shared play time"),
                ("Best for", "Busy owners, cats home alone during day", "Bonding sessions, high-energy cats"),
            ],
        ),
        (
            "Catnip vs Silvervine as Cat Attractants",
            "Catnip (Nepeta cataria)",
            "Silvervine (Actinidia polygama)",
            [
                ("Response rate in cats", "Approximately 60–70% of cats respond", "Approximately 75–80% of cats respond"),
                ("Active compounds", "Nepetalactone — single active compound", "Multiple actinidine compounds for broader effect"),
                ("Duration of effect", "5–15 minutes per exposure", "5–30 minutes, often longer-lasting"),
                ("Availability", "Widely available in pet stores globally", "Less common, often sourced from Asian suppliers"),
                ("Safety", "Non-toxic, non-addictive at normal exposure", "Non-toxic, non-addictive, safe for regular use"),
                ("Form factors", "Dried leaves, sprays, infused toys", "Sticks, powder, fruit galls, infused toys"),
            ],
        ),
        (
            "Indoor Play Approaches for Cats",
            "Structured Play Sessions",
            "Free-Range Toy Access",
            [
                ("Calorie burn", "Higher — focused activity in 10–15 min bursts", "Lower — sporadic engagement throughout day"),
                ("Behavioural benefits", "Reduces aggression and nighttime hyperactivity", "Provides ongoing comfort and stimulation"),
                ("Toy rotation", "Easier to rotate as toys are stored between sessions", "All toys available may lead to habituation"),
                ("Multi-cat suitability", "Can be tailored to each cat individually", "May cause resource guarding over favourite toys"),
                ("Owner effort", "Requires scheduling dedicated play time", "Minimal — set up toy stations once"),
            ],
        ),
    ],
    "Cat Supplies": [
        (
            "Cat Litter Types Compared",
            "Clumping Clay Litter",
            "Crystal (Silica Gel) Litter",
            [
                ("Absorbency", "Forms solid clumps for easy scooping", "Absorbs moisture, traps odour in crystals"),
                ("Dust level", "Moderate to high — can trigger respiratory sensitivity", "Very low dust, better for sensitive cats"),
                ("Odour control duration", "Good for 1–2 weeks with daily scooping", "Effective for 2–4 weeks before full replacement"),
                ("Weight per bag", "Heavy — 5–10 kg bags common", "Lightweight — 2–4 kg bags cover same period"),
                ("Environmental impact", "Clay mining is resource-intensive, not biodegradable", "Not biodegradable, but lower volume used"),
                ("Cost per month", "£8–£15 for single-cat household", "£12–£20 for single-cat household"),
            ],
        ),
        (
            "Cat Collar Types Compared",
            "Breakaway Safety Collars",
            "GPS Tracking Collars",
            [
                ("Primary purpose", "Identification with safety release mechanism", "Real-time location tracking via app"),
                ("Weight", "Very light — 10–20 grams", "Heavier — 25–40 grams with tracker unit"),
                ("Safety mechanism", "Releases under pressure to prevent choking", "Varies — some have breakaway clips, many do not"),
                ("Battery requirement", "None", "Requires charging every 2–7 days"),
                ("Cost", "£3–£10 per collar", "£30–£100 plus monthly subscription for some"),
                ("Best for", "All cats, especially indoor-outdoor cats", "Cats that roam outdoors, escape-prone cats"),
            ],
        ),
        (
            "Grooming Tool Types for Cats",
            "Slicker Brushes",
            "Deshedding Tools",
            [
                ("Bristle type", "Fine, angled wire pins", "Stainless steel edge that reaches undercoat"),
                ("Best coat type", "Medium to long-haired cats", "Double-coated and heavy-shedding breeds"),
                ("Mat removal", "Good for light tangles and daily grooming", "Not designed for mats — targets loose undercoat"),
                ("Skin sensitivity", "Gentle with light pressure", "Can irritate if overused — limit to weekly sessions"),
                ("Fur reduction", "Removes surface loose fur", "Reduces shedding by up to 90% per manufacturer claims"),
                ("Ease of cleaning", "Push-button retract on some models", "Easy wipe-off edge on most designs"),
            ],
        ),
        (
            "Scratching Post Materials Compared",
            "Sisal Rope Posts",
            "Cardboard Scratchers",
            [
                ("Durability", "High — lasts 1–3 years with regular use", "Low to moderate — needs replacing every 2–6 months"),
                ("Scratching satisfaction", "Strong resistance provides satisfying shredding feel", "Soft shred texture, many cats prefer this feel"),
                ("Mess level", "Minimal — sisal fibres stay mostly intact", "Moderate — cardboard shreds accumulate around base"),
                ("Cost", "£15–£40 for standalone post", "£5–£15, affordable to replace frequently"),
                ("Orientation", "Typically vertical — encourages stretching", "Usually horizontal or angled — suits ground-scratchers"),
                ("Space required", "Freestanding, needs 30×30 cm floor area", "Flat or compact, fits under furniture"),
            ],
        ),
    ],
    "Pet Care": [
        (
            "Multi-Pet Household vs Single-Pet Care Approaches",
            "Multi-Pet Household",
            "Single-Pet Household",
            [
                ("Feeding management", "Separate bowls and feeding stations needed to prevent food theft", "Simple — one bowl, one schedule"),
                ("Veterinary costs", "Higher overall, but some clinics offer multi-pet discounts", "Predictable single-pet budget"),
                ("Socialisation benefits", "Built-in companionship reduces separation anxiety", "Owner is sole companion — more bonding time needed"),
                ("Space requirements", "Multiple beds, litter boxes (N+1 rule for cats), separate zones", "Single set of supplies, simpler layout"),
                ("Behavioural monitoring", "Must watch for resource guarding and hierarchy stress", "Easier to spot changes in single animal's behaviour"),
                ("Time commitment", "More daily time for feeding, grooming, individual play", "Focused attention on one pet's needs"),
            ],
        ),
        (
            "Warm-Weather vs Cold-Weather Pet Care",
            "Summer / Warm Weather",
            "Winter / Cold Weather",
            [
                ("Hydration needs", "Increased — provide multiple water stations, add ice cubes", "Standard — but heated bowls prevent freezing outdoors"),
                ("Exercise timing", "Early morning or evening to avoid heat", "Midday when temperatures are mildest"),
                ("Parasite risk", "Peak season for fleas, ticks, and mosquitoes", "Reduced but not eliminated — indoor fleas persist"),
                ("Paw care", "Hot pavement can burn pads — test with hand first", "Ice, salt, and grit can crack pads — use balm or boots"),
                ("Coat management", "Shedding peaks, regular brushing essential", "Coat thickens, reduce bathing to preserve natural oils"),
                ("Common health risks", "Heatstroke, sunburn (light-coloured pets), dehydration", "Hypothermia, dry skin, antifreeze poisoning risk"),
            ],
        ),
    ],
    "Dog Health": [
        (
            "Preventive Care vs Reactive Treatment for Dogs",
            "Preventive (Proactive) Care",
            "Reactive (Treatment-Based) Care",
            [
                ("Cost over lifetime", "Lower — vaccinations and check-ups cost less than emergency treatment", "Higher — diagnostics, surgery, and medication add up"),
                ("Health outcomes", "Earlier detection of issues, better long-term prognosis", "Conditions may be advanced before treatment begins"),
                ("Visit frequency", "Annual or bi-annual wellness exams", "As-needed when symptoms appear"),
                ("Stress on dog", "Routine visits are calmer, less invasive", "Emergency visits are stressful for dog and owner"),
                ("Examples", "Vaccinations, dental cleanings, parasite prevention, weight monitoring", "Surgery, antibiotics, pain management, specialist referrals"),
            ],
        ),
        (
            "Common Dog Supplement Types Compared",
            "Joint Support Supplements",
            "Digestive Health Supplements",
            [
                ("Key ingredients", "Glucosamine, chondroitin, MSM, omega-3 fatty acids", "Probiotics, prebiotics, pumpkin fibre, digestive enzymes"),
                ("Primary benefit", "Supports cartilage health and reduces joint stiffness", "Balances gut flora, firms stools, reduces gas"),
                ("Best for", "Senior dogs, large breeds, active working dogs", "Dogs on antibiotics, sensitive stomachs, dietary transitions"),
                ("Time to see results", "4–8 weeks of consistent daily use", "1–2 weeks for digestive improvements"),
                ("Form factors", "Chewable tablets, soft chews, liquid", "Powder, capsules, fortified treats"),
                ("Veterinary guidance", "Recommended before starting, especially with existing conditions", "Generally safe but vet consultation advised for chronic issues"),
            ],
        ),
        (
            "Dog Dental Care Methods Compared",
            "Daily Tooth Brushing",
            "Dental Chews and Treats",
            [
                ("Plaque removal effectiveness", "Most effective — mechanical brushing removes plaque from all surfaces", "Moderate — reduces plaque through chewing action on outer teeth"),
                ("Ease of compliance", "Requires training dog to accept brush, daily commitment", "Easy — dogs treat them as rewards"),
                ("Cost", "Low — toothbrush and enzymatic paste last months", "Ongoing — £10–£25 per month depending on dog size"),
                ("Gum health benefit", "Direct — massage action improves gum circulation", "Indirect — some chews have added enzymes"),
                ("Veterinary recommendation", "Gold standard for at-home dental care", "Good supplement to brushing, not a replacement"),
            ],
        ),
    ],
    "Uncategorized": [
        (
            "Enrichment Activity Types for Pets",
            "Food-Based Enrichment",
            "Sensory Enrichment",
            [
                ("Engagement type", "Problem-solving to access treats or meals", "Exploring new textures, sounds, and scents"),
                ("Calorie consideration", "Counts toward daily food intake — adjust meals", "No calorie impact, purely experiential"),
                ("Setup effort", "Low to moderate — fill puzzles, freeze kongs", "Low — rotate scents, add new textures to space"),
                ("Duration of engagement", "10–30 minutes depending on difficulty", "Variable — cats and dogs explore at their own pace"),
                ("Examples", "Puzzle feeders, snuffle mats, frozen treat kongs", "Herb gardens (cat grass), new fabric textures, nature sounds"),
                ("Best for", "Food-motivated pets, weight management", "Anxious pets, indoor animals needing variety"),
            ],
        ),
        (
            "Toy Material Safety for Pets",
            "Natural Materials (Rubber, Cotton, Wool)",
            "Synthetic Materials (Nylon, Polyester, TPR)",
            [
                ("Chew safety", "Generally digestible in small amounts if ingested", "May cause blockages if large pieces are swallowed"),
                ("Durability", "Moderate — natural rubber is resilient, cotton frays", "High — nylon and TPR resist heavy chewing"),
                ("Chemical concerns", "Fewer additives, look for organic certifications", "Check for BPA-free, phthalate-free labelling"),
                ("Environmental impact", "Biodegradable, lower carbon footprint", "Non-biodegradable, but longer-lasting reduces waste"),
                ("Allergen risk", "Low — natural fibres rarely cause reactions", "Low — but dyes and coatings may irritate sensitive pets"),
                ("Cost range", "Mid to high — natural materials cost more to source", "Low to mid — mass production keeps prices down"),
            ],
        ),
        (
            "Active Play vs Calm Play for Pets",
            "Active / Physical Play",
            "Calm / Cognitive Play",
            [
                ("Energy expenditure", "High — running, jumping, tugging", "Low — sniffing, licking, problem-solving"),
                ("Best time of day", "Morning or early evening when energy peaks", "Before bedtime or during rest periods"),
                ("Behavioural benefit", "Burns excess energy, reduces destructive behaviour", "Reduces anxiety, promotes relaxation and focus"),
                ("Suitable for", "Young, high-energy pets", "Senior pets, recovering animals, anxious pets"),
                ("Toy examples", "Fetch balls, flirt poles, tug ropes", "Snuffle mats, lick pads, treat puzzles"),
                ("Session length", "10–20 minutes of high-intensity activity", "15–40 minutes of gentle engagement"),
            ],
        ),
    ],
}


# ─── Helper Functions ────────────────────────────────────────────────────────

def log(msg):
    """Print timestamped log message."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def wp_get(endpoint, retries=MAX_RETRIES):
    """GET request to WordPress API with retry logic for 429 errors."""
    url = f"{WP_API}/{endpoint}"
    for attempt in range(1, retries + 1):
        time.sleep(SLEEP_GET)
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, "-w", "\n%{http_code}", url],
            capture_output=True, text=True, timeout=60
        )
        output = result.stdout.strip()
        lines = output.rsplit("\n", 1)
        if len(lines) == 2:
            body, status_code = lines
        else:
            body = output
            status_code = "000"

        if status_code == "429":
            wait = BACKOFF_BASE * attempt
            log(f"  429 rate-limited on GET {endpoint}, retry {attempt}/{retries} in {wait}s")
            time.sleep(wait)
            continue

        try:
            return json.loads(body)
        except json.JSONDecodeError:
            log(f"  JSON decode error on GET {endpoint} (status {status_code}), retry {attempt}/{retries}")
            if attempt < retries:
                time.sleep(BACKOFF_BASE * attempt)
                continue
            return None

    log(f"  FAILED: GET {endpoint} after {retries} retries")
    return None


def wp_post(post_id, data, retries=MAX_RETRIES):
    """POST update to WordPress API with temp file for payload."""
    url = f"{WP_API}/posts/{post_id}"

    # Write JSON to temp file to handle large payloads
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        json.dump(data, tmp, ensure_ascii=False)
        tmp_path = tmp.name

    try:
        for attempt in range(1, retries + 1):
            time.sleep(SLEEP_POST)
            result = subprocess.run(
                ["curl", "-s", "-X", "POST", "--compressed", "-u", AUTH,
                 "-H", "Content-Type: application/json",
                 "-d", f"@{tmp_path}", "-w", "\n%{http_code}", url],
                capture_output=True, text=True, timeout=120
            )
            output = result.stdout.strip()
            lines = output.rsplit("\n", 1)
            if len(lines) == 2:
                body, status_code = lines
            else:
                body = output
                status_code = "000"

            if status_code == "429":
                wait = BACKOFF_BASE * attempt
                log(f"  429 rate-limited on POST {post_id}, retry {attempt}/{retries} in {wait}s")
                time.sleep(wait)
                continue

            if status_code in ("200", "201"):
                try:
                    return json.loads(body)
                except json.JSONDecodeError:
                    return {"id": post_id, "status": "ok"}
            else:
                log(f"  POST {post_id} returned status {status_code}, retry {attempt}/{retries}")
                if attempt < retries:
                    time.sleep(BACKOFF_BASE * attempt)
                    continue
                return None

        log(f"  FAILED: POST {post_id} after {retries} retries")
        return None
    finally:
        os.unlink(tmp_path)


def fetch_all_posts():
    """Fetch all published posts from WordPress with pagination."""
    all_posts = []
    page = 1
    while True:
        log(f"Fetching posts page {page}...")
        data = wp_get(f"posts?per_page=100&page={page}&context=edit&status=publish")
        if not data or not isinstance(data, list) or len(data) == 0:
            break
        all_posts.extend(data)
        log(f"  Got {len(data)} posts (total: {len(all_posts)})")
        if len(data) < 100:
            break
        page += 1
    return all_posts


def get_post_categories(post):
    """Get category IDs for a post."""
    return post.get("categories", [])


def assign_cluster(post, category_map):
    """Assign a post to one of the CONTESTED clusters based on its categories."""
    post_cats = set(get_post_categories(post))

    # Check against contested clusters in priority order
    for cluster_name in CLUSTER_PRIORITY:
        cat_id = category_map[cluster_name]
        if cat_id in post_cats:
            return cluster_name
    return None


def has_comparison_table(content):
    """Check if post already has a comparison table."""
    if not content:
        return False

    indicators = [
        "wp:table",
        'class="wp-block-table',
        "is-style-stripes",
        "Compared:",
        "comparison-table",
        "<thead>",
    ]

    content_lower = content.lower()
    matches = sum(1 for ind in indicators if ind.lower() in content_lower)

    # Need at least 2 indicators for a real comparison table
    # A simple HTML table in content shouldn't count unless it's styled as comparison
    if "wp:table" in content and "<thead>" in content:
        return True
    if "is-style-stripes" in content.lower():
        return True
    if "compared:" in content_lower and "<table" in content_lower:
        return True

    return matches >= 3


def has_strong_comparison(content):
    """Check if existing comparison table is strong (4+ rows)."""
    if not content:
        return False

    # Count <tr> tags inside tables
    table_pattern = re.compile(r'<table.*?</table>', re.DOTALL | re.IGNORECASE)
    tables = table_pattern.findall(content)

    for table in tables:
        row_count = table.lower().count('<tr>')
        # A strong table has header + 4+ data rows = 5+ <tr> tags
        if row_count >= 5:
            return True
    return False


def build_comparison_block(heading_topic, col_a, col_b, rows):
    """Build a Gutenberg-formatted comparison table block."""
    # Build table rows
    row_html = ""
    for feature, val_a, val_b in rows:
        row_html += f"<tr><td>{feature}</td><td>{val_a}</td><td>{val_b}</td></tr>"

    block = (
        f'\n\n<!-- wp:heading {{"level":2}} -->\n'
        f'<h2 class="wp-block-heading">Compared: {heading_topic}</h2>\n'
        f'<!-- /wp:heading -->\n\n'
        f'<!-- wp:table {{"className":"is-style-stripes"}} -->\n'
        f'<figure class="wp-block-table is-style-stripes"><table>'
        f'<thead><tr><th>Feature</th><th>{col_a}</th><th>{col_b}</th></tr></thead>'
        f'<tbody>{row_html}</tbody>'
        f'</table></figure>\n'
        f'<!-- /wp:table -->'
    )
    return block


def find_insertion_point(content):
    """Find the best insertion point for comparison table.

    Insert BEFORE any 'Research Sources', 'Why We Reference', 'Sources',
    'References' sections. Otherwise, append to end.
    """
    # Patterns that indicate source/reference sections at end
    source_patterns = [
        r'<!-- wp:heading.*?>\s*<h[23][^>]*>\s*(?:Research Sources|Why We Reference|Sources|References|Our Sources)',
        r'<h[23][^>]*>\s*(?:Research Sources|Why We Reference|Sources|References|Our Sources)',
    ]

    earliest_pos = len(content)
    for pattern in source_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match and match.start() < earliest_pos:
            earliest_pos = match.start()

    return earliest_pos


def select_templates_for_post(post, cluster, all_templates):
    """Select which comparison template(s) to use for a given post."""
    content = post.get("content", {}).get("raw", "") or ""
    title = post.get("title", {}).get("raw", "") or ""
    combined = (title + " " + content).lower()

    templates = all_templates.get(cluster, [])
    if not templates:
        return []

    # Score templates by relevance to post content
    scored = []
    for template in templates:
        heading, col_a, col_b, rows = template
        # Check keywords from heading and column names
        keywords = heading.lower().split() + col_a.lower().split() + col_b.lower().split()
        keywords = [k for k in keywords if len(k) > 3 and k not in ("for", "the", "and", "with", "from", "that", "this", "types", "compared")]

        score = sum(1 for kw in keywords if kw in combined)
        scored.append((score, template))

    # Sort by relevance score descending
    scored.sort(key=lambda x: x[0], reverse=True)

    # Return the most relevant template, or the first one if no match
    if scored:
        best_score, best_template = scored[0]
        # If no relevance at all, still use first template for the cluster
        if best_score == 0:
            return [templates[0]]
        return [best_template]
    return []


def select_templates_for_uncategorized(post, all_templates):
    """Special handling for Uncategorized posts - match broader topics."""
    content = post.get("content", {}).get("raw", "") or ""
    title = post.get("title", {}).get("raw", "") or ""
    combined = (title + " " + content).lower()

    # First check if post relates to a specific contested cluster by topic
    topic_signals = {
        "Indoor Cats": ["indoor cat", "apartment cat", "house cat", "indoor feline"],
        "Dog Supplies": ["dog bowl", "dog feeder", "leash", "dog collar", "dog crate", "dog supply"],
        "Cat Toys": ["cat toy", "wand toy", "feather toy", "catnip", "cat play"],
        "Cat Supplies": ["cat litter", "scratching post", "cat collar", "cat brush", "cat supply"],
        "Pet Care": ["pet care", "multi-pet", "seasonal care", "pet health general"],
        "Dog Health": ["dog health", "dog supplement", "dog dental", "dog vitamin"],
    }

    for cluster, signals in topic_signals.items():
        if any(s in combined for s in signals):
            return select_templates_for_post(post, cluster, all_templates)

    # Default: use Uncategorized templates
    return select_templates_for_post(post, "Uncategorized", all_templates)


# ─── Main Engine ─────────────────────────────────────────────────────────────

def main():
    log("=" * 70)
    log("PetHub Online - Comparison Enhancement Engine")
    log("=" * 70)
    log(f"Target: Push 7 CONTESTED clusters above 90 dominance")
    log(f"Strategy: Add/strengthen comparison tables in posts")
    log("")

    # Step 1: Fetch all posts
    log("STEP 1: Fetching all published posts...")
    all_posts = fetch_all_posts()
    log(f"Total posts fetched: {len(all_posts)}")
    log("")

    if not all_posts:
        log("ERROR: No posts fetched. Exiting.")
        sys.exit(1)

    # Step 2: Categorize posts into contested clusters
    log("STEP 2: Assigning posts to CONTESTED clusters...")
    cluster_posts = {name: [] for name in CLUSTER_PRIORITY}
    unassigned = 0
    blocked = 0

    for post in all_posts:
        post_cats = set(get_post_categories(post))

        # Skip blocked categories
        if any(cat_id in post_cats for cat_id in BLOCKED_CATEGORIES.values()):
            blocked += 1
            continue

        cluster = assign_cluster(post, CATEGORY_MAP)
        if cluster:
            cluster_posts[cluster].append(post)
        else:
            unassigned += 1

    for name in CLUSTER_PRIORITY:
        log(f"  {name}: {len(cluster_posts[name])} posts")
    log(f"  Blocked (Dog Food/Harnesses): {blocked}")
    log(f"  Not in contested clusters: {unassigned}")
    log("")

    # Step 3: Process each cluster in priority order
    log("STEP 3: Processing clusters in priority order...")
    log("")

    csv_rows = []
    summary = {name: {"enhanced": 0, "skipped": 0, "failed": 0} for name in CLUSTER_PRIORITY}

    for cluster_name in CLUSTER_PRIORITY:
        posts = cluster_posts[cluster_name]
        log(f"{'─' * 60}")
        log(f"CLUSTER: {cluster_name} ({len(posts)} posts)")
        log(f"{'─' * 60}")

        if not posts:
            log(f"  No posts found for {cluster_name}, skipping.")
            log("")
            continue

        for post in posts:
            post_id = post["id"]
            title_raw = post.get("title", {}).get("raw", "Untitled")
            title = title_raw[:60]
            content_raw = post.get("content", {}).get("raw", "") or ""

            log(f"  Post {post_id}: {title}")

            # Check for existing comparison tables
            existing = has_comparison_table(content_raw)
            strong = has_strong_comparison(content_raw) if existing else False

            if existing and strong:
                log(f"    Already has strong comparison table - SKIP")
                csv_rows.append([post_id, title_raw, cluster_name, "yes", "skipped_strong", "", "skipped"])
                summary[cluster_name]["skipped"] += 1
                continue

            # Select appropriate template
            if cluster_name == "Uncategorized":
                templates = select_templates_for_uncategorized(post, COMPARISON_TEMPLATES)
            else:
                templates = select_templates_for_post(post, cluster_name, COMPARISON_TEMPLATES)

            if not templates:
                log(f"    No suitable template found - SKIP")
                csv_rows.append([post_id, title_raw, cluster_name, str(existing).lower(), "no_template", "", "skipped"])
                summary[cluster_name]["skipped"] += 1
                continue

            # Build comparison block
            heading, col_a, col_b, rows = templates[0]
            comparison_block = build_comparison_block(heading, col_a, col_b, rows)

            # Find insertion point
            insert_pos = find_insertion_point(content_raw)

            # Build new content
            new_content = content_raw[:insert_pos] + comparison_block + "\n\n" + content_raw[insert_pos:]

            action = "added_comparison" if not existing else "strengthened_comparison"

            # Update via API
            log(f"    {'Adding' if not existing else 'Strengthening'} comparison: {heading}")
            result = wp_post(post_id, {"content": new_content})

            if result:
                log(f"    SUCCESS - Updated post {post_id}")
                csv_rows.append([post_id, title_raw, cluster_name, str(existing).lower(), action, heading, "success"])
                summary[cluster_name]["enhanced"] += 1
            else:
                log(f"    FAILED - Could not update post {post_id}")
                csv_rows.append([post_id, title_raw, cluster_name, str(existing).lower(), action, heading, "failed"])
                summary[cluster_name]["failed"] += 1

        log("")

    # Step 4: Write CSV report
    log("STEP 4: Writing CSV report...")
    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["post_id", "title", "cluster", "had_comparison", "action_taken", "table_topic", "status"])
        writer.writerows(csv_rows)
    log(f"  CSV written to: {CSV_PATH}")
    log("")

    # Step 5: Summary
    log("=" * 70)
    log("SUMMARY")
    log("=" * 70)

    total_enhanced = 0
    total_skipped = 0
    total_failed = 0

    for cluster_name in CLUSTER_PRIORITY:
        s = summary[cluster_name]
        log(f"  {cluster_name:20s}  enhanced={s['enhanced']}  skipped={s['skipped']}  failed={s['failed']}")
        total_enhanced += s["enhanced"]
        total_skipped += s["skipped"]
        total_failed += s["failed"]

    log(f"{'─' * 60}")
    log(f"  {'TOTAL':20s}  enhanced={total_enhanced}  skipped={total_skipped}  failed={total_failed}")
    log("")
    log(f"CSV report: {CSV_PATH}")
    log(f"Engine complete at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 70)


if __name__ == "__main__":
    main()
