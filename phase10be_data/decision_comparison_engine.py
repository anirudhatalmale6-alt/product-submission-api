#!/usr/bin/env python3
"""
Phase 10BE (Decision Support Dominance) + 10BF (Comparison Saturation)
Dog Food, Dog Beds, Puppy Care, Dog Health clusters
pethubonline.com
"""

import subprocess, json, csv, time, re, os, tempfile, html

# ── Config ──────────────────────────────────────────────────────────────
WP_API = "https://pethubonline.com/wp-json/wp/v2"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"

CATEGORIES = {
    "Dog Food": 1467,
    "Dog Beds": 1401,
    "Puppy Care": 1442,
    "Dog Health": 1450,
}

SKIP_IDS = {3836, 3837, 3838, 5467, 3839, 5510, 3960, 5522, 4160, 5460,
            5520, 5417, 4004, 4153, 4103, 4110, 4167}

CSV_PATH = "/var/lib/freelancer/projects/40416335/phase10be_data/decision_comparison_dogfood_beds_puppy_health.csv"

# ── API Helpers ─────────────────────────────────────────────────────────
def api_get(endpoint):
    url = f"{WP_API}/{endpoint}"
    r = subprocess.run(
        ["curl", "-s", "--compressed", "-u", f"{WP_USER}:{WP_PASS}", url],
        capture_output=True, text=True
    )
    return json.loads(r.stdout)

def api_put(post_id, data):
    url = f"{WP_API}/posts/{post_id}"
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(data, tmp)
    tmp.close()
    r = subprocess.run(
        ["curl", "-s", "--compressed", "-X", "POST",
         "-u", f"{WP_USER}:{WP_PASS}",
         "-H", "Content-Type: application/json",
         "-d", f"@{tmp.name}", url],
        capture_output=True, text=True
    )
    os.unlink(tmp.name)
    resp = json.loads(r.stdout)
    if "id" in resp:
        return True
    print(f"  ERROR updating {post_id}: {r.stdout[:300]}")
    return False

def fetch_all_posts():
    posts = {}
    for name, cid in CATEGORIES.items():
        page = 1
        while True:
            data = api_get(f"posts?categories={cid}&status=publish&per_page=100&page={page}&context=edit")
            if not isinstance(data, list) or len(data) == 0:
                break
            for p in data:
                if p["id"] not in SKIP_IDS and p["id"] not in posts:
                    posts[p["id"]] = {
                        "id": p["id"],
                        "title": html.unescape(p["title"]["raw"]),
                        "cluster": name,
                        "raw": p["content"]["raw"],
                    }
            if len(data) < 100:
                break
            page += 1
    return posts


# ── Block Templates ─────────────────────────────────────────────────────

def make_evaluation_block(items):
    """bg #f0f9ff, border #bae6fd (sky blue)"""
    li = "".join(f"<li>{it}</li>" for it in items)
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#f0f9ff"}},"border":{{"radius":"6px","width":"1px","color":"#bae6fd"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#bae6fd;border-width:1px;border-radius:6px;background-color:#f0f9ff;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">How to Evaluate</h4>
<!-- /wp:heading -->
<!-- wp:list -->
<ul class="wp-block-list">{li}</ul>
<!-- /wp:list -->
</div>
<!-- /wp:group -->'''


def make_troubleshooting_block(items):
    """bg #fefce8, border #fde047 (yellow)"""
    li = "".join(f"<li>{it}</li>" for it in items)
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#fefce8"}},"border":{{"radius":"6px","width":"1px","color":"#fde047"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#fde047;border-width:1px;border-radius:6px;background-color:#fefce8;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">Common Problems and Solutions</h4>
<!-- /wp:heading -->
<!-- wp:list -->
<ul class="wp-block-list">{li}</ul>
<!-- /wp:list -->
</div>
<!-- /wp:group -->'''


def make_scenario_block(items):
    """bg #fdf4ff, border #e879f9 (fuchsia)"""
    li = "".join(f"<li>{it}</li>" for it in items)
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#fdf4ff"}},"border":{{"radius":"6px","width":"1px","color":"#e879f9"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#e879f9;border-width:1px;border-radius:6px;background-color:#fdf4ff;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">Which Option Suits Your Situation</h4>
<!-- /wp:heading -->
<!-- wp:list -->
<ul class="wp-block-list">{li}</ul>
<!-- /wp:list -->
</div>
<!-- /wp:group -->'''


def make_comparison_table(caption, headers, rows):
    """wp:table is-style-stripes"""
    thead = "<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>"
    tbody_rows = ""
    for row in rows:
        tbody_rows += "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
    return f'''<!-- wp:table {{"className":"is-style-stripes"}} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr>{"".join(f"<th>{h}</th>" for h in headers)}</tr></thead><tbody>{tbody_rows}</tbody></table><figcaption class="wp-element-caption">{caption}</figcaption></figure>
<!-- /wp:table -->'''


# ── Cluster-specific content ────────────────────────────────────────────

EVALUATION_CONTENT = {
    "Dog Food": {
        "default": [
            "Ingredient transparency — check whether the label lists specific protein sources (e.g., chicken, lamb) rather than vague terms like 'meat derivatives'",
            "Nutritional adequacy statement — look for confirmation the food meets FEDIAF or AAFCO guidelines for the intended life stage",
            "Digestibility indicators — observe stool quality, consistency, and volume as a practical measure of how well your dog processes the food",
            "Protein-to-filler ratio — compare the percentage of named animal protein against cereals, grains, or plant-based fillers",
            "Allergen risk assessment — identify common allergens (wheat, soya, dairy) and cross-reference with any known sensitivities in your dog",
            "Caloric density relative to feeding guidelines — ensure the recommended portion size aligns with your dog's weight management needs",
        ],
    },
    "Dog Beds": {
        "default": [
            "Size appropriateness — measure your dog from nose to tail base whilst lying in their preferred sleeping position, then add 15–20 cm for comfort",
            "Material safety and certification — check for OEKO-TEX or equivalent certification confirming no harmful chemicals in fabrics and foams",
            "Washability and hygiene — assess whether the cover is removable and machine-washable, and whether the inner filling can be spot-cleaned",
            "Joint support level — for older or arthritic dogs, evaluate foam density (minimum 35 kg/m³ for genuine orthopaedic benefit) per BVA guidance",
            "Durability under daily use — consider stitching quality, zip strength, and whether the base has a non-slip surface",
            "Temperature regulation — check whether the bed uses breathable fabrics for summer or insulating materials for winter months",
        ],
        "cooling": [
            "Cooling mechanism type — distinguish between gel-infused foam, elevated airflow designs, and phase-change fabric technologies",
            "Heat dissipation duration — assess how long the cooling effect lasts under sustained body contact before it reaches ambient temperature",
            "Material breathability — check whether the cover fabric wicks moisture and allows air circulation underneath",
            "Weight capacity relative to cooling surface — verify the cooling layer maintains effectiveness under your dog's body weight",
            "Indoor versus outdoor suitability — determine whether the cooling bed is designed for climate-controlled rooms or direct sunlight",
        ],
        "washing": [
            "Machine-wash compatibility — check maximum temperature, spin speed, and whether the cover survives repeated wash cycles without shrinking",
            "Drying method requirements — assess whether the bed needs air-drying only or can tolerate tumble-drying on a low heat setting",
            "Stain resistance baseline — evaluate the fabric's initial resistance to common soiling (mud, drool, urine) before washing becomes necessary",
            "Fill material integrity after washing — determine whether foam or fibre filling clumps, compresses, or retains shape through wash cycles",
            "Frequency guidelines — balance hygiene needs (fortnightly minimum per PDSA advice) against material degradation from over-washing",
        ],
        "placement": [
            "Draught exposure — assess whether the chosen spot is protected from cold air currents near doors, windows, or corridors",
            "Noise and foot traffic levels — evaluate how much household activity passes through the area and whether your dog can rest undisturbed",
            "Floor surface suitability — check whether hard floors need a non-slip base and whether carpeted areas trap allergens beneath the bed",
            "Temperature stability — ensure the location maintains a consistent temperature between 18–22°C as recommended for canine comfort",
            "Access for elderly or injured dogs — confirm the bed location does not require jumping, climbing stairs, or navigating obstacles",
        ],
        "safety": [
            "Chewing and ingestion risk — assess whether any components (zips, buttons, loose threads) could be swallowed and cause obstruction",
            "Flame retardant transparency — check that any fire-retardant treatments used comply with UK furniture safety regulations (BS 7177) without harmful chemicals",
            "Off-gassing period — new foam beds may release volatile organic compounds; ventilate for 48–72 hours before first use",
            "Allergen potential — evaluate whether fill materials or cover fabrics are hypoallergenic, especially for dogs with sensitive skin",
            "Structural collapse risk — check the bed supports your dog's weight without bottoming out, which can cause joint pressure on hard floors beneath",
        ],
        "materials": [
            "Foam density versus comfort — compare standard polyurethane (25–30 kg/m³) against memory foam (40–60 kg/m³) for support and longevity",
            "Cover fabric durability — assess whether the outer material resists scratching, digging, and daily wear without pilling or tearing",
            "Filling recovery rate — test whether the bed returns to its original shape after compression, indicating quality resilient foam or fibre",
            "Waterproof lining presence — check for a water-resistant barrier between the cover and filling to protect against accidents and spills",
            "Eco-credential verification — confirm any sustainability claims (recycled materials, organic cotton) with recognised third-party certification",
        ],
        "sizing": [
            "Sleeping position measurement — measure your dog in their typical sleep position, as curlers need less surface area than sprawlers",
            "Weight-to-size ratio — ensure the bed's foam or filling supports your dog's weight without excessive compression",
            "Growth allowance for young dogs — factor in expected adult size if purchasing for a growing puppy to avoid premature replacement",
            "Crate compatibility — measure the internal crate floor dimensions and compare against the bed's outer measurements including any bolsters",
            "Multi-dog consideration — if dogs share space, assess whether individual beds or a larger shared bed suits their social sleeping behaviour",
        ],
        "seasonal": [
            "Summer breathability — check whether the bed uses mesh panels, elevated frames, or moisture-wicking fabrics for warm-weather comfort",
            "Winter insulation — evaluate whether the bed provides thermal layering, raised sides, or a thicker base for cold-floor protection",
            "Transition ease — consider whether the bed design allows seasonal adjustments (removable bolsters, reversible covers) without full replacement",
            "Humidity management — assess how well the bed materials resist mould and mildew in damp British seasons, particularly autumn and winter",
            "UV resistance for outdoor beds — determine whether fabrics fade or degrade with sunlight exposure during summer garden use",
        ],
        "puppy_beds": [
            "Chew resistance rating — puppies are prolific chewers; evaluate whether seams, corners, and materials withstand destructive teething behaviour",
            "Size scalability — decide whether to buy a full-size bed now or a smaller transitional bed that matches the puppy's current proportions",
            "Accident tolerance — check whether the bed has a waterproof liner or easily washable components for house-training accidents",
            "Crate training compatibility — ensure the bed sits flat inside the crate without bunching and does not block the door mechanism",
            "Safety for unsupervised use — remove beds with small detachable parts (buttons, toggles) that a puppy could chew off and swallow",
        ],
        "types": [
            "Bed shape versus sleeping style — match your dog's preferred resting position (curled, stretched, burrowed) to the appropriate bed shape",
            "Elevation benefits — raised beds improve airflow and joint access but may not suit dogs who prefer nesting or burrowing",
            "Bolster versus flat design — bolster beds offer head support and security, whilst flat mats provide unrestricted movement",
            "Indoor versus outdoor durability — outdoor beds require water-resistant, UV-stable materials that indoor beds typically do not offer",
            "Travel adaptability — assess whether the bed folds, rolls, or compresses for transport without losing shape or support quality",
        ],
        "terminology": [
            "Density rating understanding — learn what kg/m³ values mean in practice for foam support, durability, and comfort trade-offs",
            "Denier count relevance — higher denier fabric is more tear-resistant, important for dogs that scratch or dig before settling",
            "Orthopaedic versus memory foam distinction — not all orthopaedic claims involve genuine memory foam; check the specific fill description",
            "R-value for insulation — understand how thermal resistance ratings apply to beds used on cold tile, concrete, or outdoor surfaces",
            "Certification labels decoded — recognise what OEKO-TEX, GreenGuard, and BS 7177 labels actually guarantee about materials and safety",
        ],
    },
    "Puppy Care": {
        "default": [
            "Age-appropriateness — ensure any product, food, or training method is suitable for your puppy's current developmental stage",
            "Veterinary alignment — cross-reference advice with BVA or RCVS guidelines to confirm it reflects current evidence-based practice",
            "Safety during unsupervised use — assess whether any item or environment is safe when you cannot directly monitor the puppy",
            "Socialisation impact — evaluate whether the activity or product supports positive social development during the critical 3–14 week window",
            "Gradual introduction principle — check that any new routine, food, or environment is introduced incrementally to avoid overwhelming the puppy",
        ],
        "vaccination": [
            "Vaccine schedule compliance — verify your puppy's vaccination timeline aligns with the standard UK protocol (first jab at 6–8 weeks, second at 10–12 weeks)",
            "Post-vaccination observation period — monitor for mild side effects (lethargy, slight swelling) for 24–48 hours after each vaccination",
            "Socialisation-safety balance — assess which environments are safe for socialisation before full vaccination (carrying in public, avoiding dog-frequented ground)",
            "Booster schedule awareness — understand the difference between primary course and annual booster requirements recommended by your veterinary practice",
            "Record keeping — maintain an up-to-date vaccination card and ensure the microchip database reflects current ownership details",
        ],
        "puppy_proofing": [
            "Toxin accessibility — identify all household items (chocolate, grapes, xylitol, cleaning products) reachable from puppy height and secure them",
            "Cable and cord management — assess electrical cords, blind cords, and charging cables for chewing and strangulation risk",
            "Small object hazard — evaluate each room for items small enough to be swallowed (coins, hair ties, children's toys, buttons)",
            "Escape route assessment — check fences, gates, balconies, and doors for gaps a small puppy could squeeze through",
            "Surface and furniture risk — determine whether slippery floors need mats, and whether furniture heights pose jumping injury risks for developing joints",
        ],
        "sleep": [
            "Age-based sleep duration — verify your expectations match normal ranges (18–20 hours for very young puppies, reducing to 12–14 hours by adulthood)",
            "Sleep environment quality — ensure the sleeping area is quiet, dark, draught-free, and maintained at 18–22°C for optimal rest",
            "Routine consistency — assess whether your puppy's bedtime and wake-up schedule is regular, as inconsistency disrupts circadian development",
            "Night-time toileting needs — factor in that puppies under 16 weeks typically cannot hold their bladder through a full 8-hour night",
            "Crate versus open bed suitability — evaluate your puppy's comfort level and whether crate training supports or hinders their sleep quality",
        ],
        "teething": [
            "Teething stage identification — determine whether your puppy is in the primary (3–6 weeks), mixed (12–16 weeks), or adult (6–7 months) dentition phase",
            "Chew toy material safety — ensure toys are made from non-toxic, appropriately firm materials that soothe gums without breaking into swallowable fragments",
            "Pain indicator recognition — assess for excessive drooling, reluctance to eat, blood on toys, or pawing at the mouth as signs of teething discomfort",
            "Frozen treat suitability — check whether frozen carrots, wet flannels, or purpose-made freezable toys are safe and appropriate for your puppy's age",
            "Adult tooth monitoring — verify that all 42 adult teeth have erupted correctly and that no retained baby teeth require veterinary extraction",
        ],
        "socialisation": [
            "Critical window timing — focus primary socialisation efforts between 3 and 14 weeks, when puppies are most receptive to new experiences",
            "Experience diversity — evaluate whether your socialisation plan covers people, animals, environments, sounds, surfaces, and handling exercises",
            "Positive association building — ensure every new encounter is paired with treats, praise, or play to build confidence rather than fear",
            "Overwhelm threshold — monitor body language (tucked tail, whale eye, excessive lip-licking) to detect when the puppy needs a break",
            "Ongoing maintenance — socialisation is not complete at 14 weeks; continue regular, positive exposure throughout adolescence",
        ],
        "training": [
            "Reward timing precision — deliver treats or praise within 1–2 seconds of the desired behaviour for effective association learning",
            "Session length appropriateness — keep training sessions to 3–5 minutes for young puppies, gradually increasing to 10–15 minutes as attention span develops",
            "Consistency across household — check that every family member uses the same commands, hand signals, and reward criteria to prevent confusion",
            "Distraction level progression — start training in a quiet room and gradually introduce distractions rather than expecting focus in stimulating environments",
            "Force-free method verification — confirm the training approach uses only positive reinforcement, as recommended by the APBC and Dogs Trust",
        ],
        "collars": [
            "Fit accuracy — ensure two fingers fit between the collar and neck; check weekly as puppies grow rapidly during their first year",
            "Material safety for young skin — choose soft, lightweight materials (padded nylon, rolled leather) that do not irritate developing puppy skin",
            "ID tag compliance — verify the collar carries a tag with your name and address, as required by the Control of Dogs Order 1992",
            "Breakaway versus fixed clasp — assess whether a safety breakaway clasp is needed for unsupervised wear to prevent choking if the collar snags",
            "Harness transition timing — determine when to introduce a harness for lead walks, especially for breeds prone to tracheal sensitivity",
        ],
        "first_week": [
            "Environment preparation — assess whether the sleeping area, feeding station, and toileting spot are set up before the puppy arrives",
            "Routine establishment — evaluate whether a consistent daily schedule for feeding, toileting, play, and rest has been planned",
            "Bonding versus overwhelming — balance the family's excitement with the puppy's need for quiet adjustment time in a new environment",
            "Veterinary registration urgency — confirm a health check appointment is booked within the first 48–72 hours of arrival",
            "House-training baseline — set realistic expectations that accidents are normal and respond with patience and enzymatic cleaners, not punishment",
        ],
        "first_time_owner": [
            "Preparation checklist — verify essential supplies (crate, bed, food, bowls, lead, collar, ID tag, toys) are ready before the puppy arrives",
            "Veterinary relationship establishment — register with a local practice before bringing the puppy home, and schedule a first health check within 48 hours",
            "Realistic time commitment — assess whether your daily schedule allows for feeding four times daily (young puppies), hourly toilet breaks, and supervised play",
            "Support network identification — locate puppy training classes, behavioural advice lines (Dogs Trust, Blue Cross), and emergency veterinary contacts",
            "Long-term cost awareness — understand ongoing expenses including food, insurance, vaccinations, neutering, dental care, and annual health checks",
        ],
        "glossary": [
            "Term source verification — check whether definitions align with recognised UK veterinary and welfare organisations (BVA, RCVS, Kennel Club)",
            "Context-specific meaning — understand that some terms (e.g., 'socialisation') have specific clinical definitions that differ from casual usage",
            "Age-stage relevance — assess whether the guidance associated with each term applies to your puppy's current developmental period",
            "Cross-reference depth — evaluate whether the glossary links to more detailed guides where additional context is needed",
        ],
    },
    "Dog Health": {
        "default": [
            "Symptom severity assessment — distinguish between signs that warrant routine veterinary consultation and those requiring emergency attention",
            "Evidence source quality — verify whether the health advice references peer-reviewed veterinary research or recognised UK bodies (BVA, RCVS, PDSA)",
            "Breed-specific relevance — check whether the guidance accounts for conditions more prevalent in certain breeds or size categories",
            "Prevention versus treatment focus — evaluate whether the information helps you prevent problems or manage existing conditions",
            "Professional guidance boundary — identify when the advice recommends consulting a veterinary professional rather than self-managing at home",
        ],
        "dental": [
            "Plaque and tartar distinction — understand that plaque is the soft film removed by daily brushing, whilst tarite requires professional veterinary scaling",
            "Brushing technique and frequency — assess whether daily brushing with a dog-specific enzymatic toothpaste is achievable within your routine",
            "Professional dental check schedule — verify when annual dental examinations are recommended and what signs indicate an earlier appointment is needed",
            "Diet impact on dental health — evaluate whether your dog's current food supports dental health through mechanical cleaning action or specific formulations",
            "Warning sign recognition — identify red gums, persistent bad breath, reluctance to eat, or pawing at the mouth as indicators requiring veterinary attention",
            "Home dental product safety — confirm that any dental chews, water additives, or toys carry VOHC (Veterinary Oral Health Council) acceptance",
        ],
        "general": [
            "Preventive care schedule — evaluate whether your dog's vaccination, parasite prevention, and health check routine follows current BVA guidelines",
            "Body condition scoring — learn to assess your dog's weight using the 1–9 body condition scale recommended by veterinary nutritionists",
            "Age-appropriate health monitoring — understand which health checks become more important as your dog enters middle age (typically 7+ years for large breeds, 10+ for small)",
            "Insurance adequacy — assess whether your pet insurance covers the conditions most relevant to your dog's breed, age, and lifestyle",
            "Emergency preparedness — verify you know the location and contact details for your nearest emergency veterinary practice outside normal hours",
        ],
        "terminology": [
            "Clinical versus colloquial meaning — recognise that veterinary terms often have precise definitions that differ from everyday pet-owner language",
            "Diagnostic terminology understanding — assess whether you can interpret common test results (blood panels, urinalysis) discussed during veterinary consultations",
            "Medication instruction clarity — verify you understand dosage terms (mg/kg, BID, SID) and administration routes (oral, topical, subcutaneous)",
            "Condition severity grading — learn how vets grade conditions (mild, moderate, severe) and what each grade implies for treatment and prognosis",
            "Specialist referral awareness — understand when terms like 'orthopaedic specialist' or 'veterinary dermatologist' indicate a referral is advisable",
        ],
    },
}

TROUBLESHOOTING_CONTENT = {
    "Dog Food": {
        "default": [
            "Dog refuses new food — mix 25% new food with 75% current food, gradually shifting the ratio over 7–10 days to allow digestive adjustment",
            "Loose stools after diet change — slow the transition further; if diarrhoea persists beyond 5 days, consult your vet to rule out sensitivity",
            "Excessive flatulence on current diet — consider whether high-fibre or legume-heavy ingredients are the cause; trial a simpler protein-and-grain formula",
            "Dog eats too quickly — use a slow-feeder bowl or scatter-feed to extend mealtimes and reduce the risk of bloat, especially in deep-chested breeds",
            "Fussy eating despite good health — maintain consistent mealtimes, remove uneaten food after 20 minutes, and avoid supplementing with high-value treats between meals",
        ],
    },
    "Dog Beds": {
        "default": [
            "Dog refuses to use the new bed — place a familiar-smelling blanket or worn t-shirt on the bed for the first week to transfer reassuring scent",
            "Bed flattens within weeks — the foam density is likely below 30 kg/m³; replace with a higher-density option that resists body-weight compression",
            "Persistent odour despite washing — the inner filling may harbour bacteria; wash the entire bed (not just the cover) or replace the insert",
            "Dog drags the bed around the room — add a non-slip base mat or choose a bed with a rubberised bottom surface designed for hard floors",
            "Cover zip breaks repeatedly — look for beds with concealed or heavy-duty YKK zips; exposed lightweight zips are the most common failure point",
        ],
        "cooling": [
            "Cooling effect fades quickly — gel-based pads typically need 15–20 minutes without contact to recharge; elevated mesh beds offer continuous airflow instead",
            "Dog avoids the cooling bed — the surface may feel unfamiliar; place their usual blanket on top initially and remove it gradually over several days",
            "Gel pad punctures from claws — trim nails regularly and consider a fabric-covered cooling mat rather than an exposed gel surface",
        ],
        "washing": [
            "Cover shrinks after machine wash — always wash on 30°C and air-dry; check the care label for maximum temperature before first wash",
            "Foam insert takes days to dry — stand the foam upright in a well-ventilated area; never tumble-dry foam as heat damages the cell structure",
            "Stain sets before cleaning — keep an enzymatic pet cleaner to hand and treat accidents within minutes; standard detergent often fails on protein-based stains",
            "Bed smells worse after washing — residual moisture breeds bacteria; ensure thorough drying and consider adding white vinegar to the rinse cycle",
        ],
        "placement": [
            "Dog ignores the bed in its current spot — experiment with different locations; dogs often prefer a quiet corner with a wall behind them for security",
            "Bed slides on hard floor — place a rubber mat or non-slip rug pad underneath; some beds include built-in grip bases for smooth surfaces",
            "Bed is in a draught path — feel for cold air currents at floor level near doors and windows; relocate the bed at least 30 cm away from these sources",
        ],
        "safety": [
            "Dog chews and swallows bed material — remove the bed immediately, monitor for vomiting or lethargy, and consult your vet if you suspect ingestion",
            "Strong chemical smell from new bed — air the bed outdoors or in a well-ventilated room for 48–72 hours before allowing your dog to use it",
            "Zip or fastener comes loose — remove any detachable small parts that pose a choking hazard and replace with a bed using concealed or stitched closures",
        ],
        "materials": [
            "Memory foam feels too firm in winter — memory foam stiffens in cold temperatures; place the bed away from cold floors or add an insulating layer beneath",
            "Fabric pills after a few weeks — pilling indicates low denier fabric; choose covers rated at 300D or higher for durability against scratching and digging",
            "Polyester filling clumps after washing — redistribute filling by hand whilst damp and dry flat; if clumping persists, the filling may need replacement",
        ],
        "sizing": [
            "Dog hangs limbs over the bed edges — the bed is too small; re-measure in the stretched sleeping position and add 15–20 cm to each dimension",
            "Bed is too large for the crate — measure the crate's internal floor dimensions, not the external frame, before purchasing a crate mat or bed",
            "Puppy outgrows the bed quickly — for rapidly growing breeds, consider an adjustable bed or buy for projected adult size with temporary blanket fillers",
        ],
        "seasonal": [
            "Dog pants on the bed in summer — the bed may lack breathability; switch to an elevated mesh frame or add a cooling mat on top during warm months",
            "Dog shivers on the bed in winter — add a fleece blanket or switch to a hooded or cave-style bed that retains body heat more effectively",
            "Bed develops mildew in humid weather — ensure the bed is fully dried after washing and place it in a room with adequate ventilation",
        ],
        "puppy_beds": [
            "Puppy destroys the bed overnight — use a simple, inexpensive towel or blanket in the crate until the chewing phase passes, typically by 7–8 months",
            "Puppy toilets on the bed — remove the bed temporarily during active house-training; reintroduce once the puppy is reliably clean through the night",
            "Puppy whines when placed on the bed — ensure the bed is in a warm, sheltered spot near family activity; a ticking clock or warm water bottle can mimic litter warmth",
        ],
        "types": [
            "Dog ignores the bolster bed — some dogs dislike head support; try a flat mat style and observe whether usage increases",
            "Elevated bed wobbles on carpet — check that all four legs are fully locked in and sitting on a level surface; uneven flooring causes instability",
            "Cave bed retains too much heat — cave or hooded beds suit colder months; switch to an open design during warmer seasons or in heated rooms",
        ],
        "terminology": [
            "Confused by foam density ratings — density (kg/m³) indicates support quality, not firmness; higher density lasts longer and supports heavier dogs",
            "Unsure about denier count meaning — denier measures fabric thread thickness; higher numbers (300D+) resist tearing and scratching better",
            "Misled by 'orthopaedic' labelling — not all beds labelled orthopaedic contain genuine memory foam; check the specific fill description and density rating",
        ],
    },
    "Puppy Care": {
        "default": [
            "Puppy cries at night — place the crate near your bed initially and gradually move it to the desired location over 1–2 weeks",
            "House-training regression — revisit basics: increase toilet break frequency, reward success immediately, and clean accidents with enzymatic cleaner to remove scent markers",
            "Puppy nips during play — redirect biting onto appropriate toys; if nipping continues, end the play session immediately with a calm 'ouch' and brief withdrawal of attention",
            "Puppy refuses to walk on the lead — let the puppy wear the collar and lead indoors first; practise in the garden before attempting pavement walks",
            "Overwhelmed puppy hides frequently — reduce stimulation, provide a covered crate or den space, and allow the puppy to approach new things at their own pace",
        ],
        "vaccination": [
            "Puppy is lethargic after vaccination — mild lethargy for 24–48 hours is normal; contact your vet if the puppy refuses food for more than a day or shows swelling at the injection site",
            "Missed the second vaccination window — contact your vet promptly; delayed boosters may require restarting the primary course depending on the gap",
            "Puppy was exposed to unvaccinated dogs — inform your vet immediately; they may recommend monitoring for specific symptoms depending on vaccination status",
        ],
        "puppy_proofing": [
            "Puppy found and chewed something toxic — contact your vet or the Animal PoisonLine (01202 509000) immediately with details of what was ingested and the quantity",
            "Puppy keeps escaping the designated safe area — check for gaps at floor level, ensure baby gates are properly secured, and cover any spaces behind furniture",
            "Puppy chews electrical cables — use cable covers or bitter apple spray on exposed wires; unplug and secure any cables at puppy height when unsupervised",
        ],
        "sleep": [
            "Puppy wakes at 4 a.m. every night — gradually shift the final evening toilet trip later by 10–15 minutes every few days to extend the overnight period",
            "Puppy sleeps all day but is restless at night — increase daytime activity with short, age-appropriate play sessions and enforce brief nap periods in the crate",
            "Puppy refuses the crate at bedtime — make the crate positive with treats and a Kong, never use it for punishment, and cover it with a blanket for den-like comfort",
        ],
        "teething": [
            "Puppy chews everything in sight — provide a rotation of 3–4 appropriate chew toys and freeze a wet flannel for soothing gum relief",
            "Blood spots on toys — small amounts of blood during teething are normal as baby teeth loosen; consult your vet if bleeding is heavy or persistent",
            "Puppy refuses food during teething — soften kibble with warm water or offer wet food temporarily; see your vet if food refusal lasts more than 48 hours",
        ],
        "socialisation": [
            "Puppy is fearful of other dogs — increase distance, pair the sight of other dogs with high-value treats, and let the puppy set the pace for closer approach",
            "Puppy is over-excited around new people — teach a 'sit for greeting' protocol; ask visitors to ignore the puppy until calm behaviour is offered",
            "Puppy panics at loud sounds — play recorded sounds at a very low volume during positive activities, gradually increasing volume over weeks (desensitisation)",
        ],
        "training": [
            "Puppy ignores commands in new environments — go back to basics in a controlled setting; gradually increase environmental difficulty as reliability improves",
            "Family members use different commands — create a written command list and ensure every person in the household uses identical words and gestures",
            "Puppy loses interest during training — shorten sessions to 2–3 minutes, use higher-value rewards, and end on a success to maintain motivation",
        ],
        "collars": [
            "Collar causes fur rubbing or irritation — switch to a wider, padded collar or rolled leather style that distributes pressure more evenly across the neck",
            "Puppy freezes when the collar is first fitted — let the puppy wear the collar indoors for short periods with treats, gradually extending the duration",
            "ID tag jingles and startles the puppy — use a slide-on tag or silicone tag silencer to reduce noise whilst maintaining legal identification compliance",
        ],
        "first_week": [
            "Puppy will not eat in the new home — offer small, frequent meals in a quiet location; appetite typically returns within 24–48 hours as the puppy settles",
            "Existing pet is hostile towards the puppy — keep them separated initially, introduce through a baby gate, and supervise all interactions until calm coexistence is established",
            "Puppy has diarrhoea on arrival — stress-related digestive upset is common; maintain the breeder's food for the first 2 weeks before any diet transition",
        ],
        "first_time_owner": [
            "Feeling overwhelmed by puppy demands — this is completely normal; prioritise sleep, house-training, and feeding routines, and accept that perfection is not required in week one",
            "Unsure whether behaviour is normal — contact the Dogs Trust behaviour helpline or your vet for reassurance; most puppy behaviour that concerns new owners is developmentally normal",
            "Budget is tighter than expected — prioritise vaccinations, quality food, and insurance; many training resources (Kennel Club, Dogs Trust) are free or low-cost",
        ],
        "glossary": [
            "Confused by a veterinary term — ask your vet to explain in plain language; most practices are happy to clarify terminology during consultations",
            "Conflicting definitions online — cross-reference any term with BVA, RCVS, or Kennel Club resources to verify the UK-standard definition",
            "Term does not seem to apply to your situation — puppy care terminology is often stage-specific; check whether the term applies to your puppy's current age and developmental phase",
        ],
    },
    "Dog Health": {
        "default": [
            "Dog shows sudden behavioural change — any abrupt shift in energy, appetite, or temperament may indicate pain or illness; schedule a veterinary assessment",
            "Recurring mild symptoms not improving — if a condition persists beyond 5–7 days despite home management, professional diagnosis is necessary to rule out underlying causes",
            "Confusion about medication dosage — always follow your vet's prescription exactly; never adjust dosage based on internet advice without veterinary confirmation",
            "Dog resists dental examination at home — gradually desensitise by lifting the lip for a second, rewarding, and slowly building to longer inspections over weeks",
            "Conflicting health advice from different sources — prioritise guidance from your veterinary practice, BVA, and RCVS over unverified online forums or social media",
        ],
        "dental": [
            "Dog resists toothbrushing — start by letting the dog lick enzymatic toothpaste from your finger, then gradually introduce a finger brush over 2–3 weeks",
            "Bad breath persists despite brushing — persistent halitosis often indicates periodontal disease below the gum line; schedule a professional veterinary dental examination",
            "Bleeding gums during brushing — mild bleeding may indicate early gingivitis; reduce brushing pressure and consult your vet if it persists beyond a week",
            "Dog breaks a tooth on a chew — remove the chew immediately and contact your vet; fractured teeth can expose the pulp and cause infection",
            "Tartar builds up quickly despite daily care — some dogs are genetically predisposed to tartar accumulation; discuss professional cleaning frequency with your vet",
        ],
        "general": [
            "Dog is overweight but you follow feeding guidelines — feeding guidelines are starting points only; your vet can calculate precise calorie needs based on body condition score",
            "Annual vaccinations seem unnecessary — discuss titre testing with your vet to determine whether booster vaccinations are needed based on existing immunity levels",
            "Dog limps intermittently — on-and-off lameness can indicate early joint disease; record when it occurs and consult your vet for orthopaedic assessment",
            "Insurance claim was rejected — review the policy's pre-existing condition and waiting period clauses; consider switching to a lifetime policy for ongoing coverage",
        ],
        "terminology": [
            "Confused by blood test abbreviations — ask your vet to walk through each value; common ones include ALT (liver), BUN (kidney), and WBC (white blood cells)",
            "Unsure what a diagnosis means in practice — request a written summary from your vet with the condition name, expected progression, and management plan",
            "Medication label instructions unclear — BID means twice daily, SID means once daily, PO means by mouth; confirm timing and food requirements with your vet",
        ],
    },
}

SCENARIO_CONTENT = {
    "Dog Food": {
        "default": [
            "If your dog has a sensitive stomach — choose a limited-ingredient diet with a single novel protein source and no artificial additives, introduced gradually over 10 days",
            "If you have a highly active working dog — select a food formulated for working dogs with higher protein (26%+) and fat (16%+) content to sustain energy output",
            "If your dog is overweight — transition to a light or weight-management formula with reduced calorie density, guided by your vet's target weight and feeding plan",
            "If you are feeding a senior dog — consider a diet with added joint-support ingredients (glucosamine, chondroitin) and moderate protein to support muscle maintenance without kidney strain",
        ],
    },
    "Dog Beds": {
        "default": [
            "If your dog has arthritis or joint stiffness — choose a memory foam bed with a minimum density of 40 kg/m³ and a low-profile entry point so the dog does not need to step up",
            "If your dog is a destructive chewer — select a bed with a reinforced ballistic nylon cover and no exposed zips, buttons, or loose threads",
            "If your dog overheats easily — opt for an elevated mesh-frame bed or a gel-insert cooling mat that allows airflow beneath and around the dog",
            "If you have a multi-dog household — provide individual beds in separate locations to reduce resource guarding and ensure each dog has a secure resting space",
        ],
        "cooling": [
            "If your dog pants heavily indoors during summer — an elevated mesh bed with a removable cooling gel pad provides both airflow and contact cooling",
            "If your dog is brachycephalic (flat-faced) — prioritise breathability and consistent cooling, as these breeds regulate temperature less efficiently",
            "If you need a portable cooling solution for travel — choose a lightweight, foldable cooling mat that does not require electricity or refrigeration",
        ],
        "washing": [
            "If your dog has allergies — wash the bed weekly at 60°C (if the fabric allows) to kill dust mites, and use a fragrance-free, hypoallergenic detergent",
            "If your dog has frequent accidents — choose a bed with a waterproof liner between cover and foam, and keep two spare covers for rotation",
            "If you have limited drying space — select a bed with a quick-dry polyester cover rather than cotton, which retains moisture for significantly longer",
        ],
        "placement": [
            "If your dog is anxious or noise-sensitive — position the bed in a quiet interior room away from external walls, doors, and windows where noise is loudest",
            "If you live in a small flat — choose a corner placement that does not block walkways, and select a bed shape (rectangular, bolster) that fits flush against the wall",
            "If your dog has mobility issues — place the bed on a ground-floor level with no steps or thresholds to negotiate, ideally on a non-slip surface",
        ],
        "safety": [
            "If your dog is a prolific chewer — remove any bed with detachable parts (zips, toggles, piping) and use a simple, one-piece mat until the chewing phase passes",
            "If your dog has sensitive skin or allergies — select a bed with OEKO-TEX certified fabrics and no flame-retardant chemical treatments beyond UK regulatory requirements",
            "If you have a new puppy — choose a low-cost, easily washable bed without small parts, and expect to replace it as the puppy grows and chewing habits change",
        ],
        "materials": [
            "If your dog weighs over 30 kg — choose high-density foam (45 kg/m³ or above) to prevent the bed from compressing to the floor under sustained body weight",
            "If you prioritise easy cleaning — select a bed with a fully removable, machine-washable outer cover and a waterproof inner liner protecting the foam core",
            "If eco-credentials matter to you — look for beds made from recycled PET bottles or organic cotton, verified by third-party certification (GRS, GOTS)",
        ],
        "sizing": [
            "If your dog switches between curling up and stretching out — measure in both positions and choose a bed that accommodates the larger measurement plus 15 cm",
            "If you are buying for a growing puppy — purchase a bed sized for the projected adult dimensions of the breed, using a blanket to fill the extra space temporarily",
            "If the bed is for crate use — measure the internal crate floor carefully and select a flat mat that sits flush without bunching against the sides or door",
        ],
        "seasonal": [
            "If your home is poorly insulated in winter — add a self-warming thermal mat beneath the main bed to reflect body heat back towards the dog",
            "If your dog spends time in the garden during summer — choose a UV-resistant, water-repellent outdoor bed that can be brought inside overnight",
            "If you want one bed for all seasons — select a design with a reversible cover (fleece on one side, mesh on the other) to switch between warm and cool surfaces",
        ],
        "puppy_beds": [
            "If your puppy is crate training — use a flat, washable mat that sits flush inside the crate without bunching or blocking the door",
            "If your puppy is still teething — choose an inexpensive, replaceable bed or layer old towels until the destructive phase passes (typically 6–8 months)",
            "If your puppy is anxious at night — a bolster or cave-style bed with sides creates a den-like sense of security that mimics the warmth of littermates",
        ],
        "types": [
            "If your dog is elderly with stiff joints — a low-entry orthopaedic bed allows easy access without the need to step up or over bolster edges",
            "If your dog lives in a warm climate or overheats — an elevated mesh-frame bed promotes airflow beneath and around the dog for passive cooling",
            "If you need a travel-friendly option — a lightweight, rollable mat is easier to transport and clean than a bulky bolster or orthopaedic bed",
        ],
        "terminology": [
            "If you are comparing foam types for the first time — focus on density (kg/m³) as the primary indicator of support quality, not marketing terms like 'plush' or 'premium'",
            "If your dog has a diagnosed joint condition — ask your vet for specific density and support recommendations rather than relying on generic 'orthopaedic' labelling",
            "If you are choosing fabric for a heavy-shedding breed — prioritise tightly woven, high-denier covers that resist hair embedding and can be easily vacuumed or lint-rolled",
        ],
    },
    "Puppy Care": {
        "default": [
            "If you work full-time from home — structure puppy breaks into your work schedule with a crate or playpen for enforced naps between activity periods",
            "If you have young children — supervise all puppy-child interactions, teach children to be calm and gentle, and provide the puppy with a child-free safe space",
            "If you adopted a rescue puppy with unknown history — allow extra time for adjustment, avoid overwhelming socialisation, and consult a qualified behaviourist if fear responses persist",
            "If you live in a flat without a garden — establish a consistent outdoor toilet routine and use puppy pads only as a temporary bridge during initial house-training",
        ],
        "vaccination": [
            "If your puppy has not had their first vaccination by 9 weeks — contact a vet immediately to start the primary course without further delay",
            "If you want to socialise before full vaccination — carry your puppy in public rather than placing them on the ground; attend controlled puppy classes that require vaccination proof",
            "If your puppy has a reaction to a vaccine — monitor for mild lethargy or localised swelling for 24 hours; contact your vet if symptoms worsen or a facial swelling occurs",
        ],
        "puppy_proofing": [
            "If you have a large house with many rooms — puppy-proof gradually by restricting access to one or two rooms initially and expanding as the puppy matures",
            "If you have other pets — create separate feeding and resting areas and introduce pets through barriers before allowing supervised face-to-face contact",
            "If you have a garden — check fences for gaps, remove toxic plants (lilies, daffodils, foxglove), and supervise outdoor time until recall is reliable",
        ],
        "sleep": [
            "If your puppy sleeps in a crate — position it in your bedroom initially for reassurance, with a covered top and a warm (not hot) water bottle wrapped in a towel",
            "If your puppy wakes frequently at night — take them for a brief, boring toilet trip with no play or interaction, then return them to the crate immediately",
            "If your puppy naps excessively during the day — this is normal for puppies under 4 months; enforced naps actually support better nighttime sleep quality",
        ],
        "teething": [
            "If your puppy is 12–16 weeks and losing baby teeth — offer a variety of textures (rubber, rope, frozen cloth) to soothe different areas of the gums",
            "If retained baby teeth are visible alongside adult teeth — schedule a veterinary dental check; retained teeth may need extraction to prevent crowding and infection",
            "If your puppy is in severe teething pain — frozen carrots and purpose-made freezable toys provide temporary numbing relief; consult your vet if pain seems excessive",
        ],
        "socialisation": [
            "If your puppy is extremely shy — work at the puppy's pace using counter-conditioning (pairing triggers with treats) rather than forcing exposure",
            "If you live in a rural area with limited socialisation opportunities — use recorded sound CDs, invite visitors regularly, and attend structured puppy classes further afield",
            "If your puppy is overly bold and mouthy — redirect energy into structured play and reward calm behaviour; consider a positive-reinforcement puppy class for impulse control",
        ],
        "training": [
            "If your puppy is food-motivated — use small, soft treats broken into pea-sized pieces to keep training sessions efficient without overfeeding",
            "If your puppy is toy-motivated — use a favourite toy as the reward instead of food; keep the toy special by only producing it during training sessions",
            "If your puppy seems unresponsive to training — rule out hearing issues, check for pain or illness, and ensure the training environment is free from overwhelming distractions",
        ],
        "collars": [
            "If your puppy pulls strongly on the lead — transition to a well-fitted Y-shaped harness that distributes pressure across the chest rather than the neck",
            "If your puppy is a toy or small breed — choose an ultra-lightweight collar (under 30g) with a narrow width appropriate for a small neck circumference",
            "If your puppy will be off-lead in open spaces — ensure the collar carries a secure ID tag and consider adding an AirTag-compatible holder for additional tracking",
        ],
        "first_week": [
            "If the puppy came from a breeder — ask for a piece of bedding or towel carrying the mother's scent to ease the transition into your home",
            "If the puppy was adopted from a rescue — expect a longer adjustment period; provide a predictable routine and a quiet, safe space to decompress",
            "If the puppy arrives during a busy household period — delay the arrival if possible; the first week requires dedicated, calm attention for bonding and routine-setting",
        ],
        "first_time_owner": [
            "If you are nervous about getting things right — join a Kennel Club-accredited puppy class within the first month for hands-on guidance and community support",
            "If your budget is limited — focus spending on vaccinations, quality food, and insurance; homemade enrichment and free training resources fill the remaining gaps effectively",
            "If you have conflicting advice from family and friends — follow your vet's recommendations as the primary authority, supplemented by APBC or Dogs Trust guidance",
        ],
        "glossary": [
            "If you are reading this glossary before getting a puppy — focus on the age-stage and health terms first, as these will be most relevant in your first veterinary consultations",
            "If a term seems contradictory to advice elsewhere — check the publication date and source authority; veterinary best practice evolves, and older guidance may be outdated",
            "If you need more detail than the glossary provides — follow the cross-reference links to our full-length guides covering each topic in depth",
        ],
    },
    "Dog Health": {
        "default": [
            "If your dog is a senior (7+ years for large breeds, 10+ for small breeds) — schedule biannual veterinary health checks and discuss age-appropriate screening for common conditions",
            "If your dog has a chronic condition — work with your vet to create a long-term management plan including regular monitoring, adjusted diet, and appropriate exercise levels",
            "If you have a brachycephalic breed — be alert to breathing difficulties, overheating, and dental crowding; discuss breed-specific health screening with your vet",
            "If you are unsure whether a symptom is an emergency — contact your vet or the nearest emergency practice for telephone triage rather than waiting to see if it resolves",
        ],
        "dental": [
            "If your dog already has visible tartar buildup — schedule a professional veterinary dental cleaning under anaesthesia; home brushing alone cannot remove established tartar",
            "If your dog is under 1 year old — start a toothbrushing routine now using puppy-safe enzymatic toothpaste to establish the habit before dental disease develops",
            "If your dog has had teeth extracted — follow your vet's soft-food and pain management instructions for the recovery period, typically 10–14 days",
        ],
        "general": [
            "If your dog has breed-specific health risks — discuss relevant screening tests (hip scoring, eye testing, heart checks) with your vet at the appropriate age",
            "If your dog suddenly loses appetite or energy — treat this as a priority veterinary consultation; sudden changes often indicate pain, infection, or organ dysfunction",
            "If your pet insurance has a high excess or exclusions — compare lifetime policies from multiple providers and switch during the renewal window if better coverage is available",
        ],
        "terminology": [
            "If you are preparing for a veterinary consultation — write down your questions in advance, including any terms from test results or previous notes you do not understand",
            "If you receive a diagnosis you do not fully understand — ask the vet to explain the condition, prognosis, and all treatment options in plain language before making decisions",
            "If you need to explain symptoms to an emergency vet by phone — describe what you observe (behaviour, colour, frequency) rather than attempting to use medical terminology",
        ],
    },
}


# ── Comparison Tables (Phase 10BF) ─────────────────────────────────────

COMPARISON_TABLES = {
    "Dog Food": {
        "default": [
            {
                "caption": "Dog Food Price Ranges: Budget, Mid-Range, and Premium Compared",
                "headers": ["Factor", "Budget", "Mid-Range", "Premium"],
                "rows": [
                    ["Typical monthly cost (medium dog)", "£20–£35", "£35–£55", "£55–£90+"],
                    ["Primary protein source", "Meat derivatives or meal", "Named meat or meat meal", "Fresh or dehydrated named meat"],
                    ["Filler content", "Higher cereal and grain content", "Moderate grain or grain-free", "Minimal fillers, whole ingredients"],
                    ["Artificial additives", "Common (colours, flavours)", "Fewer or none", "Typically none"],
                    ["FEDIAF compliance", "Yes (minimum standards met)", "Yes (often exceeds minimums)", "Yes (exceeds with added supplements)"],
                    ["Ingredient transparency", "Vague category terms", "Percentage breakdowns usual", "Full ingredient sourcing disclosed"],
                ],
            },
        ],
    },
    "Dog Beds": {
        "default": [
            {
                "caption": "Dog Bed Materials: Key Properties and Trade-Offs",
                "headers": ["Material", "Support Level", "Durability", "Breathability", "Wash Ease"],
                "rows": [
                    ["Standard polyurethane foam", "Moderate", "1–2 years typical", "Low", "Cover only; foam spot-clean"],
                    ["Memory foam (viscoelastic)", "High", "3–5 years typical", "Low–moderate", "Cover only; foam air-dry"],
                    ["Polyester fibre fill", "Low–moderate", "6–12 months before clumping", "Moderate", "Machine washable (whole bed)"],
                    ["Gel-infused foam", "High", "2–4 years typical", "Moderate (cooling effect)", "Cover only; gel layer wipe"],
                    ["Elevated mesh fabric", "Moderate (no cushion)", "3–5 years (frame dependent)", "Excellent", "Hose down or wipe clean"],
                    ["Recycled PET fibre", "Moderate", "1–3 years typical", "Moderate", "Machine washable (check label)"],
                    ["Organic cotton fill", "Low–moderate", "1–2 years typical", "High", "Machine washable at 30°C"],
                ],
            },
        ],
        "cooling": [
            {
                "caption": "Cooling Bed Technologies: How They Compare",
                "headers": ["Cooling Method", "How It Works", "Duration of Effect", "Maintenance", "Suitability"],
                "rows": [
                    ["Gel pad (pressure-activated)", "Absorbs body heat on contact", "20–40 minutes per session", "Wipe clean; check for punctures", "Short cooling periods indoors"],
                    ["Elevated mesh frame", "Promotes continuous airflow beneath", "Constant (passive)", "Wipe frame; hose fabric", "All-day use indoors or outdoors"],
                    ["Phase-change fabric", "Absorbs and releases heat cyclically", "Several hours", "Machine wash cover", "Consistent moderate cooling"],
                    ["Water-filled mat", "Conducts heat away via water", "2–4 hours", "Drain and refill; patch if punctured", "Portable; travel-friendly"],
                    ["Aluminium or metal base", "Conducts heat away from body", "Constant (passive)", "Wipe clean", "Hot climates; hard floor placement"],
                ],
            },
        ],
        "sizing": [
            {
                "caption": "Dog Bed Sizes by Breed Category",
                "headers": ["Breed Size", "Typical Weight Range", "Minimum Bed Dimensions", "Recommended Foam Density", "Sleeping Style Note"],
                "rows": [
                    ["Toy breeds", "Up to 5 kg", "45 × 35 cm", "25–30 kg/m³", "Often curlers; round beds suit well"],
                    ["Small breeds", "5–10 kg", "60 × 45 cm", "30–35 kg/m³", "Mix of curlers and side-sleepers"],
                    ["Medium breeds", "10–25 kg", "80 × 60 cm", "35–40 kg/m³", "Stretchers need longer beds"],
                    ["Large breeds", "25–40 kg", "100 × 75 cm", "40–45 kg/m³", "Side-sleepers need full extension space"],
                    ["Giant breeds", "40 kg+", "120 × 90 cm+", "45–55 kg/m³", "Elevated or extra-thick foam essential"],
                ],
            },
        ],
        "seasonal": [
            {
                "caption": "Seasonal Dog Bedding Needs: Summer vs Winter",
                "headers": ["Factor", "Summer Needs", "Winter Needs"],
                "rows": [
                    ["Ideal material", "Breathable mesh, cooling gel, cotton", "Fleece, thermal-lined, insulating foam"],
                    ["Bed style", "Elevated frame or flat open mat", "Bolster, cave, or hooded design"],
                    ["Cover fabric", "Moisture-wicking polyester or linen", "Plush fleece or sherpa"],
                    ["Placement priority", "Cool, shaded area away from direct sun", "Away from draughts, near gentle warmth"],
                    ["Cleaning frequency", "Weekly (increased shedding and allergens)", "Fortnightly (less outdoor dirt)"],
                    ["Additional accessories", "Cooling mat, fan-accessible position", "Self-warming pad, extra blanket"],
                ],
            },
        ],
        "puppy_beds": [
            {
                "caption": "Puppy Bed Needs by Age Stage",
                "headers": ["Age Stage", "Primary Need", "Recommended Bed Type", "Key Consideration"],
                "rows": [
                    ["8–12 weeks", "Security and warmth", "Soft mat or towel in crate", "Expect frequent washing from accidents"],
                    ["3–5 months", "Chew resistance", "Simple, inexpensive flat bed", "Avoid beds with removable parts"],
                    ["5–8 months", "Growing body support", "Mid-density foam, sized for growth", "Measure monthly; growing rapidly"],
                    ["8–12 months", "Transition to adult bed", "Adult-sized bed for projected weight", "Upgrade support density as needed"],
                    ["12+ months", "Comfort and durability", "Permanent adult bed (material matched)", "Joint support if large or giant breed"],
                ],
            },
        ],
        "materials": [
            {
                "caption": "Foam Density Comparison for Dog Beds",
                "headers": ["Density Range (kg/m³)", "Support Level", "Typical Lifespan", "Suited For", "Trade-Off"],
                "rows": [
                    ["20–25", "Low", "6–12 months", "Lightweight puppies, temporary use", "Compresses quickly under heavier dogs"],
                    ["25–30", "Low–moderate", "1–2 years", "Small breeds under 10 kg", "Adequate comfort but limited joint support"],
                    ["30–35", "Moderate", "2–3 years", "Medium breeds 10–25 kg", "Good balance of comfort and cost"],
                    ["35–45", "High", "3–5 years", "Large breeds, orthopaedic needs", "Higher cost; genuine joint support"],
                    ["45–60", "Very high", "4–6 years", "Giant breeds, severe joint conditions", "Heaviest and most expensive option"],
                ],
            },
        ],
        "safety": [
            {
                "caption": "Common Dog Bed Hazards and Prevention Measures",
                "headers": ["Hazard", "Risk Level", "Signs to Watch For", "Prevention"],
                "rows": [
                    ["Small detachable parts (zips, buttons)", "High (choking/obstruction)", "Missing components, chewing marks", "Choose beds with concealed or no zips"],
                    ["Toxic flame retardants", "Moderate (long-term exposure)", "Not visible; check certification", "Select OEKO-TEX certified beds"],
                    ["Off-gassing from new foam", "Low–moderate (respiratory)", "Chemical smell when unpacked", "Air for 48–72 hours before use"],
                    ["Fabric ingestion from chewing", "High (intestinal blockage)", "Torn fabric, missing sections", "Supervise or use chew-proof materials"],
                    ["Mould from inadequate drying", "Moderate (respiratory/skin)", "Musty smell, visible discolouration", "Dry fully after every wash"],
                    ["Slipping on hard floors", "Low–moderate (injury)", "Bed moves when dog jumps on/off", "Use non-slip base or rubber mat"],
                ],
            },
        ],
        "washing": [
            {
                "caption": "Washing Methods Compared by Bed Component",
                "headers": ["Component", "Machine Wash?", "Recommended Temperature", "Drying Method", "Frequency"],
                "rows": [
                    ["Removable fabric cover", "Yes", "30–40°C", "Tumble low heat or air-dry", "Every 1–2 weeks"],
                    ["Foam insert (standard)", "No", "Spot clean only", "Air-dry upright; never tumble", "As needed (spot clean)"],
                    ["Memory foam insert", "No", "Spot clean only", "Air-dry flat; avoid direct sun", "As needed (spot clean)"],
                    ["Polyester fibre fill bed", "Yes (whole bed)", "30°C gentle cycle", "Air-dry flat; reshape whilst damp", "Every 2–4 weeks"],
                    ["Waterproof liner", "Yes", "30°C", "Air-dry or wipe clean", "Monthly or after accidents"],
                    ["Elevated mesh frame", "N/A", "Wipe or hose down", "Air-dry naturally", "Weekly wipe; monthly deep clean"],
                ],
            },
        ],
        "placement": [
            {
                "caption": "Dog Bed Placement Locations: Pros and Cons",
                "headers": ["Location", "Advantages", "Disadvantages", "Best Suited For"],
                "rows": [
                    ["Bedroom corner", "Close to owner; reassuring overnight", "May disrupt light sleepers", "Anxious dogs, puppies in first weeks"],
                    ["Living room quiet zone", "Near family; social comfort", "Foot traffic and noise during day", "Social dogs who prefer company"],
                    ["Dedicated dog room", "Full control of environment", "Isolating if door is closed", "Multiple dogs; scheduled rest periods"],
                    ["Under a desk or table", "Den-like enclosure; draught-free", "Limited space; hard to clean under", "Small to medium breeds who burrow"],
                    ["Hallway or landing", "Central access to multiple rooms", "Often draughty; high foot traffic", "Confident dogs who guard the home"],
                    ["Conservatory or porch", "Natural light; views outside", "Temperature extremes summer/winter", "Fair-weather use only; seasonal"],
                ],
            },
        ],
        "types": [
            {
                "caption": "Dog Bed Types: Style Features and Suitability",
                "headers": ["Bed Type", "Key Feature", "Best Sleeping Style", "Drawback"],
                "rows": [
                    ["Flat mat or cushion", "Simple, portable, easy to wash", "Stretchers and sprawlers", "Minimal joint support"],
                    ["Bolster bed", "Raised edges for head resting", "Side-sleepers and leaners", "Can trap heat in summer"],
                    ["Cave or hooded bed", "Enclosed, den-like warmth", "Burrowers and anxious dogs", "Retains heat; not for warm months"],
                    ["Elevated or raised bed", "Airflow beneath; cools in summer", "All styles; especially hot dogs", "No cushioning unless mat added"],
                    ["Orthopaedic foam bed", "High-density support for joints", "Senior, arthritic, or large dogs", "Heavy; hard to move and wash"],
                    ["Donut or nest bed", "Soft, rounded, cocoon-like shape", "Curlers and toy breeds", "Not suited for large stretchers"],
                ],
            },
        ],
    },
    "Puppy Care": {
        "default": [
            {
                "caption": "Puppy Developmental Stages and Care Priorities",
                "headers": ["Age Stage", "Key Development", "Primary Care Focus", "Common Challenge"],
                "rows": [
                    ["0–3 weeks (neonatal)", "Eyes and ears open; limited mobility", "Warmth, nutrition via mother", "Rarely relevant for new owners"],
                    ["3–8 weeks (socialisation begins)", "Play behaviour, bite inhibition", "Early socialisation with litter", "Separating too early causes issues"],
                    ["8–12 weeks (new home)", "Bonding, environmental exploration", "House-training, vet registration", "Fear periods; gentle exposure needed"],
                    ["3–6 months (juvenile)", "Teething, rapid growth, training", "Basic obedience, socialisation", "Mouthing, chewing, boundary testing"],
                    ["6–12 months (adolescence)", "Sexual maturity, independence", "Consistent training, neutering decision", "Selective deafness, regression"],
                    ["12–18 months (young adult)", "Physical maturity (breed dependent)", "Advanced training, health checks", "Residual adolescent behaviour"],
                ],
            },
        ],
        "vaccination": [
            {
                "caption": "UK Puppy Vaccination Schedule Overview",
                "headers": ["Vaccination", "First Dose", "Second Dose", "Booster Frequency", "Protects Against"],
                "rows": [
                    ["Distemper (CDV)", "6–8 weeks", "10–12 weeks", "Every 3 years (after first annual)", "Distemper virus"],
                    ["Parvovirus (CPV)", "6–8 weeks", "10–12 weeks", "Every 3 years (after first annual)", "Canine parvovirus"],
                    ["Hepatitis (CAV-2)", "6–8 weeks", "10–12 weeks", "Every 3 years (after first annual)", "Infectious canine hepatitis"],
                    ["Leptospirosis (L4)", "8 weeks", "10–12 weeks", "Annually", "Leptospira bacteria"],
                    ["Kennel cough (Bb/CPiV)", "From 3 weeks (intranasal)", "Not always required", "Annually (if at risk)", "Bordetella and parainfluenza"],
                    ["Rabies (travel only)", "12 weeks minimum", "N/A (single primary dose)", "Every 1–3 years per vet advice", "Rabies virus (for pet passport)"],
                ],
            },
        ],
        "teething": [
            {
                "caption": "Puppy Teething Stages and What to Expect",
                "headers": ["Stage", "Age Range", "What Happens", "Typical Signs", "Helpful Response"],
                "rows": [
                    ["Baby teeth emerge", "2–4 weeks", "28 deciduous teeth appear", "Nibbling during nursing", "Breeder management stage"],
                    ["Full baby teeth set", "5–8 weeks", "All deciduous teeth present", "Play-biting with littermates", "Bite inhibition learning begins"],
                    ["Baby teeth start falling out", "12–16 weeks", "Incisors and canines loosen", "Increased chewing, mild bleeding", "Offer frozen chew toys"],
                    ["Premolars and molars emerge", "4–6 months", "Adult teeth push through", "Sore gums, drooling, food reluctance", "Soften kibble; rotate toys"],
                    ["Full adult set complete", "6–7 months", "42 permanent teeth in place", "Chewing intensity decreases", "Check for retained baby teeth"],
                ],
            },
        ],
        "collars": [
            {
                "caption": "Puppy Collar and Harness Types Compared",
                "headers": ["Type", "Best For", "Pressure Distribution", "Key Advantage", "Key Limitation"],
                "rows": [
                    ["Flat buckle collar", "ID tag carrying, gentle walkers", "Around neck circumference", "Simple, lightweight, legal compliance", "Can cause neck pressure if pulling"],
                    ["Breakaway collar", "Unsupervised indoor wear", "Around neck (releases under force)", "Prevents choking if collar snags", "Not secure for lead attachment"],
                    ["Y-shaped harness", "Pullers, small breeds, trachea-sensitive", "Across chest and shoulders", "No neck pressure; comfortable fit", "Does not address pulling behaviour"],
                    ["Back-clip harness", "Calm walkers, puppies learning leads", "Across chest and back", "Easy to put on; non-restrictive", "Offers less steering control"],
                    ["Front-clip harness", "Moderate pullers, training tool", "Across chest with front redirect", "Redirects pulling direction gently", "Can cause chafing if poorly fitted"],
                    ["Head collar", "Strong pullers (vet/trainer advised)", "Around muzzle and behind ears", "Maximum steering control", "Requires gradual desensitisation"],
                ],
            },
        ],
        "socialisation": [
            {
                "caption": "Socialisation Experiences Checklist by Category",
                "headers": ["Category", "Examples to Include", "When to Start", "Key Principle"],
                "rows": [
                    ["People", "Children, elderly, people in hats/uniforms", "3–8 weeks (breeder); 8–14 weeks (owner)", "Pair with treats; never force contact"],
                    ["Animals", "Vaccinated dogs, cats, livestock (at a distance)", "After first vaccination (controlled settings)", "Positive, brief encounters"],
                    ["Environments", "Parks, town centres, cars, public transport", "8–14 weeks (carried if pre-vaccination)", "Gradual exposure; watch body language"],
                    ["Surfaces", "Grass, gravel, metal grates, wet ground", "As soon as home; garden first", "Let puppy investigate at own pace"],
                    ["Sounds", "Traffic, fireworks (recorded), household appliances", "From 8 weeks at low volume", "Build volume gradually over weeks"],
                    ["Handling", "Paw touching, ear checking, mouth opening", "From day one at home", "Pair with treats; keep sessions short"],
                ],
            },
        ],
        "first_time_owner": [
            {
                "caption": "Monthly Puppy Care Cost Estimates (UK)",
                "headers": ["Expense Category", "Monthly Estimate", "Notes"],
                "rows": [
                    ["Food (quality kibble or wet)", "£30–£60", "Varies by breed size and food quality"],
                    ["Pet insurance", "£20–£50", "Lifetime policies offer best long-term cover"],
                    ["Flea, worm, and tick prevention", "£10–£20", "Vet-prescribed options are most reliable"],
                    ["Toys and enrichment", "£10–£20", "Rotate toys to maintain interest"],
                    ["Training classes", "£10–£20 per session", "Kennel Club classes from approx. £40/course"],
                    ["Grooming (breed-dependent)", "£0–£40", "Long-coated breeds need professional grooming"],
                    ["Veterinary check-ups", "£10–£25 (averaged)", "Higher in first year due to vaccinations"],
                ],
            },
        ],
    },
    "Dog Health": {
        "default": [
            {
                "caption": "Preventive Health Care Schedule by Life Stage",
                "headers": ["Life Stage", "Vaccination", "Parasite Prevention", "Health Checks", "Dental Care"],
                "rows": [
                    ["Puppy (0–12 months)", "Primary course + first booster", "Monthly flea/worm treatment", "Initial vet check; 6-month review", "Start toothbrushing from 8 weeks"],
                    ["Young adult (1–3 years)", "Annual boosters as scheduled", "Monthly or as vet advises", "Annual health check", "Daily brushing; annual dental check"],
                    ["Adult (3–7 years)", "Boosters; titre testing option", "Ongoing monthly prevention", "Annual check; weight monitoring", "Daily brushing; professional clean if needed"],
                    ["Senior (7–10 years)", "As vet advises (may reduce)", "Ongoing; kidney-safe products", "Biannual checks; blood panels", "Increased monitoring; dental disease risk rises"],
                    ["Geriatric (10+ years)", "As vet advises", "Gentle, organ-safe products", "Biannual or quarterly as needed", "Veterinary dental review every 6 months"],
                ],
            },
        ],
        "dental": [
            {
                "caption": "Dog Dental Care Methods Compared",
                "headers": ["Method", "Effectiveness", "Frequency Required", "Cost Level", "Ease of Use"],
                "rows": [
                    ["Enzymatic toothpaste + brush", "High (gold standard)", "Daily", "Low (£5–£10 per tube)", "Moderate (requires training)"],
                    ["Dental chews (VOHC accepted)", "Moderate", "Daily", "Moderate (£15–£30/month)", "Easy (dog self-administers)"],
                    ["Water additives", "Low–moderate", "Daily (added to bowl)", "Low (£5–£15/month)", "Very easy"],
                    ["Dental diet (prescription)", "Moderate–high", "Daily (replaces standard food)", "Moderate–high", "Easy (standard feeding)"],
                    ["Professional veterinary cleaning", "Very high (removes tartar)", "Annually or as vet advises", "High (£200–£500+ per session)", "N/A (requires anaesthesia)"],
                    ["Raw bones (controversial)", "Variable", "Occasional", "Low", "Risk of fractures and obstruction"],
                ],
            },
        ],
        "general": [
            {
                "caption": "Common Dog Health Indicators: Normal vs Concerning Signs",
                "headers": ["Indicator", "Normal Range", "When to Monitor", "When to Contact Vet"],
                "rows": [
                    ["Appetite", "Consistent daily intake", "Slight decrease for 1–2 days", "Refuses food for 48+ hours"],
                    ["Energy level", "Active during waking hours", "Mildly subdued after exercise", "Persistent lethargy or sudden collapse"],
                    ["Stool quality", "Firm, formed, dark brown", "Occasional soft stool", "Persistent diarrhoea, blood, or mucus"],
                    ["Water intake", "40–60 ml per kg per day", "Slight increase in hot weather", "Excessive drinking or sudden increase"],
                    ["Breathing", "15–30 breaths per minute at rest", "Panting after exercise", "Laboured breathing or persistent cough"],
                    ["Coat condition", "Shiny, smooth, minimal shedding", "Seasonal shedding increase", "Bald patches, excessive scratching, dullness"],
                    ["Gum colour", "Pink and moist", "Slightly pale after rest", "White, blue, yellow, or brick-red gums"],
                ],
            },
        ],
        "terminology": [
            {
                "caption": "Common Veterinary Test Abbreviations Explained",
                "headers": ["Abbreviation", "Full Name", "What It Measures", "When It Is Used"],
                "rows": [
                    ["CBC / FBC", "Complete/Full Blood Count", "Red and white blood cell levels, platelets", "Routine screening, illness investigation"],
                    ["ALT", "Alanine Aminotransferase", "Liver enzyme activity", "Liver function assessment"],
                    ["BUN / Urea", "Blood Urea Nitrogen", "Kidney waste filtration", "Kidney function screening"],
                    ["Creatinine", "Creatinine", "Kidney filtration efficiency", "Kidney disease monitoring"],
                    ["T4", "Thyroxine", "Thyroid hormone level", "Hypothyroidism screening"],
                    ["UA", "Urinalysis", "Urine concentration, infection markers", "Kidney, bladder, diabetes screening"],
                    ["CRP", "C-Reactive Protein", "Inflammation level", "Infection or inflammatory disease detection"],
                ],
            },
        ],
    },
}


# ── Keyword matching to get the right sub-key ──────────────────────────

def get_content_key(title, cluster):
    """Determine sub-key based on post title keywords."""
    t = title.lower()

    if cluster == "Dog Beds":
        if "cool" in t:
            return "cooling"
        if "wash" in t or "clean" in t or "maintain" in t:
            return "washing"
        if "placement" in t or "where to place" in t or "where to put" in t or "location" in t:
            return "placement"
        if "safety" in t or "hazard" in t or "non-toxic" in t:
            return "safety"
        if "material" in t or "foam" in t:
            return "materials"
        if "size" in t or "sizing" in t or "choose the right" in t:
            return "sizing"
        if "seasonal" in t or "season" in t or "through the year" in t:
            return "seasonal"
        if "puppy" in t or "crate training" in t:
            return "puppy_beds"
        if "type" in t or "glossary" in t and "terminology" not in t:
            return "types"
        if "terminology" in t or "terms explained" in t:
            return "terminology"
        return "default"

    if cluster == "Puppy Care":
        if "vaccin" in t:
            return "vaccination"
        if "proof" in t or "safety guide" in t:
            return "puppy_proofing"
        if "sleep" in t:
            return "sleep"
        if "teeth" in t or "teething" in t:
            return "teething"
        if "socialis" in t:
            return "socialisation"
        if "training" in t and "bed" not in t:
            return "training"
        if "collar" in t or "harness" in t:
            return "collars"
        if "first week" in t or "day-by-day" in t:
            return "first_week"
        if "first-time" in t or "first time" in t or "essentials" in t and "what you need" in t:
            return "first_time_owner"
        if "glossary" in t or "key terms" in t:
            return "glossary"
        return "default"

    if cluster == "Dog Health":
        if "dental" in t or "teeth" in t:
            return "dental"
        if "terminology" in t or "veterinary" in t and "terms" in t:
            return "terminology"
        if "complete guide" in t or "care uk" in t:
            return "general"
        return "default"

    # Dog Food
    return "default"


# ── Insertion Logic ─────────────────────────────────────────────────────

# Blocks that mark "footer zone" — insert BEFORE the first one found
FOOTER_MARKERS = [
    "Quick Checklist",
    "Common Mistakes",
    "Common Mistakes to Avoid",
    "Key Terms",
    "Key Takeaways",
    "Our Editorial Standards",
    "Beginner Recommendations",
    "What to Do Next",
    "When to Seek Professional Help",
    "Decision Summary",
    "How We Evaluated This Topic",
    "What to Realistically Expect",
    "Is This Right for You?",
    "Why We Reference These Sources",
]


def find_insertion_point(raw_content):
    """Find the position in raw content to insert new blocks, before the footer zone."""
    best_pos = len(raw_content)

    for marker in FOOTER_MARKERS:
        # Look for h4 with the marker text
        pattern = f'<h4 class="wp-block-heading">{re.escape(marker)}</h4>'
        idx = raw_content.find(pattern)
        if idx > 0:
            # Walk backwards to find the start of the containing wp:group block
            # Look for the nearest <!-- wp:group before this heading
            search_start = max(0, idx - 800)
            segment = raw_content[search_start:idx]
            group_idx = segment.rfind("<!-- wp:group")
            if group_idx >= 0:
                absolute_pos = search_start + group_idx
                if absolute_pos < best_pos:
                    best_pos = absolute_pos

    # If nothing found, try the glossary paragraph at the end
    if best_pos == len(raw_content):
        glossary_marker = "Unfamiliar with any terms used above?"
        idx = raw_content.find(glossary_marker)
        if idx > 0:
            # Walk back to the start of wp:paragraph
            search_start = max(0, idx - 300)
            segment = raw_content[search_start:idx]
            para_idx = segment.rfind("<!-- wp:paragraph")
            if para_idx >= 0:
                best_pos = search_start + para_idx

    return best_pos


def find_table_insertion_point(raw_content):
    """Find a good spot for additional comparison tables — after main content, before footer."""
    # Place comparison tables just before the decision-support blocks (which are before footer)
    # Find the insertion point first, then go slightly before that
    footer_pos = find_insertion_point(raw_content)

    # Look for a good spot in the main content area (last third before footer)
    content_before_footer = raw_content[:footer_pos]
    # Find the last heading (h2 or h3) in the main content
    last_h2 = content_before_footer.rfind("<!-- /wp:heading -->")
    if last_h2 > 0:
        # Find the end of the block after this heading
        end_of_section = content_before_footer.find("\n\n", last_h2 + 20)
        if end_of_section > 0 and end_of_section < footer_pos:
            return end_of_section + 2

    # If no good spot found, insert just before the footer zone
    return footer_pos


def already_has_block(raw_content, heading_text):
    """Check if a block with this h4 heading already exists."""
    return f">{heading_text}</h4>" in raw_content


# ── Main Processing ─────────────────────────────────────────────────────

def process_all():
    print("Fetching all posts...")
    posts = fetch_all_posts()
    print(f"Found {len(posts)} eligible posts")

    results = []
    table_count = 0
    target_tables = 35  # Target 30-40 tables

    # Determine which posts get tables
    # Give priority to posts with richer topic potential
    posts_sorted = sorted(posts.values(), key=lambda p: p["id"])

    for post_info in posts_sorted:
        pid = post_info["id"]
        title = post_info["title"]
        cluster = post_info["cluster"]
        raw = post_info["raw"]

        print(f"\n{'='*60}")
        print(f"Processing: [{pid}] {title} ({cluster})")

        content_key = get_content_key(title, cluster)
        print(f"  Content key: {content_key}")

        evaluation_added = False
        troubleshooting_added = False
        scenario_added = False
        tables_added = 0
        modified = False

        # Check for existing blocks
        has_eval = already_has_block(raw, "How to Evaluate")
        has_trouble = already_has_block(raw, "Common Problems and Solutions")
        has_scenario = already_has_block(raw, "Which Option Suits Your Situation")

        # Build new blocks
        new_blocks = []

        # 1. Evaluation Framework
        if not has_eval:
            eval_items = EVALUATION_CONTENT.get(cluster, {}).get(content_key)
            if not eval_items:
                eval_items = EVALUATION_CONTENT.get(cluster, {}).get("default")
            if eval_items:
                new_blocks.append(make_evaluation_block(eval_items))
                evaluation_added = True
                print(f"  + Evaluation Framework block")
        else:
            print(f"  ~ Evaluation already exists, skipping")

        # 2. Troubleshooting
        if not has_trouble:
            trouble_items = TROUBLESHOOTING_CONTENT.get(cluster, {}).get(content_key)
            if not trouble_items:
                trouble_items = TROUBLESHOOTING_CONTENT.get(cluster, {}).get("default")
            if trouble_items:
                new_blocks.append(make_troubleshooting_block(trouble_items))
                troubleshooting_added = True
                print(f"  + Troubleshooting block")
        else:
            print(f"  ~ Troubleshooting already exists, skipping")

        # 3. Scenario Guidance
        if not has_scenario:
            scenario_items = SCENARIO_CONTENT.get(cluster, {}).get(content_key)
            if not scenario_items:
                scenario_items = SCENARIO_CONTENT.get(cluster, {}).get("default")
            if scenario_items:
                new_blocks.append(make_scenario_block(scenario_items))
                scenario_added = True
                print(f"  + Scenario Guidance block")
        else:
            print(f"  ~ Scenario already exists, skipping")

        # Insert decision support blocks before footer
        if new_blocks:
            ins_pos = find_insertion_point(raw)
            combined = "\n\n".join(new_blocks) + "\n\n"
            raw = raw[:ins_pos] + combined + raw[ins_pos:]
            modified = True
            print(f"  Inserted decision blocks at position {ins_pos}")

        # 4. Comparison tables (Phase 10BF)
        if table_count < target_tables:
            cluster_tables = COMPARISON_TABLES.get(cluster, {})
            tables_for_key = cluster_tables.get(content_key, [])
            # Also consider default tables if post doesn't have key-specific ones
            if not tables_for_key and content_key != "default":
                tables_for_key = cluster_tables.get("default", [])

            for tbl in tables_for_key:
                if table_count >= target_tables:
                    break
                caption_check = tbl["caption"]
                if caption_check in raw:
                    print(f"  ~ Table '{caption_check[:40]}...' already exists, skipping")
                    continue

                table_html = make_comparison_table(tbl["caption"], tbl["headers"], tbl["rows"])
                # Insert table before the decision support blocks
                tbl_pos = find_table_insertion_point(raw)
                raw = raw[:tbl_pos] + table_html + "\n\n" + raw[tbl_pos:]
                tables_added += 1
                table_count += 1
                modified = True
                print(f"  + Table: {tbl['caption'][:50]}... (total: {table_count})")

        # Update post
        status = "skipped"
        if modified:
            success = api_put(pid, {"content": raw})
            if success:
                status = "updated"
                print(f"  >>> UPDATED successfully")
            else:
                status = "error"
                print(f"  >>> ERROR updating post")
            time.sleep(1.5)  # Rate limiting
        else:
            status = "no_changes"
            print(f"  --- No changes needed")

        results.append({
            "id": pid,
            "title": title,
            "cluster": cluster,
            "evaluation_added": "yes" if evaluation_added else "no",
            "troubleshooting_added": "yes" if troubleshooting_added else "no",
            "scenario_added": "yes" if scenario_added else "no",
            "tables_added": tables_added,
            "status": status,
        })

    # Write CSV
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "title", "cluster", "evaluation_added",
            "troubleshooting_added", "scenario_added", "tables_added", "status"
        ])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n{'='*60}")
    print(f"CSV saved to: {CSV_PATH}")
    print(f"\n=== SUMMARY ===")
    updated = sum(1 for r in results if r["status"] == "updated")
    total_evals = sum(1 for r in results if r["evaluation_added"] == "yes")
    total_troubles = sum(1 for r in results if r["troubleshooting_added"] == "yes")
    total_scenarios = sum(1 for r in results if r["scenario_added"] == "yes")
    total_tables = sum(r["tables_added"] for r in results)
    print(f"Posts updated: {updated}/{len(results)}")
    print(f"Evaluation blocks added: {total_evals}")
    print(f"Troubleshooting blocks added: {total_troubles}")
    print(f"Scenario blocks added: {total_scenarios}")
    print(f"Comparison tables added: {total_tables}")
    print(f"Errors: {sum(1 for r in results if r['status'] == 'error')}")


if __name__ == "__main__":
    process_all()
