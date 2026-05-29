#!/usr/bin/env python3
"""
Phase 10AV + 10AW + 10AY: Comparison Tables, Decision Support, Trust Depth
Clusters: Cat Supplies, Cat Toys, Dog Grooming, Indoor Cats, Uncategorized
"""

import subprocess, json, time, csv, os, sys, re, tempfile, html

API_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ay_data"
LOG_FILE = os.path.join(DATA_DIR, "multi_cluster_dominance.csv")
DELAY = 2

# ── Cluster definitions ──
CLUSTERS = {
    "Cat Supplies": [4335, 4321, 4314, 4209, 4202, 696, 7175],
    "Cat Toys": [5033, 5032, 4409, 4408, 4407, 4406, 4307, 4300, 4286, 4188, 4181, 4174, 7177],
    "Dog Grooming": [5464, 4563, 4251, 4244, 4237, 4230, 4078, 4071, 4064, 4057],
    "Indoor Cats": [5519, 5296, 7342, 7343, 7344, 7345, 7346, 7167],
    "Uncategorized": [6048, 6044, 4786, 4785, 4573, 4570, 4576, 4574, 4571, 4328, 4293, 4223, 4153, 8172, 8171],
}

# Posts that specifically need comparison tables
COMPARISON_TABLE_IDS = {7177, 8172, 8171}

# Build reverse lookup
POST_CLUSTER = {}
for cluster, ids in CLUSTERS.items():
    for pid in ids:
        POST_CLUSTER[pid] = cluster

ALL_IDS = []
for ids in CLUSTERS.values():
    ALL_IDS.extend(ids)

# ── API helpers ──
def api_get(endpoint):
    url = f"{API_BASE}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    return json.loads(result.stdout)

def api_update(post_id, data):
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(data, tmp)
    tmp.close()
    url = f"{API_BASE}/posts/{post_id}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, "-d", f"@{tmp.name}",
         "-H", "Content-Type: application/json", "-X", "POST", url],
        capture_output=True, text=True, timeout=60
    )
    os.unlink(tmp.name)
    resp = json.loads(result.stdout)
    if "id" in resp:
        return True
    print(f"  ERROR updating {post_id}: {result.stdout[:300]}")
    return False

# ── Content generation: Comparison tables ──
def generate_comparison_table(title, content_raw, cluster):
    """Generate an educational comparison table based on post topic."""
    title_lower = title.lower()

    # Post 7177: Cat Toy Terminology
    if "toy terminology" in title_lower or "play types" in title_lower:
        return """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Play Type</th><th>Best For</th><th>Considerations</th><th>Suitability</th></tr></thead><tbody><tr><td>Wand/Teaser Play</td><td>Active cats who enjoy chasing and pouncing</td><td>Requires owner participation; store safely when not in use to prevent string ingestion</td><td>All ages; adjust speed for kittens and seniors</td></tr><tr><td>Self-Play (Balls/Rollers)</td><td>Independent cats and busy households</td><td>Choose size appropriate to cat; check for loose parts regularly</td><td>Good for solo play; less suitable for very sedentary cats</td></tr><tr><td>Puzzle/Food Dispensing</td><td>Intelligent cats needing mental stimulation</td><td>Start with easy levels; too difficult puzzles cause frustration</td><td>Indoor cats and cats prone to boredom; adjust difficulty gradually</td></tr><tr><td>Catnip Toys</td><td>Cats that respond to catnip (approx. 50-70%)</td><td>Not all cats react; sensitivity is hereditary; kittens under 6 months rarely respond</td><td>Adult cats only; rotate to maintain novelty</td></tr><tr><td>Kick Toys</td><td>Cats who wrestle and bunny-kick</td><td>Choose sturdy fabric; overstuffing can cause seams to split</td><td>All ages; particularly good for cats with high prey drive</td></tr><tr><td>Electronic/Automated</td><td>Supplementing play when owners are away</td><td>Should not replace interactive play; some cats lose interest quickly</td><td>Best as a complement to hands-on play sessions</td></tr></tbody></table></figure>
<!-- /wp:table -->"""

    # Post 8172: Our Research Standards
    if "research standards" in title_lower:
        return """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Research Method</th><th>Best For</th><th>Considerations</th><th>Suitability</th></tr></thead><tbody><tr><td>Veterinary Literature Review</td><td>Health and safety claims requiring clinical evidence</td><td>Peer-reviewed sources take longer to verify; some studies may be region-specific</td><td>All health-related content; essential for medical or dietary guidance</td></tr><tr><td>Manufacturer Specification Analysis</td><td>Comparing product features, materials, and dimensions</td><td>Specifications are self-reported; independent verification is needed where possible</td><td>Product comparison guides and material safety assessments</td></tr><tr><td>UK Welfare Organisation Guidelines</td><td>Establishing baseline care standards for UK pet owners</td><td>Guidelines may differ between organisations; we note disagreements transparently</td><td>All welfare, housing, and enrichment content</td></tr><tr><td>Owner Experience Aggregation</td><td>Understanding real-world product performance over time</td><td>Anecdotal data requires large sample sizes; we note when evidence is limited</td><td>Durability assessments and practical usage guidance</td></tr><tr><td>Regulatory and Legal Review</td><td>Consumer rights, product safety standards, and labelling laws</td><td>UK regulations may differ from EU post-Brexit; we specify which standards apply</td><td>Safety warnings, labelling explanations, and consumer advice</td></tr></tbody></table></figure>
<!-- /wp:table -->"""

    # Post 8171: Why PetHub Online Exists
    if "why pethub" in title_lower:
        return """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Information Source</th><th>Best For</th><th>Considerations</th><th>Suitability</th></tr></thead><tbody><tr><td>Veterinary Practice Websites</td><td>Species-specific health conditions and treatment guidance</td><td>Often focused on clinical issues rather than product selection; may not cover everyday care decisions</td><td>Health concerns and dietary questions</td></tr><tr><td>Manufacturer Product Pages</td><td>Detailed specifications and feature lists for specific products</td><td>Inherently promotional; claims may lack independent verification</td><td>Technical details only; cross-reference with independent sources</td></tr><tr><td>Pet Owner Forums and Communities</td><td>Real-world experiences and practical tips from other owners</td><td>Anecdotal; advice quality varies widely; outdated information may persist</td><td>Supplementary insight alongside professional guidance</td></tr><tr><td>UK Welfare Charities (RSPCA, PDSA, Cats Protection)</td><td>Evidence-based welfare standards and baseline care requirements</td><td>Guidelines may be general rather than product-specific</td><td>Establishing minimum standards for housing, enrichment, and nutrition</td></tr><tr><td>Independent Review Platforms</td><td>Aggregated consumer feedback on product durability and value</td><td>Review authenticity varies; some platforms allow unverified purchases</td><td>Use alongside verified testing data for balanced assessments</td></tr></tbody></table></figure>
<!-- /wp:table -->"""

    return None  # No table needed for this post


# ── Content generation: Quick Checklist ──
def generate_checklist(title, content_raw, cluster):
    """Generate a Quick Checklist tailored to the post topic."""
    title_lower = title.lower()
    title_clean = html.unescape(title)

    # ── Cat Supplies ──
    if cluster == "Cat Supplies":
        if "litter disposal" in title_lower or "waste management" in title_lower:
            items = [
                "Scoop solid waste at least once daily to maintain hygiene and reduce odour",
                "Use dedicated pet waste bags or nappy sacks rather than standard carrier bags",
                "Double-bag waste before placing in general household waste (not recycling)",
                "Clean the full tray with hot water and mild detergent weekly",
                "Never flush cat litter, even if labelled flushable, in areas with combined sewers",
                "Store used litter bags in a sealed bin away from food preparation areas",
                "Replace the entire litter tray every 12 months as scratches harbour bacteria",
            ]
        elif "litter" in title_lower and ("type" in title_lower or "comparison" in title_lower):
            items = [
                "Match litter type to your cat's preference — observe which textures they use consistently",
                "Provide at least one tray per cat plus one extra, placed in quiet locations",
                "Fill trays to a depth of approximately 3cm for clumping litter or 5cm for non-clumping",
                "Avoid heavily scented litters as many cats find strong fragrances off-putting",
                "Transition between litter types gradually by mixing old and new over 7–10 days",
                "Check dust levels if your cat has respiratory sensitivities or asthma",
            ]
        elif "litter tray" in title_lower:
            items = [
                "Measure your cat from nose to tail base and add 50% for minimum tray length",
                "Choose open trays for nervous cats and hooded trays for cats preferring privacy",
                "Place trays away from food and water bowls in quiet, accessible locations",
                "Avoid placing trays next to noisy appliances like washing machines",
                "Provide one tray per cat plus one additional tray in multi-cat households",
                "Check that elderly or arthritic cats can step over the tray entrance comfortably",
            ]
        elif "heated" in title_lower and "bed" in title_lower:
            items = [
                "Check that the heating element has an automatic shut-off or thermostat",
                "Choose low-voltage (12V) options to reduce burn risk for cats who sleep deeply",
                "Position heated beds away from draughts but not directly against radiators",
                "Inspect power cords regularly for chewing damage — use cord protectors if needed",
                "Provide an unheated alternative nearby so your cat can self-regulate temperature",
                "Wash removable covers according to manufacturer instructions to maintain hygiene",
            ]
        elif "cat bed" in title_lower:
            items = [
                "Measure your cat while sleeping stretched out to determine minimum bed size",
                "Choose machine-washable beds or beds with removable, washable covers",
                "Place beds in quiet, elevated spots where your cat naturally chooses to rest",
                "Provide multiple bed options — some cats prefer enclosed igloos, others prefer open bolsters",
                "Replace beds when padding becomes flat or fabric shows signs of heavy wear",
                "Avoid beds with small detachable decorations that could be chewed and swallowed",
            ]
        elif "essential" in title_lower or "must-have" in title_lower:
            items = [
                "Set up food and water stations before bringing your cat home",
                "Purchase a suitable litter tray and litter type before your cat arrives",
                "Provide at least one scratching post to protect furniture and support claw health",
                "Have a secure cat carrier ready for vet visits and emergencies",
                "Choose age-appropriate toys for enrichment and daily play sessions",
                "Register with a local vet and schedule an initial health check within the first week",
                "Ensure all windows and balconies are secured if keeping your cat indoors",
            ]
        elif "glossary" in title_lower:
            items = [
                "Learn the difference between clumping and non-clumping litter before purchasing",
                "Understand scratching post materials — sisal rope, sisal fabric, and carpet each serve different needs",
                "Know your cat's life stage (kitten, adult, senior) when selecting food and products",
                "Check product labels for UKCA or CE markings indicating safety compliance",
                "Familiarise yourself with common allergen indicators in cat food ingredients lists",
                "Bookmark this glossary for quick reference when reading product descriptions",
            ]
        else:
            items = [
                "Research your cat's specific breed needs before purchasing supplies",
                "Choose products with clear safety certifications appropriate for UK sale",
                "Read the full ingredients or materials list before buying",
                "Start with essentials and add specialist items as you learn your cat's preferences",
                "Replace any supply showing signs of wear, damage, or hygiene concerns",
                "Consult your vet if unsure whether a product is suitable for your cat's health needs",
            ]

    # ── Cat Toys ──
    elif cluster == "Cat Toys":
        if "personality" in title_lower or "choose" in title_lower:
            items = [
                "Observe your cat's natural play behaviour for a week before buying new toys",
                "Offer a variety of toy types — wand, ball, puzzle — to identify preferences",
                "Rotate toys every few days to prevent boredom and maintain interest",
                "Remove damaged toys immediately to prevent ingestion of small parts",
                "Schedule at least two 10–15 minute interactive play sessions daily",
                "Store wand toys and string toys out of reach when not in use",
            ]
        elif "faq" in title_lower or "question" in title_lower:
            items = [
                "Check toy size against your cat's mouth — avoid anything small enough to swallow",
                "Supervise first use of any new toy to assess safety and your cat's reaction",
                "Replace toys when stuffing, feathers, or small parts become exposed",
                "Avoid toys with batteries unless the battery compartment is securely sealed",
                "Introduce new toys gradually alongside familiar favourites",
                "Keep a mix of interactive and self-play toys available",
            ]
        elif "kitten" in title_lower or "age" in title_lower:
            items = [
                "Choose soft, lightweight toys for kittens under 6 months",
                "Avoid small parts, long strings, and elastic bands for young kittens",
                "Increase toy complexity as your kitten grows and develops coordination",
                "Introduce puzzle feeders from around 4 months to encourage problem-solving",
                "Reduce high-energy toys for senior cats and introduce gentler alternatives",
                "Reassess toy suitability at each life stage transition",
            ]
        elif "terminology" in title_lower or "glossary" in title_lower:
            items = [
                "Learn the difference between interactive play and self-play toy categories",
                "Understand catnip sensitivity — approximately 50–70% of cats respond",
                "Know what 'enrichment' means in context: mental and physical stimulation combined",
                "Check whether 'feather toys' use real or synthetic feathers (affects durability)",
                "Recognise puzzle toy difficulty levels before purchasing",
                "Bookmark this terminology guide for reference when shopping",
            ]
        elif "wand" in title_lower or "interactive" in title_lower:
            items = [
                "Move wand toys in erratic, prey-like patterns rather than repetitive circles",
                "Let your cat 'catch' the toy periodically to prevent frustration",
                "Check the attachment point between wand and toy before each session",
                "Store wand toys in a closed cupboard to prevent unsupervised string access",
                "Replace frayed strings and worn attachments promptly",
                "Use wand play to bond with shy or newly adopted cats",
            ]
        elif "puzzle" in title_lower or "food" in title_lower:
            items = [
                "Start with the easiest difficulty setting and increase gradually",
                "Use high-value treats initially to motivate engagement with the puzzle",
                "Wash puzzle feeders after every use to prevent bacterial buildup",
                "Supervise initial sessions to ensure your cat does not become frustrated",
                "Rotate between different puzzle types to maintain mental challenge",
                "Reduce regular meal portions to account for treats used in puzzles",
            ]
        elif "catnip" in title_lower or "silver vine" in title_lower:
            items = [
                "Test with a small amount of catnip first to check your cat's sensitivity",
                "Store catnip in an airtight container to preserve potency",
                "Limit catnip exposure to 2–3 times per week to maintain effectiveness",
                "Try silver vine as an alternative if your cat does not respond to catnip",
                "Remove catnip toys after 15 minutes to prevent overstimulation",
                "Keep catnip products away from kittens under 6 months",
            ]
        elif "diy" in title_lower or "homemade" in title_lower:
            items = [
                "Use only non-toxic materials — avoid glue, paint, or treated fabrics",
                "Ensure all components are securely attached to prevent swallowing hazards",
                "Avoid small beads, buttons, or bells that could detach during play",
                "Test homemade toys under supervision before leaving them with your cat",
                "Replace DIY toys more frequently than commercial ones as they wear faster",
                "Never use rubber bands, hair ties, or dental floss as toy components",
            ]
        elif "indoor" in title_lower:
            items = [
                "Provide toys that simulate hunting — feathers, fur-textured mice, moving targets",
                "Create vertical play spaces using cat trees and wall-mounted shelves",
                "Rotate toys on a weekly schedule to prevent environmental monotony",
                "Combine play with feeding by using puzzle toys for a portion of daily food",
                "Ensure at least one interactive play session daily to prevent inactivity",
                "Place toys in different rooms to encourage exploration and movement",
            ]
        elif "senior" in title_lower or "older" in title_lower:
            items = [
                "Choose lightweight toys that require less physical effort",
                "Avoid toys requiring jumping or high-speed chasing for arthritic cats",
                "Use slow-moving wand play at ground level for gentle engagement",
                "Introduce scent-based enrichment as an alternative to vigorous play",
                "Keep play sessions shorter — 5–10 minutes rather than 15–20",
                "Consult your vet if your senior cat suddenly loses interest in all play",
            ]
        elif "multi" in title_lower or "household" in title_lower:
            items = [
                "Provide enough toys so each cat has access without competition",
                "Offer play sessions separately if cats have conflicting play styles",
                "Watch for resource guarding around favourite toys",
                "Place toys in multiple locations to reduce territorial tension",
                "Avoid laser pointers in multi-cat homes as they can trigger redirected aggression",
                "Ensure each cat gets individual interactive play time daily",
            ]
        else:
            items = [
                "Inspect all toys before each play session for loose parts or damage",
                "Rotate toys weekly to maintain your cat's interest and engagement",
                "Provide a mixture of interactive and self-play toy options",
                "Schedule at least two daily play sessions of 10–15 minutes each",
                "Store string and ribbon toys safely away when not supervised",
                "Replace any toy showing signs of wear before parts become detachable",
            ]

    # ── Dog Grooming ──
    elif cluster == "Dog Grooming":
        if "glossary" in title_lower or "terminology" in title_lower:
            items = [
                "Learn the difference between single-coated and double-coated breeds before choosing tools",
                "Understand 'hand stripping' vs 'clipping' — they produce different coat results",
                "Know your dog's coat type (smooth, wire, curly, long, double) to select appropriate techniques",
                "Familiarise yourself with grooming tool names and their intended uses",
                "Check grooming product labels for ingredients that may irritate sensitive skin",
                "Bookmark this glossary for reference when booking professional grooming appointments",
            ]
        elif "basics" in title_lower or "complete guide" in title_lower:
            items = [
                "Brush your dog's coat according to breed-specific frequency recommendations",
                "Check ears weekly for redness, odour, or excessive wax buildup",
                "Trim nails when you can hear them clicking on hard floors",
                "Introduce grooming gradually with positive reinforcement from puppyhood",
                "Use lukewarm water for bathing — never hot or cold",
                "Dry thoroughly after bathing, especially in skin folds and between toes",
                "Consult your vet or groomer if you notice skin changes during grooming",
            ]
        elif "shampoo" in title_lower or "bathe" in title_lower:
            items = [
                "Choose a shampoo formulated for the correct species — never use human shampoo on pets",
                "Test new shampoo on a small area first if your pet has sensitive skin",
                "Rinse thoroughly — residual shampoo causes irritation and flaking",
                "Bathe cats only when necessary; most cats groom themselves adequately",
                "Use lukewarm water and keep bathing sessions as calm and brief as possible",
                "Dry your pet fully after bathing to prevent skin issues, especially in cold weather",
            ]
        elif "nail" in title_lower or "claw" in title_lower:
            items = [
                "Identify the quick (blood vessel) before cutting — use a torch on light-coloured nails",
                "Trim small amounts frequently rather than large amounts infrequently",
                "Keep styptic powder on hand in case of accidental quick nicks",
                "Use sharp, species-appropriate clippers — dull blades crush rather than cut",
                "Handle your dog's paws regularly from puppyhood to build comfort with nail trims",
                "Consult a vet or groomer if nails are overgrown or you are unsure about trimming",
            ]
        elif "ear" in title_lower:
            items = [
                "Check ears weekly for redness, swelling, discharge, or unusual odour",
                "Use a vet-recommended ear cleaner — never cotton buds inside the ear canal",
                "Dry ears thoroughly after swimming or bathing to prevent infection",
                "Learn what healthy ears look like for your dog's breed",
                "Seek veterinary advice promptly if your dog shakes their head excessively or scratches ears",
                "Keep hair around the ear canal trimmed for breeds prone to ear problems",
            ]
        elif "brush" in title_lower or "coat" in title_lower:
            items = [
                "Identify your dog's coat type before selecting brushes and combs",
                "Brush in the direction of hair growth to avoid discomfort",
                "Use a slicker brush for tangles and an undercoat rake for double-coated breeds",
                "Check for mats behind ears, under legs, and around the collar area",
                "Brush before bathing — water tightens mats and makes them harder to remove",
                "Make brushing a positive experience with treats and calm praise",
            ]
        elif "professional" in title_lower or "groomer" in title_lower:
            items = [
                "Ask for qualifications — look for City and Guilds or iPET Network certification",
                "Visit the salon before booking to check cleanliness and handling practices",
                "Communicate your dog's temperament, health issues, and any sensitive areas",
                "Request a specific style by name or bring reference photos",
                "Ask how dogs are dried — cage dryers should have temperature monitoring",
                "Collect your dog promptly after grooming to minimise stress",
            ]
        elif "puppy" in title_lower:
            items = [
                "Begin gentle handling and brushing from the first week at home",
                "Keep initial grooming sessions short — under 5 minutes — with plenty of rewards",
                "Introduce tools one at a time: brush first, then nail clippers, then bathing",
                "Avoid full baths until your puppy has completed their vaccination course",
                "Book a professional grooming introduction session before the first full groom",
                "Never punish or restrain forcefully during grooming — this creates lasting anxiety",
            ]
        else:
            items = [
                "Groom your dog regularly based on their breed and coat type requirements",
                "Use tools designed for your dog's specific coat — one size does not fit all",
                "Introduce grooming gradually with positive associations and rewards",
                "Check skin condition during every grooming session for lumps, irritation, or parasites",
                "Keep grooming equipment clean and replace worn tools promptly",
                "Consult a veterinary professional if you notice persistent skin or coat problems",
            ]

    # ── Indoor Cats ──
    elif cluster == "Indoor Cats":
        if "complete guide" in title_lower or "care" in title_lower:
            items = [
                "Provide vertical space with cat trees, shelves, or window perches",
                "Offer at least two interactive play sessions daily totalling 30 minutes",
                "Rotate toys and enrichment activities weekly to prevent boredom",
                "Ensure access to fresh water in multiple locations around the home",
                "Create hiding spots using boxes, tunnels, or covered beds",
                "Schedule regular vet check-ups — indoor cats still need annual health assessments",
                "Secure windows with mesh screens to allow fresh air safely",
            ]
        elif "toy" in title_lower:
            items = [
                "Prioritise toys that simulate hunting — feather wands, moving mice, laser dots (with a physical catch reward)",
                "Include puzzle feeders to provide mental stimulation during solo time",
                "Ensure toys are accessible in multiple rooms to encourage movement",
                "Rotate toys on a 3–5 day cycle to maintain novelty",
                "Provide both interactive toys (for bonding) and self-play options (for independence)",
                "Remove and replace any toy showing signs of damage immediately",
            ]
        elif "exercise" in title_lower or "active" in title_lower:
            items = [
                "Aim for at least 30 minutes of active play daily, split across multiple sessions",
                "Use vertical space — climbing encourages natural exercise behaviours",
                "Create play circuits by placing toys and obstacles around the home",
                "Monitor your cat's weight monthly and adjust activity levels if needed",
                "Incorporate food-based activities like scatter feeding to encourage movement",
                "Consult your vet if your indoor cat shows signs of lethargy or weight gain",
            ]
        elif "enrichment" in title_lower or "stimulation" in title_lower:
            items = [
                "Provide sensory variety — visual (bird feeders at windows), auditory (nature sounds), olfactory (cat-safe herbs)",
                "Rotate enrichment items weekly to maintain interest",
                "Include opportunities for scratching, climbing, hiding, and hunting behaviours",
                "Use food puzzles for at least one meal per day",
                "Create safe outdoor access through catios or enclosed balcony spaces if possible",
                "Observe your cat's engagement and adjust enrichment based on their preferences",
            ]
        elif "safety" in title_lower or "hazard" in title_lower:
            items = [
                "Secure all windows and balcony doors with cat-safe mesh or screens",
                "Remove or secure toxic houseplants — lilies are particularly dangerous for cats",
                "Keep human medications, cleaning products, and small objects out of reach",
                "Check washing machines, tumble dryers, and dishwashers before use",
                "Secure blind cords and electrical cables to prevent strangulation or electrocution",
                "Ensure your cat is microchipped even if they live exclusively indoors",
            ]
        elif "behaviour" in title_lower or "stress" in title_lower:
            items = [
                "Learn to recognise signs of stress: over-grooming, hiding, aggression, or litter avoidance",
                "Provide multiple resources (food, water, litter, beds) in separate locations",
                "Maintain routine — indoor cats are sensitive to changes in schedule",
                "Use pheromone diffusers in areas where your cat spends the most time",
                "Allow your cat to choose when to interact — never force handling",
                "Seek veterinary advice if behaviour changes persist for more than a few days",
            ]
        elif "feeding" in title_lower or "nutrition" in title_lower or "diet" in title_lower:
            items = [
                "Feed a complete diet appropriate for indoor cats, which typically have lower energy needs",
                "Measure portions carefully — indoor cats are more prone to weight gain",
                "Use puzzle feeders to slow eating and provide mental stimulation",
                "Provide fresh water in multiple locations, away from food and litter",
                "Avoid free-feeding dry food unless your cat self-regulates well",
                "Consult your vet about dietary needs specific to your cat's age and health",
            ]
        else:
            items = [
                "Ensure your indoor cat has access to enrichment, play, and vertical space daily",
                "Monitor weight and activity levels closely — indoor cats are prone to obesity",
                "Provide multiple litter trays in quiet, accessible locations",
                "Schedule daily interactive play to compensate for the lack of outdoor stimulation",
                "Keep all windows and exits secured with appropriate screens or locks",
                "Maintain regular veterinary check-ups including dental assessments",
            ]

    # ── Uncategorized ──
    elif cluster == "Uncategorized":
        if "research standards" in title_lower:
            items = [
                "Check whether the source cites specific UK veterinary or welfare organisations",
                "Look for transparency about methodology, conflicts of interest, and update frequency",
                "Verify that product information matches current manufacturer specifications",
                "Confirm advice aligns with guidance from RSPCA, PDSA, or BVA",
                "Check the publication and last-updated dates on any guide you read",
                "Cross-reference important claims with at least two independent sources",
            ]
        elif "why pethub" in title_lower or "exists" in title_lower:
            items = [
                "Evaluate pet care sources by checking who funds them and whether they sell products",
                "Prioritise advice from UK-based veterinary and welfare organisations",
                "Look for editorial transparency — who writes the content and how is it verified",
                "Check whether a site discloses affiliate relationships and how they handle conflicts",
                "Seek sources that reference peer-reviewed research alongside practical experience",
                "Report errors or outdated information to help maintain content accuracy",
            ]
        elif "confidence" in title_lower or "shy" in title_lower or "fearful" in title_lower:
            items = [
                "Start with low-pressure toys placed near your dog's safe space — never force interaction",
                "Use treat-dispensing toys to create positive associations with play",
                "Keep initial sessions under 5 minutes and end before your dog shows stress",
                "Avoid sudden movements, loud toys, or high-energy games with anxious dogs",
                "Gradually increase challenge only after consistent comfortable engagement",
                "Consult a certified behaviourist if fear responses do not improve over several weeks",
            ]
        elif "puzzle" in title_lower or "rotating" in title_lower:
            items = [
                "Begin with beginner-level puzzles and advance only after consistent success",
                "Rotate puzzle types (sliding, lifting, spinning) to exercise different skills",
                "Increase difficulty in small increments — frustration undoes progress",
                "Use your dog's regular food in puzzles to prevent overfeeding",
                "Clean puzzles after each use to prevent mould and bacterial growth",
                "Monitor engagement — reduced interest may mean the puzzle is too easy or too hard",
            ]
        elif "dog" in title_lower and "bed" in title_lower:
            items = [
                "Place the bed in a quiet area away from high-traffic zones and draughts",
                "Choose a location where your dog naturally gravitates to rest",
                "Avoid placing beds near noisy appliances or external doors",
                "Ensure the bed is accessible — older or arthritic dogs need low-entry options",
                "Provide a bed in each room where your dog spends significant time",
                "Wash bed covers weekly and replace beds when padding loses support",
            ]
        elif "tug" in title_lower:
            items = [
                "Use a tug toy long enough to keep your hands away from your dog's mouth",
                "Teach a reliable 'drop it' command before regular tug play",
                "Let your dog win sometimes to build confidence and maintain interest",
                "Stop immediately if your dog's teeth contact your skin, even accidentally",
                "Avoid tug with puppies whose adult teeth have not fully come in",
                "Store tug toys away between sessions to maintain their value as a reward",
            ]
        elif "chew" in title_lower:
            items = [
                "Match chew toy hardness to your dog's chewing strength and jaw size",
                "Avoid chews harder than your dog's teeth — the thumbnail test applies",
                "Supervise all chewing sessions, especially with new products",
                "Discard chew toys when they become small enough to swallow",
                "Rotate chews to maintain interest and prevent obsessive chewing",
                "Consult your vet about safe chewing options for puppies and senior dogs",
            ]
        elif "fetch" in title_lower:
            items = [
                "Warm up with a short walk before vigorous fetch sessions",
                "Use appropriately sized balls — too small creates a choking risk",
                "Avoid repetitive throwing on hard surfaces to protect joints",
                "Limit fetch sessions to 15–20 minutes to prevent overexertion",
                "Never throw sticks — they cause serious mouth, throat, and chest injuries",
                "Ensure fresh water is available during and after fetch play",
            ]
        elif "squeaky" in title_lower or "plush" in title_lower:
            items = [
                "Check that squeakers are securely enclosed within reinforced stitching",
                "Supervise play and remove the toy if your dog begins extracting the squeaker",
                "Choose toys with double or triple stitching for persistent chewers",
                "Replace plush toys at the first sign of stuffing exposure",
                "Wash plush toys regularly to prevent bacterial buildup",
                "Avoid plush toys with plastic eyes, noses, or sewn-on accessories",
            ]
        elif "rope" in title_lower:
            items = [
                "Inspect rope toys before every use for fraying and loose strands",
                "Discard rope toys when fibres begin to separate — ingested strands cause intestinal blockages",
                "Use rope toys only for supervised play, never as unsupervised chew items",
                "Choose ropes sized appropriately for your dog — too thin and they shred quickly",
                "Wash rope toys weekly by soaking in hot water and allowing to dry completely",
                "Monitor your dog's stools if they have been playing with a fraying rope toy",
            ]
        elif "ball" in title_lower:
            items = [
                "Select balls larger than your dog's throat to prevent choking",
                "Avoid tennis balls for aggressive chewers — the abrasive felt wears tooth enamel",
                "Check balls for cracks or splits before each play session",
                "Use solid rubber balls rather than hollow ones for strong chewers",
                "Never allow your dog to play with balls intended for human sports (golf, squash)",
                "Provide fresh water during ball play and watch for signs of overheating",
            ]
        else:
            items = [
                "Research your pet's specific needs before purchasing any product",
                "Choose products with clear safety certifications suitable for UK sale",
                "Introduce new items gradually while supervising your pet's interaction",
                "Inspect toys and products regularly for wear, damage, or hygiene concerns",
                "Replace items promptly when they show signs of deterioration",
                "Consult your vet if you are unsure whether a product is appropriate for your pet",
            ]

    else:
        items = [
            "Research your pet's specific needs before making purchases",
            "Choose products with appropriate safety certifications",
            "Introduce new items gradually and monitor your pet's response",
            "Inspect products regularly for wear and damage",
            "Replace worn items before they become a safety hazard",
            "Consult your vet if you have concerns about product suitability",
        ]

    li_items = "".join(f"<li>{item}</li>" for item in items)
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#f5f3ff"}},"border":{{"radius":"6px","width":"1px","color":"#ddd6fe"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#ddd6fe;border-width:1px;border-radius:6px;background-color:#f5f3ff;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} --><h4 class="wp-block-heading">Quick Checklist</h4><!-- /wp:heading -->
<!-- wp:list --><ul class="wp-block-list">{li_items}</ul><!-- /wp:list -->
</div><!-- /wp:group -->'''


# ── Content generation: What to Do Next ──
def generate_next_steps(title, content_raw, cluster):
    """Generate What to Do Next steps tailored to the post topic."""
    title_lower = title.lower()

    # ── Cat Supplies ──
    if cluster == "Cat Supplies":
        if "litter disposal" in title_lower or "waste management" in title_lower:
            steps = [
                "Audit your current disposal setup — check whether bags, bins, and cleaning schedule meet hygiene standards",
                "Choose a dedicated waste containment system (sealed bin or nappy disposal unit) for the room where the tray is located",
                "Establish a daily scooping routine at the same time each day to build consistency",
                "Review your council's waste disposal guidelines to confirm correct bin use for pet waste",
            ]
        elif "litter" in title_lower and ("type" in title_lower or "comparison" in title_lower):
            steps = [
                "Identify your cat's current litter preferences by observing their behaviour",
                "If switching types, plan a 7–10 day gradual transition by mixing old and new litter",
                "Monitor your cat's tray usage for two weeks after any change to ensure acceptance",
                "Consult your vet if your cat shows persistent litter aversion or toileting problems",
            ]
        elif "litter tray" in title_lower:
            steps = [
                "Measure your cat to determine the correct minimum tray dimensions",
                "Evaluate your current tray placement against the guidelines in this article",
                "In multi-cat homes, count trays and add extras if you have fewer than one per cat plus one",
                "Set a weekly deep-cleaning schedule and a daily scooping routine",
            ]
        elif "heated" in title_lower and "bed" in title_lower:
            steps = [
                "Check your current cat bed for warmth adequacy — observe whether your cat seeks warmer spots in winter",
                "Compare heated bed options focusing on voltage, thermostat features, and washability",
                "Test the bed in your cat's preferred sleeping area before committing to a permanent location",
                "Monitor your cat's use over the first week and adjust placement if they avoid it",
            ]
        elif "cat bed" in title_lower:
            steps = [
                "Observe where your cat naturally sleeps to identify their preferred bed style and location",
                "Measure your cat while resting to determine minimum bed size requirements",
                "Select two or three bed options in different styles to discover your cat's preference",
                "Place beds in quiet, elevated spots and monitor which your cat uses most frequently",
            ]
        elif "essential" in title_lower or "must-have" in title_lower:
            steps = [
                "Create a checklist of essential supplies needed before your cat arrives",
                "Purchase food, water bowls, litter tray, and carrier as a minimum first set",
                "Set up a designated quiet room with all essentials for the first few days",
                "Register with a local veterinary practice and book an introductory appointment",
                "Gradually introduce your cat to the rest of the home once settled",
            ]
        elif "glossary" in title_lower:
            steps = [
                "Read through the full glossary to build your understanding of common cat care terms",
                "Note any terms relevant to products you currently use or plan to purchase",
                "Use this glossary as a reference when reading product reviews and care guides",
                "Share relevant terms with other household members involved in cat care",
            ]
        else:
            steps = [
                "Assess your current cat supply setup against the recommendations in this guide",
                "Identify any gaps or items needing replacement",
                "Research suitable alternatives using the criteria described above",
                "Make changes gradually and monitor your cat's response to new products",
            ]

    # ── Cat Toys ──
    elif cluster == "Cat Toys":
        if "personality" in title_lower or "choose" in title_lower:
            steps = [
                "Spend a week observing your cat's natural play preferences — do they chase, pounce, wrestle, or stalk?",
                "Match your observations to the play style categories described in this guide",
                "Select two or three toys suited to your cat's identified play personality",
                "Introduce new toys one at a time and observe engagement over several days",
                "Adjust your toy rotation based on which types generate the most sustained interest",
            ]
        elif "faq" in title_lower:
            steps = [
                "Review the questions in this guide against your own concerns about cat toys",
                "Audit your current toy collection for safety and variety",
                "Replace any toys that fail the safety checks described above",
                "Bookmark this page for reference when questions arise in future",
            ]
        elif "kitten" in title_lower or "age" in title_lower:
            steps = [
                "Determine your cat's current life stage and match toys to the age-appropriate recommendations",
                "Remove any toys from your collection that are unsuitable for your cat's current age",
                "Plan a toy transition schedule as your kitten approaches adulthood",
                "Consult your vet about appropriate play intensity if your cat has any health conditions",
            ]
        elif "terminology" in title_lower or "glossary" in title_lower:
            steps = [
                "Read through the key terms to ensure you understand common toy descriptions",
                "Use this glossary when comparing products online or in pet shops",
                "Note which play types match your cat's observed preferences",
                "Refer back to this guide when reading other PetHub Online cat toy articles",
            ]
        elif "wand" in title_lower or "interactive" in title_lower:
            steps = [
                "Schedule two daily interactive play sessions of 10–15 minutes each",
                "Practise prey-like movements — start slow, build speed, then allow the catch",
                "Inspect your wand toy's attachment point and string before each session",
                "Experiment with different wand attachments to find what excites your cat most",
            ]
        elif "puzzle" in title_lower or "food" in title_lower:
            steps = [
                "Start with the simplest puzzle toy and your cat's favourite treat",
                "Allow your cat to succeed easily at first to build confidence",
                "Increase difficulty gradually over weeks, not days",
                "Track which puzzle types engage your cat longest and invest in similar designs",
            ]
        elif "catnip" in title_lower or "silver vine" in title_lower:
            steps = [
                "Test your cat's catnip sensitivity with a small pinch on a cloth",
                "If no response, try silver vine or valerian root as alternatives",
                "Establish a 2–3 times per week schedule for catnip enrichment",
                "Store all catnip products in airtight containers between uses",
            ]
        elif "diy" in title_lower or "homemade" in title_lower:
            steps = [
                "Gather materials from the safe list provided in this guide",
                "Start with the simplest project to build your confidence",
                "Test every homemade toy under supervision before leaving it with your cat",
                "Replace DIY toys at the first sign of wear — they deteriorate faster than commercial options",
            ]
        elif "indoor" in title_lower:
            steps = [
                "Audit your home for play opportunities — vertical space, window perches, hiding spots",
                "Create a toy rotation schedule covering at least 10–14 different toys",
                "Introduce one puzzle feeder for at least one meal per day",
                "Review your cat's activity levels monthly and adjust play provision accordingly",
            ]
        elif "senior" in title_lower or "older" in title_lower:
            steps = [
                "Observe your senior cat's current mobility and energy levels",
                "Replace high-energy toys with gentler alternatives suited to their capabilities",
                "Adjust play sessions to shorter, more frequent interactions",
                "Discuss any sudden changes in playfulness with your veterinary team",
            ]
        elif "multi" in title_lower or "household" in title_lower:
            steps = [
                "Count your toys and ensure each cat has access to their own set",
                "Identify any resource-guarding behaviour around toys",
                "Schedule individual play time with each cat separately",
                "Create multiple play stations in different rooms to reduce competition",
            ]
        else:
            steps = [
                "Audit your current cat toy collection for safety and variety",
                "Identify any gaps in toy types based on the categories described in this guide",
                "Purchase or create toys to fill those gaps, prioritising safety and your cat's preferences",
                "Establish a regular toy rotation and play schedule",
            ]

    # ── Dog Grooming ──
    elif cluster == "Dog Grooming":
        if "glossary" in title_lower or "terminology" in title_lower:
            steps = [
                "Read through the glossary to build familiarity with grooming terminology",
                "Identify terms relevant to your dog's specific coat type and breed",
                "Use this glossary when communicating with professional groomers about your preferences",
                "Refer back when reading other PetHub Online grooming guides",
            ]
        elif "basics" in title_lower or "complete guide" in title_lower:
            steps = [
                "Identify your dog's coat type and look up the recommended grooming frequency",
                "Assemble a basic grooming toolkit — brush, comb, nail clippers, ear cleaner, and shampoo",
                "Establish a weekly grooming routine starting with short, positive sessions",
                "Book a professional grooming consultation if your dog's coat requires specialist techniques",
                "Monitor skin and coat condition monthly and adjust your routine as needed",
            ]
        elif "shampoo" in title_lower or "bathe" in title_lower:
            steps = [
                "Determine how often your pet needs bathing based on coat type and activity level",
                "Select an appropriate shampoo based on your pet's skin sensitivity and coat needs",
                "Prepare your bathing area with towels, shampoo, and treats before starting",
                "Follow the bathing technique described in this guide for best results",
            ]
        elif "nail" in title_lower or "claw" in title_lower:
            steps = [
                "Examine your dog's nails and identify the quick on each nail where visible",
                "Gather appropriate tools — sharp clippers, styptic powder, and treats",
                "Start with one or two nails per session if your dog is anxious",
                "Build up to full trims as your dog becomes comfortable with the process",
            ]
        elif "ear" in title_lower:
            steps = [
                "Examine your dog's ears today to establish a baseline of what looks normal",
                "Purchase a vet-recommended ear cleaning solution",
                "Add weekly ear checks to your grooming routine",
                "Seek veterinary advice immediately if you notice redness, discharge, or odour",
            ]
        elif "brush" in title_lower or "coat" in title_lower:
            steps = [
                "Identify your dog's coat type using the descriptions in this guide",
                "Select the correct brush type for your dog's coat",
                "Start with short brushing sessions in areas your dog finds comfortable",
                "Gradually work up to full-body brushing over several sessions",
            ]
        elif "professional" in title_lower or "groomer" in title_lower:
            steps = [
                "Research local groomers and check for relevant qualifications",
                "Visit your shortlisted salon to assess the environment",
                "Book an initial consultation to discuss your dog's needs and temperament",
                "Prepare your dog with positive handling exercises before the first appointment",
            ]
        elif "puppy" in title_lower:
            steps = [
                "Begin gentle daily handling of paws, ears, and mouth from the first day home",
                "Introduce one grooming tool per week with positive reinforcement",
                "Keep early sessions under 5 minutes and always end on a positive note",
                "Book a puppy grooming introduction with a professional groomer by 16 weeks of age",
            ]
        else:
            steps = [
                "Assess your current grooming routine against the recommendations in this guide",
                "Identify any grooming tasks you have been overlooking",
                "Gather any tools or products you need to address gaps",
                "Establish a consistent grooming schedule suited to your dog's breed and coat type",
            ]

    # ── Indoor Cats ──
    elif cluster == "Indoor Cats":
        if "complete guide" in title_lower or "care" in title_lower:
            steps = [
                "Audit your home environment against the indoor cat needs checklist above",
                "Identify the most significant gaps — typically vertical space, play time, or enrichment variety",
                "Address the top three gaps within the next week",
                "Schedule a veterinary health check to establish a baseline for your indoor cat",
                "Review and adjust your setup monthly as your cat's needs evolve",
            ]
        elif "toy" in title_lower:
            steps = [
                "Count and categorise your current toy collection by type (interactive, self-play, puzzle)",
                "Identify which categories are underrepresented and plan purchases accordingly",
                "Set up a toy rotation schedule and commit to daily interactive play",
                "Evaluate your cat's engagement after two weeks and adjust the toy mix",
            ]
        elif "exercise" in title_lower or "active" in title_lower:
            steps = [
                "Record your cat's current daily activity level for one week as a baseline",
                "Identify which exercise methods from this guide suit your home layout",
                "Implement at least two new activity options this week",
                "Weigh your cat and set a monthly weight monitoring schedule",
            ]
        elif "enrichment" in title_lower or "stimulation" in title_lower:
            steps = [
                "Map your home's current enrichment provision room by room",
                "Add at least one new enrichment type (sensory, food-based, or social) this week",
                "Create a weekly rotation calendar for enrichment activities",
                "Observe your cat's engagement and note which enrichment types they prefer",
            ]
        elif "safety" in title_lower or "hazard" in title_lower:
            steps = [
                "Walk through your home room by room checking for the hazards listed above",
                "Address any immediate risks — toxic plants, unsecured windows, accessible chemicals",
                "Install window screens or restrictors on any openable windows",
                "Create a pet-proofing checklist for visitors and anyone else in the household",
            ]
        elif "behaviour" in title_lower or "stress" in title_lower:
            steps = [
                "Observe your cat's behaviour for one week and note any stress indicators",
                "Review resource placement — ensure food, water, litter, and beds are in separate quiet locations",
                "Implement one environmental change from this guide to reduce identified stressors",
                "Consult your vet or a certified behaviourist if stress signs persist beyond two weeks",
            ]
        else:
            steps = [
                "Review your indoor cat's current environment against the guidance in this article",
                "Identify the most impactful improvement you can make this week",
                "Implement the change and observe your cat's response over 7–10 days",
                "Plan the next improvement based on your cat's reactions and the remaining recommendations",
            ]

    # ── Uncategorized ──
    elif cluster == "Uncategorized":
        if "research standards" in title_lower:
            steps = [
                "Review the source list for any guide you are currently using to inform pet care decisions",
                "Cross-check key claims against at least two independent, trusted sources",
                "If you find outdated or incorrect information on any PetHub Online guide, use our corrections form to report it",
                "Bookmark our editorial process and research methodology pages for reference",
            ]
        elif "why pethub" in title_lower or "exists" in title_lower:
            steps = [
                "Evaluate the pet care sources you currently rely on against the criteria outlined above",
                "Identify any sources that may have undisclosed commercial conflicts of interest",
                "Add at least one UK veterinary or welfare organisation to your regular reference sources",
                "Explore PetHub Online's category guides for evidence-based information on your pet's specific needs",
            ]
        elif "confidence" in title_lower or "shy" in title_lower:
            steps = [
                "Identify your dog's specific fear triggers by observing their behaviour in different contexts",
                "Select one low-pressure play activity from this guide to try this week",
                "Keep a brief daily log of your dog's response to track progress over time",
                "Consult a certified behaviourist (ABTC-registered) if fear responses are severe or worsening",
            ]
        elif "puzzle" in title_lower or "rotating" in title_lower:
            steps = [
                "Assess your dog's current puzzle-solving ability using the difficulty scale in this guide",
                "Select a puzzle at the appropriate starting level and introduce it with high-value treats",
                "Record your dog's completion time and success rate over the first week",
                "Advance to the next difficulty level only after consistent success at the current one",
            ]
        elif "dog" in title_lower and "bed" in title_lower:
            steps = [
                "Observe where your dog naturally chooses to rest over a typical week",
                "Evaluate those locations against the placement guidelines in this article",
                "Adjust bed placement based on the recommendations and your dog's preferences",
                "Reassess seasonally — dogs often prefer cooler spots in summer and warmer ones in winter",
            ]
        else:
            steps = [
                "Review the guidance in this article against your current pet care practices",
                "Identify the most relevant recommendation for your situation",
                "Implement one change this week and observe your pet's response",
                "Return to this guide periodically as your pet's needs change with age or season",
            ]

    else:
        steps = [
            "Review the key points in this article against your current setup",
            "Identify the single most impactful change you can make this week",
            "Implement that change and monitor your pet's response",
            "Revisit this guide in one month to assess progress and plan next steps",
        ]

    li_items = "".join(f"<li>{step}</li>" for step in steps)
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#f0fdfa"}},"border":{{"radius":"6px","width":"1px","color":"#99f6e4"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#99f6e4;border-width:1px;border-radius:6px;background-color:#f0fdfa;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} --><h4 class="wp-block-heading">What to Do Next</h4><!-- /wp:heading -->
<!-- wp:list {{"ordered":true}} --><ol class="wp-block-list">{li_items}</ol><!-- /wp:list -->
</div><!-- /wp:group -->'''


# ── Trust depth: inline references ──
def generate_trust_references(title, content_raw, cluster):
    """Generate trust depth references block for the post."""
    title_lower = title.lower()

    # Determine which organisations are most relevant
    if cluster in ("Cat Supplies", "Cat Toys", "Indoor Cats"):
        org_text = (
            'This content references welfare and care standards from '
            '<a href="https://www.rspca.org.uk/" rel="nofollow noopener" target="_blank">RSPCA</a>, '
            '<a href="https://www.pdsa.org.uk/" rel="nofollow noopener" target="_blank">PDSA</a>, '
            '<a href="https://www.cats.org.uk/" rel="nofollow noopener" target="_blank">Cats Protection</a>, '
            '<a href="https://icatcare.org/" rel="nofollow noopener" target="_blank">International Cat Care</a>, '
            'and the <a href="https://www.bva.co.uk/" rel="nofollow noopener" target="_blank">British Veterinary Association (BVA)</a>.'
        )
    elif cluster == "Dog Grooming":
        org_text = (
            'This content references welfare and grooming standards from '
            '<a href="https://www.rspca.org.uk/" rel="nofollow noopener" target="_blank">RSPCA</a>, '
            '<a href="https://www.pdsa.org.uk/" rel="nofollow noopener" target="_blank">PDSA</a>, '
            'the <a href="https://www.bva.co.uk/" rel="nofollow noopener" target="_blank">British Veterinary Association (BVA)</a>, '
            'and the <a href="https://www.rcvs.org.uk/" rel="nofollow noopener" target="_blank">Royal College of Veterinary Surgeons (RCVS)</a>.'
        )
    else:  # Uncategorized - mixed
        org_text = (
            'This content references welfare standards from '
            '<a href="https://www.rspca.org.uk/" rel="nofollow noopener" target="_blank">RSPCA</a>, '
            '<a href="https://www.pdsa.org.uk/" rel="nofollow noopener" target="_blank">PDSA</a>, '
            'the <a href="https://www.bva.co.uk/" rel="nofollow noopener" target="_blank">British Veterinary Association (BVA)</a>, '
            'and the <a href="https://www.rcvs.org.uk/" rel="nofollow noopener" target="_blank">Royal College of Veterinary Surgeons (RCVS)</a>.'
        )

    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#f8fafb"}},"border":{{"radius":"8px","width":"1px","color":"#e2e8f0"}},"spacing":{{"padding":{{"top":"20px","bottom":"20px","left":"24px","right":"24px"}},"margin":{{"top":"32px","bottom":"32px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#e2e8f0;border-width:1px;border-radius:8px;background-color:#f8fafb;margin-top:32px;margin-bottom:32px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px">
<!-- wp:heading {{"level":4}} --><h4 class="wp-block-heading">Our Editorial Standards</h4><!-- /wp:heading -->
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"14px"}}}}}} -->
<p class="wp-block-paragraph" style="font-size:14px">All content on PetHub Online is created following our <a href="https://pethubonline.com/our-editorial-process/">editorial process</a>, supported by thorough <a href="https://pethubonline.com/how-we-research-pet-products/">research methodology</a>. {org_text} We maintain transparency through our <a href="https://pethubonline.com/corrections-and-updates-policy/">corrections and updates policy</a>. Content is AI-assisted and editorially reviewed. For details on how we handle affiliate relationships, see our <a href="https://pethubonline.com/affiliate-disclosure/">affiliate disclosure</a>.</p>
<!-- /wp:paragraph -->
</div><!-- /wp:group -->'''


# ── Content insertion logic ──
def find_insertion_point(content, marker_name):
    """Find the position just before a named block section."""
    # Look for heading with the marker name
    patterns = [
        f'<h4 class="wp-block-heading">{marker_name}</h4>',
        f'<h3 class="wp-block-heading">{marker_name}</h3>',
        f'<strong>{marker_name}</strong>',
    ]
    for pat in patterns:
        idx = content.find(pat)
        if idx >= 0:
            # Walk backwards to find the start of the enclosing group/block
            search_region = content[:idx]
            # Find the nearest wp:group comment before this
            last_comment = search_region.rfind('<!-- wp:group')
            if last_comment >= 0:
                return last_comment
            # Fallback: look for <div class="wp-block-group
            last_div = search_region.rfind('<div class="wp-block-group')
            if last_div >= 0:
                return last_div
            return idx
    return -1


def process_post(post_id, cluster):
    """Process a single post: add missing blocks."""
    print(f"\n{'='*60}")
    print(f"Processing post {post_id} (cluster: {cluster})")

    data = api_get(f"posts/{post_id}?context=edit")
    if "id" not in data:
        print(f"  ERROR: Could not fetch post {post_id}: {str(data)[:200]}")
        return {"id": post_id, "title": "ERROR", "cluster": cluster,
                "comparison_added": False, "checklist_added": False,
                "next_steps_added": False, "trust_refs_added": False,
                "status": "fetch_error"}

    title = data["title"]["raw"]
    content = data["content"]["raw"]
    print(f"  Title: {title}")
    print(f"  Content length: {len(content)}")

    original_content = content
    comparison_added = False
    checklist_added = False
    next_steps_added = False
    trust_refs_added = False

    # 1. COMPARISON TABLE - only for specified posts
    has_table = "wp:table" in content
    if post_id in COMPARISON_TABLE_IDS and not has_table:
        table_html = generate_comparison_table(title, content, cluster)
        if table_html:
            # Insert table before Common Mistakes, Key Terms, or Key Takeaways
            insert_pos = None
            positions = []
            for marker in ["Common Mistakes", "Key Terms", "Key Takeaways"]:
                pos = find_insertion_point(content, marker)
                if pos >= 0:
                    positions.append(pos)

            if positions:
                insert_pos = min(positions)
            else:
                # For info pages without those markers, insert before the last h2
                last_h2 = content.rfind('<h2 class="wp-block-heading">')
                if last_h2 > 0:
                    search = content[:last_h2]
                    wp_heading = search.rfind('<!-- wp:heading')
                    if wp_heading >= 0:
                        insert_pos = wp_heading
                    else:
                        insert_pos = last_h2

            if insert_pos and insert_pos > 0:
                table_block = f'\n<!-- wp:heading {{"level":3}} -->\n<h3 class="wp-block-heading">Comparison at a Glance</h3>\n<!-- /wp:heading -->\n\n{table_html}\n\n'
                content = content[:insert_pos] + table_block + content[insert_pos:]
                comparison_added = True
                print(f"  + Added comparison table at position {insert_pos}")
            else:
                print(f"  ! Could not find insertion point for comparison table")

    # 2. QUICK CHECKLIST
    has_checklist = "Quick Checklist" in content
    if not has_checklist:
        checklist_html = generate_checklist(title, content, cluster)

        # Insert before Common Mistakes
        insert_pos = find_insertion_point(content, "Common Mistakes")
        if insert_pos < 0:
            insert_pos = find_insertion_point(content, "Key Terms")
        if insert_pos < 0:
            insert_pos = find_insertion_point(content, "Key Takeaways")
        if insert_pos < 0:
            insert_pos = find_insertion_point(content, "Our Editorial Standards")
        if insert_pos < 0:
            # Try before the trust footer div
            idx = content.find("Editorial Standards</p>")
            if idx >= 0:
                search = content[:idx]
                div_start = search.rfind('<div ')
                if div_start >= 0:
                    insert_pos = div_start

        if insert_pos > 0:
            content = content[:insert_pos] + checklist_html + "\n\n" + content[insert_pos:]
            checklist_added = True
            print(f"  + Added Quick Checklist at position {insert_pos}")
        else:
            content = content + "\n\n" + checklist_html
            checklist_added = True
            print(f"  + Added Quick Checklist at end")

    # 3. WHAT TO DO NEXT
    has_next_steps = "What to Do Next" in content
    if not has_next_steps:
        next_steps_html = generate_next_steps(title, content, cluster)

        # Insert after Quick Checklist, before Common Mistakes
        checklist_end = content.find("Quick Checklist")
        if checklist_end >= 0:
            # Find the end of the checklist group block
            search_start = checklist_end
            end_marker = "</div><!-- /wp:group -->"
            end_pos = content.find(end_marker, search_start)
            if end_pos >= 0:
                insert_pos = end_pos + len(end_marker)
            else:
                insert_pos = find_insertion_point(content, "Common Mistakes")
        else:
            insert_pos = find_insertion_point(content, "Common Mistakes")

        if insert_pos and insert_pos > 0:
            content = content[:insert_pos] + "\n\n" + next_steps_html + "\n\n" + content[insert_pos:]
            next_steps_added = True
            print(f"  + Added What to Do Next at position {insert_pos}")
        else:
            # Try before Key Takeaways
            insert_pos = find_insertion_point(content, "Key Takeaways")
            if insert_pos and insert_pos > 0:
                content = content[:insert_pos] + "\n\n" + next_steps_html + "\n\n" + content[insert_pos:]
                next_steps_added = True
                print(f"  + Added What to Do Next before Key Takeaways")
            else:
                content = content + "\n\n" + next_steps_html
                next_steps_added = True
                print(f"  + Added What to Do Next at end")

    # 4. TRUST DEPTH - check if editorial standards block already exists with proper org links
    has_editorial = "Our Editorial Standards" in content and "editorial process" in content.lower()
    has_rspca = "rspca.org.uk" in content
    has_pdsa = "pdsa.org.uk" in content
    has_bva = "bva.co.uk" in content

    if not has_editorial or not (has_rspca and has_pdsa):
        trust_html = generate_trust_references(title, content, cluster)

        if has_editorial:
            # Replace existing editorial standards block
            es_pos = content.find("Our Editorial Standards")
            if es_pos >= 0:
                search = content[:es_pos]
                block_start = search.rfind('<!-- wp:group')
                if block_start < 0:
                    block_start = search.rfind('<div class="wp-block-group')

                if block_start >= 0:
                    end_marker = "</div><!-- /wp:group -->"
                    end_pos = content.find(end_marker, es_pos)
                    if end_pos >= 0:
                        end_pos += len(end_marker)
                        content = content[:block_start] + trust_html + content[end_pos:]
                        trust_refs_added = True
                        print(f"  + Replaced Editorial Standards block with enhanced trust refs")
        else:
            # Check for the simple div-based editorial footer
            simple_footer_markers = ["Editorial Standards</p>", "editorial process</a>"]
            footer_found = False
            for marker in simple_footer_markers:
                idx = content.find(marker)
                if idx >= 0:
                    search = content[:idx]
                    div_start = search.rfind('<div ')
                    if div_start >= 0:
                        div_end = content.find('</div>', idx)
                        if div_end >= 0:
                            div_end += len('</div>')
                            content = content[:div_start] + trust_html + content[div_end:]
                            trust_refs_added = True
                            footer_found = True
                            print(f"  + Replaced simple editorial footer with trust block")
                            break

            if not footer_found:
                content = content + "\n\n" + trust_html
                trust_refs_added = True
                print(f"  + Added trust references block at end")

    # Check if anything changed
    if content == original_content:
        print(f"  = No changes needed for post {post_id}")
        return {"id": post_id, "title": title, "cluster": cluster,
                "comparison_added": False, "checklist_added": False,
                "next_steps_added": False, "trust_refs_added": False,
                "status": "no_changes_needed"}

    # Update the post
    print(f"  Updating post {post_id}...")
    success = api_update(post_id, {"content": content})

    status = "updated" if success else "update_failed"
    print(f"  Status: {status}")

    return {"id": post_id, "title": title, "cluster": cluster,
            "comparison_added": comparison_added, "checklist_added": checklist_added,
            "next_steps_added": next_steps_added, "trust_refs_added": trust_refs_added,
            "status": status}


# ── Main execution ──
def main():
    print("=" * 70)
    print("Phase 10AV/10AW/10AY: Multi-Cluster Dominance Enhancement")
    print(f"Clusters: {', '.join(CLUSTERS.keys())}")
    print(f"Total posts: {len(ALL_IDS)}")
    print("=" * 70)

    results = []

    for i, post_id in enumerate(ALL_IDS):
        cluster = POST_CLUSTER[post_id]
        result = process_post(post_id, cluster)
        results.append(result)

        if i < len(ALL_IDS) - 1:
            print(f"  Waiting {DELAY}s...")
            time.sleep(DELAY)

    # Write CSV log
    print(f"\n{'='*70}")
    print(f"Writing results to {LOG_FILE}")

    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "title", "cluster", "comparison_added",
            "checklist_added", "next_steps_added", "trust_refs_added", "status"
        ])
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    # Summary
    total = len(results)
    updated = sum(1 for r in results if r["status"] == "updated")
    no_change = sum(1 for r in results if r["status"] == "no_changes_needed")
    errors = sum(1 for r in results if "error" in r["status"])
    checklists = sum(1 for r in results if r["checklist_added"])
    next_steps = sum(1 for r in results if r["next_steps_added"])
    comparisons = sum(1 for r in results if r["comparison_added"])
    trust = sum(1 for r in results if r["trust_refs_added"])

    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"  Total posts processed: {total}")
    print(f"  Updated: {updated}")
    print(f"  No changes needed: {no_change}")
    print(f"  Errors: {errors}")
    print(f"  Comparison tables added: {comparisons}")
    print(f"  Quick Checklists added: {checklists}")
    print(f"  What to Do Next added: {next_steps}")
    print(f"  Trust references added/updated: {trust}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
