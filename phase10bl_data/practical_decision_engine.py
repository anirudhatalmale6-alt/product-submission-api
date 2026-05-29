#!/usr/bin/env python3
"""
Phase 10BK/10BL/10BN Engine — Practical Guidance, Decision Pathways, Comparison Tables
Clusters: Dog Beds (1401), Puppy Care (1442), Dog Health (1450), Dog Grooming/Care (1489)
"""

import subprocess, json, re, csv, os, sys, time, tempfile

WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
CSV_PATH = "/var/lib/freelancer/projects/40416335/phase10bl_data/practical_decision_beds_puppy_health_groom.csv"

# Category mapping (actual WP IDs)
CATEGORIES = {
    1401: "Dog Beds",
    1442: "Puppy Care",
    1450: "Dog Health",
    1489: "Dog Grooming",
}

def wp_get(endpoint):
    url = f"{WP_BASE}/{endpoint}"
    r = subprocess.run(["curl", "-s", "--compressed", "-u", f"{WP_USER}:{WP_PASS}", url],
                       capture_output=True, text=True)
    return json.loads(r.stdout)

def wp_update_post(post_id, content):
    payload = json.dumps({"content": content})
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    tmp.write(payload)
    tmp.close()
    url = f"{WP_BASE}/posts/{post_id}"
    r = subprocess.run([
        "curl", "-s", "--compressed",
        "-X", "POST",
        "-u", f"{WP_USER}:{WP_PASS}",
        "-H", "Content-Type: application/json",
        "-d", f"@{tmp.name}",
        url
    ], capture_output=True, text=True)
    os.unlink(tmp.name)
    resp = json.loads(r.stdout)
    if "id" in resp:
        return True
    print(f"  ERROR updating {post_id}: {r.stdout[:300]}")
    return False

def fetch_all_posts():
    """Fetch all posts from our 4 categories, deduplicated."""
    seen = {}
    for cat_id in CATEGORIES:
        posts = wp_get(f"posts?categories={cat_id}&per_page=50&_fields=id,title,slug,categories&context=edit")
        if not isinstance(posts, list):
            print(f"Warning: category {cat_id} returned non-list: {str(posts)[:200]}")
            continue
        for p in posts:
            pid = p["id"]
            if pid not in seen:
                # Determine primary cluster
                primary = None
                for cid in [1401, 1442, 1450, 1489]:
                    if cid in p["categories"]:
                        primary = cid
                        break
                seen[pid] = {
                    "id": pid,
                    "title": p["title"]["raw"],
                    "slug": p["slug"],
                    "categories": p["categories"],
                    "cluster": CATEGORIES.get(primary, "Unknown"),
                    "cluster_id": primary,
                }
    return seen

# ============================================================
# PHASE 10BK — PRACTICAL GUIDANCE CONTENT
# ============================================================

PRACTICAL_GUIDES = {}

# --- DOG BEDS cluster ---
PRACTICAL_GUIDES["dog-beds-generic"] = """
<ol class="wp-block-list">
<li><strong>Measure your dog correctly</strong> — With your dog lying in their natural sleep position, measure from nose to tail base and add 15cm. Measure shoulder width and add 10cm. For curlers, measure the curled diameter plus 10cm.</li>
<li><strong>Choose the right bed type for their sleep style</strong> — Side sleepers: rectangular flat beds (60×45cm small, 90×70cm large). Curlers: round donut or bolster beds (50cm small, 75cm large). Sprawlers: oversized flat mats with at least 20cm extra each side.</li>
<li><strong>Set your budget by size tier</strong> — Small beds (under 60cm): £15–35. Medium beds (60–80cm): £30–55. Large beds (80–100cm): £45–80. Extra-large (100cm+): £60–120. Orthopaedic options add £15–30 to each tier.</li>
<li><strong>Check breed-specific requirements</strong> — Greyhounds and Whippets: deep-sided bolster beds for joint support, minimum 8cm foam. Bulldogs and Pugs: flat cooling beds to prevent overheating. German Shepherds: extra-large orthopaedic beds with hip support, minimum 10cm memory foam.</li>
<li><strong>Consider seasonal bedding needs</strong> — Summer: cooling gel mats (£15–25) or elevated mesh beds (£20–40) for airflow. Winter: thermal fleece-lined beds (£25–50) or self-warming reflective beds (£20–35). Spring/autumn: standard beds with removable covers for easy washing.</li>
<li><strong>Test bed firmness</strong> — Press your fist into the centre. If it reaches the floor, the bed lacks support. Quality memory foam should compress 2–3cm and return to shape within 5 seconds. Dogs over 20kg need minimum 10cm thick foam.</li>
<li><strong>Establish a washing routine</strong> — Remove covers and machine wash at 30°C every 2 weeks. Deep clean the entire bed monthly. Replace beds showing permanent compression or odour that persists after washing, typically every 12–18 months.</li>
<li><strong>Place the bed strategically</strong> — Away from draughts and direct radiators. Quiet corner with a wall on at least one side for security. Living room for daytime naps, bedroom for overnight sleep. Avoid hallways and high-traffic areas.</li>
<li><strong>Introduce the bed gradually</strong> — Place a worn t-shirt on the bed for scent familiarity. Reward your dog for approaching and lying on the bed with a small treat. Allow 5–7 days for full acceptance. Never force your dog onto the bed.</li>
<li><strong>Plan for replacement and maintenance</strong> — Budget £40–80 annually for bed replacement. Check zips and seams monthly for wear. Keep a spare waterproof liner (£8–15) for accidents. Store seasonal beds in vacuum bags to save space.</li>
</ol>
"""

PRACTICAL_GUIDES["cooling-dog-beds"] = """
<ol class="wp-block-list">
<li><strong>Identify if your dog needs cooling</strong> — Brachycephalic breeds (Bulldogs, Pugs, Boxers), heavy-coated breeds (Huskies, Malamutes), senior dogs, and dogs over 25kg are most at risk of overheating. Watch for excessive panting, drooling, or seeking cool floor surfaces.</li>
<li><strong>Choose the right cooling mechanism</strong> — Pressure-activated gel pads: no electricity needed, £15–30, recharge by leaving unused for 15–20 minutes. Elevated mesh beds: constant airflow underneath, £20–45. Water-filled mats: fill and refrigerate, £10–20. Each suits different dogs.</li>
<li><strong>Size your cooling bed correctly</strong> — Measure your dog lying stretched out and add 10cm each direction. Gel pads: 40×50cm (small, under 10kg), 65×50cm (medium, 10–25kg), 90×60cm (large, 25kg+). Elevated beds: match to existing crate or bed dimensions.</li>
<li><strong>Set up for maximum effectiveness</strong> — Place on a hard, cool floor surface (tiles or laminate, not carpet). Position away from direct sunlight and radiators. In very hot weather (above 25°C), combine a gel pad on top of an elevated bed for dual cooling effect.</li>
<li><strong>Establish a summer cooling routine</strong> — May–September: replace or overlay standard beds with cooling options. Check gel pads for punctures weekly. Wipe elevated bed frames with damp cloth every 3–4 days. Store cooling beds properly in autumn to extend their lifespan to 2–3 seasons.</li>
<li><strong>Budget for seasonal bedding</strong> — Basic gel pad: £15–25 (replace annually). Quality elevated bed: £25–45 (lasts 3–4 years). Combined setup: £40–70 initial outlay. Replacement gel inserts: £10–15. A cooling bed can reduce summer vet visits related to heat stress.</li>
<li><strong>Monitor your dog's temperature</strong> — Normal body temperature: 38.3–39.2°C. Check ear temperature as a quick guide — ears should feel warm, not hot. If your dog avoids the cooling bed, it may be too cold; add a thin cotton sheet on top.</li>
<li><strong>Consider breed-specific cooling needs</strong> — Bulldogs/Pugs: gel pads at floor level, never elevated (risk of falling). Labradors: elevated mesh beds near water bowl. Huskies: combination cooling in rooms below 22°C. Small breeds (under 5kg): half-size gel pads to avoid over-cooling.</li>
</ol>
"""

PRACTICAL_GUIDES["orthopaedic-dog-beds"] = """
<ol class="wp-block-list">
<li><strong>Determine if your dog needs orthopaedic support</strong> — Dogs over 7 years old, breeds prone to hip dysplasia (German Shepherds, Labradors, Rottweilers), dogs recovering from surgery, and any dog showing stiffness after rest. Consult your vet if unsure — initial consultation: £30–60.</li>
<li><strong>Choose the right foam density</strong> — Standard memory foam: 40–50 kg/m³ density, suitable for dogs under 20kg. High-density foam: 50–80 kg/m³, essential for dogs 20–40kg. Premium orthopaedic: 80+ kg/m³, recommended for dogs over 40kg or those with diagnosed joint conditions.</li>
<li><strong>Select the correct thickness</strong> — Minimum 8cm for small breeds (under 10kg), 10cm for medium breeds (10–25kg), 12–15cm for large breeds (25kg+). The foam should not compress to the floor when your dog lies on it. Test by pressing firmly with your palm.</li>
<li><strong>Budget appropriately</strong> — Small orthopaedic bed (50–60cm): £35–55. Medium (70–85cm): £50–80. Large (90–110cm): £70–120. Extra-large (110cm+): £90–150. Vet-recommended brands with certified foam density typically cost 20–30% more but last significantly longer.</li>
<li><strong>Position for easy access</strong> — Place at floor level with no step up required. Dogs with arthritis struggle with raised bed frames. Add a non-slip mat underneath (£5–10) to prevent the bed sliding on hard floors. Position near a wall so your dog can brace when standing up.</li>
<li><strong>Maintain the bed's therapeutic value</strong> — Rotate the bed 180° monthly to distribute wear evenly. Memory foam loses 15–20% of its support after 18 months of daily use. Replace every 18–24 months for dogs with active joint conditions. Wash the cover fortnightly at 30°C.</li>
<li><strong>Add supplementary support</strong> — Bolster edges provide head and neck support (add £10–20 to base price). Waterproof liners protect foam from accidents (essential for senior dogs, £8–15). Heated pads beneath the bed can ease winter stiffness (£15–30, thermostatically controlled).</li>
<li><strong>Monitor joint health alongside bedding</strong> — Track morning stiffness duration: under 10 minutes is normal age-related, over 30 minutes warrants a vet visit. Joint supplements alongside proper bedding: glucosamine and chondroitin (£10–20/month). Annual joint assessment: £30–60.</li>
<li><strong>Consider breed-specific orthopaedic needs</strong> — Dachshunds: flat orthopaedic beds (never bolstered, to protect the spine). Great Danes: extra-large with minimum 15cm foam depth. Cavalier King Charles: medium beds with neck bolster support. Bulldogs: orthopaedic with cooling layer.</li>
<li><strong>Transition gradually</strong> — Place the new bed next to the existing one for 3–5 days. Encourage use with treats and familiar scent items. Most dogs adjust within a week. If your dog avoids the bed after 2 weeks, the foam may be too firm — consider a softer density option.</li>
</ol>
"""

PRACTICAL_GUIDES["puppy-beds"] = """
<ol class="wp-block-list">
<li><strong>Size for growth, not current size</strong> — Research your puppy's expected adult size. Buy a bed sized for 75% of adult dimensions. Use rolled towels or blankets to fill extra space. This avoids buying 3–4 beds as your puppy grows. Budget: £20–40 for a grow-into bed.</li>
<li><strong>Choose chew-resistant materials for the first year</strong> — Puppies teethe until 6–7 months. Select beds with reinforced seams, ballistic nylon covers, and no removable parts. Avoid beds with zips that puppies can chew open. Budget £25–40 for a durable puppy bed.</li>
<li><strong>Set up crate training beds correctly</strong> — Measure the internal crate floor (not external dimensions). Choose a flat mat 2cm smaller than the floor on each side. Thickness: 3–5cm maximum to maintain crate headroom. Waterproof-backed mats: £12–25 for puppy accidents.</li>
<li><strong>Establish a bedtime routine from day one</strong> — Week 1: place the bed in your bedroom near your own bed. Week 2–3: gradually move the bed towards its permanent position (30cm per night). Week 4+: bed in its final location. Use a warm water bottle wrapped in a towel for the first week.</li>
<li><strong>Plan for the puppy chewing phase</strong> — Months 3–7: use an inexpensive, washable bed (£10–15) that you can replace if destroyed. Months 8–12: transition to a quality bed once chewing reduces. Provide appropriate chew toys near the bed to redirect chewing behaviour.</li>
<li><strong>Manage accidents and hygiene</strong> — Puppies are not reliably house-trained until 4–6 months. Use waterproof mattress protectors (£8–12) under the bed cover. Wash covers at 60°C to eliminate bacteria. Keep two covers in rotation so one is always clean and ready.</li>
<li><strong>Match bed type to puppy age</strong> — 8–12 weeks: flat padded mat in crate. 3–6 months: bolster bed with low sides for easy entry. 6–12 months: standard adult-style bed sized for growth. Over 12 months: permanent bed matched to adult size and sleep style.</li>
<li><strong>Budget for the first year of bedding</strong> — Initial puppy mat: £10–15. Waterproof liners (×2): £16–24. Transitional bed at 6 months: £20–35. Final adult bed at 12 months: £30–80 depending on size. Total first-year bedding budget: £75–155.</li>
<li><strong>Consider breed-specific puppy needs</strong> — Large breed puppies (Labs, Goldens): orthopaedic support from 4 months for developing joints. Small breed puppies (Chihuahuas, Yorkies): enclosed donut beds for warmth and security. Flat-faced breeds: slightly raised beds for easier breathing.</li>
</ol>
"""

PRACTICAL_GUIDES["dog-bed-materials"] = """
<ol class="wp-block-list">
<li><strong>Understand the main filling types</strong> — Polyester fibre fill: budget-friendly (£15–30), loses shape after 6–8 months. Memory foam: moulds to body shape (£35–80), lasts 18–24 months. High-resilience foam: firm support (£40–90), best for dogs over 20kg. Gel-infused: cooling properties (£45–100), ideal for warm environments.</li>
<li><strong>Match material to your dog's needs</strong> — Arthritis or joint issues: memory foam minimum 10cm thick. Overheating: gel-infused or breathable mesh. Puppies and chewers: durable polyester with reinforced covers. Senior dogs: high-density foam with a soft fleece topper.</li>
<li><strong>Check cover material quality</strong> — Canvas and nylon: most durable, suit active or outdoor dogs. Microfibre: soft, easy to clean, good for indoor dogs. Faux suede: comfortable but stains easily. Always choose removable, machine-washable covers at 30–40°C.</li>
<li><strong>Assess waterproofing needs</strong> — Puppies and senior dogs: waterproof inner liner essential (£8–15 separately). Outdoor beds: fully waterproof Oxford fabric covers. Indoor use: water-resistant liner sufficient. Check the liner does not crinkle loudly, which may deter your dog.</li>
<li><strong>Test foam quality before buying</strong> — Press your fist firmly into the foam. Quality memory foam returns to shape within 3–5 seconds. If the impression stays longer than 10 seconds, the foam is too soft and will not provide support. Density should be marked: 40+ kg/m³ minimum.</li>
<li><strong>Plan replacement schedules by material</strong> — Polyester fibre: replace every 6–12 months (flattens with use). Memory foam: 18–24 months for daily-use beds. High-resilience foam: 2–3 years with proper rotation. Gel pads: replace cooling gel inserts annually, frame lasts 3–4 years.</li>
<li><strong>Budget by material tier</strong> — Budget tier (polyester, basic foam): £15–35 per bed, £30–70 annually. Mid-range (memory foam, removable covers): £35–65, £35–65 annually. Premium (high-density orthopaedic, certified foam): £60–120, £60–120 every 2 years.</li>
<li><strong>Check safety certifications</strong> — Look for CertiPUR or OEKO-TEX certification on foam beds, confirming low chemical emissions. Avoid beds with strong chemical smells — air new beds outdoors for 24–48 hours before use. UK fire safety regulations require beds to pass flammability tests.</li>
<li><strong>Consider seasonal material combinations</strong> — Summer: gel-infused foam base with breathable mesh cover. Winter: memory foam base with thermal fleece cover. Having two cover sets (£15–25 each) lets you swap seasonally without replacing the entire bed.</li>
</ol>
"""

PRACTICAL_GUIDES["dog-bed-washing"] = """
<ol class="wp-block-list">
<li><strong>Set up a regular washing schedule</strong> — Removable covers: wash every 2 weeks at 30°C. Inner liners: wash monthly at 40°C. Full bed deep clean: every 2–3 months. Dogs with skin conditions or allergies: wash covers weekly. Mark washing days on your calendar.</li>
<li><strong>Prepare the bed for machine washing</strong> — Remove all loose hair with a lint roller or rubber glove first (saves your washing machine filter). Check for and remove any hidden treats or toys. Close all zips to prevent snagging. Use a pet-safe detergent (£3–6 per bottle, lasts 2–3 months).</li>
<li><strong>Wash foam inserts by hand</strong> — Fill a bathtub with lukewarm water and a capful of mild detergent. Submerge the foam and gently squeeze (never wring). Rinse 3–4 times until water runs clear. Press water out between clean towels. Air dry completely — this takes 24–48 hours.</li>
<li><strong>Remove stubborn odours effectively</strong> — Sprinkle bicarbonate of soda liberally over the bed surface. Leave for 30 minutes, then vacuum thoroughly. For persistent smells, add 100ml white vinegar to the wash cycle. Enzyme-based pet odour sprays (£4–8) break down organic matter.</li>
<li><strong>Dry beds properly to prevent mould</strong> — Tumble dry covers on low heat if the label permits. Never tumble dry memory foam — it will crumble. Air dry foam outdoors in warm weather (4–6 hours) or indoors near (not on) a radiator (24–48 hours). Ensure 100% dryness before reassembling.</li>
<li><strong>Manage between-wash maintenance</strong> — Vacuum the bed surface every 2–3 days to remove hair and dander. Spot clean accidents immediately with enzyme cleaner. Keep a waterproof liner (£8–12) between foam and cover to protect the insert. Shake out covers outdoors weekly.</li>
<li><strong>Know when to replace rather than wash</strong> — Foam that stays compressed after washing has lost its support. Persistent odour after 2 thorough wash cycles indicates deep contamination. Visible mould on foam (not just the cover) means immediate replacement. Typical bed lifespan: 12–18 months with regular washing.</li>
<li><strong>Budget for washing supplies</strong> — Pet-safe detergent: £3–6 per bottle. Bicarbonate of soda (bulk): £2–3 per kg. Enzyme cleaner spray: £4–8. Spare waterproof liners: £8–12 each. Lint roller refills: £3–5 for 3 rolls. Total annual maintenance: £25–40.</li>
</ol>
"""

PRACTICAL_GUIDES["dog-bed-placement"] = """
<ol class="wp-block-list">
<li><strong>Choose the right room for your dog's main bed</strong> — Most dogs benefit from a bed in the room where the family spends the most time (usually the living room). Place a second bed in your bedroom if your dog sleeps with you. Avoid kitchens (too many hazards) and conservatories (temperature extremes).</li>
<li><strong>Position away from environmental stressors</strong> — Minimum 1 metre from radiators and heat sources. Away from external doors (draughts in winter, heat in summer). Not directly under windows (cold draughts and stimulation from outside). At least 50cm from speakers or TVs (noise sensitivity).</li>
<li><strong>Create a den-like setup for anxious dogs</strong> — Place the bed in a corner with walls on two sides. Consider a covered crate bed (crate: £25–50, cover: £10–20) for dogs that like enclosed spaces. Add a blanket draped over one side for extra security. Avoid high-traffic hallways and doorways.</li>
<li><strong>Consider flooring underneath</strong> — Hard floors: place a non-slip mat (£5–10) underneath to prevent the bed sliding. Carpet: use a waterproof mat (£8–15) underneath for accident protection. Tiled floors in summer: ideal for cooling — skip the mat for natural temperature regulation.</li>
<li><strong>Adapt placement seasonally</strong> — Summer: move beds to tiled or stone floors, away from direct sunlight. A spot near an open window (safely screened) provides natural ventilation. Winter: move beds away from external walls, closer to the centre of heated rooms. Spring/autumn: standard positions work well.</li>
<li><strong>Set up multi-dog households correctly</strong> — Each dog needs their own bed, separated by at least 1 metre. Dominant dogs often prefer elevated positions — place their bed on a low platform (£10–20). Anxious dogs prefer beds in quieter corners. Never force dogs to share a bed.</li>
<li><strong>Manage nighttime bed placement</strong> — For puppies: bedroom near your bed for the first 2–4 weeks, then gradually move towards the desired location (30cm per night). Adult dogs: consistent location builds routine. Senior dogs: ground-floor bedrooms to avoid stairs, near a door for toilet access.</li>
<li><strong>Test and adjust over 7–10 days</strong> — Place the bed and observe for a week. If your dog consistently sleeps elsewhere, move the bed to that preferred location. Watch for signs of discomfort: circling without settling, leaving the bed within minutes, or choosing hard floors instead.</li>
</ol>
"""

PRACTICAL_GUIDES["dog-bed-safety"] = """
<ol class="wp-block-list">
<li><strong>Check materials before purchase</strong> — Look for CertiPUR-certified foam (free from harmful chemicals). Check OEKO-TEX Standard 100 labels on fabric. Avoid beds with strong chemical odours — off-gas new beds outdoors for 24–48 hours. UK beds must meet fire safety standards (BS 5852).</li>
<li><strong>Inspect for physical hazards monthly</strong> — Check zips are fully covered by fabric guards to prevent skin catching. Test seam strength by pulling gently — any give means replacement is needed. Remove beds with exposed stuffing immediately (ingestion risk). Check for loose buttons or decorative elements.</li>
<li><strong>Choose safe beds for chewers</strong> — Heavy-duty ballistic nylon covers (£30–50) resist chewing. Avoid beds with removable foam pieces that can be swallowed. No beds with small detachable parts (buttons, toggles, tassels). Consider chew-proof elevated beds (£25–45) for persistent destroyers.</li>
<li><strong>Manage puppy-specific safety risks</strong> — Remove beds with zip access until puppies are past the chewing phase (7–8 months). Avoid heated beds for puppies under 12 months (burn risk). Use flat mats without raised edges that puppies could get tangled in. Check beds twice daily during teething.</li>
<li><strong>Address senior dog safety</strong> — Low-entry beds (maximum 5cm edge height) for dogs with mobility issues. Non-slip base essential for older dogs on hard floors. Avoid elevated beds if your dog has balance problems. Place near a wall for support when standing up. Budget: £35–70 for senior-specific beds.</li>
<li><strong>Monitor heated bed safety</strong> — Only use thermostatically controlled heated pads (£15–30) — never human heating pads. Maximum surface temperature should not exceed 38°C. Always provide an unheated area so your dog can move away. Check cords weekly for chew damage. Unplug when unsupervised.</li>
<li><strong>Set replacement triggers</strong> — Replace immediately if: foam is permanently compressed (no longer returns to shape), fabric is torn with exposed filling, mould is visible after thorough cleaning, or your dog develops unexplained skin irritation. Typical safe lifespan: 12–18 months with regular inspection.</li>
<li><strong>Create a bed safety checklist</strong> — Monthly: check zips, seams, and fabric integrity. Quarterly: inspect foam condition and density. Seasonally: assess if the bed type suits current temperature. Annually: consider full replacement based on wear. Keep receipts for warranty claims (many quality beds offer 1–2 year guarantees).</li>
</ol>
"""

PRACTICAL_GUIDES["seasonal-dog-bedding"] = """
<ol class="wp-block-list">
<li><strong>Plan your seasonal bed rotation</strong> — Spring (March–May): transition from thermal to standard bedding. Summer (June–August): switch to cooling beds. Autumn (September–November): return to standard. Winter (December–February): add thermal layers. Budget £30–60 for a second seasonal cover set.</li>
<li><strong>Set up summer cooling effectively</strong> — Cooling gel mats: £15–25, place on top of existing beds. Elevated mesh beds: £20–40, allow air circulation underneath. Breathable cotton or linen covers replace fleece covers. Move beds to tiled floors and away from south-facing windows.</li>
<li><strong>Prepare winter warmth properly</strong> — Thermal fleece covers: £12–20, trap body heat. Self-warming beds with reflective lining: £20–35. Draught excluders around bed area: £5–10. Raise beds 5cm off cold floors using a simple platform (pallet or foam board: £5–15). Never place directly against cold external walls.</li>
<li><strong>Monitor your dog's temperature cues</strong> — Too hot: seeking cool floors, panting on the bed, spreading limbs wide. Too cold: curling tightly, shivering, reluctance to leave the bed. Adjust bedding within 24 hours of noticing these signs. Ideal ambient temperature for sleeping dogs: 15–21°C.</li>
<li><strong>Manage UK weather transitions</strong> — British weather is unpredictable — keep both seasonal options accessible. April and October often need rapid switches. A good dual-purpose solution: memory foam base (year-round) with interchangeable covers (summer cotton: £10–15, winter fleece: £12–20).</li>
<li><strong>Address breed-specific seasonal needs</strong> — Double-coated breeds (Huskies, Collies): cooling beds essential May–September, never add thermal layers. Short-coated breeds (Greyhounds, Whippets): thermal beds from October–April, pyjamas for very cold nights (£10–18). Brachycephalic breeds: cooling priority year-round.</li>
<li><strong>Store off-season bedding correctly</strong> — Wash thoroughly before storage. Dry completely to prevent mould. Store in vacuum bags (£5–8 for a pack of 4) to save space and keep clean. Label bags clearly. Store gel mats flat, never folded. Typical storage: spare room, under-bed, or airing cupboard.</li>
<li><strong>Calculate annual seasonal bedding costs</strong> — Budget option: 2 cover sets (£20–30 total), rotate seasonally. Mid-range: dedicated summer and winter beds (£50–90 total). Premium: orthopaedic base with seasonal toppers and covers (£80–140 total). Replacement covers annually: £15–25 per set.</li>
</ol>
"""

PRACTICAL_GUIDES["puppy-bed-training"] = """
<ol class="wp-block-list">
<li><strong>Start bed training from the first night</strong> — Place the bed next to your own bed at floor level. Add a piece of clothing with your scent. Use a warm (not hot) water bottle wrapped in a towel to mimic littermate warmth. Expect whimpering for 2–3 nights — this is normal.</li>
<li><strong>Follow the gradual move schedule</strong> — Night 1–7: bed next to yours. Night 8–14: move 30cm towards the door each night. Night 15–21: bed just outside your bedroom door. Night 22–28: bed in its permanent location. This 4-week transition prevents separation anxiety.</li>
<li><strong>Create positive bed associations</strong> — Give a small treat every time your puppy voluntarily goes to the bed. Use a consistent cue word like "bed" or "settle." Never use the bed as punishment. Play calming music at bedtime (classical music has been shown to reduce puppy stress).</li>
<li><strong>Handle nighttime toilet breaks</strong> — Puppies under 12 weeks: expect 1–2 toilet breaks per night. Set an alarm for every 3–4 hours initially. Carry your puppy to the toilet spot quietly — no playing or excitement. Return directly to the bed. By 16 weeks, most puppies sleep 6–7 hours.</li>
<li><strong>Choose the right first bed</strong> — Crate mat for crate-trained puppies: £12–20. Bolster bed with low sides for non-crate puppies: £15–25. Waterproof base essential: saves foam from accidents. Avoid expensive beds until after the chewing phase (6–8 months). Budget £10–15 for the starter bed.</li>
<li><strong>Manage the crate-and-bed combination</strong> — Crate size: large enough for your puppy to stand, turn, and lie down. Place a flat mat inside (3–5cm thick maximum). Cover the crate with a blanket leaving the front open for ventilation. Crate cost: £25–50 depending on adult size needed.</li>
<li><strong>Troubleshoot common bed training problems</strong> — Puppy won't settle: increase daytime exercise by 10–15 minutes. Puppy chews the bed: provide a frozen Kong toy (£5–8) as an alternative. Puppy cries at night: wait 5 minutes before responding (unless toilet need is likely). Puppy sleeps elsewhere: move their bed to that spot temporarily.</li>
<li><strong>Track your puppy's bedtime milestones</strong> — Week 1–2: adjusting to new home, expect disrupted sleep. Week 3–4: should settle within 15 minutes. Month 2: sleeping 5–6 hours through. Month 3: sleeping 6–7 hours. Month 4+: sleeping through the night (7–8 hours). If progress stalls, consult your vet (£30–60 consultation).</li>
</ol>
"""

# --- PUPPY CARE cluster ---
PRACTICAL_GUIDES["puppy-care-generic"] = """
<ol class="wp-block-list">
<li><strong>Prepare your home before puppy arrives</strong> — Puppy-proof room by room: cover electrical cables (cable protectors: £5–10), secure bin lids, remove toxic houseplants, and install stair gates (£15–30 each). Budget £50–100 for initial puppy-proofing supplies.</li>
<li><strong>Stock essential puppy supplies</strong> — Food and water bowls (stainless steel: £8–12), puppy food (£15–30/month for quality brand), collar and lead (£10–20), ID tag (£3–5, legal requirement from 8 weeks), crate (£25–50), bedding (£15–25), puppy pads (£8–15 for 50 pack).</li>
<li><strong>Follow the vaccination schedule</strong> — First vaccination at 6–8 weeks: £30–50 (usually done by breeder). Second vaccination at 10–12 weeks: £30–50. Some vets offer a third at 16 weeks. Full protection 1–2 weeks after final jab. Annual booster: £30–60. Keep vaccination records safe.</li>
<li><strong>Establish a feeding routine immediately</strong> — 8–12 weeks: 4 meals per day. 3–6 months: 3 meals per day. 6–12 months: 2 meals per day. Transition food gradually over 7–10 days (mix old and new in shifting ratios). Fresh water available at all times. Monthly food cost: £15–40 depending on breed size.</li>
<li><strong>Start socialisation before 14 weeks</strong> — This is the critical window for positive experiences. Before full vaccination: carry your puppy in public to experience sounds and sights safely. After vaccination: introduce to other vaccinated dogs, different surfaces, vehicles, and people of all ages. Puppy classes: £40–80 for a 6-week course.</li>
<li><strong>Register with a vet within the first week</strong> — Initial health check: £30–60 (some practices offer free first puppy checks). Microchipping (legal requirement): £10–20 if not already done. Flea treatment from 8 weeks: £5–12/month. Worming from 2 weeks: £3–8/month. Pet insurance: £15–40/month.</li>
<li><strong>Begin basic training from day one</strong> — Toilet training: take outside every 2 hours and after meals, praise immediately on success. Name recognition: say their name, reward when they look at you. "Sit" command: can start from 8 weeks using treat luring. Keep sessions to 5 minutes maximum for young puppies.</li>
<li><strong>Plan the first-year cost timeline</strong> — Month 1: initial supplies and vet (£200–400). Months 2–3: vaccinations, food, insurance (£100–200). Months 4–6: neutering/spaying (£100–300), puppy classes (£40–80). Months 7–12: ongoing food, insurance, flea/worm treatment (£50–80/month). Total first year: £800–1,800.</li>
<li><strong>Set up a sleep and routine schedule</strong> — Puppies need 18–20 hours of sleep daily until 12 weeks, then 16–18 hours until 6 months. Create a consistent daily routine: wake, toilet, breakfast, play, nap, lunch, training, nap, walk (after vaccinations), dinner, quiet time, bed. Consistency reduces anxiety.</li>
<li><strong>Monitor health milestones weekly</strong> — Weeks 8–12: rapid growth, ensure adequate nutrition. Weeks 12–16: teething begins, provide appropriate chew toys (£5–10). Months 4–6: adult teeth emerge, check alignment. Month 6: discuss neutering/spaying with vet. Month 12: transition to adult food gradually over 2 weeks.</li>
</ol>
"""

PRACTICAL_GUIDES["puppy-vaccination"] = """
<ol class="wp-block-list">
<li><strong>Understand the core vaccination schedule</strong> — First jab at 6–8 weeks: covers distemper, hepatitis, parvovirus, and leptospirosis (DHP+L). Second jab at 10–12 weeks: booster of the same. Some vets add a third at 16 weeks for high-risk areas. Full immunity develops 1–2 weeks after the final jab.</li>
<li><strong>Budget for the complete vaccination course</strong> — Primary course (2 jabs): £60–100 total. Initial vet consultation (if separate): £30–60. First annual booster at 12 months: £30–60. Subsequent annual boosters: £30–60. Kennel cough vaccine (optional, nasal spray): £20–40. Rabies (for travel): £50–70.</li>
<li><strong>Prepare for the vaccination appointment</strong> — Bring your puppy's previous vaccination records from the breeder. Note any health concerns to discuss. Take your puppy in a secure carrier (£15–30) or on a lead. Avoid setting your puppy on the vet waiting room floor — carry them to reduce disease exposure.</li>
<li><strong>Manage post-vaccination care</strong> — Monitor for 24–48 hours after each jab. Normal: mild lethargy, slight swelling at injection site, reduced appetite for one meal. Concerning (contact vet): vomiting, diarrhoea, facial swelling, difficulty breathing, collapse. Keep your puppy calm and rested for 24 hours post-vaccination.</li>
<li><strong>Follow the outdoor access timeline</strong> — Before first jab: garden only (if no unknown dogs have accessed it). After first jab: carry in arms in public for socialisation (no ground contact). 1–2 weeks after second jab: short walks on pavements (avoid parks and unknown dogs). After full course: full outdoor access.</li>
<li><strong>Keep records organised</strong> — Your vet provides a vaccination card — keep this with your important documents. Register on your vet's online portal if available. Set calendar reminders for booster dates. Many boarding kennels and dog daycares require up-to-date vaccination proof. Lost records can be retrieved from your vet.</li>
<li><strong>Understand booster requirements</strong> — Annual boosters are essential: leptospirosis immunity wanes after 12 months. DHP boosters may be given every 3 years depending on your vet's protocol. Missed boosters: if more than 15 months since last jab, a full primary course may be needed. Cost of restart: £60–100.</li>
<li><strong>Consider optional vaccinations based on lifestyle</strong> — Kennel cough: recommended if using boarding, daycare, or dog parks (£20–40/year). Rabies: only required for travel under the Pet Travel Scheme (£50–70, valid 3 years). Discuss with your vet which optional vaccines suit your puppy's lifestyle and risk level.</li>
</ol>
"""

PRACTICAL_GUIDES["puppy-teething"] = """
<ol class="wp-block-list">
<li><strong>Know the teething timeline</strong> — Weeks 2–4: baby teeth begin emerging (28 teeth total). Weeks 12–16: baby teeth start falling out. Months 4–6: adult teeth emerge (42 teeth total). Month 7: all adult teeth should be in place. If baby teeth remain alongside adult teeth after 7 months, consult your vet (£30–60).</li>
<li><strong>Recognise teething signs</strong> — Increased chewing on everything available. Drooling more than usual. Slight bleeding from gums (pink saliva on toys is normal). Reduced appetite for hard kibble. Irritability and restlessness. Occasionally mild fever. These are all normal and temporary.</li>
<li><strong>Provide appropriate chew relief</strong> — Frozen Kongs stuffed with puppy-safe paste: £5–8 for the toy, £3–5 for filling. Rubber teething rings designed for puppies: £3–7. Frozen damp flannels: free and very effective. Avoid: antlers, bones, and ice cubes (risk of tooth fracture). Rotate toys to maintain interest.</li>
<li><strong>Protect your belongings during teething</strong> — Apply bitter apple spray to furniture legs and cables: £4–7 per bottle. Provide a clear "yes" (approved chew toys) vs "no" (furniture, shoes) system. Redirect immediately when chewing inappropriate items — offer an approved toy within 2 seconds. Puppy-proof low shelves and table edges.</li>
<li><strong>Adjust feeding during peak teething</strong> — Soften kibble with warm water for 10 minutes during weeks 14–20. Offer frozen banana slices or carrot sticks as soothing snacks. Avoid very hard treats that could damage loose teeth. Maintain regular feeding schedule even if appetite temporarily drops. Wet puppy food: £1–2 per day as a temporary alternative.</li>
<li><strong>Start dental hygiene habits early</strong> — From 8 weeks: gently rub gums with your finger daily to get your puppy used to mouth handling. From 12 weeks: introduce a puppy finger brush (£3–5) with enzymatic puppy toothpaste (£4–7). Never use human toothpaste (toxic to dogs). Aim for daily brushing by 6 months.</li>
<li><strong>Monitor for teething complications</strong> — Persistent baby teeth (not fallen out by 7 months): vet extraction may be needed (£50–150 under sedation). Misaligned adult teeth: discuss with vet at 6-month check. Swollen or very red gums beyond normal teething: possible infection, vet visit needed. Broken baby teeth usually resolve naturally.</li>
<li><strong>Budget for the teething phase</strong> — Chew toys (rotation of 4–5): £15–30. Teething gel (optional, vet-approved): £5–8. Bitter apple spray: £4–7. Puppy toothbrush and paste: £7–12. Replacement of any destroyed items: variable. Vet dental check at 6 months: £30–60. Total teething phase budget: £60–120.</li>
</ol>
"""

PRACTICAL_GUIDES["puppy-first-week"] = """
<ol class="wp-block-list">
<li><strong>Prepare before collection day</strong> — Set up a puppy-safe room with bed, water, and puppy pads. Buy supplies in advance: food (same brand as breeder, £5–15), bowls (£8–12), collar with ID tag (£10–15, legal requirement), lead (£5–10), crate (£25–50), enzymatic cleaner for accidents (£5–8).</li>
<li><strong>Day 1: focus on comfort and calm</strong> — Collect puppy in the morning to allow maximum daytime settling. Bring a blanket rubbed on the puppy's littermates for scent comfort. Offer a small meal of the breeder's food. Show the toilet area immediately. Limit visitors — just immediate household members. First night: bed next to yours.</li>
<li><strong>Day 2–3: establish toilet training</strong> — Take outside (or to puppy pads) every 1–2 hours, immediately after waking, eating, and playing. Praise and treat within 3 seconds of toileting in the right place. Expect 5–8 accidents daily — this is normal. Clean with enzymatic cleaner (not bleach, which smells like urine to dogs).</li>
<li><strong>Day 3–4: introduce gentle handling</strong> — Handle paws, ears, and mouth briefly (10–15 seconds) 3–4 times daily. Pair with treats and calm praise. This prepares for future grooming, vet examinations, and nail trimming. Gently touch the collar area to build tolerance. Never force — if the puppy pulls away, try again later.</li>
<li><strong>Day 4–5: begin name training and house rules</strong> — Say your puppy's name, reward with a treat when they look at you. Practice 5–6 times per session, 3 sessions daily. Establish where the puppy is and isn't allowed from the start. Use stair gates (£15–30) to manage access. Consistency from all household members is essential.</li>
<li><strong>Day 5–7: start short alone-time practice</strong> — Leave the room for 30 seconds, return calmly (no fuss). Gradually extend to 2–3 minutes by day 7. This prevents separation anxiety later. Provide a Kong or chew toy during alone time. Never make departures or returns dramatic.</li>
<li><strong>Throughout the week: monitor health closely</strong> — Watch for: diarrhoea lasting more than 24 hours, refusal to eat for more than one meal, lethargy beyond normal puppy sleepiness, coughing or sneezing. Register with a vet within 48 hours of bringing your puppy home. First vet check: £30–60 (some offer free puppy checks).</li>
<li><strong>Week 1 feeding schedule</strong> — 8–10 week old puppy: 4 meals per day at consistent times (e.g., 7am, 11am, 3pm, 7pm). Use the same food as the breeder for the first 2 weeks. Portion size: follow packet guidelines for your puppy's expected adult weight. Fresh water available at all times but limit 2 hours before bedtime to reduce nighttime toilet needs.</li>
</ol>
"""

PRACTICAL_GUIDES["puppy-sleep"] = """
<ol class="wp-block-list">
<li><strong>Understand puppy sleep requirements by age</strong> — 8–10 weeks: 18–20 hours per day. 3–6 months: 16–18 hours per day. 6–12 months: 14–16 hours per day. Adult dogs: 12–14 hours per day. Puppies that don't get enough sleep become hyperactive and nippy — more sleep often solves behaviour issues.</li>
<li><strong>Create the ideal sleep environment</strong> — Dark or dim room (blackout blinds: £10–20 if needed). Quiet area away from household noise. Temperature between 16–20°C. A covered crate provides den-like security (crate: £25–50, cover: £10–20). White noise machine or fan for consistent background sound (£10–25).</li>
<li><strong>Establish a consistent bedtime routine</strong> — Same time each evening (aim for 9–10pm). Final toilet break 15 minutes before bed. 10 minutes of calm interaction (gentle stroking, quiet voice). Place in bed with a familiar scent item. Dim lights 30 minutes before bedtime. This routine signals sleep time within 3–5 days.</li>
<li><strong>Manage nighttime waking</strong> — Under 12 weeks: expect 1–2 toilet breaks per night (set an alarm every 3–4 hours). 12–16 weeks: may still need 1 break. 16+ weeks: most puppies sleep 6–8 hours through. For toilet breaks: carry outside quietly, no play or fuss, return to bed immediately. Avoid eye contact and talking.</li>
<li><strong>Schedule daytime naps properly</strong> — Enforce nap times if your puppy won't settle naturally. Rule of thumb: 1 hour awake, 2 hours sleeping. Use the crate or a quiet room for naps. Overtired puppies become destructive and bitey — this is the most common reason for "bad" puppy behaviour. 3–4 enforced naps daily.</li>
<li><strong>Transition sleeping locations gradually</strong> — Week 1: next to your bed. Week 2: 1 metre from your bed. Week 3: near the bedroom door. Week 4: just outside the bedroom. Week 5+: in the chosen permanent location. Move 30cm per night for the smoothest transition. Never rush this process — it prevents separation anxiety.</li>
<li><strong>Troubleshoot sleep problems</strong> — Crying at night: ensure toilet needs are met, then wait 5 minutes before responding. Waking too early: ensure the room is dark and avoid responding to early-morning noise. Restless sleep: check room temperature and bed comfort. Won't nap: increase physical activity by 10 minutes. Consult your vet if sleep issues persist beyond 2 weeks (£30–60).</li>
<li><strong>Track sleep patterns for vet visits</strong> — Note roughly how many hours your puppy sleeps daily. Record nighttime waking frequency. Track any changes in sleep patterns (sudden increase or decrease). This information helps your vet identify health issues early. Use a simple notebook or phone notes — no special app needed.</li>
</ol>
"""

PRACTICAL_GUIDES["puppy-proofing"] = """
<ol class="wp-block-list">
<li><strong>Start with the kitchen</strong> — Secure bin lids with locks (£3–5) or use a bin cupboard. Move cleaning products to high shelves or locked cupboards. Cover oven knobs if accessible. Block access behind appliances where cables are exposed. Remove food from low surfaces. Dishwasher tablets and pods are extremely toxic — store out of reach.</li>
<li><strong>Secure the living room</strong> — Cover or hide electrical cables with cable protectors (£5–10 per metre). Move remote controls, shoes, and small objects off low surfaces. Secure bookshelves and TV stands that could topple. Remove or elevate houseplants (lilies, poinsettias, and aloe vera are toxic to dogs). Use cord tidies for blind cords (strangulation risk).</li>
<li><strong>Puppy-proof bedrooms and bathrooms</strong> — Keep laundry baskets closed (socks are the most common item dogs swallow). Store medications in locked cabinets — even one paracetamol tablet can be fatal to a puppy. Close toilet lids. Remove bath products from tub edges. Store hair ties and elastic bands (choking hazard) in drawers.</li>
<li><strong>Make the garden safe</strong> — Check fencing for gaps — puppies can squeeze through spaces as small as 10cm. Secure gate latches at adult height. Remove or fence off toxic plants: daffodils, foxgloves, yew, rhododendrons. Cover or fence ponds and water features. Store garden chemicals (slug pellets, fertiliser) in locked sheds. Budget: £30–80 for garden puppy-proofing.</li>
<li><strong>Install barriers and gates</strong> — Stair gates prevent falls and restrict access: £15–30 each, typically need 2–3. Pressure-fit gates work for most doorways (63–90cm width). Wall-mounted gates for the top of stairs (essential safety, £20–35). Playpen for a safe contained area: £25–45. Check gate spacing is less than 5cm to prevent head entrapment.</li>
<li><strong>Create a puppy-safe zone</strong> — Designate one fully proofed room as the puppy's main area. Include bed, water, toys, and puppy pads. Remove all rugs (or use washable ones: £10–20) during toilet training. Close off the room with a gate when unsupervised. This is your puppy's safe space for the first 3–4 months.</li>
<li><strong>Address common hidden hazards</strong> — Check for: loose carpet edges (tripping and chewing), gaps behind sofas (puppies get stuck), small toy parts on the floor (if children in household), exposed nails or screws in furniture, toxic food in accessible bags (chocolate, grapes, onions, xylitol gum).</li>
<li><strong>Budget for puppy-proofing supplies</strong> — Stair gates (×2): £30–60. Cable protectors: £10–20. Bin locks: £6–10. Playpen: £25–45. Cupboard locks (×6): £6–12. Bitter apple deterrent spray: £4–7. Garden fence repair/reinforcement: £20–50. Total comprehensive puppy-proofing: £100–200.</li>
</ol>
"""

PRACTICAL_GUIDES["puppy-socialisation"] = """
<ol class="wp-block-list">
<li><strong>Understand the critical socialisation window</strong> — The period between 3–14 weeks is when puppies are most receptive to new experiences. After 14 weeks, fear responses become stronger and socialisation becomes harder. Start immediately when your puppy arrives home (typically 8 weeks). Every positive experience counts.</li>
<li><strong>Create a socialisation checklist</strong> — Aim to expose your puppy to 100 different positive experiences before 16 weeks. Include: 20+ different people (ages, appearances, uniforms), 10+ different dogs (sizes, breeds), 10+ surfaces (grass, gravel, metal, wood), 10+ sounds (traffic, sirens, fireworks recordings), 10+ environments (car, vet, shops that allow dogs).</li>
<li><strong>Socialise safely before full vaccination</strong> — Carry your puppy in arms or in a sling (£10–20) to public places. Visit friends' homes with vaccinated dogs. Attend puppy-specific classes (usually accept puppies with first vaccination): £40–80 for a 6-week course. Avoid dog parks, pavements with high dog traffic, and unknown dogs until fully vaccinated.</li>
<li><strong>Follow the 3-second rule</strong> — When introducing something new, let your puppy observe for 3 seconds before approaching. If they show curiosity, allow exploration. If they show fear (backing away, tail tucked), increase distance and pair with treats. Never force your puppy towards something scary. Retreat and try again another day.</li>
<li><strong>Introduce handling exercises daily</strong> — Touch paws (5 seconds each) — pair with a treat. Look in ears gently. Lift lips to check teeth. Touch tail and back end. Briefly hold your puppy's collar. These exercises prepare for vet visits, grooming, and nail trimming. Practice 2–3 times daily for 2–3 minutes each session.</li>
<li><strong>Start puppy classes at 8–10 weeks</strong> — Look for classes that use positive reinforcement only. Class size should be 6–8 puppies maximum. The venue should be clean and disinfected. Cost: £40–80 for a 6-week course, or £8–15 per individual session. Benefits: controlled socialisation, basic commands, and professional guidance.</li>
<li><strong>Avoid common socialisation mistakes</strong> — Don't overwhelm: 1–2 new experiences per day is enough. Don't force interactions with people or dogs. Don't assume all dogs are friendly — always ask before approaching. Don't skip socialisation during bad weather — use indoor alternatives. Don't stop at 14 weeks — continue throughout the first year.</li>
<li><strong>Track progress and plan ahead</strong> — Use a simple notebook to record new experiences and your puppy's reactions. Note any fear responses for gentle re-exposure later. By 16 weeks, your puppy should be comfortable with most everyday situations. Any persistent fears beyond 6 months may benefit from a behaviourist (£50–100 per session).</li>
</ol>
"""

PRACTICAL_GUIDES["puppy-care-glossary"] = """
<ol class="wp-block-list">
<li><strong>Learn essential health terms first</strong> — Microchipping: legal requirement, implanted between shoulder blades (£10–20 if not done by breeder). Neutering/spaying: surgical sterilisation (£100–300 depending on size/sex). Deworming: treatment for intestinal parasites, every 2 weeks until 12 weeks, then monthly until 6 months (£3–8 per treatment).</li>
<li><strong>Understand vaccination terminology</strong> — DHP: distemper, hepatitis, parvovirus (core vaccines). Lepto: leptospirosis (core in UK). Primary course: first 2 jabs at 8 and 10–12 weeks (£60–100 total). Booster: annual follow-up jab (£30–60). Titre test: blood test to check immunity levels without vaccinating (£50–80).</li>
<li><strong>Know your feeding terms</strong> — Complete food: provides all required nutrition (look for this on labels). Complementary food: must be mixed with other food. Kibble: dry food. Wet food: tinned or pouch. Life-stage food: formulated for puppy/adult/senior (always use puppy food until 12 months). Feeding guides are on every packet — follow weight-based recommendations.</li>
<li><strong>Familiarise yourself with behaviour terms</strong> — Socialisation: positive exposure to new experiences (critical period 3–14 weeks). Habituation: getting used to everyday stimuli. Desensitisation: gradual exposure to reduce fear. Positive reinforcement: rewarding desired behaviour (treats, praise). Bite inhibition: learning to control mouth pressure (taught through play).</li>
<li><strong>Understand grooming terms</strong> — Coat types: smooth (short, close-lying), double (dense undercoat + topcoat), wire (rough, bristly), long (flowing). Moulting: seasonal shedding, heaviest in spring and autumn. Stripping: removing dead wire coat by hand (professional: £30–60). Dematting: removing tangled fur (prevention better than cure — brush 3× weekly).</li>
<li><strong>Learn training terminology</strong> — Crate training: teaching your puppy to see a crate as a safe den. House training: teaching toilet habits (expect 4–6 months for reliability). Recall: coming when called (start training from 8 weeks). Heel: walking beside you without pulling. Clicker: small device making a consistent sound to mark good behaviour (£2–4).</li>
<li><strong>Know when terms matter at the vet</strong> — Worming protocol: every 2 weeks from 2–12 weeks, monthly to 6 months, then every 3 months lifelong (£3–8 per treatment). Flea prevention: monthly topical or tablet from 8 weeks (£5–12/month). Kennel cough: infectious respiratory disease, vaccine is a nasal spray (£20–40).</li>
<li><strong>Understand cost-related terms</strong> — Excess: amount you pay before insurance covers costs (£50–250 typical). Lifetime policy: covers conditions for the dog's whole life (£20–40/month). Per-condition policy: covers each condition for 12 months only (£10–25/month, cheaper but less comprehensive). Always read the exclusions before choosing a policy.</li>
</ol>
"""

PRACTICAL_GUIDES["first-time-dog-owner"] = """
<ol class="wp-block-list">
<li><strong>Research before choosing a breed</strong> — Match energy levels to your lifestyle: working breeds (Collies, Spaniels) need 2+ hours exercise daily; companion breeds (Cavaliers, Shih Tzus) need 30–60 minutes. Consider grooming needs: low-maintenance (Beagle, Labrador) vs high-maintenance (Poodle, Bichon Frise). Adoption fee: £50–200 from rescue; purchase: £500–3,000 from a registered breeder.</li>
<li><strong>Budget for the first year realistically</strong> — Initial setup (bed, crate, bowls, lead, toys): £150–300. Vaccinations: £60–100. Neutering/spaying: £100–300. Monthly food: £30–60. Monthly insurance: £15–40. Flea/worm prevention: £15–25/month. Annual vet check: £30–60. Total first year: £1,000–2,500 depending on breed and health.</li>
<li><strong>Register with a vet before bringing your dog home</strong> — Ask for recommendations from friends or local breed groups. Check opening hours and emergency cover. Register online or by phone. Book a first health check within 72 hours of bringing your dog home. First consultation: £30–60 (some offer free first checks for new puppies).</li>
<li><strong>Set up your home properly</strong> — Designate a feeding area (easy-to-clean floor). Choose a bed location (quiet corner, away from draughts). Set up a crate if using one (covered for den feel). Stock 2 weeks of food, treats, poo bags, and cleaning supplies. Install stair gates if needed (£15–30 each). Total setup time: 2–3 hours.</li>
<li><strong>Establish house rules from day one</strong> — Decide as a household: is the dog allowed on furniture? In bedrooms? Upstairs? Consistency from all family members is crucial — mixed signals confuse dogs and slow training. Write rules down and post them visibly. Changing rules later is much harder than starting strict and relaxing over time.</li>
<li><strong>Learn the legal requirements</strong> — Microchipping: compulsory for all dogs over 8 weeks (£10–20). ID tag on collar: must show owner's name and address (£3–5). Dog licence: not required in England, Scotland, or Wales. Lead laws: dogs must be on lead on roads, local bylaws may apply in parks. Pick up after your dog: fines up to £1,000.</li>
<li><strong>Build a daily routine</strong> — Morning: toilet, breakfast, 15–30 minute walk. Midday: toilet break, lunch (puppies only). Afternoon: play session or training (15–20 minutes). Evening: main walk (30–60 minutes depending on breed), dinner, quiet time. Bedtime: final toilet break, settle in bed. Dogs thrive on predictability.</li>
<li><strong>Plan for ongoing costs</strong> — Monthly budget: food £30–60, insurance £15–40, flea/worm treatment £15–25, treats and toys £10–20. Annual costs: vet check-up £30–60, booster vaccinations £30–60, dental cleaning if needed £150–300. Emergency vet fund or insurance excess: keep £200–500 accessible. Total ongoing: £100–150/month.</li>
</ol>
"""

PRACTICAL_GUIDES["puppy-training-guide"] = """
<ol class="wp-block-list">
<li><strong>Start with the four essential commands</strong> — "Sit": lure with treat above nose, reward when bottom touches floor. "Down": lure from sit position, draw treat to floor. "Stay": ask for sit, take one step back, reward. "Come": call name + "come" with high-value treat. Practice each 5–6 times per session, 3 sessions daily. Start from 8 weeks.</li>
<li><strong>Master toilet training in 4–6 weeks</strong> — Take outside every 1–2 hours, immediately after waking, eating, and playing. Use a consistent phrase ("go toilet"). Praise and treat within 3 seconds of success. Ignore accidents indoors — clean with enzymatic cleaner (£5–8). Keep a log of toilet times to predict patterns. Most puppies are reliable by 16–20 weeks.</li>
<li><strong>Use positive reinforcement only</strong> — Small training treats (£3–5 per bag, pea-sized pieces): use for new learning. Verbal praise and fuss: use for known behaviours. Toy rewards: use for high-energy dogs. Never punish mistakes — this creates fear and slows learning. A clicker (£2–4) helps mark exact moments of good behaviour.</li>
<li><strong>Invest in puppy classes</strong> — Group classes: £40–80 for a 6-week course (best for socialisation + basics). One-to-one training: £30–60 per session (best for specific issues). Online courses: £15–30 (good supplement, not a replacement for social learning). Start classes between 8–14 weeks for maximum benefit. Ask about the trainer's qualifications and methods.</li>
<li><strong>Address biting and mouthing immediately</strong> — Normal in puppies until 6 months. When your puppy bites: yelp once ("ouch"), turn away for 10 seconds, resume play. If biting continues, calmly leave the room for 30 seconds. Provide appropriate chew alternatives (Kong: £5–8, rope toy: £3–6). Never use hands as play toys. Most puppies grow out of mouthing by 7–8 months.</li>
<li><strong>Build lead walking skills gradually</strong> — Week 1: wear collar indoors for short periods (10–15 minutes). Week 2: attach lead indoors, let it drag (supervised). Week 3: hold the lead indoors, encourage following with treats. Week 4+: short outdoor walks (5 minutes per month of age). Stop moving when the lead tightens, resume when loose. Harness (£10–20) recommended over collar for walks.</li>
<li><strong>Manage common first-year challenges</strong> — Jumping up: turn away, only greet when all four paws are on the floor. Counter surfing: keep surfaces clear, reward "off" with a treat. Pulling on lead: stop-start technique (stop when pulling, move when loose). Barking: identify the cause (boredom, fear, attention), address the root. Seek professional help if issues persist beyond 3 weeks of consistent training.</li>
<li><strong>Set a training schedule for the first year</strong> — Weeks 8–12: toilet training, name recognition, "sit." Weeks 12–16: "down," "stay," lead introduction, socialisation. Months 4–6: recall, loose-lead walking, crate independence. Months 6–9: distraction training, impulse control ("leave it," "wait"). Months 9–12: proofing all commands in different environments. Training is a lifelong commitment, not a one-time effort.</li>
</ol>
"""

PRACTICAL_GUIDES["puppy-collars"] = """
<ol class="wp-block-list">
<li><strong>Measure your puppy's neck correctly</strong> — Use a soft tape measure around the base of the neck (where the collar sits). Add 2–3cm for comfort — you should be able to fit two fingers between the collar and neck. Re-measure every 2 weeks during rapid growth (8–16 weeks). Write measurements down to track growth.</li>
<li><strong>Choose the right first collar</strong> — Lightweight flat collar for puppies under 5kg: £5–10. Adjustable nylon collar with a quick-release buckle: safest option (£8–15). Avoid chain, prong, or slip collars — these are not suitable for puppies. Start with the smallest adjustable size and size up as needed.</li>
<li><strong>Add a legal ID tag immediately</strong> — UK law requires a tag with owner's name and address on all dogs in public (£3–5 for engraved tag). Include a phone number (optional but recommended). Do not put the dog's name on the tag (helps prevent theft). Replace tags when details change or text becomes illegible.</li>
<li><strong>Introduce the collar gradually</strong> — Day 1: let your puppy sniff the collar, reward with a treat. Day 2: place the collar loosely for 5 minutes, distract with play. Day 3: increase to 15 minutes. Day 4–5: wear for 30–60 minutes supervised. Day 6+: wear during all waking hours. Remove at night and during crate time for safety (snagging risk).</li>
<li><strong>Know when to switch to a harness</strong> — If your puppy pulls on the lead: a harness (£10–25) distributes pressure away from the throat. Brachycephalic breeds (Pugs, Bulldogs): always use a harness (respiratory concerns). Small breeds under 5kg: harness reduces neck injury risk. Use collar for ID tag + harness for lead attachment as a combination approach.</li>
<li><strong>Budget for collar progression</strong> — First puppy collar (8–12 weeks): £5–10. Second collar (3–6 months): £8–15. Adolescent/adult collar (6–12 months): £10–20. ID tags (×2 for replacement): £6–10. First harness (if needed): £10–25. Total collar costs in the first year: £30–60. Quality collars last 6–12 months before outgrowing.</li>
<li><strong>Check collar fit weekly during growth spurts</strong> — The two-finger rule: always maintain a two-finger gap. Signs the collar is too tight: red marks on skin, difficulty swallowing, coughing. Signs too loose: collar slips over ears, puppy catches jaw on collar. Growth spurts are most rapid at 8–16 weeks and again at 6–9 months.</li>
<li><strong>Consider reflective and safety features</strong> — Reflective collars (£8–15) or clip-on LED lights (£3–7) for winter walks. Breakaway collars for unsupervised indoor wear (snap open if caught). Waterproof collars (£10–18) for water-loving breeds. GPS tracker collars (£30–80 + monthly subscription £3–5) for dogs that roam — useful during off-lead training.</li>
</ol>
"""

PRACTICAL_GUIDES["puppy-food"] = """
<ol class="wp-block-list">
<li><strong>Choose the right food type for your puppy's age</strong> — Wet food: easier for very young puppies (8–10 weeks), £1–2 per day. Dry kibble: convenient and good for dental health, £15–30/month. Raw diet: requires careful nutritional balance, £30–60/month. Always select food labelled "complete" (provides all nutrients) not "complementary" (needs additions).</li>
<li><strong>Follow age-appropriate feeding frequencies</strong> — 8–12 weeks: 4 meals per day (e.g., 7am, 11am, 3pm, 7pm). 3–6 months: 3 meals per day (e.g., 7am, 12pm, 5pm). 6–12 months: 2 meals per day (e.g., 7am, 5pm). 12 months+: 2 meals per day for life. Consistent timing helps with toilet training and digestion.</li>
<li><strong>Calculate correct portion sizes</strong> — Follow the packet guidelines based on your puppy's expected adult weight, not current weight. Weigh food with kitchen scales (£5–10) rather than estimating. Adjust every 2 weeks based on body condition — you should feel ribs easily but not see them. Overfeeding causes rapid growth, which stresses developing joints.</li>
<li><strong>Transition between foods safely</strong> — Day 1–2: 75% old food, 25% new food. Day 3–4: 50% each. Day 5–6: 25% old, 75% new. Day 7: 100% new food. If diarrhoea occurs, slow the transition to 10–14 days. Sudden food changes are the most common cause of puppy digestive upset.</li>
<li><strong>Understand breed-specific nutritional needs</strong> — Large breeds (Labs, German Shepherds): specific large-breed puppy food with controlled calcium for joint development, £20–40/month. Small breeds (Chihuahuas, Yorkies): small-kibble formula, higher calorie density, £15–25/month. Giant breeds (Great Danes): must not grow too quickly — controlled-energy diets essential.</li>
<li><strong>Budget for monthly feeding costs</strong> — Small breed puppy: £15–25/month for quality food. Medium breed: £20–35/month. Large breed: £30–50/month. Giant breed: £40–70/month. Treats (training): £5–10/month (should not exceed 10% of daily calories). Fresh water: available at all times in a clean stainless steel bowl (£5–8).</li>
<li><strong>Know which foods are dangerous</strong> — Toxic to dogs: chocolate, grapes, raisins, onions, garlic, xylitol (sweetener), macadamia nuts, avocado. Cooked bones: can splinter and cause internal injury. Alcohol: extremely toxic even in small amounts. If ingestion occurs, contact your vet immediately or the Animal PoisonLine (£35 per call, 01202 509000).</li>
<li><strong>Plan the transition to adult food</strong> — Small breeds: transition at 10–12 months. Medium breeds: transition at 12 months. Large breeds: transition at 12–18 months. Giant breeds: transition at 18–24 months. Follow the same 7-day gradual transition method. Adult food has lower protein and calorie density — switching too early can affect growth.</li>
</ol>
"""

PRACTICAL_GUIDES["puppy-toys"] = """
<ol class="wp-block-list">
<li><strong>Stock essential toy types</strong> — Chew toys for teething: rubber Kongs (£5–8), rope toys (£3–6). Interactive toys for mental stimulation: puzzle feeders (£8–15), snuffle mats (£10–18). Comfort toys: soft plush for bedtime (£4–8). Fetch toys: tennis-sized balls (£2–4, avoid small balls for large breed puppies — choking hazard). Start with 4–5 toys.</li>
<li><strong>Match toys to your puppy's age and size</strong> — 8–12 weeks: soft rubber toys, small plush toys, puppy-specific Kongs. 3–6 months (teething peak): frozen Kongs, cooling teethers (£4–7), sturdy rope toys. 6–12 months: larger chew toys, interactive puzzles, training-specific toys. Always choose toys larger than your puppy's mouth to prevent choking.</li>
<li><strong>Rotate toys to maintain interest</strong> — Keep 3–4 toys available at a time. Rotate every 3–4 days. Store unused toys in a closed container. When rotated toys reappear, puppies treat them as new. This also extends toy lifespan and saves money. Exception: keep one comfort toy available constantly for security.</li>
<li><strong>Use toys for training and enrichment</strong> — Stuff Kongs with puppy food paste or peanut butter (xylitol-free) and freeze for 2–3 hours — provides 15–30 minutes of focused activity. Scatter kibble in a snuffle mat for mealtime enrichment. Use tug toys (£5–8) to teach "drop it" and impulse control. Interactive play builds your bond.</li>
<li><strong>Inspect toys regularly for safety</strong> — Check all toys daily for: loose parts, torn seams, exposed stuffing, small pieces that could break off. Rubber toys: replace when they show teeth marks deeper than 2mm. Rope toys: replace when fibres start separating (ingested fibres can cause intestinal blockages). Plush toys: remove if your puppy is a destructive chewer.</li>
<li><strong>Budget for toys across the first year</strong> — Initial toy starter kit: £25–40. Monthly toy replacement: £5–10 (more during heavy teething at 3–6 months). Puzzle toys (longer lasting): £8–15 each. Total first-year toy budget: £80–160. Invest more in durable interactive toys and less in cheap plush that won't survive a week.</li>
<li><strong>Avoid dangerous toy choices</strong> — Never give: cooked bones (splinter risk), toys with button eyes or small attachments, toys designed for children (not tested for dog use), sticks (splinter and impalement risk). Supervise all play with new toys for the first 15 minutes. Remove any toy your puppy can compress to fit entirely in their mouth.</li>
<li><strong>Create DIY enrichment toys for free</strong> — Knotted old t-shirt: free tug toy. Cardboard box with treats hidden inside: free puzzle. Muffin tin with tennis balls covering treats: free snuffle game. Frozen banana or carrot sticks: free teething soother. Empty plastic bottle (cap removed, supervised): free crunchy toy. Creativity costs nothing.</li>
</ol>
"""

# --- DOG HEALTH cluster ---
PRACTICAL_GUIDES["dog-health-generic"] = """
<ol class="wp-block-list">
<li><strong>Schedule regular veterinary check-ups</strong> — Annual health check for adult dogs: £30–60. Senior dogs (7+ years): twice-yearly checks recommended (£60–120/year). Puppies: monthly checks until 16 weeks, then at 6 months and 12 months. Annual booster vaccinations: £30–60. Always bring a list of any concerns to discuss with your vet.</li>
<li><strong>Maintain preventative treatments year-round</strong> — Flea treatment: monthly topical or tablet (£5–12/month). Worming: every 3 months for adult dogs (£3–8 per treatment). Tick prevention: especially March–October in the UK (£5–15/month). Some combination products cover all three (£10–20/month). Never skip winter treatments — parasites are increasingly year-round in the UK.</li>
<li><strong>Monitor your dog's weight monthly</strong> — Weigh at home using bathroom scales (weigh yourself, then yourself holding the dog, subtract). Ideal body condition: you can feel ribs easily but not see them, clear waist when viewed from above. Overweight dogs: reduce food by 10% and increase exercise by 15 minutes daily. Consult your vet if weight changes are sudden (£30–60 consultation).</li>
<li><strong>Learn the warning signs of common conditions</strong> — Seek same-day vet care for: persistent vomiting or diarrhoea (over 24 hours), blood in urine or stool, sudden lethargy or collapse, difficulty breathing, bloated abdomen, seizures. Non-urgent but needs attention within a week: gradual weight loss, increased thirst, lumps or bumps, persistent coughing, limping.</li>
<li><strong>Establish a dental care routine</strong> — Brush teeth daily with enzymatic dog toothpaste (£4–7) and a finger brush or dog toothbrush (£3–5). Start gradually — just gum rubbing for the first week. Dental chews: 1 per day (£5–15/month). Professional dental cleaning under anaesthetic: £150–300 every 1–2 years for breeds prone to dental disease. Dental examination: £20–40.</li>
<li><strong>Support joint health from the right age</strong> — Large breeds: start joint supplements from 12 months (glucosamine + chondroitin: £10–20/month). All breeds over 7 years: consider joint supplementation. Maintain healthy weight — every extra kilogram puts 4× the stress on joints. Gentle, consistent exercise is better than occasional intense activity. Joint assessment: £30–60.</li>
<li><strong>Build an emergency fund</strong> — Keep £200–500 accessible for unexpected vet visits. Average emergency consultation: £100–250. Common emergency costs: gastric foreign body removal (£1,000–3,000), broken leg repair (£1,500–4,000). Pet insurance: £15–40/month covers major emergencies (check excess amounts: typically £50–250). Emergency out-of-hours vet visit: £150–350.</li>
<li><strong>Track your dog's health baselines</strong> — Normal resting heart rate: 60–140 bpm (smaller dogs higher). Normal temperature: 38.3–39.2°C. Normal breathing rate at rest: 10–35 breaths per minute. Normal gum colour: pink (pale, white, blue, or yellow gums are emergencies). Know your dog's normal behaviour — you are the best judge of subtle changes.</li>
</ol>
"""

PRACTICAL_GUIDES["dog-dental-health"] = """
<ol class="wp-block-list">
<li><strong>Start a daily brushing routine</strong> — Week 1: let your dog lick toothpaste (enzymatic, dog-safe: £4–7) off your finger. Week 2: rub finger along the outside of teeth and gums. Week 3: introduce a finger brush (£3–5) or soft dog toothbrush. Week 4+: brush all outer tooth surfaces for 30–60 seconds. Focus on the upper back teeth where plaque builds fastest.</li>
<li><strong>Choose the right dental products</strong> — Enzymatic toothpaste: £4–7, breaks down plaque chemically. Finger brush: £3–5, easiest for beginners. Angled dog toothbrush: £3–6, reaches back teeth better. Dental water additive: £5–10/month, reduces bacteria. Dental chews (VOHC-approved): £5–15/month. Never use human toothpaste — fluoride and xylitol are toxic to dogs.</li>
<li><strong>Recognise dental disease early</strong> — Stage 1: bad breath and slight yellowing (reversible with brushing). Stage 2: visible tartar, red gum line (needs professional cleaning: £150–300). Stage 3: gum recession, loose teeth (extraction may be needed: £100–200 per tooth). Stage 4: severe infection, tooth loss, bone damage (extensive treatment: £300–800). 80% of dogs show dental disease by age 3.</li>
<li><strong>Schedule professional dental care</strong> — Annual dental examination: £20–40 (often included in annual check-up). Professional cleaning under anaesthetic: £150–300. Frequency: every 1–2 years for most dogs, annually for prone breeds (small breeds, Greyhounds, Cavaliers). X-rays if needed: £50–100 additional. Post-cleaning antibiotics if infection present: £15–30.</li>
<li><strong>Use dental chews effectively</strong> — Choose VOHC (Veterinary Oral Health Council) approved products for proven effectiveness. One appropriate-sized chew per day after the main meal. Supervise chewing — remove small pieces that could be swallowed whole. Dental chews are a supplement to brushing, not a replacement. Budget: £5–15/month depending on dog size.</li>
<li><strong>Address breed-specific dental needs</strong> — Small breeds (Yorkies, Chihuahuas): crowded teeth, need more frequent cleaning, start dental checks from 6 months. Brachycephalic breeds (Pugs, Bulldogs): misaligned teeth trap food, brush daily without exception. Greyhounds: genetically prone to dental disease, professional cleaning often needed annually. Large breeds: less prone but check for fractured teeth from chewing.</li>
<li><strong>Know when dental problems need urgent attention</strong> — Immediate vet visit: broken tooth with exposed pulp, facial swelling, bleeding from the mouth that doesn't stop, refusal to eat for more than 24 hours. Within a week: bad breath that worsens suddenly, pawing at the mouth, drooling excessively, loose teeth. Emergency dental visit: £80–200 consultation.</li>
<li><strong>Budget for lifetime dental care</strong> — Daily brushing supplies: £30–50/year. Dental chews: £60–180/year. Annual vet dental check: £20–40/year. Professional cleaning (every 1–2 years): £150–300. Potential extractions: £100–200 per tooth. Total annual dental budget: £150–350. Prevention (brushing + chews) saves significantly compared to treatment costs.</li>
</ol>
"""

PRACTICAL_GUIDES["dog-joint-supplements"] = """
<ol class="wp-block-list">
<li><strong>Determine if your dog needs joint support</strong> — Breeds predisposed to joint issues: German Shepherds, Labradors, Golden Retrievers, Rottweilers, Dachshunds. Signs of joint discomfort: stiffness after rest (especially morning), reluctance to jump or climb stairs, slowing on walks, licking or chewing joints. Age factor: most dogs benefit from supplementation after 7 years.</li>
<li><strong>Understand the key supplement ingredients</strong> — Glucosamine: building block for cartilage repair (recommended dose: 20mg per kg of body weight daily). Chondroitin: slows cartilage breakdown (often paired with glucosamine). MSM: anti-inflammatory properties. Omega-3 fatty acids: reduce joint inflammation. Green-lipped mussel: contains natural glucosamine and omega-3. Turmeric: anti-inflammatory (consult vet for correct dose).</li>
<li><strong>Choose the right supplement format</strong> — Tablets/capsules: most concentrated, £10–20/month. Liquid: easy to add to food, £12–25/month. Powder: mix into meals, £8–18/month. Treats/chews: most palatable, £12–25/month but may contain fillers. Veterinary-grade supplements cost more (£15–30/month) but guarantee ingredient quality and concentration.</li>
<li><strong>Set realistic expectations for results</strong> — Joint supplements are not painkillers — they support cartilage health over time. Allow 4–6 weeks before assessing improvement. Signs of benefit: easier movement after rest, more willingness to exercise, reduced stiffness on cold mornings. If no improvement after 8 weeks, consult your vet about alternative approaches (£30–60).</li>
<li><strong>Support supplements with lifestyle changes</strong> — Maintain healthy weight: every extra kilogram adds 4× stress on joints. Provide low-impact exercise: swimming (if available), short frequent walks instead of long runs. Use ramps for car access (£20–40) and steps for sofa/bed access (£15–30). Orthopaedic bed (£50–120) for quality rest. Non-slip mats on hard floors (£5–10 each).</li>
<li><strong>Monitor and adjust over time</strong> — Keep a simple diary of your dog's mobility: note morning stiffness duration, willingness to exercise, and any limping. Share this with your vet at check-ups. Dose may need adjusting as your dog ages. Some dogs need combination supplements — start with glucosamine/chondroitin and add omega-3 if needed. Annual joint assessment: £30–60.</li>
<li><strong>Know when supplements aren't enough</strong> — Supplements cannot reverse advanced arthritis or structural joint damage. If mobility continues declining despite supplementation, your vet may recommend: prescription anti-inflammatory medication (£15–30/month), physiotherapy (£30–50 per session), hydrotherapy (£25–40 per session), or in severe cases, surgical options (£1,500–5,000).</li>
<li><strong>Budget for long-term joint care</strong> — Basic glucosamine supplement: £8–15/month. Combination supplement (glucosamine + chondroitin + MSM): £12–25/month. Omega-3 fish oil: £5–12/month. Total supplement cost: £15–35/month. Orthopaedic bed replacement every 2 years: £50–120. Annual joint health check: £30–60. Total annual joint care budget: £250–550.</li>
</ol>
"""

PRACTICAL_GUIDES["dog-flea-treatment"] = """
<ol class="wp-block-list">
<li><strong>Choose the right flea treatment type</strong> — Spot-on treatments: applied to back of neck monthly (£5–12/month). Oral tablets: swallowed monthly, fast-acting (£8–15/month). Flea collars: continuous release over 6–8 months (£15–30 per collar). Sprays: immediate knockdown, less residual protection (£8–15 per bottle). Consult your vet for the most effective option for your area and dog.</li>
<li><strong>Treat year-round, not just summer</strong> — Central-heated UK homes harbour fleas throughout winter. Flea eggs can survive in carpets for up to 6 months. Missing even one month allows populations to rebuild. Monthly treatment is essential January through December. Switching products occasionally can help prevent resistance building.</li>
<li><strong>Check for fleas regularly</strong> — Use a flea comb (£2–4) weekly, focusing behind ears and at the tail base. Look for "flea dirt" (black specks that turn red-brown on a wet tissue). Part the fur to check skin directly. Early detection prevents full infestations. If you find live fleas despite treatment, contact your vet to discuss alternative products.</li>
<li><strong>Treat your home as well as your dog</strong> — Wash all pet bedding at 60°C weekly during active infestations. Vacuum all floors thoroughly every 2–3 days (dispose of the bag or empty the canister immediately). Use a household flea spray (£8–15 per can, treats 1–2 rooms): spray carpets, skirting boards, and furniture crevices. Home treatment takes 2–3 months to eliminate all life stages.</li>
<li><strong>Treat all pets in the household simultaneously</strong> — Fleas move between animals. Treat every cat and dog on the same day with species-appropriate products (cat flea treatments differ from dog treatments — never use dog products on cats, they can be fatal). Even indoor cats need treatment if dogs go outside. Coordinate treatment with all pet owners in your household.</li>
<li><strong>Address flea allergy dermatitis</strong> — Some dogs are allergic to flea saliva, causing severe itching from even one bite. Signs: intense scratching, hair loss (especially at tail base and thighs), red inflamed skin, secondary skin infections. Treatment: strict year-round flea prevention plus vet-prescribed anti-itch medication (£20–40/month). Vet consultation for skin issues: £30–60.</li>
<li><strong>Combine flea and tick prevention wisely</strong> — Many products cover both fleas and ticks. Tick season in the UK: March–October (but year-round in some areas). Combination spot-ons: £8–15/month. Combination tablets: £10–18/month. Check for ticks after countryside and woodland walks using a tick removal tool (£3–5). Lyme disease risk areas: consult your vet about additional tick protection.</li>
<li><strong>Budget for annual flea prevention</strong> — Monthly spot-on treatment: £60–144/year. Monthly oral tablet: £96–180/year. Long-lasting collar (×2 per year): £30–60/year. Household flea spray (×2 per year for prevention): £16–30. Flea comb: £2–4 (one-off). Total annual flea prevention: £80–220. Compare: treating an infestation costs £150–400+ including home treatment and vet visits.</li>
</ol>
"""

PRACTICAL_GUIDES["dog-health-care-complete"] = """
<ol class="wp-block-list">
<li><strong>Create an annual health calendar</strong> — January: check pet insurance renewal. March: start tick prevention alongside flea treatment. April: annual vet check-up and booster vaccination (£60–120 combined). June: summer parasite review. September: autumn health check for senior dogs. December: review the year's health records and plan for the next year.</li>
<li><strong>Build a first aid kit for your dog</strong> — Conforming bandage (£2–3), sterile gauze pads (£2–4), antiseptic wound wash (£4–6), tweezers for splinters (£3–5), tick removal tool (£3–5), digital thermometer (£5–8, rectal use only), styptic powder for nail bleeding (£4–6), emergency vet phone number card. Store in a labelled container. Total: £25–40.</li>
<li><strong>Understand your dog's life stage health needs</strong> — Puppy (0–1 year): vaccinations, neutering, growth monitoring. Adult (1–7 years): annual check-ups, weight management, dental care. Senior (7+ years): twice-yearly checks, joint support, organ function blood tests (£50–100). Giant breeds become "senior" at 5–6 years. Adjust care proactively, not reactively.</li>
<li><strong>Manage nutrition for health</strong> — Feed a complete, balanced food appropriate for life stage. Treats: maximum 10% of daily calorie intake. Fresh water: available at all times, change daily, wash bowls every 2 days. Supplements only on veterinary advice. Food allergy signs: itchy skin, ear infections, digestive upset — elimination diet trial: 8–12 weeks under vet supervision (£30–60 consultation).</li>
<li><strong>Exercise appropriately for your dog's breed and age</strong> — Small breeds: 30–60 minutes daily. Medium breeds: 60–90 minutes daily. Large active breeds: 90–120+ minutes daily. Puppies: 5 minutes per month of age, twice daily (e.g., 4-month puppy = 20 minutes twice). Senior dogs: shorter, gentler walks — prioritise consistency over intensity. Adjust in extreme heat (above 25°C) or cold (below 0°C).</li>
<li><strong>Keep vaccinations and preventative care current</strong> — Core annual booster: £30–60. Flea prevention: £5–12/month. Worming: every 3 months (£3–8 per treatment). Tick prevention March–October: £5–15/month. Kennel cough vaccine (if needed): £20–40/year. Total annual preventative care: £200–400. Prevention is always cheaper than treatment.</li>
<li><strong>Recognise breed-specific health risks</strong> — Labradors: obesity, hip/elbow dysplasia, eye conditions. German Shepherds: hip dysplasia, degenerative myelopathy. Bulldogs: breathing difficulties (BOAS), skin fold infections, spinal issues. Cavaliers: heart disease (mitral valve), syringomyelia. Dachshunds: intervertebral disc disease. Discuss breed-specific screening with your vet.</li>
<li><strong>Plan financially for healthcare</strong> — Pet insurance (lifetime policy): £20–40/month (£240–480/year). Annual routine costs: £300–500 (check-ups, vaccinations, preventatives). Emergency fund: keep £200–500 accessible. Average unexpected vet bill in the UK: £300–800. Dental cleaning every 1–2 years: £150–300. Total annual health budget: £600–1,200 depending on breed and age.</li>
</ol>
"""

PRACTICAL_GUIDES["seasonal-dog-care"] = """
<ol class="wp-block-list">
<li><strong>Prepare for spring (March–May)</strong> — Restart tick prevention if paused over winter (£5–15/month). Schedule annual vet check-up and booster vaccination. Increase exercise gradually after a quieter winter. Begin moulting management: brush double-coated breeds daily (furminator-type tools: £10–20). Check garden for toxic spring bulbs (daffodils, tulips) before allowing outdoor access.</li>
<li><strong>Manage summer safely (June–August)</strong> — Never leave your dog in a car — even with windows open, temperatures can reach lethal levels in 10 minutes. Walk early morning (before 8am) and evening (after 7pm) when pavements are cooler. Test pavement temperature: if you can't hold your hand on it for 5 seconds, it's too hot for paws. Provide shade and fresh water at all times. Cooling mat: £15–25.</li>
<li><strong>Recognise and prevent heatstroke</strong> — Warning signs: excessive panting, drooling, red gums, vomiting, staggering, collapse. Immediate action: move to shade, apply cool (not cold) water to ears, paws, and belly, offer small amounts of water, get to a vet urgently. At-risk breeds: Bulldogs, Pugs, Boxers, Cavaliers, and any overweight or senior dog. Emergency vet visit: £150–350.</li>
<li><strong>Prepare for autumn (September–November)</strong> — Reduce exercise duration as daylight shortens. Add reflective gear for evening walks: reflective collar (£8–15), LED collar light (£3–7), hi-vis dog coat (£10–20). Watch for conkers and acorns (mildly toxic if eaten in quantity). Start transition to warmer bedding. Continue flea treatment — central heating reactivates dormant flea eggs indoors.</li>
<li><strong>Manage winter care (December–February)</strong> — Protect paws from road salt and grit: rinse feet after walks or use paw wax (£5–8). Short-coated breeds need a waterproof dog coat (£10–25) for walks below 5°C. Reduce walk duration in extreme cold but maintain frequency. Antifreeze is extremely toxic and tastes sweet to dogs — clean any spills immediately and store securely.</li>
<li><strong>Adjust feeding seasonally</strong> — Active outdoor dogs may need 10–15% more food in winter to maintain body heat. Less active dogs in winter: reduce food by 10% to prevent weight gain. Summer: ensure adequate hydration, add water to kibble if your dog drinks less in heat. Monitor weight monthly and adjust portions accordingly.</li>
<li><strong>Handle fireworks season (October–January)</strong> — Create a safe den space with the bed in a quiet interior room. Close curtains, play background music or TV. Use an Adaptil diffuser (£15–25, plug in 48 hours before expected fireworks). Do not punish anxious behaviour or force your dog outside. Severe anxiety: discuss medication with your vet well in advance (£30–60 consultation + £10–20 medication).</li>
<li><strong>Plan seasonal health spending</strong> — Spring: vet check + booster (£60–120), grooming tools (£10–20). Summer: cooling products (£15–40), increased water access. Autumn: reflective gear (£15–30), updated flea treatment. Winter: dog coat (£10–25), paw protection (£5–10). Total seasonal extras: £100–250/year on top of regular healthcare budget.</li>
</ol>
"""

PRACTICAL_GUIDES["dog-dental-care-products"] = """
<ol class="wp-block-list">
<li><strong>Build a complete dental care kit</strong> — Enzymatic dog toothpaste (poultry or beef flavour): £4–7. Finger brush for beginners: £3–5. Angled-head dog toothbrush: £3–6. Dental water additive: £5–10. VOHC-approved dental chews: £5–15/month. Dental spray for difficult dogs: £6–10. Total starter kit: £25–45.</li>
<li><strong>Choose the right toothpaste</strong> — Always use enzymatic dog toothpaste — it continues working after brushing. Popular flavours: poultry, beef, or seafood (helps your dog accept brushing). Avoid human toothpaste (contains fluoride and xylitol, both toxic). A tube lasts 4–8 weeks depending on dog size. Replace if the consistency changes or the expiry date passes.</li>
<li><strong>Select the best brush for your dog</strong> — Finger brush: best for small dogs and dogs new to brushing (£3–5, replace monthly). Dual-headed toothbrush: cleans both sides simultaneously (£4–7). Angled-head brush: reaches back molars more easily (£3–6). Electric dog toothbrushes: available but most dogs find vibration stressful. Start with the simplest option and upgrade as your dog becomes comfortable.</li>
<li><strong>Use dental chews correctly</strong> — Choose VOHC (Veterinary Oral Health Council) approved products for proven plaque reduction. Give one chew per day after the largest meal. Match chew size to your dog: too small = choking risk, too large = ineffective. Calorie content: dental chews can be 50–100 calories each — reduce meal portions accordingly. Monthly cost: £5–15 depending on dog size.</li>
<li><strong>Try dental water additives</strong> — Add to drinking water daily for passive dental protection. Most are tasteless and odourless. Active ingredients typically include chlorhexidine or zinc. Change water daily (do not top up). Costs £5–10 per bottle (lasts 4–6 weeks). Effective as a supplement to brushing but not a replacement. Monitor water intake — some dogs drink less initially.</li>
<li><strong>Consider dental diets for prone breeds</strong> — Prescription dental diets have kibble designed to scrape teeth as the dog chews. Available for dogs prone to dental disease (small breeds, brachycephalic breeds). Cost: £15–30/month (more than standard food). Requires veterinary recommendation. Most effective when combined with daily brushing. Not suitable for all dogs — discuss with your vet.</li>
<li><strong>Know what to avoid</strong> — Hard bones and antlers: cause tooth fractures (common emergency: £100–300 per extraction). Tennis balls: abrasive surface wears down enamel over time. Human dental products: toxic to dogs. Very hard nylon chews: can crack teeth if your dog is an aggressive chewer. Rope toys: fibres can wrap around teeth and damage gums.</li>
<li><strong>Schedule professional dental care alongside home care</strong> — Annual dental check: £20–40 (often included in annual health check). Professional scale and polish: £150–300 under anaesthetic. Pre-anaesthetic blood test (recommended for dogs over 7): £50–80. Extractions if needed: £50–200 per tooth. Home care reduces professional intervention frequency — daily brushing can halve the need for professional cleaning.</li>
</ol>
"""

# --- DOG GROOMING cluster ---
PRACTICAL_GUIDES["dog-grooming-generic"] = """
<ol class="wp-block-list">
<li><strong>Establish a grooming schedule by coat type</strong> — Smooth coat (Boxer, Dalmatian): brush weekly, bath every 6–8 weeks. Double coat (Labrador, Husky): brush 3× weekly (daily during moult), bath every 8–12 weeks. Wire coat (Terriers, Schnauzers): brush 2–3× weekly, hand-strip every 6–8 weeks. Long coat (Shih Tzu, Maltese): brush daily, bath every 4–6 weeks, professional trim every 6–8 weeks.</li>
<li><strong>Invest in the right grooming tools</strong> — Slicker brush (all coat types): £5–10. Bristle brush (smooth coats): £4–8. Undercoat rake (double coats): £8–15. Dematting comb (long coats): £6–12. Nail clippers (guillotine or scissor style): £5–10. Styptic powder for nail bleeding: £4–6. Grooming table (optional for large dogs): £30–60. Total starter kit: £30–50.</li>
<li><strong>Learn to brush effectively</strong> — Always brush in the direction of hair growth. Start from the head and work towards the tail. For double coats: use an undercoat rake first, then finish with a slicker brush. For long coats: work in sections, holding the hair above the section you're brushing. Remove mats gently with a dematting comb — never cut mats with scissors (skin injury risk).</li>
<li><strong>Bathe your dog correctly</strong> — Use lukewarm water (test on your inner wrist). Wet thoroughly, avoiding ears and eyes. Apply dog shampoo (£4–8) from neck to tail, working into a lather. Rinse completely — soap residue causes skin irritation. Towel dry, then use a low-heat dryer if your dog tolerates it. Sensitive skin: use hypoallergenic or oatmeal shampoo (£5–10).</li>
<li><strong>Trim nails every 2–4 weeks</strong> — Use guillotine clippers for small to medium dogs, scissor clippers for large dogs. Cut at a 45-degree angle, trimming 1–2mm at a time. Avoid the quick (pink area inside the nail visible in light-coloured nails). For dark nails: trim tiny amounts until you see a grey or pink circle in the cut surface. If you cut the quick: apply styptic powder immediately. Alternatively, use a nail grinder (£10–20).</li>
<li><strong>Clean ears fortnightly</strong> — Use a dog-specific ear cleaner (£5–8). Apply cleaner into the ear canal, massage the base for 30 seconds, let your dog shake, then wipe with cotton wool. Never use cotton buds — they push debris deeper. Signs of infection: redness, swelling, discharge, odour, head shaking. Ear infection vet visit: £30–60 plus treatment (£10–25).</li>
<li><strong>Consider professional grooming for complex coats</strong> — Full professional groom: £25–50 for small dogs, £40–70 for medium, £50–90 for large. Frequency: every 6–8 weeks for breeds requiring trimming. Bath and brush only: £15–30. Ask about qualifications — look for City & Guilds Level 3 or equivalent. Book in advance: popular groomers have 2–4 week waiting lists.</li>
<li><strong>Maintain grooming between professional visits</strong> — Brush 2–3 times weekly (daily for long and double coats). Check and clean ears fortnightly. Trim nails every 2–4 weeks. Wipe paws after muddy walks. Check for lumps, ticks, and skin changes during every brushing session. Teeth brushing: daily (see our dental care guide). Grooming is also a health check opportunity.</li>
</ol>
"""

PRACTICAL_GUIDES["dog-brushes"] = """
<ol class="wp-block-list">
<li><strong>Match your brush to your dog's coat type</strong> — Smooth coats (Labrador, Beagle): bristle brush (£4–8) or rubber curry brush (£3–6). Double coats (German Shepherd, Husky): undercoat rake (£8–15) plus slicker brush (£5–10). Wire coats (Terrier, Schnauzer): slicker brush plus stripping knife (£8–12). Long coats (Maltese, Shih Tzu): pin brush (£6–10) plus wide-tooth comb (£4–8).</li>
<li><strong>Invest in quality over quantity</strong> — A good slicker brush with flexible pins lasts 2–3 years (£8–12). Cheap brushes with rigid pins can scratch skin. Undercoat rakes should have rounded pin tips to prevent skin damage. Dematting tools need sharp but safe blades (£6–12). Replace brushes when pins bend, loosen, or lose their coating.</li>
<li><strong>Learn the correct brushing technique</strong> — Slicker brush: short, gentle strokes in the direction of hair growth, lift at the end of each stroke. Undercoat rake: long, slow strokes from skin outward, apply light pressure only. Pin brush: use like a human hairbrush, working through long hair in sections. Bristle brush: firm circular motions to distribute oils and remove loose hair.</li>
<li><strong>Establish a brushing schedule</strong> — Smooth coats: once weekly, 10–15 minutes. Short double coats: twice weekly, 15–20 minutes. Long double coats: 3–4 times weekly, 20–30 minutes. Wire coats: 2–3 times weekly, 15–20 minutes. Long silky coats: daily, 15–20 minutes. During spring and autumn moult: increase to daily for all double-coated breeds.</li>
<li><strong>Address mats and tangles properly</strong> — Spray a detangling solution (£4–7) on the mat. Hold the hair above the mat to reduce pulling on skin. Use a dematting comb or mat splitter to work through gently, starting at the outer edge. Never try to brush through a tight mat with a slicker brush — this is painful. Severe matting may need professional grooming (bath and demat: £30–60).</li>
<li><strong>Handle moulting season effectively</strong> — UK dogs moult most heavily in spring (April–May) and autumn (September–October). Double-coated breeds may shed their entire undercoat over 2–3 weeks. Daily brushing with an undercoat rake followed by a slicker brush is essential. A deshedding tool (£10–20) removes loose undercoat efficiently. Regular brushing reduces household hair by up to 90%.</li>
<li><strong>Make brushing a positive experience</strong> — Start puppies early: gentle brushing from 8 weeks, even if the coat doesn't need it. Keep sessions short initially (2–3 minutes) and build up. Pair with treats and calm praise. Stop if your dog shows stress (lip licking, yawning, turning away). A positive association now prevents grooming anxiety for life.</li>
<li><strong>Budget for a complete brush kit</strong> — Basic kit (one coat type): £10–20. Comprehensive kit (multiple tools): £25–45. Replacement brushes annually: £10–15. Detangling spray: £4–7. Deshedding tool: £10–20. Total annual grooming tool budget: £20–40 for maintenance, £30–50 for initial setup.</li>
</ol>
"""

PRACTICAL_GUIDES["dog-shampoo"] = """
<ol class="wp-block-list">
<li><strong>Choose shampoo based on skin condition, not coat appearance</strong> — Normal skin: general dog shampoo with balanced pH 6.5–7.5 (£4–8). Dry or flaky skin: oatmeal or aloe vera shampoo (£5–10). Itchy or allergic skin: hypoallergenic, fragrance-free shampoo (£6–12). Greasy coat: deep-cleaning or clarifying shampoo (£5–9). Puppy: specifically formulated, very gentle (£4–7).</li>
<li><strong>Understand the bathing frequency for your breed</strong> — Most dogs: every 4–8 weeks. Oily-coated breeds (Basset Hound): every 2–4 weeks. Dogs with skin conditions: as directed by your vet (could be weekly with medicated shampoo). Over-bathing strips natural oils and causes dry, irritated skin. Under-bathing allows dirt and bacteria to build up.</li>
<li><strong>Follow the correct bathing procedure</strong> — Step 1: brush thoroughly to remove loose hair and mats (bathing mats tightens them). Step 2: wet coat completely with lukewarm water. Step 3: apply shampoo from neck to tail, avoiding eyes and ears. Step 4: massage into a lather for 3–5 minutes (or per product instructions). Step 5: rinse thoroughly — at least twice as long as lathering.</li>
<li><strong>Use conditioner for appropriate coat types</strong> — Long coats: conditioner prevents tangling and eases brushing (£5–10). Wire coats: skip conditioner (softens the coat texture). Double coats: light conditioner on the outer coat only. Leave-in spray conditioner: convenient for between baths (£4–8). Apply conditioner from mid-shaft to tips, avoid roots and skin.</li>
<li><strong>Handle medicated shampoos correctly</strong> — Antibacterial (chlorhexidine): for skin infections, requires 10-minute contact time. Antifungal (miconazole or ketoconazole): for yeast infections, 10-minute contact. Anti-itch (hydrocortisone or pramoxine): for allergic skin, follow vet's instructions. Medicated shampoos cost £8–15 and require a vet prescription or recommendation. Never self-diagnose skin conditions.</li>
<li><strong>Read and understand ingredient labels</strong> — Avoid: parabens, artificial fragrances, sulphates (SLS/SLES), and artificial colours. Good ingredients: oatmeal (soothes itching), aloe vera (moisturises), tea tree oil in low concentrations (antibacterial), coconut oil (conditions). "Natural" on the label is not regulated — always check the actual ingredients list.</li>
<li><strong>Dry your dog properly after bathing</strong> — Towel dry first: use a highly absorbent microfibre towel (£5–10). Blow dryer: use on the lowest heat setting, keep 30cm from skin, move constantly to prevent burns. Air drying: suitable in warm weather but dogs with dense undercoats can develop skin infections if they stay damp. Drying time: 15–45 minutes depending on coat type and method.</li>
<li><strong>Budget for bathing supplies</strong> — Dog shampoo: £4–12 per bottle (lasts 3–6 months depending on dog size). Conditioner: £5–10 per bottle. Microfibre towels (×2): £8–15. Non-slip bath mat: £5–10. Shower attachment with hose: £8–15 (makes rinsing much easier). Total annual bathing budget: £25–50 for home bathing. Compare: professional bath at a groomer: £15–30 per visit.</li>
</ol>
"""

PRACTICAL_GUIDES["dog-nail-clippers"] = """
<ol class="wp-block-list">
<li><strong>Choose the right tool for your dog</strong> — Guillotine clippers: best for small to medium dogs with thinner nails (£5–8). Scissor/plier clippers: best for medium to large dogs with thick nails (£6–12). Electric nail grinder: best for dogs afraid of clipping, files nails gradually (£10–20). Have styptic powder on hand (£4–6) in case you cut the quick.</li>
<li><strong>Learn to identify the quick</strong> — The quick is the blood vessel inside the nail. Light nails: visible as a pink area through the nail. Dark nails: not visible — trim 1–2mm at a time and look for a grey or chalky circle in the cut surface (the quick is just beyond this). Cutting the quick is painful and bleeds — apply styptic powder and firm pressure for 30 seconds if this happens.</li>
<li><strong>Follow the correct trimming technique</strong> — Hold the paw firmly but gently. Cut at a 45-degree angle, following the natural curve of the nail. Trim just 1–2mm at a time for dark nails. For light nails, stop 2mm before the visible pink quick. Trim dewclaws (if present) — these don't wear down naturally and can grow into the pad if neglected.</li>
<li><strong>Establish a regular trimming schedule</strong> — Every 2–4 weeks for most dogs. More frequent for indoor dogs (nails don't wear down on soft surfaces). Less frequent for dogs that walk regularly on pavements and concrete. Test: if you can hear clicking on hard floors, the nails need trimming. Overgrown nails cause discomfort, altered gait, and can lead to joint problems.</li>
<li><strong>Desensitise your dog to nail trimming gradually</strong> — Week 1: handle paws daily, touch nails, reward with treats. Week 2: hold the clipper near paws, click it (without cutting), reward. Week 3: clip one nail per session, reward generously. Week 4: clip 2–3 nails per session. Within 6 weeks, most dogs accept a full trim. Never rush or force — one bad experience can create lifelong fear.</li>
<li><strong>Use a nail grinder as an alternative</strong> — Electric grinders (£10–20) file the nail gradually — less risk of cutting the quick. Use low speed, touch the nail for 3–5 seconds at a time. Avoid long hair catching in the rotating head — hold fur back with your fingers. Grinders are louder than clippers — desensitise to the sound first (run the grinder nearby during treat time for 3–4 days).</li>
<li><strong>Know when to seek professional help</strong> — If your dog's nails are severely overgrown (curling into pads), see a vet (£30–60) — the quick extends with the nail and needs gradual receding. If you're nervous about cutting dark nails, book a vet nurse nail trim (£5–15) and ask them to show you the technique. Professional groomers also offer nail trims: £5–10 as a standalone service.</li>
<li><strong>Budget for nail care</strong> — Guillotine or scissor clippers: £5–12 (replace annually when blades dull). Electric grinder: £10–20 (replacement heads: £5–8 every 6 months). Styptic powder: £4–6 (lasts a year). Professional nail trim if preferred: £5–15 per visit, 6–12 visits per year = £30–180/year. Home trimming total annual cost: £15–30.</li>
</ol>
"""

PRACTICAL_GUIDES["dog-grooming-supplies"] = """
<ol class="wp-block-list">
<li><strong>Build a complete home grooming kit</strong> — Slicker brush: £5–10. Bristle or pin brush: £4–10. Steel comb: £4–8. Nail clippers: £5–12. Dog shampoo: £4–8. Towels (×2 microfibre): £8–15. Ear cleaner: £5–8. Styptic powder: £4–6. Grooming wipes (for between baths): £3–5 per pack. Total: £40–80 for a comprehensive kit.</li>
<li><strong>Prioritise purchases by urgency</strong> — Buy first: brush appropriate for your dog's coat, nail clippers, shampoo. Buy second: ear cleaner, styptic powder, comb. Buy later: deshedding tool, grooming table, blow dryer. You don't need everything on day one — build your kit over the first 2–3 months as you learn what your specific dog needs.</li>
<li><strong>Choose quality tools that last</strong> — Stainless steel combs and scissors last years (£8–15 each). Cheap plastic tools break quickly and may hurt your dog. Professional-grade slicker brushes (£10–15) have self-cleaning mechanisms and flexible pin beds. Quality nail clippers stay sharp for 12–18 months vs 3–6 months for budget options. Cost per use is lower with quality tools.</li>
<li><strong>Set up a grooming station at home</strong> — Use a non-slip mat on a table or work surface (£5–10) for small to medium dogs. For large dogs: groom on the floor with a washable mat underneath. Keep all tools in a dedicated container or bag (£5–10). Good lighting is essential — natural light or a bright lamp. A calm, quiet room reduces grooming anxiety.</li>
<li><strong>Stock up on consumables</strong> — Shampoo: £4–8 per bottle, budget 6–8 bottles per year for a medium dog. Ear cleaner: £5–8 per bottle, lasts 3–4 months. Dental chews: £5–15/month. Grooming wipes: £3–5 per pack, 1 pack per month for between-bath touch-ups. Paw balm for cracked pads: £4–7. Annual consumables budget: £80–150.</li>
<li><strong>Consider a grooming table for regular home grooming</strong> — Foldable grooming table with arm and noose: £30–60. Benefits: correct working height reduces back strain, non-slip surface keeps dog secure, arm and noose prevent jumping off (never leave unattended). Worth the investment if grooming at home every 2–4 weeks. Portable tables fold flat for storage.</li>
<li><strong>Maintain your grooming tools</strong> — Clean hair from brushes after every use. Wash brushes in warm soapy water monthly. Oil clipper blades and scissor pivots every 3–4 uses. Sharpen scissors every 6 months (professional sharpening: £5–10). Replace brush pins when they bend or lose coating. Well-maintained tools work better and last longer.</li>
<li><strong>Calculate annual grooming costs: home vs professional</strong> — Home grooming: £80–150/year in supplies (after initial £40–80 kit). Professional grooming (every 6–8 weeks): £200–520/year for a medium dog, £320–720/year for a large dog. Combination approach: home brushing and washing, professional trim every 8–12 weeks: £120–300/year. Home grooming also strengthens the bond with your dog.</li>
</ol>
"""

PRACTICAL_GUIDES["harness-vs-collar"] = """
<ol class="wp-block-list">
<li><strong>Assess your dog's specific needs</strong> — Pullers: harness distributes force away from the neck (front-clip harness: £15–25). Small breeds under 5kg: harness reduces tracheal injury risk. Brachycephalic breeds (Pugs, Bulldogs): harness always (breathing concerns). Well-trained on-lead dogs: collar is fine (flat collar: £8–15). Most dogs benefit from both: collar for ID tag, harness for lead walks.</li>
<li><strong>Measure for a harness correctly</strong> — Chest girth: measure the widest part of the ribcage (behind the front legs). Neck girth: where the harness will sit (usually lower than a collar). Weight: check the harness weight range matches your dog. Two-finger rule: you should fit two fingers under every strap. Re-measure every month for growing puppies.</li>
<li><strong>Choose the right harness type</strong> — Back-clip harness: easiest to put on, good for calm dogs (£10–20). Front-clip harness: redirects pulling, best for training (£15–25). Dual-clip harness: both attachment points, most versatile (£18–30). Step-in harness: dogs step into it, good for head-shy dogs (£12–20). Head halter: maximum pull control but requires proper fitting (£10–18).</li>
<li><strong>Understand the collar basics</strong> — Flat collar: standard everyday collar, holds ID tag (£8–15). Martingale collar: tightens slightly to prevent escape, good for narrow-headed breeds like Greyhounds (£10–18). Breakaway collar: snaps open under pressure, safest for unsupervised wear (£8–12). Never use choke chains, prong collars, or shock collars — these cause pain and fear.</li>
<li><strong>Introduce a harness gradually</strong> — Day 1: let your dog sniff the harness, treat. Day 2: drape over body, treat, remove. Day 3: fasten loosely for 5 minutes indoors. Day 4: tighten to correct fit, 10–15 minutes indoors with play. Day 5: attach lead indoors. Day 6+: short outdoor walks. Most dogs accept a harness fully within a week. Forcing causes lasting resistance.</li>
<li><strong>Check fit regularly</strong> — Harnesses can shift and rub, causing chafing. Check after every walk for red marks under the "arms" (front legs). Adjust straps as needed. Growing puppies may outgrow a harness in 4–8 weeks. Seasonal coat changes (moult or winter growth) may require strap adjustment. Replace worn harnesses with frayed straps or broken buckles.</li>
<li><strong>Consider breed-specific recommendations</strong> — Dachshunds: harness essential (back and neck protection). Greyhounds: martingale collar (prevents slipping over narrow head) plus harness for walks. French Bulldogs: wide, padded harness (breathing and skin sensitivity). Border Collies: back-clip harness suits their active movement. Giant breeds: heavy-duty harness with handle (£20–35).</li>
<li><strong>Budget for collar and harness needs</strong> — Puppy collar: £5–10 (will outgrow). Adult collar with ID: £8–15. Harness: £10–30 depending on type and quality. Replacement over first year (puppy growth): 2–3 collars + 1–2 harnesses = £30–70. Lead: £5–15. Total first-year walking equipment: £50–100. Quality harnesses from established brands last 2–3 years for adult dogs.</li>
</ol>
"""

PRACTICAL_GUIDES["dog-harness-measuring"] = """
<ol class="wp-block-list">
<li><strong>Gather your measuring tools</strong> — Soft fabric tape measure: £1–3. If you don't have one, use a piece of string and measure against a ruler. Measure when your dog is standing naturally (not sitting or lying down). Have treats ready to keep your dog still. Ask a helper to hold the dog steady if needed.</li>
<li><strong>Measure the chest girth (most important measurement)</strong> — Wrap the tape measure around the widest part of the ribcage, just behind the front legs. The tape should be snug but not tight — you should be able to slide one finger underneath. Note the measurement in centimetres. This is the primary sizing measurement for most harnesses.</li>
<li><strong>Measure the neck girth</strong> — Measure where the harness neck strap will sit — this is lower on the neck than where a collar sits (approximately where the neck meets the chest). Again, snug with one finger clearance. For overhead harnesses, also note your dog's head circumference (widest point over the ears).</li>
<li><strong>Record your dog's weight</strong> — Weigh using bathroom scales: step on with your dog, then without, subtract. Most harness brands provide weight ranges alongside measurements. If your dog falls between two sizes, choose the larger size. Weight helps determine which size chart range to focus on. Weigh monthly for puppies, quarterly for adults.</li>
<li><strong>Use the manufacturer's size chart specifically</strong> — Sizing varies significantly between brands — a "Medium" in one brand may be "Large" in another. Always use the specific manufacturer's chart for the harness you're buying. If between sizes, contact the retailer for advice. Many online retailers offer free exchanges for sizing issues. Keep the receipt and tags until you've confirmed fit.</li>
<li><strong>Check the fit when the harness arrives</strong> — Two-finger test: you should fit two flat fingers under every strap. No rubbing: check under the front legs (most common chafing point). Full range of movement: your dog should walk, sit, and lie down without restriction. The harness should not rotate or shift during movement. If it rides up or slips sideways, it's the wrong size or style.</li>
<li><strong>Re-measure at key intervals</strong> — Puppies: every 2 weeks during rapid growth (8–16 weeks), then monthly until 12 months. Adult dogs: every 3–6 months (weight fluctuations and seasonal coat changes affect fit). After illness or diet changes: re-measure. After switching food brands: weight may shift. A poorly fitting harness is worse than no harness — it can cause injury.</li>
<li><strong>Common measurement mistakes to avoid</strong> — Measuring too tightly (causes a too-small purchase). Measuring while the dog is sitting (gives a larger chest measurement than standing). Using a rigid ruler instead of a soft tape. Assuming your dog is the same size as a friend's dog of the same breed. Ignoring coat length — long-haired dogs measure larger but need the same support.</li>
</ol>
"""

PRACTICAL_GUIDES["dog-harness-complete-guide"] = """
<ol class="wp-block-list">
<li><strong>Understand harness types and their purposes</strong> — Back-clip: lead attaches on the back, easiest to use, good for small dogs and non-pullers (£10–20). Front-clip: lead attaches on the chest, redirects pulling, best training aid (£15–25). Dual-clip: both options, most versatile (£18–30). No-pull: tightens slightly when the dog pulls, discouraging the behaviour (£15–25).</li>
<li><strong>Select the right material</strong> — Nylon webbing: most common, lightweight, affordable (£10–20), dries quickly. Padded mesh: comfortable, breathable, good for sensitive skin (£15–25). Leather: durable, stylish, requires maintenance (£25–50). Neoprene-lined: waterproof, comfortable, good for active dogs (£20–35). For UK weather: choose quick-drying materials that handle rain.</li>
<li><strong>Fit the harness in 5 steps</strong> — Step 1: loosen all straps fully. Step 2: place the harness over your dog's head or guide legs through (depending on style). Step 3: fasten the chest and/or belly buckle. Step 4: adjust straps until snug with a two-finger gap everywhere. Step 5: attach the lead and walk a few steps — watch for any rubbing, shifting, or restriction.</li>
<li><strong>Use a harness for training effectively</strong> — Front-clip for pulling: when your dog pulls, the clip position turns them back towards you. Start with 5-minute training walks. Reward walking with a loose lead. Combine with the "stop-start" method: stop when the lead tightens, move when it's loose. Progress to longer walks over 2–3 weeks. A harness is a management tool, not a cure — pair with training.</li>
<li><strong>Maintain your harness properly</strong> — Hand wash monthly in lukewarm water with mild detergent. Air dry completely before re-use (never tumble dry — damages buckles and weakens webbing). Check all buckles and clips weekly for cracks or stiffness. Inspect stitching for fraying. Replace when: buckles crack, webbing frays, padding compresses permanently. Quality harnesses last 2–3 years.</li>
<li><strong>Address common harness problems</strong> — Rubbing under front legs: try a wider chest strap or padded harness (£15–25). Harness rotates sideways: adjust the back strap tighter. Dog escapes by backing out: add a belly strap or switch to an escape-proof design (£20–30). Dog refuses to wear: desensitise gradually over 5–7 days with treats (see introduction steps above).</li>
<li><strong>Match harness to activity</strong> — Daily walks: standard front or back-clip harness. Car travel: crash-tested car harness with seatbelt loop (£15–30, look for ECE R17 or equivalent certification). Hiking: heavy-duty harness with handle and reflective strips (£25–40). Swimming: quick-release harness with a grab handle (£20–35). Night walks: reflective or LED harness (£15–30).</li>
<li><strong>Budget for harness ownership</strong> — Puppy harnesses (will outgrow 2–3 times): £20–60 total in first year. Adult first harness: £15–30. Replacement every 2–3 years: £15–30. Car harness (if driving): £15–30. Specialist activity harness: £20–40. Total first-year harness cost: £30–90 depending on needs. Buy adjustable designs to maximise usable lifespan.</li>
</ol>
"""

# Map slugs to their guide content; with fallback to cluster-generic
SLUG_TO_GUIDE_KEY = {
    # Dog Beds
    "best-dog-beds-uk": "dog-beds-generic",
    "best-cooling-dog-beds-uk": "cooling-dog-beds",
    "best-orthopaedic-dog-beds-uk": "orthopaedic-dog-beds",
    "best-puppy-beds-uk": "puppy-beds",
    "dog-bed-types-glossary": "dog-bed-materials",
    "dog-bed-materials-explained": "dog-bed-materials",
    "how-to-wash-dog-bed": "dog-bed-washing",
    "how-to-wash-and-dry-a-dog-bed-safely": "dog-bed-washing",
    "where-to-place-dog-bed": "dog-bed-placement",
    "dog-bed-placement-guide-where-to-put-your-dogs-bed": "dog-bed-placement",
    "how-to-choose-the-right-dog-bed-size": "dog-beds-generic",
    "dog-bed-terminology-materials-types-and-sizing-terms-explained": "dog-bed-materials",
    "dog-bed-safety-avoiding-hazards-and-choosing-non-toxic-materials": "dog-bed-safety",
    "seasonal-dog-bedding-adjusting-comfort-through-the-year": "seasonal-dog-bedding",
    "puppy-bed-training-helping-your-dog-love-their-bed": "puppy-bed-training",
    # Puppy Care
    "puppy-care-essentials-glossary": "puppy-care-glossary",
    "puppy-care-glossary-essential-terms-for-new-puppy-owners": "puppy-care-glossary",
    "first-time-dog-owner-essentials": "first-time-dog-owner",
    "puppy-socialisation-timeline-guide": "puppy-socialisation",
    "best-puppy-training-guide-uk": "puppy-training-guide",
    "best-puppy-collars-uk": "puppy-collars",
    "best-puppy-food-uk": "puppy-food",
    "best-puppy-toys-uk": "puppy-toys",
    "puppy-vaccination-schedule-uk": "puppy-vaccination",
    "puppy-teething-guide-stages-signs-and-soothing-tips": "puppy-teething",
    "first-week-new-puppy-guide": "puppy-first-week",
    "puppy-sleep-guide-by-age": "puppy-sleep",
    "puppy-proofing-home-safety-guide": "puppy-proofing",
    # Dog Health
    "best-dog-health-and-care-uk": "dog-health-care-complete",
    "best-dog-dental-care-uk": "dog-dental-care-products",
    "best-dog-flea-treatment-uk": "dog-flea-treatment",
    "best-dog-joint-supplements-uk": "dog-joint-supplements",
    "dog-dental-health-care-guide": "dog-dental-health",
    "dog-health-terminology-understanding-common-veterinary-and-care-terms": "dog-health-generic",
    "seasonal-dog-care-guide": "seasonal-dog-care",
    # Dog Grooming
    "dog-grooming-basics-guide": "dog-grooming-generic",
    "best-dog-grooming-supplies-uk": "dog-grooming-supplies",
    "best-dog-brushes-uk": "dog-brushes",
    "best-dog-shampoo-uk": "dog-shampoo",
    "best-dog-nail-clippers-uk": "dog-nail-clippers",
    "harness-vs-collar-which-is-better": "harness-vs-collar",
    "how-to-measure-dog-for-harness": "dog-harness-measuring",
    "dog-harnesses-complete-guide": "dog-harness-complete-guide",
}

# ============================================================
# PHASE 10BL — DECISION PATHWAY CONTENT
# ============================================================

DECISION_PATHWAYS = {}

DECISION_PATHWAYS["dog-beds"] = """
<ul class="wp-block-list">
<li><strong>If your dog weighs under 10kg</strong> → Small donut bed or flat mat (50–60cm diameter), budget £15–30. Most small breeds prefer enclosed, bolstered beds for warmth and security. Look for beds with 5–8cm foam thickness.</li>
<li><strong>If your dog weighs 10–25kg</strong> → Medium rectangular or bolster bed (70–85cm), budget £30–55. Consider your dog's sleeping style: side sleepers need rectangular, curlers suit round or oval beds. Minimum 8cm foam for adequate support.</li>
<li><strong>If your dog weighs over 25kg</strong> → Large or extra-large orthopaedic bed (90–120cm), budget £50–100. Prioritise high-density foam (50+ kg/m³) for lasting support. Waterproof liners are recommended for larger breeds. Check weight capacity ratings.</li>
<li><strong>If your dog has arthritis or joint issues</strong> → Memory foam orthopaedic bed with minimum 10cm thickness, budget £50–120. Place at floor level with no step up. Non-slip base essential. Consider a heated pad underneath in winter (£15–30). Consult your vet about complementary joint supplements.</li>
<li><strong>If your dog overheats easily or you need a summer bed</strong> → Cooling gel mat (£15–25) or elevated mesh bed (£20–45). Brachycephalic breeds, heavy-coated breeds, and dogs over 25kg benefit most. Place on a cool hard floor away from direct sunlight. Combine both for maximum cooling in heatwaves.</li>
<li><strong>If you're buying for a growing puppy</strong> → Size the bed for 75% of expected adult dimensions, fill extra space with towels. Use a chew-resistant, waterproof-backed mat for the first 6–8 months (£10–20), then invest in a quality adult bed. Total first-year bedding: £75–155.</li>
</ul>
"""

DECISION_PATHWAYS["cooling-dog-beds"] = """
<ul class="wp-block-list">
<li><strong>If your dog pants excessively indoors in summer</strong> → Pressure-activated gel pad is the simplest starting point (£15–25). No setup required, place on existing bed or floor. Recharges when your dog moves off. Replace gel insert annually.</li>
<li><strong>If your dog seeks tile or stone floors in warm weather</strong> → Elevated mesh bed allows airflow on all sides (£20–45). Place on hard flooring away from direct sunlight. Combine with a thin gel pad on top for dual cooling. Particularly effective for dogs over 20kg.</li>
<li><strong>If your dog is a brachycephalic breed (Bulldog, Pug, Boxer)</strong> → Floor-level gel pad only — avoid elevated beds (risk of falling for flat-faced breeds). Choose a pad at least 10cm larger than your dog in every direction. Budget £15–30. Monitor closely in temperatures above 22°C.</li>
<li><strong>If your dog has a thick double coat (Husky, Malamute, Collie)</strong> → Combined approach: elevated bed with mesh top, placed in an air-conditioned or naturally cool room. May need cooling from May through September. Budget £35–60 for the combination. Never clip a double coat for cooling — it removes insulation.</li>
<li><strong>If you want one bed that works year-round</strong> → Memory foam base (year-round support) with interchangeable seasonal covers: breathable mesh for summer (£10–15), thermal fleece for winter (£12–20). Total: £50–90. Add a removable gel topper for the hottest weeks only.</li>
</ul>
"""

DECISION_PATHWAYS["orthopaedic-dog-beds"] = """
<ul class="wp-block-list">
<li><strong>If your dog shows stiffness only after intense exercise</strong> → Standard memory foam bed (40–50 kg/m³ density, 8cm thick), budget £35–55. This may be sufficient for mild discomfort. Monitor for progression and consult your vet at the annual check-up.</li>
<li><strong>If your dog has diagnosed arthritis or hip dysplasia</strong> → High-density orthopaedic foam (50–80 kg/m³, minimum 10cm thick), budget £50–100. Floor-level placement with non-slip base is essential. Consider adding a heated pad for winter mornings (£15–30). Pair with vet-recommended joint supplements.</li>
<li><strong>If your dog is recovering from orthopaedic surgery</strong> → Veterinary-grade orthopaedic bed with waterproof liner, budget £70–120. Flat design with no raised edges (easy entry and exit). Place on a non-slip surface. Replace every 12–18 months to maintain support. Follow your vet's specific post-surgery bedding advice.</li>
<li><strong>If your large breed puppy needs joint protection during growth</strong> → Supportive foam bed (not the softest memory foam — developing joints need firm support), budget £30–50. Large breed puppies (Labs, German Shepherds, Goldens) benefit from orthopaedic support from 4 months. Size for adult dimensions.</li>
<li><strong>If your senior dog (7+ years) needs general comfort</strong> → Medium-density memory foam with a soft fleece top layer, budget £45–80. Bolster edges for head and neck support. Low-entry design (maximum 5cm edge height). Add a waterproof liner for incontinence protection (£8–15). Consider a bed near a wall for standing support.</li>
</ul>
"""

DECISION_PATHWAYS["puppy-care"] = """
<ul class="wp-block-list">
<li><strong>If your puppy is 8–12 weeks old (just arrived home)</strong> → Focus on: settling in routine, first vet visit (£30–60), beginning toilet training, and creating a safe puppy zone. Avoid overwhelming with too many new experiences. Immediate purchases: food, bed, crate, collar with ID tag. Budget: £150–300 for initial setup.</li>
<li><strong>If your puppy is 12–16 weeks (socialisation window)</strong> → Priority: controlled socialisation experiences before the window closes at 14–16 weeks. Enrol in puppy classes (£40–80). Complete vaccination course. Begin lead training indoors. Start gentle grooming handling. This is the most important developmental period.</li>
<li><strong>If your puppy is 4–6 months (teething and testing boundaries)</strong> → Focus on: providing appropriate chew toys (£15–30), reinforcing house training, building recall outdoors, managing biting and mouthing. Consider neutering discussion with your vet. Expect some regression in training — this is normal. Increase mental stimulation.</li>
<li><strong>If your puppy is 6–12 months (adolescent phase)</strong> → Priority: consistent training reinforcement, increasing exercise gradually (5 minutes per month of age), proofing commands in different environments. This phase tests boundaries — patience and consistency are key. Consider an advanced training class (£50–100). Transition to adult food around 12 months.</li>
<li><strong>If you're getting a puppy from a rescue (unknown history)</strong> → Allow extra time for settling: 2–4 weeks before expecting normal behaviour. Be patient with toilet training — rescue puppies may need 6–8 weeks. Register with a behaviourist early if issues arise (£50–100/session). Prioritise building trust over training commands initially.</li>
<li><strong>If you're a first-time puppy owner and feeling overwhelmed</strong> → Focus on three things only for the first week: toilet training, feeding routine, and sleep routine. Everything else can wait. Join an online puppy support group (free). Book a vet nurse advice appointment (often free or £10–20). You don't need to be perfect — consistency matters more than intensity.</li>
</ul>
"""

DECISION_PATHWAYS["puppy-vaccination"] = """
<ul class="wp-block-list">
<li><strong>If your puppy has had their first jab from the breeder</strong> → Book the second vaccination for 10–12 weeks of age (£30–50). Check which vaccine brand was used — some vets prefer to match brands for the course. Bring the vaccination card from the breeder. Full immunity develops 1–2 weeks after the second jab.</li>
<li><strong>If you're adopting a puppy with unknown vaccination history</strong> → Your vet will likely recommend starting the full primary course from scratch (£60–100). This is the safest approach. Keep your puppy away from unvaccinated dogs and public ground until the course is complete. Some rescues include the first vaccination in the adoption fee.</li>
<li><strong>If you're concerned about vaccination side effects</strong> → Serious reactions are very rare (less than 1 in 10,000). Mild lethargy and reduced appetite for 24 hours is normal. The risk of parvovirus, distemper, or leptospirosis far outweighs vaccination risks. Discuss specific concerns with your vet before the appointment.</li>
<li><strong>If you need kennel cough vaccination for boarding</strong> → Book the nasal spray vaccine at least 2 weeks before boarding (£20–40). It's separate from the core vaccination course. Most boarding kennels require it annually. Can be given from 3 weeks of age. Protection lasts approximately 12 months.</li>
<li><strong>If you've missed the annual booster</strong> → Contact your vet immediately. If less than 15 months since the last booster, a single jab usually restores immunity. If longer, a full primary course may be needed (£60–100). Leptospirosis immunity wanes fastest — this is the most important booster to keep current in the UK.</li>
</ul>
"""

DECISION_PATHWAYS["puppy-teething"] = """
<ul class="wp-block-list">
<li><strong>If your puppy is chewing everything destructively</strong> → Increase the number and variety of approved chew toys (aim for 5–6 in rotation). Freeze Kongs and wet flannels for soothing relief. Apply bitter apple spray (£4–7) to furniture and cables. Supervise closely and redirect within 2 seconds of inappropriate chewing.</li>
<li><strong>If your puppy refuses to eat during teething</strong> → Soften kibble with warm water for 10 minutes. Offer frozen banana or carrot slices. Try wet food temporarily (£1–2/day). If appetite loss continues more than 48 hours, consult your vet (£30–60) to rule out retained baby teeth or infection.</li>
<li><strong>If your puppy's gums are very swollen or bleeding heavily</strong> → Mild swelling and pink-tinged saliva are normal during teething. However, if gums are very red, significantly swollen, or bleeding continuously, see your vet within 48 hours (£30–60). This may indicate infection or a retained baby tooth.</li>
<li><strong>If baby teeth haven't fallen out by 7 months</strong> → Retained baby teeth can cause alignment problems with adult teeth. Your vet may recommend extraction under sedation (£50–150). The most commonly retained teeth are the upper canines. Don't try to wiggle or pull baby teeth at home — this risks root fracture.</li>
<li><strong>If your puppy is biting hands and ankles during teething</strong> → This is normal teething behaviour combined with puppy play. Yelp once, turn away for 10 seconds. Offer a cold chew toy as an alternative. If biting breaks skin, end the play session entirely for 5 minutes. Consistent responses reduce biting within 2–3 weeks.</li>
</ul>
"""

DECISION_PATHWAYS["puppy-first-week"] = """
<ul class="wp-block-list">
<li><strong>If your puppy won't stop crying at night</strong> → Place the bed directly next to yours for the first 3–5 nights. Use a warm water bottle wrapped in a towel. A ticking clock mimics a heartbeat. Wait 5 minutes before responding to whimpering (unless a toilet break is likely). Most puppies settle within 3–5 nights with patience.</li>
<li><strong>If your puppy has diarrhoea in the first few days</strong> → Stress-related diarrhoea is common during the first 48 hours of a new home. If mild: ensure fresh water is available, stick to the breeder's food, feed smaller meals. If it continues beyond 48 hours, contains blood, or your puppy seems lethargic: contact your vet immediately (£30–60).</li>
<li><strong>If your puppy won't eat</strong> → Appetite loss is normal on the first day due to stress. Offer the same food the breeder used. Try warming the food slightly to release aromas. Offer smaller portions more frequently. If your puppy doesn't eat anything for 24 hours or misses 3 meals, call your vet for advice (£30–60).</li>
<li><strong>If your puppy is hiding and won't come out</strong> → This is a normal fear response in a new environment. Don't force interaction — let your puppy come to you in their own time. Sit on the floor near their hiding spot, speak softly, and toss treats gently towards them. Most puppies gain confidence within 24–48 hours. Keep the household calm and quiet.</li>
<li><strong>If you have other pets and introductions are tense</strong> → Keep them separated for the first 2–3 days (stair gate between rooms). Allow scent exchange: swap bedding between pets. First visual introduction through a gate. First supervised meeting after 3–4 days, both on leads, keep it brief (2–3 minutes). Always give existing pets more attention, not less.</li>
</ul>
"""

DECISION_PATHWAYS["puppy-sleep"] = """
<ul class="wp-block-list">
<li><strong>If your puppy won't settle for naps during the day</strong> → Your puppy is likely overtired (paradoxically, overtired puppies become hyperactive). Enforce a nap: place in a covered crate or quiet room after 1 hour of activity. Most puppies protest for 5–10 minutes, then sleep. If they don't settle after 15 minutes, take them for a toilet break and try again.</li>
<li><strong>If your puppy wakes multiple times at night</strong> → Under 12 weeks: 1–2 wakeups for toilet is normal. Set a proactive alarm to pre-empt crying. 12–16 weeks: should reduce to 0–1 wakeup. Over 16 weeks: should sleep through (7–8 hours). If frequent waking persists, check: room temperature (16–20°C ideal), last meal timing (not too close to bedtime), and exercise levels.</li>
<li><strong>If your puppy sleeps too much or too little</strong> → Puppies sleep 18–20 hours daily until 12 weeks. If significantly more or less: monitor for 48 hours. Excessive sleep with lethargy during waking hours: possible illness, see your vet (£30–60). Very little sleep with hyperactivity: likely overtiredness — enforce structured nap times.</li>
<li><strong>If your puppy refuses to sleep in their bed or crate</strong> → Check the bed is comfortable and in a suitable location (quiet, draught-free, 16–20°C). Add your scent (worn t-shirt). Never force entry. Lure with treats and praise. Feed meals in the crate. If your puppy consistently chooses another spot, consider moving the bed there temporarily.</li>
<li><strong>If you're unsure about crate vs open bed for sleeping</strong> → Crates suit: puppies in toilet training (natural den instinct prevents soiling), anxious puppies (enclosed space feels safe), households with hazards. Open beds suit: confident puppies past the toilet training phase, homes with no unsupervised risks. Many dogs transition from crate to open bed at 6–12 months.</li>
</ul>
"""

DECISION_PATHWAYS["puppy-proofing"] = """
<ul class="wp-block-list">
<li><strong>If you live in a flat or small home</strong> → Focus on: cable management in every room (cable protectors: £5–10), storing all shoes and small objects at height, securing cleaning products. Use a playpen (£25–45) as a safe zone when you can't supervise. Even small spaces need thorough proofing — puppies find hazards in every corner.</li>
<li><strong>If you have children</strong> → Secure small toys, Lego, and craft supplies in closed containers. Teach children to keep bedroom doors closed. Supervise all puppy-child interactions (never leave under-10s alone with a puppy). Baby gates separate puppy and child spaces. Store children's snacks out of puppy reach — chocolate, raisins, and grapes are toxic to dogs.</li>
<li><strong>If you have a garden</strong> → Walk the entire perimeter checking for gaps (puppies squeeze through 10cm gaps). Secure pond and pool access. Fence off compost heaps (mouldy food is toxic). Check for and remove toxic plants: foxglove, lily, yew, daffodil bulbs. Lock garden sheds containing chemicals. Budget: £30–80 for garden puppy-proofing.</li>
<li><strong>If you rent and cannot make permanent changes</strong> → Use pressure-fit stair gates (no drilling: £15–30). Use furniture to block access to problem areas. Cable protectors stick with removable adhesive. Bitter apple spray (£4–7) deters chewing without causing damage. Cover furniture with washable throws (£10–20). All temporary solutions, all effective.</li>
<li><strong>If your puppy is an extreme chewer</strong> → Double down on cable protection (metal conduit if needed: £10–15). Apply bitter apple spray to all furniture legs and edges. Provide 5–6 chew toy alternatives in rotation. Consider a larger crate or pen for unsupervised periods. Most extreme chewing eases after 7–8 months when teething ends.</li>
</ul>
"""

# Generic decision pathways for posts without specific ones
DECISION_PATHWAYS["dog-health"] = """
<ul class="wp-block-list">
<li><strong>If your dog is under 3 years old with no known health conditions</strong> → Annual vet check-up (£30–60), monthly flea and tick prevention (£8–15/month), quarterly worming (£3–8), and core annual vaccination booster (£30–60) form your baseline. Pet insurance (£15–30/month for younger dogs) provides emergency cover. Total annual cost: £300–500.</li>
<li><strong>If your dog is 3–7 years old (adult maintenance)</strong> → Maintain all preventative treatments. Add annual dental check (£20–40). Monitor weight monthly — obesity is the most common health problem. Discuss breed-specific screening with your vet. Budget for one unexpected vet visit per year (£100–300). Total annual: £400–700.</li>
<li><strong>If your dog is over 7 years old (senior care)</strong> → Increase to twice-yearly vet checks (£60–120/year). Annual blood panel to check organ function (£50–100). Joint supplement consideration (£10–20/month). Dental care becomes more critical. Adjust exercise (shorter, more frequent walks). Total annual: £600–1,200. Insurance premiums increase but cover becomes more valuable.</li>
<li><strong>If your dog has a chronic health condition</strong> → Work with your vet to create a management plan. Monthly medication costs vary widely (£15–100/month depending on condition). Specialist referrals if needed (£150–350 initial consultation). Ensure your insurance covers ongoing conditions (lifetime policies: £25–45/month). Keep detailed health records for consistency across vet visits.</li>
<li><strong>If you're choosing between insurance options</strong> → Lifetime policy (£20–40/month): covers conditions for life, best overall value. Per-condition policy (£10–25/month): covers each condition for 12 months only, cheaper but less comprehensive. Accident-only (£5–15/month): emergencies only. Always check excess amounts (£50–250) and annual claim limits. Read exclusions carefully.</li>
</ul>
"""

DECISION_PATHWAYS["dog-dental-health"] = """
<ul class="wp-block-list">
<li><strong>If your dog will not accept tooth brushing</strong> → Start with dental water additive (£5–10/month) as a passive first step. Add VOHC-approved dental chews daily (£5–15/month). Dental spray (£6–10) can be applied without a brush. Work on desensitisation gradually: start with finger on gums with flavoured toothpaste. Most dogs accept brushing within 3–4 weeks of gradual introduction.</li>
<li><strong>If your dog already has visible tartar build-up</strong> → Brushing alone won't remove hardened tartar. Book a professional dental cleaning under anaesthetic (£150–300). After cleaning, begin a daily brushing routine to prevent recurrence. Add dental chews and water additives as secondary prevention. Re-check in 6 months to assess if the routine is effective.</li>
<li><strong>If your dog has persistent bad breath</strong> → Mild breath is normal for dogs. Sudden or severe bad breath can indicate dental disease, kidney problems, or diabetes. Book a vet check within a week (£30–60). Dental disease is the most common cause — expect a recommendation for professional cleaning. Don't mask the smell with products — address the cause.</li>
<li><strong>If you have a small breed prone to dental disease</strong> → Daily brushing is essential (not optional) for breeds like Yorkshire Terriers, Chihuahuas, and Poodles. Professional cleaning may be needed annually (£150–300). Start dental care from puppy age. Small breed dental food (£15–30/month) can supplement brushing. Budget £200–400/year for comprehensive small breed dental care.</li>
<li><strong>If your dog is senior and has never had dental care</strong> → Book a vet dental assessment (£30–60) before starting any home care. Your vet may recommend professional cleaning first. Pre-anaesthetic blood tests are important for senior dogs (£50–80). After cleaning, establish a gentle daily routine. It's never too late to start — even partial care improves comfort.</li>
</ul>
"""

DECISION_PATHWAYS["dog-flea-treatment"] = """
<ul class="wp-block-list">
<li><strong>If you're choosing your first flea treatment</strong> → Start with a vet-recommended spot-on treatment (£5–12/month) — these are the most established and widely used. Apply monthly, year-round. Prescription products from your vet are more effective than over-the-counter alternatives. Ask your vet during the initial health check.</li>
<li><strong>If your dog dislikes spot-on application</strong> → Oral flea tablets are an excellent alternative (£8–15/month). Given as a flavoured chew, most dogs take them willingly. Fast-acting (kills fleas within hours). No need to avoid bathing after application (unlike spot-ons). Discuss with your vet which oral option suits your dog.</li>
<li><strong>If you have an active flea infestation</strong> → Treat all pets simultaneously with a fast-acting product. Treat your home: wash all bedding at 60°C, vacuum daily for 2 weeks, use a household flea spray (£8–15 per room). Home treatment takes 2–3 months to eliminate all life stages. Budget for the full course: £50–100 for home treatment plus ongoing pet prevention.</li>
<li><strong>If you want combined flea and tick protection</strong> → Combination products are more cost-effective and convenient. Spot-on combinations: £8–15/month. Oral combinations: £10–18/month. Long-lasting collar (covers fleas and ticks for 6–8 months): £20–35. Discuss with your vet which parasites are most prevalent in your area of the UK.</li>
<li><strong>If your dog has flea allergy dermatitis</strong> → Strict year-round prevention is essential — a single flea bite triggers a reaction. Use the fastest-killing product available (discuss with your vet). Treat all household pets. Wash bedding weekly at 60°C. Your vet may prescribe anti-itch medication alongside prevention (£20–40/month). Total monthly cost with allergy management: £30–60.</li>
</ul>
"""

DECISION_PATHWAYS["dog-joint-supplements"] = """
<ul class="wp-block-list">
<li><strong>If your dog is a large breed under 5 years with no symptoms</strong> → Preventative supplementation is optional at this stage. Focus on: maintaining healthy weight, appropriate exercise, and quality nutrition. Consider starting a basic glucosamine supplement at 4–5 years (£8–15/month). Discuss timing with your vet at the annual check-up.</li>
<li><strong>If your dog shows early signs of stiffness (especially after rest)</strong> → Start a glucosamine and chondroitin combination supplement (£12–25/month). Allow 4–6 weeks to assess improvement. Add omega-3 fish oil (£5–12/month) for anti-inflammatory benefits. Book a vet assessment (£30–60) to establish a baseline and rule out other causes.</li>
<li><strong>If your dog has diagnosed arthritis</strong> → Supplements alone may not be sufficient. Your vet may recommend: prescription anti-inflammatory medication (£15–30/month) alongside supplements. Combine with: orthopaedic bed (£50–120), weight management, and controlled exercise. Physiotherapy (£30–50/session) or hydrotherapy (£25–40/session) may significantly improve quality of life.</li>
<li><strong>If supplements haven't helped after 8 weeks</strong> → Don't increase the dose without vet advice. Your vet may recommend: switching to a different supplement formula, adding prescription medication, or investigating with X-rays (£100–200). Some dogs respond better to green-lipped mussel extract than glucosamine. Specialist orthopaedic referral may be appropriate (£150–300 consultation).</li>
<li><strong>If you're on a tight budget but your dog needs joint support</strong> → Start with omega-3 fish oil (£5–8/month for a basic supplement — most affordable anti-inflammatory). Maintain strict weight control (free but highly effective). Ensure consistent, moderate exercise. Basic glucosamine tablets (£8–12/month). Ask your vet about the most cost-effective prescription options if medication is needed.</li>
</ul>
"""

DECISION_PATHWAYS["dog-grooming"] = """
<ul class="wp-block-list">
<li><strong>If you have a low-maintenance coat type (smooth or short coat)</strong> → Weekly brushing with a bristle brush (£4–8), bathing every 6–8 weeks, nail trim every 3–4 weeks. Professional grooming rarely needed — save budget for vet dental care instead. Total annual grooming cost: £30–60 for supplies only. Most tasks take 15–20 minutes.</li>
<li><strong>If you have a double-coated breed (Labrador, Husky, German Shepherd)</strong> → Brush 3× weekly with an undercoat rake and slicker brush (£15–25 for both). During spring and autumn moult: daily brushing is essential. Bathe every 8–12 weeks. Never clip or shave a double coat — it damages the coat structure. Professional deshedding treatment: £30–50 per visit if needed.</li>
<li><strong>If you have a breed requiring regular haircuts (Poodle, Shih Tzu, Bichon)</strong> → Professional grooming every 6–8 weeks is essential (£35–70 per visit, £280–560/year). Between visits: daily brushing to prevent matting, regular ear checks. Home grooming kit: £40–60. Face and paw trimming at home can extend time between professional visits.</li>
<li><strong>If your dog hates being groomed</strong> → Start desensitisation: handle paws, ears, and coat daily for 30 seconds, paired with high-value treats. Keep sessions very short (2–3 minutes) and positive. Build up gradually over 3–4 weeks. Consider a mobile groomer who comes to your home (less stressful: £40–80 per visit). A professional behaviourist may help with severe grooming anxiety (£50–100/session).</li>
<li><strong>If you want to learn home grooming to save money</strong> → Start with brushing, nail trimming, and bathing — these three skills cover 80% of grooming needs. Watch breed-specific tutorials from qualified groomers. Invest in quality tools (£40–80 total). Practice on calm, clean coat first. Consider one professional grooming session to observe technique before trying at home.</li>
</ul>
"""

DECISION_PATHWAYS["dog-brushes"] = """
<ul class="wp-block-list">
<li><strong>If you have a smooth-coated dog (Boxer, Dachshund, Beagle)</strong> → Bristle brush (£4–8) for weekly sessions, rubber curry brush (£3–6) during moulting. Sessions take 10–15 minutes. Focus on distributing natural skin oils. These coats are the easiest to maintain — one brush is often sufficient.</li>
<li><strong>If you have a double-coated dog (Labrador, Husky, Golden Retriever)</strong> → Undercoat rake (£8–15) as the primary tool, slicker brush (£5–10) for finishing. Deshedding tool (£10–20) for seasonal moults. Brush 3× weekly, increasing to daily during spring and autumn shedding. Total tool investment: £25–45.</li>
<li><strong>If you have a long-coated dog (Maltese, Shih Tzu, Afghan Hound)</strong> → Pin brush (£6–10) for daily brushing, wide-tooth comb (£4–8) for detangling, dematting comb (£6–12) for stubborn mats. Daily 15–20 minute sessions are essential to prevent matting. Detangling spray (£4–7) makes brushing easier and more comfortable.</li>
<li><strong>If you have a wire-coated dog (Terrier, Schnauzer, Wirehaired Dachshund)</strong> → Slicker brush (£5–10) for regular maintenance, stripping knife (£8–12) for removing dead coat every 6–8 weeks. Never clip a wire coat if you want to maintain texture — hand-stripping preserves the correct coat quality. Professional stripping: £30–60 per session.</li>
<li><strong>If you're unsure which brush to buy</strong> → A quality slicker brush (£8–12) is the most versatile single tool — works on nearly all coat types. Add a comb (£4–8) as your second tool. Once you understand your dog's specific needs, invest in specialised tools. Ask your vet or groomer for breed-specific recommendations at your next appointment.</li>
</ul>
"""

DECISION_PATHWAYS["dog-shampoo"] = """
<ul class="wp-block-list">
<li><strong>If your dog has normal, healthy skin</strong> → General dog shampoo with balanced pH (6.5–7.5), budget £4–8 per bottle. Bathe every 4–8 weeks. Avoid human shampoo (wrong pH for dogs). A single quality shampoo is all you need — you don't need multiple products for a healthy coat.</li>
<li><strong>If your dog has dry, flaky, or itchy skin</strong> → Oatmeal-based or aloe vera shampoo (£5–10). Bathe no more frequently than every 4 weeks (over-bathing worsens dry skin). Consider adding a conditioner (£5–10). If itching persists after 2 washes, consult your vet (£30–60) — it may be allergies rather than dry skin.</li>
<li><strong>If your dog has a diagnosed skin condition</strong> → Use the medicated shampoo prescribed by your vet (£8–15). Follow contact time instructions exactly (usually 10 minutes). Frequency as directed (may be weekly during flare-ups). Do not switch products without vet approval. These shampoos treat the condition — general shampoo will not help.</li>
<li><strong>If your dog has a white or light-coloured coat</strong> → Whitening or brightening shampoo (£6–10) removes yellowing and staining. Use every 4–6 weeks. Alternate with a gentle standard shampoo for every other bath. Avoid bleach-based whiteners — they irritate skin. Tear stain remover (£5–8) for facial staining on breeds like Maltese and Bichon.</li>
<li><strong>If your dog swims regularly or gets muddy frequently</strong> → Deep-cleaning or clarifying shampoo (£5–9) once monthly. For between-bath cleanup: waterless/dry dog shampoo spray (£4–8) or grooming wipes (£3–5 per pack). Rinse with plain water after swimming (especially sea or chlorinated water). Always dry the coat thoroughly to prevent skin infections.</li>
</ul>
"""

DECISION_PATHWAYS["dog-nail-clippers"] = """
<ul class="wp-block-list">
<li><strong>If you're trimming nails for the first time</strong> → Start with guillotine-style clippers for small to medium dogs (£5–8) — simplest to use. Practice the desensitisation process over 2 weeks before the first actual trim. Have styptic powder ready (£4–6). Trim just 1mm on the first attempt. Consider watching a vet nurse demonstrate first (£5–15 appointment).</li>
<li><strong>If your dog has thick or large nails</strong> → Scissor/plier-style clippers with a safety guard (£6–12) provide more cutting force. Replace or sharpen annually (dull blades crush rather than cut cleanly). For very thick nails (Great Danes, Rottweilers), professional-grade clippers may be needed (£10–18).</li>
<li><strong>If your dog is terrified of nail clippers</strong> → Try an electric nail grinder instead (£10–20) — the gradual filing is less startling than the clip. Desensitise to the sound first: run the grinder near your dog during treat time for 3–4 days. Touch the grinder to one nail for 3 seconds, treat. Build up slowly. Some dogs tolerate grinders who panic with clippers.</li>
<li><strong>If you accidentally cut the quick regularly</strong> → Switch to a grinder (impossible to hit the quick as dramatically). If using clippers: invest in a model with an adjustable safety stop. Trim smaller amounts more frequently (every 2 weeks, 1mm per session). Good lighting is essential — use a torch behind light-coloured nails to illuminate the quick.</li>
<li><strong>If you'd rather not trim nails at home</strong> → Vet nurse nail trim: £5–15 per visit, every 3–4 weeks (£65–195/year). Groomer nail trim: £5–10 per visit. Walking regularly on pavements and concrete naturally wears nails (but may not be sufficient alone). This is a perfectly valid choice — many experienced dog owners prefer professional nail care.</li>
</ul>
"""

DECISION_PATHWAYS["harness-vs-collar"] = """
<ul class="wp-block-list">
<li><strong>If your dog pulls on the lead</strong> → Front-clip harness (£15–25) redirects pulling force towards you. Combine with the stop-start walking technique. A collar on a pulling dog puts dangerous pressure on the trachea and cervical spine. Transition to a collar once loose-lead walking is reliable. Training should accompany the harness — it manages pulling but doesn't teach the dog.</li>
<li><strong>If your dog walks calmly on a loose lead</strong> → A flat collar (£8–15) is perfectly suitable. Ensure it fits correctly (two-finger gap). The collar holds the ID tag (legal requirement). For calm dogs, a harness isn't necessary but many owners prefer the comfort and control. A collar is lighter and simpler for well-trained dogs.</li>
<li><strong>If you have a small breed under 5kg</strong> → Always use a harness for lead walks (£10–20). Small breeds are vulnerable to tracheal collapse from collar pressure. Use the collar for ID only, never for lead attachment. Choose a lightweight, padded harness. Check fit carefully — small dogs are harder to fit correctly.</li>
<li><strong>If you have a brachycephalic breed (Pug, Bulldog, French Bulldog)</strong> → Harness essential (£15–25) — never walk on a collar. These breeds already have compromised airways. Choose a wide, padded chest strap that doesn't restrict breathing. Avoid harnesses with straps across the throat. A Y-shaped front design is ideal for flat-faced breeds.</li>
<li><strong>If your dog is an escape artist</strong> → Escape-proof harness with an additional belly strap (£20–30). Martingale collar as a backup (tightens slightly but cannot fully close). Double-clip: lead attached to both harness and collar for maximum security. Some dogs need a custom-fitted harness — consult a professional dog walker or trainer for sizing advice.</li>
</ul>
"""

# Fallbacks for remaining slugs
DECISION_PATHWAYS["seasonal-dog-bedding"] = DECISION_PATHWAYS["dog-beds"]
DECISION_PATHWAYS["puppy-bed-training"] = DECISION_PATHWAYS["puppy-care"]
DECISION_PATHWAYS["dog-bed-safety"] = DECISION_PATHWAYS["dog-beds"]
DECISION_PATHWAYS["dog-bed-washing"] = DECISION_PATHWAYS["dog-beds"]
DECISION_PATHWAYS["dog-bed-placement"] = DECISION_PATHWAYS["dog-beds"]
DECISION_PATHWAYS["dog-bed-materials"] = DECISION_PATHWAYS["dog-beds"]
DECISION_PATHWAYS["puppy-care-glossary"] = DECISION_PATHWAYS["puppy-care"]
DECISION_PATHWAYS["first-time-dog-owner"] = DECISION_PATHWAYS["puppy-care"]
DECISION_PATHWAYS["puppy-socialisation"] = DECISION_PATHWAYS["puppy-care"]
DECISION_PATHWAYS["puppy-training-guide"] = DECISION_PATHWAYS["puppy-care"]
DECISION_PATHWAYS["puppy-collars"] = DECISION_PATHWAYS["puppy-care"]
DECISION_PATHWAYS["puppy-food"] = DECISION_PATHWAYS["puppy-care"]
DECISION_PATHWAYS["puppy-toys"] = DECISION_PATHWAYS["puppy-care"]
DECISION_PATHWAYS["dog-health-generic"] = DECISION_PATHWAYS["dog-health"]
DECISION_PATHWAYS["dog-health-care-complete"] = DECISION_PATHWAYS["dog-health"]
DECISION_PATHWAYS["dog-dental-care-products"] = DECISION_PATHWAYS["dog-dental-health"]
DECISION_PATHWAYS["seasonal-dog-care"] = DECISION_PATHWAYS["dog-health"]
DECISION_PATHWAYS["dog-grooming-generic"] = DECISION_PATHWAYS["dog-grooming"]
DECISION_PATHWAYS["dog-grooming-supplies"] = DECISION_PATHWAYS["dog-grooming"]
DECISION_PATHWAYS["dog-harness-measuring"] = DECISION_PATHWAYS["harness-vs-collar"]
DECISION_PATHWAYS["dog-harness-complete-guide"] = DECISION_PATHWAYS["harness-vs-collar"]

# ============================================================
# PHASE 10BN — COMPARISON TABLES
# ============================================================

COMPARISON_TABLES = {}

# DOG BEDS tables
COMPARISON_TABLES["dog-beds-material"] = """<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Material</th><th>Comfort Level</th><th>Durability</th><th>UK Price Range</th><th>Best Suited For</th><th>Maintenance</th></tr></thead><tbody>
<tr><td>Polyester Fibre Fill</td><td>Moderate — soft but flattens over time</td><td>6–12 months before replacement</td><td>£15–35</td><td>Budget beds, puppies during chewing phase</td><td>Machine washable, reshape regularly</td></tr>
<tr><td>Standard Foam</td><td>Good — consistent support</td><td>12–18 months</td><td>£25–50</td><td>Healthy adult dogs, everyday use</td><td>Spot clean, replace when compressed</td></tr>
<tr><td>Memory Foam</td><td>Excellent — moulds to body shape</td><td>18–24 months</td><td>£40–80</td><td>Senior dogs, joint issues, larger breeds</td><td>Hand wash insert, machine wash cover</td></tr>
<tr><td>High-Density Foam (50+ kg/m³)</td><td>Excellent — firm and supportive</td><td>2–3 years</td><td>£60–120</td><td>Heavy breeds over 25kg, diagnosed arthritis</td><td>Rotate monthly, professional clean annually</td></tr>
<tr><td>Gel-Infused Foam</td><td>Very good — cooling and supportive</td><td>2–3 years (gel pad: replace annually)</td><td>£50–100</td><td>Breeds prone to overheating, summer use</td><td>Wipe gel pad, hand wash foam</td></tr>
<tr><td>Elevated Mesh</td><td>Moderate — firm, airflow underneath</td><td>3–4 years for frame</td><td>£20–45</td><td>Hot climates, outdoor use, dogs over 15kg</td><td>Wipe down, machine wash fabric sling</td></tr>
<tr><td>Self-Warming Reflective</td><td>Good — retains body heat</td><td>12–18 months</td><td>£20–40</td><td>Short-coated breeds, cold rooms, winter use</td><td>Machine wash cover, spot clean reflective layer</td></tr>
</tbody></table></figure>"""

COMPARISON_TABLES["dog-beds-size"] = """<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Dog Size Category</th><th>Typical Breeds</th><th>Weight Range</th><th>Recommended Bed Dimensions</th><th>Minimum Foam Depth</th><th>UK Price Range</th></tr></thead><tbody>
<tr><td>Extra Small</td><td>Chihuahua, Toy Poodle, Papillon</td><td>Under 5kg</td><td>40–50cm diameter or 45×35cm</td><td>5cm</td><td>£12–25</td></tr>
<tr><td>Small</td><td>Jack Russell, Shih Tzu, Cavalier</td><td>5–10kg</td><td>50–60cm diameter or 55×45cm</td><td>5–8cm</td><td>£15–35</td></tr>
<tr><td>Medium</td><td>Cocker Spaniel, Beagle, Whippet</td><td>10–20kg</td><td>65–80cm diameter or 75×55cm</td><td>8cm</td><td>£30–55</td></tr>
<tr><td>Large</td><td>Labrador, Golden Retriever, Boxer</td><td>20–35kg</td><td>85–100cm diameter or 95×70cm</td><td>10cm</td><td>£45–80</td></tr>
<tr><td>Extra Large</td><td>German Shepherd, Rottweiler, Doberman</td><td>35–50kg</td><td>100–120cm long × 80cm wide</td><td>12cm</td><td>£60–100</td></tr>
<tr><td>Giant</td><td>Great Dane, Mastiff, Irish Wolfhound</td><td>Over 50kg</td><td>120–150cm long × 90cm+ wide</td><td>15cm</td><td>£80–150</td></tr>
</tbody></table></figure>"""

COMPARISON_TABLES["dog-beds-seasonal"] = """<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Season</th><th>Recommended Bed Type</th><th>Cover Material</th><th>Placement</th><th>UK Price Range</th><th>Key Consideration</th></tr></thead><tbody>
<tr><td>Spring (Mar–May)</td><td>Standard foam or memory foam</td><td>Cotton or polyester blend</td><td>Standard position, good ventilation</td><td>£25–60</td><td>Transition period — moult management</td></tr>
<tr><td>Summer (Jun–Aug)</td><td>Cooling gel mat or elevated mesh bed</td><td>Breathable mesh or cotton</td><td>Tiled floor, away from direct sun</td><td>£15–45</td><td>Cooling priority for all breeds</td></tr>
<tr><td>Autumn (Sep–Nov)</td><td>Standard foam with warm cover</td><td>Fleece or microfibre</td><td>Away from external walls and doors</td><td>£25–50</td><td>Prepare for temperature drop</td></tr>
<tr><td>Winter (Dec–Feb)</td><td>Thermal or self-warming bed</td><td>Thermal fleece or sherpa</td><td>Central room, raised off cold floor</td><td>£25–60</td><td>Draught protection essential</td></tr>
<tr><td>Year-Round Option</td><td>Memory foam base + 2 cover sets</td><td>Summer cotton + winter fleece</td><td>Adjust position seasonally</td><td>£50–90 total</td><td>Most economical long-term solution</td></tr>
</tbody></table></figure>"""

COMPARISON_TABLES["dog-beds-price-tiers"] = """<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Budget Tier</th><th>Typical Materials</th><th>Expected Lifespan</th><th>UK Price Range</th><th>Best Suited For</th><th>Replacement Cost/Year</th></tr></thead><tbody>
<tr><td>Budget</td><td>Polyester fill, basic fabric cover</td><td>6–8 months</td><td>£10–25</td><td>Puppies (chewing phase), temporary beds</td><td>£20–50/year</td></tr>
<tr><td>Mid-Range</td><td>Standard foam, removable washable cover</td><td>12–18 months</td><td>£25–50</td><td>Healthy adult dogs, everyday use</td><td>£25–50/year</td></tr>
<tr><td>Premium</td><td>Memory foam, waterproof liner, quality cover</td><td>18–24 months</td><td>£50–80</td><td>Senior dogs, breeds with joint concerns</td><td>£30–50/year</td></tr>
<tr><td>Veterinary Grade</td><td>High-density certified foam, medical-grade cover</td><td>2–3 years</td><td>£80–150</td><td>Diagnosed arthritis, post-surgery recovery</td><td>£35–75/year</td></tr>
<tr><td>Cooling Specialist</td><td>Gel pad or elevated mesh frame</td><td>1–3 years (varies by type)</td><td>£15–50</td><td>Summer use, overheating breeds</td><td>£15–50/year</td></tr>
<tr><td>Thermal Specialist</td><td>Self-warming reflective + fleece</td><td>12–18 months</td><td>£20–45</td><td>Winter use, thin-coated breeds</td><td>£20–45/year</td></tr>
</tbody></table></figure>"""

# PUPPY CARE tables
COMPARISON_TABLES["puppy-cost-monthly"] = """<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Month</th><th>Key Expenses</th><th>Estimated Cost (Small Breed)</th><th>Estimated Cost (Large Breed)</th><th>Notes</th></tr></thead><tbody>
<tr><td>Month 1 (Setup)</td><td>Bed, crate, bowls, collar, lead, toys, food, first vet visit</td><td>£200–350</td><td>£250–450</td><td>Largest single outlay — plan ahead</td></tr>
<tr><td>Month 2</td><td>Second vaccination, food, puppy pads, insurance starts</td><td>£80–140</td><td>£100–180</td><td>Vaccination: £30–50</td></tr>
<tr><td>Month 3</td><td>Puppy classes, food, flea/worm treatment, replacement toys</td><td>£70–120</td><td>£90–150</td><td>Puppy classes: £40–80 for 6 weeks</td></tr>
<tr><td>Months 4–5</td><td>Food, insurance, preventatives, teething toys</td><td>£50–80/month</td><td>£60–100/month</td><td>Peak teething phase — extra chew toys</td></tr>
<tr><td>Month 6</td><td>Neutering/spaying, transition bed, 6-month vet check</td><td>£150–300</td><td>£200–400</td><td>Neutering costs vary by size and sex</td></tr>
<tr><td>Months 7–11</td><td>Ongoing food, insurance, preventatives, training</td><td>£50–80/month</td><td>£70–110/month</td><td>Adolescent phase — possible training investment</td></tr>
<tr><td>Month 12</td><td>Annual booster, adult food transition, permanent bed</td><td>£80–140</td><td>£100–180</td><td>Transition to adult routine</td></tr>
</tbody></table></figure>"""

COMPARISON_TABLES["puppy-vaccination-schedule"] = """<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Age</th><th>Vaccine</th><th>What It Covers</th><th>Estimated UK Cost</th><th>Outdoor Access After</th><th>Notes</th></tr></thead><tbody>
<tr><td>6–8 weeks</td><td>First primary (DHP + Lepto)</td><td>Distemper, Hepatitis, Parvovirus, Leptospirosis</td><td>£30–50</td><td>Garden only (if secure)</td><td>Often done by breeder</td></tr>
<tr><td>10–12 weeks</td><td>Second primary (DHP + Lepto)</td><td>Same diseases — booster dose</td><td>£30–50</td><td>Pavements 1–2 weeks later</td><td>Full immunity develops in 7–14 days</td></tr>
<tr><td>16 weeks (optional)</td><td>Third primary (some vets)</td><td>Additional parvovirus cover</td><td>£20–40</td><td>Full outdoor access</td><td>Recommended in high-risk areas</td></tr>
<tr><td>12 months</td><td>First annual booster</td><td>DHP + Lepto (complete booster)</td><td>£30–60</td><td>Maintain current access</td><td>Essential — immunity wanes</td></tr>
<tr><td>Any age (optional)</td><td>Kennel cough (nasal)</td><td>Bordetella bronchiseptica, parainfluenza</td><td>£20–40</td><td>N/A</td><td>Required for boarding and daycare</td></tr>
<tr><td>Any age (for travel)</td><td>Rabies</td><td>Rabies virus</td><td>£50–70</td><td>N/A</td><td>Required for Pet Travel Scheme</td></tr>
</tbody></table></figure>"""

COMPARISON_TABLES["puppy-food-transition"] = """<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Day</th><th>Old Food Ratio</th><th>New Food Ratio</th><th>What to Watch For</th><th>If Problems Occur</th></tr></thead><tbody>
<tr><td>Day 1–2</td><td>75%</td><td>25%</td><td>Normal stool consistency</td><td>Continue at this ratio for 2 more days</td></tr>
<tr><td>Day 3–4</td><td>50%</td><td>50%</td><td>Slight softening may occur (normal)</td><td>Return to 75/25 for another 2 days</td></tr>
<tr><td>Day 5–6</td><td>25%</td><td>75%</td><td>Stool should be firming up</td><td>Return to 50/50 for another 2 days</td></tr>
<tr><td>Day 7+</td><td>0%</td><td>100%</td><td>Normal appetite and digestion</td><td>Return to 75% new/25% old if issues arise</td></tr>
<tr><td>Day 10–14 (if sensitive)</td><td>Extend transition</td><td>Slower ratio changes</td><td>Sensitive stomachs need slower transitions</td><td>Consult vet if diarrhoea persists 48+ hours</td></tr>
</tbody></table></figure>"""

# DOG HEALTH tables
COMPARISON_TABLES["supplement-types"] = """<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Supplement Type</th><th>Active Ingredients</th><th>Primary Purpose</th><th>UK Cost/Month</th><th>Time to See Effect</th><th>Best Suited For</th></tr></thead><tbody>
<tr><td>Glucosamine + Chondroitin</td><td>Glucosamine HCl, chondroitin sulphate</td><td>Cartilage repair and protection</td><td>£10–20</td><td>4–6 weeks</td><td>Early joint stiffness, large breeds over 5 years</td></tr>
<tr><td>Omega-3 Fish Oil</td><td>EPA, DHA fatty acids</td><td>Anti-inflammatory, coat and skin health</td><td>£5–12</td><td>4–8 weeks</td><td>Inflammatory conditions, dry skin, general health</td></tr>
<tr><td>Green-Lipped Mussel</td><td>Natural glucosamine, omega-3, minerals</td><td>Joint support and inflammation reduction</td><td>£8–18</td><td>4–6 weeks</td><td>Dogs that don't respond to standard glucosamine</td></tr>
<tr><td>MSM (Methylsulfonylmethane)</td><td>Organic sulphur compound</td><td>Pain relief, tissue repair</td><td>£5–10</td><td>2–4 weeks</td><td>Often combined with glucosamine for enhanced effect</td></tr>
<tr><td>Turmeric/Curcumin</td><td>Curcuminoids (with piperine for absorption)</td><td>Anti-inflammatory, antioxidant</td><td>£5–12</td><td>4–6 weeks</td><td>General anti-inflammatory support, senior dogs</td></tr>
<tr><td>Multivitamin</td><td>Vitamins A, D, E, B-complex, minerals</td><td>General nutritional support</td><td>£5–15</td><td>4–8 weeks</td><td>Dogs on limited diets, recovery from illness</td></tr>
<tr><td>Probiotic</td><td>Beneficial bacteria strains</td><td>Digestive health, immune support</td><td>£8–15</td><td>1–2 weeks</td><td>After antibiotics, digestive issues, food transitions</td></tr>
</tbody></table></figure>"""

COMPARISON_TABLES["dental-care-methods"] = """<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Method</th><th>Effectiveness</th><th>UK Cost</th><th>Frequency</th><th>Dog Acceptance</th><th>Best Used As</th></tr></thead><tbody>
<tr><td>Daily Tooth Brushing</td><td>Highest — removes plaque before it hardens</td><td>£30–50/year (paste + brush)</td><td>Daily</td><td>Moderate — requires training</td><td>Primary dental care method</td></tr>
<tr><td>VOHC-Approved Dental Chews</td><td>Good — mechanical plaque removal</td><td>£60–180/year</td><td>Daily (1 chew)</td><td>High — most dogs enjoy them</td><td>Supplement to brushing</td></tr>
<tr><td>Dental Water Additive</td><td>Moderate — reduces bacteria passively</td><td>£40–80/year</td><td>Daily (in water bowl)</td><td>Very high — tasteless</td><td>Starting point for resistant dogs</td></tr>
<tr><td>Dental Spray</td><td>Moderate — targets gum line</td><td>£40–70/year</td><td>Daily</td><td>Low to moderate — some dogs resist</td><td>Alternative when brushing is not possible</td></tr>
<tr><td>Raw Bones (with vet guidance)</td><td>Good — natural scraping action</td><td>£3–8 per bone</td><td>1–2 times per week</td><td>Very high</td><td>Supervised enrichment only</td></tr>
<tr><td>Professional Cleaning</td><td>Highest — removes tartar under anaesthesia</td><td>£150–300 per session</td><td>Every 1–2 years</td><td>N/A (under anaesthesia)</td><td>Periodic deep clean, essential for advanced tartar</td></tr>
<tr><td>Dental Diet (Prescription)</td><td>Moderate to good — special kibble design</td><td>£15–30/month</td><td>At every meal</td><td>High — tastes like normal food</td><td>Prone breeds with vet recommendation</td></tr>
</tbody></table></figure>"""

COMPARISON_TABLES["flea-treatment-comparison"] = """<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Treatment Type</th><th>Application Method</th><th>Speed of Action</th><th>Duration</th><th>UK Cost/Month</th><th>Key Advantage</th><th>Key Limitation</th></tr></thead><tbody>
<tr><td>Spot-On (Prescription)</td><td>Liquid on back of neck</td><td>12–24 hours</td><td>1 month</td><td>£5–12</td><td>Widely available, proven track record</td><td>Must avoid bathing 48 hours after</td></tr>
<tr><td>Oral Tablet (Prescription)</td><td>Flavoured chew tablet</td><td>2–6 hours</td><td>1 month</td><td>£8–15</td><td>Fastest action, no bathing restriction</td><td>Must be given with food for absorption</td></tr>
<tr><td>Flea Collar</td><td>Worn continuously</td><td>24–48 hours</td><td>6–8 months</td><td>£3–5 (amortised)</td><td>Continuous protection, no monthly application</td><td>Not suitable for dogs that swim often</td></tr>
<tr><td>Spot-On (Over-the-Counter)</td><td>Liquid on back of neck</td><td>24–48 hours</td><td>1 month</td><td>£3–8</td><td>No vet visit needed, widely available</td><td>Less effective than prescription options</td></tr>
<tr><td>Household Spray</td><td>Sprayed on carpets and furniture</td><td>Immediate contact kill</td><td>6–12 months residual</td><td>One-off: £8–15</td><td>Treats the environment (where 95% of fleas live)</td><td>Does not treat the dog directly</td></tr>
<tr><td>Natural/Herbal</td><td>Spray, collar, or shampoo</td><td>Variable</td><td>Variable</td><td>£5–15</td><td>No chemical active ingredients</td><td>Limited evidence of effectiveness</td></tr>
</tbody></table></figure>"""

# DOG GROOMING tables
COMPARISON_TABLES["brush-types-by-coat"] = """<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Brush Type</th><th>Coat Type Suited</th><th>Example Breeds</th><th>UK Price Range</th><th>How It Works</th><th>Frequency of Use</th></tr></thead><tbody>
<tr><td>Bristle Brush</td><td>Smooth, short coats</td><td>Boxer, Dalmatian, Beagle</td><td>£4–8</td><td>Removes loose hair, distributes natural oils</td><td>Once weekly</td></tr>
<tr><td>Slicker Brush</td><td>Most coat types (versatile)</td><td>Golden Retriever, Poodle, Collie</td><td>£5–12</td><td>Fine wire pins remove tangles and loose undercoat</td><td>2–4 times weekly</td></tr>
<tr><td>Pin Brush</td><td>Long, silky coats</td><td>Maltese, Afghan Hound, Shih Tzu</td><td>£6–10</td><td>Rounded-tip pins glide through long hair gently</td><td>Daily</td></tr>
<tr><td>Undercoat Rake</td><td>Dense double coats</td><td>Husky, German Shepherd, Labrador</td><td>£8–15</td><td>Long teeth reach through topcoat to remove loose undercoat</td><td>2–3 times weekly (daily when moulting)</td></tr>
<tr><td>Rubber Curry Brush</td><td>Smooth, very short coats</td><td>French Bulldog, Pug, Staffie</td><td>£3–6</td><td>Rubber nubs massage skin and lift loose hair</td><td>Once weekly</td></tr>
<tr><td>Dematting Comb</td><td>Long coats prone to matting</td><td>Cockapoo, Labradoodle, Cocker Spaniel</td><td>£6–12</td><td>Curved blades cut through mats without pulling skin</td><td>As needed (prevention better than cure)</td></tr>
<tr><td>Deshedding Tool</td><td>Heavy-shedding double coats</td><td>Husky, Akita, Malamute</td><td>£10–20</td><td>Thinning blade removes bulk of loose undercoat</td><td>1–2 times weekly during moult season</td></tr>
</tbody></table></figure>"""

COMPARISON_TABLES["shampoo-types-by-skin"] = """<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Shampoo Type</th><th>Skin Condition</th><th>Key Ingredients</th><th>UK Price Range</th><th>Bathing Frequency</th><th>When to Use</th></tr></thead><tbody>
<tr><td>General Purpose</td><td>Normal, healthy skin</td><td>Mild surfactants, balanced pH 6.5–7.5</td><td>£4–8</td><td>Every 4–8 weeks</td><td>Routine bathing for healthy dogs</td></tr>
<tr><td>Oatmeal-Based</td><td>Dry, flaky, mildly itchy skin</td><td>Colloidal oatmeal, aloe vera</td><td>£5–10</td><td>Every 4–6 weeks</td><td>Seasonal dryness, mild irritation</td></tr>
<tr><td>Hypoallergenic</td><td>Sensitive or allergy-prone skin</td><td>Minimal ingredients, fragrance-free</td><td>£6–12</td><td>As needed (vet-guided)</td><td>Dogs with known allergies or sensitivities</td></tr>
<tr><td>Medicated (Antibacterial)</td><td>Bacterial skin infections</td><td>Chlorhexidine (2–4%)</td><td>£8–15</td><td>2–3 times weekly (vet-prescribed)</td><td>Active bacterial skin infection (vet diagnosis)</td></tr>
<tr><td>Medicated (Antifungal)</td><td>Yeast/fungal infections</td><td>Miconazole, ketoconazole</td><td>£8–15</td><td>2–3 times weekly (vet-prescribed)</td><td>Yeast dermatitis (vet diagnosis)</td></tr>
<tr><td>Whitening/Brightening</td><td>Normal skin, stained white coat</td><td>Optical brighteners, gentle surfactants</td><td>£6–10</td><td>Every 4–6 weeks</td><td>White-coated breeds with yellowing</td></tr>
<tr><td>Puppy-Specific</td><td>Delicate puppy skin</td><td>Ultra-mild, tear-free, no fragrance</td><td>£4–7</td><td>As needed (minimal frequency)</td><td>Puppies under 12 months</td></tr>
</tbody></table></figure>"""

COMPARISON_TABLES["grooming-frequency-by-breed"] = """<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Coat Type</th><th>Example Breeds</th><th>Brushing Frequency</th><th>Bathing Frequency</th><th>Professional Grooming</th><th>Annual Grooming Cost (Home)</th><th>Annual Grooming Cost (Professional)</th></tr></thead><tbody>
<tr><td>Smooth/Short</td><td>Boxer, Staffie, Greyhound</td><td>Once weekly (10 min)</td><td>Every 6–8 weeks</td><td>Rarely needed</td><td>£30–50</td><td>£60–120</td></tr>
<tr><td>Short Double</td><td>Labrador, Pug, Beagle</td><td>Twice weekly (15 min)</td><td>Every 6–8 weeks</td><td>Optional deshedding visits</td><td>£40–70</td><td>£120–240</td></tr>
<tr><td>Long Double</td><td>Golden Retriever, Collie, Husky</td><td>3–4 times weekly (20 min)</td><td>Every 8–12 weeks</td><td>Every 8–12 weeks for tidy-up</td><td>£50–80</td><td>£200–400</td></tr>
<tr><td>Wire/Rough</td><td>Fox Terrier, Schnauzer, Airedale</td><td>2–3 times weekly (15 min)</td><td>Every 6–8 weeks</td><td>Hand-stripping every 6–8 weeks</td><td>£40–60</td><td>£240–480</td></tr>
<tr><td>Long Silky</td><td>Maltese, Shih Tzu, Afghan Hound</td><td>Daily (15–20 min)</td><td>Every 4–6 weeks</td><td>Every 6–8 weeks (essential)</td><td>£60–100</td><td>£280–560</td></tr>
<tr><td>Curly/Non-Shedding</td><td>Poodle, Bichon Frise, Cockapoo</td><td>3–4 times weekly (20 min)</td><td>Every 4–6 weeks</td><td>Every 6–8 weeks (essential)</td><td>£60–100</td><td>£280–560</td></tr>
<tr><td>Hairless</td><td>Chinese Crested, Xoloitzcuintli</td><td>N/A (skin care instead)</td><td>Weekly (skin maintenance)</td><td>Rarely needed</td><td>£40–80 (skincare products)</td><td>£60–120</td></tr>
</tbody></table></figure>"""

# Map post slug -> list of table keys to add
SLUG_TO_TABLES = {
    # Dog Beds
    "best-dog-beds-uk": ["dog-beds-material", "dog-beds-size", "dog-beds-price-tiers"],
    "best-cooling-dog-beds-uk": ["dog-beds-seasonal"],
    "best-orthopaedic-dog-beds-uk": ["dog-beds-material", "dog-beds-size"],
    "best-puppy-beds-uk": ["dog-beds-size", "dog-beds-price-tiers"],
    "dog-bed-types-glossary": ["dog-beds-material", "dog-beds-price-tiers"],
    "dog-bed-materials-explained": ["dog-beds-material"],
    "how-to-wash-dog-bed": [],
    "how-to-wash-and-dry-a-dog-bed-safely": [],
    "where-to-place-dog-bed": ["dog-beds-seasonal"],
    "dog-bed-placement-guide-where-to-put-your-dogs-bed": ["dog-beds-seasonal"],
    "how-to-choose-the-right-dog-bed-size": ["dog-beds-size", "dog-beds-price-tiers"],
    "dog-bed-terminology-materials-types-and-sizing-terms-explained": ["dog-beds-material"],
    "dog-bed-safety-avoiding-hazards-and-choosing-non-toxic-materials": ["dog-beds-material"],
    "seasonal-dog-bedding-adjusting-comfort-through-the-year": ["dog-beds-seasonal"],
    "puppy-bed-training-helping-your-dog-love-their-bed": ["dog-beds-size"],
    # Puppy Care
    "puppy-care-essentials-glossary": ["puppy-vaccination-schedule"],
    "puppy-care-glossary-essential-terms-for-new-puppy-owners": ["puppy-vaccination-schedule"],
    "first-time-dog-owner-essentials": ["puppy-cost-monthly"],
    "puppy-socialisation-timeline-guide": [],
    "best-puppy-training-guide-uk": ["puppy-cost-monthly"],
    "best-puppy-collars-uk": [],
    "best-puppy-food-uk": ["puppy-food-transition"],
    "best-puppy-toys-uk": [],
    "puppy-vaccination-schedule-uk": ["puppy-vaccination-schedule"],
    "puppy-teething-guide-stages-signs-and-soothing-tips": [],
    "first-week-new-puppy-guide": ["puppy-cost-monthly"],
    "puppy-sleep-guide-by-age": [],
    "puppy-proofing-home-safety-guide": [],
    # Dog Health
    "best-dog-health-and-care-uk": ["supplement-types", "dental-care-methods", "flea-treatment-comparison"],
    "best-dog-dental-care-uk": ["dental-care-methods"],
    "best-dog-flea-treatment-uk": ["flea-treatment-comparison"],
    "best-dog-joint-supplements-uk": ["supplement-types"],
    "dog-dental-health-care-guide": ["dental-care-methods"],
    "dog-health-terminology-understanding-common-veterinary-and-care-terms": ["supplement-types"],
    "seasonal-dog-care-guide": ["flea-treatment-comparison"],
    # Dog Grooming
    "dog-grooming-basics-guide": ["brush-types-by-coat", "grooming-frequency-by-breed"],
    "best-dog-grooming-supplies-uk": ["brush-types-by-coat", "shampoo-types-by-skin"],
    "best-dog-brushes-uk": ["brush-types-by-coat", "grooming-frequency-by-breed"],
    "best-dog-shampoo-uk": ["shampoo-types-by-skin"],
    "best-dog-nail-clippers-uk": [],
    "harness-vs-collar-which-is-better": [],
    "how-to-measure-dog-for-harness": [],
    "dog-harnesses-complete-guide": [],
}

# ============================================================
# BLOCK BUILDER FUNCTIONS
# ============================================================

def build_practical_guide_block(guide_key):
    """Build the Practical Guide block (emerald, bg #ecfdf5, border #6ee7b7)."""
    content = PRACTICAL_GUIDES.get(guide_key, "")
    if not content:
        return ""
    return (
        '<div class="wp-block-group has-border-color has-background" '
        'style="border-color:#6ee7b7;border-width:1px;border-radius:6px;'
        'background-color:#ecfdf5;margin-top:24px;margin-bottom:24px;'
        'padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<h4 class="wp-block-heading">Step-by-Step Practical Guide</h4>\n'
        f'{content.strip()}\n'
        '</div>\n'
    )

def build_decision_pathway_block(pathway_key):
    """Build the Decision Pathway block (orange, bg #fff7ed, border #fdba74)."""
    content = DECISION_PATHWAYS.get(pathway_key, "")
    if not content:
        return ""
    return (
        '<div class="wp-block-group has-border-color has-background" '
        'style="border-color:#fdba74;border-width:1px;border-radius:6px;'
        'background-color:#fff7ed;margin-top:24px;margin-bottom:24px;'
        'padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<h4 class="wp-block-heading">Your Decision Pathway</h4>\n'
        f'{content.strip()}\n'
        '</div>\n'
    )

# ============================================================
# INSERTION LOGIC
# ============================================================

def find_insertion_point_practical(content):
    """Find insertion point BEFORE 'How to Evaluate' or 'How We Evaluated This Topic'."""
    # Try "How to Evaluate" first (more common in newer posts)
    patterns = [
        r'<div[^>]*>[\s\S]*?<h4[^>]*>How to Evaluate</h4>',
        r'<div[^>]*>[\s\S]*?<h4[^>]*>How We Evaluated This Topic</h4>',
    ]
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            return match.start()

    # Fallback: before "Key Takeaways"
    match = re.search(r'<div[^>]*>[\s\S]*?<h4[^>]*>Key Takeaways</h4>', content)
    if match:
        return match.start()

    # Last fallback: before "Frequently Asked Questions"
    match = re.search(r'<h2[^>]*>Frequently Asked Questions</h2>', content)
    if match:
        return match.start()

    return None

def find_insertion_point_decision(content):
    """Find insertion point AFTER 'Which Option Suits Your Situation' block."""
    # Find the block containing "Which Option Suits"
    match = re.search(r'<div[^>]*>[\s\S]*?<h4[^>]*>Which Option Suits Your Situation</h4>', content)
    if match:
        # Find the closing </div> after this block
        start_pos = match.start()
        # Count div nesting from the opening div
        div_depth = 0
        pos = start_pos
        while pos < len(content):
            open_match = re.match(r'<div[^>]*>', content[pos:])
            close_match = re.match(r'</div>', content[pos:])
            if open_match:
                div_depth += 1
                pos += len(open_match.group())
            elif close_match:
                div_depth -= 1
                pos += len(close_match.group())
                if div_depth == 0:
                    return pos  # Insert right after the closing div
            else:
                pos += 1
        return None

    # Fallback: after "Common Problems and Solutions" block
    match = re.search(r'<div[^>]*>[\s\S]*?<h4[^>]*>Common Problems and Solutions</h4>', content)
    if match:
        start_pos = match.start()
        div_depth = 0
        pos = start_pos
        while pos < len(content):
            open_match = re.match(r'<div[^>]*>', content[pos:])
            close_match = re.match(r'</div>', content[pos:])
            if open_match:
                div_depth += 1
                pos += len(open_match.group())
            elif close_match:
                div_depth -= 1
                pos += len(close_match.group())
                if div_depth == 0:
                    return pos
            else:
                pos += 1

    # Last fallback: end of content
    return len(content)

def find_table_insertion_point(content):
    """Find where to insert comparison tables - after the last existing table, or before FAQ."""
    # Find last existing table
    tables = list(re.finditer(r'</figure>', content))
    if tables:
        return tables[-1].end()

    # Before FAQ
    match = re.search(r'<h2[^>]*>Frequently Asked Questions</h2>', content)
    if match:
        return match.start()

    # Before Related Guides/Reading at end
    matches = list(re.finditer(r'<h2[^>]*>Related (?:Guides|Reading)</h2>', content))
    if matches:
        return matches[-1].start()

    return len(content)

def insert_blocks(content, slug, guide_key, pathway_key, table_keys):
    """Insert all three block types into the content."""
    practical_added = False
    decision_added = False
    tables_added = 0

    # Check if blocks already exist
    has_practical = "Step-by-Step Practical Guide" in content
    has_decision = "Your Decision Pathway" in content

    # 1. Insert Practical Guide (before Evaluation Framework)
    if not has_practical and guide_key and guide_key in PRACTICAL_GUIDES:
        practical_block = build_practical_guide_block(guide_key)
        if practical_block:
            insert_pos = find_insertion_point_practical(content)
            if insert_pos is not None:
                content = content[:insert_pos] + "\n" + practical_block + "\n" + content[insert_pos:]
                practical_added = True

    # 2. Insert Decision Pathway (after Scenario Guidance)
    if not has_decision and pathway_key and pathway_key in DECISION_PATHWAYS:
        decision_block = build_decision_pathway_block(pathway_key)
        if decision_block:
            insert_pos = find_insertion_point_decision(content)
            if insert_pos is not None:
                content = content[:insert_pos] + "\n" + decision_block + "\n" + content[insert_pos:]
                decision_added = True

    # 3. Insert Comparison Tables
    if table_keys:
        tables_html = ""
        for tk in table_keys:
            if tk in COMPARISON_TABLES:
                table_content = COMPARISON_TABLES[tk]
                # Check if this specific table already exists (by checking a unique header combo)
                # Use the first <th> text as a fingerprint
                th_match = re.search(r'<th>(.*?)</th>', table_content)
                if th_match:
                    fingerprint = th_match.group(1)
                    if fingerprint in content:
                        continue  # Table already present
                tables_html += "\n" + table_content + "\n"
                tables_added += 1

        if tables_html:
            insert_pos = find_table_insertion_point(content)
            content = content[:insert_pos] + "\n" + tables_html + "\n" + content[insert_pos:]

    return content, practical_added, decision_added, tables_added

# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    print("=" * 70)
    print("PHASE 10BK/10BL/10BN ENGINE")
    print("Practical Guidance + Decision Pathways + Comparison Tables")
    print("=" * 70)

    # Fetch all posts
    print("\n[1] Fetching posts from all 4 clusters...")
    posts = fetch_all_posts()
    print(f"    Found {len(posts)} unique posts")

    # CSV tracking
    csv_rows = []

    # Process each post
    for idx, (pid, pdata) in enumerate(sorted(posts.items()), 1):
        title = pdata["title"]
        slug = pdata["slug"]
        cluster = pdata["cluster"]
        print(f"\n[{idx}/{len(posts)}] Processing: {title}")
        print(f"    ID: {pid} | Slug: {slug} | Cluster: {cluster}")

        # Get raw content
        post_full = wp_get(f"posts/{pid}?_fields=content&context=edit")
        if "content" not in post_full:
            print(f"    ERROR: Could not fetch content for {pid}")
            csv_rows.append({
                "id": pid, "title": title, "cluster": cluster,
                "practical_guide_added": "ERROR", "decision_pathway_added": "ERROR",
                "comparison_tables_added": "ERROR", "status": "fetch_error"
            })
            continue

        content = post_full["content"]["raw"]

        # Determine content keys
        guide_key = SLUG_TO_GUIDE_KEY.get(slug)
        if not guide_key:
            # Fallback to cluster-generic
            cluster_generic_map = {
                "Dog Beds": "dog-beds-generic",
                "Puppy Care": "puppy-care-generic",
                "Dog Health": "dog-health-generic",
                "Dog Grooming": "dog-grooming-generic",
            }
            guide_key = cluster_generic_map.get(cluster)

        pathway_key = SLUG_TO_GUIDE_KEY.get(slug)
        if not pathway_key:
            cluster_pathway_map = {
                "Dog Beds": "dog-beds",
                "Puppy Care": "puppy-care",
                "Dog Health": "dog-health",
                "Dog Grooming": "dog-grooming",
            }
            pathway_key = cluster_pathway_map.get(cluster)

        # Decision pathway key needs to be looked up differently
        if pathway_key and pathway_key in DECISION_PATHWAYS:
            pass  # Already good
        else:
            # Try slug-to-guide mapping to find the pathway
            cluster_pathway_map = {
                "Dog Beds": "dog-beds",
                "Puppy Care": "puppy-care",
                "Dog Health": "dog-health",
                "Dog Grooming": "dog-grooming",
            }
            pathway_key = cluster_pathway_map.get(cluster)

        table_keys = SLUG_TO_TABLES.get(slug, [])

        print(f"    Guide key: {guide_key}")
        print(f"    Pathway key: {pathway_key}")
        print(f"    Table keys: {table_keys}")

        # Insert blocks
        new_content, p_added, d_added, t_added = insert_blocks(
            content, slug, guide_key, pathway_key, table_keys
        )

        if not p_added and not d_added and t_added == 0:
            print("    SKIP: All blocks already present or no insertion point found")
            csv_rows.append({
                "id": pid, "title": title, "cluster": cluster,
                "practical_guide_added": "already_present",
                "decision_pathway_added": "already_present",
                "comparison_tables_added": "0",
                "status": "skipped"
            })
            continue

        # Update the post
        print(f"    Inserting: Practical={'YES' if p_added else 'no'}, "
              f"Decision={'YES' if d_added else 'no'}, Tables={t_added}")

        success = wp_update_post(pid, new_content)

        status = "updated" if success else "update_failed"
        csv_rows.append({
            "id": pid, "title": title, "cluster": cluster,
            "practical_guide_added": "yes" if p_added else "already_present",
            "decision_pathway_added": "yes" if d_added else "already_present",
            "comparison_tables_added": str(t_added),
            "status": status
        })

        if success:
            print(f"    SUCCESS: Post {pid} updated")
        else:
            print(f"    FAILED: Post {pid} update failed")

        # Rate limiting
        time.sleep(1.5)

    # Write CSV
    print(f"\n\nWriting CSV to {CSV_PATH}")
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "title", "cluster", "practical_guide_added",
            "decision_pathway_added", "comparison_tables_added", "status"
        ])
        writer.writeheader()
        writer.writerows(csv_rows)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    total = len(csv_rows)
    updated = sum(1 for r in csv_rows if r["status"] == "updated")
    skipped = sum(1 for r in csv_rows if r["status"] == "skipped")
    failed = sum(1 for r in csv_rows if "error" in r["status"] or "failed" in r["status"])
    practical_count = sum(1 for r in csv_rows if r["practical_guide_added"] == "yes")
    decision_count = sum(1 for r in csv_rows if r["decision_pathway_added"] == "yes")
    table_count = sum(int(r["comparison_tables_added"]) for r in csv_rows if r["comparison_tables_added"].isdigit())

    print(f"Total posts processed: {total}")
    print(f"Updated: {updated}")
    print(f"Skipped (already done): {skipped}")
    print(f"Failed: {failed}")
    print(f"Practical Guides added: {practical_count}")
    print(f"Decision Pathways added: {decision_count}")
    print(f"Comparison Tables added: {table_count}")
    print(f"\nCSV saved to: {CSV_PATH}")


if __name__ == "__main__":
    main()
