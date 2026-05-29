#!/usr/bin/env python3
"""
Phase 10AT/10AG/10AR — Citation Leadership + Glossary Saturation
Clusters: Dog Food, Educational, Dog Training
Adds: Key Terms/Glossary, Common Mistakes, Beginner Recommendations blocks
"""

import subprocess
import json
import time
import csv
import os
import sys
import tempfile
import re
import html

# ─── credentials ───────────────────────────────────────────────────────
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
BASE = "https://pethubonline.com/wp-json/wp/v2"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10at_data"
LOG_FILE = os.path.join(DATA_DIR, "citation_leadership_log.csv")
DELAY = 2  # seconds between API calls

# ─── post IDs per cluster ──────────────────────────────────────────────
DOG_FOOD_IDS = [5467, 5460, 3839, 3838, 3837, 3836, 7172]
EDUCATIONAL_IDS = [5521, 5462, 5424, 5419, 5416, 5415, 5414, 4574, 4272, 4265, 4216, 4167, 4160, 4146]
DOG_TRAINING_IDS = [5523, 5512, 5458, 5036, 4792, 4791, 4132, 4125, 4118]

# ─── glossary terms per cluster ────────────────────────────────────────
DOG_FOOD_GLOSSARY = {
    "Complete Nutrition": "A diet that provides all essential nutrients (proteins, fats, vitamins, minerals) in the correct proportions, meeting FEDIAF or AAFCO standards for a specific life stage.",
    "Crude Protein": "The total protein content in pet food as measured by nitrogen analysis; listed on labels as a minimum percentage guarantee.",
    "Ash Content": "The mineral residue remaining after food is incinerated; indicates overall mineral levels including calcium, phosphorus, and magnesium.",
    "FEDIAF Guidelines": "Standards set by the European Pet Food Industry Federation defining minimum and maximum nutrient levels for complete pet foods.",
    "Hypoallergenic Diet": "A diet formulated with novel or hydrolysed protein sources to reduce the risk of triggering food allergies or intolerances.",
    "Grain-Free": "Pet food made without cereal grains such as wheat, maize, or rice; often substitutes legumes or potatoes as carbohydrate sources.",
    "Life-Stage Feeding": "Adjusting nutrient profiles and portion sizes according to a dog’s age bracket — puppy, adult, or senior — to match changing metabolic needs.",
    "Guaranteed Analysis": "The section on pet food labels listing minimum or maximum percentages of crude protein, crude fat, crude fibre, and moisture.",
}

DOG_TRAINING_GLOSSARY = {
    "Positive Reinforcement": "A training method that rewards desired behaviour with treats, praise, or play, increasing the likelihood the behaviour is repeated.",
    "Clicker Conditioning": "Using a small clicking device to mark the exact moment a dog performs a desired behaviour, followed immediately by a reward.",
    "Desensitisation": "Gradually exposing a dog to a feared stimulus at low intensity, slowly increasing exposure to reduce the fear response over time.",
    "Counterconditioning": "Pairing a stimulus that causes an unwanted reaction with something the dog enjoys, changing the emotional association from negative to positive.",
    "Marker Word": "A consistent verbal cue (e.g. “yes!”) used to pinpoint the moment a dog performs correctly, functioning similarly to a clicker.",
    "Threshold": "The point at which a dog transitions from calm to reactive; effective training occurs below threshold where the dog can still learn.",
    "Impulse Control": "Teaching a dog to regulate its own behaviour — waiting, settling, or resisting temptation — rather than acting on immediate urges.",
    "Shaping": "Reinforcing successive approximations of a target behaviour, gradually guiding the dog toward the full desired action.",
}

# Educational glossary — dynamically selected per post topic
EDUCATIONAL_GLOSSARY_POOL = {
    "socialisation": {
        "Critical Socialisation Period": "The developmental window (roughly 3–14 weeks) during which puppies are most receptive to new experiences, people, and environments.",
        "Habituation": "The process by which a puppy learns to accept routine stimuli (sounds, textures, surfaces) as non-threatening through repeated neutral exposure.",
        "Fear Imprint Period": "Specific developmental phases where negative experiences can create lasting phobias; careful management is essential during these windows.",
        "Puppy Class": "A structured group session for puppies under 16 weeks, combining basic training with supervised social interaction.",
        "Environmental Enrichment": "Providing varied sensory experiences — novel objects, sounds, surfaces — to build confidence and cognitive resilience.",
    },
    "health": {
        "Preventive Healthcare": "Routine veterinary measures (vaccinations, parasite control, dental checks) designed to detect or prevent illness before clinical signs appear.",
        "Body Condition Score (BCS)": "A numerical scale (typically 1–9) used by veterinarians to assess whether a pet is underweight, ideal, or overweight based on visual and tactile evaluation.",
        "Titre Testing": "A blood test measuring antibody levels to determine whether a dog retains immunity from previous vaccinations, helping avoid unnecessary boosters.",
        "Microchipping": "Implanting a small RFID chip under the skin for permanent identification; a legal requirement in the UK for all dogs over eight weeks old.",
        "Neutering": "Surgical removal of reproductive organs (castration in males, spaying in females) to prevent breeding and reduce certain health and behavioural risks.",
    },
    "behaviour": {
        "Body Language": "The system of physical signals — ear position, tail carriage, posture, facial expression — dogs use to communicate emotional states.",
        "Calming Signals": "Subtle behaviours (lip licking, yawning, turning away) dogs display to de-escalate tension or signal non-threat intentions.",
        "Resource Guarding": "A behaviour where a dog uses defensive actions (growling, snapping, stiffening) to protect valued items such as food, toys, or resting spots.",
        "Separation Anxiety": "A condition where a dog shows extreme distress (vocalisation, destruction, house soiling) when left alone or separated from its attachment figure.",
        "Trigger Stacking": "The cumulative effect of multiple stressors occurring close together, reducing a dog’s ability to cope and lowering the threshold for reactive behaviour.",
    },
    "nutrition": {
        "Macronutrients": "The three main energy-providing nutrients — protein, fat, and carbohydrate — required in relatively large amounts in the diet.",
        "Micronutrients": "Vitamins and minerals required in small quantities but essential for metabolic processes, immune function, and cellular health.",
        "Digestibility": "The proportion of nutrients in food that are actually absorbed by the body rather than excreted; higher digestibility means more nutritional value per gram.",
        "Metabolisable Energy (ME)": "The energy from food available to the body after accounting for losses in faeces, urine, and gases; the standard measure for pet food calorie content.",
        "Omega-3 Fatty Acids": "Essential polyunsaturated fats (EPA and DHA) that support skin health, coat condition, joint function, and cognitive development in dogs.",
    },
    "grooming": {
        "Double Coat": "A coat type consisting of a dense, insulating undercoat beneath a longer, protective topcoat; common in breeds like Labrador Retrievers and German Shepherds.",
        "Undercoat Rake": "A specialised grooming tool designed to remove loose undercoat hair without damaging the topcoat.",
        "Hand Stripping": "A grooming technique for wire-coated breeds where dead hair is manually plucked rather than clipped, maintaining correct coat texture.",
        "Matting": "Tangled clumps of fur that form when loose hair becomes trapped and compacted, causing skin irritation and restricting airflow to the skin.",
        "Deshedding": "The process of removing loose undercoat hair using specialised tools or treatments, reducing household shedding and promoting coat health.",
    },
    "safety": {
        "Toxic Ingestion": "Consumption of a substance harmful to dogs, including chocolate, xylitol, grapes, certain plants, and human medications.",
        "Pet-Proofing": "Systematically identifying and removing or securing hazards in a home or garden to prevent accidental injury or poisoning.",
        "Microchip Registration": "Recording a pet’s microchip number on an approved database with up-to-date owner contact details; legally required in the UK.",
        "First Aid Kit (Pet)": "A collection of supplies (bandages, antiseptic, digital thermometer, tick remover, emergency vet contact) kept accessible for immediate pet care.",
        "Recall Training": "Teaching a dog to return immediately when called, considered one of the most important safety behaviours for off-lead exercise.",
    },
    "general": {
        "Enrichment": "Activities and environments that stimulate a dog’s natural behaviours and cognitive abilities, reducing boredom and promoting mental well-being.",
        "Breed-Specific Needs": "The unique exercise, grooming, training, and health requirements associated with a dog’s breed heritage and genetic predispositions.",
        "Veterinary Behaviourist": "A veterinarian with additional specialist training in diagnosing and treating behavioural disorders, often using a combination of behaviour modification and medication.",
        "Positive Reinforcement": "Rewarding desired behaviour to increase the likelihood it will be repeated; the foundation of modern, evidence-based dog training.",
        "Life-Stage Needs": "The changing requirements for nutrition, exercise, veterinary care, and mental stimulation as a dog progresses from puppy to adult to senior.",
    },
}

# ─── common mistakes per cluster ───────────────────────────────────────
DOG_FOOD_MISTAKES = [
    "Switching foods abruptly instead of transitioning gradually over 7–10 days, which commonly causes digestive upset.",
    "Choosing food based solely on marketing claims rather than checking the guaranteed analysis and ingredient quality.",
    "Over-supplementing a complete diet with extra vitamins or minerals, which can create dangerous nutrient imbalances.",
    "Using adult food for puppies (or vice versa), ignoring the different caloric and nutrient density each life stage requires.",
    "Assuming grain-free automatically means healthier — some grain-free diets have been linked to dilated cardiomyopathy (DCM) concerns.",
    "Feeding table scraps as a regular portion of the diet, displacing balanced nutrition and encouraging begging behaviour.",
]

DOG_TRAINING_MISTAKES = [
    "Repeating commands multiple times before the dog responds, which teaches the dog to ignore the first cue.",
    "Punishing a dog after the fact — dogs cannot connect delayed punishment to a past action, causing confusion and anxiety.",
    "Skipping foundation behaviours (sit, stay, recall) and jumping to advanced tricks before reliability is established.",
    "Training sessions that are too long; dogs learn best in short bursts of 5–10 minutes with breaks between.",
    "Inconsistent rules between household members, undermining the dog’s understanding of expected behaviour.",
    "Using the dog’s name as a recall command rather than a distinct recall word, diluting the name’s meaning.",
]

EDUCATIONAL_MISTAKES_POOL = {
    "socialisation": [
        "Waiting until vaccinations are fully complete before any socialisation, missing the critical developmental window.",
        "Flooding a puppy with overwhelming experiences instead of introducing stimuli gradually at the puppy’s pace.",
        "Confusing socialisation with simply being around other dogs — quality, controlled interactions matter more than quantity.",
        "Forcing a fearful puppy to “face its fears” rather than using gradual desensitisation and positive associations.",
    ],
    "health": [
        "Skipping annual veterinary check-ups because the dog “seems fine” — many conditions are asymptomatic in early stages.",
        "Using human medications on dogs without veterinary guidance, which can cause serious toxicity.",
        "Ignoring dental health until problems become severe; dental disease affects over 80% of dogs by age three.",
        "Assuming a cold, wet nose means the dog is healthy — this is an unreliable indicator of overall well-being.",
    ],
    "behaviour": [
        "Interpreting a wagging tail as always meaning happiness — tail movement can also indicate arousal, anxiety, or warning.",
        "Attributing human emotions and motivations to dog behaviour (anthropomorphism), leading to misunderstanding and inappropriate responses.",
        "Punishing growling, which removes the dog’s warning system and increases the risk of biting without prior warning.",
        "Assuming a dog that rolls over is always requesting belly rubs — it can also be a submissive or appeasement gesture.",
    ],
    "nutrition": [
        "Relying on marketing buzzwords (“premium”, “holistic”, “human-grade”) without checking the actual nutrient profile.",
        "Calculating portions based on the dog’s current weight when the dog is overweight, perpetuating excess weight.",
        "Adding raw eggs, garlic, or other “natural supplements” without understanding the risks or consulting a veterinarian.",
        "Assuming all dogs of the same breed need exactly the same amount of food, ignoring individual metabolism and activity levels.",
    ],
    "grooming": [
        "Bathing a dog too frequently, stripping natural oils and causing dry, irritated skin.",
        "Using human shampoo on dogs, which has the wrong pH balance and can cause skin problems.",
        "Neglecting to check and clean ears regularly, especially in floppy-eared breeds prone to infections.",
        "Cutting nails too short without knowing where the quick is, causing pain and making the dog fear nail trims.",
    ],
    "safety": [
        "Leaving toxic foods (chocolate, grapes, xylitol-containing products) accessible on countertops or in bins.",
        "Assuming a fenced garden is escape-proof without checking for gaps, weak points, or items dogs can climb on.",
        "Not securing dogs in vehicles — unrestrained dogs are a distraction and at serious risk during sudden stops.",
        "Relying solely on a collar instead of a well-fitted harness for dogs that pull, risking neck and trachea injury.",
    ],
    "general": [
        "Underestimating a dog’s exercise needs based on size alone — some small breeds require more activity than larger ones.",
        "Skipping mental stimulation and relying only on physical exercise, which can lead to boredom-driven behavioural issues.",
        "Choosing a breed based on appearance without researching temperament, energy levels, and care requirements.",
        "Ignoring early signs of stress or discomfort, allowing small issues to develop into entrenched behavioural problems.",
    ],
}

# ─── beginner recommendations per cluster ──────────────────────────────
DOG_FOOD_RECS = [
    "Start with a FEDIAF-compliant complete food appropriate for your dog’s life stage — this ensures all essential nutrients are covered without supplementation.",
    "Weigh portions using kitchen scales rather than estimating with a scoop; even small daily overfeeding compounds into significant weight gain.",
    "Introduce new foods gradually by mixing 25% new with 75% current food, adjusting the ratio over 7–10 days.",
    "Keep a feeding diary for the first month to track how your dog responds to a new diet (energy, coat, stool quality).",
    "Consult your veterinarian before switching to a raw, home-cooked, or therapeutic diet to ensure nutritional completeness.",
]

DOG_TRAINING_RECS = [
    "Begin with three core behaviours — sit, stay, and recall — before adding complexity; reliability in basics underpins everything else.",
    "Keep sessions short (5–10 minutes) and end on a success to maintain your dog’s enthusiasm and positive associations with training.",
    "Use high-value treats (small, soft, smelly) for new or difficult behaviours, switching to praise and play as the behaviour becomes reliable.",
    "Train in low-distraction environments first, then gradually increase difficulty by adding distance, duration, and distractions.",
    "Be consistent with cue words and hand signals across all family members to avoid confusing your dog.",
]

EDUCATIONAL_RECS_POOL = {
    "socialisation": [
        "Start socialisation within the first week of bringing your puppy home, using safe environments and vaccinated dogs.",
        "Aim for variety: introduce your puppy to different people, surfaces, sounds, and gentle handling every day.",
        "Watch your puppy’s body language during new experiences — retreat and try again more gently if you see signs of stress.",
        "Enrol in a reputable puppy class before 16 weeks to combine structured socialisation with early training.",
    ],
    "health": [
        "Establish a relationship with a veterinary practice early and schedule routine check-ups every 6–12 months.",
        "Keep a health journal recording vaccinations, parasite treatments, weight changes, and any unusual symptoms.",
        "Learn to perform a basic home health check: eyes, ears, teeth, skin, paws, and body condition scoring.",
        "Ask your vet about breed-specific health screenings relevant to your dog’s genetic background.",
    ],
    "behaviour": [
        "Learn the basics of canine body language before interpreting your dog’s behaviour — free resources from the APDT are a good starting point.",
        "Reward calm, relaxed behaviour at home to build a default settle; this is one of the most valuable behaviours you can reinforce.",
        "If you notice sudden behavioural changes, consult your vet first to rule out pain or medical causes.",
        "Keep a behaviour diary noting triggers, contexts, and your dog’s responses to identify patterns over time.",
    ],
    "nutrition": [
        "Read the guaranteed analysis panel and ingredients list rather than relying on front-of-pack marketing claims.",
        "Use your dog’s body condition score (not breed charts alone) to determine whether portion sizes need adjusting.",
        "Treats should make up no more than 10% of daily caloric intake; subtract treat calories from meal portions.",
        "If considering a special diet (raw, grain-free, home-cooked), consult a veterinary nutritionist for a balanced recipe.",
    ],
    "grooming": [
        "Establish a grooming routine early in your dog’s life so it becomes a positive, familiar experience.",
        "Invest in breed-appropriate grooming tools — a slicker brush for long coats, a rubber curry for short coats.",
        "Make grooming sessions short and reward-based initially, gradually increasing duration as your dog becomes comfortable.",
        "Check ears, teeth, and nails weekly; catching small issues early prevents them from becoming costly veterinary problems.",
    ],
    "safety": [
        "Conduct a room-by-room pet-proofing audit before bringing a new dog home, checking for toxic plants, accessible chemicals, and small swallowable objects.",
        "Keep your veterinarian’s emergency number and the nearest out-of-hours clinic details saved in your phone.",
        "Ensure your dog’s microchip details are registered and up to date — this is the single most effective tool for reuniting lost pets.",
        "Practise recall in safe, enclosed areas before trusting off-lead in open spaces; a reliable recall is your primary safety tool.",
    ],
    "general": [
        "Research your chosen breed thoroughly before committing — consider energy levels, grooming needs, and typical health concerns.",
        "Build a daily routine that includes physical exercise, mental stimulation, training, and rest periods.",
        "Join a local dog training class to build skills in a structured, supportive environment with professional guidance.",
        "Budget for ongoing costs (veterinary care, insurance, food, grooming) alongside the initial purchase or adoption fee.",
    ],
}


# ─── block templates ───────────────────────────────────────────────────
def glossary_block(terms: dict) -> str:
    """Key Terms / Glossary — grey background."""
    items = "\n".join(
        f'<li><strong>{term}</strong> – {defn}</li>' for term, defn in terms.items()
    )
    return (
        '<!-- wp:group {"style":{"color":{"background":"#f8fafc"},"border":{"radius":"6px","width":"1px","color":"#e2e8f0"},"spacing":{"padding":{"top":"16px","bottom":"16px","left":"20px","right":"20px"},"margin":{"top":"24px","bottom":"24px"}}},"layout":{"type":"constrained"}} -->\n'
        '<div class="wp-block-group has-border-color has-background" style="border-color:#e2e8f0;border-width:1px;border-radius:6px;background-color:#f8fafc;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<!-- wp:heading {"level":4} --><h4 class="wp-block-heading">\U0001f4d6 Key Terms</h4><!-- /wp:heading -->\n'
        f'<!-- wp:list --><ul class="wp-block-list">{items}</ul><!-- /wp:list -->\n'
        '</div>\n<!-- /wp:group -->'
    )


def mistakes_block(mistakes: list) -> str:
    """Common Mistakes — red background."""
    items = "\n".join(f"<li>{m}</li>" for m in mistakes)
    return (
        '<!-- wp:group {"style":{"color":{"background":"#fef2f2"},"border":{"radius":"6px","width":"1px","color":"#fecaca"},"spacing":{"padding":{"top":"16px","bottom":"16px","left":"20px","right":"20px"},"margin":{"top":"24px","bottom":"24px"}}},"layout":{"type":"constrained"}} -->\n'
        '<div class="wp-block-group has-border-color has-background" style="border-color:#fecaca;border-width:1px;border-radius:6px;background-color:#fef2f2;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<!-- wp:heading {"level":4} --><h4 class="wp-block-heading">⚠️ Common Mistakes to Avoid</h4><!-- /wp:heading -->\n'
        f'<!-- wp:list --><ul class="wp-block-list">{items}</ul><!-- /wp:list -->\n'
        '</div>\n<!-- /wp:group -->'
    )


def recs_block(recs: list) -> str:
    """Beginner Recommendations — blue background."""
    items = "\n".join(f"<li>{r}</li>" for r in recs)
    return (
        '<!-- wp:group {"style":{"color":{"background":"#eff6ff"},"border":{"radius":"6px","width":"1px","color":"#bfdbfe"},"spacing":{"padding":{"top":"16px","bottom":"16px","left":"20px","right":"20px"},"margin":{"top":"24px","bottom":"24px"}}},"layout":{"type":"constrained"}} -->\n'
        '<div class="wp-block-group has-border-color has-background" style="border-color:#bfdbfe;border-width:1px;border-radius:6px;background-color:#eff6ff;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<!-- wp:heading {"level":4} --><h4 class="wp-block-heading">\U0001f4a1 Beginner Recommendations</h4><!-- /wp:heading -->\n'
        f'<!-- wp:list --><ul class="wp-block-list">{items}</ul><!-- /wp:list -->\n'
        '</div>\n<!-- /wp:group -->'
    )


# ─── helpers ───────────────────────────────────────────────────────────
def api_get(endpoint: str) -> dict:
    """GET request via curl subprocess."""
    url = f"{BASE}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30,
    )
    if not result.stdout.strip():
        raise RuntimeError(f"Empty response from {url}")
    return json.loads(result.stdout)


def api_update(post_id: int, data: dict) -> dict:
    """POST (update) via curl subprocess with temp file."""
    url = f"{BASE}/posts/{post_id}"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f, ensure_ascii=False)
        tmppath = f.name
    try:
        result = subprocess.run(
            [
                "curl", "-s", "--compressed",
                "-u", AUTH,
                "-X", "POST",
                "-H", "Content-Type: application/json",
                "-d", f"@{tmppath}",
                url,
            ],
            capture_output=True, text=True, timeout=60,
        )
        if not result.stdout.strip():
            raise RuntimeError(f"Empty response updating post {post_id}")
        resp = json.loads(result.stdout)
        if "id" not in resp:
            raise RuntimeError(f"Update failed for {post_id}: {result.stdout[:300]}")
        return resp
    finally:
        os.unlink(tmppath)


def detect_topic(title: str, content: str) -> str:
    """Detect educational topic from title/content keywords."""
    text = (title + " " + content).lower()
    scores = {
        "socialisation": sum(1 for w in ["sociali", "puppy class", "introduce", "new experience", "puppy party"] if w in text),
        "health": sum(1 for w in ["health", "vet", "vaccin", "parasite", "illness", "disease", "check-up", "symptom", "neuter", "spay"] if w in text),
        "behaviour": sum(1 for w in ["behaviour", "behavior", "body language", "anxiety", "aggress", "reactive", "calm", "stress", "bark"] if w in text),
        "nutrition": sum(1 for w in ["nutrition", "feed", "diet", "food", "kibble", "portion", "calor", "weight", "protein", "fat"] if w in text),
        "grooming": sum(1 for w in ["groom", "brush", "bath", "coat", "nail", "fur", "shed", "trim", "clip"] if w in text),
        "safety": sum(1 for w in ["safe", "toxic", "poison", "emergency", "hazard", "danger", "escape", "secure", "first aid"] if w in text),
    }
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "general"
    return best


def has_block(content: str, marker: str) -> bool:
    """Check if a block type already exists."""
    return marker.lower() in content.lower()


def find_insertion_point(content: str) -> int:
    """Find the best insertion point: before editorial standards / trust footer, or end."""
    # Look for editorial standards / trust footer patterns
    patterns = [
        r'<!--\s*wp:group.*?editorial.standards',
        r'<!--\s*wp:group.*?trust.footer',
        r'<!--\s*wp:group.*?#e8f5e9',  # green trust footer pattern
        r'<!--\s*wp:group.*?Our Commitment',
        r'<!--\s*wp:group.*?Editorial Standards',
        r'<div[^>]*class="[^"]*editorial',
        r'<h[234][^>]*>\s*(?:Our Commitment|Editorial Standards|About (?:This|Our) (?:Content|Guide))',
    ]
    for pat in patterns:
        m = re.search(pat, content, re.IGNORECASE | re.DOTALL)
        if m:
            return m.start()
    return len(content)


def select_educational_glossary(topic: str) -> dict:
    """Pick glossary terms for an educational post based on its detected topic."""
    pool = EDUCATIONAL_GLOSSARY_POOL.get(topic, EDUCATIONAL_GLOSSARY_POOL["general"])
    return pool


def select_educational_mistakes(topic: str) -> list:
    """Pick common mistakes for an educational post based on its detected topic."""
    pool = EDUCATIONAL_MISTAKES_POOL.get(topic, EDUCATIONAL_MISTAKES_POOL["general"])
    return pool


def select_educational_recs(topic: str) -> list:
    """Pick beginner recs for an educational post based on its detected topic."""
    pool = EDUCATIONAL_RECS_POOL.get(topic, EDUCATIONAL_RECS_POOL["general"])
    return pool


# ─── main processing ──────────────────────────────────────────────────
def process_post(post_id: int, cluster: str, log_rows: list):
    """Fetch, augment, and update a single post."""
    print(f"\n{'='*60}")
    print(f"Processing post {post_id} (cluster: {cluster})")

    # Fetch post
    post = api_get(f"posts/{post_id}?_fields=id,title,content,slug")
    title = post["title"]["rendered"]
    content_raw = post["content"]["rendered"]
    print(f"  Title: {title}")
    print(f"  Content length: {len(content_raw)} chars")
    time.sleep(DELAY)

    # Fetch raw content (block editor)
    post_raw = api_get(f"posts/{post_id}?context=edit&_fields=id,content")
    content = post_raw["content"]["raw"]
    print(f"  Raw content length: {len(content)} chars")
    time.sleep(DELAY)

    # Track what we add
    glossary_added = False
    mistakes_added = False
    recs_added = False
    comparison_added = False

    blocks_to_insert = []

    # ── Determine content for this cluster ──
    if cluster == "Dog Food":
        glossary_terms = DOG_FOOD_GLOSSARY
        mistake_items = DOG_FOOD_MISTAKES
        rec_items = DOG_FOOD_RECS
    elif cluster == "Dog Training":
        glossary_terms = DOG_TRAINING_GLOSSARY
        mistake_items = DOG_TRAINING_MISTAKES
        rec_items = DOG_TRAINING_RECS
    else:  # Educational
        topic = detect_topic(title, content)
        print(f"  Detected topic: {topic}")
        glossary_terms = select_educational_glossary(topic)
        mistake_items = select_educational_mistakes(topic)
        rec_items = select_educational_recs(topic)

    # ── Check and build glossary block ──
    if has_block(content, "Key Terms"):
        print("  [SKIP] Key Terms block already exists")
    else:
        blocks_to_insert.append(glossary_block(glossary_terms))
        glossary_added = True
        print(f"  [ADD] Key Terms ({len(glossary_terms)} terms)")

    # ── Check and build mistakes block ──
    if has_block(content, "Common Mistakes"):
        print("  [SKIP] Common Mistakes block already exists")
    else:
        blocks_to_insert.append(mistakes_block(mistake_items))
        mistakes_added = True
        print(f"  [ADD] Common Mistakes ({len(mistake_items)} items)")

    # ── Check and build recs block ──
    if has_block(content, "Beginner Recommendations"):
        print("  [SKIP] Beginner Recommendations block already exists")
    else:
        blocks_to_insert.append(recs_block(rec_items))
        recs_added = True
        print(f"  [ADD] Beginner Recommendations ({len(rec_items)} items)")

    # ── Update if anything to add ──
    if blocks_to_insert:
        insertion_point = find_insertion_point(content)
        new_blocks = "\n\n".join(blocks_to_insert)
        updated_content = content[:insertion_point] + "\n\n" + new_blocks + "\n\n" + content[insertion_point:]

        print(f"  Inserting {len(blocks_to_insert)} block(s) at position {insertion_point}")
        print(f"  New content length: {len(updated_content)} chars")

        resp = api_update(post_id, {"content": updated_content})
        print(f"  Updated post {resp['id']} successfully")
        status = "updated"
        time.sleep(DELAY)
    else:
        print("  Nothing to add — all blocks present")
        status = "skipped"

    log_rows.append({
        "id": post_id,
        "title": title,
        "cluster": cluster,
        "glossary_added": glossary_added,
        "common_mistakes_added": mistakes_added,
        "beginner_recs_added": recs_added,
        "comparison_added": comparison_added,
        "status": status,
    })


def main():
    log_rows = []
    all_posts = (
        [(pid, "Dog Food") for pid in DOG_FOOD_IDS]
        + [(pid, "Educational") for pid in EDUCATIONAL_IDS]
        + [(pid, "Dog Training") for pid in DOG_TRAINING_IDS]
    )

    total = len(all_posts)
    print(f"Phase 10AT/10AG/10AR — Citation Leadership")
    print(f"Total posts to process: {total}")
    print(f"Clusters: Dog Food ({len(DOG_FOOD_IDS)}), Educational ({len(EDUCATIONAL_IDS)}), Dog Training ({len(DOG_TRAINING_IDS)})")

    for i, (pid, cluster) in enumerate(all_posts, 1):
        try:
            print(f"\n[{i}/{total}]", end="")
            process_post(pid, cluster, log_rows)
        except Exception as e:
            print(f"  ERROR on post {pid}: {e}")
            log_rows.append({
                "id": pid,
                "title": f"ERROR: {e}",
                "cluster": cluster,
                "glossary_added": False,
                "common_mistakes_added": False,
                "beginner_recs_added": False,
                "comparison_added": False,
                "status": "error",
            })
            time.sleep(DELAY)

    # ── Write CSV log ──
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "title", "cluster", "glossary_added",
            "common_mistakes_added", "beginner_recs_added",
            "comparison_added", "status",
        ])
        writer.writeheader()
        writer.writerows(log_rows)

    print(f"\n{'='*60}")
    print(f"COMPLETE — {total} posts processed")
    updated = sum(1 for r in log_rows if r["status"] == "updated")
    skipped = sum(1 for r in log_rows if r["status"] == "skipped")
    errors = sum(1 for r in log_rows if r["status"] == "error")
    print(f"  Updated: {updated}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors:  {errors}")
    print(f"Log written to: {LOG_FILE}")


if __name__ == "__main__":
    main()
