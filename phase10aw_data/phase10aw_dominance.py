#!/usr/bin/env python3
"""
Phase 10AV (Comparison Dominance) + 10AW (Decision Support Dominance)
Clusters: Dog Beds, Dog Harnesses
- Dog Beds: Add comparison tables (5 posts) + Quick Checklist + What to Do Next (all 14 posts)
- Dog Harnesses: Add Quick Checklist + What to Do Next (all 12 posts)
"""

import subprocess, json, time, csv, os, tempfile, re, html

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
BASE = "https://pethubonline.com/wp-json/wp/v2"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10aw_data"
CSV_PATH = os.path.join(DATA_DIR, "dog_beds_harnesses_dominance.csv")

DOG_BED_IDS = [5522, 5510, 4784, 4783, 4018, 4011, 4004, 3996, 7332, 7333, 7334, 7335, 7336, 7174]
DOG_HARNESS_IDS = [5418, 4414, 4413, 4412, 4411, 4279, 4258, 4139, 4049, 4042, 4034, 4027]
BEDS_NEEDING_TABLE = [7174, 7336, 7332, 7335, 7333]

DELAY = 2  # seconds between API calls


def api_get(endpoint):
    """Fetch from WP REST API."""
    url = f"{BASE}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    return json.loads(result.stdout)


def api_update(post_id, data):
    """Update post via WP REST API."""
    url = f"{BASE}/posts/{post_id}"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        tmpfile = f.name
    try:
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-d", f"@{tmpfile}",
             "-H", "Content-Type: application/json",
             "-X", "POST", url],
            capture_output=True, text=True, timeout=30
        )
        resp = json.loads(result.stdout)
        if 'id' in resp:
            return True
        else:
            print(f"  ERROR updating {post_id}: {resp.get('message', 'Unknown error')}")
            return False
    finally:
        os.unlink(tmpfile)


# ============================================================
# COMPARISON TABLES (10AV) — Topic-appropriate for each post
# ============================================================

COMPARISON_TABLES = {
    7174: {
        # "Dog Bed Terminology: Materials, Types, and Sizing Terms Explained"
        "table": """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Material Type</th><th>Best For</th><th>Considerations</th><th>Suitability</th></tr></thead><tbody><tr><td>Memory foam</td><td>Joint support and pressure relief</td><td>Heavier, retains heat in warm weather, higher price point</td><td>Senior dogs, large breeds, dogs with arthritis</td></tr><tr><td>High-resilience polyester fibre</td><td>Everyday comfort on a budget</td><td>Flattens over time, may need replacing sooner</td><td>Puppies, healthy adult dogs, multi-dog households</td></tr><tr><td>Orthopaedic foam (high-density)</td><td>Musculoskeletal conditions</td><td>Firmness varies by density rating, check kg/m³ specification</td><td>Post-surgery recovery, breeds prone to hip dysplasia</td></tr><tr><td>Gel-infused foam</td><td>Temperature regulation</td><td>Cooling effect diminishes over time, mid-to-high cost</td><td>Brachycephalic breeds, dogs in warm climates</td></tr><tr><td>Shredded foam blend</td><td>Adjustable loft and firmness</td><td>Can clump unevenly, needs occasional redistribution</td><td>Dogs that dig or nest before settling</td></tr><tr><td>Waterproof nylon outer</td><td>Outdoor use and incontinence</td><td>Less breathable, may feel warm, wipe-clean surface</td><td>Elderly dogs, outdoor kennels, working dogs</td></tr></tbody></table></figure>
<!-- /wp:table -->"""
    },
    7336: {
        # "Dog Bed Safety: Avoiding Hazards and Choosing Non-Toxic Materials"
        "table": """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Safety Feature</th><th>Best For</th><th>Considerations</th><th>Suitability</th></tr></thead><tbody><tr><td>OEKO-TEX certified fabric</td><td>Chemical-free sleeping environment</td><td>Look for Standard 100 label; not all beds carry certification</td><td>Puppies, dogs with skin sensitivities, allergy-prone breeds</td></tr><tr><td>Non-toxic foam (CertiPUR certified)</td><td>Avoiding off-gassing chemicals</td><td>Allow new beds to air for 48–72 hours before use</td><td>Indoor dogs, brachycephalic breeds sensitive to airborne irritants</td></tr><tr><td>Removable, machine-washable cover</td><td>Hygiene and allergen control</td><td>Check wash temperature tolerance; some shrink above 40°C</td><td>All dogs, especially those with skin conditions</td></tr><tr><td>Chew-resistant reinforced stitching</td><td>Preventing ingestion of filling</td><td>No bed is truly indestructible; supervise heavy chewers</td><td>Puppies, anxious dogs, breeds with strong chew drive</td></tr><tr><td>Anti-slip base</td><td>Preventing bed movement on hard floors</td><td>Rubber dots may leave marks on some floor finishes</td><td>Elderly dogs, dogs with mobility issues, polished floors</td></tr><tr><td>Flame-retardant-free filling</td><td>Reducing chemical exposure</td><td>Check UK fire safety labelling requirements for pet bedding</td><td>Dogs that chew or mouth their bedding frequently</td></tr></tbody></table></figure>
<!-- /wp:table -->"""
    },
    7332: {
        # "How to Wash and Dry a Dog Bed Safely"
        "table": """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Bed Type</th><th>Best Washing Method</th><th>Considerations</th><th>Suitability</th></tr></thead><tbody><tr><td>Removable cover with foam insert</td><td>Machine wash cover at 30–40°C; spot-clean foam</td><td>Never machine wash memory foam — it absorbs water and loses structure</td><td>Most common bed type; easiest ongoing maintenance</td></tr><tr><td>Fully stuffed polyester bed</td><td>Machine wash whole bed on gentle cycle</td><td>Use large-capacity machine; tumble dry low or air dry flat</td><td>Small to medium dog beds that fit your machine drum</td></tr><tr><td>Waterproof nylon bed</td><td>Wipe down surface; occasional hand wash</td><td>Avoid harsh chemicals that degrade the waterproof coating</td><td>Outdoor beds, kennel beds, incontinent dogs</td></tr><tr><td>Orthopaedic foam mattress</td><td>Vacuum surface; spot-clean with enzyme cleaner</td><td>Full submersion damages foam cell structure permanently</td><td>Senior dogs, post-surgery recovery beds</td></tr><tr><td>Heated or electric bed</td><td>Unplug and remove electrical elements; hand wash fabric only</td><td>Never submerge heating elements; check manufacturer guidance</td><td>Elderly dogs, dogs with circulation issues</td></tr><tr><td>Bolster or nest bed</td><td>Machine wash if small; hand wash raised edges separately</td><td>Bolster filling can clump — reshape while damp</td><td>Dogs that curl up or lean against edges</td></tr></tbody></table></figure>
<!-- /wp:table -->"""
    },
    7335: {
        # "Seasonal Dog Bedding: Adjusting Comfort Through the Year"
        "table": """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Season</th><th>Best Bedding Approach</th><th>Considerations</th><th>Suitability</th></tr></thead><tbody><tr><td>Spring (mild, variable)</td><td>Medium-weight bed with breathable cotton cover</td><td>Transition period — watch for dampness if bed is near open windows</td><td>Most breeds; adjust layers as temperatures fluctuate</td></tr><tr><td>Summer (warm to hot)</td><td>Elevated cooling bed or gel-infused mat</td><td>Move bed away from direct sunlight; ensure airflow underneath</td><td>Brachycephalic breeds, double-coated dogs, overweight dogs</td></tr><tr><td>Autumn (cooling, damp)</td><td>Insulated bed with moisture-wicking cover</td><td>Check for draughts at floor level; raise bed if on stone or tile</td><td>Short-coated breeds, older dogs, dogs in unheated rooms</td></tr><tr><td>Winter (cold)</td><td>Self-warming or thermal-lined bed with fleece topper</td><td>Avoid placing directly against cold external walls; check for condensation</td><td>Senior dogs, small breeds, dogs with thin coats</td></tr><tr><td>Year-round (climate-controlled home)</td><td>Standard memory foam or polyester bed</td><td>Central heating can dry skin — add a humidifier or breathable cover</td><td>Indoor dogs in well-insulated homes</td></tr><tr><td>Outdoor kennels (all seasons)</td><td>Waterproof base with removable seasonal inserts</td><td>Inspect weekly for mould, dampness, and pest activity</td><td>Working dogs, farm dogs, dogs with outdoor shelters</td></tr></tbody></table></figure>
<!-- /wp:table -->"""
    },
    7333: {
        # "Dog Bed Placement Guide: Where to Put Your Dog's Bed"
        "table": """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Placement Location</th><th>Best For</th><th>Considerations</th><th>Suitability</th></tr></thead><tbody><tr><td>Living room corner (away from doorways)</td><td>Dogs that want to be near the family</td><td>Avoid high-traffic paths; ensure the dog can rest undisturbed</td><td>Social breeds, anxious dogs that settle better near people</td></tr><tr><td>Owner’s bedroom</td><td>Dogs with separation anxiety or new puppies</td><td>May disrupt light sleepers; set boundaries early if needed</td><td>Puppies in training, recently rehomed dogs</td></tr><tr><td>Hallway or landing</td><td>Dogs that like to monitor household activity</td><td>Can be draughty; check for cold air at floor level</td><td>Guard-oriented breeds, confident dogs</td></tr><tr><td>Kitchen (away from appliances)</td><td>Easy-clean flooring for messy dogs</td><td>Avoid placing near ovens, dishwashers, or bins with food scraps</td><td>Dogs that drool or shed heavily, working breed households</td></tr><tr><td>Crate or enclosed den</td><td>Dogs that prefer a secure, enclosed space</td><td>Ensure adequate ventilation; size bed to fit crate dimensions exactly</td><td>Crate-trained dogs, dogs that dig or nest</td></tr><tr><td>Conservatory or sunroom</td><td>Warmth-seeking dogs in cooler months</td><td>Can overheat in summer — provide shade and an alternative cool spot</td><td>Small breeds, elderly dogs, short-coated dogs in winter</td></tr></tbody></table></figure>
<!-- /wp:table -->"""
    },
}


# ============================================================
# QUICK CHECKLISTS (10AW) — Tailored per post topic
# ============================================================

def get_quick_checklist(post_id, title, cluster):
    """Generate topic-appropriate Quick Checklist."""

    beds_checklists = {
        5522: [
            "Consult your vet before choosing an orthopaedic bed if your dog has a diagnosed joint condition",
            "Check the foam density rating — look for at least 35 kg/m³ for meaningful support",
            "Ensure the bed is large enough for your dog to stretch out fully without hanging off the edges",
            "Confirm the cover is removable and machine-washable for ongoing hygiene",
            "Place the bed on a flat, draught-free surface away from stairs your dog must navigate",
            "Monitor your dog’s comfort for the first week and note any changes in mobility or willingness to use the bed",
        ],
        5510: [
            "Measure your dog from nose to tail base while they lie in their preferred sleeping position",
            "Add 15–20 cm to each dimension to allow comfortable movement",
            "Check the internal dimensions of the bed, not just the outer measurements",
            "If choosing a bolster bed, account for the space the raised edges take from the sleeping area",
            "For puppies, size for their expected adult weight and add a temporary filler insert",
            "When unsure between two sizes, always choose the larger option",
            "Keep the receipt so you can exchange if the fit is not right",
        ],
        4784: [
            "Identify your dog’s sleeping style before choosing a material — side-sleepers need more cushioning",
            "Check foam density ratings in kg/m³ rather than relying on vague marketing terms",
            "Prioritise removable, washable covers regardless of which filling you choose",
            "Allow new memory foam beds to air for 48–72 hours before first use to reduce off-gassing",
            "Consider a waterproof liner if your dog is elderly, a puppy, or prone to drooling",
            "Replace any bed where the filling has flattened to less than half its original height",
        ],
        4783: [
            "Measure your dog while lying stretched out, not standing — this gives the true sleeping footprint",
            "Add a minimum of 15 cm to length and width for comfortable repositioning",
            "Check the manufacturer’s weight and size recommendations against your dog’s actual measurements",
            "Test the bed by placing it on the floor and watching if your dog can fully turn around on it",
            "For multi-dog households, provide one bed per dog plus one spare to reduce competition",
            "Re-measure growing puppies every four to six weeks until they reach adult size",
        ],
        4018: [
            "Choose a machine-washable bed — puppies have frequent accidents during house training",
            "Avoid expensive beds until your puppy finishes teething, typically around six months",
            "Size the bed for your puppy’s expected adult dimensions if your breed’s growth is predictable",
            "Place the bed in a quiet corner where your puppy can retreat and rest undisturbed",
            "Remove any loose decorative elements that could be chewed off and swallowed",
            "Introduce the bed gradually with treats and praise to build positive associations",
        ],
        4011: [
            "Check your dog shows signs of overheating before investing in a cooling bed — panting, seeking cool floors",
            "Compare gel-mat, elevated mesh, and pressure-activated cooling mechanisms to find what suits your dog",
            "Ensure any gel mat has a puncture-resistant outer layer if your dog is a chewer",
            "Place the cooling bed away from direct sunlight and radiators for maximum effectiveness",
            "Clean the surface regularly — cooling beds collect fur and dust that reduce their efficiency",
            "Have a standard bed available alongside the cooling option for colder months",
        ],
        4004: [
            "Ask your vet if an orthopaedic bed is appropriate for your dog’s specific condition",
            "Look for foam density of at least 35 kg/m³ — lower densities offer limited joint support",
            "Choose a bed with low entry points if your dog has reduced mobility",
            "Ensure the cover zips off for washing and the waterproof liner protects the foam",
            "Position the bed on a non-slip surface to prevent it sliding when your dog steps on or off",
            "Monitor pressure points for redness or hair loss during the first fortnight of use",
        ],
        3996: [
            "Identify your dog’s preferred sleeping position — curled, sprawled, or leaning against a surface",
            "Set a realistic budget that accounts for replacing the bed every two to three years",
            "Prioritise washability and durability over decorative features",
            "Check that the bed dimensions match your dog’s measurements plus 15–20 cm extra",
            "Read the care label before purchasing to confirm it fits your washing routine",
            "If your dog has joint issues, consider an orthopaedic option regardless of age",
        ],
        7332: [
            "Check the care label before washing — not all beds tolerate machine washing",
            "Remove loose fur with a lint roller or vacuum before putting the cover in the machine",
            "Use a pet-safe, fragrance-free detergent to avoid skin irritation",
            "Wash covers at 30–40°C unless the label specifically permits a higher temperature",
            "Never machine wash memory foam — spot-clean with an enzyme cleaner instead",
            "Dry beds thoroughly before returning them to use — damp bedding encourages mould and bacteria",
            "Aim to wash covers every one to two weeks and deep-clean the entire bed monthly",
        ],
        7333: [
            "Choose a spot away from high-traffic areas and doorways so your dog can rest undisturbed",
            "Check floor-level temperature — tile and stone floors are colder, so raise or insulate the bed",
            "Avoid placing beds directly next to radiators, as overheating disrupts sleep quality",
            "Ensure your dog can see part of the household from their bed to reduce anxiety",
            "Keep the bed away from external doors and windows that cause draughts",
            "Provide at least one bed option per floor of your home for dogs with mobility concerns",
        ],
        7334: [
            "Start bed training from day one using treats and a calm, positive tone",
            "Place the bed in a quiet area where your puppy can observe you without being in the way",
            "Use a consistent command such as ‘bed’ or ‘settle’ each time you direct them to the bed",
            "Reward your puppy every time they go to the bed voluntarily during the first two weeks",
            "Avoid forcing your puppy onto the bed — let them choose it to build a positive association",
            "Keep initial bed sessions short (five to ten minutes) and gradually extend the duration",
        ],
        7335: [
            "Assess your dog’s comfort at the start of each season — look for signs of overheating or shivering",
            "Swap to a breathable cotton or mesh cover for summer and a fleece topper for winter",
            "Move the bed away from direct sunlight in summer and away from draughty windows in winter",
            "Check floor-level temperature with your hand — if it feels cold, elevate or insulate the bed",
            "Wash bedding more frequently in autumn and spring when dogs shed their seasonal coats",
            "Keep a lightweight spare bed available for transition periods when weather changes quickly",
        ],
        7336: [
            "Inspect the bed weekly for loose threads, torn fabric, or exposed filling your dog could ingest",
            "Choose beds with OEKO-TEX or CertiPUR-certified materials to minimise chemical exposure",
            "Allow new beds to air in a ventilated room for 48–72 hours before your dog uses them",
            "Avoid beds with small, detachable decorative elements that present a choking hazard",
            "Replace any bed where stitching has come apart or filling is accessible through gaps",
            "Position the bed away from electrical cables, curtain cords, and other household hazards",
            "If your dog chews their bed, supervise initial use and consider a chew-resistant design",
        ],
        7174: [
            "Familiarise yourself with foam density ratings (kg/m³) before comparing bed specifications",
            "Learn the difference between internal and external bed dimensions to avoid sizing mistakes",
            "Understand what ‘orthopaedic’ means in pet bedding — it is not a regulated term in the UK",
            "Check whether ‘waterproof’ refers to a removable liner or the entire bed construction",
            "Know your dog’s sleeping style terminology — curler, sprawler, or side-sleeper — to match bed shape",
            "Ask manufacturers to clarify vague terms like ‘premium’ or ‘luxury’ with measurable specifications",
        ],
    }

    harness_checklists = {
        5418: [
            "Identify your primary need — everyday walking, no-pull training, or activity-specific use",
            "Measure your dog’s girth behind the front legs with a flexible tape before shopping",
            "Choose a harness with at least two adjustment points for a secure, comfortable fit",
            "Check that the harness does not restrict shoulder movement during normal walking",
            "Ensure all buckles and clips are easy to operate with one hand for quick fitting",
            "Inspect the harness monthly for fraying, stretched elastic, or damaged clips",
        ],
        4414: [
            "Consider your dog’s breed, size, and any respiratory or tracheal concerns before choosing",
            "Use a harness for dogs that pull — collars concentrate force on the neck and throat",
            "A flat collar is sufficient for calm dogs that walk on a loose lead",
            "Brachycephalic breeds (pugs, bulldogs, etc.) should always use a harness, not a collar",
            "Attach ID tags to a collar even if you walk with a harness — collars carry legal identification",
            "Try both options and observe your dog’s comfort and gait before committing",
        ],
        4413: [
            "Use a flexible fabric tape measure, not a rigid ruler or builder’s tape",
            "Measure girth around the widest part of the ribcage, just behind the front legs",
            "Measure neck circumference at the base where the collar would sit",
            "Take chest length from the base of the neck to the start of the ribcage",
            "Record measurements in centimetres and compare against the manufacturer’s size chart",
            "Re-measure every three months for growing puppies or dogs that have gained or lost weight",
        ],
        4412: [
            "Check whether the harness uses front-clip, dual-clip, or tightening-based no-pull mechanics",
            "Ensure the front clip sits on the chest bone, not off to one side",
            "Pair the harness with consistent loose-lead training for lasting behaviour change",
            "Avoid harnesses that restrict shoulder movement during normal walking pace",
            "Monitor for rubbing under the front legs during the first week of use",
            "A no-pull harness is a management tool — it works alongside training, not instead of it",
        ],
        4411: [
            "Match the harness type to your dog’s size, build, and walking behaviour",
            "Ensure a two-finger gap between every strap and your dog’s body",
            "Check that the harness does not ride up into the armpits or press on the windpipe",
            "Introduce the harness gradually indoors with treats before using it on walks",
            "Inspect all hardware (buckles, D-rings, clips) before each walk for signs of wear",
            "Replace the harness if your dog outgrows it or if any strap shows fraying",
        ],
        4279: [
            "Choose a harness specifically designed for cats — dog harnesses do not fit feline body shapes",
            "Measure your cat’s girth behind the front legs and neck circumference before ordering",
            "Start harness training indoors, allowing your cat to wear it for short sessions with treats",
            "Ensure the harness is escape-proof — cats can back out of poorly fitted designs",
            "Attach the lead to a back-mounted D-ring to avoid pressure on the throat",
            "Never leave your cat unsupervised while wearing a harness, indoors or out",
        ],
        4258: [
            "Choose a collar with a quick-release safety breakaway clasp to prevent strangulation",
            "Ensure you can fit two fingers between the collar and your cat’s neck",
            "Attach an ID tag with your contact details — this is a legal requirement in many areas",
            "Check the collar weekly for tightness, especially on growing kittens",
            "Avoid collars with bells if your cat shows stress — some cats find the noise distressing",
            "Reflective or high-visibility collars improve safety for cats that go outdoors at night",
        ],
        4139: [
            "Match lead length to your training goal — 3–5 m for recall, 1.2–1.8 m for heel work",
            "Choose a lightweight material that does not weigh down a small dog’s harness",
            "Use a long line only in safe, open areas away from roads and obstacles",
            "Never wrap a long line around your hand — use a knot-stop system or hold in loops",
            "Pair the training lead with a harness, not a collar, to avoid neck strain during stops",
            "Inspect the clip and fabric before each session for signs of wear or corrosion",
        ],
        4049: [
            "Start with a lightweight, adjustable collar that grows with your puppy",
            "Fit the collar so two fingers slide easily between the collar and your puppy’s neck",
            "Attach an ID tag immediately — it is a legal requirement under the Control of Dogs Order 1992",
            "Check the fit weekly during growth spurts, typically every one to two weeks for young puppies",
            "Choose a flat buckle or quick-release clasp — avoid chain or slip collars for puppies",
            "Introduce the collar for short periods indoors before using it outdoors",
        ],
        4042: [
            "Choose a lead length appropriate for your walking environment — 1.2 m for pavements, longer for open spaces",
            "Match lead width and clip size to your dog’s weight to avoid equipment failure",
            "Leather leads soften with use and are durable; nylon is lightweight and weather-resistant",
            "Avoid retractable leads near roads or in crowded areas — they reduce your control",
            "Check the clip mechanism before each walk by opening and closing it several times",
            "Wash fabric leads regularly to remove bacteria, salt, and grit that weaken the material",
        ],
        4034: [
            "Identify whether you need front-clip, dual-clip, or head-collar style no-pull management",
            "Ensure the front attachment point sits centrally on the chest for even pressure distribution",
            "Combine the harness with positive reinforcement training for lasting behaviour change",
            "Check for rubbing marks under the front legs after the first three to five walks",
            "Adjust both chest and belly straps so you can fit two fingers under each",
            "A no-pull harness is a training aid — transition to a standard harness once lead manners improve",
        ],
        4027: [
            "Decide whether a collar, harness, or both suits your dog’s breed, size, and temperament",
            "Measure your dog’s neck and girth before ordering — do not guess from breed averages",
            "Keep a flat collar with ID tags on your dog at all times, even if you walk with a harness",
            "Check that no equipment restricts breathing, shoulder movement, or natural gait",
            "Replace any collar or harness with visible wear, stretched webbing, or damaged hardware",
            "For dogs that pull, start with a front-clip harness and work on loose-lead training in parallel",
        ],
    }

    if cluster == "Dog Beds":
        items = beds_checklists.get(post_id, [])
    else:
        items = harness_checklists.get(post_id, [])

    if not items:
        return None

    li_items = "".join(f"<li>{item}</li>" for item in items)
    return f"""<!-- wp:group {{"style":{{"color":{{"background":"#f5f3ff"}},"border":{{"radius":"6px","width":"1px","color":"#ddd6fe"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#ddd6fe;border-width:1px;border-radius:6px;background-color:#f5f3ff;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} --><h4 class="wp-block-heading">Quick Checklist</h4><!-- /wp:heading -->
<!-- wp:list --><ul class="wp-block-list">{li_items}</ul><!-- /wp:list -->
</div>
<!-- /wp:group -->"""


# ============================================================
# WHAT TO DO NEXT (10AW) — Tailored per post topic
# ============================================================

def get_next_steps(post_id, title, cluster):
    """Generate topic-appropriate What to Do Next block."""

    beds_next = {
        5522: [
            "Book a vet check-up to assess your dog’s joint health and get specific bedding recommendations.",
            "Measure your dog in their preferred sleeping position and note the dimensions needed.",
            "Research beds with a foam density of at least 35 kg/m³ and removable, washable covers.",
            "Set up the new bed in a quiet, draught-free location and observe your dog’s comfort over the first week.",
        ],
        5510: [
            "Measure your dog from nose to tail base while they lie in their most common sleeping position.",
            "Add 15–20 cm to each measurement and write down the minimum bed dimensions you need.",
            "Compare your measurements against the internal dimensions listed on bed product pages.",
            "Order the bed, and if the fit is not right, exchange for the next size up within the return window.",
        ],
        4784: [
            "Identify your dog’s sleeping habits — do they curl up, sprawl, or lean against something?",
            "Match those habits to the material type that provides the right level of support and warmth.",
            "Check any shortlisted beds for foam density ratings, cover washability, and certification labels.",
            "Purchase a bed and allow it to air for 48–72 hours before your dog uses it.",
        ],
        4783: [
            "Measure your dog in their favourite resting position using a flexible tape measure.",
            "Compare your measurements to at least three beds’ internal dimension specifications.",
            "Choose the bed that gives at least 15 cm extra space on each side of your dog.",
            "Place the bed in your chosen location and watch whether your dog fits comfortably with room to turn.",
        ],
        4018: [
            "Estimate your puppy’s adult size using breed growth charts or your vet’s guidance.",
            "Choose a machine-washable bed that is affordable enough to replace after the teething phase.",
            "Set up the bed in your puppy’s designated sleeping area with a familiar-smelling blanket.",
            "Begin bed training on day one using treats, praise, and a consistent ‘bed’ command.",
        ],
        4011: [
            "Observe whether your dog actively seeks cool surfaces during warm weather — this confirms the need.",
            "Compare gel-mat, elevated mesh, and pressure-activated cooling mechanisms for your dog’s size.",
            "Position the cooling bed in a shaded area away from direct sunlight and heat sources.",
            "Monitor your dog’s behaviour during the first few warm days to confirm they are using and benefiting from the bed.",
        ],
        4004: [
            "Speak with your vet to confirm whether an orthopaedic bed is appropriate for your dog’s condition.",
            "Measure your dog and compare against beds with at least 35 kg/m³ foam density.",
            "Choose a bed with low side entry points if your dog has limited mobility.",
            "Place the bed on a non-slip surface and observe your dog’s comfort and willingness to use it over two weeks.",
        ],
        3996: [
            "Identify your dog’s preferred sleeping position and note their nose-to-tail measurement.",
            "Set a budget that allows for a quality bed you will replace every two to three years.",
            "Narrow your options to beds with removable, washable covers and appropriate dimensions.",
            "Order your chosen bed, set it up in a quiet spot, and allow your dog to explore it at their own pace.",
        ],
        7332: [
            "Check your current bed’s care label and note the maximum wash temperature and drying instructions.",
            "Vacuum or lint-roll loose fur from the bed before the first wash.",
            "Wash the cover with a pet-safe, fragrance-free detergent at the recommended temperature.",
            "Dry the bed thoroughly — feel inside seams and padding to confirm no damp remains before returning it to use.",
        ],
        7333: [
            "Walk through your home and identify two or three potential spots that are quiet, draught-free, and away from direct heat.",
            "Check floor-level temperature at each spot by placing your hand flat on the floor for 30 seconds.",
            "Place the bed in your top choice location and observe whether your dog settles there voluntarily.",
            "If your dog consistently avoids the spot, move the bed to your second option and repeat the observation.",
        ],
        7334: [
            "Set up the bed in a consistent location before your puppy arrives or before you begin training.",
            "Introduce the bed with treats placed on it, allowing your puppy to approach voluntarily.",
            "Use a single, consistent command each time you direct your puppy to the bed.",
            "Practise short sessions (five to ten minutes) several times a day for the first two weeks, then gradually extend.",
        ],
        7335: [
            "Check your dog’s current bedding setup and assess whether it suits the approaching season.",
            "Purchase a breathable summer cover and a fleece winter topper so you are prepared for transitions.",
            "Adjust the bed’s position — move away from windows in summer and away from draughty spots in winter.",
            "Set a calendar reminder to swap bedding covers and inspect the bed at each seasonal change.",
        ],
        7336: [
            "Inspect your dog’s current bed for loose threads, torn fabric, and exposed or accessible filling.",
            "Check the label for safety certifications such as OEKO-TEX Standard 100 or CertiPUR.",
            "Remove or replace any bed with detachable decorative elements or damaged stitching.",
            "Position the bed away from electrical cables, blind cords, and other household hazards.",
            "Set a weekly reminder to do a quick visual safety check of the bed and surrounding area.",
        ],
        7174: [
            "Review the key terms in this glossary and note which ones are relevant to your dog’s needs.",
            "Use the terminology to compare bed specifications more accurately when shopping.",
            "Ask manufacturers to clarify any vague marketing claims using the measurable terms you have learned.",
            "Bookmark this glossary so you can refer back when reading bed reviews or product descriptions.",
        ],
    }

    harness_next = {
        5418: [
            "Measure your dog’s girth and neck circumference using a flexible tape measure.",
            "Match your dog’s size and walking behaviour to the harness type that suits them.",
            "Try the harness on your dog indoors and check for a two-finger gap under every strap.",
            "Take a short test walk and watch for rubbing, restricted movement, or discomfort.",
        ],
        4414: [
            "Assess your dog’s walking behaviour — do they pull, walk calmly, or have respiratory concerns?",
            "Choose a harness if your dog pulls or has any neck, throat, or breathing issues.",
            "Keep a flat collar with ID tags on your dog regardless of whether you walk with a harness.",
            "Try your chosen option on a short walk and observe your dog’s comfort and movement.",
        ],
        4413: [
            "Gather a flexible fabric tape measure, a pen, and paper before you start.",
            "Measure girth, neck, and chest length while your dog stands naturally on a flat surface.",
            "Write down all measurements in centimetres and compare them to the manufacturer’s size chart.",
            "Order the size indicated by the chart, and if between sizes, choose the larger option.",
        ],
        4412: [
            "Identify the type of no-pull mechanism that suits your dog — front-clip, dual-clip, or tightening.",
            "Fit the harness so the front clip sits centrally on the chest bone.",
            "Begin loose-lead training exercises alongside harness use for lasting results.",
            "Check for rubbing under the front legs after the first three walks and adjust straps if needed.",
        ],
        4411: [
            "Determine your primary use case — daily walks, training, running, or car travel.",
            "Measure your dog accurately and select a harness with at least two adjustment points.",
            "Introduce the harness indoors with treats before attaching a lead.",
            "Walk a short route on the first outing and check fit, comfort, and hardware function afterwards.",
        ],
        4279: [
            "Measure your cat’s girth and neck with a flexible tape while they stand calmly.",
            "Choose a cat-specific harness with escape-proof design and a back-mounted D-ring.",
            "Let your cat wear the harness indoors for short sessions over several days before going outside.",
            "Take your first outdoor walk in a quiet, enclosed garden — not a busy pavement.",
        ],
        4258: [
            "Measure your cat’s neck circumference and ensure the collar has a breakaway safety clasp.",
            "Attach an ID tag with your name, phone number, and postcode before putting the collar on.",
            "Fit the collar so two fingers slide comfortably between it and your cat’s neck.",
            "Check the fit weekly, especially for growing kittens, and adjust or replace as needed.",
        ],
        4139: [
            "Decide what you are training — recall, heel work, or general manners — and choose the length accordingly.",
            "Pair the training lead with a well-fitted harness rather than a collar.",
            "Practise in a secure, open area away from roads before using the lead near traffic.",
            "Inspect the lead clip and fabric before each session for wear or damage.",
        ],
        4049: [
            "Measure your puppy’s neck and buy an adjustable collar that allows for growth.",
            "Attach an ID tag with your contact details — this is a legal requirement in the UK.",
            "Let your puppy wear the collar indoors for short periods before attaching a lead.",
            "Re-check the collar fit every week during your puppy’s rapid growth phase.",
        ],
        4042: [
            "Assess your typical walking environment — pavement, park, woodland — and match the lead length.",
            "Choose a lead material and clip size appropriate for your dog’s weight.",
            "Test the clip mechanism before your first walk to ensure it opens and closes smoothly.",
            "Establish a routine of checking the lead for wear after every five to ten uses.",
        ],
        4034: [
            "Confirm that pulling is a training issue, not a pain response — consult your vet if unsure.",
            "Select a front-clip or dual-clip harness sized to your dog’s girth measurement.",
            "Fit the harness, check the two-finger rule on all straps, and take a short test walk.",
            "Begin structured loose-lead training sessions alongside harness use to build lasting habits.",
        ],
        4027: [
            "Decide whether your dog needs a collar, harness, or both based on their behaviour and breed.",
            "Measure your dog’s neck and girth accurately before browsing products.",
            "Order equipment with adjustment points and test the fit indoors before your first walk.",
            "Keep a flat collar with ID tags on your dog at all times, alongside any walking harness.",
        ],
    }

    if cluster == "Dog Beds":
        items = beds_next.get(post_id, [])
    else:
        items = harness_next.get(post_id, [])

    if not items:
        return None

    li_items = "".join(f"<li>{item}</li>" for item in items)
    return f"""<!-- wp:group {{"style":{{"color":{{"background":"#f0fdfa"}},"border":{{"radius":"6px","width":"1px","color":"#99f6e4"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#99f6e4;border-width:1px;border-radius:6px;background-color:#f0fdfa;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} --><h4 class="wp-block-heading">What to Do Next</h4><!-- /wp:heading -->
<!-- wp:list {{"ordered":true}} --><ol class="wp-block-list">{li_items}</ol><!-- /wp:list -->
</div>
<!-- /wp:group -->"""


def find_insertion_point(content):
    """
    Find the insertion point before Common Mistakes / When to Seek Help /
    Beginner Recs / Key Terms / Key Takeaways / Editorial Standards / trust footer.

    Block order: ... Quick Checklist ... What to Do Next ... Common Mistakes ...
    When to Seek Help ... Beginner Recs ... Key Terms ... Key Takeaways ... [trust footer]
    """
    markers = [
        'Common Mistakes',
        'When to Seek Professional Help',
        'When to Seek Help',
        'Beginner Recommendations',
        'Decision Summary',
        'Why We Reference',
        'Key Terms',
        'Key Takeaways',
        'Our Editorial Standards',
        'editorial-trust-footer',
    ]

    for marker in markers:
        idx = content.find(marker)
        if idx == -1:
            continue

        search_region = content[:idx]

        # Look for the nearest block-level container start
        wp_group_idx = search_region.rfind('<!-- wp:group')
        div_group_idx = search_region.rfind('<div class="wp-block-group')
        hr_idx = search_region.rfind('<hr class="wp-block-separator')
        h2_idx = search_region.rfind('<h2 class="wp-block-heading">')

        if marker == 'editorial-trust-footer':
            ft_idx = search_region.rfind('<div class="editorial-trust-footer')
            if ft_idx != -1:
                return ft_idx

        candidates = [i for i in [wp_group_idx, div_group_idx, hr_idx, h2_idx] if i != -1]
        if candidates:
            best = max(candidates)
            if idx - best < 500:
                return best

    return max(0, len(content) - 500)


def find_table_insertion_point(content):
    """Find a good point to insert the comparison table — before support blocks."""
    return find_insertion_point(content)


def process_post(post_id, cluster, csv_writer):
    """Process a single post: fetch, add missing blocks, update."""
    print(f"\n{'='*60}")
    print(f"Processing post {post_id} ({cluster})...")

    data = api_get(f"posts/{post_id}?context=edit&_fields=id,title,content")
    title = data['title']['raw']
    content = data['content']['raw']

    print(f"  Title: {title}")
    print(f"  Content length: {len(content)}")

    comparison_added = False
    checklist_added = False
    next_steps_added = False
    modified = False

    # 1. COMPARISON TABLE (only for dog beds needing tables)
    if post_id in BEDS_NEEDING_TABLE and 'wp-block-table' not in content:
        table_data = COMPARISON_TABLES.get(post_id)
        if table_data:
            table_html = table_data['table']
            insert_idx = find_table_insertion_point(content)
            table_block = f"\n\n<!-- wp:heading {{\"level\":3}} -->\n<h3 class=\"wp-block-heading\">Quick Comparison</h3>\n<!-- /wp:heading -->\n\n{table_html}\n\n"
            content = content[:insert_idx] + table_block + content[insert_idx:]
            comparison_added = True
            modified = True
            print(f"  + Added comparison table")

    # 2. QUICK CHECKLIST
    if 'Quick Checklist' not in content:
        checklist_block = get_quick_checklist(post_id, title, cluster)
        if checklist_block:
            insert_idx = find_insertion_point(content)
            content = content[:insert_idx] + "\n\n" + checklist_block + "\n\n" + content[insert_idx:]
            checklist_added = True
            modified = True
            print(f"  + Added Quick Checklist")

    # 3. WHAT TO DO NEXT
    if 'What to Do Next' not in content:
        next_block = get_next_steps(post_id, title, cluster)
        if next_block:
            if 'Quick Checklist' in content:
                cl_idx = content.find('Quick Checklist')
                end_search = content[cl_idx:]
                end_group = end_search.find('</div>\n<!-- /wp:group -->')
                if end_group == -1:
                    end_group = end_search.find('</div>\r\n<!-- /wp:group -->')
                if end_group != -1:
                    insert_idx = cl_idx + end_group + len('</div>\n<!-- /wp:group -->')
                else:
                    insert_idx = find_insertion_point(content)
            else:
                insert_idx = find_insertion_point(content)

            content = content[:insert_idx] + "\n\n" + next_block + "\n\n" + content[insert_idx:]
            next_steps_added = True
            modified = True
            print(f"  + Added What to Do Next")

    status = "no_changes"
    if modified:
        time.sleep(DELAY)
        success = api_update(post_id, {"content": content})
        if success:
            status = "updated"
            print(f"  => Post {post_id} UPDATED successfully")
        else:
            status = "error"
            print(f"  => ERROR updating post {post_id}")
    else:
        print(f"  => No changes needed for post {post_id}")
        status = "already_complete"

    csv_writer.writerow([
        post_id, title, cluster,
        comparison_added, checklist_added, next_steps_added,
        status
    ])

    time.sleep(DELAY)
    return status


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['id', 'title', 'cluster', 'comparison_added', 'checklist_added', 'next_steps_added', 'status'])

        results = {"updated": 0, "already_complete": 0, "error": 0, "no_changes": 0}

        print("\n" + "=" * 70)
        print("PROCESSING DOG BEDS CLUSTER (14 posts)")
        print("=" * 70)
        for pid in DOG_BED_IDS:
            status = process_post(pid, "Dog Beds", writer)
            results[status] = results.get(status, 0) + 1

        print("\n" + "=" * 70)
        print("PROCESSING DOG HARNESSES CLUSTER (12 posts)")
        print("=" * 70)
        for pid in DOG_HARNESS_IDS:
            status = process_post(pid, "Dog Harnesses", writer)
            results[status] = results.get(status, 0) + 1

    print("\n" + "=" * 70)
    print("PHASE 10AV + 10AW COMPLETE")
    print("=" * 70)
    print(f"  Updated:          {results['updated']}")
    print(f"  Already complete:  {results['already_complete']}")
    print(f"  Errors:           {results['error']}")
    print(f"  No changes:       {results['no_changes']}")
    print(f"  CSV log:          {CSV_PATH}")


if __name__ == "__main__":
    main()
