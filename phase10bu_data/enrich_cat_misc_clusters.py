#!/usr/bin/env python3
"""
Phase 10BU/10BV/10BY Content Enrichment for Cat & Misc clusters.
Clusters: Cat Supplies, Cat Toys, Indoor Cats, Dog Harnesses, Training Supplies, Pet Care
"""

import csv
import json
import subprocess
import tempfile
import time
import os
import re

# ── Config ──────────────────────────────────────────────────────────────
WP_URL = "https://pethubonline.com/wp-json/wp/v2"
WP_AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
TARGET_CLUSTERS = {"Cat Supplies", "Cat Toys", "Indoor Cats", "Dog Harnesses", "Training Supplies", "Pet Care"}
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase10bu_data"
CITATION_CSV = "/var/lib/freelancer/projects/40416335/phase10br_data/citation_preference.csv"
MOAT_CSV = "/var/lib/freelancer/projects/40416335/phase10bq_data/authority_moat_v2.csv"

# ── Load score data ────────────────────────────────────────────────────
def load_csv(path):
    rows = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = int(row["id"])
            rows[pid] = row
    return rows

citation_data = load_csv(CITATION_CSV)
moat_data = load_csv(MOAT_CSV)

# Filter to target clusters
target_posts = {}
for pid, row in citation_data.items():
    if row["cluster"] in TARGET_CLUSTERS:
        target_posts[pid] = {
            "id": pid,
            "title": row["title"],
            "cluster": row["cluster"],
            "citation": row,
            "moat": moat_data.get(pid, {}),
        }

print(f"Found {len(target_posts)} posts in target clusters")

# ── WordPress API helpers ──────────────────────────────────────────────
def wp_get(endpoint, retries=3):
    url = f"{WP_URL}{endpoint}"
    for attempt in range(retries):
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", WP_AUTH, url],
            capture_output=True, text=True, timeout=60
        )
        try:
            data = json.loads(result.stdout)
            return data
        except (json.JSONDecodeError, ValueError):
            if "429" in result.stdout[:200] or result.stdout.strip() == "":
                wait = 5 * (attempt + 1)
                print(f"  Rate limited on GET, waiting {wait}s (attempt {attempt+1})")
                time.sleep(wait)
            else:
                print(f"  GET parse error: {result.stdout[:200]}")
                time.sleep(3)
    return None

def wp_put(post_id, content, retries=3):
    url = f"{WP_URL}/posts/{post_id}"
    payload = json.dumps({"content": content})
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    tmp.write(payload)
    tmp.close()
    for attempt in range(retries):
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", WP_AUTH,
             "-X", "PUT",
             "-H", "Content-Type: application/json",
             "-d", f"@{tmp.name}",
             url],
            capture_output=True, text=True, timeout=120
        )
        try:
            resp = json.loads(result.stdout)
            if "id" in resp:
                os.unlink(tmp.name)
                return True
            elif "429" in str(resp) or "Too Many" in result.stdout[:300]:
                wait = 5 * (attempt + 1)
                print(f"  Rate limited on PUT, waiting {wait}s (attempt {attempt+1})")
                time.sleep(wait)
            else:
                print(f"  PUT error for {post_id}: {result.stdout[:300]}")
                os.unlink(tmp.name)
                return False
        except json.JSONDecodeError:
            if "429" in result.stdout[:300]:
                wait = 5 * (attempt + 1)
                print(f"  Rate limited on PUT, waiting {wait}s (attempt {attempt+1})")
                time.sleep(wait)
            else:
                print(f"  PUT JSON error for {post_id}: {result.stdout[:200]}")
                os.unlink(tmp.name)
                return False
    os.unlink(tmp.name)
    return False

def fetch_post_content(post_id):
    """Fetch a single post's raw Gutenberg content"""
    time.sleep(2)
    data = wp_get(f"/posts/{post_id}?context=edit")
    if isinstance(data, dict) and "content" in data:
        c = data["content"]
        if isinstance(c, dict):
            return c.get("raw", c.get("rendered", ""))
        return c
    return None

# ── Block detection ────────────────────────────────────────────────────
def has_block(content, heading_text):
    """Check if a block with given heading already exists"""
    pattern = re.compile(re.escape(heading_text), re.IGNORECASE)
    return bool(pattern.search(content))

# ── Block generators ───────────────────────────────────────────────────

# UK institution references per cluster/topic
UK_REFS = {
    "Cat Supplies": {
        "research_sources": (
            "Our recommendations align with Cats Protection's published guidance on essential cat "
            "equipment and environmental needs, which reflects current UK feline welfare standards. "
            "We reference International Cat Care (iCatCare) veterinary guidelines on cat product "
            "suitability, material safety, and species-appropriate design. The RSPCA's five welfare "
            "needs framework informs our assessments of whether supplies meet the environmental and "
            "behavioural needs of cats. Blue Cross cat care resources and PDSA's PAW Report data on "
            "UK cat ownership practices provide additional context for our product guidance."
        ),
        "why_sources": (
            "The cat supplies market includes products that may not meet feline-specific needs despite "
            "being marketed for cats. We reference Cats Protection, iCatCare, and the RSPCA because "
            "these UK organisations evaluate cat products based on feline behaviour science and welfare "
            "outcomes rather than commercial interests. Our methodology assesses supplies against "
            "species-appropriate criteria as defined by UK veterinary and welfare bodies."
        ),
    },
    "Cat Toys": {
        "research_sources": (
            "Our toy guidance references International Cat Care (iCatCare) published research on feline "
            "play behaviour, prey drive, and environmental enrichment needs. Cats Protection's guidance "
            "on safe play and toy selection for indoor and outdoor cats informs our safety assessments. "
            "We consult the RSPCA's environmental enrichment standards for cats, which emphasise the "
            "importance of play in meeting behavioural welfare needs. The PDSA's PAW Report provides "
            "UK-wide data on cat enrichment practices and the Blue Cross's cat play resources contribute "
            "additional UK veterinary context."
        ),
        "why_sources": (
            "Cat toys vary widely in safety, durability, and suitability for different play styles. "
            "We reference iCatCare, Cats Protection, and the RSPCA because these organisations base "
            "their toy guidance on feline behavioural science — including prey sequence patterns, "
            "appropriate play duration, and material safety. Our approach evaluates toys against "
            "these evidence-based standards rather than novelty or marketing appeal."
        ),
    },
    "Indoor Cats": {
        "research_sources": (
            "Our indoor cat guidance draws on International Cat Care (iCatCare) published protocols "
            "for indoor cat environmental enrichment, which represent current veterinary consensus on "
            "feline welfare indoors. Cats Protection's indoor cat resources, including their guidance "
            "on vertical space, territory management, and stimulation, inform our practical advice. "
            "The RSPCA's position on keeping cats indoors and their five welfare needs framework "
            "provide the ethical and welfare context for our recommendations. Battersea's cat "
            "rehoming guidance on indoor-only environments and PDSA's data on indoor cat health "
            "outcomes contribute additional UK-specific evidence."
        ),
        "why_sources": (
            "Indoor cats face unique welfare challenges including reduced physical activity, limited "
            "territory, and potential behavioural issues if their environment is not properly enriched. "
            "We reference iCatCare, Cats Protection, and the RSPCA because their indoor cat guidance "
            "is grounded in feline behavioural science and veterinary research. Our approach ensures "
            "advice reflects what UK feline welfare experts recommend rather than anecdotal opinion."
        ),
    },
    "Dog Harnesses": {
        "research_sources": (
            "Our harness guidance references the RSPCA's published position on dog walking equipment, "
            "which evaluates harness designs against the five welfare needs including freedom from "
            "pain and distress. The British Veterinary Association (BVA) guidance on appropriate "
            "restraint equipment for dogs informs our assessments of harness fit and pressure "
            "distribution. We consult the Kennel Club's advice on lead and harness training, "
            "particularly for puppies and reactive dogs. Blue Cross walking equipment recommendations "
            "and PDSA practical guidance on harness use provide additional UK-specific veterinary context."
        ),
        "why_sources": (
            "Dog harness marketing frequently makes claims about comfort, training effectiveness, and "
            "injury prevention that may not be supported by evidence. We reference the RSPCA, BVA, "
            "and Kennel Club because these UK organisations evaluate walking equipment based on "
            "animal welfare outcomes and veterinary biomechanics. Our methodology focuses on fit, "
            "pressure distribution, and suitability for specific needs as defined by UK professionals."
        ),
    },
    "Training Supplies": {
        "research_sources": (
            "Our training supply guidance aligns with the Kennel Club's published position on reward-based "
            "training methods, which represent current UK canine behaviour science consensus. The British "
            "Veterinary Association (BVA) position statement on aversive training methods informs our "
            "assessment of training tools and their welfare implications. We reference the RSPCA's "
            "training guidance, which advocates positive reinforcement and opposes punitive equipment. "
            "Blue Cross training resources and the Animal Behaviour and Training Council (ABTC) "
            "professional standards provide additional UK-specific frameworks for our recommendations."
        ),
        "why_sources": (
            "Training equipment ranges from evidence-supported reward-based tools to aversive devices "
            "that UK veterinary and welfare organisations advise against. We reference the Kennel Club, "
            "BVA, and RSPCA because their training guidance reflects peer-reviewed behavioural science "
            "and UK animal welfare law. Our approach evaluates training supplies based on their alignment "
            "with positive reinforcement principles endorsed by UK professional bodies."
        ),
    },
    "Pet Care": {
        "research_sources": (
            "Our general pet care guidance references the RSPCA's Animal Welfare Act 2006 compliance "
            "framework and their five welfare needs model, which applies to all companion animals. "
            "The British Veterinary Association (BVA) position statements on preventive care and "
            "the PDSA's annual PAW Report provide UK-wide data on pet care practices across species. "
            "We consult Cats Protection and International Cat Care (iCatCare) for feline-specific care "
            "guidance, and the Kennel Club for canine-specific standards. Blue Cross multi-species "
            "care resources contribute additional practical UK context."
        ),
        "why_sources": (
            "Pet care advice spans multiple species, each with distinct needs that generic guidance "
            "can overlook. We reference the RSPCA, BVA, and species-specific organisations like "
            "iCatCare and the Kennel Club because they maintain separate, evidence-based guidance "
            "for each companion animal type. Our methodology ensures care advice is species-appropriate "
            "and reflects UK veterinary consensus rather than generalised assumptions."
        ),
    },
}

# Glossary terms per cluster
GLOSSARY_TERMS = {
    "Cat Supplies": [
        ("Sisal", "A natural plant fibre commonly wrapped around scratching posts; durable and satisfying for cats to scratch, preferred over carpet by most feline behaviourists."),
        ("Breakaway collar", "A cat collar designed with a safety release mechanism that opens under pressure, preventing strangulation if the collar catches on branches, fences, or furniture."),
        ("Clumping litter", "Cat litter, typically bentonite clay-based, that forms solid clumps on contact with moisture, allowing spot-cleaning without replacing the entire tray."),
        ("Microchip cat flap", "A cat door that reads your cat's implanted microchip and only unlocks for registered cats, preventing neighbourhood cats from entering your home."),
        ("Enzymatic cleaner", "A cleaning product that uses enzymes to break down organic compounds in cat urine and faeces, eliminating odour at the molecular level rather than masking it."),
    ],
    "Cat Toys": [
        ("Prey sequence", "The natural feline hunting cycle of stare-stalk-chase-pounce-catch-kill-eat; effective cat toys simulate one or more stages of this sequence."),
        ("Wand toy", "A stick or rod with a string and attached lure (feathers, fabric) that allows interactive play mimicking prey movement while keeping hands at a safe distance."),
        ("Puzzle feeder", "A device that requires a cat to manipulate, push, or solve a mechanism to access food or treats, providing mental stimulation and slowing eating speed."),
        ("Catnip (Nepeta cataria)", "A herb from the mint family whose essential oil nepetalactone triggers a temporary euphoric response in approximately 50-70% of cats; the effect is genetic and harmless."),
        ("Environmental enrichment", "Modifications to a cat's living space — including toys, climbing structures, hiding spots, and sensory stimuli — that promote natural behaviours and reduce stress."),
    ],
    "Indoor Cats": [
        ("Vertical space", "Elevated areas such as cat trees, shelves, and window perches that allow indoor cats to climb, survey their territory, and feel secure — a key welfare need identified by iCatCare."),
        ("Resource station", "A distinct area containing one key resource (food, water, litter, or resting spot); iCatCare recommends one per cat plus one extra in multi-cat households."),
        ("Window enrichment", "Bird feeders, window perches, or visual stimuli placed near windows to provide indoor cats with mental stimulation and environmental engagement."),
        ("Territorial marking", "Natural feline behaviours including scratching, rubbing, and spraying used to establish territory; indoor cats need appropriate outlets such as scratching posts and chin-rubbing surfaces."),
        ("Indoor zoning", "Dividing indoor space into functional zones (feeding, resting, playing, toileting) to give cats predictable access to resources and reduce inter-cat conflict."),
    ],
    "Dog Harnesses": [
        ("Y-front harness", "A harness with a Y-shaped front strap that sits on the breastbone rather than across the shoulders, allowing natural front-leg movement and reducing gait restriction."),
        ("Back-clip harness", "A harness with the lead attachment on the back between the shoulder blades, suitable for calm walkers but offering less directional control for dogs that pull."),
        ("Front-clip harness", "A harness with the lead attachment at the chest, which redirects a pulling dog sideways toward the handler rather than allowing forward momentum."),
        ("Girth measurement", "The circumference of a dog's ribcage measured just behind the front legs; the primary measurement for correct harness sizing and fit."),
        ("Pressure distribution", "How a harness spreads lead tension across the dog's body; well-designed harnesses distribute force across the chest and ribcage rather than concentrating it on the throat."),
    ],
    "Training Supplies": [
        ("Positive reinforcement", "A training method that rewards desired behaviours with treats, praise, or play, increasing the likelihood of those behaviours being repeated; endorsed by the Kennel Club and BVA."),
        ("Clicker", "A small handheld device that produces a consistent click sound used to mark the exact moment a dog performs a desired behaviour, bridging the gap between action and reward."),
        ("Long line", "A training lead typically 5-15 metres in length that allows a dog controlled freedom during recall training while maintaining handler safety and control."),
        ("High-value treat", "A food reward with strong appeal (e.g., small pieces of cooked chicken, cheese, or liver) used during training when competing with distractions or teaching new behaviours."),
        ("Marker word", "A short, consistent verbal cue (e.g., 'yes' or 'good') used like a clicker to mark the precise moment a desired behaviour occurs, signalling that a reward follows."),
    ],
    "Pet Care": [
        ("Five welfare needs", "The five needs defined in the UK Animal Welfare Act 2006: suitable environment, suitable diet, ability to exhibit normal behaviour, companionship needs, and protection from pain, suffering, injury, and disease."),
        ("Preventive care", "Routine veterinary and home-based health measures including vaccinations, parasite treatments, dental care, and regular health checks aimed at preventing disease rather than treating it."),
        ("Species-appropriate", "Care, equipment, or environmental conditions designed to meet the specific biological and behavioural needs of a particular animal species rather than applying generic standards."),
        ("Microchipping", "The implantation of a small electronic chip (approximately rice-grain sized) under the skin that stores a unique identification number; compulsory for dogs in England and now for cats from June 2024."),
        ("Body Condition Score (BCS)", "A standardised assessment scale (typically 1-9 for dogs, 1-9 for cats) used by UK vets to evaluate whether a pet is underweight, ideal weight, or overweight based on visual and physical examination."),
    ],
}

# Comparison tables per post (tailored to specific high-priority posts)
def get_comparison_table(post_id, title, cluster):
    """Generate comparison table HTML specific to the post topic"""
    tables = {
        # Cat Supplies
        4286: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Cat Scratching Post Materials Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Feature</th><th>Sisal Rope</th><th>Sisal Fabric</th><th>Cardboard</th></tr></thead><tbody><tr><td>Durability</td><td>High; withstands heavy scratching for 1-3 years depending on use</td><td>High; flat weave resists shredding better than rope in some cases</td><td>Low to moderate; needs replacing every 2-6 months</td></tr><tr><td>Scratch Feel</td><td>Rough texture satisfies claw-sheathing instinct; vertical shredding action</td><td>Smoother than rope; suits cats that prefer a flatter surface</td><td>Soft shred; appeals to cats that enjoy digging and raking</td></tr><tr><td>Mess Level</td><td>Low; minimal fibre shedding</td><td>Very low; tightly woven surface resists fraying</td><td>Moderate to high; cardboard particles shed with use</td></tr><tr><td>Cost</td><td>Moderate; widely available in UK pet shops</td><td>Moderate to high; less common than rope-wrapped posts</td><td>Low; budget-friendly and often replaceable as inserts</td></tr><tr><td>Best For</td><td>Most cats; the standard recommendation from Cats Protection</td><td>Cats that prefer flat-surface scratching or are gentle scratchers</td><td>Budget-conscious owners or as secondary scratching options</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        4314: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Cat Litter Tray Types Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Feature</th><th>Open Tray</th><th>Hooded / Enclosed</th><th>Top-Entry</th></tr></thead><tbody><tr><td>Odour Containment</td><td>Minimal; odours disperse freely</td><td>Moderate; hood traps some odour but can concentrate ammonia</td><td>Good; enclosed design limits odour escape</td></tr><tr><td>Cat Acceptance</td><td>High; most cats accept open trays readily (iCatCare recommendation)</td><td>Variable; some cats dislike feeling enclosed or trapped</td><td>Variable; requires jumping in, not suitable for kittens or senior cats</td></tr><tr><td>Litter Tracking</td><td>Higher; litter scatters easily over low sides</td><td>Moderate; hood reduces scatter but litter sticks to flap</td><td>Low; top entry catches litter on exit grate</td></tr><tr><td>Cleaning Access</td><td>Very easy; full access from above</td><td>Requires removing hood for thorough cleaning</td><td>Moderate; must reach through top opening</td></tr><tr><td>Best For</td><td>Multi-cat homes, senior cats, and kittens (Cats Protection standard)</td><td>Owners wanting reduced odour in small spaces</td><td>Homes with dogs that access litter or high-scatter cats</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        4293: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Cat Tree Height Categories Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Feature</th><th>Small (Under 100cm)</th><th>Medium (100-150cm)</th><th>Tall (150cm+)</th></tr></thead><tbody><tr><td>Floor Space</td><td>Compact; suits small flats and single rooms</td><td>Moderate footprint; needs wall space or corner</td><td>Large base needed for stability; may need wall anchoring</td></tr><tr><td>Climbing Value</td><td>Limited vertical exercise; one or two platforms</td><td>Good climbing range; typically 3-4 platforms</td><td>Full vertical territory; multiple levels, platforms, and perches</td></tr><tr><td>Stability</td><td>Generally stable due to low centre of gravity</td><td>Check base width; may wobble with large cats</td><td>Must be wall-anchored for safety, especially with multiple cats</td></tr><tr><td>Cat Weight Limit</td><td>Typically suited to cats up to 5-6kg</td><td>Usually rated for cats up to 6-8kg per platform</td><td>Check manufacturer rating; quality models support 8kg+ per platform</td></tr><tr><td>Best For</td><td>Kittens, single cats in small spaces, supplementary furniture</td><td>Most single or two-cat households with moderate space</td><td>Multi-cat homes or active breeds needing maximum vertical territory</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        # Cat Toys
        4195: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Indoor Cat Toy Types Compared by Play Style</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Feature</th><th>Wand / Fishing Rod Toys</th><th>Puzzle Feeders</th><th>Automated / Electronic Toys</th></tr></thead><tbody><tr><td>Play Type</td><td>Interactive; simulates prey movement through stalk-chase-pounce sequence</td><td>Solo; engages problem-solving and foraging instincts</td><td>Semi-independent; random movement patterns mimic prey</td></tr><tr><td>Human Involvement</td><td>Required throughout; you control the prey simulation</td><td>Setup only; cat engages independently</td><td>Minimal after activation; batteries or USB charging required</td></tr><tr><td>Exercise Value</td><td>High; promotes jumping, running, and pouncing</td><td>Low physical but high mental stimulation</td><td>Moderate; depends on design and cat's engagement level</td></tr><tr><td>Duration</td><td>10-15 minute sessions recommended (iCatCare guidance)</td><td>Can engage cats for 10-30 minutes depending on difficulty</td><td>Variable; some cats lose interest quickly, others stay engaged</td></tr><tr><td>Best For</td><td>Daily play sessions; all indoor cats need interactive play (Cats Protection)</td><td>Cats home alone during the day; overweight cats needing slower feeding</td><td>Supplementary enrichment between interactive sessions</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        4181: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Interactive Cat Toy Categories Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Feature</th><th>Wand Toys</th><th>Puzzle Toys</th><th>Kick Toys</th></tr></thead><tbody><tr><td>Prey Simulation</td><td>Bird or insect flight; mouse-like ground movement</td><td>Foraging and hunting for hidden food</td><td>Prey capture; bunny-kick wrestling</td></tr><tr><td>Engagement Style</td><td>Handler-led; requires active participation</td><td>Self-directed; cat works at own pace</td><td>Self-directed; cat holds and kicks independently</td></tr><tr><td>Safety Consideration</td><td>Store out of reach after play to prevent string ingestion</td><td>Ensure puzzle gaps cannot trap paws</td><td>Check seams and fillings regularly for wear</td></tr><tr><td>Recommended Frequency</td><td>2-3 sessions daily, 5-15 minutes each</td><td>Available daily; rotate every few days for novelty</td><td>Available as needed; replace when worn</td></tr><tr><td>Best For</td><td>Cats with strong chase drive; bonding through play</td><td>Food-motivated cats; mental stimulation for indoor cats</td><td>Cats that enjoy wrestling; outlet for bunny-kick behaviour</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        # Dog Harnesses
        5418: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Dog Harness Attachment Types Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Feature</th><th>Front-Clip</th><th>Back-Clip</th><th>Dual-Clip (Front + Back)</th></tr></thead><tbody><tr><td>Pull Reduction</td><td>Redirects dog sideways when pulling; reduces forward momentum</td><td>No pull reduction; allows full forward pull</td><td>Front clip for training, back clip for relaxed walks</td></tr><tr><td>Gait Impact</td><td>May alter natural gait if poorly fitted; check strap position</td><td>Minimal gait interference when properly fitted</td><td>Varies by which clip is in use</td></tr><tr><td>Ease of Use</td><td>Lead may tangle under legs during direction changes</td><td>Simple; lead stays on back out of the way</td><td>Slightly more complex; two D-ring options</td></tr><tr><td>Training Value</td><td>Useful for teaching loose-lead walking alongside reward-based methods</td><td>Limited training feedback; best for already-trained dogs</td><td>Versatile; switch clips as training progresses</td></tr><tr><td>Best For</td><td>Dogs learning to walk without pulling (Kennel Club positive training context)</td><td>Calm walkers, small dogs, and dogs comfortable on lead</td><td>Dogs in active training transitioning to relaxed walking</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        4027: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Dog Walking Equipment Types Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Feature</th><th>Flat Collar</th><th>Y-Front Harness</th><th>Head Halter</th></tr></thead><tbody><tr><td>Pressure Point</td><td>Concentrated on neck and trachea</td><td>Distributed across chest and ribcage</td><td>Around muzzle and behind ears</td></tr><tr><td>Trachea Risk</td><td>Risk of tracheal damage in dogs that pull (BVA caution)</td><td>No throat pressure when properly fitted</td><td>No throat pressure; head control instead</td></tr><tr><td>Escape Risk</td><td>Moderate; dogs can back out if collar is loose</td><td>Low with properly fitted Y-front design</td><td>Moderate; requires correct fit and acclimatisation</td></tr><tr><td>Training Compatibility</td><td>Suitable for dogs that walk calmly on lead</td><td>Compatible with positive reinforcement training methods</td><td>Requires careful introduction; not all dogs tolerate them</td></tr><tr><td>Best For</td><td>ID tag carrying; calm walkers; always used with a harness for safety</td><td>Daily walking for most dogs; RSPCA-recommended for dogs that pull</td><td>Veterinary or behaviourist-guided use for specific training needs</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        # Training Supplies
        4132: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Puppy Training Methods Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Feature</th><th>Positive Reinforcement</th><th>Clicker Training</th><th>Lure-Reward Training</th></tr></thead><tbody><tr><td>Mechanism</td><td>Rewards desired behaviour with treats, praise, or play</td><td>Click marks exact moment of desired behaviour, followed by treat</td><td>Food lure guides dog into position, then rewarded</td></tr><tr><td>Timing Precision</td><td>Depends on handler speed; marker word helps</td><td>High; click provides consistent, precise timing</td><td>Moderate; lure provides continuous guidance</td></tr><tr><td>UK Professional Endorsement</td><td>Kennel Club, BVA, RSPCA, and ABTC all endorse</td><td>Widely endorsed; used by many ABTC-registered trainers</td><td>Accepted; useful for teaching initial positions</td></tr><tr><td>Equipment Needed</td><td>Treats and/or toys</td><td>Clicker device plus treats</td><td>High-value treats initially; phase out lure over time</td></tr><tr><td>Best For</td><td>All training; the foundation of modern UK dog training</td><td>Precise behaviours; trick training; agility foundations</td><td>Teaching sit, down, and spin to puppies and beginner dogs</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        4118: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Training Approach Comparison for Common Behaviours</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Behaviour</th><th>Positive Approach</th><th>Why It Works</th><th>What to Avoid</th></tr></thead><tbody><tr><td>Pulling on Lead</td><td>Stop and wait when lead goes tight; reward when lead is loose</td><td>Dog learns that pulling stops forward movement; loose lead continues the walk</td><td>Yanking lead or using choke/prong collars (BVA advises against aversive methods)</td></tr><tr><td>Jumping Up</td><td>Turn away and ignore; reward four-paws-on-floor greeting</td><td>Removes the attention that jumping seeks; reinforces calm greeting</td><td>Pushing dog down or kneeing; these can inadvertently reward with physical contact</td></tr><tr><td>Recall</td><td>High-value treat reward every time dog returns; use long line for safety</td><td>Coming back becomes more rewarding than the distraction</td><td>Calling dog to punish or end fun; this poisons the recall cue</td></tr><tr><td>Barking</td><td>Identify trigger; reward quiet moments; teach a "quiet" cue</td><td>Addresses the root cause (fear, excitement, attention-seeking)</td><td>Shouting or using anti-bark devices (RSPCA advises against punishment-based tools)</td></tr><tr><td>Mouthing/Nipping</td><td>Redirect to toy; end play briefly if teeth touch skin</td><td>Teaches bite inhibition through natural consequence (play stops)</td><td>Physical corrections or holding mouth shut; these can increase fear and aggression</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        # Indoor Cats
        7346: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Indoor Cat Diet Considerations Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Factor</th><th>Indoor Cat</th><th>Outdoor Cat</th><th>Key Difference</th></tr></thead><tbody><tr><td>Calorie Needs</td><td>Lower; reduced activity means fewer calories needed daily</td><td>Higher; hunting, patrolling, and weather exposure increase demand</td><td>Indoor cats typically need 10-20% fewer calories (consult vet for exact amount)</td></tr><tr><td>Weight Risk</td><td>Higher obesity risk due to reduced activity and boredom eating</td><td>Lower obesity risk; natural activity levels regulate intake</td><td>Regular BCS assessment is critical for indoor cats</td></tr><tr><td>Hairball Risk</td><td>Higher; more grooming due to inactivity can increase ingestion</td><td>Lower; natural fibre intake outdoors may help</td><td>Indoor formulas often include added fibre for hairball management</td></tr><tr><td>Hydration</td><td>May drink less if water source is not appealing</td><td>May access additional water sources outdoors</td><td>Multiple water stations and wet food help indoor cat hydration</td></tr><tr><td>Enrichment Feeding</td><td>Essential; puzzle feeders simulate hunting behaviour</td><td>Hunting provides natural foraging enrichment</td><td>iCatCare recommends puzzle feeders as standard for indoor cats</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        # Pet Care
        4576: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Multi-Pet Household Needs Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Need</th><th>Dogs</th><th>Cats</th><th>Multi-Pet Consideration</th></tr></thead><tbody><tr><td>Feeding</td><td>Typically 2 meals daily; food can be left briefly</td><td>Little and often preferred; graze feeding common</td><td>Separate feeding areas; prevent dogs accessing cat food (higher protein/fat)</td></tr><tr><td>Personal Space</td><td>Den or bed area; generally social animals</td><td>Elevated hiding spots; need escape routes from dogs</td><td>Cats must have dog-free zones with vertical escape routes (iCatCare)</td></tr><tr><td>Toileting</td><td>Outdoor access or scheduled walks</td><td>Litter tray: one per cat plus one extra (Cats Protection rule)</td><td>Place litter trays where dogs cannot access them to prevent coprophagia</td></tr><tr><td>Exercise</td><td>Daily walks and physical play</td><td>Indoor play sessions; climbing and hunting simulation</td><td>Do not expect dogs and cats to exercise together; meet needs separately</td></tr><tr><td>Introductions</td><td>Gradual, controlled meetings on lead</td><td>Scent swapping before visual introduction</td><td>Follow RSPCA multi-pet introduction protocol: scent first, barrier meetings, supervised access</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
    }
    return tables.get(post_id)

# Practical step-by-step guides per post
def get_practical_guide(post_id, title, cluster):
    """Generate practical guide HTML specific to the post topic"""
    guides = {
        4286: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: Choosing and Placing a Cat Scratching Post</h4>
<ol><li><strong>Step 1 — Measure your cat's stretch:</strong> Watch your cat scratch and measure their full stretch from paws to tail base. The scratching post must be at least as tall as this measurement so your cat can fully extend — Cats Protection recommends posts tall enough for a full body stretch.</li><li><strong>Step 2 — Choose the material:</strong> Sisal rope or sisal fabric are preferred by most cats and recommended by feline behaviourists. Avoid carpet-covered posts, which can confuse cats about what surfaces are acceptable to scratch.</li><li><strong>Step 3 — Check stability:</strong> Push the post firmly from the top. It should not wobble or tip. A heavy, wide base is essential — cats will avoid unstable posts. Wall-mounted options eliminate tip risk entirely.</li><li><strong>Step 4 — Place near existing scratch targets:</strong> Position the post where your cat already scratches (near furniture, doorways, or sleeping areas). Cats scratch to mark territory, so high-traffic areas are natural choices.</li><li><strong>Step 5 — Encourage use without force:</strong> Rub catnip on the post or play with a wand toy near it. Never physically place your cat's paws on the post — Cats Protection advises this creates negative associations. Reward any voluntary interaction with the post.</li></ol>
</div>
<!-- /wp:group -->""",
        4314: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: Setting Up a Cat Litter Tray Correctly</h4>
<ol><li><strong>Step 1 — Choose tray size:</strong> The tray should be at least 1.5 times your cat's body length (nose to tail base). Kittens and senior cats need trays with low sides (under 10cm) for easy entry. iCatCare recommends larger trays over smaller ones.</li><li><strong>Step 2 — Select litter depth:</strong> Fill to a depth of approximately 3-5cm. Most cats prefer enough litter to dig and cover, but excessive depth wastes litter. Watch your cat's digging behaviour and adjust accordingly.</li><li><strong>Step 3 — Position thoughtfully:</strong> Place in a quiet, accessible location away from food and water bowls. Avoid high-traffic areas or near washing machines and boilers. Cats Protection recommends one tray per cat plus one extra, in different locations.</li><li><strong>Step 4 — Establish a cleaning routine:</strong> Scoop solid waste and clumps at least once daily. Replace all litter and wash the tray with hot water (no strong disinfectants) weekly. Cats may refuse a dirty tray, leading to house-soiling.</li><li><strong>Step 5 — Monitor for problems:</strong> Changes in litter tray habits (avoiding the tray, urinating outside it, straining) can indicate medical issues including urinary tract problems. The PDSA advises contacting your vet if litter habits change suddenly.</li></ol>
</div>
<!-- /wp:group -->""",
        4132: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: Setting Up a Positive Puppy Training Routine</h4>
<ol><li><strong>Step 1 — Gather your supplies:</strong> Start with high-value treats (small, soft pieces of cooked chicken or commercial training treats), a treat pouch, a standard lead, and optionally a clicker. The Kennel Club recommends beginning training from day one at home.</li><li><strong>Step 2 — Keep sessions short:</strong> Puppies have limited attention spans. Train for 3-5 minutes at a time, 3-4 times daily. End each session on a success. ABTC-registered trainers recommend short, positive sessions over long, repetitive ones.</li><li><strong>Step 3 — Start with name recognition and sit:</strong> Say your puppy's name and reward eye contact. For sit, hold a treat above the nose and move it slowly back over the head — the puppy's bottom naturally lowers. Mark and reward immediately.</li><li><strong>Step 4 — Begin recall training indoors:</strong> In a hallway or small room, call your puppy's name followed by "come." Reward generously every time they reach you. The Kennel Club recommends establishing reliable indoor recall before attempting outdoor recall with a long line.</li><li><strong>Step 5 — Track progress and seek help if needed:</strong> Note which cues your puppy responds to reliably. If you encounter persistent issues (biting, fear, or resource guarding), consult an ABTC-registered behaviourist or trainer rather than relying on online advice. The BVA advises against aversive training tools at any stage.</li></ol>
</div>
<!-- /wp:group -->""",
        5418: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: Fitting a Dog Harness Correctly</h4>
<ol><li><strong>Step 1 — Measure your dog:</strong> Measure the girth (ribcage circumference just behind the front legs) and neck circumference with a soft tape measure. Compare to the manufacturer's size chart — if between sizes, choose the larger size with room to adjust.</li><li><strong>Step 2 — Check the two-finger rule:</strong> Once fitted, you should be able to slide two fingers flat between the harness and your dog's body at every point. Too tight restricts breathing and movement; too loose allows escape or chafing.</li><li><strong>Step 3 — Verify strap position:</strong> The front strap of a Y-front harness should sit on the breastbone, not across the shoulders. Side straps should sit behind the front legs without rubbing the armpits. No strap should cross the throat.</li><li><strong>Step 4 — Test movement:</strong> Let your dog walk, sit, and lie down in the harness indoors. Watch for signs of restriction: shortened stride, reluctance to move, or the harness shifting to one side. Adjust straps if the harness rotates during movement.</li><li><strong>Step 5 — Recheck fit regularly:</strong> Weigh your dog monthly and recheck harness fit. Puppies may outgrow a harness in weeks. Adult dogs' weight fluctuates seasonally. The RSPCA advises checking walking equipment at every use for wear, especially stitching and clip mechanisms.</li></ol>
</div>
<!-- /wp:group -->""",
        7346: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: Establishing an Indoor Cat Feeding Routine</h4>
<ol><li><strong>Step 1 — Assess calorie needs:</strong> Indoor cats typically need fewer calories than outdoor cats due to lower activity levels. Consult your vet for a specific daily calorie target based on your cat's weight, age, and body condition score.</li><li><strong>Step 2 — Choose appropriate food:</strong> Look for complete cat food labelled for indoor cats, which typically has adjusted calorie density and added fibre for hairball management. Check that it meets FEDIAF nutritional guidelines for the appropriate life stage.</li><li><strong>Step 3 — Introduce puzzle feeding:</strong> Replace at least one meal with a puzzle feeder to simulate hunting behaviour and slow eating. iCatCare recommends puzzle feeders as standard enrichment for indoor cats. Start with easy puzzles and increase difficulty gradually.</li><li><strong>Step 4 — Ensure adequate hydration:</strong> Place multiple water stations around the home, away from food bowls and litter trays. Some cats prefer running water — a cat water fountain may increase intake. Wet food also contributes to daily fluid intake.</li><li><strong>Step 5 — Monitor weight monthly:</strong> Weigh your indoor cat monthly and record the results. Assess body condition by feeling ribs (should be easily felt without pressing) and checking for a visible waist from above. The PDSA reports that obesity is a leading health concern for UK indoor cats.</li></ol>
</div>
<!-- /wp:group -->""",
    }
    return guides.get(post_id)

# "At a Glance" blocks per post
def get_at_a_glance(post_id, title, cluster):
    """Generate At a Glance block specific to the post topic"""
    glances = {
        4286: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">Cat Scratching Posts: At a Glance</h4>
<ul><li><strong>Why cats scratch:</strong> Scratching is a natural behaviour for claw maintenance, territory marking (scent glands in paw pads), and stretching — it cannot and should not be stopped, only redirected.</li><li><strong>Minimum height:</strong> A scratching post should be tall enough for your cat to fully stretch while scratching. For most adult cats, this means at least 60-80cm of scratchable surface.</li><li><strong>Preferred material:</strong> Sisal rope or sisal fabric is preferred by most cats and recommended by Cats Protection. Avoid carpet, which can encourage scratching on other carpeted surfaces.</li><li><strong>Stability is non-negotiable:</strong> A post that wobbles or tips will be abandoned. Choose a heavy base or wall-mounted design. Test by pushing firmly from the top.</li><li><strong>Number needed:</strong> Cats Protection recommends at least one scratching post per cat, placed in locations where the cat spends time, particularly near sleeping areas and room entrances.</li></ul>
</div>
<!-- /wp:group -->""",
        4265: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">Cat GPS Trackers: At a Glance</h4>
<ul><li><strong>How they work:</strong> Cat GPS trackers use satellite positioning to report your cat's location to a smartphone app, typically updating every few seconds to minutes depending on the mode.</li><li><strong>Weight consideration:</strong> The tracker must be light enough for your cat to wear comfortably. Most cat-specific trackers weigh 25-35g. iCatCare advises that anything attached to a cat should not impede natural movement.</li><li><strong>Subscription costs:</strong> Most GPS trackers require a monthly subscription (typically £3-6/month) for mobile network connectivity in addition to the device purchase price.</li><li><strong>Battery life:</strong> Typical range is 2-7 days depending on tracking frequency and GPS mode. More frequent updates drain the battery faster.</li><li><strong>Collar compatibility:</strong> Always use with a breakaway safety collar. The tracker must be securely attached but the collar itself must release under pressure to prevent strangulation.</li></ul>
</div>
<!-- /wp:group -->""",
        4244: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">Cat Nail Clippers: At a Glance</h4>
<ul><li><strong>Why trim:</strong> Indoor cats' claws may not wear down naturally and can grow into the pad, causing pain. Regular trimming every 2-4 weeks prevents this — the PDSA recommends checking claw length as part of routine care.</li><li><strong>Clipper types:</strong> Scissor-style clippers suit most cat owners. Guillotine-style clippers are an alternative. Nail grinders are quieter but require acclimatisation.</li><li><strong>The quick:</strong> The pink blood vessel visible inside light-coloured nails. Cut 2mm before the quick. For dark nails, trim small amounts and stop when the cut surface shows a dark dot in the centre.</li><li><strong>Desensitisation first:</strong> Before trimming, handle your cat's paws regularly during calm moments. Cats Protection recommends gradually associating paw handling with treats over several days before attempting a trim.</li><li><strong>When to seek help:</strong> If your cat is extremely stressed by nail trimming, ask your vet or a registered veterinary nurse to demonstrate the technique or perform trims during routine visits.</li></ul>
</div>
<!-- /wp:group -->""",
        4195: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">Cat Toys for Indoor Cats: At a Glance</h4>
<ul><li><strong>Daily play is essential:</strong> Indoor cats depend entirely on their owners for exercise and hunting simulation. Cats Protection recommends at least two interactive play sessions daily.</li><li><strong>Session length:</strong> 10-15 minutes of active play per session is typically sufficient. Watch for signs your cat is tiring (lying down, panting, losing interest) and end on a catch-and-reward.</li><li><strong>Toy rotation:</strong> Cats lose interest in familiar toys. Rotate toys weekly — store some away and reintroduce them later. This maintains novelty without buying new toys constantly.</li><li><strong>End with food:</strong> Complete the prey sequence by offering a small treat or meal after play. This mimics the natural stalk-chase-catch-eat cycle and provides satisfying closure.</li><li><strong>Safety check:</strong> Inspect toys before each session. Remove any with loose strings, detached bells, or torn parts. Never leave string or ribbon toys unattended — string ingestion is a veterinary emergency.</li></ul>
</div>
<!-- /wp:group -->""",
        5418: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">Dog Harness Types: At a Glance</h4>
<ul><li><strong>Y-front design:</strong> The preferred harness shape according to canine biomechanics — the front strap sits on the sternum in a Y shape, leaving shoulders free for natural movement.</li><li><strong>Sizing priority:</strong> Girth measurement (ribcage behind front legs) is the most important sizing dimension. Neck and chest measurements are secondary. Always check the manufacturer's specific size chart.</li><li><strong>Front vs back clip:</strong> Front-clip harnesses help reduce pulling by redirecting momentum sideways. Back-clip harnesses offer comfort for calm walkers. Dual-clip options provide both.</li><li><strong>Fit check:</strong> Two flat fingers should fit between the harness and your dog's body at every strap point. No strap should sit across the throat or rub in the armpits.</li><li><strong>Regular inspection:</strong> The RSPCA advises checking harness stitching, clips, and straps before each walk. Replace any harness showing fraying, cracked clips, or worn buckles.</li></ul>
</div>
<!-- /wp:group -->""",
        4132: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">Puppy Training Essentials: At a Glance</h4>
<ul><li><strong>Start immediately:</strong> Training begins the day your puppy arrives home. The Kennel Club recommends starting with name recognition, sit, and basic handling from day one.</li><li><strong>Positive methods only:</strong> The BVA, Kennel Club, and RSPCA all endorse positive reinforcement training. Aversive tools and punishment-based methods are advised against by UK professional bodies.</li><li><strong>Session length:</strong> Keep training sessions to 3-5 minutes for puppies under 4 months, gradually increasing to 10 minutes. Multiple short sessions throughout the day are more effective than one long session.</li><li><strong>Socialisation window:</strong> The critical period is approximately 3-14 weeks. Positive exposure to varied people, sounds, surfaces, and environments during this window has lasting behavioural benefits.</li><li><strong>Professional help:</strong> For persistent issues, consult an ABTC-registered trainer or Clinical Animal Behaviourist. The ABTC maintains a public register of qualified professionals in the UK.</li></ul>
</div>
<!-- /wp:group -->""",
        7346: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">Indoor Cat Diet: At a Glance</h4>
<ul><li><strong>Calorie adjustment:</strong> Indoor cats typically need 10-20% fewer calories than outdoor cats of the same weight and age due to reduced activity levels.</li><li><strong>Obesity risk:</strong> The PDSA PAW Report consistently identifies obesity as a top health concern for UK cats, with indoor cats at higher risk due to limited exercise opportunities.</li><li><strong>Hydration matters:</strong> Indoor cats may drink less than outdoor cats. Multiple water stations, wet food, and cat water fountains can help maintain adequate hydration.</li><li><strong>Puzzle feeding:</strong> iCatCare recommends puzzle feeders for indoor cats as standard — they slow eating, provide mental stimulation, and mimic the natural foraging behaviour cats would perform outdoors.</li><li><strong>Vet-guided portions:</strong> Ask your vet for a specific daily calorie target rather than relying solely on food packaging guidelines, which are starting points and may overestimate needs for inactive indoor cats.</li></ul>
</div>
<!-- /wp:group -->""",
        4576: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">Multi-Pet Households: At a Glance</h4>
<ul><li><strong>Separate resources:</strong> Each pet needs their own food bowl, water bowl, bed, and (for cats) litter tray. The RSPCA advises against expecting dogs and cats to share resources.</li><li><strong>Cat-safe zones:</strong> iCatCare and Cats Protection recommend that cats in multi-pet homes have access to elevated, dog-free escape routes and resting areas at all times.</li><li><strong>Introduction timeline:</strong> Introducing a new pet to an existing one should take days to weeks, not hours. Scent swapping, barrier meetings, and supervised access are the RSPCA-recommended stages.</li><li><strong>Feeding separation:</strong> Feed dogs and cats in separate rooms or at different heights. Cat food is too high in protein and fat for dogs; dog food does not meet cats' taurine requirements.</li><li><strong>Veterinary considerations:</strong> Each pet maintains their own vaccination, parasite treatment, and health check schedule. Some flea treatments for dogs are toxic to cats — always use species-specific products.</li></ul>
</div>
<!-- /wp:group -->""",
    }
    return glances.get(post_id)


def build_research_sources_block(cluster):
    """Build the Research Sources and Standards block"""
    refs = UK_REFS.get(cluster, UK_REFS["Pet Care"])
    return f"""<!-- wp:group {{"style":{{"border":{{"width":"1px","radius":"8px"}},"spacing":{{"padding":{{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}}}}},"borderColor":"","backgroundColor":""}} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#f0f9ff;border-color:#bae6fd">
<h4 class="wp-block-heading">Research Sources and Standards</h4>
<p>{refs['research_sources']}</p>
</div>
<!-- /wp:group -->"""

def build_why_sources_block(cluster):
    """Build the Why We Reference Sources block"""
    refs = UK_REFS.get(cluster, UK_REFS["Pet Care"])
    return f"""<!-- wp:group {{"style":{{"border":{{"width":"1px","radius":"8px"}},"spacing":{{"padding":{{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}}}}},"borderColor":"","backgroundColor":""}} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#f0f9ff;border-color:#bae6fd">
<h4 class="wp-block-heading">Why We Reference Sources</h4>
<p>{refs['why_sources']}</p>
</div>
<!-- /wp:group -->"""

def build_glossary_block(cluster):
    """Build the Key Terms glossary block"""
    terms = GLOSSARY_TERMS.get(cluster, GLOSSARY_TERMS["Pet Care"])
    items = "".join([f'<li><strong>{t}:</strong> {d}</li>' for t, d in terms])
    return f"""<!-- wp:group {{"style":{{"border":{{"width":"1px","radius":"8px"}},"spacing":{{"padding":{{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}}}}},"borderColor":"","backgroundColor":""}} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#f8fafc;border-color:#e2e8f0">
<h4 class="wp-block-heading">Key Terms</h4>
<ul>{items}</ul>
</div>
<!-- /wp:group -->"""

# Generic practical guides for non-priority posts
GENERIC_PRACTICAL = {
    "Cat Supplies": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: Evaluating Cat Supplies</h4>
<ol><li><strong>Step 1 — Check species appropriateness:</strong> Confirm the product is designed specifically for cats, not adapted from a dog product. Cats have unique needs — their smaller size, flexibility, and grooming behaviour require purpose-designed equipment (iCatCare guidance).</li><li><strong>Step 2 — Assess material safety:</strong> Check for non-toxic materials, secure fastenings, and no small detachable parts that could be swallowed. Avoid products with strong chemical odours, which may deter cats or indicate unsafe coatings.</li><li><strong>Step 3 — Match to your cat's behaviour:</strong> Observe whether your cat prefers horizontal or vertical scratching, open or enclosed sleeping spaces, and ground-level or elevated positions. Choose supplies that match these natural preferences rather than forcing change.</li><li><strong>Step 4 — Consider multi-cat households:</strong> If you have multiple cats, Cats Protection recommends one of each key resource per cat plus one extra (litter trays, feeding stations, scratching posts, beds) to prevent resource guarding.</li><li><strong>Step 5 — Review and replace regularly:</strong> Inspect all cat supplies monthly for wear, damage, and hygiene. Replace items with frayed rope, cracked plastic, or persistent odour. Clean fabric items at 30-40°C and replace beds when filling loses support.</li></ol>
</div>
<!-- /wp:group -->""",
    "Cat Toys": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: Creating an Effective Cat Play Routine</h4>
<ol><li><strong>Step 1 — Schedule daily play sessions:</strong> Aim for at least two interactive play sessions daily, each lasting 10-15 minutes. Schedule sessions before meals to mimic the natural hunt-catch-eat sequence recommended by iCatCare.</li><li><strong>Step 2 — Mimic prey movement:</strong> Move wand toys away from your cat (not toward them), using erratic, stop-start movements. Drag toys along the floor, flutter them in the air, and hide them behind furniture to simulate different prey types.</li><li><strong>Step 3 — Let your cat catch the toy:</strong> Every session should include successful catches. A cat that never catches the "prey" becomes frustrated. Allow a catch every few minutes and let your cat hold and kick the toy.</li><li><strong>Step 4 — End with food:</strong> After the final catch, offer a small meal or treat. This completes the prey sequence (stalk-chase-catch-eat) and signals that playtime is over, helping your cat settle afterward.</li><li><strong>Step 5 — Rotate toys weekly:</strong> Store most toys in a sealed bag and rotate them every 5-7 days. Cats lose interest in familiar objects but respond to "rediscovered" toys as if new. Always store wand toys out of reach between sessions to prevent unsupervised string play.</li></ol>
</div>
<!-- /wp:group -->""",
    "Indoor Cats": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: Setting Up an Indoor Cat Environment</h4>
<ol><li><strong>Step 1 — Provide vertical space:</strong> Install cat shelves, a tall cat tree, or window perches at different heights. iCatCare identifies vertical space as one of the most important environmental needs for indoor cats, providing exercise, territory, and security.</li><li><strong>Step 2 — Create resource stations:</strong> Set up separate areas for food, water, litter, scratching, and resting. In multi-cat homes, provide one of each resource per cat plus one extra in different locations (Cats Protection guideline).</li><li><strong>Step 3 — Offer window enrichment:</strong> Position a perch or shelf near a window with a view of birds or outdoor activity. Consider a bird feeder outside the window to provide visual stimulation — a key enrichment for indoor cats.</li><li><strong>Step 4 — Establish play and feeding routines:</strong> Schedule interactive play sessions at consistent times (at least twice daily) and introduce puzzle feeders for at least one meal. Routine and mental stimulation help prevent the boredom-related behaviour problems common in indoor cats.</li><li><strong>Step 5 — Provide hiding and retreat spaces:</strong> Ensure your cat has access to enclosed spaces (boxes, igloo beds, covered perches) where they can retreat and feel safe. The RSPCA emphasises that cats need the ability to hide as part of their welfare needs, especially in busy households.</li></ol>
</div>
<!-- /wp:group -->""",
    "Dog Harnesses": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: Choosing and Fitting a Dog Harness</h4>
<ol><li><strong>Step 1 — Measure accurately:</strong> Use a soft tape measure to record your dog's girth (ribcage behind front legs), neck circumference, and chest width. Measure while your dog is standing naturally. These three measurements determine the correct harness size.</li><li><strong>Step 2 — Choose the right type:</strong> For dogs that pull: consider a front-clip or dual-clip harness. For calm walkers: a back-clip harness provides comfort. The RSPCA advises that harnesses should never restrict natural shoulder movement.</li><li><strong>Step 3 — Apply the two-finger test:</strong> After fitting, check that you can slide two flat fingers between every strap and your dog's body. No strap should press into the throat, restrict the shoulders, or chafe in the armpit area.</li><li><strong>Step 4 — Introduce gradually:</strong> Let your dog wear the harness indoors for short periods with treats before going on walks. The Kennel Club recommends positive association — pair the harness with rewards so your dog is comfortable before adding lead pressure.</li><li><strong>Step 5 — Inspect before every walk:</strong> Check all stitching, buckles, and clips for wear. Ensure no straps have twisted or loosened since the last use. The RSPCA advises replacing any harness with cracked clips, frayed stitching, or worn padding.</li></ol>
</div>
<!-- /wp:group -->""",
    "Training Supplies": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: Building a Positive Training Toolkit</h4>
<ol><li><strong>Step 1 — Start with treats:</strong> Choose small (pea-sized), soft training treats that your dog can eat quickly without losing focus. For high-distraction environments, use high-value treats like cooked chicken or cheese. The Kennel Club emphasises that reward value should match task difficulty.</li><li><strong>Step 2 — Add a marker:</strong> Choose a clicker or a consistent marker word (e.g., "yes"). The marker bridges the gap between the desired behaviour and the treat delivery, improving training precision. Practice marker timing before training sessions.</li><li><strong>Step 3 — Select appropriate leads:</strong> A standard 1.5-2m lead for everyday walks and a 5-10m long line for recall training. Retractable leads are not recommended for training by the Kennel Club as they provide inconsistent feedback.</li><li><strong>Step 4 — Avoid aversive tools:</strong> The BVA, Kennel Club, and RSPCA all advise against choke chains, prong collars, shock collars, and spray collars. These tools cause pain or fear and can worsen behavioural problems. Focus on reward-based equipment only.</li><li><strong>Step 5 — Know when to seek professional help:</strong> If progress stalls or behavioural issues arise (aggression, severe anxiety, resource guarding), consult an ABTC-registered Clinical Animal Behaviourist. The ABTC register at abtc.org.uk lists qualified professionals by location across the UK.</li></ol>
</div>
<!-- /wp:group -->""",
    "Pet Care": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: Establishing a Pet Care Routine</h4>
<ol><li><strong>Step 1 — Register with a vet:</strong> Register your pet with a local veterinary practice within the first week of ownership. Book an initial health check to establish a baseline and confirm vaccination and microchip status. The BVA recommends annual health checks for all pets.</li><li><strong>Step 2 — Set up a feeding routine:</strong> Feed species-appropriate complete food at consistent times daily. Dogs typically need 2 meals per day; cats may prefer little-and-often feeding. Follow your vet's calorie guidance rather than packaging alone.</li><li><strong>Step 3 — Maintain parasite prevention:</strong> Follow your vet's recommended schedule for flea, tick, and worm treatments. Treatment intervals vary by product and species. Never use dog flea treatments on cats — some ingredients are toxic to cats (RSPCA warning).</li><li><strong>Step 4 — Meet species-specific needs:</strong> Dogs need daily walks and social interaction. Cats need scratching posts, vertical space, and play sessions. All pets need a suitable environment, diet, companionship, and healthcare — the five welfare needs under the Animal Welfare Act 2006.</li><li><strong>Step 5 — Schedule preventive care:</strong> Annual vet check-ups, dental assessments, and weight monitoring help catch problems early. Senior pets (dogs 7+, cats 11+) benefit from twice-yearly check-ups. Keep a simple log of vaccinations, treatments, and any health changes to share with your vet.</li></ol>
</div>
<!-- /wp:group -->""",
}

# Generic At a Glance for non-priority posts
GENERIC_AT_A_GLANCE = {
    "Cat Supplies": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">At a Glance</h4>
<ul><li><strong>Essential supplies:</strong> At minimum, cats need a litter tray, scratching post, food and water bowls, a bed, and safe toys — Cats Protection lists these as the core requirements for any cat home.</li><li><strong>Multi-cat rule:</strong> In households with more than one cat, provide one of each key resource per cat plus one extra (litter trays, feeding stations, scratching posts) to prevent competition and stress.</li><li><strong>Safety first:</strong> Choose supplies with no small detachable parts, non-toxic materials, and (for collars) breakaway safety mechanisms. iCatCare advises checking all cat products for species-appropriate design.</li><li><strong>Replace on wear:</strong> Inspect supplies monthly. Replace scratching posts when sisal is shredded through, litter trays when scratched and stained beyond cleaning, and beds when filling loses support.</li></ul>
</div>
<!-- /wp:group -->""",
    "Cat Toys": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">At a Glance</h4>
<ul><li><strong>Play is a welfare need:</strong> Cats Protection and iCatCare identify interactive play as essential for cat welfare, particularly for indoor cats who cannot hunt naturally.</li><li><strong>The prey sequence:</strong> Effective play mimics stalk-chase-pounce-catch-eat. End sessions with a catch and a food reward to complete the cycle and prevent frustration.</li><li><strong>Safety essentials:</strong> Never leave string, ribbon, or wand toys unattended — string ingestion can cause life-threatening intestinal blockages. Inspect toys before each session for loose parts.</li><li><strong>Rotation maintains interest:</strong> Store unused toys in a sealed bag and swap them every 5-7 days. Cats respond to familiar toys as if new after a break period.</li></ul>
</div>
<!-- /wp:group -->""",
    "Indoor Cats": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">At a Glance</h4>
<ul><li><strong>Environmental enrichment is essential:</strong> iCatCare identifies five pillars of a healthy feline environment: safe space, multiple resources, play and hunting opportunities, positive human interaction, and respect for the cat's sense of smell.</li><li><strong>Vertical space:</strong> Cat trees, shelves, and perches provide territory, exercise, and security. Indoor cats with access to vertical space show fewer stress-related behaviours (Cats Protection).</li><li><strong>Weight management:</strong> Indoor cats are at higher risk of obesity due to reduced activity. Monthly weigh-ins and vet-guided portion control are important preventive measures (PDSA PAW Report).</li><li><strong>Litter tray standards:</strong> One per cat plus one extra, placed in quiet locations away from food and water. Clean daily and fully replace litter weekly (iCatCare).</li></ul>
</div>
<!-- /wp:group -->""",
    "Dog Harnesses": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">At a Glance</h4>
<ul><li><strong>Why harnesses over collars:</strong> Harnesses distribute lead pressure across the chest and ribcage rather than concentrating it on the neck, reducing the risk of tracheal damage — particularly important for dogs that pull (BVA guidance).</li><li><strong>Key measurement:</strong> Girth (ribcage circumference just behind the front legs) is the primary sizing measurement. Always check the manufacturer's size chart rather than assuming S/M/L will fit.</li><li><strong>Two-finger fit rule:</strong> After fitting, you should be able to slide two flat fingers between every strap and your dog's body. This ensures comfort without risk of escape.</li><li><strong>Educational note:</strong> A harness is a management tool, not a training solution on its own. Pair harness use with positive reinforcement training for loose-lead walking (Kennel Club recommendation).</li></ul>
</div>
<!-- /wp:group -->""",
    "Training Supplies": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">At a Glance</h4>
<ul><li><strong>Positive reinforcement standard:</strong> The Kennel Club, BVA, and RSPCA all endorse reward-based training as the most effective and welfare-friendly approach for dogs of all ages.</li><li><strong>Core equipment:</strong> High-value training treats, a treat pouch, a clicker or marker word, a standard lead (1.5-2m), and a long line (5-10m) for recall training cover most training needs.</li><li><strong>Aversive tools to avoid:</strong> Choke chains, prong collars, shock collars, and spray collars are advised against by the BVA and RSPCA. These tools can cause physical pain and worsen behavioural problems.</li><li><strong>Professional guidance:</strong> For persistent training challenges, the ABTC maintains a register of qualified trainers and Clinical Animal Behaviourists at abtc.org.uk.</li></ul>
</div>
<!-- /wp:group -->""",
    "Pet Care": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">At a Glance</h4>
<ul><li><strong>Five welfare needs:</strong> Under the UK Animal Welfare Act 2006, all pet owners must provide: a suitable environment, a suitable diet, the ability to exhibit normal behaviours, appropriate companionship, and protection from pain, suffering, injury, and disease.</li><li><strong>Species-specific care:</strong> Dogs and cats have fundamentally different needs. Dog flea treatments can be toxic to cats. Cat food does not meet dog nutritional requirements. Always use species-appropriate products.</li><li><strong>Preventive care:</strong> Annual vet checks, up-to-date vaccinations, regular parasite treatment, and dental care form the foundation of pet health (BVA recommendation).</li><li><strong>Microchipping:</strong> Compulsory for dogs in England and, from June 2024, for cats. Ensure your contact details are kept up to date on the microchip database.</li></ul>
</div>
<!-- /wp:group -->""",
}

# Generic comparison tables for non-priority posts
GENERIC_COMPARISON = {
    "Cat Supplies": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Cat Supply Material Types Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Feature</th><th>Stainless Steel</th><th>Ceramic</th><th>Plastic (BPA-Free)</th></tr></thead><tbody><tr><td>Hygiene</td><td>Non-porous; bacteria-resistant; easy to sanitise</td><td>Non-porous when glazed; chip-resistant glazes safest</td><td>Micro-scratches harbour bacteria; linked to feline chin acne</td></tr><tr><td>Durability</td><td>Very durable; dent-resistant</td><td>Heavy but can chip or crack if dropped</td><td>Lightweight; scratches easily; may retain odours</td></tr><tr><td>Cat Acceptance</td><td>Generally well-accepted; low-profile bowls suit whisker-sensitive cats</td><td>Heavy and stable; less likely to slide</td><td>Some cats dislike static charge or chemical smell</td></tr><tr><td>Dishwasher Safe</td><td>Yes</td><td>Usually; check manufacturer label</td><td>May warp at high temperatures</td></tr><tr><td>Veterinary Recommendation</td><td>Preferred by most UK vets for food and water</td><td>Acceptable; popular for water fountains</td><td>Travel and temporary use only; not recommended for daily feeding</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
    "Cat Toys": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Cat Toy Safety Considerations Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Feature</th><th>Supervised Toys (Wands, Strings)</th><th>Semi-Supervised (Puzzle Feeders)</th><th>Unsupervised (Balls, Mice)</th></tr></thead><tbody><tr><td>Supervision Needed</td><td>Must be present throughout; store away after use</td><td>Initial supervision; can be left once cat is familiar</td><td>Safe to leave out; check regularly for damage</td></tr><tr><td>Choking Risk</td><td>String/ribbon ingestion is a veterinary emergency</td><td>Low if no small removable parts</td><td>Check that bells and eyes are securely attached</td></tr><tr><td>Engagement Level</td><td>Very high; interactive bonding with owner</td><td>High; food motivation drives engagement</td><td>Variable; novelty fades without rotation</td></tr><tr><td>Wear Indicators</td><td>Fraying string, loose feathers, bent wire</td><td>Cracked plastic, jammed mechanisms</td><td>Torn fabric, loose stuffing, detached small parts</td></tr><tr><td>Replacement Frequency</td><td>Replace when string frays or attachments loosen</td><td>Replace when mechanisms break or cannot be cleaned</td><td>Replace when damaged or heavily soiled</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
    "Indoor Cats": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Indoor Cat Environmental Needs Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Need</th><th>Minimum Provision</th><th>Enhanced Provision</th><th>Why It Matters</th></tr></thead><tbody><tr><td>Vertical Space</td><td>One cat tree or set of shelves</td><td>Multiple levels across rooms; walkway shelves</td><td>Vertical territory reduces stress and increases exercise (iCatCare)</td></tr><tr><td>Scratching</td><td>One scratching post per cat</td><td>Variety of surfaces (sisal, cardboard) in multiple locations</td><td>Scratching is a territorial and claw-maintenance need; cannot be eliminated</td></tr><tr><td>Hiding Spaces</td><td>One enclosed resting spot</td><td>Multiple hiding options at different heights</td><td>Ability to hide is an RSPCA-identified welfare need for all cats</td></tr><tr><td>Play/Hunting</td><td>Two interactive play sessions daily</td><td>Puzzle feeders, automated toys, and window enrichment</td><td>Indoor cats cannot hunt; play is their only outlet for predatory instincts</td></tr><tr><td>Outdoor Access</td><td>Window view of outdoor activity</td><td>Catio (enclosed outdoor space) or cat-proof garden</td><td>Visual or physical outdoor access improves welfare without safety risks</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
    "Dog Harnesses": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Dog Harness Fit Indicators Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Indicator</th><th>Good Fit</th><th>Too Tight</th><th>Too Loose</th></tr></thead><tbody><tr><td>Two-Finger Test</td><td>Two flat fingers slide easily under every strap</td><td>Cannot fit fingers; straps press into skin or fur</td><td>More than three fingers fit; straps lift away from body</td></tr><tr><td>Shoulder Movement</td><td>Front legs move freely without strap interference</td><td>Shortened stride; reluctance to walk or trot</td><td>Harness shifts forward over shoulders during movement</td></tr><tr><td>Chest Strap Position</td><td>Sits on breastbone in Y shape; clear of throat</td><td>Presses against windpipe or restricts breathing</td><td>Slides to one side; lead attachment off-centre</td></tr><tr><td>Side Straps</td><td>Behind front legs without rubbing armpits</td><td>Chafing marks or fur loss in armpit area</td><td>Straps slide down legs; dog can step out of harness</td></tr><tr><td>Overall Position</td><td>Stays centred on body during walking, sitting, and lying down</td><td>Dog resists putting harness on; scratches at straps</td><td>Rotates during movement; D-ring shifts off back or chest centre</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
    "Training Supplies": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Training Lead Types Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Feature</th><th>Standard Lead (1.5-2m)</th><th>Long Line (5-15m)</th><th>Retractable Lead</th></tr></thead><tbody><tr><td>Primary Use</td><td>Everyday walks and close-quarters training</td><td>Recall training, distance work, and controlled freedom</td><td>Casual walking in open spaces</td></tr><tr><td>Handler Control</td><td>High; short length provides direct communication</td><td>Moderate; requires line management skills</td><td>Low; inconsistent tension gives poor feedback to dog</td></tr><tr><td>Training Value</td><td>Foundation tool for loose-lead walking</td><td>Essential for safe recall practice before off-lead</td><td>Not recommended for training (Kennel Club guidance)</td></tr><tr><td>Safety</td><td>Low tangle risk; reliable clip essential</td><td>Wear gloves to prevent rope burns; avoid wrapping around fingers</td><td>Mechanism can fail; thin cord can cause friction injuries</td></tr><tr><td>UK Professional View</td><td>Standard recommendation for all dog owners</td><td>Recommended by trainers for recall practice</td><td>The Kennel Club and many ABTC trainers advise against for training</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
    "Pet Care": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Dog vs Cat Care Needs Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Care Area</th><th>Dogs</th><th>Cats</th><th>Key Difference</th></tr></thead><tbody><tr><td>Exercise</td><td>Daily walks: 30-60+ minutes twice daily (breed-dependent)</td><td>Indoor play sessions: 10-15 minutes twice daily</td><td>Dogs need outdoor exercise; cats can meet exercise needs indoors with enrichment</td></tr><tr><td>Feeding</td><td>2 meals daily at set times; portion control important</td><td>Little-and-often preferred; some cats graze-feed</td><td>Never swap food — cat food is too high in protein/fat for dogs; dog food lacks taurine for cats</td></tr><tr><td>Dental Care</td><td>Brush 2-3 times weekly; dental chews supplement</td><td>Brush if cat tolerates; dental diet may help</td><td>Both species: 80%+ show dental disease by age 3 (BVA data)</td></tr><tr><td>Parasite Treatment</td><td>Monthly or quarterly per vet advice</td><td>Monthly or quarterly; cat-specific products only</td><td>Some dog flea treatments contain permethrin, which is toxic to cats (RSPCA warning)</td></tr><tr><td>Vet Check-ups</td><td>Annually; twice yearly for dogs 7+</td><td>Annually; twice yearly for cats 11+</td><td>Cats often hide illness signs; regular vet checks are especially important (iCatCare)</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
}


# ── Main processing ────────────────────────────────────────────────────

def find_insert_position(content):
    """Find position to insert new blocks — before trust footer or at end"""
    # Look for common footer patterns
    footer_patterns = [
        '<!-- wp:group {"className":"trust-footer"',
        "Our Research Standards",
        "Why PetHub Online Exists",
        "Editorial Standards",
        "Our Editorial Process",
    ]

    best_pos = len(content)
    for pattern in footer_patterns:
        idx = content.rfind(pattern)
        if idx != -1 and idx < best_pos:
            # Find the start of the block containing this pattern
            # Look backwards for the nearest wp:group or wp:separator
            block_start = content.rfind("<!-- wp:", 0, idx)
            if block_start != -1 and block_start < best_pos:
                best_pos = block_start

    return best_pos

def determine_needed_blocks(post_info):
    """Determine which blocks are needed based on scores"""
    needed = []
    cit = post_info["citation"]
    moat = post_info["moat"]
    cluster = post_info["cluster"]
    pid = post_info["id"]

    ref_quality = float(cit.get("reference_quality", 100))
    comp_useful = float(cit.get("comparison_usefulness", 100))
    prac_spec = float(cit.get("practical_specificity", 100))
    extractability = float(cit.get("extractability", 100))
    trust_depth = float(cit.get("trust_depth", 100))

    glossary_moat = float(moat.get("glossary_moat", 100))
    trust_moat = float(moat.get("trust_moat", 100))
    citation_moat = float(moat.get("citation_moat", 100))

    # Reference quality < 80 → add Research Sources
    if ref_quality < 80:
        needed.append("research_sources")

    # Comparison usefulness < 85 → add comparison table
    if comp_useful < 85:
        needed.append("comparison_table")

    # Practical specificity < 80 → add practical guide
    if prac_spec < 80:
        needed.append("practical_guide")

    # Extractability < 90 → add At a Glance
    if extractability < 90:
        needed.append("at_a_glance")

    # Trust depth < 95 → add Why We Reference Sources
    if trust_depth < 95:
        needed.append("why_sources")

    # Glossary moat < 80 → add Key Terms
    if glossary_moat < 80:
        needed.append("glossary")

    # Trust moat < 70 → add Why We Reference Sources (if not already added)
    if trust_moat < 70 and "why_sources" not in needed:
        needed.append("why_sources")

    # Citation moat < 75 → add Research Sources (if not already added)
    if citation_moat < 75 and "research_sources" not in needed:
        needed.append("research_sources")

    return needed

def process_post(post_info):
    """Process a single post: fetch, enrich, update"""
    pid = post_info["id"]
    title = post_info["title"]
    cluster = post_info["cluster"]

    print(f"\n{'='*60}")
    print(f"Processing: [{pid}] {title} ({cluster})")

    # Fetch current content
    content = fetch_post_content(pid)
    if content is None:
        print(f"  ERROR: Could not fetch post {pid}")
        return {"status": "fetch_error", "blocks_added": 0}

    needed = determine_needed_blocks(post_info)
    if not needed:
        print(f"  All scores already high — no enrichment needed")
        return {"status": "already_optimal", "blocks_added": 0}

    print(f"  Needed blocks: {needed}")

    new_blocks = []
    blocks_added_list = []
    comparison_added = 0
    trust_refs_added = 0
    glossary_added = 0
    practical_enhanced = 0
    extractability_enhanced = 0

    # Generate each needed block, checking for duplicates
    if "research_sources" in needed:
        if not has_block(content, "Research Sources and Standards"):
            block = build_research_sources_block(cluster)
            new_blocks.append(block)
            blocks_added_list.append("research_sources")
            trust_refs_added += 1
            print(f"  + Research Sources and Standards")
        else:
            print(f"  ~ Research Sources already exists, skipping")

    if "comparison_table" in needed:
        # Check for existing comparison tables
        if not has_block(content, "Compared") and not has_block(content, "wp-block-table is-style-stripes"):
            # Try post-specific table first, then generic
            table = get_comparison_table(pid, title, cluster)
            if table is None:
                table = GENERIC_COMPARISON.get(cluster)
            if table:
                new_blocks.append(table)
                blocks_added_list.append("comparison_table")
                comparison_added += 1
                print(f"  + Comparison Table")
        else:
            print(f"  ~ Comparison table already exists, skipping")

    if "practical_guide" in needed:
        if not has_block(content, "Step-by-Step"):
            guide = get_practical_guide(pid, title, cluster)
            if guide is None:
                guide = GENERIC_PRACTICAL.get(cluster)
            if guide:
                new_blocks.append(guide)
                blocks_added_list.append("practical_guide")
                practical_enhanced += 1
                print(f"  + Practical Guide")
        else:
            print(f"  ~ Practical guide already exists, skipping")

    if "at_a_glance" in needed:
        if not has_block(content, "At a Glance"):
            glance = get_at_a_glance(pid, title, cluster)
            if glance is None:
                glance = GENERIC_AT_A_GLANCE.get(cluster)
            if glance:
                new_blocks.append(glance)
                blocks_added_list.append("at_a_glance")
                extractability_enhanced += 1
                print(f"  + At a Glance")
        else:
            print(f"  ~ At a Glance already exists, skipping")

    if "why_sources" in needed:
        if not has_block(content, "Why We Reference Sources"):
            block = build_why_sources_block(cluster)
            new_blocks.append(block)
            blocks_added_list.append("why_sources")
            trust_refs_added += 1
            print(f"  + Why We Reference Sources")
        else:
            print(f"  ~ Why We Reference Sources already exists, skipping")

    if "glossary" in needed:
        if not has_block(content, "Key Terms"):
            block = build_glossary_block(cluster)
            new_blocks.append(block)
            blocks_added_list.append("glossary")
            glossary_added += 1
            print(f"  + Key Terms Glossary")
        else:
            print(f"  ~ Key Terms already exists, skipping")

    if not new_blocks:
        print(f"  All needed blocks already present in content")
        return {
            "status": "blocks_already_present",
            "blocks_added": 0,
            "blocks_added_list": [],
            "comparison_added": 0,
            "trust_refs_added": 0,
            "glossary_added": 0,
            "practical_enhanced": 0,
            "extractability_enhanced": 0,
        }

    # Find insert position and build updated content
    insert_pos = find_insert_position(content)
    enrichment_html = "\n\n".join(new_blocks)

    updated_content = content[:insert_pos] + "\n\n" + enrichment_html + "\n\n" + content[insert_pos:]

    # PUT back to WordPress
    print(f"  Updating post {pid} with {len(new_blocks)} new blocks...")
    success = wp_put(pid, updated_content)

    if success:
        print(f"  SUCCESS: Updated post {pid}")
        status = "updated"
    else:
        print(f"  FAILED: Could not update post {pid}")
        status = "update_failed"

    # Rate limiting — be respectful
    time.sleep(2)

    return {
        "status": status,
        "blocks_added": len(new_blocks),
        "blocks_added_list": blocks_added_list,
        "comparison_added": comparison_added,
        "trust_refs_added": trust_refs_added,
        "glossary_added": glossary_added,
        "practical_enhanced": practical_enhanced,
        "extractability_enhanced": extractability_enhanced,
    }


# ── Execute ────────────────────────────────────────────────────────────

# Priority order: posts with highest citation_preference_score first within each cluster
# Prioritise posts that have tailored comparison tables and guides
PRIORITY_IDS = [4286, 4314, 4293, 4265, 4244, 4195, 4181, 4132, 4118, 5418, 4027, 7346, 4576]

# Sort remaining by citation preference score descending
remaining_ids = []
for pid, info in target_posts.items():
    if pid not in PRIORITY_IDS:
        score = float(info["citation"]["citation_preference_score"])
        remaining_ids.append((pid, score))
remaining_ids.sort(key=lambda x: -x[1])

processing_order = PRIORITY_IDS + [pid for pid, _ in remaining_ids]

results = []
total_blocks = 0
total_comparisons = 0
total_trust_refs = 0
total_glossary = 0
total_practical = 0
total_extractability = 0

print(f"\n{'#'*60}")
print(f"Phase 10BU/10BV/10BY Cat & Misc Cluster Enrichment")
print(f"Total posts to process: {len(processing_order)}")
print(f"{'#'*60}")

for pid in processing_order:
    if pid not in target_posts:
        print(f"\nWARNING: Post {pid} not found in target clusters, skipping")
        continue

    try:
        info = target_posts[pid]
        result = process_post(info)
        time.sleep(3)

        total_blocks += result.get("blocks_added", 0)
        total_comparisons += result.get("comparison_added", 0)
        total_trust_refs += result.get("trust_refs_added", 0)
        total_glossary += result.get("glossary_added", 0)
        total_practical += result.get("practical_enhanced", 0)
        total_extractability += result.get("extractability_enhanced", 0)

        results.append({
            "id": pid,
            "title": info["title"],
            "cluster": info["cluster"],
            "blocks_added": "|".join(result.get("blocks_added_list", [])),
            "comparison_tables_added": result.get("comparison_added", 0),
            "trust_refs_added": result.get("trust_refs_added", 0),
            "glossary_added": result.get("glossary_added", 0),
            "practical_enhanced": result.get("practical_enhanced", 0),
            "extractability_enhanced": result.get("extractability_enhanced", 0),
            "status": result["status"],
        })
    except Exception as e:
        print(f"\nERROR processing post {pid}: {e}")
        results.append({
            "id": pid, "title": target_posts[pid]["title"],
            "cluster": target_posts[pid]["cluster"],
            "blocks_added": "", "comparison_tables_added": 0,
            "trust_refs_added": 0, "glossary_added": 0,
            "practical_enhanced": 0, "extractability_enhanced": 0,
            "status": f"error: {str(e)[:100]}",
        })

# ── Write output CSV ──────────────────────────────────────────────────
output_csv = os.path.join(OUTPUT_DIR, "citation_moat_trust_cat_misc_clusters.csv")
with open(output_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "id", "title", "cluster", "blocks_added", "comparison_tables_added",
        "trust_refs_added", "glossary_added", "practical_enhanced",
        "extractability_enhanced", "status"
    ])
    writer.writeheader()
    for row in results:
        writer.writerow(row)

print(f"\n{'#'*60}")
print(f"ENRICHMENT COMPLETE")
print(f"{'#'*60}")
print(f"Posts processed:     {len(results)}")
print(f"Total blocks added:  {total_blocks}")
print(f"Comparison tables:   {total_comparisons}")
print(f"Trust references:    {total_trust_refs}")
print(f"Glossaries:          {total_glossary}")
print(f"Practical guides:    {total_practical}")
print(f"At a Glance blocks:  {total_extractability}")
print(f"Output CSV:          {output_csv}")
