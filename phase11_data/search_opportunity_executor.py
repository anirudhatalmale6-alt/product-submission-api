#!/usr/bin/env python3
"""
PetHub Online Phase 11M - Search Opportunity Execution Engine
=============================================================
Executes the highest-confidence content opportunities for priority clusters:
  Indoor Cats, Pet Care, Dog Supplies, Cat Toys.

Focus: low competition, high authority fit, AI-answer opportunities, UK-specific gaps.

Creates 12 draft posts (3 per cluster) via WP REST API.
All content is educational, UK-focused, no fake expertise or affiliate links.
"""

import csv
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime

# ─── Configuration ───────────────────────────────────────────────────────────

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_API = "https://pethubonline.com/wp-json/wp/v2"
SLEEP_GET = 2
SLEEP_POST = 3
MAX_RETRIES = 3
BACKOFF_BASE = 5

DATA_DIR = "/var/lib/freelancer/projects/40416335/phase11_data"

CATEGORY_MAP = {
    "Indoor Cats": 1413,
    "Pet Care": 1397,
    "Dog Supplies": 1376,
    "Cat Toys": 1459,
}

# ─── Logging ─────────────────────────────────────────────────────────────────

LOG_LINES = []

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_LINES.append(line)

# ─── WordPress API helpers ───────────────────────────────────────────────────

def wp_get(endpoint, retries=MAX_RETRIES):
    url = f"{WP_API}/{endpoint}"
    for attempt in range(1, retries + 1):
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True, timeout=60
        )
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            log(f"  JSON parse error on GET {endpoint}, attempt {attempt}")
            if attempt < retries:
                time.sleep(BACKOFF_BASE * attempt)
                continue
            return None
        if isinstance(data, dict) and data.get("code") == "rest_post_invalid_page_number":
            return None
        if isinstance(data, dict) and "code" in data:
            log(f"  WP error: {data.get('code')} on GET {endpoint}")
            return None
        return data
    return None


def wp_create_post(payload, retries=MAX_RETRIES):
    """Create a new post via WP REST API using temp file for large payloads."""
    url = f"{WP_API}/posts"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        json.dump(payload, tmp, ensure_ascii=False)
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
                log(f"  429 rate-limited, retry {attempt}/{retries} in {wait}s")
                time.sleep(wait)
                continue
            if status_code in ("200", "201"):
                try:
                    return json.loads(body)
                except json.JSONDecodeError:
                    return {"id": 0, "status": "created"}
            else:
                log(f"  POST status {status_code}, retry {attempt}/{retries}")
                if attempt < retries:
                    time.sleep(BACKOFF_BASE * attempt)
                    continue
                log(f"  FAILED to create post after {retries} retries. Body: {body[:300]}")
                return None
        return None
    finally:
        os.unlink(tmp_path)


# ─── Fetch existing posts ───────────────────────────────────────────────────

def fetch_all_posts():
    """Fetch all published + draft posts from WP REST API."""
    all_posts = []
    for status in ["publish", "draft"]:
        page = 1
        while True:
            log(f"Fetching {status} posts page {page}...")
            data = wp_get(f"posts?per_page=100&page={page}&context=edit&status={status}")
            if not data or not isinstance(data, list) or len(data) == 0:
                break
            all_posts.extend(data)
            log(f"  Got {len(data)} {status} posts (total: {len(all_posts)})")
            if len(data) < 100:
                break
            page += 1
            time.sleep(SLEEP_GET)
    return all_posts


def extract_existing_titles(posts):
    """Extract normalised titles from existing posts for duplication check."""
    titles = set()
    for p in posts:
        title_raw = p.get("title", {})
        if isinstance(title_raw, dict):
            title = title_raw.get("rendered", title_raw.get("raw", ""))
        else:
            title = str(title_raw)
        title = title.replace("&#8211;", "-").replace("&#8217;", "'").replace("&amp;", "&")
        title = re.sub(r'<[^>]+>', '', title)
        titles.add(normalise(title))
    return titles


def normalise(text):
    """Normalise text for fuzzy matching."""
    return re.sub(r'[^a-z0-9 ]', '', text.lower()).strip()


def title_already_exists(new_title, existing_titles):
    """Check if a similar title already exists."""
    norm = normalise(new_title)
    for existing in existing_titles:
        # Check exact match or significant substring overlap
        if norm == existing:
            return True
        words = set(norm.split())
        existing_words = set(existing.split())
        if len(words) > 3 and len(words & existing_words) >= len(words) * 0.7:
            return True
    return False


# ─── Read existing opportunity data ─────────────────────────────────────────

def read_csv_data(filepath):
    """Read CSV file and return list of dicts."""
    rows = []
    if not os.path.exists(filepath):
        log(f"  WARNING: {filepath} not found")
        return rows
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


# ─── Content generation (Gutenberg blocks) ──────────────────────────────────

def wp_paragraph(text):
    return f'<!-- wp:paragraph -->\n<p>{text}</p>\n<!-- /wp:paragraph -->'


def wp_heading(text, level=2):
    return f'<!-- wp:heading {{"level":{level}}} -->\n<h{level} class="wp-block-heading">{text}</h{level}>\n<!-- /wp:heading -->'


def wp_list(items, ordered=False):
    tag = "ol" if ordered else "ul"
    inner = "".join(f"<li>{item}</li>" for item in items)
    return f'<!-- wp:list -->\n<{tag}>{inner}</{tag}>\n<!-- /wp:list -->'


def wp_table(headers, rows):
    """Generate a Gutenberg table block."""
    head_cells = "".join(f"<th>{h}</th>" for h in headers)
    body_rows = ""
    for row in rows:
        cells = "".join(f"<td>{c}</td>" for c in row)
        body_rows += f"<tr>{cells}</tr>"
    return (
        '<!-- wp:table -->\n'
        '<figure class="wp-block-table"><table><thead><tr>'
        f'{head_cells}</tr></thead><tbody>{body_rows}</tbody></table></figure>\n'
        '<!-- /wp:table -->'
    )


def wp_faq_block(qa_pairs):
    """Generate FAQ section with structured Q&A (no schema markup)."""
    blocks = [wp_heading("Frequently Asked Questions")]
    for q, a in qa_pairs:
        blocks.append(wp_heading(q, level=3))
        blocks.append(wp_paragraph(a))
    return "\n\n".join(blocks)


def count_words(html_content):
    """Count words in HTML content."""
    text = re.sub(r'<[^>]+>', ' ', html_content)
    text = re.sub(r'\s+', ' ', text).strip()
    return len(text.split())


# ─── Opportunity content definitions ────────────────────────────────────────

OPPORTUNITIES = {
    "Indoor Cats": [
        {
            "slug": "catio-kits-uk-guide",
            "title": "Catio Kits UK: Complete Guide to Outdoor Cat Enclosures",
            "focus_keyword": "catio kits UK",
            "opportunity_type": "low_competition + AI_answer",
            "sections": [
                {
                    "heading": "What Is a Catio and Why Consider One in the UK?",
                    "content": (
                        "A catio is a secure outdoor enclosure that allows cats to experience fresh air, "
                        "sunlight, and outdoor stimulation without the risks of free roaming. In the UK, where "
                        "busy roads, local wildlife, and unpredictable weather pose genuine concerns, catios offer "
                        "a practical compromise between indoor safety and outdoor enrichment."
                    ),
                    "extra": (
                        "Cats Protection, one of the UK's leading feline welfare charities, acknowledges that "
                        "keeping cats indoors or providing secure outdoor access can reduce risks from road traffic "
                        "and infectious diseases. A catio provides exactly this kind of managed outdoor experience."
                    ),
                },
                {
                    "heading": "Types of Catio Kits Available in the UK",
                    "content": (
                        "UK suppliers offer several catio formats to suit different homes and budgets. "
                        "Understanding the main types helps you choose the right option for your property and cat."
                    ),
                    "list": [
                        "<strong>Window box catios</strong> attach directly to a window frame, ideal for flats and smaller homes with limited garden space",
                        "<strong>Lean-to catios</strong> rest against an exterior wall, providing a larger enclosed area without major construction",
                        "<strong>Freestanding enclosures</strong> can be placed anywhere in the garden and come in various sizes from small runs to walk-in structures",
                        "<strong>Cat-proofing fence toppers</strong> convert an entire garden into a secure space using roller bars or mesh panels",
                    ],
                },
                {
                    "heading": "Key Features to Look For in UK Catio Kits",
                    "content": (
                        "The UK climate means your catio needs to withstand rain, wind, and temperature swings. "
                        "Look for pressure-treated timber or powder-coated galvanised steel frames that resist moisture. "
                        "Mesh panels should be sturdy enough that cats cannot push through, with apertures no wider than 25mm."
                    ),
                    "extra": (
                        "A waterproof roof section or polycarbonate panels provide shelter from rain, while still "
                        "allowing light through. Shelving inside the catio gives cats vertical space to climb and perch. "
                        "Check that any kit you consider includes clear assembly instructions and all required fixings, "
                        "as UK suppliers vary in what is included."
                    ),
                },
                {
                    "heading": "UK Catio Kit Price Ranges",
                    "table": {
                        "headers": ["Catio Type", "Typical UK Price Range", "Best For"],
                        "rows": [
                            ["Window box catio", "£80 – £200", "Flats, limited outdoor space"],
                            ["Lean-to enclosure (small)", "£200 – £500", "Terraced houses, patios"],
                            ["Freestanding run (medium)", "£300 – £800", "Gardens with available space"],
                            ["Walk-in catio (large)", "£600 – £1,500+", "Larger gardens, multiple cats"],
                            ["Fence-topper system (full garden)", "£400 – £1,200", "Entire garden conversion"],
                        ],
                    },
                },
                {
                    "heading": "Planning Permission and UK Regulations",
                    "content": (
                        "Most catio kits fall under permitted development rights in England and Wales, meaning "
                        "planning permission is not usually required provided the structure does not exceed certain "
                        "size limits. However, if you live in a conservation area, a listed building, or a leasehold "
                        "property, additional restrictions may apply."
                    ),
                    "extra": (
                        "It is always worth checking with your local planning authority before installation. "
                        "If you rent your home, your landlord's written permission is typically needed. "
                        "Scottish planning rules differ slightly, so Scottish residents should consult their local council."
                    ),
                },
            ],
            "faq": [
                ("Do I need planning permission for a catio in the UK?",
                 "Most catios fall within permitted development rules and do not require planning permission. "
                 "However, conservation areas, listed buildings, and leasehold properties may have additional restrictions. "
                 "Check with your local planning authority before building."),
                ("How much does a catio cost in the UK?",
                 "UK catio kits range from around £80 for a simple window box to over £1,500 for a large walk-in "
                 "enclosure. Fence-topping systems to secure an entire garden typically cost £400 to £1,200."),
                ("Can a catio withstand UK weather?",
                 "Quality UK catio kits use pressure-treated timber or galvanised steel designed for the British climate. "
                 "Look for weatherproof roofing panels and rust-resistant mesh to ensure longevity through rain and wind."),
                ("Is a catio suitable for a flat or apartment?",
                 "Window box catios are specifically designed for flats and attach to window frames. "
                 "You will need your landlord or management company's permission, and the window must be accessible."),
            ],
        },
        {
            "slug": "diy-catio-building-plans-uk",
            "title": "DIY Catio Plans: How to Build a Cat Enclosure in the UK",
            "focus_keyword": "DIY catio plans UK",
            "opportunity_type": "how_to + AI_answer",
            "sections": [
                {
                    "heading": "Why Build a DIY Catio?",
                    "content": (
                        "Building your own catio can save significantly compared to pre-made kits, and allows "
                        "you to customise the size, shape, and features to match your UK property. A DIY approach "
                        "is particularly useful for awkward spaces, non-standard windows, or when you want to "
                        "integrate the structure with existing fencing or outbuildings."
                    ),
                    "extra": (
                        "Many UK cat owners find that a weekend build using readily available timber and mesh "
                        "from suppliers like B&Q, Wickes, or Screwfix produces a solid catio for a fraction "
                        "of the cost of commercial kits."
                    ),
                },
                {
                    "heading": "Materials You Will Need",
                    "content": (
                        "For a standard lean-to catio of approximately 1.8m x 1.2m x 2m, you will need the "
                        "following materials, all available from UK DIY stores."
                    ),
                    "list": [
                        "Pressure-treated timber battens (38mm x 63mm) for the frame — approximately 20 linear metres",
                        "Galvanised welded mesh (19mm or 25mm aperture) — approximately 8 square metres",
                        "Polycarbonate roofing sheet or corrugated bitumen panel for weather protection",
                        "Galvanised staples, screws, hinges, and a latch for the access door",
                        "Cable ties as temporary mesh fixings during assembly",
                        "Optional: shelving brackets and treated timber shelves for climbing platforms",
                    ],
                },
                {
                    "heading": "Step-by-Step Build Process",
                    "content": (
                        "Start by measuring your available space and sketching a plan. The catio needs to connect "
                        "securely to your home, typically via a window or cat flap. Build the timber frame first, "
                        "ensuring all joints are squared and secured with exterior-grade screws."
                    ),
                    "list": [
                        "Prepare a level base using slabs or treated timber sleepers",
                        "Construct the rectangular frame sections (back wall, two sides, front wall with door opening)",
                        "Join the frame sections together and fix to the house wall using appropriate masonry fixings",
                        "Attach the roofing panel at a slight angle for rainwater runoff (minimum 10-degree pitch)",
                        "Staple galvanised mesh securely to all open frame sections, overlapping edges by at least 50mm",
                        "Install the access door with a secure latch that cats cannot open",
                        "Add internal shelving, ramps, or platforms at varying heights",
                        "Create the cat entry point via an existing window or install a cat flap through the wall",
                    ],
                },
                {
                    "heading": "Weatherproofing for UK Conditions",
                    "content": (
                        "The British climate demands proper weatherproofing. Apply exterior wood preservative or paint "
                        "to all exposed timber, even if it is pressure-treated, for additional longevity. Seal the "
                        "joint where the catio meets the house wall using exterior silicone sealant to prevent "
                        "rainwater ingress."
                    ),
                    "extra": (
                        "Consider adding a sheltered resting area inside the catio with a waterproof cushion or "
                        "raised bed where your cat can retreat during showers. In winter, a self-heating pet pad "
                        "can make the catio usable year-round."
                    ),
                },
                {
                    "heading": "DIY Catio Cost Breakdown (UK Prices)",
                    "table": {
                        "headers": ["Material", "Approximate UK Cost", "Where to Buy"],
                        "rows": [
                            ["Pressure-treated timber (20m)", "£40 – £60", "B&Q, Wickes, Screwfix"],
                            ["Galvanised welded mesh (8 sqm)", "£30 – £50", "Screwfix, eBay, farm suppliers"],
                            ["Roofing panel", "£15 – £35", "B&Q, Wickes"],
                            ["Fixings, hinges, latch", "£15 – £25", "Screwfix, B&Q"],
                            ["Wood preservative", "£10 – £15", "B&Q, Wilko"],
                            ["Total estimate", "£110 – £185", ""],
                        ],
                    },
                },
            ],
            "faq": [
                ("How long does it take to build a DIY catio?",
                 "A basic lean-to catio can typically be built in a weekend by one person with standard DIY skills. "
                 "Larger or more complex designs may take two to three days."),
                ("What tools do I need to build a catio?",
                 "A drill/driver, saw (hand saw or circular saw), staple gun, tape measure, spirit level, "
                 "and tin snips for cutting mesh. All are available from UK tool hire shops if you do not own them."),
                ("Do I need to treat the timber for UK weather?",
                 "Pressure-treated timber is recommended as a baseline, with an additional coat of exterior wood "
                 "preservative applied annually for longevity in the UK climate."),
            ],
        },
        {
            "slug": "indoor-cat-exercise-routines-uk",
            "title": "Indoor Cat Exercise: Daily Routines to Keep UK Cats Active",
            "focus_keyword": "indoor cat exercise",
            "opportunity_type": "AI_answer + UK_gap",
            "sections": [
                {
                    "heading": "Why Indoor Cats Need Structured Exercise",
                    "content": (
                        "Indoor cats in the UK face a higher risk of weight gain and associated health issues because "
                        "they lack the natural exercise that comes from outdoor hunting and territory patrol. The "
                        "Association of Pet Obesity Prevention notes that indoor cats are significantly more likely "
                        "to be overweight compared to those with outdoor access."
                    ),
                    "extra": (
                        "A structured daily exercise routine helps indoor cats maintain a healthy weight, reduces "
                        "stress-related behaviours like over-grooming, and provides the mental stimulation they "
                        "would otherwise get from exploring outdoors."
                    ),
                },
                {
                    "heading": "Morning Exercise Routine (10-15 Minutes)",
                    "content": (
                        "Cats are naturally most active at dawn. A short morning play session aligns with their "
                        "natural rhythm and sets a positive tone for the day."
                    ),
                    "list": [
                        "<strong>Wand toy hunting game (5 mins)</strong> — mimic prey movements along the floor and behind furniture to trigger the stalk-chase-pounce sequence",
                        "<strong>Vertical climbing challenge (3 mins)</strong> — use a feather toy to lure your cat up and down a cat tree or wall shelves",
                        "<strong>Food puzzle breakfast (5 mins)</strong> — serve a portion of breakfast in a slow feeder or puzzle ball to combine eating with physical and mental effort",
                    ],
                },
                {
                    "heading": "Evening Exercise Routine (15-20 Minutes)",
                    "content": (
                        "The second peak activity period for cats is around dusk. This is the ideal time for a "
                        "longer, more vigorous play session before the evening meal."
                    ),
                    "list": [
                        "<strong>Chase and retrieve (5 mins)</strong> — toss small toys or crinkle balls along a hallway for your cat to chase and bring back",
                        "<strong>Laser pointer session (3 mins, always end with a physical toy)</strong> — guide the dot along walls and floors, finishing by landing it on a treat or toy so your cat gets a tangible reward",
                        "<strong>Tunnel and box obstacle course (5 mins)</strong> — set up cat tunnels and cardboard boxes in a circuit and encourage exploration with treats",
                        "<strong>Interactive fishing rod play (5 mins)</strong> — vary the speed and direction to simulate different prey types, allowing your cat to catch the toy regularly to maintain motivation",
                    ],
                },
                {
                    "heading": "Weekly Activity Planner for Indoor Cats",
                    "table": {
                        "headers": ["Day", "Morning Activity", "Evening Activity", "Focus"],
                        "rows": [
                            ["Monday", "Wand toy hunting", "Tunnel obstacle course", "Cardio and exploration"],
                            ["Tuesday", "Puzzle feeder breakfast", "Laser pointer + toy finish", "Mental stimulation"],
                            ["Wednesday", "Vertical climbing", "Chase and retrieve", "Agility and speed"],
                            ["Thursday", "Wand toy hunting", "Interactive fishing rod", "Hunt simulation"],
                            ["Friday", "Food puzzle ball", "Box and tunnel circuit", "Problem-solving"],
                            ["Saturday", "Extended wand session", "New toy introduction", "Novelty and enrichment"],
                            ["Sunday", "Gentle vertical play", "Catnip toy rotation", "Recovery and variety"],
                        ],
                    },
                },
                {
                    "heading": "Adapting Exercise for Different Life Stages",
                    "content": (
                        "Kittens under one year old have enormous energy and benefit from three or four short "
                        "sessions daily rather than two longer ones. Adult cats aged one to seven typically do well "
                        "with the two-session approach described above."
                    ),
                    "extra": (
                        "Senior cats over eight years old may prefer gentler, shorter activities. Focus on "
                        "low-impact play like slow wand movements along the floor rather than high jumping. "
                        "If your cat shows reluctance to exercise, consult your vet to rule out pain or joint issues."
                    ),
                },
            ],
            "faq": [
                ("How much exercise does an indoor cat need each day?",
                 "Most indoor cats benefit from at least 20 to 30 minutes of active play spread across two sessions daily. "
                 "Kittens may need more, while senior cats may be content with shorter, gentler sessions."),
                ("What are signs my indoor cat is not getting enough exercise?",
                 "Common indicators include weight gain, destructive behaviour (scratching furniture, knocking items off surfaces), "
                 "over-grooming, excessive vocalisation, and lethargy. If you notice these, try increasing daily play time."),
                ("Can I leave my indoor cat with automated toys while at work?",
                 "Automated toys like battery-powered mice and ball tracks provide some stimulation, but they do not replace "
                 "interactive play with you. Use them as supplements between your morning and evening sessions."),
                ("Is it safe to use laser pointers with cats?",
                 "Laser pointers are generally safe when used correctly. Never shine the laser directly into your cat's eyes, "
                 "and always end the session by landing the dot on a physical toy or treat so your cat gets a satisfying catch."),
            ],
        },
    ],

    "Pet Care": [
        {
            "slug": "multi-pet-household-management-uk",
            "title": "Multi-Pet Household Management: UK Guide for Harmony",
            "focus_keyword": "multi-pet household UK",
            "opportunity_type": "UK_gap + AI_answer",
            "sections": [
                {
                    "heading": "Challenges of Multi-Pet Households in the UK",
                    "content": (
                        "Around 12 million UK households own at least one pet, and a significant number keep "
                        "multiple animals. Managing several pets under one roof brings unique challenges including "
                        "territorial disputes, feeding logistics, veterinary costs, and ensuring each animal "
                        "receives adequate individual attention."
                    ),
                    "extra": (
                        "Whether you are combining cats and dogs, keeping multiple cats, or managing a mix of "
                        "species, a structured approach to introductions, resources, and routines makes multi-pet "
                        "living considerably smoother."
                    ),
                },
                {
                    "heading": "Introducing New Pets to an Existing Household",
                    "content": (
                        "The introduction period is critical. Rushing introductions is the most common cause of "
                        "long-term conflict between household pets. A gradual, scent-based approach works for "
                        "most species combinations."
                    ),
                    "list": [
                        "<strong>Separate spaces first</strong> — keep new arrivals in a separate room for at least 3 to 7 days with their own food, water, litter, and bedding",
                        "<strong>Scent swapping</strong> — exchange bedding between existing and new pets so they become familiar with each other's scent before meeting",
                        "<strong>Visual introduction</strong> — use a baby gate or glass door for initial visual contact while maintaining a physical barrier",
                        "<strong>Supervised meetings</strong> — allow brief, supervised face-to-face sessions, gradually increasing duration over one to two weeks",
                        "<strong>Separate feeding stations</strong> — maintain individual feeding areas to prevent food guarding, particularly important with dogs and cats together",
                    ],
                },
                {
                    "heading": "Resource Management for Multiple Pets",
                    "content": (
                        "Competition over resources is the primary driver of conflict in multi-pet homes. "
                        "The general rule is to provide one resource per pet plus one extra."
                    ),
                    "table": {
                        "headers": ["Resource", "Cats (Per Cat + 1)", "Dogs", "Notes"],
                        "rows": [
                            ["Food bowls", "One per cat, separated", "One per dog, separated", "Feed in different rooms if guarding occurs"],
                            ["Water stations", "Multiple around the house", "At least two locations", "Cats often prefer water away from food"],
                            ["Litter trays", "One per cat plus one extra", "N/A", "Place in quiet, accessible locations"],
                            ["Sleeping spots", "Multiple elevated and hidden", "Individual beds", "Provide escape routes for all pets"],
                            ["Scratching posts", "One per cat minimum", "N/A", "Vertical and horizontal options"],
                        ],
                    },
                },
                {
                    "heading": "Veterinary and Insurance Considerations in the UK",
                    "content": (
                        "Multi-pet households face higher veterinary costs. UK pet insurance providers typically "
                        "offer multi-pet discounts of 5% to 15% when insuring two or more animals on the same policy. "
                        "Compare policies carefully, as coverage levels and excess amounts vary significantly between providers."
                    ),
                    "extra": (
                        "Budget for annual vaccinations, flea and worm treatments, and dental checks for each pet. "
                        "A rough UK estimate for routine annual veterinary care is £200 to £400 per cat and "
                        "£300 to £600 per dog, depending on size and breed."
                    ),
                },
                {
                    "heading": "Daily Routine Tips for Multi-Pet UK Homes",
                    "content": (
                        "Establishing predictable routines reduces anxiety for all pets. Feed at consistent times, "
                        "schedule individual play or walk sessions, and ensure each animal has quiet retreat space."
                    ),
                    "list": [
                        "Stagger feeding times if pets eat at different speeds or require different diets",
                        "Walk dogs separately initially if introducing a new dog to the household",
                        "Provide vertical territory for cats in shared spaces (cat trees, wall shelves)",
                        "Rotate toys weekly to maintain novelty for all pets",
                        "Schedule one-on-one attention time with each pet daily, even if brief",
                    ],
                },
            ],
            "faq": [
                ("How many pets can you legally keep in a UK home?",
                 "There is no specific UK-wide legal limit on the number of pets in a private home. "
                 "However, local council by-laws, tenancy agreements, and the Animal Welfare Act 2006 "
                 "require that all animals are properly cared for. Keeping more animals than you can "
                 "adequately care for could constitute a welfare offence."),
                ("Do UK pet insurers offer multi-pet discounts?",
                 "Many UK insurers offer multi-pet discounts, typically 5% to 15% when insuring two or "
                 "more pets on the same policy. Providers like ManyPets, Bought By Many, and Direct Line "
                 "are known for multi-pet options, but always compare coverage details, not just price."),
                ("How long does it take to introduce a new cat to existing pets?",
                 "A proper introduction typically takes two to four weeks. Some cats adjust within a week, "
                 "while others may need a month or more. Rushing the process is the most common mistake "
                 "and can lead to lasting conflict."),
            ],
        },
        {
            "slug": "seasonal-pet-care-calendar-uk",
            "title": "Seasonal Pet Care Calendar UK: Monthly Guide for Pet Owners",
            "focus_keyword": "seasonal pet care UK",
            "opportunity_type": "UK_gap + AI_answer",
            "sections": [
                {
                    "heading": "Why Seasonal Pet Care Matters in the UK",
                    "content": (
                        "The UK's four distinct seasons bring different health risks and care requirements for pets. "
                        "From adder bites in spring to antifreeze poisoning in winter, knowing what to watch for "
                        "each month helps you protect your pets proactively rather than reactively."
                    ),
                },
                {
                    "heading": "Spring (March to May): Parasite Season Begins",
                    "content": (
                        "As temperatures rise above 8°C, flea and tick activity increases significantly. "
                        "Spring is the time to ensure parasite prevention is up to date."
                    ),
                    "list": [
                        "<strong>March</strong> — restart or continue flea and tick treatments, check gardens for toxic spring bulbs (daffodils, tulips, crocuses)",
                        "<strong>April</strong> — watch for adder activity as snakes emerge from hibernation, particularly in heathland and woodland areas",
                        "<strong>May</strong> — begin checking pets for ticks after walks, especially in long grass; consider lungworm prevention for dogs",
                    ],
                },
                {
                    "heading": "Summer (June to August): Heat and Outdoor Hazards",
                    "content": (
                        "UK summers are increasingly warm, and pets are vulnerable to heat-related issues. "
                        "Dogs are especially at risk of heatstroke, which can be fatal."
                    ),
                    "list": [
                        "<strong>June</strong> — adjust walk times to early morning and evening to avoid peak heat; never leave dogs in parked cars",
                        "<strong>July</strong> — watch for grass seeds that can embed in paws and ears; keep cats indoors during heatwaves above 30°C",
                        "<strong>August</strong> — blue-green algae in ponds and lakes is at peak risk; avoid letting dogs swim in or drink from stagnant water",
                    ],
                },
                {
                    "heading": "Autumn (September to November): Preparation and Hazards",
                    "content": (
                        "Autumn brings falling temperatures and specific UK hazards including conkers, "
                        "acorns, and firework season."
                    ),
                    "list": [
                        "<strong>September</strong> — harvest mites are active; check between toes and on ears for orange clusters",
                        "<strong>October</strong> — keep dogs away from conkers and acorns which are toxic; check garden sheds and bonfires for hedgehogs before lighting",
                        "<strong>November</strong> — prepare for firework season (5th November and surrounding weeks) with anxiety management, safe spaces, and calming aids",
                    ],
                },
                {
                    "heading": "Winter (December to February): Cold Weather and Toxins",
                    "content": (
                        "Winter in the UK brings antifreeze risks, rock salt on paws, and reduced daylight "
                        "affecting outdoor exercise."
                    ),
                    "list": [
                        "<strong>December</strong> — keep chocolate, mince pies, and Christmas plants (poinsettia, mistletoe, holly) away from pets; antifreeze leaks are a major risk",
                        "<strong>January</strong> — wipe dog paws after walks to remove rock salt and grit; provide warm sleeping areas away from draughts",
                        "<strong>February</strong> — use reflective collars and LED leads for dark evening walks; check outdoor water bowls for freezing",
                    ],
                },
                {
                    "heading": "Year-Round UK Pet Care Checklist",
                    "table": {
                        "headers": ["Task", "Frequency", "Applies To"],
                        "rows": [
                            ["Flea and tick prevention", "Monthly (year-round)", "Cats and dogs"],
                            ["Worming treatment", "Every 3 months (adults)", "Cats and dogs"],
                            ["Annual vaccination booster", "Yearly", "Cats and dogs"],
                            ["Dental check", "Yearly (at annual check-up)", "Cats and dogs"],
                            ["Microchip details update", "As needed (when you move)", "Cats and dogs (legally required for dogs)"],
                            ["Pet insurance review", "Annually at renewal", "All pets"],
                        ],
                    },
                },
            ],
            "faq": [
                ("When should I start flea treatment in the UK?",
                 "Most UK vets recommend year-round flea prevention, as centrally heated homes allow fleas to "
                 "survive through winter. If you use seasonal treatment, restart no later than March when "
                 "temperatures consistently rise above 8°C."),
                ("Are conkers poisonous to dogs?",
                 "Horse chestnuts (conkers) contain aesculin, which is toxic to dogs if ingested. Symptoms include "
                 "vomiting, diarrhoea, and restlessness. Keep dogs away from conkers during autumn walks and "
                 "contact your vet immediately if ingestion is suspected."),
                ("How do I keep my pet safe during UK firework season?",
                 "Create a safe den area away from windows, close curtains, play background music or white noise, "
                 "and consider veterinary-approved calming products. Walk dogs before dark and keep cats indoors "
                 "from late October through to mid-November."),
                ("Is antifreeze dangerous for cats in the UK?",
                 "Antifreeze containing ethylene glycol is extremely toxic to cats and can be fatal even in tiny "
                 "amounts. Cats are attracted to its sweet taste. Clean up any spills immediately, store containers "
                 "securely, and consider using propylene glycol-based alternatives which are less toxic."),
            ],
        },
        {
            "slug": "first-time-pet-owner-guide-uk",
            "title": "First-Time Pet Owner UK: Complete Beginner Guide",
            "focus_keyword": "first-time pet owner UK",
            "opportunity_type": "UK_gap + AI_answer",
            "sections": [
                {
                    "heading": "Before You Get a Pet: Essential UK Considerations",
                    "content": (
                        "Becoming a pet owner in the UK is a significant commitment of time, money, and lifestyle. "
                        "Before bringing an animal home, consider the practical realities including costs, time "
                        "requirements, housing restrictions, and the pet's full lifespan."
                    ),
                    "extra": (
                        "The PDSA estimates that the lifetime cost of a medium-sized dog in the UK is approximately "
                        "£27,000, while a cat costs around £18,000 over its lifetime. These figures include "
                        "food, insurance, veterinary care, and basic equipment."
                    ),
                },
                {
                    "heading": "Choosing the Right Pet for Your UK Lifestyle",
                    "content": (
                        "Your living situation, work schedule, and activity level should guide your choice of pet. "
                        "A high-energy working dog breed is unsuitable for a small flat and a full-time office worker."
                    ),
                    "table": {
                        "headers": ["Lifestyle Factor", "Dog Considerations", "Cat Considerations"],
                        "rows": [
                            ["Small flat or apartment", "Small, low-energy breeds only; needs regular outdoor walks", "Well-suited to indoor living with enrichment"],
                            ["Full-time office work", "Requires dog walker or daycare; separation anxiety risk", "More independent; cope better with owner absence"],
                            ["Active outdoor lifestyle", "Ideal match; many breeds thrive on long walks and hikes", "Less relevant; cats self-exercise or stay indoors"],
                            ["Young children in the home", "Choose breeds known for patience; supervise all interactions", "Older cats often tolerate children better than kittens"],
                            ["Rented property", "Check tenancy agreement; many UK landlords restrict dogs", "Often more accepted by landlords; still check agreement"],
                        ],
                    },
                },
                {
                    "heading": "Essential First-Year Costs in the UK",
                    "content": (
                        "The first year of pet ownership typically costs more than subsequent years due to "
                        "one-off purchases and initial veterinary procedures."
                    ),
                    "table": {
                        "headers": ["Expense", "Dog (First Year)", "Cat (First Year)"],
                        "rows": [
                            ["Adoption or purchase", "£150 – £2,000+", "£50 – £800+"],
                            ["Neutering/spaying", "£150 – £400", "£50 – £150"],
                            ["Vaccinations (primary course)", "£80 – £150", "£50 – £100"],
                            ["Microchipping", "Often included in adoption", "Often included in adoption"],
                            ["Pet insurance (annual)", "£200 – £600", "£100 – £300"],
                            ["Food (annual estimate)", "£300 – £800", "£200 – £500"],
                            ["Equipment (bed, bowls, lead, toys)", "£100 – £300", "£80 – £200"],
                        ],
                    },
                },
                {
                    "heading": "UK Legal Requirements for Pet Owners",
                    "content": (
                        "UK pet ownership comes with specific legal obligations. Understanding these before "
                        "you get a pet helps you start on the right footing."
                    ),
                    "list": [
                        "<strong>Microchipping</strong> — all dogs in the UK must be microchipped and registered by 8 weeks old (law since 2016); cats in England must be microchipped by 20 weeks (from June 2024)",
                        "<strong>Animal Welfare Act 2006</strong> — owners have a legal duty to meet five welfare needs: suitable environment, suitable diet, normal behaviour patterns, housing with or apart from other animals as appropriate, and protection from pain, suffering, injury, and disease",
                        "<strong>Dangerous Dogs Act 1991</strong> — certain breeds are banned in the UK; all dogs must be under control in public",
                        "<strong>Dog fouling</strong> — most UK local authorities issue fixed penalty notices (typically £50 to £100) for not cleaning up after your dog in public spaces",
                    ],
                },
                {
                    "heading": "Finding a Reputable Source in the UK",
                    "content": (
                        "Where you get your pet matters enormously. Avoid online marketplace ads that may conceal "
                        "puppy farms or kitten mills. The UK government introduced Lucy's Law in 2020, banning "
                        "third-party sales of puppies and kittens, meaning you must buy direct from a breeder "
                        "or adopt from a rescue centre."
                    ),
                    "list": [
                        "UK rescue centres: Battersea, RSPCA, Cats Protection, Dogs Trust, local breed-specific rescues",
                        "KC Assured Breeders (Kennel Club registered) for pedigree dogs",
                        "GCCF or TICA registered breeders for pedigree cats",
                        "Always visit the animal in person before committing; see them with their mother",
                        "Ask for veterinary health records and vaccination certificates",
                    ],
                },
            ],
            "faq": [
                ("How much does it cost to own a pet in the UK?",
                 "Annual costs for a dog in the UK typically range from £1,000 to £2,000 including food, "
                 "insurance, and routine veterinary care. Cats are generally less expensive at £600 to £1,200 "
                 "annually. First-year costs are higher due to neutering, vaccinations, and initial equipment purchases."),
                ("Do I need pet insurance in the UK?",
                 "Pet insurance is not legally required in the UK, but it is strongly recommended. A single veterinary "
                 "emergency can cost £1,000 to £5,000 or more. Lifetime policies offer the most comprehensive "
                 "coverage, while accident-only policies are the most affordable option."),
                ("Can I keep a pet in a rented property in the UK?",
                 "The Tenant Fees Act 2019 and subsequent guidance encourage landlords to consider pet requests, but "
                 "they are not obligated to agree. Always get written permission from your landlord before getting a pet. "
                 "Some landlords may require an additional pet deposit or pet damage clause."),
            ],
        },
    ],

    "Dog Supplies": [
        {
            "slug": "dog-coats-jackets-uk-guide",
            "title": "Dog Coats and Jackets UK: Choosing the Right One",
            "focus_keyword": "dog coats UK",
            "opportunity_type": "low_competition + UK_gap",
            "sections": [
                {
                    "heading": "Do Dogs Need Coats in the UK?",
                    "content": (
                        "Not every dog needs a coat, but many breeds benefit from extra protection during UK winters. "
                        "Short-haired breeds, small dogs, elderly dogs, and those with health conditions are most "
                        "vulnerable to cold and wet weather."
                    ),
                    "extra": (
                        "Breeds like Greyhounds, Whippets, Staffies, and Chihuahuas have thin coats and low body fat, "
                        "making them particularly susceptible to the UK's damp, cold conditions from October through March. "
                        "Double-coated breeds like Huskies and Border Collies generally do not need coats and may overheat."
                    ),
                },
                {
                    "heading": "Types of Dog Coats for UK Weather",
                    "content": (
                        "The UK's varied weather means different coats serve different purposes. "
                        "Many UK dog owners keep two or three coats for different conditions."
                    ),
                    "table": {
                        "headers": ["Coat Type", "Best For", "Key Features"],
                        "rows": [
                            ["Waterproof raincoat", "Wet, mild days", "Sealed seams, PU or PVC coating, belly coverage"],
                            ["Fleece-lined waterproof", "Cold, wet UK winters", "Outer waterproof layer + inner fleece for warmth"],
                            ["Quilted or padded jacket", "Very cold, dry days", "Insulated fill, good for sub-zero walks"],
                            ["Lightweight fleece", "Cool autumn evenings", "Breathable, easy to wash, layering base"],
                            ["Reflective high-vis coat", "Dark winter walks", "Reflective strips or panels for visibility"],
                            ["Cooling coat", "Summer heatwaves", "Soak in water to cool through evaporation"],
                        ],
                    },
                },
                {
                    "heading": "How to Measure Your Dog for a Coat",
                    "content": (
                        "Correct sizing is essential for comfort and function. An ill-fitting coat restricts "
                        "movement or fails to provide adequate coverage."
                    ),
                    "list": [
                        "<strong>Back length</strong> — measure from the base of the neck (where the collar sits) to the base of the tail",
                        "<strong>Chest girth</strong> — measure around the widest part of the chest, just behind the front legs",
                        "<strong>Neck circumference</strong> — measure around the base of the neck where the collar sits",
                        "Add 2 to 3 cm to each measurement for comfort, especially for breeds with deep chests",
                        "Check the manufacturer's size chart as sizing varies significantly between UK brands",
                    ],
                },
                {
                    "heading": "Features That Matter in the UK Climate",
                    "content": (
                        "When choosing a dog coat for UK conditions, prioritise waterproofing over insulation. "
                        "The UK rarely gets extreme cold, but rain is near-constant from autumn through spring."
                    ),
                    "list": [
                        "Taped or sealed seams to prevent water seeping through stitching",
                        "Belly panel or bib for protection from puddle splash and underside dampness",
                        "Adjustable straps at neck and chest for a secure, non-restrictive fit",
                        "Reflective elements for visibility during dark winter walks (sunset before 4pm in December)",
                        "Machine-washable fabric for easy cleaning after muddy walks",
                        "Harness-compatible design with a lead hole or slit for easy attachment",
                    ],
                },
                {
                    "heading": "UK Dog Coat Price Guide",
                    "table": {
                        "headers": ["Price Range", "What to Expect", "Typical Brands"],
                        "rows": [
                            ["£5 – £15", "Basic waterproof or fleece, limited durability", "Pets at Home own-brand, Amazon basics"],
                            ["£15 – £35", "Good waterproofing, fleece lining, adjustable fit", "Ancol, Danish Design, Rosewood"],
                            ["£35 – £60", "High-quality materials, sealed seams, reflective", "Ruffwear, Hurtta, Equafleece"],
                            ["£60+", "Performance grade, technical fabrics, multi-season", "Ruffwear, Red Original, Siccaro"],
                        ],
                    },
                },
            ],
            "faq": [
                ("Should my dog wear a coat in the rain UK?",
                 "Dogs with thin, single-layer coats benefit from a waterproof coat in UK rain. Breeds like "
                 "Greyhounds, Whippets, and Staffies lose body heat quickly when wet. Double-coated breeds "
                 "generally manage fine without a raincoat."),
                ("What size dog coat do I need?",
                 "Measure your dog's back length (neck to tail base), chest girth (widest point behind front legs), "
                 "and neck circumference. Add 2 to 3 cm for comfort and check the specific brand's size chart, "
                 "as sizing varies between UK manufacturers."),
                ("Can dogs overheat in coats?",
                 "Active dogs and double-coated breeds can overheat in insulated coats, especially during exercise. "
                 "Remove the coat if your dog is panting excessively, and choose a lightweight waterproof rather "
                 "than an insulated coat for active walks in mild-to-cool weather."),
            ],
        },
        {
            "slug": "dog-travel-accessories-uk",
            "title": "Dog Travel Accessories UK: Essential Gear for UK Trips",
            "focus_keyword": "dog travel accessories UK",
            "opportunity_type": "UK_gap + low_competition",
            "sections": [
                {
                    "heading": "UK Legal Requirements for Travelling with Dogs",
                    "content": (
                        "When travelling with your dog in the UK, legal requirements vary depending on the mode "
                        "of transport. In a car, Rule 57 of the Highway Code states that dogs must be suitably "
                        "restrained so they cannot distract the driver or be injured in an emergency stop."
                    ),
                    "extra": (
                        "While the Highway Code does not specify exactly how to restrain your dog, acceptable "
                        "methods include a secured crate, a car harness attached to the seatbelt, a dog guard "
                        "separating the boot area, or a purpose-built dog car seat for smaller breeds."
                    ),
                },
                {
                    "heading": "Car Travel Accessories for Dogs",
                    "table": {
                        "headers": ["Accessory", "Purpose", "UK Price Range"],
                        "rows": [
                            ["Dog car harness", "Seatbelt restraint for medium to large dogs", "£10 – £40"],
                            ["Dog car seat (small breeds)", "Elevated, secured seat for small dogs", "£15 – £50"],
                            ["Boot liner or mat", "Protects boot carpet from mud, hair, and scratches", "£15 – £45"],
                            ["Dog car crate", "Secure containment in the boot area", "£40 – £200"],
                            ["Dog car ramp", "Helps elderly or large dogs access the boot safely", "£25 – £80"],
                            ["Dog guard or barrier", "Separates boot from passenger area", "£20 – £60"],
                        ],
                    },
                },
                {
                    "heading": "Travel Water and Food Equipment",
                    "content": (
                        "Keeping your dog hydrated during UK road trips is essential, especially during summer "
                        "months when cars heat up quickly. Collapsible bowls and travel water bottles take "
                        "minimal space and are indispensable for longer journeys."
                    ),
                    "list": [
                        "<strong>Collapsible silicone bowl</strong> — folds flat, attaches to a lead or bag with a carabiner",
                        "<strong>Travel water bottle with built-in trough</strong> — allows one-handed water dispensing at motorway service stops",
                        "<strong>Portable food container</strong> — keeps measured portions fresh for multi-day trips",
                        "<strong>No-spill car water bowl</strong> — weighted base prevents spills during transit",
                    ],
                },
                {
                    "heading": "Public Transport with Dogs in the UK",
                    "content": (
                        "UK public transport policies for dogs vary by operator. Understanding the rules before "
                        "you travel avoids refusal of service."
                    ),
                    "list": [
                        "<strong>Trains</strong> — most UK train operators allow dogs free of charge; they must be on a lead or in a carrier; two dogs per passenger is typical maximum",
                        "<strong>Buses</strong> — policies vary by operator; many require dogs to sit on the floor, not on seats; some operators charge a fare",
                        "<strong>London Underground</strong> — dogs are allowed on leads; they must use escalators not lifts (unless the dog is being carried)",
                        "<strong>Ferries</strong> — most UK ferry companies require dogs to stay in the car or in designated pet-friendly areas; advance booking for pet facilities is recommended",
                    ],
                },
                {
                    "heading": "Dog-Friendly UK Holiday Essentials",
                    "content": (
                        "The UK has an expanding network of dog-friendly accommodation, beaches, and attractions. "
                        "Packing a dedicated dog travel kit makes trips smoother for everyone."
                    ),
                    "list": [
                        "Familiar blanket or bed from home to reduce anxiety in new surroundings",
                        "Up-to-date vaccination records and microchip details",
                        "LED collar or light-up lead for dark coastal or countryside walks",
                        "Towel specifically for post-walk drying (microfibre dries quickly and packs small)",
                        "Poo bags and a portable bag dispenser",
                        "A long training lead (5m to 10m) for beaches where dogs must be on leads",
                    ],
                },
            ],
            "faq": [
                ("Do dogs need to wear a seatbelt in the UK?",
                 "The Highway Code (Rule 57) requires dogs to be suitably restrained in vehicles so they cannot "
                 "distract the driver. While it does not mandate a specific restraint type, a crash-tested dog "
                 "harness, secured crate, or dog guard are all accepted methods. Unrestrained dogs can result "
                 "in a careless driving charge."),
                ("Can I take my dog on UK trains for free?",
                 "Most UK train operators allow dogs to travel free of charge, provided they are on a lead or in "
                 "a carrier and do not occupy a seat. Policies vary between operators, so check with your specific "
                 "train company before travelling."),
                ("What do I need to take my dog on a UK ferry?",
                 "Requirements vary by operator, but generally you need up-to-date vaccination records, a secure "
                 "lead, and advance booking for pet-friendly facilities. Dogs typically stay in the vehicle or "
                 "designated pet areas during the crossing."),
            ],
        },
        {
            "slug": "dog-feeding-station-setup-guide",
            "title": "Dog Feeding Station Setup: Complete Guide for UK Owners",
            "focus_keyword": "dog feeding station",
            "opportunity_type": "low_competition + AI_answer",
            "sections": [
                {
                    "heading": "What Is a Dog Feeding Station?",
                    "content": (
                        "A dog feeding station is a designated area with raised or floor-level bowls for food and "
                        "water, often on a stand or built into a piece of furniture. Beyond aesthetics, a properly "
                        "set up feeding station supports better posture during eating, reduces mess, and helps "
                        "establish a consistent feeding routine."
                    ),
                },
                {
                    "heading": "Benefits of Raised Feeding Stations",
                    "content": (
                        "Raised feeding stations bring food and water to a more comfortable height, particularly "
                        "for medium to large dogs. This can reduce neck strain during meals."
                    ),
                    "list": [
                        "Reduces neck and joint strain for taller breeds and elderly dogs with mobility issues",
                        "Promotes a slower, more comfortable eating posture",
                        "Keeps the feeding area tidier as spills are contained on the station surface",
                        "Prevents bowls from sliding across the floor during enthusiastic eating",
                        "Creates a clear, consistent feeding location that supports routine",
                    ],
                    "extra": (
                        "Important note: there has been discussion about whether raised feeding stations increase "
                        "the risk of bloat (gastric dilatation-volvulus or GDV) in deep-chested breeds. "
                        "Research findings are mixed, and no definitive conclusion exists. If you own a breed "
                        "prone to bloat (such as Great Danes, German Shepherds, or Setters), discuss feeding "
                        "station height with your vet."
                    ),
                },
                {
                    "heading": "Types of Dog Feeding Stations Available in the UK",
                    "table": {
                        "headers": ["Type", "Best For", "UK Price Range"],
                        "rows": [
                            ["Simple raised stand (metal or wood)", "Most dogs; basic, functional", "£10 – £30"],
                            ["Adjustable height stand", "Growing puppies; multi-dog homes", "£20 – £50"],
                            ["Built-in furniture station", "Kitchen integration; aesthetics", "£50 – £150"],
                            ["Silicone mat with bowls", "Small dogs; mess containment", "£8 – £20"],
                            ["Wall-mounted fold-down", "Small spaces; caravans", "£25 – £60"],
                            ["Slow feeder station", "Fast eaters; weight management", "£12 – £35"],
                        ],
                    },
                },
                {
                    "heading": "Choosing the Right Height",
                    "content": (
                        "The correct feeding station height allows your dog to eat with their head slightly "
                        "lowered from standing position. As a general guide, the top of the bowl should be "
                        "at your dog's lower chest height."
                    ),
                    "table": {
                        "headers": ["Dog Size", "Approximate Shoulder Height", "Suggested Bowl Height"],
                        "rows": [
                            ["Small (under 10kg)", "20 – 30 cm", "5 – 10 cm (floor level or very low stand)"],
                            ["Medium (10 – 25kg)", "35 – 50 cm", "15 – 25 cm"],
                            ["Large (25 – 40kg)", "50 – 65 cm", "25 – 35 cm"],
                            ["Giant (40kg+)", "65 – 80 cm", "35 – 45 cm"],
                        ],
                    },
                },
                {
                    "heading": "Setting Up Your Feeding Station",
                    "content": (
                        "Location and setup matter as much as the station itself. Choose a quiet area away from "
                        "high foot traffic where your dog can eat without feeling pressured."
                    ),
                    "list": [
                        "Place the station on a non-slip surface or use a mat underneath to catch spills",
                        "Keep food and water bowls separate (some dogs prefer water in a different location)",
                        "Use stainless steel or ceramic bowls rather than plastic, which can harbour bacteria and cause chin acne",
                        "Wash bowls daily with hot water and washing-up liquid",
                        "In multi-dog households, maintain separate feeding stations with visual barriers if needed",
                        "Avoid placing the station near the back door in winter where draughts can make the water cold",
                    ],
                },
            ],
            "faq": [
                ("Should I use a raised feeding station for my dog?",
                 "Raised feeding stations can benefit medium to large dogs and elderly dogs with joint issues by "
                 "reducing neck strain. For small dogs, floor-level bowls are usually fine. Owners of deep-chested "
                 "breeds should consult their vet, as research on raised feeders and bloat risk is inconclusive."),
                ("What height should a dog feeding station be?",
                 "The top of the food bowl should be approximately at your dog's lower chest height. For medium dogs, "
                 "this is typically 15 to 25 cm. For large dogs, 25 to 35 cm. Adjustable stands are useful "
                 "for growing puppies or multi-dog households."),
                ("How often should I clean my dog's feeding station?",
                 "Wash food bowls after every meal and water bowls daily. Wipe down the station surface daily "
                 "and deep clean weekly. Stainless steel and ceramic bowls are easier to sanitise than plastic."),
                ("Can I make a DIY dog feeding station?",
                 "A simple DIY feeding station can be made from a wooden crate or pallet with holes cut for bowls. "
                 "Sand all surfaces smooth to prevent splinters, and use pet-safe wood sealant. UK DIY stores "
                 "sell suitable materials for under £20."),
            ],
        },
    ],

    "Cat Toys": [
        {
            "slug": "diy-cat-toys-household-items",
            "title": "DIY Cat Toys from Household Items: Easy Projects",
            "focus_keyword": "DIY cat toys",
            "opportunity_type": "AI_answer + low_competition",
            "sections": [
                {
                    "heading": "Why Make DIY Cat Toys?",
                    "content": (
                        "Cats are notoriously indifferent to expensive toys while being fascinated by cardboard "
                        "boxes and bottle caps. Making toys from household items is free, eco-friendly, and "
                        "allows you to refresh your cat's toy collection regularly without spending money."
                    ),
                    "extra": (
                        "DIY toys also let you tailor the play experience to your cat's preferences. Some cats "
                        "prefer crinkly textures, others respond to feathery movements, and some are obsessed with "
                        "anything that rolls. Homemade toys let you experiment without waste."
                    ),
                },
                {
                    "heading": "Sock and Fabric Toys",
                    "content": (
                        "Old socks and fabric scraps make excellent cat toys with minimal effort."
                    ),
                    "list": [
                        "<strong>Catnip sock</strong> — fill a clean sock with dried catnip and tie a knot at the open end; this becomes a kick toy your cat can wrestle",
                        "<strong>Fabric strip teaser</strong> — cut old t-shirts into strips and tie them to a stick or wooden spoon for a simple wand toy",
                        "<strong>Braided fleece rope</strong> — braid three strips of old fleece blanket into a rope for batting and carrying",
                        "<strong>Sock fish</strong> — stuff a sock with crinkly paper and fabric scraps, tie off the end, and draw eyes with a non-toxic marker",
                    ],
                },
                {
                    "heading": "Cardboard and Paper Toys",
                    "content": (
                        "Cardboard is perhaps the most versatile free cat toy material available."
                    ),
                    "list": [
                        "<strong>Box maze</strong> — tape multiple cardboard boxes together with holes cut between them for a tunnel-and-room maze",
                        "<strong>Toilet roll treat puzzle</strong> — fold the ends of a toilet paper tube closed with treats inside; your cat must figure out how to extract them",
                        "<strong>Paper bag rustler</strong> — place a few treats inside a paper bag (never plastic) for crinkle-hunting fun",
                        "<strong>Cardboard scratcher</strong> — cut corrugated cardboard into strips, stack them tightly in a box with the corrugated edges facing up for a free scratching pad",
                    ],
                },
                {
                    "heading": "Interactive Puzzle Toys from Kitchen Items",
                    "content": (
                        "Food puzzles slow down eating and provide mental stimulation. Several effective "
                        "puzzles can be made from common kitchen items."
                    ),
                    "list": [
                        "<strong>Muffin tin puzzle</strong> — place treats in muffin tin cups and cover some with tennis balls or scrunched paper for your cat to uncover",
                        "<strong>Egg box forager</strong> — place dry food or treats in the cups of an egg box and partially close the lid",
                        "<strong>Bottle roller</strong> — cut small holes in a clean, dry plastic bottle (remove the cap) and fill with dry food; the cat rolls it to dispense treats",
                        "<strong>Ice cube treat</strong> — freeze treats or small amounts of tuna water in ice cube trays for a summer enrichment activity",
                    ],
                },
                {
                    "heading": "Safety Guidelines for Homemade Cat Toys",
                    "content": (
                        "While DIY cat toys are rewarding to make, safety must come first. Cats can chew, "
                        "swallow, and choke on small parts."
                    ),
                    "list": [
                        "Never use string, yarn, or elastic bands unsupervised — these are common causes of intestinal obstruction in cats",
                        "Avoid small parts that could be swallowed (buttons, beads, googly eyes)",
                        "Never use plastic bags — suffocation risk; use paper bags only",
                        "Check toys regularly for wear and discard when damaged",
                        "Avoid toxic materials including glue with strong fumes, permanent markers on chew toys, or treated wood",
                        "Supervise play with any new homemade toy until you are confident it is safe for your cat",
                    ],
                },
            ],
            "faq": [
                ("Are homemade cat toys safe?",
                 "Homemade cat toys are safe when made with appropriate materials and checked regularly for wear. "
                 "Avoid string, elastic bands, small detachable parts, and plastic bags. Always supervise your cat "
                 "with a new toy until you know they play with it safely."),
                ("What household items can I use as cat toys?",
                 "Socks, cardboard boxes, toilet paper rolls, paper bags, egg boxes, muffin tins, and clean plastic "
                 "bottles all make excellent cat toys. Dried catnip from garden centres adds extra appeal to fabric toys."),
                ("How often should I replace homemade cat toys?",
                 "Check homemade toys before each play session. Replace immediately if they show signs of coming apart, "
                 "have loose threads, or have been chewed to the point where small pieces could break off."),
            ],
        },
        {
            "slug": "cat-puzzle-feeders-uk-guide",
            "title": "Cat Puzzle Feeders UK: Guide to Food Puzzles for Cats",
            "focus_keyword": "cat puzzle feeders UK",
            "opportunity_type": "UK_gap + AI_answer",
            "sections": [
                {
                    "heading": "What Are Cat Puzzle Feeders?",
                    "content": (
                        "Cat puzzle feeders are devices that require your cat to work for their food through "
                        "pawing, pushing, sliding, or manipulating the feeder to release kibble or treats. "
                        "They mimic the mental challenge of hunting and are widely recommended by feline "
                        "behaviourists as an enrichment tool for indoor cats."
                    ),
                    "extra": (
                        "Research published in the Journal of Feline Medicine and Surgery suggests that food "
                        "puzzles can reduce stress, decrease behavioural problems, and help with weight management "
                        "in indoor cats by slowing down eating and providing cognitive stimulation."
                    ),
                },
                {
                    "heading": "Types of Cat Puzzle Feeders",
                    "content": (
                        "Puzzle feeders come in several designs, each offering different difficulty levels "
                        "and types of interaction."
                    ),
                    "table": {
                        "headers": ["Puzzle Type", "How It Works", "Difficulty Level"],
                        "rows": [
                            ["Ball dispenser", "Cat rolls the ball to release food through holes", "Beginner"],
                            ["Stationary board puzzle", "Cat uses paws to extract food from cups, pegs, and tunnels", "Beginner to intermediate"],
                            ["Sliding tile puzzle", "Cat slides panels to reveal hidden food compartments", "Intermediate"],
                            ["Tower or tube puzzle", "Cat reaches into vertical tubes or layers to fish out food", "Intermediate"],
                            ["Multi-stage maze", "Food travels through connected channels requiring multiple interactions", "Advanced"],
                        ],
                    },
                },
                {
                    "heading": "Choosing a Puzzle Feeder for Your Cat",
                    "content": (
                        "Start with the easiest puzzle type and increase difficulty as your cat gains confidence. "
                        "A cat that has never used a puzzle feeder may give up quickly if the challenge is too high."
                    ),
                    "list": [
                        "Begin with a simple ball dispenser or open-top board where food is visible",
                        "Use high-value treats initially to motivate engagement, then transition to regular dry food",
                        "Choose puzzles that match your cat's play style: batters prefer rolling toys, fishers prefer tube-style puzzles",
                        "For multi-cat homes, provide one puzzle per cat to prevent food guarding",
                        "Look for puzzles that are dishwasher-safe or easy to hand wash, as hygiene matters",
                    ],
                },
                {
                    "heading": "UK Cat Puzzle Feeder Price Ranges",
                    "table": {
                        "headers": ["Feeder Type", "UK Price Range", "Example Features"],
                        "rows": [
                            ["Basic treat ball", "£3 – £8", "Single hole, adjustable opening size"],
                            ["Board puzzle (beginner)", "£8 – £15", "Multiple cups and pegs, open design"],
                            ["Multi-function board", "£15 – £25", "Several puzzle types on one board"],
                            ["Maze or tower puzzle", "£20 – £40", "Multiple difficulty levels, transparent walls"],
                            ["Electronic automated puzzle", "£35 – £70", "Timer-activated, programmable difficulty"],
                        ],
                    },
                },
                {
                    "heading": "Introducing Your Cat to Puzzle Feeders",
                    "content": (
                        "Patience is key when introducing puzzle feeders. Many cats need a gradual introduction "
                        "to understand and enjoy the concept."
                    ),
                    "list": [
                        "Start by placing treats on top of and around the puzzle so your cat associates it with food",
                        "For board puzzles, begin with all compartments open and food visible",
                        "Gradually increase difficulty by closing compartments or reducing hole sizes",
                        "Never remove your cat's regular food bowl entirely — offer puzzles alongside normal meals initially",
                        "If your cat shows frustration (walking away, vocalising), reduce the difficulty",
                        "Rotate between two or three different puzzles weekly to maintain novelty",
                    ],
                },
            ],
            "faq": [
                ("Are puzzle feeders good for cats?",
                 "Puzzle feeders are widely recommended by feline behaviourists for indoor cats. They provide mental "
                 "stimulation, slow down eating, help with weight management, and can reduce stress-related "
                 "behaviours. They are particularly beneficial for cats that eat too quickly or seem bored."),
                ("How do I get my cat to use a puzzle feeder?",
                 "Start with the easiest setting and high-value treats. Place food on top of and around the puzzle "
                 "initially. Gradually increase difficulty over days or weeks as your cat gains confidence. "
                 "Never force it — some cats take a few days to engage."),
                ("Can I use wet food in a puzzle feeder?",
                 "Some puzzle feeders are designed for wet food, typically lick mats or shallow board styles. "
                 "Most traditional puzzle feeders work with dry kibble or treats. Check the product description "
                 "before purchasing if you want to use wet food."),
                ("How often should I clean cat puzzle feeders?",
                 "Clean puzzle feeders after every use with hot water and washing-up liquid. Most plastic and "
                 "silicone puzzles are dishwasher-safe. Regular cleaning prevents bacterial growth, especially "
                 "in warmer weather."),
            ],
        },
        {
            "slug": "interactive-cat-toys-solo-play-uk",
            "title": "Interactive Cat Toys for Solo Play UK: Keep Cats Busy",
            "focus_keyword": "interactive cat toys solo play UK",
            "opportunity_type": "UK_gap + AI_answer",
            "sections": [
                {
                    "heading": "Why Cats Need Solo Play Options",
                    "content": (
                        "Most UK cat owners work during the day, leaving their cats alone for eight or more hours. "
                        "Interactive toys that operate without human involvement provide essential stimulation "
                        "during these extended alone periods, reducing boredom-related behaviours like excessive "
                        "meowing, over-eating, and furniture destruction."
                    ),
                },
                {
                    "heading": "Types of Interactive Solo Cat Toys",
                    "content": (
                        "Solo play toys fall into several categories, each targeting different aspects of "
                        "feline behaviour and engagement."
                    ),
                    "table": {
                        "headers": ["Toy Type", "How It Works", "Engagement Duration"],
                        "rows": [
                            ["Ball track circuits", "Balls roll through enclosed or semi-enclosed tracks", "Self-paced, often 15-30 min sessions"],
                            ["Battery-powered moving toys", "Automated mice, bugs, or feathers that move unpredictably", "10-20 min per battery cycle"],
                            ["Motion-activated toys", "Activate when the cat walks past or touches them", "On-demand, throughout the day"],
                            ["Puzzle feeders", "Food dispensed through manipulation", "5-20 min per meal"],
                            ["Catnip-filled kickers", "Weighted toys for bunny-kicking and wrestling", "Self-directed, intermittent"],
                            ["Window-mounted bird feeders", "External bird feeder provides visual stimulation", "Hours of passive entertainment"],
                        ],
                    },
                },
                {
                    "heading": "Setting Up a Solo Play Station",
                    "content": (
                        "Rather than scattering toys randomly, create a dedicated play area that encourages "
                        "exploration and keeps your cat engaged throughout the day."
                    ),
                    "list": [
                        "Place a ball track circuit near a window where natural light attracts attention",
                        "Set up a puzzle feeder with a portion of the day's food allocation for midday foraging",
                        "Mount a bird feeder outside a window your cat frequents for hours of visual enrichment",
                        "Rotate battery-powered toys weekly to maintain novelty — cats lose interest in familiar automated toys quickly",
                        "Include at least one catnip kicker toy for physical solo wrestling",
                        "Position a scratching post or pad near the play area for post-play stretching",
                    ],
                },
                {
                    "heading": "UK Price Guide for Solo Play Toys",
                    "table": {
                        "headers": ["Toy Category", "UK Price Range", "Where to Buy"],
                        "rows": [
                            ["Ball track circuit", "£8 – £25", "Pets at Home, Amazon, Zooplus"],
                            ["Battery-powered mouse/bug", "£5 – £15", "Pets at Home, Amazon"],
                            ["Motion-activated toy", "£12 – £35", "Amazon, specialist pet shops"],
                            ["Puzzle feeder board", "£8 – £25", "Pets at Home, Zooplus"],
                            ["Catnip kicker toy", "£4 – £12", "Pets at Home, independent UK makers on Etsy"],
                            ["Window bird feeder", "£8 – £20", "Amazon, RSPB shop, garden centres"],
                        ],
                    },
                },
                {
                    "heading": "Safety Considerations for Unsupervised Play",
                    "content": (
                        "Since solo play toys are used when you are not present, safety is paramount. "
                        "Not all toys are suitable for unsupervised use."
                    ),
                    "list": [
                        "Never leave wand toys, string, or ribbon toys accessible when you are out — strangulation and ingestion risk",
                        "Check battery compartments are securely sealed on all electronic toys",
                        "Avoid small detachable parts that could be swallowed",
                        "Ensure ball track circuits are stable and cannot tip over",
                        "Remove any toy that shows signs of damage or wear before leaving your cat alone",
                        "If using a window bird feeder, ensure the window is secured and cat-proofed",
                    ],
                },
            ],
            "faq": [
                ("What is the best toy for a cat home alone all day?",
                 "A combination approach works better than any single toy. Set up a ball track circuit, a puzzle "
                 "feeder with a portion of daily food, and a window bird feeder for visual stimulation. Rotate "
                 "battery-powered toys weekly to maintain interest."),
                ("Are battery-powered cat toys safe to leave unsupervised?",
                 "Most battery-powered cat toys are designed for solo use and are generally safe if the battery "
                 "compartment is securely closed. Check toys regularly for damage, and remove any with exposed "
                 "wires or loose parts. Avoid toys with string or ribbon attachments for unsupervised play."),
                ("How do I stop my cat getting bored when I am at work?",
                 "Provide a morning play session before you leave, set up puzzle feeders with a portion of food, "
                 "leave safe solo toys available, and mount a bird feeder outside a window. Rotate toys every few "
                 "days and provide a second interactive play session when you return home."),
            ],
        },
    ],
}


# ─── Main execution ─────────────────────────────────────────────────────────

def build_content(opportunity):
    """Build full Gutenberg content from opportunity definition."""
    blocks = []

    # Intro paragraph (first section's content)
    sections = opportunity["sections"]

    for section in sections:
        blocks.append(wp_heading(section["heading"]))
        if "content" in section:
            blocks.append(wp_paragraph(section["content"]))

        if "extra" in section:
            blocks.append(wp_paragraph(section["extra"]))

        if "list" in section:
            blocks.append(wp_list(section["list"]))

        if "table" in section:
            tbl = section["table"]
            blocks.append(wp_table(tbl["headers"], tbl["rows"]))

    # FAQ block
    if "faq" in opportunity:
        blocks.append(wp_faq_block(opportunity["faq"]))

    return "\n\n".join(blocks)


def main():
    log("=" * 70)
    log("PetHub Online Phase 11M - Search Opportunity Execution Engine")
    log("=" * 70)

    # ── Step 1: Read existing opportunity data ──
    log("\n[Step 1] Reading existing opportunity data...")
    search_opps = read_csv_data(os.path.join(DATA_DIR, "search_opportunities.csv"))
    content_gaps = read_csv_data(os.path.join(DATA_DIR, "content_gap_by_cluster.csv"))
    quick_wins = read_csv_data(os.path.join(DATA_DIR, "quick_wins.csv"))
    log(f"  Search opportunities: {len(search_opps)} rows")
    log(f"  Content gaps: {len(content_gaps)} rows")
    log(f"  Quick wins: {len(quick_wins)} rows")

    # ── Step 2: Fetch existing posts ──
    log("\n[Step 2] Fetching existing posts from WordPress...")
    existing_posts = fetch_all_posts()
    existing_titles = extract_existing_titles(existing_posts)
    log(f"  Total existing posts: {len(existing_posts)}")
    log(f"  Unique normalised titles: {len(existing_titles)}")

    # ── Step 3: Execute opportunities ──
    log("\n[Step 3] Executing content opportunities...")

    execution_log = []
    cluster_stats = {}

    for cluster_name, category_id in CATEGORY_MAP.items():
        log(f"\n--- Cluster: {cluster_name} (category {category_id}) ---")
        opportunities = OPPORTUNITIES.get(cluster_name, [])

        if cluster_name not in cluster_stats:
            cluster_stats[cluster_name] = {
                "drafts_created": 0,
                "total_words": 0,
                "readiness_scores": [],
                "top_opportunity": "",
            }

        for opp in opportunities:
            title = opp["title"]
            slug = opp["slug"]
            focus_kw = opp["focus_keyword"]
            opp_type = opp["opportunity_type"]

            # Check for duplicate
            if title_already_exists(title, existing_titles):
                log(f"  SKIP (already exists): {title}")
                execution_log.append({
                    "post_id": "SKIPPED",
                    "title": title,
                    "cluster": cluster_name,
                    "opportunity_type": opp_type,
                    "status": "skipped_duplicate",
                    "word_count": 0,
                    "has_faq": "no",
                    "has_comparison": "no",
                    "uk_signals": "",
                })
                continue

            # Build content
            content = build_content(opp)
            word_count = count_words(content)
            has_faq = "yes" if "faq" in opp else "no"
            has_comparison = "yes" if any("table" in s for s in opp["sections"]) else "no"

            # Detect UK signals
            uk_signals = []
            if "£" in content:
                uk_signals.append("UK_pricing")
            if "UK" in content:
                uk_signals.append("UK_focus")
            if any(brand in content for brand in ["B&Q", "Wickes", "Screwfix", "Pets at Home", "RSPCA", "Battersea"]):
                uk_signals.append("UK_brands")
            if any(reg in content for reg in ["Highway Code", "Animal Welfare Act", "Lucy's Law", "planning permission"]):
                uk_signals.append("UK_regulations")
            uk_signals_str = ", ".join(uk_signals)

            # Calculate readiness score
            readiness = 50  # base
            if has_faq == "yes":
                readiness += 15
            if has_comparison == "yes":
                readiness += 10
            if word_count >= 800:
                readiness += 10
            if "UK" in title:
                readiness += 5
            if len(uk_signals) >= 3:
                readiness += 10

            log(f"  Creating draft: {title}")
            log(f"    Words: {word_count}, FAQ: {has_faq}, Comparison: {has_comparison}, UK signals: {uk_signals_str}")

            # Create the draft post via WP API
            payload = {
                "title": title,
                "content": content,
                "status": "draft",
                "slug": slug,
                "categories": [category_id],
            }

            result = wp_create_post(payload)

            if result and result.get("id"):
                post_id = result.get("id", "UNKNOWN")
                log(f"    Created draft post ID: {post_id}")
                existing_titles.add(normalise(title))

                execution_log.append({
                    "post_id": str(post_id),
                    "title": title,
                    "cluster": cluster_name,
                    "opportunity_type": opp_type,
                    "status": "draft_created",
                    "word_count": word_count,
                    "has_faq": has_faq,
                    "has_comparison": has_comparison,
                    "uk_signals": uk_signals_str,
                })

                cluster_stats[cluster_name]["drafts_created"] += 1
                cluster_stats[cluster_name]["total_words"] += word_count
                cluster_stats[cluster_name]["readiness_scores"].append(readiness)
                if not cluster_stats[cluster_name]["top_opportunity"]:
                    cluster_stats[cluster_name]["top_opportunity"] = title
            else:
                log(f"    FAILED to create draft for: {title}")
                execution_log.append({
                    "post_id": "FAILED",
                    "title": title,
                    "cluster": cluster_name,
                    "opportunity_type": opp_type,
                    "status": "creation_failed",
                    "word_count": word_count,
                    "has_faq": has_faq,
                    "has_comparison": has_comparison,
                    "uk_signals": uk_signals_str,
                })

    # ── Step 4: Write CSVs ──
    log("\n[Step 4] Writing output CSVs...")

    # execution log CSV
    log_csv = os.path.join(DATA_DIR, "opportunity_execution_log.csv")
    with open(log_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "post_id", "title", "cluster", "opportunity_type", "status",
            "word_count", "has_faq", "has_comparison", "uk_signals"
        ])
        writer.writeheader()
        writer.writerows(execution_log)
    log(f"  Written: {log_csv}")

    # execution summary CSV
    summary_csv = os.path.join(DATA_DIR, "opportunity_execution_summary.csv")
    with open(summary_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "cluster", "drafts_created", "total_words", "avg_readiness_score", "top_opportunity"
        ])
        writer.writeheader()
        for cluster_name in CATEGORY_MAP:
            stats = cluster_stats.get(cluster_name, {})
            scores = stats.get("readiness_scores", [])
            avg_score = round(sum(scores) / len(scores), 1) if scores else 0
            writer.writerow({
                "cluster": cluster_name,
                "drafts_created": stats.get("drafts_created", 0),
                "total_words": stats.get("total_words", 0),
                "avg_readiness_score": avg_score,
                "top_opportunity": stats.get("top_opportunity", ""),
            })
    log(f"  Written: {summary_csv}")

    # ── Step 5: Print summary ──
    log("\n" + "=" * 70)
    log("EXECUTION SUMMARY")
    log("=" * 70)

    total_drafts = 0
    total_words = 0
    for cluster_name in CATEGORY_MAP:
        stats = cluster_stats.get(cluster_name, {})
        dc = stats.get("drafts_created", 0)
        tw = stats.get("total_words", 0)
        scores = stats.get("readiness_scores", [])
        avg = round(sum(scores) / len(scores), 1) if scores else 0
        top = stats.get("top_opportunity", "N/A")
        log(f"  {cluster_name}: {dc} drafts, {tw} words, avg readiness {avg}, top: {top}")
        total_drafts += dc
        total_words += tw

    log(f"\n  TOTAL: {total_drafts} drafts created, {total_words} total words")

    skipped = sum(1 for e in execution_log if e["status"] == "skipped_duplicate")
    failed = sum(1 for e in execution_log if e["status"] == "creation_failed")
    if skipped:
        log(f"  Skipped (duplicates): {skipped}")
    if failed:
        log(f"  Failed: {failed}")

    log("\n  Output files:")
    log(f"    {log_csv}")
    log(f"    {summary_csv}")
    log("\nPhase 11M complete.")


if __name__ == "__main__":
    main()
