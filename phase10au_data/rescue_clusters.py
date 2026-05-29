#!/usr/bin/env python3
"""
Phase 10AR/10AS/10AT/10AU – Cluster Rescue for Dog Beds + Indoor Cats
Adds missing: Key Terms, Common Mistakes, When to Seek Professional Help,
Beginner Recommendations, At a Glance, Key Takeaways
"""

import subprocess, json, time, csv, re, sys, tempfile, os

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
BASE = "https://pethubonline.com/wp-json/wp/v2/posts"
LOG_PATH = "/var/lib/freelancer/projects/40416335/phase10au_data/rescue_dog_beds_indoor_cats.csv"
DELAY = 2.5

DOG_BEDS_IDS = [5522, 5510, 4784, 4783, 4018, 4011, 4004, 3996, 7332, 7333, 7334, 7335, 7336, 7174]
INDOOR_CATS_IDS = [5519, 5296, 7342, 7343, 7344, 7345, 7346, 7167]

# ─── Topic-specific content generators ────────────────────────────────────

def get_glossary_terms(title, cluster):
    """Return 5-8 glossary terms specific to the post topic."""
    title_lower = title.lower()

    if cluster == "Dog Beds":
        if "orthopaedic" in title_lower or "orthop" in title_lower or "joint" in title_lower:
            return [
                ("<strong>Orthopaedic bed</strong>", "A dog bed specifically designed with supportive foam or filling to relieve pressure on joints, bones, and muscles."),
                ("<strong>Memory foam</strong>", "Viscoelastic polyurethane foam that moulds to a dog’s body shape, distributing weight evenly to reduce pressure points."),
                ("<strong>High-density foam</strong>", "Foam with a density rating above 30 kg/m³, providing firmer and more durable support than standard foam."),
                ("<strong>Bolster</strong>", "A raised cushioned edge around a dog bed that provides neck and head support and a sense of security."),
                ("<strong>Pressure point</strong>", "An area of the body where bones are close to the skin surface and concentrated weight can cause discomfort or sores."),
                ("<strong>Degenerative joint disease</strong>", "A progressive condition where cartilage in joints breaks down over time, causing pain and reduced mobility."),
                ("<strong>Crate mat</strong>", "A flat, low-profile bed designed to fit inside a dog crate or kennel, often with non-slip backing."),
            ]
        elif "sizing" in title_lower or "measure" in title_lower or "size" in title_lower or "fit" in title_lower:
            return [
                ("<strong>Nose-to-tail measurement</strong>", "The distance from the tip of a dog’s nose to the base of their tail, used as the primary sizing reference."),
                ("<strong>Bolster bed</strong>", "A bed with raised edges that provides a headrest and sense of enclosure, requiring slightly larger dimensions."),
                ("<strong>Sleeping style</strong>", "The habitual position a dog adopts when resting, such as curled, sprawled, or on their side, which affects bed size needs."),
                ("<strong>Internal dimensions</strong>", "The usable sleeping area inside the bed’s raised edges, as opposed to the outer dimensions of the product."),
                ("<strong>Crate-compatible bed</strong>", "A bed sized specifically to fit within standard crate dimensions without bunching or folding."),
                ("<strong>Growth allowance</strong>", "Additional space factored into bed sizing for puppies to accommodate expected growth over the coming months."),
            ]
        elif "material" in title_lower or "foam" in title_lower or "fabric" in title_lower:
            return [
                ("<strong>Memory foam</strong>", "Viscoelastic polyurethane foam that responds to heat and pressure, moulding to a dog’s body shape for even weight distribution."),
                ("<strong>Egg-crate foam</strong>", "Foam cut into a convoluted peak-and-valley pattern that promotes airflow and provides lighter cushioning."),
                ("<strong>Polyester fill</strong>", "Synthetic fibre stuffing that is lightweight, hypoallergenic, and machine-washable, commonly used in budget dog beds."),
                ("<strong>Denier</strong>", "A unit measuring the thickness and durability of fabric fibres; higher denier fabrics resist tearing and punctures better."),
                ("<strong>Waterproof liner</strong>", "An internal barrier layer that prevents moisture, urine, or drool from reaching the foam core of a dog bed."),
                ("<strong>Ripstop fabric</strong>", "A reinforced woven material with interlocking threads that prevent small tears from spreading, ideal for chew-resistant beds."),
                ("<strong>CertiPUR certification</strong>", "An independent testing standard confirming that foam is free from harmful chemicals, heavy metals, and ozone depleters."),
            ]
        elif "wash" in title_lower or "clean" in title_lower or "dry" in title_lower or "hygien" in title_lower:
            return [
                ("<strong>Removable cover</strong>", "A zippered outer layer on a dog bed that can be taken off and machine-washed separately from the filling."),
                ("<strong>Waterproof liner</strong>", "A protective inner layer between the cover and foam core that prevents moisture from penetrating the filling."),
                ("<strong>Enzymatic cleaner</strong>", "A cleaning product containing biological enzymes that break down organic matter such as urine, saliva, and odour-causing bacteria."),
                ("<strong>Air tumble dry</strong>", "A dryer setting using no heat or very low heat to dry fabrics without damaging foam, waterproof coatings, or fabric integrity."),
                ("<strong>Dust mites</strong>", "Microscopic organisms that feed on dead skin cells and thrive in soft furnishings, a common allergen for dogs and humans."),
                ("<strong>Pre-treatment</strong>", "Applying a stain remover or cleaning solution to soiled areas before a full wash cycle to improve stain removal."),
            ]
        elif "puppy" in title_lower or "puppies" in title_lower or "young" in title_lower:
            return [
                ("<strong>Chew-resistant fabric</strong>", "Heavy-duty material, often ballistic nylon or ripstop, designed to withstand a puppy’s teething and chewing behaviour."),
                ("<strong>Crate training bed</strong>", "A flat or low-profile bed designed to fit inside a crate during house-training and sleep routine establishment."),
                ("<strong>Waterproof liner</strong>", "An internal protective layer that prevents accidents from reaching and damaging the bed’s filling during toilet training."),
                ("<strong>Growth stage sizing</strong>", "Choosing a bed based on the predicted adult size of a puppy rather than their current measurements."),
                ("<strong>Bolster bed</strong>", "A bed with cushioned raised edges that provides a sense of security and warmth for young dogs."),
                ("<strong>Machine-washable</strong>", "A bed or cover that can be cleaned in a standard domestic washing machine, essential during the messy puppy stage."),
            ]
        elif "travel" in title_lower or "portable" in title_lower or "outdoor" in title_lower:
            return [
                ("<strong>Portable bed</strong>", "A lightweight, foldable dog bed designed for transport to different locations such as holidays, cars, or visits."),
                ("<strong>Roll-up mat</strong>", "A thin, flexible sleeping surface that can be rolled and secured with straps for easy packing and carrying."),
                ("<strong>Non-slip base</strong>", "A rubberised or textured bottom layer that prevents the bed from sliding on smooth floors, car boots, or tent floors."),
                ("<strong>Water-resistant fabric</strong>", "Material treated with a durable water repellent (DWR) coating that causes moisture to bead and roll off the surface."),
                ("<strong>Elevated cot bed</strong>", "A raised platform bed with a breathable mesh or fabric top, keeping dogs off damp or hot ground surfaces."),
                ("<strong>Compression sack</strong>", "A stuff sack that compresses a travel bed into a smaller volume for fitting into luggage, rucksacks, or car boots."),
            ]
        elif "senior" in title_lower or "older" in title_lower or "ageing" in title_lower or "elderly" in title_lower:
            return [
                ("<strong>Orthopaedic support</strong>", "Specialised cushioning, typically memory foam, that relieves pressure on ageing joints and reduces pain from arthritis."),
                ("<strong>Low-entry bed</strong>", "A bed with a reduced or absent front bolster, allowing dogs with limited mobility to step in without lifting their legs high."),
                ("<strong>Thermoregulating material</strong>", "Fabrics or foams designed to retain warmth in winter and dissipate heat in summer, benefiting temperature-sensitive senior dogs."),
                ("<strong>Pressure sores</strong>", "Skin ulcers that develop when bony areas press against hard surfaces for prolonged periods, common in less mobile older dogs."),
                ("<strong>Memory foam</strong>", "Viscoelastic foam that moulds to the body’s contours, distributing weight evenly and easing joint strain."),
                ("<strong>Incontinence liner</strong>", "A waterproof inner layer that protects the bed core from urine accidents, which become more frequent in senior dogs."),
            ]
        elif "chew" in title_lower or "destruc" in title_lower or "indestructible" in title_lower or "tough" in title_lower:
            return [
                ("<strong>Ballistic nylon</strong>", "A thick, tightly woven synthetic fabric originally developed for military use, highly resistant to tearing and puncturing."),
                ("<strong>Ripstop weave</strong>", "A reinforced fabric construction where thicker threads are interwoven at intervals to prevent small tears from spreading."),
                ("<strong>Denier rating</strong>", "A measure of fibre thickness; higher denier (1000D+) fabrics offer greater resistance to a dog’s teeth and claws."),
                ("<strong>Chew-proof</strong>", "Marketing term for beds constructed from exceptionally durable materials, though no bed is truly indestructible."),
                ("<strong>Elevated cot bed</strong>", "A raised bed frame with a taut fabric sleeping surface, reducing accessible edges and filling that dogs can chew."),
                ("<strong>Destructive chewing</strong>", "Persistent, forceful chewing behaviour often driven by anxiety, boredom, or teething rather than simple exploration."),
            ]
        else:
            # Generic dog beds glossary
            return [
                ("<strong>Orthopaedic bed</strong>", "A dog bed with specialised foam or filling designed to support joints and relieve pressure points during rest."),
                ("<strong>Memory foam</strong>", "Viscoelastic foam that moulds to a dog’s body shape, distributing weight evenly to reduce joint strain."),
                ("<strong>Bolster</strong>", "A raised, cushioned edge around a dog bed providing head and neck support and a feeling of security."),
                ("<strong>Crate mat</strong>", "A flat, low-profile sleeping pad designed to fit inside standard dog crates and kennels."),
                ("<strong>Waterproof liner</strong>", "A protective internal layer between the cover and filling that prevents moisture penetration."),
                ("<strong>Removable cover</strong>", "A zippered outer fabric layer that can be detached and machine-washed for hygiene maintenance."),
                ("<strong>Non-slip base</strong>", "A rubberised or textured bottom surface that prevents the bed from sliding on hard floors."),
            ]

    elif cluster == "Indoor Cats":
        if "exercise" in title_lower or "active" in title_lower or "play" in title_lower:
            return [
                ("<strong>Environmental enrichment</strong>", "Modifications to a cat’s living space that encourage natural behaviours such as climbing, hunting, and exploring."),
                ("<strong>Vertical space</strong>", "Elevated areas like cat trees, shelves, and perches that allow cats to climb and observe from height, fulfilling a core feline instinct."),
                ("<strong>Food puzzle</strong>", "An interactive feeding device that requires a cat to manipulate, paw, or solve a challenge to access food, providing mental stimulation."),
                ("<strong>Prey-sequence play</strong>", "Play that mimics the natural hunting cycle: stare, stalk, pounce, catch, and ‘kill bite,’ providing complete physical and mental satisfaction."),
                ("<strong>Zoomies</strong>", "Sudden bursts of frantic running energy, common in indoor cats with insufficient daily physical activity."),
                ("<strong>Interactive toy</strong>", "A toy that requires human participation, such as wand toys or laser pointers, promoting bonding and exercise simultaneously."),
            ]
        elif "stress" in title_lower or "anxiety" in title_lower or "calm" in title_lower or "behavio" in title_lower:
            return [
                ("<strong>Environmental enrichment</strong>", "Changes to a cat’s surroundings that encourage natural behaviours and reduce boredom-related stress."),
                ("<strong>Redirected aggression</strong>", "Aggressive behaviour directed at a nearby person or animal when the actual source of frustration is inaccessible."),
                ("<strong>Feliway</strong>", "A synthetic feline facial pheromone product that can help reduce stress-related behaviours in cats."),
                ("<strong>Safe space</strong>", "A quiet, enclosed area where a cat can retreat when feeling overwhelmed, with access to food, water, and a litter tray."),
                ("<strong>Resource guarding</strong>", "Behaviour where a cat protects valued items such as food, resting spots, or litter trays from other animals."),
                ("<strong>Vertical territory</strong>", "Elevated spaces that allow cats to establish personal areas above ground level, reducing conflict in multi-cat households."),
            ]
        elif "enrich" in title_lower or "stimul" in title_lower or "bore" in title_lower or "mental" in title_lower:
            return [
                ("<strong>Environmental enrichment</strong>", "Providing opportunities for natural behaviours through physical and mental challenges in the home environment."),
                ("<strong>Food puzzle</strong>", "A device that makes cats work for their food by batting, pawing, or solving a mechanism, mimicking foraging behaviour."),
                ("<strong>Vertical space</strong>", "Cat-accessible elevated areas such as shelves, trees, and wall-mounted perches that satisfy the instinct to climb and survey."),
                ("<strong>Rotation schedule</strong>", "Regularly swapping available toys and activities to maintain novelty and prevent habituation and boredom."),
                ("<strong>Scent enrichment</strong>", "Introducing safe, novel smells such as catnip, silver vine, or outdoor scents to stimulate a cat’s powerful sense of smell."),
                ("<strong>Window perch</strong>", "A secure platform attached to or placed near a window, providing visual stimulation from outdoor activity."),
                ("<strong>Clicker training</strong>", "A positive-reinforcement training method using a clicking sound to mark desired behaviour, followed by a treat reward."),
            ]
        elif "safe" in title_lower or "proof" in title_lower or "hazard" in title_lower or "toxic" in title_lower:
            return [
                ("<strong>Cat-proofing</strong>", "The process of removing or securing hazards in a home to prevent injury or poisoning of indoor cats."),
                ("<strong>Toxic plant</strong>", "A plant species that can cause illness or death if ingested by a cat, including lilies, poinsettias, and dieffenbachia."),
                ("<strong>Window restrictor</strong>", "A device fitted to windows that limits how far they can open, preventing cats from falling or escaping."),
                ("<strong>Vertical territory</strong>", "Safe elevated spaces that allow cats to move around a room at height, away from floor-level hazards."),
                ("<strong>Cord management</strong>", "Securing or concealing electrical cables and blind cords to prevent chewing, entanglement, or electrocution."),
                ("<strong>Microchipping</strong>", "Implanting a tiny electronic chip under a cat’s skin for permanent identification, required by law in England since June 2024."),
            ]
        elif "health" in title_lower or "weight" in title_lower or "diet" in title_lower or "nutrition" in title_lower or "obes" in title_lower:
            return [
                ("<strong>Body condition score (BCS)</strong>", "A numerical scale (typically 1–9) used by veterinarians to assess whether a cat is underweight, ideal, or overweight."),
                ("<strong>Obligate carnivore</strong>", "An animal that requires nutrients found only in meat, making a high-protein diet essential for cats."),
                ("<strong>Environmental enrichment</strong>", "Home modifications and activities that encourage physical movement and mental stimulation, helping to manage weight."),
                ("<strong>Food puzzle</strong>", "A feeding device that slows consumption and encourages activity, helping indoor cats maintain a healthy weight."),
                ("<strong>Taurine</strong>", "An essential amino acid for cats that supports heart function, vision, and reproduction, found naturally in meat."),
                ("<strong>Indoor cat metabolism</strong>", "The typically lower caloric needs of indoor cats compared to outdoor cats, due to reduced physical activity levels."),
            ]
        else:
            # Generic indoor cats glossary
            return [
                ("<strong>Environmental enrichment</strong>", "Modifications to a cat’s living space that stimulate natural behaviours such as climbing, hunting, and exploring."),
                ("<strong>Vertical space</strong>", "Elevated areas like cat trees and shelves that allow cats to climb and observe from height, a core feline need."),
                ("<strong>Food puzzle</strong>", "An interactive device requiring a cat to work for food, providing mental stimulation and slowing eating."),
                ("<strong>Litter tray rule</strong>", "The guideline of providing one litter tray per cat plus one extra, placed in separate quiet locations."),
                ("<strong>Scratching post</strong>", "A dedicated surface for claw maintenance and territory marking, essential for protecting furniture in indoor homes."),
                ("<strong>Window perch</strong>", "A secure platform by a window that provides visual stimulation and a warm resting spot for indoor cats."),
                ("<strong>Microchipping</strong>", "A permanent identification method required by law for cats in England since June 2024."),
            ]
    return []


def get_common_mistakes(title, cluster):
    """Return 4-6 mistakes specific to the post topic."""
    title_lower = title.lower()

    if cluster == "Dog Beds":
        if "orthopaedic" in title_lower or "orthop" in title_lower or "joint" in title_lower:
            return [
                "Buying a thin foam bed labelled ‘orthopaedic’ without checking the foam density – look for at least 30 kg/m³ density.",
                "Choosing a bed that is too small, forcing the dog to curl up and placing extra strain on already sore joints.",
                "Placing the orthopaedic bed near a radiator or draughty doorway, which can worsen inflammation or cause stiffness.",
                "Assuming an orthopaedic bed replaces veterinary treatment for joint conditions rather than complementing it.",
                "Neglecting to wash the cover regularly, allowing bacteria and allergens to build up around a vulnerable dog.",
            ]
        elif "sizing" in title_lower or "measure" in title_lower or "size" in title_lower or "fit" in title_lower:
            return [
                "Measuring the dog while standing instead of lying stretched out, resulting in a bed that is too short.",
                "Forgetting to add 15–20 cm to the nose-to-tail measurement to allow comfortable stretching.",
                "Using outer bed dimensions instead of internal sleeping area dimensions when comparing products.",
                "Buying a puppy-sized bed for a growing dog without accounting for their expected adult size.",
                "Choosing a round bed for a dog that sleeps stretched out, or a flat mat for one that prefers to curl up.",
            ]
        elif "material" in title_lower or "foam" in title_lower or "fabric" in title_lower:
            return [
                "Selecting the cheapest foam without checking density – low-density foam compresses within weeks and loses support.",
                "Choosing a fabric based on appearance rather than durability, leading to rapid wear from claws and teeth.",
                "Ignoring the importance of a waterproof liner, especially for puppies, seniors, or dogs prone to drooling.",
                "Assuming all memory foam is equal – quality varies enormously and cheaper versions may contain harmful chemicals.",
                "Overlooking fabric breathability in warm climates, causing the dog to overheat and avoid the bed.",
            ]
        elif "wash" in title_lower or "clean" in title_lower or "dry" in title_lower:
            return [
                "Machine-washing foam inserts directly, which destroys the foam structure and support properties.",
                "Using hot water or harsh detergents that degrade waterproof liners and irritate a dog’s skin.",
                "Tumble-drying covers on high heat, causing shrinkage and damage to water-resistant coatings.",
                "Waiting until the bed smells noticeably bad before washing – dust mites and bacteria accumulate long before odour appears.",
                "Forgetting to vacuum the bed weekly between washes to remove hair, dander, and debris from the surface.",
            ]
        elif "puppy" in title_lower or "puppies" in title_lower:
            return [
                "Spending heavily on a premium bed that the puppy quickly outgrows or destroys during teething.",
                "Choosing a bed without a waterproof liner during the house-training period, leading to permanent stains and odours.",
                "Placing the bed in a high-traffic area where the puppy cannot settle or feel safe enough to sleep.",
                "Not providing a crate-compatible bed when crate training, causing the puppy to associate the crate with discomfort.",
                "Selecting a bed with small removable parts or decorations that a puppy could chew off and swallow.",
            ]
        elif "travel" in title_lower or "portable" in title_lower or "outdoor" in title_lower:
            return [
                "Choosing a travel bed that is too bulky or heavy to comfortably carry, defeating its portable purpose.",
                "Using a home bed for travel instead of a dedicated travel bed, risking damage from dirt, moisture, and insects.",
                "Forgetting to introduce the travel bed at home first, so the dog does not associate it with rest.",
                "Selecting a non-waterproof travel bed for outdoor or camping use where ground moisture is likely.",
                "Not securing the travel bed in a car boot, allowing it to slide during braking and unsettling the dog.",
            ]
        elif "senior" in title_lower or "older" in title_lower or "ageing" in title_lower:
            return [
                "Keeping a flat, unsupportive bed for a senior dog instead of upgrading to orthopaedic support as joints age.",
                "Choosing a bed with high bolsters that a dog with arthritis or mobility issues struggles to climb over.",
                "Placing the bed far from the family, isolating an older dog who needs reassurance and warmth.",
                "Washing the bed too infrequently, allowing bacteria that can worsen skin conditions common in senior dogs.",
                "Assuming a dog’s reluctance to use a new bed means they dislike it – seniors need time to adjust to change.",
            ]
        elif "chew" in title_lower or "destruc" in title_lower or "tough" in title_lower:
            return [
                "Assuming ‘chew-proof’ labels guarantee the bed will survive any dog – no bed is truly indestructible.",
                "Punishing the dog for destroying beds instead of addressing the root cause (anxiety, boredom, teething).",
                "Choosing zipped covers that a determined chewer can unzip to access and ingest the filling inside.",
                "Buying the cheapest option repeatedly instead of investing once in a genuinely durable, well-constructed bed.",
                "Leaving a known chewer unsupervised with a new bed before you have assessed how they interact with it.",
            ]
        else:
            return [
                "Choosing the wrong bed size by guessing rather than measuring the dog in their natural sleeping position.",
                "Prioritising appearance over comfort, selecting a bed that suits the room but not the dog’s needs.",
                "Ignoring the importance of washability – a bed that cannot be cleaned regularly becomes a hygiene concern.",
                "Placing the bed in an inconvenient location and wondering why the dog refuses to use it.",
                "Assuming all dogs have the same bed preferences regardless of breed, age, health, and sleeping style.",
            ]

    elif cluster == "Indoor Cats":
        if "exercise" in title_lower or "active" in title_lower or "play" in title_lower:
            return [
                "Relying solely on solo toys and expecting the cat to exercise itself without human-led interactive play sessions.",
                "Using laser pointers without finishing the session with a tangible toy the cat can ‘catch,’ causing frustration.",
                "Scheduling play sessions at the wrong time of day – cats are most active at dawn and dusk, not midday.",
                "Providing the same toys every day without rotation, leading to boredom and disengagement.",
                "Assuming a cat that sleeps all day is simply lazy rather than under-stimulated and lacking exercise opportunities.",
            ]
        elif "stress" in title_lower or "anxiety" in title_lower or "calm" in title_lower or "behavio" in title_lower:
            return [
                "Punishing a stressed cat for inappropriate urination or scratching, which increases anxiety rather than resolving it.",
                "Introducing changes to the home all at once instead of gradually, overwhelming a sensitive indoor cat.",
                "Ignoring subtle stress signs like over-grooming, hiding, or appetite changes until they become severe.",
                "Using strong-scented air fresheners or essential oil diffusers near cat areas, which many cats find distressing.",
                "Forcing interaction with a stressed cat instead of allowing them to approach on their own terms.",
            ]
        elif "enrich" in title_lower or "stimul" in title_lower or "bore" in title_lower or "mental" in title_lower:
            return [
                "Providing enrichment items without rotating them, leading to habituation and renewed boredom.",
                "Relying on food puzzles alone without also offering climbing, play, and social interaction opportunities.",
                "Placing all enrichment in one room instead of distributing activities throughout the home.",
                "Choosing enrichment items that are too difficult, causing frustration rather than stimulation.",
                "Assuming a quiet, inactive cat is content when they may actually be under-stimulated and withdrawn.",
            ]
        elif "safe" in title_lower or "proof" in title_lower or "hazard" in title_lower or "toxic" in title_lower:
            return [
                "Assuming a cat will instinctively avoid toxic plants – many cats chew greenery regardless of toxicity.",
                "Leaving windows open without restrictors, risking ‘high-rise syndrome’ falls even from low floors.",
                "Storing human medications in accessible locations – paracetamol is lethal to cats even in small doses.",
                "Using dog flea treatments on cats, many of which contain permethrin that is highly toxic to felines.",
                "Failing to secure blind cords and electrical cables that pose strangulation and electrocution risks.",
            ]
        elif "health" in title_lower or "weight" in title_lower or "diet" in title_lower or "obes" in title_lower:
            return [
                "Free-feeding dry food throughout the day, which leads to overeating in bored indoor cats.",
                "Using outdoor cat feeding guidelines for indoor cats, who typically need 20–30% fewer calories.",
                "Ignoring gradual weight gain because the cat ‘looks fine’ – even 0.5 kg excess can be significant for a cat.",
                "Switching food abruptly rather than transitioning over 7–10 days, causing digestive upset and food refusal.",
                "Assuming weight management is only about food, overlooking the critical role of daily exercise and enrichment.",
            ]
        else:
            return [
                "Assuming indoor cats need less veterinary care because they are not exposed to outdoor risks.",
                "Providing only one litter tray in a multi-cat household, leading to stress and inappropriate elimination.",
                "Neglecting environmental enrichment, resulting in a bored cat that develops behavioural problems.",
                "Keeping windows and doors unsecured, risking accidental escape of a cat unaccustomed to outdoor dangers.",
                "Overlooking dental health because the cat shows no obvious signs of pain – cats hide dental issues well.",
            ]
    return []


def get_when_to_seek_help(title, cluster):
    """Return 3-5 warning signs specific to the post topic."""
    title_lower = title.lower()

    if cluster == "Dog Beds":
        if "orthopaedic" in title_lower or "joint" in title_lower:
            return [
                "Your dog consistently refuses to lie down or takes a long time to settle, which may indicate the bed is not providing adequate pain relief.",
                "You notice new or worsening limping, stiffness, or difficulty rising that does not improve with an orthopaedic bed – consult your vet promptly.",
                "Pressure sores, calluses, or hair loss develop on elbows or hips despite using a supportive bed, suggesting the condition needs veterinary assessment.",
                "Your dog yelps or whimpers when shifting position during sleep, indicating pain that requires professional evaluation.",
            ]
        elif "wash" in title_lower or "clean" in title_lower:
            return [
                "Your dog develops persistent skin irritation, rashes, or hot spots that may be caused by allergens or bacteria in bedding.",
                "A strong, lingering odour remains even after thorough washing, which could indicate a bacterial or fungal issue requiring veterinary advice.",
                "You notice fleas or flea dirt in the bed despite regular cleaning – seek veterinary flea treatment for the dog and professional home treatment.",
            ]
        else:
            return [
                "Your dog suddenly refuses to use their bed or shows signs of pain when lying down, which may indicate an underlying health issue.",
                "You notice swelling, redness, or sores on joints or pressure points, suggesting the current bed is not providing adequate support.",
                "Your dog’s sleeping pattern changes dramatically – excessive sleep or restlessness can both signal a health concern worth investigating with your vet.",
                "Persistent scratching, chewing, or skin irritation that worsens around bedtime may indicate an allergy to bed materials.",
            ]

    elif cluster == "Indoor Cats":
        if "exercise" in title_lower or "active" in title_lower:
            return [
                "Your cat becomes increasingly lethargic and shows no interest in toys, play, or interaction – this may signal illness rather than laziness.",
                "You notice rapid weight gain despite regular play sessions, which warrants a veterinary check for thyroid or metabolic issues.",
                "Your cat pants or breathes heavily during mild exercise, which is abnormal for cats and requires immediate veterinary attention.",
                "Sudden aggression during play or unprovoked attacks on household members may indicate pain or neurological issues.",
            ]
        elif "stress" in title_lower or "anxiety" in title_lower or "behavio" in title_lower:
            return [
                "Over-grooming has progressed to bald patches or skin lesions that could become infected without veterinary intervention.",
                "Your cat stops eating for more than 24 hours, which can lead to hepatic lipidosis (fatty liver disease) and requires urgent care.",
                "Inappropriate urination persists despite addressing environmental factors, as it may indicate cystitis or other urinary conditions.",
                "Aggressive behaviour escalates or becomes unpredictable, potentially indicating pain or a neurological issue.",
            ]
        else:
            return [
                "Your indoor cat stops eating or drinking for more than 24 hours – cats can develop liver problems rapidly when they stop eating.",
                "You notice sudden changes in litter tray habits, such as straining, blood in urine, or urinating outside the tray, which require prompt veterinary attention.",
                "Persistent hiding, withdrawal, or loss of interest in activities the cat previously enjoyed may indicate illness or chronic pain.",
                "Rapid weight loss or gain without dietary changes warrants a veterinary check for conditions common in indoor cats such as diabetes or hyperthyroidism.",
            ]
    return []


def get_beginner_recs(title, cluster):
    """Return beginner recommendations paragraph (3-4 sentences)."""
    title_lower = title.lower()

    if cluster == "Dog Beds":
        if "orthopaedic" in title_lower or "joint" in title_lower:
            return "Start with a bed that has at least 7–10 cm of memory foam and a removable, machine-washable cover. Place it in a warm, draught-free spot where your dog already likes to rest. If your dog is reluctant to try it, place a familiar blanket or one of your worn t-shirts on the bed to encourage use. Ask your vet whether additional support such as a heated pad would benefit your dog’s specific condition."
        elif "sizing" in title_lower or "measure" in title_lower or "size" in title_lower:
            return "Measure your dog from nose to tail base while they are lying stretched out in their favourite sleeping position, then add 15–20 cm to each dimension. If your dog curls up to sleep, a round or oval bed slightly larger than their curled size works well. When in doubt between two sizes, always choose the larger option. Keep the receipt so you can exchange if the fit is not right."
        elif "material" in title_lower or "foam" in title_lower:
            return "For a first dog bed, a polyester-filled bed with a removable, machine-washable cover offers the best balance of comfort, hygiene, and affordability. Upgrade to memory foam when your dog reaches their senior years or if a vet recommends extra joint support. Prioritise washability and a waterproof liner over premium filling materials, as hygiene matters more than luxury for everyday use."
        elif "wash" in title_lower or "clean" in title_lower:
            return "Choose a bed with a removable, machine-washable cover and wash it fortnightly on a 30°C cycle with a pet-safe detergent. Vacuum the bed weekly to remove hair and dander between washes. Spot-clean any accidents immediately with an enzymatic cleaner before they set into the fabric. Having a spare cover lets you keep the bed in use whilst one cover is being washed and dried."
        elif "puppy" in title_lower or "puppies" in title_lower:
            return "Start with an affordable, machine-washable bed that you will not mind replacing as your puppy grows. A waterproof liner is essential during house training. Place the bed inside the crate if you are crate training, and always near where the family spends time so your puppy feels included. Expect to upgrade to a larger, more supportive bed once your puppy reaches adult size."
        elif "travel" in title_lower or "portable" in title_lower:
            return "Choose a lightweight, roll-up travel mat that your dog can use at home first to build positive associations before trips. Look for a water-resistant base and a machine-washable top for easy cleaning after outdoor adventures. Pack the travel bed in your car boot permanently so it is always available for spontaneous outings or vet visits."
        elif "senior" in title_lower or "older" in title_lower:
            return "Invest in a memory foam bed with low entry sides so your older dog can step in without strain. Place the bed in the warmest, quietest room of the house and consider adding a non-slip rug underneath if it is on a hard floor. Give your dog several days to adjust to the new bed and use familiar-smelling bedding to ease the transition."
        elif "chew" in title_lower or "destruc" in title_lower or "tough" in title_lower:
            return "Start with an elevated cot-style bed, as these have less accessible fabric and no loose filling for chewers to reach. Supervise your dog with the new bed initially to assess their behaviour before leaving them alone with it. Address the root cause of destructive chewing (boredom, anxiety, teething) alongside providing a durable bed, as no bed alone solves the underlying issue."
        else:
            return "Start with a simple, machine-washable bed that suits your dog’s sleeping style – a bolster bed for dogs that curl up, or a flat mattress for those that sprawl. Measure your dog lying down and add 15–20 cm for comfort. Place the bed in a quiet, draught-free spot near the family, and give your dog a few days to adjust to it before deciding if it is the right choice."

    elif cluster == "Indoor Cats":
        if "exercise" in title_lower or "active" in title_lower or "play" in title_lower:
            return "Begin with two short interactive play sessions per day, around 10–15 minutes each, using a wand toy at dawn and dusk when cats are naturally most active. Add a cat tree or wall-mounted shelves to create vertical climbing opportunities. Rotate toys every few days to maintain novelty. Consistency matters more than intensity – a daily routine of moderate play is far more effective than occasional marathon sessions."
        elif "stress" in title_lower or "anxiety" in title_lower or "behavio" in title_lower:
            return "Ensure your cat has at least one quiet, elevated hiding spot in every room they frequent – even a cardboard box on a shelf works well. Maintain a predictable daily routine for feeding and play, as cats thrive on consistency. Avoid strong scents like air fresheners near their resting areas. If you suspect stress, keep a simple diary of behaviours and triggers to share with your vet."
        elif "enrich" in title_lower or "stimul" in title_lower or "bore" in title_lower:
            return "Start with three simple enrichment additions: a food puzzle for one meal per day, a window perch for visual stimulation, and a daily 10-minute interactive play session. Rotate toys weekly rather than offering everything at once. Scatter a few treats around the house for your cat to ‘hunt’ during the day. Build complexity gradually as your cat gains confidence with each new challenge."
        elif "safe" in title_lower or "proof" in title_lower or "hazard" in title_lower:
            return "Begin by removing all toxic plants (lilies are the most dangerous), securing windows with restrictors, and tucking away electrical cords. Check each room from your cat’s perspective – get down to their level and look for small objects, gaps behind appliances, and accessible medications. Complete one room at a time rather than trying to cat-proof the entire home in a single day."
        elif "health" in title_lower or "weight" in title_lower or "diet" in title_lower or "obes" in title_lower:
            return "Switch from free-feeding to measured meals twice daily, using the indoor cat feeding guidelines on your chosen food’s packaging as a starting point. Weigh your cat monthly on a kitchen scale and track the trend. Add a food puzzle for at least one meal to slow eating and provide mental stimulation. Schedule an annual vet health check even if your cat seems perfectly well."
        else:
            return "Begin with the basics: provide at least one litter tray per cat plus one extra, offer a cat tree or elevated perch, and schedule two 10–15 minute interactive play sessions daily. Keep windows secured with restrictors and remove any toxic houseplants. Register your cat with a local UK veterinary practice and ensure they are microchipped, which is now a legal requirement in England. Build enrichment gradually rather than overwhelming your cat with changes all at once."
    return ""


def get_at_a_glance(title, cluster):
    """Return At a Glance bullet points for the post."""
    title_lower = title.lower()

    if cluster == "Dog Beds":
        if "orthopaedic" in title_lower or "joint" in title_lower:
            return [
                "Orthopaedic beds use high-density memory foam (30+ kg/m³) to support joints and relieve pressure points",
                "Ideal for senior dogs, large breeds, and any dog recovering from surgery or managing arthritis",
                "Look for at least 7–10 cm of foam depth with a removable, washable cover and waterproof liner",
                "Placement matters – position the bed in a warm, draught-free location away from direct heat sources",
            ]
        elif "sizing" in title_lower or "measure" in title_lower or "size" in title_lower:
            return [
                "Measure your dog nose-to-tail while lying down and add 15–20 cm to each dimension",
                "Match bed shape to sleeping style: bolster beds for curlers, flat mattresses for sprawlers",
                "Check internal sleeping area dimensions, not just the outer product measurements",
                "When choosing between two sizes, always go larger for comfort and future-proofing",
            ]
        elif "material" in title_lower or "foam" in title_lower:
            return [
                "Memory foam offers the best joint support but varies hugely in quality – check density ratings",
                "Polyester fill is affordable, machine-washable, and suitable for most healthy dogs",
                "Fabric durability matters as much as filling – look for high-denier or ripstop options for active dogs",
                "A waterproof liner between cover and foam extends bed life and simplifies cleaning",
            ]
        elif "wash" in title_lower or "clean" in title_lower:
            return [
                "Wash removable covers fortnightly on a 30°C cycle with pet-safe, fragrance-free detergent",
                "Never machine-wash foam inserts – spot-clean with a damp cloth and enzymatic cleaner instead",
                "Vacuum the bed weekly to remove hair, dander, and dust mites between full washes",
                "Air-dry covers fully before reassembling to prevent mould and mildew growth",
            ]
        elif "puppy" in title_lower or "puppies" in title_lower:
            return [
                "Start with affordable, washable beds you can replace as your puppy grows and teethes",
                "A waterproof liner is essential during house training to protect the bed’s filling",
                "Size the bed for the puppy’s predicted adult weight to avoid frequent replacements",
                "Place the bed inside the crate if crate training to create a positive sleep association",
            ]
        elif "travel" in title_lower or "portable" in title_lower:
            return [
                "Choose a travel bed under 2 kg that packs down compactly for car boots and luggage",
                "Introduce the travel bed at home first so your dog associates it with rest before trips",
                "A water-resistant base is essential for outdoor use on damp or uneven ground",
                "Look for non-slip backing to keep the bed stable on smooth car boot or tent surfaces",
            ]
        elif "senior" in title_lower or "older" in title_lower:
            return [
                "Senior dogs benefit most from memory foam beds with low-entry or step-in sides",
                "Position the bed in the warmest room, away from draughts, and on a non-slip surface",
                "Orthopaedic support becomes essential once joint stiffness, limping, or slow rising appears",
                "Heated pads can provide additional comfort but should be thermostatically controlled for safety",
            ]
        elif "chew" in title_lower or "destruc" in title_lower or "tough" in title_lower:
            return [
                "No dog bed is truly indestructible – focus on high-denier, ripstop, or ballistic nylon fabrics",
                "Elevated cot-style beds are harder to destroy as there is less accessible fabric and no loose filling",
                "Address the root cause of chewing (boredom, anxiety, teething) alongside choosing a durable bed",
                "Supervise your dog with any new bed initially to assess their behaviour before leaving them alone",
            ]
        else:
            return [
                "Choose a bed that matches your dog’s size, sleeping style, and any health requirements",
                "Machine-washable covers and waterproof liners are essential for long-term hygiene",
                "Place the bed in a quiet, draught-free spot where your dog naturally chooses to rest",
                "Upgrade to orthopaedic support as your dog ages or if joint issues are diagnosed",
            ]

    elif cluster == "Indoor Cats":
        if "exercise" in title_lower or "active" in title_lower or "play" in title_lower:
            return [
                "Indoor cats need at least 20–30 minutes of active play daily to maintain a healthy weight",
                "Interactive wand toys mimic prey and provide the most effective exercise and mental stimulation",
                "Vertical spaces (cat trees, shelves) encourage climbing and help cats burn energy naturally",
                "Schedule play sessions at dawn and dusk to align with a cat’s natural activity peaks",
            ]
        elif "stress" in title_lower or "anxiety" in title_lower or "behavio" in title_lower:
            return [
                "Common stress signs include over-grooming, hiding, appetite changes, and inappropriate urination",
                "Provide at least one safe, elevated hiding spot per cat in every room they frequent",
                "Maintain consistent daily routines for feeding, play, and litter tray cleaning",
                "Synthetic pheromone diffusers (such as Feliway) can help reduce environmental stress",
            ]
        elif "enrich" in title_lower or "stimul" in title_lower or "bore" in title_lower:
            return [
                "Enrichment combines physical activity, mental challenges, and sensory stimulation in the home",
                "Rotate toys and activities weekly to prevent habituation and maintain your cat’s interest",
                "Food puzzles turn mealtimes into mental exercise, slowing eating and reducing boredom",
                "Distribute enrichment across multiple rooms so your cat has reasons to move through the home",
            ]
        elif "safe" in title_lower or "proof" in title_lower or "hazard" in title_lower:
            return [
                "Remove all toxic plants (especially lilies), secure windows with restrictors, and tuck away cords",
                "Check each room from cat-level height to spot hazards like small objects and gaps behind appliances",
                "Store all human medications securely – paracetamol is lethal to cats even in tiny doses",
                "Microchipping is now a legal requirement for cats in England as of June 2024",
            ]
        elif "health" in title_lower or "weight" in title_lower or "diet" in title_lower or "obes" in title_lower:
            return [
                "Indoor cats typically need 20–30% fewer calories than outdoor cats due to lower activity levels",
                "Use measured meals instead of free-feeding to prevent gradual weight gain",
                "Monitor body condition monthly – you should be able to feel ribs easily without pressing firmly",
                "Annual veterinary check-ups are essential even for cats that appear perfectly healthy",
            ]
        else:
            return [
                "Indoor cats live longer on average but require deliberate enrichment to stay mentally healthy",
                "Provide one litter tray per cat plus one extra, each in a separate quiet location",
                "Daily interactive play and vertical climbing opportunities are non-negotiable for indoor wellbeing",
                "Register with a UK vet, keep vaccinations current, and ensure your cat is microchipped",
            ]
    return []


def get_key_takeaways(title, cluster):
    """Return Key Takeaways bullet points."""
    title_lower = title.lower()

    if cluster == "Dog Beds":
        if "orthopaedic" in title_lower or "joint" in title_lower:
            return [
                "Choose orthopaedic beds with at least 10 cm of high-density memory foam for genuine joint support",
                "Measure your dog lying stretched out and add 15–20 cm to each dimension for the correct size",
                "Wash covers fortnightly to maintain hygiene and reduce allergens around a vulnerable dog",
                "Place the bed away from draughts and direct heat sources for optimal comfort",
            ]
        elif "sizing" in title_lower or "measure" in title_lower or "size" in title_lower:
            return [
                "Always measure your dog in their natural sleeping position, not while standing",
                "Add at least 15–20 cm to nose-to-tail length for comfortable movement during sleep",
                "Match bed shape to your dog’s sleeping style for the best fit and usage",
                "Keep receipts and check return policies in case the first size is not right",
            ]
        elif "material" in title_lower or "foam" in title_lower:
            return [
                "Foam density (measured in kg/m³) is the most reliable indicator of quality and longevity",
                "Washable covers and waterproof liners matter more than premium filling for daily practicality",
                "Match material choice to your dog’s life stage, health needs, and chewing behaviour",
                "Check for safety certifications like CertiPUR when choosing foam-based beds",
            ]
        elif "wash" in title_lower or "clean" in title_lower:
            return [
                "Wash covers fortnightly and vacuum the bed weekly to maintain a healthy sleeping environment",
                "Use a 30°C cycle with pet-safe, fragrance-free detergent to protect fabrics and your dog’s skin",
                "Never machine-wash foam inserts – spot-clean only to preserve their structure and support",
                "Keep a spare cover so the bed is always available during washing and drying cycles",
            ]
        else:
            return [
                "Choose a bed based on your dog’s measured size, sleeping style, and any health requirements",
                "Prioritise washability and a waterproof liner for long-term hygiene and convenience",
                "Place the bed in a quiet, draught-free spot and give your dog time to adjust to it",
                "Upgrade bedding as your dog’s needs change with age, health, and seasonal conditions",
            ]

    elif cluster == "Indoor Cats":
        if "exercise" in title_lower or "active" in title_lower or "play" in title_lower:
            return [
                "Commit to at least two interactive play sessions daily, 10–15 minutes each, at dawn and dusk",
                "Combine horizontal running games with vertical climbing opportunities for full-body exercise",
                "Rotate toys weekly and always end sessions with a ‘catch’ to prevent frustration",
                "Monitor your cat’s weight monthly to ensure exercise levels are maintaining a healthy condition",
            ]
        elif "stress" in title_lower or "anxiety" in title_lower or "behavio" in title_lower:
            return [
                "Learn to recognise subtle stress signals before they escalate into serious health or behavioural issues",
                "Provide multiple safe retreats, consistent routines, and respect your cat’s need for personal space",
                "In multi-cat homes, ensure each cat has separate access to food, water, litter, and resting spots",
                "Consult a veterinary behaviourist if stress-related problems persist despite environmental changes",
            ]
        elif "enrich" in title_lower or "stimul" in title_lower or "bore" in title_lower:
            return [
                "Effective enrichment combines physical, mental, and sensory stimulation across multiple rooms",
                "Rotate toys and activities on a weekly schedule to maintain novelty and engagement",
                "Food puzzles are one of the easiest and most effective enrichment tools for indoor cats",
                "Build enrichment complexity gradually, allowing your cat to master each level before advancing",
            ]
        else:
            return [
                "Indoor cats require deliberate daily enrichment including play, climbing, and mental stimulation",
                "Follow the litter tray rule: one per cat plus one extra, each in a separate quiet location",
                "Schedule annual veterinary check-ups and keep microchipping and vaccinations current",
                "Monitor weight, behaviour, and litter habits closely – indoor cats hide illness well",
            ]
    return []


# ─── Block builders ───────────────────────────────────────────────────────

def build_glossary_block(terms):
    items = "\n".join([f'<li>{t} – {d}</li>' for t, d in terms])
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#f8fafc"}},"border":{{"radius":"6px","width":"1px","color":"#e2e8f0"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#e2e8f0;border-width:1px;border-radius:6px;background-color:#f8fafc;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">Key Terms</h4>
<!-- /wp:heading -->
<!-- wp:list -->
<ul class="wp-block-list">{items}</ul>
<!-- /wp:list -->
</div>
<!-- /wp:group -->'''


def build_mistakes_block(mistakes):
    items = "\n".join([f'<li>{m}</li>' for m in mistakes])
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#fef2f2"}},"border":{{"radius":"6px","width":"1px","color":"#fecaca"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#fecaca;border-width:1px;border-radius:6px;background-color:#fef2f2;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">Common Mistakes to Avoid</h4>
<!-- /wp:heading -->
<!-- wp:list -->
<ul class="wp-block-list">{items}</ul>
<!-- /wp:list -->
</div>
<!-- /wp:group -->'''


def build_seek_help_block(items_list):
    items = "\n".join([f'<li>{i}</li>' for i in items_list])
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#fffbeb"}},"border":{{"radius":"6px","width":"1px","color":"#fde68a"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#fde68a;border-width:1px;border-radius:6px;background-color:#fffbeb;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">When to Seek Professional Help</h4>
<!-- /wp:heading -->
<!-- wp:list -->
<ul class="wp-block-list">{items}</ul>
<!-- /wp:list -->
</div>
<!-- /wp:group -->'''


def build_beginner_block(text):
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#eff6ff"}},"border":{{"radius":"6px","width":"1px","color":"#bfdbfe"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#bfdbfe;border-width:1px;border-radius:6px;background-color:#eff6ff;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">Beginner Recommendations</h4>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>{text}</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->'''


def build_at_a_glance_block(bullets):
    items = "\n".join([f'<li>{b}</li>' for b in bullets])
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#eef2ff"}},"border":{{"radius":"6px","width":"1px","color":"#c7d2fe"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"20px","bottom":"20px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#c7d2fe;border-width:1px;border-radius:6px;background-color:#eef2ff;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">At a Glance</h4>
<!-- /wp:heading -->
<!-- wp:list -->
<ul class="wp-block-list">{items}</ul>
<!-- /wp:list -->
</div>
<!-- /wp:group -->'''


def build_key_takeaways_block(bullets):
    items = "\n".join([f'<li>{b}</li>' for b in bullets])
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


# ─── API helpers ──────────────────────────────────────────────────────────

def fetch_post(post_id):
    """Fetch raw content for a post. Retry up to 3 times."""
    url = f"{BASE}/{post_id}?context=edit"
    for attempt in range(3):
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True, timeout=30
        )
        try:
            data = json.loads(result.stdout)
            if "id" in data:
                return data
        except json.JSONDecodeError:
            pass
        print(f"  Retry {attempt+1} for post {post_id}...")
        time.sleep(3)
    return None


def update_post(post_id, content):
    """Update post content via REST API."""
    payload = json.dumps({"content": content})
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(payload)
        tmp_path = f.name
    try:
        url = f"{BASE}/{post_id}"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-d", f"@{tmp_path}",
             "-H", "Content-Type: application/json",
             "-X", "POST", url],
            capture_output=True, text=True, timeout=60
        )
        try:
            data = json.loads(result.stdout)
            if data.get("id") == post_id:
                return True
            else:
                print(f"  Update error for {post_id}: {result.stdout[:300]}")
                return False
        except json.JSONDecodeError:
            print(f"  JSON decode error on update for {post_id}: {result.stdout[:300]}")
            return False
    finally:
        os.unlink(tmp_path)


# ─── Trust footer detection ──────────────────────────────────────────────

def find_trust_footer_position(content):
    """Find the position of the editorial standards trust footer."""
    # Look for common trust footer patterns
    patterns = [
        r'<hr class="wp-block-separator[^"]*"[^/]*/>\s*\n\s*<h3[^>]*>About Our Editorial Standards</h3>',
        r'<!-- wp:separator.*?-->.*?<!-- /wp:separator -->\s*\n.*?About Our Editorial Standards',
        r'<hr class="wp-block-separator',
        r'About Our Editorial Standards',
    ]
    for pat in patterns:
        m = re.search(pat, content, re.DOTALL)
        if m:
            # Return the start of this match
            return m.start()

    # Also look for affiliate disclosure block that often precedes trust footer
    m = re.search(r'affiliate disclosure', content, re.IGNORECASE)
    if m:
        # Go back to find the start of the containing block
        # Look for the nearest preceding <!-- wp:group or <div
        before = content[:m.start()]
        last_group = before.rfind('<!-- wp:group')
        if last_group >= 0:
            return last_group

    return None


def find_first_paragraph_end(content):
    """Find position after the first paragraph for At a Glance insertion."""
    # Look for the end of the first substantial paragraph
    # Skip quick-answer paragraphs
    m = re.search(r'<!-- /wp:paragraph -->', content)
    if m:
        return m.end()
    m = re.search(r'</p>', content)
    if m:
        return m.end()
    return 0


# ─── Main processing ─────────────────────────────────────────────────────

def process_post(post_id, cluster):
    """Process a single post, adding all missing blocks."""
    print(f"\n{'='*60}")
    print(f"Processing post {post_id} ({cluster})")

    data = fetch_post(post_id)
    if not data:
        print(f"  FAILED to fetch post {post_id}")
        return {
            "id": post_id, "title": "FETCH_FAILED", "cluster": cluster,
            "glossary_added": "no", "common_mistakes_added": "no",
            "when_to_seek_help_added": "no", "beginner_recs_added": "no",
            "at_a_glance_added": "no", "key_takeaways_added": "no",
            "status": "fetch_failed"
        }

    title = data.get("title", {}).get("raw", "Unknown")
    content = data.get("content", {}).get("raw", "")
    print(f"  Title: {title}")
    print(f"  Content length: {len(content)}")

    # Check what already exists
    has_glossary = "Key Terms" in content
    has_mistakes = "Common Mistakes" in content
    has_seek_help = "When to Seek Professional Help" in content
    has_beginner = "Beginner Recommendations" in content
    has_at_glance = bool(re.search(r'At a Glance', content))
    has_takeaways = "Key Takeaways" in content

    print(f"  Existing: glossary={has_glossary}, mistakes={has_mistakes}, seek_help={has_seek_help}, "
          f"beginner={has_beginner}, at_glance={has_at_glance}, takeaways={has_takeaways}")

    # Track what we add
    added = {
        "glossary_added": "already_exists" if has_glossary else "no",
        "common_mistakes_added": "already_exists" if has_mistakes else "no",
        "when_to_seek_help_added": "already_exists" if has_seek_help else "no",
        "beginner_recs_added": "already_exists" if has_beginner else "no",
        "at_a_glance_added": "already_exists" if has_at_glance else "no",
        "key_takeaways_added": "already_exists" if has_takeaways else "no",
    }

    modified = False

    # ── At a Glance (after first paragraph) ──
    if not has_at_glance:
        bullets = get_at_a_glance(title, cluster)
        if bullets:
            block = build_at_a_glance_block(bullets)
            # Insert after first paragraph
            pos = find_first_paragraph_end(content)
            if pos > 0:
                content = content[:pos] + "\n\n" + block + "\n\n" + content[pos:]
                added["at_a_glance_added"] = "yes"
                modified = True
                print(f"  + Added At a Glance after position {pos}")

    # ── Build blocks to insert before trust footer ──
    # ORDER: Common Mistakes ... When to Seek Help ... Beginner Recommendations ... Key Terms ... Key Takeaways
    blocks_to_insert = []

    if not has_mistakes:
        mistakes = get_common_mistakes(title, cluster)
        if mistakes:
            blocks_to_insert.append(("common_mistakes_added", build_mistakes_block(mistakes)))

    if not has_seek_help:
        help_items = get_when_to_seek_help(title, cluster)
        if help_items:
            blocks_to_insert.append(("when_to_seek_help_added", build_seek_help_block(help_items)))

    if not has_beginner:
        rec_text = get_beginner_recs(title, cluster)
        if rec_text:
            blocks_to_insert.append(("beginner_recs_added", build_beginner_block(rec_text)))

    if not has_glossary:
        terms = get_glossary_terms(title, cluster)
        if terms:
            blocks_to_insert.append(("glossary_added", build_glossary_block(terms)))

    if not has_takeaways:
        takeaways = get_key_takeaways(title, cluster)
        if takeaways:
            blocks_to_insert.append(("key_takeaways_added", build_key_takeaways_block(takeaways)))

    if blocks_to_insert:
        # Find trust footer position
        footer_pos = find_trust_footer_position(content)
        if footer_pos:
            combined = "\n\n".join([b[1] for b in blocks_to_insert])
            content = content[:footer_pos] + "\n\n" + combined + "\n\n" + content[footer_pos:]
            for key, _ in blocks_to_insert:
                added[key] = "yes"
            modified = True
            print(f"  + Inserted {len(blocks_to_insert)} blocks before trust footer at position {footer_pos}")
        else:
            # Fallback: insert before the last paragraph or at end
            # Try to find key takeaways block if it exists and insert before it
            # Or just append before the very end
            combined = "\n\n".join([b[1] for b in blocks_to_insert])
            content = content + "\n\n" + combined
            for key, _ in blocks_to_insert:
                added[key] = "yes"
            modified = True
            print(f"  + Appended {len(blocks_to_insert)} blocks at end (no trust footer found)")

    if modified:
        time.sleep(DELAY)
        success = update_post(post_id, content)
        if success:
            print(f"  SUCCESS: Updated post {post_id}")
            added["status"] = "updated"
        else:
            print(f"  FAILED: Could not update post {post_id}")
            added["status"] = "update_failed"
    else:
        print(f"  SKIPPED: All blocks already exist")
        added["status"] = "no_changes_needed"

    return {
        "id": post_id,
        "title": title,
        "cluster": cluster,
        **added,
    }


def main():
    print("=" * 70)
    print("Phase 10AR/10AS/10AT/10AU – Dog Beds + Indoor Cats Cluster Rescue")
    print("=" * 70)

    all_posts = [(pid, "Dog Beds") for pid in DOG_BEDS_IDS] + \
                [(pid, "Indoor Cats") for pid in INDOOR_CATS_IDS]

    results = []
    total = len(all_posts)

    for i, (post_id, cluster) in enumerate(all_posts):
        print(f"\n[{i+1}/{total}] Processing {cluster} post {post_id}")
        result = process_post(post_id, cluster)
        results.append(result)
        if i < total - 1:
            time.sleep(DELAY)

    # Write CSV log
    fieldnames = ["id", "title", "cluster", "glossary_added", "common_mistakes_added",
                  "when_to_seek_help_added", "beginner_recs_added", "at_a_glance_added",
                  "key_takeaways_added", "status"]
    with open(LOG_PATH, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n{'='*70}")
    print(f"COMPLETE. Processed {total} posts. Log: {LOG_PATH}")

    # Summary
    updated = sum(1 for r in results if r["status"] == "updated")
    skipped = sum(1 for r in results if r["status"] == "no_changes_needed")
    failed = sum(1 for r in results if "fail" in r["status"])
    print(f"Updated: {updated}, Skipped (already complete): {skipped}, Failed: {failed}")

    # Per-block summary
    for field in ["glossary_added", "common_mistakes_added", "when_to_seek_help_added",
                  "beginner_recs_added", "at_a_glance_added", "key_takeaways_added"]:
        yes_count = sum(1 for r in results if r.get(field) == "yes")
        exist_count = sum(1 for r in results if r.get(field) == "already_exists")
        print(f"  {field}: added={yes_count}, already_existed={exist_count}")


if __name__ == "__main__":
    main()
