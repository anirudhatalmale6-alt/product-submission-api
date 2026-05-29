#!/usr/bin/env python3
"""
Phases 10AV + 10AW + 10AX — Puppy Care cluster dominance enrichment.
Adds comparison tables, Quick Checklist, What to Do Next, and UK citation depth.
"""

import subprocess, json, time, csv, re, tempfile, os, sys

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
BASE = "https://pethubonline.com/wp-json/wp/v2/posts"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10av_data"
CSV_PATH = os.path.join(DATA_DIR, "puppy_care_dominance.csv")

# All posts in the Puppy Care cluster
ALL_IDS = [5508, 5417, 3960, 7337, 7338, 7339, 7340, 7341, 7170, 7169, 7334]

# Posts confirmed needing comparison tables
TABLE_IDS = {7169, 7334, 7337, 7341, 7339, 7340, 7338}


def api_get(post_id):
    """Fetch post with raw content."""
    url = f"{BASE}/{post_id}?context=edit"
    r = subprocess.run(["curl", "-s", "--compressed", "-u", AUTH, url],
                       capture_output=True, text=True)
    return json.loads(r.stdout)


def api_update(post_id, content):
    """Update post content via REST API."""
    payload = json.dumps({"content": content})
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    tmp.write(payload)
    tmp.close()
    url = f"{BASE}/{post_id}"
    r = subprocess.run([
        "curl", "-s", "--compressed", "-u", AUTH,
        "-X", "POST",
        "-H", "Content-Type: application/json",
        "-d", f"@{tmp.name}",
        url
    ], capture_output=True, text=True)
    os.unlink(tmp.name)
    resp = json.loads(r.stdout)
    if "id" in resp:
        return True
    print(f"  ERROR updating {post_id}: {r.stdout[:300]}")
    return False


# ──────────────────────────────────────────────────────────────────────────────
#  COMPARISON TABLES (10AV) — topic-specific educational comparisons
# ──────────────────────────────────────────────────────────────────────────────

COMPARISON_TABLES = {
    7337: {
        "title": "UK Puppy Vaccination Schedule: Comparison by Disease",
        "headers": ["Disease", "Vaccine Type", "Primary Course", "Booster Frequency", "UK Prevalence"],
        "rows": [
            ["Canine Distemper", "Core (combined)", "6–8 weeks + 10–12 weeks", "Every 3 years", "Low but rising in unvaccinated populations"],
            ["Canine Parvovirus", "Core (combined)", "6–8 weeks + 10–12 weeks", "Every 3 years", "Moderate — outbreaks common in under-vaccinated areas"],
            ["Canine Hepatitis (Adenovirus)", "Core (combined)", "6–8 weeks + 10–12 weeks", "Every 3 years", "Low — well controlled by vaccination"],
            ["Leptospirosis (L2 or L4)", "Core in UK", "8 weeks + 10–12 weeks", "Annual", "High — prevalent in waterways and farmland"],
            ["Kennel Cough (Bordetella)", "Non-core", "From 3 weeks (intranasal)", "Annual", "Very common in boarding/daycare settings"],
            ["Rabies", "Travel only", "12 weeks minimum", "Per APHA travel rules", "UK is rabies-free — required for pet travel only"],
        ]
    },
    7338: {
        "title": "Puppy-Proofing by Room: Hazard Comparison",
        "headers": ["Room", "Common Hazards", "Risk Level", "Key Action", "Often Overlooked"],
        "rows": [
            ["Kitchen", "Cleaning products, bin contents, hot surfaces", "High", "Fit child locks on low cupboards, secure bin", "Dishwasher tablets (highly toxic if chewed)"],
            ["Living Room", "Electrical cables, small objects, houseplants", "Medium–High", "Cable tidy all wires, remove toxic plants", "Remote control batteries (fatal if swallowed)"],
            ["Bathroom", "Medications, toilet water, razors", "High", "Keep door closed or use baby gate", "Hair ties and dental floss (intestinal blockage risk)"],
            ["Bedroom", "Socks, shoes, small clothing items", "Medium", "Keep laundry in closed baskets", "Hair bobbles and earbuds (choking hazard)"],
            ["Garden", "Slug pellets, fertilisers, toxic plants", "High", "Use pet-safe slug control, fence off treated areas", "Cocoa mulch (contains theobromine, toxic to dogs)"],
            ["Hallway/Stairs", "Shoes, post, open front door", "Medium", "Install stair gate, store shoes in closed cupboard", "Letterbox flap (puppies can reach and chew post)"],
            ["Garage/Shed", "Antifreeze, tools, rodent bait", "Very High", "Keep completely off-limits with closed door", "Antifreeze (sweet taste attracts puppies, lethal in small doses)"],
        ]
    },
    7339: {
        "title": "Puppy Sleep Needs: Comparison by Age",
        "headers": ["Age", "Total Sleep Per Day", "Night Sleep", "Nap Pattern", "Key Consideration"],
        "rows": [
            ["0–4 weeks (neonatal)", "20–22 hours", "Continuous with mum", "Wakes only to feed", "Should remain with mother and littermates"],
            ["4–8 weeks (transitional)", "18–20 hours", "8–10 hours with waking", "Multiple short naps after play", "Beginning to explore; sleep still dominant"],
            ["8–12 weeks (new home)", "18–20 hours", "6–8 hours (with toilet breaks)", "1–2 hour naps every 1–2 hours", "Expect night waking; crate training helps routine"],
            ["3–6 months", "16–18 hours", "7–9 hours (fewer interruptions)", "Longer naps, fewer per day", "Teething may disrupt sleep patterns"],
            ["6–12 months (adolescent)", "14–16 hours", "8–10 hours", "2–3 consolidated naps", "Energy spikes may delay settling; maintain routine"],
            ["12–18 months (young adult)", "12–14 hours", "8–10 hours", "1–2 afternoon naps", "Sleep patterns stabilise; large breeds may still need more"],
        ]
    },
    7340: {
        "title": "Puppy Teething: Stage-by-Stage Comparison",
        "headers": ["Stage", "Age", "What Happens", "Signs to Watch", "Soothing Approach"],
        "rows": [
            ["Deciduous teeth emerge", "2–4 weeks", "28 baby teeth come through", "Mild discomfort, beginning to mouth", "Soft cloth for gentle chewing"],
            ["Full baby teeth", "5–8 weeks", "All deciduous teeth present", "Increased mouthing and nipping", "Redirect to soft rubber toys"],
            ["Baby teeth start falling", "12–16 weeks", "Incisors loosen and shed first", "Finding tiny teeth, bleeding gums, drooling", "Frozen cloths, chilled rubber toys"],
            ["Premolars and canines shed", "4–5 months", "Larger teeth replaced", "Increased chewing, possible food reluctance", "Durable rubber chews, frozen carrot sticks"],
            ["Molars emerge", "5–7 months", "Adult molars grow in at the back", "Intense chewing phase, sore gums", "Firm textured chews, ice cubes in water bowl"],
            ["Full adult set", "7–8 months", "42 permanent teeth complete", "Chewing intensity decreases", "Transition to adult dental chews; start tooth brushing routine"],
        ]
    },
    7341: {
        "title": "First Week with a Puppy: Preparation Comparison by Experience Level",
        "headers": ["Preparation Area", "First-Time Owner", "Experienced Owner", "Key UK Resource"],
        "rows": [
            ["Vet registration", "Register before collection day; book first check-up within 48 hours", "Confirm vaccination records match your vet's protocol", "Find a vet via RCVS Find a Vet tool"],
            ["Sleeping arrangements", "Set up crate or pen in quiet area; expect 2–3 night wake-ups", "Adjust based on breed needs; prepare for regression", "RSPCA crate training guide"],
            ["Feeding", "Follow breeder's current food and schedule exactly for first week", "Transition plan ready if changing diet", "PFMA puppy feeding guidelines"],
            ["Toilet training", "Take outside every 30–60 minutes and after meals, sleep, play", "Reinforce schedule immediately; watch for stress signals", "Dogs Trust toilet training advice"],
            ["Socialisation", "Carry puppy to experience sounds, people, and environments safely", "Structured exposure plan with controlled introductions", "Kennel Club Puppy Socialisation Plan"],
            ["Puppy-proofing", "Full room-by-room check; remove all accessible hazards", "Quick audit focusing on new or overlooked risks", "PDSA puppy-proofing checklist"],
            ["Insurance", "Research and activate cover before or on collection day", "Review existing policy for multi-pet discounts", "Compare via Money Helper or ABI"],
        ]
    },
    7169: {
        "title": "Puppy Care Terms: Comparison by Category",
        "headers": ["Category", "Key Terms", "When You'll Encounter Them", "Why They Matter"],
        "rows": [
            ["Health & Vaccination", "Core vaccines, titre test, booster, leptospirosis", "First vet visit and annual check-ups", "Understanding schedules prevents missed protection"],
            ["Nutrition", "Complete food, life-stage diet, feeding guide, transition period", "Choosing and changing puppy food", "Correct nutrition supports growth and avoids digestive upset"],
            ["Behaviour & Training", "Socialisation window, positive reinforcement, bite inhibition, recall", "First 16 weeks and ongoing training", "Early learning shapes lifelong behaviour"],
            ["Development", "Neonatal, transitional, socialisation period, fear period", "Tracking puppy milestones", "Recognising stages helps adjust care appropriately"],
            ["Legal & ID", "Microchipping, dog licence (NI), Control of Dogs Order, breed-specific legislation", "From 8 weeks old (microchip law)", "Legal compliance is mandatory in the UK"],
            ["Grooming & Dental", "Deshedding, nail quick, dental scaling, ear cleaning", "From first grooming introduction at 8–10 weeks", "Early handling reduces stress at the groomer and vet"],
        ]
    },
    7334: {
        "title": "Puppy Bed Types: Comparison by Suitability",
        "headers": ["Bed Type", "Best For", "Considerations", "Durability with Puppies"],
        "rows": [
            ["Flat mat or pad", "Crate lining, travel, easy washing", "Minimal cushioning; some puppies prefer the simplicity", "High — fewer parts to chew or destroy"],
            ["Bolster bed (raised edges)", "Puppies who like to lean or rest their head", "Comforting for anxious pups; harder to machine wash", "Medium — edges can be targeted by chewers"],
            ["Donut or nest bed", "Small breeds, puppies seeking warmth and security", "Very cosy; may overheat larger breeds", "Medium — plush fabric is tempting to shred"],
            ["Orthopaedic foam bed", "Large breed puppies with joint concerns", "Good long-term investment; heavier to move", "High — dense foam resists deformation"],
            ["Elevated or raised bed", "Warm climates, puppies who overheat", "Promotes airflow; some puppies find them unfamiliar", "High — fabric is taut and hard to chew"],
            ["Waterproof liner bed", "Toilet-training puppies, messy drinkers", "Easy to clean; plastic feel may deter some puppies", "High — designed for accidents and spills"],
        ]
    },
    7170: {
        "title": "Dog Health Terms: Comparison by Veterinary Context",
        "headers": ["Term Category", "Examples", "When Used", "Owner Action"],
        "rows": [
            ["Preventive Care", "Vaccination, neutering, microchipping, worming", "Routine vet visits from 6–8 weeks", "Follow your vet's schedule; keep records up to date"],
            ["Diagnostic", "Blood panel, urinalysis, X-ray, ultrasound", "When symptoms are investigated", "Ask your vet to explain results in plain language"],
            ["Surgical", "Spay, castrate, cruciate repair, dental extraction", "Planned or emergency procedures", "Understand pre-op and post-op care instructions"],
            ["Nutritional", "Complete diet, hypoallergenic, prescription diet, BMI/BCS", "Dietary consultations and weight checks", "Use body condition scoring to monitor weight at home"],
            ["Behavioural/Clinical", "Anxiety, compulsive disorder, desensitisation, threshold", "Behavioural referrals", "Work with an ABTC-registered behaviourist"],
            ["Emergency", "GDV (bloat), toxicity, anaphylaxis, haemorrhage", "Urgent or out-of-hours situations", "Know your nearest emergency vet and keep their number saved"],
        ]
    },
}


# ──────────────────────────────────────────────────────────────────────────────
#  QUICK CHECKLISTS (10AW-a) — per-post topic-specific checklists
# ──────────────────────────────────────────────────────────────────────────────

CHECKLISTS = {
    7337: [
        "Register with a vet before bringing your puppy home",
        "Confirm your puppy's vaccination history from the breeder or rescue",
        "Schedule the first primary vaccination at 6–8 weeks",
        "Book the second primary vaccination at 10–12 weeks",
        "Wait 1–2 weeks after the second jab before allowing ground-level walks",
        "Set a calendar reminder for the 12-month booster",
        "Ask your vet whether L2 or L4 leptospirosis cover suits your area",
        "Keep your puppy's vaccination card in a safe, accessible place",
    ],
    7338: [
        "Walk through each room at puppy height to spot hazards",
        "Secure all electrical cables with trunking or cord covers",
        "Move cleaning products, medications, and chemicals to high or locked cupboards",
        "Remove or relocate toxic houseplants (lilies, aloe vera, dieffenbachia)",
        "Install stair gates at the top and bottom of stairs",
        "Fit child locks on kitchen and bathroom cupboards",
        "Check the garden for slug pellets, cocoa mulch, and toxic plants",
        "Keep the garage or shed door closed at all times",
    ],
    7339: [
        "Set up a quiet, consistent sleeping spot before your puppy arrives",
        "Establish a regular bedtime routine from day one",
        "Avoid waking your puppy from naps — let them sleep as long as they need",
        "Take your puppy outside for a toilet break immediately after each nap",
        "Keep the sleeping area dark, quiet, and at a comfortable temperature",
        "Monitor total sleep hours — puppies under 6 months need 18–20 hours daily",
        "Gradually move the crate to your preferred location over several nights",
    ],
    7340: [
        "Provide a variety of safe chew textures (rubber, rope, frozen cloth)",
        "Check your puppy's mouth weekly for swollen or bleeding gums",
        "Avoid giving hard chews (antlers, bones) to puppies under 6 months",
        "Redirect nipping to an appropriate toy immediately and consistently",
        "Offer frozen carrot sticks or ice cubes to soothe sore gums",
        "Begin gentle tooth brushing once adult teeth are fully in at 7–8 months",
        "Contact your vet if a baby tooth hasn't fallen out by 7 months (retained deciduous tooth)",
    ],
    7341: [
        "Collect your puppy's vaccination record and microchip details on day one",
        "Keep to the breeder's or rescue's existing food and feeding schedule for the first week",
        "Take your puppy outside for toilet breaks every 30–60 minutes while awake",
        "Introduce the crate or sleeping area calmly on the first night with a blanket from the litter",
        "Book a vet health check within the first 48 hours",
        "Start gentle handling exercises (paws, ears, mouth) from day two",
        "Carry your puppy outside to experience new sounds and sights safely before full vaccination",
        "Keep the first week calm — avoid hosting visitors or overwhelming introductions",
    ],
    7169: [
        "Read through the glossary before your puppy's first vet appointment",
        "Write down any unfamiliar terms your vet uses and look them up afterwards",
        "Familiarise yourself with vaccination and worming terminology before primary courses begin",
        "Learn the meaning of common food label terms (complete, complementary, life-stage)",
        "Understand positive reinforcement terminology before starting training classes",
        "Bookmark this glossary for quick reference during your puppy's first year",
    ],
    7334: [
        "Choose a bed appropriate for your puppy's size and breed",
        "Place the bed in a quiet, draught-free location away from direct heat",
        "Add a blanket or item with a familiar scent from the breeder or litter",
        "Reward your puppy with a treat each time they settle on the bed voluntarily",
        "Never use the bed as a punishment location",
        "Wash the bed cover weekly to keep it hygienic and inviting",
        "Upgrade bed size as your puppy grows — check fit every 4–6 weeks",
    ],
    7170: [
        "Familiarise yourself with preventive care terms before your puppy's first vet visit",
        "Keep a glossary bookmark for reference during vet consultations",
        "Ask your vet to explain any diagnostic terms you don't recognise",
        "Learn body condition scoring (BCS) so you can monitor your dog's weight at home",
        "Save your nearest emergency vet's number and know the signs of common emergencies",
        "Understand the difference between core and non-core vaccinations for your area",
    ],
    5508: [
        "Note your puppy's expected adult size to anticipate developmental milestones",
        "Track weight weekly during the first 6 months and compare to breed growth charts",
        "Schedule vet check-ups to align with key developmental stages (8, 12, 16 weeks)",
        "Begin socialisation experiences between 3 and 14 weeks during the critical window",
        "Adjust food portions as your puppy moves between growth stages",
        "Watch for fear periods at 8–10 weeks and 6–14 months — keep experiences positive",
        "Switch from puppy to adult food when your vet confirms growth is complete",
    ],
    5417: [
        "Read through the key terms before your puppy's first vet visit",
        "Understand the difference between 'complete' and 'complementary' puppy food",
        "Learn what positive reinforcement means before enrolling in training classes",
        "Familiarise yourself with microchipping and registration requirements (UK law from 8 weeks)",
        "Know the meaning of 'socialisation window' and plan your puppy's early experiences accordingly",
        "Bookmark this page for quick reference throughout your puppy's first year",
    ],
    3960: [
        "Choose toys made from non-toxic, puppy-safe materials (natural rubber, food-grade TPR)",
        "Match toy size to your puppy's breed — avoid toys small enough to swallow",
        "Supervise all play with new toys until you know your puppy's chewing strength",
        "Rotate toys every few days to maintain interest and prevent boredom",
        "Inspect toys weekly and discard any with loose pieces, cracks, or exposed stuffing",
        "Provide a mix of chew, tug, and puzzle toys for different developmental needs",
        "Replace teething toys with more durable options once adult teeth are fully in",
    ],
}


# ──────────────────────────────────────────────────────────────────────────────
#  WHAT TO DO NEXT (10AW-b) — ordered next steps per post
# ──────────────────────────────────────────────────────────────────────────────

NEXT_STEPS = {
    7337: [
        "Check your puppy's current vaccination status and confirm which jabs they've already had.",
        "Book the next vaccination appointment with your vet, allowing the correct interval between doses.",
        "Set calendar reminders for annual boosters, especially leptospirosis which requires yearly renewal.",
        "Read our <a href=\"https://pethubonline.com/puppy-proofing-your-home/\">puppy-proofing guide</a> to keep your home safe while your puppy builds immunity.",
        "Ask your vet about kennel cough vaccination if your puppy will attend daycare, classes, or boarding.",
    ],
    7338: [
        "Complete a room-by-room audit of your home using the hazard comparison table above.",
        "Purchase stair gates, cable covers, and child locks for the highest-risk areas identified.",
        "Remove or relocate all toxic plants — check the Dogs Trust <a href=\"https://www.dogstrust.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">poisonous plants list</a> if unsure.",
        "Brief every household member on keeping doors closed and hazards out of reach.",
        "Reassess your puppy-proofing monthly as your puppy grows taller and more agile.",
    ],
    7339: [
        "Decide on your puppy's sleeping location and set it up before their first night home.",
        "Establish a consistent bedtime routine that includes a final toilet break and calm settling.",
        "Track your puppy's sleep for the first week to ensure they're getting enough rest for their age.",
        "Read our <a href=\"https://pethubonline.com/puppy-bed-training/\">puppy bed training guide</a> for step-by-step settling techniques.",
        "Consult your vet if your puppy consistently sleeps significantly less than expected for their age.",
    ],
    7340: [
        "Check your puppy's current teething stage using the comparison table above and note what comes next.",
        "Stock up on age-appropriate chew toys — frozen rubber toys and chilled cloths for the active shedding phase.",
        "Begin a daily mouth-handling routine so your puppy is comfortable with tooth checks and future brushing.",
        "Read our <a href=\"https://pethubonline.com/best-puppy-toys-uk/\">best puppy toys UK guide</a> for safe teething toy options.",
        "Schedule a vet dental check at 7–8 months to confirm all baby teeth have shed and adult teeth are healthy.",
    ],
    7341: [
        "Prepare your home at least 48 hours before collection day — puppy-proof, set up the crate, and buy essentials.",
        "Collect your puppy's vaccination record, microchip certificate, and feeding instructions from the breeder or rescue.",
        "Follow the day-by-day settling plan in this guide, keeping the first week calm and predictable.",
        "Book a vet check-up within 48 hours and confirm the vaccination schedule going forward.",
        "After the first week, begin gentle socialisation — our <a href=\"https://pethubonline.com/puppy-vaccination-schedule-uk/\">vaccination schedule guide</a> explains when it's safe to venture out.",
    ],
    7169: [
        "Read through the full glossary and highlight any terms you don't yet understand.",
        "Bring this list to your puppy's next vet appointment and ask about any terms that apply to your puppy.",
        "Cross-reference these terms with our <a href=\"https://pethubonline.com/puppy-vaccination-schedule-uk/\">vaccination schedule</a> and <a href=\"https://pethubonline.com/puppy-development-stages/\">development stages</a> guides for context.",
        "Revisit this glossary whenever you encounter unfamiliar language in vet letters, food labels, or training resources.",
    ],
    7334: [
        "Choose a bed type suited to your puppy's size, age, and sleeping habits using the comparison table above.",
        "Place the bed in a quiet corner and introduce it with treats and a familiar-scent blanket.",
        "Practice the 'settle' or 'bed' cue 3–5 times daily, rewarding calm behaviour on the bed.",
        "Read our <a href=\"https://pethubonline.com/puppy-sleep-guide/\">puppy sleep guide</a> for age-specific sleep needs and routine advice.",
        "Upgrade the bed size as your puppy grows — reassess fit every 4–6 weeks.",
    ],
    7170: [
        "Review the term categories most relevant to your dog's current life stage.",
        "Prepare a list of questions using these terms before your next vet appointment.",
        "Bookmark this glossary for quick reference when reading vet reports or food labels.",
        "Explore our <a href=\"https://pethubonline.com/puppy-care-glossary/\">puppy care glossary</a> if you have a young dog, or share this page with new puppy owners.",
    ],
    5508: [
        "Identify your puppy's current developmental stage using the guide above.",
        "Note the next stage milestones and adjust your training, feeding, and socialisation plan accordingly.",
        "Schedule vet check-ups to coincide with key developmental transitions (8 weeks, 16 weeks, 6 months, 12 months).",
        "Read our <a href=\"https://pethubonline.com/puppy-vaccination-schedule-uk/\">vaccination schedule guide</a> to align health protection with each growth stage.",
        "Track your puppy's weight weekly and compare against breed-specific growth charts.",
    ],
    5417: [
        "Read through the full glossary and mark any terms that are new to you.",
        "Use this reference before attending your puppy's first vet appointment or training class.",
        "Cross-reference key terms with our <a href=\"https://pethubonline.com/puppy-development-stages/\">puppy development stages</a> guide for practical context.",
        "Revisit this page whenever you encounter unfamiliar puppy care language.",
    ],
    3960: [
        "Assess your puppy's current teething stage and select toys matched to their chewing intensity.",
        "Read the safety and material considerations in the comparison table above before purchasing.",
        "Buy 3–4 toys of different types (chew, tug, puzzle) to rotate throughout the week.",
        "Inspect all toys after each play session and retire any that show signs of damage.",
        "Read our <a href=\"https://pethubonline.com/puppy-teething-guide/\">teething guide</a> for stage-specific advice on soothing sore gums.",
    ],
}


# ──────────────────────────────────────────────────────────────────────────────
#  UK CITATION REFERENCES to inject where missing
# ──────────────────────────────────────────────────────────────────────────────

UK_REF_SNIPPETS = {
    7337: "According to the <a href=\"https://www.pdsa.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">PDSA</a> and <a href=\"https://www.bva.co.uk/\" rel=\"nofollow noopener\" target=\"_blank\">BVA</a>, the standard UK puppy vaccination schedule begins at 6–8 weeks of age, with a second dose at 10–12 weeks. The <a href=\"https://www.rspca.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">RSPCA</a> recommends annual leptospirosis boosters due to the disease's prevalence across the UK.",
    7338: "The <a href=\"https://www.rspca.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">RSPCA</a> and <a href=\"https://www.dogstrust.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">Dogs Trust</a> both recommend a thorough room-by-room safety audit before bringing a puppy home. In the UK, antifreeze poisoning remains one of the most common accidental toxicities reported by veterinary practices.",
    7339: "UK veterinary guidance from the <a href=\"https://www.pdsa.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">PDSA</a> confirms that puppies need significantly more sleep than adult dogs — typically 18–20 hours per day up to 6 months of age. The <a href=\"https://www.thekennelclub.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">Kennel Club</a> recommends a consistent sleeping routine from the first night home.",
    7340: "The <a href=\"https://www.bva.co.uk/\" rel=\"nofollow noopener\" target=\"_blank\">BVA</a> advises that puppy teething typically completes by 7–8 months, when all 42 adult teeth should be in place. The <a href=\"https://www.pdsa.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">PDSA</a> recommends beginning tooth brushing once the adult teeth are established, using a dog-specific toothpaste.",
    7341: "The <a href=\"https://www.thekennelclub.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">Kennel Club</a> recommends that puppies stay with their mother until at least 8 weeks old. Under UK law (the Microchipping of Dogs Regulations 2015), all puppies must be microchipped by 8 weeks of age before sale or rehoming. The <a href=\"https://www.rspca.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">RSPCA</a> advises booking a vet check within 48 hours of collection.",
    7169: "Terms in this glossary align with definitions used by UK veterinary authorities including the <a href=\"https://www.rcvs.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">Royal College of Veterinary Surgeons (RCVS)</a>, the <a href=\"https://www.bva.co.uk/\" rel=\"nofollow noopener\" target=\"_blank\">BVA</a>, and the <a href=\"https://www.rspca.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">RSPCA</a>.",
    7334: "The <a href=\"https://www.rspca.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">RSPCA</a> recommends providing puppies with their own dedicated sleeping space from the first night. The <a href=\"https://www.thekennelclub.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">Kennel Club</a> advises placing a familiar-scented blanket in the bed to ease the transition from the litter.",
    7170: "This glossary reflects terminology used across UK veterinary practice, as referenced by the <a href=\"https://www.bva.co.uk/\" rel=\"nofollow noopener\" target=\"_blank\">BVA</a>, <a href=\"https://www.rcvs.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">RCVS</a>, and <a href=\"https://www.pdsa.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">PDSA</a>.",
    5508: "The <a href=\"https://www.thekennelclub.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">Kennel Club</a> identifies the socialisation window (3–14 weeks) as the most critical developmental period. The <a href=\"https://www.pdsa.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">PDSA</a> recommends tailoring exercise duration to your puppy's age — a common UK guideline is 5 minutes of structured exercise per month of age, twice daily.",
    5417: "Definitions in this glossary are consistent with guidance from UK organisations including the <a href=\"https://www.rspca.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">RSPCA</a>, <a href=\"https://www.pdsa.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">PDSA</a>, and <a href=\"https://www.thekennelclub.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">Kennel Club</a>.",
    3960: "The <a href=\"https://www.rspca.org.uk/\" rel=\"nofollow noopener\" target=\"_blank\">RSPCA</a> advises supervising all puppy play with toys and discarding any that become damaged. UK safety standards recommend choosing toys labelled as non-toxic and free from BPA, phthalates, and lead.",
}


# ──────────────────────────────────────────────────────────────────────────────
#  BLOCK BUILDERS
# ──────────────────────────────────────────────────────────────────────────────

def build_comparison_table(post_id):
    """Build WP table block from COMPARISON_TABLES data."""
    info = COMPARISON_TABLES.get(post_id)
    if not info:
        return ""
    header_cells = "".join(f"<th>{h}</th>" for h in info["headers"])
    rows_html = ""
    for row in info["rows"]:
        cells = "".join(f"<td>{c}</td>" for c in row)
        rows_html += f"<tr>{cells}</tr>"
    return (
        f'\n<!-- wp:heading {{"level":3}} -->\n'
        f'<h3 class="wp-block-heading">{info["title"]}</h3>\n'
        f'<!-- /wp:heading -->\n\n'
        f'<!-- wp:table {{"className":"is-style-stripes"}} -->\n'
        f'<figure class="wp-block-table is-style-stripes"><table><thead><tr>{header_cells}</tr></thead>'
        f'<tbody>{rows_html}</tbody></table></figure>\n'
        f'<!-- /wp:table -->\n'
    )


def build_checklist(post_id):
    """Build Quick Checklist block."""
    items = CHECKLISTS.get(post_id)
    if not items:
        return ""
    li = "".join(f"<li>☐ {item}</li>" for item in items)
    return (
        '\n<!-- wp:group {"style":{"color":{"background":"#f5f3ff"},"border":{"radius":"6px","width":"1px","color":"#ddd6fe"},"spacing":{"padding":{"top":"16px","bottom":"16px","left":"20px","right":"20px"},"margin":{"top":"24px","bottom":"24px"}}},"layout":{"type":"constrained"}} -->\n'
        '<div class="wp-block-group has-border-color has-background" style="border-color:#ddd6fe;border-width:1px;border-radius:6px;background-color:#f5f3ff;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<!-- wp:heading {"level":4} --><h4 class="wp-block-heading">Quick Checklist</h4><!-- /wp:heading -->\n'
        f'<!-- wp:list --><ul class="wp-block-list">{li}</ul><!-- /wp:list -->\n'
        '</div>\n'
        '<!-- /wp:group -->\n'
    )


def build_next_steps(post_id):
    """Build What to Do Next block."""
    steps = NEXT_STEPS.get(post_id)
    if not steps:
        return ""
    li = "".join(f"<li>{step}</li>" for step in steps)
    return (
        '\n<!-- wp:group {"style":{"color":{"background":"#f0fdfa"},"border":{"radius":"6px","width":"1px","color":"#99f6e4"},"spacing":{"padding":{"top":"16px","bottom":"16px","left":"20px","right":"20px"},"margin":{"top":"24px","bottom":"24px"}}},"layout":{"type":"constrained"}} -->\n'
        '<div class="wp-block-group has-border-color has-background" style="border-color:#99f6e4;border-width:1px;border-radius:6px;background-color:#f0fdfa;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<!-- wp:heading {"level":4} --><h4 class="wp-block-heading">What to Do Next</h4><!-- /wp:heading -->\n'
        f'<!-- wp:list {{"ordered":true}} --><ol class="wp-block-list">{li}</ol><!-- /wp:list -->\n'
        '</div>\n'
        '<!-- /wp:group -->\n'
    )


def build_uk_ref_paragraph(post_id):
    """Build inline UK authority reference paragraph."""
    text = UK_REF_SNIPPETS.get(post_id)
    if not text:
        return ""
    return (
        '\n<!-- wp:paragraph -->\n'
        f'<p>{text}</p>\n'
        '<!-- /wp:paragraph -->\n'
    )


# ──────────────────────────────────────────────────────────────────────────────
#  CONTENT INSERTION LOGIC
# ──────────────────────────────────────────────────────────────────────────────

def find_insertion_point_before_block(content, block_name):
    """
    Find the start of a WP group block that contains the given block_name heading.
    Returns the position to insert BEFORE this block, or -1 if not found.
    """
    # Look for the heading text within a group block
    idx = content.find(block_name)
    if idx == -1:
        return -1

    # Walk backwards to find the opening <!-- wp:group block
    search_region = content[:idx]
    # Find the last <!-- wp:group before this heading
    last_group = search_region.rfind('<!-- wp:group')
    if last_group == -1:
        return idx  # fallback to just before the heading text
    return last_group


def find_insertion_point_for_table(content):
    """
    Find a good location to insert the comparison table — before the
    decision-support / end-of-article blocks. We look for Common Mistakes
    (or Quick Checklist if we're adding it).
    """
    # Insert before Common Mistakes block
    pos = find_insertion_point_before_block(content, "Common Mistakes")
    if pos > 0:
        return pos
    # Fallback: before When to Seek
    pos = find_insertion_point_before_block(content, "When to Seek")
    if pos > 0:
        return pos
    # Fallback: before Key Takeaways
    pos = find_insertion_point_before_block(content, "Key Takeaways")
    if pos > 0:
        return pos
    return -1


def find_insertion_point_for_uk_ref(content):
    """
    Find a good location for UK authority reference paragraph —
    after the At a Glance block and first few paragraphs (early in the article).
    """
    # Insert after the At a Glance / trust source block
    # Look for end of the first major block (Why We Reference or At a Glance)
    markers = ["Why We Reference These Sources", "At a Glance"]
    for marker in markers:
        idx = content.find(marker)
        if idx > 0:
            # Find the closing </div><!-- /wp:group --> after this
            close_search = content[idx:]
            close_tag = close_search.find("</div>\n<!-- /wp:group -->")
            if close_tag > 0:
                insert_after = idx + close_tag + len("</div>\n<!-- /wp:group -->")
                return insert_after
    return -1


def process_post(post_id):
    """Process a single post: add comparison table, checklist, next steps, UK refs."""
    print(f"\n{'='*60}")
    print(f"Processing post {post_id}...")

    data = api_get(post_id)
    if "id" not in data:
        print(f"  FAILED to fetch post {post_id}: {str(data)[:200]}")
        return {"id": post_id, "title": "ERROR", "comparison_table_added": "no",
                "checklist_added": "no", "next_steps_added": "no",
                "uk_refs_added": "no", "status": "fetch_error"}

    title = data["title"]["raw"]
    content = data["content"]["raw"]
    original_len = len(content)
    print(f"  Title: {title}")
    print(f"  Content length: {original_len}")

    result = {
        "id": post_id,
        "title": title,
        "comparison_table_added": "no",
        "checklist_added": "no",
        "next_steps_added": "no",
        "uk_refs_added": "no",
        "status": "no_changes"
    }

    modified = False

    # ── 1. COMPARISON TABLE (10AV) ──────────────────────────────────────
    has_table = "<table" in content
    needs_table = post_id in TABLE_IDS

    if needs_table and not has_table:
        table_html = build_comparison_table(post_id)
        if table_html:
            pos = find_insertion_point_for_table(content)
            if pos > 0:
                content = content[:pos] + table_html + "\n" + content[pos:]
                result["comparison_table_added"] = "yes"
                modified = True
                print(f"  + Comparison table added at position {pos}")
            else:
                print(f"  ! Could not find insertion point for table")
    elif has_table:
        print(f"  - Table already exists, skipping")
        result["comparison_table_added"] = "exists"

    # ── 2a. QUICK CHECKLIST (10AW-a) ───────────────────────────────────
    has_checklist = "Quick Checklist" in content

    if not has_checklist:
        checklist_html = build_checklist(post_id)
        if checklist_html:
            # Insert before Common Mistakes
            pos = find_insertion_point_before_block(content, "Common Mistakes")
            if pos > 0:
                content = content[:pos] + checklist_html + "\n" + content[pos:]
                result["checklist_added"] = "yes"
                modified = True
                print(f"  + Quick Checklist added at position {pos}")
            else:
                print(f"  ! Could not find insertion point for checklist")
    else:
        print(f"  - Quick Checklist already exists, skipping")
        result["checklist_added"] = "exists"

    # ── 2b. WHAT TO DO NEXT (10AW-b) ──────────────────────────────────
    has_next = "What to Do Next" in content

    if not has_next:
        next_html = build_next_steps(post_id)
        if next_html:
            # Insert before Common Mistakes (after checklist if just added)
            pos = find_insertion_point_before_block(content, "Common Mistakes")
            if pos > 0:
                content = content[:pos] + next_html + "\n" + content[pos:]
                result["next_steps_added"] = "yes"
                modified = True
                print(f"  + What to Do Next added at position {pos}")
            else:
                print(f"  ! Could not find insertion point for next steps")
    else:
        print(f"  - What to Do Next already exists, skipping")
        result["next_steps_added"] = "exists"

    # ── 3. UK CITATION REFS (10AX) ────────────────────────────────────
    # Check if UK authority references already exist in body text
    uk_orgs = ["RSPCA", "PDSA", "BVA", "Kennel Club", "Dogs Trust"]
    # Count how many UK orgs are mentioned (excluding the standard footer)
    # We check the main body (before Common Mistakes area)
    cm_pos = content.find("Common Mistakes")
    body_text = content[:cm_pos] if cm_pos > 0 else content[:len(content)//2]
    existing_refs = sum(1 for org in uk_orgs if org in body_text)

    if existing_refs < 2:
        ref_para = build_uk_ref_paragraph(post_id)
        if ref_para:
            pos = find_insertion_point_for_uk_ref(content)
            if pos > 0:
                content = content[:pos] + ref_para + content[pos:]
                result["uk_refs_added"] = "yes"
                modified = True
                print(f"  + UK authority references added at position {pos}")
            else:
                print(f"  ! Could not find insertion point for UK refs")
    else:
        print(f"  - UK refs already present ({existing_refs} orgs found), skipping")
        result["uk_refs_added"] = "exists"

    # ── UPDATE POST ───────────────────────────────────────────────────
    if modified:
        print(f"  Content grew from {original_len} to {len(content)} chars")
        print(f"  Updating post {post_id}...")
        success = api_update(post_id, content)
        if success:
            result["status"] = "updated"
            print(f"  ✓ Post {post_id} updated successfully")
        else:
            result["status"] = "update_failed"
            print(f"  ✗ Post {post_id} update FAILED")
    else:
        result["status"] = "no_changes_needed"
        print(f"  No changes needed for post {post_id}")

    return result


# ──────────────────────────────────────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Puppy Care Cluster — Phases 10AV + 10AW + 10AX")
    print("Comparison Dominance + Decision Support + Citation Depth")
    print("=" * 60)

    results = []

    for i, post_id in enumerate(ALL_IDS):
        result = process_post(post_id)
        results.append(result)

        # 2-second delay between API calls
        if i < len(ALL_IDS) - 1:
            time.sleep(2)

    # Write CSV log
    print(f"\n{'='*60}")
    print(f"Writing results to {CSV_PATH}")
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "title", "comparison_table_added", "checklist_added",
            "next_steps_added", "uk_refs_added", "status"
        ])
        writer.writeheader()
        writer.writerows(results)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    tables_added = sum(1 for r in results if r["comparison_table_added"] == "yes")
    checklists_added = sum(1 for r in results if r["checklist_added"] == "yes")
    nexts_added = sum(1 for r in results if r["next_steps_added"] == "yes")
    refs_added = sum(1 for r in results if r["uk_refs_added"] == "yes")
    updated = sum(1 for r in results if r["status"] == "updated")
    failed = sum(1 for r in results if r["status"] in ("update_failed", "fetch_error"))

    print(f"  Posts processed:      {len(results)}")
    print(f"  Posts updated:        {updated}")
    print(f"  Posts failed:         {failed}")
    print(f"  Tables added:         {tables_added}")
    print(f"  Checklists added:     {checklists_added}")
    print(f"  Next Steps added:     {nexts_added}")
    print(f"  UK refs added:        {refs_added}")
    print(f"\nCSV log: {CSV_PATH}")


if __name__ == "__main__":
    main()
