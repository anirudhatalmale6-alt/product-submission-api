#!/usr/bin/env python3
"""
Phase 10BK/10BL/10BO Engine — Practical Guidance, Decision Support v3, Trust Depth
Targets: Cat Toys, Cat Supplies, Indoor Cats, Uncategorized clusters
All posts in category 1 (Uncategorized) on pethubonline.com
"""

import subprocess
import json
import csv
import time
import sys
import os
import re
import tempfile

# ── Configuration ──
WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
CSV_PATH = "/var/lib/freelancer/projects/40416335/phase10bo_data/practical_decision_trust_cat_indoor_uncat.csv"

# ── Target posts mapped to logical clusters ──
# Cat Toys cluster
CAT_TOYS_POSTS = [5414, 5296]
# Cat Supplies cluster
CAT_SUPPLIES_POSTS = [5458]
# Indoor Cats cluster
INDOOR_CATS_POSTS = [5519]
# Uncategorized (general pet posts that include cat/multi-species content)
UNCATEGORIZED_POSTS = [
    5521,  # Pet Health Terminology
    5511,  # Pet Enrichment Explained
    5509,  # Pet Toy Safety
    5467,  # Pet Feeding Guide
    5464,  # Pet Grooming Glossary
    5460,  # Pet Nutrition Terminology
]

ALL_POSTS = {}
for pid in CAT_TOYS_POSTS:
    ALL_POSTS[pid] = "Cat Toys"
for pid in CAT_SUPPLIES_POSTS:
    ALL_POSTS[pid] = "Cat Supplies"
for pid in INDOOR_CATS_POSTS:
    ALL_POSTS[pid] = "Indoor Cats"
for pid in UNCATEGORIZED_POSTS:
    ALL_POSTS[pid] = "Uncategorized"


def wp_api(method, endpoint, data=None):
    """Make WP REST API call via subprocess curl."""
    url = f"{WP_BASE}/{endpoint}"
    cmd = ["curl", "-s", "--compressed", "-u", f"{WP_USER}:{WP_PASS}"]

    if method == "GET":
        cmd.append(url)
    elif method == "POST":
        cmd.extend(["-X", "POST"])
        cmd.extend(["-H", "Content-Type: application/json"])
        if data:
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            json.dump(data, tmp)
            tmp.close()
            cmd.extend(["-d", f"@{tmp.name}"])
        cmd.append(url)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if data and 'tmp' in locals():
        try:
            os.unlink(tmp.name)
        except:
            pass

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  ERROR parsing response for {endpoint}: {result.stdout[:200]}")
        return None


# ══════════════════════════════════════════════════════════════════════
# PHASE 10BK — PRACTICAL GUIDANCE CONTENT
# ══════════════════════════════════════════════════════════════════════

PRACTICAL_GUIDES = {
    5414: {
        "title": "Step-by-Step Practical Guide",
        "intro": "Follow these practical steps to choose and use cat toys effectively for your pet's wellbeing.",
        "steps": [
            "<strong>Step 1: Assess your cat's play style</strong> — Observe whether your cat prefers chasing (wand toys, £5–12), pouncing (spring toys, £3–6), or batting (ball track toys, £10–20). Spend 2–3 days noting which movements attract the most interest.",
            "<strong>Step 2: Build a starter toy kit</strong> — Every cat needs a minimum of one wand toy (£5–12), one self-play toy such as a ball track (£10–20), and one sensory toy like a catnip mouse (£2–5). Budget approximately £20–40 for an initial set.",
            "<strong>Step 3: Introduce toys gradually</strong> — Present one new toy at a time. Allow 24–48 hours before introducing another. Place new toys in your cat's preferred play area, typically near a window or open floor space of at least 1.5m x 1.5m.",
            "<strong>Step 4: Schedule interactive play sessions</strong> — Commit to a minimum of two 15–20 minute play sessions daily, ideally at dawn and dusk when cats are naturally most active. Use wand toys during these sessions.",
            "<strong>Step 5: Rotate toys weekly</strong> — Keep 3–4 toys available at any time and store the rest. Rotate every 5–7 days to maintain novelty. This extends toy life by 40–60% and keeps engagement high.",
            "<strong>Step 6: Check toy safety monthly</strong> — Inspect all toys for loose parts, fraying string (discard if shorter than 30cm on wand toys), or exposed stuffing. Replace damaged toys immediately. Budget £5–10 per month for replacements.",
            "<strong>Step 7: Match toys to age and ability</strong> — Kittens under 6 months: small, soft toys without detachable parts, £3–8 each. Adult cats: sturdier interactive toys, £8–15. Senior cats (10+ years): gentler, low-impact toys, £5–12.",
            "<strong>Step 8: Add puzzle feeders for mental enrichment</strong> — Start with a simple puzzle feeder (£8–15) and fill with 10–15 pieces of dry food. Gradually increase difficulty over 2–4 weeks as your cat masters each level.",
            "<strong>Step 9: Create a dedicated play space</strong> — Designate an area of at least 2m x 2m with a non-slip surface. Include vertical elements (cat tree, minimum 100cm tall, £30–80) for climbing and a tunnel (£8–15) for hiding.",
            "<strong>Step 10: Adjust for seasonal changes</strong> — Winter: increase indoor play sessions to three per day as outdoor stimulation decreases. Summer: use cooling mats (£10–20) near play areas. Spring/autumn: introduce new textures to match seasonal shedding.",
            "<strong>Step 11: Multi-cat household adjustments</strong> — Provide at least one set of toys per cat plus spares. Ensure play areas have multiple exit routes. Budget an additional £15–25 per extra cat for their own toy collection.",
            "<strong>Step 12: Monitor and adapt</strong> — Track your cat's engagement weekly. If interest drops in all toys, consult your veterinarian — sudden disinterest can indicate pain or illness. Healthy cats should show active play interest daily."
        ]
    },
    5296: {
        "title": "Step-by-Step Practical Guide",
        "intro": "Use this guide to set up a complete indoor enrichment system for your house cat.",
        "steps": [
            "<strong>Step 1: Evaluate your indoor space</strong> — Measure available floor area and vertical space. Indoor cats need a minimum of 18 square metres of accessible living space. Identify window positions for stimulation stations and ensure at least 2 rooms are accessible.",
            "<strong>Step 2: Invest in a quality cat tree</strong> — Choose a tree at least 120cm tall for adult cats, with a stable base of minimum 50cm x 50cm. Budget £40–80 for a well-built option. Position near a window for outdoor viewing — this provides hours of passive enrichment.",
            "<strong>Step 3: Set up interactive wand toy sessions</strong> — Purchase 2–3 wand toys (£5–12 each) with interchangeable attachments. Schedule two 15–20 minute play sessions daily — morning and evening. Mimic prey movements: drag slowly, then quick bursts.",
            "<strong>Step 4: Introduce puzzle feeders progressively</strong> — Start with a basic treat ball (£5–10) using high-value treats. After 1–2 weeks, upgrade to a multi-level puzzle feeder (£12–25). Aim for 20–30% of daily food delivered via puzzles to prevent obesity.",
            "<strong>Step 5: Create self-play stations</strong> — Set up ball track toys (£10–20) and spring toys (£3–6) in 2–3 locations around your home. Place near natural pathways your cat uses. Self-play toys are essential for working households where cats are alone 6–8 hours daily.",
            "<strong>Step 6: Provide sensory enrichment</strong> — Rotate catnip toys (£2–5 each) every 2–3 days. Offer silver vine sticks (£4–8 for a pack of 5) as an alternative — approximately 75% of cats respond to silver vine, including many who ignore catnip.",
            "<strong>Step 7: Establish a tunnel and hide system</strong> — Install at least one tunnel (£8–15, minimum 90cm length) and 2–3 hiding spots such as covered beds (£15–30) or cardboard boxes (free). Indoor cats particularly need escape routes for feeling secure.",
            "<strong>Step 8: Install window enrichment</strong> — Attach a window perch (£15–30, weight capacity must exceed your cat's weight by 50%) or bird feeder outside a window. This provides the single most effective passive enrichment for indoor cats.",
            "<strong>Step 9: Rotate toys on a strict schedule</strong> — Keep 4–5 toys out and store 8–10. Swap every 5–7 days. Mark rotation dates on a calendar. Consistent rotation keeps indoor cats mentally stimulated without constant new purchases.",
            "<strong>Step 10: Consider safe outdoor access</strong> — If space and budget allow, a window catio costs £80–200 for a basic model. Alternatively, harness training (harness: £10–20) can start from 4 months of age with 5-minute sessions, increasing by 2 minutes weekly.",
            "<strong>Step 11: Monitor weight and activity</strong> — Weigh your indoor cat monthly — healthy adult weight is typically 3.5–5.5kg depending on breed. Indoor cats need 200–250 kcal daily (less than outdoor cats). Adjust play intensity if weight increases by more than 10%.",
            "<strong>Step 12: Seasonal indoor adjustments</strong> — Winter: heated beds (£20–40) and increased play sessions. Summer: cooling mats (£10–20) and frozen treat toys. Spring: increase grooming sessions for moulting. Adjust toy types to match your cat's seasonal energy levels."
        ]
    },
    5458: {
        "title": "Step-by-Step Practical Guide",
        "intro": "Follow these steps to provide appropriate scratching outlets and redirect unwanted scratching behaviour.",
        "steps": [
            "<strong>Step 1: Provide the right scratching posts</strong> — Purchase at least one vertical scratching post per cat, minimum 80cm tall for adult cats, with a stable base of at least 30cm x 30cm. Sisal-wrapped posts (£15–40) are preferred by the majority of cats.",
            "<strong>Step 2: Add horizontal scratching options</strong> — Some cats prefer horizontal surfaces. Corrugated cardboard scratchers (£5–12) are inexpensive and popular. Place one flat scratcher and one angled scratcher to test preference. Replace cardboard scratchers every 2–3 months.",
            "<strong>Step 3: Position scratchers strategically</strong> — Place scratching posts next to furniture your cat currently targets, near sleeping areas (cats scratch upon waking), and at room entrances. Cats use scratching for territorial marking, so high-traffic areas are essential.",
            "<strong>Step 4: Use positive reinforcement</strong> — When your cat uses the post, offer a treat (£3–6 per bag of training treats) or verbal praise immediately. Never punish scratching — this increases stress and worsens the behaviour. Catnip on the post (£2–4 per pouch) can attract initial interest.",
            "<strong>Step 5: Protect furniture during transition</strong> — Apply double-sided tape (£4–8 per roll) or furniture protectors (£8–15 per pack of 4) to targeted surfaces. These deterrents are temporary — use for 4–6 weeks while redirecting to appropriate surfaces.",
            "<strong>Step 6: Maintain claw health</strong> — Check claws fortnightly. Indoor cats may need claw trimming every 3–4 weeks using cat-specific nail clippers (£5–10). Overgrown claws can catch in carpet and cause injury. If your cat resists, ask your veterinary nurse (£10–20 per session).",
            "<strong>Step 7: Monitor for stress scratching</strong> — Excessive scratching, particularly in new locations, can indicate stress. Common triggers include new pets, house moves, or changes in routine. If scratching increases suddenly, identify and address the stressor. Consider Feliway diffusers (£20–30) for stress reduction.",
            "<strong>Step 8: Multi-cat household setup</strong> — Provide one scratching post per cat plus one extra, distributed across different rooms. Cats in multi-cat homes scratch more for territorial communication. Budget an additional £15–40 per extra cat for dedicated scratching surfaces.",
            "<strong>Step 9: Replace worn scratching surfaces</strong> — Inspect scratching posts monthly. Replace sisal rope when frayed or flattened (every 12–18 months for regular use). Cardboard scratchers: every 2–3 months. Some posts offer replaceable sisal sleeves (£8–15) for cost savings.",
            "<strong>Step 10: Accommodate different life stages</strong> — Kittens: smaller, lighter posts (30–50cm, £8–15) from 8 weeks. Adult cats: full-height posts (80cm+, £15–40). Senior cats: lower, more stable posts with wider bases, or angled scratchers that require less stretching (£10–20).",
            "<strong>Step 11: Never declaw</strong> — Declawing is illegal in the UK under the Animal Welfare Act 2006. It causes chronic pain and behavioural problems. If scratching is a persistent problem despite appropriate provision, consult a certified clinical animal behaviourist (ABTC-registered, £80–150 per consultation).",
            "<strong>Step 12: Track and adjust</strong> — Keep a simple log of which scratching surfaces your cat uses and which furniture they target. After 4–6 weeks, you should see a clear pattern. Remove unused scratchers and reinforce preferred types and positions."
        ]
    },
    5519: {
        "title": "Step-by-Step Practical Guide",
        "intro": "Follow this comprehensive guide to create an enriching, healthy indoor environment for your house cat.",
        "steps": [
            "<strong>Step 1: Set up the litter tray system</strong> — Provide one tray per cat plus one extra (e.g., 2 cats = 3 trays). Use open trays (£8–25 each) at least 1.5 times your cat's body length. Fill with 5–7cm depth of clumping litter (£10–20 per month). Place in quiet, accessible locations away from food and water.",
            "<strong>Step 2: Create vertical territory</strong> — Install a cat tree (minimum 120cm, £40–80) and/or wall-mounted shelves (£15–30 per shelf). Indoor cats need vertical space to feel secure and exercise. Aim for at least 3 vertical resting spots at different heights throughout your home.",
            "<strong>Step 3: Establish a play routine</strong> — Schedule a minimum of two 15–20 minute interactive play sessions daily using wand toys (£5–12). Indoor cats without adequate play develop obesity, stress behaviours, and over-grooming. Vary toy types between sessions.",
            "<strong>Step 4: Provide window enrichment</strong> — Install at least one window perch (£15–30) with a view of outdoor activity. A bird feeder outside the window provides hours of passive stimulation. Ensure windows have secure screens (£10–25) if opened in warm weather.",
            "<strong>Step 5: Manage indoor diet carefully</strong> — Indoor cats require 15–20% fewer calories than outdoor cats. Feed approximately 200–250 kcal daily for an average 4kg adult cat. Use measured portions (kitchen scales: £8–15) rather than free-feeding. Weigh monthly and adjust if weight changes by more than 200g.",
            "<strong>Step 6: Deliver food through enrichment</strong> — Serve 20–30% of daily food via puzzle feeders (£8–25) or scatter feeding. This replaces the foraging activity indoor cats miss. Start simple and increase difficulty over 2–4 weeks.",
            "<strong>Step 7: Provide fresh water sources</strong> — Offer water in at least 2 locations, away from food bowls. Cat water fountains (£15–40) encourage drinking — essential for indoor cats prone to urinary issues. Change water daily; clean fountains weekly.",
            "<strong>Step 8: Maintain scratching provision</strong> — Provide at least one vertical scratching post (minimum 80cm, £15–40) per cat and one horizontal scratcher (£5–12). Position near sleeping areas and room entrances. Replace sisal posts every 12–18 months.",
            "<strong>Step 9: Create hiding and resting spots</strong> — Provide 2–3 enclosed resting areas per cat: covered beds (£15–30), igloo beds (£10–25), or cardboard boxes. Indoor cats need retreat spaces to manage stress and feel secure, especially in busy households.",
            "<strong>Step 10: Clean litter trays on schedule</strong> — Scoop solid waste daily. Full litter change and tray wash weekly using hot water and mild detergent (avoid bleach or strong chemicals). A cat with a dirty tray may start eliminating elsewhere — the most common indoor cat behavioural complaint.",
            "<strong>Step 11: Monitor health indicators</strong> — Watch for: excessive grooming (potential stress), reduced play interest (potential pain or illness), changes in litter tray habits (potential urinary or digestive issues), weight gain above 10% of ideal body weight. Book a veterinary check-up every 6–12 months (£40–60 per consultation).",
            "<strong>Step 12: Consider seasonal adjustments</strong> — Winter: heated beds (£20–40), increase play to compensate for shorter days, ensure humidity stays above 40% (dry air affects respiratory health). Summer: cooling mats (£10–20), ensure fresh water is always available, check windows are secure if opened."
        ]
    },
    5521: {
        "title": "Step-by-Step Practical Guide",
        "intro": "Use this guide to understand and act on common health terms you may encounter from your veterinarian or on pet health resources.",
        "steps": [
            "<strong>Step 1: Create a pet health record</strong> — Start a dedicated folder (physical or digital) for your pet's health documents. Include vaccination records, weight history, and veterinary visit summaries. Review every 6 months. A basic pet health journal costs £3–8.",
            "<strong>Step 2: Learn to assess body condition</strong> — Use the Body Condition Score (BCS) scale of 1–9. Score 4–5 is ideal: ribs easily felt but not visible, waist visible from above. For cats, healthy weight is typically 3.5–5.5kg; for medium dogs, 10–25kg. Weigh monthly using bathroom scales (hold pet, subtract your weight).",
            "<strong>Step 3: Understand vaccination schedules</strong> — Core vaccinations for cats: feline parvovirus, calicivirus, herpesvirus (initial course from 8–9 weeks, booster at 12 weeks, annual or triennial depending on type). Core for dogs: distemper, parvovirus, hepatitis. Vaccination costs £40–60 for primary course, £30–50 for annual boosters.",
            "<strong>Step 4: Recognise emergency signs</strong> — Seek immediate veterinary attention for: difficulty breathing, collapse, seizures, bloated abdomen (dogs), inability to urinate (cats — emergency within 24 hours), profuse bleeding, or suspected poisoning. Keep your emergency vet number saved — out-of-hours visits cost £150–300.",
            "<strong>Step 5: Manage parasite prevention</strong> — Treat for fleas monthly (£5–12 per treatment), worms quarterly for cats and dogs (£3–8 per treatment), and ticks in high-risk areas seasonally. Indoor cats still need flea prevention — fleas enter on clothing and shoes.",
            "<strong>Step 6: Understand prescription terminology</strong> — 'BID' means twice daily, 'SID' once daily, 'PRN' as needed, 'PO' by mouth. Always complete full antibiotic courses. Store medications at recommended temperatures. Pet prescriptions cost £10–20; shop around for dispensing.",
            "<strong>Step 7: Schedule preventive care</strong> — Annual health check: £40–60. Dental check: included or £20–40 separately. Blood panel for seniors (8+ years cats, 7+ years dogs): £80–150. Preventive care reduces lifetime veterinary costs by an estimated 20–30%.",
            "<strong>Step 8: Monitor dental health</strong> — Check your pet's teeth monthly for tartar build-up (yellow/brown deposits), red gums, or bad breath. Dental disease affects over 85% of cats and dogs over 3 years. Cat dental cleaning under anaesthesia: £200–400. Dog dental scaling: £250–500.",
            "<strong>Step 9: Know when to seek a specialist</strong> — Your vet may refer to an RCVS-recognised specialist for complex conditions. Specialist consultations cost £150–300. Common referrals include cardiology, orthopaedics, dermatology, and oncology. Ask your vet to explain referral reasons clearly.",
            "<strong>Step 10: Consider pet insurance</strong> — Lifetime policies (£15–50 per month for cats, £20–80 for dogs) provide the most comprehensive coverage. Compare excess levels (£50–250 typical) and annual limits (£4,000–15,000). Pre-existing conditions are excluded — insure early."
        ]
    },
    5511: {
        "title": "Step-by-Step Practical Guide",
        "intro": "Follow these steps to build an effective enrichment programme for your cat or dog.",
        "steps": [
            "<strong>Step 1: Assess current enrichment levels</strong> — List all activities your pet engages in daily: play sessions, puzzle toys, social interaction, outdoor access, training. If fewer than 3 enrichment activities daily, your pet likely needs more stimulation.",
            "<strong>Step 2: Choose appropriate puzzle feeders</strong> — For cats: start with a treat ball (£5–10) or snuffle mat (£8–15). For dogs: Kong Classic (£6–12 depending on size) or Lickimat (£5–10). Serve 20–30% of daily food through enrichment devices to replace natural foraging behaviour.",
            "<strong>Step 3: Establish daily play schedules</strong> — Cats: minimum two 15–20 minute interactive sessions daily. Dogs: minimum 30 minutes structured play plus 30 minutes off-lead exercise where safe. Consistency matters more than duration — same times each day builds routine.",
            "<strong>Step 4: Add sensory enrichment</strong> — Cats: catnip (£2–5), silver vine (£4–8), valerian root toys (£5–10). Dogs: scent trails using treats, herb gardens (dog-safe herbs: parsley, rosemary, mint), novel textures. Rotate sensory items every 2–3 days to maintain novelty.",
            "<strong>Step 5: Introduce training as enrichment</strong> — Short training sessions (5–10 minutes) count as mental enrichment. Cats can learn clicker training (clicker: £2–4, training treats: £3–6). Dogs: practise one new cue per week alongside familiar ones. Positive reinforcement only.",
            "<strong>Step 6: Provide social enrichment</strong> — For dogs: regular interaction with other dogs if temperamentally suited. For cats: respect individual social preferences — some cats thrive alone, others enjoy feline company. Never force social interaction.",
            "<strong>Step 7: Create exploration opportunities</strong> — Rotate household items: new boxes, paper bags (handles removed), crinkly materials. Dogs benefit from 'sniff walks' (15–20 minutes of slow walking with free sniffing). These cost nothing and provide significant mental stimulation.",
            "<strong>Step 8: Build an enrichment rotation calendar</strong> — Plan a 7-day rotation: Day 1 — puzzle feeder; Day 2 — scent games; Day 3 — new toy introduction; Day 4 — training session; Day 5 — social play; Day 6 — exploration items; Day 7 — rest and gentle interaction. Budget: £5–15 per week.",
            "<strong>Step 9: Adjust for age and ability</strong> — Puppies/kittens: short, frequent sessions (5–10 minutes, 4–5 times daily). Adults: longer, fewer sessions. Seniors: gentler activities, lower physical demand, more scent-based enrichment. Arthritic pets: raised feeders (£8–20), ground-level activities.",
            "<strong>Step 10: Monitor wellbeing indicators</strong> — Effective enrichment reduces: excessive barking/meowing, destructive behaviour, over-grooming, and lethargy. If problem behaviours persist despite adequate enrichment, consult an ABTC-registered behaviourist (£80–150 per session)."
        ]
    },
    5509: {
        "title": "Step-by-Step Practical Guide",
        "intro": "Follow these steps to ensure every toy you buy or use is safe for your pet.",
        "steps": [
            "<strong>Step 1: Check toy sizing</strong> — Toys must be appropriate for your pet's size. For cats: avoid toys smaller than 3cm diameter (choking risk). For dogs: the toy should not fit entirely in the mouth. Measure your pet's mouth width and select accordingly.",
            "<strong>Step 2: Inspect materials before purchase</strong> — Look for toys made from natural rubber (£5–15), food-grade silicone, or tightly woven fabric. Avoid toys with strong chemical odours, loose glued-on eyes, or small detachable parts. UK-compliant toys should meet BS EN 71 safety principles even though pet toys are not formally regulated under this standard.",
            "<strong>Step 3: Perform the pull test</strong> — Before giving any toy, pull firmly on all attachments: eyes, bells, ribbons, squeakers. If any part detaches with moderate force, discard the toy. Repeat this test weekly for toys in active use.",
            "<strong>Step 4: Establish a weekly inspection routine</strong> — Every Sunday (or your chosen day), inspect all toys for: tears, exposed stuffing, fraying rope, cracked rubber, worn squeakers. Budget £5–10 per month for replacement toys. Discard any toy that fails inspection.",
            "<strong>Step 5: Store toys safely</strong> — Keep toys in a dedicated bin or basket (£5–15) when not in use. This prevents unsupervised play with damaged toys and maintains novelty. Cat wand toys with string must always be stored out of reach — string ingestion requires emergency surgery (£1,500–3,000).",
            "<strong>Step 6: Clean toys regularly</strong> — Rubber toys: dishwasher safe or hot soapy water weekly. Fabric toys: machine wash at 30°C monthly. Rope toys: soak in dilute pet-safe disinfectant (£4–8 per bottle) fortnightly. Replace any toy that cannot be cleaned effectively.",
            "<strong>Step 7: Match materials to play style</strong> — Heavy chewers (dogs): solid rubber or nylon (£8–20). Gentle players (cats, small dogs): plush or fleece (£3–10). Fetch players: natural rubber balls (£4–8). Avoid tennis balls for regular use — the abrasive felt wears tooth enamel.",
            "<strong>Step 8: Supervise new toy introductions</strong> — Monitor your pet with any new toy for the first 30 minutes. Watch for: aggressive chewing that breaks pieces off, attempts to swallow parts, or frustration/fear responses. Remove immediately if any concern arises.",
            "<strong>Step 9: Know the emergency signs</strong> — If your pet swallows a toy part: drooling, pawing at mouth, retching, loss of appetite, lethargy, or absent bowel movements. Contact your vet immediately — do not wait. Foreign body removal costs £1,000–3,000 in the UK.",
            "<strong>Step 10: Research before bulk buying</strong> — Check product reviews on UK-specific platforms. Avoid unbranded marketplace toys with no safety information. Reputable UK brands include Kong, Beco, and Rosewood. Spending £2–3 more per toy on quality dramatically reduces safety risks."
        ]
    },
    5467: {
        "title": "Step-by-Step Practical Guide",
        "intro": "Use this step-by-step guide to establish a healthy, well-portioned feeding routine for your pet.",
        "steps": [
            "<strong>Step 1: Determine your pet's caloric needs</strong> — Average indoor cat (4kg): 200–250 kcal/day. Average medium dog (15kg, moderately active): 700–900 kcal/day. Check food packaging for kcal per serving. Neutered pets typically need 10–15% fewer calories.",
            "<strong>Step 2: Choose an appropriate feeding method</strong> — Scheduled feeding (2–3 meals daily) is recommended for most pets. Cats: 2 meals plus puzzle feeder enrichment. Dogs: 2 meals, 12 hours apart. Free-feeding dry food suits some cats but increases obesity risk — monitor weight monthly.",
            "<strong>Step 3: Measure portions accurately</strong> — Use digital kitchen scales (£8–15) rather than measuring cups — cups can vary by 20–30%. Weigh food at each meal for the first month, then maintain the habit. This single step prevents the majority of pet obesity cases.",
            "<strong>Step 4: Set up feeding stations properly</strong> — Cats: elevated bowls (8–12cm height, £5–15) reduce neck strain. Water bowl separate from food, at least 1 metre apart. Dogs: appropriate height feeders for large breeds (£15–30). Multi-pet households: separate stations to prevent guarding.",
            "<strong>Step 5: Transition foods gradually</strong> — When switching foods, mix over 7–10 days: Day 1–3: 75% old / 25% new. Day 4–6: 50/50. Day 7–9: 25% old / 75% new. Day 10: 100% new. Abrupt changes cause digestive upset — vomiting, diarrhoea, or food refusal.",
            "<strong>Step 6: Apply the 10% treat rule</strong> — Treats should comprise no more than 10% of daily calories. For a cat on 220 kcal/day, that is only 22 kcal of treats (approximately 4–5 small commercial cat treats). Dog training treats: break into pea-sized pieces. Training treats: £3–6 per bag.",
            "<strong>Step 7: Ensure adequate hydration</strong> — Cats need approximately 200–250ml water daily. Wet food provides 70–80% moisture. If feeding dry food, ensure water intake is adequate — cat fountains (£15–40) increase water consumption by 30–50%. Dogs: 50ml per kg body weight daily.",
            "<strong>Step 8: Use enrichment feeding</strong> — Serve 20–30% of meals via puzzle feeders (cats: £8–15; dogs: £8–25), lick mats (£5–10), or scatter feeding. This slows eating, provides mental stimulation, and reduces boredom-related begging. Start with easy puzzles and progress over 2–4 weeks.",
            "<strong>Step 9: Monitor body condition monthly</strong> — Use the Body Condition Score (1–9 scale): 4–5 is ideal. Ribs should be easily felt but not visible. Visible waist from above. If BCS reaches 6 or above, reduce daily intake by 10–15% and increase activity.",
            "<strong>Step 10: Adjust for life stages</strong> — Kittens/puppies: 3–4 meals daily, higher protein. Adults: 2 meals. Seniors (cats 8+, dogs 7+): reduced calories by 10–20%, consider joint-support diets (£15–30 per month premium over standard food). Pregnant/nursing: up to 2x normal calories.",
            "<strong>Step 11: Read food labels properly</strong> — Ingredients are listed by weight. Look for a named meat source as the first ingredient. 'Complete' food meets all nutritional needs; 'complementary' does not. Check for the FEDIAF compliance statement. Premium cat food: £1.50–3.00 per day; premium dog food: £2–5 per day.",
            "<strong>Step 12: Know when to seek advice</strong> — Consult your vet if: sudden appetite loss lasting more than 24 hours (cats) or 48 hours (dogs), unexplained weight loss exceeding 5% in a month, persistent vomiting after meals, or difficulty eating. A nutrition consultation costs £40–80."
        ]
    },
    5464: {
        "title": "Step-by-Step Practical Guide",
        "intro": "Follow this guide to establish a safe, effective grooming routine for your cat or dog.",
        "steps": [
            "<strong>Step 1: Gather essential grooming tools</strong> — Cats: slicker brush (£5–10), fine-toothed comb (£3–8), nail clippers (£5–10). Dogs: breed-appropriate brush (£5–15), deshedding tool for double coats (£10–20), nail clippers or grinder (£8–25). Total starter kit: £20–50.",
            "<strong>Step 2: Start grooming gradually</strong> — Begin with 2–3 minute sessions, rewarding cooperation with treats. Increase duration by 1–2 minutes per session over 2–3 weeks. Short-haired cats: brush once weekly. Long-haired cats: daily brushing to prevent matting. Dogs: varies by coat type.",
            "<strong>Step 3: Establish a brushing schedule</strong> — Short-haired cats: once weekly, 5 minutes. Long-haired cats (Persian, Ragdoll): daily, 10–15 minutes. Short-haired dogs: weekly. Double-coated dogs: 2–3 times weekly, daily during spring/autumn moult. Long-haired dogs: daily.",
            "<strong>Step 4: Learn safe nail trimming</strong> — Trim 1–2mm from the tip only, avoiding the quick (pink area visible in light-coloured nails). Indoor cats: every 3–4 weeks. Dogs: every 4–6 weeks or when nails click on hard floors. Cat nail clippers: £5–10. If uncertain, veterinary nurse trim costs £10–20.",
            "<strong>Step 5: Check ears regularly</strong> — Inspect ears weekly for redness, odour, excess wax, or dark discharge. Clean only the visible outer ear with a damp cotton pad — never insert anything into the ear canal. Ear cleaner solution: £5–10 per bottle, lasts 2–3 months.",
            "<strong>Step 6: Maintain dental hygiene</strong> — Brush teeth 2–3 times weekly using pet-specific toothpaste (£4–8, never human toothpaste). Cat toothbrush: finger brush type (£3–5). Dog toothbrush: angled head (£3–8). Dental chews for dogs: £5–15 per month. Dental disease affects 85%+ of pets over 3 years.",
            "<strong>Step 7: Bathing guidelines</strong> — Cats: rarely need bathing unless medically directed. Dogs: every 4–8 weeks depending on breed, activity, and coat. Use pet-specific shampoo (£5–12 per bottle). Overbathing strips natural oils and causes dry, irritated skin. Water temperature: lukewarm (37–38°C).",
            "<strong>Step 8: Watch for skin problems during grooming</strong> — During every grooming session, check for: lumps, bumps, bald patches, flaky skin, parasites (fleas appear as tiny dark moving dots; flea dirt looks like black pepper). Report findings to your vet promptly. Skin consultation: £40–60.",
            "<strong>Step 9: Seasonal grooming adjustments</strong> — Spring/autumn: increase brushing frequency for moulting — daily for 4–6 weeks. Summer: check paw pads for hot pavement burns (walk dogs before 10am or after 6pm). Winter: moisturise cracked paw pads with pet-safe balm (£5–10).",
            "<strong>Step 10: Know when to use a professional</strong> — Professional dog grooming: £25–60 per session depending on breed and size. Frequency: every 6–8 weeks for breeds requiring clipping. Choose groomers who are City & Guilds Level 3 qualified or members of the Pet Industry Federation."
        ]
    },
    5460: {
        "title": "Step-by-Step Practical Guide",
        "intro": "Use this guide to decode pet food labels and make informed nutrition choices for your cat or dog.",
        "steps": [
            "<strong>Step 1: Understand 'complete' vs 'complementary'</strong> — 'Complete' pet food provides all required nutrients — this should be the foundation of your pet's diet. 'Complementary' food (e.g., treats, toppers, some wet foods) does not and must be fed alongside complete food. Check every packet — this single distinction is the most important label element.",
            "<strong>Step 2: Read the ingredients list</strong> — Ingredients are listed by weight in descending order. A named meat source (e.g., 'chicken' not 'meat and animal derivatives') as the first ingredient indicates higher protein quality. Cat food must list taurine as added or inherent — it is essential and cats cannot synthesise it.",
            "<strong>Step 3: Check the analytical constituents</strong> — Key values: crude protein (cats: minimum 26% dry matter; dogs: minimum 18%), crude fat (cats: minimum 9%; dogs: minimum 5.5%), crude fibre, and crude ash (mineral content). Compare like-for-like by converting wet food values to dry matter basis — divide by (100 minus moisture percentage).",
            "<strong>Step 4: Look for FEDIAF compliance</strong> — The Federation of European Pet Food Industries sets nutritional guidelines. UK pet foods should state compliance. This is not a legal requirement but indicates the manufacturer follows evidence-based nutritional standards. Premium food costs £1.50–3.00/day for cats, £2–5/day for dogs.",
            "<strong>Step 5: Understand life-stage labelling</strong> — 'Kitten' or 'puppy' food has higher protein and calories for growth. 'Adult' is maintenance. 'Senior' typically has reduced calories and added joint support. Feeding the wrong life-stage food can cause deficiencies or excess weight. Switch at: kittens to adult at 12 months; puppies vary by breed (12–24 months).",
            "<strong>Step 6: Decode marketing terms</strong> — 'Natural' has no legal definition in UK pet food. 'Organic' must meet organic certification standards. 'Grain-free' is not inherently better — grains are a safe carbohydrate source for most pets. 'Hypoallergenic' should mean novel or hydrolysed protein sources — confirm on label.",
            "<strong>Step 7: Compare cost per day, not per bag</strong> — Higher-quality food is often more nutrient-dense, meaning smaller portions. Calculate: (bag price ÷ servings per bag) = cost per meal. A £40 bag lasting 40 days (£1/day) may be better value than a £15 bag lasting 10 days (£1.50/day).",
            "<strong>Step 8: Evaluate treat nutrition</strong> — Apply the 10% rule: treats should not exceed 10% of daily calorie intake. A typical cat treat is 3–5 kcal each. Budget: £3–6 per month for cat treats, £5–10 for dog treats. Consider using pieces of the pet's regular food as training rewards.",
            "<strong>Step 9: Assess special dietary needs</strong> — Common prescription diets include: urinary (cats, £25–40 per month), gastrointestinal (£20–35), renal (£25–40), weight management (£20–30). These require veterinary recommendation. Never feed prescription diets without veterinary guidance.",
            "<strong>Step 10: Store food correctly</strong> — Dry food: resealable container (£8–20), use within 4–6 weeks of opening. Wet food: refrigerate opened tins, use within 48 hours, serve at room temperature. Treats: follow packaging guidance. Proper storage prevents nutrient degradation and bacterial contamination."
        ]
    },
}


# ══════════════════════════════════════════════════════════════════════
# PHASE 10BL — DECISION PATHWAY CONTENT
# ══════════════════════════════════════════════════════════════════════

DECISION_PATHWAYS = {
    5414: {
        "title": "Your Decision Pathway",
        "intro": "Find the scenario that best matches your situation for a clear recommendation.",
        "paths": [
            "<strong>If you have a kitten under 6 months</strong> → Focus on small, soft interactive toys without detachable parts. Wand toys with short strings (under 40cm) and crinkle balls are ideal. Avoid string toys that could be ingested. Budget: £3–8 per toy, starter kit of 5–6 toys for £20–35.",
            "<strong>If your cat ignores most toys</strong> → Try silver vine sticks (£4–8 for 5) — 75% of cats respond, including many who ignore catnip. Also try electronic motion toys (£10–20) that mimic prey movement. Schedule play sessions at dawn or dusk when cats are naturally most active.",
            "<strong>If you have an indoor-only cat</strong> → Prioritise puzzle feeders (£8–15), a ball track toy (£10–20), and wand toys (£5–12). Indoor cats need a minimum of 5–6 different toy types and two 15–20 minute play sessions daily. Total enrichment budget: £40–70 initially.",
            "<strong>If your cat is overweight</strong> → Replace food bowls with puzzle feeders to slow eating and increase activity. Schedule three 10–15 minute play sessions daily instead of two. Use interactive toys that encourage running and jumping. Consult your vet before any diet change (£40–60 per visit).",
            "<strong>If you have multiple cats</strong> → Provide at least one set of self-play toys per cat, plus shared interactive toys for supervised sessions. Ensure each cat has solo play access. Budget approximately £25–40 per additional cat. Watch for resource guarding during toy use.",
            "<strong>If your cat is a senior (10+ years)</strong> → Choose low-impact toys: gentle wand toys with slow movements (£5–10), catnip cushions (£3–6), and simple puzzle feeders at easy difficulty (£8–12). Reduce session length to 10 minutes but maintain frequency. Avoid toys requiring jumping from heights."
        ]
    },
    5296: {
        "title": "Your Decision Pathway",
        "intro": "Choose the pathway that matches your indoor cat's specific needs.",
        "paths": [
            "<strong>If your indoor cat is home alone for 6+ hours daily</strong> → Invest heavily in self-play toys: ball track (£10–20), electronic motion toy (£10–20), tunnel (£8–15), and window perch (£15–30). Pre-set puzzle feeders before leaving. Total setup: £50–80.",
            "<strong>If your indoor cat shows signs of boredom (over-grooming, excessive meowing)</strong> → Increase interactive play to three 15–20 minute sessions daily. Add puzzle feeders for all meals. Install a catio (£80–200) or start harness training (£10–20 for harness). Consider a Feliway diffuser (£20–30) for stress.",
            "<strong>If you are setting up for a new indoor kitten</strong> → Start with a small cat tree (60–80cm, £20–40), 3–4 soft toys (£3–8 each), a simple puzzle feeder (£5–10), and a tunnel (£8–15). Total starter budget: £50–80. Upgrade the cat tree to 120cm+ when fully grown.",
            "<strong>If your indoor cat is gaining weight</strong> → Serve 100% of meals through puzzle feeders and scatter feeding. Increase play sessions to 3×15 minutes daily. Install vertical climbing opportunities (wall shelves: £15–30 each) to encourage exercise. Target a loss of 1–2% body weight per week.",
            "<strong>If you want to provide outdoor access safely</strong> → Window catios: £80–200 for a basic model, no planning permission needed for most. Harness training: start from 4 months, 5 minutes indoors first, increase by 2 minutes per session. Full garden enclosure: £200–500+ depending on size.",
            "<strong>If you are transitioning an outdoor cat to indoors</strong> → Expect an adjustment period of 4–8 weeks. Provide maximum enrichment from day one: cat tree, multiple toy types, puzzle feeders, window perches. Use Feliway (£20–30) and maintain a strict play schedule. Budget £100–150 for the initial enrichment setup."
        ]
    },
    5458: {
        "title": "Your Decision Pathway",
        "intro": "Match your scratching situation to the right solution below.",
        "paths": [
            "<strong>If your cat is scratching furniture despite having a scratching post</strong> → The post may be in the wrong location. Move it directly next to the targeted furniture. Apply double-sided tape (£4–8) to the furniture temporarily. The post must be taller than 80cm and completely stable — wobbly posts are rejected.",
            "<strong>If you are setting up scratching for a new cat</strong> → Start with one tall sisal post (£15–40), one corrugated cardboard scratcher (£5–12), and one angled scratcher (£8–15). Place near sleeping areas and room entrances. Total initial cost: £28–67. Observe preferences over 2 weeks before buying more.",
            "<strong>If you have multiple cats with scratching conflicts</strong> → Provide one scratching post per cat plus one extra, distributed across separate rooms. Cats use scratching for territorial communication — concentrated scratching stations increase tension. Budget £15–40 per additional cat.",
            "<strong>If your senior cat has reduced scratching</strong> → Check claws for overgrowth — reduced scratching in older cats often indicates joint stiffness. Switch to low-profile angled scratchers (£8–15) and horizontal pads (£5–12). Veterinary check recommended (£40–60) to assess arthritis.",
            "<strong>If scratching has suddenly increased</strong> → This often signals stress: new pet, house move, changed routine, or building work. Address the stressor where possible. Add Feliway diffusers (£20–30 per room). Provide extra scratching surfaces temporarily. If it persists beyond 3 weeks, consult a behaviourist (£80–150).",
            "<strong>If your kitten is learning to scratch</strong> → Introduce a small, stable post (30–50cm, £8–15) from 8 weeks of age. Use positive reinforcement when the kitten uses it. Protect furniture during the learning phase (4–8 weeks) with furniture covers (£8–15). Upgrade to a full-size post by 6 months."
        ]
    },
    5519: {
        "title": "Your Decision Pathway",
        "intro": "Find the scenario closest to your indoor cat's situation for tailored guidance.",
        "paths": [
            "<strong>If you are keeping a cat indoors for the first time</strong> → Budget £100–150 for initial setup: cat tree (120cm+, £40–80), litter trays (£8–25 each), scratching post (£15–40), puzzle feeders (£8–15 each), window perch (£15–30). Ongoing monthly costs: £40–70 for litter, food, and toy replacement.",
            "<strong>If your indoor cat is overweight (BCS 6+)</strong> → Reduce daily calories by 10–15% (consult your vet first). Serve all food via puzzle feeders. Increase play to three 15–20 minute sessions daily. Add vertical climbing opportunities. Target 1–2% body weight loss per week. Veterinary weight clinic: £20–40 per check.",
            "<strong>If your indoor cat is showing stress signs (over-grooming, hiding, aggression)</strong> → Ensure adequate resources: one litter tray per cat plus one extra, separate feeding stations, multiple hiding spots, and at least 3 elevated resting areas. Add Feliway diffuser (£20–30). If signs persist beyond 2 weeks, consult a behaviourist (£80–150).",
            "<strong>If you have multiple indoor cats</strong> → Each cat needs their own: litter tray plus one shared extra, feeding station, resting spot, and scratching post. Minimum space: 18m² per cat. Vertical space helps cats share territory peacefully. Budget an additional £50–80 per extra cat for resources.",
            "<strong>If your indoor cat is a kitten under 12 months</strong> → Kitten-proof the entire home: secure cables, remove toxic plants (lilies are lethal to cats), install window locks. Provide 3–4 short play sessions daily (10 minutes each). Kitten food (higher protein) until 12 months. Monthly costs: £50–70 including food, litter, and toys.",
            "<strong>If your indoor cat is elderly (12+ years)</strong> → Lower litter tray sides (maximum 10cm entry height). Add ramp access to favourite spots. Heated beds (£20–40) ease joint stiffness. Reduce play intensity but maintain 2 gentle sessions daily. Six-monthly vet checks (£40–60) become essential. Consider senior-specific food (£2–4 per day)."
        ]
    },
    5521: {
        "title": "Your Decision Pathway",
        "intro": "Select the path that best matches your pet health needs.",
        "paths": [
            "<strong>If you are a first-time pet owner</strong> → Register with a local veterinary practice immediately (initial consultation: £40–60). Arrange vaccinations, microchipping (legal requirement for dogs; recommended for cats, £20–30), and neutering (cats: £40–80; dogs: £100–300). Set up monthly parasite prevention (£5–12).",
            "<strong>If your pet has a chronic condition</strong> → Ask your vet for a written management plan including medication names, dosages, and monitoring schedule. Keep a symptom diary. Lifetime pet insurance (£15–80/month) is strongly recommended if not already in place. Specialist referrals: £150–300 per consultation.",
            "<strong>If you are considering pet insurance</strong> → Lifetime policies offer the best coverage (£15–50/month for cats, £20–80 for dogs). Check annual limits (£4,000–15,000) and excess levels (£50–250). Insure from the earliest age possible — pre-existing conditions are always excluded.",
            "<strong>If your pet is entering senior years (cats 8+, dogs 7+)</strong> → Switch to six-monthly vet checks (£40–60 each). Request annual blood panels (£80–150) to catch organ changes early. Discuss diet adjustments and joint support supplements (£8–20/month). Senior pets benefit from consistent routines and reduced stress.",
            "<strong>If you suspect a health emergency</strong> → Do not wait. Contact your vet or out-of-hours service immediately. Common emergencies: difficulty breathing, seizures, inability to urinate (cats), bloated abdomen (dogs), collapse, poisoning. Emergency treatment: £150–300+ for initial assessment. Keep the VPIS (Veterinary Poisons Information Service) number accessible."
        ]
    },
    5511: {
        "title": "Your Decision Pathway",
        "intro": "Choose your situation for targeted enrichment advice.",
        "paths": [
            "<strong>If your pet shows destructive behaviour when alone</strong> → This signals insufficient enrichment or separation anxiety. Start with puzzle feeders filled before departure (£8–15 each), a Kong stuffed with frozen filling for dogs (£6–12), and a radio or TV left on for background noise. If destruction is severe, consult an ABTC behaviourist (£80–150).",
            "<strong>If you have a limited enrichment budget</strong> → Effective enrichment does not require expensive toys. Cardboard boxes (free), paper bags with handles removed (free), scatter feeding (no cost), scent trails using regular food (no cost), and training sessions (clicker: £2–4) provide excellent stimulation. Total cost: under £5.",
            "<strong>If you have a senior pet with reduced mobility</strong> → Focus on scent-based enrichment (snuffle mats: £8–15), gentle puzzle feeders at easy settings, and calm social interaction. Avoid toys requiring jumping or fast movement. Raised feeding stations (£8–20) reduce neck strain. Short, frequent sessions (5–10 minutes, 3–4 daily).",
            "<strong>If your cat and dog live together</strong> → Provide species-specific enrichment: cats need vertical space and solo toys; dogs need outdoor exercise and social play. Ensure the cat has dog-free zones with elevated escape routes. Separate enrichment sessions prevent competition. Budget for both species independently.",
            "<strong>If you want to start training as enrichment</strong> → Begin with clicker training (clicker: £2–4, treats: £3–6). Cats: 3–5 minute sessions, 2–3 times daily. Dogs: 5–10 minute sessions, 2–3 times daily. Start with one simple behaviour (sit, touch, come) and build from there. Training is the highest-value enrichment activity available.",
            "<strong>If your pet seems lethargic despite adequate enrichment</strong> → First rule out medical causes — book a vet check (£40–60). If health is confirmed normal, vary enrichment types and timing. Try novel items: different textures, new scents, rotating puzzle difficulty. Some pets need environmental changes (rearrange furniture, new walking routes) rather than more toys."
        ]
    },
    5509: {
        "title": "Your Decision Pathway",
        "intro": "Find the safety scenario that applies to your situation.",
        "paths": [
            "<strong>If your pet is a heavy chewer (destroys toys quickly)</strong> → Choose solid rubber toys rated for aggressive chewers (£10–20). Avoid plush, rope, or thin plastic toys. Check toys after every play session. Consider Kong Extreme range or similar. Never leave unsupervised with any toy. Budget £10–15 per month for replacements.",
            "<strong>If you have a puppy or kitten (under 12 months)</strong> → Use only age-appropriate toys: no small parts, no long strings, no hard bones. Cat kittens: soft fabric toys 4–6cm, crinkle balls (£2–5). Dog puppies: soft rubber teething toys (£5–10). Supervise all play. Replace toys the moment any part loosens.",
            "<strong>If your pet has swallowed a toy piece</strong> → Contact your vet immediately. Do not induce vomiting unless instructed by a veterinary professional. Watch for: loss of appetite, vomiting, lethargy, straining to defecate, abdominal pain. Foreign body surgery costs £1,000–3,000 in the UK. Time is critical.",
            "<strong>If you are buying toys from online marketplaces</strong> → Be cautious with unbranded imports: check for material safety information, avoid strong chemical odours, inspect construction quality before use. Prefer UK-based brands with clear contact details. The extra £2–3 for a reputable brand significantly reduces risk.",
            "<strong>If your pet plays with children's toys</strong> → Children's toys often have small parts, batteries, or toxic paint not tested for animal ingestion. Keep children's and pet toys strictly separate. Educate children about which toys belong to the pet. Coin batteries are extremely dangerous if swallowed — lethal within hours."
        ]
    },
    5467: {
        "title": "Your Decision Pathway",
        "intro": "Match your feeding situation to the appropriate guidance below.",
        "paths": [
            "<strong>If your pet is overweight (BCS 6+)</strong> → Consult your vet before changing diet (£40–60). Reduce daily calories by 10–15%. Switch to scheduled feeding if free-feeding. Serve all food via puzzle feeders. Use low-calorie treats only. Weigh monthly. Target 1–2% body weight loss per week. Weight management food: £20–35 per month.",
            "<strong>If you are transitioning to a new food</strong> → Mix over 7–10 days to prevent digestive upset. Start 75%/25% old/new, shifting gradually. If diarrhoea or vomiting occurs, slow the transition to 14 days. Never switch food abruptly. Keep both foods in stock during the transition period.",
            "<strong>If your cat is not drinking enough water</strong> → Add a water fountain (£15–40) — flowing water increases cat water intake by 30–50%. Place water bowls away from food (minimum 1 metre). Offer wet food (70–80% moisture). Add a small amount of tuna water to a second bowl. Multiple water stations increase consumption.",
            "<strong>If you have a fussy eater</strong> → Warm wet food slightly (to body temperature, not hot) to release aroma. Offer food for 20 minutes, then remove — do not leave out all day. Avoid adding human food as toppers (creates dependency). If fussiness is new, see your vet — dental pain and nausea cause food refusal.",
            "<strong>If you feed a raw diet</strong> → Ensure the diet meets FEDIAF complete nutritional standards. Handle raw food with strict hygiene: separate utensils, clean surfaces immediately, wash hands thoroughly. Children and immunocompromised individuals face higher risk. Freeze-dried raw options (£3–6/day for cats) reduce handling risk.",
            "<strong>If you have multiple pets with different dietary needs</strong> → Feed in separate rooms or use microchip-activated feeders (£50–100 each) that only open for the correct pet. Supervise mealtimes. Remove uneaten food within 20 minutes. This prevents prescription diet cross-contamination and calorie theft."
        ]
    },
    5464: {
        "title": "Your Decision Pathway",
        "intro": "Choose the grooming scenario that matches your pet's needs.",
        "paths": [
            "<strong>If your long-haired cat has matted fur</strong> → Do not attempt to cut mats with scissors (high risk of skin cuts). Use a mat splitter (£5–10) or wide-toothed comb with cornflour dusted into the mat. Work from the outer edge inward. For severe matting, a professional groomer (£30–50 for cats) or veterinary nurse is safer.",
            "<strong>If your pet resists grooming</strong> → Go back to basics: 1–2 minute sessions with high-value treats. Pair the sight of grooming tools with treats for 3–5 days before attempting grooming. Use a soft brush first. Build positive associations over 2–3 weeks. Never restrain forcefully — this increases future resistance.",
            "<strong>If your dog has a double coat</strong> → Never shave a double coat — it does not regrow correctly and removes UV protection. Use an undercoat rake (£8–15) 2–3 times weekly, daily during moult (spring/autumn, lasting 4–6 weeks). Professional deshedding treatment: £40–60 per session.",
            "<strong>If you notice skin problems during grooming</strong> → Common findings: bald patches (could indicate ringworm, allergies, or stress), flaky skin (diet or environment), lumps (veterinary check advised within 2 weeks), flea dirt (start flea treatment immediately, £5–12 per month). Veterinary skin consultation: £40–60.",
            "<strong>If your senior pet finds grooming painful</strong> → Use ultra-soft brushes (£8–15) and shorter sessions (3–5 minutes). Groom in their preferred resting spot rather than moving them. Focus on comfort areas first. If stiffness is apparent, discuss pain management with your vet (£40–60). Arthritis affects most pets over 10 years.",
            "<strong>If you are unsure which tools to buy</strong> → Start with the basics: one breed-appropriate brush (£5–15), a fine-toothed comb (£3–8), and nail clippers (£5–10). Total: £13–33. Add specialist tools only after identifying your pet's specific coat needs. Avoid gimmick tools — a quality slicker brush handles most coat types."
        ]
    },
    5460: {
        "title": "Your Decision Pathway",
        "intro": "Select the nutrition scenario that applies to your situation.",
        "paths": [
            "<strong>If you are choosing food for the first time</strong> → Select a 'complete' food from a reputable UK brand with FEDIAF compliance. Match to life stage (kitten/puppy, adult, senior). Named meat source as first ingredient. Budget: £1.50–3/day for cats, £2–5/day for dogs. Avoid the cheapest options — quality ingredients cost more but require smaller portions.",
            "<strong>If your pet has food allergies or sensitivities</strong> → Work with your vet to conduct a dietary elimination trial (8–12 weeks on a single novel protein). Hypoallergenic diets: £25–50/month. Do not self-diagnose — many symptoms attributed to food allergies are actually environmental. Veterinary dermatology referral: £150–300 if needed.",
            "<strong>If you want to compare food quality between brands</strong> → Convert wet food analytical constituents to dry matter basis for fair comparison. Calculate cost per day rather than cost per bag. Check the ingredients list for named proteins. Look for the FEDIAF statement. Ignore marketing claims like 'premium' or 'natural' — these have no regulated definition.",
            "<strong>If your pet needs a prescription diet</strong> → Prescription diets require veterinary recommendation and typically cost £20–50/month. Common types: urinary, renal, gastrointestinal, weight management, joint support. Buy from your vet or an authorised retailer with a valid prescription. Never substitute with a regular diet without veterinary approval.",
            "<strong>If you are feeding a senior pet (cats 8+, dogs 7+)</strong> → Senior food has reduced calories (10–20% less), often with added glucosamine for joints and adjusted mineral levels for kidney support. Transition gradually over 10 days. Senior food costs approximately 10–15% more than adult formulas. Combine with regular weight monitoring and six-monthly vet checks."
        ]
    },
}


# ══════════════════════════════════════════════════════════════════════
# PHASE 10BO — TRUST DEPTH / RESEARCH SOURCES CONTENT
# ══════════════════════════════════════════════════════════════════════

TRUST_SOURCES = {
    5414: {
        "title": "Research Sources and Standards",
        "intro": "The guidance in this article is informed by the following UK organisations and standards.",
        "sources": [
            "<strong>International Cat Care (iCatCare)</strong> — Guidance on feline play behaviour, toy safety, and enrichment best practices. iCatCare is a leading international feline welfare charity based in the UK.",
            "<strong>Cats Protection</strong> — The UK’s largest cat welfare charity. Their ‘Essential Guide to Cat Care’ provides evidence-based recommendations on play, enrichment, and indoor cat management.",
            "<strong>PDSA (People’s Dispensary for Sick Animals)</strong> — Their annual PAW Report provides data on UK pet welfare, including enrichment practices and common welfare concerns.",
            "<strong>RSPCA</strong> — Guidance on the five welfare needs under the Animal Welfare Act 2006, including the need for an appropriate environment and the ability to exhibit normal behaviour patterns.",
            "<strong>British Veterinary Association (BVA)</strong> — Position statements on companion animal welfare, including the importance of environmental enrichment and species-appropriate play."
        ]
    },
    5296: {
        "title": "Research Sources and Standards",
        "intro": "This guide draws on evidence and guidance from the following UK organisations.",
        "sources": [
            "<strong>International Cat Care (iCatCare)</strong> — Their ‘Indoor Cat Guidance’ publication provides detailed recommendations for environmental enrichment, play schedules, and welfare monitoring for house cats.",
            "<strong>Cats Protection</strong> — The ‘Keeping Your Cat Happy Indoors’ guidance covers space requirements, enrichment strategies, and common behavioural challenges for indoor cats in the UK.",
            "<strong>PDSA</strong> — The annual PAW Report consistently highlights that indoor cats are at higher risk of obesity and behavioural issues, reinforcing the importance of structured enrichment programmes.",
            "<strong>Animal Welfare Act 2006</strong> — UK law establishes five welfare needs for all animals, including the need for a suitable environment and the ability to exhibit normal behaviour patterns — both directly relevant to indoor cat care.",
            "<strong>Royal College of Veterinary Surgeons (RCVS)</strong> — Professional standards for veterinary advice on feline welfare, including guidance on obesity prevention and behavioural health in indoor cats."
        ]
    },
    5458: {
        "title": "Research Sources and Standards",
        "intro": "The information in this guide is supported by the following UK organisations and welfare standards.",
        "sources": [
            "<strong>International Cat Care (iCatCare)</strong> — Published guidance on feline scratching behaviour, including surface preferences, post positioning, and the welfare implications of declawing.",
            "<strong>Cats Protection</strong> — Their ‘Essential Guide to Cat Care’ covers scratching as a natural behaviour and provides practical advice on redirecting scratching from furniture.",
            "<strong>Animal Welfare Act 2006</strong> — Declawing cats is illegal in England and Wales under this Act, and in Scotland under the Animal Health and Welfare (Scotland) Act 2006, recognising it as a mutilation causing chronic pain.",
            "<strong>Association of Pet Behaviour Counsellors (APBC)</strong> — Provides evidence-based guidance on addressing unwanted scratching through environmental modification and positive reinforcement rather than punishment.",
            "<strong>RSPCA</strong> — Position statement on cat welfare emphasises that scratching is an essential feline behaviour and that appropriate provision is a welfare requirement under the five needs framework."
        ]
    },
    5519: {
        "title": "Research Sources and Standards",
        "intro": "This comprehensive guide draws on evidence from the following UK organisations and standards.",
        "sources": [
            "<strong>International Cat Care (iCatCare)</strong> — Their ‘Indoor Cat Guidance’ and ‘Creating an Indoor Environment for Cats’ publications provide the evidence base for environmental enrichment, litter tray management, and welfare monitoring.",
            "<strong>Cats Protection</strong> — The UK’s largest cat charity. Their ‘Essential Guide to Keeping Your Cat Happy Indoors’ covers space requirements, resource provision, and behavioural health for house cats.",
            "<strong>PDSA</strong> — Their annual PAW Report provides UK-specific data on indoor cat welfare, reporting that indoor cats are significantly more likely to be obese and under-stimulated than outdoor cats.",
            "<strong>British Veterinary Association (BVA)</strong> — Guidance on indoor cat nutrition, weight management, and preventive healthcare. Their position supports regular health checks for indoor cats every 6–12 months.",
            "<strong>Animal Welfare Act 2006</strong> — Establishes the legal framework for the five welfare needs that apply to all kept animals, including indoor cats: suitable environment, suitable diet, ability to exhibit normal behaviour, housing with or apart from other animals, and protection from pain and suffering."
        ]
    },
    5521: {
        "title": "Research Sources and Standards",
        "intro": "Health terminology and guidance in this article is informed by the following UK bodies.",
        "sources": [
            "<strong>Royal College of Veterinary Surgeons (RCVS)</strong> — The regulatory body for veterinary surgeons in the UK. Sets professional standards for veterinary practice and maintains the register of qualified veterinary professionals.",
            "<strong>British Veterinary Association (BVA)</strong> — Represents veterinary surgeons across the UK. Provides guidance on preventive healthcare, vaccination protocols, and evidence-based veterinary practice.",
            "<strong>PDSA</strong> — Their annual PAW Report provides comprehensive data on UK pet health trends, vaccination rates, parasite prevention, and the cost of veterinary care across the nation.",
            "<strong>Veterinary Poisons Information Service (VPIS)</strong> — The UK’s 24-hour toxicology advice service for veterinary professionals. The definitive resource for animal poisoning guidance.",
            "<strong>Animal Welfare Act 2006</strong> — The primary legislation governing animal welfare in England and Wales, establishing owners’ legal duty to meet five welfare needs including protection from pain, suffering, and disease."
        ]
    },
    5511: {
        "title": "Research Sources and Standards",
        "intro": "Enrichment guidance in this article draws on the following UK organisations and evidence.",
        "sources": [
            "<strong>International Cat Care (iCatCare)</strong> — Evidence-based guidance on feline environmental enrichment, including play, puzzle feeders, and social needs for cats at all life stages.",
            "<strong>Animal Behaviour and Training Council (ABTC)</strong> — The UK’s regulatory body for animal behaviour and training. Maintains a register of qualified animal behaviourists and sets evidence-based practice standards.",
            "<strong>PDSA</strong> — Their annual PAW Report provides data on enrichment practices in UK households, consistently finding that a significant proportion of pets do not receive adequate mental stimulation.",
            "<strong>Cats Protection and Dogs Trust</strong> — Both charities provide species-specific enrichment guidance based on behavioural science. Dogs Trust’s ‘Dog School’ programme promotes positive enrichment-based training.",
            "<strong>British Veterinary Association (BVA)</strong> — Supports enrichment as a core component of pet welfare and publishes guidance on the behavioural health benefits of structured play and mental stimulation."
        ]
    },
    5509: {
        "title": "Research Sources and Standards",
        "intro": "Safety guidance in this article is informed by the following UK standards and organisations.",
        "sources": [
            "<strong>BS EN 71 (Toy Safety Standard)</strong> — While primarily a children’s toy standard, its material safety and choking hazard principles provide useful safety benchmarks for pet toy assessment. No equivalent mandatory standard exists for pet toys in the UK.",
            "<strong>RSPCA</strong> — Guidance on toy safety under the Animal Welfare Act 2006, emphasising owners’ responsibility to provide safe enrichment and avoid toys that present ingestion or injury risks.",
            "<strong>British Veterinary Association (BVA)</strong> — Position on foreign body ingestion prevention and the importance of size-appropriate, durable toys as part of responsible pet ownership.",
            "<strong>Pet Industry Federation (PIF)</strong> — UK trade body that promotes product quality standards among member manufacturers and retailers, including guidance on pet toy materials and construction.",
            "<strong>Veterinary Poisons Information Service (VPIS)</strong> — Provides guidance on toxic materials that may be found in poorly manufactured toys, including certain dyes, coatings, and fillings."
        ]
    },
    5467: {
        "title": "Research Sources and Standards",
        "intro": "Feeding guidance in this article is informed by the following UK and European standards.",
        "sources": [
            "<strong>FEDIAF (European Pet Food Industry Federation)</strong> — Sets nutritional guidelines for complete and complementary pet food across Europe. FEDIAF compliance indicates a food meets evidence-based nutritional requirements for the stated species and life stage.",
            "<strong>PDSA</strong> — Their annual PAW Report provides data on UK pet feeding practices, consistently highlighting overfeeding and obesity as the most prevalent welfare concerns in companion animals.",
            "<strong>British Veterinary Association (BVA)</strong> — Guidance on pet nutrition, weight management, and the role of diet in preventive healthcare. BVA supports regular body condition scoring as standard veterinary practice.",
            "<strong>Pet Food Manufacturers’ Association (PFMA)</strong> — Provides UK-specific data on pet food labelling requirements, feeding guidelines, and nutritional standards for the UK market.",
            "<strong>Royal College of Veterinary Surgeons (RCVS)</strong> — Professional standards for veterinary nutrition advice, including guidance on prescription diets and nutritional management of chronic conditions."
        ]
    },
    5464: {
        "title": "Research Sources and Standards",
        "intro": "Grooming guidance in this article draws on the following UK organisations and standards.",
        "sources": [
            "<strong>City & Guilds (Level 2 and 3 Dog Grooming qualifications)</strong> — The recognised UK qualification standard for professional dog groomers. Level 3 indicates full competency in all breed grooming techniques.",
            "<strong>Pet Industry Federation (PIF)</strong> — Sets standards for professional grooming establishments in the UK, including hygiene, animal welfare, and practitioner qualifications.",
            "<strong>International Cat Care (iCatCare)</strong> — Guidance on cat-specific grooming needs, including coat care for different breeds, nail trimming, and dental hygiene as part of routine welfare management.",
            "<strong>British Veterinary Association (BVA)</strong> — Guidance on recognising skin conditions, parasite detection during grooming, and the role of regular grooming in preventive health monitoring.",
            "<strong>RSPCA</strong> — Welfare guidance on grooming as part of the five welfare needs, emphasising that regular grooming is a welfare responsibility and that severe matting constitutes neglect under the Animal Welfare Act 2006."
        ]
    },
    5460: {
        "title": "Research Sources and Standards",
        "intro": "Nutrition terminology and guidance in this article is informed by the following organisations and standards.",
        "sources": [
            "<strong>FEDIAF (European Pet Food Industry Federation)</strong> — The primary authority on pet food nutritional guidelines in Europe. Their nutritional guidelines, updated regularly, set minimum and maximum nutrient levels for complete pet foods.",
            "<strong>Pet Food Manufacturers’ Association (PFMA)</strong> — The UK trade body for pet food manufacturers. Provides guidance on UK labelling requirements, ingredient declarations, and analytical constituent reporting.",
            "<strong>Food Standards Agency (FSA)</strong> — Oversees the safety and standards of animal feed (including pet food) in the UK. Ensures pet food meets hygiene and safety regulations.",
            "<strong>British Veterinary Association (BVA)</strong> — Position statements on pet nutrition, including evidence-based guidance on raw feeding risks, the importance of complete diets, and nutritional management of chronic conditions.",
            "<strong>PDSA</strong> — Provides accessible, evidence-based nutrition guidance for pet owners, including label reading guides and dietary advice based on their annual PAW Report findings on UK pet feeding practices."
        ]
    },
}


# ══════════════════════════════════════════════════════════════════════
# HTML BLOCK BUILDERS
# ══════════════════════════════════════════════════════════════════════

def build_practical_guide_block(post_id):
    """Phase 10BK: Build Practical Guide HTML block with emerald styling."""
    data = PRACTICAL_GUIDES.get(post_id)
    if not data:
        return None

    steps_html = "\n".join(f"<li>{s}</li>" for s in data["steps"])

    return f'''
<div class="wp-block-group has-border-color has-background is-layout-constrained" style="border-color:#6ee7b7;border-width:2px;border-radius:6px;background-color:#ecfdf5;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<h4 class="wp-block-heading">{data["title"]}</h4>
<p class="wp-block-paragraph" style="font-size:14px">{data["intro"]}</p>
<ol class="wp-block-list" style="font-size:14px">
{steps_html}
</ol>
</div>
'''


def build_decision_pathway_block(post_id):
    """Phase 10BL: Build Decision Pathway HTML block with orange styling."""
    data = DECISION_PATHWAYS.get(post_id)
    if not data:
        return None

    paths_html = "\n".join(f"<li>{p}</li>" for p in data["paths"])

    return f'''
<div class="wp-block-group has-border-color has-background is-layout-constrained" style="border-color:#fdba74;border-width:2px;border-radius:6px;background-color:#fff7ed;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<h4 class="wp-block-heading">{data["title"]}</h4>
<p class="wp-block-paragraph" style="font-size:14px">{data["intro"]}</p>
<ul class="wp-block-list" style="font-size:14px">
{paths_html}
</ul>
</div>
'''


def build_trust_sources_block(post_id):
    """Phase 10BO: Build Research Sources HTML block with sky blue styling."""
    data = TRUST_SOURCES.get(post_id)
    if not data:
        return None

    sources_html = "\n".join(f"<li>{s}</li>" for s in data["sources"])

    return f'''
<div class="wp-block-group has-border-color has-background is-layout-constrained" style="border-color:#bae6fd;border-width:2px;border-radius:6px;background-color:#f0f9ff;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<h4 class="wp-block-heading">{data["title"]}</h4>
<p class="wp-block-paragraph" style="font-size:14px">{data["intro"]}</p>
<ul class="wp-block-list" style="font-size:14px">
{sources_html}
</ul>
</div>
'''


# ══════════════════════════════════════════════════════════════════════
# INSERTION LOGIC
# ══════════════════════════════════════════════════════════════════════

def find_insertion_point_before(content, marker):
    """Find the insertion point BEFORE a given section header/marker.
    Returns the position just before the <div> or <h4> containing the marker.
    """
    idx = content.lower().find(marker.lower())
    if idx < 0:
        return -1

    # Walk backwards to find the start of the containing div or heading
    search_start = max(0, idx - 500)
    segment = content[search_start:idx]

    # Look for the last <div that opens before this marker
    last_div = segment.rfind('<div ')
    last_h4 = segment.rfind('<h4 ')

    # Use whichever is closer (later in the text)
    candidates = []
    if last_div >= 0:
        candidates.append(search_start + last_div)
    if last_h4 >= 0:
        candidates.append(search_start + last_h4)

    if candidates:
        return max(candidates)
    return idx


def find_insertion_point_after(content, marker):
    """Find the insertion point AFTER a given section (after its closing </div>).
    Returns position after the closing </div> of the block containing the marker.
    """
    idx = content.lower().find(marker.lower())
    if idx < 0:
        return -1

    # Find the containing div start
    search_start = max(0, idx - 500)
    segment = content[search_start:idx]
    last_div_start = segment.rfind('<div ')

    if last_div_start < 0:
        # No containing div, look for closing after the marker
        close_idx = content.find('</div>', idx)
        if close_idx >= 0:
            return close_idx + len('</div>')
        return idx + len(marker)

    div_start = search_start + last_div_start

    # Count nested divs to find the matching close
    pos = div_start
    depth = 0
    while pos < len(content):
        next_open = content.find('<div', pos + 1)
        next_close = content.find('</div>', pos + 1)

        if next_close < 0:
            break

        if pos == div_start:
            depth = 1
            if next_open >= 0 and next_open < next_close:
                pos = next_open
                depth += 1
            else:
                pos = next_close
                depth -= 1
            continue

        if next_open >= 0 and next_open < next_close:
            depth += 1
            pos = next_open
        else:
            depth -= 1
            pos = next_close
            if depth <= 0:
                return pos + len('</div>')

    # Fallback
    close_idx = content.find('</div>', idx)
    if close_idx >= 0:
        return close_idx + len('</div>')
    return idx + 200


def insert_blocks(content, post_id):
    """Insert all three blocks into the post content at correct positions.

    INSERT ORDER:
    - Practical Guide BEFORE "How to Evaluate" (Evaluation Framework)
    - Decision Pathway AFTER "Which Option Suits Your Situation" (Scenario Guidance)
    - Research Sources AFTER Decision Pathway but BEFORE "Quick Checklist"
    """

    practical_block = build_practical_guide_block(post_id)
    decision_block = build_decision_pathway_block(post_id)
    trust_block = build_trust_sources_block(post_id)

    results = {"practical": False, "decision": False, "trust": False}

    # Check for already-existing blocks (idempotency)
    if 'Step-by-Step Practical Guide' in content:
        print(f"    [SKIP] Practical Guide already exists")
        practical_block = None
        results["practical"] = True  # Already present

    if 'Your Decision Pathway' in content:
        print(f"    [SKIP] Decision Pathway already exists")
        decision_block = None
        results["decision"] = True

    if 'Research Sources and Standards' in content:
        print(f"    [SKIP] Research Sources already exists")
        trust_block = None
        results["trust"] = True

    if not practical_block and not decision_block and not trust_block:
        return content, results

    # STEP 1: Insert Practical Guide BEFORE "How to Evaluate"
    if practical_block:
        # Try "How to Evaluate" first, then "Evaluation Framework"
        insert_pos = find_insertion_point_before(content, "How to Evaluate")
        if insert_pos < 0:
            insert_pos = find_insertion_point_before(content, "Evaluation Framework")
        if insert_pos < 0:
            # Fallback: before "Common Problems"
            insert_pos = find_insertion_point_before(content, "Common Problems")
        if insert_pos < 0:
            # Fallback: before "Quick Checklist"
            insert_pos = find_insertion_point_before(content, "Quick Checklist")
        if insert_pos < 0:
            # Last resort: before "Sources and Further Reading"
            insert_pos = find_insertion_point_before(content, "Sources and Further Reading")

        if insert_pos >= 0:
            content = content[:insert_pos] + practical_block + "\n" + content[insert_pos:]
            results["practical"] = True
            print(f"    [OK] Practical Guide inserted at position {insert_pos}")
        else:
            # Append before end
            content = content + practical_block
            results["practical"] = True
            print(f"    [OK] Practical Guide appended at end")

    # STEP 2: Insert Decision Pathway AFTER "Which Option Suits Your Situation"
    if decision_block:
        insert_pos = find_insertion_point_after(content, "Which Option Suits Your Situation")
        if insert_pos < 0:
            insert_pos = find_insertion_point_after(content, "Which Option Suits")
        if insert_pos < 0:
            # Fallback: after "Common Problems and Solutions"
            insert_pos = find_insertion_point_after(content, "Common Problems and Solutions")
        if insert_pos < 0:
            # Fallback: before Quick Checklist
            insert_pos = find_insertion_point_before(content, "Quick Checklist")

        if insert_pos >= 0:
            content = content[:insert_pos] + "\n" + decision_block + content[insert_pos:]
            results["decision"] = True
            print(f"    [OK] Decision Pathway inserted at position {insert_pos}")
        else:
            content = content + decision_block
            results["decision"] = True
            print(f"    [OK] Decision Pathway appended at end")

    # STEP 3: Insert Research Sources AFTER Decision Pathway but BEFORE Quick Checklist
    if trust_block:
        # Find "Your Decision Pathway" (just inserted) and insert after it
        dp_pos = content.find("Your Decision Pathway")
        if dp_pos >= 0:
            insert_pos = find_insertion_point_after(content, "Your Decision Pathway")
            if insert_pos >= 0:
                content = content[:insert_pos] + "\n" + trust_block + content[insert_pos:]
                results["trust"] = True
                print(f"    [OK] Research Sources inserted after Decision Pathway at {insert_pos}")
            else:
                # Fallback before Quick Checklist
                insert_pos = find_insertion_point_before(content, "Quick Checklist")
                if insert_pos >= 0:
                    content = content[:insert_pos] + trust_block + "\n" + content[insert_pos:]
                    results["trust"] = True
                    print(f"    [OK] Research Sources inserted before Quick Checklist at {insert_pos}")
                else:
                    content = content + trust_block
                    results["trust"] = True
                    print(f"    [OK] Research Sources appended at end")
        else:
            # No decision pathway found, insert before Quick Checklist
            insert_pos = find_insertion_point_before(content, "Quick Checklist")
            if insert_pos >= 0:
                content = content[:insert_pos] + trust_block + "\n" + content[insert_pos:]
                results["trust"] = True
                print(f"    [OK] Research Sources inserted before Quick Checklist at {insert_pos}")
            else:
                content = content + trust_block
                results["trust"] = True
                print(f"    [OK] Research Sources appended at end")

    return content, results


# ══════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ══════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("Phase 10BK/10BL/10BO Engine")
    print("Practical Guidance + Decision Support v3 + Trust Depth")
    print("=" * 70)
    print()

    csv_rows = []
    success_count = 0
    error_count = 0

    for post_id, cluster in ALL_POSTS.items():
        print(f"\n[{post_id}] Processing — Cluster: {cluster}")

        # Fetch post
        post = wp_api("GET", f"posts/{post_id}?context=edit")
        if not post or "content" not in post:
            print(f"  ERROR: Could not fetch post {post_id}")
            csv_rows.append({
                "id": post_id,
                "title": "FETCH ERROR",
                "cluster": cluster,
                "practical_guide_added": "error",
                "decision_pathway_added": "error",
                "trust_sources_added": "error",
                "status": "error"
            })
            error_count += 1
            continue

        title = post["title"]["raw"]
        content = post["content"]["raw"]
        print(f"  Title: {title}")
        print(f"  Content length: {len(content)} chars")

        # Check we have content for this post
        has_practical = post_id in PRACTICAL_GUIDES
        has_decision = post_id in DECISION_PATHWAYS
        has_trust = post_id in TRUST_SOURCES

        if not has_practical and not has_decision and not has_trust:
            print(f"  SKIP: No content defined for this post")
            csv_rows.append({
                "id": post_id,
                "title": title,
                "cluster": cluster,
                "practical_guide_added": "no_content",
                "decision_pathway_added": "no_content",
                "trust_sources_added": "no_content",
                "status": "skipped"
            })
            continue

        # Insert blocks
        new_content, results = insert_blocks(content, post_id)

        if new_content == content:
            print(f"  No changes needed (all blocks already present or no insertion points)")
            csv_rows.append({
                "id": post_id,
                "title": title,
                "cluster": cluster,
                "practical_guide_added": "already_present" if results["practical"] else "not_applicable",
                "decision_pathway_added": "already_present" if results["decision"] else "not_applicable",
                "trust_sources_added": "already_present" if results["trust"] else "not_applicable",
                "status": "no_change"
            })
            continue

        # Update post
        print(f"  Updating post... (new length: {len(new_content)} chars, delta: +{len(new_content) - len(content)} chars)")

        update_result = wp_api("POST", f"posts/{post_id}", {"content": new_content})

        if update_result and "id" in update_result:
            print(f"  SUCCESS: Post {post_id} updated")
            success_count += 1
            csv_rows.append({
                "id": post_id,
                "title": title,
                "cluster": cluster,
                "practical_guide_added": "yes" if results["practical"] else "not_applicable",
                "decision_pathway_added": "yes" if results["decision"] else "not_applicable",
                "trust_sources_added": "yes" if results["trust"] else "not_applicable",
                "status": "updated"
            })
        else:
            error_msg = update_result.get("message", "Unknown error") if update_result else "No response"
            print(f"  ERROR updating: {error_msg}")
            error_count += 1
            csv_rows.append({
                "id": post_id,
                "title": title,
                "cluster": cluster,
                "practical_guide_added": "error",
                "decision_pathway_added": "error",
                "trust_sources_added": "error",
                "status": f"error: {error_msg[:50]}"
            })

        # Rate limit
        time.sleep(2)

    # Write CSV
    print(f"\n{'=' * 70}")
    print(f"Writing CSV to {CSV_PATH}")
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "title", "cluster",
            "practical_guide_added", "decision_pathway_added", "trust_sources_added",
            "status"
        ])
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"CSV written: {len(csv_rows)} rows")

    # Summary
    print(f"\n{'=' * 70}")
    print(f"SUMMARY")
    print(f"  Total posts processed: {len(ALL_POSTS)}")
    print(f"  Successful updates: {success_count}")
    print(f"  Errors: {error_count}")
    print(f"  No change needed: {len(ALL_POSTS) - success_count - error_count}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
