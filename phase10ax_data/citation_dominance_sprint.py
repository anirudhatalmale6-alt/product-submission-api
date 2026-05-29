#!/usr/bin/env python3
"""
Phase 10AX — Citation Dominance Sprint
Clusters: Dog Food, Educational, Dog Training
Goal: Push citation confidence above 70 by adding comparison tables,
      Quick Checklists, What to Do Next boxes, UK enrichment, and
      extractable definitions.
"""

import subprocess
import json
import csv
import os
import time
import tempfile
import re
import html
from datetime import datetime

# ─── Configuration ───────────────────────────────────────────────────────────
WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ax_data"
LOG_FILE = os.path.join(DATA_DIR, "citation_dominance_log.csv")

DOG_FOOD_IDS = [5467, 5460, 3839, 3838, 3837, 3836, 7172]
EDUCATIONAL_IDS = [5521, 5462, 5424, 5419, 5416, 5415, 5414, 4574, 4272, 4265, 4216, 4167, 4160, 4146]
DOG_TRAINING_IDS = [5523, 5512, 5458, 5036, 4792, 4791, 4132, 4125, 4118]

ALL_POSTS = (
    [(pid, "Dog Food") for pid in DOG_FOOD_IDS] +
    [(pid, "Educational") for pid in EDUCATIONAL_IDS] +
    [(pid, "Dog Training") for pid in DOG_TRAINING_IDS]
)


# ─── API helpers ─────────────────────────────────────────────────────────────
def wp_get(endpoint):
    """GET from WP REST API using subprocess curl."""
    url = f"{WP_API}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl GET failed: {result.stderr}")
    return json.loads(result.stdout)


def wp_update(post_id, data):
    """POST update to WP REST API using subprocess curl with temp file."""
    url = f"{WP_API}/posts/{post_id}"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        tmppath = f.name
    try:
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", f"@{tmppath}",
             url],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            raise RuntimeError(f"curl POST failed: {result.stderr}")
        resp = json.loads(result.stdout)
        if "id" not in resp:
            raise RuntimeError(f"Update failed for {post_id}: {result.stdout[:500]}")
        return resp
    finally:
        os.unlink(tmppath)


# ─── Detection helpers ───────────────────────────────────────────────────────
def has_comparison_table(content):
    return "wp-block-table" in content and "<thead>" in content

def has_checklist(content):
    return "Quick Checklist" in content and "#f5f3ff" in content

def has_next_steps(content):
    return "What to Do Next" in content and "#f0fdfa" in content

def has_common_mistakes(content):
    return "Common Mistakes" in content

def has_key_terms(content):
    return "Key Terms" in content

def has_key_takeaways(content):
    return "Key Takeaways" in content

def has_trust_footer(content):
    return "trust-footer" in content.lower() or "editorial standards" in content.lower() or "independently researched" in content.lower()


# ─── Content generation — Comparison Tables ──────────────────────────────────
def generate_comparison_table(title, cluster):
    """Generate a cluster/topic-specific comparison table."""
    title_lower = title.lower()

    if cluster == "Dog Food":
        if "glossary" in title_lower or "ingredient" in title_lower or "nutrition" in title_lower or "label" in title_lower:
            return _table("Dog Food Ingredient Categories at a Glance", [
                ("Category", "Best For", "Considerations", "Suitability"),
            ], [
                ("Named Meat Meals (e.g. chicken meal)", "High protein on a budget", "Rendered; check source transparency", "Most adult dogs"),
                ("Fresh/Frozen Raw", "Maximum nutrient retention", "Requires careful handling; higher cost per kg", "Healthy adults with vet guidance"),
                ("Whole Grains (brown rice, oats)", "Sustained energy release", "Not suitable for grain-sensitive dogs", "Active breeds, working dogs"),
                ("Grain-Free (potato, legume base)", "Dogs with confirmed grain allergies", "Linked to DCM concerns — consult your vet", "Only with veterinary recommendation"),
                ("Novel Proteins (venison, duck)", "Elimination diets", "Higher price; limited availability in UK shops", "Allergy-prone dogs"),
                ("By-Products", "Budget-friendly formulas", "Quality varies widely; PFMA standards apply", "Non-sensitive dogs on a budget"),
                ("Added Supplements (glucosamine, omega-3)", "Joint and coat support", "Check mg per kg dosage on label", "Senior dogs, large breeds"),
            ])
        elif "puppy" in title_lower or "puppies" in title_lower:
            return _table("Puppy Food Comparison by Type", [
                ("Food Type", "Best For", "Considerations", "Suitability"),
            ], [
                ("Dry Kibble (puppy formula)", "Convenience and dental health", "Ensure meets FEDIAF growth standards", "All puppy breeds"),
                ("Wet/Canned Puppy Food", "Fussy eaters; hydration boost", "Higher cost per meal; shorter shelf life once opened", "Small breeds, picky puppies"),
                ("Raw Puppy Diet", "Owners committed to raw feeding", "Must be nutritionally complete — BVA advises caution for pups", "With veterinary supervision only"),
                ("Mixed Feeding (dry + wet)", "Balanced texture and nutrition", "Calculate total daily kcal to avoid overfeeding", "Most puppies over 8 weeks"),
                ("Breed-Specific Puppy Formulas", "Large or giant breed puppies", "Controlled calcium/phosphorus ratios for growth", "Large breeds (over 25 kg adult weight)"),
            ])
        elif "senior" in title_lower or "older" in title_lower or "ageing" in title_lower:
            return _table("Senior Dog Food Comparison", [
                ("Food Type", "Best For", "Considerations", "Suitability"),
            ], [
                ("Senior Dry Kibble", "Daily convenience and dental support", "Lower calorie density; added joint supplements", "Most dogs over 7 years"),
                ("Senior Wet Food", "Dogs with dental issues or low appetite", "Higher moisture aids hydration; check phosphorus levels", "Dogs with kidney concerns"),
                ("Prescription Senior Diets", "Dogs with diagnosed conditions", "Vet-authorised only; tailored nutrient profiles", "Dogs with renal, cardiac, or mobility issues"),
                ("Home-Cooked Senior Meals", "Owners wanting full ingredient control", "Must be balanced — consult a veterinary nutritionist", "With professional guidance"),
                ("Senior Supplements (added to food)", "Targeted joint or cognitive support", "Glucosamine, omega-3, antioxidants — check dosages", "As complement to complete diet"),
            ])
        elif "allerg" in title_lower or "sensitiv" in title_lower:
            return _table("Allergy-Friendly Dog Food Options", [
                ("Food Type", "Best For", "Considerations", "Suitability"),
            ], [
                ("Limited Ingredient Diets (LID)", "Identifying allergens via elimination", "Single protein + single carb source", "Dogs with suspected food allergies"),
                ("Hydrolysed Protein Diets", "Severe allergies confirmed by vet", "Proteins broken down below immune threshold", "Prescription; vet supervision required"),
                ("Novel Protein (e.g. venison, duck, insect)", "Dogs reacting to common proteins", "Higher price; check for cross-contamination", "After elimination trial"),
                ("Grain-Free Formulas", "Confirmed grain intolerance only", "PFMA notes most dogs tolerate grains well", "Only with veterinary recommendation"),
                ("Home-Prepared Elimination Diet", "Full control during allergy testing", "Must be nutritionally complete — short-term only", "With veterinary nutritionist oversight"),
            ])
        elif "raw" in title_lower or "barf" in title_lower:
            return _table("Raw Feeding Methods Compared", [
                ("Method", "Best For", "Considerations", "Suitability"),
            ], [
                ("Commercial Raw (frozen/freeze-dried)", "Convenience with raw benefits", "PFMA-regulated; balanced formulas available", "Most healthy adult dogs"),
                ("DIY BARF (bones and raw food)", "Experienced raw feeders", "Requires careful nutrient balancing; bone-size safety", "With nutritional knowledge"),
                ("Prey Model Raw", "Mimicking whole-prey ratios", "80/10/10 meat/bone/offal — tricky to balance minerals", "Advanced raw feeders"),
                ("Dehydrated Raw", "Travel and storage convenience", "Add water to rehydrate; lighter than frozen", "Dogs transitioning to raw"),
                ("Mixed Raw + Kibble", "Gradual transition approach", "BVA advises consistency; monitor digestion", "Dogs tolerating both formats"),
            ])
        else:
            # Generic dog food comparison
            return _table("Dog Food Types Compared", [
                ("Food Type", "Best For", "Considerations", "Suitability"),
            ], [
                ("Complete Dry Kibble", "Daily convenience and dental health", "Check for FEDIAF 'complete' label; store in airtight container", "Most adult dogs"),
                ("Wet/Canned Food", "Fussy eaters and hydration", "Higher moisture content (approx. 75%); refrigerate after opening", "Picky eaters, senior dogs"),
                ("Raw Diet (commercial)", "Nutrient density and palatability", "Follow PFMA raw feeding guidelines; handle hygienically", "Healthy adults with vet approval"),
                ("Freeze-Dried", "Convenience with raw-style nutrition", "Rehydrate before feeding; lighter to store", "Travel, active owners"),
                ("Prescription Diets", "Specific health conditions", "Vet-authorised; tailored nutrient profiles", "Dogs with diagnosed conditions"),
                ("Home-Cooked", "Full ingredient control", "Must be balanced — consult a veterinary nutritionist", "With professional guidance only"),
            ])

    elif cluster == "Dog Training":
        if "lead" in title_lower or "leash" in title_lower or "walk" in title_lower or "heel" in title_lower:
            return _table("Lead Training Methods Compared", [
                ("Method", "Best For", "Considerations", "Suitability"),
            ], [
                ("Positive Reinforcement (treats + praise)", "Building willing cooperation", "Reward desired position; ignore pulling", "All dogs, especially puppies"),
                ("Stop-Start Technique", "Persistent pullers", "Stop walking when lead tightens; resume when loose", "Adolescent dogs, strong pullers"),
                ("Direction Changes", "Dogs that forge ahead", "Turn 180° when dog pulls; reward for catching up", "Medium to large breeds"),
                ("Front-Clip Harness Training", "Dogs needing mechanical advantage", "Redirects forward motion; pair with reward training", "Strong dogs during transition"),
                ("Heel Work with Marker", "Precision positioning", "Mark and reward exact heel position; build duration gradually", "Dogs progressing to advanced obedience"),
            ])
        elif "recall" in title_lower or "come" in title_lower:
            return _table("Recall Training Approaches Compared", [
                ("Method", "Best For", "Considerations", "Suitability"),
            ], [
                ("High-Value Treat Recall", "Building initial response", "Use chicken, cheese, or liver; reward every successful recall", "Puppies and beginners"),
                ("Long-Line Training", "Practising in open spaces safely", "Use 5–10 metre line; never jerk — guide gently", "Adolescent dogs"),
                ("Two-Person Recall Game", "Making recall fun and fast", "Partners take turns calling; massive reward each time", "All ages, especially puppies"),
                ("Emergency Recall (special cue)", "Life-saving situations", "Unique word + jackpot reward; practise weekly", "All dogs once basics are solid"),
                ("Distraction Proofing", "Real-world reliability", "Gradually increase distractions; never punish slow returns", "Dogs with basic recall established"),
            ])
        elif "crate" in title_lower:
            return _table("Crate Training Approaches Compared", [
                ("Approach", "Best For", "Considerations", "Suitability"),
            ], [
                ("Gradual Introduction (treats in crate)", "Building positive association", "Leave door open initially; feed meals inside", "All puppies, anxious dogs"),
                ("Crate Games", "Making the crate exciting", "Toss treats in; reward calm entry; build duration slowly", "Playful puppies and adolescents"),
                ("Overnight Crate Training", "Housetraining support", "Place near bedroom initially; take out for toilet breaks", "Puppies under 6 months"),
                ("Crate for Travel Safety", "Car journeys and vet visits", "Use crash-tested crate; acclimatise before travel day", "All dogs travelling by car"),
                ("Crate-Free Transition", "Mature, trustworthy dogs", "Gradually increase unsupervised freedom; proof the room", "Adult dogs with solid housetraining"),
            ])
        elif "aggress" in title_lower or "reactiv" in title_lower:
            return _table("Reactivity Management Approaches", [
                ("Approach", "Best For", "Considerations", "Suitability"),
            ], [
                ("Counter-Conditioning (CC)", "Changing emotional response", "Pair trigger with high-value treat below threshold", "Mild to moderate reactivity"),
                ("Desensitisation (DS)", "Reducing trigger sensitivity", "Gradual exposure at increasing proximity; never flood", "All reactivity levels with professional help"),
                ("BAT 2.0 (Behaviour Adjustment Training)", "Dog-led approach to triggers", "Allow dog to observe and choose to disengage; reward", "Dogs who shut down with treat-based methods"),
                ("Management + Avoidance", "Immediate safety while training", "Use distance, barriers, quiet walking routes", "All reactive dogs — essential foundation"),
                ("Professional Referral (ABTC-registered)", "Complex or escalating cases", "Seek ABTC or APBC accredited behaviourist in the UK", "Aggression, fear-based reactivity"),
            ])
        else:
            return _table("Dog Training Methods Compared", [
                ("Method", "Best For", "Considerations", "Suitability"),
            ], [
                ("Positive Reinforcement", "Building trust and willing behaviour", "Reward desired actions; ignore unwanted ones", "All dogs — RSPCA recommended"),
                ("Clicker Training", "Precise timing of reward markers", "Click marks exact moment of correct behaviour", "Detail-oriented training, trick work"),
                ("Lure-Reward Training", "Teaching new positions and movements", "Use treat as lure initially; fade lure quickly", "Puppies, food-motivated dogs"),
                ("Shaping (successive approximation)", "Complex behaviours built in steps", "Reward small steps toward final behaviour", "Clever breeds, advanced training"),
                ("Capturing", "Natural behaviours you want on cue", "Wait for behaviour to occur naturally; mark and reward", "Calm behaviours, default sits"),
                ("Relationship-Based Training", "Overall household harmony", "Focus on communication and mutual understanding", "All dogs — complements other methods"),
            ])

    elif cluster == "Educational":
        if "vaccin" in title_lower or "jab" in title_lower:
            return _table("Core vs Non-Core Vaccinations (UK)", [
                ("Vaccination", "Protects Against", "Schedule", "Suitability"),
            ], [
                ("Distemper (core)", "Canine distemper virus", "Primary course at 8–10 weeks; booster at 12 weeks; then every 3 years", "All dogs — required"),
                ("Parvovirus (core)", "Canine parvovirus", "Primary course at 8–10 weeks; booster at 12 weeks; then every 3 years", "All dogs — highly recommended"),
                ("Leptospirosis (core in UK)", "Bacterial infection from water/rats", "Two doses 2–4 weeks apart; annual booster", "All UK dogs — endemic risk"),
                ("Kennel Cough (non-core)", "Bordetella bronchiseptica + parainfluenza", "Intranasal or injectable; annual", "Dogs mixing with others, boarding, daycare"),
                ("Rabies (travel)", "Rabies virus", "Single dose from 12 weeks; booster per manufacturer guidance", "Dogs travelling abroad under Pet Passport/AHC"),
            ])
        elif "dental" in title_lower or "teeth" in title_lower:
            return _table("Dog Dental Care Methods Compared", [
                ("Method", "Effectiveness", "Considerations", "Suitability"),
            ], [
                ("Daily Tooth Brushing", "Most effective home method", "Use dog-specific toothpaste; build up gradually over 2 weeks", "All dogs — gold standard per BVA"),
                ("Dental Chews (VOHC approved)", "Moderate plaque reduction", "Check for VOHC seal; size-appropriate to prevent choking", "Dogs who resist brushing"),
                ("Dental Diets", "Mechanical cleaning through kibble texture", "Must be sole diet for full effect; VOHC-approved options exist", "Dogs prone to tartar build-up"),
                ("Water Additives", "Mild antibacterial action", "Easy to use; limited evidence for plaque removal alone", "As supplement to brushing"),
                ("Professional Veterinary Dental", "Comprehensive cleaning under anaesthesia", "Allows full examination and X-rays; typically £200–£500 in the UK", "Annual check or when tartar is severe"),
            ])
        elif "groom" in title_lower or "bath" in title_lower or "coat" in title_lower:
            return _table("Grooming Approaches by Coat Type", [
                ("Coat Type", "Grooming Frequency", "Key Tools", "Professional Grooming"),
            ], [
                ("Short/Smooth (e.g. Labrador)", "Weekly brush", "Rubber curry comb, bristle brush", "Every 8–12 weeks for bath and nail trim"),
                ("Double Coat (e.g. Border Collie)", "2–3 times weekly; daily when moulting", "Undercoat rake, slicker brush", "Every 6–8 weeks; never shave double coats"),
                ("Long/Silky (e.g. Yorkshire Terrier)", "Daily to prevent mats", "Pin brush, metal comb, detangler spray", "Every 4–6 weeks for trim and bath"),
                ("Wire/Rough (e.g. Border Terrier)", "2–3 times weekly", "Stripping knife or stone, slicker brush", "Hand-stripping every 8–12 weeks"),
                ("Curly/Non-Shedding (e.g. Poodle)", "Daily to prevent matting", "Slicker brush, metal comb", "Every 4–6 weeks — essential to prevent pelting"),
            ])
        elif "flea" in title_lower or "tick" in title_lower or "worm" in title_lower or "parasit" in title_lower:
            return _table("Parasite Prevention Options (UK)", [
                ("Treatment Type", "Covers", "Frequency", "Considerations"),
            ], [
                ("Spot-On (e.g. prescription pipettes)", "Fleas, ticks, some worms", "Monthly application to skin", "Prescription spot-ons often more effective than over-the-counter"),
                ("Oral Tablets (prescription)", "Fleas and/or ticks", "Monthly or 3-monthly depending on product", "Fast-acting; good for dogs that swim frequently"),
                ("Worming Tablets", "Roundworms, tapeworms", "Every 3 months for adults; monthly for puppies under 6 months", "ESCCAP guidelines recommend regular testing"),
                ("Flea Collars (prescription-grade)", "Fleas and ticks", "Lasts 7–8 months typically", "Ensure snug fit; check for skin irritation"),
                ("Environmental Sprays", "Flea eggs and larvae in home", "As needed during infestations", "Treat all carpets, bedding, soft furnishings simultaneously"),
            ])
        elif "insur" in title_lower:
            return _table("UK Pet Insurance Types Compared", [
                ("Policy Type", "Coverage", "Considerations", "Best For"),
            ], [
                ("Lifetime Cover", "Ongoing conditions renewed annually", "Highest premiums but most comprehensive; condition limit resets yearly", "Dogs with breed-related health risks"),
                ("Annual/Time-Limited", "Conditions covered for 12 months only", "Lower premiums; pre-existing conditions excluded after year", "Budget-conscious owners with healthy dogs"),
                ("Maximum Benefit", "Fixed payout per condition, no time limit", "Once limit reached, condition excluded permanently", "Middle-ground option"),
                ("Accident Only", "Injuries from accidents", "Cheapest option; no illness cover", "Young, healthy dogs as minimal safety net"),
            ])
        elif "exercise" in title_lower or "fitness" in title_lower or "walk" in title_lower:
            return _table("Exercise Needs by Dog Size and Age", [
                ("Category", "Daily Exercise", "Considerations", "Suitability"),
            ], [
                ("Small Breeds (under 10 kg)", "30–60 minutes", "Shorter walks; watch for overheating in brachycephalic breeds", "Toy and small terrier breeds"),
                ("Medium Breeds (10–25 kg)", "60–90 minutes", "Mix of walks, play, and mental stimulation", "Spaniels, collies, mid-size crossbreeds"),
                ("Large Breeds (25–45 kg)", "60–120 minutes", "Avoid high-impact exercise under 12–18 months (joint development)", "Retrievers, setters, pointers"),
                ("Giant Breeds (over 45 kg)", "45–90 minutes", "Lower intensity; joint-conscious exercise; avoid stairs when young", "Great Danes, mastiffs, Newfoundlands"),
                ("Senior Dogs (any size)", "20–45 minutes, split across day", "Gentle walks; monitor for stiffness; hydrotherapy if arthritic", "Dogs over 7–10 years depending on breed"),
                ("Puppies (under 12 months)", "5 minutes per month of age, twice daily", "Kennel Club 5-minute rule; avoid forced repetitive exercise", "All puppies — protect growing joints"),
            ])
        elif "first aid" in title_lower or "emergency" in title_lower or "poison" in title_lower:
            return _table("Common Dog Emergencies — Quick Reference", [
                ("Emergency", "Signs to Watch For", "Immediate Action", "When to Call the Vet"),
            ], [
                ("Chocolate Ingestion", "Vomiting, restlessness, rapid breathing", "Note type and amount eaten; do NOT induce vomiting", "Immediately — use VPIS calculator for risk"),
                ("Heatstroke", "Excessive panting, drooling, collapse", "Move to shade; cool with tepid (not cold) water", "Immediately — even if dog seems to recover"),
                ("Bloat (GDV)", "Swollen abdomen, retching without vomiting", "Do not wait — this is life-threatening", "Emergency vet immediately"),
                ("Suspected Fracture", "Limping, swelling, inability to bear weight", "Restrict movement; do not splint at home", "Same day — keep dog calm during transport"),
                ("Seizures", "Convulsions, paddling legs, loss of consciousness", "Clear space around dog; do not restrain; time the seizure", "If seizure lasts over 3 minutes or clusters occur"),
                ("Bee/Wasp Sting", "Swelling at site, pawing at face", "Remove sting if visible; apply cold compress", "If swelling affects breathing or allergic reaction suspected"),
            ])
        elif "anxiety" in title_lower or "stress" in title_lower or "separation" in title_lower:
            return _table("Anxiety Management Approaches", [
                ("Approach", "Best For", "Considerations", "Suitability"),
            ], [
                ("Gradual Desensitisation", "Separation anxiety", "Increase alone-time in tiny increments; never flood", "All severity levels — foundational approach"),
                ("Enrichment and Puzzle Toys", "Boredom-related anxiety", "Rotate toys; use snuffle mats and Kongs", "Mild anxiety, prevention"),
                ("Adaptil (DAP) Diffuser", "General anxiety, new environments", "Synthetic pheromone; plug in near resting area", "Mild to moderate — can complement other methods"),
                ("Behavioural Referral (ABTC)", "Severe or worsening anxiety", "Seek ABTC or APBC accredited behaviourist", "When home methods are insufficient"),
                ("Veterinary Medication", "Clinical anxiety disorders", "Prescribed by vet alongside behaviour modification", "Severe cases — never medication alone"),
            ])
        elif "breed" in title_lower or "choos" in title_lower or "adopt" in title_lower:
            return _table("Choosing a Dog — Key Considerations", [
                ("Factor", "Questions to Ask", "Where to Research", "Common Pitfalls"),
            ], [
                ("Lifestyle Match", "How active are you? Home size? Work hours?", "Kennel Club Breed Selector; PDSA pet fitness data", "Choosing by appearance alone"),
                ("Breed Health", "What conditions are common in this breed?", "Kennel Club Breed Health pages; breed-specific surveys", "Ignoring breed-specific health testing"),
                ("Rescue vs Breeder", "Are you prepared for unknowns vs waiting for a puppy?", "RSPCA, Dogs Trust, breed-specific rescues", "Buying from unlicensed breeders (Lucy's Law applies)"),
                ("Cost of Ownership", "Can you afford £1,500–£2,000+ per year?", "PDSA PAW Report annual cost data", "Underestimating insurance, vet bills, food costs"),
                ("Time Commitment", "10–15 years; daily walks, training, socialisation?", "The Kennel Club; RSPCA pet ownership guides", "Not planning for holidays, illness, life changes"),
            ])
        elif "health" in title_lower or "wellness" in title_lower or "check" in title_lower or "vet" in title_lower:
            return _table("Routine Health Checks for Dogs (UK)", [
                ("Check", "Frequency", "What It Covers", "Typical UK Cost"),
            ], [
                ("Annual Vet Health Check", "Yearly (6-monthly for seniors)", "Full physical exam, weight, dental, heart, skin", "£30–£65 consultation fee"),
                ("Vaccination Boosters", "Annually (some 3-yearly)", "DHP, leptospirosis, kennel cough as needed", "Included in annual check or £40–£80"),
                ("Parasite Prevention", "Monthly flea/tick; quarterly worming", "Prescription treatments most effective", "£10–£25 per month"),
                ("Dental Check", "At every vet visit; professional clean annually if needed", "Tartar, gingivitis, fractured teeth", "£200–£500 for professional clean"),
                ("Weight Monitoring", "Monthly at home; each vet visit", "Body condition score (1–9 scale, ideal 4–5)", "Free — use PFMA Pet Size-O-Meter"),
                ("Blood Tests (senior dogs)", "Annually from age 7+", "Kidney, liver, thyroid function", "£80–£200 depending on panel"),
            ])
        elif "social" in title_lower or "puppy class" in title_lower:
            return _table("Socialisation Methods Compared", [
                ("Method", "Best Age", "Considerations", "Suitability"),
            ], [
                ("Puppy Classes (indoor, supervised)", "8–16 weeks", "Controlled environment; trainer-led introductions", "All puppies — Kennel Club Good Citizen scheme"),
                ("Controlled Home Visits", "From day one in new home", "Invite calm, vaccinated dogs; supervise all interactions", "Before vaccination course is complete"),
                ("Public Place Exposure (carried)", "8–12 weeks (pre-vaccination)", "Carry puppy to experience sounds, sights, surfaces safely", "All puppies — critical socialisation window"),
                ("Adolescent Socialisation Classes", "4–12 months", "Address fear periods; reinforce positive associations", "Adolescent dogs showing new wariness"),
                ("Adult Dog Socialisation", "Any age", "Slower pace; respect thresholds; use parallel walking", "Rescue dogs, under-socialised adults"),
            ])
        else:
            # Generic educational
            return _table("Dog Care Essentials at a Glance", [
                ("Topic", "Key Recommendation", "UK Authority", "How Often"),
            ], [
                ("Nutrition", "Feed FEDIAF-complete food appropriate to life stage", "PFMA (pfma.org.uk)", "Twice daily for adults; 3–4 times for puppies"),
                ("Vaccinations", "Keep core vaccines up to date; annual leptospirosis booster", "BVA / BSAVA", "Primary course + annual or triennial boosters"),
                ("Parasite Control", "Year-round flea, tick, and worm prevention", "ESCCAP UK (esccapuk.org.uk)", "Monthly flea/tick; quarterly worming"),
                ("Dental Care", "Daily brushing with dog-specific toothpaste", "BVA / BVDA", "Daily at home; annual vet dental check"),
                ("Exercise", "Minimum 30 minutes daily; breed-appropriate", "PDSA / Kennel Club", "Daily — adjust for age and breed"),
                ("Insurance", "Lifetime policy recommended for comprehensive cover", "ABI / PDSA PAW Report", "Ongoing — review annually at renewal"),
                ("Training", "Positive reinforcement methods only", "RSPCA / ABTC", "Ongoing — start from day one"),
            ])

    return ""


def _table(caption, headers, rows):
    """Build a WordPress block-editor table."""
    header_row = headers[0]
    thead = "<thead><tr>" + "".join(f"<th>{h}</th>" for h in header_row) + "</tr></thead>"
    tbody_rows = ""
    for row in rows:
        tbody_rows += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
    tbody = f"<tbody>{tbody_rows}</tbody>"

    return (
        f'<!-- wp:heading {{"level":3}} -->\n'
        f'<h3 class="wp-block-heading">{caption}</h3>\n'
        f'<!-- /wp:heading -->\n\n'
        f'<!-- wp:table {{"className":"is-style-stripes"}} -->\n'
        f'<figure class="wp-block-table is-style-stripes"><table>{thead}{tbody}</table></figure>\n'
        f'<!-- /wp:table -->'
    )


# ─── Content generation — Quick Checklist ────────────────────────────────────
def generate_checklist(title, cluster):
    """Generate topic-specific Quick Checklist items."""
    title_lower = title.lower()
    items = []

    if cluster == "Dog Food":
        if "glossary" in title_lower or "ingredient" in title_lower or "label" in title_lower:
            items = [
                "Check the label says ‘complete’ rather than ‘complementary’ — only complete foods provide full nutrition",
                "Look for a named protein source (e.g. ‘chicken’ not ‘meat and animal derivatives’)",
                "Verify the food meets FEDIAF nutritional guidelines for your dog’s life stage",
                "Compare the ‘analytical constituents’ panel: crude protein, fat, fibre, and ash percentages",
                "Check the ingredients list is ordered by weight — the first ingredient should be a protein source",
                "Confirm the ‘best before’ date and store according to label instructions",
                "Calculate the daily feeding amount in grams based on your dog’s weight in kg",
                "Consult your vet before switching to a specialised diet (grain-free, raw, or prescription)"
            ]
        elif "puppy" in title_lower:
            items = [
                "Choose a food labelled ‘complete’ for growth or ‘puppy’ meeting FEDIAF standards",
                "Feed 3–4 meals per day until 12 weeks, then reduce to 2–3 meals",
                "Weigh food portions in grams — follow the manufacturer’s feeding guide for your puppy’s expected adult weight",
                "Transition foods gradually over 7–10 days (25% new food increase every 2–3 days)",
                "Avoid supplementing a complete puppy food with calcium — excess can harm growing bones",
                "Monitor body condition weekly using the PFMA Puppy Size-O-Meter"
            ]
        elif "senior" in title_lower or "older" in title_lower:
            items = [
                "Switch to a senior-formulated diet from around age 7 (earlier for giant breeds)",
                "Weigh portions carefully in grams — senior dogs need fewer calories",
                "Look for foods with added glucosamine and omega-3 for joint support",
                "Check phosphorus levels if your vet flags kidney concerns",
                "Consider warming food slightly to enhance aroma for fussy senior dogs",
                "Book a 6-monthly vet check including weight and body condition assessment"
            ]
        elif "allerg" in title_lower or "sensitiv" in title_lower:
            items = [
                "Work with your vet to run a proper elimination diet before switching foods",
                "Keep a food diary noting ingredients and any symptoms for at least 8 weeks",
                "Choose limited ingredient diets (LID) with a single named protein source",
                "Avoid treats that contain common allergens during the elimination period",
                "Re-introduce ingredients one at a time to identify the specific trigger",
                "Ask your vet about hydrolysed protein diets for severe cases"
            ]
        else:
            items = [
                "Ensure the food is labelled ‘complete’ and meets FEDIAF standards for your dog’s life stage",
                "Weigh daily portions in grams using a kitchen scale rather than estimating by volume",
                "Provide fresh water at all times — especially important when feeding dry kibble",
                "Transition between foods gradually over 7–10 days to avoid digestive upset",
                "Store dry food in a sealed container away from heat and moisture",
                "Review your dog’s body condition score monthly using the PFMA Pet Size-O-Meter",
                "Consult your vet before adding supplements to a complete diet"
            ]

    elif cluster == "Dog Training":
        if "lead" in title_lower or "leash" in title_lower or "walk" in title_lower:
            items = [
                "Use a well-fitting Y-shaped harness or flat collar — avoid choke chains (RSPCA advises against them)",
                "Keep treats in an easily accessible pouch on your belt or pocket",
                "Reward your dog every few steps for walking on a loose lead initially",
                "Stop moving immediately when the lead becomes taut — wait for slack before continuing",
                "Keep early sessions short (5–10 minutes) in a low-distraction environment",
                "Practise indoors or in the garden before moving to busier streets"
            ]
        elif "recall" in title_lower:
            items = [
                "Use a consistent recall word (not the dog’s name) and a happy, upbeat tone",
                "Always reward recall with a high-value treat (chicken, cheese, liver)",
                "Never punish a dog that comes back slowly — they’ll be slower next time",
                "Practise in a secure, enclosed area before trying off-lead in open spaces",
                "Use a long line (5–10 metres) during the training phase for safety",
                "Build an emergency recall using a unique word and jackpot rewards"
            ]
        elif "crate" in title_lower:
            items = [
                "Choose a crate large enough for your dog to stand, turn around, and lie flat",
                "Place the crate in a quiet area of the home where the family spends time",
                "Feed meals inside the crate to build a positive association",
                "Never use the crate as punishment — it must always feel like a safe space",
                "Build up crate time gradually: start with seconds, progress to minutes over days",
                "Cover three sides with a blanket for a den-like feel if your dog prefers it"
            ]
        else:
            items = [
                "Use positive reinforcement only — reward desired behaviours with treats, praise, or play",
                "Keep training sessions short (5–10 minutes) to maintain focus and enthusiasm",
                "End every session on a success, even if you need to ask for an easier behaviour",
                "Use a marker word (‘yes!’) or clicker at the exact moment of the correct behaviour",
                "Practise new skills in low-distraction environments before adding challenges",
                "Be consistent — everyone in the household should use the same cues and rules",
                "If your dog is struggling, make the task easier rather than repeating failed attempts"
            ]

    elif cluster == "Educational":
        if "vaccin" in title_lower:
            items = [
                "Book your puppy’s first vaccination from 8 weeks of age",
                "Keep your vaccination card safe — you’ll need it for boarding, daycare, and travel",
                "Do not walk your puppy in public areas until 1–2 weeks after the second vaccine",
                "Set annual reminders for booster vaccinations",
                "Discuss non-core vaccines (kennel cough, rabies) based on your dog’s lifestyle",
                "Ask your vet about titre testing as an alternative to routine boosters for DHP"
            ]
        elif "dental" in title_lower or "teeth" in title_lower:
            items = [
                "Brush your dog’s teeth daily using dog-specific toothpaste (never human toothpaste)",
                "Start by letting your dog lick the toothpaste, then gradually introduce the brush over 2 weeks",
                "Check for VOHC-approved dental chews as a supplement to brushing",
                "Lift your dog’s lips weekly to check for redness, swelling, or tartar build-up",
                "Book a professional dental check at your annual vet visit",
                "Watch for signs of dental pain: dropping food, pawing at mouth, reluctance to eat"
            ]
        elif "flea" in title_lower or "tick" in title_lower or "worm" in title_lower or "parasit" in title_lower:
            items = [
                "Use year-round flea and tick prevention — UK homes are warm enough for fleas in winter",
                "Choose prescription parasite treatments over shop-bought for better efficacy",
                "Worm adult dogs at least every 3 months; puppies monthly until 6 months old",
                "Treat all pets in the household simultaneously to prevent reinfestation",
                "Wash bedding at 60°C and vacuum thoroughly during a flea outbreak",
                "Check for ticks after walks in long grass, woodland, or heathland"
            ]
        elif "insur" in title_lower:
            items = [
                "Insure your dog as early as possible — pre-existing conditions are typically excluded",
                "Compare lifetime policies for the most comprehensive ongoing cover",
                "Check the annual per-condition limit, not just the total payout amount",
                "Read the excess structure: per-claim, per-condition, and any co-payment percentages",
                "Review your policy annually at renewal — premiums and terms can change",
                "Keep all vet records and receipts organised for smooth claims"
            ]
        elif "anxiety" in title_lower or "stress" in title_lower or "separation" in title_lower:
            items = [
                "Never punish anxious behaviour — it increases fear and makes the problem worse",
                "Start separation training with very short absences (seconds) and build up gradually",
                "Provide enrichment (Kongs, snuffle mats, puzzle feeders) when leaving",
                "Consider an Adaptil diffuser near your dog’s resting area",
                "Film your dog when you leave to identify specific anxiety triggers",
                "Seek an ABTC-registered behaviourist if anxiety is severe or worsening"
            ]
        elif "exercise" in title_lower or "fitness" in title_lower:
            items = [
                "Follow the Kennel Club’s 5-minute rule for puppies: 5 minutes per month of age, twice daily",
                "Split exercise into two or more sessions per day rather than one long walk",
                "Include mental stimulation (training, scent work, puzzle toys) alongside physical exercise",
                "Avoid high-impact activities (jumping, forced running) for dogs under 12–18 months",
                "Adjust exercise intensity in hot weather — walk during cooler hours",
                "Monitor your dog’s body condition and adjust exercise if they are over or underweight"
            ]
        else:
            items = [
                "Register with a local vet within the first week of bringing your dog home",
                "Keep vaccinations, worming, and flea treatments up to date year-round",
                "Monitor your dog’s weight monthly using the PFMA Pet Size-O-Meter body condition tool",
                "Provide daily enrichment: puzzle feeders, training games, and safe chew toys",
                "Socialise your dog gradually and positively to new people, animals, and environments",
                "Learn your dog’s body language — the RSPCA and Dogs Trust provide free visual guides",
                "Budget for annual vet checks, insurance, and unexpected health costs"
            ]

    if not items:
        return ""

    li = "\n".join(f"<li>{item}</li>" for item in items)
    return (
        '<!-- wp:group {"style":{"color":{"background":"#f5f3ff"},"border":{"radius":"6px","width":"1px","color":"#ddd6fe"},"spacing":{"padding":{"top":"16px","bottom":"16px","left":"20px","right":"20px"},"margin":{"top":"24px","bottom":"24px"}}},"layout":{"type":"constrained"}} -->\n'
        '<div class="wp-block-group has-border-color has-background" style="border-color:#ddd6fe;border-width:1px;border-radius:6px;background-color:#f5f3ff;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<!-- wp:heading {"level":4} --><h4 class="wp-block-heading">Quick Checklist</h4><!-- /wp:heading -->\n'
        f'<!-- wp:list --><ul class="wp-block-list">{li}</ul><!-- /wp:list -->\n'
        '</div><!-- /wp:group -->'
    )


# ─── Content generation — What to Do Next ────────────────────────────────────
def generate_next_steps(title, cluster):
    """Generate topic-specific What to Do Next steps."""
    title_lower = title.lower()
    steps = []

    if cluster == "Dog Food":
        if "glossary" in title_lower or "ingredient" in title_lower or "label" in title_lower:
            steps = [
                "Pick up your dog’s current food bag and read through the ingredients list using the definitions in this glossary",
                "Compare the analytical constituents (protein, fat, fibre, ash) against FEDIAF guidelines for your dog’s life stage",
                "If any ingredient concerns you, discuss alternatives with your vet at the next appointment",
                "Use the PFMA website (pfma.org.uk) for further guidance on pet food labelling regulations in the UK"
            ]
        elif "puppy" in title_lower:
            steps = [
                "Check your current puppy food meets FEDIAF standards and is labelled ‘complete for growth’",
                "Weigh out tomorrow’s portions using a kitchen scale and the feeding guide on the pack",
                "Schedule a puppy weight check with your vet in the next 2 weeks",
                "Start a simple feeding diary to track weight gain and any digestive changes"
            ]
        elif "senior" in title_lower or "older" in title_lower:
            steps = [
                "Book a senior health check with your vet to discuss dietary needs",
                "Assess your dog’s body condition score using the PFMA Pet Size-O-Meter",
                "If switching to senior food, plan a gradual 10-day transition starting this week",
                "Ask your vet about joint supplements if your dog shows any stiffness"
            ]
        elif "allerg" in title_lower or "sensitiv" in title_lower:
            steps = [
                "Book a vet appointment to discuss a structured elimination diet plan",
                "Begin a food diary today — note every food, treat, and chew your dog receives",
                "Remove all treats and extras for the elimination period (8–12 weeks minimum)",
                "After identifying triggers, source an appropriate limited ingredient diet"
            ]
        else:
            steps = [
                "Weigh your dog this week and calculate their daily food requirement in grams using the manufacturer’s guide",
                "Check your current food bag confirms FEDIAF compliance and ‘complete’ labelling",
                "Assess your dog’s body condition score using the free PFMA Pet Size-O-Meter tool",
                "If considering a diet change, plan a gradual 7–10 day transition and consult your vet if in doubt"
            ]

    elif cluster == "Dog Training":
        if "lead" in title_lower or "leash" in title_lower or "walk" in title_lower:
            steps = [
                "Choose your training equipment: a well-fitting harness or flat collar and a 1.5–2 metre lead",
                "Stock up on small, soft training treats (pea-sized pieces of chicken or cheese work well)",
                "Practise loose lead walking indoors or in your garden for 5 minutes today",
                "Gradually add mild distractions over the next week before trying a public pavement"
            ]
        elif "recall" in title_lower:
            steps = [
                "Choose a clear recall word that you do not already use (e.g. ‘come’ or ‘here’)",
                "Practise 5 recall repetitions in your home today, rewarding every success with a high-value treat",
                "Move to your garden or a secure outdoor area for the next training sessions",
                "Purchase a long line (5–10 metres) for practising recall before going off-lead in open spaces"
            ]
        else:
            steps = [
                "Pick one skill to focus on this week and practise it in 5-minute daily sessions",
                "Stock up on small, soft training treats and choose your marker word or get a clicker",
                "Find a quiet, low-distraction space in your home for initial training sessions",
                "Once the behaviour is reliable at home, gradually practise in more challenging environments",
                "If you feel stuck, look for a Kennel Club Good Citizen Scheme class in your area"
            ]

    elif cluster == "Educational":
        if "vaccin" in title_lower:
            steps = [
                "Check your dog’s vaccination card and note when the next booster is due",
                "Book a vet appointment if any vaccinations are overdue",
                "Discuss titre testing with your vet if you want to check immunity levels before boosting",
                "Set calendar reminders for annual boosters going forward"
            ]
        elif "dental" in title_lower or "teeth" in title_lower:
            steps = [
                "Purchase a dog-specific toothbrush and enzymatic toothpaste this week",
                "Start by letting your dog lick the toothpaste from your finger for 3–5 days",
                "Gradually introduce the brush, working up to daily brushing over 2 weeks",
                "Book a dental check at your next vet visit to assess current oral health"
            ]
        elif "flea" in title_lower or "tick" in title_lower or "worm" in title_lower:
            steps = [
                "Check when your dog last received flea, tick, and worming treatments",
                "Book a vet appointment for prescription-strength parasite prevention",
                "Set monthly calendar reminders for flea/tick treatment and quarterly reminders for worming",
                "Wash all pet bedding at 60°C this week as a precautionary measure"
            ]
        elif "insur" in title_lower:
            steps = [
                "Review your current policy documents and note the excess, per-condition limit, and exclusions",
                "Get at least three comparison quotes from different providers",
                "Prioritise lifetime cover if your dog has breed-specific health risks",
                "Set a reminder 4 weeks before your renewal date to compare options"
            ]
        elif "anxiety" in title_lower or "separation" in title_lower:
            steps = [
                "Set up a camera to film your dog during short absences this week",
                "Start practising micro-absences (stepping outside for 10 seconds) and gradually increasing",
                "Introduce an enrichment activity (Kong, snuffle mat) paired with your departure cue",
                "If anxiety does not improve within 2 weeks, contact an ABTC-registered behaviourist"
            ]
        else:
            steps = [
                "Review your dog’s care routine against the checklist above and note any gaps",
                "Book a vet check-up if your dog has not been seen in the last 12 months",
                "Download the PDSA or RSPCA pet care guides for additional breed-specific advice",
                "Set monthly reminders for weight checks, parasite treatments, and dental care"
            ]

    if not steps:
        return ""

    li = "\n".join(f"<li>{step}</li>" for step in steps)
    return (
        '<!-- wp:group {"style":{"color":{"background":"#f0fdfa"},"border":{"radius":"6px","width":"1px","color":"#99f6e4"},"spacing":{"padding":{"top":"16px","bottom":"16px","left":"20px","right":"20px"},"margin":{"top":"24px","bottom":"24px"}}},"layout":{"type":"constrained"}} -->\n'
        '<div class="wp-block-group has-border-color has-background" style="border-color:#99f6e4;border-width:1px;border-radius:6px;background-color:#f0fdfa;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<!-- wp:heading {"level":4} --><h4 class="wp-block-heading">What to Do Next</h4><!-- /wp:heading -->\n'
        f'<!-- wp:list {{"ordered":true}} --><ol class="wp-block-list">{li}</ol><!-- /wp:list -->\n'
        '</div><!-- /wp:group -->'
    )


# ─── UK Enrichment ───────────────────────────────────────────────────────────
def apply_uk_enrichment(content, cluster):
    """Add UK-specific inline references and measurements."""
    # Convert common US measurements to UK
    conversions = [
        (r'\b(\d+)\s*lbs?\b', lambda m: f'{m.group(1)} lbs ({round(int(m.group(1)) * 0.4536, 1)} kg)'),
        (r'\b(\d+)\s*oz\b', lambda m: f'{m.group(1)} oz ({round(int(m.group(1)) * 28.35)} ml)'),
        (r'\b(\d+)\s*cups?\b', lambda m: f'{m.group(1)} cups ({round(int(m.group(1)) * 236.6)} ml)'),
    ]
    for pattern, repl in conversions:
        # Only convert if not already followed by parenthetical conversion
        content = re.sub(pattern + r'(?!\s*\()', repl, content)

    # UK spelling fixes
    uk_spellings = [
        ('behavior', 'behaviour'),
        ('behaviors', 'behaviours'),
        ('behavioral', 'behavioural'),
        ('flavor', 'flavour'),
        ('flavors', 'flavours'),
        ('color', 'colour'),
        ('colors', 'colours'),
        ('fiber', 'fibre'),
        ('center', 'centre'),
        ('centers', 'centres'),
        ('recognize', 'recognise'),
        ('recognized', 'recognised'),
        ('organize', 'organise'),
        ('organized', 'organised'),
        ('minimize', 'minimise'),
        ('minimize', 'minimise'),
        ('optimize', 'optimise'),
        ('optimized', 'optimised'),
        ('specialize', 'specialise'),
        ('specialized', 'specialised'),
        ('analyze', 'analyse'),
        ('analyzed', 'analysed'),
        ('catalog', 'catalogue'),
        ('traveled', 'travelled'),
        ('traveling', 'travelling'),
        ('favorite', 'favourite'),
        ('favorites', 'favourites'),
        ('license', 'licence'),
        ('defense', 'defence'),
        ('offense', 'offence'),
        ('practicing', 'practising'),
    ]
    for us, uk in uk_spellings:
        # Case-insensitive replacement but preserve original case pattern
        content = re.sub(
            re.escape(us),
            uk,
            content,
            flags=re.IGNORECASE
        )

    return content


# ─── Build extractable definitions for key terms ────────────────────────────
def generate_definitions(title, cluster):
    """Generate extractable bold-term definitions as a small block."""
    title_lower = title.lower()
    defs = []

    if cluster == "Dog Food":
        if "glossary" in title_lower or "ingredient" in title_lower or "label" in title_lower:
            defs = [
                ("<strong>Complete food</strong> is a pet food that provides all the nutrients a dog needs in the correct proportions, meeting FEDIAF nutritional guidelines without requiring any supplementation."),
                ("<strong>Analytical constituents</strong> are the standardised nutritional values printed on pet food labels in the UK and EU, listing crude protein, crude fat, crude fibre, crude ash, and moisture percentages."),
                ("<strong>Crude ash</strong> is the mineral content remaining after a food sample is incinerated, indicating the total inorganic mineral level in the product."),
                ("<strong>Named protein source</strong> refers to a specific animal ingredient identified by species (e.g. chicken, lamb, salmon) rather than a generic term like ‘meat and animal derivatives’."),
            ]
        elif "raw" in title_lower:
            defs = [
                ("<strong>BARF diet</strong> stands for Biologically Appropriate Raw Food, a feeding approach based on raw meat, bones, offal, and vegetables designed to mimic a dog’s ancestral diet."),
                ("<strong>Prey model raw</strong> is a raw feeding method following an approximate 80/10/10 ratio of muscle meat, bone, and offal without added vegetables or grains."),
            ]
        else:
            defs = [
                ("<strong>FEDIAF</strong> (European Pet Food Industry Federation) sets the nutritional guidelines that UK and EU pet food manufacturers follow to ensure products meet minimum and maximum nutrient levels for each life stage."),
                ("<strong>PFMA</strong> (Pet Food Manufacturers’ Association) is the UK trade body representing pet food producers, providing consumer guidance on feeding, labelling, and pet nutrition."),
            ]

    elif cluster == "Dog Training":
        defs = [
            ("<strong>Positive reinforcement</strong> is a training method where desired behaviours are rewarded with treats, praise, or play, increasing the likelihood the behaviour will be repeated."),
            ("<strong>Marker word</strong> (or clicker) is a consistent signal given at the exact moment a dog performs the correct behaviour, bridging the gap between the action and the reward."),
        ]
        if "reactiv" in title_lower or "aggress" in title_lower:
            defs.append("<strong>Counter-conditioning</strong> is the process of changing a dog’s emotional response to a trigger by pairing the trigger with something the dog values highly, such as a favourite treat.")
            defs.append("<strong>Threshold</strong> in dog behaviour refers to the distance or intensity at which a dog notices a trigger but can still respond to cues and take treats without reacting.")
        if "recall" in title_lower:
            defs.append("<strong>Emergency recall</strong> is a specially trained, high-value recall cue reserved for potentially dangerous situations, practised separately from the everyday recall word.")

    elif cluster == "Educational":
        if "vaccin" in title_lower:
            defs = [
                ("<strong>Core vaccines</strong> are vaccinations recommended for all dogs regardless of lifestyle, including distemper, parvovirus, and in the UK, leptospirosis."),
                ("<strong>Titre testing</strong> is a blood test measuring a dog’s antibody levels against specific diseases, used to assess existing immunity before deciding on booster vaccinations."),
            ]
        elif "dental" in title_lower:
            defs = [
                ("<strong>VOHC</strong> (Veterinary Oral Health Council) awards a seal of acceptance to dental products that meet pre-set standards for reducing plaque or tartar in dogs and cats."),
                ("<strong>Periodontal disease</strong> is an infection of the tissues surrounding the teeth, progressing from gingivitis (gum inflammation) to bone loss if untreated."),
            ]
        elif "anxiety" in title_lower or "separation" in title_lower:
            defs = [
                ("<strong>Separation anxiety</strong> is a behavioural condition where a dog experiences significant distress when separated from their owner, often resulting in destructive behaviour, vocalisation, or house soiling."),
                ("<strong>Desensitisation</strong> is the gradual, controlled exposure to a feared trigger at a low enough intensity that the dog remains calm, progressively building tolerance over time."),
            ]
        elif "parasit" in title_lower or "flea" in title_lower or "worm" in title_lower:
            defs = [
                ("<strong>ESCCAP</strong> (European Scientific Counsel Companion Animal Parasites) provides evidence-based parasite control guidelines used by UK veterinary professionals."),
                ("<strong>Endoparasites</strong> are internal parasites such as roundworms and tapeworms that live inside the host’s body, typically in the gastrointestinal tract."),
            ]
        else:
            defs = [
                ("<strong>Body condition score (BCS)</strong> is a standardised 1–9 scale used by veterinary professionals to assess whether a dog is underweight, ideal, or overweight based on visual and hands-on evaluation."),
                ("<strong>PDSA</strong> (People’s Dispensary for Sick Animals) is a UK veterinary charity providing free and low-cost treatment, and publishes the annual PAW Report on pet wellbeing."),
            ]

    if not defs:
        return ""

    paras = "\n\n".join(
        f'<!-- wp:paragraph -->\n<p>{d}</p>\n<!-- /wp:paragraph -->'
        for d in defs
    )
    return (
        '<!-- wp:heading {"level":3} -->\n'
        '<h3 class="wp-block-heading">Key Terms</h3>\n'
        '<!-- /wp:heading -->\n\n'
        + paras
    )


# ─── Insert blocks in correct order ─────────────────────────────────────────
def insert_blocks(content, title, cluster):
    """Insert missing blocks in the correct order within the post content.

    Target order: ... Quick Checklist ... What to Do Next ... Common Mistakes ... Key Terms ... Key Takeaways ... [trust footer]
    """
    added = {"comparison": False, "checklist": False, "next_steps": False, "uk_enrichment": False}

    # 1. UK enrichment (applied to entire content)
    new_content = apply_uk_enrichment(content, cluster)
    if new_content != content:
        added["uk_enrichment"] = True
    content = new_content

    # 2. Generate blocks we need to add
    comparison_block = "" if has_comparison_table(content) else generate_comparison_table(title, cluster)
    checklist_block = "" if has_checklist(content) else generate_checklist(title, cluster)
    next_steps_block = "" if has_next_steps(content) else generate_next_steps(title, cluster)
    definitions_block = "" if has_key_terms(content) else generate_definitions(title, cluster)

    if comparison_block:
        added["comparison"] = True
    if checklist_block:
        added["checklist"] = True
    if next_steps_block:
        added["next_steps"] = True

    # 3. Find insertion points
    # We want: ... [comparison near top/middle] ... Quick Checklist ... What to Do Next ... Common Mistakes ... Key Terms ... Key Takeaways ... [trust footer]

    # Find anchor points in existing content
    common_mistakes_pos = content.lower().find("common mistakes")
    key_takeaways_pos = content.lower().find("key takeaways")
    trust_footer_pos = content.lower().find("trust-footer")
    if trust_footer_pos == -1:
        trust_footer_pos = content.lower().find("editorial standards")
    if trust_footer_pos == -1:
        trust_footer_pos = content.lower().find("independently researched")

    # Build the insertion block for checklist + next_steps + definitions
    # These go BEFORE Common Mistakes if it exists, else BEFORE Key Takeaways, else at end
    middle_blocks = ""
    if checklist_block:
        middle_blocks += "\n\n" + checklist_block
    if next_steps_block:
        middle_blocks += "\n\n" + next_steps_block
    if definitions_block:
        middle_blocks += "\n\n" + definitions_block

    if middle_blocks:
        if common_mistakes_pos > 0:
            # Find the heading block start just before "Common Mistakes"
            # Look backwards for <!-- wp:heading
            search_region = content[:common_mistakes_pos]
            last_heading = search_region.rfind("<!-- wp:heading")
            if last_heading > 0:
                content = content[:last_heading] + middle_blocks + "\n\n" + content[last_heading:]
            else:
                content = content[:common_mistakes_pos] + middle_blocks + "\n\n" + content[common_mistakes_pos:]
        elif key_takeaways_pos > 0:
            search_region = content[:key_takeaways_pos]
            last_heading = search_region.rfind("<!-- wp:heading")
            if last_heading > 0:
                content = content[:last_heading] + middle_blocks + "\n\n" + content[last_heading:]
            else:
                content = content[:key_takeaways_pos] + middle_blocks + "\n\n" + content[key_takeaways_pos:]
        elif trust_footer_pos > 0:
            content = content[:trust_footer_pos] + middle_blocks + "\n\n" + content[trust_footer_pos:]
        else:
            content = content + middle_blocks

    # Insert comparison table near the top — after the first few paragraphs (after ~2000 chars or after 3rd paragraph)
    if comparison_block:
        # Find a good spot: after the 3rd <!-- /wp:paragraph --> or after 2000 chars, whichever comes first
        para_end_pattern = "<!-- /wp:paragraph -->"
        pos = 0
        for i in range(3):
            next_pos = content.find(para_end_pattern, pos)
            if next_pos == -1:
                break
            pos = next_pos + len(para_end_pattern)

        if pos > 0:
            content = content[:pos] + "\n\n" + comparison_block + "\n\n" + content[pos:]
        else:
            # Fallback: insert at ~2000 chars
            insert_at = min(2000, len(content) // 3)
            # Find next block boundary
            next_block = content.find("<!-- /wp:", insert_at)
            if next_block > 0:
                next_block = content.find("-->", next_block)
                if next_block > 0:
                    next_block += 3
                    content = content[:next_block] + "\n\n" + comparison_block + "\n\n" + content[next_block:]
                else:
                    content = content + "\n\n" + comparison_block
            else:
                content = content + "\n\n" + comparison_block

    return content, added


# ─── Main processing loop ───────────────────────────────────────────────────
def main():
    print(f"[{datetime.now().isoformat()}] Phase 10AX Citation Dominance Sprint starting")
    print(f"Total posts to process: {len(ALL_POSTS)}")
    print(f"  Dog Food: {len(DOG_FOOD_IDS)} posts")
    print(f"  Educational: {len(EDUCATIONAL_IDS)} posts")
    print(f"  Dog Training: {len(DOG_TRAINING_IDS)} posts")
    print()

    # Initialize CSV log
    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["id", "title", "cluster", "comparison_added", "checklist_added",
                         "next_steps_added", "uk_enrichment", "status"])

    results = []
    success_count = 0
    error_count = 0

    for idx, (post_id, cluster) in enumerate(ALL_POSTS, 1):
        print(f"[{idx}/{len(ALL_POSTS)}] Processing post {post_id} ({cluster})...")

        try:
            # Fetch post
            post = wp_get(f"posts/{post_id}?_fields=id,title,content")
            title = post["title"]["rendered"]
            content = post["content"]["rendered"]
            print(f"  Title: {title}")
            print(f"  Content length: {len(content)} chars")

            # Check what's already present
            already_has = []
            if has_comparison_table(content):
                already_has.append("comparison_table")
            if has_checklist(content):
                already_has.append("checklist")
            if has_next_steps(content):
                already_has.append("next_steps")
            if has_key_terms(content):
                already_has.append("key_terms")

            if already_has:
                print(f"  Already has: {', '.join(already_has)}")

            # Fetch raw content for editing
            post_raw = wp_get(f"posts/{post_id}?context=edit&_fields=id,title,content")
            raw_content = post_raw["content"]["raw"]

            # Insert missing blocks
            updated_content, added = insert_blocks(raw_content, title, cluster)

            if updated_content == raw_content:
                print(f"  SKIP: No changes needed (all blocks present)")
                row = [post_id, title, cluster, "skip", "skip", "skip", "skip", "no_changes"]
                results.append(row)
                with open(LOG_FILE, 'a', newline='') as f:
                    csv.writer(f).writerow(row)
                time.sleep(1)
                continue

            # Update the post
            resp = wp_update(post_id, {"content": updated_content})
            print(f"  UPDATED: comparison={added['comparison']}, checklist={added['checklist']}, "
                  f"next_steps={added['next_steps']}, uk_enrichment={added['uk_enrichment']}")

            row = [
                post_id, title, cluster,
                "yes" if added["comparison"] else "skip",
                "yes" if added["checklist"] else "skip",
                "yes" if added["next_steps"] else "skip",
                "yes" if added["uk_enrichment"] else "skip",
                "updated"
            ]
            results.append(row)
            success_count += 1

            with open(LOG_FILE, 'a', newline='') as f:
                csv.writer(f).writerow(row)

        except Exception as e:
            print(f"  ERROR: {e}")
            row = [post_id, title if 'title' in dir() else "unknown", cluster,
                   "error", "error", "error", "error", f"error: {str(e)[:100]}"]
            results.append(row)
            error_count += 1

            with open(LOG_FILE, 'a', newline='') as f:
                csv.writer(f).writerow(row)

        # 2-second delay between posts
        time.sleep(2)

    # Summary
    print("\n" + "="*70)
    print("PHASE 10AX CITATION DOMINANCE SPRINT — COMPLETE")
    print("="*70)
    print(f"Total posts processed: {len(ALL_POSTS)}")
    print(f"Successfully updated: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Skipped (no changes): {len(ALL_POSTS) - success_count - error_count}")
    print(f"\nLog saved to: {LOG_FILE}")

    # Per-cluster summary
    for cluster_name in ["Dog Food", "Educational", "Dog Training"]:
        cluster_rows = [r for r in results if r[2] == cluster_name]
        updated = sum(1 for r in cluster_rows if r[7] == "updated")
        print(f"\n{cluster_name}: {updated}/{len(cluster_rows)} updated")
        for r in cluster_rows:
            print(f"  {r[0]}: comparison={r[3]}, checklist={r[4]}, next_steps={r[5]}, uk={r[6]} — {r[7]}")


if __name__ == "__main__":
    main()
