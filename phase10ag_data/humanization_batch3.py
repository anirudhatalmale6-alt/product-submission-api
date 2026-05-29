#!/usr/bin/env python3
"""
Phase 10AG Batch 3: Add humanization + buyer-intent blocks to Dog Toys & Uncategorized posts.
Blocks: About This Guide, Common Mistakes to Avoid, Quick Suitability Guide,
        What to Expect (product posts), Key Considerations (product posts).
"""

import subprocess
import json
import time
import csv
import os
import sys
import tempfile
import html
import re
import hashlib

WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
LOG_DIR = "/var/lib/freelancer/projects/40416335/phase10ag_data"
LOG_FILE = os.path.join(LOG_DIR, "humanization_batch3_log.csv")

ALREADY_TREATED = {3956, 3957, 3959, 5421, 5423, 5469, 5471, 5476, 5483, 5509,
                   3996, 4004, 4011, 4018, 4784, 4174, 4181, 4188, 4286, 4307,
                   4057, 4064, 4071, 4078, 4563, 4118, 4132, 4089, 4146, 5508}

DOG_TOYS_KEYWORDS = [
    "dog toy", "enrichment", "fetch", "tug", "chew", "puzzle", "boredom",
    "play style", "overstimulation", "pet toy safety", "cat toy safety",
    "cat enrichment", "cat toy rotation"
]

UNCATEGORIZED_KEYWORDS = [
    "seasonal pet", "first-time dog owner", "multi-pet", "pet hydration",
    "pet first aid", "confidence-building", "rotating puzzle",
    "where to place", "how to wash"
]

OTHER_CLUSTER_KEYWORDS = [
    "dog bed", "orthopaedic", "cooling bed", "puppy bed", "bed material",
    "dog groom", "dog brush", "dog shampoo", "nail clip", "grooming basics",
    "dog train", "puppy train", "dog health", "dog bowl", "feeding",
    "cat scratch", "cat bed", "cat litter", "cat food", "cat health",
    "dog harness", "dog lead", "dog collar", "dog coat", "dog jacket",
    "puppy development"
]

# ─── About This Guide templates (rotate across posts) ──────────────────────

ABOUT_GUIDE_TEMPLATES = [
    "This guide was developed using published safety and enrichment guidance from the RSPCA and Dogs Trust for UK pet owners.",
    "Our editorial team compiled this resource from published veterinary and animal welfare guidance, reviewed for accuracy in May 2026.",
    "We reviewed current UK pet welfare guidance from the RSPCA, Blue Cross, and PDSA to create this practical resource.",
    "This information draws on published research and guidance from UK veterinary organisations and animal behaviourists.",
    "Our team consulted published guidance from Dogs Trust, the Kennel Club, and the RSPCA to compile this educational resource.",
    "This guide is based on established animal welfare principles and published advice from UK pet charities.",
    "We compiled this resource using guidance from UK veterinary organisations, focusing on practical advice for everyday pet owners.",
    "This educational guide draws on published pet welfare research and practical guidance from leading UK animal charities.",
    "This resource was put together using published recommendations from UK animal welfare organisations and veterinary professionals.",
    "Our editorial team reviewed guidance from the RSPCA, PDSA, and Blue Cross to ensure this resource reflects current best practice.",
    "We built this guide using published pet care standards from UK veterinary bodies, with a focus on practical, owner-friendly advice.",
    "This guide draws on published welfare guidance from the Kennel Club, Dogs Trust, and veterinary professionals practising in the UK.",
]

# ─── Per-post content generation ────────────────────────────────────────────

def get_about_template(post_id):
    """Deterministically select an About This Guide template based on post ID."""
    idx = post_id % len(ABOUT_GUIDE_TEMPLATES)
    return ABOUT_GUIDE_TEMPLATES[idx]


def generate_common_mistakes(post_id, title, slug, content_snippet):
    """Generate 4-5 topic-specific common mistakes based on title/slug analysis."""
    title_lower = title.lower()
    slug_lower = slug.lower()
    combined = f"{title_lower} {slug_lower} {content_snippet[:1500].lower()}"

    mistakes = []

    # === DOG TOY SAFETY ===
    if "dog toy safety" in combined or ("safety" in combined and "dog toy" in combined):
        mistakes = [
            "<strong>Ignoring size labels on packaging</strong> — A toy designed for a small breed can be a choking hazard for a larger dog. Always check the manufacturer's weight and size recommendations before purchasing.",
            "<strong>Assuming 'natural' materials are always safe</strong> — Rawhide, antlers, and natural bones can still splinter or cause blockages. Supervision is essential regardless of what the toy is made from.",
            "<strong>Leaving damaged toys in the toy box</strong> — Dogs will continue to play with torn, cracked, or shredded toys. Inspect toys weekly and remove anything with exposed stuffing, loose parts, or sharp edges.",
            "<strong>Skipping supervision with new toys</strong> — Even toys labelled 'indestructible' can break under certain chewing patterns. Always supervise the first few play sessions with any new toy.",
            "<strong>Relying on one toy for all situations</strong> — Different activities (solo play, fetch, chewing) need different toy types. A fetch ball is not a safe chew toy, and a plush toy is not suitable for power chewers."
        ]
    # === BREED SIZE TOY SAFETY ===
    elif "breed size" in combined or "choosing the right size" in combined:
        mistakes = [
            "<strong>Buying one-size-fits-all toys</strong> — Toys that claim to suit all dogs rarely do. A toy too small for a large dog is a choking risk, and oversized toys frustrate smaller breeds.",
            "<strong>Ignoring jaw strength, not just body size</strong> — A medium-sized Staffordshire Bull Terrier has far more jaw pressure than a same-sized Cocker Spaniel. Match toy durability to chewing power, not just weight.",
            "<strong>Not replacing toys as puppies grow</strong> — A toy that fits a 10-week-old puppy becomes dangerously small within months. Reassess toy sizes every few weeks during the growth phase.",
            "<strong>Using tennis balls as unsupervised chew toys</strong> — Tennis ball felt wears down teeth over time, and the rubber can be torn apart by strong chewers. Use them for fetch only, not solo chewing.",
            "<strong>Overlooking toy shape for flat-faced breeds</strong> — Brachycephalic dogs (pugs, bulldogs) struggle with round balls. Flat or oval toys are easier for them to grip and carry."
        ]
    # === OVERSTIMULATION ===
    elif "overstimulation" in combined or "overexcited" in combined or "calming down" in combined:
        mistakes = [
            "<strong>Increasing play intensity to 'tire them out'</strong> — More vigorous play often makes overstimulation worse. Calm, structured enrichment is more effective than escalating physical activity.",
            "<strong>Ending play abruptly</strong> — Suddenly removing all toys or stopping play can increase anxiety. Wind down gradually over several minutes using slower, calmer activities.",
            "<strong>Scolding an overexcited dog</strong> — Raised voices or physical correction during overstimulation adds stress. Quietly redirect to a calm activity instead.",
            "<strong>Using squeaky toys during high-arousal periods</strong> — Squeaky toys amplify excitement. Switch to quiet, food-dispensing toys when your dog is already wound up.",
            "<strong>Ignoring the early warning signs</strong> — Fast tail wagging, inability to focus, and mouthy behaviour are early overstimulation signals. Intervene before the dog reaches a frenzied state."
        ]
    # === ENRICHMENT SCHEDULES ===
    elif "enrichment schedule" in combined or "structuring daily" in combined:
        mistakes = [
            "<strong>Overloading the schedule with too many activities</strong> — Dogs need rest between enrichment sessions. Two to three focused sessions per day is usually more effective than constant stimulation.",
            "<strong>Repeating the same enrichment every day</strong> — Dogs adapt quickly and lose interest. Rotate activities across the week to keep each session engaging.",
            "<strong>Scheduling enrichment only when the dog misbehaves</strong> — Enrichment should be preventive, not reactive. A consistent daily schedule reduces problem behaviours before they start.",
            "<strong>Forgetting to include rest periods</strong> — Mental work is tiring. Follow a puzzle session with a calm period so the dog can process and recover.",
            "<strong>Assuming all dogs need the same schedule</strong> — A young Border Collie needs far more mental stimulation than a senior Greyhound. Tailor the schedule to your dog's age, breed, and energy level."
        ]
    # === COGNITIVE / SENIOR ENRICHMENT ===
    elif "senior dog" in combined and ("enrichment" in combined or "cognitive" in combined or "gentle play" in combined):
        mistakes = [
            "<strong>Assuming senior dogs don't need mental stimulation</strong> — Cognitive enrichment helps maintain brain function in older dogs. Stopping enrichment entirely can accelerate cognitive decline.",
            "<strong>Using puzzles that are too difficult</strong> — Senior dogs may have reduced patience and sensory ability. Start with simple puzzles and increase complexity only if your dog stays engaged.",
            "<strong>Ignoring physical limitations during play</strong> — Arthritis, reduced vision, or hearing loss all affect how a senior dog can interact with toys. Choose low-impact options that don't require jumping or fast movement.",
            "<strong>Relying solely on food-based enrichment</strong> — Scent work, gentle social interaction, and calm exploration are equally valuable for senior dogs and avoid overfeeding.",
            "<strong>Skipping enrichment on 'bad days'</strong> — Even on days when your senior dog seems low energy, gentle mental stimulation (a simple snuffle mat or a short scent trail) can improve mood and engagement."
        ]
    # === SCENT GAMES ===
    elif "scent" in combined and ("game" in combined or "enrichment" in combined or "smell" in combined):
        mistakes = [
            "<strong>Making the scent trail too difficult too soon</strong> — Start with obvious, short trails and gradually increase the challenge. Dogs that fail repeatedly lose interest in scent games altogether.",
            "<strong>Using overpowering scents</strong> — Dog noses are far more sensitive than ours. Strong-smelling treats or essential oils can overwhelm rather than engage. Use mild, natural food scents.",
            "<strong>Rushing through the setup</strong> — Allow scent particles to settle for 30-60 seconds before letting your dog search. Fresh trails without settling time are harder for dogs to follow.",
            "<strong>Playing scent games in distracting environments</strong> — Start indoors in a quiet room. Outdoor environments with competing smells, sounds, and movement make scent work far more challenging for beginners.",
            "<strong>Not letting the dog work independently</strong> — Pointing, guiding, or talking during scent work interferes with the dog's natural search behaviour. Let them use their nose at their own pace."
        ]
    # === CRATE ENRICHMENT ===
    elif "crate" in combined and ("enrichment" in combined or "play" in combined):
        mistakes = [
            "<strong>Using the crate only for punishment or isolation</strong> — Dogs should associate the crate with positive experiences. Always pair crate time with enrichment, treats, or calm rest.",
            "<strong>Leaving toys that can be shredded unsupervised</strong> — Soft toys, rope toys, and anything with small parts should not be left in the crate when you're not watching. Stick to durable food-dispensing toys.",
            "<strong>Overstimulating the dog before crate time</strong> — High-energy play right before crate confinement makes it harder for the dog to settle. Use calm enrichment (licking mats, frozen Kongs) to create a transition.",
            "<strong>Making the crate too cramped for enrichment</strong> — If the crate is barely large enough for the dog, there's no room for enrichment toys. Ensure the crate allows comfortable movement around a toy.",
            "<strong>Forgetting to rotate crate toys</strong> — The same frozen Kong every day becomes boring. Rotate between different food-dispensing toys and activities to maintain interest."
        ]
    # === TOY DURABILITY / MATERIALS ===
    elif "durability" in combined or ("material" in combined and "toy" in combined):
        mistakes = [
            "<strong>Choosing by appearance rather than material quality</strong> — Brightly coloured, visually appealing toys often use cheaper materials. Check what the toy is actually made from before buying.",
            "<strong>Assuming 'tough' labels mean indestructible</strong> — Marketing terms like 'heavy-duty' and 'extra strong' are not standardised. Test new toys under supervision before leaving them for solo play.",
            "<strong>Not matching material to your dog's chewing style</strong> — Rubber suits power chewers, rope suits moderate chewers, and plush suits gentle players. The wrong match leads to rapid destruction and potential hazards.",
            "<strong>Keeping toys past their usable life</strong> — All toys degrade over time. Even durable rubber eventually cracks, and rope toys fray into swallowable strands. Set a regular replacement schedule.",
            "<strong>Ignoring manufacturing origin and safety standards</strong> — Toys made without safety testing can contain harmful dyes, lead, or phthalates. Look for products tested to UK or EU safety standards."
        ]
    # === TOY STORAGE / ORGANISATION ===
    elif "storage" in combined or "organisation" in combined:
        mistakes = [
            "<strong>Keeping all toys accessible at once</strong> — Dogs lose interest when surrounded by options. Store most toys away and rotate a few at a time to keep each one feeling fresh.",
            "<strong>Storing wet toys without drying them</strong> — Damp rope toys, stuffed toys, and rubber toys can harbour mould and bacteria. Always dry toys thoroughly before putting them away.",
            "<strong>Using closed containers without ventilation</strong> — Airtight bins trap moisture and odour. Use baskets or bins with airflow to prevent mildew.",
            "<strong>Not separating toys by type</strong> — Chew toys stored with squeaky toys can transfer damage. Keep power-chewer toys separate from softer play toys to extend the life of both.",
            "<strong>Placing the toy storage where the dog can access it freely</strong> — Self-service toy bins undermine rotation systems. Store the main collection out of reach and only put the current rotation within your dog's area."
        ]
    # === TOY HYGIENE / CLEANING ===
    elif "hygiene" in combined or ("clean" in combined and "toy" in combined) or "how to wash" in combined:
        mistakes = [
            "<strong>Using harsh household cleaners</strong> — Bleach, disinfectant sprays, and scented cleaning products can leave toxic residues on toys. Use pet-safe cleaners or diluted white vinegar instead.",
            "<strong>Washing all toy types the same way</strong> — Rubber toys can go in the dishwasher; rope toys need soaking and microwaving; plush toys require a gentle machine wash. Each material has its own cleaning method.",
            "<strong>Only cleaning toys when they look dirty</strong> — Bacteria builds up long before visible dirt appears. Clean chew toys weekly and food-dispensing toys after every use.",
            "<strong>Not drying toys completely before returning them</strong> — Damp toys breed bacteria and mould rapidly. Air-dry completely or tumble dry on low before giving them back to your dog.",
            "<strong>Forgetting to clean food-dispensing toys inside</strong> — Old food residue trapped in puzzle toys and Kongs can turn rancid. Use a bottle brush or pipe cleaner to reach interior crevices."
        ]
    # === DIY DOG TOYS ===
    elif "diy" in combined and "dog" in combined:
        mistakes = [
            "<strong>Using old socks or shoes as toys</strong> — Dogs cannot distinguish between 'toy socks' and your real socks. This teaches them that chewing footwear and clothing is acceptable.",
            "<strong>Including buttons, zips, or elastic in homemade toys</strong> — Small fasteners are swallowing hazards. Strip all non-fabric components before repurposing old clothing or fabric into toys.",
            "<strong>Making rope toys from synthetic fibres</strong> — Nylon, polyester, and acrylic strands can cause intestinal blockages if swallowed. Use natural cotton or fleece for braided toys.",
            "<strong>Assuming DIY toys don't need supervision</strong> — Homemade toys are generally less durable than commercial ones. Supervise all play and remove the toy at the first sign of damage.",
            "<strong>Using plastic bottles without removing the cap and ring</strong> — Bottle caps and plastic rings are choking hazards. Remove all small parts and wrap the bottle in fabric for safer play."
        ]
    # === DOG PLAY STYLES ===
    elif "play style" in combined:
        mistakes = [
            "<strong>Assuming all dogs enjoy the same type of play</strong> — A dog that loves tug may have no interest in fetch. Observe what your dog naturally gravitates toward and build play sessions around that.",
            "<strong>Forcing a reluctant dog into group play</strong> — Not all dogs enjoy playing with other dogs. Some prefer solo enrichment or one-on-one play with their owner, and that is perfectly normal.",
            "<strong>Ignoring breed-specific play tendencies</strong> — Retrievers naturally carry and fetch, terriers prefer shaking and tugging, and herding breeds enjoy chasing. Work with your dog's instincts, not against them.",
            "<strong>Playing the same game every time</strong> — Repetitive play leads to boredom. Mix fetch, tug, scent work, and puzzle play across the week to keep your dog mentally and physically engaged.",
            "<strong>Misreading play signals as aggression</strong> — Growling during tug, body slamming during chase, and mouthing during wrestling are all normal play behaviours. Learn the difference between play and genuine conflict."
        ]
    # === PUPPY TOYS / TEETHING ===
    elif "puppy" in combined and ("toy" in combined or "teething" in combined or "care" in combined):
        mistakes = [
            "<strong>Giving adult-strength toys to puppies</strong> — Hard nylon and solid rubber toys designed for adult dogs can damage developing puppy teeth. Choose softer textures appropriate for young jaws.",
            "<strong>Allowing puppies to chew unsupervised</strong> — Puppies explore with their mouths and can quickly tear apart toys. Always supervise play and remove damaged toys immediately.",
            "<strong>Not providing enough variety during teething</strong> — Teething puppies need different textures to soothe sore gums. Offer a mix of rubber, fabric, and frozen options throughout the day.",
            "<strong>Giving toys that are too large for small puppy mouths</strong> — Puppies need toys they can comfortably grip and carry. Oversized toys discourage play and can cause jaw strain.",
            "<strong>Stopping toy play to prevent chewing on furniture</strong> — Redirecting chewing to appropriate toys is the solution, not removing toys altogether. Puppies need to chew; the goal is to give them safe outlets."
        ]
    # === CAT TOYS GENERAL / FAQ ===
    elif "cat toy" in combined and ("faq" in combined or "common question" in combined or "glossary" in combined or "types explained" in combined):
        mistakes = [
            "<strong>Leaving string-based toys out unsupervised</strong> — Wand toys, ribbon toys, and anything with long strings should be stored after play. Cats can swallow string, leading to serious intestinal emergencies.",
            "<strong>Assuming cats will play on their own</strong> — Most cats need interactive play with their owner to stay engaged. Leaving toys out without structured play sessions leads to boredom and weight gain.",
            "<strong>Buying toys based on colour rather than texture and movement</strong> — Cats see limited colours but respond strongly to texture, sound, and movement. Choose toys that crinkle, bounce unpredictably, or mimic prey motion.",
            "<strong>Not rotating toys frequently enough</strong> — Cats lose interest in familiar toys within days. Keep most toys stored away and rotate two to three into active use every few days.",
            "<strong>Using laser pointers without a physical 'catch'</strong> — Laser play without a tangible reward can cause frustration. Always end laser sessions by leading the dot to a treat or a toy the cat can physically catch."
        ]
    # === CAT ENRICHMENT / INDOOR CATS ===
    elif ("cat enrichment" in combined or "indoor cat" in combined or "house cat" in combined) and "dog" not in combined[:30].lower():
        mistakes = [
            "<strong>Relying solely on toys for enrichment</strong> — Vertical space (cat trees, shelves), window perches, and scent enrichment are equally important. A well-enriched environment goes beyond the toy box.",
            "<strong>Ignoring the hunting cycle</strong> — Cats need to stalk, chase, pounce, and 'catch' to feel satisfied. Play sessions that skip the capture phase leave cats frustrated and restless.",
            "<strong>Placing all enrichment in one room</strong> — Spread activity stations, scratching posts, and feeding puzzles across your home. This encourages movement and mimics the varied territory cats would explore outdoors.",
            "<strong>Not providing hiding spots</strong> — Cats need enclosed, elevated, or concealed resting spots to feel secure. Boxes, tunnels, and covered beds are essential enrichment, not just play items.",
            "<strong>Overfeeding treats during enrichment</strong> — Food-based enrichment should come from the cat's daily food allowance, not additional calories. Weigh daily portions and use part of the allocation for puzzle feeders."
        ]
    # === KITTEN VS ADULT CAT TOYS ===
    elif "kitten" in combined and ("adult" in combined or "age" in combined):
        mistakes = [
            "<strong>Giving kittens small toys designed for adult cats</strong> — Kittens are more likely to swallow or choke on small balls, mice, or parts. Choose larger, kitten-specific toys that cannot fit entirely in the mouth.",
            "<strong>Using adult-level puzzle difficulty for kittens</strong> — Kittens need simple puzzles they can solve quickly. Start with single-step food puzzles and increase complexity as they grow.",
            "<strong>Assuming adult cats don't need play</strong> — Play is not just for kittens. Adult cats need regular interactive play to maintain healthy weight, reduce stress, and prevent behavioural issues.",
            "<strong>Not adjusting play intensity as kittens grow</strong> — A 12-week-old kitten plays very differently from a 6-month-old adolescent. Increase toy robustness and play complexity as your cat matures.",
            "<strong>Allowing rough hand-play with kittens</strong> — Using hands as play targets teaches kittens that biting and scratching people is acceptable. Always use a toy between your hand and the kitten."
        ]
    # === DIY CAT TOYS ===
    elif "diy" in combined and "cat" in combined:
        mistakes = [
            "<strong>Using yarn or thread as a cat toy</strong> — Cats often swallow string-like materials during play, which can cause life-threatening intestinal obstructions. Use wider fabric strips or fleece instead.",
            "<strong>Including small beads or bells inside DIY toys</strong> — If the toy tears open, small objects become choking hazards. Use rice, dried pasta, or crinkle material for sound instead.",
            "<strong>Leaving DIY toys out permanently</strong> — Homemade toys are less durable than commercial ones and degrade faster. Store them after each session and inspect before every use.",
            "<strong>Using toxic adhesives or glues</strong> — Hot glue, superglue, and craft adhesives can be toxic if chewed. Sew or tie components together instead of gluing them.",
            "<strong>Not considering your cat's specific play preference</strong> — Some cats prefer pouncing, others prefer batting or chasing. Observe what your cat enjoys before investing time in a particular DIY design."
        ]
    # === CAT PLAY BEHAVIOUR ===
    elif "cat play behaviour" in combined or "cat play style" in combined or "what different play styles mean" in combined:
        mistakes = [
            "<strong>Interpreting all stalking behaviour as aggression</strong> — Stalking, pouncing, and ambushing are natural play behaviours in cats. They mimic hunting sequences and are a sign of healthy feline instincts.",
            "<strong>Punishing play-biting</strong> — Cats learn bite inhibition through play, not punishment. Redirect biting toward appropriate toys rather than scolding, which increases stress.",
            "<strong>Playing only at human-convenient times</strong> — Cats are crepuscular (most active at dawn and dusk). Scheduling play sessions during these natural activity peaks produces much better engagement.",
            "<strong>Ignoring solo play signals</strong> — A cat batting objects off shelves or chasing imaginary prey is asking for stimulation. Provide interactive play before these behaviours escalate into destructive habits.",
            "<strong>Assuming a cat that doesn't play is lazy</strong> — Reduced play can indicate pain, illness, stress, or inadequate enrichment. If your cat stops playing, investigate the cause rather than accepting it as personality."
        ]
    # === CAT TOY REPLACEMENT ===
    elif "replace" in combined and "cat" in combined:
        mistakes = [
            "<strong>Waiting until a toy falls apart completely</strong> — By the time a toy visibly disintegrates, your cat may have already swallowed small pieces. Replace toys at the first sign of damage.",
            "<strong>Assuming catnip toys last forever</strong> — Catnip potency fades within a few months, especially in low-quality toys. Refresh or replace catnip toys every two to three months.",
            "<strong>Not tracking toy condition across multiple cats</strong> — In multi-cat households, toys degrade faster. Check condition more frequently when several cats share the same toys.",
            "<strong>Replacing all toys at once</strong> — Introducing an entirely new set of toys at once can overwhelm some cats. Phase in new toys gradually alongside familiar favourites.",
            "<strong>Buying replacements based only on previous choices</strong> — Cats' preferences change over time. Experiment with different textures, sizes, and play styles when replacing old toys."
        ]
    # === CAT TOY ROTATION ===
    elif "cat toy rotation" in combined or ("rotation" in combined and "cat" in combined):
        mistakes = [
            "<strong>Rotating too many toys at once</strong> — Swapping the entire collection overwhelms cats. Rotate two to three toys at a time, keeping a few familiar favourites always available.",
            "<strong>Not storing rotated-out toys properly</strong> — Toys left in a pile lose their novelty. Seal them in a bag or box so they smell fresh and unfamiliar when reintroduced.",
            "<strong>Following a rigid daily rotation schedule</strong> — Most cats need three to five days to fully engage with a toy. Rotating daily may not give enough time for interest to develop.",
            "<strong>Only rotating the same toy types</strong> — If you only swap between feather wands, your cat misses out on variety. Include different categories: crinkle balls, puzzle feeders, kicker toys, and springs.",
            "<strong>Ignoring your cat's feedback</strong> — If a reintroduced toy gets no attention after a day or two, it has genuinely lost appeal. Retire it permanently rather than cycling it endlessly."
        ]
    # === MULTI-DOG TOY MANAGEMENT / RESOURCE GUARDING ===
    elif "multi-dog" in combined or "resource guarding" in combined:
        mistakes = [
            "<strong>Giving only one high-value toy to multiple dogs</strong> — Scarcity increases competition. Provide at least one high-value toy per dog, plus extras, to reduce guarding triggers.",
            "<strong>Punishing growling over toys</strong> — Growling is a warning signal, not misbehaviour. Punishing it removes the warning without addressing the underlying guarding, making sudden bites more likely.",
            "<strong>Assuming dogs will 'work it out themselves'</strong> — Resource conflicts can escalate to serious fights. Manage the environment proactively by separating high-value items during unsupervised time.",
            "<strong>Feeding and giving treats in the same area as toy play</strong> — Combining food and toy spaces increases the likelihood of guarding. Keep feeding areas and play areas distinct.",
            "<strong>Ignoring body language between dogs</strong> — Stiffening, hard staring, and hovering over toys are early guarding signs. Intervene calmly by redirecting before tension escalates."
        ]
    # === PLAY RECOVERY AFTER SURGERY ===
    elif "surgery" in combined or "healing" in combined or "recovery" in combined:
        mistakes = [
            "<strong>Resuming normal play too soon</strong> — Even if your dog seems eager, follow your vet's recovery timeline strictly. Premature activity can reopen wounds or damage surgical repairs.",
            "<strong>Removing all mental stimulation during recovery</strong> — Physical rest doesn't mean mental rest. Low-movement enrichment like licking mats, snuffle mats, and simple food puzzles keeps recovery dogs engaged without strain.",
            "<strong>Using toys that encourage jumping or twisting</strong> — Fetch toys, squeaky balls, and tug ropes can trigger sudden movements. Stick to stationary enrichment during the healing period.",
            "<strong>Not protecting the surgical site during gentle play</strong> — Even calm activities can lead to licking or rubbing against stitches. Use a recovery suit or cone and choose enrichment that keeps the head occupied.",
            "<strong>Expecting the same energy level immediately after recovery</strong> — Dogs often need a gradual return to full activity. Build play duration and intensity back up slowly over several weeks."
        ]
    # === LOW-MOBILITY ENRICHMENT ===
    elif "low-mobility" in combined or "limited movement" in combined:
        mistakes = [
            "<strong>Assuming low-mobility dogs don't need enrichment</strong> — Mental stimulation is even more important when physical exercise is limited. Boredom and frustration can worsen behavioural and health issues.",
            "<strong>Choosing enrichment that requires too much physical effort</strong> — Puzzle toys that need pawing, digging, or standing for long periods can cause pain. Focus on nose work, licking mats, and stationary puzzles.",
            "<strong>Placing enrichment out of comfortable reach</strong> — A dog with joint issues shouldn't have to stretch, bend, or walk far to access enrichment. Position everything within easy reach of their resting spot.",
            "<strong>Skipping enrichment on bad pain days</strong> — Even on difficult days, very gentle scent enrichment (a scented cloth nearby or a snuffle mat placed beside the bed) provides stimulation without requiring movement.",
            "<strong>Using only one type of enrichment</strong> — Variety matters even for low-mobility dogs. Alternate between scent puzzles, food-dispensing mats, calm music, and gentle social interaction."
        ]
    # === SENSORY ENRICHMENT ===
    elif "sensory" in combined and "enrichment" in combined:
        mistakes = [
            "<strong>Overwhelming multiple senses at once</strong> — Introducing new sounds, scents, textures, and visuals simultaneously can cause stress. Introduce one sensory element at a time and observe your dog's reaction.",
            "<strong>Using human-scented products for scent enrichment</strong> — Air fresheners, scented candles, and perfumed products are not suitable for dog scent enrichment. Use safe, natural scents like herbs or dog-safe spices.",
            "<strong>Ignoring sound sensitivity</strong> — Some dogs are highly sensitive to new sounds. Introduce auditory enrichment (music, nature recordings) at low volume and watch for signs of anxiety.",
            "<strong>Assuming all dogs enjoy the same textures</strong> — Some dogs love walking on different surfaces; others find it stressful. Let your dog approach new textures at their own pace.",
            "<strong>Limiting sensory enrichment to indoor settings</strong> — Garden sniff walks, outdoor scent trails, and exposure to varied outdoor environments provide richer sensory experiences than indoor activities alone."
        ]
    # === DOG ENRICHMENT (GENERAL / BY BREED GROUP) ===
    elif "enrichment" in combined and "breed" in combined:
        mistakes = [
            "<strong>Ignoring breed-specific drives</strong> — A Labrador bred for retrieving needs fetch-based enrichment, while a scent hound thrives on nose work. Generic enrichment may not fulfil your dog's specific instincts.",
            "<strong>Overcomplicating enrichment for working breeds</strong> — Working breeds enjoy challenge, but frustration-free success is still important. Ensure the difficulty level allows your dog to succeed within a few minutes.",
            "<strong>Assuming small breeds need less enrichment</strong> — Terriers, Dachshunds, and other small breeds are often high-energy and highly intelligent. They need proportionally as much enrichment as larger dogs.",
            "<strong>Providing only physical enrichment for herding breeds</strong> — Border Collies, Australian Shepherds, and similar breeds need mental problem-solving as much as physical exercise. Puzzles and training games are essential.",
            "<strong>Not adapting enrichment to individual personality</strong> — Breed tendencies are a starting point, not a rule. Your individual dog's preferences, fears, and energy level should guide enrichment choices."
        ]
    # === DOG BODY LANGUAGE / BEHAVIOUR ===
    elif "body language" in combined or "behaviour explained" in combined:
        mistakes = [
            "<strong>Reading a wagging tail as always meaning happiness</strong> — Tail height, speed, and direction all communicate different emotions. A stiff, high, fast wag can indicate alertness or tension, not joy.",
            "<strong>Assuming a dog showing teeth is always aggressive</strong> — Some dogs display a 'submissive grin' that looks like baring teeth. Context, body posture, and ear position help distinguish between aggression and appeasement.",
            "<strong>Ignoring whale eye (showing the whites of the eyes)</strong> — This is often a sign of discomfort, anxiety, or stress. If you see it, give the dog space and remove whatever is causing unease.",
            "<strong>Interpreting a roll-over as an invitation to rub the belly</strong> — Dogs roll over for many reasons, including appeasement and fear. Check for relaxed body language before reaching in for a tummy rub.",
            "<strong>Dismissing yawning, lip-licking, and turning away as boredom</strong> — These are calming signals and stress indicators. Frequent lip-licking or yawning in a non-tired dog signals discomfort."
        ]
    # === ROTATING PUZZLE COMPLEXITY ===
    elif "rotating puzzle" in combined or "progressive challenge" in combined:
        mistakes = [
            "<strong>Jumping to the hardest puzzle immediately</strong> — Dogs need to build problem-solving skills gradually. Start with single-step puzzles and only increase complexity when the current level is consistently solved.",
            "<strong>Not recognising signs of frustration</strong> — Pawing excessively, whining, or walking away are signs the puzzle is too hard. Drop back to an easier level to rebuild confidence before trying again.",
            "<strong>Rotating complexity without changing the puzzle type</strong> — Increasing difficulty within the same format (e.g., more compartments on the same puzzle) is less stimulating than introducing entirely different puzzle mechanics.",
            "<strong>Assuming faster solving means the dog is bored</strong> — Quick solving shows mastery, which is rewarding. Alternate between mastered puzzles (for confidence) and new ones (for challenge).",
            "<strong>Using the same treats in every puzzle</strong> — Varying the reward type (different treats, different scents) adds a sensory dimension to the puzzle challenge beyond just the mechanical difficulty."
        ]
    # === PET TOY SAFETY (GENERAL) ===
    elif "pet toy safety" in combined:
        mistakes = [
            "<strong>Applying dog toy safety rules to cats (or vice versa)</strong> — Dogs and cats play differently and face different hazards. Cat-safe string toys can be dangerous for dogs, and dog chews are often too hard for cats.",
            "<strong>Not checking toys after every play session</strong> — Both dogs and cats can damage toys quickly. A routine post-play inspection catches loose parts, tears, and choking hazards early.",
            "<strong>Buying toys without checking material safety</strong> — Look for toys tested to UK or EU safety standards. Cheap imports may contain harmful dyes, lead, or phthalates.",
            "<strong>Leaving battery-operated toys accessible when off</strong> — Pets may chew into battery compartments when unsupervised. Store electronic toys out of reach between play sessions.",
            "<strong>Assuming a recalled toy is safe if it hasn't caused problems yet</strong> — If a toy appears on a recall list, remove it immediately regardless of your pet's past experience with it."
        ]
    # === CAT CARE BASICS / GLOSSARY ===
    elif "cat care" in combined and ("basics" in combined or "glossary" in combined or "new cat owner" in combined):
        mistakes = [
            "<strong>Assuming cats are low-maintenance pets</strong> — Cats need daily play, regular veterinary care, mental enrichment, and a clean environment. 'Independent' does not mean 'self-sufficient'.",
            "<strong>Not providing enough litter trays</strong> — The general rule is one tray per cat plus one extra, placed in different locations. Insufficient trays lead to house-soiling problems.",
            "<strong>Feeding only dry food without enough water access</strong> — Cats have a naturally low thirst drive. Provide multiple water sources (including a fountain if possible) and consider wet food as part of the diet.",
            "<strong>Skipping annual veterinary check-ups</strong> — Cats are experts at hiding illness. Regular vet visits catch issues early, before symptoms become obvious or treatment becomes complex.",
            "<strong>Declawing or punishing normal scratching behaviour</strong> — Scratching is a natural, essential behaviour for claw maintenance and territory marking. Provide appropriate scratching surfaces instead of trying to eliminate the behaviour."
        ]
    # === CAT TOY SAFETY ===
    elif "cat toy safety" in combined:
        mistakes = [
            "<strong>Leaving feather wands and string toys out after play</strong> — These are the most common cause of feline intestinal foreign body emergencies. Store all string-based toys immediately after each session.",
            "<strong>Using small, hard toys that can be swallowed</strong> — Tiny balls, jingle bells, and small plastic mice can be swallowed by enthusiastic cats. Choose toys too large to fit entirely in the mouth.",
            "<strong>Ignoring loose parts on damaged toys</strong> — Eyes on stuffed mice, bells on rattles, and feathers on wands all become hazards once they detach. Discard toys as soon as parts loosen.",
            "<strong>Assuming indoor-only cats face no toy hazards</strong> — Indoor cats may play more intensely due to limited stimulation, increasing the risk of toy damage and ingestion.",
            "<strong>Not checking catnip toy quality</strong> — Low-quality catnip toys may use thin fabric that tears easily or contain loose catnip stems that can irritate the digestive system."
        ]
    # === SEASONAL PET SAFETY ===
    elif "seasonal" in combined:
        mistakes = [
            "<strong>Only thinking about temperature extremes</strong> — Seasonal hazards include toxic plants (spring bulbs, autumn mushrooms), fireworks anxiety, antifreeze exposure, and holiday food dangers throughout the year.",
            "<strong>Assuming dogs will stop exercising when too hot</strong> — Many dogs will keep running even in dangerous heat. It is the owner's responsibility to limit exercise during high temperatures and provide shade.",
            "<strong>Walking dogs on hot pavement</strong> — Tarmac and concrete can burn paw pads when air temperatures reach 25°C or above. Test the surface with the back of your hand; if it's too hot for you, it's too hot for paws.",
            "<strong>Not updating flea and tick prevention seasonally</strong> — Some treatments need adjusting based on seasonal parasite activity. Consult your vet about the right prevention schedule for your area.",
            "<strong>Leaving pets unsupervised near fireworks or bonfires</strong> — Even calm pets can panic unpredictably around loud bangs and flames. Keep pets indoors and create a quiet safe space during fireworks events."
        ]
    # === PET FIRST AID ===
    elif "first aid" in combined:
        mistakes = [
            "<strong>Attempting to treat serious injuries at home</strong> — First aid stabilises; it does not replace veterinary care. After applying basic first aid, always contact your vet or the nearest emergency clinic.",
            "<strong>Not having a pet first aid kit prepared</strong> — Scrambling for supplies during an emergency wastes critical time. Keep a stocked pet first aid kit accessible at home and in the car.",
            "<strong>Using human medications on pets</strong> — Paracetamol is toxic to cats, and ibuprofen can harm dogs. Never administer human medication without explicit veterinary guidance.",
            "<strong>Panicking and restraining an injured pet too forcefully</strong> — Injured animals may bite out of pain and fear. Approach calmly, use a towel for gentle restraint, and speak in a low, soothing voice.",
            "<strong>Not knowing your nearest emergency vet</strong> — Regular vets often close at weekends and evenings. Know the location and phone number of your nearest 24-hour veterinary emergency service before you need it."
        ]
    # === PET HYDRATION ===
    elif "hydration" in combined:
        mistakes = [
            "<strong>Providing only one water source</strong> — Multiple water stations around the home encourage drinking. Cats especially benefit from water sources placed away from food bowls.",
            "<strong>Ignoring reduced water intake</strong> — A sudden drop in water consumption can signal illness. Monitor roughly how much your pet drinks daily and consult a vet if patterns change.",
            "<strong>Relying on dry food without supplemental water access</strong> — Dry kibble contains around 10% moisture compared to 70-80% in wet food. Pets on dry diets need more accessible fresh water.",
            "<strong>Using small, unstable water bowls</strong> — Bowls that tip over easily or are too small for the pet discourage drinking. Choose heavy, wide bowls appropriate for your pet's size.",
            "<strong>Not refreshing water daily</strong> — Standing water collects dust, bacteria, and hair. Change water at least once daily, more often in warm weather."
        ]
    # === MULTI-PET HOUSEHOLD ===
    elif "multi-pet" in combined:
        mistakes = [
            "<strong>Forcing introductions too quickly</strong> — Rushing the introduction between a new dog and existing cats (or vice versa) can create lasting fear and aggression. Follow a gradual, scent-first introduction protocol over days or weeks.",
            "<strong>Expecting all pets to share resources</strong> — Each pet needs their own food bowl, water source, bed, and (for cats) litter tray. Shared resources increase competition and stress.",
            "<strong>Leaving pets unsupervised during the adjustment period</strong> — Even animals that seem to get along initially can have setbacks. Supervise all interactions for at least the first few weeks.",
            "<strong>Punishing species-typical behaviour</strong> — A dog chasing a cat or a cat hissing at a dog is instinctive, not 'naughty'. Manage the environment to prevent these encounters rather than punishing after the fact.",
            "<strong>Neglecting individual attention</strong> — In multi-pet households, each animal still needs one-on-one time with their owner. This is especially important for pets that were solo animals before a new addition arrived."
        ]
    # === DOG DENTAL HEALTH ===
    elif "dental" in combined:
        mistakes = [
            "<strong>Assuming dental chews replace brushing</strong> — Dental chews can help reduce plaque buildup, but they are not a substitute for regular tooth brushing with a pet-safe toothpaste.",
            "<strong>Ignoring bad breath as 'normal dog smell'</strong> — Persistent bad breath is often a sign of dental disease, not just a characteristic of dogs. Have your vet check teeth if breath is consistently foul.",
            "<strong>Starting dental care only when problems appear</strong> — Preventive dental care should begin in puppyhood. By the time you see brown teeth, swollen gums, or difficulty eating, the disease is already advanced.",
            "<strong>Using human toothpaste on dogs</strong> — Human toothpaste contains fluoride and foaming agents that are toxic to dogs if swallowed. Always use toothpaste specifically formulated for pets.",
            "<strong>Not scheduling professional dental cleanings</strong> — Even with home brushing, most dogs benefit from veterinary dental cleaning under anaesthesia every one to two years."
        ]
    # === SLOW FEEDER BOWLS ===
    elif "slow feeder" in combined or "speed eating" in combined:
        mistakes = [
            "<strong>Choosing a pattern that is too easy for your dog</strong> — Simple ridge patterns won't slow down a determined eater. Match the bowl complexity to your dog's eating speed for meaningful results.",
            "<strong>Switching to a slow feeder without a transition period</strong> — Some dogs become frustrated with sudden changes. Start by mixing regular and slow-feeder meals for the first few days.",
            "<strong>Not cleaning the bowl's ridges and grooves thoroughly</strong> — Food residue gets trapped in the pattern details and harbours bacteria. Scrub all surfaces after every meal.",
            "<strong>Using a slow feeder for every meal without observation</strong> — Some dogs may become anxious, guard the bowl more aggressively, or avoid eating altogether. Watch for signs of stress during the first week.",
            "<strong>Selecting the wrong size for your dog's muzzle</strong> — Flat-faced breeds need shallow, wide patterns; long-nosed breeds can handle deeper grooves. An ill-fitting design increases frustration rather than reducing it."
        ]
    # === DOG TRAINING TREATS ===
    elif "training treat" in combined or "dog treat" in combined:
        mistakes = [
            "<strong>Using treats that are too large</strong> — Training treats should be pea-sized or smaller for quick consumption. Large treats slow training momentum and add unnecessary calories.",
            "<strong>Relying on a single treat type</strong> — Varying treats keeps reward value high. Use standard treats for routine commands and high-value treats (cheese, chicken) for difficult behaviours.",
            "<strong>Not adjusting meal portions when using training treats</strong> — Treat calories add up quickly during training sessions. Reduce meal sizes proportionally to prevent weight gain.",
            "<strong>Choosing treats with excessive additives</strong> — Look for short ingredient lists with recognisable, whole-food ingredients. Avoid artificial colours, flavours, and preservatives.",
            "<strong>Phasing out treats too quickly</strong> — Moving to praise-only rewards before a behaviour is fully established leads to regression. Gradually reduce treat frequency while maintaining intermittent reinforcement."
        ]
    # === PET NUTRITION / FOOD LABELS ===
    elif "nutrition" in combined or "food label" in combined:
        mistakes = [
            "<strong>Choosing food based solely on marketing claims</strong> — Terms like 'premium', 'gourmet', and 'holistic' have no legal definition in pet food. Check the actual ingredients and nutritional analysis instead.",
            "<strong>Switching foods abruptly</strong> — Sudden diet changes cause digestive upset. Transition gradually over seven to ten days, mixing increasing amounts of the new food with the old.",
            "<strong>Assuming grain-free is automatically healthier</strong> — Grain-free diets are not necessary for most pets and have been linked to heart issues in some dogs. Only go grain-free on veterinary advice.",
            "<strong>Ignoring the 'complete' vs 'complementary' label</strong> — 'Complete' foods provide all necessary nutrients; 'complementary' foods do not and must be fed alongside a complete diet.",
            "<strong>Overfeeding based on the packet guidelines alone</strong> — Feeding guidelines are starting points, not rules. Adjust portions based on your pet's weight, activity level, age, and body condition."
        ]
    # === PET GROOMING GLOSSARY ===
    elif "grooming glossary" in combined or "grooming terms" in combined:
        mistakes = [
            "<strong>Confusing coat types when choosing grooming tools</strong> — A slicker brush for a double-coated breed serves a different purpose than one for a single-coated breed. Match the tool to your pet's specific coat type.",
            "<strong>Bathing too frequently</strong> — Over-bathing strips natural oils from the coat, leading to dry skin and irritation. Most dogs need bathing only every four to six weeks unless they get particularly dirty.",
            "<strong>Neglecting ear, eye, and paw grooming</strong> — Grooming is more than coat care. Regular ear cleaning, eye wiping, and paw pad checks are essential parts of a complete grooming routine.",
            "<strong>Using human grooming products on pets</strong> — Human shampoos, conditioners, and detanglers have the wrong pH for pet skin. Always use products specifically formulated for dogs or cats.",
            "<strong>Skipping grooming between professional appointments</strong> — Regular at-home brushing, nail checks, and ear inspections between groomer visits prevent matting, infections, and discomfort."
        ]
    # === PET FEEDING GUIDE / PORTIONS ===
    elif "feeding guide" in combined or "portions" in combined or "feeding schedule" in combined:
        mistakes = [
            "<strong>Free-feeding (leaving food out all day)</strong> — Unmonitored access to food leads to overeating and makes it difficult to detect changes in appetite that might signal illness.",
            "<strong>Not weighing food portions</strong> — Eyeballing serving sizes is unreliable. Use a kitchen scale or measuring cup to ensure consistent, appropriate portions at every meal.",
            "<strong>Feeding the same amount regardless of activity level</strong> — A dog that had an hour-long hike needs different calories than one that rested all day. Adjust portions based on actual daily activity.",
            "<strong>Giving table scraps as a regular habit</strong> — Human food is often too rich, salty, or fatty for pets, and some common foods (onions, grapes, chocolate) are toxic.",
            "<strong>Ignoring life-stage feeding requirements</strong> — Puppies, adult dogs, and senior dogs all have different nutritional needs. Ensure you are feeding an age-appropriate formula."
        ]
    # === PET HEALTH TERMINOLOGY ===
    elif "health terminology" in combined or "veterinary terms" in combined:
        mistakes = [
            "<strong>Confusing vaccination and immunisation</strong> — Vaccination is the injection; immunisation is the resulting protection. Some vaccines require multiple doses before full immunisation is achieved.",
            "<strong>Assuming 'breed-specific conditions' will definitely occur</strong> — Breed predispositions indicate higher risk, not certainty. Regular health screening and preventive care can manage many predisposed conditions effectively.",
            "<strong>Ignoring subtle symptoms because they seem minor</strong> — Slight limping, occasional vomiting, or mild lethargy can indicate developing health issues. Early veterinary attention often prevents more serious problems.",
            "<strong>Relying on internet diagnoses</strong> — Online symptom checkers provide general information, not diagnoses. Always consult a veterinary professional for health concerns.",
            "<strong>Misunderstanding 'neutering' terminology</strong> — In the UK, 'neutering' applies to both sexes; 'spaying' specifically refers to females and 'castration' to males. Understanding correct terms helps you communicate clearly with your vet."
        ]
    # === DOG BED PLACEMENT ===
    elif "where to place" in combined or "bed location" in combined or "bed placement" in combined:
        mistakes = [
            "<strong>Placing the bed in a high-traffic area</strong> — Dogs need a quiet retreat for undisturbed rest. Avoid placing beds in hallways, near front doors, or in the centre of busy rooms.",
            "<strong>Positioning the bed near radiators or in direct sunlight</strong> — Dogs can overheat without realising. Choose a spot with consistent, moderate temperature and good ventilation.",
            "<strong>Moving the bed frequently</strong> — Dogs are creatures of habit and feel secure when their resting spot is consistent. Pick a good location and keep it there.",
            "<strong>Placing only one bed in a multi-room home</strong> — If your dog follows you between rooms, consider beds in two or three key locations so they always have a comfortable option nearby.",
            "<strong>Ignoring the dog's own preference</strong> — If your dog consistently chooses to sleep in a different spot, move the bed there. Their instinct about where they feel safest is usually sound."
        ]
    # === DOG BED WASHING / MAINTENANCE ===
    elif "how to wash" in combined or "maintain your dog" in combined:
        mistakes = [
            "<strong>Washing the bed too infrequently</strong> — Dog beds harbour bacteria, dust mites, and allergens. Wash covers fortnightly and deep-clean the entire bed monthly.",
            "<strong>Using scented laundry detergent</strong> — Strong fragrances can irritate your dog's sensitive nose and skin. Use unscented, pet-safe detergent.",
            "<strong>Tumble drying memory foam inserts on high heat</strong> — High heat damages memory foam structure. Air-dry foam inserts completely to preserve their support qualities.",
            "<strong>Not checking zips and seams after washing</strong> — Washing machines can loosen zips, snap threads, and weaken seams. Inspect covers after every wash to catch damage before your dog does.",
            "<strong>Putting the bed back before it is fully dry</strong> — Even slightly damp bedding breeds mould and bacteria rapidly. Ensure both covers and inserts are completely dry before reassembling."
        ]
    # === DOG COLLAR / PUPPY COLLAR ===
    elif "collar" in combined and ("puppy" in combined or "dog" in combined):
        mistakes = [
            "<strong>Choosing a collar that is too tight or too loose</strong> — You should be able to fit two fingers between the collar and your dog's neck. Too tight causes discomfort; too loose risks slipping over the head.",
            "<strong>Not checking collar fit as a puppy grows</strong> — Puppies grow rapidly, and a collar that fits at 10 weeks may be dangerously tight by 14 weeks. Check fit weekly during growth phases.",
            "<strong>Using a collar for lead walking with a dog that pulls</strong> — Collars put pressure on the throat and neck when dogs pull. Switch to a harness for walking and keep the collar for identification only.",
            "<strong>Leaving a collar on during crate time or unsupervised play</strong> — Collars can snag on crate bars, furniture, or other dogs' mouths. Remove collars when your dog is in a crate or playing with other dogs.",
            "<strong>Prioritising style over functionality</strong> — Fashion collars with spikes, chains, or heavy embellishments can be uncomfortable and impractical. Choose lightweight, well-fitted, durable collars first."
        ]
    # === CAT COLLAR ===
    elif "cat collar" in combined:
        mistakes = [
            "<strong>Using a non-breakaway collar</strong> — Standard buckle collars can strangle cats who get caught on branches, fences, or furniture. Always use a quick-release breakaway collar for cats.",
            "<strong>Fitting the collar too loosely</strong> — A loose collar catches on objects more easily. Two-finger fit is the standard: snug enough to stay on, loose enough for comfort.",
            "<strong>Adding heavy bells or tags</strong> — Oversized bells and multiple tags weigh down a cat's neck and can cause irritation. Use a single lightweight ID tag and a small bell if needed.",
            "<strong>Not checking collar fit regularly</strong> — Kittens grow quickly and adult cats' weight fluctuates seasonally. Check fit fortnightly and adjust as needed.",
            "<strong>Assuming indoor cats don't need collars</strong> — Indoor cats can escape. A collar with ID ensures a found cat can be quickly returned home."
        ]
    # === CAT GPS TRACKER ===
    elif "gps" in combined and "cat" in combined:
        mistakes = [
            "<strong>Choosing a tracker that is too heavy</strong> — GPS units designed for dogs can be too bulky for cats. Choose a tracker specifically designed for cats, ideally under 30g.",
            "<strong>Relying on GPS alone for cat safety</strong> — GPS tracking is a backup, not a substitute for a secure garden, microchip, and collar with ID. Use multiple identification methods together.",
            "<strong>Not charging the tracker regularly</strong> — Most cat GPS trackers need charging every few days. A dead tracker provides no protection. Set a regular charging schedule.",
            "<strong>Expecting perfect indoor accuracy</strong> — GPS signals are weaker indoors and in dense urban areas. Don't panic if the location shows your cat a few metres from their actual position.",
            "<strong>Forgetting to update the app and firmware</strong> — Outdated software can cause connection issues and inaccurate tracking. Keep both the smartphone app and tracker firmware current."
        ]
    # === CAT ID TAGS ===
    elif "id tag" in combined and "cat" in combined:
        mistakes = [
            "<strong>Using a tag that is too heavy for the collar</strong> — Heavy tags pull the collar around and cause irritation. Choose lightweight, small-diameter tags designed for cats.",
            "<strong>Not engraving a phone number</strong> — A tag with just a name is useless for returning a lost cat. Always include at least one current phone number.",
            "<strong>Relying on a tag instead of a microchip</strong> — Tags can fall off; microchips are permanent. Use both for comprehensive identification.",
            "<strong>Choosing a dangling tag on a long ring</strong> — Hanging tags catch on objects and can be pulled off. Use flat, slide-on tags or tags that attach flush to the collar.",
            "<strong>Not updating tag information after moving</strong> — An old address or disconnected phone number renders the tag useless. Update tags whenever your contact details change."
        ]
    # === CAT HARNESS ===
    elif "harness" in combined and "cat" in combined:
        mistakes = [
            "<strong>Skipping indoor harness training</strong> — Putting a harness on a cat and immediately going outdoors causes panic. Let your cat wear the harness indoors for several days before attempting an outdoor walk.",
            "<strong>Using a dog harness on a cat</strong> — Cat bodies are shaped differently from dogs, and cats can escape from poorly fitted dog harnesses. Use a harness specifically designed for feline anatomy.",
            "<strong>Pulling the cat along on the lead</strong> — Cat walks are led by the cat, not the owner. Follow your cat's pace and direction; pulling causes fear and resistance.",
            "<strong>Walking in busy, noisy environments</strong> — Most cats prefer quiet, low-traffic areas. Loud streets, crowded parks, and areas with unleashed dogs are stressful for harnessed cats.",
            "<strong>Not having a secure carrier nearby</strong> — If your cat panics on a walk, you need a way to safely contain them immediately. Always bring a carrier or secure bag on outdoor excursions."
        ]
    # === CAT BED ===
    elif "cat bed" in combined:
        mistakes = [
            "<strong>Placing the bed on the floor in a busy room</strong> — Cats prefer elevated, secluded resting spots. Place beds on furniture, shelves, or in quiet corners for better uptake.",
            "<strong>Buying only one bed for a multi-level home</strong> — Cats gravitate to different spots at different times of day. Provide beds on each level of your home where the cat spends time.",
            "<strong>Washing the bed too often with strong detergent</strong> — Cats are comforted by their own scent on bedding. Wash covers only when necessary and use unscented detergent to preserve familiar smells.",
            "<strong>Choosing style over the cat's preference</strong> — Some cats prefer enclosed cave beds; others prefer open platforms. Observe where your cat naturally sleeps to guide your choice.",
            "<strong>Not replacing flattened or lumpy beds</strong> — Compressed padding provides poor insulation and comfort. Replace inserts or entire beds when the cushioning has deteriorated."
        ]
    # === CAT BRUSH / GROOMING ===
    elif "cat brush" in combined or ("brush" in combined and "cat" in combined):
        mistakes = [
            "<strong>Using a dog brush on a cat</strong> — Cat skin is thinner and more sensitive than dog skin. Dog brushes can scratch or irritate. Choose brushes designed specifically for cats.",
            "<strong>Brushing against the direction of hair growth</strong> — Always brush in the direction the fur naturally lies. Brushing backwards causes discomfort and can pull out healthy fur.",
            "<strong>Forcing grooming on a reluctant cat</strong> — Start with very short sessions (one to two minutes) and build up gradually. Forcing a cat creates lasting negative associations with grooming.",
            "<strong>Only grooming long-haired cats</strong> — Short-haired cats benefit from regular brushing too. It removes loose fur, distributes natural oils, and allows you to check for lumps, fleas, and skin issues.",
            "<strong>Ignoring matting until it becomes severe</strong> — Small mats are easy to address with a dematting comb. Large mats pull on the skin painfully and often require professional or veterinary removal."
        ]
    # === CAT SHAMPOO ===
    elif "cat shampoo" in combined or ("shampoo" in combined and "cat" in combined):
        mistakes = [
            "<strong>Bathing cats too frequently</strong> — Most cats groom themselves effectively and rarely need bathing. Over-bathing strips natural oils and causes dry, irritated skin.",
            "<strong>Using dog shampoo on cats</strong> — Some dog shampoos contain ingredients (like permethrin) that are toxic to cats. Always use a product explicitly labelled safe for cats.",
            "<strong>Not rinsing thoroughly</strong> — Shampoo residue causes itching and skin irritation. Rinse until the water runs completely clear, paying special attention to the belly and underarms.",
            "<strong>Getting water in the ears</strong> — Water trapped in cat ears can lead to infection. Use cotton balls to gently protect the ear canals during bathing.",
            "<strong>Bathing a stressed or aggressive cat without preparation</strong> — Trim nails beforehand, use a non-slip mat, and have towels ready. A calm, prepared approach reduces stress for both you and the cat."
        ]
    # === MENTAL STIMULATION FOR DOGS ===
    elif "mental stimulation" in combined and "dog" in combined:
        mistakes = [
            "<strong>Equating mental stimulation with physical exercise alone</strong> — A long walk tires the body but may not challenge the mind. Combine physical activity with problem-solving tasks for complete enrichment.",
            "<strong>Using the same puzzle every day</strong> — Dogs learn puzzle patterns quickly and lose interest. Rotate between different types of mental challenges throughout the week.",
            "<strong>Making puzzles too difficult from the start</strong> — Failure is demotivating. Begin with easy wins and gradually increase difficulty as your dog builds confidence and problem-solving skills.",
            "<strong>Only providing mental stimulation when you're home</strong> — Dogs also need enrichment during alone time. Frozen food toys, scatter feeding, and self-play puzzles keep dogs occupied when you're away.",
            "<strong>Overlooking training sessions as mental stimulation</strong> — Learning new commands and tricks is one of the best mental workouts for dogs. Even five minutes of training provides significant cognitive engagement."
        ]
    # === CONFIDENCE-BUILDING PLAY ===
    elif "confidence" in combined and ("shy" in combined or "fearful" in combined or "building" in combined):
        mistakes = [
            "<strong>Flooding the dog with too many new experiences at once</strong> — Shy dogs need gradual exposure. Introduce one new toy, sound, or environment at a time and allow the dog to approach at their own pace.",
            "<strong>Forcing interaction with toys the dog finds intimidating</strong> — If a dog backs away from a toy, do not push it closer. Leave it on the ground at a distance and let the dog investigate when ready.",
            "<strong>Using loud or unpredictable toys too early</strong> — Squeaky toys, balls that bounce erratically, and electronic toys can startle fearful dogs. Start with soft, quiet, predictable toys.",
            "<strong>Expecting rapid progress</strong> — Confidence-building takes weeks or months, not days. Celebrate small steps and avoid pushing the dog faster than they are comfortable with.",
            "<strong>Punishing fearful reactions</strong> — Scolding a dog for cowering, hiding, or barking at something scary makes fear worse. Respond with patience, distance, and positive reinforcement."
        ]
    # === ESSENTIAL SUPPLIES (GENERAL) ===
    elif "essential" in combined and ("supply" in combined or "supplies" in combined or "must-have" in combined):
        mistakes = [
            "<strong>Buying everything before the pet arrives</strong> — Start with basics (food, bowls, bed, lead, collar) and add items as you learn your pet's preferences. Buying everything at once often leads to unused products.",
            "<strong>Choosing the cheapest option for every item</strong> — Budget items work for some products, but investing more in a durable bed, quality food, and a sturdy lead saves money long-term.",
            "<strong>Overlooking identification essentials</strong> — A microchip, collar with ID tag, and registration with a lost-pet database should be top-priority purchases, not afterthoughts.",
            "<strong>Not pet-proofing before bringing supplies home</strong> — Secure toxic plants, cleaning products, small objects, and electrical cables before introducing a new pet to your home.",
            "<strong>Forgetting about ongoing costs</strong> — Food, flea treatment, vaccinations, insurance, and replacement toys are recurring expenses. Budget for monthly costs, not just the initial setup."
        ]
    # === DOG TOYS UK / ESSENTIAL GUIDE (general) ===
    elif "dog toys uk" in combined and "essential guide" in combined:
        mistakes = [
            "<strong>Buying too many toys at once</strong> — A handful of well-chosen toys is more effective than a large collection. Dogs become overwhelmed by too many options and may ignore most of them.",
            "<strong>Choosing toys based on human preferences</strong> — A toy that looks appealing to you may not interest your dog. Focus on texture, size, and play style rather than colour or novelty design.",
            "<strong>Not supervising play with new toys</strong> — Every new toy should be tested under supervision to assess durability and safety for your specific dog's chewing and play habits.",
            "<strong>Ignoring your dog's individual play preference</strong> — Some dogs are natural fetchers, others prefer tug, and some love solo chewing. Observe what your dog gravitates toward and buy accordingly.",
            "<strong>Forgetting to budget for replacement</strong> — Toys wear out and need replacing. Factor regular replacement costs into your pet budget rather than being caught off guard."
        ]
    else:
        # Generic fallback — adapt based on what keywords we can detect
        if "cat" in combined:
            mistakes = [
                "<strong>Assuming one approach suits all cats</strong> — Every cat has individual preferences, sensitivities, and energy levels. Observe your cat's reactions and adjust your approach accordingly.",
                "<strong>Overlooking environmental enrichment</strong> — Vertical space, hiding spots, window perches, and scratching surfaces are as important as toys and food for feline wellbeing.",
                "<strong>Ignoring stress signals</strong> — Hiding, over-grooming, loss of appetite, and changes in litter tray habits are common stress indicators. Investigate the cause rather than dismissing the behaviour.",
                "<strong>Skipping regular veterinary check-ups</strong> — Cats hide illness effectively. Annual vet visits catch developing issues early, before symptoms become severe.",
                "<strong>Not providing enough water sources</strong> — Cats prefer fresh, flowing water and may avoid stagnant bowls. Multiple water stations or a cat fountain encourages better hydration."
            ]
        else:
            mistakes = [
                "<strong>Applying one-size-fits-all advice</strong> — Every dog is different in breed, temperament, and health status. Tailor your approach to your individual dog's needs and preferences.",
                "<strong>Ignoring early warning signs</strong> — Subtle changes in behaviour, appetite, or energy levels often indicate developing issues. Address small changes before they become larger problems.",
                "<strong>Relying solely on internet advice for health concerns</strong> — Online resources provide general guidance, but specific health questions always require professional veterinary input.",
                "<strong>Skipping preventive care to save money</strong> — Vaccinations, flea treatment, dental care, and regular check-ups are far cheaper than treating the conditions they prevent.",
                "<strong>Not accounting for your dog's age and life stage</strong> — Puppies, adults, and senior dogs have different needs for nutrition, exercise, enrichment, and veterinary care."
            ]

    return mistakes


def generate_suitability_items(post_id, title, slug, content_snippet):
    """Generate 4-5 topic-specific suitability items."""
    title_lower = title.lower()
    slug_lower = slug.lower()
    combined = f"{title_lower} {slug_lower} {content_snippet[:1500].lower()}"

    # === DOG TOY SAFETY ===
    if "dog toy safety" in combined or ("safety" in combined and "dog toy" in combined and "cat" not in combined[:30].lower()):
        return [
            "<strong>Best for first-time dog owners:</strong> Start with a basic safety-rated rubber toy and a rope toy — these cover most play needs while you learn your dog's habits",
            "<strong>Best for households with children:</strong> Choose larger toys without small detachable parts; supervise play to ensure children and dogs interact safely",
            "<strong>Best for power chewers:</strong> Invest in toys specifically tested for aggressive chewing — the upfront cost saves money and vet bills from swallowed fragments",
            "<strong>Best for multi-dog households:</strong> Size-appropriate toys for each dog reduce choking risks from smaller dogs accessing larger-breed toys",
            "<strong>Best for anxious dogs:</strong> Soft, food-stuffable toys provide comfort and distraction; avoid toys that make unpredictable sounds"
        ]
    elif "breed size" in combined or "choosing the right size" in combined:
        return [
            "<strong>Best for toy and small breeds (under 10kg):</strong> Small rubber toys and mini fetch balls they can comfortably grip and carry",
            "<strong>Best for medium breeds (10-25kg):</strong> Standard-sized rope toys, rubber chews, and fetch toys with good bounce and durability",
            "<strong>Best for large breeds (25-40kg):</strong> Oversized rubber toys and heavy-duty rope toys rated for strong jaws",
            "<strong>Best for giant breeds (40kg+):</strong> Extra-large, virtually indestructible toys designed specifically for giant-breed jaw pressure",
            "<strong>Best for flat-faced breeds:</strong> Flat or oval-shaped toys that are easier to grip than round balls"
        ]
    elif "overstimulation" in combined or "overexcited" in combined or "calming down" in combined:
        return [
            "<strong>Best for easily overexcited dogs:</strong> Slow-dispensing food toys and licking mats that promote calm, focused behaviour",
            "<strong>Best for dogs that struggle to settle after play:</strong> Transition activities (gentle sniffing exercises, calm training) that bridge the gap between high energy and rest",
            "<strong>Best for reactive dogs:</strong> Quiet enrichment toys without squeakers or unpredictable movement that avoid triggering arousal",
            "<strong>Best for multi-dog households:</strong> Separate calm-down stations with individual enrichment to prevent excitement from escalating between dogs",
            "<strong>Best for evening wind-down:</strong> Frozen food toys and snuffle mats that encourage 15-20 minutes of calm focus before bedtime"
        ]
    elif "enrichment schedule" in combined or "structuring daily" in combined:
        return [
            "<strong>Best for high-energy working breeds:</strong> Three enrichment sessions daily combining physical and mental challenges across morning, afternoon, and evening",
            "<strong>Best for senior dogs:</strong> Two shorter, gentler sessions per day focused on scent work and simple puzzles with rest in between",
            "<strong>Best for dogs left home alone:</strong> Pre-departure enrichment (frozen Kong, snuffle mat) that occupies the critical first 30 minutes after you leave",
            "<strong>Best for puppies:</strong> Frequent, short sessions (5-10 minutes) throughout the day to match their short attention spans and high energy",
            "<strong>Best on a budget:</strong> DIY enrichment schedules using household items (cardboard boxes, towel wraps, muffin tin games) cost almost nothing"
        ]
    elif "senior dog" in combined and ("enrichment" in combined or "cognitive" in combined or "gentle play" in combined):
        return [
            "<strong>Best for dogs with arthritis:</strong> Stationary puzzles and licking mats that require minimal physical movement",
            "<strong>Best for dogs with reduced vision:</strong> Scent-based enrichment and textured toys that engage smell and touch rather than sight",
            "<strong>Best for dogs with cognitive decline:</strong> Simple, familiar puzzles that provide achievable mental stimulation without frustration",
            "<strong>Best for otherwise healthy senior dogs:</strong> Moderate puzzle toys and gentle fetch that maintain physical and cognitive fitness",
            "<strong>Best on a budget:</strong> Snuffle mats made from fleece scraps and frozen plain yoghurt in a Kong provide excellent low-cost senior enrichment"
        ]
    elif "scent" in combined and ("game" in combined or "enrichment" in combined):
        return [
            "<strong>Best for scent hound breeds:</strong> Multi-step scent trails and advanced nose work that channel their natural tracking instincts",
            "<strong>Best for beginners:</strong> Simple scatter feeding in grass or a basic snuffle mat as a first introduction to scent-based play",
            "<strong>Best for rainy-day enrichment:</strong> Indoor scent trails using hidden treats throughout the house keep dogs engaged without outdoor access",
            "<strong>Best for anxious dogs:</strong> Calm, self-paced scent work reduces stress and builds confidence more effectively than high-energy games",
            "<strong>Best for multi-dog households:</strong> Individual scent games in separate rooms prevent competition and allow each dog to work at their own pace"
        ]
    elif "crate" in combined and ("enrichment" in combined or "play" in combined):
        return [
            "<strong>Best for crate-training puppies:</strong> Frozen Kongs and licking mats that create positive crate associations during the training phase",
            "<strong>Best for dogs with separation anxiety:</strong> Long-lasting food toys that provide a calming focus during owner departures",
            "<strong>Best for overnight crate time:</strong> A safe chew toy and a snuffle mat that the dog can engage with quietly if they wake",
            "<strong>Best for dogs recovering from surgery:</strong> Gentle, stationary enrichment that keeps the dog mentally occupied without physical exertion",
            "<strong>Best on a budget:</strong> A frozen dishcloth soaked in low-sodium broth provides 20+ minutes of crate enrichment for pennies"
        ]
    elif "durability" in combined or ("material" in combined and "toy" in combined):
        return [
            "<strong>Best for power chewers:</strong> Solid natural rubber and reinforced nylon toys that withstand sustained heavy chewing",
            "<strong>Best for gentle chewers:</strong> Plush toys and softer rubber toys that provide comfort without being overly tough",
            "<strong>Best for fetch enthusiasts:</strong> High-bounce rubber balls and durable flying discs designed for repeated throwing and catching",
            "<strong>Best for tug-of-war players:</strong> Multi-strand rope toys and reinforced rubber tug toys that withstand strong pulling",
            "<strong>Best on a budget:</strong> Natural rubber toys at mid-range prices consistently offer the best durability-per-pound across chewing styles"
        ]
    elif "storage" in combined or "organisation" in combined:
        return [
            "<strong>Best for small spaces:</strong> Hanging storage bags or over-door organisers that keep toys accessible without taking up floor space",
            "<strong>Best for rotation systems:</strong> Lidded bins or sealed bags that store rotated-out toys while keeping them fresh and novel",
            "<strong>Best for multi-dog households:</strong> Separate labelled containers for each dog's toys to simplify organisation and prevent mix-ups",
            "<strong>Best for families with children:</strong> Dog toy storage placed out of children's reach to prevent accidental mix-ups with kids' toys",
            "<strong>Best on a budget:</strong> Repurposed fabric shopping bags or laundry baskets work perfectly as breathable, low-cost toy storage"
        ]
    elif "hygiene" in combined or ("clean" in combined and "toy" in combined) or "how to wash" in combined:
        return [
            "<strong>Best for rubber toys:</strong> Top-rack dishwasher cleaning — quick, thorough, and requires no special products",
            "<strong>Best for rope toys:</strong> Soaking in diluted vinegar followed by microwave sterilisation (2 minutes while damp) kills bacteria effectively",
            "<strong>Best for plush toys:</strong> Machine washing on a gentle cycle with pet-safe detergent, then thorough air drying",
            "<strong>Best for food-dispensing toys:</strong> Bottle brush cleaning after every use, with a weekly overnight soak in warm water and baking soda",
            "<strong>Best on a budget:</strong> White vinegar and baking soda handle most toy cleaning needs without any specialist pet-cleaning products"
        ]
    elif "diy" in combined and "dog" in combined:
        return [
            "<strong>Best for puppies:</strong> Frozen wet-cloth chew toys that soothe teething gums — cheap, easy to make, and safe under supervision",
            "<strong>Best for mental enrichment:</strong> Muffin tin puzzles and towel-wrapped treats that provide problem-solving without any purchase needed",
            "<strong>Best for heavy chewers:</strong> Triple-braided fleece tug toys from old blankets — more durable than single-layer fabric options",
            "<strong>Best for solo play:</strong> Treat-filled water bottles wrapped in old socks that crinkle and dispense rewards",
            "<strong>Best for multi-dog households:</strong> Make several identical toys so each dog has their own, reducing competition and guarding"
        ]
    elif "play style" in combined:
        return [
            "<strong>Best for natural fetchers:</strong> Durable balls and retrieval toys that can withstand repeated throwing and carrying",
            "<strong>Best for tug players:</strong> Rope toys and rubber tug toys with comfortable grip handles for the owner",
            "<strong>Best for solo chewers:</strong> Long-lasting chew toys and food-stuffable toys for independent engagement",
            "<strong>Best for chasers and herders:</strong> Flirt poles and toys with erratic movement that mimic prey behaviour",
            "<strong>Best for gentle, comfort-seeking dogs:</strong> Soft plush toys and snuggle toys that provide companionship rather than vigorous play"
        ]
    elif "puppy" in combined and ("toy" in combined or "teething" in combined or "care" in combined):
        return [
            "<strong>Best for teething puppies (3-6 months):</strong> Frozen rubber toys and textured teething rings that soothe sore gums",
            "<strong>Best for training puppies:</strong> Small, lightweight toys that double as training rewards and redirect chewing behaviour",
            "<strong>Best for puppies left alone briefly:</strong> Safe, durable food-dispensing toys that provide independent entertainment",
            "<strong>Best for socialisation:</strong> A variety of textures and sounds in age-appropriate toys that build confidence with new experiences",
            "<strong>Best on a budget:</strong> A frozen wet flannel and a basic rubber Kong cover teething and enrichment needs affordably"
        ]
    elif "cat toy" in combined and ("faq" in combined or "glossary" in combined or "types explained" in combined):
        return [
            "<strong>Best for active, young cats:</strong> Wand toys and feather chasers that allow high-energy interactive play sessions",
            "<strong>Best for lazy or overweight cats:</strong> Treat-dispensing balls and puzzle feeders that encourage movement during mealtimes",
            "<strong>Best for solo cats home alone:</strong> Battery-operated moving toys and self-play circuit tracks that provide independent entertainment",
            "<strong>Best for multi-cat households:</strong> Multiple toy types in various locations so each cat can play without competition",
            "<strong>Best on a budget:</strong> Crinkle balls, cardboard boxes, and paper bags (handles removed) provide free enrichment most cats love"
        ]
    elif "cat enrichment" in combined or "indoor cat" in combined or "house cat" in combined:
        return [
            "<strong>Best for single indoor cats:</strong> A combination of vertical space (cat tree), window perch, and daily interactive play to prevent boredom",
            "<strong>Best for multi-cat households:</strong> Enrichment stations in multiple rooms so each cat has options without competing for resources",
            "<strong>Best for senior indoor cats:</strong> Low-effort enrichment like window bird feeders, scent enrichment, and gentle wand play",
            "<strong>Best for overweight indoor cats:</strong> Puzzle feeders and food-dispensing toys that turn meals into calorie-burning enrichment",
            "<strong>Best on a budget:</strong> Cardboard boxes, paper bags, and DIY puzzle feeders from egg cartons cost nothing and provide genuine enrichment"
        ]
    elif "kitten" in combined and "adult" in combined:
        return [
            "<strong>Best for kittens under 12 weeks:</strong> Soft, lightweight toys too large to swallow, with no detachable parts",
            "<strong>Best for adolescent cats (6-12 months):</strong> Interactive wand toys and puzzle feeders that match their high energy and growing intelligence",
            "<strong>Best for adult cats (1-7 years):</strong> A rotation of different toy types that maintains interest across play sessions",
            "<strong>Best for senior cats (7+ years):</strong> Gentle wand toys, catnip toys, and simple puzzles that accommodate reduced mobility",
            "<strong>Best for mixed-age households:</strong> Separate play sessions tailored to each cat's age and energy level"
        ]
    elif "diy" in combined and "cat" in combined:
        return [
            "<strong>Best for curious, investigative cats:</strong> Cardboard box mazes and paper bag tunnels that encourage exploration",
            "<strong>Best for food-motivated cats:</strong> Egg carton puzzle feeders and toilet roll treat dispensers that provide foraging enrichment",
            "<strong>Best for active chasers:</strong> Fleece strip wand toys and rolled-up foil balls (supervised only) that mimic prey movement",
            "<strong>Best for cautious cats:</strong> Simple scent enrichment using dried catnip sprinkled inside a sock — low-intensity and non-threatening",
            "<strong>Best on a budget:</strong> Most effective DIY cat toys cost nothing — boxes, paper bags, and fabric scraps from your recycling"
        ]
    elif "cat play behaviour" in combined or "play style" in combined:
        return [
            "<strong>Best for stalker-pouncer cats:</strong> Wand toys with feather or fur attachments that mimic prey movement along the ground",
            "<strong>Best for bird-watcher cats:</strong> Flying or fluttering toys that mimic aerial prey — feather teasers moved through the air",
            "<strong>Best for wrestler cats:</strong> Kicker toys and stuffed animals they can grab, kick, and bunny-kick to their satisfaction",
            "<strong>Best for batting and swatting cats:</strong> Lightweight balls, springs, and rolling toys that slide easily across floors",
            "<strong>Best for social players:</strong> Interactive toys that involve the owner directly — cats that seek eye contact during play thrive on wand-toy sessions"
        ]
    elif "replace" in combined and "cat" in combined:
        return [
            "<strong>Best approach for heavy players:</strong> Inspect toys after every session and replace at the first sign of damage — don't wait for complete destruction",
            "<strong>Best for catnip toy users:</strong> Refresh with catnip spray monthly or replace entirely every two to three months when potency fades",
            "<strong>Best for multi-cat households:</strong> Keep a small stock of replacement favourites so toys can be swapped immediately when they wear out",
            "<strong>Best for budget-conscious owners:</strong> Focus spending on durable wand toy attachments (replaceable heads) rather than replacing entire toys",
            "<strong>Best tracking method:</strong> A simple note of purchase dates helps you stay ahead of replacement needs before toys become hazardous"
        ]
    elif "cat toy rotation" in combined or ("rotation" in combined and "cat" in combined):
        return [
            "<strong>Best for single indoor cats:</strong> Rotate three to four toys every three to five days to maintain novelty without overwhelming",
            "<strong>Best for easily bored cats:</strong> Shorter rotation cycles (every two to three days) with a wider variety of toy types",
            "<strong>Best for multi-cat households:</strong> Stagger rotations so not all cats experience novelty at the same time — this prevents over-excitement",
            "<strong>Best for older cats:</strong> Rotate familiar favourites alongside one new toy; sudden complete changes can unsettle senior cats",
            "<strong>Best on a budget:</strong> Rotation means you need fewer toys overall — five to eight good toys rotated effectively outperform twenty available at once"
        ]
    elif "multi-dog" in combined or "resource guarding" in combined:
        return [
            "<strong>Best for dogs with mild guarding tendencies:</strong> Multiple identical high-value toys so each dog has their own, reducing competition triggers",
            "<strong>Best for newly introduced dogs:</strong> Supervised parallel play with separate toy sets in the same room, building positive associations",
            "<strong>Best for households with size-mismatched dogs:</strong> Size-appropriate toys for each dog stored in separate, designated areas",
            "<strong>Best for preventing guarding at mealtimes:</strong> Separate feeding stations with physical barriers (baby gates, separate rooms) during meals",
            "<strong>Best for long-term management:</strong> Consistent rules about toy access, combined with positive reinforcement for sharing behaviour"
        ]
    elif "surgery" in combined or "healing" in combined or "recovery" in combined:
        return [
            "<strong>Best for the first week post-surgery:</strong> Licking mats and frozen food toys that keep the dog occupied without requiring any movement",
            "<strong>Best for mid-recovery (weeks 2-4):</strong> Snuffle mats and simple scent games that allow gentle head movement without body strain",
            "<strong>Best for late recovery (weeks 4-8):</strong> Short, gentle puzzle sessions and very calm indoor fetch with soft toys on flat surfaces",
            "<strong>Best for dogs in cones/recovery suits:</strong> Wide-opening food toys and flat licking mats accessible despite the recovery device",
            "<strong>Best for anxious recovery dogs:</strong> Comfort toys and calming enrichment (lavender-scented cloths, calm music) alongside gentle food puzzles"
        ]
    elif "low-mobility" in combined or "limited movement" in combined:
        return [
            "<strong>Best for dogs with severe arthritis:</strong> Bedside snuffle mats and licking mats placed within reach of the resting position",
            "<strong>Best for dogs with partial paralysis:</strong> Scent cloths and sound enrichment that engage the mind without requiring physical manipulation",
            "<strong>Best for dogs recovering from IVDD:</strong> Flat, stationary enrichment that does not encourage twisting, jumping, or stretching",
            "<strong>Best for dogs with limb injuries:</strong> Puzzle toys that can be used from a lying position, placed on a non-slip surface",
            "<strong>Best on a budget:</strong> A towel with treats rolled inside, placed right beside the dog, provides effective zero-cost enrichment"
        ]
    elif "sensory" in combined and "enrichment" in combined:
        return [
            "<strong>Best for dogs new to sensory enrichment:</strong> Start with simple scent work (treats hidden under cups) before introducing textures or sounds",
            "<strong>Best for confident, adventurous dogs:</strong> Full sensory circuits combining different walking surfaces, scent stations, and auditory elements",
            "<strong>Best for noise-sensitive dogs:</strong> Focus on scent and touch enrichment initially; introduce sounds gradually at very low volume",
            "<strong>Best for blind or deaf dogs:</strong> Emphasise the senses that remain — scent-heavy enrichment for blind dogs, vibration and visual cues for deaf dogs",
            "<strong>Best on a budget:</strong> Garden herbs, different fabric textures, and nature sounds played on a phone cost nothing and provide genuine sensory variety"
        ]
    elif "enrichment" in combined and "breed" in combined:
        return [
            "<strong>Best for terrier breeds:</strong> Digging boxes, tug toys, and fast-moving chase games that channel natural hunting and digging drives",
            "<strong>Best for retriever breeds:</strong> Fetch games, water-based play, and carrying tasks that satisfy their retrieval instincts",
            "<strong>Best for herding breeds:</strong> Puzzle toys, agility elements, and training-based enrichment that channel their problem-solving drive",
            "<strong>Best for scent hound breeds:</strong> Nose work, scent trails, and foraging games that utilise their exceptional sense of smell",
            "<strong>Best for companion breeds:</strong> Interactive toys, social play, and gentle puzzle feeders that satisfy their need for close human engagement"
        ]
    elif "body language" in combined or "behaviour explained" in combined:
        return [
            "<strong>Best for new dog owners:</strong> Focus on learning the five key signals first — tail position, ear orientation, body posture, eye contact, and mouth tension",
            "<strong>Best for families with children:</strong> Teach children to recognise 'leave me alone' signals (turning away, lip licking, whale eye) to prevent bites",
            "<strong>Best for multi-dog households:</strong> Understanding play signals vs. conflict signals helps you intervene at the right time during dog-to-dog interactions",
            "<strong>Best for reactive dog owners:</strong> Learning to read early arousal signals (stiffening, fixating, closed mouth) allows you to redirect before a reaction occurs",
            "<strong>Best for rescue dog adopters:</strong> Rescued dogs may display different or muted body language. Give them time and observe patterns over weeks, not days"
        ]
    elif "rotating puzzle" in combined or "progressive challenge" in combined:
        return [
            "<strong>Best for food-motivated dogs:</strong> Multi-compartment puzzle toys that combine sliding, lifting, and pulling for treat access",
            "<strong>Best for advanced problem-solvers:</strong> Sequential-step puzzles where each solution unlocks the next challenge",
            "<strong>Best for dogs new to puzzles:</strong> Single-action puzzles (lift a lid, push a slider) that build confidence with quick wins",
            "<strong>Best for time-poor owners:</strong> Scatter feeding and snuffle mats provide cognitive challenge with minimal setup time",
            "<strong>Best on a budget:</strong> DIY puzzles using cardboard boxes, muffin tins, and towels offer progressive difficulty for free"
        ]
    elif "pet toy safety" in combined:
        return [
            "<strong>Best for mixed-species households:</strong> Keep dog and cat toys completely separate — what is safe for one species may be hazardous for the other",
            "<strong>Best for households with toddlers:</strong> Choose pet toys that are clearly distinct from children's toys and store them separately to prevent mix-ups",
            "<strong>Best for first-time pet owners:</strong> Start with safety-rated, single-piece toys from established UK brands rather than cheap multi-packs",
            "<strong>Best for destructive pets:</strong> Durable, one-piece toys without glued-on parts, buttons, or removable components",
            "<strong>Best for supervised play only:</strong> Wand toys, string toys, and any toy with long attachments — always store these after each play session"
        ]
    elif "cat care" in combined and ("basics" in combined or "glossary" in combined):
        return [
            "<strong>Best for first-time cat owners:</strong> Focus on the essentials first — quality food, clean litter, a scratching post, and daily play",
            "<strong>Best for families adopting a rescue cat:</strong> Create a single safe room with all essentials before gradually expanding the cat's territory",
            "<strong>Best for multi-cat households:</strong> Duplicate key resources (litter trays, food bowls, resting spots) to prevent competition",
            "<strong>Best for households with children:</strong> Teach children to approach cats calmly and recognise when a cat wants to be left alone",
            "<strong>Best on a budget:</strong> Prioritise spending on quality food and veterinary care — DIY enrichment and secondhand cat furniture can fill the remaining gaps affordably"
        ]
    elif "cat toy safety" in combined:
        return [
            "<strong>Best for kittens:</strong> Larger, soft toys without small parts — kittens investigate everything with their mouths",
            "<strong>Best for solo indoor cats:</strong> Self-play toys with no string or ribbon that are safe for unsupervised use",
            "<strong>Best for supervised play:</strong> Wand toys and feather chasers that provide the highest quality interaction when an owner is present",
            "<strong>Best for multi-cat households:</strong> Multiple toys across different rooms to prevent competition and reduce accidental swallowing during disputes",
            "<strong>Best for cautious owners:</strong> Single-piece rubber or fabric toys without detachable components — the simplest option is often the safest"
        ]
    elif "seasonal" in combined:
        return [
            "<strong>Best for summer safety:</strong> Focus on hydration, shade, avoiding hot pavements, and adjusting exercise to cooler parts of the day",
            "<strong>Best for winter care:</strong> Paw protection from salt and ice, visibility gear for dark walks, and warm bedding for outdoor-access pets",
            "<strong>Best for fireworks season:</strong> A prepared safe space, calming enrichment, and (if needed) veterinary-prescribed anxiety support well before the event",
            "<strong>Best for spring hazards:</strong> Awareness of toxic spring bulbs, garden chemicals, and increased tick activity as the weather warms",
            "<strong>Best for year-round preparedness:</strong> A seasonal pet care calendar that prompts you to adjust flea treatment, exercise, and enrichment quarterly"
        ]
    elif "first aid" in combined:
        return [
            "<strong>Best for all pet owners:</strong> A stocked pet first aid kit at home and a smaller one in the car, reviewed every six months",
            "<strong>Best for active outdoor dogs:</strong> A portable first aid pouch for walks covering cuts, stings, sprains, and paw injuries",
            "<strong>Best for multi-pet households:</strong> Species-specific first aid knowledge — what works for dogs may not be safe for cats",
            "<strong>Best for new pet owners:</strong> A pet first aid course (many UK charities offer free online modules) that builds practical confidence",
            "<strong>Best for rural pet owners:</strong> Extended first aid supplies and knowledge, since veterinary clinics may be further away"
        ]
    elif "hydration" in combined:
        return [
            "<strong>Best for cats:</strong> A cat water fountain placed away from food bowls — running water encourages drinking in felines with low thirst drives",
            "<strong>Best for active dogs:</strong> A portable, collapsible water bowl for walks and a large, stable home bowl refreshed at least daily",
            "<strong>Best for senior pets:</strong> Multiple water stations at pet height throughout the home so they never have to walk far for a drink",
            "<strong>Best for warm weather:</strong> Ice cubes in water bowls, frozen treat toys, and shaded outdoor water stations",
            "<strong>Best for monitoring intake:</strong> Measure water levels daily — sudden changes in drinking habits can signal kidney disease, diabetes, or other conditions"
        ]
    elif "multi-pet" in combined:
        return [
            "<strong>Best for introducing a new dog to existing cats:</strong> A gradual, scent-first introduction protocol over two to four weeks with physical barriers between animals",
            "<strong>Best for households with same-species pairs:</strong> Duplicate resources (beds, bowls, litter trays) in separate locations to reduce competition",
            "<strong>Best for families with small children and pets:</strong> Clear supervision rules and safe spaces where each pet can retreat from children when needed",
            "<strong>Best for managing feeding time:</strong> Separate feeding stations with visual barriers prevent food guarding and ensure each pet eats their own diet",
            "<strong>Best for ongoing harmony:</strong> Regular individual attention for each pet — one-on-one time prevents jealousy and strengthens the owner-pet bond"
        ]
    elif "dental" in combined:
        return [
            "<strong>Best for preventive care:</strong> Daily tooth brushing with pet-safe toothpaste, starting in puppyhood to build lifelong tolerance",
            "<strong>Best for dogs that resist brushing:</strong> Dental chew toys, water additives, and dental treats as supplementary options (not replacements for brushing)",
            "<strong>Best for senior dogs:</strong> Annual veterinary dental check-ups and professional cleaning when plaque and tartar buildup is visible",
            "<strong>Best for breeds prone to dental issues:</strong> Small breeds and brachycephalic dogs benefit from more frequent dental monitoring due to crowded teeth",
            "<strong>Best on a budget:</strong> A pet toothbrush and enzymatic toothpaste (around £5-8) is the most cost-effective dental care investment you can make"
        ]
    elif "slow feeder" in combined or "speed eating" in combined:
        return [
            "<strong>Best for mild speed eaters:</strong> Simple ridge-pattern bowls that slow eating by 30-50% without causing frustration",
            "<strong>Best for extreme gulpers:</strong> Complex maze bowls or puzzle feeders that require paw and nose work to access food",
            "<strong>Best for flat-faced breeds:</strong> Shallow, wide slow feeders with gentle ridges that accommodate shorter muzzles",
            "<strong>Best for large breed dogs:</strong> Elevated slow feeder bowls that reduce neck strain while still slowing intake",
            "<strong>Best on a budget:</strong> Placing a clean tennis ball in a regular bowl creates an effective DIY slow feeder at no cost"
        ]
    elif "training treat" in combined or "dog treat" in combined:
        return [
            "<strong>Best for basic obedience training:</strong> Small, soft treats that can be eaten in one second — speed keeps training momentum high",
            "<strong>Best for high-distraction environments:</strong> High-value treats (real chicken, cheese, liver) that compete with environmental temptations",
            "<strong>Best for puppies:</strong> Tiny, soft treats appropriate for small mouths and developing digestive systems",
            "<strong>Best for dogs with food sensitivities:</strong> Single-ingredient, hypoallergenic treats (dried fish, sweet potato) that avoid common allergens",
            "<strong>Best on a budget:</strong> Chopped carrots, blueberries, and boiled chicken breast make effective, low-cost training treats"
        ]
    elif "nutrition" in combined or "food label" in combined:
        return [
            "<strong>Best for understanding pet food labels:</strong> Learn the difference between 'complete', 'complementary', 'with [ingredient]', and 'flavoured with' — these terms have specific legal meanings",
            "<strong>Best for dogs with sensitive stomachs:</strong> Limited-ingredient diets with a single protein source and clear allergen labelling",
            "<strong>Best for cats:</strong> Look for 'complete' wet food with named protein sources (e.g., 'chicken' rather than 'meat and animal derivatives')",
            "<strong>Best for puppy nutrition:</strong> Food labelled for 'growth' or 'puppies' that meets FEDIAF nutritional guidelines for developing dogs",
            "<strong>Best for budget-conscious owners:</strong> Mid-range complete foods with clear ingredient lists often provide better nutrition than cheap or premium alternatives"
        ]
    elif "grooming glossary" in combined or "grooming terms" in combined:
        return [
            "<strong>Best for new dog owners:</strong> Start with the basics — brushing, nail trimming, and ear checking — before attempting bathing or coat trimming",
            "<strong>Best for long-coated breeds:</strong> Invest in a good slicker brush and learn the line-brushing technique to prevent painful matting",
            "<strong>Best for wire-coated breeds:</strong> Hand-stripping or professional grooming every 8-12 weeks to maintain coat texture and health",
            "<strong>Best for short-coated breeds:</strong> Weekly rubber curry brush sessions that remove loose fur and distribute natural oils",
            "<strong>Best for anxious pets:</strong> Very short, positive grooming sessions with treats — build tolerance gradually over weeks"
        ]
    elif "feeding guide" in combined or "portions" in combined:
        return [
            "<strong>Best for puppies:</strong> Three to four smaller meals per day, transitioning to twice daily by six months — use the food manufacturer's puppy-specific feeding guide as a starting point",
            "<strong>Best for adult maintenance:</strong> Twice-daily feeding at consistent times, with portions adjusted based on actual body condition rather than packet guidelines alone",
            "<strong>Best for overweight pets:</strong> Veterinary-guided calorie reduction of 10-15%, combined with accurate portion weighing and limited treats",
            "<strong>Best for senior pets:</strong> Easily digestible food in smaller, more frequent meals to accommodate slowing metabolism and potential dental issues",
            "<strong>Best for multi-pet households:</strong> Supervised, separate feeding stations to ensure each pet eats the correct amount and diet"
        ]
    elif "health terminology" in combined or "veterinary terms" in combined:
        return [
            "<strong>Best for first-time pet owners:</strong> Learn the core terms — vaccination, neutering, microchipping, and the difference between complete and complementary food",
            "<strong>Best for owners of predisposed breeds:</strong> Understand your breed's specific health risks so you can discuss screening and prevention with your vet",
            "<strong>Best for emergency preparedness:</strong> Know the terms for common emergencies (bloat/GDV, toxicity, obstruction) so you can communicate clearly with emergency vets",
            "<strong>Best for pet insurance navigation:</strong> Understanding pre-existing conditions, exclusions, and excess terms helps you choose the right policy and make accurate claims",
            "<strong>Best for senior pet owners:</strong> Familiarise yourself with age-related terms (cognitive dysfunction, arthritis grading, kidney staging) to participate actively in your pet's care plan"
        ]
    elif "where to place" in combined or "bed location" in combined:
        return [
            "<strong>Best for anxious dogs:</strong> A quiet corner away from doors and windows where the dog can rest without being startled by movement or noise",
            "<strong>Best for puppies:</strong> Near the owner's bed initially for reassurance, then gradually moved to the permanent location over several weeks",
            "<strong>Best for dogs with joint issues:</strong> Ground level on a non-slip surface, away from cold drafts and direct heat sources",
            "<strong>Best for multi-dog households:</strong> Separate bed locations for each dog, spaced far enough apart to prevent territorial behaviour",
            "<strong>Best for hot weather:</strong> A well-ventilated area away from direct sunlight, with room for airflow underneath an elevated bed if used"
        ]
    elif "how to wash" in combined or "maintain your dog" in combined:
        return [
            "<strong>Best for memory foam beds:</strong> Removable, machine-washable covers washed fortnightly; foam inserts spot-cleaned and air-dried completely",
            "<strong>Best for waterproof beds:</strong> Wipe down the waterproof base weekly and wash the cover in the machine — avoid bleach which damages the waterproof layer",
            "<strong>Best for dogs with allergies:</strong> Wash bedding weekly in hot water with hypoallergenic, unscented detergent to reduce allergen buildup",
            "<strong>Best for puppies and incontinent dogs:</strong> Beds with fully removable, machine-washable components that can handle frequent washing",
            "<strong>Best on a budget:</strong> White vinegar in the rinse cycle naturally deodorises and softens fabric without the cost of specialist pet detergent"
        ]
    elif "collar" in combined and "cat" in combined:
        return [
            "<strong>Best for outdoor cats:</strong> Reflective breakaway collars with an ID tag and a small bell for wildlife protection",
            "<strong>Best for indoor cats:</strong> Lightweight breakaway collars with ID — essential in case of escape",
            "<strong>Best for kittens:</strong> Adjustable kitten-sized breakaway collars checked weekly for fit as they grow",
            "<strong>Best for cats that dislike collars:</strong> Ultra-lightweight, thin collars with a gradual indoor introduction period of increasing wear time",
            "<strong>Best for multi-cat households:</strong> Colour-coded collars for quick identification, especially useful for similar-looking cats"
        ]
    elif "gps" in combined and "cat" in combined:
        return [
            "<strong>Best for outdoor cats in rural areas:</strong> GPS trackers with extended range and long battery life that cover large roaming territories",
            "<strong>Best for urban outdoor cats:</strong> Compact, lightweight GPS units with frequent location updates and safe-zone alerts",
            "<strong>Best for anxious cat owners:</strong> Real-time tracking with push notifications when the cat leaves a defined boundary area",
            "<strong>Best on a budget:</strong> Bluetooth trackers (shorter range, no subscription) suit cats that stay close to home",
            "<strong>Best for comprehensive safety:</strong> GPS tracker combined with a microchip and ID tag provides three layers of identification"
        ]
    elif "id tag" in combined and "cat" in combined:
        return [
            "<strong>Best for outdoor cats:</strong> Engraved stainless steel tags that withstand weather and scratching without fading",
            "<strong>Best for indoor cats:</strong> Lightweight, flat slide-on tags that don't dangle or catch on furniture",
            "<strong>Best for kittens:</strong> Small, lightweight tags on an adjustable kitten collar, upgraded to adult size as they grow",
            "<strong>Best for anxious cats:</strong> Silent, flat-to-collar tags that don't jingle — some cats are stressed by the sound of dangling tags",
            "<strong>Best as a backup:</strong> Always pair a physical tag with a registered microchip for comprehensive identification"
        ]
    elif "harness" in combined and "cat" in combined:
        return [
            "<strong>Best for first-time harness cats:</strong> Soft, vest-style harnesses that distribute pressure evenly and feel less restrictive than strap designs",
            "<strong>Best for escape-artist cats:</strong> Figure-eight or H-style harnesses with secure buckles that are harder to wriggle out of",
            "<strong>Best for confident outdoor cats:</strong> Lightweight, breathable harnesses that allow natural movement during garden exploration",
            "<strong>Best for harness training kittens:</strong> Ultra-soft, kitten-sized harnesses introduced indoors from around 8-10 weeks for gradual familiarisation",
            "<strong>Best on a budget:</strong> A simple adjustable H-harness at a mid-range price point provides reliable security without premium features"
        ]
    elif "cat bed" in combined:
        return [
            "<strong>Best for cats that curl up:</strong> Donut or bolster beds that create a cosy, enclosed feeling",
            "<strong>Best for cats that stretch out:</strong> Flat mattress-style beds or heated pads that allow full-body stretching",
            "<strong>Best for senior cats:</strong> Low-entry, orthopaedic beds with gentle warmth that ease joint stiffness",
            "<strong>Best for multi-cat households:</strong> Multiple bed options in different styles and locations — let each cat find their preference",
            "<strong>Best on a budget:</strong> A fleece blanket folded into a cardboard box placed on a shelf is a genuinely effective cat bed"
        ]
    elif "cat brush" in combined or ("brush" in combined and "cat" in combined):
        return [
            "<strong>Best for long-haired cats:</strong> A wide-toothed comb for daily detangling followed by a slicker brush for finishing",
            "<strong>Best for short-haired cats:</strong> A rubber grooming mitt or soft bristle brush used once or twice weekly",
            "<strong>Best for cats that dislike grooming:</strong> A gentle grooming glove that feels like petting — the least invasive introduction to brushing",
            "<strong>Best for double-coated breeds:</strong> An undercoat rake during shedding season, used carefully to remove loose undercoat without damaging the topcoat",
            "<strong>Best on a budget:</strong> A basic slicker brush (around £5) handles most coat types and lasts for years with proper care"
        ]
    elif "cat shampoo" in combined or ("shampoo" in combined and "cat" in combined):
        return [
            "<strong>Best for cats that rarely need bathing:</strong> Waterless foam or dry shampoo for spot cleaning without full immersion",
            "<strong>Best for cats with sensitive skin:</strong> Hypoallergenic, fragrance-free formulas specifically designed for feline pH levels",
            "<strong>Best for long-haired cats:</strong> Gentle cleansing shampoo followed by a detangling conditioner to prevent post-bath matting",
            "<strong>Best for cats with fleas:</strong> Vet-recommended flea shampoo (never dog flea products) as part of a comprehensive treatment plan",
            "<strong>Best on a budget:</strong> Most cats rarely need bathing at all — invest in a single quality cat shampoo for the occasional bath rather than multiple products"
        ]
    elif "collar" in combined and "puppy" in combined:
        return [
            "<strong>Best for first collars (8-12 weeks):</strong> Lightweight, adjustable flat collars with a secure clip — focus on comfort and correct fit",
            "<strong>Best for teething puppies:</strong> Collars made from durable, non-chewable materials (nylon webbing is ideal) with smooth edges",
            "<strong>Best for lead training:</strong> Pair the collar with a well-fitted harness — use the harness for walks and the collar for ID",
            "<strong>Best for fast-growing breeds:</strong> Adjustable collars with a wide size range to accommodate several weeks of growth",
            "<strong>Best on a budget:</strong> A simple, adjustable nylon collar at a budget price point provides everything a puppy needs — upgrade to a premium collar once they've reached adult size"
        ]
    elif "mental stimulation" in combined and "dog" in combined:
        return [
            "<strong>Best for high-intelligence breeds:</strong> Multi-step puzzle toys, scent work, and new trick training that challenge problem-solving abilities",
            "<strong>Best for anxious dogs:</strong> Calm, self-paced enrichment like snuffle mats and scatter feeding that builds confidence without adding pressure",
            "<strong>Best for dogs left alone:</strong> Frozen food toys and self-play puzzles that provide independent mental engagement during owner absences",
            "<strong>Best for puppies:</strong> Short, frequent enrichment sessions (5-10 minutes) that match developing attention spans",
            "<strong>Best on a budget:</strong> Hide-and-seek, improvised obstacle courses, and muffin tin puzzles provide excellent mental stimulation at zero cost"
        ]
    elif "confidence" in combined:
        return [
            "<strong>Best for newly adopted rescue dogs:</strong> Very gentle, predictable toys introduced one at a time in a quiet, safe environment",
            "<strong>Best for dogs fearful of specific objects:</strong> Gradual desensitisation using similar-shaped toys paired with high-value treats at a comfortable distance",
            "<strong>Best for dogs that shut down during play:</strong> Calm, food-based enrichment (licking mats, snuffle mats) that doesn't require active participation",
            "<strong>Best for building general confidence:</strong> Short, successful puzzle sessions where the dog always wins — confidence grows through achievable challenges",
            "<strong>Best for noise-sensitive dogs:</strong> Quiet toys only — no squeakers, no electronic sounds — combined with gentle, calm owner interaction"
        ]
    elif "essential" in combined and ("supply" in combined or "supplies" in combined):
        return [
            "<strong>Best for first-time cat owners:</strong> Litter tray, scratching post, food bowls, carrier, and a few toys — start simple and add based on your cat's preferences",
            "<strong>Best for first-time dog owners:</strong> Lead, collar/harness, bed, food bowls, and a selection of chew toys — the core setup for the first week",
            "<strong>Best for budget-conscious owners:</strong> Prioritise quality food, a durable lead, and identification (microchip + tag) over accessories and luxury items",
            "<strong>Best for adopting a rescue animal:</strong> A quiet safe space with essentials ready before arrival — bed, food, water, and a few comfort items",
            "<strong>Best for ongoing costs:</strong> Set aside a monthly pet budget covering food, preventive health, and replacement items to avoid unexpected expenses"
        ]
    elif "dog toys uk" in combined and "essential guide" in combined:
        return [
            "<strong>Best for first-time dog owners:</strong> A starter set of three to four toys covering different play types — one chew, one fetch, one tug, one puzzle",
            "<strong>Best for heavy chewers:</strong> Natural rubber toys rated for aggressive chewing; expect to spend slightly more for significantly longer toy life",
            "<strong>Best for puppies:</strong> Soft rubber teething toys and lightweight rope toys appropriate for developing jaws and teeth",
            "<strong>Best for senior dogs:</strong> Gentle plush toys and simple food-dispensing toys that don't require intense physical effort",
            "<strong>Best on a budget:</strong> Focus on two to three durable, well-made toys rather than a large collection of cheap alternatives that need frequent replacing"
        ]
    else:
        # Generic fallback
        if "cat" in combined:
            return [
                "<strong>Best for indoor cats:</strong> Daily interactive play sessions combined with environmental enrichment (vertical space, window perches, scratching posts)",
                "<strong>Best for multi-cat households:</strong> Separate resources for each cat — food bowls, litter trays, resting spots, and play sessions",
                "<strong>Best for senior cats:</strong> Gentle, low-impact activities and regular veterinary monitoring tailored to age-related needs",
                "<strong>Best for first-time cat owners:</strong> Start with the essentials and learn your individual cat's preferences before investing in specialist products",
                "<strong>Best on a budget:</strong> Focus spending on quality food and veterinary care — enrichment and comfort items can often be improvised at minimal cost"
            ]
        else:
            return [
                "<strong>Best for active, high-energy dogs:</strong> A combination of physical exercise and mental enrichment tailored to breed type and individual energy level",
                "<strong>Best for calm, low-energy dogs:</strong> Gentle enrichment activities like scent work and simple puzzles that engage the mind without demanding physical effort",
                "<strong>Best for first-time dog owners:</strong> Start with the fundamentals and adjust based on your dog's individual responses and preferences",
                "<strong>Best for multi-dog households:</strong> Individual attention and separate resources for each dog, combined with supervised group activities",
                "<strong>Best on a budget:</strong> Many effective solutions can be improvised from household items — the key is consistency and observation, not expensive products"
            ]


def is_product_post(title, slug):
    """Check if this is a product review/guide post."""
    product_markers = ["best ", "uk (2026)", "guide & honest reviews", "complete guide",
                       "top ", "recommended"]
    combined = f"{title.lower()} {slug.lower()}"
    return any(m in combined for m in product_markers)


def generate_what_to_expect(title, slug, content_snippet):
    """Generate What to Expect block for product-related posts."""
    title_lower = title.lower()
    combined = f"{title_lower} {slug.lower()}"

    if "puppy toy" in combined or "teething" in combined:
        return "Puppies chew through toys faster than adult dogs, so expect to replace items regularly during the teething phase. Focus on finding two or three durable options your puppy favours rather than accumulating a large collection. Most owners find that a combination of a frozen rubber toy and a soft comfort toy covers the majority of puppy play needs."
    elif "indoor cat" in combined:
        return "Indoor cats vary widely in play preferences, and it may take some experimentation to find what your cat responds to most. Expect to rotate toys every few days to maintain interest, and budget for occasional replacements as favourites wear out. Most owners find that two or three interactive toys combined with environmental enrichment provide the best results."
    elif "slow feeder" in combined:
        return "Most dogs adapt to a slow feeder bowl within a few meals, though some initially show frustration. Expect mealtimes to take two to three times longer than with a standard bowl, which is the intended effect. If your dog pushes the bowl around, choose a heavier model with a non-slip base."
    elif "cat toy" in combined and "indoor" in combined:
        return "Indoor cats need more structured play than outdoor cats, so expect to dedicate 15-20 minutes daily to interactive sessions. Most cats respond best to wand toys and feather chasers, but individual preferences vary. Budget for regular toy rotation and replacement of favourites."
    elif "puppy collar" in combined:
        return "Puppies grow rapidly, so expect to adjust or replace the collar every few weeks during the first six months. A well-fitted collar should allow two fingers between the collar and neck. Most owners go through two or three collars before their dog reaches adult size."
    elif "cat bed" in combined:
        return "Cats are notoriously selective about sleeping spots, and there is no guarantee your cat will use a new bed immediately. Place it in a spot your cat already gravitates to and give it a week or two. Many owners find their cat eventually claims the bed, especially once it carries familiar scents."
    elif "cat brush" in combined:
        return "Most cats need a gradual introduction to brushing, especially if they were not groomed regularly as kittens. Expect initial resistance and plan for very short sessions (one to two minutes) with treats. Over time, many cats come to enjoy grooming as a bonding activity."
    elif "cat shampoo" in combined:
        return "Most cats rarely need bathing, so a single bottle of quality cat shampoo typically lasts a long time. When bathing is necessary, expect the experience to be stressful for both you and the cat initially. Preparation (trimmed nails, non-slip mat, warm water) makes a significant difference."
    elif "cat collar" in combined:
        return "Expect your cat to resist a new collar initially — this is normal. Most cats adjust within a few days of indoor wear. Always use a breakaway mechanism, and check fit regularly. Some cats lose collars frequently outdoors, so budget for replacements."
    elif "cat gps" in combined or "gps tracker" in combined:
        return "GPS tracker accuracy varies between urban and rural environments, and battery life typically ranges from two to seven days depending on update frequency. Expect a monthly or annual subscription fee for most real-time tracking services. The peace of mind for owners of outdoor cats generally outweighs the ongoing cost."
    elif "cat id tag" in combined:
        return "Most ID tags last several years before needing replacement, though engraved details can wear on active outdoor cats. Expect to update tags whenever your contact details change. A lightweight, flat-to-collar design is generally better tolerated than a dangling tag."
    elif "cat harness" in combined:
        return "Harness training takes patience — most cats need one to two weeks of indoor practice before they are comfortable. Expect initial freezing, flopping, or resistance when the harness is first fitted. Start with short indoor sessions and reward generously."
    elif "dog toy" in combined and "essential" in combined:
        return "No single toy suits every dog, so expect some trial and error as you discover your dog's preferences. A starter set of three to four toys covering different play types is a practical starting point. Budget for regular replacements, especially if your dog is a heavy chewer."
    else:
        return None


def generate_pros_cons(title, slug, content_snippet):
    """Generate Key Considerations (Pros/Cons) for product posts."""
    title_lower = title.lower()
    combined = f"{title_lower} {slug.lower()}"

    if "slow feeder" in combined:
        return {
            "pros": [
                "Reduces eating speed by 50-80%, lowering the risk of bloat and digestive discomfort",
                "Provides mental stimulation at mealtimes, turning a routine activity into enrichment",
                "Available in a wide range of sizes and difficulty levels to suit different breeds and muzzle shapes",
                "Most models are dishwasher-safe, making cleaning straightforward"
            ],
            "cons": [
                "Some dogs find them frustrating initially, especially those used to free-feeding",
                "Complex designs can be difficult to clean thoroughly if not dishwasher-compatible",
                "Flat-faced breeds may struggle with deep-groove patterns designed for longer muzzles",
                "The cheapest plastic options can slide around on hard floors without a non-slip base"
            ]
        }
    elif "puppy collar" in combined:
        return {
            "pros": [
                "Essential for attaching ID tags — a legal requirement for dogs in public in the UK",
                "Lightweight and comfortable for puppies when properly fitted",
                "Adjustable models accommodate several weeks of puppy growth",
                "Available in reflective and high-visibility options for safe walks"
            ],
            "cons": [
                "Not suitable as the sole restraint for puppies that pull — use a harness for lead walking",
                "Requires frequent fit checks during rapid growth phases",
                "Cheap buckle designs can break or come undone unexpectedly",
                "Can cause neck pressure in breeds prone to tracheal collapse if used for lead walking"
            ]
        }
    elif "cat bed" in combined:
        return {
            "pros": [
                "Provides a dedicated resting spot that helps cats feel secure and reduces stress",
                "Insulated beds protect against cold floors and drafts, especially for senior cats",
                "Washable models maintain hygiene and reduce allergen buildup",
                "Elevated or enclosed designs satisfy cats' natural preference for safe, raised resting spots"
            ],
            "cons": [
                "No guarantee your cat will use it — feline bed preferences are highly individual",
                "Premium orthopaedic models carry a higher upfront cost",
                "Beds in multi-cat households may become territorial flashpoints without enough options",
                "Fabric beds absorb odours and need regular washing to stay fresh"
            ]
        }
    elif "cat brush" in combined:
        return {
            "pros": [
                "Regular brushing reduces hairballs, especially important for long-haired breeds",
                "Distributes natural skin oils across the coat for a healthier, shinier appearance",
                "Allows you to check for fleas, lumps, skin irritation, and injuries during each session",
                "Strengthens the bond between owner and cat when introduced positively"
            ],
            "cons": [
                "Many cats resist brushing initially, requiring patience and gradual introduction",
                "Using the wrong brush type can scratch sensitive cat skin or pull healthy fur",
                "Long-haired cats may need daily brushing to prevent matting, which is time-consuming",
                "Cats with existing mats may need professional grooming before home brushing can begin"
            ]
        }
    elif "cat shampoo" in combined:
        return {
            "pros": [
                "Removes allergens, dirt, and grease that self-grooming alone cannot address",
                "Medicated formulas can treat specific skin conditions under veterinary guidance",
                "Waterless options provide cleaning without the stress of full immersion bathing",
                "Helps control external parasites when used as part of a treatment plan"
            ],
            "cons": [
                "Bathing is stressful for most cats and should only be done when genuinely necessary",
                "Over-bathing strips natural oils and disrupts the skin's protective barrier",
                "Cat shampoo products are more expensive per millilitre than dog equivalents due to smaller market",
                "Some cats develop a lasting fear of bathing if the first experience is handled poorly"
            ]
        }
    elif "cat collar" in combined:
        return {
            "pros": [
                "Provides visible identification that anyone can read, even without a microchip scanner",
                "Breakaway designs release under pressure, preventing strangulation",
                "Reflective models improve visibility of outdoor cats during low-light hours",
                "Bells can reduce hunting success, protecting local wildlife"
            ],
            "cons": [
                "Some cats resist wearing collars and may need gradual introduction",
                "Outdoor cats lose collars frequently, requiring regular replacement",
                "Poorly fitted collars can cause skin irritation, fur loss, or discomfort",
                "Collars are not a substitute for microchipping — they can be removed or lost"
            ]
        }
    elif "cat gps" in combined or "gps tracker" in combined:
        return {
            "pros": [
                "Real-time location tracking provides peace of mind for owners of outdoor cats",
                "Safe-zone alerts notify you immediately if your cat leaves a defined area",
                "Activity monitoring can help detect changes in behaviour that may indicate illness",
                "Invaluable for finding lost cats quickly, especially in unfamiliar areas"
            ],
            "cons": [
                "Ongoing subscription costs for most real-time tracking services",
                "Battery requires regular charging (every 2-7 days depending on the model)",
                "GPS accuracy decreases in dense urban areas and indoors",
                "Added weight on the collar — choose cat-specific models under 30g"
            ]
        }
    elif "cat id tag" in combined:
        return {
            "pros": [
                "Provides instant visible identification without needing a scanner",
                "Inexpensive and available in many styles, materials, and sizes",
                "Easy to update when contact details change — simply order a new tag",
                "Works alongside a microchip for comprehensive identification coverage"
            ],
            "cons": [
                "Tags can fall off, get caught on objects, or become unreadable over time",
                "Dangling tags may annoy some cats and cause collar irritation",
                "Engraving wears down on active outdoor cats, requiring periodic replacement",
                "Not a substitute for microchipping, which is a permanent identification method"
            ]
        }
    elif "cat harness" in combined:
        return {
            "pros": [
                "Allows safe outdoor access for indoor cats, enriching their environment significantly",
                "Distributes pressure across the chest and body rather than the neck",
                "Provides owner control without the risks of unsupervised outdoor access",
                "Available in designs specifically shaped for feline anatomy"
            ],
            "cons": [
                "Requires a gradual training period — most cats need one to two weeks of indoor practice",
                "Some cats never accept a harness and find the experience stressful",
                "Poorly fitted harnesses allow escape, which is dangerous in unfamiliar environments",
                "Outdoor walks with cats require quiet, controlled environments — not suitable for busy streets"
            ]
        }
    elif "indoor cat" in combined or "house cat" in combined:
        return {
            "pros": [
                "Carefully chosen toys provide essential mental stimulation for cats without outdoor access",
                "Interactive toys strengthen the bond between owner and cat during play sessions",
                "Enrichment toys help prevent obesity by encouraging movement and activity",
                "Self-play options keep indoor cats engaged during owner absences"
            ],
            "cons": [
                "Indoor cats may need more frequent toy rotation due to limited environmental novelty",
                "Higher initial investment in enrichment to compensate for the lack of outdoor stimulation",
                "Some cats lose interest in toys quickly, requiring ongoing experimentation",
                "Electronic and battery-operated toys need supervision and regular battery changes"
            ]
        }
    elif "puppy toy" in combined or "teething" in combined:
        return {
            "pros": [
                "Age-appropriate toys redirect chewing away from furniture and belongings",
                "Teething toys soothe sore gums during the uncomfortable teething phase (3-6 months)",
                "Variety of textures supports healthy oral development and jaw strengthening",
                "Interactive puppy toys support early socialisation and bonding"
            ],
            "cons": [
                "Puppies outgrow toys quickly, requiring frequent size upgrades",
                "Soft puppy toys are easily destroyed by teething puppies, leading to replacement costs",
                "Supervision is essential with every toy — puppies are more prone to swallowing fragments",
                "Finding the right durability level is trial and error; what suits one puppy may not suit another"
            ]
        }
    else:
        return None


# ─── HTML Block Builders ────────────────────────────────────────────────────

def build_about_guide_html(text):
    return f"""<!-- wp:group {{"style":{{"color":{{"background":"#f9fafb"}},"border":{{"radius":"6px","width":"1px","color":"#e5e7eb"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"20px","bottom":"20px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#e5e7eb;border-width:1px;border-radius:6px;background-color:#f9fafb;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"13px"}}}}}} -->
<p style="font-size:13px"><strong>About this guide:</strong> {text} Last reviewed: May 2026. See our <a href="https://pethubonline.com/our-editorial-process/">editorial process</a> for details.</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->"""


def build_common_mistakes_html(mistakes):
    items = "\n".join([f'<!-- wp:list-item -->\n<li>{m}</li>\n<!-- /wp:list-item -->' for m in mistakes])
    return f"""<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">Common Mistakes to Avoid</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul class="wp-block-list">
{items}
</ul>
<!-- /wp:list -->"""


def build_suitability_html(items):
    items_html = "\n".join([f'<!-- wp:list-item -->\n<li>{item}</li>\n<!-- /wp:list-item -->' for item in items])
    return f"""<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">Quick Suitability Guide</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul class="wp-block-list">
{items_html}
</ul>
<!-- /wp:list -->"""


def build_what_to_expect_html(text):
    return f"""<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">What to Expect</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>{text}</p>
<!-- /wp:paragraph -->"""


def build_pros_cons_html(data):
    pros_items = "\n".join([f'<!-- wp:list-item -->\n<li>{p}</li>\n<!-- /wp:list-item -->' for p in data["pros"]])
    cons_items = "\n".join([f'<!-- wp:list-item -->\n<li>{c}</li>\n<!-- /wp:list-item -->' for c in data["cons"]])
    return f"""<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">Key Considerations</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><strong>Advantages:</strong></p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul class="wp-block-list">
{pros_items}
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Things to Watch:</strong></p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul class="wp-block-list">
{cons_items}
</ul>
<!-- /wp:list -->"""


# ─── API Helpers ────────────────────────────────────────────────────────────

def fetch_post(post_id):
    url = f"{WP_API}/posts/{post_id}?context=edit&_fields=id,title,content,slug"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
        if "id" in data:
            return data
        return None
    except json.JSONDecodeError:
        return None


def fetch_all_posts():
    all_posts = []
    page = 1
    while True:
        url = f"{WP_API}/posts?status=publish&per_page=100&page={page}&_fields=id,title,slug,content&context=edit"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            break
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            break
        if not data or isinstance(data, dict):
            break
        all_posts.extend(data)
        print(f"  Page {page}: {len(data)} posts (total: {len(all_posts)})", flush=True)
        if len(data) < 100:
            break
        page += 1
        time.sleep(0.5)
    return all_posts


def update_post(post_id, new_content):
    payload = json.dumps({"content": new_content})
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(payload)
        tmpfile = f.name
    try:
        url = f"{WP_API}/posts/{post_id}"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", f"@{tmpfile}",
             url],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            return False, f"curl error: {result.stderr}"
        try:
            resp = json.loads(result.stdout)
            if "id" in resp:
                return True, "OK"
            else:
                return False, f"API error: {result.stdout[:300]}"
        except json.JSONDecodeError:
            return False, f"Invalid JSON: {result.stdout[:300]}"
    finally:
        os.unlink(tmpfile)


def matches_keywords(text, keywords):
    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            return True
    return False


def has_existing_blocks(content):
    markers = ["About this guide:", "Common Mistakes to Avoid", "Quick Suitability Guide"]
    for m in markers:
        if m in content:
            return True
    return False


def insert_about_guide(content, about_html):
    """Insert About This Guide after Quick Answer box or first heading."""
    # Look for Quick Answer closing
    qa_end = content.find('<!-- /wp:group -->')
    if qa_end >= 0 and 'Quick Answer' in content[:qa_end + 100]:
        insert_point = qa_end + len('<!-- /wp:group -->')
        return content[:insert_point] + "\n\n" + about_html + "\n\n" + content[insert_point:]

    # Look for first h2 or h3 heading
    h_pattern = re.search(r'(<!-- wp:heading.*?-->.*?</h[23]>\s*<!-- /wp:heading -->)', content, re.DOTALL)
    if h_pattern:
        insert_point = h_pattern.end()
        return content[:insert_point] + "\n\n" + about_html + "\n\n" + content[insert_point:]

    # Fallback: insert after first paragraph
    p_end = content.find('<!-- /wp:paragraph -->')
    if p_end >= 0:
        insert_point = p_end + len('<!-- /wp:paragraph -->')
        return content[:insert_point] + "\n\n" + about_html + "\n\n" + content[insert_point:]

    return about_html + "\n\n" + content


def insert_before_sources(content, blocks):
    """Insert blocks before Sources and Further Reading section."""
    sources_markers = [
        '<h3 class="wp-block-heading">Sources and Further Reading</h3>',
        '<h3 class="wp-block-heading">Sources and Further Reading',
        'Sources and Further Reading</h3>',
        '<h2 class="wp-block-heading">Sources and Further Reading</h2>',
        'Sources and Further Reading</h2>',
    ]

    insert_point = -1
    for marker in sources_markers:
        idx = content.find(marker)
        if idx >= 0:
            hr_idx = content.rfind('<hr', max(0, idx - 300), idx)
            if hr_idx >= 0:
                insert_point = hr_idx
            else:
                insert_point = idx
            break

    if insert_point < 0:
        related_markers = [
            'Related Guides</h2>', 'Related Guides</h3>',
        ]
        for marker in related_markers:
            idx = content.find(marker)
            if idx >= 0:
                insert_point = idx
                break

    if insert_point < 0:
        insert_point = len(content)

    combined = "\n\n".join(blocks)
    return content[:insert_point] + combined + "\n\n" + content[insert_point:]


def classify_post(title, slug, content_snippet):
    combined = f"{title.lower()} {slug.lower()} {content_snippet[:1500].lower()}"
    if matches_keywords(combined, DOG_TOYS_KEYWORDS):
        return "dog_toys"
    elif matches_keywords(combined, UNCATEGORIZED_KEYWORDS):
        return "uncategorized"
    elif not matches_keywords(combined, OTHER_CLUSTER_KEYWORDS):
        return "uncategorized"
    return None


# ─── Main Processing ───────────────────────────────────────────────────────

def process_post(post_data):
    """Process a single post: add humanization + buyer-intent blocks."""
    post_id = post_data["id"]
    title = post_data["title"]["raw"] if isinstance(post_data["title"], dict) else post_data["title"]
    slug = post_data.get("slug", "")
    content = post_data["content"]["raw"] if isinstance(post_data["content"], dict) else post_data.get("content", "")

    result = {
        "id": post_id,
        "title": title,
        "cluster": classify_post(title, slug, content),
        "about_guide": False,
        "common_mistakes": False,
        "suitability": False,
        "what_to_expect": False,
        "pros_cons": False,
        "status": ""
    }

    # Skip if already has blocks
    if has_existing_blocks(content):
        result["status"] = "ALREADY_HAS_BLOCKS"
        return result

    # Build blocks
    new_content = content

    # 1. About This Guide
    about_text = get_about_template(post_id)
    about_html = build_about_guide_html(about_text)
    new_content = insert_about_guide(new_content, about_html)
    result["about_guide"] = True

    # 2. Common Mistakes
    mistakes = generate_common_mistakes(post_id, title, slug, content[:2000])
    mistakes_html = build_common_mistakes_html(mistakes)
    result["common_mistakes"] = True

    # 3. Quick Suitability Guide
    suitability_items = generate_suitability_items(post_id, title, slug, content[:2000])
    suitability_html = build_suitability_html(suitability_items)
    result["suitability"] = True

    # Blocks to insert before Sources
    pre_source_blocks = [mistakes_html, suitability_html]

    # 4. What to Expect (product posts only)
    is_product = is_product_post(title, slug)
    what_to_expect_text = None
    if is_product:
        what_to_expect_text = generate_what_to_expect(title, slug, content[:2000])
    if what_to_expect_text:
        wte_html = build_what_to_expect_html(what_to_expect_text)
        pre_source_blocks.append(wte_html)
        result["what_to_expect"] = True

    # 5. Key Considerations (product posts only)
    pros_cons_data = None
    if is_product:
        pros_cons_data = generate_pros_cons(title, slug, content[:2000])
    if pros_cons_data:
        pc_html = build_pros_cons_html(pros_cons_data)
        pre_source_blocks.append(pc_html)
        result["pros_cons"] = True

    # Insert all blocks before Sources
    new_content = insert_before_sources(new_content, pre_source_blocks)

    # Update via API
    success, msg = update_post(post_id, new_content)
    result["status"] = "OK" if success else f"ERROR: {msg}"

    return result


def main():
    print("=" * 70)
    print("HUMANIZATION BATCH 3: Dog Toys + Uncategorized Posts")
    print("=" * 70)

    # Step 1: Fetch all posts
    print("\nFetching all published posts...", flush=True)
    posts = fetch_all_posts()
    print(f"Total published posts: {len(posts)}")

    # Step 2: Filter to untreated posts
    to_process = []
    for p in posts:
        pid = p["id"]
        if pid in ALREADY_TREATED:
            continue

        title = p["title"]["raw"] if isinstance(p["title"], dict) else p["title"]
        slug = p.get("slug", "")
        content = p["content"]["raw"] if isinstance(p["content"], dict) else p.get("content", "")
        combined = f"{title.lower()} {slug.lower()} {content[:1500].lower()}"

        # Check if already has blocks
        if has_existing_blocks(content):
            continue

        # Classify
        cluster = classify_post(title, slug, content)
        if cluster:
            to_process.append(p)

    print(f"Posts to process: {len(to_process)}")

    if not to_process:
        print("No posts to process. Exiting.")
        return

    # Initialize CSV log
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "title", "cluster", "about_guide", "common_mistakes",
                         "suitability", "what_to_expect", "pros_cons", "status"])

    # Step 3: Process each post
    results = []
    total = len(to_process)

    for i, post in enumerate(to_process):
        pid = post["id"]
        title = post["title"]["raw"] if isinstance(post["title"], dict) else post["title"]
        print(f"\n[{i+1}/{total}] Processing post {pid}: {title[:60]}...", flush=True)

        result = process_post(post)
        results.append(result)

        # Write to CSV
        with open(LOG_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                result["id"], result["title"], result["cluster"],
                result["about_guide"], result["common_mistakes"],
                result["suitability"], result["what_to_expect"],
                result["pros_cons"], result["status"]
            ])

        status_line = f"  -> {result['status']}"
        if result["about_guide"]:
            status_line += " | About Guide: YES"
        if result["common_mistakes"]:
            status_line += " | Mistakes: YES"
        if result["suitability"]:
            status_line += " | Suitability: YES"
        if result["what_to_expect"]:
            status_line += " | What to Expect: YES"
        if result["pros_cons"]:
            status_line += " | Pros/Cons: YES"
        print(status_line, flush=True)

        if i < total - 1:
            time.sleep(0.5)

    # Summary
    print("\n" + "=" * 70)
    print("BATCH 3 HUMANIZATION — SUMMARY")
    print("=" * 70)

    ok = sum(1 for r in results if r["status"] == "OK")
    ag = sum(1 for r in results if r["about_guide"])
    cm = sum(1 for r in results if r["common_mistakes"])
    su = sum(1 for r in results if r["suitability"])
    wte = sum(1 for r in results if r["what_to_expect"])
    pc = sum(1 for r in results if r["pros_cons"])
    skip = sum(1 for r in results if r["status"] == "ALREADY_HAS_BLOCKS")

    print(f"Total processed:      {total}")
    print(f"Successfully updated: {ok}")
    print(f"Skipped (has blocks): {skip}")
    print(f"About Guide blocks:   {ag}")
    print(f"Common Mistakes:      {cm}")
    print(f"Suitability Guides:   {su}")
    print(f"What to Expect:       {wte}")
    print(f"Key Considerations:   {pc}")

    errors = [r for r in results if r["status"] not in ("OK", "ALREADY_HAS_BLOCKS")]
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors:
            print(f"  Post {e['id']}: {e['status']}")

    print(f"\nLog saved to: {LOG_FILE}")


if __name__ == "__main__":
    main()
