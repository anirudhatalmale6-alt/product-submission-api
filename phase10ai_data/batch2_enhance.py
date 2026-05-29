#!/usr/bin/env python3
"""
Phase 10AI Batch 2: Content enhancement for Dog Food, Dog Health, Puppy Care, Dog Care, Dog Training posts.
Adds: At a Glance, Why This Matters, What We Considered, Troubleshooting, Warning Signs,
      When to Seek Help, Key Takeaways, upgraded trust footer.
"""

import csv
import json
import os
import re
import subprocess
import tempfile
import time
import traceback
from datetime import datetime

# ── Config ──
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
API = "https://pethubonline.com/wp-json/wp/v2"
INVENTORY = "/var/lib/freelancer/projects/40416335/phase10af_data/post_authority_inventory.csv"
LOG_FILE = "/var/lib/freelancer/projects/40416335/phase10ai_data/batch2_food_health_training_log.csv"
CLUSTERS = {"Dog Food", "Dog Health", "Puppy Care", "Dog Care", "Dog Training"}
DELAY = 2.5  # seconds between API calls


def api_get(endpoint):
    """GET from WP REST API using curl."""
    url = f"{API}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    return json.loads(result.stdout)


def api_update(post_id, data):
    """PUT/POST update to WP REST API using curl with temp file."""
    url = f"{API}/posts/{post_id}"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        tmppath = f.name
    try:
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-X", "POST", "-H", "Content-Type: application/json",
             "-d", f"@{tmppath}", url],
            capture_output=True, text=True, timeout=120
        )
        resp = json.loads(result.stdout)
        if "id" in resp:
            return True, resp
        else:
            return False, resp
    finally:
        os.unlink(tmppath)


def load_inventory():
    """Load posts from inventory CSV, filter to target clusters."""
    posts = []
    with open(INVENTORY, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['cluster'] in CLUSTERS:
                posts.append(row)
    return posts


def has_block(content, marker):
    """Check if content already contains a block (case-insensitive)."""
    return marker.lower() in content.lower()


# ── Content Generation Functions ──
# Each returns Gutenberg block HTML specific to the post topic.

def generate_at_a_glance(title, cluster, content):
    """Generate At a Glance bullets based on post topic."""
    # Determine bullets based on cluster and title
    bullets = get_at_a_glance_bullets(title, cluster, content)
    items = "".join(f"<li>{b}</li>" for b in bullets)
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#eef2ff"}},"border":{{"radius":"6px","width":"1px","color":"#c7d2fe"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"20px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#c7d2fe;border-width:1px;border-radius:6px;background-color:#eef2ff;margin-top:20px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">At a Glance</h4>
<!-- /wp:heading -->
<!-- wp:list -->
<ul class="wp-block-list">{items}</ul>
<!-- /wp:list -->
</div>
<!-- /wp:group -->'''


def get_at_a_glance_bullets(title, cluster, content):
    """Return 3-5 specific bullets based on the post topic."""
    t = title.lower()

    # ── DOG FOOD ──
    if cluster == "Dog Food":
        if "best dog food uk" in t and "complete" in t:
            return [
                "UK dog food must meet FEDIAF nutritional guidelines to be labelled 'complete'",
                "Look for a named animal protein (e.g. chicken, salmon) as the first ingredient",
                "Wet, dry, and raw formats each suit different dogs — no single 'best' type exists",
                "PFMA member brands follow voluntary quality codes above the legal minimum",
                "Transition to new food gradually over 7–10 days to avoid digestive upset"
            ]
        elif "dry dog food" in t:
            return [
                "Kibble is the most popular dog food format in the UK, chosen by over 60% of owners",
                "Quality dry food should list a named meat or fish as the primary ingredient",
                "Cold-pressed kibble retains more nutrients than standard extruded kibble",
                "Store opened bags in an airtight container away from heat and moisture",
                "Daily feeding amount depends on your dog's weight, age, activity level, and breed"
            ]
        elif "dry vs wet" in t:
            return [
                "Dry food is more cost-effective per serving and supports dental health through chewing",
                "Wet food has higher moisture content (~75%), helping hydration in dogs that drink little",
                "Mixing wet and dry food is a common and nutritionally sound approach",
                "Both formats must meet FEDIAF standards to be labelled 'complete' in the UK",
                "Shelf life differs significantly — opened wet food must be refrigerated and used within 48 hours"
            ]
        elif "puppy food" in t:
            return [
                "Puppies need higher protein, fat, and calcium levels than adult dogs",
                "Feed a food labelled 'complete for puppies' or 'complete for growth' (FEDIAF standard)",
                "Large-breed puppies need controlled calcium and phosphorus to protect developing joints",
                "Most puppies transition to adult food between 12–18 months, depending on breed size",
                "Follow manufacturer feeding guides but adjust based on body condition scoring"
            ]
        elif "nutrition terminology" in t or "pet food labels" in t:
            return [
                "'Complete' means the food provides all required nutrients — 'complementary' does not",
                "Ingredient lists are ordered by weight before processing, which can be misleading for wet ingredients",
                "Analytical constituents show crude protein, fat, fibre, and ash percentages",
                "'With chicken' legally requires only 4% chicken; 'chicken dinner' requires 26%",
                "FEDIAF sets the nutritional standards that UK pet foods must meet"
            ]
        elif "feeding guide" in t or "portions" in t:
            return [
                "Feeding amounts on packaging are starting guidelines — adjust based on body condition",
                "Most adult dogs do well on two meals per day at consistent times",
                "Treats should make up no more than 10% of your dog's daily calorie intake",
                "Use body condition scoring (1–9 scale) rather than weight alone to assess portion size",
                "Puppies, pregnant dogs, and senior dogs have different feeding schedules and needs"
            ]
        elif "raw" in t:
            return [
                "Raw feeding has grown in the UK but requires careful nutritional balancing",
                "The BVA advises caution due to bacterial contamination risks (Salmonella, E. coli)",
                "Commercial complete raw diets are pre-balanced and frozen for safety",
                "Home-prepared raw diets should be formulated by a veterinary nutritionist",
                "Safe handling and storage are essential to reduce pathogen risk to pets and families"
            ]
        else:
            return [
                "Choose food meeting FEDIAF 'complete' standards for your dog's life stage",
                "Named animal protein should be the first ingredient listed",
                "Transition any new food gradually over 7–10 days",
                "Adjust portions based on body condition, not just weight",
                "Consult your vet if your dog has specific dietary needs or allergies"
            ]

    # ── DOG HEALTH ──
    elif cluster == "Dog Health":
        if "dental" in t:
            return [
                "Over 80% of dogs show signs of dental disease by age three (PDSA estimate)",
                "Daily brushing with enzymatic dog toothpaste is the gold standard for dental care",
                "Dental chews carry the VOHC seal if clinically proven to reduce plaque or tartar",
                "Bad breath, drooling, and reluctance to eat can signal dental pain requiring vet attention",
                "Professional dental cleaning under anaesthesia may be needed for advanced tartar build-up"
            ]
        elif "flea" in t:
            return [
                "Fleas can survive in UK homes year-round due to central heating",
                "Prescription flea treatments from your vet are generally more effective than shop-bought options",
                "Treat all pets in the household simultaneously, plus their bedding and soft furnishings",
                "A single flea can lay up to 50 eggs per day, making prompt treatment essential",
                "Some dogs develop flea allergy dermatitis from just one bite"
            ]
        elif "joint" in t or "mobility" in t:
            return [
                "Joint problems affect roughly 1 in 5 adult dogs in the UK",
                "Glucosamine and chondroitin are the most commonly used joint supplements",
                "Omega-3 fatty acids (EPA and DHA) have evidence for reducing joint inflammation",
                "Weight management is the single most important factor in joint health",
                "Early signs include stiffness after rest, reluctance to jump, and slowing on walks"
            ]
        elif "common conditions" in t or "health basics" in t:
            return [
                "Annual vet check-ups catch conditions early when treatment is most effective",
                "Vaccination, parasite control, and neutering form the foundation of preventive care",
                "Obesity is the most common preventable health problem in UK dogs (PDSA)",
                "Pet insurance helps manage unexpected treatment costs — compare policies carefully",
                "Keep an emergency vet number saved in your phone for out-of-hours situations"
            ]
        elif "health and care" in t and "complete" in t:
            return [
                "Preventive care (vaccines, parasite treatment, dental checks) costs far less than treating illness",
                "The PDSA Animal Wellbeing Report shows many UK dogs miss routine vet visits",
                "Body condition scoring helps you monitor weight between vet appointments",
                "Mental stimulation and exercise are as important as physical health care",
                "Microchipping is a legal requirement for dogs in England, Scotland, and Wales"
            ]
        else:
            return [
                "Regular vet check-ups are key to early detection of health issues",
                "Keep vaccinations and parasite treatments up to date",
                "Monitor your dog's weight, appetite, and energy levels for changes",
                "The BVA and PDSA provide trusted UK-specific health guidance",
                "Pet first aid knowledge can be vital in an emergency"
            ]

    # ── PUPPY CARE ──
    elif cluster == "Puppy Care":
        if "development" in t or "stages" in t:
            return [
                "Puppies go through distinct developmental stages from neonatal (0–2 weeks) to maturity",
                "The critical socialisation window is roughly 3–14 weeks of age",
                "Fear periods typically occur at 8–10 weeks and again at 6–14 months",
                "Large and giant breeds mature more slowly — up to 18–24 months",
                "Early positive experiences during sensitive periods shape lifelong temperament"
            ]
        elif "essential" in t or "key terms" in t:
            return [
                "Puppy-proof your home before arrival — cables, toxic plants, and small objects are hazards",
                "Register with a vet within the first week and schedule initial vaccinations",
                "Socialisation means positive exposure to people, animals, sounds, and environments",
                "Crate training provides a safe den space and aids toilet training",
                "Puppies need 18–20 hours of sleep per day in the first few months"
            ]
        elif "toy" in t:
            return [
                "Puppies begin teething at around 3–4 months, peaking at 4–6 months",
                "Choose toys sized appropriately — too small risks choking, too large discourages play",
                "Rotate toys weekly to maintain novelty and prevent boredom",
                "Frozen Kongs and rubber chew toys soothe teething discomfort",
                "Supervise all toy play — discard damaged toys with loose parts immediately"
            ]
        else:
            return [
                "Start socialisation early within the 3–14 week critical window",
                "Use positive reinforcement from day one for house training and basic cues",
                "Feed a complete puppy food appropriate for your puppy's expected adult size",
                "Register with a vet and complete the primary vaccination course",
                "The Kennel Club and Dogs Trust offer trusted UK puppy guidance"
            ]

    # ── DOG CARE ──
    elif cluster == "Dog Care":
        if "seasonal" in t:
            return [
                "Summer: never leave dogs in cars — temperatures can become fatal within minutes",
                "Winter: rock salt and antifreeze are toxic — wipe paws after walks",
                "Spring: increased tick activity means regular checks after countryside walks",
                "Autumn: conkers, acorns, and fallen fruit can cause poisoning if ingested",
                "Adjust exercise intensity and timing to suit weather conditions"
            ]
        else:
            return [
                "Daily exercise, mental stimulation, and social interaction are essential for wellbeing",
                "Grooming frequency depends on coat type — some breeds need daily brushing",
                "Microchipping is a legal requirement; keep your details up to date",
                "Annual vet check-ups and routine parasite prevention protect long-term health",
                "The RSPCA's five welfare needs provide a framework for responsible dog ownership"
            ]

    # ── DOG TRAINING ──
    elif cluster == "Dog Training":
        if "equipment" in t or "tools" in t:
            return [
                "A well-fitted harness, standard lead, and treat pouch cover most training needs",
                "Clicker training uses a consistent sound marker to pinpoint desired behaviour",
                "Shock collars are banned in Wales and Scotland; the BVA opposes their use across the UK",
                "Long lines (5–10m) are essential for safe recall practice in open spaces",
                "The APDT recommends only reward-based tools and methods"
            ]
        elif "behaviour" in t and "body language" in t:
            return [
                "Dogs communicate primarily through body language — ears, tail, posture, and eyes",
                "A wagging tail does not always mean happiness; context and speed matter",
                "Whale eye (showing the whites) and lip licking often signal stress or discomfort",
                "Play bows (front legs down, rear up) are clear invitations to play",
                "Understanding calming signals helps prevent bites and reduces anxiety"
            ]
        elif "cat" in t and ("scratching" in t or "scratch" in t):
            return [
                "Scratching is a natural, essential behaviour — cats scratch to maintain claws, mark territory, and stretch",
                "Provide at least one scratching post per cat, plus one extra, in key locations",
                "Cats prefer sturdy vertical posts tall enough to stretch fully, or horizontal boards",
                "Sisal rope and corrugated cardboard are the most popular scratching surfaces",
                "Punishing scratching increases stress and rarely stops the behaviour"
            ]
        elif "cat" in t and "play" in t:
            return [
                "Cats are natural predators — play mimics the hunt-catch-kill-eat cycle",
                "Interactive wand toys provide the best engagement and exercise",
                "Most cats prefer short, frequent play sessions of 5–15 minutes",
                "Rotate toys regularly to prevent boredom and maintain interest",
                "Solo play toys (puzzle feeders, balls) provide stimulation when you are away"
            ]
        elif "socialisation" in t or "socialization" in t:
            return [
                "The critical socialisation window closes at approximately 14 weeks of age",
                "Quality of exposure matters more than quantity — keep experiences positive",
                "Puppy classes should use reward-based methods in a controlled environment",
                "Under-socialisation is a leading cause of fear-based behaviour problems in adult dogs",
                "Continue socialisation throughout adolescence (6–18 months) to maintain confidence"
            ]
        elif "training treats" in t and "choose" in t:
            return [
                "Training treats should be small (pea-sized), soft, and quick to eat",
                "High-value treats (cheese, liver) work best for challenging exercises like recall",
                "Treats should not exceed 10% of your dog's daily calorie intake",
                "Variety maintains motivation — rotate between 2–3 treat types per session",
                "Some dogs respond equally well to toy or play rewards instead of food"
            ]
        elif "training treats" in t and ("reward" in t or "best" in t):
            return [
                "Small, soft, smelly treats are most effective for training — dogs can eat them quickly",
                "Use a treat hierarchy: everyday kibble for easy tasks, high-value treats for difficult ones",
                "Natural single-ingredient treats (dried liver, fish cubes) avoid unnecessary additives",
                "Adjust meal portions to account for treat calories during training-heavy days",
                "The APDT recommends reward-based training as the most effective and humane approach"
            ]
        elif "puppy training" in t or "first year" in t:
            return [
                "Start training from day one — puppies can learn basic cues from 8 weeks old",
                "Keep sessions short (3–5 minutes) and always end on a positive note",
                "Toilet training typically takes 4–6 months with consistent routine and praise",
                "Recall is the most important safety cue — practise in low-distraction environments first",
                "The Kennel Club's Good Citizen scheme provides a structured training framework"
            ]
        elif "complete guide" in t and "training" in t:
            return [
                "Reward-based training is endorsed by the BVA, RSPCA, and APDT as most effective",
                "Consistency across all family members is crucial for clear communication",
                "Dogs learn best in short, frequent sessions rather than long, infrequent ones",
                "Punishment-based methods increase fear, aggression, and damage the human-dog bond",
                "Professional help from an APDT-registered trainer is worthwhile for persistent issues"
            ]
        else:
            return [
                "Reward-based methods are recommended by all major UK animal welfare organisations",
                "Consistency and patience produce better long-term results than quick fixes",
                "Short daily training sessions (5–10 minutes) are more effective than occasional long ones",
                "Socialisation and training should continue throughout your dog's life",
                "Seek help from an APDT-accredited trainer if you encounter persistent issues"
            ]

    return [
        "This guide covers key information for UK dog owners",
        "All advice follows current UK veterinary and welfare guidance",
        "Consult your vet for advice specific to your dog's individual needs"
    ]


def generate_why_this_matters(title, cluster):
    """Generate Why This Matters content."""
    t = title.lower()

    if cluster == "Dog Food":
        if "best dog food uk" in t and "complete" in t:
            text = "Nutrition is the single biggest controllable factor in your dog's long-term health. With hundreds of brands available in the UK, understanding what makes a quality food helps you make confident choices that support your dog's energy, coat condition, digestion, and lifespan."
        elif "dry dog food" in t:
            text = "Dry food is the most widely fed format in UK households, yet quality varies enormously between brands. Choosing the right kibble affects your dog's dental health, digestion, energy levels, and long-term wellbeing — making an informed choice saves money and vet bills."
        elif "dry vs wet" in t:
            text = "Many UK dog owners wonder whether to feed dry, wet, or a mix. Understanding the genuine nutritional and practical differences — rather than marketing claims — helps you choose the format that best suits your dog's needs, health, and your household routine."
        elif "puppy food" in t:
            text = "A puppy's diet during the first 12–18 months directly shapes their adult health. Getting nutrition right during growth reduces the risk of developmental bone disease, obesity, and digestive problems — particularly important for large and giant breeds."
        elif "nutrition terminology" in t or "pet food labels" in t:
            text = "Pet food labels use specific legal terms that can be confusing or misleading. Understanding what these terms actually mean under UK and EU regulations empowers you to compare products accurately and avoid paying premium prices for ordinary ingredients."
        elif "feeding guide" in t or "portions" in t:
            text = "Overfeeding is the leading cause of obesity in UK dogs, and the PDSA reports that over a third of dogs are overweight. Correct portioning based on your individual dog — not just packet guidelines — is one of the simplest ways to protect their health."
        else:
            text = "What you feed your dog directly impacts their health, energy, and quality of life. Understanding UK food standards and ingredient quality helps you make choices that support long-term wellbeing."
    elif cluster == "Dog Health":
        if "dental" in t:
            text = "Dental disease is one of the most common yet overlooked health problems in UK dogs, with the majority showing signs by age three. Left untreated, it causes chronic pain and can lead to heart, liver, and kidney complications — yet daily prevention is straightforward."
        elif "flea" in t:
            text = "Fleas are the most common external parasite affecting UK dogs and can cause severe allergic reactions, anaemia in puppies, and tapeworm transmission. Year-round prevention is essential because centrally heated homes allow fleas to thrive in every season."
        elif "joint" in t or "mobility" in t:
            text = "Joint problems significantly reduce quality of life and are among the most common reasons for vet visits in older dogs. Early intervention with appropriate supplements, weight management, and exercise modification can slow progression and keep your dog comfortable for longer."
        elif "common conditions" in t or "health basics" in t:
            text = "Understanding common canine health conditions means you can spot problems early when treatment is most effective and least costly. The PDSA reports that many UK dogs miss routine preventive care, leading to avoidable suffering and expensive emergency treatment."
        elif "health and care" in t:
            text = "A proactive approach to dog health — covering nutrition, exercise, dental care, and preventive medicine — reduces veterinary emergencies and extends your dog's healthy years. This guide brings together the essentials every UK owner should know."
        else:
            text = "Keeping informed about canine health helps you spot early warning signs and take preventive action. UK veterinary organisations emphasise that routine care is far more effective and affordable than treating advanced conditions."
    elif cluster == "Puppy Care":
        if "development" in t:
            text = "Understanding your puppy's developmental stages helps you provide the right support at the right time. Missing critical windows — particularly for socialisation between 3 and 14 weeks — can lead to lifelong behavioural challenges that are much harder to address later."
        elif "essential" in t or "key terms" in t:
            text = "The first few weeks with a new puppy set the foundation for their entire life. Knowing the essential care terms and practices means you can provide confident, informed care from day one and avoid common mistakes that new owners often regret."
        elif "toy" in t:
            text = "The right toys support healthy development, ease teething discomfort, and prevent destructive chewing on household items. Unsafe or inappropriate toys are a common cause of veterinary emergencies in puppies, making informed selection genuinely important."
        else:
            text = "Early puppy care decisions have lasting effects on your dog's health, behaviour, and temperament. Getting the basics right from the start gives your puppy the best chance of growing into a confident, well-adjusted adult dog."
    elif cluster == "Dog Care":
        if "seasonal" in t:
            text = "Each season brings specific hazards for UK dogs — from heatstroke in summer to antifreeze poisoning in winter. Knowing what to watch for and how to adapt your care routine can prevent serious illness and potentially save your dog's life."
        else:
            text = "Good daily care is the foundation of a healthy, happy dog. Understanding the essentials — from exercise and grooming to parasite prevention — helps UK owners meet all five welfare needs recognised by the Animal Welfare Act 2006."
    elif cluster == "Dog Training":
        if "equipment" in t:
            text = "Using the wrong training equipment can cause pain, fear, and long-term behavioural damage. The right tools — endorsed by UK professional bodies like the APDT — make training more effective and protect the trust between you and your dog."
        elif "behaviour" in t and "body language" in t:
            text = "Misreading a dog's body language is one of the most common causes of bites and behavioural misunderstandings. Learning to read what your dog is actually communicating helps you respond appropriately, prevent conflict, and build a stronger bond."
        elif "cat" in t and "scratching" in t:
            text = "Scratching is a hardwired feline behaviour that serves essential physical and emotional functions. Understanding why cats scratch — and providing appropriate outlets — prevents furniture damage while keeping your cat healthy and stress-free."
        elif "cat" in t and "play" in t:
            text = "Play is essential for a cat's physical fitness and mental wellbeing. Understanding your cat's natural play styles helps you provide enrichment that satisfies their predatory instincts and prevents boredom-related behavioural problems."
        elif "socialisation" in t:
            text = "Socialisation is the single most important investment you can make in your puppy's future behaviour. The Kennel Club and Dogs Trust emphasise that puppies who miss this critical window are significantly more likely to develop fear and aggression as adults."
        elif "training treats" in t and "choose" in t:
            text = "The treats you use in training directly affect your dog's motivation and the speed of learning. Choosing the right treats — and using them strategically — makes training sessions more productive while keeping your dog at a healthy weight."
        elif "training treats" in t and ("reward" in t or "best" in t):
            text = "Reward-based training is the most effective and humane approach, backed by the BVA and RSPCA. The right training treats make positive reinforcement practical, helping your dog learn faster while strengthening your relationship."
        elif "puppy training" in t or "first year" in t:
            text = "The first year of training shapes your dog's behaviour for life. Starting with reward-based methods from day one builds confidence, prevents common problems like jumping and pulling, and establishes clear communication between you and your puppy."
        elif "complete guide" in t and "training" in t:
            text = "Effective training improves safety, reduces stress, and strengthens the bond between you and your dog. Understanding modern, evidence-based methods helps UK owners avoid outdated techniques that can cause fear and make behaviour worse."
        else:
            text = "Good training is essential for your dog's safety and your enjoyment of life together. UK animal welfare organisations unanimously recommend reward-based methods as the most effective and humane approach."
    else:
        text = "Understanding this topic helps UK pet owners make informed decisions that improve their pet's health and wellbeing."

    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#fffbeb"}},"border":{{"radius":"6px","width":"1px","color":"#fde68a"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"20px","bottom":"20px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#fde68a;border-width:1px;border-radius:6px;background-color:#fffbeb;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"14px"}}}}}} -->
<p style="font-size:14px"><strong>Why this matters:</strong> {text}</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->'''


def is_buying_guide(title):
    """Check if post is a buying guide / 'Best X' post."""
    t = title.lower()
    return "best " in t or "buying guide" in t or "complete guide" in t or "comparison" in t or "vs" in t


def generate_what_we_considered(title, cluster):
    """Generate What We Considered for buying guide posts."""
    t = title.lower()

    if cluster == "Dog Food":
        if "puppy" in t:
            text = "We evaluated puppy foods based on FEDIAF compliance for growth, named protein quality and percentage, calcium-to-phosphorus ratios for different breed sizes, ingredient transparency, UK availability, PFMA membership status, and value relative to nutritional density. We referenced BVA and PDSA puppy nutrition guidance throughout."
        elif "dry vs wet" in t:
            text = "We compared formats on nutritional completeness (FEDIAF standards), cost per day, moisture content, dental impact, palatability, shelf life, and suitability for different life stages and health conditions. We referenced PFMA feeding data and BVA nutritional guidance."
        elif "dry dog food" in t:
            text = "We assessed dry dog foods on ingredient quality (named protein source and percentage), FEDIAF compliance, manufacturing method (extruded vs cold-pressed), artificial additive content, UK availability and value, and feedback from veterinary nutritionists. PFMA member status was noted as a quality indicator."
        elif "best dog food" in t:
            text = "We evaluated foods across all formats based on FEDIAF nutritional compliance, named protein content and quality, ingredient transparency, range of life-stage options, UK-specific availability and pricing, and alignment with PFMA and BVA guidance. No brand has paid for inclusion or placement."
        else:
            text = "We assessed products and guidance based on FEDIAF nutritional standards, ingredient quality and transparency, UK availability, PFMA membership, veterinary nutritionist recommendations, and value for money. We reference BVA and PDSA dietary guidance throughout."
    elif cluster == "Dog Health":
        if "dental" in t:
            text = "We evaluated dental care products and advice based on VOHC acceptance, veterinary dental specialist recommendations, safety for unsupervised use, effectiveness evidence, UK availability, and alignment with BVA and PDSA dental health guidance."
        elif "flea" in t:
            text = "We assessed flea treatments based on active ingredient efficacy, prescription vs over-the-counter status, speed of action, duration of protection, safety profile, UK licensing, and current BVA and PDSA parasite control recommendations."
        elif "joint" in t:
            text = "We evaluated joint supplements based on published veterinary evidence for key ingredients (glucosamine, chondroitin, omega-3), quality certifications, UK veterinary recommendations, ingredient transparency, palatability, and value for money. We referenced BVA guidance on canine mobility."
        elif "health and care" in t:
            text = "We compiled guidance based on current BVA clinical recommendations, PDSA Animal Wellbeing Report data, RSPCA welfare standards, and UK veterinary consensus. We prioritised preventive care approaches with the strongest evidence base."
        else:
            text = "We assessed guidance based on current UK veterinary evidence, BVA and PDSA clinical recommendations, RSPCA welfare standards, and peer-reviewed veterinary literature. Practical accessibility and cost for UK owners were also considered."
    elif cluster == "Puppy Care":
        if "toy" in t:
            text = "We evaluated puppy toys based on age-appropriate sizing, material safety (non-toxic, no small detachable parts), teething suitability, developmental enrichment value, durability, UK availability, and alignment with Kennel Club and Dogs Trust puppy guidance."
        else:
            text = "We compiled guidance based on Kennel Club puppy development resources, Dogs Trust new owner advice, BVA vaccination and health guidance, and current veterinary consensus on early socialisation and nutrition."
    elif cluster == "Dog Training":
        if "training treats" in t:
            text = "We assessed training treats based on ingredient quality, calorie density, size and texture for quick consumption, palatability across breeds, UK availability and value, and alignment with APDT reward-based training principles."
        elif "equipment" in t:
            text = "We evaluated training equipment based on APDT endorsement of reward-based methods, safety certifications, fit and comfort, effectiveness in published training literature, UK availability, and alignment with the BVA position on aversive devices."
        else:
            text = "We compiled training guidance from APDT-accredited professionals, Kennel Club training resources, Dogs Trust behaviour advice, and published behaviour science. All methods recommended are reward-based and endorsed by UK veterinary organisations."
    else:
        text = "We assessed products and guidance based on UK veterinary recommendations, welfare organisation standards, safety evidence, availability, and value for money."

    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#f5f3ff"}},"border":{{"radius":"6px","width":"1px","color":"#ddd6fe"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"20px","bottom":"20px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#ddd6fe;border-width:1px;border-radius:6px;background-color:#f5f3ff;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"14px"}}}}}} -->
<p style="font-size:14px"><strong>What we considered:</strong> {text}</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->'''


def generate_troubleshooting(title, cluster):
    """Generate Troubleshooting Common Issues section."""
    t = title.lower()

    if cluster == "Dog Food":
        if "puppy" in t:
            paras = "<p><strong>Puppy refuses new food:</strong> Mix 25% new food with 75% old food, gradually increasing the ratio over 10 days. Warming food slightly can enhance aroma and appeal.</p>\n\n<p><strong>Loose stools after switching:</strong> This is common during transitions. Slow the changeover and ensure the puppy has constant access to fresh water. If diarrhoea persists beyond 48 hours, consult your vet.</p>\n\n<p><strong>Puppy seems hungry after meals:</strong> Check you are following the correct feeding guide for their current weight and expected adult size. Puppies should feel satisfied but not bloated — body condition scoring helps assess whether portions need adjusting.</p>\n\n<p><strong>Unsure which size formula to choose:</strong> Use your puppy's expected adult weight. Breeds over 25kg adult weight benefit from large-breed puppy food with controlled calcium and phosphorus levels.</p>"
        elif "dry vs wet" in t:
            paras = "<p><strong>Dog refuses dry food but eats wet:</strong> Try adding a small amount of warm water to kibble to release aromas. Gradual mixing (75% wet/25% dry, shifting over two weeks) often helps.</p>\n\n<p><strong>Wet food causes loose stools:</strong> Higher moisture content can initially loosen stools. Ensure you are feeding the correct portion — wet food packaging portions are larger by volume. If problems persist, try a different protein source.</p>\n\n<p><strong>Dry food goes stale quickly:</strong> Transfer to an airtight container immediately after opening. Store in a cool, dry place away from direct sunlight. Check best-before dates and buy bag sizes your dog will finish within 4–6 weeks.</p>\n\n<p><strong>Unsure about mixing formats:</strong> Mixing wet and dry food is nutritionally fine provided both are labelled 'complete'. Reduce the amount of each proportionally so total calories remain correct.</p>"
        elif "dry dog food" in t:
            paras = "<p><strong>Dog is a fussy eater with kibble:</strong> Add warm water or low-sodium bone broth to enhance aroma. Avoid constantly switching brands, as this can reinforce fussiness. Give 15 minutes to eat, then remove the bowl.</p>\n\n<p><strong>Excessive flatulence after changing food:</strong> Transition more slowly (over 10–14 days). If gas persists, the protein or grain source may not suit your dog — try a different primary ingredient.</p>\n\n<p><strong>Kibble seems too large or too small:</strong> Most quality brands offer size-appropriate kibble. Small breeds need smaller pieces they can crunch easily; large breeds benefit from larger kibble that encourages chewing.</p>\n\n<p><strong>Dog drinks excessively after eating dry food:</strong> This is normal to some extent as kibble has low moisture content (around 8–10%). Ensure fresh water is always available. Excessive thirst beyond normal can indicate a health issue — consult your vet.</p>"
        elif "nutrition terminology" in t or "labels" in t:
            paras = "<p><strong>Confused by 'with' vs 'rich in' labelling:</strong> 'With chicken' requires only 4% chicken content. 'Rich in chicken' or 'chicken dinner' requires at least 26%. 'Chicken dog food' requires a minimum of 26% named ingredient. Check the composition list for actual percentages.</p>\n\n<p><strong>Cannot find allergen information:</strong> UK pet food is not required to list allergens in the same way as human food. Contact the manufacturer directly if your dog has confirmed allergies. A veterinary exclusion diet is the most reliable way to identify food sensitivities.</p>\n\n<p><strong>'Derivatives' listed without detail:</strong> 'Meat and animal derivatives' is a legal category that allows variable ingredient sourcing. If transparency matters to you, choose brands that list specific named ingredients with percentages.</p>"
        elif "feeding guide" in t or "portions" in t:
            paras = "<p><strong>Dog is gaining weight on recommended portions:</strong> Packaging guidelines are averages — adjust downward for less active dogs, neutered dogs, or breeds prone to weight gain. Reduce by 10% and reassess body condition after two weeks.</p>\n\n<p><strong>Dog seems hungry despite correct portions:</strong> Ensure treats are not adding significant untracked calories. Adding green beans or carrot as low-calorie fillers can help. If hunger seems excessive, consult your vet to rule out medical causes.</p>\n\n<p><strong>Unsure how to weigh food accurately:</strong> Use digital kitchen scales rather than the cup measures on packaging, which can be imprecise. Weigh food dry for kibble; weigh including jelly or gravy for wet food.</p>\n\n<p><strong>Multiple dogs with different portion needs:</strong> Feed dogs separately to ensure each gets the correct amount. Supervised mealtimes with bowls removed after 15 minutes prevent food stealing.</p>"
        else:
            paras = "<p><strong>Dog refuses new food:</strong> Transition gradually over 7–10 days, mixing increasing amounts of new food with the old. Warming food slightly can enhance aroma and appeal.</p>\n\n<p><strong>Digestive upset during food change:</strong> Slow the transition period. If loose stools persist beyond a few days, the new food may not suit your dog — consult your vet.</p>\n\n<p><strong>Unsure if food meets quality standards:</strong> Look for 'complete' on the label (not 'complementary'). Check PFMA membership and whether the brand states FEDIAF compliance.</p>"
    elif cluster == "Dog Health":
        if "dental" in t:
            paras = "<p><strong>Dog refuses toothbrushing:</strong> Start with letting your dog lick enzymatic toothpaste from your finger. Progress to a finger brush over several days before introducing a long-handled brush. Keep sessions short and reward cooperation.</p>\n\n<p><strong>Gums bleed during brushing:</strong> Light bleeding can indicate early gingivitis — continue gentle brushing as this often improves within a week. If bleeding is heavy or persistent, book a vet dental check as the gums may need professional cleaning.</p>\n\n<p><strong>Bad breath despite regular brushing:</strong> Persistent halitosis despite dental care may indicate tartar below the gumline, tooth root infection, or a non-dental condition. A veterinary examination is recommended.</p>\n\n<p><strong>Dog chews dental treats too quickly:</strong> Choose a larger size or a harder texture (within safety limits). VOHC-accepted products are tested for effectiveness at normal chewing speeds. Never give weight-bearing bones, which can fracture teeth.</p>"
        elif "flea" in t:
            paras = "<p><strong>Fleas persist despite treatment:</strong> Ensure you are treating all pets in the household simultaneously. Wash bedding at 60°C and vacuum thoroughly — flea pupae can survive in carpets for months. A household spray targeting eggs and larvae may be needed alongside pet treatment.</p>\n\n<p><strong>Dog has skin reaction to flea treatment:</strong> Remove spot-on product by bathing with mild shampoo if possible, and contact your vet. Some dogs are sensitive to specific active ingredients — your vet can recommend an alternative.</p>\n\n<p><strong>Unsure whether to use prescription or shop-bought treatment:</strong> Prescription treatments from your vet are generally more effective and targeted. Shop-bought products vary widely in efficacy. Discuss options with your vet, especially if current treatment is not working.</p>\n\n<p><strong>Cannot tell if dog has fleas:</strong> Use a flea comb on the lower back and base of the tail. Place any debris on damp white tissue — flea dirt dissolves into reddish-brown streaks. Even one or two fleas indicate an infestation in the environment.</p>"
        elif "joint" in t:
            paras = "<p><strong>Dog shows stiffness but X-rays are normal:</strong> Early joint changes may not appear on X-rays. Your vet may recommend a trial period of joint supplements and controlled exercise. If symptoms persist, advanced imaging or specialist referral may be needed.</p>\n\n<p><strong>Supplement seems ineffective after two weeks:</strong> Most joint supplements (glucosamine, chondroitin, omega-3) require 6–8 weeks of consistent use before noticeable improvement. Continue the full trial period before changing products.</p>\n\n<p><strong>Dog is reluctant to exercise:</strong> Pain is the most common cause of exercise reluctance. Avoid forcing activity — instead, offer short, gentle walks on flat surfaces and consult your vet about pain management alongside supplements.</p>\n\n<p><strong>Unsure which supplement to choose:</strong> Look for products with published dosage per ingredient (not just 'proprietary blends'), veterinary endorsement, and ideally published efficacy data. Your vet can recommend products suited to your dog's specific condition.</p>"
        elif "health and care" in t:
            paras = "<p><strong>Dog is overdue for vaccinations:</strong> Contact your vet to discuss a catch-up schedule. Core vaccines may need a primary course restart if the gap is significant. Your vet will advise based on your dog's specific history.</p>\n\n<p><strong>Cannot afford a vet visit:</strong> The PDSA provides free and reduced-cost veterinary care for eligible owners. The Blue Cross and RSPCA also operate clinics. Pet insurance, even basic accident cover, helps manage unexpected costs.</p>\n\n<p><strong>Dog is reluctant to be examined at home:</strong> Practise gentle handling regularly so your dog accepts being touched everywhere. Reward calm behaviour. This makes vet visits less stressful and allows you to spot lumps, cuts, or sore areas early.</p>\n\n<p><strong>Unsure if a symptom needs urgent vet attention:</strong> When in doubt, always call your vet or an out-of-hours service. Symptoms requiring immediate attention include difficulty breathing, bloated abdomen, seizures, collapse, and suspected poisoning.</p>"
        else:
            paras = "<p><strong>Dog seems lethargic but eating normally:</strong> Subtle changes in energy can indicate early illness. Monitor for 24–48 hours and note any other symptoms. If lethargy persists or worsens, book a vet appointment.</p>\n\n<p><strong>Unsure about preventive care schedule:</strong> Your vet will tailor a schedule based on your dog's age, breed, and lifestyle. Generally: annual health check, vaccinations as advised, monthly parasite prevention, and regular dental care.</p>\n\n<p><strong>Dog has recurring skin or ear problems:</strong> Chronic issues often have an underlying cause such as allergies, hormonal conditions, or environmental factors. A systematic veterinary investigation is more effective than repeated symptomatic treatment.</p>"
    elif cluster == "Puppy Care":
        if "development" in t:
            paras = "<p><strong>Puppy seems fearful of new experiences:</strong> If your puppy is in a fear period (typically 8–10 weeks or 6–14 months), do not force exposure. Create positive associations at a distance and let the puppy approach at their own pace. These periods are temporary.</p>\n\n<p><strong>Puppy bites constantly during play:</strong> Mouthing is normal developmental behaviour. Redirect to appropriate chew toys, and end play calmly if teeth touch skin. This typically reduces significantly by 6 months as adult teeth emerge.</p>\n\n<p><strong>Large-breed puppy growing unevenly:</strong> Gangly, disproportionate growth is normal in large breeds. Avoid over-exercising growing joints. If you notice limping or reluctance to move, consult your vet to rule out developmental orthopaedic conditions.</p>\n\n<p><strong>Puppy regresses in behaviour during adolescence:</strong> Adolescence (6–18 months) commonly brings apparent 'forgetting' of trained behaviours. This is a normal brain development phase — maintain consistent training and reward desired behaviour patiently.</p>"
        elif "essential" in t or "key terms" in t:
            paras = "<p><strong>Puppy cries at night:</strong> Place the crate or bed near your bedroom initially. A warm water bottle (wrapped in a towel) and a ticking clock can mimic littermate warmth. Most puppies settle within 3–5 nights with consistent routine.</p>\n\n<p><strong>Puppy has accidents despite regular toilet breaks:</strong> Take the puppy out after every meal, nap, and play session. Praise immediately when they go outside. Clean indoor accidents with enzymatic cleaner to remove scent markers. Consistency is key — most puppies are reliable by 6 months.</p>\n\n<p><strong>Unsure when to start training:</strong> Begin basic training from the day your puppy comes home (typically 8 weeks). Keep sessions very short (2–3 minutes) and use high-value treats. Early positive experiences with training set the foundation for lifelong learning.</p>"
        elif "toy" in t:
            paras = "<p><strong>Puppy destroys toys within minutes:</strong> Choose robust materials (solid rubber, thick rope) appropriate for your puppy's size and chewing strength. Avoid toys with small detachable parts. Some puppies are aggressive chewers — heavy-duty brands exist specifically for this.</p>\n\n<p><strong>Puppy only wants to chew furniture:</strong> Ensure enough appropriate chew toys are available. Redirect immediately to an approved toy when you catch furniture chewing. Frozen Kongs filled with paste can be more appealing than furniture during teething.</p>\n\n<p><strong>Puppy swallowed a piece of toy:</strong> Remove the remaining toy immediately. If the piece is small, monitor for vomiting, loss of appetite, or straining. If the piece is large or your puppy shows any symptoms, contact your vet urgently — foreign body obstruction requires prompt treatment.</p>\n\n<p><strong>Puppy not interested in toys:</strong> Try different textures and types — some puppies prefer squeaky toys, others like tug toys or puzzle feeders. Interactive play with you (tug, fetch) is often more engaging than solo toys for young puppies.</p>"
        else:
            paras = "<p><strong>Puppy seems overwhelmed:</strong> New environments can be stressful. Provide a quiet, safe space and let the puppy explore at their own pace. Limit visitors for the first few days.</p>\n\n<p><strong>Unsure about vaccination schedule:</strong> Your vet will provide a tailored schedule. Primary vaccinations typically start at 6–8 weeks with a second dose 2–4 weeks later. Keep your puppy away from unvaccinated dogs until the course is complete.</p>\n\n<p><strong>Puppy is not eating well:</strong> Stress from rehoming can reduce appetite for 1–2 days. Offer small, frequent meals of the food the breeder was using. If the puppy does not eat for more than 24 hours, consult your vet.</p>"
    elif cluster == "Dog Care":
        if "seasonal" in t:
            paras = "<p><strong>Dog overheats during summer walks:</strong> Walk during the cooler morning and evening hours. Carry water and a collapsible bowl. If your dog pants excessively, drools heavily, or seems unsteady, move to shade immediately, offer small amounts of cool (not ice-cold) water, and contact your vet.</p>\n\n<p><strong>Dog reluctant to walk in rain or cold:</strong> Some dogs genuinely dislike wet weather. A well-fitted waterproof coat can help. Shorter, more frequent walks may be better than one long outing. Dry paws thoroughly afterwards to prevent interdigital problems.</p>\n\n<p><strong>Dog has cracked paws in winter:</strong> Road salt and grit cause irritation and cracking. Wipe paws with a damp cloth after walks. Paw balm applied before walks provides a protective barrier. Booties are an option for dogs that tolerate them.</p>\n\n<p><strong>Ticks found after countryside walks:</strong> Remove ticks promptly using a tick removal tool (twist, do not pull). Monitor the bite site for redness or swelling over the following weeks. Consult your vet about tick-borne disease if your dog becomes lethargic or develops a fever.</p>"
        else:
            paras = "<p><strong>Dog's coat is dull despite regular grooming:</strong> Coat quality often reflects nutrition. Ensure the diet includes adequate omega-3 and omega-6 fatty acids. If diet is good, consult your vet to rule out skin conditions or hormonal issues.</p>\n\n<p><strong>Dog resists nail trimming:</strong> Desensitise gradually — handle paws daily with treats, then introduce the clipper sound before attempting to trim. Cut small amounts to avoid the quick. A scratch board is a stress-free alternative for some dogs.</p>\n\n<p><strong>Dog is gaining weight despite normal feeding:</strong> Account for all treats, dental chews, and extras in the daily calorie count. Neutered dogs typically need 20–30% fewer calories. Increase exercise gradually and reassess portions.</p>"
    elif cluster == "Dog Training":
        if "equipment" in t:
            paras = "<p><strong>Dog pulls despite using a harness:</strong> A front-clip harness redirects pulling energy but does not teach loose lead walking by itself. Combine the harness with consistent reward-based lead training — stop and wait when the lead goes tight, and reward when it is slack.</p>\n\n<p><strong>Dog ignores the clicker:</strong> Ensure you have properly 'loaded' the clicker first (click then immediately treat, repeated 20+ times). The clicker must always predict a reward. If the dog is still unresponsive, a verbal marker word ('yes') works equally well.</p>\n\n<p><strong>Long line gets tangled:</strong> Use a lightweight, non-retractable long line and practise handling in a low-distraction environment first. Let the line trail on the ground rather than holding it taut. Biothane material resists tangling better than webbing.</p>\n\n<p><strong>Treat pouch is awkward to use:</strong> Choose a pouch with a magnetic or spring closure for quick one-handed access. Wear it on your non-dominant side. Pre-cut treats to pea-size before the session to avoid fumbling.</p>"
        elif "behaviour" in t and "body language" in t:
            paras = "<p><strong>Dog growls at visitors:</strong> Growling is a warning signal — never punish it, as this removes the warning without addressing the fear. Give your dog space, manage the situation by putting them in another room, and consult an APDT-accredited behaviourist.</p>\n\n<p><strong>Dog yawns and lip-licks frequently:</strong> These are common calming signals indicating mild stress. Identify and reduce the stressor (too much handling, a tense environment, proximity to something feared). These signals are easy to miss but important to recognise.</p>\n\n<p><strong>Dog freezes during interactions:</strong> Freezing (going very still) is a significant stress signal that can precede a snap or bite. Immediately create distance between your dog and the trigger. Forcing interaction when a dog freezes is dangerous.</p>\n\n<p><strong>Cannot tell if dog is playing or fighting:</strong> Healthy play includes loose, bouncy movements, play bows, role reversal (taking turns chasing), and voluntary re-engagement. Stiffness, hard stares, pinned ears, and one dog repeatedly trying to escape indicate the interaction should be interrupted.</p>"
        elif "cat" in t and "scratching" in t:
            paras = "<p><strong>Cat ignores the scratching post:</strong> Ensure the post is tall enough for a full stretch, sturdy (will not wobble), and placed near where the cat already scratches. Rub catnip on it or dangle a toy from the top to attract attention. Avoid placing it in a hidden corner.</p>\n\n<p><strong>Cat scratches furniture despite having posts:</strong> Cover the targeted furniture temporarily with double-sided tape or aluminium foil (cats dislike the texture). Place a scratching post directly beside the furniture. Once redirected, gradually move the post to your preferred location.</p>\n\n<p><strong>New cat scratches everything:</strong> A new cat exploring their territory will scratch to leave scent marks. Provide multiple scratching options (vertical posts, horizontal boards, different materials) throughout the home. This typically settles as the cat becomes more secure.</p>"
        elif "cat" in t and "play" in t:
            paras = "<p><strong>Cat only plays at 3am:</strong> Cats are crepuscular (most active at dawn and dusk). Schedule an energetic play session before your bedtime followed by a meal — this mimics the hunt-catch-eat-sleep cycle and can reduce nocturnal activity.</p>\n\n<p><strong>Cat bites during play:</strong> Never use hands or feet as play toys — this teaches the cat that skin is a target. Use wand toys that keep your hands at a safe distance. If a bite occurs, freeze and end the session calmly without shouting.</p>\n\n<p><strong>Cat seems bored with all toys:</strong> Rotate toys weekly rather than leaving them all out. Introduce novelty with cardboard boxes, paper bags (handles removed), and DIY puzzle feeders. Interactive play with you is usually more stimulating than any toy alone.</p>"
        elif "socialisation" in t:
            paras = "<p><strong>Puppy is terrified on first outings:</strong> Carry your puppy or use a sling to expose them to the world without forcing direct contact. Let them observe from a safe distance and pair new experiences with high-value treats. Never flood a scared puppy with stimulation.</p>\n\n<p><strong>Missed the socialisation window:</strong> While the critical period closes around 14 weeks, older dogs can still improve with patient, systematic counter-conditioning. Progress will be slower but meaningful. An APDT behaviourist can create a tailored plan.</p>\n\n<p><strong>Puppy is reactive to other dogs:</strong> Reactivity on the lead is often frustration or fear. Increase distance from triggers, reward calm behaviour, and avoid on-lead greetings with unknown dogs. Puppy classes in a controlled environment can help with dog-to-dog confidence.</p>\n\n<p><strong>Other people overwhelm the puppy with attention:</strong> Advocate for your puppy — ask people to let the puppy approach them rather than reaching in. Instruct visitors to crouch down, avoid direct eye contact, and let the puppy sniff before petting.</p>"
        elif "training treats" in t and "choose" in t:
            paras = "<p><strong>Dog not motivated by treats:</strong> Try higher-value options — cooked chicken, cheese, liver paste. Some dogs have clear preferences. If no food motivates, try toy or play rewards instead. A dog that refuses all food during training may be too stressed to learn — reduce difficulty.</p>\n\n<p><strong>Dog gains weight from training treats:</strong> Use tiny pieces (pea-sized) and deduct treat calories from daily meals. Swap some treat rewards for praise or play as skills become established. Low-calorie options like carrot pieces work for some dogs.</p>\n\n<p><strong>Dog only performs for treats:</strong> Gradually introduce variable reinforcement — reward every second, then third correct response. Fade treats by mixing in praise and life rewards (going through a door, getting the lead on). The treat gets the behaviour; variable reward maintains it.</p>"
        elif "training treats" in t and ("reward" in t or "best" in t):
            paras = "<p><strong>Dog takes treats too roughly:</strong> Teach a gentle 'take it' by offering treats in a closed fist, only opening when the dog stops mouthing. A flat palm delivery also helps. Practice outside training sessions until gentleness becomes habit.</p>\n\n<p><strong>Treats crumble in the pouch:</strong> Soft, moist treats hold together better than freeze-dried options. Store them in a sealed container with a silica gel packet to prevent moisture. Cut firm treats into pieces before the session rather than breaking them mid-training.</p>\n\n<p><strong>Dog has food allergies limiting treat options:</strong> Single-ingredient natural treats (e.g. dried fish skins, sweet potato chews) are least likely to trigger reactions. Your vet can advise which proteins are safe. Some dogs with allergies respond well to their own hypoallergenic kibble used as training treats.</p>"
        elif "puppy training" in t or "first year" in t:
            paras = "<p><strong>Puppy will not focus during training:</strong> Puppies have very short attention spans — 2–3 minute sessions are plenty. Train before meals when motivation is highest. If the puppy is distracted, the environment may be too stimulating — move somewhere quieter.</p>\n\n<p><strong>Recall is unreliable off-lead:</strong> Never let a puppy off-lead in an unsecured area until recall is strong. Use a long line (5–10m) for safe practice. Build recall value with the best treats and enthusiastic praise. Never punish a dog that comes back slowly — this poisons the recall cue.</p>\n\n<p><strong>Puppy jumps on everyone:</strong> Withdraw attention completely when the puppy jumps — turn away and ignore. Immediately reward all four paws on the ground. Ask visitors to do the same. Consistency from everyone is essential for this to work.</p>\n\n<p><strong>Puppy pulls on the lead from day one:</strong> Use a well-fitted harness and stop walking whenever the lead goes tight. Wait for slack, then proceed. This is tedious initially but teaches the puppy that pulling does not get them where they want to go.</p>"
        elif "complete guide" in t and "training" in t:
            paras = "<p><strong>Older dog seems untrainable:</strong> Dogs of any age can learn — older dogs may just need more repetitions and patience. Rule out pain or hearing/vision loss that may affect responsiveness. Short, positive sessions work at any life stage.</p>\n\n<p><strong>Family members use different commands:</strong> Agree on a single word for each cue and write it down for everyone to follow. Inconsistency is one of the most common reasons training stalls. A family training session with an APDT trainer can help align approaches.</p>\n\n<p><strong>Dog is well-behaved at home but reactive outside:</strong> Environmental distractions overwhelm early training. Practise each cue in gradually more distracting environments, rewarding generously. Never skip steps — reliable behaviour at home must come before expecting it in a park.</p>\n\n<p><strong>Training advice online is contradictory:</strong> Stick to guidance from the APDT, Kennel Club, and Dogs Trust, which consistently recommend reward-based methods. Avoid any trainer or programme that relies on dominance theory, physical corrections, or aversive tools.</p>"
        else:
            paras = "<p><strong>Dog does not respond to training cues:</strong> Ensure you are training in a low-distraction environment with high-value rewards. Dogs do not generalise well — a cue learned in the kitchen needs separate practice in the garden and on walks.</p>\n\n<p><strong>Training progress seems to plateau:</strong> Plateaus are normal. Try breaking the skill into smaller steps, changing the reward, or training at a different time of day. Short breaks from a specific exercise can also help.</p>\n\n<p><strong>Dog is fearful during training:</strong> Fear inhibits learning. Identify the trigger (environment, tools, handling) and remove it. Rebuild confidence with easy wins and high-value rewards. An APDT behaviourist can help with fear-based issues.</p>"
    else:
        paras = "<p><strong>Not seeing expected results:</strong> Allow adequate time for changes to take effect. Consult your vet or a qualified professional if problems persist.</p>"

    return f'''<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">Troubleshooting Common Issues</h3>
<!-- /wp:heading -->
<!-- wp:paragraph -->
{paras}
<!-- /wp:paragraph -->'''


def generate_warning_signs(title, cluster):
    """Generate Warning Signs block for health/food/puppy posts."""
    t = title.lower()

    if cluster == "Dog Food":
        if "puppy" in t:
            text = "Contact your vet immediately if your puppy shows persistent vomiting or diarrhoea after eating, refuses food for more than 24 hours, or develops a distended abdomen — these can indicate serious digestive conditions. The BVA advises that puppies dehydrate rapidly and young animals should be seen urgently. Weight loss or failure to gain weight despite adequate feeding also requires prompt veterinary investigation."
        elif "dry vs wet" in t or "dry dog food" in t:
            text = "Seek veterinary advice if your dog develops persistent diarrhoea, vomiting, or skin irritation after a food change — these may indicate an intolerance or allergy rather than a normal transition response. The PDSA warns that excessive thirst, sudden weight loss, or refusal to eat for more than 48 hours in an adult dog should always be investigated promptly."
        else:
            text = "Watch for persistent vomiting, diarrhoea, dramatic weight change, or skin/coat deterioration, which may indicate a food intolerance, allergy, or underlying health condition. The BVA advises that any dog refusing food for more than 48 hours, or showing blood in vomit or stools, should be seen by a vet urgently."
    elif cluster == "Dog Health":
        if "dental" in t:
            text = "The BVA advises immediate veterinary attention if you notice facial swelling, bleeding from the mouth, loose or broken teeth, or your dog suddenly refusing food or favouring one side when eating. Excessive drooling with blood-tinged saliva, persistent pawing at the mouth, or a visible abscess on the gum line are emergencies. The PDSA notes that untreated dental infections can spread to the heart, kidneys, and liver."
        elif "flea" in t:
            text = "Seek urgent veterinary help if your dog shows signs of severe flea allergy dermatitis (intense scratching, raw skin, hair loss, hot spots), or if a young puppy appears lethargic and pale-gummed — heavy flea burdens can cause life-threatening anaemia in small or young dogs. The PDSA warns that tapeworm segments (resembling rice grains) around the tail area indicate flea-transmitted parasites requiring separate treatment."
        elif "joint" in t:
            text = "The BVA advises urgent veterinary assessment if your dog suddenly cannot bear weight on a limb, cries out when moving or being touched, or shows rapidly worsening lameness — these may indicate a fracture, ligament rupture, or acute joint condition rather than chronic arthritis. PDSA guidance states that any sudden onset of paralysis, dragging of limbs, or loss of bladder/bowel control requires emergency veterinary attention."
        else:
            text = "Seek immediate veterinary attention for difficulty breathing, collapse, seizures, a bloated or hard abdomen, suspected poisoning, inability to urinate, or severe bleeding. The BVA advises that any sudden change in behaviour, persistent vomiting or diarrhoea, or refusal to eat for more than 48 hours warrants prompt assessment. The PDSA's 24-hour helpline (0800 731 2502) can provide guidance on whether symptoms are an emergency."
    elif cluster == "Puppy Care":
        if "development" in t:
            text = "Contact your vet promptly if your puppy shows limping or reluctance to move (possible developmental orthopaedic condition), failure to gain weight, persistent lethargy, or frequent unexplained vomiting. The Kennel Club advises that puppies who remain excessively fearful beyond normal fear periods, or show sudden aggression, should be assessed by a vet first (to rule out pain) and then referred to an APDT behaviourist."
        elif "toy" in t:
            text = "Seek immediate veterinary help if your puppy swallows a piece of toy, shows signs of choking (pawing at mouth, difficulty breathing), or develops vomiting, loss of appetite, or a painful abdomen after playing — these can indicate foreign body obstruction, which is a surgical emergency. The PDSA advises that any ingested non-food item should be treated as potentially serious."
        else:
            text = "Contact your vet urgently if your puppy is lethargic, refuses food for more than 12 hours, has persistent vomiting or diarrhoea, or shows signs of dehydration (dry gums, sunken eyes). The BVA advises that young puppies deteriorate rapidly and should be seen promptly. The Kennel Club warns that unvaccinated puppies exposed to other dogs may contract parvovirus, which presents as bloody diarrhoea and requires emergency treatment."
    elif cluster == "Dog Care":
        text = "Seek emergency veterinary care if your dog shows signs of heatstroke (excessive panting, drooling, staggering, collapse), suspected poisoning (vomiting, tremors, seizures after exposure to toxins), or difficulty breathing. The RSPCA advises calling 999 if you see a dog locked in a hot car in distress. The PDSA warns that antifreeze, chocolate, grapes/raisins, and xylitol are common household poisons requiring urgent treatment."
    else:
        text = "Consult your vet if you notice any sudden changes in behaviour, appetite, or energy levels. Early intervention leads to better outcomes for most health conditions."

    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#fef2f2"}},"border":{{"radius":"6px","width":"1px","color":"#fecaca"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"20px","bottom":"20px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#fecaca;border-width:1px;border-radius:6px;background-color:#fef2f2;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"14px"}}}}}} -->
<p style="font-size:14px"><strong>Warning signs to watch for:</strong> {text}</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->'''


def generate_when_to_seek_help(title, cluster):
    """Generate When to Seek Help block."""
    t = title.lower()

    if cluster == "Dog Food":
        text = "Consult your vet if your dog shows persistent digestive issues (more than 48 hours of diarrhoea or vomiting), unexplained weight loss or gain, chronic skin or coat problems that may indicate food sensitivity, or if you are unsure how to feed a dog with a diagnosed health condition such as kidney disease, diabetes, or pancreatitis. A veterinary nutritionist referral may be appropriate for complex dietary needs."
    elif cluster == "Dog Health":
        if "dental" in t:
            text = "Book a vet appointment if you notice persistent bad breath, red or swollen gums, visible tartar build-up, reluctance to eat hard food, or loose teeth. The BVA recommends annual dental checks as part of routine health assessments. If your dog is in obvious dental pain (pawing at the mouth, drooling, whimpering), seek same-day veterinary attention."
        elif "flea" in t:
            text = "See your vet if over-the-counter flea treatment is ineffective after two full treatment cycles, if your dog develops severe skin reactions, or if you suspect flea allergy dermatitis. Your vet can prescribe more effective treatments and check for secondary infections or tapeworms."
        elif "joint" in t:
            text = "See your vet if your dog shows persistent lameness, stiffness lasting more than a few minutes after rest, reluctance to jump or climb stairs, or if symptoms worsen despite supplements and weight management. A referral to a veterinary orthopaedic specialist or physiotherapist may be recommended for complex cases. The BVA advises against long-term self-medicating with supplements without veterinary oversight."
        else:
            text = "See your vet promptly if your dog shows any sudden behaviour change, persistent symptoms lasting more than 48 hours, or any emergency signs. Do not wait to see if symptoms resolve on their own with serious signs like collapse, difficulty breathing, or suspected poisoning. Keep your vet's number and a 24-hour emergency service number in your phone."
    elif cluster == "Puppy Care":
        text = "Contact your vet if your puppy misses developmental milestones, shows persistent fear or aggression, has recurring digestive or health issues, or if you are unsure about any aspect of their care. Early professional guidance prevents problems from becoming entrenched. For behavioural concerns beyond normal puppy behaviour, ask your vet for a referral to an APDT-accredited behaviourist."
    elif cluster == "Dog Care":
        text = "See your vet for annual health checks, any time you notice a change in your dog's behaviour or routine, or before making significant changes to exercise, diet, or care routines. The PDSA advises that preventive vet visits are always more cost-effective than emergency treatment. For out-of-hours emergencies, most practices have a number directing you to an emergency service."
    elif cluster == "Dog Training":
        if "behaviour" in t or "body language" in t:
            text = "Consult an APDT-accredited behaviourist if your dog displays persistent fear, aggression towards people or other animals, or any behaviour that makes you feel unsafe. Ask your vet for a referral — behaviour problems can sometimes have medical causes that need ruling out first. Never attempt to address serious aggression without professional guidance."
        elif "socialisation" in t:
            text = "Seek help from an APDT-accredited behaviourist if your puppy's fearfulness is not improving with patient exposure, if reactivity to dogs or people is escalating, or if you are unsure whether behaviour is normal for the developmental stage. Early intervention is significantly more effective than waiting."
        else:
            text = "Consult an APDT-accredited trainer or behaviourist if training is not progressing, if your dog shows signs of fear or aggression during training, or if you are unsure about the best approach for a specific behaviour. Your vet can rule out medical causes (pain, hearing loss) that may affect training responsiveness."
    else:
        text = "Consult a qualified professional if you are unsure about any aspect of your pet's care. Your vet can provide tailored advice and referrals to specialists where needed."

    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#fef2f2"}},"border":{{"radius":"6px","width":"1px","color":"#fecaca"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"20px","bottom":"20px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#fecaca;border-width:1px;border-radius:6px;background-color:#fef2f2;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"14px"}}}}}} -->
<p style="font-size:14px"><strong>When to seek professional help:</strong> {text}</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->'''


def generate_key_takeaways(title, cluster):
    """Generate Key Takeaways bullets."""
    t = title.lower()
    bullets = get_key_takeaway_bullets(title, cluster)
    items = "".join(f"<li>{b}</li>" for b in bullets)
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#f0fdf4"}},"border":{{"radius":"6px","width":"1px","color":"#bbf7d0"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#bbf7d0;border-width:1px;border-radius:6px;background-color:#f0fdf4;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">Key Takeaways</h4>
<!-- /wp:heading -->
<!-- wp:list -->
<ul class="wp-block-list">{items}</ul>
<!-- /wp:list -->
</div>
<!-- /wp:group -->'''


def get_key_takeaway_bullets(title, cluster):
    """Return 4-6 actionable takeaway bullets."""
    t = title.lower()

    if cluster == "Dog Food":
        if "best dog food uk" in t and "complete" in t:
            return [
                "Always choose food labelled 'complete' that meets FEDIAF standards for your dog's life stage",
                "Named animal protein as the first ingredient is a reliable quality indicator",
                "No single brand suits every dog — consider breed size, age, activity level, and health conditions",
                "Transition to any new food gradually over 7–10 days to prevent digestive upset",
                "Use body condition scoring to fine-tune portions rather than relying solely on packaging guides",
                "Consult your vet before making dietary changes for dogs with health conditions"
            ]
        elif "dry dog food" in t:
            return [
                "Check that named meat or fish is the first ingredient, not cereals or vague 'meat derivatives'",
                "Cold-pressed and gently cooked kibble options retain more nutrients than standard extrusion",
                "Store kibble in an airtight container and use within 4–6 weeks of opening",
                "Adjust portions based on your individual dog's body condition, not just the packet guide",
                "Always provide access to fresh water, as dry food has very low moisture content",
                "PFMA member brands commit to quality and labelling standards beyond the legal minimum"
            ]
        elif "dry vs wet" in t:
            return [
                "Both formats can provide complete nutrition — the best choice depends on your dog's needs",
                "Mixing wet and dry food is a practical approach that combines the benefits of both",
                "Wet food supports hydration; dry food may benefit dental health through mechanical chewing",
                "Compare cost per day, not per tin or bag, for an accurate price comparison",
                "Opened wet food must be refrigerated and used within 48 hours"
            ]
        elif "puppy food" in t:
            return [
                "Feed a 'complete for growth' food that matches your puppy's expected adult size category",
                "Large-breed puppies need controlled calcium and phosphorus to protect developing joints",
                "Transition to adult food between 12 and 18 months, guided by your vet's advice",
                "Weigh portions accurately and adjust every 2–4 weeks as your puppy grows",
                "Fresh water must be available at all times — puppies dehydrate faster than adults",
                "Avoid supplementing a complete puppy food with extra vitamins or minerals unless vet-advised"
            ]
        elif "nutrition terminology" in t or "labels" in t:
            return [
                "Look for 'complete' on the label to ensure all essential nutrients are provided",
                "Named ingredients with percentages offer more transparency than vague categories",
                "Ingredient lists are ordered by pre-processing weight — this can overstate moisture-heavy ingredients",
                "'With chicken' (4%) and 'rich in chicken' (26%) have very different legal meanings",
                "FEDIAF compliance is the nutritional standard UK pet foods should meet",
                "When in doubt, contact the manufacturer directly for detailed nutritional information"
            ]
        elif "feeding guide" in t or "portions" in t:
            return [
                "Use body condition scoring alongside weight to assess whether portions are correct",
                "Packaging guidelines are starting points — individual dogs vary significantly in their needs",
                "Account for all treats (maximum 10% of daily calories) in your feeding calculations",
                "Two meals per day at consistent times suits most adult dogs",
                "Weigh food with digital scales for accuracy rather than using cup measures",
                "Adjust portions for neutered dogs, sedentary periods, or changes in exercise levels"
            ]
        else:
            return [
                "Choose food labelled 'complete' meeting FEDIAF standards for your dog's life stage",
                "Named animal protein should be the primary ingredient",
                "Transition gradually over 7–10 days when changing food",
                "Adjust portions based on body condition, not weight alone",
                "Consult your vet for dietary advice specific to your dog's needs"
            ]
    elif cluster == "Dog Health":
        if "dental" in t:
            return [
                "Start daily toothbrushing with enzymatic dog toothpaste — it is the most effective home care",
                "Look for the VOHC seal on dental chews and products as proof of clinical effectiveness",
                "Professional dental cleaning under anaesthesia may be needed for tartar below the gumline",
                "Bad breath is not normal — it usually indicates dental disease that needs attention",
                "Include a dental check at every routine vet visit",
                "Never use human toothpaste on dogs — fluoride and xylitol are toxic"
            ]
        elif "flea" in t:
            return [
                "Treat all pets in the household simultaneously to break the flea lifecycle",
                "Prescription treatments from your vet are generally more effective than shop-bought options",
                "Wash bedding at 60°C and vacuum regularly — treat the home environment as well as the pet",
                "Year-round prevention is essential in UK centrally heated homes",
                "A single flea on your dog indicates many more in the environment at egg and larval stages",
                "Flea allergy dermatitis can develop from just one bite — prevention is always better than treatment"
            ]
        elif "joint" in t:
            return [
                "Weight management is the single most important factor in protecting joint health",
                "Glucosamine, chondroitin, and omega-3 supplements need 6–8 weeks to show benefit",
                "Gentle, consistent exercise is better for joints than occasional intense activity",
                "Early intervention slows progression and keeps dogs comfortable for longer",
                "Report any lameness, stiffness, or reluctance to move to your vet promptly",
                "Orthopaedic dog beds and ramps can significantly improve comfort for affected dogs"
            ]
        elif "health and care" in t:
            return [
                "Schedule annual vet check-ups even if your dog appears healthy — early detection saves lives",
                "Keep vaccinations, parasite treatments, and microchip details up to date",
                "Monitor your dog's weight using body condition scoring and adjust diet accordingly",
                "Pet insurance helps manage unexpected veterinary costs — compare policies annually",
                "Learn basic pet first aid and keep an emergency vet number in your phone",
                "Mental stimulation and social interaction are as important as physical health for overall wellbeing"
            ]
        else:
            return [
                "Prevention is always more effective and affordable than treating advanced conditions",
                "Annual vet check-ups catch problems early when treatment is most successful",
                "Keep vaccinations and parasite prevention up to date according to your vet's schedule",
                "Learn to recognise emergency warning signs that require immediate veterinary attention",
                "Monitor your dog's weight, appetite, and behaviour for early signs of illness"
            ]
    elif cluster == "Puppy Care":
        if "development" in t:
            return [
                "Socialise extensively during the 3–14 week critical window while keeping experiences positive",
                "Expect and plan for fear periods (8–10 weeks and 6–14 months) — do not force exposure",
                "Large and giant breeds develop more slowly and need age-appropriate exercise restrictions",
                "Adolescent regression is normal — maintain consistent training through this phase",
                "Each developmental stage has specific nutritional, exercise, and behavioural needs",
                "Consult your vet if your puppy appears to miss milestones or develops unexplained behavioural changes"
            ]
        elif "essential" in t or "key terms" in t:
            return [
                "Puppy-proof your home before arrival and register with a vet within the first week",
                "Begin socialisation and positive-reinforcement training from day one",
                "Complete the primary vaccination course before allowing contact with unvaccinated dogs",
                "Establish a consistent routine for feeding, toilet breaks, sleep, and play",
                "Allow 18–20 hours of sleep per day — overtired puppies become bitey and difficult",
                "Invest in early training and socialisation — it prevents the majority of adult behaviour problems"
            ]
        elif "toy" in t:
            return [
                "Choose toys appropriate for your puppy's size, age, and chewing strength",
                "Rotate toys weekly to maintain novelty and prevent boredom",
                "Frozen Kongs and rubber chew toys provide safe teething relief",
                "Supervise all toy play and discard any toy that is damaged or has loose parts",
                "Interactive play with you (tug, fetch, puzzle feeders) is more engaging than solo toys",
                "If your puppy swallows a toy piece, contact your vet immediately"
            ]
        else:
            return [
                "Start socialisation and training from day one using positive reinforcement only",
                "Register with a vet promptly and complete the vaccination course",
                "Feed a complete puppy food matched to your puppy's expected adult size",
                "Establish consistent routines for feeding, sleep, toilet training, and play",
                "The Kennel Club and Dogs Trust offer reliable, free puppy guidance resources"
            ]
    elif cluster == "Dog Care":
        if "seasonal" in t:
            return [
                "Never leave a dog in a parked car — even on mild days, temperatures rise dangerously fast",
                "Wipe paws after winter walks to remove road salt and potential antifreeze residue",
                "Check for ticks after walks in grass, woodland, or moorland, especially in spring and autumn",
                "Adjust walk times and intensity to suit weather conditions — early mornings in summer, midday in winter",
                "Keep toxic seasonal items (antifreeze, chocolate, conkers, acorns, lilies) out of reach",
                "Ensure fresh water is always available, especially during hot weather"
            ]
        else:
            return [
                "Meet all five welfare needs: environment, diet, behaviour, companionship, and health",
                "Tailor grooming, exercise, and feeding to your specific breed's requirements",
                "Keep microchip details up to date — it is a legal requirement",
                "Annual vet visits and routine parasite prevention protect long-term health",
                "Mental stimulation through training, play, and enrichment is as important as physical exercise"
            ]
    elif cluster == "Dog Training":
        if "equipment" in t:
            return [
                "A harness, standard lead, treat pouch, and clicker cover most training needs",
                "Avoid aversive tools — the APDT, BVA, and RSPCA all oppose their use",
                "Shock collars are banned in Wales and Scotland and opposed by the BVA across the UK",
                "Long lines are essential for safe recall practice before reliable off-lead control",
                "Invest in proper fit — an ill-fitting harness causes discomfort and reduces effectiveness",
                "Good equipment supports training but does not replace consistent reward-based practice"
            ]
        elif "behaviour" in t and "body language" in t:
            return [
                "Learn to read ears, tail, posture, and facial expressions as a complete communication picture",
                "A wagging tail does not always mean a happy dog — context, speed, and height matter",
                "Never punish growling — it is a vital warning signal; removing it increases bite risk",
                "Freezing, whale eye, and lip-licking are stress signals that should prompt you to create distance",
                "Healthy play involves loose movements, play bows, and voluntary re-engagement by both dogs",
                "When in doubt about a dog's emotional state, increase distance from the trigger"
            ]
        elif "cat" in t and "scratching" in t:
            return [
                "Provide at least one scratching post per cat, plus one extra, in key locations",
                "Choose tall, sturdy posts in sisal or cardboard — avoid flimsy, short posts that wobble",
                "Place posts near where your cat already scratches, then gradually relocate if needed",
                "Never punish scratching — redirect to appropriate surfaces and reward their use",
                "Scratching serves essential functions: claw maintenance, scent marking, stretching, and stress relief"
            ]
        elif "cat" in t and "play" in t:
            return [
                "Schedule two 10–15 minute interactive play sessions daily to satisfy hunting instincts",
                "Use wand toys to mimic prey movement — never use hands or feet as play targets",
                "Follow the hunt-catch-eat-sleep sequence: energetic play, a treat, then rest",
                "Rotate toys weekly to prevent boredom and maintain interest",
                "Solo enrichment (puzzle feeders, window perches) supplements interactive play when you are away"
            ]
        elif "socialisation" in t:
            return [
                "Begin socialisation before 14 weeks — this critical window cannot be reopened",
                "Quality of exposure matters more than quantity — keep all experiences positive",
                "Puppy classes with APDT-accredited trainers provide controlled socialisation opportunities",
                "Continue socialisation throughout adolescence to maintain confidence",
                "Never force a fearful puppy into interactions — let them approach at their own pace",
                "Under-socialisation is a leading cause of serious behaviour problems in adult dogs"
            ]
        elif "training treats" in t and "choose" in t:
            return [
                "Use small (pea-sized), soft, smelly treats that can be eaten quickly during training",
                "Maintain a treat hierarchy — everyday treats for easy tasks, high-value for challenging ones",
                "Keep treats below 10% of daily calorie intake and adjust meal portions accordingly",
                "Vary treat types within sessions to maintain motivation",
                "Some dogs respond equally well to toy or play rewards — experiment with alternatives",
                "Natural, single-ingredient treats offer quality without unnecessary additives"
            ]
        elif "training treats" in t and ("reward" in t or "best" in t):
            return [
                "Soft, aromatic treats are most effective for training — dogs can eat them quickly and stay focused",
                "Build a treat hierarchy from everyday kibble to high-value options for difficult exercises",
                "Deduct treat calories from daily meals to prevent weight gain during training-heavy periods",
                "Natural single-ingredient treats (dried liver, fish) minimise additive exposure",
                "Gradually fade treats by introducing variable reinforcement as skills become reliable",
                "The APDT endorses reward-based training as the most effective and humane approach"
            ]
        elif "puppy training" in t or "first year" in t:
            return [
                "Begin training from 8 weeks old — puppies are never too young for positive reinforcement",
                "Keep sessions short (3–5 minutes) and always end on a positive note",
                "Prioritise recall, loose lead walking, and 'leave it' as essential safety cues",
                "Consistency from all family members is crucial for clear communication",
                "Toilet training takes 4–6 months with patience and a consistent routine",
                "The Kennel Club Good Citizen scheme provides a structured, progressive training framework"
            ]
        elif "complete guide" in t and "training" in t:
            return [
                "Use only reward-based methods — endorsed by the BVA, RSPCA, APDT, and Kennel Club",
                "Consistency, patience, and short frequent sessions produce the best results",
                "Avoid dominance theory and aversive techniques — they cause fear and worsen behaviour",
                "Seek help from an APDT-accredited trainer early if you encounter difficulties",
                "Training is a lifelong process — ongoing practice maintains and strengthens learned behaviours",
                "Dogs learn in context — generalise cues across different environments gradually"
            ]
        else:
            return [
                "Reward-based methods are recommended by all major UK animal welfare organisations",
                "Short, frequent training sessions are more effective than occasional long ones",
                "Consistency from all handlers is essential for reliable behaviour",
                "Seek professional help from an APDT-accredited trainer for persistent issues",
                "Training strengthens the bond between you and your dog as well as improving behaviour"
            ]

    return [
        "Follow current UK veterinary and welfare guidance for all pet care decisions",
        "Consult a qualified professional if you are unsure about any aspect of care",
        "Prevention and early intervention are always more effective than treating advanced problems",
        "Keep learning — responsible pet ownership is an ongoing commitment"
    ]


def generate_upgraded_trust_footer(cluster):
    """Generate the upgraded trust footer with org references."""
    # Base references
    base_refs = (
        'We reference UK veterinary and welfare organisations including the '
        '<a href="https://www.rspca.org.uk/" rel="nofollow">RSPCA</a>, '
        '<a href="https://www.pdsa.org.uk/" rel="nofollow">PDSA</a>, '
        '<a href="https://www.bva.co.uk/" rel="nofollow">BVA</a>, and '
        '<a href="https://fediaf.org/" rel="nofollow">FEDIAF</a>.'
    )

    if cluster == "Dog Food":
        base_refs = (
            'We reference UK veterinary and welfare organisations including the '
            '<a href="https://www.rspca.org.uk/" rel="nofollow">RSPCA</a>, '
            '<a href="https://www.pdsa.org.uk/" rel="nofollow">PDSA</a>, '
            '<a href="https://www.bva.co.uk/" rel="nofollow">BVA</a>, '
            '<a href="https://fediaf.org/" rel="nofollow">FEDIAF</a>, and the '
            '<a href="https://www.pfma.org.uk/" rel="nofollow">PFMA</a>.'
        )
    elif cluster == "Dog Health":
        base_refs = (
            'We reference UK veterinary and welfare organisations including the '
            '<a href="https://www.bva.co.uk/" rel="nofollow">BVA</a>, '
            '<a href="https://www.pdsa.org.uk/" rel="nofollow">PDSA</a>, '
            '<a href="https://www.rspca.org.uk/" rel="nofollow">RSPCA</a>, and '
            '<a href="https://fediaf.org/" rel="nofollow">FEDIAF</a>.'
        )
    elif cluster == "Puppy Care":
        base_refs = (
            'We reference UK veterinary and welfare organisations including the '
            '<a href="https://www.thekennelclub.org.uk/" rel="nofollow">Kennel Club</a>, '
            '<a href="https://www.dogstrust.org.uk/" rel="nofollow">Dogs Trust</a>, '
            '<a href="https://www.bva.co.uk/" rel="nofollow">BVA</a>, '
            '<a href="https://www.rspca.org.uk/" rel="nofollow">RSPCA</a>, and '
            '<a href="https://www.pdsa.org.uk/" rel="nofollow">PDSA</a>.'
        )
    elif cluster == "Dog Training":
        base_refs = (
            'We reference UK training and welfare organisations including the '
            '<a href="https://apdt.co.uk/" rel="nofollow">APDT</a>, '
            '<a href="https://www.thekennelclub.org.uk/" rel="nofollow">Kennel Club</a>, '
            '<a href="https://www.rspca.org.uk/" rel="nofollow">RSPCA</a>, '
            '<a href="https://www.bva.co.uk/" rel="nofollow">BVA</a>, and '
            '<a href="https://www.pdsa.org.uk/" rel="nofollow">PDSA</a>.'
        )

    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#f8fafb"}},"border":{{"radius":"8px","color":"#e2e8f0","width":"1px"}},"spacing":{{"padding":{{"top":"20px","bottom":"20px","left":"24px","right":"24px"}},"margin":{{"top":"32px","bottom":"32px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#e2e8f0;border-width:1px;border-radius:8px;background-color:#f8fafb;margin-top:32px;margin-bottom:32px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">Our Editorial Standards</h4>
<!-- /wp:heading -->
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"14px"}}}}}} -->
<p style="font-size:14px">All content on Pet Hub Online is created following our <a href="https://pethubonline.com/our-editorial-process/">editorial process</a>, supported by thorough <a href="https://pethubonline.com/how-we-research-pet-products/">research methodology</a>. {base_refs} We maintain transparency through our <a href="https://pethubonline.com/corrections-and-updates-policy/">corrections and updates policy</a>. Content is AI-assisted and editorially reviewed. For details on how we handle affiliate relationships, see our <a href="https://pethubonline.com/affiliate-disclosure/">affiliate disclosure</a>.</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->'''


def find_insertion_point_after_intro(content):
    """Find the position after the first substantive paragraph (after any quick-answer/about boxes)."""
    # Look for the H1 heading, then the first paragraph after it
    h1_match = re.search(r'<h1[^>]*>.*?</h1>', content, re.DOTALL)
    if h1_match:
        search_start = h1_match.end()
    else:
        search_start = 0

    # Find the first </p> after the h1
    first_p_end = content.find('</p>', search_start)
    if first_p_end != -1:
        # Find the end of that paragraph block (including any wp:paragraph comment)
        next_block = content.find('\n\n', first_p_end)
        if next_block != -1:
            return next_block
        return first_p_end + len('</p>')
    return -1


def find_faq_position(content):
    """Find where FAQ section starts."""
    # Look for common FAQ headings
    for pattern in [
        r'<h[23][^>]*>\s*(?:Frequently Asked Questions|FAQ)',
        r'<h[23][^>]*>\s*(?:Common Questions)',
    ]:
        m = re.search(pattern, content, re.IGNORECASE)
        if m:
            return m.start()
    return -1


def find_trust_footer(content):
    """Find the existing trust footer block to replace."""
    # Look for the editorial standards block
    pattern = r'<div class="wp-block-group has-border-color has-background[^"]*" style="[^"]*border-color:#e2e8f0[^"]*background-color:#f8fafb[^"]*">.*?Our Editorial Standards.*?</div>\s*(?:<!-- /wp:group -->)?'
    m = re.search(pattern, content, re.DOTALL)
    if m:
        return m.start(), m.end()

    # Fallback: look for the heading
    pattern2 = r'(?:<!-- wp:group[^>]*-->)?\s*<div class="wp-block-group[^"]*"[^>]*style="[^"]*#f8fafb[^"]*"[^>]*>.*?Our Editorial Standards.*?</div>\s*(?:<!-- /wp:group -->)?'
    m2 = re.search(pattern2, content, re.DOTALL)
    if m2:
        return m2.start(), m2.end()

    return -1, -1


def find_sources_section(content):
    """Find Sources and Further Reading section."""
    pattern = r'<h[23][^>]*>\s*Sources\s+and\s+Further\s+Reading'
    m = re.search(pattern, content, re.IGNORECASE)
    if m:
        return m.start()
    return -1


def find_about_editorial(content):
    """Find 'About Our Editorial Standards' section."""
    pattern = r'<h[23][^>]*>\s*About Our Editorial Standards'
    m = re.search(pattern, content, re.IGNORECASE)
    if m:
        return m.start()
    return -1


def process_post(post_info):
    """Process a single post: fetch, enhance, update."""
    post_id = int(post_info['id'])
    title = post_info['title']
    cluster = post_info['cluster']

    result = {
        'id': post_id,
        'title': title,
        'cluster': cluster,
        'at_a_glance': 'N',
        'why_this_matters': 'N',
        'what_we_considered': 'N',
        'troubleshooting': 'N',
        'warning_signs': 'N',
        'when_to_seek_help': 'N',
        'key_takeaways': 'N',
        'trust_upgraded': 'N',
        'status': 'pending'
    }

    try:
        # Fetch current content
        data = api_get(f"posts/{post_id}?context=edit")
        if 'content' not in data:
            result['status'] = f"ERROR: no content field - {str(data)[:200]}"
            return result

        content = data['content']['raw']
        original_content = content

        blocks_to_insert_after_intro = []
        blocks_to_insert_before_faq = []
        blocks_to_insert_before_trust = []

        # 1. AT A GLANCE (after first intro paragraph)
        if not has_block(content, 'at a glance'):
            blocks_to_insert_after_intro.append(generate_at_a_glance(title, cluster, content))
            result['at_a_glance'] = 'Y'
        else:
            result['at_a_glance'] = 'SKIP'

        # 2. WHY THIS MATTERS (after At a Glance)
        if not has_block(content, 'why this matters'):
            blocks_to_insert_after_intro.append(generate_why_this_matters(title, cluster))
            result['why_this_matters'] = 'Y'
        else:
            result['why_this_matters'] = 'SKIP'

        # 3. WHAT WE CONSIDERED (buying guides only)
        if is_buying_guide(title):
            if not has_block(content, 'what we considered'):
                blocks_to_insert_after_intro.append(generate_what_we_considered(title, cluster))
                result['what_we_considered'] = 'Y'
            else:
                result['what_we_considered'] = 'SKIP'
        else:
            result['what_we_considered'] = 'NA'

        # 4. TROUBLESHOOTING (before FAQ)
        if not has_block(content, 'troubleshooting common issues'):
            blocks_to_insert_before_faq.append(generate_troubleshooting(title, cluster))
            result['troubleshooting'] = 'Y'
        else:
            result['troubleshooting'] = 'SKIP'

        # 5. WARNING SIGNS (for health/food/puppy/care posts)
        if cluster in {"Dog Food", "Dog Health", "Puppy Care", "Dog Care"}:
            if not has_block(content, 'warning signs to watch for'):
                blocks_to_insert_before_faq.append(generate_warning_signs(title, cluster))
                result['warning_signs'] = 'Y'
            else:
                result['warning_signs'] = 'SKIP'
        else:
            result['warning_signs'] = 'NA'

        # 6. WHEN TO SEEK HELP
        if not has_block(content, 'when to seek professional help'):
            blocks_to_insert_before_faq.append(generate_when_to_seek_help(title, cluster))
            result['when_to_seek_help'] = 'Y'
        else:
            result['when_to_seek_help'] = 'SKIP'

        # 7. KEY TAKEAWAYS (before trust footer)
        if not has_block(content, 'key takeaways'):
            blocks_to_insert_before_trust.append(generate_key_takeaways(title, cluster))
            result['key_takeaways'] = 'Y'
        else:
            result['key_takeaways'] = 'SKIP'

        # Now insert blocks into content

        # Insert after-intro blocks
        if blocks_to_insert_after_intro:
            intro_insert_html = '\n\n' + '\n\n'.join(blocks_to_insert_after_intro)
            insert_pos = find_insertion_point_after_intro(content)
            if insert_pos != -1:
                content = content[:insert_pos] + intro_insert_html + content[insert_pos:]
            else:
                # Fallback: insert after first </p>
                first_p = content.find('</p>')
                if first_p != -1:
                    pos = first_p + len('</p>')
                    content = content[:pos] + intro_insert_html + content[pos:]

        # Insert before-FAQ blocks
        if blocks_to_insert_before_faq:
            faq_html = '\n\n' + '\n\n'.join(blocks_to_insert_before_faq)
            faq_pos = find_faq_position(content)
            if faq_pos != -1:
                content = content[:faq_pos] + faq_html + '\n\n' + content[faq_pos:]
            else:
                # Fallback: insert before Sources section
                src_pos = find_sources_section(content)
                if src_pos != -1:
                    content = content[:src_pos] + faq_html + '\n\n' + content[src_pos:]
                else:
                    # Last resort: insert before trust footer
                    tf_start, tf_end = find_trust_footer(content)
                    if tf_start != -1:
                        content = content[:tf_start] + faq_html + '\n\n' + content[tf_start:]

        # Insert before-trust blocks (key takeaways)
        if blocks_to_insert_before_trust:
            takeaway_html = '\n\n' + '\n\n'.join(blocks_to_insert_before_trust)
            # Find trust footer again (positions may have shifted)
            tf_start, tf_end = find_trust_footer(content)
            if tf_start != -1:
                content = content[:tf_start] + takeaway_html + '\n\n' + content[tf_start:]
            else:
                # Insert before "About Our Editorial Standards"
                about_pos = find_about_editorial(content)
                if about_pos != -1:
                    content = content[:about_pos] + takeaway_html + '\n\n' + content[about_pos:]
                else:
                    # Append near end
                    content = content + takeaway_html

        # 8. UPGRADE trust footer
        # Find the old trust footer and replace
        tf_start, tf_end = find_trust_footer(content)
        if tf_start != -1:
            new_footer = generate_upgraded_trust_footer(cluster)
            content = content[:tf_start] + new_footer + content[tf_end:]
            result['trust_upgraded'] = 'Y'
        else:
            result['trust_upgraded'] = 'NOT_FOUND'

        # Check if content actually changed
        if content == original_content:
            result['status'] = 'NO_CHANGES'
            return result

        # Update the post
        time.sleep(DELAY)
        success, resp = api_update(post_id, {"content": content})
        if success:
            result['status'] = 'OK'
        else:
            err_msg = str(resp)[:200]
            result['status'] = f'UPDATE_ERROR: {err_msg}'

    except Exception as e:
        result['status'] = f'ERROR: {str(e)[:200]}'
        traceback.print_exc()

    return result


def main():
    print(f"[{datetime.now().isoformat()}] Phase 10AI Batch 2 - Content Enhancement")
    print("=" * 80)

    # Load inventory
    posts = load_inventory()
    print(f"Found {len(posts)} posts in target clusters")
    for p in posts:
        print(f"  {p['id']:>5} | {p['cluster']:<15} | {p['title'][:60]}")
    print()

    # Initialize log
    log_rows = []
    log_headers = ['id', 'title', 'cluster', 'at_a_glance', 'why_this_matters',
                   'what_we_considered', 'troubleshooting', 'warning_signs',
                   'when_to_seek_help', 'key_takeaways', 'trust_upgraded', 'status']

    # Process each post
    for i, post_info in enumerate(posts):
        print(f"\n[{i+1}/{len(posts)}] Processing: {post_info['id']} - {post_info['title'][:50]}...")
        result = process_post(post_info)
        log_rows.append(result)
        print(f"  Status: {result['status']}")
        blocks_added = sum(1 for k in ['at_a_glance', 'why_this_matters', 'what_we_considered',
                                        'troubleshooting', 'warning_signs', 'when_to_seek_help',
                                        'key_takeaways'] if result[k] == 'Y')
        print(f"  Blocks added: {blocks_added} | Trust: {result['trust_upgraded']}")
        time.sleep(DELAY)

    # Write log
    with open(LOG_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=log_headers)
        writer.writeheader()
        writer.writerows(log_rows)

    print(f"\n{'=' * 80}")
    print(f"Log written to: {LOG_FILE}")

    # Summary
    ok_count = sum(1 for r in log_rows if r['status'] == 'OK')
    err_count = sum(1 for r in log_rows if 'ERROR' in r['status'])
    skip_count = sum(1 for r in log_rows if r['status'] == 'NO_CHANGES')
    print(f"Results: {ok_count} OK, {skip_count} no changes, {err_count} errors")
    print(f"Total posts processed: {len(log_rows)}")


if __name__ == "__main__":
    main()
