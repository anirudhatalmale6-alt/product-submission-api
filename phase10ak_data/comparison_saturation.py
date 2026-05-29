#!/usr/bin/env python3
"""
Phase 10AK - Comparison Saturation Engine for PetHub Online
Adds educational comparison tables to posts that lack them.
Skips Dog Grooming, Dog Harnesses, Dog Beds clusters.
"""

import csv
import json
import subprocess
import tempfile
import time
import re
import os

# ── Config ──────────────────────────────────────────────────────────────────
WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ak_data"
INVENTORY = "/var/lib/freelancer/projects/40416335/phase10af_data/post_authority_inventory.csv"
LOG_FILE = os.path.join(DATA_DIR, "comparison_saturation_log.csv")

TARGET_CLUSTERS = [
    "Dog Food", "Dog Health", "Dog Training", "Dog Care",
    "Cat Toys", "Cat Supplies", "Indoor Cats", "Educational",
    "Uncategorized", "Puppy Care"
]

SKIP_CLUSTERS = ["Dog Grooming", "Dog Harnesses", "Dog Beds", "Dog Toys"]

DELAY = 2  # seconds between API calls

# ── Column schemas per cluster ──────────────────────────────────────────────
COLUMN_SCHEMAS = {
    "Dog Food": ["Option", "Best For", "Key Ingredient Focus", "Life Stage", "Activity Level"],
    "Dog Health": ["Approach", "Best For", "When to Use", "Effectiveness", "Cost Level"],
    "Dog Training": ["Method", "Best For", "Time Investment", "Difficulty", "Evidence Base"],
    "Dog Care": ["Approach", "Best For", "Key Consideration", "Suitability", "Maintenance"],
    "Cat Toys": ["Type", "Best For", "Play Style", "Durability", "Indoor/Outdoor"],
    "Cat Supplies": ["Product Type", "Best For", "Key Feature", "Maintenance", "Value"],
    "Indoor Cats": ["Approach", "Best For", "Key Benefit", "Effort Level", "Suitability"],
    "Educational": ["Topic", "Key Takeaway", "Who Benefits", "Difficulty", "Resources Needed"],
    "Uncategorized": ["Option", "Best For", "Key Consideration", "Suitability", "Maintenance"],
    "Puppy Care": ["Approach", "Best For", "Age Range", "Time Needed", "Common Mistakes"],
}

# ── Topic-specific table data ───────────────────────────────────────────────
# Each function generates 5-6 rows based on the post title/topic

def generate_table_rows(post_id, title, cluster):
    """Generate educational comparison rows based on post title and cluster."""
    title_lower = title.lower()

    # ── Dog Food ──
    if cluster == "Dog Food":
        if "puppy" in title_lower or "growth" in title_lower:
            return [
                ["High-Protein Kibble", "Active growing puppies", "Animal-based protein (30%+)", "Puppy (2-12 months)", "High"],
                ["Grain-Inclusive Formula", "Puppies with no sensitivities", "Whole grains for energy", "Puppy (2-12 months)", "Moderate"],
                ["Grain-Free Formula", "Puppies with grain allergies", "Legume/potato carb sources", "Puppy (2-12 months)", "Moderate"],
                ["Wet/Canned Puppy Food", "Fussy eaters or weaning pups", "High moisture content", "Weaning to 12 months", "Low-Moderate"],
                ["Raw or Freeze-Dried", "Owners wanting minimal processing", "Whole meat and organs", "Puppy (4+ months)", "High"],
                ["Large-Breed Puppy Formula", "Breeds over 25kg adult weight", "Controlled calcium/phosphorus", "Puppy (2-18 months)", "Moderate"],
            ]
        elif "dry" in title_lower and "wet" in title_lower:
            return [
                ["Dry Kibble", "Convenience-focused owners", "Shelf-stable grains/protein", "All life stages", "Low-Moderate"],
                ["Wet/Canned Food", "Hydration-conscious owners", "High moisture (70-80%)", "All life stages", "Low"],
                ["Semi-Moist Pouches", "Training or topping use", "Moderate moisture blend", "Adult maintenance", "Moderate"],
                ["Mixed Feeding (Dry+Wet)", "Balanced nutrition seekers", "Combined nutrient profiles", "All life stages", "Moderate"],
                ["Air-Dried Food", "Owners wanting less processing", "Gentle dehydration preserves nutrients", "Adult/Senior", "Moderate-High"],
            ]
        elif "dry" in title_lower:
            return [
                ["Cold-Pressed Kibble", "Nutrient preservation priority", "Low-temperature processing", "All life stages", "Moderate"],
                ["Extruded Kibble", "Budget-conscious daily feeding", "High-heat shaped pellets", "All life stages", "Moderate"],
                ["High-Protein Dry", "Active or working dogs", "Animal protein 30%+", "Active adult", "High"],
                ["Grain-Free Dry", "Dogs with grain sensitivities", "Legume/sweet potato base", "Adult maintenance", "Moderate"],
                ["Weight Management Dry", "Overweight or sedentary dogs", "Reduced fat, high fibre", "Adult/Senior", "Low-Moderate"],
                ["Senior Dry Formula", "Dogs over 7 years", "Joint support + easy digestion", "Senior (7+)", "Low"],
            ]
        elif "nutrition" in title_lower or "label" in title_lower or "terminology" in title_lower:
            return [
                ["Protein Sources", "Muscle and tissue repair", "Named meat as first ingredient", "All life stages", "All"],
                ["Fat Content", "Energy and coat health", "Omega-3 and Omega-6 balance", "All life stages", "Moderate-High"],
                ["Fibre Levels", "Digestive regularity", "Beet pulp or chicory root", "Adult/Senior", "All"],
                ["Vitamin Supplements", "Immune system support", "A, D, E, B-complex", "All life stages", "All"],
                ["Mineral Balance", "Bone and dental health", "Calcium-to-phosphorus ratio", "Growth/Senior", "All"],
            ]
        elif "feeding" in title_lower or "portion" in title_lower:
            return [
                ["Free Feeding", "Self-regulating adult dogs", "Always-available kibble", "Adult maintenance", "Low"],
                ["Scheduled Meals", "Most adult dogs", "Set times, measured portions", "All life stages", "All"],
                ["Puzzle Feeding", "Fast eaters or bored dogs", "Slow dispensing enrichment", "Adult", "All"],
                ["Timed Feeding", "Overweight dogs", "Food available for set window", "Adult/Senior", "Moderate"],
                ["Hand Feeding", "Training-focused owners", "Portion used as reward", "Puppy/Training", "Moderate-High"],
            ]
        else:
            return [
                ["Complete Dry Food", "Everyday balanced nutrition", "Balanced protein/carb/fat", "All life stages", "Moderate"],
                ["Wet Food", "Hydration and palatability", "High moisture, rich flavour", "All life stages", "Low-Moderate"],
                ["Raw Diet (BARF)", "Owners wanting whole foods", "Unprocessed meat and bone", "Adult", "High"],
                ["Prescription Diet", "Dogs with medical conditions", "Veterinary-formulated nutrients", "As prescribed", "Varies"],
                ["Grain-Free Formula", "Dogs with grain intolerance", "Alternative carb sources", "Adult", "Moderate"],
                ["Senior Formula", "Ageing dogs (7+ years)", "Joint and digestive support", "Senior", "Low-Moderate"],
            ]

    # ── Dog Health ──
    if cluster == "Dog Health":
        if "dental" in title_lower or "teeth" in title_lower:
            return [
                ["Daily Tooth Brushing", "All dogs", "Daily prevention", "Very High", "Low"],
                ["Dental Chews", "Dogs who resist brushing", "Daily supplement", "Moderate", "Low"],
                ["Water Additives", "Easy passive care", "Daily in water bowl", "Low-Moderate", "Very Low"],
                ["Professional Cleaning", "Tartar buildup cases", "Annual vet visits", "Very High", "High"],
                ["Dental Diet Kibble", "Plaque-prone breeds", "Daily at mealtimes", "Moderate", "Low"],
                ["Raw Bones (Supervised)", "Strong chewers only", "Weekly supervised sessions", "Moderate", "Low"],
            ]
        elif "flea" in title_lower or "prevention" in title_lower:
            return [
                ["Spot-On Treatments", "Monthly topical protection", "Monthly application", "High", "Moderate"],
                ["Oral Flea Tablets", "Quick systemic action", "Monthly or as needed", "Very High", "Moderate"],
                ["Flea Collars", "Continuous passive protection", "Replace every 6-8 months", "Moderate", "Low"],
                ["Flea Shampoos", "Active infestations", "During bathing only", "Low (temporary)", "Low"],
                ["Environmental Sprays", "Home and bedding treatment", "During outbreaks", "High (for home)", "Low-Moderate"],
            ]
        elif "joint" in title_lower or "mobility" in title_lower or "supplement" in title_lower:
            return [
                ["Glucosamine Supplements", "Early joint support", "Daily ongoing use", "Moderate", "Moderate"],
                ["Omega-3 Fatty Acids", "Anti-inflammatory support", "Daily with food", "Moderate", "Low-Moderate"],
                ["Physiotherapy", "Post-surgery or injury", "Scheduled sessions", "High", "High"],
                ["Weight Management", "Overweight dogs", "Ongoing lifestyle change", "Very High", "Low"],
                ["Hydrotherapy", "Low-impact rehabilitation", "Weekly sessions", "High", "High"],
                ["Joint-Support Diet", "Breed-prone dogs", "Daily nutrition choice", "Moderate", "Moderate"],
            ]
        else:
            return [
                ["Preventive Vet Visits", "All dogs annually", "Scheduled check-ups", "Very High", "Moderate"],
                ["Vaccination Schedule", "Puppies and adults", "As per vet timeline", "Very High", "Low-Moderate"],
                ["Parasite Prevention", "All dogs year-round", "Monthly treatments", "High", "Low-Moderate"],
                ["Weight Monitoring", "All dogs regularly", "Monthly weigh-ins", "High", "Low"],
                ["Dental Care Routine", "All dogs", "Daily brushing/chews", "High", "Low"],
                ["First Aid Knowledge", "Emergency readiness", "Learn basics in advance", "Situational", "Low"],
            ]

    # ── Dog Training ──
    if cluster == "Dog Training":
        if "socialisation" in title_lower or "socialization" in title_lower:
            return [
                ["Puppy Classes", "New puppies 8-16 weeks", "Weekly 6-8 weeks", "Moderate", "Strong (AVSAB endorsed)"],
                ["Controlled Exposure", "Fearful or sheltered dogs", "Daily short sessions", "Easy-Moderate", "Strong"],
                ["Desensitisation", "Dogs with specific fears", "Gradual over weeks", "Moderate", "Strong (behaviour science)"],
                ["Parallel Walking", "Dog-reactive dogs", "Weekly with helper dog", "Moderate", "Moderate"],
                ["Home Visitor Exposure", "Dogs wary of strangers", "Regular arranged visits", "Easy", "Moderate"],
            ]
        elif "treat" in title_lower or "reward" in title_lower:
            return [
                ["Small Soft Treats", "Quick reward delivery", "Low per-treat time", "Easy", "Strong (operant conditioning)"],
                ["Freeze-Dried Meat", "High-value motivation", "Low per-treat time", "Easy", "Strong"],
                ["Kibble Pieces", "Low-distraction training", "Minimal extra time", "Easy", "Moderate"],
                ["Vegetable Pieces", "Weight-conscious training", "Minimal prep time", "Easy", "Moderate"],
                ["Lick-Based Rewards", "Duration behaviours", "Moderate (licking time)", "Easy", "Strong"],
                ["Play Rewards", "Toy-driven dogs", "Variable session length", "Moderate", "Strong"],
            ]
        elif "equipment" in title_lower or "tool" in title_lower:
            return [
                ["Flat Collar + Lead", "Basic loose-lead walking", "Low setup time", "Easy", "Standard best practice"],
                ["Front-Clip Harness", "Reducing pulling behaviour", "Moderate fitting time", "Easy", "Supported by trainers"],
                ["Long Line (5-10m)", "Recall training outdoors", "Moderate supervision", "Moderate", "Strong (controlled freedom)"],
                ["Treat Pouch", "Efficient reward delivery", "Minimal", "Easy", "Practical standard"],
                ["Clicker", "Precision marker training", "Short learning curve", "Easy-Moderate", "Strong (operant conditioning)"],
                ["Target Stick", "Position and trick training", "Moderate practice", "Moderate", "Strong"],
            ]
        elif "behaviour" in title_lower or "body language" in title_lower:
            return [
                ["Positive Reinforcement", "Most dogs and situations", "Moderate consistency", "Easy-Moderate", "Very Strong (AVSAB)"],
                ["Counter-Conditioning", "Fear or anxiety responses", "Weeks to months", "Moderate", "Strong"],
                ["Management/Prevention", "Immediate safety needs", "Ongoing environmental control", "Easy", "Strong (practical)"],
                ["Desensitisation", "Specific triggers/phobias", "Gradual over weeks", "Moderate-Hard", "Strong"],
                ["Relationship-Based Training", "Trust-building with shy dogs", "Long-term approach", "Moderate", "Growing evidence"],
            ]
        elif "scratching" in title_lower or "cat" in title_lower:
            return [
                ["Vertical Scratching Posts", "Cats who stretch upward", "Minimal daily effort", "Easy", "Strong (natural behaviour)"],
                ["Horizontal Scratch Pads", "Cats who scratch ground level", "Minimal daily effort", "Easy", "Strong"],
                ["Sisal Rope Surfaces", "Heavy scratchers", "Monthly inspection", "Easy", "Standard recommendation"],
                ["Cardboard Scratchers", "Budget-friendly enrichment", "Weekly replacement check", "Easy", "Moderate"],
                ["Redirecting Training", "Cats scratching furniture", "Consistent daily practice", "Moderate", "Strong (positive reinforcement)"],
            ]
        else:
            return [
                ["Positive Reinforcement", "All dogs and skill levels", "Daily short sessions", "Easy-Moderate", "Very Strong (AVSAB)"],
                ["Clicker Training", "Precision skill building", "15-min daily sessions", "Moderate", "Strong (operant conditioning)"],
                ["Lure-Reward Training", "Puppies and beginners", "Short guided sessions", "Easy", "Strong"],
                ["Shaping (Free-Shaping)", "Advanced trick training", "Patience-heavy sessions", "Moderate-Hard", "Strong"],
                ["Capturing", "Reinforcing natural behaviours", "Ongoing observation", "Easy", "Strong"],
                ["Management Strategies", "Preventing unwanted habits", "Environmental setup", "Easy", "Practical standard"],
            ]

    # ── Dog Care ──
    if cluster == "Dog Care":
        if "seasonal" in title_lower:
            return [
                ["Summer Heat Protection", "Hot weather safety", "Shade, water, cool mats", "High", "Daily monitoring"],
                ["Winter Cold Protection", "Cold-sensitive breeds", "Coats, paw balm, warm bedding", "High", "Daily as needed"],
                ["Spring Allergy Management", "Allergy-prone dogs", "Paw washing, vet consultation", "Moderate", "Regular checks"],
                ["Autumn Parasite Check", "All dogs after summer", "Flea/tick/worm treatment review", "High", "Monthly"],
                ["Year-Round Hydration", "All dogs always", "Fresh water availability", "Very High", "Minimal"],
                ["Seasonal Exercise Adjustment", "Active dogs", "Adapt duration to temperature", "High", "Daily planning"],
            ]
        else:
            return [
                ["Daily Exercise", "Physical and mental health", "Breed-appropriate activity", "Very High", "Daily time commitment"],
                ["Regular Grooming", "Coat and skin health", "Brushing, bathing schedule", "High", "Weekly-Monthly"],
                ["Dental Care", "Preventing dental disease", "Brushing and dental chews", "High", "Daily"],
                ["Parasite Prevention", "Year-round protection", "Monthly flea/tick/worming", "Very High", "Monthly treatment"],
                ["Weight Monitoring", "Preventing obesity", "Regular weigh-ins, portion control", "High", "Weekly checks"],
            ]

    # ── Cat Toys ──
    if cluster == "Cat Toys":
        if "interactive" in title_lower or "wand" in title_lower or "puzzle" in title_lower:
            return [
                ["Wand/Feather Toys", "Active hunters", "Chase and pounce", "Moderate (replace feathers)", "Indoor"],
                ["Puzzle Feeders", "Food-motivated cats", "Problem-solving", "High", "Indoor"],
                ["Laser Pointers (with treat follow-up)", "High-energy chasers", "Chase/sprint", "Very High", "Indoor"],
                ["Ball Track Toys", "Independent players", "Batting and swatting", "High", "Indoor"],
                ["Electronic Moving Toys", "Cats needing stimulation when alone", "Erratic prey mimicry", "Moderate", "Indoor"],
            ]
        elif "catnip" in title_lower:
            return [
                ["Catnip-Stuffed Mice", "Catnip-responsive cats", "Kick and toss", "Moderate", "Indoor"],
                ["Silvervine Sticks", "Cats unresponsive to catnip", "Chew and rub", "Low (consumable)", "Indoor"],
                ["Catnip Spray (on existing toys)", "Refreshing old toys", "Applied enrichment", "N/A", "Indoor"],
                ["Valerian Root Toys", "Alternative herbal response", "Roll and bunny-kick", "Moderate", "Indoor"],
                ["Dried Catnip Loose", "DIY toy stuffing", "Sniffing and rolling", "N/A (refill as needed)", "Indoor"],
            ]
        elif "scratching" in title_lower or "scratcher" in title_lower:
            return [
                ["Vertical Sisal Posts", "Cats who stretch tall", "Scratching and stretching", "Very High", "Indoor"],
                ["Horizontal Cardboard Pads", "Ground-level scratchers", "Clawing and resting", "Low (replace monthly)", "Indoor"],
                ["Wall-Mounted Scratchers", "Space-saving homes", "Stretching and marking", "High", "Indoor"],
                ["Sisal-Wrapped Furniture", "Multi-use enrichment", "Climbing and scratching", "Very High", "Indoor"],
                ["Angled Ramp Scratchers", "Cats with joint issues", "Gentle stretch scratching", "Moderate", "Indoor"],
                ["Corrugated Lounger Scratchers", "Cats who like to rest and scratch", "Scratching and lounging", "Moderate", "Indoor"],
            ]
        elif "diy" in title_lower or "homemade" in title_lower:
            return [
                ["Paper Ball Toys", "Budget play enrichment", "Batting and chasing", "Low (replace often)", "Indoor"],
                ["Cardboard Box Hideaways", "Cats who love hiding", "Exploring and ambushing", "Low (recycle weekly)", "Indoor"],
                ["Sock Kicker Toys", "Bunny-kick enthusiasts", "Kicking and wrestling", "Moderate", "Indoor"],
                ["Toilet Roll Puzzle Feeders", "Food-motivated cats", "Foraging and problem-solving", "Low (disposable)", "Indoor"],
                ["Feather-on-String Wands", "Active play sessions", "Chasing and leaping", "Low (supervised only)", "Indoor"],
            ]
        elif "kitten" in title_lower or "age" in title_lower:
            return [
                ["Soft Plush Toys", "Kittens under 6 months", "Gentle batting and cuddling", "Low-Moderate", "Indoor"],
                ["Small Rolling Balls", "Young kittens learning coordination", "Chase and paw", "High", "Indoor"],
                ["Feather Wands (supervised)", "Kittens 3+ months", "Pounce and leap", "Moderate", "Indoor"],
                ["Interactive Puzzles (easy)", "Kittens 4+ months", "Simple problem-solving", "High", "Indoor"],
                ["Adult Hunting Toys", "Cats 1+ year", "Stalk, chase, capture", "High", "Indoor/Outdoor"],
                ["Senior Gentle Toys", "Cats 10+ years", "Low-effort batting", "High", "Indoor"],
            ]
        elif "replace" in title_lower or "how often" in title_lower:
            return [
                ["Plush/Fabric Toys", "Gentle players", "Cuddling and carrying", "Low (replace when torn)", "Indoor"],
                ["Rubber/Silicone Toys", "Chewers and batters", "Biting and tossing", "High", "Indoor"],
                ["Feather Attachments", "Wand toy components", "Chase stimulation", "Very Low (replace monthly)", "Indoor"],
                ["Catnip Toys", "Herbal enrichment", "Rolling and kicking", "Moderate (refresh scent)", "Indoor"],
                ["Electronic/Battery Toys", "Independent play", "Automated movement", "High (replace batteries)", "Indoor"],
            ]
        elif "cat tree" in title_lower or "climbing" in title_lower:
            return [
                ["Tall Multi-Level Trees", "Active climbing cats", "Climbing and perching", "Very High", "Indoor"],
                ["Compact Cat Trees", "Small spaces or single cats", "Resting and light climbing", "High", "Indoor"],
                ["Wall-Mounted Shelves", "Space-saving vertical play", "Jumping and perching", "Very High", "Indoor"],
                ["Window Perch Add-Ons", "Bird-watching cats", "Observation and rest", "High", "Indoor"],
                ["Sisal-Wrapped Trees", "Scratchers and climbers", "Combined scratching/climbing", "Very High", "Indoor"],
            ]
        else:
            return [
                ["Wand and Feather Toys", "Interactive play with owners", "Chase and pounce", "Moderate", "Indoor"],
                ["Puzzle Feeders", "Food-motivated cats", "Problem-solving", "High", "Indoor"],
                ["Catnip Toys", "Catnip-responsive cats", "Rolling and kicking", "Moderate", "Indoor"],
                ["Ball and Track Toys", "Independent play", "Batting and chasing", "High", "Indoor"],
                ["Crinkle Toys", "Sound-stimulated cats", "Pouncing and batting", "Moderate", "Indoor"],
                ["Laser Pointers (with follow-up toy)", "High-energy cats", "Sprint chasing", "Very High", "Indoor"],
            ]

    # ── Cat Supplies ──
    if cluster == "Cat Supplies":
        if "litter" in title_lower and ("disposal" in title_lower or "waste" in title_lower):
            return [
                ["Standard Bin Disposal", "Budget-conscious owners", "Simple bag-and-bin method", "Daily scooping", "Low"],
                ["Dedicated Litter Genie", "Odour control priority", "Sealed odour-lock system", "Cartridge replacement", "Moderate"],
                ["Biodegradable Bags", "Eco-conscious owners", "Compostable waste bags", "Daily scooping", "Moderate"],
                ["Flushable Litter", "Convenience seekers (check local rules)", "Water-soluble formula", "Daily flushing", "Moderate"],
                ["Composting (non-edible plants only)", "Garden owners", "Long-term decomposition", "Monthly turning", "Low"],
            ]
        elif "litter" in title_lower and ("tray" in title_lower or "box" in title_lower):
            return [
                ["Open Litter Tray", "Most cats (easy access)", "Low sides, easy entry", "Daily scoop, weekly wash", "Low"],
                ["Hooded/Enclosed Tray", "Privacy-seeking cats", "Odour containment", "Daily scoop, weekly wash", "Moderate"],
                ["Top-Entry Tray", "Cats that scatter litter", "Reduced tracking", "Daily scoop, weekly wash", "Moderate"],
                ["Self-Cleaning Tray", "Busy multi-cat households", "Automated raking/rotation", "Periodic mechanism check", "High"],
                ["Corner/Space-Saving Tray", "Small living spaces", "Compact triangular design", "Daily scoop, weekly wash", "Low-Moderate"],
            ]
        elif "litter" in title_lower:
            return [
                ["Clumping Clay Litter", "Easy daily maintenance", "Forms solid clumps for scooping", "Daily scooping", "Moderate"],
                ["Non-Clumping Clay", "Budget-conscious owners", "Absorbs without clumping", "Full replacement weekly", "Low"],
                ["Wood Pellet Litter", "Eco-friendly preference", "Biodegradable, natural scent", "Regular sifting", "Low-Moderate"],
                ["Paper-Based Litter", "Post-surgery or sensitive cats", "Dust-free, soft texture", "Frequent changes", "Moderate"],
                ["Silica Crystal Litter", "Low-maintenance seekers", "High absorption, colour-change indicator", "Monthly replacement", "Moderate-High"],
                ["Tofu/Plant-Based Litter", "Flushable option seekers", "Biodegradable, lightweight", "Daily scooping", "Moderate"],
            ]
        elif "bed" in title_lower:
            return [
                ["Enclosed/Cave Beds", "Shy or anxious cats", "Secure den-like space", "Weekly wash of cover", "Moderate"],
                ["Flat/Cushion Beds", "Cats who sprawl", "Open sleeping surface", "Weekly wash", "Moderate"],
                ["Heated Beds", "Senior or arthritic cats", "Gentle consistent warmth", "Wipe-down, check cord", "Moderate-High"],
                ["Window Perch Beds", "Bird-watching cats", "Suction-mount sunning spot", "Weekly wipe-down", "Moderate"],
                ["Radiator Beds", "Warmth-seeking cats in winter", "Hooks over radiator", "Weekly wash of cover", "Low"],
            ]
        elif "essential" in title_lower or "must" in title_lower or "supplies" in title_lower:
            return [
                ["Food and Water Bowls", "Every cat household", "Non-tip, easy-clean material", "Daily washing", "Low"],
                ["Litter Tray and Litter", "Every cat household", "Appropriate size and type", "Daily scooping, weekly deep clean", "Low-Moderate"],
                ["Scratching Post", "Claw health and territory marking", "Sturdy sisal or cardboard", "Monthly condition check", "Low"],
                ["Cat Carrier", "Vet visits and travel", "Secure, well-ventilated design", "Clean after each use", "Low"],
                ["Enrichment Toys", "Mental and physical stimulation", "Variety of play types", "Regular rotation and inspection", "Low"],
                ["Grooming Tools", "Coat and skin health", "Brush suited to coat type", "Weekly grooming sessions", "Low"],
            ]
        else:
            return [
                ["Food and Water Stations", "Daily nutrition needs", "Stainless steel or ceramic", "Daily cleaning", "Low"],
                ["Litter Tray Setup", "Hygiene essentials", "Size-appropriate tray + litter", "Daily scooping", "Moderate"],
                ["Scratching Surfaces", "Claw maintenance", "Sisal, cardboard, or wood", "Monthly replacement check", "Low"],
                ["Bedding", "Rest and comfort", "Washable, warm material", "Weekly washing", "Moderate"],
                ["Carrier/Transport", "Vet and travel needs", "Secure, ventilated design", "Clean after each use", "Low"],
            ]

    # ── Indoor Cats ──
    if cluster == "Indoor Cats":
        if "toy" in title_lower:
            return [
                ["Wand Toys (daily sessions)", "All indoor cats", "Interactive play mimics hunting", "Moderate (owner-led)", "Indoor only"],
                ["Puzzle Feeders", "Food-motivated indoor cats", "Slows eating, adds challenge", "Moderate (self-directed)", "Indoor only"],
                ["Window Bird Feeders", "Cats who watch outside", "Visual prey stimulation", "Low (refill seed)", "Indoor only"],
                ["Rotating Toy Collection", "Boredom-prone indoor cats", "Maintains novelty", "Moderate (swap weekly)", "Indoor only"],
                ["Vertical Climbing Spaces", "Active indoor cats", "Exercise and territory", "High (durable)", "Indoor only"],
            ]
        else:
            return [
                ["Vertical Space (cat trees/shelves)", "Active climbers", "Exercise and territory enrichment", "Moderate", "High for indoor cats"],
                ["Window Enrichment", "Bird-watching cats", "Visual and sensory stimulation", "Low", "Very High for indoor cats"],
                ["Interactive Daily Play", "All indoor cats (15+ min/day)", "Mimics hunting behaviour", "Moderate", "Essential"],
                ["Puzzle Feeding", "Fast eaters or bored cats", "Mental stimulation at mealtimes", "Moderate", "High for indoor cats"],
                ["Safe Outdoor Access (catio/harness)", "Cats craving outdoors", "Controlled outdoor enrichment", "High setup", "Excellent where feasible"],
                ["Multi-Room Rotation", "Cats in small spaces", "Environmental variety", "Low", "Good for studio/flat cats"],
            ]

    # ── Educational ──
    if cluster == "Educational":
        if "veterinary" in title_lower or "health term" in title_lower or "pet health" in title_lower:
            return [
                ["Vaccination Terminology", "Understanding vet records", "New pet owners", "Beginner", "Vet handouts"],
                ["Common Condition Names", "Recognising diagnoses", "All pet owners", "Beginner-Intermediate", "Vet consultation"],
                ["Medication Terms", "Following prescriptions correctly", "Owners managing treatments", "Intermediate", "Vet guidance"],
                ["Diagnostic Test Names", "Understanding lab results", "Owners of ill pets", "Intermediate", "Vet records"],
                ["Emergency Warning Signs", "Knowing when to act fast", "All pet owners", "Beginner", "Pet first aid guide"],
            ]
        elif "training" in title_lower or "terminology" in title_lower:
            return [
                ["Reinforcement vs Punishment", "Understanding learning theory", "New dog owners", "Beginner", "Training guides"],
                ["Classical Conditioning", "Fear and association learning", "Reactive dog owners", "Intermediate", "Behaviour books"],
                ["Operant Conditioning", "Everyday obedience training", "All trainers", "Beginner-Intermediate", "Training classes"],
                ["Desensitisation Concepts", "Managing phobias and fears", "Owners of anxious pets", "Intermediate", "Professional behaviourist"],
                ["Body Language Signals", "Reading your pet's emotions", "All pet owners", "Beginner", "Visual guides"],
            ]
        elif "cat care" in title_lower or "cat owner" in title_lower or "glossary" in title_lower and "cat" in title_lower:
            return [
                ["Indoor Environment Setup", "Creating safe cat spaces", "New cat owners", "Beginner", "Cat welfare guides"],
                ["Nutrition Basics", "Understanding feeding needs", "First-time owners", "Beginner", "Vet nutritionist advice"],
                ["Litter Training Principles", "Maintaining hygiene habits", "Kitten adopters", "Beginner", "Cat behaviour guides"],
                ["Health Check Indicators", "Spotting early illness signs", "All cat owners", "Beginner-Intermediate", "Vet consultation"],
                ["Socialisation Concepts", "Helping cats adjust", "Multi-pet households", "Intermediate", "Behaviour resources"],
            ]
        elif "play style" in title_lower or "dog play" in title_lower:
            return [
                ["Chase Play", "Understanding pursuit behaviour", "Dog park visitors", "Beginner", "Observation and guides"],
                ["Wrestling/Rough Play", "Knowing safe vs aggressive play", "Multi-dog owners", "Intermediate", "Trainer guidance"],
                ["Object Play (fetch/tug)", "Channelling toy drive", "Active dog owners", "Beginner", "Toy selection guides"],
                ["Solitary Play", "Recognising independent enrichment", "Busy owners", "Beginner", "Enrichment articles"],
                ["Sensory Play (sniffing)", "Scent-based enrichment value", "All dog owners", "Beginner", "Enrichment resources"],
            ]
        elif "bed" in title_lower:
            return [
                ["Orthopaedic Beds", "Joint support concepts", "Senior dog owners", "Beginner", "Vet recommendations"],
                ["Bolster/Nest Beds", "Security and warmth needs", "Anxious dog owners", "Beginner", "Breed guides"],
                ["Cooling Beds", "Temperature regulation", "Hot climate owners", "Beginner", "Seasonal care guides"],
                ["Elevated/Cot Beds", "Airflow and joint relief", "Large breed owners", "Beginner", "Product guides"],
                ["Cave/Hooded Beds", "Den instinct and anxiety", "Small/anxious breeds", "Beginner", "Behaviour resources"],
            ]
        elif "chewer" in title_lower or "aggressive" in title_lower:
            return [
                ["Rubber Enrichment Toys", "Understanding durable materials", "Power chewer owners", "Beginner", "Material safety guides"],
                ["Nylon Chew Toys", "Hard chewing needs", "Adult heavy chewers", "Beginner", "Size guides"],
                ["Rope Toys (supervised)", "Tug and texture needs", "Interactive play seekers", "Beginner-Intermediate", "Safety guidelines"],
                ["Frozen Enrichment", "Teething and calming chewing", "Puppy owners", "Beginner", "DIY enrichment guides"],
                ["Size-Appropriate Selection", "Preventing choking hazards", "All dog owners", "Beginner", "Vet and trainer advice"],
            ]
        elif "hydration" in title_lower or "water" in title_lower:
            return [
                ["Standard Water Bowls", "Daily home hydration basics", "All pet owners", "Beginner", "Vet guidelines"],
                ["Travel Water Bottles", "On-the-go hydration methods", "Active/travelling owners", "Beginner", "Travel guides"],
                ["Water Fountains", "Encouraging water intake", "Reluctant drinkers", "Beginner", "Product comparison guides"],
                ["Dehydration Warning Signs", "Recognising hydration issues", "All pet owners", "Beginner-Intermediate", "Vet first aid resources"],
                ["Seasonal Hydration Needs", "Adjusting intake by weather", "All pet owners", "Beginner", "Seasonal care guides"],
            ]
        elif "bowl" in title_lower or "feeder" in title_lower or "feeding" in title_lower or "elevated" in title_lower:
            return [
                ["Standard Floor Bowls", "Basic everyday feeding setup", "All pet owners", "Beginner", "Vet feeding guidelines"],
                ["Elevated/Raised Bowls", "Understanding ergonomic feeding", "Large breed or senior owners", "Beginner", "Vet advice on posture"],
                ["Slow Feeder Bowls", "Preventing fast eating", "Speed-eating dogs", "Beginner", "Enrichment guides"],
                ["Puzzle Feeders", "Mental enrichment at mealtimes", "Bored or food-driven dogs", "Beginner-Intermediate", "Enrichment resources"],
                ["Material Comparison (steel/ceramic/plastic)", "Choosing safe materials", "Health-conscious owners", "Beginner", "Safety guides"],
            ]
        elif "gps" in title_lower or "tracker" in title_lower:
            return [
                ["GPS Collar Trackers", "Real-time outdoor cat monitoring", "Outdoor cat owners", "Intermediate", "Product comparison resources"],
                ["Bluetooth Proximity Tags", "Short-range indoor finding", "Indoor cat owners", "Beginner", "Basic tech guides"],
                ["Activity Monitoring", "Understanding health data", "Health-conscious owners", "Intermediate", "Vet consultation"],
                ["Geofencing Alerts", "Boundary escape notifications", "Cats near roads", "Intermediate", "App setup guides"],
                ["Battery and Subscription Considerations", "Ongoing cost awareness", "Budget-conscious owners", "Beginner", "Comparison reviews"],
            ]
        elif "id tag" in title_lower or "identification" in title_lower:
            return [
                ["Engraved Metal Tags", "Durable visible identification", "All cat owners", "Beginner", "Pet ID regulations"],
                ["QR Code Tags", "Digital profile access", "Tech-savvy owners", "Beginner", "QR tag services"],
                ["Slide-On Collar Tags", "Quiet, snag-free identification", "Outdoor cats", "Beginner", "Collar fitting guides"],
                ["Microchipping", "Permanent legal identification", "All cat owners (UK law)", "Beginner", "Vet or rescue services"],
                ["Combining Tag + Microchip", "Comprehensive identification", "All responsible owners", "Beginner", "Vet advice"],
            ]
        elif "collar" in title_lower:
            return [
                ["Breakaway Safety Collars", "Snag-release protection", "Outdoor cats", "Beginner", "Cat safety guides"],
                ["Reflective Collars", "Nighttime visibility", "Outdoor/dusk-active cats", "Beginner", "Road safety resources"],
                ["Flea Collars", "Parasite prevention (supplementary)", "Outdoor cats", "Beginner-Intermediate", "Vet parasite advice"],
                ["Elastic/Stretch Collars", "Basic safety stretch feature", "All cats", "Beginner", "Collar fitting guides"],
                ["Bell Collars", "Wildlife protection alerts", "Hunting cats outdoors", "Beginner", "Wildlife charity advice"],
            ]
        elif "radiator" in title_lower:
            return [
                ["Fleece-Lined Radiator Beds", "Winter warmth-seeking cats", "Cold-climate cat owners", "Beginner", "Cat comfort guides"],
                ["Wire-Frame Radiator Perches", "Sturdy elevated warming", "Heavier cats", "Beginner", "Weight limit guides"],
                ["Safety and Temperature", "Avoiding overheating", "All radiator bed users", "Beginner", "Vet advice on heat"],
                ["Alternative Warming Options", "Non-radiator heated beds", "Homes without radiators", "Beginner", "Product comparison guides"],
                ["Placement and Stability", "Secure mounting considerations", "Safety-conscious owners", "Beginner", "Installation guides"],
            ]
        else:
            return [
                ["Daily Care Routines", "Building consistent pet care habits", "New pet owners", "Beginner", "Vet and trainer guides"],
                ["Nutrition Fundamentals", "Understanding balanced pet diets", "All pet owners", "Beginner-Intermediate", "Veterinary nutritionists"],
                ["Behaviour Basics", "Reading and responding to pet signals", "First-time owners", "Beginner", "Behaviour guides"],
                ["Health Prevention", "Vaccinations, parasite control, check-ups", "All pet owners", "Beginner", "Vet practice resources"],
                ["Enrichment Principles", "Mental and physical stimulation needs", "All pet owners", "Beginner", "Enrichment research"],
            ]

    # ── Uncategorized ──
    if cluster == "Uncategorized":
        if "confidence" in title_lower or "shy" in title_lower or "fearful" in title_lower:
            return [
                ["Gentle Approach Training", "Shy or fearful dogs", "Safe confidence building", "High for shy dogs", "Daily short sessions"],
                ["Novel Object Introduction", "Dogs wary of new things", "Gradual desensitisation", "High for nervous dogs", "Weekly new items"],
                ["Confidence Course (home)", "Building physical confidence", "Low obstacles, tunnels", "Moderate-High", "Weekly practice"],
                ["Social Play (controlled)", "Dogs learning dog manners", "Calm parallel exposure", "High", "Supervised weekly"],
                ["Scent Enrichment", "Low-pressure mental work", "Sniffing and searching", "High for all dogs", "Daily 10-min sessions"],
            ]
        elif "puzzle" in title_lower or "rotating" in title_lower or "complexity" in title_lower:
            return [
                ["Beginner Puzzles (single step)", "New-to-puzzle dogs", "Simple reveal or slide", "Easy entry point", "Daily rotation"],
                ["Intermediate Puzzles (multi-step)", "Dogs mastering basics", "Sequence of actions needed", "Moderate challenge", "Every 2-3 days"],
                ["Advanced Puzzles (combination lock)", "Smart, experienced dogs", "Multiple mechanisms", "High challenge", "Weekly introduction"],
                ["DIY Puzzle Enrichment", "Budget-conscious owners", "Household item challenges", "Varies with design", "Daily creation"],
                ["Timed Challenge Puzzles", "Competitive or driven dogs", "Speed-based reward", "High motivation", "2-3 times weekly"],
            ]
        elif "bed" in title_lower and "place" in title_lower:
            return [
                ["Quiet Corner Placement", "Anxious or noise-sensitive dogs", "Low traffic, sheltered spot", "Very High", "Occasional repositioning"],
                ["Bedroom Placement", "Dogs needing owner proximity", "Near owner's bed, consistent warmth", "High", "Minimal"],
                ["Living Room Central", "Social, family-oriented dogs", "Part of family activity", "High", "Regular cleaning"],
                ["Crate Inside Placement", "Crate-trained dogs", "Secure den-like feel", "Very High", "Weekly wash"],
                ["Multi-Location Setup", "Free-roaming dogs", "Bed options per room", "High", "Rotate and wash regularly"],
            ]
        elif "wash" in title_lower or "maintain" in title_lower and "bed" in title_lower:
            return [
                ["Weekly Cover Washing", "Regular hygiene maintenance", "Machine wash removable cover", "High", "Weekly laundry cycle"],
                ["Monthly Deep Clean", "Full bed sanitisation", "Soak/steam inner cushion", "Very High", "Monthly schedule"],
                ["Spot Cleaning", "Quick accident response", "Enzyme cleaner on stains", "Moderate", "As needed"],
                ["Outdoor Sun Drying", "Natural deodorising", "UV exposure kills bacteria", "Moderate", "Weekly when sunny"],
                ["Replacement Schedule", "Maintaining support quality", "Replace every 1-2 years", "Essential for comfort", "Annual assessment"],
            ]
        elif "seasonal" in title_lower or "safety" in title_lower:
            return [
                ["Summer Heat Awareness", "Dogs and cats in warm weather", "Shade, hydration, cool surfaces", "Very High", "Daily monitoring"],
                ["Winter Cold Protection", "Outdoor-access pets", "Warm bedding, shorter walks", "High", "Daily checks"],
                ["Spring Allergy Season", "Allergy-prone pets", "Paw washing, vet allergy review", "Moderate", "Seasonal vet visit"],
                ["Autumn Hazards", "Conker/mushroom/firework risks", "Supervised outdoor time", "High", "Awareness and avoidance"],
                ["Holiday/Celebration Safety", "Pets around festivities", "Noise, food, decoration hazards", "High", "Event-by-event planning"],
            ]
        elif "first" in title_lower and "owner" in title_lower:
            return [
                ["Home Preparation", "Before bringing a dog home", "Safe spaces, supplies, pet-proofing", "Essential", "One-time setup"],
                ["Vet Registration", "Within first week", "Health check, vaccinations, microchip", "Essential", "First-week priority"],
                ["Routine Establishment", "First month at home", "Feeding, walking, toilet schedule", "Very High", "Daily consistency"],
                ["Basic Training Start", "First two weeks", "Name response, sit, house training", "Very High", "Daily short sessions"],
                ["Socialisation Plan", "8-16 weeks (puppies)", "Positive new experiences", "Very High", "Daily varied exposure"],
                ["Emergency Preparedness", "Before it is needed", "Vet number, first aid, insurance", "Essential", "One-time setup"],
            ]
        elif "multi" in title_lower and "pet" in title_lower:
            return [
                ["Gradual Introduction", "New pet joining household", "Slow, controlled first meetings", "Very High", "Days to weeks of patience"],
                ["Separate Resources", "Preventing conflict", "Individual bowls, beds, litter trays", "High", "Ongoing provision"],
                ["Supervised Interactions", "Building safe relationships", "Positive shared experiences", "High", "Daily monitoring"],
                ["Escape Routes and Safe Zones", "Cats in dog households", "High perches, gated areas", "Very High", "Permanent setup"],
                ["Feeding Separation", "Preventing food guarding", "Different rooms or times", "High", "Every mealtime"],
            ]
        elif "slow feeder" in title_lower:
            return [
                ["Maze Bowl Feeders", "Most speed-eating dogs", "Channels slow kibble access", "High (durable plastic)", "Daily wash"],
                ["Lick Mat Feeders", "Wet food or paste feeding", "Spreading and licking action", "High (silicone)", "Daily wash"],
                ["Snuffle Mat Feeders", "Dogs who love sniffing", "Nose-work foraging", "Moderate (fabric)", "Weekly wash"],
                ["Puzzle Box Feeders", "Smart, food-driven dogs", "Problem-solving to access food", "High (plastic/wood)", "Weekly clean"],
                ["Scatter Feeding (no bowl)", "All dogs, zero cost", "Spread food on ground/grass", "N/A", "None"],
            ]
        elif "cat tree" in title_lower:
            return [
                ["Tall Multi-Level Trees", "Active, climbing cats", "Vertical exercise and perching", "Good for active households", "Monthly stability check"],
                ["Compact Single-Post Trees", "Small spaces or kittens", "Basic scratching and resting", "Good for small flats", "Monthly check"],
                ["Wall-Mounted Systems", "Modern/minimalist homes", "Customisable climbing routes", "Space-efficient", "Quarterly bracket check"],
                ["Tree-with-Condo Combos", "Multi-cat households", "Private resting plus play", "Multi-cat suitability", "Monthly cleaning"],
                ["Ceiling-to-Floor Poles", "Very active cats", "Maximum climbing height", "Active cat households", "Monthly tension check"],
            ]
        else:
            return [
                ["Daily Exercise Routine", "Overall health and wellbeing", "Breed-appropriate physical activity", "Very High", "Daily time commitment"],
                ["Mental Enrichment Plan", "Preventing boredom behaviours", "Puzzles, training, scent work", "High", "Daily rotation"],
                ["Consistent Feeding Schedule", "Digestive health and weight", "Measured portions, set times", "Very High", "Twice daily"],
                ["Regular Health Checks", "Early issue detection", "Home checks between vet visits", "High", "Monthly self-checks"],
                ["Safe Environment Audit", "Hazard prevention", "Remove toxic plants, secure cables", "Essential", "Quarterly review"],
            ]

    # ── Puppy Care ──
    if cluster == "Puppy Care":
        if "development" in title_lower or "stage" in title_lower:
            return [
                ["Neonatal Period (0-2 weeks)", "Breeder awareness", "Birth to 2 weeks", "Minimal (mother-led)", "Overhandling too early"],
                ["Transitional Period (2-4 weeks)", "Early sensory development", "2-4 weeks", "Gentle daily handling", "Ignoring early stimulation"],
                ["Socialisation Window (3-14 weeks)", "Building confidence", "3-14 weeks", "Daily varied exposure", "Missing this critical window"],
                ["Juvenile Period (3-6 months)", "Basic training foundation", "3-6 months", "Daily structured sessions", "Inconsistent rules"],
                ["Adolescence (6-18 months)", "Handling regression", "6-18 months", "Patient reinforcement", "Giving up on training"],
                ["Social Maturity (1-3 years)", "Full behaviour emergence", "1-3 years", "Ongoing refinement", "Expecting puppy behaviour"],
            ]
        elif "essential" in title_lower or "key term" in title_lower:
            return [
                ["Crate Training Basics", "House training foundation", "8 weeks onwards", "Daily short sessions", "Using crate as punishment"],
                ["Socialisation Fundamentals", "Building a confident puppy", "8-16 weeks critical window", "Daily positive exposures", "Overwhelming the puppy"],
                ["House Training Routine", "Establishing toilet habits", "From day one at home", "Frequent outdoor trips", "Punishing indoor accidents"],
                ["Bite Inhibition Training", "Teaching gentle mouth use", "8-16 weeks", "Redirect during play", "Rough play encouragement"],
                ["Vet Visit Preparation", "Reducing clinic anxiety", "Before first vaccination", "Short positive visits", "Only visiting when ill"],
            ]
        elif "toy" in title_lower or "teething" in title_lower:
            return [
                ["Soft Rubber Teething Toys", "Sore gums during teething", "3-6 months teething peak", "Supervised daily chewing", "Giving hard bones too early"],
                ["Frozen Enrichment (wet cloth)", "Pain relief during teething", "4-6 months", "10-15 min supervised sessions", "Using ice directly on gums"],
                ["Small Plush Toys", "Comfort and gentle play", "8 weeks onwards", "Supervised play sessions", "Leaving unsupervised with stuffing"],
                ["Puppy Puzzle Toys", "Mental stimulation", "10 weeks onwards", "Short daily brain sessions", "Choosing too-difficult puzzles"],
                ["Tug Toys (gentle)", "Interactive bonding play", "12 weeks onwards", "Short gentle sessions", "Tugging too hard on young teeth"],
                ["Size-Appropriate Balls", "Fetch introduction", "12 weeks onwards", "Short outdoor sessions", "Using balls small enough to swallow"],
            ]
        else:
            return [
                ["Early Socialisation", "Building lifelong confidence", "8-16 weeks", "Daily positive experiences", "Waiting until fully vaccinated"],
                ["Consistent Routine", "Security and house training", "From day one", "Set daily schedule", "Irregular feeding/toilet times"],
                ["Positive-Only Training", "Foundation obedience", "8 weeks onwards", "5-10 min daily sessions", "Using punishment or dominance"],
                ["Supervised Free Time", "Safety and learning", "All waking hours initially", "Active monitoring", "Unsupervised roaming too early"],
                ["Gradual Independence", "Preventing separation anxiety", "From first week home", "Short alone-time increases", "Never leaving puppy alone to practise"],
            ]

    # fallback
    return [
        ["Option A", "General purpose", "Primary consideration", "Widely suitable", "Low maintenance"],
        ["Option B", "Specific needs", "Secondary consideration", "Moderate suitability", "Moderate maintenance"],
        ["Option C", "Advanced users", "Specialised consideration", "Targeted suitability", "Higher maintenance"],
        ["Option D", "Budget-conscious", "Cost consideration", "Broadly suitable", "Minimal maintenance"],
        ["Option E", "Premium choice", "Quality consideration", "Selective suitability", "Regular maintenance"],
    ]


def build_table_html(columns, rows):
    """Build the WordPress Gutenberg table block."""
    header_cells = "".join(f"<th>{col}</th>" for col in columns)
    body_rows = ""
    for row in rows:
        cells = "".join(f"<td>{cell}</td>" for cell in row)
        body_rows += f"<tr>{cells}</tr>\n"

    table_html = f"""<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">Quick Comparison</h3>
<!-- /wp:heading -->
<!-- wp:table {{"className":"is-style-stripes"}} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr>{header_cells}</tr></thead><tbody>
{body_rows.strip()}
</tbody></table></figure>
<!-- /wp:table -->"""
    return table_html


def count_table_rows(content):
    """Count data rows in existing tables (tbody tr elements)."""
    # Find all tbody sections and count <tr> inside
    tbody_matches = re.findall(r'<tbody[^>]*>(.*?)</tbody>', content, re.DOTALL)
    max_rows = 0
    for tbody in tbody_matches:
        rows = re.findall(r'<tr[^>]*>', tbody)
        max_rows = max(max_rows, len(rows))
    return max_rows


def fetch_post(post_id):
    """Fetch post content from WP REST API."""
    url = f"{WP_API}/posts/{post_id}?_fields=id,title,content"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def update_post(post_id, new_content):
    """Update post content via WP REST API."""
    payload = {"content": new_content}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(payload, f, ensure_ascii=False)
        tmpfile = f.name

    url = f"{WP_API}/posts/{post_id}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH,
         "-d", f"@{tmpfile}",
         "-H", "Content-Type: application/json",
         "-X", "POST", url],
        capture_output=True, text=True, timeout=60
    )
    os.unlink(tmpfile)
    if result.returncode != 0:
        return False
    try:
        resp = json.loads(result.stdout)
        return "id" in resp
    except json.JSONDecodeError:
        return False


def insert_table_before_footer(content, table_html):
    """Insert table before the 'Our Editorial Standards' trust footer, or at the end."""
    # Look for the editorial standards section
    patterns = [
        r'(<!-- wp:heading[^>]*-->[\s\S]*?Our Editorial Standards[\s\S]*?<!-- /wp:heading -->)',
        r'(<!-- wp:separator[^>]*-->[\s\S]*?<!-- /wp:separator -->\s*<!-- wp:heading[^>]*-->[\s\S]*?(?:Editorial Standards|Trust|Transparency))',
        r'(<hr\s*class="wp-block-separator[^"]*"[^/]*/>\s*<!-- /wp:separator -->\s*\n\s*<!-- wp:heading)',
        r'(<!-- wp:separator\s*\{[^}]*\}\s*-->\s*<hr\s*class="wp-block-separator)',
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            insert_pos = match.start()
            return content[:insert_pos] + "\n\n" + table_html + "\n\n" + content[insert_pos:]

    # If no footer found, look for the last separator
    separators = list(re.finditer(r'<!-- wp:separator', content))
    if separators:
        insert_pos = separators[-1].start()
        return content[:insert_pos] + "\n\n" + table_html + "\n\n" + content[insert_pos:]

    # Fallback: insert before last closing element
    return content + "\n\n" + table_html


def remove_existing_small_table(content):
    """Remove existing comparison/quick comparison table if it has fewer than 4 rows."""
    # Find "Quick Comparison" heading + table block pattern
    pattern = r'(<!-- wp:heading[^>]*-->\s*<h[23][^>]*>Quick Comparison</h[23]>\s*<!-- /wp:heading -->\s*<!-- wp:table[^>]*-->.*?<!-- /wp:table -->)'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    if match:
        table_section = match.group(1)
        rows_in_table = count_table_rows(table_section)
        if rows_in_table < 4:
            content = content[:match.start()] + content[match.end():]
            return content, rows_in_table
    return content, -1


def main():
    # Load inventory
    posts = []
    with open(INVENTORY, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cluster = row.get('cluster', '')
            if cluster in TARGET_CLUSTERS:
                posts.append(row)

    print(f"Found {len(posts)} posts in target clusters")

    # Initialize log
    with open(LOG_FILE, 'w', newline='', encoding='utf-8') as logf:
        writer = csv.writer(logf)
        writer.writerow(["id", "title", "cluster", "had_table", "table_added", "rows_added", "status"])

    processed = 0
    added = 0
    upgraded = 0
    skipped = 0

    for post_info in posts:
        post_id = post_info['id']
        title = post_info['title']
        cluster = post_info['cluster']

        print(f"\n[{processed+1}/{len(posts)}] Processing: {title} (ID: {post_id}, Cluster: {cluster})")

        # Fetch post content
        data = fetch_post(post_id)
        time.sleep(DELAY)

        if not data:
            print(f"  ERROR: Could not fetch post {post_id}")
            with open(LOG_FILE, 'a', newline='', encoding='utf-8') as logf:
                csv.writer(logf).writerow([post_id, title, cluster, "unknown", "no", 0, "fetch_error"])
            processed += 1
            continue

        content = data.get('content', {}).get('rendered', '')
        if not content:
            content = data.get('content', '')
            if isinstance(content, dict):
                content = content.get('raw', content.get('rendered', ''))

        has_table = '<table' in content.lower()
        existing_rows = count_table_rows(content) if has_table else 0

        # Decide action
        if has_table and existing_rows >= 4:
            print(f"  SKIP: Already has table with {existing_rows} rows")
            with open(LOG_FILE, 'a', newline='', encoding='utf-8') as logf:
                csv.writer(logf).writerow([post_id, title, cluster, "yes", "no", 0, "skipped_adequate_table"])
            skipped += 1
            processed += 1
            continue

        # Need to add or upgrade table
        columns = COLUMN_SCHEMAS.get(cluster, ["Option", "Best For", "Key Consideration", "Suitability", "Maintenance"])
        rows = generate_table_rows(post_id, title, cluster)
        table_html = build_table_html(columns, rows)

        # For upgrade: need to fetch raw content
        url_raw = f"{WP_API}/posts/{post_id}?context=edit&_fields=id,content"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url_raw],
            capture_output=True, text=True, timeout=30
        )
        time.sleep(DELAY)

        try:
            raw_data = json.loads(result.stdout)
            raw_content = raw_data.get('content', {}).get('raw', '')
        except (json.JSONDecodeError, AttributeError):
            print(f"  ERROR: Could not get raw content for {post_id}")
            with open(LOG_FILE, 'a', newline='', encoding='utf-8') as logf:
                csv.writer(logf).writerow([post_id, title, cluster, str(has_table), "no", 0, "raw_fetch_error"])
            processed += 1
            continue

        if not raw_content:
            print(f"  ERROR: Empty raw content for {post_id}")
            with open(LOG_FILE, 'a', newline='', encoding='utf-8') as logf:
                csv.writer(logf).writerow([post_id, title, cluster, str(has_table), "no", 0, "empty_raw_content"])
            processed += 1
            continue

        action = "added"
        had_table_str = "no"

        if has_table and existing_rows < 4:
            # Remove old small table, then add new one
            raw_content, old_rows = remove_existing_small_table(raw_content)
            had_table_str = f"yes({old_rows}rows)"
            action = "upgraded"
            print(f"  UPGRADE: Removing {old_rows}-row table, adding {len(rows)}-row table")
        else:
            print(f"  ADD: Inserting new {len(rows)}-row comparison table")

        # Insert the new table
        new_content = insert_table_before_footer(raw_content, table_html)

        # Update the post
        success = update_post(post_id, new_content)
        time.sleep(DELAY)

        if success:
            status = f"table_{action}"
            if action == "upgraded":
                upgraded += 1
            else:
                added += 1
            print(f"  SUCCESS: Table {action} ({len(rows)} rows)")
        else:
            status = "update_failed"
            print(f"  ERROR: Update failed for {post_id}")

        with open(LOG_FILE, 'a', newline='', encoding='utf-8') as logf:
            csv.writer(logf).writerow([post_id, title, cluster, had_table_str, "yes" if success else "no", len(rows) if success else 0, status])

        processed += 1

    print(f"\n{'='*60}")
    print(f"PHASE 10AK COMPARISON SATURATION COMPLETE")
    print(f"{'='*60}")
    print(f"Total processed: {processed}")
    print(f"Tables added: {added}")
    print(f"Tables upgraded: {upgraded}")
    print(f"Skipped (adequate): {skipped}")
    print(f"Log: {LOG_FILE}")


if __name__ == "__main__":
    main()
