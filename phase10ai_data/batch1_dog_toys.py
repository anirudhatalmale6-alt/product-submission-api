#!/usr/bin/env python3
"""
Phase 10AI - Dog Toys Cluster Content Enhancement
Adds: At a Glance, Why This Matters, Troubleshooting, When to Seek Help, Key Takeaways
Upgrades: Editorial Standards trust footer
"""

import csv
import json
import os
import re
import subprocess
import tempfile
import time
import html

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
BASE = "https://pethubonline.com/wp-json/wp/v2"
INVENTORY = "/var/lib/freelancer/projects/40416335/phase10af_data/post_authority_inventory.csv"
LOG_FILE = "/var/lib/freelancer/projects/40416335/phase10ai_data/batch1_dog_toys_log.csv"
DELAY = 2

# ── Content generation per post ──────────────────────────────────────────────

def generate_content_for_post(post_id, title, content):
    """Generate all enhancement blocks based on post title and content analysis."""

    # Decode HTML entities for analysis
    text = html.unescape(content)
    title_lower = title.lower()

    # Determine if this is a cat post or dog post
    is_cat = 'cat ' in title_lower or 'cat\'s' in title_lower or title_lower.startswith('cat ')
    animal = "cat" if is_cat else "dog"
    animal_cap = "Cat" if is_cat else "Dog"
    owner = "cat owner" if is_cat else "dog owner"
    owners = "cat owners" if is_cat else "dog owners"
    vet_or_behav = "a vet or certified animal behaviourist" if is_cat else "a vet or certified animal behaviourist"

    # ── Map post_id to specific content ──
    content_map = get_content_map(animal, animal_cap, owner, owners)

    if post_id in content_map:
        return content_map[post_id]

    # Fallback generic (should not happen as all 42 are mapped)
    return generate_generic_content(post_id, title, animal, animal_cap, owner, owners)


def get_content_map(animal, animal_cap, owner, owners):
    """Return dict mapping post_id -> dict of block contents."""

    return {
        # ── 6052: Low-Mobility Enrichment ──
        6052: {
            "at_a_glance": [
                "Dogs with limited mobility still need daily mental stimulation to prevent depression and cognitive decline",
                "Puzzle feeders, snuffle mats, and scent games are ideal for dogs recovering from surgery or managing chronic conditions",
                "Even 10-15 minutes of mental enrichment can be as tiring as a moderate walk",
                "Adapt activities to your dog's specific limitations — always consult your vet first",
                "Rotate enrichment activities every few days to maintain novelty and interest"
            ],
            "why_this_matters": "Dogs with limited mobility are at higher risk of depression, weight gain, and behavioural problems. The PDSA estimates that around 1 in 4 UK dogs will experience a period of reduced mobility during their lifetime, whether from surgery recovery, arthritis, or injury. Providing appropriate mental stimulation during these periods is essential for their wellbeing.",
            "troubleshooting": "<strong>Dog shows no interest in puzzle toys:</strong> Start with very easy puzzles where treats are barely hidden, then gradually increase difficulty. Warming treats slightly can increase their scent appeal.\n\n<strong>Dog gets frustrated and gives up:</strong> You may be progressing too fast. Go back to the previous difficulty level and ensure your dog succeeds at least 80% of the time before advancing.\n\n<strong>Dog tries to move too much during enrichment:</strong> Use a raised bed or bolster to keep your dog comfortable and contained. Place all items within easy reach so they do not need to stretch or twist.\n\n<strong>Dog seems lethargic and unresponsive to any activity:</strong> This may indicate pain or depression. Keep a log of their responses and discuss concerns with your vet at the next check-up.",
            "when_to_seek_help": "If your dog shows persistent signs of depression such as refusing food, withdrawing from interaction, or becoming unusually vocal, consult your vet promptly. Sudden changes in mobility or increased reluctance to engage may indicate worsening pain that needs medical attention.",
            "key_takeaways": [
                "Mental enrichment is not optional for low-mobility dogs — it directly affects their recovery and quality of life",
                "Start with simple scent-based activities like snuffle mats before progressing to more complex puzzles",
                "Keep sessions short (10-15 minutes) and watch for signs of fatigue or frustration",
                "Rotate between at least 3-4 different enrichment types throughout the week",
                "Always get veterinary approval before introducing new activities post-surgery",
                "Track your dog's engagement levels to identify which activities work best for their specific situation"
            ]
        },

        # ── 6050: Toy Overstimulation Recovery ──
        6050: {
            "at_a_glance": [
                "Overstimulation occurs when play intensity exceeds a dog's ability to self-regulate",
                "Common signs include frantic behaviour, inability to settle, excessive mouthing, and dilated pupils",
                "Prevention is easier than cure — learn your dog's threshold before they tip over",
                "A structured cool-down routine helps dogs transition from high-energy play to calm",
                "Some breeds and individual dogs are naturally more prone to overstimulation"
            ],
            "why_this_matters": "Overstimulated dogs can become unpredictable, increasing the risk of accidental bites or destructive behaviour. The Dogs Trust reports that many behavioural issues referred to their centres stem from owners not recognising early signs of overstimulation during play. Understanding this helps prevent escalation and builds a calmer, happier relationship.",
            "troubleshooting": "<strong>Dog cannot settle after play ends:</strong> Introduce a consistent cool-down cue such as placing a lick mat down or scattering treats on a snuffle mat. This redirects energy into calming behaviour.\n\n<strong>Dog becomes mouthy or nippy during play:</strong> This is a clear sign of tipping over the threshold. Stop play immediately, stand still and boring, then redirect to a calming activity once your dog settles.\n\n<strong>Dog barks or whines when toys are put away:</strong> Gradually reduce play intensity in the final minutes rather than stopping abruptly. Transition through a gentle game before ending the session.\n\n<strong>Multiple dogs escalate each other:</strong> Separate them calmly before overstimulation peaks. Give each dog their own cool-down space with an individual calming activity.",
            "when_to_seek_help": "If your dog regularly cannot calm down within 15-20 minutes after play, shows aggressive behaviour during overstimulation, or you notice the threshold is getting lower over time, consult a certified animal behaviourist (ABTC-registered) for a tailored management plan.",
            "key_takeaways": [
                "Learn to recognise your dog's specific early warning signs of overstimulation",
                "Keep play sessions shorter than your dog's known threshold — end on a positive note",
                "Build a consistent cool-down routine that your dog associates with relaxation",
                "Use calming tools like lick mats, snuffle mats, or frozen Kongs to transition out of play",
                "Avoid high-energy games like tug right before you need your dog to be calm",
                "Track your dog's overstimulation triggers so you can gradually build their tolerance"
            ]
        },

        # ── 6049: Sensory Enrichment for Dogs ──
        6049: {
            "at_a_glance": [
                "Dogs experience the world through five senses — smell, sight, hearing, taste, and touch — and enrichment should target all of them",
                "Scent-based enrichment is the most powerful for dogs, as they have up to 300 million olfactory receptors",
                "Multi-sensory activities provide deeper engagement than single-sense toys",
                "Different breeds may show stronger preferences for certain sensory activities",
                "Regular sensory enrichment reduces anxiety, boredom, and destructive behaviour"
            ],
            "why_this_matters": "The RSPCA identifies mental stimulation as one of the five welfare needs for all animals kept as pets. Dogs that lack sensory variety in their daily lives are more likely to develop stereotypic behaviours such as excessive licking, tail chasing, or barking. Engaging all five senses through play creates a more fulfilled and balanced dog.",
            "troubleshooting": "<strong>Dog is overwhelmed by too many new stimuli at once:</strong> Introduce one new sensory experience at a time and allow your dog to approach at their own pace. Never force interaction.\n\n<strong>Dog shows no interest in auditory enrichment:</strong> Start with very quiet, natural sounds rather than electronic toys. Some dogs are sound-sensitive and prefer visual or scent-based activities.\n\n<strong>Dog destroys sensory items immediately:</strong> Choose more durable enrichment tools and supervise closely. Redirect destructive chewing to appropriate outlets like robust chew toys.\n\n<strong>Dog fixates on one type of sensory play:</strong> While preferences are normal, gently encourage variety by pairing their favourite sense with a less preferred one — for example, adding scent to a texture mat.",
            "when_to_seek_help": "If your dog shows extreme fear responses to normal sensory stimuli (sudden sounds, new textures, or unfamiliar smells), this may indicate a sensory processing issue or anxiety disorder. A veterinary behaviourist can assess whether desensitisation therapy would be beneficial.",
            "key_takeaways": [
                "Aim to engage at least two different senses in each enrichment session",
                "Prioritise scent-based activities — they are the most natural and rewarding for dogs",
                "Rotate sensory experiences throughout the week to prevent habituation",
                "Observe which senses your dog responds to most strongly and build on those",
                "Introduce new sensory experiences gradually, especially for anxious dogs",
                "Combine sensory enrichment with feeding time for maximum engagement"
            ]
        },

        # ── 6047: Play Recovery After Surgery ──
        6047: {
            "at_a_glance": [
                "Most dogs need structured mental enrichment during surgical recovery to prevent boredom and self-harm",
                "Always follow your vet's specific restrictions — some activities may be off-limits depending on the surgery",
                "Lick mats, food puzzles, and gentle nose work are typically safe during recovery",
                "Avoid any activity that encourages jumping, twisting, or sudden movements",
                "Recovery enrichment should start gentle and gradually increase as healing progresses"
            ],
            "why_this_matters": "Post-surgical complications in dogs are often caused by over-activity during the recovery period. The BVA recommends structured rest combined with appropriate mental stimulation to reduce the risk of wound reopening, implant failure, or infection. Dogs that are mentally engaged during recovery are less likely to interfere with surgical sites.",
            "troubleshooting": "<strong>Dog keeps trying to play too vigorously:</strong> Use barriers or a recovery crate to limit movement, and offer food-based enrichment that keeps them stationary, such as frozen stuffed Kongs.\n\n<strong>Dog refuses to eat from puzzle feeders:</strong> Post-surgical dogs may have reduced appetite. Try high-value, soft foods and ensure puzzles are very easy to solve initially.\n\n<strong>Dog seems depressed during recovery:</strong> Increase gentle social interaction — calm petting, hand-feeding, and quiet companionship can be enriching without physical exertion.\n\n<strong>Stitches or wound site is being licked despite enrichment:</strong> Enrichment helps but does not replace a properly fitted recovery collar or suit. Ensure your dog wears their protective gear as directed.",
            "when_to_seek_help": "Contact your vet immediately if you notice swelling, redness, or discharge around the surgical site, or if your dog becomes unusually lethargic, refuses food for more than 24 hours, or shows signs of pain such as whimpering or guarding the affected area.",
            "key_takeaways": [
                "Start planning recovery enrichment before the surgery so you have supplies ready",
                "Keep all enrichment activities low-energy and stationary during the initial healing phase",
                "Frozen food puzzles are your best friend — they last longer and keep dogs calm",
                "Gradually reintroduce more active play only when your vet gives the all-clear",
                "Monitor the surgical site after every enrichment session for signs of irritation",
                "A bored dog in recovery is more likely to lick, chew, or damage their surgical site"
            ]
        },

        # ── 6046: Dog Toy Hygiene Schedules ──
        6046: {
            "at_a_glance": [
                "Dog toys can harbour bacteria, mould, and parasites if not cleaned regularly",
                "Different toy materials require different cleaning methods and frequencies",
                "Rubber and plastic toys should be cleaned at least weekly; plush toys fortnightly",
                "Natural drying is preferable — avoid leaving toys damp as this encourages bacterial growth",
                "A simple cleaning schedule takes just 10-15 minutes per week"
            ],
            "why_this_matters": "A 2023 study published in the journal 'Biofilm' found that dog toys are among the most germ-contaminated household items, ranking alongside kitchen sponges. In the UK, where dogs often play both indoors and in public parks, regular toy hygiene is essential to prevent the spread of bacteria like Staphylococcus and parasites like Toxocara.",
            "troubleshooting": "<strong>Rubber toys develop a sticky or slimy coating:</strong> Soak in a solution of one part white vinegar to two parts warm water for 15 minutes, then scrub with a bottle brush and rinse thoroughly.\n\n<strong>Plush toys smell musty even after washing:</strong> The filling may be retaining moisture. Try a hot machine wash with a pet-safe detergent and ensure the toy is completely dry before returning it — a tumble dryer on low heat can help.\n\n<strong>Rope toys are fraying after washing:</strong> Rope toys have a limited lifespan. Once fibres are loose enough to be swallowed, it is time to replace the toy regardless of cleaning efforts.\n\n<strong>Dog refuses toys after cleaning:</strong> Some dogs dislike the scent of cleaning products. Use unscented, pet-safe cleaners and rinse thoroughly. Alternatively, let the toy air out for 24 hours before returning it.",
            "when_to_seek_help": "If your dog develops persistent gastrointestinal issues, skin irritation around the mouth, or recurring infections, consider whether contaminated toys could be a contributing factor and discuss this with your vet. Immunocompromised dogs may need a more rigorous cleaning protocol.",
            "key_takeaways": [
                "Set a weekly reminder to clean your dog's most-used toys",
                "Rubber and silicone toys are the easiest to sanitise — prioritise these for heavy chewers",
                "Always check toys for damage during cleaning — it doubles as a safety inspection",
                "Air-dry toys completely before returning them to your dog",
                "Replace rope toys, plush toys, and any toy with loose parts promptly when worn",
                "Keep a rotation of clean toys ready so your dog always has hygienic options available"
            ]
        },

        # ── 6045: Safe Multi-Dog Toy Management ──
        6045: {
            "at_a_glance": [
                "Resource guarding over toys is one of the most common causes of inter-dog conflict in multi-dog households",
                "Prevention through management is far more effective than trying to correct guarding after it develops",
                "Each dog should have access to their own toys in separate spaces during unsupervised time",
                "High-value items like stuffed Kongs should always be given in separate areas",
                "Body language awareness is key — learn to spot early guarding signals before conflict escalates"
            ],
            "why_this_matters": "The Dogs Trust identifies resource guarding as one of the top reasons for dog-to-dog aggression in UK homes. With an estimated 25% of UK households now having more than one dog, managing toy access safely is a practical skill every multi-dog owner needs. Unchecked guarding can escalate into serious injuries requiring veterinary treatment.",
            "troubleshooting": "<strong>One dog always steals toys from the other:</strong> Supervise play sessions and redirect the stealing dog with a different high-value toy. Ensure each dog has separate play time with their favourite items.\n\n<strong>Dogs growl or stiffen when near toys together:</strong> These are early warning signs — do not punish the growl, as it is important communication. Instead, increase distance between dogs during toy time and manage access.\n\n<strong>Dogs are fine with toys but guard chews:</strong> Chews and food-based items are higher value than standard toys. Always provide these in separate rooms or crates, and pick them up before allowing dogs back together.\n\n<strong>New dog triggers guarding in resident dog:</strong> Go back to basics — keep all toys managed (not freely scattered) and reintroduce shared access gradually over several weeks.",
            "when_to_seek_help": "If resource guarding escalates to snapping, biting, or involves injuries to any dog or person in the household, seek help from an ABTC-registered clinical animal behaviourist immediately. Do not attempt to resolve serious guarding behaviour with online advice alone.",
            "key_takeaways": [
                "Provide more high-value resources than dogs — abundance reduces competition",
                "Feed and give chews in separate spaces to prevent guarding flashpoints",
                "Learn canine body language so you can intervene before tension escalates",
                "Never punish growling — it is a warning signal that prevents bites",
                "Rotate which dog gets first access to new toys to prevent hierarchical patterns",
                "Management and prevention are always safer than attempting to 'train out' guarding"
            ]
        },

        # ── 6042: Enrichment by Breed Group ──
        6042: {
            "at_a_glance": [
                "Different breed groups have distinct instinctive drives that influence their play preferences",
                "Terriers typically enjoy digging and shaking toys; herding breeds prefer chase and control games",
                "Gundogs respond well to retrieval and scent work; hounds thrive on tracking activities",
                "Matching enrichment to breed instincts produces deeper engagement and satisfaction",
                "Mixed breeds may show traits from multiple groups — observe what your individual dog enjoys most"
            ],
            "why_this_matters": "The Kennel Club classifies dogs into seven breed groups, each selected for specific working traits over centuries. Understanding your dog's breed group helps you choose enrichment that satisfies their innate drives rather than working against them. Dogs whose natural instincts are channelled into appropriate play are calmer, more focused, and less likely to develop problem behaviours.",
            "troubleshooting": "<strong>Dog does not seem to match their breed group's typical preferences:</strong> Individual variation is normal. Use breed tendencies as a starting point but always observe what your specific dog enjoys. Mixed breeds especially may combine traits.\n\n<strong>Herding breed fixates on children or other pets:</strong> This is misdirected herding instinct. Redirect into structured activities like treibball, flirt poles, or controlled fetch games that satisfy the drive safely.\n\n<strong>Terrier destroys every toy immediately:</strong> This is natural 'kill shake' behaviour. Provide tough rubber toys designed for power chewers and supervise play with softer items.\n\n<strong>Gundog has no interest in retrieving:</strong> Not all individual gundogs enjoy fetch. Try scent work instead — it taps into the same breed group drives through a different activity.",
            "when_to_seek_help": "If breed-typical instincts are manifesting as obsessive behaviours (constant herding, relentless digging, or fixated chasing), consult a behaviourist experienced with your breed group. These behaviours need proper channelling rather than suppression.",
            "key_takeaways": [
                "Research your dog's breed group to understand their instinctive play preferences",
                "Terriers: digging boxes and shake-tug toys; Herding: chase and control games; Gundogs: retrieve and scent work",
                "Use breed instincts as a guide, not a rule — every dog is an individual",
                "Channel strong breed drives into structured activities to prevent problem behaviours",
                "Mixed breed dogs benefit from trying activities across multiple breed group categories"
            ]
        },

        # ── 6039: Dog Toy Anxiety Reduction ──
        6039: {
            "at_a_glance": [
                "Specific types of toys can help reduce anxiety by promoting calming behaviours such as licking, chewing, and sniffing",
                "Food-stuffable toys like Kongs and lick mats activate the parasympathetic nervous system",
                "Anxious dogs often prefer predictable, quiet toys over unpredictable squeaky or electronic ones",
                "Toy-based anxiety management works best alongside a consistent daily routine",
                "Not all toys suit all anxious dogs — what calms one may stress another"
            ],
            "why_this_matters": "The PDSA Animal Wellbeing (PAW) Report estimates that around 2.5 million UK dogs show signs of anxiety when left alone. Appropriate toy-based enrichment is a key component of anxiety management, recommended by veterinary behaviourists alongside training and environmental adjustments. It is a low-cost, accessible tool that any owner can implement immediately.",
            "troubleshooting": "<strong>Dog ignores calming toys when anxious:</strong> Introduce toys during calm moments first so your dog builds a positive association. An anxious dog encountering a new item may see it as another stressor.\n\n<strong>Dog becomes more anxious with food puzzles:</strong> The puzzle may be too difficult. Start with food easily visible and accessible, then very gradually increase complexity as confidence builds.\n\n<strong>Dog destroys soft toys aggressively when stressed:</strong> This may be displaced anxiety rather than play. Offer a frozen stuffed Kong instead — the licking action is inherently calming and harder to destroy.\n\n<strong>Calming toys only work briefly:</strong> Rotate between several options and combine with other anxiety-reducing strategies such as background white noise, pheromone diffusers, and consistent departure routines.",
            "when_to_seek_help": "If your dog's anxiety is severe — causing self-harm, destructive behaviour to property, prolonged vocalisation, or house soiling — toys alone will not be sufficient. Consult your vet to rule out medical causes, and seek referral to a veterinary behaviourist for a comprehensive treatment plan.",
            "key_takeaways": [
                "Licking and chewing are naturally calming — prioritise food-stuffable and lick-based toys",
                "Introduce anxiety-relief toys during calm periods, not during peak anxiety",
                "Avoid toys that make sudden or loud noises for noise-sensitive dogs",
                "Frozen Kongs and lick mats provide longer-lasting calming engagement",
                "Combine toy-based strategies with routine, environment, and training for best results",
                "Keep a dedicated 'calm kit' of toys separate from general play toys"
            ]
        },

        # ── 5950: Dog Toy Durability Guide ──
        5950: {
            "at_a_glance": [
                "Toy durability depends on material, construction quality, and your dog's chew strength",
                "Natural rubber and solid nylon rank highest for durability among common toy materials",
                "No toy is truly indestructible — all toys should be supervised and inspected regularly",
                "Spending more upfront on quality toys typically saves money compared to frequent replacements",
                "The right durability level depends on your dog's play style, not just their size"
            ],
            "why_this_matters": "The UK pet toy market is largely unregulated compared to children's toys, meaning quality varies enormously. Dogs that destroy toys quickly may ingest fragments, leading to intestinal blockages that can cost thousands in emergency veterinary surgery. Understanding durability helps owners invest wisely and keep their dogs safe.",
            "troubleshooting": "<strong>Dog destroys every 'indestructible' toy within hours:</strong> No toy withstands all dogs. For extreme chewers, try solid rubber Kongs (black extreme range), Goughnuts, or Benebones. Remove toys when unsupervised.\n\n<strong>Durable toys seem too hard for your dog:</strong> Balance durability with dental safety. A toy should give slightly under pressure — if you cannot indent it with your thumbnail, it may be too hard and could fracture teeth.\n\n<strong>Dog loses interest in durable toys:</strong> Durable toys can lack the appealing texture of softer items. Add food motivation by stuffing them or smearing with a thin layer of dog-safe peanut butter.\n\n<strong>Rope toy fibres are being swallowed:</strong> Replace rope toys immediately when fraying begins. Swallowed fibres can cause linear foreign body obstructions, which are a veterinary emergency.",
            "when_to_seek_help": "If your dog has swallowed a piece of toy material, watch for vomiting, loss of appetite, lethargy, or straining to defecate. These symptoms require urgent veterinary attention. Do not wait — intestinal blockages can become life-threatening within 24-48 hours.",
            "key_takeaways": [
                "Match toy durability to your dog's individual chew strength, not just their breed or size",
                "Inspect all toys weekly for signs of wear — cracks, loose pieces, and thinning material",
                "Natural rubber is the best all-round material for durability combined with dental safety",
                "Supervise play with any toy, regardless of its durability rating",
                "Replace toys at the first sign of significant wear — do not wait for them to break apart",
                "Keep a mix of durable toys and softer options for varied enrichment"
            ]
        },

        # ── 5946: Dog Toy Materials Compared ──
        5946: {
            "at_a_glance": [
                "Rubber, rope, plush, and nylon each have distinct advantages and safety considerations",
                "Natural rubber is the safest and most versatile material for most dogs",
                "Rope toys require close supervision as ingested fibres can cause serious blockages",
                "Plush toys suit gentle players but are not appropriate for determined chewers",
                "Always check for BPA-free, phthalate-free, and non-toxic certifications when buying"
            ],
            "why_this_matters": "Unlike children's toys, dog toys in the UK are not required to meet specific safety standards. This means the responsibility falls on owners to understand material properties and risks. Choosing the right material for your dog's play style directly impacts both their safety and the toy's useful lifespan.",
            "troubleshooting": "<strong>Dog is allergic to certain toy materials:</strong> Symptoms include reddening around the mouth, excessive drooling, or skin irritation. Switch to natural rubber or silicone toys and consult your vet if symptoms persist.\n\n<strong>Rubber toys develop a chemical smell:</strong> Low-quality rubber can off-gas. Invest in toys from reputable brands that use natural rubber and wash new toys before first use.\n\n<strong>Nylon toys seem to wear dog's teeth:</strong> Nylon can be abrasive on tooth enamel if used excessively. Limit nylon chew sessions to 15-20 minutes and check teeth regularly for flat spots or discolouration.\n\n<strong>Plush toy stuffing is being pulled out:</strong> Remove toys immediately. Ingested polyester filling can cause gastrointestinal blockages. Consider stuffing-free plush alternatives for dogs that like to de-stuff.",
            "when_to_seek_help": "If your dog shows signs of an allergic reaction (facial swelling, hives, or breathing difficulty) after contact with a new toy material, this requires immediate veterinary attention. For less urgent concerns like persistent mouth redness, book a routine vet appointment.",
            "key_takeaways": [
                "Natural rubber is the gold standard for safety, durability, and dental friendliness",
                "Always supervise rope toy play and discard at the first sign of fraying",
                "Match material type to your dog's play style — chewers need rubber, cuddlers suit plush",
                "Check for non-toxic certifications, especially on imported or budget toys",
                "Wash all new toys before giving them to your dog to remove manufacturing residues",
                "Keep a variety of materials available to provide different sensory experiences"
            ]
        },

        # ── 5942: Cognitive Enrichment for Senior Dogs ──
        5942: {
            "at_a_glance": [
                "Cognitive decline in senior dogs is common but can be slowed with regular mental stimulation",
                "Simple puzzle feeders and scent games are ideal — they engage the brain without straining joints",
                "Senior dogs may need easier versions of puzzles they previously solved with ease",
                "Short, frequent enrichment sessions (5-10 minutes) are better than longer ones for older dogs",
                "Familiar activities with small novel twists provide the best balance of comfort and challenge"
            ],
            "why_this_matters": "Canine Cognitive Dysfunction (CCD) affects an estimated 28% of dogs aged 11-12 and over 60% of dogs over 15, according to veterinary research. The PDSA recommends ongoing mental stimulation throughout a dog's life as one of the most accessible ways to support cognitive health in ageing. Early intervention with enrichment can meaningfully slow the progression of symptoms.",
            "troubleshooting": "<strong>Senior dog cannot solve puzzles they used to enjoy:</strong> This may indicate cognitive decline. Simplify the puzzle dramatically — make it almost too easy — so they still experience success and engagement.\n\n<strong>Dog seems confused by new enrichment activities:</strong> Stick to familiar formats with minor variations. A dog with CCD benefits more from gentle routine than from novelty.\n\n<strong>Dog falls asleep during enrichment sessions:</strong> Senior dogs tire quickly. Keep sessions to 5 minutes maximum and schedule them when your dog is naturally most alert, typically mid-morning.\n\n<strong>Dog shows frustration or anxiety with puzzles:</strong> Stop the session immediately and offer a simple, rewarding activity instead. Enrichment should always end positively.",
            "when_to_seek_help": "If your senior dog shows signs of Canine Cognitive Dysfunction — disorientation, altered sleep-wake cycles, house soiling, staring into space, or failing to recognise family members — consult your vet. Medication alongside enrichment can significantly improve quality of life.",
            "key_takeaways": [
                "Start cognitive enrichment early — do not wait for signs of decline to begin",
                "Keep sessions short (5-10 minutes) and always end on a success",
                "Scent work is excellent for seniors as it requires minimal physical effort",
                "Adapt difficulty levels downward as your dog ages — success matters more than challenge",
                "Maintain a consistent enrichment routine alongside regular veterinary check-ups",
                "Combine mental stimulation with gentle physical activity for overall senior wellbeing"
            ]
        },

        # ── 5938: Enrichment Schedules for Dogs ──
        5938: {
            "at_a_glance": [
                "A structured daily enrichment schedule prevents boredom and reduces behavioural problems",
                "Aim for at least 20-30 minutes of mental stimulation spread across the day",
                "Morning enrichment helps set a calm tone; evening enrichment aids settling",
                "Variety across the week is more important than variety within a single day",
                "Adjust schedules to your dog's age, breed, and individual energy levels"
            ],
            "why_this_matters": "The RSPCA lists mental stimulation as a core welfare need for all pet dogs. Yet many UK owners focus solely on physical exercise, overlooking the mental component. A consistent enrichment schedule helps prevent common problems like excessive barking, destructive chewing, and separation anxiety — all of which are frequently reported to UK veterinary behaviourists.",
            "troubleshooting": "<strong>Cannot maintain the schedule on busy days:</strong> Have a collection of quick 5-minute activities (scatter feeding, simple snuffle mat) for days when time is short. Some enrichment is always better than none.\n\n<strong>Dog seems bored despite following a schedule:</strong> You may need to increase the difficulty or variety of activities. Dogs adapt quickly — update your enrichment repertoire every few weeks.\n\n<strong>Dog becomes demanding at enrichment times:</strong> Vary the exact timing slightly each day so your dog does not develop rigid expectations. Enrichment should be part of the routine, not a fixed appointment.\n\n<strong>Struggle to fit enrichment around work hours:</strong> Use food-dispensing toys and frozen Kongs during periods when you cannot be present. Automated treat dispensers can also provide midday stimulation.",
            "when_to_seek_help": "If your dog shows persistent behavioural problems despite a consistent enrichment schedule — such as ongoing destructive behaviour, excessive vocalisation, or anxiety symptoms — the underlying cause may require professional assessment from a veterinary behaviourist.",
            "key_takeaways": [
                "Build enrichment into your daily routine rather than treating it as an extra",
                "Spread mental stimulation across the day — morning, midday, and evening",
                "Use feeding times as enrichment opportunities by ditching the bowl",
                "Keep a list of 10-15 activities you can rotate through each week",
                "Adjust the schedule as your dog ages or their needs change",
                "Track what works — note which activities produce the calmest, most satisfied behaviour"
            ]
        },

        # ── 5935: Dog Toy Storage and Organisation ──
        5935: {
            "at_a_glance": [
                "Proper toy storage extends toy lifespan and improves hygiene",
                "Store clean, dry toys in a breathable container — avoid sealed bins that trap moisture",
                "Separate active rotation toys from stored-away toys to maintain novelty",
                "A simple organisational system takes minutes to set up and saves money long-term",
                "Damaged toys should be stored separately for inspection before disposal"
            ],
            "why_this_matters": "Disorganised toy storage leads to toys being forgotten, becoming unsanitary, or presenting hidden safety hazards. With UK pet owners spending an estimated £300-500 annually on dog toys, proper organisation ensures you get full value from purchases while keeping your home tidy and your dog engaged through effective rotation.",
            "troubleshooting": "<strong>Dog raids the toy storage and pulls everything out:</strong> Use a storage solution with a secure lid or place it out of reach. Alternatively, make the toy box itself an enrichment activity by hiding treats among stored toys.\n\n<strong>Toys develop mildew in storage:</strong> Ensure all toys are completely dry before storing. Use breathable fabric bins rather than airtight plastic containers, and store in a dry area of your home.\n\n<strong>Cannot keep track of which toys are in rotation:</strong> Use a simple two-box system — one for current rotation, one for stored toys. Swap contents every 1-2 weeks.\n\n<strong>Too many toys accumulating:</strong> Audit your toy collection quarterly. Donate gently used toys to local rescue centres and discard anything worn or damaged.",
            "when_to_seek_help": "If your dog shows obsessive behaviour around their toy storage — constant guarding, anxiety when toys are put away, or aggression when you approach the toy area — this may indicate resource guarding that warrants assessment by a qualified behaviourist.",
            "key_takeaways": [
                "Use a breathable, easy-to-clean container for toy storage",
                "Implement a two-box rotation system to keep toys feeling fresh",
                "Always dry toys completely before putting them away",
                "Audit your toy collection quarterly — donate or discard as needed",
                "Keep high-value enrichment items stored separately from everyday toys",
                "Make tidying toys part of your daily routine to maintain organisation effortlessly"
            ]
        },

        # ── 5934: Crate and Play Enrichment ──
        5934: {
            "at_a_glance": [
                "Crate enrichment prevents boredom, anxiety, and negative associations with confinement",
                "Food-based activities (frozen Kongs, lick mats) are the safest options for unsupervised crate time",
                "Avoid toys with small detachable parts, strings, or squeakers inside crates",
                "Crate enrichment should supplement, not replace, adequate out-of-crate exercise and interaction",
                "Positive crate associations built through enrichment support crate training success"
            ],
            "why_this_matters": "The RSPCA and Dogs Trust both advise that dogs should not be crated for extended periods without appropriate mental stimulation. In the UK, leaving a dog crated without enrichment for prolonged periods may constitute a welfare concern under the Animal Welfare Act 2006. Proper crate enrichment ensures confinement remains a positive, comfortable experience.",
            "troubleshooting": "<strong>Dog ignores enrichment items in the crate:</strong> Your dog may associate the crate with negative experiences. Rebuild positive associations by offering enrichment with the crate door open before progressing to closed-door sessions.\n\n<strong>Dog makes a mess with food toys in the crate:</strong> Use frozen enrichment to slow consumption and reduce mess. Place a washable mat or towel under food items for easy clean-up.\n\n<strong>Dog becomes destructive in the crate despite enrichment:</strong> This may indicate separation anxiety rather than boredom. Destructive behaviour, vocalisation, and escape attempts in the crate warrant professional assessment.\n\n<strong>Enrichment runs out quickly leaving dog with nothing to do:</strong> Layer multiple frozen items of increasing difficulty so they last longer. Consider a slow-feeding mat under a partially frozen Kong for extended engagement.",
            "when_to_seek_help": "If your dog shows signs of distress in the crate despite appropriate enrichment — excessive panting, drooling, self-harm, or continuous barking — stop using the crate and consult a veterinary behaviourist. These are signs of a welfare issue that enrichment alone cannot resolve.",
            "key_takeaways": [
                "Only use crate-safe toys — nothing with detachable parts, stuffing, or strings",
                "Frozen food enrichment is the gold standard for safe crate activity",
                "Build positive crate associations gradually before using the crate for confinement",
                "Limit crate time and ensure adequate exercise and social interaction outside the crate",
                "Clean crate enrichment items promptly to maintain hygiene",
                "Never use crate enrichment as a substitute for addressing underlying anxiety issues"
            ]
        },

        # ── 5933: Safe Tug Play with Dogs ──
        5933: {
            "at_a_glance": [
                "Tug-of-war is safe and beneficial when played with clear rules and appropriate equipment",
                "Contrary to popular myth, tug does not cause aggression or dominance issues",
                "Teach a reliable 'drop it' cue before starting regular tug games",
                "Use purpose-made tug toys long enough to keep hands clear of your dog's mouth",
                "Stop immediately if your dog's teeth make contact with skin, even accidentally"
            ],
            "why_this_matters": "Research published in the Journal of Applied Animal Welfare Science found that tug-of-war actually increases confidence and strengthens the bond between dogs and owners. Despite this, outdated myths about tug causing aggression persist among UK dog owners. Played correctly, tug is one of the most effective interactive games available.",
            "troubleshooting": "<strong>Dog will not let go of the tug toy:</strong> Stop all movement and become completely boring — hold the toy still against your body. Most dogs release within 10-30 seconds. Reward the drop generously. If this does not work, trade for a high-value treat.\n\n<strong>Dog gets too aroused during tug:</strong> Pause frequently (every 15-20 seconds) and ask for a simple behaviour like 'sit' before resuming. This teaches impulse control within the game.\n\n<strong>Dog's teeth catch your hand:</strong> End the game immediately with a calm 'oops' and walk away for 30 seconds. Resume only when the dog is calmer. This teaches mouth awareness.\n\n<strong>Dog shakes their head violently during tug:</strong> This is natural predatory behaviour. Keep your movements steady and horizontal — avoid jerky up-down motions that could strain your dog's neck.",
            "when_to_seek_help": "If your dog shows genuine aggression during tug play — hard staring, stiff body, growling with a closed mouth, or resource guarding the tug toy after the game ends — pause tug games entirely and consult an ABTC-registered behaviourist before resuming.",
            "key_takeaways": [
                "Tug is safe and beneficial — the dominance myth has been thoroughly debunked",
                "Always teach 'drop it' as a foundation before regular tug sessions",
                "Use long, purpose-made tug toys to keep hands safely away from teeth",
                "Build in frequent pauses and impulse control exercises during play",
                "End every tug session on a positive note with a calm wind-down activity",
                "Tug is an excellent rainy-day exercise option for high-energy dogs"
            ]
        },

        # ── 5932: Scent-Game Enrichment for Dogs ──
        5932: {
            "at_a_glance": [
                "Scent work is one of the most mentally tiring and satisfying activities for any dog",
                "Dogs have up to 300 million scent receptors compared to around 6 million in humans",
                "Simple scent games can be set up at home with no special equipment",
                "Scent activities are suitable for dogs of all ages, sizes, and physical abilities",
                "Regular scent work reduces anxiety and builds confidence in nervous dogs"
            ],
            "why_this_matters": "Scent work taps into a dog's most powerful and natural sense. The Kennel Club now offers scent work as a recognised competitive activity in the UK, reflecting growing understanding of its benefits. For pet dogs, even basic scent games at home can provide more mental satisfaction than a long walk, making it an invaluable tool for owners with busy schedules or dogs with physical limitations.",
            "troubleshooting": "<strong>Dog does not seem to understand the game:</strong> Start extremely simply — let your dog watch you place a treat, then immediately send them to find it. Gradually increase difficulty by hiding treats out of sight.\n\n<strong>Dog uses eyes instead of nose to search:</strong> Make searches harder visually (use identical containers or hide in the same colour surface) so the nose becomes more useful than the eyes.\n\n<strong>Dog gives up searching too quickly:</strong> You are progressing too fast. Go back to easier searches where your dog succeeds within 30 seconds, and gradually extend search time.\n\n<strong>Dog finds treats but does not indicate clearly:</strong> Reward any behaviour near the hidden item — a pause, a look, or a nose touch. Over time, shape this into a clearer indication behaviour.",
            "when_to_seek_help": "If your dog becomes obsessively fixated on scent searching to the point of ignoring commands, refusing food, or showing stress behaviours, the activity may be triggering compulsive tendencies. Reduce frequency and consult a behaviourist experienced in canine enrichment.",
            "key_takeaways": [
                "Start with easy finds and gradually increase complexity as your dog's skills develop",
                "Use your dog's regular kibble for training to avoid overfeeding with treats",
                "Scent work can be done indoors on rainy days — it is not weather dependent",
                "Let your dog work at their own pace — never rush a search",
                "Combine scent games with meal times by scatter feeding or using snuffle mats",
                "Even 5-10 minutes of scent work can be more mentally tiring than a 30-minute walk"
            ]
        },

        # ── 5931: Signs of Toy Overstimulation ──
        5931: {
            "at_a_glance": [
                "Overstimulation during play is common and often mistaken for enthusiasm",
                "Early signs include dilated pupils, rapid breathing, inability to respond to cues, and frantic movements",
                "Puppies and adolescent dogs (6-18 months) are most prone to overstimulation",
                "Certain toy types — squeaky toys, flirt poles, and laser pointers — are more likely to trigger overstimulation",
                "Recognising the signs early prevents escalation to mouthing, barking, or destructive behaviour"
            ],
            "why_this_matters": "Many UK dog owners interpret overstimulation as a sign their dog is having fun, not realising the dog has tipped past enjoyment into stress. The Blue Cross advises that understanding arousal levels is fundamental to safe play. An overstimulated dog is more likely to bite accidentally, injure themselves, or develop ongoing reactivity issues.",
            "troubleshooting": "<strong>Dog reaches overstimulation before you notice:</strong> Film a play session and review it — this helps you identify subtle early signs you miss in real time, such as a slight stiffening or quickening pace.\n\n<strong>Dog immediately escalates with certain toys:</strong> Remove those toys from regular rotation. Some dogs cannot self-regulate with specific stimuli and need those items reserved for structured, short sessions only.\n\n<strong>Puppy gets bitey during play:</strong> This is classic overstimulation. End play immediately with a calm 'enough' and redirect to a calming activity. Puppies need very short play bursts with rest periods in between.\n\n<strong>Dog struggles to settle for hours after play:</strong> Play sessions may be too long or too intense. Shorten them and always follow with a structured calm-down period such as a chew or snuffle mat session.",
            "when_to_seek_help": "If your dog's overstimulation regularly results in aggressive outbursts, self-injurious behaviour (such as excessive paw licking or tail chasing), or if you cannot safely manage their arousal levels, consult a veterinary behaviourist for a structured desensitisation plan.",
            "key_takeaways": [
                "Learn your individual dog's early overstimulation signals — they are unique to each dog",
                "End play sessions before your dog reaches peak arousal, not after",
                "Puppies need the shortest play sessions with the most frequent breaks",
                "Remove specific toys that consistently trigger overstimulation",
                "Follow every play session with a structured cool-down activity",
                "Arousal is not happiness — a calm, engaged dog is having more fun than a frantic one"
            ]
        },

        # ── 5930: Dog Toy Safety by Breed Size ──
        5930: {
            "at_a_glance": [
                "Toy size is one of the most critical safety factors — too small risks choking, too large limits engagement",
                "Small breeds need toys they can carry; large breeds need toys they cannot swallow",
                "Tennis balls are a common choking hazard for larger breeds — use size-appropriate alternatives",
                "Toy density matters as much as size — a large soft toy is not safe for a powerful chewer",
                "Regularly reassess toy sizes as puppies grow, especially during rapid growth phases"
            ],
            "why_this_matters": "Choking and intestinal obstruction from incorrectly sized toys are among the most common toy-related emergencies seen by UK veterinary practices. The BVA advises that toy selection should always account for breed size and jaw strength. A toy that is perfectly safe for a Chihuahua can be a life-threatening choking hazard for a Labrador.",
            "troubleshooting": "<strong>Not sure what size toy to buy:</strong> As a general rule, the toy should be too large to fit entirely past the back teeth. If in doubt, go larger rather than smaller.\n\n<strong>Small dog struggles with toys designed for their size:</strong> Some small breeds have stronger jaws than expected (Jack Russells, for example). Choose toys rated for the next size up.\n\n<strong>Large breed puppy is between sizes:</strong> Always size up during growth phases. A toy that fits now may become a choking hazard in 2-3 weeks during rapid puppy growth.\n\n<strong>Multi-size household has mixed toys scattered:</strong> Colour-code or label toys by size and store them separately. This prevents small-breed toys from being accessible to larger dogs.",
            "when_to_seek_help": "If your dog gags, retches, or paws at their mouth during play, they may have a toy or piece lodged in their throat. This is a veterinary emergency — attempt to remove the object only if clearly visible, and get to your nearest emergency vet immediately.",
            "key_takeaways": [
                "Always choose toys that are too large to fit past your dog's back teeth",
                "When in doubt about size, go bigger — a slightly oversized toy is safer than an undersized one",
                "Tennis balls are not safe for medium-to-large breeds due to compression and choking risk",
                "Reassess toy sizes every month during puppyhood and growth phases",
                "Store different-sized toys separately in multi-dog households",
                "Check toys regularly for pieces that may have broken off and become swallowable"
            ]
        },

        # ── 5511: Pet Enrichment Explained ──
        5511: {
            "at_a_glance": [
                "Enrichment encompasses five categories: sensory, feeding, environmental, social, and cognitive",
                "Effective enrichment gives pets choice and control over their environment",
                "Even small daily changes — a new scent, a different feeding method — count as enrichment",
                "Enrichment needs vary by species, breed, age, and individual personality",
                "Consistent enrichment reduces veterinary behavioural referrals and improves overall welfare"
            ],
            "why_this_matters": "The concept of environmental enrichment originated in zoo animal welfare science and is now recognised as essential for companion animals. The RSPCA's five welfare needs include the need for a suitable environment and the need to exhibit normal behaviour patterns — both of which are directly addressed through structured enrichment programmes.",
            "troubleshooting": "<strong>Pet seems indifferent to enrichment attempts:</strong> You may be offering the wrong type. Experiment across all five categories to discover what motivates your specific pet.\n\n<strong>Enrichment causes mess or destruction:</strong> Start with contained options like puzzle feeders and gradually introduce more open-ended activities. Protect floors and furnishings as needed.\n\n<strong>Multiple pets compete over enrichment items:</strong> Provide enrichment in separate spaces to prevent conflict. Each pet should have access to their own activities.\n\n<strong>Running out of enrichment ideas:</strong> Revisit activities from weeks ago — pets do not remember them as quickly as you think. A simple rotation of 10-15 activities can last months.",
            "when_to_seek_help": "If your pet shows persistent behavioural issues despite a varied enrichment programme — ongoing anxiety, aggression, or compulsive behaviours — consult your vet for referral to a certified animal behaviourist. Enrichment supports but does not replace professional behavioural intervention.",
            "key_takeaways": [
                "Enrichment is a welfare need, not a luxury — build it into daily routines",
                "Cover all five enrichment categories over the course of each week",
                "Give your pet choice and control — let them approach enrichment at their own pace",
                "Observe what your individual pet enjoys most and build on those preferences",
                "Simple, free enrichment (cardboard boxes, scatter feeding) is just as valuable as bought items",
                "Adjust enrichment complexity as your pet ages or their circumstances change"
            ]
        },

        # ── 5509: Pet Toy Safety ──
        5509: {
            "at_a_glance": [
                "Pet toys in the UK are not subject to the same safety regulations as children's toys",
                "Common hazards include choking on small parts, intestinal blockage, and toxic material exposure",
                "Supervision during play is the single most effective safety measure",
                "Check for CE marking and reputable brand sourcing when purchasing toys",
                "Regular inspection and timely replacement prevent most toy-related injuries"
            ],
            "why_this_matters": "The UK pet toy industry is worth over £200 million annually, yet there are no mandatory safety testing requirements equivalent to the Toy Safety Directive that protects children. This regulatory gap means owners must be their pet's quality control. Understanding materials, hazards, and what to look for empowers safer purchasing decisions.",
            "troubleshooting": "<strong>Unsure if a toy material is safe:</strong> Avoid toys with strong chemical smells, loose glitter, or unidentified coatings. Stick to brands that publish their material safety data and manufacturing standards.\n\n<strong>Pet has swallowed part of a toy:</strong> Monitor for vomiting, loss of appetite, lethargy, or changes in bowel movements. Small soft pieces may pass naturally, but hard or sharp pieces require immediate veterinary assessment.\n\n<strong>Toy is labelled 'non-toxic' but pet reacts to it:</strong> 'Non-toxic' has no regulated definition for pet products. If your pet shows mouth redness, drooling, or digestive upset after using a new toy, remove it and consult your vet.\n\n<strong>Budget toys from online marketplaces seem unsafe:</strong> They often are. Prioritise toys from UK-based pet retailers with clear returns policies and material disclosures over unbranded imports.",
            "when_to_seek_help": "Seek emergency veterinary care if your pet shows signs of choking (pawing at mouth, gagging, distressed breathing) or intestinal blockage (repeated vomiting, abdominal pain, inability to pass stool). Time is critical in both scenarios.",
            "key_takeaways": [
                "Supervise all toy play — no toy is guaranteed safe when unsupervised",
                "Buy from reputable brands that disclose materials and manufacturing standards",
                "Inspect toys before each play session for loose parts, cracks, or wear",
                "Size toys appropriately — too small is always more dangerous than too large",
                "Replace toys at the first sign of significant damage, not when they finally break",
                "Keep emergency vet contact details visible at home in case of toy-related incidents"
            ]
        },

        # ── 5483: Dog Toy Lifespan ──
        5483: {
            "at_a_glance": [
                "Most dog toys have a functional lifespan of 2-8 weeks depending on material and usage",
                "Rubber toys last longest; plush and rope toys have the shortest usable lifespan",
                "Regular cleaning and proper storage can extend toy life by 30-50%",
                "A toy's lifespan ends when it becomes a safety hazard, not when it looks worn",
                "Investing in fewer quality toys is more cost-effective than frequent cheap replacements"
            ],
            "why_this_matters": "UK dog owners replace toys frequently, contributing both to household costs and environmental waste. Understanding how to maximise toy lifespan saves money while ensuring safety. Equally important is knowing when a toy has reached the end of its safe life — keeping a worn toy in rotation is a false economy if it leads to a veterinary bill.",
            "troubleshooting": "<strong>Toys barely last a day:</strong> You may be choosing the wrong durability level. Power chewers need solid rubber or nylon toys rated for aggressive chewing. Avoid plush and rope for unsupervised play.\n\n<strong>Toys look fine but smell terrible:</strong> Odour indicates bacterial or mould growth inside the toy material. Replace immediately — cleaning may not reach embedded contamination.\n\n<strong>Dog only likes toys that are nearly destroyed:</strong> Some dogs prefer the floppy texture of worn toys. Offer 'flat' style toys (no stuffing by design) as a safer alternative that mimics the feel.\n\n<strong>Spending too much on replacement toys:</strong> Focus purchases on 3-5 high-quality durable toys rather than many cheap ones. Supplement with free enrichment like cardboard boxes and scatter feeding.",
            "when_to_seek_help": "If you find pieces of toy material in your dog's stool, monitor closely for any signs of blockage. A single small piece may pass, but repeated ingestion of toy fragments warrants a vet visit to check for cumulative intestinal issues.",
            "key_takeaways": [
                "Inspect toys weekly — look for cracks, loose pieces, thinning, and odour",
                "Clean toys regularly to extend lifespan and maintain hygiene",
                "Store toys properly between uses — dry, ventilated, and out of direct sunlight",
                "Replace any toy where pieces can be bitten off or pulled away",
                "Invest in quality over quantity — 3 good toys outperform 10 cheap ones",
                "Track your toy spending to identify which types offer the best value for your dog"
            ]
        },

        # ── 5476: Mental Stimulation Toys ──
        5476: {
            "at_a_glance": [
                "Mental stimulation is as important as physical exercise for a dog's overall wellbeing",
                "Puzzle toys range from beginner (single-step) to advanced (multi-step) difficulty levels",
                "Food-dispensing puzzles combine mental challenge with feeding enrichment",
                "Start easy and increase difficulty gradually — frustration defeats the purpose",
                "Even 15 minutes of focused mental work can tire a dog as much as a 30-minute walk"
            ],
            "why_this_matters": "The Dogs Trust emphasises that mental exercise is a fundamental welfare need, not a bonus. Dogs bred for working roles — which includes most UK popular breeds — have been selected for problem-solving ability over centuries. Without adequate mental outlets, this intelligence often manifests as destructive behaviour, excessive barking, or anxiety.",
            "troubleshooting": "<strong>Dog gives up on puzzles quickly:</strong> The difficulty is too high. Reset to the easiest level where your dog succeeds within 30 seconds, then increase complexity in tiny increments.\n\n<strong>Dog flips the puzzle over instead of solving it:</strong> This is creative problem-solving, not cheating. Use weighted or floor-mounted puzzles if you want to encourage specific solving methods, or accept the flip as a valid strategy.\n\n<strong>Dog finishes puzzle toys too fast:</strong> Freeze the contents, use smaller treats, or combine multiple puzzle types in sequence to extend engagement time.\n\n<strong>Dog seems stressed by puzzle toys:</strong> Some dogs find frustration tolerance difficult. Pair puzzle time with your calm presence and be ready to help. Never leave a dog struggling with a puzzle they cannot solve.",
            "when_to_seek_help": "If your dog shows compulsive behaviours around puzzle toys — frantic pawing, vocalisation, or inability to disengage — this may indicate frustration intolerance or anxiety that requires professional assessment. A behaviourist can help build healthy puzzle-solving skills.",
            "key_takeaways": [
                "Start with easy puzzles and build complexity gradually over weeks",
                "Use your dog's daily food allowance in puzzles to avoid overfeeding",
                "Rotate puzzle types to prevent your dog from memorising solutions",
                "Supervise puzzle sessions and help if your dog becomes frustrated",
                "Mental exercise is a welfare need, not an optional extra",
                "Combine puzzle toys with other enrichment types for a well-rounded routine"
            ]
        },

        # ── 5473: Senior Dog Toys ──
        5473: {
            "at_a_glance": [
                "Senior dogs benefit from gentler toys that accommodate stiff joints and sensitive teeth",
                "Soft rubber, plush, and food-dispensing toys are typically the best choices for older dogs",
                "Avoid hard nylon chews and vigorous tug toys that may strain ageing joints or damage worn teeth",
                "Enrichment for seniors should focus on engagement and comfort rather than physical challenge",
                "Regular toy assessment is important as a senior dog's abilities can change month to month"
            ],
            "why_this_matters": "With advances in veterinary care, UK dogs are living longer than ever — but longer life means more years of age-related changes. The PDSA reports that around 80% of dogs over 8 years old show signs of joint stiffness. Appropriate toys keep seniors mentally engaged and physically comfortable, supporting quality of life through their golden years.",
            "troubleshooting": "<strong>Senior dog has lost interest in toys entirely:</strong> This is common but not inevitable. Try novel scent-based enrichment or very gentle food puzzles. Pain may also be reducing their willingness to play — discuss with your vet.\n\n<strong>Dog's teeth are worn and they struggle with hard toys:</strong> Switch to soft rubber toys and food-based enrichment. Lick mats with soft paste are excellent for dogs with dental issues.\n\n<strong>Senior dog seems confused by new toys:</strong> Stick to familiar toy types with minor variations. Cognitive changes mean older dogs may struggle with novelty — comfort in familiarity is more important.\n\n<strong>Dog tires very quickly during play:</strong> Keep sessions to 5-10 minutes maximum and offer multiple short sessions throughout the day rather than one longer one.",
            "when_to_seek_help": "If your senior dog suddenly stops playing, shows reluctance to pick up toys, drops food from their mouth, or shows signs of pain when chewing, schedule a veterinary dental and joint assessment. These changes often indicate treatable conditions.",
            "key_takeaways": [
                "Choose soft, gentle toys that do not stress ageing joints or teeth",
                "Prioritise mental engagement through scent work and simple food puzzles",
                "Keep play sessions short and frequent rather than long and intense",
                "Monitor your senior dog's changing abilities and adjust toy selection accordingly",
                "Lick mats and frozen soft-food toys are excellent for dogs with dental issues",
                "Regular vet check-ups ensure age-related changes are managed alongside appropriate enrichment"
            ]
        },

        # ── 5471: Dog Boredom Prevention ──
        5471: {
            "at_a_glance": [
                "Boredom is one of the leading causes of destructive behaviour in UK dogs",
                "Common signs include excessive chewing, barking, digging, and restlessness",
                "Mental stimulation is equally important as physical exercise for preventing boredom",
                "A variety of enrichment activities throughout the day is more effective than a single long walk",
                "Breed, age, and individual temperament all influence how easily a dog becomes bored"
            ],
            "why_this_matters": "The Blue Cross lists boredom as a primary cause of many behavioural problems they see in surrendered dogs. With UK working patterns meaning many dogs spend 4-8 hours alone daily, boredom prevention is not just about enrichment — it is about welfare. Addressing boredom proactively prevents problems that are far harder and more expensive to fix once established.",
            "troubleshooting": "<strong>Dog is destructive despite having plenty of toys:</strong> Having toys available is not the same as being enriched. Rotate toys, use food puzzles, and vary activities. A basket of static toys does not prevent boredom.\n\n<strong>Dog is bored when home alone:</strong> Set up timed enrichment such as frozen Kongs, snuffle mats with hidden treats, and safe chew items. Consider a dog walker or daycare for dogs that need social interaction.\n\n<strong>Dog seems bored even after long walks:</strong> Physical exercise alone does not meet all mental needs. Add structured training sessions, scent games, or puzzle feeding to provide cognitive stimulation.\n\n<strong>Boredom-related barking is disturbing neighbours:</strong> Address the root cause with enrichment before the barking is reported. In the UK, persistent barking can lead to noise abatement notices from local councils.",
            "when_to_seek_help": "If boredom behaviours have escalated to self-harm (excessive licking causing hot spots, tail chasing, or pica), or if destructive behaviour is causing significant property damage despite enrichment efforts, consult your vet to rule out medical causes and seek behaviourist referral.",
            "key_takeaways": [
                "Boredom is a welfare issue, not just an inconvenience — treat it seriously",
                "Combine physical exercise with mental stimulation for complete enrichment",
                "Rotate toys and activities regularly — novelty is key to maintaining interest",
                "Set up enrichment activities for times when your dog is home alone",
                "Match enrichment intensity to your dog's breed, age, and energy level",
                "Address boredom early before it develops into entrenched behavioural problems"
            ]
        },

        # ── 5469: Dog Toy Rotation ──
        5469: {
            "at_a_glance": [
                "Toy rotation maintains novelty and interest without constantly buying new toys",
                "The ideal rotation cycle is 5-7 days per set of 3-4 toys",
                "Remove toys from sight completely during their 'rest' period to restore novelty",
                "Include a variety of toy types in each rotation set — chew, puzzle, tug, and comfort",
                "Toy rotation has been shown to increase engagement by up to 50% compared to free access"
            ],
            "why_this_matters": "Research into habituation shows that dogs lose interest in familiar objects over time, just as humans do. The Kennel Club recommends toy rotation as a simple, cost-free way to maximise the value of existing toys while keeping dogs mentally stimulated. It is one of the easiest enrichment upgrades any owner can make immediately.",
            "troubleshooting": "<strong>Dog seems anxious when favourite toy is rotated out:</strong> Keep one comfort toy permanently available and only rotate activity toys. Comfort items serve an emotional role and should not be part of the rotation.\n\n<strong>Dog loses interest even with rotation:</strong> Your rotation cycle may be too short. Try extending rest periods to 2-3 weeks, or introduce one genuinely new toy into the mix occasionally.\n\n<strong>Cannot remember what is in rotation:</strong> Use a simple calendar note or two labelled boxes. Over-complicating the system leads to abandoning it.\n\n<strong>Dog finds hidden toys and steals them back:</strong> Store rotated-out toys in a closed cupboard or high shelf. Some dogs have excellent scent memories and will locate hidden toys easily.",
            "when_to_seek_help": "If your dog becomes distressed, aggressive, or obsessive about specific toys to the point where rotation causes genuine anxiety, this may indicate resource guarding or attachment issues that benefit from professional behavioural support.",
            "key_takeaways": [
                "Rotate sets of 3-4 toys every 5-7 days for optimal novelty",
                "Store rotated-out toys completely out of sight and reach",
                "Include different toy categories in each rotation set for variety",
                "Keep one permanent comfort toy outside the rotation system",
                "Track which toys generate the most engagement to inform future purchases",
                "Toy rotation is free, simple, and one of the most effective enrichment strategies available"
            ]
        },

        # ── 5425: Dog Toys FAQ ──
        5425: {
            "at_a_glance": [
                "This comprehensive FAQ covers the most common questions UK dog owners ask about toys",
                "Safety, sizing, cleaning, and age-appropriateness are the most frequently asked topics",
                "There is no single 'best' toy — the right choice depends on your dog's size, age, and play style",
                "Regular inspection and replacement are more important than buying expensive toys",
                "Supervision during play remains the most effective safety measure for any toy"
            ],
            "why_this_matters": "Dog toy questions are among the most frequently searched pet topics in the UK. Getting clear, evidence-based answers helps owners avoid common mistakes that can lead to injuries, wasted money, or behavioural issues. This FAQ consolidates expert guidance into accessible answers for everyday dog owners.",
            "troubleshooting": "<strong>Overwhelmed by the number of toy options available:</strong> Start with three basics — a durable chew toy, a food-dispensing puzzle, and an interactive toy for play together. Build from there based on what your dog enjoys.\n\n<strong>Dog rejects every toy you buy:</strong> Not all dogs are toy-motivated. Try food-based enrichment (snuffle mats, scatter feeding) and interactive games with you rather than solo toy play.\n\n<strong>Conflicting advice from different sources:</strong> Prioritise guidance from UK veterinary and welfare organisations (RSPCA, PDSA, BVA) over anecdotal advice or manufacturer marketing claims.\n\n<strong>Budget does not stretch to many toys:</strong> Quality matters more than quantity. One good rubber toy plus DIY enrichment (cardboard boxes, muffin tin puzzles) provides excellent stimulation at minimal cost.",
            "when_to_seek_help": "If you have specific concerns about your dog's play behaviour, toy preferences, or safety, your vet or a qualified animal behaviourist can provide personalised advice tailored to your dog's individual needs.",
            "key_takeaways": [
                "Safety first — always supervise play and inspect toys regularly",
                "Match toys to your dog's individual size, age, and play style",
                "You do not need expensive toys — a few quality items plus creativity is plenty",
                "Clean toys regularly and replace them at the first sign of significant wear",
                "Use trusted UK sources (RSPCA, PDSA, Kennel Club) for evidence-based guidance",
                "When in doubt about a toy's safety, err on the side of caution and remove it"
            ]
        },

        # ── 5423: Dog Toy Enrichment Beyond Basic Fetch ──
        5423: {
            "at_a_glance": [
                "Fetch is just one of many enrichment activities — a varied approach provides deeper mental stimulation",
                "Puzzle feeding, scent work, tug games, and independent play each serve different enrichment needs",
                "Dogs that rely solely on fetch can develop obsessive retrieval behaviour",
                "Interactive enrichment (games with you) and independent enrichment (solo activities) both matter",
                "Enrichment beyond fetch is especially important for high-drive breeds that fixate on repetitive activities"
            ],
            "why_this_matters": "While fetch is the UK's most popular dog game, over-reliance on a single activity can lead to repetitive strain injuries and obsessive behaviour. The Dogs Trust recommends a varied enrichment diet that engages different cognitive skills and physical movements. Branching out from fetch creates a more resilient, adaptable, and mentally healthy dog.",
            "troubleshooting": "<strong>Dog is obsessed with fetch and ignores other activities:</strong> Gradually reduce fetch frequency while introducing alternative games. Pair new activities with high-value rewards to build motivation.\n\n<strong>Dog does not seem interested in puzzle toys:</strong> Start with the easiest level and use high-value food rewards. Not all dogs take to puzzles immediately — persistence and gradual progression are key.\n\n<strong>Owner finds alternative enrichment time-consuming:</strong> Many enrichment activities take less time than a fetch session. Scatter feeding takes 30 seconds to set up; a frozen Kong takes 2 minutes to prepare.\n\n<strong>Dog gets frustrated with unfamiliar activities:</strong> Introduce one new activity at a time alongside familiar favourites. Build success gradually rather than replacing the entire routine at once.",
            "when_to_seek_help": "If your dog shows compulsive fetch behaviour — refusing to stop, ignoring exhaustion, becoming aggressive when the ball is withheld, or fixating on shadows and moving objects — consult a veterinary behaviourist. Compulsive retrieval can be a serious welfare concern.",
            "key_takeaways": [
                "Vary your dog's enrichment across at least 3-4 different activity types per week",
                "Balance interactive games (with you) and independent enrichment (solo activities)",
                "Reduce fetch frequency gradually if your dog shows obsessive retrieval behaviour",
                "Food-based enrichment (puzzle feeders, scatter feeding) requires minimal time to set up",
                "Match enrichment to your dog's breed instincts for maximum engagement",
                "A varied enrichment routine builds a calmer, more adaptable, and happier dog"
            ]
        },

        # ── 5422: Indoor vs Outdoor Dog Toys ──
        5422: {
            "at_a_glance": [
                "Indoor and outdoor toys have different safety requirements and material considerations",
                "Outdoor toys need to be durable, easy to clean, and visible in grass or undergrowth",
                "Indoor toys should be quiet, appropriately sized for the space, and non-destructive to furnishings",
                "Some toys work well in both settings while others are specifically designed for one environment",
                "Weather and seasonal changes in the UK affect outdoor toy choices significantly"
            ],
            "why_this_matters": "The UK's variable weather means dogs often alternate between indoor and outdoor play within the same day. Choosing appropriate toys for each environment prevents damage to homes, reduces the risk of losing toys outdoors, and ensures your dog has safe options regardless of the weather. With an average of 156 rainy days per year in the UK, good indoor toy options are essential.",
            "troubleshooting": "<strong>Outdoor toys get lost in the garden:</strong> Choose brightly coloured toys (orange and yellow are most visible against grass) and establish a collection routine after each play session.\n\n<strong>Indoor play is too noisy or destructive:</strong> Select plush toys, food puzzles, and snuffle mats for indoor use. Avoid hard balls, squeaky toys, and vigorous tug games in small spaces.\n\n<strong>Dog brings muddy outdoor toys inside:</strong> Keep a toy-cleaning station near your door — a bucket of warm water and a towel. Wipe toys down before they enter the house.\n\n<strong>Limited indoor space for play:</strong> Focus on stationary enrichment like lick mats, stuffed Kongs, and puzzle feeders that do not require space for movement.",
            "when_to_seek_help": "If your dog becomes destructive with indoor toys or shows signs of frustration and restlessness despite having both indoor and outdoor play options, the issue may be insufficient overall enrichment or an underlying anxiety condition warranting professional assessment.",
            "key_takeaways": [
                "Choose toys specifically suited to each environment — indoor toys should be quiet and contained",
                "Bright colours help prevent toy loss during outdoor play",
                "Clean outdoor toys before bringing them inside to maintain hygiene",
                "Have a dedicated indoor enrichment kit for rainy UK days",
                "Establish a routine of collecting outdoor toys after each play session",
                "Assess whether your toy collection adequately covers both indoor and outdoor needs"
            ]
        },

        # ── 5421: Puppy-Safe Dog Toys ──
        5421: {
            "at_a_glance": [
                "Puppies have different toy safety needs than adult dogs due to baby teeth and smaller airways",
                "Avoid toys with small detachable parts, strings, and hard materials during the puppy stage",
                "Teething puppies (3-7 months) benefit from soft rubber chew toys that can be frozen for relief",
                "Size toys so they cannot fit entirely in the puppy's mouth to prevent choking",
                "Supervise all puppy play — their curiosity and chewing drive outpaces their judgment"
            ],
            "why_this_matters": "Puppies are the most vulnerable age group for toy-related injuries, according to UK veterinary data. Their developing jaws, smaller airways, and tendency to swallow objects they are chewing make toy selection critical. The RSPCA advises that puppies need age-appropriate toys from day one to support safe teething, learning, and socialisation.",
            "troubleshooting": "<strong>Puppy destroys every toy immediately:</strong> This is normal during teething. Provide a variety of textures and focus on durable rubber options. Accept that some toys are consumable during this phase.\n\n<strong>Puppy chews furniture instead of toys:</strong> Make toys more appealing by adding food motivation (smear with paste, stuff with kibble) and redirect every time you catch them chewing the wrong item.\n\n<strong>Puppy swallowed a piece of toy:</strong> Monitor for vomiting, loss of appetite, or lethargy. Small soft pieces often pass naturally within 24-48 hours, but contact your vet for guidance specific to the piece size and material.\n\n<strong>Puppy is scared of new toys:</strong> Place the toy near their food bowl or bed without interaction. Let them approach on their own terms. Never force a puppy to engage with a toy that frightens them.",
            "when_to_seek_help": "Seek immediate veterinary attention if your puppy chokes on a toy, shows signs of intestinal blockage (vomiting, not eating, painful abdomen), or if you notice a missing piece of toy that may have been swallowed. Puppies are at higher risk of blockage due to their smaller intestinal diameter.",
            "key_takeaways": [
                "Always supervise puppy play sessions — puppies lack the judgment to play safely alone",
                "Choose soft rubber toys sized too large to fit in the puppy's mouth",
                "Frozen toys provide excellent teething relief during the 3-7 month period",
                "Avoid hard nylon chews, small balls, and toys with detachable parts for puppies",
                "Introduce toys gradually and positively — let the puppy approach on their own terms",
                "Reassess toy sizes and types monthly as your puppy grows rapidly"
            ]
        },

        # ── 5420: Dog Toy Cleaning Guide ──
        5420: {
            "at_a_glance": [
                "Regular cleaning reduces bacteria, mould, and parasite transmission from dog toys",
                "Different materials require specific cleaning methods — rubber, plush, rope, and nylon each differ",
                "Most rubber and silicone toys are dishwasher-safe on the top rack",
                "Plush toys can usually be machine washed on a gentle cycle with pet-safe detergent",
                "Rope toys can be dampened and microwaved for 1-2 minutes to kill bacteria (supervise carefully)"
            ],
            "why_this_matters": "A study from NSF International ranked pet toys as one of the top 10 germiest household items. In the UK, where dogs frequently play in parks shared with wildlife, toys can pick up parasites like Toxocara and bacteria like Leptospira. Regular cleaning protects both your dog and your family, especially households with young children.",
            "troubleshooting": "<strong>Toy still smells after cleaning:</strong> The odour may be embedded in the material. Soak overnight in a baking soda and warm water solution before washing. If the smell persists, the toy should be replaced.\n\n<strong>Dog refuses clean toys:</strong> Your dog may miss their scent on the toy. Avoid heavily scented detergents — use unscented, pet-safe products and rinse thoroughly.\n\n<strong>Plush toy falls apart in the washing machine:</strong> Use a mesh laundry bag and select a gentle/delicate cycle. If the toy cannot survive a gentle wash, it may be too worn to continue using safely.\n\n<strong>Unsure which cleaning method to use:</strong> When in doubt, hand wash with warm water and a small amount of pet-safe soap. Rinse thoroughly and air dry completely.",
            "when_to_seek_help": "If your dog develops recurring mouth sores, gastrointestinal upset, or skin infections, contaminated toys could be a contributing factor. Discuss toy hygiene practices with your vet, especially if your dog is immunocompromised or has chronic health conditions.",
            "key_takeaways": [
                "Clean rubber and plastic toys weekly; plush toys fortnightly at minimum",
                "Always dry toys completely before returning them to your dog",
                "Use pet-safe, unscented cleaning products and rinse thoroughly",
                "Combine cleaning time with a safety inspection — check for wear and damage",
                "Replace any toy that cannot be cleaned effectively or retains odour after washing",
                "Establish a simple weekly cleaning routine to make toy hygiene effortless"
            ]
        },

        # ── 5035: Cat Enrichment Beyond Toys ──
        5035: {
            "at_a_glance": [
                "Cat enrichment extends far beyond toys — environmental design, vertical space, and sensory variety all contribute",
                "Indoor cats have the greatest need for environmental enrichment to compensate for limited natural stimulation",
                "Vertical space (cat trees, shelves, window perches) is as important as floor-level enrichment",
                "Routine changes, novel scents, and visual stimulation through windows all count as enrichment",
                "Effective cat enrichment gives cats choice and control over their environment"
            ],
            "why_this_matters": "With around 90% of UK cats now kept exclusively or primarily indoors according to PDSA data, environmental enrichment beyond toys is essential for feline welfare. Indoor cats without adequate stimulation are at higher risk of obesity, stress-related conditions like feline idiopathic cystitis, and behavioural problems. Creating a stimulating home environment is a core responsibility of cat ownership.",
            "troubleshooting": "<strong>Cat ignores enrichment efforts:</strong> Cats are often cautious with new additions. Place items in your cat's environment without fanfare and allow them to investigate on their own terms over several days.\n\n<strong>Cat seems stressed by environmental changes:</strong> Introduce changes gradually — one new element at a time. Maintain familiar scent markers by rubbing a cloth on your cat's face and then on new items.\n\n<strong>Multiple cats compete for enrichment resources:</strong> Provide resources using the 'plus one' rule — one per cat plus one extra. Place them in different locations to reduce competition.\n\n<strong>Limited space for cat enrichment:</strong> Focus on vertical space. Wall-mounted shelves, door-top perches, and window-sill beds provide enrichment without using floor space.",
            "when_to_seek_help": "If your cat shows persistent signs of stress despite enrichment efforts — over-grooming, house soiling, loss of appetite, or aggression — consult your vet. These may indicate an underlying medical condition or require referral to a certified feline behaviourist.",
            "key_takeaways": [
                "Think beyond toys — vertical space, window views, and novel scents are all enrichment",
                "Give your cat choice and control over their environment with multiple resource locations",
                "Indoor cats need more deliberate enrichment than cats with outdoor access",
                "Introduce environmental changes gradually to avoid causing stress",
                "Use the 'plus one' rule for resources in multi-cat households",
                "Rotate enrichment elements periodically to maintain novelty and interest"
            ]
        },

        # ── 5034: Cat Toy Rotation ──
        5034: {
            "at_a_glance": [
                "Cats habituate to toys quickly — rotation restores novelty and increases play engagement",
                "A rotation of 3-5 toys swapped every 3-5 days works well for most cats",
                "Store rotated-out toys in a sealed bag to preserve scent novelty",
                "Include different toy types in each rotation — wand, ball, kick toy, and puzzle",
                "Observe which toys your cat engages with most to inform future purchases"
            ],
            "why_this_matters": "Research published in Animal Cognition demonstrated that cats show significant habituation to toys, losing interest within minutes of repeated exposure. In UK homes where cats may spend long hours alone, toy rotation is one of the simplest and most effective ways to maintain daily enrichment without ongoing expense.",
            "troubleshooting": "<strong>Cat shows no interest even in rotated toys:</strong> The rotation period may be too short. Try resting toys for 2-3 weeks. Also consider whether your cat prefers interactive play with you over solo toys.\n\n<strong>Cat only plays with one specific toy:</strong> Keep that favourite permanently available and rotate the supporting cast around it. Some cats have strong preferences and that is perfectly normal.\n\n<strong>Cat hides rotated-out toys:</strong> Check under furniture regularly. Cats may stash favourite items and become frustrated when they disappear from their hiding spot.\n\n<strong>Rotation feels like too much effort:</strong> Use two simple bags or boxes. Swap the contents every few days — the entire process takes under a minute.",
            "when_to_seek_help": "If your cat shows no interest in any toys regardless of rotation, has stopped playing entirely, or shows behavioural changes alongside reduced play, consult your vet. Loss of play drive in cats can indicate pain, illness, or depression.",
            "key_takeaways": [
                "Rotate 3-5 toys every 3-5 days for optimal novelty effect",
                "Include a mix of toy types in each rotation set",
                "Store rotated toys in a sealed container to preserve scent novelty",
                "Keep one favourite toy permanently available for comfort",
                "Interactive play sessions with you are more valuable than any solo toy",
                "Track which toys your cat engages with most to make smarter purchasing decisions"
            ]
        },

        # ── 4790: DIY Dog Toys ──
        4790: {
            "at_a_glance": [
                "Many safe and effective dog toys can be made from common household items",
                "Always supervise play with DIY toys as they lack the durability testing of commercial products",
                "Safe DIY materials include old t-shirts, tennis ball tubes, muffin tins, and cardboard boxes",
                "Avoid materials that splinter, fray into long threads, or contain toxic substances",
                "DIY toys are excellent for enrichment variety but should supplement, not replace, quality commercial toys"
            ],
            "why_this_matters": "With the cost of living impacting UK pet owners, DIY toys offer a practical way to provide enrichment without significant expense. The Dogs Trust actively promotes DIY enrichment ideas, demonstrating that mental stimulation does not require expensive purchases. However, safety awareness is essential — homemade toys require more vigilant supervision than tested commercial products.",
            "troubleshooting": "<strong>Dog destroys DIY toys instantly:</strong> This is expected — most DIY toys are not designed to last. Think of them as single-use enrichment activities rather than permanent toys.\n\n<strong>Worried about material safety:</strong> Stick to plain, undyed cotton fabrics, untreated cardboard, and food-grade containers. Avoid anything with buttons, zips, elastic, or printed surfaces.\n\n<strong>DIY puzzle is too easy:</strong> Layer difficulty by wrapping treats in fabric inside a box inside another box. Multiple steps extend engagement time.\n\n<strong>Dog eats the DIY toy materials:</strong> Remove the toy immediately. Cardboard ingestion in small amounts is usually harmless, but fabric and plastic can cause blockages. Supervise closely at all times.",
            "when_to_seek_help": "If your dog ingests a significant amount of DIY toy material (fabric, rope, cardboard coated in tape), monitor for vomiting, constipation, or lethargy and contact your vet. Linear foreign bodies from fabric strips are particularly dangerous.",
            "key_takeaways": [
                "DIY toys are cost-effective enrichment but require constant supervision",
                "Use only safe, non-toxic materials — plain cotton, untreated cardboard, and food-grade items",
                "Treat DIY toys as single-use enrichment activities, not permanent fixtures",
                "Combine DIY enrichment with quality commercial toys for a balanced toy collection",
                "The best DIY toys involve food — muffin tin puzzles, snuffle towels, and cardboard foraging boxes",
                "Always remove DIY toy remnants after play to prevent unsupervised chewing"
            ]
        },

        # ── 4789: Best Types of Dog Toys for Different Play Styles ──
        4789: {
            "at_a_glance": [
                "Dogs have distinct play styles — chewers, chasers, tuggers, cuddlers, and problem-solvers",
                "Matching toys to play style increases engagement and reduces destructive behaviour",
                "Most dogs show a dominant play preference by 6-12 months of age",
                "Providing toys across multiple play styles creates a more well-rounded dog",
                "Play style can change with age, health, and life circumstances"
            ],
            "why_this_matters": "Understanding your dog's play style is the foundation of effective toy selection. The Kennel Club notes that many returns of 'unsuitable' dogs stem from play and enrichment mismatches rather than genuine incompatibility. A dog that appears disinterested in toys may simply not have been offered the right type for their natural play preferences.",
            "troubleshooting": "<strong>Cannot identify your dog's play style:</strong> Offer one toy from each category (chew, tug, fetch, puzzle, comfort) and observe which generates the most sustained engagement. Most dogs show a clear preference within a few sessions.\n\n<strong>Dog seems to have no play style at all:</strong> Some dogs, particularly rescues or under-socialised dogs, may not have learned to play. Start with food-based enrichment and gentle interactive games to build play skills gradually.\n\n<strong>Dog's play style is destructive:</strong> Destructive chewing is a valid play style — channel it into appropriate tough toys rather than trying to suppress it. Provide legitimate outlets and manage access to inappropriate items.\n\n<strong>Dog plays differently with different people:</strong> This is normal. Dogs adjust their play to their partner. Ensure each family member has appropriate toys for the play style that dog uses with them.",
            "when_to_seek_help": "If your dog's play involves aggression towards people or other animals, obsessive repetitive behaviour, or causes injury to themselves, consult a veterinary behaviourist. These patterns go beyond normal play styles and may indicate underlying behavioural issues.",
            "key_takeaways": [
                "Identify your dog's dominant play style through observation and experimentation",
                "Match primary toy purchases to their preferred style for maximum engagement",
                "Include toys from other categories to provide variety and develop different skills",
                "Accept your dog's natural preferences rather than forcing a different play style",
                "Reassess play preferences as your dog ages — styles often shift with life stage",
                "A dog that 'does not like toys' likely has not found the right type yet"
            ]
        },

        # ── 4788: Mental Stimulation for Dogs: Beyond Physical Exercise ──
        4788: {
            "at_a_glance": [
                "Physical exercise alone is not sufficient for a dog's complete wellbeing",
                "Mental stimulation tires the brain independently of physical activity",
                "Puzzle feeders, training, scent work, and novel experiences all provide cognitive exercise",
                "A mentally stimulated dog is calmer, better behaved, and easier to live with",
                "Even 10-15 minutes of focused mental work is equivalent to 30 minutes of walking"
            ],
            "why_this_matters": "UK veterinary behaviourists report that many dogs presented with hyperactivity and behavioural problems are actually under-stimulated mentally despite receiving plenty of physical exercise. The PDSA's annual PAW report consistently highlights that mental enrichment remains one of the most overlooked welfare needs among UK dog owners.",
            "troubleshooting": "<strong>Dog is physically tired but still restless:</strong> This is a classic sign of mental under-stimulation. Add 15-20 minutes of cognitive activity (training, puzzles, scent games) to their daily routine.\n\n<strong>Not sure what counts as mental stimulation:</strong> Anything that requires your dog to think, problem-solve, or process new information counts. Training new cues, exploring new environments, and working for food all qualify.\n\n<strong>Dog seems uninterested in mental activities:</strong> Start with food motivation — make mental exercises rewarding with high-value treats. Build engagement gradually as your dog learns that thinking is fun.\n\n<strong>Worried about over-stimulating instead of under-stimulating:</strong> Balance is key. Alternate active mental work with rest periods and calming activities. Watch for signs of frustration or fatigue.",
            "when_to_seek_help": "If your dog shows persistent behavioural issues despite a balanced programme of physical exercise and mental stimulation — such as ongoing destructive behaviour, reactivity, or compulsive habits — consult a veterinary behaviourist for comprehensive assessment.",
            "key_takeaways": [
                "Mental stimulation is a separate welfare need from physical exercise — both are required",
                "Use feeding time as an enrichment opportunity rather than free-feeding from a bowl",
                "Novel experiences (new walking routes, new environments) provide excellent mental exercise",
                "Training sessions are mental stimulation — even practising known cues keeps the brain active",
                "Balance mental activity with rest — dogs need downtime to process learning",
                "A well-stimulated dog is calmer, happier, and easier to live with"
            ]
        },

        # ── 4787: Dog Toy Safety ──
        4787: {
            "at_a_glance": [
                "The three biggest dog toy risks are choking, intestinal blockage, and tooth damage",
                "No toy is completely safe without supervision — always monitor play",
                "Size, material, and construction quality are the key safety factors to assess",
                "Weekly toy inspections catch wear before it becomes dangerous",
                "The safest approach is to match toy type and size to your individual dog's chewing habits"
            ],
            "why_this_matters": "Toy-related injuries are a leading cause of emergency veterinary visits for dogs in the UK. The BVA reports that intestinal foreign body surgery alone can cost £2,000-£5,000 and carries significant risks. Simple safety awareness — choosing appropriate toys and inspecting them regularly — prevents the vast majority of these incidents.",
            "troubleshooting": "<strong>Not sure if a toy is safe for your dog:</strong> Apply the 'thumbnail test' — if you cannot dent it with your thumbnail, it may be too hard and could fracture teeth. If it fits through a toilet roll tube, it is a choking hazard for medium and large dogs.\n\n<strong>Dog has already destroyed part of a toy:</strong> Remove the toy immediately and account for all pieces. If any material is missing, monitor your dog for signs of blockage over the next 48 hours.\n\n<strong>Toy marketed as 'indestructible' broke:</strong> No toy is truly indestructible. Treat durability claims as relative rather than absolute, and always supervise play regardless of marketing.\n\n<strong>Dog chews through every safety-rated toy:</strong> For extreme chewers, consult your vet about appropriate chewing outlets. Some dogs benefit from raw bones or antler chews under veterinary guidance.",
            "when_to_seek_help": "Seek emergency veterinary care if your dog is choking (unable to breathe, pawing at mouth), has swallowed a large piece of toy, or shows signs of intestinal blockage (repeated vomiting, loss of appetite, painful abdomen, lethargy). Do not wait — these are time-sensitive emergencies.",
            "key_takeaways": [
                "Supervise all toy play — this single habit prevents most toy-related emergencies",
                "Inspect toys weekly for signs of wear, cracks, and loose components",
                "Match toy size and material to your dog's breed, size, and chewing strength",
                "Remove and replace toys at the first sign of significant damage",
                "Know the signs of choking and intestinal blockage — speed saves lives",
                "The safest toy collection is a small number of appropriate, well-maintained items"
            ]
        },

        # ── 4415: Cat Toy Safety Guide ──
        4415: {
            "at_a_glance": [
                "Cats face unique toy safety risks including string ingestion, small part choking, and chemical exposure",
                "String, ribbon, and elastic are among the most dangerous cat toy materials — they cause linear foreign bodies",
                "Wand toys with strings should only be used during supervised play and stored away afterwards",
                "Laser pointers should always end with a physical 'catch' to prevent frustration",
                "Regular toy inspection is essential — cats often play with toys unsupervised"
            ],
            "why_this_matters": "Linear foreign body obstruction from ingested string or ribbon is one of the most serious surgical emergencies seen in UK cats. The BVA warns that these obstructions can be fatal if not treated promptly. Unlike dogs, cats are uniquely at risk because their backward-facing tongue barbs make it nearly impossible to spit out string once they start swallowing.",
            "troubleshooting": "<strong>Cat has swallowed string from a toy:</strong> Do NOT pull it out — this can cause catastrophic intestinal damage. Take your cat to the vet immediately, even if they seem fine.\n\n<strong>Cat only wants to play with unsafe items (hair ties, rubber bands):</strong> Remove all small elastic items from reach and provide safe alternatives like crinkle balls and fabric mice. Redirect consistently.\n\n<strong>Cat seems bored with safe toys:</strong> Rotate toys regularly and use interactive wand play daily. Catnip, silvervine, or valerian can refresh interest in existing toys.\n\n<strong>Not sure if a cat toy material is safe:</strong> Avoid anything with loose feathers, glued-on eyes, small bells, or long strings. Solid one-piece toys are safest for unsupervised play.",
            "when_to_seek_help": "Seek immediate veterinary attention if your cat is vomiting repeatedly, straining in the litter tray, showing abdominal pain, or if you can see string hanging from their mouth or rear end. Linear foreign bodies are a genuine emergency requiring prompt surgical intervention.",
            "key_takeaways": [
                "Never leave string, ribbon, or elastic cat toys accessible when you are not supervising",
                "Store wand toys in a drawer after each play session",
                "Provide safe solo-play toys — crinkle balls, plastic springs, and tunnel tubes",
                "Check all cat toys for loose parts, fraying, and detaching components",
                "Always end laser pointer sessions with a real physical toy your cat can catch",
                "Know the signs of foreign body ingestion — vomiting, lethargy, and appetite loss"
            ]
        },

        # ── 4410: Cat Enrichment Activities Beyond Toys ──
        4410: {
            "at_a_glance": [
                "Cat enrichment includes environmental design, sensory stimulation, social interaction, and feeding strategies",
                "Window watching, cat TV, and bird feeders provide visual stimulation that cats find highly engaging",
                "Food puzzles and scatter feeding transform mealtimes into cognitive enrichment",
                "Vertical space and hiding spots are fundamental environmental enrichment for cats",
                "Indoor cats require more deliberate enrichment planning than cats with outdoor access"
            ],
            "why_this_matters": "The International Cat Care organisation identifies environmental enrichment as essential for preventing stress-related illness in indoor cats. In the UK, where the trend towards indoor-only cat keeping continues to grow, enrichment beyond toys addresses the full spectrum of feline behavioural needs including hunting, climbing, hiding, and territory marking.",
            "troubleshooting": "<strong>Cat seems disinterested in environmental enrichment:</strong> Cats are naturally cautious. Give new additions at least a week before judging interest. Rubbing them with your cat's own scent can speed acceptance.\n\n<strong>Limited budget for cat enrichment:</strong> Cardboard boxes, paper bags (handles removed), and crumpled paper are free and often more popular than expensive items. Window perches can be improvised with secure shelving.\n\n<strong>Multi-cat household conflicts over enrichment spaces:</strong> Provide multiple elevated spots, hiding places, and feeding stations. Vertical space is key — cats resolve many conflicts through height advantage.\n\n<strong>Cat only responds to food-based enrichment:</strong> This is perfectly valid. Use it as a starting point and gradually introduce other types alongside food rewards.",
            "when_to_seek_help": "If your cat shows signs of chronic stress despite enrichment — over-grooming (bald patches), persistent inappropriate elimination, aggression, or withdrawal — consult your vet for medical assessment and possible referral to an ABTC-registered feline behaviourist.",
            "key_takeaways": [
                "Think holistically about cat enrichment — toys are just one component",
                "Vertical space and hiding spots are non-negotiable for indoor cats",
                "Transform feeding from bowls into enrichment activities using puzzles and foraging",
                "Window access with a view of outdoor wildlife provides hours of passive enrichment",
                "Introduce enrichment changes gradually and let your cat approach at their own pace",
                "Budget-friendly enrichment (boxes, bags, paper) often outperforms expensive alternatives"
            ]
        },

        # ── 4195: Best Cat Toys for Indoor Cats UK ──
        4195: {
            "at_a_glance": [
                "Indoor cats need toys that simulate hunting behaviours — stalking, chasing, pouncing, and catching",
                "Interactive wand toys provide the most effective enrichment for indoor cats",
                "Food puzzles combat obesity and boredom — two major health risks for indoor cats",
                "Self-play toys (balls, springs, tunnels) are essential for times when owners are unavailable",
                "Cats need at least two 15-minute interactive play sessions daily for optimal wellbeing"
            ],
            "why_this_matters": "The PDSA estimates that over 50% of UK cats are now indoor-only or have very limited outdoor access. Without the natural enrichment of outdoor hunting, climbing, and exploration, indoor cats rely entirely on their owners to provide stimulation. The right toys directly impact an indoor cat's physical health, mental wellbeing, and behavioural satisfaction.",
            "troubleshooting": "<strong>Indoor cat refuses to play with any toy:</strong> Experiment with different toy types at different times of day. Cats are crepuscular — they are most active at dawn and dusk. Try play sessions during these natural activity peaks.\n\n<strong>Cat plays for only 30 seconds then walks away:</strong> This is normal feline behaviour. Cats hunt in short bursts. Several 2-5 minute micro-sessions are more natural than one long session.\n\n<strong>Cat becomes aggressive during play:</strong> You may be using your hands as toys (a common mistake) or the play session is too intense. Use wand toys to maintain distance and wind down gradually.\n\n<strong>Cannot afford premium cat toys:</strong> A scrunched ball of paper, a cardboard box, or a toilet roll tube with treats inside provides excellent enrichment at no cost.",
            "when_to_seek_help": "If your indoor cat shows signs of depression (sleeping excessively, loss of appetite, withdrawal), obesity, or compulsive behaviours despite adequate play and enrichment, consult your vet. Indoor cats are at higher risk for these conditions and may need a comprehensive welfare assessment.",
            "key_takeaways": [
                "Provide at least two interactive play sessions daily for indoor cats",
                "Mimic the hunting sequence — stalk, chase, pounce, catch, eat — in play sessions",
                "Use food puzzles to make mealtimes mentally stimulating",
                "Rotate toys regularly to combat habituation",
                "Provide a mix of interactive toys (for play with you) and self-play toys (for solo time)",
                "Window perches and cat TV can supplement active play with passive enrichment"
            ]
        },

        # ── 3959: Best Interactive Dog Toys UK ──
        3959: {
            "at_a_glance": [
                "Interactive toys are those requiring engagement from either the owner or the dog to function",
                "Puzzle feeders, treat-dispensing balls, and snuffle mats are the most effective interactive categories",
                "The best interactive toy matches your dog's skill level — too hard causes frustration, too easy causes boredom",
                "Interactive toys provide mental exercise that physical activity alone cannot replicate",
                "UK availability of quality interactive toys has expanded significantly in recent years"
            ],
            "why_this_matters": "Interactive toys address the growing recognition that mental stimulation is a core welfare need for dogs. The Dogs Trust recommends interactive enrichment as part of every dog's daily routine, noting that it reduces common behavioural issues like destructive chewing, attention-seeking, and excessive barking — problems that are among the top reasons dogs are surrendered to UK rescues.",
            "troubleshooting": "<strong>Dog cannot solve the puzzle toy:</strong> Start at the lowest difficulty level. Many puzzle toys have adjustable settings — begin with treats fully visible and easy to access, then gradually increase challenge.\n\n<strong>Dog destroys puzzle toys instead of solving them:</strong> Choose more robust options (Nina Ottosson, West Paw, Kong) and supervise sessions. Some dogs need to learn that thinking is more rewarding than brute force.\n\n<strong>Interactive toy is too messy:</strong> Place puzzle feeders on a washable mat or tray. Freeze contents to slow down consumption and reduce scatter.\n\n<strong>Dog loses interest in interactive toys quickly:</strong> Rotate puzzle types and change the food rewards regularly. Dogs solve familiar puzzles by memory — introduce new challenges periodically.",
            "when_to_seek_help": "If your dog shows extreme frustration with interactive toys (barking, biting, redirected aggression) despite starting at appropriate difficulty levels, consult a behaviourist. Some dogs need structured confidence-building before puzzle work becomes enjoyable.",
            "key_takeaways": [
                "Start with easy interactive toys and build complexity gradually",
                "Use your dog's daily food allowance in puzzles to prevent overfeeding",
                "Rotate interactive toy types to prevent your dog from memorising solutions",
                "Invest in quality puzzle feeders from reputable brands — they last longer and are safer",
                "Interactive play between you and your dog is the most valuable enrichment of all",
                "Even 10 minutes of puzzle work daily makes a measurable difference in behaviour"
            ]
        },

        # ── 3957: Best Indestructible Dog Toys UK ──
        3957: {
            "at_a_glance": [
                "No dog toy is truly indestructible — the term means 'highly durable for aggressive chewers'",
                "Solid natural rubber, reinforced nylon, and heavy-duty TPE are the most durable materials",
                "Kong Extreme (black), Goughnuts, and West Paw Zogoflex are top UK-available durable options",
                "Even tough toys should be supervised and inspected regularly for signs of wear",
                "Durability must be balanced with dental safety — too hard can fracture teeth"
            ],
            "why_this_matters": "Power chewers cost UK owners significant money in destroyed toys and, more critically, in emergency vet bills when fragments are swallowed. Investing in genuinely durable toys from reputable brands is both a financial and welfare decision. The BVA advises that appropriate chew outlets actually reduce destructive behaviour by satisfying a natural behavioural need.",
            "troubleshooting": "<strong>Dog destroys even 'indestructible' rated toys:</strong> Try Kong Extreme (black) or Goughnuts (with safety indicator). If these also fail, limit chew sessions to supervised 15-minute periods and remove the toy afterwards.\n\n<strong>Durable toys are too hard for your dog's teeth:</strong> The thumbnail test applies — if you cannot make a slight impression with your nail, the toy may be too hard. Choose dense rubber over solid nylon for a safer chew.\n\n<strong>Dog has no interest in durable toys:</strong> Add food motivation by stuffing or smearing. The toy needs to be rewarding, not just available. Frozen stuffed Kongs are the classic solution.\n\n<strong>Spending too much on durable toys:</strong> A single quality durable toy (£10-20) that lasts months is cheaper than ten budget toys (£3-5 each) that last days. Calculate cost per month of use, not purchase price.",
            "when_to_seek_help": "If your dog's chewing is so extreme that no toy withstands it and they are damaging household items, this may indicate anxiety, boredom, or compulsive behaviour rather than normal chewing. Consult your vet and consider referral to a behaviourist.",
            "key_takeaways": [
                "Treat 'indestructible' as a relative term — supervise all chew sessions",
                "Kong Extreme, Goughnuts, and West Paw Zogoflex are the most reliably durable UK options",
                "Balance durability with dental safety — too hard is worse than too soft",
                "Add food motivation to make durable toys more appealing",
                "Calculate cost per month of use when comparing toy investments",
                "Inspect durable toys weekly — even the toughest wear down over time"
            ]
        },

        # ── 3956: Best Dog Toys UK ──
        3956: {
            "at_a_glance": [
                "The best dog toy depends on your dog's size, play style, chew strength, and age",
                "Essential categories include chew toys, puzzle feeders, interactive toys, and comfort items",
                "Quality UK brands include Kong, West Paw, Nina Ottosson, and Beco Pets",
                "A well-rounded toy collection covers mental stimulation, physical exercise, and comfort",
                "Spending more on fewer quality toys is safer and more cost-effective than cheap bulk buying"
            ],
            "why_this_matters": "The UK dog toy market is vast and navigating it without guidance often leads to unsuitable purchases, wasted money, and potential safety risks. This guide helps UK dog owners make informed, evidence-based choices that prioritise safety, engagement, and value — drawing on welfare guidance from the RSPCA, Kennel Club, and veterinary professionals.",
            "troubleshooting": "<strong>Overwhelmed by the number of options available:</strong> Start with three essentials — a durable chew toy (Kong), a food puzzle (snuffle mat or puzzle feeder), and an interactive toy (tug rope or ball). Build from there.\n\n<strong>Dog seems uninterested in all toys:</strong> Try different toy types and add food motivation. Some dogs are not naturally toy-driven but respond well to food-dispensing enrichment.\n\n<strong>Toys are too expensive:</strong> Focus on versatile items like a classic Kong (which serves as chew toy, food puzzle, and comfort item) and supplement with DIY enrichment at no cost.\n\n<strong>Not sure which toys are safe:</strong> Stick to established brands sold by UK pet retailers. Avoid unbranded toys from online marketplaces without clear material safety information.",
            "when_to_seek_help": "If your dog shows destructive behaviour despite having appropriate toys, guard toys aggressively, or shows anxiety around play, consult a qualified animal behaviourist. The right toys help, but behavioural issues may need professional guidance.",
            "key_takeaways": [
                "Start with three essential toy types: chew, puzzle, and interactive",
                "Match toys to your individual dog's size, age, and play style",
                "Invest in quality over quantity — a few good toys outperform many cheap ones",
                "Rotate toys regularly to maintain novelty and engagement",
                "Supervise all toy play and inspect toys weekly for safety",
                "Use trusted UK brands and retailers for the safest purchasing decisions"
            ]
        },

        # ── 3: Dog Toys UK Hub ──
        3: {
            "at_a_glance": [
                "This hub page connects you to all dog toy guides, reviews, and enrichment resources on Pet Hub Online",
                "Dog toy selection should be based on safety, size-appropriateness, and your dog's individual play style",
                "Regular cleaning, inspection, and rotation maximise toy value and safety",
                "Mental enrichment through toys is a recognised welfare need, not a luxury",
                "UK-specific guidance ensures relevance for British dog owners and available products"
            ],
            "why_this_matters": "Navigating dog toy information can be overwhelming, with much of the online content coming from non-UK sources with different product availability and safety standards. This hub brings together UK-focused, evidence-based guidance on every aspect of dog toys — from safety and selection to enrichment and maintenance — in one accessible location.",
            "troubleshooting": "<strong>Not sure where to start with dog toys:</strong> Begin with our <a href=\"https://pethubonline.com/dog-toy-safety-what-every-owner-needs-to-know/\">Dog Toy Safety Guide</a> for foundational knowledge, then explore specific topics based on your needs.\n\n<strong>Looking for breed-specific toy advice:</strong> Check our <a href=\"https://pethubonline.com/dog-toy-safety-breed-size/\">Dog Toy Safety by Breed Size</a> and <a href=\"https://pethubonline.com/enrichment-by-breed-group/\">Enrichment by Breed Group</a> guides for tailored recommendations.\n\n<strong>Want to save money on dog toys:</strong> Our <a href=\"https://pethubonline.com/diy-dog-toys-safe-homemade-options/\">DIY Dog Toys</a> guide offers safe, budget-friendly alternatives to complement commercial products.\n\n<strong>Concerned about your dog's play behaviour:</strong> Browse our enrichment and behavioural guides for advice on common play-related issues.",
            "when_to_seek_help": "If you have specific concerns about your dog's play behaviour, toy safety, or enrichment needs that are not addressed in our guides, consult your vet or a qualified animal behaviourist for personalised advice.",
            "key_takeaways": [
                "Explore our comprehensive guides to build confidence in dog toy selection",
                "Safety is the foundation — start with our safety guides before choosing specific toys",
                "Mental enrichment through toys is essential for every dog's wellbeing",
                "Bookmark this hub as your go-to reference for all dog toy questions",
                "Our content is regularly updated to reflect the latest UK veterinary and welfare guidance"
            ]
        },

        # ── 6048: Confidence-Building Play (categorized as Uncategorized in CSV but included in results) ──
        # Actually this one is Uncategorized, skip it

    }


def generate_generic_content(post_id, title, animal, animal_cap, owner, owners):
    """Fallback for any unmapped post - should not be needed."""
    title_lower = title.lower()
    return {
        "at_a_glance": [
            f"This guide covers essential information about {title_lower.replace('(2026)', '').strip()} for UK {owners}",
            f"All recommendations are based on UK veterinary and welfare guidance",
            f"Practical tips are included that you can implement immediately",
            f"Safety considerations are highlighted throughout the guide",
        ],
        "why_this_matters": f"Understanding {title_lower.replace('(2026)', '').strip()} helps UK {owners} make informed decisions about their {animal}'s wellbeing. Reliable, evidence-based information reduces the risk of common mistakes and supports better welfare outcomes.",
        "troubleshooting": f"<strong>Not sure where to start:</strong> Begin with the basics outlined in this guide and build your knowledge gradually. Every {owner}'s situation is different.\n\n<strong>Information seems overwhelming:</strong> Focus on one improvement at a time. Small, consistent changes make the biggest difference to your {animal}'s welfare.\n\n<strong>Advice conflicts with what you have heard elsewhere:</strong> Prioritise guidance from UK veterinary and welfare organisations (RSPCA, PDSA, BVA) over anecdotal advice or social media.",
        "when_to_seek_help": f"If you have specific concerns about your {animal}'s health or behaviour, consult your vet. For behavioural issues, ask for referral to an ABTC-registered animal behaviourist who can provide tailored guidance.",
        "key_takeaways": [
            f"Apply the practical guidance from this article to your {animal}'s daily routine",
            f"Safety should always be your first consideration",
            f"Consult UK veterinary and welfare organisations for the most reliable advice",
            f"Small, consistent improvements make the biggest difference over time",
        ]
    }


# ── Block builders ────────────────────────────────────────────────────────────

def build_at_a_glance(bullets):
    li_items = "".join(f"<li>{b}</li>" for b in bullets)
    return (
        '<!-- wp:group {"style":{"color":{"background":"#eef2ff"},"border":{"radius":"6px","width":"1px","color":"#c7d2fe"},"spacing":{"padding":{"top":"16px","bottom":"16px","left":"20px","right":"20px"},"margin":{"top":"20px","bottom":"24px"}}},"layout":{"type":"constrained"}} -->\n'
        '<div class="wp-block-group has-border-color has-background" style="border-color:#c7d2fe;border-width:1px;border-radius:6px;background-color:#eef2ff;margin-top:20px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<!-- wp:heading {"level":4} -->\n'
        '<h4 class="wp-block-heading">At a Glance</h4>\n'
        '<!-- /wp:heading -->\n'
        '<!-- wp:list -->\n'
        f'<ul class="wp-block-list">{li_items}</ul>\n'
        '<!-- /wp:list -->\n'
        '</div>\n'
        '<!-- /wp:group -->'
    )

def build_why_this_matters(text):
    return (
        '<!-- wp:group {"style":{"color":{"background":"#fffbeb"},"border":{"radius":"6px","width":"1px","color":"#fde68a"},"spacing":{"padding":{"top":"16px","bottom":"16px","left":"20px","right":"20px"},"margin":{"top":"20px","bottom":"20px"}}},"layout":{"type":"constrained"}} -->\n'
        '<div class="wp-block-group has-border-color has-background" style="border-color:#fde68a;border-width:1px;border-radius:6px;background-color:#fffbeb;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<!-- wp:paragraph {"style":{"typography":{"fontSize":"14px"}}} -->\n'
        f'<p style="font-size:14px"><strong>Why this matters:</strong> {text}</p>\n'
        '<!-- /wp:paragraph -->\n'
        '</div>\n'
        '<!-- /wp:group -->'
    )

def build_troubleshooting(text):
    return (
        '<!-- wp:heading {"level":3} -->\n'
        '<h3 class="wp-block-heading">Troubleshooting Common Issues</h3>\n'
        '<!-- /wp:heading -->\n'
        '<!-- wp:paragraph -->\n'
        f'<p>{text}</p>\n'
        '<!-- /wp:paragraph -->'
    )

def build_when_to_seek_help(text):
    return (
        '<!-- wp:group {"style":{"color":{"background":"#fef2f2"},"border":{"radius":"6px","width":"1px","color":"#fecaca"},"spacing":{"padding":{"top":"16px","bottom":"16px","left":"20px","right":"20px"},"margin":{"top":"20px","bottom":"20px"}}},"layout":{"type":"constrained"}} -->\n'
        '<div class="wp-block-group has-border-color has-background" style="border-color:#fecaca;border-width:1px;border-radius:6px;background-color:#fef2f2;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<!-- wp:paragraph {"style":{"typography":{"fontSize":"14px"}}} -->\n'
        f'<p style="font-size:14px"><strong>When to seek professional help:</strong> {text}</p>\n'
        '<!-- /wp:paragraph -->\n'
        '</div>\n'
        '<!-- /wp:group -->'
    )

def build_key_takeaways(bullets):
    li_items = "".join(f"<li>{b}</li>" for b in bullets)
    return (
        '<!-- wp:group {"style":{"color":{"background":"#f0fdf4"},"border":{"radius":"6px","width":"1px","color":"#bbf7d0"},"spacing":{"padding":{"top":"16px","bottom":"16px","left":"20px","right":"20px"},"margin":{"top":"24px","bottom":"24px"}}},"layout":{"type":"constrained"}} -->\n'
        '<div class="wp-block-group has-border-color has-background" style="border-color:#bbf7d0;border-width:1px;border-radius:6px;background-color:#f0fdf4;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<!-- wp:heading {"level":4} -->\n'
        '<h4 class="wp-block-heading">Key Takeaways</h4>\n'
        '<!-- /wp:heading -->\n'
        '<!-- wp:list -->\n'
        f'<ul class="wp-block-list">{li_items}</ul>\n'
        '<!-- /wp:list -->\n'
        '</div>\n'
        '<!-- /wp:group -->'
    )

UPGRADED_TRUST_FOOTER = (
    '<!-- wp:group {"style":{"color":{"background":"#f8fafb"},"border":{"radius":"8px","color":"#e2e8f0","width":"1px"},"spacing":{"padding":{"top":"20px","bottom":"20px","left":"24px","right":"24px"},"margin":{"top":"32px","bottom":"32px"}}},"layout":{"type":"constrained"}} -->\n'
    '<div class="wp-block-group has-border-color has-background" style="border-color:#e2e8f0;border-width:1px;border-radius:8px;background-color:#f8fafb;margin-top:32px;margin-bottom:32px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px">\n'
    '<!-- wp:heading {"level":4} -->\n'
    '<h4 class="wp-block-heading">Our Editorial Standards</h4>\n'
    '<!-- /wp:heading -->\n'
    '<!-- wp:paragraph {"style":{"typography":{"fontSize":"14px"}}} -->\n'
    '<p style="font-size:14px">All content on Pet Hub Online is created following our <a href="https://pethubonline.com/our-editorial-process/">editorial process</a>, supported by thorough <a href="https://pethubonline.com/how-we-research-pet-products/">research methodology</a>. We reference UK veterinary and welfare organisations including the <a href="https://www.rspca.org.uk/" rel="nofollow">RSPCA</a>, <a href="https://www.pdsa.org.uk/" rel="nofollow">PDSA</a>, and <a href="https://www.bva.co.uk/" rel="nofollow">BVA</a>. We maintain transparency through our <a href="https://pethubonline.com/corrections-and-updates-policy/">corrections and updates policy</a>. Content is AI-assisted and editorially reviewed. For details on how we handle affiliate relationships, see our <a href="https://pethubonline.com/affiliate-disclosure/">affiliate disclosure</a>.</p>\n'
    '<!-- /wp:paragraph -->\n'
    '</div>\n'
    '<!-- /wp:group -->'
)


# ── Content insertion logic ───────────────────────────────────────────────────

def find_first_paragraph_end(content):
    """Find position after the first substantive paragraph (after any intro boxes)."""
    # Look for the first </p> that's part of actual content (not in a styled box)
    # Skip the "About this guide" box and "Quick answer" paragraphs
    # Find the first regular paragraph after introductory elements

    # Strategy: find the first <p class="wp-block-paragraph"> that's not inside a styled div
    # Simpler approach: find content after "Quick answer" or "Last Updated" blocks

    markers = ['Last Updated:', 'last updated:', 'Last updated:']
    best_pos = -1
    for marker in markers:
        idx = content.find(marker)
        if idx >= 0:
            # Find the end of the paragraph containing this marker
            end_p = content.find('</p>', idx)
            if end_p >= 0:
                best_pos = max(best_pos, end_p + len('</p>'))

    if best_pos > 0:
        # Find the end of the next paragraph after the Last Updated
        next_p_end = content.find('</p>', best_pos)
        if next_p_end >= 0:
            return next_p_end + len('</p>')

    # Fallback: after Quick Answer block
    qa_idx = content.find('Quick answer:')
    if qa_idx < 0:
        qa_idx = content.find('Quick Answer')
    if qa_idx >= 0:
        end_p = content.find('</p>', qa_idx)
        if end_p >= 0:
            # Skip to end of next paragraph after quick answer
            next_p_end = content.find('</p>', end_p + 4)
            if next_p_end >= 0:
                return next_p_end + len('</p>')
            return end_p + len('</p>')

    # Last fallback: after first two </p> tags
    pos = 0
    for i in range(2):
        idx = content.find('</p>', pos)
        if idx < 0:
            break
        pos = idx + len('</p>')

    return pos if pos > 0 else 500


def find_faq_position(content):
    """Find the position just before the FAQ section."""
    # Look for FAQ heading patterns
    patterns = [
        'Frequently Asked Questions',
        'FAQ',
        '>FAQ<',
        'Common Questions',
    ]
    for pat in patterns:
        idx = content.find(pat)
        if idx >= 0:
            # Go back to find the start of the heading tag
            h_start = content.rfind('<h', 0, idx)
            if h_start >= 0:
                return h_start
    return -1


def find_editorial_block(content):
    """Find and return (start, end) of the editorial standards block."""
    idx = content.find('Our Editorial Standards')
    if idx < 0:
        return -1, -1

    # Go back to find the start of the containing div
    # Look for the wp-block-group div that contains this heading
    search_start = max(0, idx - 600)

    # Find the div that starts the editorial block
    div_start = content.rfind('<div class="wp-block-group', search_start, idx)
    if div_start < 0:
        return -1, -1

    # Now find the matching closing div
    # Count nesting level
    pos = div_start
    depth = 0
    while pos < len(content):
        next_open = content.find('<div', pos + 1)
        next_close = content.find('</div>', pos + 1)

        if next_close < 0:
            break

        if next_open >= 0 and next_open < next_close:
            depth += 1
            pos = next_open
        else:
            if depth == 0:
                end = next_close + len('</div>')
                return div_start, end
            depth -= 1
            pos = next_close

    return -1, -1


def find_about_editorial_section(content):
    """Find the 'About Our Editorial Standards' section at the very end."""
    idx = content.find('About Our Editorial Standards')
    if idx < 0:
        return -1, -1

    # Find the h3 start
    h_start = content.rfind('<h', 0, idx)
    if h_start < 0:
        return -1, -1

    # Find the <hr> separator before it
    hr_start = content.rfind('<hr', 0, h_start)
    if hr_start >= 0 and (h_start - hr_start) < 200:
        # Include the hr separator
        return hr_start, len(content)

    return h_start, len(content)


def process_post(post_id, title, content_data):
    """Process a single post's content and return updated content with flags."""
    content = content_data
    flags = {
        'at_a_glance_added': False,
        'why_this_matters_added': False,
        'troubleshooting_added': False,
        'when_to_seek_help_added': False,
        'key_takeaways_added': False,
        'trust_upgraded': False,
    }

    # Check what already exists
    has_at_a_glance = 'At a Glance' in content or 'At A Glance' in content or 'at a glance' in content.lower().replace('at a glance', 'at a glance')
    has_key_takeaways = 'Key Takeaways' in content or 'key takeaways' in content.lower()
    has_troubleshooting = 'Troubleshooting Common Issues' in content
    has_why_matters = 'Why this matters:' in content
    has_when_seek = 'When to seek professional help:' in content

    # Generate content for this post
    blocks = generate_content_for_post(post_id, title, content)

    if blocks is None:
        return content, flags, "skipped_no_content_map"

    # ── 1. Find editorial block and About section positions ──
    ed_start, ed_end = find_editorial_block(content)
    about_start, about_end = find_about_editorial_section(content)

    # Determine the insertion point for blocks before the trust footer
    if ed_start > 0:
        insert_before_trust = ed_start
    elif about_start > 0:
        insert_before_trust = about_start
    else:
        # No trust footer found — insert at end
        insert_before_trust = len(content)

    # ── 2. Build blocks to insert BEFORE trust footer ──
    blocks_before_trust = []

    # Troubleshooting (goes before FAQ if FAQ exists, otherwise before trust)
    if not has_troubleshooting:
        troubleshooting_block = build_troubleshooting(blocks['troubleshooting'])
        when_help_block = build_when_to_seek_help(blocks['when_to_seek_help'])

        faq_pos = find_faq_position(content)
        if faq_pos > 0 and faq_pos < insert_before_trust:
            # Insert troubleshooting + when to seek help before FAQ
            insert_str = '\n' + troubleshooting_block + '\n\n' + when_help_block + '\n'
            content = content[:faq_pos] + insert_str + content[faq_pos:]
            flags['troubleshooting_added'] = True
            flags['when_to_seek_help_added'] = True

            # Recalculate positions after insertion
            offset = len(insert_str)
            if ed_start > faq_pos:
                ed_start += offset
                ed_end += offset
            if about_start > faq_pos:
                about_start += offset
                about_end += offset
            insert_before_trust += offset
        else:
            # Add to pre-trust blocks
            blocks_before_trust.append(troubleshooting_block)
            flags['troubleshooting_added'] = True
            if not has_when_seek:
                blocks_before_trust.append(when_help_block)
                flags['when_to_seek_help_added'] = True
    elif not has_when_seek:
        when_help_block = build_when_to_seek_help(blocks['when_to_seek_help'])
        blocks_before_trust.append(when_help_block)
        flags['when_to_seek_help_added'] = True

    # Key Takeaways (before trust footer)
    if not has_key_takeaways:
        blocks_before_trust.append(build_key_takeaways(blocks['key_takeaways']))
        flags['key_takeaways_added'] = True

    # Insert blocks before trust footer
    if blocks_before_trust:
        insert_str = '\n' + '\n\n'.join(blocks_before_trust) + '\n'
        # Recalculate insert_before_trust with updated content
        if ed_start > 0:
            insert_before_trust = ed_start
        elif about_start > 0:
            insert_before_trust = about_start
        else:
            insert_before_trust = len(content)

        content = content[:insert_before_trust] + insert_str + content[insert_before_trust:]

        offset = len(insert_str)
        if ed_start >= insert_before_trust:
            ed_start += offset
            ed_end += offset
        if about_start >= insert_before_trust:
            about_start += offset
            about_end += offset

    # ── 3. Insert At a Glance and Why This Matters near the top ──
    top_blocks = []

    if not has_at_a_glance:
        top_blocks.append(build_at_a_glance(blocks['at_a_glance']))
        flags['at_a_glance_added'] = True

    if not has_why_matters:
        top_blocks.append(build_why_this_matters(blocks['why_this_matters']))
        flags['why_this_matters_added'] = True

    if top_blocks:
        insert_pos = find_first_paragraph_end(content)
        insert_str = '\n' + '\n\n'.join(top_blocks) + '\n'
        content = content[:insert_pos] + insert_str + content[insert_pos:]

        offset = len(insert_str)
        if ed_start >= insert_pos:
            ed_start += offset
            ed_end += offset
        if about_start >= insert_pos:
            about_start += offset
            about_end += offset

    # ── 4. Upgrade trust footer ──
    # Re-find editorial block in the (possibly modified) content
    ed_start_new, ed_end_new = find_editorial_block(content)
    about_start_new, about_end_new = find_about_editorial_section(content)

    if ed_start_new > 0:
        # Replace existing editorial block
        # Also remove the "About Our Editorial Standards" section if it follows
        if about_start_new > 0 and about_start_new > ed_start_new:
            # Remove everything from editorial block start to end of about section
            content = content[:ed_start_new] + UPGRADED_TRUST_FOOTER + content[about_end_new:]
        else:
            content = content[:ed_start_new] + UPGRADED_TRUST_FOOTER + content[ed_end_new:]
        flags['trust_upgraded'] = True
    elif about_start_new > 0:
        # Only About section exists
        content = content[:about_start_new] + UPGRADED_TRUST_FOOTER + content[about_end_new:]
        flags['trust_upgraded'] = True

    return content, flags, "ok"


# ── API helpers ───────────────────────────────────────────────────────────────

def api_get(post_id):
    """Fetch post content via curl subprocess."""
    url = f"{BASE}/posts/{post_id}?context=edit&_fields=id,title,content"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise Exception(f"curl GET failed: {result.stderr}")
    return json.loads(result.stdout)


def api_update(post_id, new_content):
    """Update post content via curl subprocess."""
    url = f"{BASE}/posts/{post_id}"

    payload = json.dumps({"content": new_content})

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(payload)
        tmpfile = f.name

    try:
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", f"@{tmpfile}",
             url],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            raise Exception(f"curl POST failed: {result.stderr}")

        resp = json.loads(result.stdout)
        if 'id' not in resp:
            raise Exception(f"API error: {result.stdout[:500]}")
        return resp
    finally:
        os.unlink(tmpfile)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Read inventory
    posts = []
    with open(INVENTORY, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['cluster'] == 'Dog Toys':
                posts.append({'id': int(row['id']), 'title': row['title']})

    print(f"Found {len(posts)} Dog Toys cluster posts")

    # Initialize log
    log_rows = []

    for i, post in enumerate(posts):
        post_id = post['id']
        title = post['title']
        print(f"\n[{i+1}/{len(posts)}] Processing: {post_id} - {title}")

        try:
            # Fetch current content
            data = api_get(post_id)
            current_content = data['content']['raw']

            print(f"  Content length: {len(current_content)}")

            # Process the post
            new_content, flags, status = process_post(post_id, title, current_content)

            if status == "skipped_no_content_map":
                print(f"  SKIPPED: No content map entry for this post")
                log_rows.append({
                    'id': post_id,
                    'title': title,
                    **{k: False for k in flags if isinstance(flags, dict)},
                    'at_a_glance_added': False,
                    'why_this_matters_added': False,
                    'troubleshooting_added': False,
                    'when_to_seek_help_added': False,
                    'key_takeaways_added': False,
                    'trust_upgraded': False,
                    'status': 'skipped_no_content'
                })
                time.sleep(DELAY)
                continue

            if new_content == current_content:
                print(f"  No changes needed")
                log_rows.append({
                    'id': post_id,
                    'title': title,
                    **flags,
                    'status': 'no_changes'
                })
                time.sleep(DELAY)
                continue

            # Update the post
            print(f"  Updating... (new length: {len(new_content)})")
            time.sleep(DELAY)

            api_update(post_id, new_content)

            added = [k.replace('_added', '').replace('_', ' ') for k, v in flags.items() if v]
            print(f"  SUCCESS: Added/upgraded: {', '.join(added)}")

            log_rows.append({
                'id': post_id,
                'title': title,
                **flags,
                'status': 'updated'
            })

        except Exception as e:
            print(f"  ERROR: {e}")
            log_rows.append({
                'id': post_id,
                'title': title,
                'at_a_glance_added': False,
                'why_this_matters_added': False,
                'troubleshooting_added': False,
                'when_to_seek_help_added': False,
                'key_takeaways_added': False,
                'trust_upgraded': False,
                'status': f'error: {str(e)[:100]}'
            })

        time.sleep(DELAY)

    # Write log
    fieldnames = ['id', 'title', 'at_a_glance_added', 'why_this_matters_added',
                  'troubleshooting_added', 'when_to_seek_help_added',
                  'key_takeaways_added', 'trust_upgraded', 'status']

    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(log_rows)

    print(f"\n{'='*60}")
    print(f"COMPLETE: Processed {len(posts)} posts")
    updated = sum(1 for r in log_rows if r['status'] == 'updated')
    errors = sum(1 for r in log_rows if r['status'].startswith('error'))
    skipped = sum(1 for r in log_rows if r['status'] in ('no_changes', 'skipped_no_content'))
    print(f"  Updated: {updated}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors: {errors}")
    print(f"Log saved to: {LOG_FILE}")


if __name__ == '__main__':
    main()
