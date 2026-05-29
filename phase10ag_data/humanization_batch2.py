#!/usr/bin/env python3
"""
Phase 10AG Batch 2: Add humanization + buyer-intent blocks to posts in
Cat Supplies, Cat Toys, Dog Harnesses, Dog Beds, Indoor Cats, and Educational
clusters that don't already have them.

Blocks added:
1. "About This Guide" editorial block
2. "Common Mistakes to Avoid"
3. "Quick Suitability Guide"
4. "What to Expect" (where applicable)
5. Practical Routine Checklist (where applicable)
6. Key Considerations / Pros-Cons (for product guides)
"""

import subprocess
import json
import time
import csv
import os
import sys
import tempfile
import html as html_mod
import re

WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
LOG_DIR = "/var/lib/freelancer/projects/40416335/phase10ag_data"
LOG_FILE = os.path.join(LOG_DIR, "humanization_batch2_log.csv")

ALREADY_TREATED = {3956, 3957, 3959, 5421, 5423, 5469, 5471, 5476, 5483, 5509,
                   3996, 4004, 4011, 4018, 4784, 4174, 4181, 4188, 4286, 4307,
                   4057, 4064, 4071, 4078, 4563, 4118, 4132, 4089, 4146, 5508}

# ─── Cluster definitions ──────────────────────────────────────────────────────

ABOUT_TEMPLATES = {
    "Cat Supplies": "This guide was developed using published advice from Cats Protection, International Cat Care, and the RSPCA, focusing on practical product guidance for UK cat owners.",
    "Cat Toys": "Our team reviewed published guidance from Cats Protection and International Cat Care on feline play behaviour to compile this resource.",
    "Dog Harnesses": "This guide draws on fitting and safety guidance from the Kennel Club and Dogs Trust, alongside published veterinary recommendations.",
    "Dog Beds": "We reviewed published guidance from veterinary orthopaedic sources and UK pet welfare charities to compile this bedding guide.",
    "Indoor Cats": "This resource is based on published indoor cat welfare guidance from International Cat Care and Cats Protection.",
    "Educational": "This educational resource was compiled using published guidance from UK veterinary organisations and pet welfare charities.",
}

# ─── Per-post content definitions ────────────────────────────────────────────

# Cat Supplies cluster
POST_DATA = {
    # ── Cat Supplies ──────────────────────────────────────────────────────
    4335: {
        "cluster": "Cat Supplies",
        "common_mistakes": [
            "Using standard bin bags instead of sealed disposal bags — the smell escapes quickly and permeates the room.",
            "Flushing cat litter down the toilet — even 'flushable' types can damage plumbing and introduce Toxoplasma into waterways.",
            "Placing the disposal bin far from the litter tray — inconvenience leads to delayed scooping and odour build-up.",
            "Forgetting to clean the disposal bin itself — internal residue accumulates and creates a persistent smell regardless of bag quality.",
        ],
        "suitability": [
            "<strong>Best for small flats:</strong> Sealed disposal bins with odour-lock lids that contain smell in compact living spaces.",
            "<strong>Best for multi-cat households:</strong> Larger-capacity bins or dual-bin setups that handle higher waste volumes without daily outdoor trips.",
            "<strong>Best for eco-conscious owners:</strong> Biodegradable disposal bags paired with compostable litter for reduced environmental impact.",
            "<strong>Best for convenience-focused owners:</strong> One-hand-operation disposal bins that streamline the daily scooping routine.",
            "<strong>Best on a budget:</strong> Nappy disposal bags are widely available, inexpensive, and seal odour effectively for standard waste volumes.",
        ],
        "pros_cons": {
            "advantages": [
                "A dedicated disposal system controls odour far more effectively than a standard household bin.",
                "Sealed disposal reduces bacterial spread, which is particularly important for immunocompromised owners.",
                "Streamlines the daily scooping routine, making consistent tray hygiene more achievable.",
            ],
            "considerations": [
                "Proprietary refill cartridges for some systems add ongoing running costs.",
                "Disposal bins still require regular cleaning to prevent internal odour build-up.",
                "Biodegradable bag options exist but typically cost more than standard plastic alternatives.",
            ],
        },
        "routine": {
            "title": "Quick Waste Disposal Routine",
            "items": [
                "Daily: Scoop waste into a lined disposal bin or sealed bag immediately after cleaning the tray.",
                "Weekly: Empty the disposal bin and wipe it down with mild disinfectant to prevent odour build-up.",
                "Fortnightly: Check your disposal bag supply and restock before running out.",
                "Monthly: Clean the area around the disposal bin and litter tray to prevent bacterial transfer.",
                "Ongoing: Never flush cat litter — even types labelled 'flushable' can cause blockages and environmental harm.",
            ],
        },
    },
    4328: {
        "cluster": "Cat Supplies",
        "common_mistakes": [
            "Assuming self-cleaning trays eliminate all maintenance — the waste receptacle still needs regular emptying and the tray needs periodic deep cleaning.",
            "Choosing a noisy model for a timid cat — mechanical sounds can frighten noise-sensitive cats away from using the tray entirely.",
            "Placing the self-cleaning tray in a tight corner without ventilation — odour still builds if airflow is restricted around the unit.",
            "Skipping the transition period — most cats need gradual introduction, with the old tray available alongside the new one for at least a week.",
        ],
        "suitability": [
            "<strong>Best for busy owners:</strong> Self-cleaning trays reduce daily scooping to occasional waste drawer emptying, saving significant time.",
            "<strong>Best for multi-cat households:</strong> Models with frequent cleaning cycles keep the tray fresh between uses, reducing avoidance behaviour.",
            "<strong>Best for odour-sensitive households:</strong> Automatic cleaning after each use prevents waste from sitting and generating smell.",
            "<strong>Best for confident, adaptable cats:</strong> Cats that are not easily startled by mechanical noise adapt fastest to self-cleaning units.",
            "<strong>Best on a budget:</strong> Semi-automatic rake-style trays offer most of the convenience benefit at a fraction of the price of fully electronic models.",
        ],
        "pros_cons": {
            "advantages": [
                "Dramatically reduces the time and effort required for daily litter maintenance.",
                "Consistent automatic cleaning means the tray stays fresher between owner interventions.",
                "Useful for owners with mobility limitations who find manual scooping difficult.",
            ],
            "considerations": [
                "Higher upfront cost compared to standard trays, with ongoing costs for proprietary accessories.",
                "Mechanical components can malfunction, requiring troubleshooting or replacement parts.",
                "Not all cats accept self-cleaning trays — some are permanently deterred by the noise or motion.",
            ],
        },
    },
    4321: {
        "cluster": "Cat Supplies",
        "common_mistakes": [
            "Switching litter types abruptly — cats can be extremely particular about texture and scent, and sudden changes may cause tray avoidance.",
            "Choosing scented litter for human preference — many cats dislike strong fragrances and may refuse to use the tray.",
            "Not filling the tray deep enough — most cats need 5 to 7 centimetres of litter depth for comfortable digging and covering.",
            "Storing opened litter bags in damp areas — moisture-compromised litter clumps poorly and loses odour-control effectiveness.",
        ],
        "suitability": [
            "<strong>Best for odour control:</strong> Clumping clay or silica crystal litters that form tight clumps and trap odour when scooped daily.",
            "<strong>Best for kittens:</strong> Non-clumping litter until around 12 weeks old, as young kittens may ingest clumping litter during exploration.",
            "<strong>Best for cats with respiratory sensitivity:</strong> Low-dust or dust-free formulas such as natural paper or wood pellet litters.",
            "<strong>Best for the environment:</strong> Biodegradable litters made from wood, paper, corn, or tofu that decompose more sustainably than clay.",
            "<strong>Best on a budget:</strong> Wood pellet litter offers excellent absorbency and odour control at the lowest ongoing monthly cost.",
        ],
        "routine": {
            "title": "Quick Litter Management Checklist",
            "items": [
                "Daily: Scoop all clumps and solids — consistent daily scooping extends the usable life of clumping litter significantly.",
                "Weekly: Stir remaining litter to distribute moisture evenly and check for odour breakthrough.",
                "Fortnightly: Complete litter change for non-clumping types; top up for clumping types as needed.",
                "Monthly: Deep clean the tray during a full litter change using hot water and mild soap only.",
                "Ongoing: Store unused litter sealed in a cool, dry place to maintain clumping and odour-control performance.",
            ],
        },
        "pros_cons": {
            "advantages": [
                "Choosing the right litter type significantly reduces odour, tracking, and daily maintenance effort.",
                "Clumping litters make waste removal faster and more hygienic with daily scooping.",
                "Natural litter alternatives are better for the environment and reduce the dust associated with clay.",
            ],
            "considerations": [
                "Cats can be highly particular about litter texture and scent — any change needs gradual transition.",
                "Scented litters may appeal to owners but can actively deter cats with sensitive noses.",
                "Natural litters may not clump as tightly as clay, sometimes requiring more frequent full changes.",
            ],
        },
    },
    4314: {
        "cluster": "Cat Supplies",
        "common_mistakes": [
            "Buying a tray that is too small — the tray should be at least 1.5 times your cat's body length for comfortable use.",
            "Placing the tray near food or water bowls — cats instinctively avoid toileting near their food source.",
            "Having too few trays in a multi-cat household — the standard guideline is one tray per cat plus one extra.",
            "Choosing a covered tray without checking your cat's preference — some cats feel trapped and may avoid hooded designs.",
        ],
        "suitability": [
            "<strong>Best for kittens:</strong> Low-sided, open trays without lids that are easy to access during litter training.",
            "<strong>Best for large breeds (Maine Coon, Ragdoll):</strong> Extra-large trays with high sides to prevent scatter — standard sizes are often too small.",
            "<strong>Best for multi-cat households:</strong> One tray per cat plus one extra, placed in separate locations throughout the home.",
            "<strong>Best for odour control:</strong> Covered or hooded trays with carbon filters, combined with daily scooping.",
            "<strong>Best on a budget:</strong> A large, basic open tray scooped daily is more hygienic than an expensive self-cleaning unit used inconsistently.",
        ],
        "routine": {
            "title": "Quick Litter Tray Maintenance Checklist",
            "items": [
                "Daily: Scoop clumps and solid waste at least once, ideally twice for multi-cat households.",
                "Weekly: Top up litter to maintain a depth of 5 to 7 centimetres for effective clumping and digging.",
                "Fortnightly: Full litter change and tray wash with warm water and mild, unscented soap.",
                "Monthly: Inspect the tray for scratches or cracks where bacteria can harbour — replace heavily damaged trays.",
                "Every 6 to 12 months: Replace the entire tray, as plastic absorbs odours over time regardless of cleaning frequency.",
            ],
        },
        "pros_cons": {
            "advantages": [
                "A clean, appropriately sized tray is the foundation of reliable indoor toileting behaviour.",
                "The right tray size and style reduces litter scatter and makes cleaning more efficient.",
                "Covered trays contain odour and provide the privacy that some cats prefer.",
            ],
            "considerations": [
                "Covered trays can trap odour inside, making the tray unpleasant for the cat even when owners cannot detect it.",
                "Self-cleaning trays have mechanical parts that can malfunction and may frighten noise-sensitive cats.",
                "The one-tray-per-cat-plus-one guideline means multiple trays in multi-cat homes, which requires dedicated space.",
            ],
        },
    },
    4223: {
        "cluster": "Cat Supplies",
        "common_mistakes": [
            "Fitting a window perch to a single-glazed or poorly sealed window — the suction cups may not hold on uneven or cold surfaces.",
            "Not checking the weight rating before purchase — a perch that collapses under your cat will create lasting fear of using it.",
            "Positioning the perch where direct sunlight creates excessive heat — cats can overheat, especially in summer.",
            "Ignoring the view — perches overlooking a blank wall provide no enrichment; aim for windows with garden or street activity.",
        ],
        "suitability": [
            "<strong>Best for indoor-only cats:</strong> Window perches provide vital environmental enrichment and visual stimulation that indoor cats need.",
            "<strong>Best for elderly cats:</strong> Low-entry perches with padded surfaces that offer comfortable sunning spots without requiring climbing.",
            "<strong>Best for bird-watching cats:</strong> Perches positioned at windows overlooking gardens or bird feeders maximise engagement.",
            "<strong>Best for small living spaces:</strong> Suction-mounted perches use zero floor space and can be repositioned seasonally.",
            "<strong>Best on a budget:</strong> A basic suction-cup shelf with a removable fleece pad provides the core benefit at minimal cost.",
        ],
        "what_to_expect": "Most cats take a few days to a week to start using a new window perch confidently. Place treats or catnip on the perch initially to encourage exploration. Once established, window perches often become a cat's favourite resting spot.",
    },
    4216: {
        "cluster": "Cat Supplies",
        "common_mistakes": [
            "Not checking radiator compatibility — hook-on beds require specific radiator panel types and may not fit modern convector designs.",
            "Choosing a bed that hangs too low — your cat should be able to get in and out comfortably without jumping from a difficult height.",
            "Using the bed when the radiator is off for extended periods — the appeal is warmth, so the bed may be ignored in summer months.",
            "Forgetting to wash the bed cover regularly — radiator heat accelerates odour development in unwashed fabric.",
        ],
        "suitability": [
            "<strong>Best for heat-seeking cats:</strong> Cats that gravitate towards warm spots will use a radiator bed daily during colder months.",
            "<strong>Best for elderly or arthritic cats:</strong> Gentle warmth from the radiator soothes stiff joints — similar to a low-level heated pad.",
            "<strong>Best for small homes:</strong> Radiator beds use vertical space, keeping floor area clear for other furniture.",
            "<strong>Best for multi-cat households:</strong> Placing one on each radiator gives every cat access to a warm perch without competition.",
            "<strong>Best on a budget:</strong> Basic fleece-lined radiator hammocks provide effective warmth at a very low price point.",
        ],
        "what_to_expect": "Some cats take to radiator beds immediately, while others need encouragement with treats or familiar bedding. The bed is most appealing during the heating season and may see less use in warmer months.",
    },
    4209: {
        "cluster": "Cat Supplies",
        "common_mistakes": [
            "Leaving a heated bed switched on continuously when unattended — always use models with thermostatic controls or automatic shut-off features.",
            "Choosing a bed without chew-resistant cabling — exposed wires are a serious hazard, especially in multi-pet homes.",
            "Setting the temperature too high — cats regulate their own position relative to heat, so a gentle warmth is safer than intense heat.",
            "Using a heated bed for a healthy young cat that does not need supplemental warmth — it is most beneficial for elderly, arthritic, or thin-coated cats.",
        ],
        "suitability": [
            "<strong>Best for elderly cats with arthritis:</strong> Low-level warmth eases joint stiffness and encourages restful sleep during cold months.",
            "<strong>Best for thin-coated or hairless breeds:</strong> Sphynx and other low-coat breeds benefit significantly from supplemental warmth.",
            "<strong>Best for post-surgery recovery:</strong> Gentle warmth supports healing and comfort during convalescence, with veterinary approval.",
            "<strong>Best for draughty or cold homes:</strong> Heated beds compensate for lower ambient temperatures without raising overall heating costs.",
            "<strong>Best on a budget:</strong> Self-warming beds using reflective thermal linings provide warmth without any electricity costs at all.",
        ],
        "what_to_expect": "Heated beds are most effective during the colder months from October through to March. Most cats discover and adopt a heated bed within a few days. Look for models with removable, washable covers for easy maintenance.",
        "pros_cons": {
            "advantages": [
                "Provides targeted warmth that particularly benefits elderly, arthritic, or thin-coated cats.",
                "Thermostatically controlled models maintain a safe, consistent temperature without manual adjustment.",
                "Can reduce the need for higher central heating settings, offering some energy savings.",
            ],
            "considerations": [
                "Electric models require a power source near the bed location and ongoing (small) electricity costs.",
                "Cable safety is a concern in households with chewing pets — always choose chew-resistant cord designs.",
                "Healthy adult cats with normal coats generally do not require a heated bed.",
            ],
        },
    },
    4202: {
        "cluster": "Cat Supplies",
        "common_mistakes": [
            "Choosing a bed based on appearance rather than your cat's sleeping style — observe whether they curl up, stretch out, or prefer enclosed spaces first.",
            "Placing the bed in a high-traffic area — cats need a quiet, secure retreat where they feel safe sleeping.",
            "Buying a bed that is too large — many cats prefer a snug fit that mimics the security of a nest or den.",
            "Not washing the bed cover regularly — unwashed bedding accumulates allergens and odour that may deter your cat from using it.",
        ],
        "suitability": [
            "<strong>Best for cats that curl up:</strong> Donut-style or bolster beds that provide a cosy, enclosed nest feeling.",
            "<strong>Best for cats that stretch out:</strong> Flat mat-style or open pillow beds that allow full extension.",
            "<strong>Best for elderly cats:</strong> Beds with low entry points and supportive padding that are easy to access.",
            "<strong>Best for multi-cat households:</strong> Multiple beds in different locations give each cat their own territory and reduce conflict.",
            "<strong>Best on a budget:</strong> A simple fleece-lined bed in a quiet location will be used more than an expensive bed placed in the wrong spot.",
        ],
        "what_to_expect": "Cats can be particular about bed choices — some take to a new bed immediately, while others may ignore it for weeks. Placing familiar-scented items or catnip in the bed can speed up acceptance. Location matters as much as the bed itself.",
        "pros_cons": {
            "advantages": [
                "A dedicated bed provides warmth, security, and a defined rest space that supports healthy sleep patterns.",
                "Machine-washable covers make hygiene maintenance straightforward.",
                "Beds placed strategically can redirect cats away from furniture or human beds.",
            ],
            "considerations": [
                "Cats are notoriously selective — the 'best' bed is the one your individual cat actually uses.",
                "Bed preferences may change seasonally (cooler enclosed beds in summer, warmer options in winter).",
                "Kittens and young cats may chew or scratch beds, so durability matters in the early months.",
            ],
        },
    },
    696: {
        "cluster": "Cat Supplies",
        "common_mistakes": [
            "Buying everything at once before understanding your cat's preferences — start with essentials and add items based on what your cat actually uses.",
            "Choosing the cheapest option for items that affect welfare — litter trays, food bowls, and scratching posts are worth investing in properly.",
            "Neglecting vertical space — cats need climbing opportunities and elevated resting spots, not just floor-level accessories.",
            "Placing all supplies in one location — food, water, litter, and resting areas should be separated throughout the home.",
        ],
        "suitability": [
            "<strong>Best starting point for new cat owners:</strong> Focus on litter tray, quality food, scratching post, and a safe resting space before adding extras.",
            "<strong>Best for indoor-only cats:</strong> Prioritise enrichment items (scratching posts, window perches, interactive toys) to compensate for limited outdoor access.",
            "<strong>Best for kittens:</strong> Age-appropriate items with safety as the priority — avoid small parts, dangling cords, and toxic materials.",
            "<strong>Best for multi-cat households:</strong> Duplicate essentials (trays, bowls, beds) to prevent resource competition and territorial stress.",
            "<strong>Best on a budget:</strong> Essential supplies first (tray, food, scratcher), then add enrichment items gradually as budget allows.",
        ],
    },

    # ── Cat Toys ──────────────────────────────────────────────────────────
    5458: {
        "cluster": "Cat Toys",
        "common_mistakes": [
            "Punishing scratching behaviour — scratching is a natural, essential feline behaviour and punishment only causes stress without solving the problem.",
            "Not providing enough scratching surfaces — one post for three cats is rarely sufficient; offer multiple surfaces in different orientations.",
            "Placing scratching posts in hidden corners — cats scratch in prominent locations to mark territory, so posts should be in visible, social areas.",
            "Ignoring surface preference — some cats prefer sisal rope, others prefer cardboard or carpet; experiment to discover what your cat likes.",
        ],
        "suitability": [
            "<strong>Best for understanding new cats:</strong> Observing scratching preferences helps you choose the right surface type and orientation from the start.",
            "<strong>Best for furniture-scratching cats:</strong> Identifying the preferred surface and angle, then placing an appropriate scratcher directly alongside the targeted furniture.",
            "<strong>Best for multi-cat households:</strong> Understanding scratching as territorial marking helps explain why each cat needs their own scratching spots.",
            "<strong>Best for indoor-only cats:</strong> Scratching is one of several essential outlets for natural behaviour that indoor cats lack from outdoor access.",
        ],
    },
    5414: {
        "cluster": "Cat Toys",
        "common_mistakes": [
            "Assuming all cats enjoy the same types of toys — play preferences vary significantly between individual cats and even change with age.",
            "Leaving string-based toys out unsupervised — cats can swallow string and ribbon, causing dangerous intestinal blockages requiring surgery.",
            "Relying solely on battery-operated toys for enrichment — interactive human-led play is essential for bonding and cannot be fully replaced by automated options.",
            "Not rotating toys — cats habituate to the same toys quickly; storing and reintroducing them in rotation maintains novelty.",
        ],
        "suitability": [
            "<strong>Best reference for new cat owners:</strong> Understanding toy categories helps you build a balanced collection covering different play needs.",
            "<strong>Best for matching toys to play style:</strong> Identifying whether your cat prefers chase, pounce, batting, or puzzle play directs better purchasing decisions.",
            "<strong>Best for understanding toy safety:</strong> Knowing which materials and designs pose risks helps you avoid hazardous products.",
            "<strong>Best for building a toy rotation system:</strong> Understanding the range of available types makes it easier to create variety without overspending.",
        ],
    },
    5296: {
        "cluster": "Cat Toys",
        "common_mistakes": [
            "Buying too many toys at once — indoor cats benefit more from a small, regularly rotated collection than a large static pile.",
            "Choosing toys that are too large for your cat's mouth and paws — oversized toys frustrate rather than engage.",
            "Leaving laser pointer sessions without a physical 'catch' — always end with a tangible toy or treat to prevent frustration.",
            "Ignoring quiet enrichment options — puzzle feeders and scent-based enrichment complement active play and suit calmer moments.",
        ],
        "suitability": [
            "<strong>Best for solo indoor cats:</strong> A mix of interactive (human-led), self-play, and automated toys to cover alone time and bonding.",
            "<strong>Best for overweight indoor cats:</strong> Active toys that encourage movement — wand toys and ball tracks that require physical effort.",
            "<strong>Best for anxious indoor cats:</strong> Gentle, predictable toys like slow puzzle feeders rather than erratic electronic options.",
            "<strong>Best for senior indoor cats:</strong> Low-intensity puzzle feeders and scent enrichment that engage the mind without demanding agility.",
            "<strong>Best on a budget:</strong> Crinkle balls, cardboard boxes, and one quality wand toy provide more enrichment than an expensive collection.",
        ],
        "what_to_expect": "Indoor cats typically need two interactive play sessions daily of 10 to 15 minutes each. You may need to test several toy types before finding what engages your individual cat. Rotating toys weekly maintains interest without constant new purchases.",
    },
    5033: {
        "cluster": "Cat Toys",
        "common_mistakes": [
            "Projecting human preferences onto your cat — the toy you find appealing may not match your cat's natural play instincts at all.",
            "Giving up too quickly on a new toy — some cats need multiple exposures before engaging, especially with puzzle-type toys.",
            "Assuming a cat that does not play is lazy — low play engagement often signals the wrong toy type rather than a disinterested cat.",
            "Overlooking scent-based play — many cats respond strongly to catnip, silver vine, or valerian even when they show little interest in physical toys.",
        ],
        "suitability": [
            "<strong>Best for hunter-type cats:</strong> Wand toys with feather or fur attachments that mimic prey movement patterns.",
            "<strong>Best for curious, problem-solving cats:</strong> Puzzle feeders and multi-step treat toys that reward investigation.",
            "<strong>Best for shy or cautious cats:</strong> Gentle, slow-moving toys and individual play sessions in a quiet room.",
            "<strong>Best for high-energy, athletic cats:</strong> Ball tracks, fetch toys, and climbing-based play that burns physical energy.",
            "<strong>Best for sedentary cats:</strong> Catnip or silver vine toys that spark interest without requiring the cat to initiate movement.",
        ],
    },
    5036: {
        "cluster": "Cat Toys",
        "common_mistakes": [
            "Interpreting all rough play as aggression — many cats have vigorous play styles that look fierce but are completely normal hunting rehearsal.",
            "Allowing kittens to play-bite hands — habits established in kittenhood persist into adulthood and become painful with adult teeth.",
            "Ignoring changes in play behaviour — a sudden loss of interest in play can indicate pain, illness, or environmental stress.",
            "Forcing play when a cat signals disinterest — tail flicking, ears back, and walking away are clear signals to stop.",
        ],
        "suitability": [
            "<strong>Best for understanding your cat:</strong> Recognising play styles helps you choose enrichment that matches natural instincts rather than fighting them.",
            "<strong>Best for multi-cat households:</strong> Understanding different play styles helps prevent mismatched play from escalating into genuine conflict.",
            "<strong>Best for kitten owners:</strong> Establishing appropriate play patterns early prevents problematic behaviours from becoming ingrained.",
            "<strong>Best for adopters of adult cats:</strong> Observing play style gives insight into personality and helps build trust through appropriate engagement.",
        ],
    },
    5032: {
        "cluster": "Cat Toys",
        "common_mistakes": [
            "Assuming catnip works for all cats — around 30 to 40 percent of cats have no genetic response to catnip at all.",
            "Leaving interactive toys out all the time — they lose novelty value and some (like wand toys) pose unsupervised safety risks.",
            "Spending heavily on electronic toys before testing simpler options — many cats prefer a crinkle ball over an expensive automated device.",
            "Not adjusting toy selection as your cat ages — kittens, adults, and seniors have different play needs and energy levels.",
        ],
        "suitability": [
            "<strong>Best quick reference for new owners:</strong> Covers the most common toy-related questions in one accessible resource.",
            "<strong>Best for troubleshooting toy disinterest:</strong> Practical answers on why cats ignore certain toys and how to re-engage them.",
            "<strong>Best for safety-conscious owners:</strong> Answers common safety questions about toy materials, supervision, and replacement timing.",
            "<strong>Best for budget-conscious owners:</strong> Practical guidance on which toys offer the best value and which to skip.",
        ],
    },
    5035: {
        "cluster": "Cat Toys",
        "common_mistakes": [
            "Relying solely on toys for enrichment — cats also need vertical space, window views, scent stimulation, and social interaction.",
            "Overlooking food-based enrichment — scatter feeding and puzzle feeders engage natural foraging instincts that toys alone do not address.",
            "Not providing outdoor-like experiences for indoor cats — catio spaces, safe garden access, or window bird feeders add vital variety.",
            "Underestimating the enrichment value of cardboard boxes and paper bags — these free items provide exploration, hiding, and play opportunities.",
        ],
        "suitability": [
            "<strong>Best for indoor-only cats:</strong> Beyond-toy enrichment is essential for replacing the diverse stimulation of outdoor access.",
            "<strong>Best for bored or destructive cats:</strong> Environmental enrichment often resolves behaviour problems that toys alone cannot.",
            "<strong>Best for busy owners:</strong> Many enrichment strategies (scatter feeding, rotating shelf access) require minimal ongoing effort once set up.",
            "<strong>Best for multi-cat households:</strong> Environmental enrichment reduces territorial tension by creating more resources and activity zones.",
        ],
    },
    5034: {
        "cluster": "Cat Toys",
        "common_mistakes": [
            "Rotating too many toys at once — keep only 3 to 5 toys available at a time and swap the rest in weekly.",
            "Washing toys too aggressively before rotation — some toys carry your cat's scent, which maintains familiarity and interest.",
            "Only rotating physical toys while ignoring puzzle feeders and scent enrichment — variety across types matters most.",
            "Forgetting to inspect toys during rotation — check for wear, loose parts, and damage before reintroducing stored toys.",
        ],
        "suitability": [
            "<strong>Best for indoor cats with limited stimulation:</strong> Rotation is the single most effective way to maintain toy novelty without constant purchasing.",
            "<strong>Best for owners on a budget:</strong> A rotation system means fewer total toys needed — 10 to 12 toys rotated weekly feels like a much larger collection.",
            "<strong>Best for cats that lose interest quickly:</strong> Systematic rotation specifically targets the habituation that causes cats to ignore familiar toys.",
            "<strong>Best for multi-cat households:</strong> Rotating toys across cats and locations keeps enrichment fresh for every animal.",
        ],
        "routine": {
            "title": "Quick Toy Rotation Checklist",
            "items": [
                "Weekly: Swap 3 to 5 available toys for 3 to 5 stored toys — keep the rotation on a consistent schedule.",
                "During rotation: Inspect each toy for wear, fraying, loose parts, or damage before putting it back in circulation.",
                "Monthly: Introduce one completely new toy to the rotation pool and retire any that are worn beyond safe use.",
                "Seasonally: Adjust the toy mix — more active toys in spring and summer, more puzzle and comfort toys in winter.",
                "Ongoing: Store rotated toys in a sealed container to preserve scent freshness and maintain the 'new toy' effect.",
            ],
        },
    },
    4415: {
        "cluster": "Cat Toys",
        "common_mistakes": [
            "Leaving string, ribbon, or elastic toys unsupervised — linear foreign bodies are one of the most common and dangerous feline surgical emergencies.",
            "Ignoring toy size relative to your cat — toys that are too small can be swallowed, while oversized toys may cause frustration.",
            "Assuming 'natural' materials are automatically safe — wooden toys can splinter and some plant-based materials may be toxic.",
            "Keeping broken or heavily worn toys in circulation — damaged toys can expose sharp edges, small parts, or stuffing that poses ingestion risks.",
        ],
        "suitability": [
            "<strong>Best safety reference for new cat owners:</strong> Understanding toy hazards before purchasing helps prevent avoidable accidents.",
            "<strong>Best for households with kittens:</strong> Kittens are more likely to chew and swallow toy parts, making safety awareness especially critical.",
            "<strong>Best for multi-pet homes:</strong> Knowing which toys require supervision helps manage play in households where different pets share space.",
            "<strong>Best for choosing gifts:</strong> Safety knowledge helps you select appropriate toys when buying for someone else's cat.",
        ],
    },
    4406: {
        "cluster": "Cat Toys",
        "common_mistakes": [
            "Relying entirely on automated toys during the day — no electronic toy fully replaces the engagement of interactive human-led play.",
            "Overstimulating your cat with too many electronic toys running simultaneously — this can cause anxiety rather than enrichment.",
            "Not providing a 'wind-down' period after active play — end sessions with a treat or gentle activity to simulate the hunt-catch-eat cycle.",
            "Assuming an indoor cat does not need daily play — indoor cats specifically need structured play to compensate for the lack of outdoor hunting activity.",
        ],
        "suitability": [
            "<strong>Best for solo indoor cats:</strong> A combination of automated and interactive toys covers both independent and social play needs.",
            "<strong>Best for overweight indoor cats:</strong> Active play toys that encourage movement and calorie burn through chase and pounce activities.",
            "<strong>Best for anxious indoor cats:</strong> Predictable, gentle toys like slow puzzle feeders rather than erratic electronic options that may startle.",
            "<strong>Best for senior indoor cats:</strong> Low-intensity puzzle feeders and scent enrichment that engage the mind without demanding physical agility.",
            "<strong>Best on a budget:</strong> Rotating a small toy collection weekly creates novelty without constant purchasing — cats prefer variety over volume.",
        ],
    },
    4410: {
        "cluster": "Cat Toys",
        "common_mistakes": [
            "Treating enrichment as optional — for indoor cats especially, environmental enrichment is a welfare necessity, not a luxury.",
            "Focusing only on physical play while neglecting mental stimulation — puzzle feeders and scent enrichment are equally important.",
            "Not tailoring enrichment to individual cat personality — a shy cat needs different approaches than a bold, confident one.",
            "Making all enrichment changes at once — introduce new elements gradually to avoid overwhelming a sensitive cat.",
        ],
        "suitability": [
            "<strong>Best for indoor-only cats:</strong> Non-toy enrichment compensates for the diverse stimulation that outdoor access naturally provides.",
            "<strong>Best for cats showing boredom-related behaviours:</strong> Overgrooming, overeating, and destructive behaviour often respond to increased enrichment.",
            "<strong>Best for limited living spaces:</strong> Vertical enrichment (shelves, cat walks) uses wall space without requiring additional floor area.",
            "<strong>Best for multi-cat homes:</strong> Environmental enrichment reduces resource competition and creates multiple activity zones.",
        ],
    },
    4409: {
        "cluster": "Cat Toys",
        "common_mistakes": [
            "Giving kittens toys designed for adult cats — small parts, heavy toys, and complex puzzles are inappropriate for developing cats.",
            "Stopping interactive play as a cat reaches adulthood — adult cats still need daily play for physical and mental health.",
            "Assuming senior cats do not want to play — they do, but they need gentler, shorter sessions with age-appropriate toys.",
            "Using the same toys from kittenhood through to senior years without adapting — play needs change significantly with age.",
        ],
        "suitability": [
            "<strong>Best for kitten owners:</strong> Understanding age-appropriate toy selection protects growing cats from hazards and supports healthy development.",
            "<strong>Best for adopters of cats with unknown history:</strong> Matching toys to apparent age and energy level helps build engagement from the start.",
            "<strong>Best for multi-age households:</strong> Knowing which toys suit different life stages prevents younger cats from dominating play resources.",
            "<strong>Best for senior cat owners:</strong> Adapted play maintains cognitive function and physical mobility in ageing cats.",
        ],
    },
    4408: {
        "cluster": "Cat Toys",
        "common_mistakes": [
            "Keeping toys until they completely fall apart — by that point they have likely been unsafe for some time.",
            "Only checking toys visually — squeeze, pull, and flex toys to test for hidden weakness that visual inspection misses.",
            "Not tracking when toys were purchased — older toys lose structural integrity even if they appear visually intact.",
            "Assuming expensive toys last longer — build quality varies regardless of price, and all toys eventually wear out with use.",
        ],
        "suitability": [
            "<strong>Best for safety-conscious owners:</strong> Understanding replacement timing prevents avoidable ingestion and injury risks.",
            "<strong>Best for multi-cat households:</strong> More cats means faster toy wear — replacement schedules need adjusting accordingly.",
            "<strong>Best for budget planning:</strong> Knowing typical toy lifespans helps predict and budget for ongoing replacement costs.",
            "<strong>Best for cats that are aggressive chewers:</strong> Heavy chewers need more frequent replacement checks than gentle players.",
        ],
        "routine": {
            "title": "Quick Toy Inspection Checklist",
            "items": [
                "Weekly: Quick visual and tactile check of all toys currently in rotation — squeeze, pull, and flex each one.",
                "Monthly: Thorough inspection of stored toys before rotation — check seams, attachments, and surfaces for wear.",
                "After heavy play sessions: Check wand toy attachments, string integrity, and stuffed toy seams for new damage.",
                "Every 3 months: Replace catnip toys (potency fades), check battery compartments on electronic toys, and assess overall collection condition.",
                "Ongoing: Remove any toy immediately if stuffing is exposed, parts are loose, or material is fraying.",
            ],
        },
    },
    4407: {
        "cluster": "Cat Toys",
        "common_mistakes": [
            "Using toxic adhesives, paints, or dyes — only use materials known to be safe if ingested, since cats will chew.",
            "Making toys with small detachable parts — buttons, beads, and bells that can come loose are choking and ingestion hazards.",
            "Using yarn or string without supervision — homemade string toys should only be used during supervised play and stored away afterwards.",
            "Creating toys that are too fragile — a DIY toy that breaks apart quickly creates more hazard than enrichment.",
        ],
        "suitability": [
            "<strong>Best for budget-conscious owners:</strong> Household items like cardboard boxes, paper bags, and old socks make effective free toys.",
            "<strong>Best for eco-conscious owners:</strong> Repurposing household items reduces waste and avoids plastic-heavy commercial toy packaging.",
            "<strong>Best for creative play sessions:</strong> Homemade toys can be customised to your specific cat's preferences and play style.",
            "<strong>Best for testing preferences:</strong> Try DIY versions before investing in commercial equivalents to see what your cat actually enjoys.",
        ],
    },
    4293: {
        "cluster": "Cat Toys",
        "common_mistakes": [
            "Choosing a tree that is too small for your cat — the top platform should comfortably accommodate your cat's full body length.",
            "Buying a lightweight tree for a large cat — heavy cats need a tree with a wide, weighted base to prevent toppling.",
            "Placing the tree in an unused corner — cats use trees most when positioned near windows or in social areas of the home.",
            "Assuming all cats will use a tree immediately — some need gradual encouragement with treats, catnip, and patience.",
        ],
        "suitability": [
            "<strong>Best for multi-cat households:</strong> Trees with multiple platforms at different heights give each cat their own territory and reduce conflict.",
            "<strong>Best for indoor-only cats:</strong> Cat trees provide essential climbing, scratching, and elevated resting that indoor cats cannot access outdoors.",
            "<strong>Best for large breeds:</strong> Sturdy, heavy-base trees rated for higher weight limits with extra-wide platforms.",
            "<strong>Best for small homes:</strong> Slim, tall trees that use vertical space efficiently without a large floor footprint.",
            "<strong>Best on a budget:</strong> A simple two-platform tree with sisal wrapping covers the core needs of climbing, scratching, and elevated resting.",
        ],
        "what_to_expect": "Most cats explore a new tree within the first few days, though some take a week or more. Placing treats, catnip, or favourite toys on the platforms accelerates adoption. Trees placed near windows with outside views see the most consistent use.",
        "pros_cons": {
            "advantages": [
                "Combines scratching, climbing, resting, and play in a single piece of cat furniture.",
                "Provides essential vertical territory that reduces stress in multi-cat households.",
                "Keeps cats physically active and maintains healthy muscle tone through climbing.",
            ],
            "considerations": [
                "Quality trees with good stability are a significant upfront investment.",
                "Sisal wrapping and platforms wear over time and may need replacement or re-wrapping.",
                "Large trees take up considerable floor space and are difficult to move once assembled.",
            ],
        },
    },
    4195: {
        "cluster": "Cat Toys",
        "common_mistakes": [
            "Expecting toys alone to satisfy an indoor cat's needs — environmental enrichment, vertical space, and window views are equally important.",
            "Choosing only passive toys — indoor cats need daily interactive (human-led) play sessions, not just solo-play options.",
            "Providing too many toys at once instead of rotating them — this leads to rapid habituation and apparent disinterest.",
            "Not matching toy intensity to your cat's current mood — offer active toys during alert periods and gentle options during calmer times.",
        ],
        "suitability": [
            "<strong>Best for sole indoor cats:</strong> A balanced mix of interactive, self-play, and puzzle toys to cover social and solo needs.",
            "<strong>Best for cats prone to weight gain:</strong> Active toys that encourage running, jumping, and pouncing to maintain healthy body condition.",
            "<strong>Best for cats left alone during the day:</strong> Timer-activated or motion-triggered toys that provide stimulation during owner absence.",
            "<strong>Best for enrichment-focused owners:</strong> Toys combined with food puzzles and scent enrichment create a comprehensive indoor enrichment programme.",
            "<strong>Best on a budget:</strong> A quality wand toy, a few crinkle balls, and a simple puzzle feeder cover the essential indoor play categories.",
        ],
        "what_to_expect": "Indoor cats typically need two structured play sessions daily, ideally 10 to 15 minutes each, in addition to access to self-play toys. Expect to experiment with different toy types before finding what engages your specific cat. Most indoor cats show noticeable behaviour improvements within a few weeks of establishing a consistent play routine.",
    },

    # ── Dog Harnesses ─────────────────────────────────────────────────────
    5418: {
        "cluster": "Dog Harnesses",
        "common_mistakes": [
            "Choosing a harness type based on appearance rather than function — different activities and dog sizes need different harness designs.",
            "Assuming all back-clip harnesses are the same — the attachment point position, padding, and strap width vary significantly and affect comfort.",
            "Not considering your dog's body shape — barrel-chested breeds, sighthounds, and toy breeds all need different harness proportions.",
            "Ignoring the adjustment points — harnesses with more adjustment points provide better customisation for unusual body shapes.",
        ],
        "suitability": [
            "<strong>Best starting reference:</strong> Understanding harness types before purchasing prevents expensive trial-and-error with unsuitable styles.",
            "<strong>Best for matching harness to activity:</strong> Walking, running, car travel, and training each have optimal harness designs.",
            "<strong>Best for understanding trade-offs:</strong> Every harness type has specific strengths and limitations that suit different situations.",
            "<strong>Best for breed-specific guidance:</strong> Certain body types work better with specific harness designs, which this guide helps identify.",
        ],
    },
    4414: {
        "cluster": "Dog Harnesses",
        "common_mistakes": [
            "Defaulting to a collar for all dogs — flat-faced breeds, toy breeds, and dogs with tracheal issues should always use harnesses instead.",
            "Using a collar as the sole restraint for a dog that pulls — sustained collar pressure damages the neck and can worsen pulling behaviour.",
            "Assuming harnesses encourage pulling — properly fitted harnesses, especially front-clip designs, actually reduce pulling in most dogs.",
            "Forgetting that collars and harnesses serve different purposes — collars for ID tags and casual control, harnesses for walking and training.",
        ],
        "suitability": [
            "<strong>Best for dogs with neck or tracheal concerns:</strong> Harnesses distribute force across the chest, eliminating dangerous pressure on the neck.",
            "<strong>Best for small and toy breeds:</strong> Harnesses protect fragile tracheas that are vulnerable to collar pressure.",
            "<strong>Best for dogs that pull:</strong> Front-clip harnesses redirect pulling energy without the discomfort or risk of a collar.",
            "<strong>Best for calm, trained dogs:</strong> A well-fitted collar may be sufficient for dogs that walk reliably on a loose lead.",
        ],
        "pros_cons": {
            "advantages": [
                "Harnesses eliminate neck pressure, protecting the trachea and cervical spine during walks.",
                "Front-clip designs provide immediate pulling reduction without pain or discomfort.",
                "Many dogs find harnesses more comfortable than collars, especially during extended walks.",
            ],
            "considerations": [
                "Harnesses take longer to put on and adjust than simply clipping a lead to a collar.",
                "Poorly fitted harnesses can cause chafing, restrict movement, or allow escape.",
                "Some dogs dislike the sensation of a harness initially and need gradual, positive introduction.",
            ],
        },
    },
    4413: {
        "cluster": "Dog Harnesses",
        "common_mistakes": [
            "Measuring only the chest and ignoring the neck and girth — harnesses need multiple measurements for a proper fit.",
            "Measuring too tightly — allow two fingers' width between the tape measure and your dog's body to ensure comfortable movement.",
            "Using human clothing sizes as a reference — dog harness sizing varies hugely between brands and cannot be assumed from weight alone.",
            "Not re-measuring after weight changes — seasonal weight fluctuation, growth, or diet changes can alter harness fit significantly.",
        ],
        "suitability": [
            "<strong>Best for first-time harness buyers:</strong> Accurate measurement prevents the most common reason for harness returns — wrong size.",
            "<strong>Best for growing puppies:</strong> Regular re-measurement ensures the harness keeps pace with rapid growth.",
            "<strong>Best for breeds with unusual proportions:</strong> Dachshunds, Bulldogs, and Greyhounds all need careful measurement due to non-standard body shapes.",
            "<strong>Best for online purchasers:</strong> Accurate home measurement is essential when you cannot try a harness on in person before buying.",
        ],
    },
    4412: {
        "cluster": "Dog Harnesses",
        "common_mistakes": [
            "Expecting a no-pull harness to train your dog automatically — the harness manages pulling but loose-lead training must continue alongside it.",
            "Using a back-clip harness as a no-pull solution — only front-clip or dual-clip designs provide the pulling redirection effect.",
            "Not adjusting the harness properly after fitting — a front clip that sits off-centre causes uneven gait and reduces effectiveness.",
            "Relying on the harness indefinitely without training — the goal is to phase out the no-pull harness as training progresses.",
        ],
        "suitability": [
            "<strong>Best for moderate to strong pullers:</strong> Front-clip harnesses redirect pulling energy toward the handler without causing discomfort.",
            "<strong>Best for training-focused owners:</strong> No-pull harnesses complement reward-based training programmes for faster loose-lead progress.",
            "<strong>Best for reactive dogs:</strong> Dual-clip harnesses offer maximum control during encounters with triggers.",
            "<strong>Best for dog walkers managing multiple dogs:</strong> Immediate pulling reduction makes multi-dog walks more manageable.",
        ],
        "what_to_expect": "Most dogs show noticeable pulling reduction within the first few walks with a properly fitted front-clip harness. However, this is management, not training — pair the harness with consistent reward-based walking practice for lasting improvement.",
    },
    4411: {
        "cluster": "Dog Harnesses",
        "common_mistakes": [
            "Buying a harness without measuring your dog first — guessing size is the most common cause of ill-fitting harnesses.",
            "Not checking the harness fit regularly — body shape changes with weight, age, and coat growth.",
            "Ignoring signs of discomfort — rubbing, reluctance to walk, or changed gait may indicate a harness that does not fit correctly.",
            "Choosing the cheapest option regardless of build quality — poorly constructed harnesses can break under strain, creating a safety risk.",
        ],
        "suitability": [
            "<strong>Best comprehensive reference:</strong> Covers all major harness types, fitting principles, and safety considerations in one guide.",
            "<strong>Best for first-time dog owners:</strong> Foundational knowledge that prevents common and potentially costly harness mistakes.",
            "<strong>Best for owners of multiple breeds:</strong> Understanding that different body types need different harness styles and fitting approaches.",
            "<strong>Best for safety-conscious owners:</strong> Detailed guidance on construction quality, stitching, and hardware reliability.",
        ],
        "what_to_expect": "A well-fitted harness should feel snug but allow natural movement — you should be able to slide two flat fingers under any strap. Most dogs need a brief adjustment period when transitioning from a collar to a harness.",
    },
    4279: {
        "cluster": "Dog Harnesses",
        "common_mistakes": [
            "Using a dog harness design on a cat — cats have different body proportions and escape instincts that require specifically designed cat harnesses.",
            "Skipping the indoor acclimatisation period — cats need days or even weeks of wearing the harness indoors before attempting outdoor walks.",
            "Taking a harnessed cat to busy or noisy areas — most cats prefer quiet gardens or enclosed spaces, not pavements or parks.",
            "Pulling on the lead when the cat stops — cats do not walk like dogs; they explore at their own pace, and pulling causes panic.",
        ],
        "suitability": [
            "<strong>Best for indoor cats needing outdoor access:</strong> Harness walking provides safe, controlled outdoor enrichment for indoor-only cats.",
            "<strong>Best for confident, curious cats:</strong> Cats that show interest in doors and windows are typically the best candidates for harness training.",
            "<strong>Best for young cats:</strong> Kittens and young adults adapt to harness wearing more readily than older cats.",
            "<strong>Best for secure garden exploration:</strong> Even in enclosed gardens, a harness provides an extra safety layer against escape.",
            "<strong>Best on a budget:</strong> A basic figure-of-eight or H-style cat harness with an adjustable fit covers most needs effectively.",
        ],
        "what_to_expect": "Harness training a cat is a gradual process that typically takes two to four weeks. Most cats initially freeze, roll over, or refuse to walk when first wearing a harness — this is completely normal. Patience and very short, positive indoor sessions build confidence over time.",
    },
    4272: {
        "cluster": "Dog Harnesses",
        "common_mistakes": [
            "Relying on a collar tag as the sole form of identification — tags can fall off, become unreadable, or be removed; microchipping is legally required alongside tags.",
            "Choosing a tag that is too large or heavy for your cat's collar — oversized tags irritate the neck and can get caught on objects.",
            "Not including a phone number on the tag — a name alone provides no way for a finder to contact you.",
            "Forgetting to update tag information after moving house or changing phone number — outdated contact details defeat the purpose of the tag.",
        ],
        "suitability": [
            "<strong>Best for outdoor and indoor-outdoor cats:</strong> ID tags provide immediate visual identification if your cat is found by a neighbour or stranger.",
            "<strong>Best alongside microchipping:</strong> Tags offer instant contact information without needing a scanner, complementing the permanent chip.",
            "<strong>Best for multi-cat households:</strong> Tags help distinguish your cats to visitors, pet sitters, and veterinary staff.",
            "<strong>Best on a budget:</strong> Basic engraved metal tags are inexpensive, durable, and provide the essential identification function.",
        ],
    },
    4265: {
        "cluster": "Dog Harnesses",
        "common_mistakes": [
            "Expecting GPS tracking to work indoors — most GPS trackers rely on satellite signals that are weak or unavailable inside buildings.",
            "Choosing a heavy tracker for a small cat — the tracker should weigh no more than 3 to 5 percent of your cat's body weight.",
            "Not charging the tracker regularly — a dead tracker provides no protection, so build charging into a routine.",
            "Assuming GPS tracking replaces microchipping — trackers can fall off or run out of battery; a microchip is permanent and legally required.",
        ],
        "suitability": [
            "<strong>Best for outdoor cats in rural areas:</strong> GPS tracking helps locate cats that roam wide distances across fields and farmland.",
            "<strong>Best for anxious owners of outdoor cats:</strong> Real-time location data provides peace of mind about your cat's whereabouts.",
            "<strong>Best for cats that tend to wander far:</strong> Geofencing alerts notify you if your cat leaves a defined safe zone.",
            "<strong>Best for multi-cat households:</strong> Individual trackers help monitor each cat's territory and activity patterns.",
        ],
    },
    4258: {
        "cluster": "Dog Harnesses",
        "common_mistakes": [
            "Using a collar without a quick-release safety mechanism — cats can strangle if a standard collar catches on branches, fences, or furniture.",
            "Fitting the collar too tightly — you should be able to slide two fingers between the collar and your cat's neck.",
            "Assuming indoor cats do not need collars — even indoor cats can escape, and a collar with ID provides immediate identification.",
            "Not checking collar fit regularly — weight changes and coat growth affect how a collar sits over time.",
        ],
        "suitability": [
            "<strong>Best for outdoor and indoor-outdoor cats:</strong> A breakaway collar with an ID tag is the most basic and important safety accessory.",
            "<strong>Best for cats that wear collars comfortably:</strong> Not all cats tolerate collars, but those that do benefit from the identification and visibility.",
            "<strong>Best for night-time outdoor cats:</strong> Reflective or high-visibility collars improve visibility to drivers and pedestrians.",
            "<strong>Best on a budget:</strong> A basic reflective breakaway collar with an engraved ID tag provides complete identification at minimal cost.",
        ],
    },
    4139: {
        "cluster": "Dog Harnesses",
        "common_mistakes": [
            "Using a long training lead in enclosed or busy areas — long lines require open space to avoid tangling around people, objects, or other dogs.",
            "Letting the lead drag on the ground without supervision — a dragging lead can snag on objects and create a trip or strangulation hazard.",
            "Attaching a long line to a collar — always use a harness with long training leads to prevent neck injury if the dog runs to the end of the line.",
            "Using a retractable lead as a training tool — retractable leads teach dogs that pulling extends their range, undermining loose-lead training.",
        ],
        "suitability": [
            "<strong>Best for recall training:</strong> Long lines (5 to 10 metres) give controlled freedom while maintaining a safety connection during training.",
            "<strong>Best for strong pullers:</strong> Short traffic handles on padded leads provide close control in busy areas.",
            "<strong>Best for multi-dog walking:</strong> Coupler leads or dual-handle systems keep two dogs at comfortable distance without tangling.",
            "<strong>Best for small breeds:</strong> Lightweight, narrow leads that do not weigh down a small dog's collar or harness.",
            "<strong>Best on a budget:</strong> A sturdy nylon lead with a quality snap hook outperforms most premium alternatives — clip quality matters more than lead material.",
        ],
    },
    4049: {
        "cluster": "Dog Harnesses",
        "common_mistakes": [
            "Buying an adult-sized collar for a puppy to 'grow into' — an oversized collar is a slip-off and safety risk.",
            "Using a collar without an ID tag from day one — even puppies should wear identification as soon as they come home.",
            "Choosing a heavy collar for a small breed puppy — young puppies need lightweight, soft materials that they barely notice wearing.",
            "Not adjusting the collar as the puppy grows — puppies grow rapidly, and a collar that fit last week may be too tight this week.",
        ],
        "suitability": [
            "<strong>Best for tiny breed puppies:</strong> Ultra-lightweight, soft collars that are barely perceptible and reduce neck strain.",
            "<strong>Best for medium breed puppies:</strong> Adjustable nylon collars that accommodate several months of growth before replacement.",
            "<strong>Best for strong breed puppies:</strong> Puppy harnesses rather than collars, to protect developing necks during the pulling-heavy learning phase.",
            "<strong>Best for puppies starting lead training:</strong> A simple flat collar for ID combined with a lightweight harness for walking provides the safest dual setup.",
            "<strong>Best on a budget:</strong> A basic adjustable nylon collar with a clip-on ID tag covers the essentials until your puppy reaches adult size.",
        ],
    },
    4042: {
        "cluster": "Dog Harnesses",
        "common_mistakes": [
            "Using a retractable lead for daily walks — the inconsistent length teaches dogs that pulling gains more range and undermines training.",
            "Choosing a lead that is uncomfortable to hold — thin leads cut into hands when a dog pulls, especially nylon in wet weather.",
            "Attaching a lead to a collar on a pulling dog — the force is concentrated on the neck, risking tracheal and spinal damage.",
            "Not matching lead length to the walking environment — a long lead in a busy street creates tangling and safety hazards.",
        ],
        "suitability": [
            "<strong>Best for training recall:</strong> Long training leads of 5 to 10 metres give controlled freedom with a maintained safety connection.",
            "<strong>Best for strong pullers:</strong> Short, padded leads with traffic handles for close control in crowded areas.",
            "<strong>Best for multi-dog walking:</strong> Coupler leads that keep two dogs at comfortable distance without tangling.",
            "<strong>Best for small breeds:</strong> Lightweight, narrow leads that do not burden a small dog's collar or harness.",
            "<strong>Best on a budget:</strong> A sturdy nylon lead with a reliable snap hook delivers better value than most premium options.",
        ],
    },
    4034: {
        "cluster": "Dog Harnesses",
        "common_mistakes": [
            "Expecting the harness to do all the work — a no-pull harness manages pulling but does not train your dog; loose-lead training must continue alongside.",
            "Using a back-clip attachment and calling it a no-pull harness — only front-clip or dual-clip designs redirect pulling momentum.",
            "Not adjusting the front clip position correctly — a clip that sits off-centre causes uneven gait and reduces the no-pull effect.",
            "Leaving the no-pull harness on permanently — extended wear without adjustment breaks can cause rubbing and discomfort.",
        ],
        "suitability": [
            "<strong>Best for moderate to strong pullers:</strong> Front-clip harnesses redirect pulling energy toward the handler without causing pain.",
            "<strong>Best for training-focused owners:</strong> Paired with reward-based techniques, no-pull harnesses accelerate loose-lead progress.",
            "<strong>Best for reactive dogs:</strong> Dual-clip harnesses provide maximum control during encounters with triggers.",
            "<strong>Best for barrel-chested breeds:</strong> Adjustable harnesses with multiple strap points accommodate non-standard body shapes.",
            "<strong>Best on a budget:</strong> Mid-range front-clip harnesses deliver the same pulling reduction as premium brands in most cases.",
        ],
    },
    4027: {
        "cluster": "Dog Harnesses",
        "common_mistakes": [
            "Using a collar on a dog with a flat face or short neck — brachycephalic breeds are especially vulnerable to collar pressure on the airway.",
            "Not measuring your dog before purchasing — incorrect sizing is the leading cause of harness returns and discomfort.",
            "Choosing based on brand name alone — fit, function, and construction quality matter far more than brand reputation.",
            "Ignoring the two-finger test — if you cannot slide two flat fingers under every strap, the harness is too tight.",
        ],
        "suitability": [
            "<strong>Best for first-time dog owners:</strong> Foundational guidance on when collars and harnesses are appropriate and how to fit them.",
            "<strong>Best for dogs that pull:</strong> Front-clip harnesses provide immediate, humane pulling reduction during the training period.",
            "<strong>Best for small and toy breeds:</strong> Harnesses protect fragile tracheas that collars can easily damage.",
            "<strong>Best for active dogs:</strong> Padded adventure harnesses with back handles support hiking and outdoor activities.",
            "<strong>Best on a budget:</strong> A well-fitted basic Y-shaped harness offers better comfort and control than most expensive collars.",
        ],
    },

    # ── Dog Beds ──────────────────────────────────────────────────────────
    5522: {
        "cluster": "Dog Beds",
        "common_mistakes": [
            "Waiting until joint problems are advanced before taking action — early intervention with weight management and appropriate bedding is far more effective.",
            "Relying solely on supplements without addressing weight — carrying excess weight is the single biggest modifiable factor in joint disease progression.",
            "Assuming joint stiffness is just 'old age' — stiffness can indicate treatable conditions and always warrants veterinary assessment.",
            "Buying any bed labelled 'orthopaedic' without checking the foam specification — not all products marketed as orthopaedic contain genuine memory foam.",
        ],
        "suitability": [
            "<strong>Best for owners of large breed dogs:</strong> Large breeds are disproportionately affected by joint issues and benefit most from proactive orthopaedic care.",
            "<strong>Best for senior dog owners:</strong> Understanding joint health helps you recognise early signs and intervene before mobility deteriorates significantly.",
            "<strong>Best for post-surgery care:</strong> Practical guidance on recovery environments, including appropriate bedding and activity modification.",
            "<strong>Best for breed-predisposed dogs:</strong> Breeds prone to hip dysplasia, elbow dysplasia, and arthritis benefit from preventative measures from a young age.",
        ],
    },
    5510: {
        "cluster": "Dog Beds",
        "common_mistakes": [
            "Measuring your dog while they are curled up — always measure in a natural standing or stretched-out position for accurate bed sizing.",
            "Forgetting to add extra space to measurements — beds should be at least 15 to 20 centimetres longer than your dog's nose-to-tail length.",
            "Choosing a bed based on dog weight alone — dogs of the same weight can have very different body lengths and shapes.",
            "Not considering sleeping style — dogs that curl up need different dimensions than dogs that stretch flat.",
        ],
        "suitability": [
            "<strong>Best for first-time bed buyers:</strong> Accurate sizing prevents the most common reason for bed returns and dissatisfaction.",
            "<strong>Best for growing puppies:</strong> Understanding how to size up appropriately avoids buying beds that become too small within weeks.",
            "<strong>Best for multi-dog households:</strong> Each dog needs individually sized bedding based on their own measurements.",
            "<strong>Best for dogs with unusual proportions:</strong> Long-bodied breeds like Dachshunds and deep-chested breeds like Greyhounds need sizing beyond standard guidelines.",
        ],
    },
    5416: {
        "cluster": "Dog Beds",
        "common_mistakes": [
            "Assuming all memory foam beds are equal — foam density, thickness, and quality vary enormously and directly affect support and longevity.",
            "Choosing a bolster bed for a dog that stretches out — bolsters reduce the usable sleeping area and may feel restrictive.",
            "Buying the most expensive bed without considering your dog's actual preferences — some dogs prefer simple flat mats over elaborate designs.",
            "Not considering washability — beds without removable, machine-washable covers are difficult to keep hygienic over time.",
        ],
        "suitability": [
            "<strong>Best reference for new dog owners:</strong> Understanding bed types helps make an informed first purchase rather than an expensive guess.",
            "<strong>Best for matching bed to sleeping style:</strong> Curling, stretching, leaning, and burrowing dogs all need different bed shapes.",
            "<strong>Best for understanding material trade-offs:</strong> Foam types, fill materials, and fabric choices each have pros and cons worth understanding.",
            "<strong>Best for seasonal planning:</strong> Different bed types suit different seasons — cooling beds for summer, insulated beds for winter.",
        ],
    },
    4783: {
        "cluster": "Dog Beds",
        "common_mistakes": [
            "Measuring only the dog's back length — the full nose-to-tail measurement in a natural lying position is what matters for bed sizing.",
            "Ignoring the 'stretch factor' — dogs often extend fully during deep sleep and need more space than their curled-up position suggests.",
            "Buying a bed to match a crate without checking the dog's actual dimensions — the crate size may itself be incorrect.",
            "Assuming breed-based size guides are accurate for all individuals — mixed breeds and breed variations mean individual measurement is always best.",
        ],
        "suitability": [
            "<strong>Best for preventing sizing mistakes:</strong> A step-by-step measuring approach eliminates the guesswork that causes most bed returns.",
            "<strong>Best for fast-growing puppies:</strong> Knowing how to measure and when to size up saves money on premature replacements.",
            "<strong>Best for multi-dog households:</strong> Individual measurements for each dog ensure everyone has a properly fitted bed.",
            "<strong>Best for dogs that share beds:</strong> Measuring for shared use requires accounting for both dogs' combined stretched-out dimensions.",
        ],
    },

    # ── Indoor Cats ───────────────────────────────────────────────────────
    5519: {
        "cluster": "Indoor Cats",
        "common_mistakes": [
            "Assuming indoor cats need less attention than outdoor cats — the opposite is true, as indoor cats rely entirely on their owners for stimulation.",
            "Not providing enough vertical space — indoor cats need climbing opportunities, shelves, and elevated resting spots to feel secure.",
            "Keeping the same environment static for years — regularly rearranging enrichment, adding new scratch surfaces, and rotating toys prevents stagnation.",
            "Underestimating the importance of window access — visual stimulation from outside activity is one of the most valuable resources for indoor cats.",
            "Feeding from a bowl exclusively — scatter feeding and puzzle feeders engage natural foraging instincts that bowls completely bypass.",
        ],
        "suitability": [
            "<strong>Best for first-time indoor cat owners:</strong> Comprehensive guidance covering the specific welfare needs of cats without outdoor access.",
            "<strong>Best for owners transitioning a cat indoors:</strong> Practical steps for making the adjustment less stressful for a previously outdoor cat.",
            "<strong>Best for flat and apartment owners:</strong> Space-efficient enrichment strategies that work in smaller living environments.",
            "<strong>Best for multi-cat indoor households:</strong> Managing territory, resources, and social dynamics when cats share confined indoor space.",
            "<strong>Best for owners concerned about indoor cat welfare:</strong> Evidence-based reassurance that indoor cats can thrive with appropriate care and enrichment.",
        ],
        "what_to_expect": "Indoor cats can live long, healthy, and enriched lives with the right environment. However, they require more active management of their physical and mental stimulation than outdoor cats. Expect to invest time daily in interactive play, and to create an environment that offers variety, climbing, scratching, and visual interest.",
        "routine": {
            "title": "Quick Indoor Cat Welfare Checklist",
            "items": [
                "Daily: Two interactive play sessions of 10 to 15 minutes each, plus access to self-play and puzzle toys.",
                "Weekly: Rotate toys, refresh catnip on scratching surfaces, and check that all enrichment items are in good condition.",
                "Monthly: Reassess the home environment — add a new element like a cardboard box, new perch location, or different puzzle feeder.",
                "Seasonally: Adjust window access (screens for summer ventilation), refresh climbing furniture, and vary scent enrichment.",
                "Ongoing: Maintain the litter tray, food, water, and resting areas in separate locations and keep to a predictable daily routine.",
            ],
        },
        "pros_cons": {
            "advantages": [
                "Indoor cats are protected from traffic, predators, toxins, and infectious diseases that outdoor cats face daily.",
                "Owners have full oversight of diet, health, and behaviour, enabling earlier detection of problems.",
                "Indoor cats typically have longer lifespans than outdoor cats when their environmental needs are met.",
            ],
            "considerations": [
                "Indoor cats require more active enrichment management from their owners to prevent boredom and behavioural issues.",
                "Without outdoor access, indoor cats depend entirely on their home environment for exercise and stimulation.",
                "Some cats, particularly those accustomed to outdoor access, may find the transition to indoor living stressful.",
            ],
        },
    },

    # ── Educational ───────────────────────────────────────────────────────
    5523: {
        "cluster": "Educational",
        "common_mistakes": [
            "Buying training equipment without understanding its purpose — tools used incorrectly can confuse your dog or create negative associations.",
            "Using aversive training tools (choke chains, prong collars, shock devices) — these cause pain and fear, and are condemned by every major UK animal welfare organisation.",
            "Investing in expensive equipment before mastering basic reward-based techniques — treats, a clicker, and a standard lead cover most training needs.",
            "Assuming equipment fixes behaviour — tools assist training but never replace the consistent practice and patience that create lasting behaviour change.",
        ],
        "suitability": [
            "<strong>Best for new dog owners:</strong> Understanding training tools before purchasing prevents wasted spending and misuse.",
            "<strong>Best for owners choosing a training class:</strong> Knowing what equipment to expect helps you assess whether a class uses evidence-based methods.",
            "<strong>Best for ethical training decisions:</strong> Clear guidance on which tools are welfare-appropriate and which to avoid.",
            "<strong>Best for budget-conscious owners:</strong> Most effective training requires minimal equipment — understanding this prevents overspending.",
        ],
    },
    5512: {
        "cluster": "Educational",
        "common_mistakes": [
            "Interpreting tail wagging as always meaning happiness — tail position, speed, and direction convey very different emotional states.",
            "Punishing growling — growling is a vital warning signal; suppressing it removes the warning without addressing the underlying discomfort or fear.",
            "Assuming a dog that rolls over always wants a belly rub — this posture can also indicate submission, anxiety, or an attempt to de-escalate tension.",
            "Ignoring subtle stress signals (lip licking, yawning, whale eye) — these early warnings help prevent escalation to more serious reactions.",
        ],
        "suitability": [
            "<strong>Best for new dog owners:</strong> Foundational body language literacy that prevents common misunderstandings in daily interactions.",
            "<strong>Best for families with children:</strong> Teaching children to read dog signals is one of the most effective ways to prevent bites.",
            "<strong>Best for owners of rescued dogs:</strong> Understanding fear and stress signals helps build trust with dogs that have uncertain histories.",
            "<strong>Best for multi-dog households:</strong> Reading inter-dog communication helps you intervene before play escalates into genuine conflict.",
        ],
    },
    5511: {
        "cluster": "Educational",
        "common_mistakes": [
            "Treating enrichment as a luxury rather than a welfare necessity — lack of enrichment causes measurable stress and behavioural problems.",
            "Only providing physical enrichment while neglecting mental stimulation — puzzle feeders, scent work, and training provide essential cognitive engagement.",
            "Offering enrichment only when you remember — consistency matters; irregular enrichment is less effective than a daily routine.",
            "Assuming enrichment means buying expensive toys — many of the most effective enrichment activities cost nothing (scatter feeding, cardboard boxes, training games).",
        ],
        "suitability": [
            "<strong>Best for new pet owners:</strong> An accessible introduction to what enrichment means and why it matters for pet welfare.",
            "<strong>Best for owners of bored or destructive pets:</strong> Enrichment is often the most effective response to behaviour problems caused by under-stimulation.",
            "<strong>Best for indoor cats and less-active dogs:</strong> These animals benefit most from structured enrichment that compensates for limited natural stimulation.",
            "<strong>Best for budget-conscious owners:</strong> Most effective enrichment activities require little or no financial investment.",
        ],
    },
    5464: {
        "cluster": "Educational",
        "common_mistakes": [
            "Assuming all grooming terminology means the same thing across breeds — a 'clip' on a Poodle is very different from a 'clip' on a Cocker Spaniel.",
            "Confusing hand-stripping with clipping — these are fundamentally different techniques suited to different coat types.",
            "Not understanding the difference between deshedding and dematting — using the wrong technique damages the coat and causes discomfort.",
            "Thinking professional grooming is purely cosmetic — grooming maintains skin health, detects early health problems, and prevents painful matting.",
        ],
        "suitability": [
            "<strong>Best for new dog owners:</strong> Understanding grooming terminology helps you communicate clearly with professional groomers.",
            "<strong>Best for owners of breeds requiring professional grooming:</strong> Knowing what services your breed needs prevents miscommunication and unsuitable cuts.",
            "<strong>Best for home groomers:</strong> Correct terminology helps you find the right tutorials, tools, and techniques for your dog's coat type.",
            "<strong>Best as a reference during groomer consultations:</strong> Shared vocabulary between owner and groomer ensures expectations are aligned.",
        ],
    },
    5462: {
        "cluster": "Educational",
        "common_mistakes": [
            "Confusing negative reinforcement with punishment — these are technically different concepts, and misunderstanding leads to incorrect training application.",
            "Using 'dominance theory' terminology — this framework has been widely discredited by modern behavioural science and leads to harmful training practices.",
            "Misunderstanding what 'positive' and 'negative' mean in training — these refer to adding or removing stimuli, not to good and bad.",
            "Thinking 'correction' is a neutral term — in practice, corrections typically involve aversive stimuli that cause discomfort or fear.",
        ],
        "suitability": [
            "<strong>Best for new dog owners:</strong> Understanding training terminology correctly prevents being misled by outdated or harmful training methods.",
            "<strong>Best for owners choosing a trainer:</strong> Knowing what terminology ethical trainers use (and avoid) helps you identify qualified professionals.",
            "<strong>Best for understanding training resources:</strong> Books, videos, and online guides use these terms frequently; knowing them aids comprehension.",
            "<strong>Best for families training together:</strong> Shared understanding of terminology ensures consistency between all household members.",
        ],
    },
    5419: {
        "cluster": "Educational",
        "common_mistakes": [
            "Assuming cats are low-maintenance pets — cats have complex environmental, social, and health needs that require ongoing attention.",
            "Not understanding obligate carnivore status — cats have specific nutritional requirements that plant-based or dog-food diets cannot meet.",
            "Overlooking the importance of regular veterinary check-ups — cats are masters at hiding illness, making routine health checks essential.",
            "Ignoring environmental enrichment for indoor cats — without enrichment, indoor cats develop stress-related behavioural and health problems.",
        ],
        "suitability": [
            "<strong>Best for prospective cat owners:</strong> Foundational knowledge that helps you prepare properly before bringing a cat home.",
            "<strong>Best for new cat owners:</strong> A quick-reference glossary for the terms and concepts you encounter in the first months of cat ownership.",
            "<strong>Best for families adopting their first cat:</strong> Age-appropriate explanations that help the whole family understand cat care basics.",
            "<strong>Best for owners new to UK-specific guidance:</strong> UK-relevant information on registration, vaccination, and welfare standards.",
        ],
    },
    5415: {
        "cluster": "Educational",
        "common_mistakes": [
            "Interpreting all rough play as aggression — many dogs have energetic, noisy play styles that are entirely normal and healthy.",
            "Forcing dogs with different play styles to interact — mismatched play styles can cause genuine conflict between otherwise friendly dogs.",
            "Not recognising when play has tipped into over-arousal — panting, stiffening, and escalating intensity signal the need for a break.",
            "Assuming a dog that does not play is unhappy — some dogs, especially seniors, express contentment through calm companionship rather than play.",
        ],
        "suitability": [
            "<strong>Best for multi-dog households:</strong> Understanding different play styles helps match compatible dogs and prevent conflict.",
            "<strong>Best for new dog owners:</strong> Recognising your dog's natural play style guides better toy selection and interaction.",
            "<strong>Best for owners visiting dog parks:</strong> Reading play dynamics helps you decide when to intervene and when to let dogs interact freely.",
            "<strong>Best for owners of rescued dogs:</strong> Play style observation provides insight into temperament and socialisation history.",
        ],
    },

    # ── Additional posts caught by broader keyword matching ──────────────
    4786: {
        "cluster": "Dog Beds",
        "common_mistakes": [
            "Placing the bed near household appliances that produce noise — washing machines, dishwashers, and boilers can make the location stressful.",
            "Putting the bed in a draughty spot — dogs feel draughts at floor level that humans do not notice at standing height.",
            "Choosing a high-traffic hallway as the bed location — dogs need a retreat space where they will not be constantly disturbed.",
            "Moving the bed frequently — dogs build associations with locations, and constant changes can cause insecurity.",
        ],
        "suitability": [
            "<strong>Best for first-time dog owners:</strong> Bed placement is as important as bed quality — getting the location right maximises bed use.",
            "<strong>Best for dogs that refuse to use their bed:</strong> Often the issue is location, not the bed itself; this guide helps troubleshoot.",
            "<strong>Best for multi-dog households:</strong> Each dog needs their own bed in a location that feels like their own territory.",
            "<strong>Best for anxious dogs:</strong> A well-placed bed in a quiet corner provides a secure retreat space that reduces overall anxiety.",
        ],
    },
    4785: {
        "cluster": "Dog Beds",
        "common_mistakes": [
            "Machine-washing a memory foam core — most memory foam cannot be machine washed and will be ruined; only the removable cover is washable.",
            "Using strong-scented detergents — dogs have sensitive noses and may avoid a bed that smells strongly of artificial fragrance.",
            "Not drying the bed thoroughly — damp bedding develops mould and bacteria that cause skin irritation and odour.",
            "Waiting until the bed smells before washing — regular cleaning prevents odour build-up and extends the bed's usable life.",
        ],
        "suitability": [
            "<strong>Best for owners of messy or outdoor dogs:</strong> Practical cleaning routines that keep beds hygienic despite heavy use.",
            "<strong>Best for allergy-prone dogs:</strong> Regular washing removes accumulated allergens that trigger skin reactions.",
            "<strong>Best for puppy owners:</strong> Puppies create more mess, so knowing how to clean efficiently saves both time and replacement costs.",
            "<strong>Best for extending bed lifespan:</strong> Proper maintenance significantly extends the usable life of quality dog beds.",
        ],
        "routine": {
            "title": "Quick Bed Maintenance Checklist",
            "items": [
                "Weekly: Remove the cover and machine wash at 40°C with a mild, unscented detergent.",
                "Fortnightly: Vacuum the bed base and surrounding area to remove hair, dander, and debris.",
                "Monthly: Spot-clean the foam or fill with a damp cloth and allow to air dry completely before replacing the cover.",
                "Seasonally: Deep clean or replace the bed liner, inspect for flattened foam, and check zippers and seams for wear.",
                "Ongoing: Air the bed outside on dry days to freshen it naturally and reduce retained moisture.",
            ],
        },
    },
    4300: {
        "cluster": "Cat Toys",
        "common_mistakes": [
            "Placing a cardboard scratcher in a corner nobody visits — scratching is a social and territorial behaviour that needs a prominent location.",
            "Not replacing worn-out scratchers — once the corrugated surface is flattened, the scratcher loses its appeal and effectiveness.",
            "Only providing horizontal scratchers when your cat prefers vertical surfaces — observe which orientation your cat naturally chooses.",
            "Throwing away a lightly used scratcher — flip it over; most double-sided cardboard scratchers have a second usable surface underneath.",
        ],
        "suitability": [
            "<strong>Best for testing scratching preferences:</strong> Inexpensive enough to experiment with horizontal, angled, and inclined positions.",
            "<strong>Best for multi-cat households:</strong> Affordable enough to place one per cat, reducing competition over scratching territory.",
            "<strong>Best for eco-conscious owners:</strong> Made from recyclable cardboard, often from recycled sources — the most sustainable scratching option.",
            "<strong>Best for budget-conscious owners:</strong> The lowest cost per use of any scratching surface, easily replaced when worn.",
        ],
    },
}


# ─── Block builders ───────────────────────────────────────────────────────────

def build_about_guide_block(cluster):
    """Build the 'About This Guide' editorial block."""
    text = ABOUT_TEMPLATES.get(cluster, ABOUT_TEMPLATES["Educational"])
    return f"""<!-- wp:group {{"style":{{"color":{{"background":"#f9fafb"}},"border":{{"radius":"6px","width":"1px","color":"#e5e7eb"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"20px","bottom":"20px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#e5e7eb;border-width:1px;border-radius:6px;background-color:#f9fafb;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"13px"}}}}}} -->
<p style="font-size:13px"><strong>About this guide:</strong> {text} Last reviewed: May 2026. See our <a href="https://pethubonline.com/our-editorial-process/">editorial process</a> for details.</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->"""


def build_common_mistakes_block(mistakes):
    """Build 'Common Mistakes to Avoid' section."""
    items_html = "\n".join(f"<li>{m}</li>" for m in mistakes)
    return f"""
<h3 class="wp-block-heading">Common Mistakes to Avoid</h3>

<ul class="wp-block-list">
{items_html}
</ul>
"""


def build_suitability_block(items):
    """Build 'Quick Suitability Guide' section."""
    items_html = "\n".join(f"<li>{item}</li>" for item in items)
    return f"""
<h3 class="wp-block-heading">Quick Suitability Guide</h3>

<ul class="wp-block-list">
{items_html}
</ul>
"""


def build_what_to_expect_block(text):
    """Build 'What to Expect' section."""
    return f"""
<h3 class="wp-block-heading">What to Expect</h3>

<!-- wp:paragraph -->
<p>{text}</p>
<!-- /wp:paragraph -->
"""


def build_routine_block(data):
    """Build routine/checklist block."""
    items_html = "\n".join(f"<li>{item}</li>" for item in data["items"])
    return f"""
<h3 class="wp-block-heading">{data["title"]}</h3>

<ul class="wp-block-list">
{items_html}
</ul>
"""


def build_pros_cons_block(data):
    """Build Key Considerations (Pros/Cons) block."""
    adv_html = "\n".join(f"<li>{a}</li>" for a in data["advantages"])
    con_html = "\n".join(f"<li>{c}</li>" for c in data["considerations"])
    return f"""
<h3 class="wp-block-heading">Key Considerations</h3>

<div class="wp-block-columns">
<div class="wp-block-column">

<h4 class="wp-block-heading">Advantages</h4>

<ul class="wp-block-list">
{adv_html}
</ul>

</div>
<div class="wp-block-column">

<h4 class="wp-block-heading">Things to Watch</h4>

<ul class="wp-block-list">
{con_html}
</ul>

</div>
</div>
"""


# ─── API functions ────────────────────────────────────────────────────────────

def fetch_post(post_id):
    """Fetch post content via WP API."""
    url = f"{WP_API}/posts/{post_id}?context=edit&_fields=id,title,content"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
        if "id" not in data:
            return None
        return data
    except json.JSONDecodeError:
        return None


def update_post(post_id, new_content):
    """Update post content via WP API using temp file."""
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


def has_block(content, marker):
    """Check if content already contains a specific marker string."""
    return marker.lower() in content.lower()


def find_insert_point_after_first_heading(content):
    """Find insertion point after the Quick Answer box or first heading."""
    # Look for Quick Answer box end
    qa_markers = ["<!-- /wp:group -->", "quick answer"]

    # Try to find end of first wp:group (Quick Answer box)
    # First, find the Quick Answer heading or similar
    quick_answer_pattern = re.search(r'(?i)(quick\s+answer|at\s+a\s+glance|key\s+takeaway)', content[:3000])
    if quick_answer_pattern:
        # Find the closing of the group block after it
        group_end = content.find("<!-- /wp:group -->", quick_answer_pattern.end())
        if group_end > 0:
            return group_end + len("<!-- /wp:group -->")

    # Fallback: after first heading
    h_match = re.search(r'</h[1-3]>', content[:2000])
    if h_match:
        return h_match.end()

    # Last resort: beginning
    return 0


def find_insert_point_before_sources(content):
    """Find insertion point before Sources and Further Reading section."""
    sources_markers = [
        'Sources and Further Reading',
        'Sources &amp; Further Reading',
        'Sources and further reading',
    ]

    for marker in sources_markers:
        idx = content.lower().find(marker.lower())
        if idx >= 0:
            # Look for HR separator before
            hr_idx = content.rfind('<hr', max(0, idx - 300), idx)
            if hr_idx >= 0:
                return hr_idx
            # Look for heading tag before marker
            h_idx = content.rfind('<h', max(0, idx - 100), idx)
            if h_idx >= 0:
                return h_idx
            return idx

    # Try Related Guides
    for marker in ['Related Guides', 'related guides']:
        idx = content.lower().find(marker.lower())
        if idx >= 0:
            h_idx = content.rfind('<h', max(0, idx - 100), idx)
            if h_idx >= 0:
                return h_idx
            return idx

    return len(content)


def process_post(post_id, post_data):
    """Process a single post: fetch, check, insert blocks, update."""
    cluster = post_data["cluster"]

    post = fetch_post(post_id)
    if not post:
        return {
            "id": post_id, "title": "FETCH_ERROR", "cluster": cluster,
            "about_guide": False, "common_mistakes": False, "suitability": False,
            "what_to_expect": False, "routine": False, "pros_cons": False,
            "status": "FETCH_ERROR"
        }

    title = html_mod.unescape(post["title"]["raw"])
    content = post["content"]["raw"]

    # Track what we add
    added = {
        "about_guide": False, "common_mistakes": False, "suitability": False,
        "what_to_expect": False, "routine": False, "pros_cons": False
    }

    blocks_after_heading = []
    blocks_before_sources = []

    # BLOCK 1: About This Guide (insert after first heading)
    if not has_block(content, "About this guide"):
        blocks_after_heading.append(build_about_guide_block(cluster))
        added["about_guide"] = True

    # BLOCK 2: Common Mistakes (insert before Sources)
    if not has_block(content, "Common Mistakes to Avoid") and "common_mistakes" in post_data:
        blocks_before_sources.append(build_common_mistakes_block(post_data["common_mistakes"]))
        added["common_mistakes"] = True

    # BLOCK 3: Quick Suitability Guide (insert before Sources)
    if not has_block(content, "Quick Suitability Guide") and "suitability" in post_data:
        blocks_before_sources.append(build_suitability_block(post_data["suitability"]))
        added["suitability"] = True

    # BLOCK 4: What to Expect (insert before Sources)
    if not has_block(content, "What to Expect") and "what_to_expect" in post_data:
        blocks_before_sources.append(build_what_to_expect_block(post_data["what_to_expect"]))
        added["what_to_expect"] = True

    # BLOCK 5: Routine/Checklist (insert before Sources)
    if not has_block(content, post_data.get("routine", {}).get("title", "XYZNOTFOUND")) and "routine" in post_data:
        # Also check generic routine markers
        routine_title = post_data["routine"]["title"]
        if not has_block(content, routine_title):
            blocks_before_sources.append(build_routine_block(post_data["routine"]))
            added["routine"] = True

    # BLOCK 6: Key Considerations / Pros-Cons (insert before Sources)
    if not has_block(content, "Key Considerations") and "pros_cons" in post_data:
        blocks_before_sources.append(build_pros_cons_block(post_data["pros_cons"]))
        added["pros_cons"] = True

    # Check if anything to add
    if not any(added.values()):
        return {
            "id": post_id, "title": title, "cluster": cluster,
            **added, "status": "ALREADY_COMPLETE"
        }

    # Insert blocks
    new_content = content

    # Insert "About This Guide" after first heading
    if blocks_after_heading:
        insert_pt = find_insert_point_after_first_heading(new_content)
        combined = "\n\n" + "\n\n".join(blocks_after_heading) + "\n\n"
        new_content = new_content[:insert_pt] + combined + new_content[insert_pt:]

    # Insert remaining blocks before Sources
    if blocks_before_sources:
        insert_pt = find_insert_point_before_sources(new_content)
        combined = "\n\n" + "\n\n".join(blocks_before_sources) + "\n\n"
        new_content = new_content[:insert_pt] + combined + new_content[insert_pt:]

    # Update via API
    success, msg = update_post(post_id, new_content)
    status = "UPDATED" if success else f"ERROR: {msg}"

    return {
        "id": post_id, "title": title, "cluster": cluster,
        **added, "status": status
    }


def main():
    os.makedirs(LOG_DIR, exist_ok=True)

    # Initialize CSV log
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "title", "cluster", "about_guide", "common_mistakes",
                         "suitability", "what_to_expect", "routine", "pros_cons", "status"])

    post_ids = sorted(POST_DATA.keys())
    total = len(post_ids)
    results = []

    print(f"Processing {total} posts across 6 clusters...\n")

    for i, post_id in enumerate(post_ids):
        data = POST_DATA[post_id]
        cluster = data["cluster"]
        print(f"[{i+1}/{total}] Post {post_id} ({cluster})...", end=" ", flush=True)

        result = process_post(post_id, data)
        results.append(result)

        # Write to CSV
        with open(LOG_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                result["id"], result["title"], result["cluster"],
                result["about_guide"], result["common_mistakes"],
                result["suitability"], result["what_to_expect"],
                result["routine"], result["pros_cons"], result["status"]
            ])

        print(f"{result['status']}", flush=True)

        if i < total - 1:
            time.sleep(0.5)

    # Summary
    print("\n" + "=" * 70)
    print("HUMANIZATION BATCH 2 — SUMMARY")
    print("=" * 70)

    updated = sum(1 for r in results if r["status"] == "UPDATED")
    already = sum(1 for r in results if r["status"] == "ALREADY_COMPLETE")
    errors = [r for r in results if r["status"].startswith("ERROR")]

    print(f"Total posts processed:   {total}")
    print(f"Successfully updated:    {updated}")
    print(f"Already complete:        {already}")
    print(f"Errors:                  {len(errors)}")

    # Block counts
    ag = sum(1 for r in results if r["about_guide"])
    cm = sum(1 for r in results if r["common_mistakes"])
    sg = sum(1 for r in results if r["suitability"])
    we = sum(1 for r in results if r["what_to_expect"])
    rt = sum(1 for r in results if r["routine"])
    pc = sum(1 for r in results if r["pros_cons"])

    print(f"\nBlocks added:")
    print(f"  About This Guide:      {ag}")
    print(f"  Common Mistakes:       {cm}")
    print(f"  Suitability Guide:     {sg}")
    print(f"  What to Expect:        {we}")
    print(f"  Routine/Checklist:     {rt}")
    print(f"  Key Considerations:    {pc}")

    # By cluster
    print(f"\nBy cluster:")
    for cluster in ["Cat Supplies", "Cat Toys", "Dog Harnesses", "Dog Beds", "Indoor Cats", "Educational"]:
        cluster_results = [r for r in results if r["cluster"] == cluster]
        cluster_updated = sum(1 for r in cluster_results if r["status"] == "UPDATED")
        print(f"  {cluster}: {cluster_updated}/{len(cluster_results)} updated")

    if errors:
        print(f"\nErrors:")
        for e in errors:
            print(f"  Post {e['id']}: {e['status']}")

    print(f"\nLog saved to: {LOG_FILE}")


if __name__ == "__main__":
    main()
