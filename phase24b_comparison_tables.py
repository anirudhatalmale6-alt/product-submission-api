#!/usr/bin/env python3
"""
Phase 24B - Insert Comparison Tables into PetHub Online Posts
Identifies product comparison / "Best" / "Top" / "vs" / "Compared" posts
that lack HTML tables, generates a relevant comparison table, and inserts it
after the first or second paragraph.
"""

import requests
import json
import time
import re
import os
import html
from datetime import datetime
from requests.auth import HTTPBasicAuth

# ── Config ──────────────────────────────────────────────────────────────
WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = HTTPBasicAuth("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
HEADERS = {
    "Accept-Encoding": "gzip, deflate",
    "Content-Type": "application/json",
}
RESULTS_PATH = "/var/lib/freelancer/projects/40416335/phase24b_comparison_results.json"
DELAY = 2        # seconds between API calls
RETRY_WAIT = 10  # seconds on 429

# ── Helpers ─────────────────────────────────────────────────────────────

def fetch_all_posts():
    """Fetch ALL published posts with pagination."""
    all_posts = []
    page = 1
    while True:
        url = f"{WP_BASE}/posts"
        params = {
            "per_page": 100,
            "page": page,
            "status": "publish",
            "_fields": "id,title,content",
            "context": "edit",
        }
        print(f"  Fetching page {page}...")
        resp = api_get(url, params)
        if resp is None:
            break
        posts = resp.json()
        if not posts:
            break
        all_posts.extend(posts)
        total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
        print(f"    Got {len(posts)} posts (total pages: {total_pages})")
        if page >= total_pages:
            break
        page += 1
        time.sleep(DELAY)
    return all_posts


def api_get(url, params):
    """GET with retry on 429."""
    for attempt in range(5):
        try:
            r = requests.get(url, params=params, auth=AUTH, headers=HEADERS, timeout=30)
            if r.status_code == 429:
                print(f"    429 rate-limited, waiting {RETRY_WAIT}s...")
                time.sleep(RETRY_WAIT)
                continue
            r.raise_for_status()
            return r
        except requests.exceptions.RequestException as e:
            print(f"    Request error (attempt {attempt+1}): {e}")
            time.sleep(RETRY_WAIT)
    return None


def api_put(url, data):
    """PUT (update) with retry on 429."""
    for attempt in range(5):
        try:
            r = requests.post(url, json=data, auth=AUTH, headers=HEADERS, timeout=30)
            if r.status_code == 429:
                print(f"    429 rate-limited, waiting {RETRY_WAIT}s...")
                time.sleep(RETRY_WAIT)
                continue
            r.raise_for_status()
            return r
        except requests.exceptions.RequestException as e:
            print(f"    Update error (attempt {attempt+1}): {e}")
            time.sleep(RETRY_WAIT)
    return None


def has_table(content):
    """Check if content already contains a table."""
    if not content:
        return False
    content_lower = content.lower()
    # Check for HTML table tags or Gutenberg table blocks
    if "<table" in content_lower:
        return True
    if "wp:table" in content_lower:
        return True
    if "wp-block-table" in content_lower:
        return True
    return False


def is_comparison_post(title):
    """Check if title indicates a comparison/product post."""
    if not title:
        return False
    clean = html.unescape(re.sub(r'<[^>]+>', '', title)).strip()
    title_lower = clean.lower()

    # Word-boundary checks for "best", "top", "vs", "compared"
    patterns = [
        r'\bbest\b',
        r'\btop\b',
        r'\bvs\.?\b',
        r'\bversus\b',
        r'\bcompared?\b',
        r'\bcomparison\b',
    ]
    for pat in patterns:
        if re.search(pat, title_lower):
            return True
    return False


def clean_title(title):
    """Strip HTML and decode entities from title."""
    return html.unescape(re.sub(r'<[^>]+>', '', title)).strip()


# ── Pet Type & Topic Detection ──────────────────────────────────────────

PET_KEYWORDS = {
    "dog": ["dog", "puppy", "canine", "pup", "doggy", "dogs", "puppies"],
    "cat": ["cat", "kitten", "feline", "kitty", "cats", "kittens"],
    "bird": ["bird", "parrot", "parakeet", "cockatiel", "avian", "birds"],
    "fish": ["fish", "aquarium", "tank", "goldfish", "betta"],
    "rabbit": ["rabbit", "bunny", "hare", "rabbits", "bunnies"],
    "hamster": ["hamster", "gerbil", "guinea pig", "hamsters"],
    "reptile": ["reptile", "snake", "lizard", "gecko", "turtle", "tortoise", "reptiles"],
    "horse": ["horse", "pony", "equine", "foal", "horses"],
}

TOPIC_CATEGORIES = {
    "food": ["food", "foods", "feed", "diet", "nutrition", "kibble", "treat", "treats", "snack", "meal", "raw diet", "wet food", "dry food", "grain-free"],
    "toy": ["toy", "toys", "chew", "chews", "interactive", "puzzle"],
    "bed": ["bed", "beds", "crate", "crates", "kennel", "house", "sleeping"],
    "collar": ["collar", "collars", "leash", "leashes", "harness", "harnesses"],
    "grooming": ["brush", "brushes", "shampoo", "grooming", "clipper", "clippers", "nail", "comb", "combs", "deshedding"],
    "health": ["supplement", "supplements", "vitamin", "vitamins", "medicine", "flea", "tick", "worm", "dewormer", "dental", "joint", "probiotic"],
    "training": ["training", "trainer", "clicker", "treat pouch", "muzzle", "pads", "potty"],
    "carrier": ["carrier", "carriers", "travel", "stroller", "car seat", "car harness", "backpack"],
    "bowl": ["bowl", "bowls", "feeder", "feeders", "fountain", "water", "slow feeder", "automatic"],
    "clothing": ["coat", "jacket", "sweater", "boots", "raincoat", "costume", "clothing", "outfit"],
    "litter": ["litter", "litter box", "litter boxes", "scooper", "mat"],
    "aquarium": ["filter", "heater", "pump", "light", "gravel", "substrate", "decoration", "plant"],
    "cage": ["cage", "cages", "habitat", "terrarium", "vivarium", "enclosure"],
}


def detect_pet_type(title_lower):
    """Return the detected pet type or 'pet'."""
    for ptype, kws in PET_KEYWORDS.items():
        if any(kw in title_lower for kw in kws):
            return ptype
    return "pet"


def detect_topic(title_lower):
    """Return the detected product/topic category."""
    for topic, kws in TOPIC_CATEGORIES.items():
        if any(kw in title_lower for kw in kws):
            return topic
    return "product"


# ── Table Generation ────────────────────────────────────────────────────

# Contextual data for building realistic comparison rows
TABLE_DATA = {
    "food": {
        "options": ["Budget Pick", "Mid-Range Choice", "Premium Selection"],
        "best_for": ["Cost-conscious owners", "Balanced nutrition & value", "Optimal health & ingredients"],
        "price": ["$15-25/bag", "$30-45/bag", "$50-70/bag"],
        "quality": ["Standard ingredients", "High-quality protein sources", "Human-grade, limited ingredient"],
        "rating": ["3.5/5", "4/5", "4.5/5"],
        "features": ["Meets basic nutritional needs", "Added vitamins & minerals", "Grain-free, all-natural formula"],
    },
    "toy": {
        "options": ["Value Pack", "Durable Favorite", "Interactive Premium"],
        "best_for": ["Light chewers & play", "Moderate to heavy chewers", "Mental stimulation & engagement"],
        "price": ["$5-10", "$12-20", "$25-40"],
        "quality": ["Basic materials", "Reinforced construction", "Heavy-duty, non-toxic materials"],
        "rating": ["3.5/5", "4.5/5", "4/5"],
        "features": ["Fun shapes, lightweight", "Long-lasting, tough fabric", "Puzzle elements, treat-dispensing"],
    },
    "bed": {
        "options": ["Budget Comfort", "Orthopedic Mid-Range", "Luxury Premium"],
        "best_for": ["Young, healthy pets", "Aging joints & comfort", "Maximum support & style"],
        "price": ["$20-35", "$45-70", "$80-120"],
        "quality": ["Polyester fill", "Memory foam core", "Medical-grade orthopedic foam"],
        "rating": ["3.5/5", "4.5/5", "4.5/5"],
        "features": ["Machine-washable cover", "Bolstered edges, anti-slip base", "Temperature-regulating, waterproof"],
    },
    "collar": {
        "options": ["Basic Everyday", "Reflective Mid-Range", "Smart Premium"],
        "best_for": ["Daily walks & ID", "Low-light visibility", "Training & GPS tracking"],
        "price": ["$8-15", "$18-30", "$40-80"],
        "quality": ["Nylon webbing", "Reinforced nylon with reflective stitching", "Durable composite with tech integration"],
        "rating": ["3.5/5", "4/5", "4.5/5"],
        "features": ["Adjustable, quick-release buckle", "Reflective strips, padded handle", "GPS, LED lights, app-connected"],
    },
    "grooming": {
        "options": ["Starter Kit", "Professional Grade", "Salon-Quality Set"],
        "best_for": ["Basic home grooming", "Regular grooming routine", "Show-quality results"],
        "price": ["$10-20", "$25-45", "$50-90"],
        "quality": ["Basic bristles & blades", "Stainless steel, ergonomic grip", "Professional-grade materials"],
        "rating": ["3.5/5", "4/5", "4.5/5"],
        "features": ["Covers basic grooming needs", "Self-cleaning, low-noise", "Full set with storage case"],
    },
    "health": {
        "options": ["Essential Basics", "Comprehensive Formula", "Veterinary-Strength"],
        "best_for": ["General wellness support", "Targeted health needs", "Specific medical conditions"],
        "price": ["$10-20/month", "$25-40/month", "$45-70/month"],
        "quality": ["Standard formulation", "High-bioavailability ingredients", "Clinically-tested compounds"],
        "rating": ["3.5/5", "4/5", "4.5/5"],
        "features": ["Basic vitamin & mineral blend", "Added probiotics & omega fatty acids", "Vet-recommended, research-backed"],
    },
    "training": {
        "options": ["Beginner Set", "Intermediate Kit", "Professional System"],
        "best_for": ["New pet owners", "Consistent training routines", "Advanced behavior modification"],
        "price": ["$10-20", "$25-45", "$50-80"],
        "quality": ["Basic materials", "Durable, well-designed tools", "Professional-grade equipment"],
        "rating": ["3.5/5", "4/5", "4.5/5"],
        "features": ["Simple clicker & treats", "Multi-tool kit with guide", "Complete system with remote training aid"],
    },
    "carrier": {
        "options": ["Soft-Sided Basic", "Hard-Shell Mid-Range", "Airline-Approved Premium"],
        "best_for": ["Short trips & vet visits", "Car travel & medium trips", "Air travel & long journeys"],
        "price": ["$20-35", "$40-65", "$70-120"],
        "quality": ["Mesh & fabric construction", "Impact-resistant plastic", "Reinforced, ventilated design"],
        "rating": ["3.5/5", "4/5", "4.5/5"],
        "features": ["Lightweight, foldable", "Secure latches, easy-clean", "TSA-compliant, comfort-padded"],
    },
    "bowl": {
        "options": ["Standard Bowl", "Slow-Feeder Design", "Automatic Dispenser"],
        "best_for": ["Basic feeding needs", "Fast eaters & portion control", "Scheduled feeding & multi-pet homes"],
        "price": ["$5-12", "$15-25", "$40-80"],
        "quality": ["Stainless steel or ceramic", "BPA-free plastic with ridges", "Electronic with timer & battery backup"],
        "rating": ["3.5/5", "4/5", "4.5/5"],
        "features": ["Non-slip base, dishwasher-safe", "Reduces bloating & overeating", "Programmable portions, app control"],
    },
    "clothing": {
        "options": ["Basic Layer", "Weather-Resistant Mid", "All-Season Premium"],
        "best_for": ["Light indoor warmth", "Rain & wind protection", "Extreme weather & outdoor activity"],
        "price": ["$10-20", "$25-40", "$45-75"],
        "quality": ["Fleece or cotton blend", "Waterproof outer, fleece lining", "Multi-layer, reflective, insulated"],
        "rating": ["3.5/5", "4/5", "4.5/5"],
        "features": ["Easy on/off, machine-washable", "Adjustable fit, hood included", "Full coverage, harness-compatible"],
    },
    "litter": {
        "options": ["Traditional Clay", "Natural Clumping", "Crystal Premium"],
        "best_for": ["Budget-friendly basics", "Eco-conscious households", "Maximum odor control"],
        "price": ["$8-15/bag", "$15-25/bag", "$20-35/bag"],
        "quality": ["Standard absorption", "Biodegradable, dust-free", "Superior moisture-locking crystals"],
        "rating": ["3/5", "4/5", "4.5/5"],
        "features": ["Widely available, affordable", "Flushable, low-tracking", "Lasts longer, color-change health indicator"],
    },
    "aquarium": {
        "options": ["Starter Equipment", "Intermediate Setup", "Advanced System"],
        "best_for": ["First-time fish keepers", "Growing hobbyists", "Experienced aquarists"],
        "price": ["$15-30", "$35-60", "$70-150"],
        "quality": ["Basic filtration & lighting", "Efficient, adjustable components", "Professional-grade, energy-efficient"],
        "rating": ["3.5/5", "4/5", "4.5/5"],
        "features": ["Easy setup, compact design", "Quiet operation, customizable flow", "Smart controls, built-in monitoring"],
    },
    "cage": {
        "options": ["Basic Enclosure", "Spacious Mid-Range", "Deluxe Habitat"],
        "best_for": ["Small pets, temporary housing", "Everyday comfort & space", "Permanent home with enrichment"],
        "price": ["$25-45", "$50-90", "$100-180"],
        "quality": ["Wire or basic plastic", "Powder-coated metal, multi-level", "Premium materials, modular design"],
        "rating": ["3.5/5", "4/5", "4.5/5"],
        "features": ["Easy to clean, portable", "Multiple access doors, ramps", "Built-in accessories, expandable"],
    },
    "product": {
        "options": ["Budget Pick", "Mid-Range Choice", "Premium Selection"],
        "best_for": ["Cost-conscious pet owners", "Balance of quality & value", "Best-in-class performance"],
        "price": ["$-$$", "$$-$$$", "$$$-$$$$"],
        "quality": ["Meets basic standards", "Above-average materials", "Top-tier, long-lasting"],
        "rating": ["3.5/5", "4/5", "4.5/5"],
        "features": ["Affordable & functional", "Great reviews, reliable", "Premium materials, warranty included"],
    },
}

# Pet-specific modifiers for "best_for" context
PET_BEST_FOR = {
    "dog": {
        "food": ["Small breeds on a budget", "Active adult dogs", "Large breeds with sensitivities"],
        "toy": ["Gentle puppies", "Medium-energy dogs", "Power chewers & large breeds"],
        "bed": ["Puppies & small dogs", "Adult dogs with joint concerns", "Senior or large breed dogs"],
    },
    "cat": {
        "food": ["Indoor cats on a budget", "Active adult cats", "Cats with dietary sensitivities"],
        "toy": ["Lazy cats needing motivation", "Playful adult cats", "Bored indoor cats"],
        "litter": ["Single-cat households", "Multi-cat homes", "Odor-sensitive owners"],
    },
    "fish": {
        "aquarium": ["Betta or small tanks", "Community tank setups", "Saltwater or planted tanks"],
    },
    "rabbit": {
        "cage": ["Young or dwarf rabbits", "Standard-size rabbits", "Large or bonded pairs"],
        "food": ["Budget hay & pellets", "Balanced diet mixes", "Organic, vet-recommended blends"],
    },
}


def generate_comparison_table(title):
    """Generate a Gutenberg-compatible comparison table block from the post title."""
    clean = clean_title(title)
    title_lower = clean.lower()

    pet_type = detect_pet_type(title_lower)
    topic = detect_topic(title_lower)

    # Get base data for this topic
    data = TABLE_DATA.get(topic, TABLE_DATA["product"])

    # Try pet-specific overrides for "best_for"
    pet_overrides = PET_BEST_FOR.get(pet_type, {}).get(topic, None)

    options = data["options"]
    best_for = pet_overrides if pet_overrides else data["best_for"]
    price = data["price"]
    quality = data["quality"]
    rating = data["rating"]
    features = data["features"]

    # Determine if we use 3 or 4 columns (always 3 options = 4 columns total)
    # Build the table HTML
    table_html = (
        '<!-- wp:table {"className":"is-style-stripes"} -->\n'
        '<figure class="wp-block-table is-style-stripes"><table><thead><tr>'
        '<th>Feature</th>'
        f'<th>{options[0]}</th>'
        f'<th>{options[1]}</th>'
        f'<th>{options[2]}</th>'
        '</tr></thead><tbody>\n'
        f'<tr><td>Best For</td><td>{best_for[0]}</td><td>{best_for[1]}</td><td>{best_for[2]}</td></tr>\n'
        f'<tr><td>Price Range</td><td>{price[0]}</td><td>{price[1]}</td><td>{price[2]}</td></tr>\n'
        f'<tr><td>Durability/Quality</td><td>{quality[0]}</td><td>{quality[1]}</td><td>{quality[2]}</td></tr>\n'
        f'<tr><td>Key Features</td><td>{features[0]}</td><td>{features[1]}</td><td>{features[2]}</td></tr>\n'
        f'<tr><td>Our Rating</td><td>{rating[0]}</td><td>{rating[1]}</td><td>{rating[2]}</td></tr>\n'
        '</tbody></table></figure>\n'
        '<!-- /wp:table -->'
    )
    return table_html


def insert_table_after_paragraph(content, table_html, after_para=2):
    """
    Insert the table block after the Nth paragraph in the content.
    Handles both Gutenberg blocks (<!-- wp:paragraph -->) and raw <p> tags.
    Falls back to after first paragraph if fewer than `after_para` exist.
    """
    if not content or not content.strip():
        return table_html + "\n" + (content or "")

    # Strategy 1: Gutenberg paragraph blocks
    # Match <!-- /wp:paragraph --> closings
    gutenberg_pattern = r'(<!-- /wp:paragraph -->)'
    gutenberg_matches = list(re.finditer(gutenberg_pattern, content))

    if gutenberg_matches:
        # Insert after the Nth paragraph block (or last available)
        idx = min(after_para, len(gutenberg_matches)) - 1
        insert_pos = gutenberg_matches[idx].end()
        return content[:insert_pos] + "\n\n" + table_html + "\n\n" + content[insert_pos:]

    # Strategy 2: Raw </p> tags
    p_pattern = r'(</p>)'
    p_matches = list(re.finditer(p_pattern, content, re.IGNORECASE))

    if p_matches:
        idx = min(after_para, len(p_matches)) - 1
        insert_pos = p_matches[idx].end()
        return content[:insert_pos] + "\n\n" + table_html + "\n\n" + content[insert_pos:]

    # Strategy 3: Insert after first double newline
    double_nl = content.find("\n\n")
    if double_nl != -1:
        return content[:double_nl] + "\n\n" + table_html + "\n\n" + content[double_nl:]

    # Fallback: prepend
    return table_html + "\n\n" + content


# ── Main ────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("Phase 24B: Comparison Table Insertion for PetHub Online")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)

    # 1. Fetch all published posts
    print("\n[1/4] Fetching all published posts...")
    all_posts = fetch_all_posts()
    print(f"  Total posts fetched: {len(all_posts)}")

    # 2. Identify qualifying posts
    print("\n[2/4] Identifying comparison posts without tables...")
    qualifying = []
    skipped_no_match = 0
    skipped_has_table = 0

    for post in all_posts:
        title_raw = post.get("title", {})
        if isinstance(title_raw, dict):
            title = title_raw.get("raw", title_raw.get("rendered", ""))
        else:
            title = str(title_raw)

        content_raw = post.get("content", {})
        if isinstance(content_raw, dict):
            content = content_raw.get("raw", content_raw.get("rendered", ""))
        else:
            content = str(content_raw)

        if not is_comparison_post(title):
            skipped_no_match += 1
            continue

        if has_table(content):
            skipped_has_table += 1
            continue

        qualifying.append({
            "id": post["id"],
            "title": clean_title(title),
            "content": content,
        })

    print(f"  Posts matching comparison keywords: {len(qualifying) + skipped_has_table}")
    print(f"  Already have tables (skipped): {skipped_has_table}")
    print(f"  Not comparison posts (skipped): {skipped_no_match}")
    print(f"  Qualifying for table insertion: {len(qualifying)}")

    # 3. Generate and insert tables
    print(f"\n[3/4] Generating and inserting tables into {len(qualifying)} posts...")
    results = {
        "phase": "24B",
        "description": "Comparison table insertion",
        "started": datetime.now().isoformat(),
        "total_posts": len(all_posts),
        "qualifying_posts": len(qualifying),
        "skipped_has_table": skipped_has_table,
        "skipped_no_match": skipped_no_match,
        "updated": [],
        "failed": [],
    }

    for i, post in enumerate(qualifying):
        pid = post["id"]
        title = post["title"]
        content = post["content"]

        print(f"\n  [{i+1}/{len(qualifying)}] ID {pid}: {title[:70]}...")

        # Generate comparison table
        table_html = generate_comparison_table(title)

        # Insert after 2nd paragraph (or 1st if content is short)
        new_content = insert_table_after_paragraph(content, table_html, after_para=2)

        # Update via API
        update_url = f"{WP_BASE}/posts/{pid}"
        update_data = {"content": new_content}

        time.sleep(DELAY)
        resp = api_put(update_url, update_data)

        if resp and resp.status_code in (200, 201):
            print(f"    OK - Table inserted")
            results["updated"].append({
                "id": pid,
                "title": title,
                "pet_type": detect_pet_type(title.lower()),
                "topic": detect_topic(title.lower()),
            })
        else:
            status = resp.status_code if resp else "no response"
            print(f"    FAILED - Status: {status}")
            results["failed"].append({
                "id": pid,
                "title": title,
                "error": str(status),
            })

    # 4. Save results
    results["completed"] = datetime.now().isoformat()
    results["total_updated"] = len(results["updated"])
    results["total_failed"] = len(results["failed"])

    print(f"\n[4/4] Saving results to {RESULTS_PATH}...")
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)

    # Summary
    print("\n" + "=" * 70)
    print("Phase 24B COMPLETE")
    print(f"  Total posts scanned: {len(all_posts)}")
    print(f"  Tables inserted: {len(results['updated'])}")
    print(f"  Failed: {len(results['failed'])}")
    print(f"  Results saved: {RESULTS_PATH}")
    print("=" * 70)


if __name__ == "__main__":
    main()
