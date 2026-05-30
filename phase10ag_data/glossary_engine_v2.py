#!/usr/bin/env python3
"""Glossary/Key Terms Insertion Engine v2 — Dictionary-based (no OpenAI needed).
Inserts 5-8 relevant key terms into posts missing glossary blocks.
Terms are matched from a curated pet care dictionary based on content relevance.
"""

import json
import subprocess
import time
import csv
import re
import os
import tempfile

WP_AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_URL = "https://pethubonline.com/wp-json/wp/v2/posts"

DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ag_data"
LOG_FILE = os.path.join(DATA_DIR, "glossary_insertion_log_v2.csv")

ALL_CATS = {
    1377: "Cat Supplies", 1459: "Cat Toys", 1413: "Indoor Cats",
    1376: "Dog Supplies", 1397: "Pet Care", 1401: "Dog Beds",
    1489: "Dog Care", 1467: "Dog Food", 1422: "Dog Harnesses",
    1450: "Dog Health", 1441: "Dog Toys", 1442: "Puppy Care",
    1474: "Training Supplies", 1: "Uncategorized",
}

# Curated pet care glossary — ~180 terms with UK English definitions
# Each term has: trigger words (for matching), definition, and relevant clusters
GLOSSARY = [
    # Dog general
    {"term": "Breed Size Classification", "triggers": ["breed size", "small breed", "medium breed", "large breed", "giant breed"], "definition": "Categorisation of dog breeds by weight and height, typically divided into small, medium, large, and giant groups for product sizing.", "clusters": ["Dog Supplies", "Dog Beds", "Dog Care", "Dog Harnesses", "Dog Health", "Dog Food"]},
    {"term": "Orthopaedic Support", "triggers": ["orthopaedic", "orthopedic", "ortho", "joint support", "memory foam"], "definition": "Specialised design features in pet products that provide cushioning and support for joints, particularly beneficial for senior or arthritic dogs.", "clusters": ["Dog Beds", "Dog Health", "Dog Care"]},
    {"term": "Waterproof Rating", "triggers": ["waterproof", "water-resistant", "water resistant", "weatherproof"], "definition": "A measure of how effectively a material prevents water penetration, important for outdoor pet products used in wet UK weather conditions.", "clusters": ["Dog Supplies", "Dog Beds", "Dog Harnesses"]},
    {"term": "Positive Reinforcement", "triggers": ["positive reinforcement", "reward-based", "reward based", "treat training"], "definition": "A training method that rewards desired behaviours rather than punishing unwanted ones, widely endorsed by UK veterinary behaviourists.", "clusters": ["Training Supplies", "Puppy Care", "Dog Care", "Dog Toys"]},
    {"term": "Desensitisation", "triggers": ["desensiti", "desensitiz", "gradual exposure", "counter-conditioning"], "definition": "A behavioural technique involving gradual, controlled exposure to a stimulus to reduce fear or anxiety responses in pets.", "clusters": ["Training Supplies", "Puppy Care", "Dog Care", "Dog Health"]},
    {"term": "Separation Anxiety", "triggers": ["separation anxiety", "home alone", "destructive behaviour when left"], "definition": "A behavioural condition where pets become distressed when separated from their owners, often resulting in destructive behaviour or excessive vocalisation.", "clusters": ["Dog Care", "Dog Toys", "Training Supplies", "Puppy Care", "Indoor Cats"]},
    {"term": "Microchipping", "triggers": ["microchip", "chip", "microchipped"], "definition": "A legal requirement in the UK for dogs, involving implantation of a small electronic chip under the skin for permanent identification purposes.", "clusters": ["Dog Care", "Puppy Care", "Pet Care", "Dog Health"]},
    {"term": "Socialisation Period", "triggers": ["socialisation", "socialization", "socialising", "socializing", "puppy socialisation"], "definition": "The critical developmental window, typically between 3-14 weeks of age, when puppies are most receptive to new experiences and learning.", "clusters": ["Puppy Care", "Training Supplies", "Dog Care"]},
    {"term": "Enrichment", "triggers": ["enrichment", "mental stimulation", "cognitive stimulation", "brain games"], "definition": "Activities and products designed to stimulate a pet's mind and natural behaviours, preventing boredom and promoting psychological wellbeing.", "clusters": ["Dog Toys", "Cat Toys", "Indoor Cats", "Dog Care", "Puppy Care"]},
    {"term": "Recall Training", "triggers": ["recall training", "recall", "come command", "reliable recall"], "definition": "Teaching a dog to return reliably when called, considered one of the most important safety commands for off-lead exercise.", "clusters": ["Training Supplies", "Puppy Care", "Dog Care"]},
    {"term": "Lead Reactivity", "triggers": ["lead reactive", "leash reactive", "lead reactivity", "leash aggression"], "definition": "Behaviour where a dog displays excessive barking, lunging, or pulling when encountering other dogs or stimuli whilst on a lead.", "clusters": ["Training Supplies", "Dog Harnesses", "Dog Care"]},
    {"term": "Crate Training", "triggers": ["crate training", "crate", "den training"], "definition": "A method of housetraining and management using a secure enclosed space that appeals to a dog's natural denning instinct.", "clusters": ["Training Supplies", "Puppy Care", "Dog Care"]},

    # Dog food specific
    {"term": "Complete Diet", "triggers": ["complete diet", "complete food", "complete and balanced", "nutritionally complete"], "definition": "A pet food formulated to provide all essential nutrients a dog needs without requiring supplementation, meeting FEDIAF guidelines.", "clusters": ["Dog Food", "Puppy Care", "Dog Health"]},
    {"term": "Grain-Free Formula", "triggers": ["grain-free", "grain free", "no grain"], "definition": "Pet food produced without cereal grains such as wheat, corn, or rice, using alternative carbohydrate sources like sweet potato or peas.", "clusters": ["Dog Food", "Dog Health"]},
    {"term": "Raw Feeding (BARF)", "triggers": ["raw feeding", "barf", "raw diet", "biologically appropriate"], "definition": "A diet consisting of uncooked meat, bones, and vegetables, based on the principle of mimicking a dog's ancestral eating patterns.", "clusters": ["Dog Food", "Dog Health"]},
    {"term": "Life Stage Nutrition", "triggers": ["life stage", "puppy food", "senior food", "adult food", "age-appropriate"], "definition": "Tailoring a pet's diet to their specific life stage — puppy, adult, or senior — each requiring different nutrient ratios for optimal health.", "clusters": ["Dog Food", "Puppy Care", "Dog Health"]},
    {"term": "Hypoallergenic Diet", "triggers": ["hypoallergenic", "limited ingredient", "novel protein", "food sensitivity"], "definition": "Specially formulated food using limited or unusual protein sources designed for dogs with food allergies or intolerances.", "clusters": ["Dog Food", "Dog Health"]},

    # Dog beds specific
    {"term": "Bolster Bed", "triggers": ["bolster", "raised edge", "raised sides", "bumper bed"], "definition": "A dog bed featuring raised cushioned edges that provide a sense of security and a comfortable head rest for dogs who like to lean.", "clusters": ["Dog Beds", "Dog Supplies"]},
    {"term": "Calming Bed", "triggers": ["calming bed", "anxiety bed", "donut bed", "nesting bed"], "definition": "A round bed with high, soft sides designed to create a cocooning effect that helps reduce anxiety and promote restful sleep in dogs.", "clusters": ["Dog Beds", "Dog Care"]},
    {"term": "Elevated Dog Bed", "triggers": ["elevated bed", "raised bed", "camp bed", "cot bed"], "definition": "A bed with a fabric surface stretched across a frame, keeping the dog off the ground for improved airflow and temperature regulation.", "clusters": ["Dog Beds", "Dog Supplies"]},
    {"term": "Denier Rating", "triggers": ["denier", "fabric strength", "tear-resistant"], "definition": "A unit measuring the thickness and strength of fabric fibres, with higher denier numbers indicating more durable and chew-resistant bed covers.", "clusters": ["Dog Beds", "Dog Supplies"]},
    {"term": "Removable Cover", "triggers": ["removable cover", "washable cover", "machine washable", "zip-off cover"], "definition": "A detachable outer layer on pet beds that can be removed for machine washing, essential for maintaining hygiene and extending bed life.", "clusters": ["Dog Beds", "Dog Supplies"]},

    # Dog harnesses specific
    {"term": "No-Pull Harness", "triggers": ["no-pull", "no pull", "anti-pull", "front-clip"], "definition": "A harness design that discourages pulling by redirecting the dog's forward motion, typically using a front chest attachment point.", "clusters": ["Dog Harnesses", "Training Supplies", "Dog Supplies"]},
    {"term": "Back-Clip Harness", "triggers": ["back-clip", "back clip", "dorsal attachment"], "definition": "A harness with the lead attachment point on the dog's back, offering comfortable everyday walking but less pulling control.", "clusters": ["Dog Harnesses", "Dog Supplies"]},
    {"term": "Girth Measurement", "triggers": ["girth", "chest measurement", "chest circumference"], "definition": "The measurement around the widest part of a dog's ribcage, the most critical dimension for ensuring correct harness fit and comfort.", "clusters": ["Dog Harnesses", "Dog Supplies"]},
    {"term": "Padded Harness", "triggers": ["padded harness", "fleece-lined", "neoprene", "comfort harness"], "definition": "A harness featuring cushioned straps or lining that distributes pressure evenly and prevents rubbing or chafing during walks.", "clusters": ["Dog Harnesses", "Dog Supplies"]},

    # Dog health specific
    {"term": "Vaccination Schedule", "triggers": ["vaccination", "vaccine", "booster", "primary vaccination", "annual booster"], "definition": "The recommended timeline for immunisations, typically starting at 6-8 weeks with primary courses followed by annual or triennial boosters.", "clusters": ["Dog Health", "Puppy Care", "Dog Care"]},
    {"term": "Parasite Prevention", "triggers": ["parasite", "flea", "tick", "worming", "lungworm"], "definition": "Regular preventative treatments against internal and external parasites, including fleas, ticks, and various types of worms.", "clusters": ["Dog Health", "Dog Care", "Puppy Care", "Cat Supplies"]},
    {"term": "Dental Hygiene", "triggers": ["dental", "teeth cleaning", "tooth", "dental chew", "periodontal"], "definition": "Regular care of a pet's teeth and gums through brushing, dental chews, or professional cleaning to prevent periodontal disease.", "clusters": ["Dog Health", "Dog Care", "Dog Toys"]},
    {"term": "Body Condition Score", "triggers": ["body condition", "weight management", "ideal weight", "overweight", "obesity"], "definition": "A numerical assessment system (typically 1-9) used by veterinarians to evaluate whether a pet is underweight, ideal, or overweight.", "clusters": ["Dog Health", "Dog Food", "Dog Care"]},
    {"term": "Hip Dysplasia", "triggers": ["hip dysplasia", "hip score", "elbow dysplasia", "joint disease"], "definition": "A hereditary skeletal condition where the hip joint develops abnormally, common in larger breeds and assessable through BVA/KC screening.", "clusters": ["Dog Health", "Dog Beds", "Dog Care"]},
    {"term": "Neutering", "triggers": ["neutering", "spaying", "castration", "desexing", "neutered"], "definition": "Surgical removal of reproductive organs, recommended by most UK vets for health benefits and population control, typically from 6 months.", "clusters": ["Dog Health", "Dog Care", "Puppy Care"]},

    # Cat general
    {"term": "Indoor-Only Cat", "triggers": ["indoor cat", "indoor-only", "house cat", "indoor only"], "definition": "A cat kept exclusively indoors for safety, increasingly common in the UK particularly in urban areas or near busy roads.", "clusters": ["Indoor Cats", "Cat Supplies", "Cat Toys"]},
    {"term": "Vertical Territory", "triggers": ["vertical space", "vertical territory", "cat tree", "climbing", "high perch"], "definition": "Elevated spaces such as shelves, trees, and perches that satisfy a cat's natural instinct to observe their environment from height.", "clusters": ["Indoor Cats", "Cat Supplies", "Cat Toys"]},
    {"term": "Scratching Post", "triggers": ["scratching post", "scratch pad", "scratching", "sisal"], "definition": "A dedicated surface for cats to sharpen claws, stretch muscles, and mark territory, preventing damage to household furniture.", "clusters": ["Cat Supplies", "Indoor Cats", "Cat Toys"]},
    {"term": "Litter Tray Management", "triggers": ["litter tray", "litter box", "litter", "cat litter"], "definition": "The care and maintenance of feline toileting areas, with the general rule of one tray per cat plus one extra, placed in quiet locations.", "clusters": ["Cat Supplies", "Indoor Cats"]},
    {"term": "Environmental Enrichment", "triggers": ["environmental enrichment", "indoor enrichment", "cat enrichment"], "definition": "Modifications to a cat's living space that promote natural behaviours such as hunting, climbing, hiding, and exploring.", "clusters": ["Indoor Cats", "Cat Toys", "Cat Supplies"]},
    {"term": "Catnip Response", "triggers": ["catnip", "catmint", "nepetalactone"], "definition": "A hereditary sensitivity affecting roughly two-thirds of cats, causing temporary euphoric behaviour when exposed to the plant Nepeta cataria.", "clusters": ["Cat Toys", "Cat Supplies", "Indoor Cats"]},
    {"term": "Prey Drive", "triggers": ["prey drive", "hunting instinct", "predatory", "chase instinct"], "definition": "The natural instinct to stalk, chase, pounce, and catch moving objects, a fundamental behaviour that should be satisfied through interactive play.", "clusters": ["Cat Toys", "Indoor Cats", "Dog Toys"]},
    {"term": "Interactive Play", "triggers": ["interactive play", "wand toy", "feather toy", "fishing rod toy"], "definition": "Guided play sessions using toys that mimic prey movement, providing essential physical exercise and mental stimulation for indoor cats.", "clusters": ["Cat Toys", "Indoor Cats", "Cat Supplies"]},
    {"term": "Puzzle Feeder", "triggers": ["puzzle feeder", "slow feeder", "food puzzle", "treat dispenser"], "definition": "A device that requires pets to solve simple challenges to access food, slowing eating speed and providing mental stimulation.", "clusters": ["Cat Toys", "Dog Toys", "Indoor Cats", "Cat Supplies"]},
    {"term": "Catio", "triggers": ["catio", "cat enclosure", "cat run", "outdoor enclosure"], "definition": "An enclosed outdoor space that allows cats to experience fresh air and nature safely, ranging from window boxes to full garden structures.", "clusters": ["Indoor Cats", "Cat Supplies"]},
    {"term": "Multi-Cat Household", "triggers": ["multi-cat", "multiple cats", "multi cat"], "definition": "A home with two or more cats, requiring careful resource management to prevent territorial disputes and stress-related behaviours.", "clusters": ["Indoor Cats", "Cat Supplies", "Cat Toys"]},

    # Pet care general
    {"term": "Pet Insurance", "triggers": ["pet insurance", "lifetime cover", "insurance policy"], "definition": "A financial product covering veterinary costs, with lifetime policies providing ongoing annual cover that resets each year at renewal.", "clusters": ["Pet Care", "Dog Health", "Dog Care"]},
    {"term": "RSPCA", "triggers": ["rspca"], "definition": "The Royal Society for the Prevention of Cruelty to Animals, the UK's leading animal welfare charity providing rescue, rehabilitation, and rehoming services.", "clusters": ["Pet Care", "Dog Care", "Dog Health"]},
    {"term": "Kennel Club", "triggers": ["kennel club", "kc registered", "kc"], "definition": "The UK's largest organisation devoted to dog health, welfare, and training, maintaining the breed register and setting breed standards.", "clusters": ["Pet Care", "Dog Care", "Dog Health", "Puppy Care", "Training Supplies"]},
    {"term": "PDSA", "triggers": ["pdsa"], "definition": "The People's Dispensary for Sick Animals, a UK veterinary charity providing free and low-cost treatment for pets of owners in financial hardship.", "clusters": ["Pet Care", "Dog Health", "Dog Care"]},
    {"term": "Cats Protection", "triggers": ["cats protection"], "definition": "The UK's leading feline welfare charity, providing advice, neutering programmes, and rehoming services for cats across the country.", "clusters": ["Pet Care", "Cat Supplies", "Indoor Cats"]},
    {"term": "British Veterinary Association", "triggers": ["british veterinary", "bva"], "definition": "The national representative body for the UK veterinary profession, providing guidance on animal health, welfare, and ethical standards.", "clusters": ["Pet Care", "Dog Health", "Dog Care"]},
    {"term": "FEDIAF Guidelines", "triggers": ["fediaf", "pet food guidelines", "nutritional guidelines"], "definition": "European Pet Food Industry Federation nutritional standards that pet food manufacturers follow to ensure products meet minimum nutrient requirements.", "clusters": ["Dog Food", "Pet Care", "Dog Health"]},
    {"term": "Animal Welfare Act 2006", "triggers": ["animal welfare act", "five needs", "welfare act"], "definition": "UK legislation establishing five welfare needs for pet owners: suitable environment, diet, ability to exhibit normal behaviour, companionship, and health protection.", "clusters": ["Pet Care", "Dog Care", "Puppy Care"]},

    # Puppy specific
    {"term": "Puppy Proofing", "triggers": ["puppy proof", "puppy-proof", "puppy safe"], "definition": "The process of making a home environment safe for a new puppy by removing hazards such as toxic plants, electrical cables, and small ingestible items.", "clusters": ["Puppy Care", "Dog Care"]},
    {"term": "House Training", "triggers": ["house training", "housetraining", "toilet training", "potty training"], "definition": "Teaching a puppy to eliminate outdoors or in a designated area through consistent scheduling, supervision, and positive reinforcement.", "clusters": ["Puppy Care", "Training Supplies", "Dog Care"]},
    {"term": "Teething Phase", "triggers": ["teething", "puppy teeth", "baby teeth", "deciduous teeth", "chewing phase"], "definition": "The period between 3-7 months when puppies lose baby teeth and adult teeth emerge, often causing increased chewing and gum discomfort.", "clusters": ["Puppy Care", "Dog Toys", "Dog Care"]},
    {"term": "Puppy Classes", "triggers": ["puppy class", "puppy school", "puppy training class"], "definition": "Structured group training sessions for young dogs, typically accepting puppies from after their first vaccination until around 18 weeks of age.", "clusters": ["Puppy Care", "Training Supplies"]},

    # Dog toys
    {"term": "Chew Durability Rating", "triggers": ["durability", "indestructible", "tough chewer", "heavy chewer", "power chewer"], "definition": "An assessment of how well a toy withstands aggressive chewing, with materials like natural rubber and nylon rated for different chewing strengths.", "clusters": ["Dog Toys", "Dog Supplies", "Puppy Care"]},
    {"term": "KONG Classic", "triggers": ["kong", "kong classic", "stuffable toy"], "definition": "A popular hollow rubber toy that can be filled with treats or food, providing extended mental stimulation and helping manage destructive chewing.", "clusters": ["Dog Toys", "Puppy Care", "Training Supplies"]},
    {"term": "Fetch Toy", "triggers": ["fetch toy", "ball launcher", "tennis ball", "fetch"], "definition": "A toy designed to be thrown and retrieved, providing cardiovascular exercise and reinforcing the bond between dog and owner during play.", "clusters": ["Dog Toys", "Training Supplies"]},
    {"term": "Tug Toy", "triggers": ["tug toy", "tug rope", "tug-of-war", "tug of war"], "definition": "An interactive toy used for controlled pulling games between dog and owner, building engagement and providing a physical outlet for natural tugging instinct.", "clusters": ["Dog Toys", "Training Supplies", "Puppy Care"]},
    {"term": "Squeaker Toy", "triggers": ["squeaker", "squeaky toy", "plush toy"], "definition": "A soft toy containing a sound-making device that triggers prey-drive responses, requiring supervision as internal components can be a choking hazard.", "clusters": ["Dog Toys", "Puppy Care"]},

    # Training supplies
    {"term": "Clicker Training", "triggers": ["clicker", "marker training", "bridge signal"], "definition": "A precise training method using a small device that makes a click sound to mark the exact moment a desired behaviour occurs, followed by a reward.", "clusters": ["Training Supplies", "Puppy Care", "Dog Care"]},
    {"term": "Long Line", "triggers": ["long line", "training lead", "tracking line", "long lead"], "definition": "An extended lead typically 5-15 metres long used for recall training, allowing dogs freedom of movement whilst maintaining safety control.", "clusters": ["Training Supplies", "Dog Supplies", "Puppy Care"]},
    {"term": "Treat Pouch", "triggers": ["treat pouch", "treat bag", "bait bag"], "definition": "A small bag worn on the belt or clipped to clothing for quick access to training treats, enabling timely reward delivery during sessions.", "clusters": ["Training Supplies", "Dog Supplies"]},
    {"term": "Head Collar", "triggers": ["head collar", "halti", "gentle leader", "head halter"], "definition": "A training aid worn around the dog's muzzle and behind the ears, providing gentle steering control by guiding the head direction.", "clusters": ["Training Supplies", "Dog Harnesses", "Dog Supplies"]},

    # Materials and safety
    {"term": "BPA-Free", "triggers": ["bpa-free", "bpa free", "food-safe", "food safe", "non-toxic material"], "definition": "Products manufactured without Bisphenol A, a chemical compound linked to health concerns, ensuring safety for food contact and chewing.", "clusters": ["Dog Toys", "Cat Toys", "Dog Food", "Dog Supplies", "Cat Supplies"]},
    {"term": "Natural Rubber", "triggers": ["natural rubber", "rubber toy", "latex-free"], "definition": "A durable, flexible material derived from rubber trees, commonly used in quality pet toys for its resilience and safety when chewed.", "clusters": ["Dog Toys", "Cat Toys", "Dog Supplies"]},
    {"term": "Reflective Material", "triggers": ["reflective", "hi-vis", "high visibility", "visibility"], "definition": "Light-reflecting fabric or strips incorporated into pet accessories to improve visibility during dark evening or early morning walks.", "clusters": ["Dog Harnesses", "Dog Supplies", "Training Supplies"]},

    # Health and wellness terms
    {"term": "Joint Supplement", "triggers": ["joint supplement", "glucosamine", "chondroitin", "joint care"], "definition": "Nutritional additions such as glucosamine and chondroitin designed to support cartilage health and mobility, particularly in senior or large breed dogs.", "clusters": ["Dog Health", "Dog Food", "Dog Care"]},
    {"term": "Stress Signals", "triggers": ["stress signal", "calming signal", "body language", "lip licking", "whale eye"], "definition": "Observable behavioural cues such as lip licking, yawning, or turning away that indicate a pet is experiencing discomfort or anxiety.", "clusters": ["Dog Care", "Training Supplies", "Puppy Care", "Dog Health"]},
    {"term": "Preventative Healthcare", "triggers": ["preventative", "preventive care", "wellness check", "health check"], "definition": "Proactive veterinary care including regular check-ups, vaccinations, parasite control, and dental care to prevent illness before it develops.", "clusters": ["Dog Health", "Dog Care", "Pet Care", "Puppy Care"]},
    {"term": "Senior Pet Care", "triggers": ["senior dog", "senior cat", "elderly pet", "ageing", "aging"], "definition": "Adapted care routines for older pets, typically dogs over 7-8 years, addressing changing nutritional, exercise, and health monitoring needs.", "clusters": ["Dog Health", "Dog Care", "Dog Beds", "Dog Food", "Pet Care"]},

    # Product comparison terms
    {"term": "Value for Money", "triggers": ["value for money", "cost-effective", "budget", "affordable", "price point"], "definition": "An assessment weighing product quality, durability, and features against purchase price to determine overall worthiness of investment.", "clusters": ["Dog Supplies", "Cat Supplies", "Dog Beds", "Dog Toys", "Cat Toys", "Dog Harnesses"]},
    {"term": "Sizing Guide", "triggers": ["sizing guide", "size chart", "size guide", "fitting guide"], "definition": "A reference chart providing measurements and weight ranges to help pet owners select correctly fitting products for their specific animal.", "clusters": ["Dog Harnesses", "Dog Beds", "Dog Supplies"]},

    # UK-specific
    {"term": "UK Stockist", "triggers": ["uk stockist", "uk retailer", "available in uk", "uk delivery", "uk shipping"], "definition": "A retailer based in or delivering to the United Kingdom, offering products meeting UK safety standards with domestic shipping options.", "clusters": ["Dog Supplies", "Cat Supplies", "Dog Beds", "Dog Toys", "Cat Toys", "Dog Harnesses", "Training Supplies"]},
    {"term": "CE/UKCA Marking", "triggers": ["ce mark", "ukca", "safety standard", "safety certification"], "definition": "Conformity markings indicating products meet UK and European safety, health, and environmental protection requirements for sale.", "clusters": ["Dog Supplies", "Cat Supplies", "Dog Toys", "Cat Toys"]},

    # Grooming
    {"term": "Double Coat", "triggers": ["double coat", "undercoat", "topcoat", "guard hairs"], "definition": "A fur type consisting of a dense insulating undercoat beneath longer protective guard hairs, requiring specific grooming tools and techniques.", "clusters": ["Dog Care", "Dog Supplies", "Dog Health"]},
    {"term": "Shedding Season", "triggers": ["shedding", "moult", "moulting", "fur loss"], "definition": "Periods of heavier hair loss, typically occurring in spring and autumn, when dogs naturally adjust their coat thickness for seasonal temperature changes.", "clusters": ["Dog Care", "Dog Supplies", "Dog Health", "Cat Supplies"]},
    {"term": "Grooming Routine", "triggers": ["grooming routine", "grooming schedule", "regular grooming", "brushing routine"], "definition": "A consistent schedule of coat brushing, nail trimming, ear cleaning, and bathing tailored to a pet's breed, coat type, and lifestyle.", "clusters": ["Dog Care", "Dog Supplies", "Cat Supplies", "Pet Care"]},

    # Walking and exercise
    {"term": "Off-Lead Exercise", "triggers": ["off-lead", "off lead", "off-leash", "free running"], "definition": "Allowing dogs to exercise without a lead in designated safe areas, requiring reliable recall and awareness of local bylaws and livestock.", "clusters": ["Dog Care", "Training Supplies", "Dog Harnesses"]},
    {"term": "Lead Length Regulations", "triggers": ["lead length", "lead law", "extendable lead", "retractable lead"], "definition": "UK guidelines and local bylaws governing acceptable lead types and lengths in public spaces, parks, and areas with livestock.", "clusters": ["Dog Harnesses", "Dog Supplies", "Training Supplies"]},

    # Safety
    {"term": "Choking Hazard", "triggers": ["choking hazard", "choking risk", "small parts", "supervision required"], "definition": "Risk of airway obstruction from toy components or treat pieces, requiring size-appropriate product selection and supervised play sessions.", "clusters": ["Dog Toys", "Cat Toys", "Puppy Care"]},
    {"term": "Toxic Plants", "triggers": ["toxic plant", "poisonous plant", "dangerous plant", "lily", "daffodil"], "definition": "Household and garden plants harmful to pets if ingested, including lilies (fatal to cats), daffodils, and azaleas among many common UK species.", "clusters": ["Pet Care", "Indoor Cats", "Puppy Care", "Dog Health", "Cat Supplies"]},

    # Travel
    {"term": "Pet Travel Scheme", "triggers": ["pet travel", "pet passport", "animal health certificate"], "definition": "UK regulations for travelling abroad with pets, requiring microchipping, rabies vaccination, and an Animal Health Certificate from a vet.", "clusters": ["Pet Care", "Dog Care"]},
    {"term": "Car Safety Restraint", "triggers": ["car restraint", "car harness", "seat belt", "travel crate", "car safety"], "definition": "Equipment securing pets during vehicle travel as required by the Highway Code, including harnesses, crates, and barriers.", "clusters": ["Dog Harnesses", "Dog Supplies", "Pet Care"]},

    # Cat-specific health
    {"term": "Feline Lower Urinary Tract Disease", "triggers": ["flutd", "urinary", "cystitis", "urinary tract"], "definition": "A group of conditions affecting the cat's bladder and urethra, influenced by diet, stress, and water intake, common in indoor cats.", "clusters": ["Indoor Cats", "Cat Supplies", "Pet Care"]},
    {"term": "Hairball Prevention", "triggers": ["hairball", "fur ball", "hair ball"], "definition": "Strategies including regular grooming, specialised diets, and malt paste to reduce the formation of ingested fur accumulations in cats.", "clusters": ["Indoor Cats", "Cat Supplies"]},
    {"term": "Feline Immunodeficiency Virus", "triggers": ["fiv", "feline immunodeficiency"], "definition": "A viral infection spread through deep bite wounds that weakens the immune system, a key reason many UK rescue cats are rehomed as indoor-only.", "clusters": ["Indoor Cats", "Pet Care"]},
    {"term": "Window Perch", "triggers": ["window perch", "window seat", "window shelf", "cat shelf"], "definition": "A mounted platform allowing cats to sit at window height for bird watching and sunbathing, providing essential visual stimulation for indoor cats.", "clusters": ["Indoor Cats", "Cat Supplies"]},

    # Comparison/review specific
    {"term": "Independent Review", "triggers": ["independent review", "unbiased", "honest review", "our assessment"], "definition": "An evaluation conducted without manufacturer influence or sponsorship, providing objective information to help pet owners make informed purchasing decisions.", "clusters": ["Dog Supplies", "Cat Supplies", "Dog Beds", "Dog Toys", "Cat Toys"]},
    {"term": "Durability Testing", "triggers": ["durability test", "stress test", "wear test", "long-term use"], "definition": "Assessment of how well a product withstands regular use over time, particularly important for toys, beds, and outdoor accessories.", "clusters": ["Dog Toys", "Dog Beds", "Dog Supplies", "Cat Toys"]},
]


def get_cluster(cats):
    for c in (cats if isinstance(cats, list) else []):
        if c in ALL_CATS:
            return ALL_CATS[c]
    return "Unknown"


def strip_html(text):
    t = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    t = re.sub(r'<[^>]+>', ' ', t)
    return re.sub(r'\s+', ' ', t).strip().lower()


def has_glossary(content):
    c = content.lower()
    if 'key-terms' in c:
        return True
    if re.search(r'<h2[^>]*>key terms</h2>', c, re.IGNORECASE):
        return True
    return False


def match_terms(plain_text, cluster, max_terms=8):
    """Find the most relevant glossary terms for a post's content."""
    scored = []
    for entry in GLOSSARY:
        cluster_match = cluster in entry.get("clusters", [])
        trigger_count = 0
        for trigger in entry["triggers"]:
            count = plain_text.count(trigger.lower())
            trigger_count += count

        if trigger_count == 0:
            continue

        score = trigger_count * (2 if cluster_match else 1)
        scored.append((score, entry))

    scored.sort(key=lambda x: -x[0])
    return [e for _, e in scored[:max_terms]]


def build_glossary_block(terms):
    items = []
    for t in terms:
        items.append(f'<li><strong>{t["term"]}</strong> — {t["definition"]}</li>')
    items_html = "\n".join(items)
    return (
        '<!-- wp:heading {"className":"key-terms-heading"} -->\n'
        '<h2 class="wp-block-heading key-terms-heading">Key Terms</h2>\n'
        '<!-- /wp:heading -->\n\n'
        '<!-- wp:list {"className":"key-terms-list"} -->\n'
        '<ul class="key-terms-list">\n'
        f'{items_html}\n'
        '</ul>\n'
        '<!-- /wp:list -->'
    )


def find_insertion_point(content):
    """Insert before Sources and References, or before last H2."""
    patterns = [
        r'(<!-- wp:heading[^>]*-->\s*<h2[^>]*>Sources\s+and\s+(?:References|Further\s+Reading)</h2>\s*<!-- /wp:heading -->)',
        r'(<!-- wp:heading[^>]*-->\s*<h2[^>]*>Sources\s+&amp;\s+References</h2>\s*<!-- /wp:heading -->)',
    ]
    for pat in patterns:
        m = re.search(pat, content, re.IGNORECASE | re.DOTALL)
        if m:
            return m.start()

    all_h2 = list(re.finditer(r'<!-- wp:heading[^>]*-->', content))
    if all_h2:
        return all_h2[-1].start()
    return len(content)


def wp_fetch_all():
    all_posts = []
    page = 1
    while True:
        time.sleep(2)
        url = f"{WP_URL}?status=publish&per_page=100&page={page}&context=edit&_fields=id,title,content,categories"
        r = subprocess.run(["curl", "-s", "--compressed", "-u", WP_AUTH, url],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            break
        posts = json.loads(r.stdout)
        if not isinstance(posts, list) or len(posts) == 0:
            break
        all_posts.extend(posts)
        if len(posts) < 100:
            break
        page += 1
    return all_posts


def wp_update(post_id, content):
    time.sleep(3)
    payload = json.dumps({"content": content})
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(payload)
        tmp = f.name
    try:
        r = subprocess.run(["curl", "-s", "--compressed", "-u", WP_AUTH,
                            "-X", "POST", "-H", "Content-Type: application/json",
                            "-d", f"@{tmp}", f"{WP_URL}/{post_id}"],
                           capture_output=True, text=True, timeout=60)
        resp = json.loads(r.stdout)
        return ("id" in resp), (resp.get("message", "ok") if "id" not in resp else "ok")
    except Exception as e:
        return False, str(e)
    finally:
        os.unlink(tmp)


def main():
    print("Glossary/Key Terms Insertion Engine v2 (dictionary-based)")
    print("=" * 60)

    posts = wp_fetch_all()
    print(f"Fetched {len(posts)} published posts\n")

    results = []
    inserted = 0
    skipped = 0
    errors = 0
    too_few = 0

    for idx, post in enumerate(posts):
        pid = post["id"]
        title = post["title"]["raw"] if isinstance(post["title"], dict) else str(post["title"])
        content = post["content"]["raw"] if isinstance(post["content"], dict) else str(post["content"])
        cluster = get_cluster(post.get("categories", []))

        if has_glossary(content):
            skipped += 1
            continue

        plain = strip_html(content)
        terms = match_terms(plain, cluster)

        if len(terms) < 5:
            too_few += 1
            results.append({
                "post_id": pid, "title": title, "cluster": cluster,
                "terms_count": len(terms), "status": "too_few_matches",
                "terms": "; ".join(t["term"] for t in terms)
            })
            print(f"  [{idx+1}] {pid}: {title[:50]} — only {len(terms)} matches, skipping")
            continue

        glossary_block = build_glossary_block(terms)
        insert_pos = find_insertion_point(content)
        new_content = content[:insert_pos].rstrip() + "\n\n" + glossary_block + "\n\n" + content[insert_pos:].lstrip()

        ok, msg = wp_update(pid, new_content)
        if ok:
            inserted += 1
            results.append({
                "post_id": pid, "title": title, "cluster": cluster,
                "terms_count": len(terms), "status": "inserted",
                "terms": "; ".join(t["term"] for t in terms)
            })
            print(f"  [{idx+1}] {pid}: {title[:50]} — {len(terms)} terms INSERTED")
        else:
            errors += 1
            results.append({
                "post_id": pid, "title": title, "cluster": cluster,
                "terms_count": len(terms), "status": "error",
                "terms": msg[:100]
            })
            print(f"  [{idx+1}] {pid}: {title[:50]} — ERROR: {msg[:60]}")

    with open(LOG_FILE, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=["post_id", "title", "cluster", "terms_count", "status", "terms"])
        w.writeheader()
        w.writerows(results)

    print("\n" + "=" * 60)
    print("GLOSSARY ENGINE v2 COMPLETE")
    print(f"Posts scanned: {len(posts)}")
    print(f"Already had glossary: {skipped}")
    print(f"Glossary inserted: {inserted}")
    print(f"Too few matches: {too_few}")
    print(f"Errors: {errors}")
    print(f"Log: {LOG_FILE}")


if __name__ == "__main__":
    main()
