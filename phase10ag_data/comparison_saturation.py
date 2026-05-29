#!/usr/bin/env python3
"""
Insert educational comparison tables into PetHub Online posts that lack them.
Targets 50 posts, prioritized by cluster coverage gaps.
"""

import json
import subprocess
import time
import csv
import os
import re
import tempfile
from datetime import datetime

WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
LOG_FILE = "/var/lib/freelancer/projects/40416335/phase10ag_data/comparison_saturation_log.csv"

# Category ID to cluster mapping
CATEGORY_CLUSTERS = {
    1377: "Cat Supplies",
    1459: "Cat Toys",
    1413: "Indoor Cats",
    1376: "Dog Supplies",
    1422: "Dog Harnesses",
    1481: "Harnesses",
    1450: "Dog Health",
    1391: "Pet Health",
    1487: "Health & Wellness",
    1489: "Dog Care",
    1397: "Pet Care",
    1378: "Pet Care Tips",
    1441: "Dog Toys",
    1460: "Interactive Toys",
    1443: "Enrichment Activities",
    1474: "Training Supplies",
    1442: "Puppy Care",
    1401: "Dog Beds",
    1396: "Pet Beds",
    1403: "Large Breeds",
    1482: "Large Dogs",
    1423: "Small Breeds",
    1467: "Dog Food",
    1468: "Grain-Free",
    1469: "Pet Nutrition",
    1402: "Pet Supplies",
    1380: "Buying Guides",
    1379: "Product Reviews",
    1494: "Arthritis Care",
    1455: "Orthopaedic Care",
    1505: "Orthopaedic Supplies",
    1438: "Winter Essentials",
    1430: "Winter Gear",
    1: "Uncategorized",
}

# Priority order for clusters (lowest coverage first)
CLUSTER_PRIORITY = {
    "Cat Supplies": 0,
    "Indoor Cats": 1,
    "Dog Health": 3,
    "Pet Health": 3,
    "Health & Wellness": 3,
    "Uncategorized": 4,
    "Training Supplies": 5,
    "Cat Toys": 6,
    "Dog Harnesses": 7,
    "Harnesses": 7,
    "Dog Supplies": 8,
    "Dog Care": 8,
    "Pet Care": 8,
    "Pet Care Tips": 8,
    "Dog Toys": 9,
    "Interactive Toys": 9,
    "Enrichment Activities": 9,
    "Puppy Care": 10,
    "Dog Beds": 11,
    "Pet Beds": 11,
    "Large Breeds": 12,
    "Large Dogs": 12,
    "Small Breeds": 12,
    "Dog Food": 13,
    "Grain-Free": 13,
    "Pet Nutrition": 13,
    "Pet Supplies": 14,
    "Buying Guides": 14,
    "Product Reviews": 14,
    "Arthritis Care": 15,
    "Orthopaedic Care": 15,
    "Orthopaedic Supplies": 15,
    "Winter Essentials": 16,
    "Winter Gear": 16,
}


def api_get(endpoint):
    """Make WP API GET call using curl subprocess."""
    url = f"{WP_API}/{endpoint}"
    cmd = ["curl", "-s", "--compressed", "-u", AUTH, url]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  ERROR parsing GET response: {result.stdout[:200]}")
        return None


def api_post(endpoint, data):
    """Make WP API POST call using curl subprocess with temp file."""
    url = f"{WP_API}/{endpoint}"
    tmpfile = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, dir='/tmp')
    json.dump(data, tmpfile)
    tmpfile.close()
    cmd = ["curl", "-s", "--compressed", "-u", AUTH, "-X", "POST",
           "-H", "Content-Type: application/json", "-d", f"@{tmpfile.name}", url]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    try:
        os.unlink(tmpfile.name)
    except:
        pass
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  ERROR parsing POST response: {result.stdout[:300]}")
        return None


def fetch_all_posts():
    """Fetch all published posts with pagination."""
    all_posts = []
    page = 1
    while True:
        print(f"Fetching page {page}...")
        data = api_get(f"posts?per_page=100&page={page}&status=publish&_fields=id,title,categories,content&context=edit")
        if not data or (isinstance(data, dict) and data.get('code')):
            break
        all_posts.extend(data)
        if len(data) < 100:
            break
        page += 1
        time.sleep(0.5)
    return all_posts


def get_cluster(categories):
    """Get the highest-priority cluster for a post's categories."""
    best_cluster = "Uncategorized"
    best_priority = 99
    for cat_id in categories:
        cluster = CATEGORY_CLUSTERS.get(cat_id, "Uncategorized")
        priority = CLUSTER_PRIORITY.get(cluster, 50)
        if priority < best_priority:
            best_priority = priority
            best_cluster = cluster
    return best_cluster, best_priority


def has_comparison_table(content):
    """Check if content already has a comparison table."""
    if "wp:table" in content or "wp-block-table" in content:
        return True
    return False


def generate_table(title, content, cluster):
    """Generate a contextually relevant comparison table based on post topic."""
    title_lower = title.lower()
    content_lower = content.lower()

    # ===== CAT SUPPLIES =====
    if cluster == "Cat Supplies" or ("cat" in cluster.lower() and "cat toys" not in cluster.lower()):
        if any(w in title_lower for w in ["litter", "box", "bathroom"]):
            return _table_cat_litter()
        elif any(w in title_lower for w in ["bed", "sleep", "nap", "rest"]):
            return _table_cat_beds()
        elif any(w in title_lower for w in ["groom", "brush", "fur", "coat", "shed"]):
            return _table_cat_grooming_tools()
        elif any(w in title_lower for w in ["food", "feed", "bowl", "dish", "eat", "diet", "nutrition"]):
            return _table_cat_feeding()
        elif any(w in title_lower for w in ["toy", "play", "chase", "feather", "mouse", "laser", "wand"]):
            return _table_cat_toys()
        elif any(w in title_lower for w in ["scratch", "post", "pad"]):
            return _table_cat_scratchers()
        elif any(w in title_lower for w in ["carrier", "travel", "transport"]):
            return _table_cat_carriers()
        elif any(w in title_lower for w in ["indoor", "window", "perch", "tree", "climb"]):
            return _table_indoor_cat_enrichment()
        elif any(w in title_lower for w in ["health", "vet", "dental", "teeth"]):
            return _table_cat_health()
        elif any(w in title_lower for w in ["collar", "harness", "leash", "walk"]):
            return _table_cat_harnesses()
        else:
            return _table_cat_supplies_general()

    # ===== INDOOR CATS =====
    if cluster == "Indoor Cats":
        if any(w in title_lower for w in ["toy", "play", "enrich", "stimul"]):
            return _table_indoor_cat_toys()
        elif any(w in title_lower for w in ["climb", "tree", "perch", "shelf", "furniture"]):
            return _table_cat_furniture()
        elif any(w in title_lower for w in ["window", "bird", "watch"]):
            return _table_window_enrichment()
        elif any(w in title_lower for w in ["exercise", "active", "weight", "fitness"]):
            return _table_indoor_exercise()
        else:
            return _table_indoor_cat_enrichment()

    # ===== CAT TOYS =====
    if cluster == "Cat Toys":
        if any(w in title_lower for w in ["puzzle", "brain", "mental"]):
            return _table_cat_puzzle_toys()
        elif any(w in title_lower for w in ["laser", "electronic", "automat"]):
            return _table_cat_electronic_toys()
        elif any(w in title_lower for w in ["feather", "wand", "interactive"]):
            return _table_cat_interactive_toys()
        else:
            return _table_cat_toys()

    # ===== DOG HARNESSES =====
    if cluster in ("Dog Harnesses", "Harnesses"):
        if any(w in title_lower for w in ["no-pull", "no pull", "pull", "walk"]):
            return _table_no_pull_harnesses()
        elif any(w in title_lower for w in ["small", "puppy", "tiny", "mini"]):
            return _table_small_dog_harnesses()
        elif any(w in title_lower for w in ["large", "big", "strong", "power"]):
            return _table_large_dog_harnesses()
        elif any(w in title_lower for w in ["car", "travel", "vehicle", "seat"]):
            return _table_car_harnesses()
        elif any(w in title_lower for w in ["hike", "trail", "adventure", "outdoor"]):
            return _table_adventure_harnesses()
        else:
            return _table_harness_types()

    # ===== DOG HEALTH =====
    if cluster in ("Dog Health", "Pet Health", "Health & Wellness"):
        if any(w in title_lower for w in ["flea", "tick", "parasite", "worm"]):
            return _table_flea_treatments()
        elif any(w in title_lower for w in ["dental", "teeth", "chew", "oral"]):
            return _table_dental_care()
        elif any(w in title_lower for w in ["joint", "hip", "arthrit", "mobil", "glucosamine"]):
            return _table_joint_supplements()
        elif any(w in title_lower for w in ["skin", "allerg", "itch", "coat", "shed"]):
            return _table_skin_allergy()
        elif any(w in title_lower for w in ["digest", "stomach", "gut", "probiotic"]):
            return _table_digestive_health()
        elif any(w in title_lower for w in ["senior", "elder", "aging", "old"]):
            return _table_senior_dog_health()
        elif any(w in title_lower for w in ["supplement", "vitamin", "omega"]):
            return _table_supplements_overview()
        elif any(w in title_lower for w in ["anxiety", "stress", "calm", "fear"]):
            return _table_anxiety_aids()
        else:
            return _table_health_general()

    # ===== DOG TRAINING =====
    if cluster in ("Training Supplies",):
        if any(w in title_lower for w in ["treat", "reward", "snack"]):
            return _table_training_treats()
        elif any(w in title_lower for w in ["leash", "lead", "walk"]):
            return _table_training_leashes()
        elif any(w in title_lower for w in ["clicker", "marker", "signal"]):
            return _table_training_methods()
        elif any(w in title_lower for w in ["puppy", "young", "baby"]):
            return _table_puppy_training()
        elif any(w in title_lower for w in ["crate", "kennel", "house"]):
            return _table_crate_training()
        elif any(w in title_lower for w in ["agility", "sport", "course"]):
            return _table_agility_equipment()
        else:
            return _table_training_methods()

    # ===== DOG BEDS =====
    if cluster in ("Dog Beds", "Pet Beds"):
        if any(w in title_lower for w in ["ortho", "memory", "joint", "senior", "arthrit"]):
            return _table_ortho_beds()
        elif any(w in title_lower for w in ["outdoor", "travel", "camping", "portable"]):
            return _table_outdoor_beds()
        elif any(w in title_lower for w in ["chew", "durable", "tough"]):
            return _table_durable_beds()
        else:
            return _table_bed_types()

    # ===== DOG TOYS / ENRICHMENT =====
    if cluster in ("Dog Toys", "Interactive Toys", "Enrichment Activities"):
        if any(w in title_lower for w in ["puzzle", "brain", "mental", "cognitive", "stimul"]):
            return _table_puzzle_toys()
        elif any(w in title_lower for w in ["chew", "tough", "durable", "destruct"]):
            return _table_chew_toys()
        elif any(w in title_lower for w in ["fetch", "ball", "throw", "outdoor"]):
            return _table_fetch_toys()
        elif any(w in title_lower for w in ["tug", "rope", "interactive"]):
            return _table_tug_toys()
        elif any(w in title_lower for w in ["puppy", "teeth", "teethe"]):
            return _table_puppy_toys()
        elif any(w in title_lower for w in ["stuff", "kong", "dispens", "treat"]):
            return _table_treat_dispensing_toys()
        elif any(w in title_lower for w in ["water", "swim", "pool"]):
            return _table_water_toys()
        elif any(w in title_lower for w in ["snuffle", "nose", "scent", "smell", "forag"]):
            return _table_scent_enrichment()
        elif any(w in title_lower for w in ["calm", "anxiety", "sooth", "comfort", "plush"]):
            return _table_comfort_toys()
        elif any(w in title_lower for w in ["senior", "elder", "old", "gentle"]):
            return _table_senior_dog_toys()
        elif any(w in title_lower for w in ["rotation", "schedul", "variety", "bore"]):
            return _table_toy_rotation()
        elif any(w in title_lower for w in ["diy", "homemade", "make"]):
            return _table_diy_enrichment()
        elif any(w in title_lower for w in ["over", "excit", "too much", "calm down", "recover"]):
            return _table_overstimulation_recovery()
        elif any(w in title_lower for w in ["sensory", "sense", "sound", "sight", "touch"]):
            return _table_scent_enrichment()
        elif any(w in title_lower for w in ["solo", "alone", "independ", "self"]):
            return _table_treat_dispensing_toys()
        elif any(w in title_lower for w in ["group", "social", "multi", "two", "pair"]):
            return _table_tug_toys()
        else:
            return _table_toy_types_overview()

    # ===== DOG FOOD / NUTRITION =====
    if cluster in ("Dog Food", "Grain-Free", "Pet Nutrition"):
        if any(w in title_lower for w in ["grain", "gluten"]):
            return _table_grain_options()
        elif any(w in title_lower for w in ["puppy", "growth"]):
            return _table_puppy_food()
        elif any(w in title_lower for w in ["senior", "mature", "aging"]):
            return _table_senior_food()
        else:
            return _table_food_types()

    # ===== PUPPY CARE =====
    if cluster == "Puppy Care":
        if any(w in title_lower for w in ["toy", "play", "chew"]):
            return _table_puppy_toys()
        elif any(w in title_lower for w in ["train", "house", "potty"]):
            return _table_puppy_training()
        elif any(w in title_lower for w in ["food", "feed", "diet"]):
            return _table_puppy_food()
        else:
            return _table_puppy_essentials()

    # ===== BREEDS =====
    if cluster in ("Large Breeds", "Large Dogs"):
        if any(w in title_lower for w in ["bed", "sleep"]):
            return _table_large_breed_beds()
        elif any(w in title_lower for w in ["toy", "play"]):
            return _table_large_breed_toys()
        elif any(w in title_lower for w in ["harness", "walk", "leash"]):
            return _table_large_dog_harnesses()
        else:
            return _table_large_breed_gear()

    if cluster == "Small Breeds":
        if any(w in title_lower for w in ["harness", "walk", "leash"]):
            return _table_small_dog_harnesses()
        else:
            return _table_small_breed_gear()

    # ===== WINTER =====
    if cluster in ("Winter Essentials", "Winter Gear"):
        return _table_winter_gear()

    # ===== ORTHO =====
    if cluster in ("Arthritis Care", "Orthopaedic Care", "Orthopaedic Supplies"):
        return _table_joint_supplements()

    # ===== BUYING GUIDES / REVIEWS =====
    if cluster in ("Buying Guides", "Product Reviews"):
        if "cat" in title_lower:
            return _table_cat_supplies_general()
        elif "harness" in title_lower:
            return _table_harness_types()
        elif "bed" in title_lower:
            return _table_bed_types()
        elif "toy" in title_lower:
            return _table_toy_types_overview()
        else:
            return _table_pet_supplies_general()

    # ===== GENERAL FALLBACK based on title keywords =====
    if any(w in title_lower for w in ["harness"]):
        return _table_harness_types()
    if any(w in title_lower for w in ["bed", "sleep", "rest"]):
        return _table_bed_types()
    if any(w in title_lower for w in ["toy", "play", "enrich", "puzzle", "mental"]):
        return _table_toy_types_overview()
    if any(w in title_lower for w in ["food", "feed", "diet", "nutrition"]):
        return _table_food_types()
    if any(w in title_lower for w in ["groom", "brush", "bath", "shampoo"]):
        return _table_grooming_tools()
    if any(w in title_lower for w in ["flea", "tick", "parasite"]):
        return _table_flea_treatments()
    if any(w in title_lower for w in ["dental", "teeth"]):
        return _table_dental_care()
    if any(w in title_lower for w in ["joint", "hip", "arthrit", "mobil"]):
        return _table_joint_supplements()
    if any(w in title_lower for w in ["train", "obedien", "command"]):
        return _table_training_methods()
    if any(w in title_lower for w in ["collar", "leash", "lead"]):
        return _table_collar_leash_types()
    if any(w in title_lower for w in ["cat"]):
        return _table_cat_supplies_general()
    if any(w in title_lower for w in ["puppy", "kitten"]):
        return _table_puppy_essentials()
    if any(w in title_lower for w in ["senior", "elder", "aging"]):
        return _table_senior_dog_health()
    if any(w in title_lower for w in ["anxiety", "stress", "calm", "fear"]):
        return _table_anxiety_aids()
    if any(w in title_lower for w in ["walk", "outdoor", "hike", "adventure"]):
        return _table_outdoor_gear()
    if any(w in title_lower for w in ["safe", "hazard", "danger", "toxic", "poison"]):
        return _table_safety_comparison()
    if any(w in title_lower for w in ["winter", "cold", "snow", "warm"]):
        return _table_winter_gear()
    if any(w in title_lower for w in ["summer", "heat", "cool"]):
        return _table_cooling_gear()
    if any(w in title_lower for w in ["travel", "car", "trip"]):
        return _table_travel_gear()
    if any(w in title_lower for w in ["clean", "wash", "maintain"]):
        return _table_cleaning_supplies()
    if any(w in title_lower for w in ["water", "swim", "hydrat"]):
        return _table_water_accessories()
    if any(w in title_lower for w in ["recover", "surgery", "heal"]):
        return _table_recovery_aids()
    if any(w in title_lower for w in ["weight", "obes"]):
        return _table_weight_management()
    if any(w in title_lower for w in ["supplement", "vitamin"]):
        return _table_supplements_overview()

    # Content-based fallback
    if "dog" in content_lower[:500]:
        return _table_pet_supplies_general()
    elif "cat" in content_lower[:500]:
        return _table_cat_supplies_general()
    else:
        return _table_pet_supplies_general()


# =====================================================
# TABLE GENERATORS - Each returns (title, headers, rows, topic)
# =====================================================

def _table_cat_litter():
    return ("Cat Litter Types",
            ["Litter Type", "Material", "Odour Control", "Dust Level", "Best For"],
            [
                ["Clumping Clay", "Sodium bentonite", "Good", "Moderate", "Multi-cat homes needing easy scoop cleanup"],
                ["Non-Clumping Clay", "Calcium bentonite", "Fair", "Moderate to High", "Budget-conscious single-cat households"],
                ["Silica Crystal", "Silica gel beads", "Excellent", "Very Low", "Owners wanting low-maintenance litter"],
                ["Pine Pellet", "Compressed pine sawdust", "Good (natural)", "Very Low", "Eco-conscious owners; kittens"],
                ["Recycled Paper", "Compressed recycled paper", "Fair", "Very Low", "Post-surgery cats; sensitive paws"],
                ["Corn or Wheat", "Ground corn/wheat kernels", "Good", "Low", "Households wanting flushable, biodegradable options"],
            ],
            "Cat litter types comparison")

def _table_cat_beds():
    return ("Cat Bed Styles",
            ["Bed Style", "Shape", "Warmth Level", "Washability", "Best For"],
            [
                ["Donut/Bolster", "Round with raised edges", "High", "Machine washable cover", "Cats that curl up; anxious cats seeking security"],
                ["Flat Mat", "Rectangular pad", "Low to Moderate", "Fully machine washable", "Cats that sprawl; warm climates"],
                ["Cave/Hooded", "Enclosed with entry hole", "Very High", "Removable cover washable", "Shy cats; cold environments"],
                ["Heated Pad", "Flat with electric element", "Highest", "Wipe clean; cover washable", "Senior cats; arthritic cats; hairless breeds"],
                ["Window Perch", "Shelf-mounted platform", "Moderate", "Removable pad washable", "Curious cats that enjoy bird-watching"],
            ],
            "Cat bed styles comparison")

def _table_cat_grooming_tools():
    return ("Cat Grooming Tools",
            ["Tool", "Coat Type", "Purpose", "Frequency", "Best For"],
            [
                ["Slicker Brush", "Medium to long coats", "Removes tangles and loose fur", "2-3 times weekly", "Persian, Maine Coon, and other long-haired breeds"],
                ["Bristle Brush", "Short coats", "Distributes natural oils", "Weekly", "British Shorthair, Siamese, and smooth-coated breeds"],
                ["Deshedding Comb", "Double coats", "Removes undercoat", "Weekly during shedding", "Cats with thick undercoats; seasonal shedders"],
                ["Flea Comb", "All coats", "Detects and removes fleas", "As needed", "Outdoor cats or flea-prone environments"],
                ["Grooming Glove", "All coats", "Gentle loose fur removal", "Daily to weekly", "Cats that dislike brushes; bonding sessions"],
            ],
            "Cat grooming tools comparison")

def _table_cat_feeding():
    return ("Cat Feeding Accessories",
            ["Feeder Type", "Material", "Capacity", "Cleaning", "Best For"],
            [
                ["Standard Bowl", "Ceramic or stainless steel", "Single meal", "Dishwasher safe", "Cats on scheduled feeding; portion control"],
                ["Elevated Feeder", "Ceramic/wood stand", "Single meal", "Dishwasher safe (bowl)", "Senior cats; cats with neck or joint issues"],
                ["Slow Feeder", "BPA-free plastic/silicone", "Single meal", "Hand wash recommended", "Fast eaters; cats prone to vomiting after meals"],
                ["Puzzle Feeder", "Plastic with movable parts", "Half to full meal", "Hand wash", "Indoor cats needing mental stimulation at mealtimes"],
                ["Automatic Dispenser", "Plastic with timer", "Multi-day supply", "Removable tray washable", "Owners with irregular schedules; multi-meal routines"],
                ["Water Fountain", "Stainless steel/ceramic", "1-3 litres", "Filter change every 2-4 weeks", "Cats reluctant to drink still water"],
            ],
            "Cat feeding accessories comparison")

def _table_cat_toys():
    return ("Cat Toy Types by Play Style",
            ["Toy Type", "Play Style", "Activity Level", "Supervision Needed", "Best For"],
            [
                ["Wand/Feather Toy", "Hunting and pouncing", "High", "Required (interactive)", "Active cats; bonding sessions; kittens"],
                ["Laser Pointer", "Chasing", "High", "Required (must end with physical toy)", "High-energy cats needing burst exercise"],
                ["Catnip Mouse", "Solo batting and kicking", "Moderate", "Minimal", "Cats that respond to catnip; solo play"],
                ["Puzzle Feeder", "Problem-solving", "Low to Moderate", "Minimal", "Indoor cats; food-motivated cats"],
                ["Crinkle Ball", "Batting and chasing", "Moderate", "Minimal", "Sound-motivated cats; nighttime play"],
                ["Electronic Motion Toy", "Chasing unpredictable movement", "High", "Minimal", "Cats left alone; boredom prevention"],
            ],
            "Cat toy types comparison")

def _table_cat_puzzle_toys():
    return ("Cat Puzzle Toy Difficulty",
            ["Difficulty Level", "Mechanism", "Solve Time", "Reward Type", "Best For"],
            [
                ["Beginner", "Single sliding door or flap", "1-3 minutes", "Visible treat retrieval", "Cats new to puzzles; building interest"],
                ["Intermediate", "Multiple sliders and pegs", "3-10 minutes", "Hidden treat discovery", "Cats that mastered beginner puzzles"],
                ["Advanced", "Sequential steps required", "10-20 minutes", "Deeply concealed treats", "Highly intelligent breeds; experienced puzzle cats"],
                ["Treat Ball (rolling)", "Roll to dispense kibble", "5-15 minutes", "Intermittent kibble release", "Active cats; mealtime enrichment"],
                ["Lick Mat (frozen)", "Licking frozen paste", "15-30 minutes", "Continuous small reward", "Calming enrichment; anxious cats; slow feeding"],
            ],
            "Cat puzzle toy comparison")

def _table_cat_electronic_toys():
    return ("Electronic and Automated Cat Toys",
            ["Toy Type", "Power Source", "Engagement Style", "Noise Level", "Best For"],
            [
                ["Automated Laser", "Battery or USB", "Random laser pattern chasing", "Silent", "Solo play for high-energy cats"],
                ["Rotating Feather", "Battery", "Circular feather mimics bird", "Quiet motor hum", "Prey-drive stimulation; kittens"],
                ["Track Ball Circuit", "Manual (gravity-powered)", "Ball rolls in enclosed track", "Quiet clicking", "Self-directed play; multiple cats"],
                ["Flopping Fish", "Rechargeable USB", "Motion-activated flip and flop", "Quiet fabric rustling", "Cats attracted to movement; solo play"],
                ["App-Controlled Rover", "Rechargeable", "Owner drives toy via smartphone", "Quiet motor", "Remote interaction when owner is away"],
            ],
            "Electronic cat toys comparison")

def _table_cat_interactive_toys():
    return ("Interactive Cat Toy Comparison",
            ["Toy Type", "Owner Involvement", "Exercise Level", "Bond Building", "Best For"],
            [
                ["Feather Wand", "High (owner controls movement)", "High", "Excellent", "Daily play sessions; prey-drive fulfilment"],
                ["String/Ribbon Toy", "High (drag and twitch)", "Moderate to High", "Excellent", "Gentle interactive play; older cats"],
                ["Fishing Rod Toy", "Moderate (cast and reel)", "High", "Good", "Longer-range play in large rooms"],
                ["Kick Stick", "Low (hold or toss)", "Moderate", "Moderate", "Cats that enjoy bunny-kicking; independent play"],
                ["Tunnel + Wand Combo", "Moderate (thread wand through tunnel)", "Very High", "Excellent", "Multi-element play; highly active cats"],
            ],
            "Interactive cat toys comparison")

def _table_cat_scratchers():
    return ("Cat Scratcher Types",
            ["Scratcher Type", "Material", "Orientation", "Durability", "Best For"],
            [
                ["Vertical Post", "Sisal rope wrapped", "Upright", "High (replaceable rope)", "Cats that stretch upward; tall cats"],
                ["Flat Cardboard Pad", "Corrugated cardboard", "Horizontal", "Low (replace every 1-3 months)", "Budget option; cats that prefer floor scratching"],
                ["Angled Ramp", "Sisal or carpet", "45-degree angle", "Moderate", "Cats that scratch at an angle; variety seekers"],
                ["Cat Tree with Posts", "Sisal + carpet + wood", "Multi-angle", "High", "Multi-cat homes; cats needing vertical territory"],
                ["Wall-Mounted Panel", "Sisal or cork", "Vertical (mounted)", "High", "Small spaces; cats that scratch furniture corners"],
            ],
            "Cat scratcher types comparison")

def _table_cat_carriers():
    return ("Cat Carrier Types",
            ["Carrier Type", "Material", "Weight", "Ventilation", "Best For"],
            [
                ["Hard-Shell Crate", "Durable plastic", "Moderate to Heavy", "Side/top vents", "Air travel; anxious cats needing security"],
                ["Soft-Sided Bag", "Nylon/polyester mesh", "Light", "Mesh panels all sides", "Short car trips; calm cats"],
                ["Backpack Carrier", "Hard bubble or mesh", "Moderate", "Mesh + window", "Walking errands; cats that enjoy observing"],
                ["Top-Loading Carrier", "Plastic with top door", "Moderate", "Side vents + top opening", "Cats difficult to load; vet visits"],
                ["Expandable Carrier", "Fabric with zip expansion", "Light to Moderate", "Mesh expansion panels", "Longer journeys; cats that need movement space"],
            ],
            "Cat carrier types comparison")

def _table_indoor_cat_enrichment():
    return ("Indoor Cat Enrichment Options",
            ["Enrichment Type", "Engagement Level", "Space Needed", "Cost Range", "Best For"],
            [
                ["Cat Tree / Tower", "High (climbing, perching)", "Moderate floor space", "Mid to Premium", "Active cats; multi-cat homes needing vertical territory"],
                ["Window Bird Feeder", "Moderate (visual stimulation)", "Window sill only", "Budget", "Sedentary cats; elderly cats enjoying passive watching"],
                ["Interactive Puzzle Feeder", "High (problem-solving)", "Minimal", "Budget to Mid", "Food-motivated cats; overweight cats"],
                ["Rotating Toy Collection", "Moderate to High", "Minimal", "Budget", "Easily bored cats; variety-seeking personalities"],
                ["Catio / Enclosed Patio", "Very High (outdoor access)", "Outdoor space required", "Mid to Premium", "Former outdoor cats; high-energy breeds"],
            ],
            "Indoor cat enrichment comparison")

def _table_cat_health():
    return ("Common Cat Health Maintenance",
            ["Health Area", "Preventive Measure", "Frequency", "Warning Signs", "Best For"],
            [
                ["Dental", "Dental treats + water additives", "Daily treats; biannual vet check", "Bad breath, drooling, pawing at mouth", "All cats over 1 year; breeds prone to dental disease"],
                ["Coat and Skin", "Regular brushing + omega supplements", "Weekly brushing; daily supplements", "Excessive scratching, bald patches, dandruff", "Long-haired breeds; indoor cats with dry environments"],
                ["Urinary", "Wet food + clean water access", "Daily wet food; always-fresh water", "Straining in litter box, blood in urine", "Male cats; cats with UTI history"],
                ["Weight", "Portion control + daily play", "Measure food daily; 15-20 min play", "Visible belly sag, difficulty jumping", "Indoor cats; neutered/spayed cats"],
                ["Parasite Prevention", "Monthly preventive treatments", "Monthly (year-round)", "Excessive scratching, visible fleas, rice-like segments", "All cats; especially those with outdoor access"],
            ],
            "Cat health maintenance comparison")

def _table_cat_harnesses():
    return ("Cat Harness Styles",
            ["Harness Style", "Design", "Escape Resistance", "Comfort", "Best For"],
            [
                ["H-Style", "Two loops (neck + chest)", "Moderate", "Lightweight, minimal coverage", "Calm cats comfortable with harnesses; short walks"],
                ["Vest/Jacket", "Full torso coverage", "High", "Padded, secure", "Escape artists; nervous cats needing more security"],
                ["Figure-8", "Single strap in figure-8", "Low to Moderate", "Very lightweight", "Indoor trial walks; cats new to harnesses"],
                ["Step-In", "Legs step through loops", "Moderate", "Easy to put on", "Cats that resist overhead dressing"],
            ],
            "Cat harness styles comparison")

def _table_cat_supplies_general():
    return ("Essential Cat Supplies by Life Stage",
            ["Supply Category", "Kitten (0-12 months)", "Adult (1-10 years)", "Senior (10+ years)", "Best For"],
            [
                ["Food", "High-protein kitten formula", "Balanced adult maintenance", "Joint-support senior formula", "Matching nutrition to growth and metabolic needs"],
                ["Bed", "Small, washable fleece pad", "Covered bed or cat tree perch", "Heated or orthopaedic bed", "Providing age-appropriate comfort and warmth"],
                ["Litter", "Unscented, fine-grain (no clumping for kittens)", "Clumping clay or silica crystal", "Low-entry box with soft litter", "Ensuring safe, comfortable bathroom habits"],
                ["Toys", "Small interactive toys, wand toys", "Puzzle feeders, varied rotation", "Gentle, easy-to-bat toys", "Encouraging play appropriate to energy level"],
                ["Grooming", "Soft brush introduction", "Breed-appropriate brush + nail clips", "Gentle grooming glove", "Building grooming habits early; maintaining coat health"],
            ],
            "Cat supplies by life stage")

def _table_indoor_cat_toys():
    return ("Indoor Cat Toy Comparison",
            ["Toy Type", "Stimulation Type", "Energy Level Required", "Solo or Interactive", "Best For"],
            [
                ["Puzzle Feeder Ball", "Cognitive + food reward", "Low", "Solo", "Overweight indoor cats; slow-feeding goal"],
                ["Feather Wand", "Prey drive + exercise", "High", "Interactive (owner-led)", "Daily play sessions; bonding time"],
                ["Catnip Kicker", "Tactile + olfactory", "Moderate", "Solo", "Cats that enjoy bunny-kicking; solo entertainment"],
                ["Automated Laser", "Chase instinct + cardio", "High", "Solo (automated)", "Cats home alone; high-energy cats"],
                ["Treat-Dispensing Mouse", "Cognitive + food reward", "Low to Moderate", "Solo", "Food-motivated cats; mental enrichment"],
                ["Tunnel System", "Exploration + hiding", "Moderate to High", "Solo or multi-cat", "Playful cats; multi-cat households"],
            ],
            "Indoor cat toys comparison")

def _table_cat_furniture():
    return ("Cat Furniture Options",
            ["Furniture Type", "Height", "Floor Space", "Features", "Best For"],
            [
                ["Compact Cat Tree", "90-120 cm", "Small", "1-2 perches, scratching post", "Studio apartments; single cats"],
                ["Floor-to-Ceiling Tower", "240+ cm", "Moderate", "Multiple platforms, hammock, sisal", "Active climbers; multi-cat homes"],
                ["Wall-Mounted Shelves", "Variable", "Zero floor space", "Floating steps and perches", "Small homes; design-conscious owners"],
                ["Window Perch", "Window height", "Zero floor space", "Suction cup or bracket mount", "Bird watchers; sun-loving cats"],
                ["Enclosed Cat House", "Ground level", "Small to Moderate", "Hiding space, removable cushion", "Shy cats; anxious cats needing retreat"],
            ],
            "Cat furniture comparison")

def _table_window_enrichment():
    return ("Window-Based Cat Enrichment",
            ["Enrichment Type", "Installation", "Engagement Duration", "Maintenance", "Best For"],
            [
                ["External Bird Feeder", "Suction cup on window", "Hours of passive watching", "Refill seeds weekly", "Sedentary cats; elderly cats"],
                ["Window Perch Bed", "Bracket or suction mount", "Extended lounging", "Wash cushion monthly", "Sun-loving cats; nap-oriented cats"],
                ["Herb Garden on Sill", "Pots on window sill", "Moderate (sniffing, nibbling)", "Water regularly", "Cats that enjoy cat grass or catnip"],
                ["Mounted Aquarium View", "Tank near window", "Extended watching", "Tank maintenance", "Visually stimulated cats; calm breeds"],
            ],
            "Window enrichment comparison")

def _table_indoor_exercise():
    return ("Indoor Cat Exercise Methods",
            ["Exercise Method", "Calories Burned", "Time Needed", "Equipment", "Best For"],
            [
                ["Wand Toy Chase", "High", "10-15 min sessions", "Wand toy", "High-energy cats; daily cardio"],
                ["Laser Pointer Play", "High", "5-10 min (short bursts)", "Laser pointer + finishing toy", "Cats needing intense burst exercise"],
                ["Staircase Play", "Moderate to High", "5-10 min", "Toy to throw up/down stairs", "Homes with stairs; overweight cats"],
                ["Puzzle Feeder Meals", "Low", "15-30 min", "Puzzle feeder", "Mental stimulation; slow feeding"],
                ["Cat Wheel", "Very High", "Self-directed", "Exercise wheel", "Extremely active breeds (Bengal, Abyssinian)"],
            ],
            "Indoor cat exercise comparison")

def _table_no_pull_harnesses():
    return ("No-Pull Harness Comparison",
            ["Design Type", "Attachment Point", "Pull Redirection", "Comfort", "Best For"],
            [
                ["Front-Clip Harness", "Chest ring", "Redirects dog sideways", "Moderate (may chafe armpits)", "Moderate pullers; training walks"],
                ["Dual-Clip Harness", "Front + back rings", "Versatile control options", "Good (distributes pressure)", "Transitioning from pulling; varied situations"],
                ["Head Halter", "Under chin / behind ears", "Turns head to redirect", "Requires acclimation", "Strong pullers; large powerful breeds"],
                ["Tightening Harness", "Back ring with front tightening", "Gentle squeeze discourages pull", "Moderate", "Dogs that respond to gentle pressure cues"],
                ["Vest-Style No-Pull", "Front ring with padded vest", "Broad chest redirection", "High (wide padding)", "Dogs with sensitive skin; long walk sessions"],
            ],
            "No-pull harness comparison")

def _table_small_dog_harnesses():
    return ("Small Dog Harness Guide",
            ["Harness Style", "Weight Range", "Padding", "Adjustability", "Best For"],
            [
                ["Step-In Mesh", "Under 5 kg", "Breathable mesh", "Two belly straps", "Toy breeds; warm weather walks"],
                ["Vest-Style Padded", "3-8 kg", "Soft fleece lining", "Velcro + clip closure", "Small breeds that pull; cold weather"],
                ["Puppy Starter", "1-4 kg", "Lightweight nylon", "Multiple growth adjustments", "Puppies; harness training introduction"],
                ["Escape-Proof Double", "3-10 kg", "Moderate padding", "Neck + chest + belly straps", "Fearful small dogs; rescue dogs"],
                ["Reflective Safety", "3-10 kg", "Standard padding", "Quick-release clips", "Evening walks; low-light visibility"],
            ],
            "Small dog harness comparison")

def _table_large_dog_harnesses():
    return ("Large Dog Harness Options",
            ["Harness Type", "Weight Capacity", "Material", "Control Level", "Best For"],
            [
                ["Padded Y-Front", "25-50 kg", "Nylon with neoprene padding", "Moderate", "Daily walks; dogs with good leash manners"],
                ["Heavy-Duty No-Pull", "30-60+ kg", "Reinforced nylon webbing", "High", "Strong pullers; working breeds"],
                ["Tactical/MOLLE Vest", "25-55 kg", "Cordura nylon", "High (handle on top)", "Working dogs; hiking; service tasks"],
                ["Car Safety Harness", "25-50 kg", "Crash-tested nylon + padding", "Restraint only", "Vehicle travel safety"],
                ["Lifting/Support Harness", "25-60 kg", "Padded with lift handle", "Mobility support", "Senior dogs; post-surgery; joint issues"],
            ],
            "Large dog harness comparison")

def _table_car_harnesses():
    return ("Dog Car Safety Restraint Comparison",
            ["Restraint Type", "Safety Level", "Size Range", "Freedom of Movement", "Best For"],
            [
                ["Crash-Tested Harness", "Highest (impact tested)", "All sizes", "Limited", "Maximum safety; frequent car travel"],
                ["Seat Belt Adapter", "Moderate", "Medium to Large", "Moderate", "Budget option; short trips"],
                ["Car Seat/Booster", "Moderate (small dogs)", "Small to Medium", "Limited to seat area", "Small breeds needing elevation to see out"],
                ["Cargo Barrier", "Moderate (containment)", "All sizes", "Full within cargo", "SUVs; estate cars; multiple dogs"],
            ],
            "Car safety restraint comparison")

def _table_adventure_harnesses():
    return ("Adventure/Hiking Harness Features",
            ["Feature", "Standard Walk Harness", "Adventure Harness", "Backpack Harness", "Best For"],
            [
                ["Durability", "Moderate", "High (reinforced stitching)", "High (heavy-duty fabric)", "Trail conditions and terrain"],
                ["Handle", "None or small", "Top grab handle", "Top handle + saddle bags", "Quick control on steep terrain"],
                ["Reflective Elements", "Minimal", "360-degree reflective strips", "Reflective + light loop", "Low-light trail visibility"],
                ["Water Resistance", "None", "Quick-dry material", "Water-resistant coating", "Stream crossings and rain"],
                ["Storage", "None", "Minimal (ID pocket)", "Side panniers for water/food", "Multi-hour hikes with dog gear"],
            ],
            "Adventure harness comparison")

def _table_harness_types():
    return ("Dog Harness Types by Activity",
            ["Harness Type", "Design", "Control Level", "Comfort", "Best For"],
            [
                ["Back-Clip Standard", "Single D-ring on back", "Low to Moderate", "High (minimal restriction)", "Well-trained dogs; casual walks"],
                ["Front-Clip No-Pull", "D-ring on chest", "High (redirects pulling)", "Moderate", "Dogs learning leash manners; moderate pullers"],
                ["Dual-Clip Versatile", "Front + back D-rings", "Adjustable", "Good", "Trainers wanting flexibility; transitional use"],
                ["Step-In Harness", "Legs step through openings", "Moderate", "Easy on/off", "Dogs that dislike overhead dressing"],
                ["Vest/Padded Harness", "Wide chest plate", "Moderate", "Very High (distributed pressure)", "Dogs with trachea concerns; brachycephalic breeds"],
                ["Head Halter", "Loop over muzzle + behind ears", "Very High", "Requires conditioning", "Strong persistent pullers; reactive dogs"],
            ],
            "Harness types by activity")

def _table_flea_treatments():
    return ("Flea and Tick Treatment Options",
            ["Treatment Type", "Application", "Duration", "Onset", "Best For"],
            [
                ["Spot-On (Topical)", "Liquid between shoulder blades", "4 weeks", "12-24 hours", "Dogs comfortable with topical application; routine monthly use"],
                ["Oral Chewable Tablet", "Flavoured chew given by mouth", "4-12 weeks (varies)", "2-4 hours", "Dogs that swim or bathe often; fussy about topical"],
                ["Flea Collar", "Worn around neck continuously", "Up to 8 months", "24-48 hours", "Low-maintenance prevention; budget-friendly long-term option"],
                ["Flea Shampoo", "Lather during bath", "Immediate kill only (no residual)", "Immediate on contact", "Active infestations needing fast knockdown; not for prevention"],
                ["Environmental Spray", "Spray on carpets, bedding, furnishings", "Varies (2-6 months)", "Immediate on contact", "Treating home environment alongside pet treatment"],
            ],
            "Flea treatment comparison")

def _table_dental_care():
    return ("Dog Dental Care Methods",
            ["Method", "Effectiveness", "Ease of Use", "Frequency", "Best For"],
            [
                ["Tooth Brushing (enzymatic paste)", "Highest", "Requires training and patience", "Daily (ideal) or 3x weekly", "Dogs conditioned to mouth handling; gold-standard care"],
                ["Dental Chews (VOHC-approved)", "Moderate to Good", "Very Easy (give as treat)", "Daily", "Dogs that resist brushing; supplemental care"],
                ["Water Additives", "Low to Moderate", "Very Easy (add to bowl)", "Daily", "Low-effort addition to other dental methods"],
                ["Dental Wipes", "Moderate", "Moderate (requires mouth access)", "Daily or alternate days", "Dogs uncomfortable with brushes; quick surface clean"],
                ["Professional Veterinary Cleaning", "Highest (below gum line)", "Requires anaesthesia", "Annually or as recommended", "All dogs as part of long-term dental health plan"],
            ],
            "Dental care comparison")

def _table_joint_supplements():
    return ("Joint Supplement Ingredients",
            ["Ingredient", "Primary Action", "Evidence Level", "Onset Time", "Best For"],
            [
                ["Glucosamine HCl", "Supports cartilage repair", "Moderate (widely used)", "4-6 weeks", "Early-stage joint support; preventive use in large breeds"],
                ["Chondroitin Sulphate", "Slows cartilage breakdown", "Moderate (often paired with glucosamine)", "4-6 weeks", "Paired with glucosamine for comprehensive joint support"],
                ["Omega-3 (EPA/DHA)", "Reduces joint inflammation", "Strong (well-researched)", "2-4 weeks", "Dogs with inflammatory joint conditions; overall health benefit"],
                ["Green-Lipped Mussel", "Anti-inflammatory + joint lubrication", "Moderate", "4-8 weeks", "Natural supplement preference; mild to moderate joint stiffness"],
                ["MSM (Methylsulfonylmethane)", "Reduces pain and swelling", "Limited but promising", "2-4 weeks", "Supplementary relief alongside primary joint supplements"],
            ],
            "Joint supplement comparison")

def _table_skin_allergy():
    return ("Dog Skin and Allergy Care Options",
            ["Treatment Type", "Active Approach", "Application", "Speed of Relief", "Best For"],
            [
                ["Medicated Shampoo", "Antimicrobial/antifungal cleansing", "Bath every 1-2 weeks", "Immediate soothing; ongoing improvement", "Bacterial or fungal skin infections; hot spots"],
                ["Oatmeal Bath", "Soothing and moisturising", "Bath as needed", "Immediate itch relief", "Mild dry skin; environmental irritation"],
                ["Omega-3 Supplement", "Reduces inflammatory response", "Daily oral supplement", "2-4 weeks", "Chronic skin conditions; coat quality improvement"],
                ["Antihistamine (vet-directed)", "Blocks histamine response", "Oral tablet as directed", "30-60 minutes", "Seasonal allergies; acute allergic reactions"],
                ["Elimination Diet", "Identifies food allergens", "8-12 week trial", "Weeks to months", "Suspected food allergies; chronic ear/skin issues"],
            ],
            "Skin and allergy care comparison")

def _table_digestive_health():
    return ("Dog Digestive Health Aids",
            ["Aid Type", "Mechanism", "Form", "Onset", "Best For"],
            [
                ["Probiotic Supplement", "Restores beneficial gut bacteria", "Powder, chew, or paste", "1-2 weeks", "Post-antibiotic recovery; chronic loose stools"],
                ["Prebiotic Fibre", "Feeds beneficial gut bacteria", "Powder additive or treats", "1-2 weeks", "Supporting probiotic effectiveness; overall gut health"],
                ["Pumpkin Puree (plain)", "Adds soluble fibre", "Mixed into food", "24-48 hours", "Mild diarrhoea or constipation; gentle, natural approach"],
                ["Digestive Enzyme Supplement", "Aids nutrient breakdown", "Powder or tablet with meals", "Within days", "Dogs with pancreatic insufficiency; poor nutrient absorption"],
                ["Bland Diet (vet-directed)", "Rests digestive system", "Boiled chicken + rice", "24-48 hours", "Acute stomach upset; transitional recovery diet"],
            ],
            "Digestive health comparison")

def _table_senior_dog_health():
    return ("Senior Dog Health Support Options",
            ["Health Area", "Approach", "Starting Age", "Frequency", "Best For"],
            [
                ["Joint Support", "Glucosamine + omega-3 supplement", "7+ years (5+ for large breeds)", "Daily", "Maintaining mobility; preventing stiffness"],
                ["Cognitive Health", "MCT oil or cognitive supplement", "8+ years", "Daily with meals", "Dogs showing confusion or behaviour changes"],
                ["Dental Monitoring", "Soft dental chews + vet cleaning", "Throughout life, increase vigilance", "Daily chews; annual vet clean", "Preventing tooth loss and pain"],
                ["Weight Management", "Reduced-calorie senior food", "When activity decreases", "Ongoing with regular weigh-ins", "Preventing obesity-related joint strain"],
                ["Regular Vet Checks", "Biannual wellness exams", "7+ years", "Every 6 months", "Early detection of age-related conditions"],
            ],
            "Senior dog health comparison")

def _table_supplements_overview():
    return ("Common Dog Supplements",
            ["Supplement", "Primary Benefit", "Common Form", "Veterinary Guidance", "Best For"],
            [
                ["Omega-3 Fish Oil", "Skin, coat, and joint health", "Liquid or soft gel", "Generally safe; dose by weight", "Dogs with dry skin, dull coat, or joint stiffness"],
                ["Glucosamine/Chondroitin", "Joint cartilage support", "Chewable tablet or powder", "Recommended for at-risk breeds", "Large breeds; senior dogs; active dogs"],
                ["Probiotics", "Gut microbiome balance", "Powder, chew, or paste", "Safe for most dogs", "Digestive issues; post-antibiotic recovery"],
                ["Multivitamin", "Nutritional gap coverage", "Chewable treat", "Only if diet incomplete", "Home-cooked diets; picky eaters"],
                ["Calming Supplement", "Anxiety and stress reduction", "Chew or liquid", "Consult vet if on medication", "Noise phobia; separation anxiety; travel stress"],
            ],
            "Dog supplements overview")

def _table_anxiety_aids():
    return ("Dog Anxiety and Calming Aids",
            ["Aid Type", "Mechanism", "Onset", "Duration", "Best For"],
            [
                ["Pressure Wrap (ThunderShirt-type)", "Gentle constant pressure", "Minutes", "While worn", "Storm/firework anxiety; travel; vet visits"],
                ["Calming Supplement (L-theanine based)", "Promotes relaxation without sedation", "30-60 minutes", "4-6 hours", "Mild anxiety; situational stress"],
                ["DAP Diffuser (pheromone)", "Mimics nursing mother pheromone", "Hours to days", "Continuous (refill monthly)", "Separation anxiety; new home adjustment"],
                ["Calming Music/White Noise", "Masks startling sounds", "Immediate", "While playing", "Noise sensitivity; alone-time background"],
                ["Puzzle Toys / Lick Mats", "Redirects focus; promotes calming licking", "Immediate engagement", "20-60 minutes", "Separation anxiety; crate training; vet waiting rooms"],
            ],
            "Anxiety aids comparison")

def _table_health_general():
    return ("Preventive Health Checklist by Age",
            ["Health Area", "Puppy (0-1 year)", "Adult (1-7 years)", "Senior (7+ years)", "Best For"],
            [
                ["Vaccinations", "Core series + boosters", "Annual or triennial boosters", "Continue on vet schedule", "Disease prevention at every life stage"],
                ["Parasite Prevention", "Start at 8-12 weeks", "Year-round monthly treatment", "Year-round; adjust for mobility", "Flea, tick, and worm protection"],
                ["Dental Care", "Introduce brushing early", "Daily brushing + annual vet check", "Biannual vet check; softer chews", "Preventing periodontal disease"],
                ["Nutrition", "Growth-formula puppy food", "Maintenance adult food", "Senior formula with joint support", "Meeting changing metabolic needs"],
                ["Vet Visits", "Monthly until 16 weeks, then biannual", "Annual wellness exam", "Every 6 months", "Early detection and ongoing monitoring"],
            ],
            "Preventive health by age")

def _table_training_treats():
    return ("Training Treat Comparison",
            ["Treat Type", "Calories", "Size", "Aroma", "Best For"],
            [
                ["Commercial Training Treats", "Low (2-5 per treat)", "Pea-sized", "Moderate", "Repetitive training sessions; portion control"],
                ["Freeze-Dried Meat", "Moderate", "Break to pea-sized", "High (strong meat scent)", "High-value reward; distraction training; recall"],
                ["Regular Kibble", "Very Low (from daily ration)", "Standard kibble size", "Low", "Low-distraction environments; weight-conscious dogs"],
                ["Soft Commercial Treats", "Low to Moderate", "Tear to small pieces", "Moderate to High", "Puppies; senior dogs; fast consumption needed"],
                ["Fresh Vegetables (carrot, green bean)", "Very Low", "Small dice", "Low", "Weight management; dogs not strongly food-motivated"],
            ],
            "Training treats comparison")

def _table_training_leashes():
    return ("Training Leash Types",
            ["Leash Type", "Length", "Material", "Control Level", "Best For"],
            [
                ["Standard Fixed (1.8m)", "1.8 metres", "Nylon or leather", "Good", "Everyday walks; basic obedience training"],
                ["Long Line (5-10m)", "5-10 metres", "Lightweight nylon", "Moderate (distance work)", "Recall training; off-lead practice in safe areas"],
                ["Short Traffic Lead (0.6m)", "0.6 metres", "Nylon or leather", "Very High", "Crowded areas; heel training; vet visits"],
                ["Hands-Free Waist Leash", "1.2-1.8 metres", "Nylon with waist belt", "Moderate", "Joggers; multi-tasking dog walks"],
                ["Double-Handle Leash", "1.8 metres with extra handle", "Nylon", "High (two grip points)", "Dogs that need occasional close control; reactive dog management"],
            ],
            "Training leash comparison")

def _table_training_methods():
    return ("Dog Training Method Comparison",
            ["Method", "Core Principle", "Tools Used", "Learning Speed", "Best For"],
            [
                ["Positive Reinforcement", "Reward desired behaviours", "Treats, toys, praise", "Moderate to Fast", "All dogs; puppies; building enthusiasm and trust"],
                ["Clicker Training", "Mark exact moment of correct behaviour", "Clicker + treats", "Fast (precise communication)", "Trick training; shaping complex behaviours"],
                ["Lure-Reward", "Guide with food lure, then reward", "High-value treats", "Fast for basic commands", "Puppies; teaching sit, down, spin, and similar positions"],
                ["Capturing", "Reward naturally occurring behaviours", "Treats (always ready)", "Slow but durable", "Calm behaviours; settle; eye contact; natural habits"],
                ["Shaping", "Reward successive approximations", "Clicker + treats", "Moderate", "Complex or creative behaviours; confident learners"],
            ],
            "Training methods comparison")

def _table_puppy_training():
    return ("Puppy Training Milestones",
            ["Age Range", "Focus Skills", "Session Length", "Key Approach", "Best For"],
            [
                ["8-10 weeks", "Name recognition, hand targeting, crate introduction", "2-3 minutes", "Lure-reward with high-value treats", "Building first positive associations with training"],
                ["10-12 weeks", "Sit, recall basics, toilet routine", "3-5 minutes", "Frequent short sessions throughout day", "Establishing core habits before socialisation window closes"],
                ["12-16 weeks", "Down, stay (brief), leash introduction, socialisation", "5-7 minutes", "Positive exposure to varied environments", "Building confidence alongside basic obedience"],
                ["4-6 months", "Reliable recall, loose-leash walking, impulse control", "10 minutes", "Gradual distraction increase; real-world practice", "Transitioning skills from home to public environments"],
                ["6-12 months", "Proofing all commands, adolescent boundary testing", "10-15 minutes", "Consistency; revisit basics; increase criteria slowly", "Maintaining reliability through adolescent regression"],
            ],
            "Puppy training milestones")

def _table_crate_training():
    return ("Crate Training Approaches",
            ["Phase", "Duration", "Goal", "Technique", "Best For"],
            [
                ["Introduction", "Day 1-3", "Positive crate association", "Treats tossed in; door open; meals near crate", "All puppies; fearful rescues (go slower)"],
                ["Short Enclosure", "Day 3-7", "Calm with door closed briefly", "Close door for 10-30 seconds; treat; open", "Building tolerance gradually"],
                ["Gradual Duration", "Week 2-3", "Settle for 5-30 minutes", "Kong or chew inside; step out of sight briefly", "Progressing to unsupervised short periods"],
                ["Nap and Night Use", "Week 3-4", "Sleep in crate overnight", "Crate in bedroom; last toilet break before bed", "Overnight house-training support"],
                ["Maintenance", "Ongoing", "Voluntary crate use as safe space", "Door open; treats occasionally; never used as punishment", "Lifelong positive crate relationship"],
            ],
            "Crate training comparison")

def _table_agility_equipment():
    return ("Agility Equipment for Beginners",
            ["Equipment", "Skill Taught", "Space Needed", "DIY Possible", "Best For"],
            [
                ["Jump Bars (adjustable)", "Jumping, timing, direction", "3-4 metres", "Yes (PVC pipes)", "Foundation obstacle; all agility dogs"],
                ["Tunnel (collapsible)", "Confidence, speed, direction changes", "5-6 metres straight line", "Affordable commercial options", "Building boldness; fun for energetic dogs"],
                ["Weave Poles (6-12)", "Body awareness, focus, handler communication", "3-6 metres", "Yes (garden stakes)", "Advanced skill; requires patience to teach"],
                ["Pause Table", "Impulse control, position holds", "1 square metre", "Yes (sturdy low platform)", "Teaching wait; competition preparation"],
            ],
            "Agility equipment comparison")

def _table_puzzle_toys():
    return ("Dog Puzzle Toy Difficulty Levels",
            ["Difficulty", "Mechanism", "Time to Solve", "Supervision", "Best For"],
            [
                ["Beginner", "Single action (push, slide, or flip)", "2-5 minutes", "Minimal", "Puppies; dogs new to puzzles; confidence building"],
                ["Intermediate", "Two-step sequence (slide then lift)", "5-15 minutes", "Minimal", "Dogs that solved beginner puzzles quickly"],
                ["Advanced", "Multi-step with sequential locks", "15-30 minutes", "Recommended", "Experienced puzzle dogs; high-intelligence breeds"],
                ["Treat-Stuffed (frozen)", "Licking and chewing extraction", "20-60 minutes", "Minimal", "Long-lasting calm activity; separation anxiety aid"],
                ["DIY / Rotation", "Varied household items (muffin tin, towel roll)", "5-15 minutes", "Recommended", "Budget-friendly enrichment; daily novelty"],
            ],
            "Puzzle toy difficulty comparison")

def _table_chew_toys():
    return ("Chew Toy Material Comparison",
            ["Material", "Durability", "Safety Profile", "Dental Benefit", "Best For"],
            [
                ["Natural Rubber (solid)", "High", "Non-toxic; monitor for small pieces", "Moderate gum massage", "Power chewers; daily unsupervised chewing"],
                ["Nylon / Polymer", "Very High", "Generally safe; discard when worn", "Gentle tooth scraping", "Aggressive chewers; long-lasting option"],
                ["Rope (cotton/hemp)", "Moderate", "Supervise (ingestion risk if shredded)", "Flossing action between teeth", "Tug-and-chew play; supervised sessions only"],
                ["Antler (split or whole)", "Very High", "Hard (tooth fracture risk if whole)", "None to Moderate", "Moderate chewers; long-lasting natural option"],
                ["Bully Stick / Tendon", "Moderate (fully consumable)", "Digestible; supervise for choking", "Moderate scraping action", "Treat-chew hybrid; food-motivated dogs"],
            ],
            "Chew toy material comparison")

def _table_fetch_toys():
    return ("Fetch Toy Comparison",
            ["Toy Type", "Material", "Throw Distance", "Visibility", "Best For"],
            [
                ["Tennis Ball", "Felt-covered rubber", "Moderate", "High (bright yellow)", "Standard fetch; most dogs; short to medium distances"],
                ["Rubber Ball (solid)", "Natural or synthetic rubber", "Moderate to Far", "Moderate (varies by colour)", "Power chewers; wet conditions; durable option"],
                ["Ball Launcher", "Plastic arm + lightweight ball", "Very Far", "High", "Large open spaces; dogs needing extended runs"],
                ["Frisbee (soft rubber)", "Flexible rubber", "Far (gliding)", "Moderate", "Dogs that enjoy aerial catches; joint-friendly landing"],
                ["Floating Fetch Toy", "Buoyant rubber or foam", "Moderate", "High (bright colours)", "Water-loving dogs; lake, river, or pool fetch"],
            ],
            "Fetch toy comparison")

def _table_tug_toys():
    return ("Tug Toy Options",
            ["Toy Type", "Material", "Durability", "Grip", "Best For"],
            [
                ["Braided Rope", "Cotton or hemp", "Moderate", "Firm knot handles", "General tug play; multiple dogs"],
                ["Rubber Tug Ring", "Natural rubber", "High", "Easy grip for dog and owner", "Power tuggers; dogs that shred fabric"],
                ["Fire Hose Tug", "Recycled fire hose fabric", "Very High", "Flat, easy-grip", "Strong dogs; outdoor play"],
                ["Bungee Tug", "Elastic core with fleece/nylon cover", "Moderate to High", "Padded handle for owner", "Joint-friendly tug; reducing impact on teeth"],
                ["Fleece Strip Tug", "Braided fleece strips", "Low to Moderate", "Soft for gentle mouths", "Puppies; gentle players; tug training introduction"],
            ],
            "Tug toy comparison")

def _table_puppy_toys():
    return ("Puppy Toy Guide by Teething Stage",
            ["Teething Stage", "Age", "Toy Type", "Material", "Best For"],
            [
                ["Early Teething", "8-12 weeks", "Soft rubber chew ring", "Flexible, gentle rubber", "Soothing early gum discomfort; safe for baby teeth"],
                ["Active Teething", "12-20 weeks", "Frozen rubber toy (fill with broth)", "Textured rubber", "Numbing sore gums; encouraging appropriate chewing"],
                ["Peak Teething", "4-6 months", "Multi-texture chew toy", "Rubber + rope combination", "Varied surface for different erupting teeth"],
                ["Post-Teething", "6-8 months", "Standard puppy chew + interactive toy", "Durable rubber", "Transitioning to adult chew habits"],
                ["Social Play", "All puppy ages", "Tug rope + fetch ball", "Soft rope + lightweight ball", "Building play skills; human-dog bonding"],
            ],
            "Puppy toys by teething stage")

def _table_treat_dispensing_toys():
    return ("Treat-Dispensing Toy Comparison",
            ["Toy Type", "Fill Options", "Duration", "Difficulty", "Best For"],
            [
                ["Classic Stuffable (cone shape)", "Kibble, peanut butter, banana, freeze", "15-60 minutes", "Adjustable by packing/freezing", "Separation anxiety; crate time; all dogs"],
                ["Rolling Dispenser Ball", "Kibble or small treats", "10-30 minutes", "Easy (gravity-fed)", "Meal replacement; overweight dogs; boredom busting"],
                ["Wobble Base Dispenser", "Kibble", "10-20 minutes", "Easy to Moderate", "Dogs that push and paw; floor play"],
                ["Puzzle Slider Board", "Small treats", "5-15 minutes", "Moderate to Hard", "Smart breeds; dogs that need cognitive challenge"],
                ["Suction Cup Lick Pad", "Soft paste, yoghurt, pumpkin", "10-30 minutes", "Easy", "Bath time distraction; grooming; calming activity"],
            ],
            "Treat-dispensing toys comparison")

def _table_water_toys():
    return ("Water-Safe Dog Toys",
            ["Toy Type", "Buoyancy", "Visibility in Water", "Material", "Best For"],
            [
                ["Floating Rubber Ball", "High (stays on surface)", "High (bright orange/yellow)", "Buoyant rubber", "Pool or lake fetch; confident swimmers"],
                ["Floating Rope Toy", "High", "Moderate (coloured rope)", "Foam core + rope", "Tug and fetch in shallow water"],
                ["Neoprene Frisbee", "High", "High (neon colours)", "Neoprene fabric", "Gliding water fetch; beach play"],
                ["Bumper/Dummy (training)", "High", "High (hunter orange)", "Canvas or rubber", "Retriever training; dock diving practice"],
            ],
            "Water toys comparison")

def _table_scent_enrichment():
    return ("Scent and Nosework Enrichment",
            ["Activity", "Setup Time", "Engagement Duration", "Difficulty", "Best For"],
            [
                ["Snuffle Mat", "1-2 minutes (scatter kibble)", "10-20 minutes", "Easy", "All dogs; mealtime enrichment; slowing fast eaters"],
                ["Scent Trail (treats)", "5 minutes (lay trail)", "5-15 minutes", "Moderate", "Dogs with high prey drive; garden enrichment"],
                ["Muffin Tin Puzzle", "2 minutes (treats under balls)", "5-10 minutes", "Easy to Moderate", "Beginner nosework; minimal equipment needed"],
                ["Box Search", "3-5 minutes (hide treat in one box)", "5-10 minutes", "Moderate", "Introducing formal nosework; confidence building"],
                ["Essential Oil Scent ID", "10 minutes (prepare scent stations)", "15-30 minutes per session", "Advanced", "Competitive nosework training; highly focused dogs"],
            ],
            "Scent enrichment comparison")

def _table_comfort_toys():
    return ("Comfort and Calming Toys",
            ["Toy Type", "Calming Mechanism", "Washability", "Durability", "Best For"],
            [
                ["Heartbeat Plush", "Simulated heartbeat vibration", "Surface wash; remove mechanism first", "Low (not for chewers)", "New puppies away from litter; anxious dogs at night"],
                ["Weighted Plush", "Gentle pressure (like a lap)", "Removable cover washable", "Moderate", "Small dogs with anxiety; crate comfort"],
                ["Lavender-Scented Toy", "Calming scent association", "Machine washable (scent fades)", "Moderate", "Mild anxiety; travel; vet visits"],
                ["Lick Mat (frozen filling)", "Repetitive licking releases endorphins", "Dishwasher safe (silicone)", "High", "Bath anxiety; alone time; general calming"],
                ["Familiar Fabric Toy", "Owner's scent on fabric", "Machine washable", "Low to Moderate", "Separation anxiety; boarding/daycare"],
            ],
            "Comfort toys comparison")

def _table_senior_dog_toys():
    return ("Toys for Senior Dogs",
            ["Toy Type", "Physical Demand", "Engagement Type", "Joint Impact", "Best For"],
            [
                ["Soft Plush Toy", "Very Low", "Comfort and gentle mouthing", "None", "Dogs with weakened jaws; comfort seeking"],
                ["Slow-Release Treat Toy", "Low", "Licking and gentle chewing", "None", "Cognitive stimulation; dogs with limited mobility"],
                ["Gentle Tug Toy (fleece)", "Low to Moderate", "Interactive with owner", "Minimal", "Maintaining play bond; gentle strength use"],
                ["Easy Puzzle (single step)", "Low", "Cognitive; nose and paw", "None", "Mental sharpness; dogs with reduced vision/hearing"],
                ["Floating Toy (if swimmer)", "Moderate", "Water-based low-impact fetch", "Very Low (buoyancy supports)", "Dogs that still enjoy water; joint-friendly exercise"],
            ],
            "Senior dog toys comparison")

def _table_toy_rotation():
    return ("Toy Rotation Strategy",
            ["Rotation Group", "Toys Available", "Duration", "When to Rotate", "Best For"],
            [
                ["Group A (Active)", "Fetch ball, tug rope, frisbee", "3-4 days", "When interest visibly drops", "High-energy play days; outdoor time"],
                ["Group B (Cognitive)", "Puzzle feeder, snuffle mat, treat ball", "3-4 days", "When solving speed plateaus", "Mental enrichment; indoor days"],
                ["Group C (Comfort)", "Plush toy, chew toy, lick mat", "3-4 days", "When dog ignores them", "Calm evenings; alone time"],
                ["Permanent (Always Out)", "One favourite comfort item", "Always available", "Never removed", "Security object; sleeping companion"],
                ["Novel (Weekly Wild Card)", "One completely new or rarely seen toy", "1-2 days", "Return to storage after brief use", "Spike of novelty and excitement"],
            ],
            "Toy rotation strategy")

def _table_diy_enrichment():
    return ("DIY Enrichment Activities",
            ["Activity", "Materials", "Setup Time", "Engagement", "Best For"],
            [
                ["Towel Roll-Up", "Old towel + treats", "2 minutes", "5-10 minutes", "Beginners; dogs new to problem-solving"],
                ["Cardboard Box Dig", "Cardboard box + crumpled paper + treats", "3 minutes", "10-15 minutes", "Dogs that enjoy digging; terriers"],
                ["Muffin Tin Puzzle", "Muffin tin + tennis balls + treats", "2 minutes", "5-10 minutes", "Visual and scent problem-solving"],
                ["Frozen Lick Plate", "Plate + yoghurt + kibble (freeze)", "5 min prep + 2 hr freeze", "15-30 minutes", "Calming; hot days; slow feeding"],
                ["Bottle Spinner", "Plastic bottle on dowel rod", "10 minutes to build", "10-20 minutes", "Paw-dexterous dogs; ongoing challenge"],
            ],
            "DIY enrichment comparison")

def _table_overstimulation_recovery():
    return ("Calming Techniques After Overexcitement",
            ["Technique", "Action", "Duration", "Effectiveness", "Best For"],
            [
                ["Calm Isolation", "Move to quiet room; no interaction", "5-10 minutes", "High (removes stimuli)", "Dogs that escalate with attention during excitement"],
                ["Lick Mat / Frozen Treat", "Offer lick-based calming activity", "10-20 minutes", "High (licking releases calming hormones)", "Redirecting energy into soothing repetitive action"],
                ["Structured Sniffing Walk", "Slow leash walk focused on sniffing", "10-15 minutes", "Moderate to High", "Dogs that settle through sensory grounding"],
                ["Gentle Massage", "Slow, firm strokes along body", "5-10 minutes", "Moderate", "Dogs that enjoy physical contact; bonding-based calming"],
                ["Crate with Chew", "Voluntary crate entry with long-lasting chew", "15-30 minutes", "High", "Dogs crate-trained; predictable decompression routine"],
            ],
            "Overstimulation recovery comparison")

def _table_toy_types_overview():
    return ("Dog Toy Categories Overview",
            ["Toy Category", "Primary Purpose", "Supervision Level", "Durability", "Best For"],
            [
                ["Chew Toys", "Satisfying natural chew drive", "Minimal to Moderate", "High", "All dogs; teething puppies; stress relief"],
                ["Fetch Toys", "Physical exercise and retrieval instinct", "Required during play", "Moderate to High", "Active dogs; outdoor play sessions"],
                ["Puzzle / Treat Toys", "Mental stimulation and problem-solving", "Minimal", "Moderate to High", "Intelligent breeds; indoor enrichment; food-motivated dogs"],
                ["Tug Toys", "Interactive play with owner or other dogs", "Required during play", "Moderate", "Social dogs; bonding; controlled energy release"],
                ["Comfort / Plush Toys", "Emotional security and gentle mouthing", "Moderate (check for tearing)", "Low to Moderate", "Anxious dogs; gentle players; nighttime comfort"],
            ],
            "Dog toy types overview")

def _table_ortho_beds():
    return ("Orthopaedic Dog Bed Comparison",
            ["Bed Type", "Fill Material", "Support Level", "Firmness", "Best For"],
            [
                ["Memory Foam (solid)", "High-density memory foam", "Excellent joint relief", "Medium-Firm", "Arthritic dogs; post-surgery recovery; senior dogs"],
                ["Egg-Crate Foam", "Contoured foam with peaks", "Good pressure distribution", "Medium", "Dogs with hip dysplasia; lightweight senior dogs"],
                ["Gel-Infused Memory Foam", "Memory foam + cooling gel", "Excellent + temperature regulation", "Medium-Firm", "Dogs that overheat; warm climates; thick-coated breeds"],
                ["Bolster Orthopaedic", "Memory foam base + bolster edges", "Excellent + head/neck support", "Medium", "Dogs that lean or rest head on edges; nesting preference"],
                ["Elevated / Cot Style", "Suspended fabric (no fill)", "Moderate (even weight distribution)", "Firm (taut surface)", "Dogs needing airflow underneath; warm climates; outdoor use"],
            ],
            "Orthopaedic bed comparison")

def _table_outdoor_beds():
    return ("Outdoor and Travel Dog Beds",
            ["Bed Type", "Material", "Portability", "Weather Resistance", "Best For"],
            [
                ["Elevated Cot", "Metal frame + breathable fabric", "Foldable; moderate weight", "Rain-draining; UV-resistant fabric", "Garden lounging; camping; warm-weather outdoor rest"],
                ["Roll-Up Travel Mat", "Waterproof nylon + thin foam", "Very portable; lightweight", "Water-resistant outer", "Hiking; car travel; visiting friends"],
                ["Self-Inflating Pad", "Air + foam hybrid", "Compact when deflated", "Water-resistant", "Camping; backpacking with dogs"],
                ["Waterproof Bolster Bed", "Waterproof fabric + polyfill", "Semi-portable", "Fully waterproof cover", "Muddy dogs; damp environments; kennel runs"],
            ],
            "Outdoor bed comparison")

def _table_durable_beds():
    return ("Chew-Resistant Dog Beds",
            ["Bed Type", "Material", "Chew Resistance", "Comfort Level", "Best For"],
            [
                ["Aluminium Frame Cot", "Ripstop fabric on metal frame", "Very High (minimal chew surface)", "Moderate (firm surface)", "Destructive chewers; kennel use"],
                ["Ballistic Nylon Cover", "Cordura/ballistic nylon over foam", "High (tear-resistant fabric)", "Good (foam underneath)", "Moderate chewers; transitioning from chewing phase"],
                ["Heavy Canvas Bed", "Industrial canvas with reinforced seams", "High", "Moderate to Good", "Working dogs; outdoor/indoor versatile use"],
                ["Rubber Mat", "Solid rubber (kennel-style)", "Very High", "Low (firm surface)", "Heavy-duty kennel use; extreme chewers"],
            ],
            "Chew-resistant bed comparison")

def _table_bed_types():
    return ("Dog Bed Types Comparison",
            ["Bed Style", "Shape", "Best Feature", "Wash Care", "Best For"],
            [
                ["Bolster / Donut", "Round/oval with raised edges", "Head and neck support", "Removable cover, machine washable", "Dogs that curl up; anxious dogs seeking enclosed feeling"],
                ["Flat Mat / Cushion", "Rectangular pad", "Versatile placement", "Fully machine washable", "Dogs that sprawl; warm climates; crate liners"],
                ["Memory Foam Mattress", "Rectangular slab", "Orthopaedic joint support", "Removable waterproof cover", "Senior dogs; large breeds; post-surgery recovery"],
                ["Elevated Cot", "Raised platform on legs", "Air circulation; joint support", "Wipe clean; fabric removable", "Outdoor use; hot climates; dogs with skin conditions"],
                ["Cave / Hooded", "Enclosed with hood or flap", "Privacy and warmth", "Removable cover, machine washable", "Anxious dogs; small breeds; cold environments"],
            ],
            "Dog bed types comparison")

def _table_grain_options():
    return ("Grain vs. Grain-Free Dog Food",
            ["Factor", "Grain-Inclusive", "Grain-Free", "Limited Ingredient", "Best For"],
            [
                ["Carb Source", "Rice, oats, barley", "Potato, pea, lentil", "Single carb (e.g., sweet potato)", "Matching digestive tolerance"],
                ["Fibre Content", "Moderate to High", "Varies widely", "Controlled", "Dogs needing specific fibre levels"],
                ["Allergy Suitability", "Not for grain-allergic dogs", "Avoids grain allergens", "Eliminates multiple allergens", "Dogs with confirmed food sensitivities"],
                ["Regulatory Notes", "Traditional formulation", "FDA investigation ongoing (DCM link)", "Vet-recommended for allergies", "Discussing options with veterinarian"],
                ["Cost Range", "Budget to Mid", "Mid to Premium", "Mid to Premium", "Balancing budget with dietary needs"],
            ],
            "Grain options comparison")

def _table_puppy_food():
    return ("Puppy Food Selection Guide",
            ["Factor", "Small Breed Puppy", "Medium Breed Puppy", "Large Breed Puppy", "Best For"],
            [
                ["Calorie Density", "Higher (fast metabolism)", "Moderate", "Controlled (prevent rapid growth)", "Matching energy to growth rate"],
                ["Kibble Size", "Very Small", "Small to Medium", "Medium to Large", "Ensuring comfortable eating and chewing"],
                ["Calcium Level", "Standard", "Standard", "Controlled (lower %)", "Preventing skeletal issues in large breeds"],
                ["Feeding Frequency", "3-4 times daily", "3 times daily", "3 times daily (measured)", "Supporting steady energy and growth"],
                ["Transition to Adult", "10-12 months", "12 months", "12-18 months", "Timing the switch to adult formula appropriately"],
            ],
            "Puppy food comparison")

def _table_senior_food():
    return ("Senior Dog Nutrition Comparison",
            ["Nutrient Focus", "Standard Adult Food", "Senior Formula", "Therapeutic/Prescription", "Best For"],
            [
                ["Calorie Level", "Maintenance", "Reduced (10-20% less)", "Targeted to condition", "Matching intake to decreased activity"],
                ["Protein", "Standard (22-28%)", "Maintained or slightly higher", "Condition-specific", "Preserving muscle mass in aging dogs"],
                ["Joint Support", "None added", "Glucosamine + chondroitin added", "Therapeutic levels", "Proactive and reactive joint care"],
                ["Fibre", "Standard", "Increased for digestion", "Targeted", "Supporting slower digestive transit"],
                ["Antioxidants", "Standard", "Enhanced (vitamins E, C)", "Condition-specific", "Supporting cognitive and immune health"],
            ],
            "Senior dog nutrition comparison")

def _table_food_types():
    return ("Dog Food Format Comparison",
            ["Format", "Moisture Content", "Shelf Life", "Palatability", "Best For"],
            [
                ["Dry Kibble", "6-10%", "12-18 months (sealed)", "Moderate", "Cost-effective daily feeding; dental crunch benefit"],
                ["Wet / Canned", "70-85%", "2-5 years (sealed)", "High", "Picky eaters; dogs needing hydration; senior dogs"],
                ["Semi-Moist", "25-35%", "6-12 months", "High", "Training rewards; transitional feeding"],
                ["Freeze-Dried Raw", "Under 5%", "12-24 months", "Very High", "Raw-diet convenience; travel; meal toppers"],
                ["Fresh / Refrigerated", "60-80%", "7-14 days (refrigerated)", "Very High", "Maximum freshness preference; dogs with digestive sensitivity"],
            ],
            "Dog food format comparison")

def _table_puppy_essentials():
    return ("Puppy Essential Supplies Checklist",
            ["Category", "Essential Item", "When Needed", "Replace Frequency", "Best For"],
            [
                ["Feeding", "Size-appropriate food and water bowls", "Day 1", "When outgrown or damaged", "Stable, non-tip feeding setup"],
                ["Sleep", "Crate + washable crate pad", "Day 1", "Pad: when soiled; Crate: when outgrown", "Safe sleeping and house-training tool"],
                ["Toilet", "Puppy pads or outdoor toilet area", "Day 1", "Pads: after each use", "House-training support in early weeks"],
                ["Play", "2-3 age-appropriate toys (chew, tug, comfort)", "Day 1", "When damaged or outgrown", "Healthy chewing habits; preventing furniture damage"],
                ["Safety", "Collar/harness + ID tag + microchip", "Day 1 (collar); 8+ weeks (microchip)", "Collar: when outgrown", "Identification and safe outdoor access"],
            ],
            "Puppy essentials comparison")

def _table_large_breed_beds():
    return ("Beds for Large Breeds",
            ["Bed Type", "Weight Capacity", "Support Type", "Key Feature", "Best For"],
            [
                ["High-Density Memory Foam", "45-70 kg", "Full orthopaedic", "4+ inch thick foam slab", "Giant breeds; arthritic large dogs"],
                ["Bolster Memory Foam", "35-55 kg", "Orthopaedic + headrest", "Raised edges for head support", "Large dogs that lean on edges; Labradors, Goldens"],
                ["Elevated XL Cot", "50+ kg", "Even weight distribution", "Raised for joint relief + airflow", "Hot climates; large outdoor dogs"],
                ["Waterproof Mattress", "40-60 kg", "Firm foam", "Easy-clean waterproof cover", "Droolers; incontinent seniors; messy drinkers"],
            ],
            "Large breed bed comparison")

def _table_large_breed_toys():
    return ("Toys for Large Dogs",
            ["Toy Type", "Size", "Durability Rating", "Material", "Best For"],
            [
                ["XL Rubber Ball", "10+ cm diameter", "Very High", "Solid natural rubber", "Fetch-loving large dogs; jaw-safe size"],
                ["Heavy-Duty Tug Rope", "60+ cm length", "High", "Thick cotton or fire hose", "Strong tuggers; multi-dog households"],
                ["Large Treat Dispenser", "15+ cm", "Very High", "Thick rubber", "Mental stimulation; power chewers"],
                ["Giant Plush (reinforced)", "45+ cm", "Moderate (double-stitched)", "Reinforced fabric, minimal stuffing", "Gentle large dogs; comfort carrying"],
                ["Oversized Frisbee", "25+ cm", "High", "Flexible rubber", "Athletic large dogs; open-field play"],
            ],
            "Large breed toys comparison")

def _table_large_breed_gear():
    return ("Gear Essentials for Large Breeds",
            ["Gear Category", "Key Requirement", "Material", "Sizing Tip", "Best For"],
            [
                ["Harness", "Wide chest plate; strong D-rings", "Reinforced nylon or leather", "Measure girth behind front legs", "Distributing pulling force; trachea protection"],
                ["Collar", "2.5+ cm wide; strong buckle", "Leather or padded nylon", "Two-finger gap when fastened", "ID tag; brief leash attachment; training"],
                ["Leash", "1.8m+; thick webbing or leather", "Leather or heavy nylon", "Comfortable handle width for grip", "Reliable control during walks"],
                ["Bed", "Orthopaedic memory foam; XL size", "High-density foam + washable cover", "Dog should fit fully stretched out", "Joint support; quality rest"],
                ["Travel Crate", "Airline-rated large/XL", "Heavy-duty plastic or aluminium", "Dog stands and turns comfortably", "Safe transport; home den"],
            ],
            "Large breed gear comparison")

def _table_small_breed_gear():
    return ("Gear Essentials for Small Breeds",
            ["Gear Category", "Key Requirement", "Safety Note", "Sizing Tip", "Best For"],
            [
                ["Harness", "Lightweight; step-in or vest style", "Avoid neck pressure (trachea risk)", "Snug but two-finger gap", "Trachea protection; toy and small breeds"],
                ["Collar", "1-1.5 cm wide; lightweight", "Breakaway option for safety", "Measure neck; lightest buckle possible", "ID tag only; not for leash attachment"],
                ["Leash", "1.2-1.5m; thin webbing", "Retractable only in safe, open areas", "Comfortable lightweight clip", "Short walks; controlled distances"],
                ["Carrier", "Airline-approved soft-sided", "Ventilation on all sides", "Dog stands and turns inside", "Vet visits; travel; public transport"],
                ["Bed", "Small donut or cave style", "Low entry point", "Cosy snug fit; not oversized", "Warmth; security; burrowing instinct"],
            ],
            "Small breed gear comparison")

def _table_winter_gear():
    return ("Winter Gear for Dogs",
            ["Gear Type", "Protection", "Material", "Temperature Range", "Best For"],
            [
                ["Fleece Coat/Jumper", "Mild cold", "Polar fleece", "5-15 degrees C", "Short-coated breeds; indoor-to-outdoor transitions"],
                ["Waterproof Jacket", "Rain and wind", "Nylon with waterproof membrane", "0-10 degrees C", "Wet climates; dogs walked in all weather"],
                ["Insulated Parka", "Severe cold", "Quilted nylon + insulation fill", "Below 0 degrees C", "Hairless/thin-coated breeds; extended outdoor time"],
                ["Dog Boots/Paw Protectors", "Ice, salt, rough terrain", "Rubber sole + neoprene/fabric upper", "Below 5 degrees C or icy conditions", "Dogs walking on salted pavements; ice and snow"],
                ["Snood / Ear Cover", "Ear warmth", "Fleece or knit fabric", "Below 5 degrees C", "Drop-eared breeds prone to ear cold; windy conditions"],
            ],
            "Winter gear comparison")

def _table_grooming_tools():
    return ("Dog Grooming Tools by Coat Type",
            ["Tool", "Coat Type", "Primary Function", "Frequency", "Best For"],
            [
                ["Slicker Brush", "Medium to Long coats", "Detangling and removing loose fur", "2-3 times weekly", "Doodles, Spaniels, Setters; tangle-prone coats"],
                ["Bristle Brush", "Short and Smooth coats", "Distributing natural oils; polishing", "Weekly", "Boxers, Beagles, Dalmatians; low-maintenance coats"],
                ["Undercoat Rake", "Double coats", "Removing dead undercoat", "Weekly during shedding season", "Huskies, German Shepherds, Retrievers"],
                ["Pin Brush", "Long Silky coats", "Gentle daily brushing without breakage", "Daily", "Yorkies, Maltese, Afghan Hounds"],
                ["Deshedding Tool", "Heavy shedders (any length)", "Reaching through topcoat to remove undercoat", "Weekly (more during blowout)", "Heavy shedders; seasonal coat changes"],
            ],
            "Grooming tools comparison")

def _table_collar_leash_types():
    return ("Dog Collar and Leash Types",
            ["Type", "Design", "Control Level", "Safety Feature", "Best For"],
            [
                ["Flat Buckle Collar", "Standard belt-style", "Low (ID purpose)", "Breakaway option available", "Everyday ID tag carrier; well-trained dogs"],
                ["Martingale Collar", "Limited-slip tightening", "Moderate (prevents backing out)", "Cannot fully choke", "Greyhounds; dogs with narrow heads; escape artists"],
                ["Standard Nylon Leash (1.8m)", "Fixed-length webbing", "Good", "None (reliable simplicity)", "Daily walks; training; general use"],
                ["Retractable Leash", "Spring-loaded extending cord", "Variable (user-controlled)", "Lock mechanism", "Trained dogs in open, safe areas only"],
                ["Slip Lead", "Combined collar + leash loop", "Moderate to High", "Tightens when pulled", "Quick on/off for vet visits; experienced handlers"],
            ],
            "Collar and leash comparison")

def _table_outdoor_gear():
    return ("Dog Outdoor Adventure Gear",
            ["Gear Item", "Purpose", "Material", "Essential For", "Best For"],
            [
                ["Hiking Harness", "Secure control on trails", "Padded nylon with handle", "All off-road walks", "Trail-walking dogs; uneven terrain"],
                ["Collapsible Water Bowl", "Hydration on the go", "Silicone or nylon", "Any walk over 30 minutes", "Travel; hiking; park visits"],
                ["Reflective Vest", "Visibility in low light", "Mesh with reflective strips", "Dawn/dusk walks", "Safety on road-adjacent paths"],
                ["Paw Wax", "Paw pad protection", "Natural beeswax blend", "Hot pavement; cold/salt", "Extreme surface temperatures"],
                ["Dog Backpack", "Dog carries own supplies", "Durable nylon with saddle bags", "Multi-hour hikes", "Fit medium-large dogs; weight distribution"],
            ],
            "Outdoor gear comparison")

def _table_safety_comparison():
    return ("Pet Safety Feature Comparison",
            ["Safety Category", "Risk", "Prevention", "Warning Signs", "Best For"],
            [
                ["Toy Safety", "Choking on small parts", "Size-appropriate toys; supervised play", "Gagging, pawing at mouth", "All dogs; especially strong chewers and puppies"],
                ["Food Safety", "Toxic food ingestion", "Secure food storage; educate household", "Vomiting, lethargy, tremors", "Households with children; counter-surfing dogs"],
                ["Home Safety", "Electrical cords; toxic plants; small objects", "Puppy-proof rooms; barrier gates", "Chewing damage; unusual behaviour", "New puppies; curious breeds; unsupervised areas"],
                ["Outdoor Safety", "Traffic; toxic substances; wildlife", "Leash use; recall training; awareness", "Sudden illness after walk; injuries", "All dogs during outdoor activities"],
                ["Water Safety", "Drowning; water intoxication", "Life jacket; supervised swimming; rest breaks", "Fatigue in water; excessive water consumption", "Dogs near pools, lakes, or beaches"],
            ],
            "Pet safety comparison")

def _table_cooling_gear():
    return ("Dog Cooling Gear for Hot Weather",
            ["Cooling Product", "Mechanism", "Duration", "Portability", "Best For"],
            [
                ["Cooling Mat (gel-based)", "Pressure-activated gel absorbs heat", "1-3 hours", "Foldable; moderate weight", "Indoor rest; crate cooling; travel"],
                ["Cooling Vest", "Evaporative cooling (soak in water)", "1-2 hours (re-wet to extend)", "Wearable; lightweight", "Outdoor walks in heat; brachycephalic breeds"],
                ["Elevated Mesh Bed", "Air circulation underneath", "Continuous (passive)", "Foldable; some weight", "Garden lounging; outdoor kennel; permanent setup"],
                ["Frozen Treat Toy", "Internal cold from frozen filling", "20-40 minutes", "Standard toy size", "Entertaining cooling; hydration encouragement"],
                ["Paddling Pool", "Full-body water immersion", "Continuous (while in use)", "Seasonal setup", "Garden use; water-loving breeds; supervised play"],
            ],
            "Cooling gear comparison")

def _table_travel_gear():
    return ("Dog Travel Essentials",
            ["Item", "Purpose", "Type Options", "Key Feature", "Best For"],
            [
                ["Travel Crate", "Safe containment in vehicle", "Hard-shell or soft-sided", "Crash-tested; ventilated", "Car and air travel; safety in transit"],
                ["Car Seat Cover", "Protecting vehicle interior", "Hammock or flat cover", "Waterproof; non-slip base", "Dogs riding on back seat"],
                ["Portable Water Bottle", "Hydration on the go", "Squeeze bottle with trough", "Leak-proof; one-handed use", "Road trips; hikes; park visits"],
                ["Travel Food Container", "Measured meal portions", "Sealable compartment bag or box", "Airtight; portion-marked", "Overnight stays; multi-day trips"],
                ["First Aid Kit", "Emergency wound and illness care", "Pre-packed pet kit", "Bandages, antiseptic, tick tool, vet number", "All travel; remote locations; peace of mind"],
            ],
            "Travel gear comparison")

def _table_cleaning_supplies():
    return ("Pet Cleaning and Maintenance Supplies",
            ["Product Type", "Use Case", "Key Feature", "Frequency", "Best For"],
            [
                ["Enzymatic Cleaner", "Urine/vomit stain and odour", "Enzyme bacteria that break down organics", "As needed (accidents)", "House-training puppies; elderly pet accidents"],
                ["Pet-Safe Disinfectant", "Crate, floor, and surface cleaning", "Non-toxic, no phenols or bleach", "Weekly", "General hygiene; multi-pet households"],
                ["Lint Roller / Fur Remover", "Clothing and furniture fur removal", "Adhesive sheets or rubber", "Daily if needed", "Heavy-shedding breeds; guests visiting"],
                ["Pet Laundry Detergent", "Washing bedding, blankets, toys", "Free from dyes and perfumes", "Weekly bed wash", "Sensitive-skin pets; allergy-prone dogs"],
                ["Paw Wash Cup", "Cleaning muddy paws at door", "Silicone bristles + water chamber", "After every muddy walk", "Rainy climates; light-coloured flooring households"],
            ],
            "Cleaning supplies comparison")

def _table_water_accessories():
    return ("Dog Water and Hydration Accessories",
            ["Accessory", "Type", "Capacity", "Best Feature", "Best For"],
            [
                ["Standard Water Bowl", "Stainless steel or ceramic", "500ml-2L", "Sturdy; dishwasher safe", "Home use; daily hydration"],
                ["Pet Water Fountain", "Electric recirculating", "1.5-3L", "Filtered; encourages drinking", "Cats and dogs reluctant to drink still water"],
                ["Travel Water Bottle", "Squeeze with fold-out trough", "300-600ml", "Portable; leak-proof", "Walks; hikes; car travel"],
                ["Slow-Flow Bowl", "Floating disc or narrow opening", "500ml-1L", "Prevents gulping", "Fast drinkers; dogs that vomit after drinking"],
            ],
            "Water accessories comparison")

def _table_recovery_aids():
    return ("Post-Surgery and Recovery Aids",
            ["Aid Type", "Purpose", "Duration of Use", "Comfort Level", "Best For"],
            [
                ["Elizabethan Cone (E-collar)", "Prevents licking/chewing wounds", "Until wound heals (7-14 days)", "Low (restricts vision/movement)", "Standard wound protection; vet-recommended"],
                ["Inflatable Recovery Collar", "Prevents reaching wounds (not face)", "Until wound heals", "Moderate (less restrictive)", "Body wounds; dogs distressed by hard cones"],
                ["Recovery Suit / Bodysuit", "Covers torso surgical sites", "Until wound heals", "High (like wearing clothes)", "Abdominal surgery; spay/neuter; dogs that panic in cones"],
                ["Orthopaedic Recovery Bed", "Joint support during rest", "Throughout recovery + ongoing", "Very High", "Joint surgery; prolonged rest periods"],
                ["Gentle Leader / Sling", "Mobility assistance for weakened limbs", "During rehabilitation", "Moderate", "Hip surgery; spinal issues; assisted walking"],
            ],
            "Recovery aids comparison")

def _table_pet_supplies_general():
    return ("Essential Pet Supplies Overview",
            ["Category", "Purpose", "Replace/Refresh", "Priority", "Best For"],
            [
                ["Food and Water Bowls", "Daily nutrition and hydration", "When damaged or stained beyond cleaning", "Essential (Day 1)", "All pets; foundation of daily care"],
                ["Bed / Sleeping Area", "Rest and recovery; sense of security", "Every 1-2 years or when worn", "Essential", "Comfort; joint health; reducing anxiety"],
                ["Collar / Harness + ID", "Identification and safe restraint", "When outgrown or worn; update ID info", "Essential", "Legal requirement; safety; lost pet recovery"],
                ["Grooming Basics", "Coat, skin, nail, and dental care", "Tools: when worn; products: as needed", "Important", "Preventing mats, infections, overgrown nails"],
                ["Toys (variety of 3-5)", "Physical exercise and mental stimulation", "Rotate weekly; replace when damaged", "Important", "Preventing boredom; healthy outlets for energy"],
            ],
            "Pet supplies overview")

def _table_weight_management():
    return ("Dog Weight Management Strategies",
            ["Strategy", "Approach", "Expected Timeline", "Owner Effort", "Best For"],
            [
                ["Portion Control", "Measure meals precisely by weight", "Gradual over 3-6 months", "Low (weigh food daily)", "Mildly overweight dogs; prevention"],
                ["Low-Calorie Diet Food", "Switch to vet-recommended formula", "3-6 months", "Low (simple food swap)", "Moderately overweight; structured diet needed"],
                ["Increased Exercise", "Add 10-15 min walks gradually", "Ongoing", "Moderate (daily commitment)", "Dogs that are under-exercised; all weight stages"],
                ["Treat Substitution", "Replace treats with carrot, apple, or training kibble", "Immediate calorie reduction", "Low", "Treat-dependent dogs; training contexts"],
                ["Feeding Puzzle/Slow Feeder", "Slow eating with mental engagement", "Supports weight plan", "Low (one-time purchase)", "Fast eaters; bored eaters"],
            ],
            "Weight management comparison")


def build_table_html(title, headers, rows, is_striped=True):
    """Build the HTML table block for WordPress."""
    stripe_class = ' is-style-stripes' if is_striped else ''

    header_cells = "".join(f"<th>{h}</th>" for h in headers)
    body_rows = ""
    for row in rows:
        cells = "".join(f"<td>{cell}</td>" for cell in row)
        body_rows += f"<tr>{cells}</tr>"

    table_html = f"""


<h3 class="wp-block-heading">{title}: At a Glance</h3>


<figure class="wp-block-table{stripe_class}"><table class="has-fixed-layout"><thead><tr>{header_cells}</tr></thead><tbody>{body_rows}</tbody></table></figure>

"""
    return table_html


def insert_table_into_content(content, table_html):
    """Insert table before Sources section or at end."""
    markers = [
        '<h3 class="wp-block-heading">Sources and Further Reading</h3>',
        '<h3 class="wp-block-heading">Sources and Further Reading',
        'Sources and Further Reading',
        '<h3 class="wp-block-heading">Our Editorial Standards</h3>',
        '<h3 class="wp-block-heading">Our Editorial Standards',
        'Our Editorial Standards',
    ]

    for marker in markers:
        idx = content.find(marker)
        if idx >= 0:
            # Find the start of the line/block before this marker
            search_start = max(0, idx - 200)
            block = content[search_start:idx]

            # Find the last newline before the marker
            last_nl = block.rfind('\n')
            if last_nl >= 0:
                insert_point = search_start + last_nl
            else:
                insert_point = idx

            return content[:insert_point] + table_html + content[insert_point:]

    # Fallback: insert at end
    return content + table_html


def main():
    print(f"=== PetHub Comparison Table Insertion ===")
    print(f"Started: {datetime.now().isoformat()}")
    print()

    # Fetch all posts
    posts = fetch_all_posts()
    print(f"Total posts fetched: {len(posts)}")

    # Filter to posts without tables
    no_table_posts = []
    has_table_count = 0
    for p in posts:
        content = p['content']['raw']
        if has_comparison_table(content):
            has_table_count += 1
        else:
            cluster, priority = get_cluster(p['categories'])
            no_table_posts.append({
                'id': p['id'],
                'title': p['title']['raw'],
                'categories': p['categories'],
                'cluster': cluster,
                'priority': priority,
                'content': content,
            })

    print(f"Posts WITH tables: {has_table_count}")
    print(f"Posts WITHOUT tables: {len(no_table_posts)}")

    # Sort by priority (lowest number = highest priority)
    no_table_posts.sort(key=lambda x: (x['priority'], x['id']))

    # Take top 50
    target_posts = no_table_posts[:50]
    print(f"Posts to process: {len(target_posts)}")
    print()

    # Print cluster breakdown
    cluster_counts = {}
    for p in target_posts:
        cluster_counts[p['cluster']] = cluster_counts.get(p['cluster'], 0) + 1
    print("Cluster breakdown of target posts:")
    for cluster, count in sorted(cluster_counts.items(), key=lambda x: -x[1]):
        print(f"  {cluster}: {count}")
    print()

    # Initialize CSV log
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'title', 'cluster', 'table_topic', 'rows', 'status'])

    success_count = 0
    fail_count = 0

    for i, post in enumerate(target_posts):
        print(f"[{i+1}/{len(target_posts)}] Processing: {post['title'][:70]}... (ID: {post['id']}, Cluster: {post['cluster']})")

        try:
            # Generate table
            table_data = generate_table(post['title'], post['content'], post['cluster'])
            if table_data is None:
                print(f"  SKIP: Could not determine appropriate table")
                with open(LOG_FILE, 'a', newline='') as f:
                    csv.writer(f).writerow([post['id'], post['title'], post['cluster'], 'N/A', 0, 'SKIPPED'])
                continue

            table_title, headers, rows, topic = table_data
            row_count = len(rows)

            # Build HTML - alternate between striped and non-striped
            is_striped = (i % 2 == 0)
            table_html = build_table_html(table_title, headers, rows, is_striped)

            # Insert into content
            new_content = insert_table_into_content(post['content'], table_html)

            # Verify insertion happened
            if new_content == post['content']:
                print(f"  ERROR: Table insertion did not modify content")
                with open(LOG_FILE, 'a', newline='') as f:
                    csv.writer(f).writerow([post['id'], post['title'], post['cluster'], topic, row_count, 'INSERTION_FAILED'])
                fail_count += 1
                continue

            # Double-check no duplicate table
            if new_content.count('wp-block-table') > 1 and post['content'].count('wp-block-table') >= 1:
                print(f"  SKIP: Post already has a table (detected in raw content)")
                with open(LOG_FILE, 'a', newline='') as f:
                    csv.writer(f).writerow([post['id'], post['title'], post['cluster'], topic, row_count, 'ALREADY_HAS_TABLE'])
                continue

            # Update via API
            update_data = {"content": new_content}
            result = api_post(f"posts/{post['id']}", update_data)

            if result and result.get('id') == post['id']:
                print(f"  SUCCESS: Inserted '{table_title}' table ({row_count} rows)")
                with open(LOG_FILE, 'a', newline='') as f:
                    csv.writer(f).writerow([post['id'], post['title'], post['cluster'], topic, row_count, 'SUCCESS'])
                success_count += 1
            else:
                error_msg = result.get('message', 'Unknown error') if result else 'No response'
                print(f"  ERROR: API update failed - {error_msg}")
                with open(LOG_FILE, 'a', newline='') as f:
                    csv.writer(f).writerow([post['id'], post['title'], post['cluster'], topic, row_count, f'API_ERROR: {error_msg}'])
                fail_count += 1

        except Exception as e:
            print(f"  EXCEPTION: {str(e)}")
            with open(LOG_FILE, 'a', newline='') as f:
                csv.writer(f).writerow([post['id'], post['title'], post['cluster'], 'EXCEPTION', 0, str(e)])
            fail_count += 1

        # Rate limiting
        time.sleep(0.5)

    print()
    print(f"=== COMPLETE ===")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Total: {success_count + fail_count}")
    print(f"Log: {LOG_FILE}")
    print(f"Finished: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
