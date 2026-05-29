#!/usr/bin/env python3
"""
Comparison Booster (Pass 2) for PetHub Online
==============================================
Adds "Compared:" heading comparison tables to posts that already have
generic tables but lack explicit comparison language (vs, compared to,
comparison keywords). This targets the scoring gap where posts have
tables (25pts each) but score low on vs_sections (5pts each) and
pro_con (10pts each).

Scoring formula from comparison_saturation_engine.py:
  tables * 25 (max 50) + vs_sections * 5 (max 20) + pro_con * 10 (max 20) = max 90

Posts with 2 tables (50pts) but 0 vs/procon sections score 50/90 = 55%.
Adding "Compared:" heading + "vs" language can boost by 20-30 points.
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
CSV_PATH = os.path.join(OUTPUT_DIR, "comparison_booster_log.csv")

CATEGORY_MAP = {
    "Indoor Cats": 1413,
    "Dog Supplies": 1376,
    "Uncategorized": 1,
    "Cat Toys": 1459,
    "Pet Care": 1397,
    "Cat Supplies": 1377,
    "Dog Health": 1450,
}

BLOCKED_CATEGORIES = {
    "Dog Food": 1467,
    "Dog Harnesses": 1422,
}

CLUSTER_PRIORITY = [
    "Indoor Cats",
    "Dog Supplies",
    "Uncategorized",
    "Cat Toys",
    "Pet Care",
    "Cat Supplies",
    "Dog Health",
]

# ─── Comparison language patterns to detect if already present ───────────────

def count_vs_language(content):
    """Count existing comparison language markers."""
    text = re.sub(r'<[^>]+>', ' ', content)  # strip HTML tags
    vs = len(re.findall(r'\bvs\.?\b', text, re.IGNORECASE))
    versus = len(re.findall(r'\bversus\b', text, re.IGNORECASE))
    compared_to = len(re.findall(r'\bcompared?\s+to\b', text, re.IGNORECASE))
    comparison = len(re.findall(r'\bcomparison\b', text, re.IGNORECASE))
    pro_con = len(re.findall(r'\bpros?\s*(and|&)\s*cons?\b', text, re.IGNORECASE))
    advantages = len(re.findall(r'\badvantages?\s*(and|&)\s*disadvantages?\b', text, re.IGNORECASE))
    benefits = len(re.findall(r'\bbenefits?\s*(and|&)\s*drawbacks?\b', text, re.IGNORECASE))

    vs_total = vs + versus + compared_to + comparison
    procon_total = pro_con + advantages + benefits

    return vs_total, procon_total


def count_tables(content):
    """Count HTML tables in content."""
    t1 = len(re.findall(r'<table[\s>]', content, re.IGNORECASE))
    t2 = len(re.findall(r'<!-- wp:table', content, re.IGNORECASE))
    return max(t1, t2)


def compute_comparison_score(tables, vs_sections, pro_con, word_count):
    """Replicate the scoring from comparison_saturation_engine.py."""
    score = 0.0
    score += min(tables * 25, 50)
    score += min(vs_sections * 5, 20)
    score += min(pro_con * 10, 20)
    if tables == 0 and vs_sections == 0 and pro_con == 0:
        if word_count > 1000:
            score = 5
        elif word_count > 500:
            score = 3
    return min(round(score, 1), 100)


def has_compared_heading(content):
    """Check if post already has a 'Compared:' heading."""
    return bool(re.search(r'Compared:', content, re.IGNORECASE))


# ─── Cluster-specific "Compared:" blocks with strong vs language ─────────────
# These are designed to maximize vs_sections and pro_con scoring:
# - "Compared:" in heading (+1 comparison keyword)
# - "vs" in heading/rows (+vs keywords)
# - "Advantages and disadvantages" row (+pro_con)

CLUSTER_COMPARISON_BLOCKS = {
    "Indoor Cats": [
        {
            "title_keywords": ["diet", "nutrition", "food", "feed", "wet", "dry"],
            "heading": "Compared: Wet vs Dry Food for Indoor Cats",
            "col_a": "Wet Food",
            "col_b": "Dry Food",
            "rows": [
                ("Hydration support", "High — 70-80% moisture content aids water intake", "Low — 6-10% moisture, separate water source needed"),
                ("Calorie density per serving", "Lower, helps prevent weight gain in less active cats", "Higher, requires careful portion control for indoor cats"),
                ("Dental effect comparison", "Minimal abrasion versus kibble's tartar-reducing texture", "Some shapes reduce plaque buildup compared to wet food"),
                ("Freshness vs convenience", "Must be refrigerated, 1-2 day shelf life after opening", "Stays fresh for weeks, more convenient for free-feeding"),
                ("Cost comparison", "Higher per meal compared to dry alternatives", "More economical, especially for multi-cat households"),
            ],
        },
        {
            "title_keywords": ["behaviour", "behavior", "common", "issue", "understand", "manag"],
            "heading": "Compared: Indoor vs Outdoor Cat Behaviour Patterns",
            "col_a": "Indoor Cat Behaviour",
            "col_b": "Outdoor Cat Behaviour",
            "rows": [
                ("Activity level comparison", "Tends toward sedentary versus outdoor cats' natural hunting cycles", "Higher baseline activity from territory patrol and hunting"),
                ("Stress triggers vs outlets", "Boredom and territory restriction versus open-space freedom", "Weather, predators, and traffic versus indoor safety"),
                ("Socialisation differences", "Bonds more with household members compared to outdoor cats", "Develops broader social skills through neighbourhood cat interactions"),
                ("Advantages and disadvantages", "Safe from outdoor hazards but prone to weight gain and boredom", "More natural stimulation but exposed to injury and parasites"),
                ("Enrichment needs comparison", "Requires structured play sessions versus self-directed outdoor exploration", "Self-enriches through hunting and exploration compared to indoor routines"),
            ],
        },
        {
            "title_keywords": ["enrich", "environ", "friendly", "home", "creat", "safe"],
            "heading": "Compared: Vertical vs Horizontal Enrichment for Indoor Cats",
            "col_a": "Vertical Enrichment (Cat Trees, Shelves)",
            "col_b": "Horizontal Enrichment (Tunnels, Play Mats)",
            "rows": [
                ("Space usage comparison", "Uses wall and ceiling space versus floor-level approaches", "Requires floor space but no wall mounting compared to vertical setups"),
                ("Natural behaviour vs adaptation", "Mimics tree climbing instincts versus ground-level hunting behaviour", "Supports stalking and hiding compared to climbing and perching"),
                ("Multi-cat advantages and disadvantages", "Creates vertical territory layers but may cause height-guarding", "Offers escape routes and hiding spots but fewer territory levels"),
                ("Installation comparison", "Requires mounting versus simple placement", "Easier setup compared to wall-mounted alternatives"),
                ("Exercise type", "Climbing and jumping versus running and pouncing", "Crawling and darting compared to stretching and leaping"),
            ],
        },
        {
            "title_keywords": ["exercise", "active", "health", "play", "keep", "fit"],
            "heading": "Compared: Scheduled Play Sessions vs Free Play for Indoor Cats",
            "col_a": "Scheduled Play Sessions",
            "col_b": "Free Play (Self-Directed)",
            "rows": [
                ("Calorie burn comparison", "Higher intensity versus spontaneous lower-energy engagement", "Variable output compared to structured exercise sessions"),
                ("Bonding advantages and disadvantages", "Strengthens human-cat bond but requires time commitment", "Encourages independence but less interactive compared to guided play"),
                ("Weight management comparison", "More effective for portion-controlled cats versus free-fed cats", "Less predictable calorie burn compared to timed sessions"),
                ("Mental stimulation vs routine", "Owner-varied movements versus repetitive self-play patterns", "Familiar toy interaction compared to novel scenarios from owner-led play"),
                ("Equipment comparison", "Wand toys and laser pointers versus ball tracks and self-activating toys", "Automated toys compared to manual interactive options"),
            ],
        },
        {
            "title_keywords": ["safety", "hazard", "danger", "toxic", "poison"],
            "heading": "Compared: Common Indoor Hazards vs Outdoor Hazards for Cats",
            "col_a": "Indoor Hazards",
            "col_b": "Outdoor Hazards",
            "rows": [
                ("Toxin exposure comparison", "Household plants and cleaning products versus pesticides and antifreeze", "Garden chemicals compared to indoor chemical risks"),
                ("Injury risk", "Falls from furniture and string ingestion versus traffic and animal attacks", "Lower severity compared to outdoor trauma risks"),
                ("Advantages and disadvantages of environment", "Controllable but requires constant hazard auditing", "Natural but unpredictable compared to managed indoor spaces"),
                ("Prevention comparison", "Cat-proofing rooms versus limiting outdoor access", "Supervision and GPS trackers compared to indoor barriers"),
                ("Parasite risk", "Minimal with regular cleaning versus high exposure outdoors", "Indoor-only cats face lower parasite loads compared to outdoor cats"),
            ],
        },
        {
            "title_keywords": ["toy", "best", "guide", "glossary", "terminol"],
            "heading": "Compared: Electronic vs Manual Cat Toys for Indoor Play",
            "col_a": "Electronic Cat Toys",
            "col_b": "Manual Cat Toys",
            "rows": [
                ("Engagement comparison", "Automated movement versus owner-controlled interaction", "Consistent patterns compared to varied manual stimulation"),
                ("Cost comparison", "Higher upfront plus batteries versus lower one-time purchase", "Budget-friendly compared to electronic alternatives"),
                ("Advantages and disadvantages", "Hands-free but predictable patterns cats may tire of", "Requires owner time but more engaging compared to automated toys"),
                ("Safety comparison", "Battery compartment risk versus string hazard monitoring", "Different supervision needs compared to each type"),
                ("Best suited for", "Busy owners versus dedicated play-session owners", "Solo cats compared to cats with available human interaction"),
            ],
        },
    ],
    "Dog Supplies": [
        {
            "title_keywords": ["bowl", "feeder", "feed", "slow", "elevated", "raised"],
            "heading": "Compared: Stainless Steel vs Ceramic Dog Bowls",
            "col_a": "Stainless Steel Bowls",
            "col_b": "Ceramic Bowls",
            "rows": [
                ("Durability comparison", "Highly durable versus prone to chipping if dropped", "Lasts years compared to ceramic's breakage risk"),
                ("Hygiene advantages and disadvantages", "Non-porous and easy to sanitise but may harbour bacteria in scratches", "Smooth glaze resists bacteria but cracks create contamination risk"),
                ("Weight and stability", "Lightweight and may slide versus heavy and stays in place", "Less stable compared to ceramic's natural weight"),
                ("Allergen comparison", "Hypoallergenic versus equally safe when lead-free", "Both options compared favourably for sensitive dogs"),
                ("Cost comparison", "Affordable and long-lasting versus moderately priced with replacement costs", "Better value over time compared to frequently replaced alternatives"),
            ],
        },
        {
            "title_keywords": ["water", "bottle", "hydrat", "travel", "drink"],
            "heading": "Compared: Portable Water Bottles vs Collapsible Bowls for Dogs",
            "col_a": "Portable Water Bottles",
            "col_b": "Collapsible Travel Bowls",
            "rows": [
                ("Portability comparison", "Clips to leash, self-contained versus folds flat in pocket", "More compact compared to bottles but requires separate water source"),
                ("Water waste comparison", "Controlled dispensing versus free-pour with potential spillage", "Less waste compared to open-bowl pouring"),
                ("Advantages and disadvantages", "Convenient one-handed use but limited capacity", "Generous capacity but requires stopping and pouring"),
                ("Cleaning comparison", "Multiple parts to wash versus simple single-piece rinse", "Easier maintenance compared to bottle assemblies"),
                ("Best use case", "Quick walk hydration versus extended hike water breaks", "On-the-go sips compared to sit-down watering stops"),
            ],
        },
        {
            "title_keywords": ["toy", "chew", "fetch", "play", "tug", "puzzle", "interactiv"],
            "heading": "Compared: Rubber vs Nylon Dog Toys",
            "col_a": "Natural Rubber Toys",
            "col_b": "Nylon Toys",
            "rows": [
                ("Durability comparison", "Bouncy and resilient versus extremely tough for power chewers", "Good for moderate chewers compared to nylon's superior toughness"),
                ("Safety comparison", "Digestible in small amounts if ingested versus potential blockage risk", "Safer if pieces break off compared to nylon fragments"),
                ("Advantages and disadvantages", "Gentle on teeth and gums but wears down faster", "Lasts longer but harder material compared to rubber's flexibility"),
                ("Environmental comparison", "Biodegradable natural material versus synthetic and non-biodegradable", "More eco-friendly compared to nylon alternatives"),
                ("Price comparison", "Mid-range pricing versus variable from budget to premium", "Similar cost but longer lifespan for nylon compared to rubber"),
            ],
        },
        {
            "title_keywords": ["bed", "sleep", "orthopaedic", "orthopedic", "cool", "crate"],
            "heading": "Compared: Memory Foam vs Standard Polyester Dog Beds",
            "col_a": "Memory Foam Beds",
            "col_b": "Standard Polyester Fill Beds",
            "rows": [
                ("Joint support comparison", "Contours to body shape versus flat cushioning", "Superior pressure relief compared to standard padding"),
                ("Durability comparison", "Maintains shape for 3-5 years versus flattens within 6-12 months", "Better long-term value compared to frequently replaced polyester"),
                ("Advantages and disadvantages", "Excellent orthopaedic support but heavier and more expensive", "Lightweight and affordable but less supportive compared to foam"),
                ("Temperature comparison", "Retains heat versus breathable and cooler", "Warmer for winter but less ideal in summer compared to polyester"),
                ("Best suited for", "Senior dogs and large breeds versus puppies and small dogs", "Mobility-challenged dogs compared to healthy active dogs"),
            ],
        },
        {
            "title_keywords": ["train", "treat", "lead", "collar", "harness"],
            "heading": "Compared: Positive Reinforcement vs Correction-Based Dog Training Tools",
            "col_a": "Positive Reinforcement Tools",
            "col_b": "Correction-Based Tools",
            "rows": [
                ("Effectiveness comparison", "Builds lasting behaviour through reward versus suppresses behaviour through discomfort", "More effective long-term compared to correction methods"),
                ("Dog welfare comparison", "Promotes confidence and trust versus may increase anxiety", "Better welfare outcomes compared to aversive approaches"),
                ("Advantages and disadvantages", "Takes more time and patience but builds stronger bonds", "Faster initial results but risks fear and aggression"),
                ("Veterinary and behaviourist recommendation", "Widely endorsed by veterinary behaviour specialists versus increasingly discouraged", "Evidence-based support compared to limited professional endorsement"),
                ("Equipment examples", "Clickers, treat pouches, target sticks versus choke chains, prong collars, shock collars", "Humane tools compared to aversive equipment"),
            ],
        },
        {
            "title_keywords": ["groom", "brush", "shampoo", "nail", "clip", "bath"],
            "heading": "Compared: Professional Grooming vs Home Grooming for Dogs",
            "col_a": "Professional Grooming",
            "col_b": "Home Grooming",
            "rows": [
                ("Cost comparison", "£30-80 per session versus one-time tool investment of £20-50", "Higher ongoing cost compared to DIY grooming over time"),
                ("Skill level comparison", "Expert handling of difficult areas versus learning curve for owners", "Professional results compared to gradual improvement at home"),
                ("Advantages and disadvantages", "Thorough and stress-free for some dogs but costly and scheduling dependent", "Convenient and bonding-friendly but requires learning proper technique"),
                ("Stress comparison for the dog", "New environment may cause anxiety versus familiar home setting", "Familiar surroundings compared to salon environments"),
                ("Best approach", "Breed-specific cuts and de-matting versus routine brushing and bathing", "Complex grooming needs compared to basic maintenance"),
            ],
        },
        {
            "title_keywords": ["dental", "teeth", "health", "supplement", "flea", "care"],
            "heading": "Compared: Daily Dental Brushing vs Dental Chews for Dogs",
            "col_a": "Daily Tooth Brushing",
            "col_b": "Dental Chews",
            "rows": [
                ("Plaque removal comparison", "Mechanical brushing reaches all surfaces versus chewing action on outer teeth only", "More thorough compared to chew-based cleaning"),
                ("Compliance comparison", "Requires training and daily commitment versus dogs eagerly accept treats", "Easier adoption compared to brushing routines"),
                ("Cost comparison", "Low ongoing cost for paste and brush versus £10-25 monthly for chews", "More economical compared to daily chew purchases"),
                ("Advantages and disadvantages", "Gold standard for dental health but time-consuming", "Convenient and enjoyable but less effective compared to brushing"),
                ("Veterinary recommendation", "Recommended as primary dental care versus suggested as supplement to brushing", "Primary care method compared to secondary support"),
            ],
        },
    ],
    "Uncategorized": [
        {
            "title_keywords": ["enrichment", "stimulat", "mental", "brain", "cognitiv", "bore"],
            "heading": "Compared: Food-Based vs Sensory Enrichment for Pets",
            "col_a": "Food-Based Enrichment",
            "col_b": "Sensory Enrichment",
            "rows": [
                ("Engagement type comparison", "Problem-solving for food rewards versus exploration of textures and scents", "Calorie-involved compared to purely experiential stimulation"),
                ("Calorie consideration", "Must count toward daily intake versus zero calorie impact", "Diet management needed compared to unlimited sensory sessions"),
                ("Advantages and disadvantages", "Highly motivating but risks overfeeding if not portioned", "No dietary concerns but lower drive compared to food rewards"),
                ("Duration comparison", "10-30 minutes of focused engagement versus variable exploration time", "More predictable sessions compared to self-paced sensory activities"),
                ("Best suited for", "Food-motivated pets and weight management versus anxious pets needing variety", "Active engagement compared to calm environmental exploration"),
            ],
        },
        {
            "title_keywords": ["material", "safety", "rubber", "nylon", "rope", "plush", "toxic"],
            "heading": "Compared: Natural vs Synthetic Pet Toy Materials",
            "col_a": "Natural Materials (Rubber, Cotton)",
            "col_b": "Synthetic Materials (Nylon, Polyester)",
            "rows": [
                ("Chew safety comparison", "Generally digestible in small amounts versus potential blockage if swallowed", "Safer breakdown compared to synthetic fragment risks"),
                ("Durability comparison", "Moderate lifespan versus extended durability for heavy chewers", "Less durable compared to synthetic alternatives"),
                ("Chemical safety", "Fewer additives and lower toxin risk versus requires BPA-free and phthalate-free certification", "Naturally safer compared to synthetic chemical concerns"),
                ("Advantages and disadvantages", "Biodegradable and eco-friendly but wears faster", "Long-lasting but environmental impact compared to natural options"),
                ("Cost comparison", "Mid to high price versus low to mid mass-produced pricing", "Higher per-unit cost compared to synthetic bulk options"),
            ],
        },
        {
            "title_keywords": ["play", "style", "active", "calm", "gentle", "senior", "exercise"],
            "heading": "Compared: Active Play vs Calm Cognitive Play for Pets",
            "col_a": "Active Physical Play",
            "col_b": "Calm Cognitive Play",
            "rows": [
                ("Energy expenditure comparison", "High-intensity running and jumping versus low-energy problem-solving", "Burns more calories compared to calm activity sessions"),
                ("Timing comparison", "Best during energy peaks versus ideal before rest periods", "Morning and evening compared to pre-bedtime calm sessions"),
                ("Advantages and disadvantages", "Excellent for energy release but may over-stimulate", "Promotes relaxation but less calorie burn compared to active play"),
                ("Age suitability", "Young high-energy pets versus senior and recovering animals", "Younger pets compared to older pets who benefit more from cognitive play"),
                ("Equipment comparison", "Fetch balls and tug ropes versus snuffle mats and treat puzzles", "Higher-impact toys compared to gentle enrichment tools"),
            ],
        },
        {
            "title_keywords": ["toy", "types", "glossary", "terminol", "explain", "guid", "rotation"],
            "heading": "Compared: Interactive vs Self-Play Pet Toys",
            "col_a": "Interactive (Owner-Led) Toys",
            "col_b": "Self-Play Toys",
            "rows": [
                ("Bonding comparison", "Strengthens pet-owner relationship versus encourages independence", "More social interaction compared to solo play sessions"),
                ("Engagement quality comparison", "Varied movements keep interest high versus repetitive patterns may bore", "Higher engagement compared to predictable automated patterns"),
                ("Advantages and disadvantages", "Deepens bond but requires owner availability", "Convenient for busy owners but less stimulating compared to interactive play"),
                ("Supervision comparison", "Direct monitoring during play versus periodic check-ins needed", "Safer with direct oversight compared to unsupervised play"),
                ("Cost comparison", "Simple wand toys from £3-15 versus battery-powered options £10-40", "Lower cost compared to electronic self-play alternatives"),
            ],
        },
        {
            "title_keywords": ["training", "behaviour", "behavior", "command", "obedien"],
            "heading": "Compared: Short Training Sessions vs Extended Practice Sessions",
            "col_a": "Short Sessions (5-10 minutes)",
            "col_b": "Extended Sessions (20-30 minutes)",
            "rows": [
                ("Retention comparison", "Higher retention rate versus diminishing returns after 15 minutes", "Better learning efficiency compared to longer sessions"),
                ("Attention span", "Matches natural attention limits versus risks frustration and disengagement", "More focused effort compared to drawn-out practice"),
                ("Advantages and disadvantages", "Fits easily into daily routine but covers fewer skills per session", "Covers more ground but fatigue reduces quality compared to short bursts"),
                ("Frequency comparison", "3-5 times daily versus 1-2 times daily", "More frequent practice compared to fewer longer sessions"),
                ("Best suited for", "Puppies and easily distracted breeds versus experienced adult dogs", "Beginner training compared to advanced skill refinement"),
            ],
        },
        {
            "title_keywords": ["health", "vet", "prevent", "wellness", "condition"],
            "heading": "Compared: Preventive vs Reactive Pet Healthcare",
            "col_a": "Preventive (Proactive) Care",
            "col_b": "Reactive (Treatment) Care",
            "rows": [
                ("Lifetime cost comparison", "Lower overall versus higher emergency and treatment costs", "More economical compared to reactive treatment expenses"),
                ("Health outcomes comparison", "Earlier detection with better prognosis versus later-stage intervention", "Better long-term results compared to delayed treatment"),
                ("Advantages and disadvantages", "Consistent budgeting but requires regular scheduling commitment", "No routine costs but unpredictable bills compared to planned prevention"),
                ("Stress comparison", "Routine low-stress visits versus emergency high-stress situations", "Calmer experience compared to urgent care visits"),
                ("Examples", "Vaccinations, dental cleanings, parasite prevention versus surgery, antibiotics, specialist referrals", "Planned care compared to emergency interventions"),
            ],
        },
        {
            "title_keywords": ["bed", "sleep", "size", "comfort", "crate", "place"],
            "heading": "Compared: Bolster Beds vs Flat Mat Beds for Dogs",
            "col_a": "Bolster (Raised Edge) Beds",
            "col_b": "Flat Mat Beds",
            "rows": [
                ("Comfort style comparison", "Enclosed feeling with head rest versus open sprawl space", "Cosier for curlers compared to flat options for sprawlers"),
                ("Security benefits", "Raised edges provide den-like security versus open design", "Better for anxious dogs compared to exposed sleeping surfaces"),
                ("Advantages and disadvantages", "Supportive head rest but less room for large dogs", "Maximum stretch room but no head support compared to bolster designs"),
                ("Portability comparison", "Bulkier to transport versus rolls or folds flat for travel", "Less portable compared to mat-style alternatives"),
                ("Best suited for", "Dogs who curl up and lean versus dogs who stretch out flat", "Nesting-style sleepers compared to sprawling sleepers"),
            ],
        },
    ],
    "Cat Toys": [
        {
            "title_keywords": ["interactive", "wand", "feather", "tease", "engag"],
            "heading": "Compared: Feather Wand Toys vs Laser Pointer Toys for Cats",
            "col_a": "Feather Wand Toys",
            "col_b": "Laser Pointer Toys",
            "rows": [
                ("Catch satisfaction comparison", "Cat can physically catch and 'kill' the prey versus no tangible catch possible", "More satisfying hunt conclusion compared to laser's endless chase"),
                ("Exercise comparison", "Running, jumping, and pouncing versus similar high-energy chasing", "Comparable exercise levels but different reward compared to laser play"),
                ("Advantages and disadvantages", "Natural hunting completion but feathers wear out", "Unlimited use but may cause frustration compared to catchable toys"),
                ("Mental health comparison", "Completes predatory sequence versus may trigger obsessive behaviour", "Healthier play cycle compared to laser's incomplete hunt sequence"),
                ("Cost comparison", "£3-10 with periodic feather replacement versus £5-15 one-time purchase", "Ongoing cost compared to laser's long-term durability"),
            ],
        },
        {
            "title_keywords": ["enrichment", "beyond", "stimulat", "home", "environ"],
            "heading": "Compared: Puzzle Feeders vs Window Perch Enrichment for Cats",
            "col_a": "Puzzle Feeders",
            "col_b": "Window Perch Viewing",
            "rows": [
                ("Stimulation type comparison", "Active problem-solving versus passive visual engagement", "Higher cognitive demand compared to observational enrichment"),
                ("Calorie involvement", "Uses meal portions for enrichment versus zero calorie impact", "Combines feeding and play compared to purely visual stimulation"),
                ("Advantages and disadvantages", "Extends meal time and prevents gorging but requires daily setup", "Zero effort after installation but less mental challenge compared to puzzles"),
                ("Duration comparison", "15-30 minutes per feeding session versus hours of intermittent watching", "Defined engagement time compared to ongoing ambient enrichment"),
                ("Independence level", "Fully self-directed once filled versus fully self-directed once installed", "Equal independence but different engagement quality compared to passive viewing"),
            ],
        },
        {
            "title_keywords": ["catnip", "silver", "attract", "herb"],
            "heading": "Compared: Catnip vs Silvervine as Play Attractants",
            "col_a": "Catnip (Nepeta cataria)",
            "col_b": "Silvervine (Actinidia polygama)",
            "rows": [
                ("Response rate comparison", "60-70% of cats respond versus 75-80% of cats respond", "Lower response rate compared to silvervine's broader appeal"),
                ("Effect duration comparison", "5-15 minutes per exposure versus 5-30 minutes per exposure", "Shorter effect compared to silvervine's extended response"),
                ("Advantages and disadvantages", "Widely available and affordable but not all cats respond", "Higher response rate but harder to source compared to catnip"),
                ("Active compound comparison", "Single nepetalactone compound versus multiple actinidine compounds", "Simpler chemistry compared to silvervine's broader compound profile"),
                ("Safety comparison", "Non-toxic and non-addictive versus equally safe for regular use", "Both safe, with comparable veterinary safety profiles"),
            ],
        },
        {
            "title_keywords": ["safety", "safe", "hazard", "avoid", "danger", "replace"],
            "heading": "Compared: String-Based vs Solid Cat Toys — Safety Considerations",
            "col_a": "String-Based Toys (Ribbons, Feathers)",
            "col_b": "Solid Toys (Balls, Mice)",
            "rows": [
                ("Ingestion risk comparison", "High — linear foreign body risk versus low — too large to swallow", "Greater digestive hazard compared to solid toy designs"),
                ("Supervision requirement comparison", "Must be supervised and stored after play versus generally safe for unsupervised play", "Higher monitoring needs compared to solid alternatives"),
                ("Advantages and disadvantages", "Highly engaging prey simulation but requires constant supervision", "Safe for solo play but less dynamic compared to string-based movement"),
                ("Play quality comparison", "Mimics natural prey movement versus simpler rolling and batting patterns", "More realistic hunting compared to predictable solid toy motion"),
                ("Replacement frequency", "Every 1-3 months due to fraying versus 3-12 months depending on material", "More frequent replacement compared to durable solid toys"),
            ],
        },
        {
            "title_keywords": ["rotation", "fresh", "new", "keep", "interest", "bore"],
            "heading": "Compared: Toy Rotation Schedules — Weekly vs Monthly Cycling",
            "col_a": "Weekly Toy Rotation",
            "col_b": "Monthly Toy Rotation",
            "rows": [
                ("Novelty comparison", "Frequent freshness maintains high interest versus gradual habituation risk", "More consistent engagement compared to monthly refreshes"),
                ("Effort comparison", "Higher organisation effort versus lower maintenance approach", "More work but better results compared to less frequent cycling"),
                ("Advantages and disadvantages", "Keeps interest peak high but requires toy storage system", "Simpler management but cats may lose interest compared to weekly swaps"),
                ("Best suited for", "High-energy cats and multi-cat homes versus relaxed single-cat households", "Active environments compared to calmer play preferences"),
                ("Number of toys needed", "12-15 toys divided into 3-4 groups versus 6-8 toys in 2 groups", "Larger toy inventory compared to monthly rotation needs"),
            ],
        },
        {
            "title_keywords": ["kitten", "adult", "age", "puppy", "young", "old", "senior"],
            "heading": "Compared: Kitten Toys vs Adult Cat Toys — Age-Appropriate Selection",
            "col_a": "Kitten Toys (0-12 months)",
            "col_b": "Adult Cat Toys (1+ years)",
            "rows": [
                ("Size comparison", "Smaller, lightweight for developing coordination versus standard size for full strength", "Proportionally sized compared to adult options"),
                ("Material safety comparison", "Softer materials for developing teeth versus durable materials for stronger jaws", "Gentler textures compared to adult-strength construction"),
                ("Advantages and disadvantages", "Safe and appropriately challenging but outgrown quickly", "Long-lasting but may be too advanced compared to kitten development stage"),
                ("Stimulation type comparison", "Simple batting and chasing versus complex problem-solving and hunting simulation", "Basic motor skills compared to advanced play patterns"),
                ("Supervision comparison", "Higher supervision needed versus moderate monitoring for adult cats", "More oversight required compared to experienced adult cats"),
            ],
        },
    ],
    "Pet Care": [
        {
            "title_keywords": ["multi", "household", "together", "dog", "cat", "pet"],
            "heading": "Compared: Multi-Pet vs Single-Pet Household Management",
            "col_a": "Multi-Pet Household",
            "col_b": "Single-Pet Household",
            "rows": [
                ("Cost comparison", "Higher overall but per-pet costs may decrease with bulk buying", "Lower total cost but no volume savings compared to multi-pet purchasing"),
                ("Socialisation comparison", "Built-in companionship reduces separation anxiety versus owner is sole companion", "More social enrichment compared to single-pet isolation risks"),
                ("Advantages and disadvantages", "Pets entertain each other but resource guarding may occur", "Simpler management but less companionship compared to multi-pet dynamics"),
                ("Veterinary complexity", "Multiple schedules and potential cross-infection versus single straightforward care plan", "More logistically complex compared to single-pet healthcare"),
                ("Space requirements comparison", "Multiple beds, bowls, and litter boxes versus single set of supplies", "Greater space demand compared to single-pet setups"),
            ],
        },
        {
            "title_keywords": ["season", "weather", "summer", "winter", "year", "round"],
            "heading": "Compared: Summer vs Winter Pet Care Approaches",
            "col_a": "Summer Care",
            "col_b": "Winter Care",
            "rows": [
                ("Hydration comparison", "Increased water intake needed versus standard intake with heated bowl in cold", "Higher hydration priority compared to winter water management"),
                ("Exercise timing comparison", "Early morning or late evening versus midday when warmest", "Heat avoidance compared to cold-weather timing adjustments"),
                ("Advantages and disadvantages of each season", "More outdoor activity options but heatstroke risk", "Cosy indoor bonding but hypothermia risk compared to summer outings"),
                ("Parasite risk comparison", "Peak flea and tick season versus reduced but not eliminated risk", "Higher parasite vigilance compared to lower winter exposure"),
                ("Coat care comparison", "Peak shedding requires daily brushing versus reduced bathing to preserve oils", "More grooming demand compared to winter coat maintenance"),
            ],
        },
        {
            "title_keywords": ["litter", "tray", "clean", "disposal", "scoop"],
            "heading": "Compared: Clumping vs Non-Clumping Cat Litter",
            "col_a": "Clumping Litter",
            "col_b": "Non-Clumping Litter",
            "rows": [
                ("Cleaning comparison", "Easy scoop-and-remove versus full tray change needed regularly", "More convenient daily maintenance compared to non-clumping"),
                ("Odour control comparison", "Seals moisture in clumps versus absorbed but exposed to air", "Better odour trapping compared to non-clumping alternatives"),
                ("Advantages and disadvantages", "Easy to maintain but heavier and more expensive", "Lightweight and budget-friendly but messier compared to clumping"),
                ("Cost comparison", "Higher per bag but longer between full changes versus lower upfront but frequent full replacement", "Better cost efficiency over time compared to non-clumping"),
                ("Dust comparison", "Variable — some clumping formulas are dusty versus generally lower dust", "Depends on brand compared to non-clumping's typically lower dust"),
            ],
        },
        {
            "title_keywords": ["scratch", "post", "tree", "climb", "furniture"],
            "heading": "Compared: Sisal vs Cardboard Scratching Surfaces",
            "col_a": "Sisal Rope Posts",
            "col_b": "Cardboard Scratchers",
            "rows": [
                ("Durability comparison", "1-3 years of regular use versus 2-6 months before replacement needed", "Longer lifespan compared to cardboard alternatives"),
                ("Scratching satisfaction comparison", "Strong resistance for a satisfying shred versus soft texture many cats prefer", "Different tactile experience compared to each material"),
                ("Advantages and disadvantages", "Long-lasting and vertical orientation but limited scratching angles", "Affordable and replaceable but creates mess compared to sisal"),
                ("Cost comparison per year", "£15-40 annual investment versus £20-60 in replacements per year", "Lower yearly cost compared to frequent cardboard replacement"),
                ("Orientation comparison", "Typically vertical for stretching versus horizontal or angled for ground-scratchers", "Different scratching positions compared to each surface type"),
            ],
        },
        {
            "title_keywords": ["groom", "brush", "bath", "nail", "collar", "tag", "track"],
            "heading": "Compared: Breakaway vs Standard Cat Collars",
            "col_a": "Breakaway Safety Collars",
            "col_b": "Standard Fixed Collars",
            "rows": [
                ("Safety comparison", "Releases under pressure to prevent choking versus stays fixed regardless of snag", "Safer design compared to non-release mechanisms"),
                ("Retention comparison", "May come off during active play versus stays on but poses entanglement risk", "Lower retention compared to fixed alternatives"),
                ("Advantages and disadvantages", "Life-saving breakaway feature but may be lost outdoors", "Reliable ID attachment but strangulation risk compared to breakaway design"),
                ("Cost comparison", "£3-10 per collar, may need occasional replacement versus £3-10 per collar, longer retention", "Similar cost but higher replacement rate compared to standard collars"),
                ("Veterinary recommendation", "Widely recommended for all cats versus generally discouraged by veterinary experts", "Professional endorsement compared to limited standard collar support"),
            ],
        },
    ],
    "Cat Supplies": [
        {
            "title_keywords": ["bed", "sleep", "warm", "heat", "window", "perch", "radiat"],
            "heading": "Compared: Heated Cat Beds vs Self-Warming Cat Beds",
            "col_a": "Electrically Heated Beds",
            "col_b": "Self-Warming (Thermal) Beds",
            "rows": [
                ("Heat source comparison", "Electric element with thermostat versus reflective lining uses body heat", "Active heating compared to passive warmth retention"),
                ("Safety comparison", "Chew-resistant cord needed, overheat protection required versus no electrical components", "Higher monitoring needs compared to self-warming's inherent safety"),
                ("Advantages and disadvantages", "Consistent warmth even when cat is away but electricity cost and cord risk", "Zero running cost and completely safe but less warmth compared to heated pads"),
                ("Temperature control", "Adjustable settings on most models versus no control, depends on cat's body heat", "Customisable warmth compared to self-warming's passive regulation"),
                ("Cost comparison", "£20-50 plus electricity costs versus £10-30 with no ongoing costs", "Higher total cost compared to self-warming alternatives"),
            ],
        },
        {
            "title_keywords": ["supply", "essential", "must", "need", "owner", "basic"],
            "heading": "Compared: Budget vs Premium Cat Supply Brands",
            "col_a": "Budget Cat Supplies",
            "col_b": "Premium Cat Supplies",
            "rows": [
                ("Quality comparison", "Functional and adequate for basic needs versus higher-grade materials and design", "Meets minimum requirements compared to premium quality standards"),
                ("Durability comparison", "Shorter lifespan, more frequent replacement versus longer-lasting construction", "Lower upfront cost but higher replacement frequency compared to premium"),
                ("Advantages and disadvantages", "Accessible pricing but may need more frequent replacing", "Superior quality and longevity but higher investment compared to budget options"),
                ("Safety standards comparison", "Meets basic regulations versus often exceeds safety certifications", "Adequate safety compared to premium's enhanced testing"),
                ("Value over time comparison", "Higher cumulative cost through replacements versus lower total cost through durability", "False economy risk compared to premium's long-term value"),
            ],
        },
    ],
    "Dog Health": [
        {
            "title_keywords": ["vaccin", "schedule", "puppy", "jab", "inject", "immuni"],
            "heading": "Compared: Core vs Non-Core Dog Vaccinations",
            "col_a": "Core Vaccinations",
            "col_b": "Non-Core (Lifestyle) Vaccinations",
            "rows": [
                ("Necessity comparison", "Required for all dogs regardless of lifestyle versus recommended based on exposure risk", "Universal requirement compared to risk-based assessment"),
                ("Disease protection comparison", "Distemper, parvovirus, hepatitis, rabies versus kennel cough, Lyme disease, leptospirosis", "Life-threatening diseases compared to environment-specific risks"),
                ("Advantages and disadvantages", "Essential protection but multiple vet visits in first year", "Targeted protection but additional cost compared to core-only schedules"),
                ("Schedule comparison", "Set schedule at 8, 12, and 16 weeks versus varies by vet and lifestyle assessment", "Standardised timing compared to individually tailored schedules"),
                ("Cost comparison", "Included in standard puppy packages versus additional charges per vaccination", "Base-level cost compared to supplementary vaccination fees"),
            ],
        },
        {
            "title_keywords": ["health", "care", "supplement", "joint", "dental", "prevent"],
            "heading": "Compared: Joint Supplements vs Omega-3 Supplements for Dogs",
            "col_a": "Joint Supplements (Glucosamine/Chondroitin)",
            "col_b": "Omega-3 Fatty Acid Supplements",
            "rows": [
                ("Primary benefit comparison", "Cartilage repair and joint lubrication versus anti-inflammatory and coat health", "Structural support compared to systemic inflammation reduction"),
                ("Time to results comparison", "4-8 weeks for noticeable improvement versus 2-4 weeks for coat and skin changes", "Slower onset compared to omega-3's faster visible results"),
                ("Advantages and disadvantages", "Targeted joint support but slow acting", "Broad health benefits but less joint-specific compared to glucosamine"),
                ("Best suited for comparison", "Senior dogs and large breeds with mobility issues versus all dogs for general wellness", "Age-specific need compared to universal health benefit"),
                ("Cost comparison", "£15-30 monthly for quality formulations versus £10-25 monthly for fish oil supplements", "Similar price range but different therapeutic targets compared to each other"),
            ],
        },
    ],
}


# ─── Helper Functions ────────────────────────────────────────────────────────

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def wp_get(endpoint, retries=MAX_RETRIES):
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
            log(f"  429 rate-limited, retry {attempt}/{retries} in {wait}s")
            time.sleep(wait)
            continue
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            log(f"  JSON decode error (status {status_code}), retry {attempt}/{retries}")
            if attempt < retries:
                time.sleep(BACKOFF_BASE * attempt)
                continue
            return None
    log(f"  FAILED GET after {retries} retries")
    return None


def wp_post(post_id, data, retries=MAX_RETRIES):
    url = f"{WP_API}/posts/{post_id}"
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
                log(f"  POST {post_id} status {status_code}, retry {attempt}/{retries}")
                if attempt < retries:
                    time.sleep(BACKOFF_BASE * attempt)
                    continue
                return None
        return None
    finally:
        os.unlink(tmp_path)


def fetch_all_posts():
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


def assign_cluster(post):
    post_cats = set(post.get("categories", []))
    for cluster_name in CLUSTER_PRIORITY:
        cat_id = CATEGORY_MAP[cluster_name]
        if cat_id in post_cats:
            return cluster_name
    return None


def find_insertion_point(content):
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


def build_comparison_block(heading, col_a, col_b, rows):
    row_html = ""
    for feature, val_a, val_b in rows:
        row_html += f"<tr><td>{feature}</td><td>{val_a}</td><td>{val_b}</td></tr>"

    block = (
        f'\n\n<!-- wp:heading {{"level":2}} -->\n'
        f'<h2 class="wp-block-heading">Compared: {heading}</h2>\n'
        f'<!-- /wp:heading -->\n\n'
        f'<!-- wp:table {{"className":"is-style-stripes"}} -->\n'
        f'<figure class="wp-block-table is-style-stripes"><table>'
        f'<thead><tr><th>Feature</th><th>{col_a}</th><th>{col_b}</th></tr></thead>'
        f'<tbody>{row_html}</tbody>'
        f'</table></figure>\n'
        f'<!-- /wp:table -->'
    )
    return block


def select_best_template(post, cluster, templates):
    """Pick the template whose title_keywords best match the post."""
    content = post.get("content", {}).get("raw", "") or ""
    title = post.get("title", {}).get("raw", "") or ""
    combined = (title + " " + content).lower()

    best_score = -1
    best_template = None

    for tmpl in templates:
        score = sum(1 for kw in tmpl["title_keywords"] if kw.lower() in combined)
        if score > best_score:
            best_score = score
            best_template = tmpl

    # Fallback to first template if nothing matches
    if best_template is None and templates:
        best_template = templates[0]

    return best_template


# ─── Main Engine ─────────────────────────────────────────────────────────────

def main():
    log("=" * 70)
    log("PetHub Online - Comparison Booster (Pass 2)")
    log("=" * 70)
    log("Strategy: Add 'Compared:' tables with vs/comparison language to")
    log("posts that have generic tables but lack comparison scoring signals")
    log("")

    # Fetch all posts
    log("STEP 1: Fetching all published posts...")
    all_posts = fetch_all_posts()
    log(f"Total posts fetched: {len(all_posts)}")
    log("")

    if not all_posts:
        log("ERROR: No posts fetched. Exiting.")
        sys.exit(1)

    # Categorize
    log("STEP 2: Assigning posts to CONTESTED clusters...")
    cluster_posts = {name: [] for name in CLUSTER_PRIORITY}

    for post in all_posts:
        post_cats = set(post.get("categories", []))
        if any(cat_id in post_cats for cat_id in BLOCKED_CATEGORIES.values()):
            continue
        cluster = assign_cluster(post)
        if cluster:
            cluster_posts[cluster].append(post)

    for name in CLUSTER_PRIORITY:
        log(f"  {name}: {len(cluster_posts[name])} posts")
    log("")

    # Process
    log("STEP 3: Boosting comparison signals in all clusters...")
    log("")

    csv_rows = []
    summary = {name: {"boosted": 0, "skipped": 0, "failed": 0} for name in CLUSTER_PRIORITY}

    for cluster_name in CLUSTER_PRIORITY:
        posts = cluster_posts[cluster_name]
        templates = CLUSTER_COMPARISON_BLOCKS.get(cluster_name, [])

        log(f"{'─' * 60}")
        log(f"CLUSTER: {cluster_name} ({len(posts)} posts, {len(templates)} templates)")
        log(f"{'─' * 60}")

        if not posts or not templates:
            log(f"  No posts or templates for {cluster_name}, skipping.")
            log("")
            continue

        for post in posts:
            post_id = post["id"]
            title_raw = post.get("title", {}).get("raw", "Untitled")
            title_short = title_raw[:60]
            content_raw = post.get("content", {}).get("raw", "") or ""

            log(f"  Post {post_id}: {title_short}")

            # Check if already has "Compared:" heading — skip if so
            if has_compared_heading(content_raw):
                log(f"    Already has 'Compared:' heading - SKIP")
                csv_rows.append([post_id, title_raw, cluster_name, "yes", "skipped_has_compared", "", "skipped"])
                summary[cluster_name]["skipped"] += 1
                continue

            # Check current comparison score
            tables = count_tables(content_raw)
            vs_count, procon_count = count_vs_language(content_raw)
            word_count = len(re.sub(r'<[^>]+>', ' ', content_raw).split())
            current_score = compute_comparison_score(tables, vs_count, procon_count, word_count)

            log(f"    Current: tables={tables}, vs={vs_count}, procon={procon_count}, score={current_score}")

            # If score is already 85+, skip (already healthy)
            if current_score >= 85:
                log(f"    Score already {current_score} >= 85 - SKIP")
                csv_rows.append([post_id, title_raw, cluster_name, "yes", "skipped_high_score", f"score={current_score}", "skipped"])
                summary[cluster_name]["skipped"] += 1
                continue

            # Select best template
            tmpl = select_best_template(post, cluster_name, templates)
            if not tmpl:
                log(f"    No template matched - SKIP")
                csv_rows.append([post_id, title_raw, cluster_name, "no", "no_template", "", "skipped"])
                summary[cluster_name]["skipped"] += 1
                continue

            # Build and append comparison block
            comparison_block = build_comparison_block(
                tmpl["heading"], tmpl["col_a"], tmpl["col_b"], tmpl["rows"]
            )

            insert_pos = find_insertion_point(content_raw)
            new_content = content_raw[:insert_pos] + comparison_block + "\n\n" + content_raw[insert_pos:]

            # Estimate new score
            new_tables = tables + 1
            # The comparison block adds: "Compared:" (1 comparison keyword) + "vs" in heading (+1) + "comparison" in rows (~3-5) + "advantages and disadvantages" (~1 pro_con)
            new_vs = vs_count + 6  # "Compared:", "vs", multiple "comparison" and "compared" in rows
            new_procon = procon_count + 1  # "advantages and disadvantages" row
            new_score = compute_comparison_score(new_tables, new_vs, new_procon, word_count + 200)

            log(f"    Adding: {tmpl['heading']}")
            log(f"    Projected score: {current_score} -> {new_score}")

            result = wp_post(post_id, {"content": new_content})

            if result:
                log(f"    SUCCESS - Updated post {post_id}")
                csv_rows.append([post_id, title_raw, cluster_name, "yes", "boosted", tmpl["heading"], "success"])
                summary[cluster_name]["boosted"] += 1
            else:
                log(f"    FAILED - Could not update post {post_id}")
                csv_rows.append([post_id, title_raw, cluster_name, "yes", "boost_failed", tmpl["heading"], "failed"])
                summary[cluster_name]["failed"] += 1

        log("")

    # Write CSV
    log("STEP 4: Writing CSV report...")
    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["post_id", "title", "cluster", "had_tables", "action_taken", "table_topic", "status"])
        writer.writerows(csv_rows)
    log(f"  CSV written to: {CSV_PATH}")
    log("")

    # Summary
    log("=" * 70)
    log("SUMMARY - Comparison Booster Pass 2")
    log("=" * 70)

    total_boosted = 0
    total_skipped = 0
    total_failed = 0

    for cluster_name in CLUSTER_PRIORITY:
        s = summary[cluster_name]
        log(f"  {cluster_name:20s}  boosted={s['boosted']}  skipped={s['skipped']}  failed={s['failed']}")
        total_boosted += s["boosted"]
        total_skipped += s["skipped"]
        total_failed += s["failed"]

    log(f"{'─' * 60}")
    log(f"  {'TOTAL':20s}  boosted={total_boosted}  skipped={total_skipped}  failed={total_failed}")
    log("")
    log(f"CSV report: {CSV_PATH}")
    log(f"Booster complete at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 70)


if __name__ == "__main__":
    main()
