#!/usr/bin/env python3
"""
Phase 10BK/10BM/10BN/10BO Engine for pethubonline.com
Clusters: Dog Food (1467), Educational (dog care/health/puppy), Dog Training (1474)

Phase 10BK: Practical Guidance Dominance — Add step-by-step practical guide blocks
Phase 10BM: Citation Confidence Sprint — Add UK authority references
Phase 10BN: Comparison Dominance — Add comparison tables
Phase 10BO: Trust Depth — Add Research Sources and Standards blocks
"""

import subprocess
import json
import re
import csv
import os
import sys
import time
import html
import tempfile

# ─── Configuration ───────────────────────────────────────────────────────────
WP_API = "https://pethubonline.com/wp-json/wp/v2"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
CSV_PATH = "/var/lib/freelancer/projects/40416335/phase10bk_data/practical_citation_dogfood_edu_training.csv"

# ─── API Helpers ─────────────────────────────────────────────────────────────
def wp_get(endpoint, params=None):
    """GET request to WP REST API."""
    url = f"{WP_API}/{endpoint}"
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", f"{WP_USER}:{WP_PASS}", url],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)


def wp_update_post(post_id, content):
    """Update post content via WP REST API using temp file for large payloads."""
    payload = json.dumps({"content": content})
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(payload)
        tmp_path = f.name
    try:
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-X", "POST",
             "-u", f"{WP_USER}:{WP_PASS}",
             "-H", "Content-Type: application/json",
             "-d", f"@{tmp_path}",
             f"{WP_API}/posts/{post_id}"],
            capture_output=True, text=True, timeout=60
        )
        resp = json.loads(result.stdout)
        if "id" in resp:
            return True, resp["id"]
        else:
            return False, resp.get("message", "Unknown error")
    except Exception as e:
        return False, str(e)
    finally:
        os.unlink(tmp_path)


# ─── Fetch All Target Posts ─────────────────────────────────────────────────
def fetch_cluster_posts():
    """Fetch posts for all 3 clusters and return categorised dict."""
    clusters = {}

    # Dog Food (category 1467)
    posts = wp_get("posts", {"categories": "1467", "per_page": "50",
                             "_fields": "id,title,slug,categories", "context": "edit"})
    clusters["Dog Food"] = [(p["id"], p["title"]["raw"], p["categories"]) for p in posts]

    # Dog Training / Training Supplies (category 1474)
    posts = wp_get("posts", {"categories": "1474", "per_page": "50",
                             "_fields": "id,title,slug,categories", "context": "edit"})
    clusters["Dog Training"] = [(p["id"], p["title"]["raw"], p["categories"]) for p in posts]

    # Educational: Dog Care (1489) + Puppy Care (1442) + Dog Health (1450)
    # excluding posts already in Dog Food or Training clusters
    dog_food_ids = {p[0] for p in clusters["Dog Food"]}
    training_ids = {p[0] for p in clusters["Dog Training"]}
    exclude = dog_food_ids | training_ids

    edu_posts = {}
    for cat_id in [1489, 1442, 1450]:
        posts = wp_get("posts", {"categories": str(cat_id), "per_page": "50",
                                 "_fields": "id,title,slug,categories", "context": "edit"})
        for p in posts:
            pid = p["id"]
            if pid not in exclude and pid not in edu_posts:
                edu_posts[pid] = (pid, p["title"]["raw"], p["categories"])
    clusters["Educational"] = list(edu_posts.values())

    return clusters


# ─── Block Generators ────────────────────────────────────────────────────────

def make_group_block(bg_colour, border_colour, heading, inner_html):
    """Create a styled wp:group block."""
    return (
        f'<!-- wp:group {{"style":{{"color":{{"background":"{bg_colour}"}},'
        f'"border":{{"radius":"6px","width":"1px","color":"{border_colour}"}},'
        f'"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},'
        f'"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->\n'
        f'<div class="wp-block-group has-border-color has-background" style="border-color:{border_colour};border-width:1px;border-radius:6px;background-color:{bg_colour};margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        f'<!-- wp:heading {{"level":4}} --><h4 class="wp-block-heading">{heading}</h4><!-- /wp:heading -->\n'
        f'{inner_html}\n'
        f'</div>\n<!-- /wp:group -->'
    )


def make_table_block(headers, rows, caption=""):
    """Create a wp:table is-style-stripes block."""
    thead = "<thead><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr></thead>"
    tbody_rows = ""
    for row in rows:
        tbody_rows += "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
    tbody = f"<tbody>{tbody_rows}</tbody>"
    cap = f'<figcaption class="wp-element-caption">{caption}</figcaption>' if caption else ""
    return (
        f'<!-- wp:table {{"className":"is-style-stripes"}} -->\n'
        f'<figure class="wp-block-table is-style-stripes"><table>{thead}{tbody}</table>{cap}</figure>\n'
        f'<!-- /wp:table -->'
    )


def make_list_block(items, ordered=False):
    """Create a wp:list block."""
    tag = "ol" if ordered else "ul"
    attr = ' {"ordered":true}' if ordered else ''
    lis = "".join(f"<li>{item}</li>" for item in items)
    return (
        f'<!-- wp:list{attr} --><{tag} class="wp-block-list">{lis}</{tag}><!-- /wp:list -->'
    )


# ─── Content Generators by Post ─────────────────────────────────────────────

# ══════════════════════════════════════════════════════════════════════════════
# PRACTICAL GUIDE CONTENT (Phase 10BK) — Rich, specific, measurable
# ══════════════════════════════════════════════════════════════════════════════

PRACTICAL_GUIDES = {
    # ─── DOG FOOD CLUSTER ────────────────────────────────────────────────
    7172: {  # Dog Food Glossary
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Check the label declaration</strong> — Look for the word 'complete' (not 'complementary'). Under The Animal Feed (England) Regulations 2010, only complete foods can serve as a sole diet. Budget complete foods start from approximately £15–£25 per 12kg bag.",
            "<strong>Step 2: Identify the primary protein source</strong> — The first ingredient should be a named animal protein (e.g., 'chicken 26%'). FEDIAF nutritional guidelines recommend a minimum of 18% crude protein for adult maintenance and 25% for growth.",
            "<strong>Step 3: Calculate daily feeding amounts</strong> — A 10kg dog typically needs 150–200g of dry food daily; a 25kg Labrador needs 300–400g daily; a 40kg German Shepherd needs 400–550g daily. Always weigh portions with a kitchen scale accurate to ±5g.",
            "<strong>Step 4: Assess the analytical constituents panel</strong> — Compare crude protein (target 22–28% for adults), crude fat (10–16%), crude fibre (2–5%), and ash (below 8%). Higher ash may indicate lower-quality mineral sources.",
            "<strong>Step 5: Verify FEDIAF compliance</strong> — Check the packaging states compliance with FEDIAF guidelines. In the UK, PFMA members must adhere to the PFMA Code of Practice, which requires FEDIAF nutritional compliance.",
            "<strong>Step 6: Evaluate cost per day rather than per bag</strong> — A £60 premium 12kg bag feeding 300g/day lasts 40 days (£1.50/day). A £25 budget 15kg bag feeding 400g/day lasts 37.5 days (£0.67/day). Mid-range typically costs £0.90–£1.20 per day for a medium breed.",
            "<strong>Step 7: Transition to new food gradually</strong> — Days 1–2: 75% old / 25% new. Days 3–4: 50/50. Days 5–7: 25% old / 75% new. Days 8–10: 100% new. Monitor stool consistency throughout; firm stools indicate good tolerance.",
            "<strong>Step 8: Adjust portions seasonally</strong> — In UK winter months (November–February), active outdoor dogs may need 10–15% more calories. In summer (June–August), reduce by 5–10% if activity decreases. Weigh your dog monthly.",
            "<strong>Step 9: Store food correctly</strong> — Dry kibble should be stored in an airtight container at below 25°C. Once opened, use within 6 weeks. Wet food should be refrigerated at 2–5°C and used within 48 hours of opening.",
            "<strong>Step 10: Schedule a weight check every 4 weeks</strong> — Use body condition scoring (BCS) on a 1–9 scale; ideal is 4–5. You should feel ribs without pressing hard, see a visible waist from above, and notice a tummy tuck from the side.",
            "<strong>Breed-specific note for brachycephalic breeds</strong> — Pugs, Bulldogs, and French Bulldogs benefit from elevated bowls at 10–15cm height and smaller kibble size (8–10mm) to reduce air ingestion and choking risk.",
            "<strong>Age-specific note for senior dogs (7+ years)</strong> — Consider foods with added glucosamine (minimum 300mg/kg) and chondroitin (minimum 200mg/kg) for joint support. Reduce phosphorus content to below 1% to support kidney function. Consult your vet for breed-specific senior transition timing.",
        ]
    },
    3836: {  # Best Dog Food UK – Complete Buying Guide
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Determine your dog's daily calorie needs</strong> — Use the formula: Resting Energy Requirement (RER) = 70 × (body weight in kg)^0.75. Multiply by 1.6 for an active adult, 1.2 for a sedentary or senior dog. A 25kg active dog needs approximately 1,100–1,200 kcal/day.",
            "<strong>Step 2: Match food type to lifestyle</strong> — Dry kibble (£0.60–£1.50/day for medium breeds) suits most households. Wet food (£1.50–£3.00/day) benefits dogs with dental issues or low water intake. Raw feeding (£2.00–£4.00/day) requires careful PFMA-compliant sourcing and a -18°C freezer.",
            "<strong>Step 3: Read the ingredient declaration correctly</strong> — Under UK feed labelling law, ingredients must be listed in descending order by weight. Fresh meat at 30% will appear high but contains ~70% water, reducing its dry-matter contribution significantly.",
            "<strong>Step 4: Compare protein on a dry-matter basis</strong> — For wet food at 75% moisture: divide protein percentage by 0.25. A wet food at 10% protein = 40% protein dry-matter. For dry food at 10% moisture: divide by 0.90. A dry food at 26% protein = 28.9% dry-matter.",
            "<strong>Step 5: Budget by breed size</strong> — Small breeds (under 10kg): £20–£35/month. Medium breeds (10–25kg): £30–£55/month. Large breeds (25–45kg): £45–£75/month. Giant breeds (45kg+): £65–£100+/month. These reflect mid-range quality dry food.",
            "<strong>Step 6: Check for PFMA membership</strong> — The Pet Food Manufacturers' Association represents over 90% of the UK pet food market. Members adhere to the PFMA Code of Practice and FEDIAF nutritional standards, providing an additional quality assurance layer.",
            "<strong>Step 7: Set a consistent feeding schedule</strong> — Adults: 2 meals per day at 12-hour intervals (e.g., 7:00 AM and 7:00 PM). Puppies under 4 months: 4 meals. Puppies 4–6 months: 3 meals. Remove uneaten food after 20 minutes to establish routine.",
            "<strong>Step 8: Monitor and adjust over 8 weeks</strong> — After switching food, allow a full 8-week trial before judging suitability. Track coat condition, energy levels, stool quality (score 2–3 on a 1–7 faecal scoring chart is ideal), and body weight weekly.",
            "<strong>Step 9: Seasonal feeding adjustments for the UK climate</strong> — During wet, cold months (October–March), working and outdoor dogs may need up to 20% more calories. During warmer months, ensure fresh water is always available; dehydration can reduce appetite.",
            "<strong>Step 10: Plan for life-stage transitions</strong> — Transition from puppy to adult food at 12 months for small/medium breeds, 15–18 months for large breeds, and 18–24 months for giant breeds. Transition to senior food at 7 years for most breeds, 5–6 years for giant breeds.",
            "<strong>Breed-specific note</strong> — Deep-chested breeds (Great Danes, Setters, Weimaraners) should be fed 2–3 smaller meals rather than one large meal to reduce bloat risk. Avoid exercise for 60 minutes after feeding.",
            "<strong>Temperature note</strong> — Serve wet food at room temperature (18–22°C); cold food straight from the fridge can cause digestive discomfort. Microwave in 10-second bursts if needed, stirring to eliminate hot spots."
        ]
    },
    3837: {  # Best Dry Dog Food UK
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Choose kibble size appropriate to your dog</strong> — Small breeds (under 10kg): 5–8mm kibble. Medium breeds (10–25kg): 10–14mm. Large breeds (25kg+): 14–20mm. Brachycephalic breeds benefit from flat or pillow-shaped kibble for easier pick-up.",
            "<strong>Step 2: Check the guaranteed analysis</strong> — For adult maintenance, target: crude protein 22–28%, crude fat 10–16%, crude fibre 2–5%, moisture below 10%. Higher protein (28–32%) for working dogs; moderate protein (20–24%) with reduced phosphorus for seniors.",
            "<strong>Step 3: Calculate your monthly cost</strong> — A 12kg bag at £40 feeding a 20kg dog at 250g/day lasts 48 days = £25/month. A 15kg bag at £55 feeding a 30kg dog at 350g/day lasts 43 days = £38/month. Always calculate cost-per-day for fair comparison.",
            "<strong>Step 4: Establish correct portion sizes by weight</strong> — Toy breeds (2–5kg): 40–100g/day. Small breeds (5–10kg): 100–180g/day. Medium breeds (10–25kg): 180–350g/day. Large breeds (25–40kg): 350–500g/day. Giant breeds (40kg+): 500–700g/day. Adjust ±10% based on activity level.",
            "<strong>Step 5: Test palatability over 5 days</strong> — Offer the new kibble mixed at 25% with current food. If your dog consistently picks out or avoids the new kibble, try a different protein source. Most dogs accept chicken or salmon readily; lamb and duck suit fussier eaters.",
            "<strong>Step 6: Store correctly to maintain freshness</strong> — Transfer to an airtight container or keep in the original bag sealed with a clip inside a container. Store in a cool, dry place below 25°C. Use within 6 weeks of opening. In the UK, kitchen cupboards away from the cooker are ideal.",
            "<strong>Step 7: Hydrate kibble for specific needs</strong> — For puppies under 8 weeks: soak kibble in warm (not boiling) water for 10–15 minutes until soft. For senior dogs with dental issues: add 2–3 tablespoons of warm water and let stand 5 minutes. This also releases aroma for fussy eaters.",
            "<strong>Step 8: Combine with wet food if needed</strong> — A 75/25 dry-to-wet ratio by weight provides dental benefits of kibble with palatability of wet food. Reduce dry portion by 25% to avoid overfeeding. Example: for a 20kg dog, use 190g dry + 65g wet instead of 250g dry.",
            "<strong>Step 9: Monitor dental health alongside dry feeding</strong> — Dry kibble provides some mechanical cleaning but is not a substitute for dental care. Brush teeth at least 3 times per week using an enzymatic dog toothpaste. Schedule a professional veterinary dental check annually (typical UK cost: £150–£300).",
            "<strong>Step 10: Review and rotate proteins every 3–6 months</strong> — Rotating between 2–3 protein sources (e.g., chicken, fish, lamb) may help prevent food sensitivities developing. Always transition over 7–10 days when switching flavours, even within the same brand.",
            "<strong>UK seasonal note</strong> — During damp UK autumn and winter, ensure kibble storage areas are not prone to condensation. Moisture ingress causes mould growth, making food unsafe. Check stored kibble weekly for unusual smell or discolouration.",
            "<strong>Puppy-specific guidance</strong> — Puppy dry food should contain DHA (minimum 0.05% of diet) for brain and eye development, and calcium at 0.8–1.2% for small breeds or 0.8–1.0% for large breed puppies to prevent developmental orthopaedic disease."
        ]
    },
    3838: {  # Dry vs Wet Dog Food UK
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Assess your dog's hydration status</strong> — Dogs should drink 40–60ml of water per kg of body weight daily. If your dog drinks less than this, wet food (70–85% moisture) can supplement hydration. A 20kg dog on dry food needs 800–1,200ml water daily; on wet food, water intake from food alone may cover 400–600ml.",
            "<strong>Step 2: Compare nutritional content on a dry-matter basis</strong> — Wet food at 8% protein and 80% moisture = 40% protein dry-matter. Dry food at 24% protein and 8% moisture = 26% protein dry-matter. Always convert before comparing to avoid misleading conclusions.",
            "<strong>Step 3: Calculate the true cost difference</strong> — Dry food for a 25kg dog: approximately £1.00–£1.80/day (mid-range). Wet food for the same dog: approximately £2.50–£4.50/day. Mixed feeding (50/50): approximately £1.75–£3.00/day. Factor in waste — wet food has a 48-hour refrigerator shelf life once opened.",
            "<strong>Step 4: Match food type to dental health needs</strong> — Dry kibble provides mild abrasive action on teeth surfaces. However, the BVDA (British Veterinary Dental Association) notes this is not a substitute for brushing. Dogs with missing teeth, gum disease, or oral pain may find wet food easier to manage.",
            "<strong>Step 5: Choose based on life stage</strong> — Puppies (weaning to 8 weeks): wet or soaked dry for easy consumption. Adult dogs: dry, wet, or mixed based on preference. Senior dogs (7+ years): wet food or hydrated kibble if dental issues present. Pregnant/nursing dogs: energy-dense wet food to meet 1.5–2× normal calorie requirements.",
            "<strong>Step 6: Establish correct portions for mixed feeding</strong> — If adding wet food to dry, reduce dry by the caloric equivalent. Example: replacing 100g of dry food (350 kcal) requires approximately 350g of wet food (100 kcal/100g). Use the feeding guides on both products and adjust proportionally.",
            "<strong>Step 7: Store each type appropriately</strong> — Dry: airtight container, below 25°C, use within 6 weeks. Wet (opened): covered in fridge at 2–5°C, use within 48 hours. Wet (unopened): store in a cool pantry; check best-before dates. Never leave wet food in the bowl for more than 4 hours at room temperature.",
            "<strong>Step 8: Trial each format for 4 weeks before deciding</strong> — Monitor stool quality (firm, dark brown, low odour is ideal), coat shine, energy levels, and weight. Record findings weekly. If loose stools persist beyond 10 days, the format may not suit your dog's digestion.",
            "<strong>Step 9: Consider environmental and waste factors</strong> — Dry food pouches/bags generate less waste than individual wet food tins. Wet food tins are recyclable via UK kerbside collection. Pouches (typically foil-lined plastic) are harder to recycle — check local council recycling guidance.",
            "<strong>Step 10: Adjust for the UK climate</strong> — In summer months (June–August), wet food spoils faster; reduce bowl portions and refresh more often. In winter (November–February), slightly warming wet food (to 20–25°C) can increase palatability and aroma.",
            "<strong>Breed-specific note</strong> — Flat-faced breeds (Pugs, Bulldogs, Shih Tzus) often find wet food or pâté textures easier to eat due to their jaw structure. Serve in shallow, wide bowls (minimum 15cm diameter, maximum 3cm depth) to reduce facial contact with food.",
            "<strong>Budget planning tip</strong> — Mixed feeding offers a middle ground: base diet of dry kibble (£0.80–£1.20/day) topped with 1–2 tablespoons of wet food for palatability (£0.30–£0.60/day), totalling £1.10–£1.80/day for a medium breed."
        ]
    },
    3839: {  # Best Puppy Food UK
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Start with breed-appropriate puppy food from day one</strong> — Small breed puppies need higher calorie density (approximately 400 kcal/100g) due to faster metabolism. Large breed puppies need controlled calcium (0.8–1.0%) and moderate calories to prevent too-rapid growth. Always select food labelled 'complete for growth' meeting FEDIAF guidelines.",
            "<strong>Step 2: Set the correct meal frequency by age</strong> — 8–12 weeks: 4 meals daily at 6-hour intervals. 3–6 months: 3 meals daily at 8-hour intervals. 6–12 months: 2–3 meals daily. 12+ months (small/medium) or 18+ months (large breeds): transition to 2 meals daily.",
            "<strong>Step 3: Calculate daily portions by expected adult weight</strong> — Puppies need 2–3× the calories per kg of an adult dog. A puppy with expected adult weight of 10kg needs approximately 400–550 kcal/day at 4 months. A puppy expected to reach 30kg needs approximately 900–1,200 kcal/day at 4 months. Use the manufacturer's growth chart and adjust monthly.",
            "<strong>Step 4: Weigh your puppy weekly</strong> — Use a bathroom scale (hold puppy and subtract your weight) or visit your vet's free nurse clinics. Small breeds should gain 5–10g per day per kg of expected adult weight. Large breeds should gain 2–4g per day per kg of expected adult weight. Plot on a growth curve chart.",
            "<strong>Step 5: Introduce the food your breeder was using first</strong> — Maintain the breeder's food for at least 2 weeks after bringing puppy home to reduce digestive stress. Then transition to your chosen food over 7–10 days using the 75/50/25 method.",
            "<strong>Step 6: Check protein and DHA levels</strong> — FEDIAF recommends minimum 25% crude protein for growth. DHA (docosahexaenoic acid) at 0.05%+ supports brain and vision development. Look for fish oil, salmon oil, or algal DHA in the ingredients list.",
            "<strong>Step 7: Budget for the puppy year</strong> — Small breed puppy food: approximately £20–£35/month. Medium breed: £30–£50/month. Large breed: £40–£65/month. These costs increase as the puppy grows — a Labrador at 6 months eats roughly twice what it did at 3 months.",
            "<strong>Step 8: Use treats wisely during training</strong> — Training treats should not exceed 10% of daily calorie intake. For a puppy eating 600 kcal/day, that is a maximum of 60 kcal in treats (roughly 15–20 small training treats). Deduct treat calories from meal portions to prevent overfeeding.",
            "<strong>Step 9: Recognise signs that food needs changing</strong> — Persistent loose stools beyond 10 days of transition, excessive flatulence, dull coat, or slow weight gain may indicate the food does not suit your puppy. Consult your vet before switching; they may recommend an elimination diet.",
            "<strong>Step 10: Plan the transition to adult food</strong> — Small breeds: transition at 10–12 months. Medium breeds: 12–14 months. Large breeds: 15–18 months. Giant breeds: 18–24 months. Transition gradually over 10–14 days. Monitor weight closely during the switch — adult food is less calorie-dense.",
            "<strong>Large breed puppy warning</strong> — Overfeeding large breed puppies accelerates growth and increases the risk of developmental orthopaedic disease (DOD). Maintain a lean body condition (BCS 4/9). Calcium should not exceed 1.0% for large breed puppy food, per FEDIAF guidelines.",
            "<strong>UK-specific note</strong> — The PFMA advises that all puppy food sold in the UK must be labelled with feeding guidelines by body weight. If guidelines are missing from the packaging, the product may not comply with The Animal Feed (England) Regulations 2010."
        ]
    },

    # ─── DOG TRAINING CLUSTER ────────────────────────────────────────────
    4118: {  # Best Dog Training and Behaviour UK – Complete Guide
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Establish a daily training schedule</strong> — Train 2–3 times per day in sessions of 5–10 minutes each. Puppies under 6 months: maximum 5 minutes per session. Adult dogs: up to 15 minutes. Schedule sessions before meals when motivation is highest.",
            "<strong>Step 2: Choose your primary reward type</strong> — High-value treats (small, soft, smelly) at approximately £2–£5 per 100g training treat bag. Low-value treats (kibble from daily ration) for easy tasks. Toy rewards for play-motivated breeds (e.g., Collies, Spaniels). Verbal praise alone is insufficient for most dogs during initial learning.",
            "<strong>Step 3: Master the five foundation behaviours in order</strong> — Week 1–2: 'Sit' (lure from nose upward). Week 2–3: 'Down' (lure from nose to floor). Week 3–4: 'Stay' (build from 2 seconds to 30 seconds). Week 4–6: 'Come' (recall on 3m lead, then 5m, then 10m). Week 6–8: 'Leave it' (food on floor, reward from hand).",
            "<strong>Step 4: Set up the training environment</strong> — Start in a quiet room with no distractions. Gradually add distractions: another person, then a toy on the floor, then practise outdoors in a quiet garden, then a low-traffic park. Each environment change may temporarily reduce reliability by 50% — this is normal.",
            "<strong>Step 5: Use a consistent marker signal</strong> — A clicker (£2–£4 from pet shops) or a consistent verbal marker ('Yes!') delivered within 0.5–1.0 seconds of the desired behaviour. The marker must always be followed by a reward to maintain its association.",
            "<strong>Step 6: Address pulling on the lead systematically</strong> — Use a front-clip harness (£15–£30) to reduce pulling force. Stop walking when the lead goes tight. Wait for your dog to look at you or create slack. Reward and continue. Expect 3–6 weeks of consistent practice for noticeable improvement.",
            "<strong>Step 7: Socialise your puppy during the critical window</strong> — Between 3 and 14 weeks of age, expose your puppy to at least 100 novel experiences: 10+ different surface types, 10+ different people (varied age, appearance), 5+ other vaccinated dogs, 5+ different environments. Record exposures on a socialisation checklist.",
            "<strong>Step 8: Manage unwanted behaviours without punishment</strong> — For jumping up: turn away, wait for four paws on the floor, then reward. For mouthing: redirect to a toy, then praise. For barking: identify the trigger, remove or manage it, reward quiet behaviour. Physical corrections (alpha rolls, scruff shakes) are condemned by the APBC and ABTC as counterproductive.",
            "<strong>Step 9: Budget for professional help when needed</strong> — Group puppy classes: £40–£80 for a 6-week course. One-to-one behavioural consultation: £80–£200 per session. Always check the trainer is accredited by the ABTC (Animal Behaviour and Training Council), the UK's regulatory body for animal behaviourists and trainers.",
            "<strong>Step 10: Maintain behaviours with a reinforcement schedule</strong> — After a behaviour is learned (>80% reliability), switch from continuous reward to a variable ratio — reward every 2nd, then 3rd, then randomly. This mirrors how slot machines maintain behaviour and makes training more resilient.",
            "<strong>Breed-specific note</strong> — Herding breeds (Collies, Shepherds) need more mental stimulation — add puzzle feeders (£8–£15) and scent work. Terriers may need extra impulse control training. Sighthounds (Greyhounds, Whippets) often have lower food motivation — try toy-based rewards.",
            "<strong>UK seasonal training note</strong> — During UK winter (November–February), daylight hours are limited. Use reflective gear and well-lit areas for outdoor training. Summer (June–August): avoid training on hot tarmac — test with your hand for 5 seconds; if it is too hot for your hand, it is too hot for paws."
        ]
    },
    4125: {  # Best Dog Training Treats UK – Reward Guide
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Calculate your dog's daily treat allowance</strong> — Treats should not exceed 10% of total daily calorie intake. A 15kg dog eating 800 kcal/day has a 80 kcal treat budget. Most training treats are 3–5 kcal each, allowing 16–27 treats per training day. Deduct equivalent calories from meals.",
            "<strong>Step 2: Classify treats into three value tiers</strong> — Low value (kibble, carrot sticks): for easy, well-known behaviours. Medium value (commercial training treats, £2–£4/100g): for proofing behaviours in new environments. High value (cheese cubes, cooked chicken, liver paste at £3–£6/100g): for difficult behaviours or high-distraction situations.",
            "<strong>Step 3: Prepare treats to the correct size</strong> — Training treats should be pea-sized (approximately 1cm cubes) to allow rapid consumption without breaking focus. For a 20-minute training session, prepare 30–40 pieces. Pre-cut and store in a treat pouch (£5–£10) worn at waist height.",
            "<strong>Step 4: Select treats based on your dog's dietary needs</strong> — For dogs with grain sensitivities: single-protein dried treats (e.g., 100% chicken breast, £4–£7/100g). For overweight dogs: low-calorie options under 3 kcal per treat (e.g., dried sprats, air-dried lung). For puppies: soft, easily chewed treats with no artificial colours or preservatives.",
            "<strong>Step 5: Rotate treats to maintain novelty</strong> — Keep 3–4 different treat types available. Introduce a new treat every 2–3 weeks and retire one temporarily. Novel treats act as higher-value rewards without increasing calorie content. Dogs habituate to familiar treats after 2–3 weeks of daily use.",
            "<strong>Step 6: Use natural alternatives from your kitchen</strong> — Cooked chicken breast: cut into 1cm cubes, approximately 1.5 kcal each. Cheese (mild cheddar): 1cm cubes, approximately 4 kcal each — use sparingly. Carrot sticks: virtually zero calories, good for low-value rewards. Blueberries: 1 kcal each, antioxidant-rich. Avoid grapes, onions, chocolate, xylitol-sweetened products.",
            "<strong>Step 7: Time your treat delivery correctly</strong> — Deliver the treat within 1–2 seconds of the desired behaviour (or after the clicker/marker). Late delivery (beyond 3 seconds) creates confusion about which behaviour earned the reward. Practice your timing without the dog first — click, then reach for treat, aim for under 2 seconds total.",
            "<strong>Step 8: Store treats safely</strong> — Opened commercial treats: reseal and store in a cool, dry cupboard; use within the timeframe on the packet (typically 4–8 weeks). Fresh treats (chicken, cheese): refrigerate at 2–5°C; use within 3 days. Freeze batches of homemade treats in portions for up to 3 months.",
            "<strong>Step 9: Monitor for adverse reactions</strong> — When introducing any new treat, give 2–3 pieces and wait 24 hours. Watch for itching, loose stools, vomiting, or lethargy. Novel protein treats (venison, duck, fish) are less likely to trigger reactions in dogs with suspected food sensitivities.",
            "<strong>Step 10: Budget for monthly training treats</strong> — Light training (pet dogs, maintenance): £5–£10/month. Active training (puppy classes, new behaviours): £10–£20/month. Intensive training (behaviour modification, competition): £15–£30/month. Homemade treats (boiled chicken, liver cake) can reduce costs by 50–60%.",
            "<strong>Breed-specific note</strong> — Breeds prone to weight gain (Labradors, Beagles, Cavalier King Charles Spaniels) need strict calorie accounting. Use their daily kibble ration as low-value treats and reserve commercial treats for difficult tasks only.",
            "<strong>Puppy-specific note</strong> — Puppies under 12 weeks have small stomachs — reduce treat size to 0.5cm cubes. Use soft treats that do not require extensive chewing. Avoid rawhide and hard chews until adult teeth are fully erupted (typically 6–7 months)."
        ]
    },
    4132: {  # Best Puppy Training Guide UK – First Year Essentials
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Begin socialisation immediately (8–14 weeks)</strong> — This is the critical socialisation window identified by veterinary behaviourists. Aim for 3–5 new positive experiences daily: different people, surfaces (grass, gravel, metal grates, carpet), sounds (traffic, doorbells, vacuum cleaners), and locations. Carry your puppy to public places before vaccinations are complete.",
            "<strong>Step 2: Establish a toilet training routine</strong> — Take puppy outside every 1–2 hours, immediately after waking, after eating (within 15 minutes), and after play sessions. Choose one toilet area in the garden and always use it. Praise and treat within 2 seconds of successful elimination outdoors. Expect full reliability by 4–6 months; large breeds may take until 6–8 months.",
            "<strong>Step 3: Introduce crate training gradually</strong> — Day 1–3: door open, treats tossed inside, no closing. Day 4–7: close door for 30 seconds to 2 minutes while puppy eats. Week 2: increase to 10–15 minutes. Week 3–4: up to 1 hour during the day. Never exceed the puppy's age in months + 1 hour (e.g., 3-month puppy = max 4 hours). Crates cost approximately £30–£60 for medium size.",
            "<strong>Step 4: Teach bite inhibition before 18 weeks</strong> — When puppy bites too hard, say 'ouch' in a high-pitched voice and withdraw attention for 15–30 seconds. Resume play. Repeat consistently. Puppies should learn to mouth gently by 14 weeks and stop mouthing hands entirely by 18–20 weeks.",
            "<strong>Step 5: Start lead training indoors at 8–10 weeks</strong> — Let puppy wear a lightweight collar (£5–£10) and drag a light lead (1.5m, £8–£12) in the house under supervision. Reward following you. First outdoor walks after second vaccination: 5 minutes per month of age (e.g., 3 months = 15 minutes). Gradually extend by 5 minutes per week.",
            "<strong>Step 6: Enrol in a puppy class by 12 weeks</strong> — Look for ABTC-registered trainers or Kennel Club Good Citizen scheme classes. Typical cost: £40–£80 for a 6-week course in the UK. Classes should be small (maximum 6–8 puppies), positive-reinforcement only, and held on clean, disinfected flooring.",
            "<strong>Step 7: Build alone-time tolerance gradually</strong> — Week 1: leave puppy in a safe area for 30 seconds while in another room. Increase by 30-second increments daily. By 4 months: aim for 30 minutes alone. By 6 months: 1–2 hours. Never leave a puppy under 6 months alone for more than 3 hours.",
            "<strong>Step 8: Establish handling exercises daily</strong> — Handle ears, paws, mouth, and tail for 30 seconds each, pairing with treats. This prepares for vet visits (average UK consultation: £35–£65) and grooming. By 12 weeks, your puppy should tolerate tooth inspection, ear checks, and nail handling without stress.",
            "<strong>Step 9: Month-by-month first-year milestones</strong> — Month 2–3: socialisation + toilet training. Month 3–4: basic commands (sit, down, come). Month 4–6: lead walking + recall reliability. Month 6–9: adolescent phase — revisit foundations, increase impulse control exercises. Month 9–12: proof all behaviours in varied environments.",
            "<strong>Step 10: Budget for the first year of training</strong> — Puppy class: £40–£80. Basic equipment (collar, lead, harness, treats, clicker): £50–£80. One-to-one session if needed: £80–£200. Total training budget for first year: approximately £170–£360. This is an investment — the RSPCA reports that behavioural issues are the leading reason for rehoming.",
            "<strong>UK-specific note</strong> — The Kennel Club Good Citizen Dog Scheme offers Bronze, Silver, and Gold awards — an excellent structured training pathway. Registration is free and classes are available nationwide.",
            "<strong>Seasonal note</strong> — Puppies arriving in UK autumn/winter (September–February) have fewer daylight hours for outdoor socialisation. Compensate with indoor socialisation activities: puppy playdates, pet-friendly shops, and car rides to new locations."
        ]
    },
    4139: {  # Best Dog Training Leads UK – Long Lines & Harnesses
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Select lead length based on training stage</strong> — Short lead (1–1.2m): for heel work and urban walking. Standard lead (1.5–1.8m): everyday walking and basic training. Long line (3–5m): recall training in enclosed spaces. Long line (10m): advanced recall and distance work in open areas. Retractable leads are not recommended for training due to inconsistent tension.",
            "<strong>Step 2: Choose the correct material</strong> — Nylon webbing (£5–£15): lightweight, quick-drying, suits most dogs. Leather (£15–£35): durable, comfortable in hand, improves with age. Biothane (£12–£25): waterproof, easy to clean, ideal for UK wet weather. Rope (£8–£20): good grip, heavier, suits larger dogs. Avoid chain leads — they are heavy and can injure both dog and handler.",
            "<strong>Step 3: Match lead width to dog size</strong> — Small breeds (under 10kg): 10–15mm width. Medium breeds (10–25kg): 15–20mm. Large breeds (25–40kg): 20–25mm. Giant breeds (40kg+): 25mm+. A lead that is too thin can cut into hands; too thick adds unnecessary weight for small dogs.",
            "<strong>Step 4: Pair lead with appropriate collar or harness</strong> — For training: front-clip harness (£15–£30) reduces pulling by redirecting the dog's centre of gravity. For general walking with a trained dog: flat collar (£8–£20) or back-clip harness. For head-shy or reactive dogs: head collar (£10–£20) under professional guidance only.",
            "<strong>Step 5: Introduce the long line safely</strong> — Start in a secure, enclosed area (garden or empty tennis court). Let the line drag while your dog explores. Practise recall: say your dog's name, then 'come', and reel in gently when they respond. Reward at your feet. Never wrap a long line around your hand — use a loop end or let it trail through gloved hands.",
            "<strong>Step 6: Practise the 'penalty yards' technique for pulling</strong> — Walk forward with a loose lead. The moment the lead goes tight, stop and walk backward 3–5 steps. Wait for your dog to return to your side. Reward and resume walking. A consistent 20-minute session daily shows improvement within 2–3 weeks.",
            "<strong>Step 7: Use a double-ended lead for transitional training</strong> — Attach one clip to a front-clip harness chest ring and one to a back ring, creating a 'Y' configuration. This gives steering control while allowing the dog to walk naturally. Double-ended leads cost approximately £12–£20.",
            "<strong>Step 8: Care for your training leads</strong> — Nylon: machine wash on cold, air dry. Leather: wipe clean, apply leather conditioner every 2–3 months. Biothane: rinse under a tap, wipe dry. Check all leads weekly for: fraying, worn stitching, weak clips, and corrosion on metal fittings. Replace immediately if any damage is found.",
            "<strong>Step 9: Build a training lead kit</strong> — Minimum kit: one 1.5m standard lead (£8–£15) + one 5m long line (£10–£18) + one front-clip harness (£15–£30). Total: £33–£63. Add a 10m long line (£15–£25) when progressing to distance recall and a treat pouch (£5–£10) for hands-free reward delivery.",
            "<strong>Step 10: Know UK lead law requirements</strong> — Under the Road Traffic Act 1988, dogs must be on a lead on designated roads. Many UK parks and commons have seasonal or permanent lead-on areas (check local bylaws). The Countryside Code recommends leads near livestock. Penalties for out-of-control dogs can include unlimited fines under the Dangerous Dogs Act 1991.",
            "<strong>Breed-specific note</strong> — Strong pullers (Huskies, Malamutes, Staffordshire Bull Terriers): use a padded, wide lead (20mm+) with a front-clip harness. Sighthounds (Greyhounds, Whippets): use a martingale collar (£10–£15) to prevent slip-outs due to narrow heads.",
            "<strong>UK weather note</strong> — In wet conditions (common October–April), leather leads become slippery and may stretch. Biothane or rubber-coated nylon handles maintain grip. Carry a spare 1.5m nylon lead in your coat pocket as backup."
        ]
    },
    4042: {  # Best Dog Leads UK – Walking & Training Lead Guide
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Measure your ideal lead length</strong> — Stand upright with your arm relaxed at your side, holding the lead handle. The clip should reach your dog's collar/harness with a 'J' curve of slack. For most handlers and medium dogs, this is 1.5–1.8m. Too short causes constant tension; too long reduces control in urban settings.",
            "<strong>Step 2: Test the handle for comfort</strong> — Look for padded handles or wide loop handles if you walk for more than 20 minutes at a time. Neoprene-padded handles (common on leads £10+) prevent friction burns. If your dog weighs over 20kg, a traffic handle (short handle 30cm from the clip) provides additional control when passing other dogs or crossing roads.",
            "<strong>Step 3: Check the clip mechanism</strong> — Trigger clips (bolt snaps) are the most common and reliable. Ensure the clip size matches your dog's D-ring: small clips (under 15mm opening) for small breeds, medium (15–20mm) for medium dogs, large (20–25mm) for large breeds. Test the spring mechanism — it should snap shut firmly. Avoid carabiner-style clips for strong pullers as they can open under sustained lateral pressure.",
            "<strong>Step 4: Match lead type to walking environment</strong> — Urban pavements: standard 1.5m lead with traffic handle. Parks and fields: 3m adjustable lead or long line. Woodland trails: a bright-coloured (hi-vis yellow or orange) lead for visibility, especially in UK autumn when light fades before 4 PM.",
            "<strong>Step 5: Consider a multi-function lead</strong> — Adjustable leads (£12–£25) offer 3–6 length settings using rings along the lead length. These combine the functionality of a short heel lead and a longer walking lead. Particularly useful for owners who walk in varied environments without carrying multiple leads.",
            "<strong>Step 6: Introduce the lead positively</strong> — For puppies or rescue dogs new to leads: clip the lead on, let them drag it in a safe indoor space for 5-minute sessions. Reward calm behaviour. Gradually pick up the lead and follow the dog with no pulling. After 3–5 sessions, begin gentle directional guidance with treats.",
            "<strong>Step 7: Inspect and replace leads on a schedule</strong> — Check weekly: stitching at clip attachment (the highest-stress point), webbing for fraying, handle loop for wear. Replace nylon leads every 12–18 months with daily use. Leather leads last 3–5+ years with conditioning every 2–3 months. Any signs of damage = immediate replacement for safety.",
            "<strong>Step 8: Use reflective or LED leads for winter walks</strong> — UK sunset is before 4 PM from November to January. A reflective lead (£8–£15) or LED clip-on light (£5–£8) makes you and your dog visible to motorists. Combine with a reflective collar band and hi-vis jacket for maximum safety.",
            "<strong>Step 9: Budget for a complete lead set</strong> — Essential: one standard 1.5m lead (£8–£15). Recommended additions: one 5m long line for training (£10–£18), one slip lead for quick use (£5–£10), one waterproof biothane lead for rainy days (£12–£25). Total comprehensive set: £35–£68.",
            "<strong>Step 10: Follow UK lead regulations</strong> — Dogs must be on leads on roads with a speed limit (Road Traffic Act 1988). Most public parks have areas requiring leads — check local authority bylaws. The Highway Code (Rule 56) advises keeping dogs on a short lead near roads. Dogs worrying livestock can be legally shot by farmers under the Animals Act 1971.",
            "<strong>Multi-dog household note</strong> — If walking two dogs, use individual leads rather than a coupler for better control. If you must use a coupler (£8–£15), only do so with dogs of similar size and walking pace.",
            "<strong>Seasonal UK note</strong> — In muddy conditions (September–April), leather leads get damaged and slippery. Keep a biothane or coated nylon lead as your winter lead. Wash and dry all leads after muddy walks to prevent bacteria buildup and odour."
        ]
    },
    4791: {  # How to Choose the Right Dog Training Treats
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Audit your dog's current daily calorie intake</strong> — Check your dog food packaging for calorie content (kcal/100g). Multiply by daily portion weight and divide by 100. A 20kg moderately active dog typically needs 800–1,000 kcal/day. Reserve 10% (80–100 kcal) for training treats and reduce meal portions accordingly.",
            "<strong>Step 2: Identify what motivates your individual dog</strong> — Offer 5 different treat types in a row and note which your dog chooses first, consumes fastest, and works hardest for. Common hierarchy: fresh meat > cheese > soft commercial treats > hard biscuits > kibble. Some dogs (e.g., working Collies) prefer toy rewards — test both food and play.",
            "<strong>Step 3: Select appropriate treat texture</strong> — Soft, moist treats: best for training (quick to eat, under 2 seconds). Semi-moist: suitable for general rewards. Hard/crunchy: slower to eat, best for end-of-session rewards or calm settling. Freeze-dried: lightweight, high value, easy to break. Avoid sticky treats that leave residue on hands and treat pouches.",
            "<strong>Step 4: Check ingredients for quality and safety</strong> — First ingredient should be a named protein (chicken, lamb, fish). Avoid treats with added sugars, artificial colours (E-numbers), propylene glycol, or BHA/BHT preservatives. UK-manufactured treats must comply with The Animal Feed (England) Regulations 2010 and display a full ingredient list.",
            "<strong>Step 5: Size treats correctly for training</strong> — Each treat should be approximately 1cm × 1cm (pea-sized) for medium dogs, 0.5cm for small breeds, and up to 1.5cm for giant breeds. A 100g bag of commercial training treats should yield 60–100 individual treats at this size. If treats are too large, cut or break them before training sessions.",
            "<strong>Step 6: Prepare a treat hierarchy for each session</strong> — Carry 3 value levels in your treat pouch: 60% low value (daily kibble), 30% medium value (commercial training treats), 10% high value (cheese, chicken). Use low for known behaviours, medium for new learning, high for breakthroughs or high-distraction environments.",
            "<strong>Step 7: Make cost-effective homemade training treats</strong> — Liver cake: blend 250g liver with 250g wholemeal flour, 1 egg, bake at 180°C for 20 minutes, cut into 1cm cubes. Yields approximately 200 treats for under £3. Dehydrated chicken: slice chicken breast thin, dehydrate at 70°C for 6–8 hours. Store in fridge for up to 5 days or freeze for 3 months.",
            "<strong>Step 8: Monitor your dog's reaction to new treats</strong> — Introduce one new treat type at a time. Give 3–5 pieces on day one and observe for 24 hours. Signs of intolerance: loose stools, itching, ear redness, excessive lip-licking. If reactions occur, discontinue and try a different single-protein treat.",
            "<strong>Step 9: Store treats correctly for freshness and safety</strong> — Soft commercial treats (opened): reseal and refrigerate, use within 2–4 weeks. Homemade treats: fridge for 5 days, freezer for 3 months. Freeze-dried treats: store in an airtight container in a cool cupboard for up to 12 months. Never leave moist treats in a treat pouch overnight — bacteria multiply rapidly.",
            "<strong>Step 10: Budget for monthly training treat costs</strong> — Pet dog, maintenance training: £5–£12/month. Puppy in active training: £10–£20/month. Behaviour modification programme: £15–£30/month. Mix commercial treats (£3–£6 per 100g bag) with homemade treats (liver cake at £1.50 per batch) to halve costs.",
            "<strong>Allergy-prone breed note</strong> — West Highland Terriers, French Bulldogs, Labradors, and Golden Retrievers have higher rates of food sensitivities. Use single-protein, novel treats (venison, duck, fish) and avoid chicken if your dog has known poultry sensitivity.",
            "<strong>Weight management note</strong> — For overweight dogs on a veterinary weight-loss programme, use ultra-low-calorie treats: raw carrot (4 kcal per stick), cucumber (1 kcal per slice), or their weight-management kibble (counted from daily ration). Every treat calorie counts when the target is weight loss of 1–2% body weight per week."
        ]
    },

    # ─── EDUCATIONAL CLUSTER ─────────────────────────────────────────────
    7341: {  # First Week with a New Puppy
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Prepare your home before the puppy arrives</strong> — Puppy-proof one room as a base: cover electrical cables (cable protectors £5–£10), remove toxic plants (lilies, ivy, daffodils), store chemicals above 1.2m height. Set up: crate (£30–£60), water bowl, bed, and 2–3 safe chew toys.",
            "<strong>Step 2: Day 1 — Keep everything calm</strong> — Collect your puppy in the morning if possible to maximise daytime settling. Drive home calmly (secure in a crate or with a passenger holding the puppy on a towel). Offer water immediately on arrival. Show the garden toilet area. Limit visitors to household members only for the first 48 hours.",
            "<strong>Step 3: Day 1–2 — Establish the toilet routine</strong> — Take puppy outside every 30–60 minutes, after every meal (within 15 minutes), after waking from naps, and after play. Stay with puppy outside; praise and treat within 2 seconds of elimination. Expect 8–12 toilet trips outside per day. Accidents indoors: clean with enzymatic cleaner (£5–£8) — never punish.",
            "<strong>Step 4: Day 2–3 — Introduce feeding schedule</strong> — 8-week puppy: 4 meals daily at roughly 6-hour intervals (e.g., 7 AM, 12 PM, 5 PM, 10 PM). Use the same food the breeder was using. Measure portions with scales. A small breed puppy needs approximately 50–80g per meal; a large breed puppy 80–120g per meal at 8 weeks.",
            "<strong>Step 5: Day 3–4 — Begin gentle handling exercises</strong> — Hold puppy on your lap for 2–3 minutes, touching paws, ears, mouth, and tail. Pair every touch with a small treat. This prepares for future vet visits (UK vet check-up: £35–£65), grooming, and nail clipping. Handle 4 times per day for 2–3 minutes each.",
            "<strong>Step 6: Day 4–5 — Introduce the crate at night</strong> — Place the crate in your bedroom initially. Add a worn t-shirt for your scent. Feed the last meal inside the crate. Expect some whining on nights 1–3 — wait for a 5-second pause in whining, then calmly let the puppy out for a toilet break. Most puppies sleep through the night (6–7 hours) within 5–7 days.",
            "<strong>Step 7: Day 5–6 — Start name recognition</strong> — Say the puppy's name in an upbeat tone. When they look at you, immediately mark ('yes!') and treat. Practise 15–20 repetitions spread across the day. By day 6–7, most puppies will orient towards you within 1–2 seconds of hearing their name.",
            "<strong>Step 8: Day 7 — Book essential vet and admin tasks</strong> — Register with a local vet (first puppy health check: typically free or £35–£65). Confirm vaccination status and schedule remaining jabs (first vaccination at 8 weeks, second at 10–12 weeks, typically £40–£70 per vaccination). Register your microchip details on a DEFRA-compliant database. Arrange puppy insurance (£15–£40/month for lifetime cover).",
            "<strong>Step 9: Monitor health indicators throughout the week</strong> — Normal puppy stool: firm, brown, 3–5 times per day. Normal sleep: 18–20 hours per day at 8 weeks. Watch for: refusal to eat for more than 12 hours, lethargy, vomiting, diarrhoea with blood, or discharge from eyes/nose — contact your vet immediately if any occur.",
            "<strong>Step 10: Plan weeks 2–4</strong> — Week 2: begin socialisation (carry puppy to see traffic, people, other sounds). Week 3: start indoor lead training (let puppy drag a light lead). Week 4: first puppy class (ABTC-accredited, £40–£80 for 6 weeks). Research local puppy groups — the Kennel Club website lists Good Citizen classes by postcode.",
            "<strong>Equipment budget for week one</strong> — Crate: £30–£60. Bed or vet bedding: £10–£25. Bowls (2): £5–£10. Collar + ID tag: £8–£15. Light lead: £5–£10. Enzymatic cleaner: £5–£8. Chew toys (3): £10–£20. Training treats: £3–£6. Total: approximately £76–£154.",
            "<strong>UK legal note</strong> — Under the Microchipping of Dogs (England) Regulations 2015, all puppies must be microchipped by 8 weeks of age. The breeder should have done this; verify the chip number and transfer details to your name on an approved database within 24 hours of purchase."
        ]
    },
    7340: {  # Puppy Teething Guide
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Understand the teething timeline</strong> — Deciduous (baby) teeth erupt: 3–6 weeks (28 teeth total). Adult teeth begin replacing them: 12–16 weeks. Full adult dentition (42 teeth): 6–7 months. The most intense chewing phase is 14–20 weeks when incisors and canines are being replaced.",
            "<strong>Step 2: Provide appropriate chew toys from 8 weeks</strong> — Soft rubber toys (e.g., puppy-grade rubber toys, £5–£10) for gentle gnawing. Frozen twisted flannels (cost: nearly free) provide cooling relief. Rope toys (£4–£8) for supervised play only. Never give hard bones, antlers, or nylon chews to teething puppies — risk of tooth fracture.",
            "<strong>Step 3: Use cold therapy for pain relief</strong> — Freeze a wet flannel for 1 hour, then offer to the puppy for supervised chewing (5–10 minutes). Freeze carrot sticks (approximately 1 kcal each, safe from 10 weeks). Refrigerate rubber toys for 2 hours. Cold reduces inflammation and soothes sore gums. Do not use ice cubes directly — they can damage emerging teeth.",
            "<strong>Step 4: Manage increased mouthing behaviour</strong> — Teething puppies mouth everything. When puppy bites hands: yelp, withdraw hands, pause interaction for 15 seconds. Redirect to a chew toy within 3 seconds. Aim for 50+ redirections per day during peak teething. Consistency across all family members is essential — one person allowing biting undermines training.",
            "<strong>Step 5: Inspect teeth weekly from 12 weeks</strong> — Gently lift lips and check for: retained baby teeth (adult and baby tooth side by side), red or swollen gums, broken tooth fragments, excessive drooling. If a baby tooth has not fallen out within 2 weeks of the adult tooth emerging, consult your vet — retained teeth may need extraction (UK cost: £150–£400 under general anaesthetic).",
            "<strong>Step 6: Introduce tooth brushing at 8–10 weeks</strong> — Use a finger brush (£3–£5 for a pack of 3) or puppy toothbrush (£2–£4) with enzymatic dog toothpaste (£4–£8, never human toothpaste). Brush for 15–30 seconds initially, 3–4 times per week, building to 2 minutes daily by 6 months. This establishes a lifelong habit — the BVDA recommends daily brushing for all dogs.",
            "<strong>Step 7: Adjust diet during heavy teething</strong> — If your puppy refuses dry kibble at 14–18 weeks (common), soak kibble in warm water for 10 minutes to soften. Alternatively, mix 25% wet food with 75% soaked dry. Maintain calorie intake — weigh food and adjust. A puppy skipping one meal during teething is normal; skipping more than 2 meals warrants a vet call.",
            "<strong>Step 8: Protect your belongings</strong> — Teething puppies chew furniture, shoes, and cables. Apply bitter apple spray (£5–£8) to furniture legs and cable covers. Provide a chew toy within reach at all times — one per room the puppy accesses. Rotate toys every 2–3 days to maintain novelty. Budget £15–£25/month for replacement chew toys during the 12–24 week peak.",
            "<strong>Step 9: Collect and check fallen baby teeth</strong> — Most baby teeth are swallowed safely (no concern). If you find a tooth, check it is intact — a fractured root left in the gum can cause infection. Save any found teeth to show your vet at the next check-up if anything looks abnormal.",
            "<strong>Step 10: Schedule a dental check at 7 months</strong> — By 7 months, all 42 adult teeth should be present. Book a vet dental check (often included in a routine appointment, £35–£65) to verify: correct occlusion (bite alignment), no retained deciduous teeth, and healthy gum colour (pink, not red or white). Early detection of dental issues prevents costly treatment later.",
            "<strong>Breed-specific note</strong> — Small and toy breeds (Chihuahuas, Yorkshire Terriers, Maltese) are more prone to retained deciduous teeth and dental crowding. Extra vigilance during tooth checks is needed. Brachycephalic breeds (Bulldogs, Pugs) may have malocclusion — discuss with your vet at the 7-month check.",
            "<strong>Teething comfort schedule</strong> — Morning: frozen flannel for 5 minutes after breakfast. Midday: refrigerated rubber toy for 10 minutes. Afternoon: supervised rope toy play for 10 minutes. Evening: frozen carrot stick (from 10 weeks) before bedtime. This routine provides 4 relief points across the day."
        ]
    },
    7339: {  # Puppy Sleep Guide
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Understand sleep needs by age</strong> — 8–12 weeks: 18–20 hours per day. 3–6 months: 16–18 hours. 6–12 months: 14–16 hours. Adult dogs: 12–14 hours. Sleep is when growth hormone is released — disrupting sleep can impair development. Let sleeping puppies rest; never wake them for play.",
            "<strong>Step 2: Create the ideal sleeping environment</strong> — Quiet room or area away from household traffic. Ambient temperature: 18–22°C (the UK average bedroom temperature). Dim lighting or complete darkness. A crate (£30–£60) provides a den-like feeling. Place a ticking clock or white noise machine (£10–£20) nearby for the first 2 weeks to simulate littermate sounds.",
            "<strong>Step 3: Establish a consistent bedtime routine</strong> — Same time each evening (e.g., 10 PM). Last toilet trip 15 minutes before bed. Calm activity only in the final hour — no vigorous play after 9 PM. Place puppy in crate or bed with a safe chew toy. This routine signals 'sleep time' within 5–7 days of consistent practice.",
            "<strong>Step 4: Handle nighttime waking correctly</strong> — Week 1–2: expect 1–2 overnight toilet breaks (puppies cannot hold their bladder for more than 3–4 hours at 8 weeks). Set an alarm for halfway through the night rather than waiting for whining. Take puppy out quietly, no talking or playing, then straight back to bed. By 12 weeks, most puppies sleep 6–7 hours continuously.",
            "<strong>Step 5: Choose the right bed for each stage</strong> — 8–16 weeks: vet bedding or a towel in the crate (£5–£10) — easy to wash after accidents. 4–6 months: a simple bolster bed (£15–£25) with removable, washable cover. 6+ months: transition to their permanent bed, sized to the dog's adult dimensions. Allow 15cm extra on all sides beyond the dog's body length.",
            "<strong>Step 6: Manage daytime naps</strong> — Puppies need scheduled naps, not just ad-hoc sleeping. After 45–60 minutes of activity, enforce a 1–2 hour nap in their crate or quiet area. Overtired puppies become bitey, hyperactive, and difficult to train. A typical day for an 8-week puppy: 1 hour awake, 2 hours nap, repeated 6–8 times.",
            "<strong>Step 7: Gradually move the crate to its permanent location</strong> — Start with the crate beside your bed (nights 1–7). Move it 30cm further from your bed every 2–3 nights. By week 3–4, the crate should be in its permanent location (another room if desired). Moving too fast causes separation anxiety; moving too slowly creates dependency.",
            "<strong>Step 8: Troubleshoot early morning waking</strong> — If your puppy wakes consistently at 5 AM: do not respond for 5 minutes (unless it is a toilet emergency — whining + circling). Gradually extend the delay by 5 minutes every 3 days. Ensure the final evening meal is not too early — feeding at 6 PM may leave a puppy hungry by 5 AM. Adjust to 7–8 PM if needed.",
            "<strong>Step 9: Monitor sleep quality indicators</strong> — Normal: twitching and 'running' during REM sleep, occasional soft vocalisation. Concerning: frequent nightmares (thrashing, screaming), inability to settle for more than 30 minutes, excessive daytime lethargy, or sudden change in sleep patterns. The latter warrants a vet visit (£35–£65 consultation).",
            "<strong>Step 10: Transition from crate to open sleeping by 12 months</strong> — If your goal is crate-free sleeping, begin at 10–12 months once toilet training is fully reliable. Leave the crate door open for 1 week. Then replace the crate with a bed in the same location. If regression occurs (chewing, accidents), return to the crate for 2 more weeks before trying again.",
            "<strong>UK seasonal note</strong> — During UK summer (June–August), bedroom temperatures can exceed 25°C. Provide a cooling mat (£10–£20) inside the crate. In winter (November–February), ensure the sleeping area is draught-free — check for gaps under external doors and single-glazed windows.",
            "<strong>Breed-specific note</strong> — Brachycephalic breeds (Bulldogs, Pugs, French Bulldogs) are prone to overheating and snoring. Keep sleeping temperature at the lower end (18°C) and ensure good ventilation. Large breed puppies grow rapidly and need frequent bed size upgrades — budget for 2–3 bed changes in the first year."
        ]
    },
    7338: {  # Puppy-Proofing Your Home
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Secure the kitchen</strong> — Install child locks on lower cupboards containing cleaning products (£5–£10 for a pack of 6). Move bins into a cupboard or use a lidded bin (£15–£30). Block access behind the cooker and fridge where puppies can become trapped. Store chocolate, grapes, raisins, onions, and xylitol-containing products above 1.2m height.",
            "<strong>Step 2: Puppy-proof the living room</strong> — Cover or elevate electrical cables using cable protectors (£5–£15 per 2m length). Remove or elevate houseplants — common toxic plants include lilies, ivy, dieffenbachia, and aloe vera. Secure loose items below 50cm height: remote controls, charger cables, children's toys, shoes. Move or protect furniture legs with bitter apple spray (£5–£8).",
            "<strong>Step 3: Make the bathroom safe</strong> — Keep the toilet lid closed (or use a clip, £3–£5) — cleaning chemicals and toilet blocks are toxic. Store medicines in a high cabinet. Remove accessible bin bags. Keep laundry baskets covered — socks and underwear are the most commonly ingested foreign bodies (surgical removal: £1,000–£3,000 in the UK).",
            "<strong>Step 4: Secure the garden</strong> — Walk the entire perimeter checking for gaps in fencing. A puppy can squeeze through a 10cm gap. Patch holes with wire mesh (£5–£15 per roll). Remove or fence off: slug pellets (metaldehyde is fatal), cocoa mulch, compost bins, lily plants, and foxglove. Check for standing water (e.g., uncovered ponds) — puppies can drown in shallow water.",
            "<strong>Step 5: Set up puppy zones</strong> — Use baby gates (£15–£30 each) to restrict access to safe areas. A new puppy should have access to 1–2 rooms maximum initially, expanding as house training progresses. The 'puppy zone' needs: water bowl, bed/crate, 2–3 safe toys, and washable flooring or puppy pads (£8–£15 for a pack of 50).",
            "<strong>Step 6: Protect stairs and heights</strong> — Block stairways with baby gates until 4–6 months of age (longer for large breeds prone to joint issues). Puppies should not regularly climb stairs until their growth plates begin closing. For small breeds, consider a ramp to the sofa (if access is permitted) to prevent jumping injuries (£15–£25).",
            "<strong>Step 7: Check for small ingestible objects</strong> — Walk through each room at puppy height (30–40cm). Look for: coins, buttons, rubber bands, hair ties, Lego, pen caps, batteries, sewing needles. These are all common foreign body ingestion items. Clear floors daily before the puppy has access.",
            "<strong>Step 8: Address seasonal hazards in the UK</strong> — Spring: slug pellets, daffodil bulbs, fertiliser. Summer: barbecue skewers, antifreeze in garages, blue-green algae in ponds. Autumn: conkers (toxic), acorns (toxic in quantity), firework debris. Winter: antifreeze (sweet-tasting, lethal at 1.5ml/kg body weight), rock salt (irritant to paws), tinsel and decorations.",
            "<strong>Step 9: Create a puppy first-aid kit</strong> — Sterile gauze pads, conforming bandage, antiseptic wash (diluted chlorhexidine), blunt-ended scissors, tick removal tool (£3–£5), and your vet's emergency phone number. Store in a labelled container at home and keep your car boot stocked with a spare kit. Kit cost: approximately £15–£25. Know your nearest emergency vet and their out-of-hours number.",
            "<strong>Step 10: Budget for the puppy-proofing process</strong> — Baby gates (2): £30–£60. Cable protectors: £10–£20. Child locks: £5–£10. Bitter apple spray: £5–£8. Bin upgrade: £15–£30. Garden fence repairs: £10–£50. First-aid kit: £15–£25. Puppy pads: £8–£15. Total: approximately £98–£218. This is a one-time investment that prevents veterinary emergencies costing hundreds to thousands of pounds.",
            "<strong>Breed-specific note</strong> — Terrier breeds and Labradors are particularly prolific chewers and ingesters of foreign objects. Spaniels are drawn to socks and soft fabrics. Sighthound puppies can jump surprisingly high — secure items up to 1m, not just 50cm.",
            "<strong>Rental property note</strong> — If renting, use adhesive cable covers (removable) rather than screwing protectors to walls. Use pressure-fit baby gates rather than screw-fix. Document any existing garden fence issues with your landlord before the puppy arrives to clarify responsibility for repairs."
        ]
    },
    7337: {  # Puppy Vaccination Schedule UK
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Understand the core vaccination schedule</strong> — First vaccination (primary course dose 1): 6–8 weeks of age. Second vaccination (dose 2): 10–12 weeks of age (minimum 2-week gap). Your puppy is typically protected 1–2 weeks after the second dose. Core vaccines in the UK cover: canine distemper, parvovirus, adenovirus (hepatitis), and leptospirosis.",
            "<strong>Step 2: Register with a vet before your puppy arrives</strong> — Many practices offer free first consultations for new puppies. Average UK vaccination cost: £40–£70 per dose (total primary course: £80–£140). Some practices offer puppy health plans (£10–£15/month) that include vaccinations, flea/worm treatments, and health checks.",
            "<strong>Step 3: Know what is optional but recommended</strong> — Kennel cough (Bordetella bronchiseptica + parainfluenza): intranasal vaccine, required by most UK boarding kennels and doggy day-care (£20–£40). Rabies: required only for Pet Travel (PETS scheme) if travelling abroad (£50–£80). Discuss with your vet which non-core vaccines suit your puppy's lifestyle.",
            "<strong>Step 4: Follow isolation rules before vaccination is complete</strong> — Before 2 weeks after the second vaccination: do not let your puppy walk on public ground where unvaccinated dogs may have been. You can carry your puppy to expose them to sights and sounds. Puppy-proofed gardens with no unknown dog access are safe. Socialisation with known, fully vaccinated dogs in private homes is acceptable.",
            "<strong>Step 5: Keep a vaccination record</strong> — Your vet provides a vaccination card or booklet. Keep it with your puppy's documents (microchip certificate, insurance policy). Photograph it and store digitally. You will need it for: boarding kennels, doggy day-care, puppy classes, dog shows, and any future vet visits or referrals.",
            "<strong>Step 6: Schedule the first annual booster at 12–15 months</strong> — The primary course requires a booster at 12 months to maintain immunity. After that, DHP (distemper, hepatitis, parvovirus) is boosted every 3 years, and leptospirosis is boosted annually. Missing a booster by more than 15 months may require restarting the primary course. Set a calendar reminder.",
            "<strong>Step 7: Manage post-vaccination care</strong> — Mild side effects (first 24–48 hours): slight lethargy, reduced appetite, small lump at injection site. Keep activity low for 24 hours post-vaccination. Provide quiet rest and ensure fresh water is available. Contact your vet if: vomiting, facial swelling, difficulty breathing, or persistent lethargy beyond 48 hours (rare allergic reactions occur in fewer than 1 in 10,000 dogs).",
            "<strong>Step 8: Coordinate with flea and worming treatments</strong> — Worming: every 2 weeks from 2–12 weeks of age, then monthly until 6 months, then every 3 months for life. Flea treatment: from 8 weeks of age (vet-prescribed products are more effective than shop-bought). Do not give multiple treatments on the same day as vaccinations — space by 2–3 days. Monthly flea/worm treatment: £8–£15.",
            "<strong>Step 9: Budget for the first year of veterinary care</strong> — Primary vaccinations (2 doses): £80–£140. Kennel cough vaccine: £20–£40. Neutering/spaying (if planned, 6–12 months): £150–£350 depending on size and sex. Microchip (if not done by breeder): £15–£30. Monthly flea/worm: £96–£180/year. Total first-year vet costs: approximately £360–£740.",
            "<strong>Step 10: Understand UK legal requirements</strong> — Under the Microchipping of Dogs (England) Regulations 2015, all dogs must be microchipped by 8 weeks. While vaccinations are not legally required, failure to protect against preventable disease may be considered under the Animal Welfare Act 2006 duty of care. Veterinary organisations including the BVA strongly recommend following the full vaccination schedule.",
            "<strong>Breed-specific note</strong> — Some breeds (Rottweilers, Dobermans) may have a less robust response to parvovirus vaccination — your vet may recommend a third dose at 16 weeks. Toy breeds may need monitoring for vaccine reactions due to smaller body mass relative to vaccine volume.",
            "<strong>UK seasonal note</strong> — Leptospirosis risk increases in autumn and winter when standing water is more prevalent and rats are more active. Ensure the annual lepto booster is current, particularly if your dog swims in or drinks from canals, rivers, or stagnant ponds."
        ]
    },
    7336: {  # Dog Bed Safety
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Choose non-toxic materials</strong> — Look for beds certified to OEKO-TEX Standard 100 or equivalent, meaning fabrics are tested for harmful substances. Avoid beds with strong chemical odours (off-gassing from flame retardants or formaldehyde in adhesives). Air new beds in a well-ventilated area for 24–48 hours before first use.",
            "<strong>Step 2: Select the correct bed size</strong> — Measure your dog from nose to tail base (not tail tip) and add 15–20cm. For width, measure across the widest point (usually shoulder width) and add 10–15cm. A 25kg Labrador typically needs a bed of at least 90cm × 70cm. An over-large bed wastes space; an undersized bed forces uncomfortable sleeping positions.",
            "<strong>Step 3: Check for chewing and ingestion hazards</strong> — Avoid beds with: removable buttons, zip pulls accessible to the dog, decorative ribbons or tassels, loose foam pieces. For heavy chewers, choose beds with hidden zips, reinforced stitching (double or triple stitching), and chew-resistant outer fabrics (e.g., ballistic nylon, 1000D+ denier). Budget: chew-resistant beds £35–£70 vs standard beds £15–£35.",
            "<strong>Step 4: Assess the filling for safety and support</strong> — Memory foam (£40–£80): good for orthopaedic support, should be CertiPUR-certified for low chemical emissions. Polyester fibre fill (£15–£35): lightweight, machine washable, but flattens over time. Polystyrene beads (£20–£40): mouldable, but extremely dangerous if ingested (choking/blockage). Avoid loose-fill beds for puppies and heavy chewers.",
            "<strong>Step 5: Ensure the cover is washable</strong> — The bed cover should be machine-washable at 40–60°C to kill bacteria and dust mites. Wash the cover every 1–2 weeks as a minimum. The RSPCA recommends regular washing to prevent skin irritation and bacterial infections. Check washing instructions before purchase — some beds are surface-clean only, which is insufficient for hygiene.",
            "<strong>Step 6: Position the bed safely</strong> — Away from direct heat sources (minimum 1m from radiators to prevent overheating or burns). Away from draughts (not by external doors or single-glazed windows). On a level, non-slip surface (add a non-slip mat beneath, £5–£10, on hard floors). Not in direct sunlight (UV degrades fabrics and foam, and causes overheating).",
            "<strong>Step 7: Inspect the bed weekly for wear</strong> — Check for: exposed foam or filling, torn seams, broken zips, flattened padding (no longer providing support). A bed that has lost 50% of its loft no longer provides adequate cushioning. Budget to replace polyester-fill beds every 6–12 months (£15–£35) or memory foam beds every 2–3 years (£40–£80).",
            "<strong>Step 8: Choose fire-safe materials</strong> — In the UK, soft furnishings must comply with The Furniture and Furnishings (Fire) (Safety) Regulations 1988 (as amended). Dog beds sold in the UK should meet these standards. Check for a compliance label. Avoid purchasing unregulated beds from overseas marketplaces without fire safety certification.",
            "<strong>Step 9: Address special needs</strong> — Senior dogs with arthritis: orthopaedic bed with 10cm+ memory foam (£50–£80), raised sides for head resting. Post-surgical dogs: low-entry bed (step-in height below 8cm) to avoid strain. Incontinent dogs: waterproof liner (£10–£20) under a washable cover. Anxious dogs: bolstered/hooded beds providing a sense of enclosure (£25–£50).",
            "<strong>Step 10: Budget for bed safety across your dog's life</strong> — Puppy stage (0–12 months): 2–3 inexpensive beds (£30–£75 total) as they will be chewed and outgrown. Adult stage (1–7 years): one quality bed replaced every 1–2 years (£30–£80). Senior stage (7+ years): orthopaedic bed replaced every 2–3 years (£50–£80). Lifetime bed budget: approximately £200–£400.",
            "<strong>Breed-specific note</strong> — Giant breeds (Great Danes, Mastiffs, St Bernards) need extra-large beds (120cm+ × 90cm+) with high-density foam to support 50–80kg body weight. Standard polyester fill compresses rapidly under heavy dogs. Deep-chested breeds benefit from beds with raised bolster edges for head and neck support.",
            "<strong>UK seasonal consideration</strong> — In UK winter, provide a thermal blanket layer (£8–£15) on top of the bed for short-coated breeds (Greyhounds, Whippets, Staffies). In summer, a cooling gel mat (£10–£25) placed on or beside the bed helps regulate temperature, especially for thick-coated breeds (Huskies, Samoyeds, Bernese Mountain Dogs)."
        ]
    },
    7334: {  # Puppy Bed Training
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Choose the right bed for training</strong> — Start with an inexpensive, washable bed (£10–£20) placed inside or next to a crate. The bed should be just large enough for the puppy to lie flat and stretch. Too large a bed reduces the 'den' feeling. Use vet bedding (£8–£15 per metre) as it wicks moisture and washes at 60°C.",
            "<strong>Step 2: Place the bed in the right location</strong> — For the first 1–2 weeks, place the bed in your bedroom within arm's reach. Your presence reduces anxiety and nighttime whining. After the puppy settles (usually 7–14 days), begin moving the bed 30cm per night toward its permanent location. Full transition takes approximately 3–4 weeks.",
            "<strong>Step 3: Create positive bed associations from day one</strong> — Drop treats (3–5 pieces) onto the bed every time you pass it. Place a Kong stuffed with food paste (£5–£10 for the Kong, £3–£6 for filling) on the bed during settled periods. Never use the bed as a punishment location. Within 5–7 days, your puppy should voluntarily choose to rest on the bed.",
            "<strong>Step 4: Introduce a 'bed' or 'place' command</strong> — Lure puppy onto the bed with a treat. The moment all four paws are on, mark ('yes!') and reward. Add the verbal cue ('bed') after 10 successful repetitions. Practise 10–15 times per day in 2-minute micro-sessions. By week 2, most puppies will go to the bed on cue from 1–2 metres away.",
            "<strong>Step 5: Build duration on the bed</strong> — Start with rewarding the puppy for staying on the bed for 2 seconds. Gradually increase: 5 seconds, 10 seconds, 30 seconds, 1 minute, 3 minutes, 5 minutes. If the puppy gets off, simply reset without a reward — no punishment. Increase by 20–30% per session, not more. Reaching a 10-minute settle typically takes 2–3 weeks of daily practice.",
            "<strong>Step 6: Add distance gradually</strong> — Once the puppy can stay on the bed for 3 minutes while you stand beside it, take one step back. Return and reward. Add one step per session until you can cross the room (3–4m). Then practise leaving the room for 5 seconds, building to 2 minutes. Do not increase both distance and duration simultaneously.",
            "<strong>Step 7: Establish a nighttime bed routine</strong> — 9:30 PM: final play/walk. 9:45 PM: last toilet trip. 10:00 PM: settle on bed with a small chew or stuffed Kong (lasting 5–10 minutes). Lights off. Same routine every night. Consistency is key — puppies learn routines within 5–7 repetitions. Expect occasional regression during teething (14–20 weeks).",
            "<strong>Step 8: Handle nighttime disturbances</strong> — If puppy whines: wait 30 seconds for a natural pause, then quietly take them outside for a toilet break (no talking, no playing). Return to bed. If puppy repeatedly gets off the bed: use a house line (light lead) clipped to the crate or a secure point near the bed — this is not a restraint but a gentle boundary reminder. Remove the line during the day.",
            "<strong>Step 9: Transition to the permanent bed</strong> — At 4–6 months, once the puppy is reliably sleeping through the night (6–8 hours), upgrade to their 'adult' bed. Place the old familiar bedding on top of the new bed for 3–5 days to transfer scent. Then remove the old bedding. The new bed should be sized for the puppy's expected adult measurements (nose to tail + 15cm, shoulder width + 10cm).",
            "<strong>Step 10: Troubleshoot common bed training issues</strong> — Puppy destroys the bed: use a chew-resistant bed (£35–£60) and provide a separate chew toy to redirect. Puppy sleeps on the floor instead: ensure the bed is not too hot — remove excess padding in summer. Puppy sleeps in the crate but not the bed: leave the crate door open with the bed inside; remove the crate door entirely after 1 week.",
            "<strong>Multi-dog household note</strong> — Each dog needs their own bed and their own 'place' command. Do not expect dogs to share a bed for training purposes. Place beds at least 1m apart to prevent resource guarding. Train each dog individually before practising in each other's presence.",
            "<strong>Budget summary</strong> — Training bed (washable): £10–£20. Vet bedding: £8–£15. Kong + filling: £8–£16. Treats for training (2 months): £10–£20. Permanent adult bed: £25–£60. Total bed training investment: approximately £61–£131."
        ]
    },
    7170: {  # Dog Health Terminology
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Learn to take your dog's vital signs at home</strong> — Normal resting heart rate: small breeds 100–140 bpm, large breeds 60–100 bpm. Normal respiration: 15–30 breaths per minute at rest. Normal temperature: 38.1–39.2°C (use a digital rectal thermometer, £5–£10). Practise checking these monthly so you recognise abnormalities quickly.",
            "<strong>Step 2: Understand common blood test abbreviations</strong> — PCV (packed cell volume): normal 37–55%, detects anaemia. ALT (alanine aminotransferase): liver function. BUN (blood urea nitrogen): kidney function. CBC (complete blood count): overall health screen. Ask your vet to explain results — a standard blood panel costs £80–£150 in the UK.",
            "<strong>Step 3: Recognise the five vital welfare needs</strong> — Under the Animal Welfare Act 2006, you must provide: a suitable environment, a suitable diet, the ability to exhibit normal behaviour, housing with or apart from other animals as appropriate, and protection from pain, suffering, injury, and disease. Failure constitutes a legal offence with penalties up to £20,000 and/or imprisonment.",
            "<strong>Step 4: Know when to seek emergency veterinary care</strong> — Immediate emergency: difficulty breathing, collapse, suspected poisoning (call VPIS: 01onal number via your vet), bloat (distended abdomen + retching without vomiting), uncontrolled bleeding, seizures lasting more than 3 minutes. Out-of-hours emergency vet fees: £150–£350 for initial consultation in the UK.",
            "<strong>Step 5: Create a health monitoring calendar</strong> — Monthly: weigh your dog, check body condition score (BCS 4–5 out of 9 is ideal), inspect teeth and gums, check ears for odour or discharge. Quarterly: review flea and worm treatment schedule. Annually: book a full veterinary health check (£35–£65), update vaccinations. Biannually for seniors (7+ years): blood work and joint assessment.",
            "<strong>Step 6: Maintain a health record folder</strong> — Include: vaccination booklet, microchip certificate, insurance policy number, regular medication details, past surgical records, and allergy information. Keep a digital backup (photographed or scanned). Share with any pet sitter, boarding kennel, or emergency contact.",
            "<strong>Step 7: Understand common medication terminology</strong> — NSAID: non-steroidal anti-inflammatory drug (e.g., meloxicam for pain). Antibiotic: for bacterial infections (always complete the full course). Antiparasitic: flea, tick, and worm treatments. 'Off-label': a medication used for a purpose not on its licence — legal and common in veterinary medicine when prescribed by a vet.",
            "<strong>Step 8: Budget for routine and emergency healthcare</strong> — Annual routine costs: vaccinations £30–£50, flea/worm £96–£180, health check £35–£65. Insurance: £15–£40/month for lifetime cover (recommended by the BVA). Without insurance, a single emergency can cost £1,000–£5,000+. The PDSA reports that UK dog owners spend an average of £1,875 per year on veterinary care.",
            "<strong>Step 9: Learn breed-specific health terminology</strong> — Brachycephalic Obstructive Airway Syndrome (BOAS): breathing difficulties in flat-faced breeds. Hip Dysplasia (HD): joint malformation, common in Labradors, German Shepherds. Degenerative Myelopathy (DM): spinal cord disease in older dogs. Progressive Retinal Atrophy (PRA): inherited blindness. Check your breed's known conditions on the Kennel Club Breed Health page.",
            "<strong>Step 10: Register with a vet and understand practice types</strong> — First-opinion practice: your general vet for routine care. Referral/specialist practice: for complex conditions, referred by your vet. Emergency/OOH practice: for out-of-hours emergencies. Charitable practices (PDSA, Blue Cross): means-tested free or low-cost care for eligible owners. Find an RCVS-accredited practice at findavet.rcvs.org.uk.",
            "<strong>UK-specific resource</strong> — The BVA (British Veterinary Association) publishes free pet health guidance at bva.co.uk. The RCVS (Royal College of Veterinary Surgeons) regulates all UK vets and maintains a public register. If concerned about veterinary care, complaints can be made to the RCVS.",
            "<strong>Senior dog note (7+ years)</strong> — Senior dogs benefit from twice-yearly health checks. Discuss screening for: arthritis (affects 80% of dogs over 8), dental disease, cognitive dysfunction (similar to dementia), and organ function decline. Early detection through regular blood work and joint assessments can add quality months to years to your dog's life."
        ]
    },
    7169: {  # Puppy Care Glossary
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Build your puppy care vocabulary before the puppy arrives</strong> — Key terms to know: socialisation window (3–14 weeks), house training, crate training, bite inhibition, recall, positive reinforcement, ABTC (Animal Behaviour and Training Council). Understanding these terms helps you follow vet and trainer advice accurately from day one.",
            "<strong>Step 2: Create a puppy supplies checklist with budget</strong> — Crate (medium): £30–£60. Bed/vet bedding: £10–£20. Bowls (2): £5–£10. Collar + ID tag: £8–£15. Lead (1.5m): £5–£12. Puppy food (first month): £15–£30. Treats: £3–£6. Toys (3–5): £15–£25. Enzymatic cleaner: £5–£8. Puppy pads: £8–£15. Total: approximately £104–£201.",
            "<strong>Step 3: Understand feeding terminology and apply it</strong> — 'Complete' food: provides all nutrients needed (choose this). 'Complementary' food: a mixer or topper only (never feed alone). 'Growth' or 'Puppy' labelled: formulated for higher energy and calcium needs. FEDIAF-compliant: meets European nutritional standards. Feed 4 meals/day at 8 weeks, reducing to 2 meals/day by 12 months.",
            "<strong>Step 4: Learn the vaccination and parasite control timeline</strong> — Week 8: first vaccination (£40–£70). Week 10–12: second vaccination. Week 12–14: safe to walk on public ground (1–2 weeks after second jab). Worming: every 2 weeks until 12 weeks, then monthly until 6 months, then every 3 months. Flea treatment: from 8 weeks, monthly. Total first-year parasite control: approximately £96–£180.",
            "<strong>Step 5: Decode behaviour signals early</strong> — Stress signals: lip licking, yawning when not tired, whale eye (showing whites), tucked tail, turning away. Play signals: play bow (front end down, back end up), loose wiggly body, open relaxed mouth. Recognising these within the first week prevents misreading your puppy and improves your bond.",
            "<strong>Step 6: Understand toilet training language and metrics</strong> — 'Fully house trained': no accidents indoors for 4+ consecutive weeks. 'Regression': a return to indoor accidents (common at 4–5 months during adolescence). Timeline: most puppies achieve reliability by 4–6 months with consistent training. Take puppy outside: every 1–2 hours, after meals (within 15 minutes), after naps, and after play.",
            "<strong>Step 7: Know your legal responsibilities</strong> — Microchipping: compulsory by 8 weeks (Microchipping of Dogs (England) Regulations 2015). Update details on an approved database when ownership changes. Dog licence: not required in England, Wales, or Scotland (abolished 1987). Northern Ireland requires a dog licence (£12.50). The Animal Welfare Act 2006 places a duty of care on all dog owners.",
            "<strong>Step 8: Learn grooming terms relevant to your breed</strong> — Single coat vs double coat (affects shedding and grooming frequency). Undercoat rake vs slicker brush (different tools for different coats). 'Hand-stripping' (terriers, spaniels): removing dead hair by hand, not clipping. Start grooming handling from 8 weeks: 2 minutes of gentle brushing daily, building to 10 minutes by 16 weeks.",
            "<strong>Step 9: Understand insurance terminology</strong> — Lifetime cover: covers conditions for the dog's entire life (recommended, £15–£40/month). Annual/time-limited: covers each condition for 12 months only, then excludes it. Excess: the amount you pay per claim (typically £50–£250). Pre-existing conditions: never covered. Take out insurance before the first vet visit to avoid exclusions. The ABI (Association of British Insurers) provides comparison guidance.",
            "<strong>Step 10: Plan your first-year milestones and costs</strong> — Month 1–3: vaccinations, socialisation, house training (vet costs: £120–£210). Month 3–6: puppy classes, lead training (£40–£80 for classes). Month 6–9: adolescence management, neutering decision (£150–£350 if proceeding). Month 9–12: proofing all training, adult food transition. Total first-year cost (excluding purchase price): approximately £1,200–£2,500 according to PDSA estimates.",
            "<strong>UK resource list</strong> — Kennel Club Good Citizen Scheme: free registration, nationwide classes. ABTC registered trainers: abtc.org.uk. PDSA cost-of-pet-ownership guide: pdsa.org.uk/paw. BVA pet health resources: bva.co.uk. RSPCA puppy care advice: rspca.org.uk.",
            "<strong>Emergency terminology</strong> — GDV (gastric dilatation-volvulus/bloat): life-threatening stomach twist, most common in deep-chested breeds. Parvovirus: highly contagious viral disease, often fatal in unvaccinated puppies. Hypoglycaemia: low blood sugar, risk in toy breed puppies under 12 weeks. Know these terms and their symptoms — early recognition saves lives."
        ]
    },
    5417: {  # Puppy Care Essentials: Key Terms
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Master the essential puppy care terms in the first week</strong> — Positive reinforcement: rewarding desired behaviour to increase its frequency. Socialisation: controlled exposure to new experiences during the 3–14 week critical period. House training: teaching your puppy to eliminate outdoors only. Crate training: using a crate as a safe, den-like space (not punishment).",
            "<strong>Step 2: Apply feeding terms correctly</strong> — Weigh food with a scale (±5g accuracy). A 10-week puppy of a medium breed needs approximately 200–300g of complete puppy food daily, split into 4 meals. 'Ad libitum' (free feeding) is not recommended for puppies — it prevents portion control and complicates house training. Stick to measured, timed meals.",
            "<strong>Step 3: Understand development stage terminology</strong> — Neonatal period (0–2 weeks): fully dependent on mother. Transitional period (2–4 weeks): eyes and ears open. Socialisation period (3–14 weeks): critical for exposure and learning. Juvenile period (14 weeks–sexual maturity): continued learning, increased independence. Adolescence (6–18 months): testing boundaries, hormonal changes.",
            "<strong>Step 4: Learn to read your puppy's body language</strong> — Calming signals (coined by Turid Rugaas): lip licking, turning head away, yawning, sniffing the ground. These are de-escalation signals. Arousal signs: stiff body, high tail, direct stare, raised hackles. Play signals: play bow, bouncy movements, soft mouth. Understanding these prevents misinterpretation and builds trust.",
            "<strong>Step 5: Apply dental care terms from 8 weeks</strong> — Deciduous teeth: 28 baby teeth present from 3–6 weeks. Permanent teeth: 42 adult teeth emerging from 12–28 weeks. Malocclusion: incorrect bite alignment (consult vet if noted). Plaque: bacterial film forming within 24 hours of eating. Tartar: hardened plaque (requires professional cleaning). Start brushing with a finger brush 3× per week from 8 weeks.",
            "<strong>Step 6: Decode veterinary paperwork</strong> — When you receive your vaccination card, check: vaccine product names, batch numbers, date administered, date of next dose, vet's signature. For microchip paperwork: verify the 15-digit number, register on an approved database (e.g., Petlog, IdentiChip), update your address and phone number within 24 hours of any change.",
            "<strong>Step 7: Understand exercise terms and limits</strong> — The 'five-minute rule': 5 minutes of structured exercise per month of age, up to twice daily. A 3-month puppy: maximum 15 minutes per walk. Free play in the garden is separate and less restricted. Over-exercising puppies (especially large breeds) before growth plates close (12–18 months) risks developmental orthopaedic disease.",
            "<strong>Step 8: Know parasite terminology</strong> — Endoparasites: internal parasites (roundworms, tapeworms, lungworm). Ectoparasites: external parasites (fleas, ticks, mites). Prophylactic treatment: preventive treatment given before infection occurs. Anthelmintic: worming medication. Puppies should be wormed every 2 weeks from 2–12 weeks of age, then monthly to 6 months. Cost: £5–£15 per treatment.",
            "<strong>Step 9: Apply socialisation terms systematically</strong> — Habituation: getting used to everyday stimuli (vacuum cleaner, doorbell). Desensitisation: gradual exposure to something feared. Counter-conditioning: pairing a feared stimulus with something positive. Flooding (exposure to feared stimulus at full intensity): AVOID — it causes trauma. Use the Puppy Socialisation Checklist approach: 3–5 new positive experiences per day.",
            "<strong>Step 10: Create a first-year timeline with key terms</strong> — Weeks 8–12: socialisation + vaccination + house training (foundation period). Weeks 12–16: first walks + puppy classes + bite inhibition (exploration period). Months 4–6: lead training + basic commands + teething (learning period). Months 6–12: adolescence + proofing + impulse control (consolidation period). Each period has specific goals — track progress weekly.",
            "<strong>UK-specific terms</strong> — DEFRA: Department for Environment, Food and Rural Affairs (regulates animal welfare). BVA: British Veterinary Association. RCVS: Royal College of Veterinary Surgeons (regulates vet practices). ABTC: Animal Behaviour and Training Council (UK regulatory body for trainers). Kennel Club: breed registration and Good Citizen Dog Scheme.",
            "<strong>Cost terminology</strong> — Excess (insurance): your contribution per claim. Lifetime cover: covers recurring conditions annually for life. Wellness plan: monthly subscription covering routine care (vaccinations, flea/worm, check-ups). Typical UK wellness plan: £10–£15/month. Lifetime insurance: £15–£40/month depending on breed and cover level."
        ]
    },
    4792: {  # Puppy Socialisation: A Complete Timeline Guide
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Start the socialisation log at 8 weeks</strong> — Create a checklist of 100 experiences across categories: people (20 types), dogs (10 types), environments (15 types), surfaces (10 types), sounds (15 types), objects (15 types), handling (15 types). Aim for 3–5 new positive exposures per day. Record each experience with date and the puppy's reaction (positive, neutral, or fearful).",
            "<strong>Step 2: Prioritise people exposure (weeks 8–12)</strong> — Your puppy should meet at least 50 different people by 14 weeks. Include: men with beards, people wearing hats/sunglasses, children (supervised), elderly people, people with umbrellas, people in uniforms, people of different ethnicities. Each meeting should be calm and positive — give the person a treat to offer your puppy.",
            "<strong>Step 3: Introduce environmental variety (weeks 8–14)</strong> — Before vaccinations are complete, carry your puppy to: high streets, train stations (external areas), car parks, outside schools at pick-up time, outdoor markets. After vaccinations: parks, woodland paths, beaches, urban centres. Aim for 3 new environments per week.",
            "<strong>Step 4: Expose to sounds systematically</strong> — Use a sound desensitisation playlist (free on Spotify/YouTube, search 'puppy socialisation sounds'). Start at 20% volume during mealtimes. Increase by 10% every 2 days. Key sounds: fireworks (critical for UK November preparations), thunderstorms, traffic, doorbells, vacuum cleaners, sirens, babies crying. Begin at 8 weeks; complete by 14 weeks.",
            "<strong>Step 5: Surface exposure (weeks 8–14)</strong> — Walk your puppy across: grass, gravel, sand, metal grates, rubber mats, tile, carpet, wooden decking, wet surfaces, and bubble wrap. Place treats on each new surface to create positive associations. Most puppies need 3–5 exposures to a novel surface before walking on it confidently.",
            "<strong>Step 6: Dog-to-dog socialisation (from 8 weeks)</strong> — Before full vaccination: arrange playdates with known, fully vaccinated adult dogs in private gardens. After vaccination: attend ABTC-accredited puppy classes (£40–£80 for 6 weeks). Ideal playmate: calm adult dog who naturally corrects rude puppy behaviour. Avoid dog parks until your puppy is at least 16 weeks with reliable recall.",
            "<strong>Step 7: Handling and husbandry exposure (weeks 8–16)</strong> — Daily handling exercises (2–3 minutes each): touch paws and nails, look inside ears, open mouth and touch teeth, lift tail, brush coat, wipe eyes. Pair every touch with a treat. By 12 weeks, your puppy should tolerate: ear examination, tooth inspection, nail handling, and being held still for 10 seconds. This prepares for vet visits (£35–£65 per check-up) and grooming.",
            "<strong>Step 8: Manage fear periods carefully</strong> — First fear period: 8–11 weeks (may show sudden fear of previously accepted stimuli). Second fear period: 6–14 months (varies by breed). During fear periods: do not force exposure. If the puppy shows fear (backing away, trembling, tucked tail), increase distance from the stimulus, offer treats at the puppy's comfort level, and retry at lower intensity the next day.",
            "<strong>Step 9: Attend formal socialisation classes (from 10–12 weeks)</strong> — Look for: ABTC-registered trainer, maximum 6–8 puppies per class, positive reinforcement only, clean disinfected flooring, vaccinated puppies only. The Kennel Club Good Citizen Puppy Foundation course is available nationwide and provides structured socialisation + basic training. Cost: £40–£80 for 6 weeks.",
            "<strong>Step 10: Continue socialisation through adolescence (4–18 months)</strong> — Socialisation does not end at 14 weeks — it transitions to 'maintenance'. Continue exposing your dog to novel experiences at least 3 times per week. Adolescent dogs (6–12 months) may show regression in confidence or reactivity — return to shorter, controlled exposures with high-value treats.",
            "<strong>UK-specific socialisation priorities</strong> — Fireworks: begin sound desensitisation by August for November (Bonfire Night). Livestock: expose to sheep, cattle, and horses at a safe distance if you walk in rural areas. Seagulls and waterfowl: common in coastal and park areas. Cycling and skateboarding: common in UK parks. Postmen: a high-frequency visitor that many dogs react to — desensitise early.",
            "<strong>Breed-specific note</strong> — Guardian breeds (German Shepherds, Rottweilers, Dobermans) need extra socialisation with strangers to prevent overprotectiveness. Herding breeds (Collies, Shelties) may develop chase responses — socialise around joggers and cyclists early. Toy breeds (Chihuahuas, Pomeranians) are often under-socialised due to being carried everywhere — let them walk and explore on their own four feet."
        ]
    },
    4570: {  # First-Time Dog Owner Essentials
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Research breeds thoroughly before committing</strong> — Consider: size (apartment vs house with garden), energy level (1–2 hours exercise vs 15 minutes), grooming needs (weekly brush vs professional grooming every 6–8 weeks at £30–£60), health predispositions, and lifespan (small breeds: 12–16 years, giant breeds: 6–10 years). Use the Kennel Club Breed Information Centre for UK-specific data.",
            "<strong>Step 2: Budget for the first year realistically</strong> — Purchase/adoption: £0 (rescue) to £500–£3,000+ (pedigree). First-year essentials: £1,200–£2,500 (PDSA estimate). Breakdown: food £300–£600, vet care £300–£700, insurance £180–£480, equipment £150–£300, training £40–£200, grooming £0–£300. Monthly ongoing cost: £100–£200 for a medium-sized dog.",
            "<strong>Step 3: Prepare your home before collection day</strong> — Essential equipment: crate (£30–£60), bed (£15–£30), bowls ×2 (£5–£10), collar + ID tag (£8–£15), lead 1.5m (£8–£15), poo bags (£5 for 300), toys ×3–5 (£15–£25), food (1 month supply, £15–£40), enzymatic cleaner (£5–£8). Puppy-proof one room thoroughly.",
            "<strong>Step 4: Register with a vet within 48 hours</strong> — Find an RCVS Practice Standards Scheme accredited practice (findavet.rcvs.org.uk). Book an initial health check. Bring: vaccination records, microchip details, any health information from the breeder/rescue. Discuss: vaccination schedule, neutering timeline, flea/worm protocol, insurance recommendations. First visit: free to £65.",
            "<strong>Step 5: Establish house rules from day one</strong> — Decide as a household before the dog arrives: allowed on furniture? Access to all rooms or restricted zones? Feeding from the table? Who handles morning/evening walks? Consistency across all family members is critical — conflicting rules cause confusion and anxiety.",
            "<strong>Step 6: Begin training immediately using positive reinforcement</strong> — Week 1: name recognition, toilet training, settling in crate/bed. Week 2–4: sit, down, stay (short duration). Month 2–3: lead walking, recall, leave it. Month 3–6: proof all commands in different environments. Use the reward-marker-repeat method: behaviour → marker ('yes!') → treat within 1–2 seconds.",
            "<strong>Step 7: Establish an exercise routine appropriate to age and breed</strong> — Puppies: 5 minutes per month of age, twice daily. Adult small breeds: 30–60 minutes daily. Adult medium breeds: 60–90 minutes daily. Adult large/working breeds: 90–120+ minutes daily. Mix walking with mental stimulation: sniff walks, puzzle feeders (£8–£15), training games. Always carry water on walks over 30 minutes.",
            "<strong>Step 8: Understand UK legal requirements</strong> — Microchipping: compulsory (Microchipping of Dogs (England) Regulations 2015). ID tag on collar in public: compulsory (Control of Dogs Order 1992) — must show owner's name and address. Lead on roads: required (Road Traffic Act 1988). Dog fouling: fines up to £1,000 (Clean Neighbourhoods and Environment Act 2005). Third-party liability insurance: strongly recommended (often included in home contents insurance).",
            "<strong>Step 9: Plan for absences and holidays</strong> — Options: dog sitter (£15–£30/day), boarding kennels (£15–£35/day), friend or family member (free but ensure competence). For work days: maximum 4 hours alone for adult dogs (RSPCA guidance). Options for longer days: doggy day-care (£20–£35/day), dog walker (£10–£15 per 30-minute walk). Research and trial before you need them.",
            "<strong>Step 10: Join a training class within the first month</strong> — The Kennel Club Good Citizen Dog Scheme (Bronze, Silver, Gold) provides a structured training pathway. Puppy classes: from 10–12 weeks (after first vaccination). Adult dog classes: any age. Look for ABTC-registered trainers (abtc.org.uk). Average cost: £40–£80 for a 6-week course. Group classes provide essential socialisation alongside training.",
            "<strong>Rescue dog note</strong> — Rescued dogs may need 2–4 weeks to decompress (the 'Rule of Threes': 3 days to decompress, 3 weeks to learn your routine, 3 months to feel at home). Avoid overwhelming with visitors, new experiences, or training demands in the first fortnight. Many rescue organisations offer post-adoption behavioural support.",
            "<strong>UK seasonal note</strong> — Plan for UK weather: waterproof dog coat (£10–£25) for short-coated breeds in winter. Paw wax (£5–£8) for protection against road salt (November–March). Reflective collar/lead for dark evenings (sunset before 4 PM, October–February). Cooling mat (£10–£20) for heatwaves (increasingly common June–August)."
        ]
    },
    4568: {  # Dog Dental Health
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Inspect your dog's mouth monthly</strong> — Gently lift the lips on each side and at the front. Healthy gums: pink (or pigmented in some breeds), firm, no swelling. Check for: tartar buildup (yellow/brown deposits at the gum line), red or bleeding gums, broken or loose teeth, lumps or growths, persistent bad breath beyond normal 'dog breath'. Report any abnormalities to your vet.",
            "<strong>Step 2: Establish daily tooth brushing</strong> — Use an enzymatic dog toothpaste (£4–£8, never human toothpaste — fluoride is toxic to dogs) and a dog toothbrush or finger brush (£3–£5). Brush at a 45-degree angle to the gum line using small circular motions. Focus on the outer surfaces where tartar accumulates most. Start at 30 seconds and build to 2 minutes over 2–3 weeks. Aim for daily brushing; minimum 3 times per week per BVDA recommendations.",
            "<strong>Step 3: Introduce brushing gradually over 14 days</strong> — Days 1–3: let dog lick toothpaste from your finger. Days 4–6: rub toothpaste on front teeth with your finger for 10 seconds. Days 7–9: introduce the brush, touch 2–3 teeth. Days 10–12: brush one side of the mouth (30 seconds). Day 13+: brush both sides (60–120 seconds). Reward after every session.",
            "<strong>Step 4: Use dental chews as a supplement, not a replacement</strong> — Look for VOHC (Veterinary Oral Health Council) accepted products — these have proven efficacy in reducing plaque or tartar. One dental chew per day is typical. Account for calories (50–90 kcal per chew for a medium-sized dog) and deduct from daily food ration. Monthly cost: £8–£15.",
            "<strong>Step 5: Schedule professional dental cleaning when needed</strong> — Signs it is time: visible tartar despite brushing, persistent bad breath, red gums, reluctance to eat hard food. Professional dental cleaning (scale and polish) requires general anaesthetic in the UK. Cost: £150–£400 depending on complexity. Includes: full examination, scaling, polishing, and extraction of any damaged teeth if needed.",
            "<strong>Step 6: Know your dog's dental disease risk factors</strong> — Small breeds (Yorkshire Terriers, Chihuahuas, Dachshunds): higher risk due to dental crowding. Brachycephalic breeds: misaligned teeth trap food. Greyhounds: breed predisposition to periodontal disease. Dogs over 3 years: approximately 80% show signs of dental disease according to the BVA. Diet: sticky or sugary treats increase plaque formation.",
            "<strong>Step 7: Choose appropriate chew toys for dental health</strong> — Rubber toys (moderate hardness): good for gum stimulation. Rope toys: flossing action between teeth (supervised use only). Avoid: antlers, bones, and very hard nylon chews — these cause tooth fractures (slab fractures of the upper premolars are the most common). The 'thumbnail test': if you cannot indent it with your thumbnail, it is too hard for your dog's teeth.",
            "<strong>Step 8: Address diet for dental support</strong> — Dry kibble provides more mechanical abrasion than wet food, but is not a standalone dental care method. Some dental-specific diets have a VOHC seal and larger kibble designed to scrub teeth. Adding raw carrots (as treats, 1–2 per day) provides natural abrasion. Fresh water after meals helps rinse food particles.",
            "<strong>Step 9: Recognise dental emergencies</strong> — Broken tooth with exposed pulp (pink/red centre): vet within 24–48 hours to prevent abscess. Swollen face or jaw: potential tooth root abscess — urgent vet visit. Sudden refusal to eat: may indicate oral pain. Bleeding from the mouth after trauma: apply gentle pressure and see a vet same day. Emergency dental treatment: £200–£500+.",
            "<strong>Step 10: Budget for lifetime dental care</strong> — Monthly toothpaste and brushes: £2–£4. Monthly dental chews: £8–£15. Annual vet dental check (included in health check): £35–£65. Professional cleaning (every 1–3 years depending on breed): £150–£400. Lifetime dental budget for a medium breed living 12 years: approximately £1,500–£3,000. Prevention through brushing reduces professional cleaning frequency significantly.",
            "<strong>Breed-specific guidance</strong> — Toy and small breeds: start dental care from 8 weeks; book first professional dental check at 1 year. Large breeds: lower risk of periodontal disease but higher risk of tooth fractures from chewing inappropriate objects. All breeds: the BVDA and BVA recommend daily brushing as the single most effective preventive measure.",
            "<strong>UK-specific note</strong> — The RCVS requires that all dental procedures involving extraction are performed by a veterinary surgeon, not a lay dental technician. 'Anaesthetic-free dental cleaning' is available in the UK but only addresses visible cosmetic tartar and cannot treat disease below the gum line — the BVA does not consider it an adequate substitute for proper veterinary dental care."
        ]
    },
    4566: {  # Seasonal Dog Care
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Prepare for UK spring (March–May)</strong> — Increase flea and tick prevention (ticks become active above 3.5°C). Check garden for toxic spring plants: daffodil bulbs, tulips, azaleas, lily of the valley. Begin allergy monitoring — pollen season starts March in southern England. Brush double-coated breeds daily during spring moult (2–4 weeks of heavy shedding). Budget for antihistamines if prescribed: £5–£15/month.",
            "<strong>Step 2: Summer safety (June–August)</strong> — Never leave dogs in cars — internal temperature reaches 47°C within 60 minutes on a 22°C day. Walk before 8 AM and after 7 PM in heatwaves. Test pavement with your palm: if too hot to hold for 5 seconds, it is too hot for paws (tarmac can reach 50°C+ in direct sun). Provide shade and fresh water at all times. Heatstroke signs: excessive panting, drooling, bright red tongue, collapse — cool with tepid (not cold) water and vet immediately.",
            "<strong>Step 3: Autumn precautions (September–November)</strong> — Conkers and acorns: toxic if ingested in quantity (atropine-like compounds). Harvest mice bring lungworm risk — ensure lungworm treatment is current (consult your vet, £8–£15/month prescription). Fireworks season: begin desensitisation 6–8 weeks before Bonfire Night (5 November). Create a safe den indoors, use DAP diffusers (£15–£20), and close curtains. Contact your vet about short-term anti-anxiety medication if needed (£10–£30).",
            "<strong>Step 4: Winter care (December–February)</strong> — Wipe paws after walks to remove road salt and grit (irritant and toxic if licked). Apply paw wax (£5–£8) before walks in icy conditions. Short-coated breeds (Greyhounds, Whippets, Staffies) need a waterproof coat (£10–£25) for walks below 5°C. Increase calories by 10–15% for active outdoor dogs. Check for antifreeze puddles on driveways — 1.5ml/kg body weight is lethal; symptoms appear within 1–12 hours.",
            "<strong>Step 5: Adjust exercise by season</strong> — Spring: gradually increase walk length as daylight extends (UK sunrise moves from 6:30 AM in March to 5:00 AM in May). Summer: split into two shorter walks (early morning + late evening). Autumn: maintain usual schedule but add reflective gear after mid-October (sunset before 6 PM). Winter: shorten walks in freezing conditions; supplement with indoor enrichment (puzzle feeders, £8–£15; sniff games; indoor training).",
            "<strong>Step 6: Maintain a year-round parasite control calendar</strong> — January–March: monthly wormer, flea treatment continues (heated homes sustain fleas year-round). April–October: add tick prevention (ticks most active). November–December: maintain flea and worm treatment, add lungworm prevention. Total annual parasite control cost: £96–£220 depending on products used. Use vet-prescribed products for best efficacy.",
            "<strong>Step 7: Manage coat and skin through the seasons</strong> — Spring moult (March–May): daily brushing for double-coated breeds, reduce bath frequency (dries skin). Summer: check for grass seeds in ears, paws, and undercoat after every walk (removal cost if embedded: £100–£250). Autumn: increase brushing as winter coat grows in. Winter: avoid over-bathing (dries skin in central heating); use a moisturising dog shampoo (£5–£10) once monthly maximum.",
            "<strong>Step 8: Adapt feeding for seasonal changes</strong> — Spring: maintain standard portions as activity increases. Summer: ensure fresh water is always available; add wet food or water to kibble to boost hydration. Autumn: begin slight calorie increase (5–10%) for dogs spending time outdoors. Winter: increase by 10–15% for active outdoor dogs. Monitor weight monthly and adjust — indoor-only dogs may need no seasonal change.",
            "<strong>Step 9: Prepare a seasonal emergency kit</strong> — Year-round: vet's phone number, nearest emergency vet address, pet first-aid kit (£15–£25). Summer additions: cooling mat (£10–£20), portable water bowl, electrolyte solution. Winter additions: paw balm, reflective gear, thermal blanket for the car. Autumn addition: DAP spray for firework anxiety (£10–£15). Keep the kit in your car and update twice yearly.",
            "<strong>Step 10: Schedule seasonal vet checks</strong> — Spring: annual vaccination booster and health check (£35–£65). Autumn: pre-winter dental check (tartar removal before reduced chewing activity). For senior dogs (7+): biannual health checks recommended. For dogs with seasonal allergies: vet visit at onset (typically March–April) to establish a management plan (antihistamines, medicated shampoo, or immunotherapy). Allergy management cost: £20–£80/month depending on severity.",
            "<strong>UK climate-specific note</strong> — The UK's maritime climate means frequent temperature fluctuations. A March morning can drop to 2°C and rise to 14°C by afternoon. Layer your dog's coat protection accordingly. Wet conditions are present approximately 150+ days per year — invest in a quality waterproof coat for breeds with single coats or very short coats.",
            "<strong>Breed-specific seasonal note</strong> — Arctic breeds (Huskies, Malamutes, Samoyeds) struggle in UK heatwaves above 25°C — provide a paddling pool, shade, and frozen treats. Hairless or minimal-coat breeds (Chinese Crested, Xoloitzcuintli) need sunscreen (pet-safe, £5–£10) on exposed skin in summer and protective clothing in winter. Spaniel breeds: check ear canals weekly in summer for grass seeds."
        ]
    },
    4563: {  # Dog Grooming Basics
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Determine your dog's coat type and grooming needs</strong> — Smooth coat (Staffies, Boxers): weekly brushing, rubber curry brush or bristle brush. Short double coat (Labradors, Beagles): twice-weekly brushing, slicker brush + undercoat rake during moult. Long coat (Setters, Afghan Hounds): daily brushing, pin brush + wide-tooth comb. Wire coat (Terriers, Schnauzers): hand-stripping every 6–8 weeks or professional clipping. Curly/wool coat (Poodles, Bichons): daily brushing, professional grooming every 4–6 weeks (£30–£60).",
            "<strong>Step 2: Assemble a basic grooming kit</strong> — Slicker brush (£5–£10): suits most coat types. Undercoat rake (£8–£15): for double-coated breeds. Steel comb (£5–£8): for detangling and finishing. Nail clippers or grinder (£8–£15): guillotine-style for small/medium, plier-style for large breeds. Ear cleaner (£5–£10). Dog shampoo (£5–£10). Towels (2–3). Total basic kit: £36–£68.",
            "<strong>Step 3: Establish a brushing routine from puppyhood</strong> — Start at 8 weeks: 2 minutes of gentle brushing daily, paired with treats. By 12 weeks: increase to 5 minutes. By 16 weeks: full grooming session of 10–15 minutes. This builds lifelong tolerance. If adopting an adult dog, reintroduce brushing in 30-second increments with high-value rewards.",
            "<strong>Step 4: Bathe your dog correctly</strong> — Frequency: every 4–8 weeks for most breeds (over-bathing strips natural oils). Use lukewarm water (37–38°C). Wet coat thoroughly, apply dog shampoo (never human shampoo — wrong pH), lather working from neck to tail, avoid eyes and ears. Rinse completely — residual shampoo causes irritation. Dry with towels, then low-heat hairdryer if tolerated (introduced gradually). In winter, bath indoors and ensure the dog is fully dry before going outside.",
            "<strong>Step 5: Trim nails every 2–4 weeks</strong> — If you can hear nails clicking on hard floors, they are too long. Cut 1–2mm at a time, angling at 45 degrees, stopping before the quick (pink area visible in light nails). For dark nails, trim in small increments and stop when you see a grey or pink oval in the nail cross-section. If you cut the quick: apply styptic powder (£3–£5) and apply pressure for 30 seconds. Professional nail trim: £5–£10 at a groomers.",
            "<strong>Step 6: Clean ears weekly</strong> — Apply vet-recommended ear cleaner (£5–£10) to the ear canal. Massage the base of the ear for 20–30 seconds. Let the dog shake. Wipe visible debris with cotton wool (never use cotton buds inside the ear canal). Normal ears: pale pink, minimal wax, no odour. Abnormal: red, swollen, dark discharge, strong smell, head shaking — vet visit needed (£35–£65 consultation). Floppy-eared breeds (Spaniels, Bassets) need extra vigilance.",
            "<strong>Step 7: Maintain dental hygiene as part of grooming</strong> — Brush teeth daily with enzymatic dog toothpaste (£4–£8) using a dog toothbrush or finger brush. Check gums for redness or swelling during each grooming session. Approximately 80% of dogs over 3 years have dental disease (BVA data). Prevention through brushing is far cheaper than professional cleaning under anaesthetic (£150–£400).",
            "<strong>Step 8: Check for parasites during every grooming session</strong> — Run a flea comb (£2–£4) through the coat, especially around the neck, base of tail, and belly. Look for: live fleas (1–2mm, fast-moving brown insects), flea dirt (black specks that turn red when placed on a wet white tissue), ticks (small grey/brown lumps, often around ears, groin, armpits). Remove ticks with a tick removal tool (£3–£5), twisting anticlockwise. Report any findings to your vet.",
            "<strong>Step 9: Know when to use a professional groomer</strong> — Breeds requiring professional grooming every 4–8 weeks: Poodles, Bichon Frises, Shih Tzus, Yorkies, Cocker Spaniels, Schnauzers. Cost: £25–£60 per session (small breed), £40–£80 (large breed). Look for groomers registered with the Pet Industry Federation or holding City & Guilds grooming qualifications. Always visit the salon first to check hygiene and handling practices.",
            "<strong>Step 10: Create a grooming schedule and budget</strong> — Weekly: brush coat, check ears, check teeth. Fortnightly: trim nails. Monthly: bathe (or as needed). Every 4–8 weeks (if applicable): professional grooming. Annual grooming costs: DIY grooming breeds (Labs, Staffies): £50–£100 (supplies). Professional grooming breeds (Poodles, Cockers): £300–£700. Budget an additional £20–£40 for replacement brushes and supplies annually.",
            "<strong>Breed-specific note</strong> — Double-coated breeds (Huskies, Collies, German Shepherds): never shave the coat — the double coat provides insulation in both hot and cold weather. Shaving can cause post-clipping alopecia and sunburn. Instead, use an undercoat rake to remove loose undercoat during moult, and consider a professional de-shedding treatment (£30–£50) twice yearly.",
            "<strong>UK seasonal grooming tip</strong> — After wet walks (common October–April), dry your dog's coat within 2 hours to prevent skin infections ('rain rot'). Pay special attention to ear canals, paw pads, and belly folds. A microfibre drying coat (£15–£25) speeds drying and is highly practical for the UK climate."
        ]
    },
    4414: {  # Harness vs Collar
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Assess your dog's walking behaviour</strong> — If your dog pulls consistently on walks, a front-clip harness (£15–£30) reduces pulling force by 50–60% compared to a collar. If your dog walks calmly at heel, a flat collar (£8–£20) is sufficient and legally satisfies the requirement for ID tag display under the Control of Dogs Order 1992.",
            "<strong>Step 2: Consider your dog's anatomy</strong> — Brachycephalic breeds (Pugs, Bulldogs, French Bulldogs): always use a harness — collars increase pressure on already compromised airways. Small breeds (Chihuahuas, Yorkies, Pomeranians): harness recommended — risk of tracheal collapse from collar pressure. Large/giant breeds: padded collar or harness based on pulling behaviour. Sighthounds (Greyhounds, Whippets): use a martingale collar (£10–£15) or hound-specific harness to prevent slip-outs from narrow heads.",
            "<strong>Step 3: Choose the correct harness type</strong> — Front-clip/Y-harness: best for pullers, redirects movement toward you. Back-clip harness: for trained walkers, easy to put on. Dual-clip: versatile, suits transition from training to walking. Step-in harness: good for head-shy dogs. Head collar (Gentle Leader style, £10–£20): for strong pullers under professional guidance only — improper use can cause neck injury.",
            "<strong>Step 4: Measure for a harness correctly</strong> — Chest girth: measure the widest part of the ribcage (behind front legs). Neck girth: measure around the base of the neck. Body length: from base of neck to base of tail. Compare measurements to the manufacturer's size chart. Between sizes? Choose the larger size and adjust straps. A properly fitted harness allows two flat fingers under all straps.",
            "<strong>Step 5: Measure for a collar correctly</strong> — Wrap a soft tape measure around the middle of your dog's neck. Add 2–5cm for comfort. You should be able to fit two fingers between the collar and the neck. A puppy collar needs replacing every 2–4 weeks during growth — buy inexpensive adjustable collars (£5–£10) until adult size is reached.",
            "<strong>Step 6: Introduce the harness gradually</strong> — Day 1: let dog sniff the harness, reward with treats. Day 2: drape over the back briefly, reward. Day 3: fasten loosely for 30 seconds, reward, remove. Day 4–5: wear for 2–5 minutes indoors. Day 6–7: wear on a short walk. Rushing the introduction creates negative associations — some dogs need up to 2 weeks to accept a harness happily.",
            "<strong>Step 7: Check fit before every walk</strong> — Ensure: no rubbing under armpits (the most common harness sore point), all buckles secure, straps not twisted, the harness has not shifted during wear. After walks, check for any redness or hair loss at contact points. Ill-fitting harnesses can cause chafing within a single walk and joint issues over time.",
            "<strong>Step 8: Combine collar and harness for maximum safety</strong> — Many trainers recommend: harness for lead attachment + collar for ID tag and backup. Use a double-ended lead (£12–£20) clipped to both the harness and collar for extra security. This is particularly important for: escape artists, reactive dogs, dogs near traffic, and newly adopted dogs whose behaviour is not yet known.",
            "<strong>Step 9: Budget for collar and harness needs</strong> — Puppy stage: 2–3 collars as they grow (£10–£30 total) + 1–2 harnesses (£15–£40). Adult dog: one quality harness (£20–£40, replaced every 1–2 years) + one collar (£8–£20, replaced annually). ID tag: £3–£5 (replace when details change). Total first-year collar/harness cost: £45–£95.",
            "<strong>Step 10: Know UK legal requirements</strong> — Under the Control of Dogs Order 1992, every dog in a public place must wear a collar with a tag showing the owner's name and address (postcode recommended). A harness alone does not satisfy this legal requirement — always attach an ID tag to the collar or harness. A microchip alone is not sufficient as a visual identifier. Fines for non-compliance: up to £5,000.",
            "<strong>Health consideration</strong> — A 2020 study published in Veterinary Record found that collar pressure during pulling can increase intraocular pressure, a concern for breeds predisposed to glaucoma (Cocker Spaniels, Basset Hounds). If your dog has eye conditions, use a harness exclusively.",
            "<strong>Seasonal UK note</strong> — In wet weather (frequent October–April), harness straps can cause skin irritation when damp against fur. Remove the harness after every walk and allow it to dry. Use a quick-dry material harness (mesh or biothane, £15–£30) for the wet season. Wash harnesses monthly to prevent bacterial buildup."
        ]
    },
    4413: {  # How to Measure Your Dog for a Harness
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Gather your measuring tools</strong> — Use a soft fabric tape measure (£1–£3 from haberdashery or pet shops). If unavailable, use a piece of string marked against a ruler. Have treats ready to keep your dog standing still. Measure when your dog is calm and standing on all four feet on a level surface.",
            "<strong>Step 2: Measure the chest girth (most important measurement)</strong> — Place the tape measure behind the front legs at the widest point of the ribcage. Pull snug but not tight — you should be able to slide a flat finger between the tape and the coat. Record in centimetres. Common measurements: small breeds 35–50cm, medium breeds 50–70cm, large breeds 70–90cm, giant breeds 90–120cm+.",
            "<strong>Step 3: Measure the neck girth</strong> — Place the tape around the base of the neck, where a collar would naturally sit (not the narrowest part of the neck, which is higher). This measurement helps with harnesses that have a neck loop or over-head design. Add 2cm to the measurement for comfort.",
            "<strong>Step 4: Measure the body length if required</strong> — Some harnesses require nose-to-tail or neck-to-tail length. Measure from the base of the neck (where the collar sits) to the base of the tail. This helps determine whether a standard or long-body harness is needed (relevant for Dachshunds, Corgis, Basset Hounds).",
            "<strong>Step 5: Weigh your dog</strong> — Many harness size charts use weight ranges as a secondary guide. Weigh using bathroom scales (hold the dog, weigh together, subtract your weight) or use your vet's scales at a free nurse clinic. Weight ranges vary significantly between manufacturers — always prioritise girth measurements over weight.",
            "<strong>Step 6: Compare measurements against the manufacturer's size chart</strong> — Every brand sizes differently. A 'medium' in one brand may be 'large' in another. Always check the specific product's size chart. If between sizes, choose the larger size — most harnesses have 5–10cm of adjustment range. For growing puppies, size up and tighten straps; recheck fit monthly.",
            "<strong>Step 7: Conduct a fit test once the harness arrives</strong> — Put the harness on and check: two flat fingers fit under every strap (neck, chest, belly). No straps sit in the armpit crease (causes chafing). The chest plate sits on the breastbone, not the throat. The back attachment sits between the shoulder blades, not on the neck. The harness does not shift side to side when the dog walks.",
            "<strong>Step 8: Test for escape-proofing</strong> — Gently pull the harness upward and backward (simulating a startle response). The harness should not slide over the head or tighten around the throat. If your dog can reverse out of it, tighten the neck strap by one hole or consider an escape-proof design with a belly strap (£20–£35).",
            "<strong>Step 9: Re-measure at regular intervals</strong> — Puppies: re-measure monthly until 12 months (18 months for giant breeds). Adult dogs: re-measure every 6 months or after significant weight change (gain or loss of 2kg+). Seasonal changes: some double-coated breeds are 2–3cm larger around the chest in winter coat versus summer. Adjust harness accordingly.",
            "<strong>Step 10: Record your dog's measurements for future purchases</strong> — Keep a note in your phone or on the dog's health record: chest girth, neck girth, weight, date measured. This saves time for future harness, coat, and collar purchases. Many online retailers accept returns but require the original packaging — measure accurately to avoid hassle.",
            "<strong>Breed-specific sizing notes</strong> — Dachshunds and Corgis: look for 'long body' or 'low profile' harnesses to avoid chest plate riding up. Deep-chested breeds (Greyhounds, Dobermans, Weimaraners): standard harnesses often gap at the belly — choose breeds-specific designs or add a belly strap. Barrel-chested breeds (Bulldogs, Staffies): measure at the widest barrel point, not behind the legs.",
            "<strong>Common sizing mistakes to avoid</strong> — Measuring over a thick coat without accounting for coat density (measure next to the skin for accurate base measurement, then add 1–2cm for coat). Using weight alone to select a size. Assuming your dog is the same size as another dog of the same breed (individual variation is significant). Not re-measuring a growing puppy frequently enough."
        ]
    },
    4411: {  # Dog Harnesses: Complete Guide
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Identify your primary need</strong> — Anti-pull training: choose a front-clip Y-harness (£15–£30). Daily walking (trained dog): back-clip harness (£12–£25). Car travel: crash-tested car harness (£20–£40, look for ECE R17 or equivalent safety testing). Hiking/outdoor: padded adventure harness with handle (£25–£50). Mobility assistance: support harness with lifting handle (£30–£60).",
            "<strong>Step 2: Understand harness types and their mechanisms</strong> — Y-harness (front clip): creates a turning motion when the dog pulls, gently redirecting them toward you. H-harness (back clip): two loops connected by a back strap, distributes pressure evenly. Step-in harness: two loops the dog steps into, buckles on the back — easiest for dogs who dislike things over their head. Norwegian harness: one chest strap + one belly strap, good for narrow-chested breeds.",
            "<strong>Step 3: Check for padding and comfort features</strong> — Padded chest plates prevent rubbing on the breastbone. Fleece-lined straps reduce friction behind the legs. Neoprene padding is waterproof (ideal for UK weather). Minimum padding width: 2cm for small breeds, 3cm for medium, 4cm for large breeds. Inadequate padding causes chafing within 2–3 walks — check after every walk for the first 2 weeks.",
            "<strong>Step 4: Ensure correct fit using the two-finger rule</strong> — You should be able to slide two flat fingers under every strap — snug enough that the harness does not rotate, loose enough that it does not restrict movement or breathing. The chest plate should sit on the sternum (breastbone), not pressing against the trachea (windpipe). No strap should cross the shoulder joint — this restricts natural stride.",
            "<strong>Step 5: Introduce the harness over 5–7 days</strong> — Day 1: place harness on the floor, let dog sniff and investigate, treat. Day 2: hold harness against dog's body, treat. Day 3: put harness on loosely for 1 minute, treat, remove. Day 4: wear harness for 5 minutes indoors with play. Day 5–7: wear harness on short garden walks. Never force the harness on — a negative first experience can create lasting resistance.",
            "<strong>Step 6: Maintain and clean your harness regularly</strong> — Nylon/polyester: machine wash on cold or hand wash with mild soap monthly. Leather: wipe clean, condition every 2–3 months. Check weekly: all buckles and clips snap securely, stitching is intact (especially at stress points), webbing is not frayed, metal fittings are not corroded. Replace any harness showing structural wear immediately.",
            "<strong>Step 7: Use the correct lead attachment point</strong> — Front clip (chest ring): for training and anti-pull work. Back clip (between shoulder blades): for everyday walking with a trained dog. Dual clip: use with a double-ended lead for transitional training (one end on front ring, one on back ring). Side clip: rare, used in canicross and bikejoring. Using the wrong clip point defeats the harness's purpose.",
            "<strong>Step 8: Address common harness problems</strong> — Rubbing under armpits: harness may be too large or straps too wide — try a Y-shaped design that avoids the armpit entirely. Dog reverses out: tighten the belly strap or switch to a 3-point harness with a belly band. Harness rotates to one side: adjust the chest strap symmetry, check that the back ring is centred on the spine. Dog freezes when harness is put on: go back to step 5 and desensitise more slowly.",
            "<strong>Step 9: Budget for harness ownership</strong> — Budget harness (basic nylon, no padding): £8–£15, suitable for calm walkers. Mid-range (padded, adjustable, reflective): £15–£30, suits most dogs. Premium (ergonomic, multi-point adjustment, weatherproof): £30–£50, for daily active use. Replace every 12–24 months depending on use intensity. A puppy may need 2–3 harness sizes in the first year (£30–£60 total).",
            "<strong>Step 10: Combine harness with appropriate training</strong> — A harness is a management tool, not a training solution. Pair with consistent loose-lead walking training: stop when the lead goes tight, reward when slack. A front-clip harness reduces pulling by approximately 50–60%, but training achieves long-term behaviour change. Budget for a 6-week training class (£40–£80) alongside your harness purchase for best results.",
            "<strong>UK legal note</strong> — A harness alone does not satisfy the legal requirement for a dog to wear an ID tag in public (Control of Dogs Order 1992). If using a harness instead of a collar, attach an ID tag to the harness D-ring or use a harness with a built-in ID tag window. The tag must display the owner's name and address.",
            "<strong>Car safety note</strong> — If using a harness for car travel in the UK, look for models that have been independently crash-tested (e.g., Centre for Pet Safety certification). A regular walking harness is not designed to restrain a dog in a collision — forces can exceed 30× the dog's body weight. Pair with a seatbelt tether (£5–£10) clipped to the back ring. Alternatively, use a secured crate in the boot."
        ]
    },
    4110: {  # Best Dog Joint Supplements UK
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Identify signs that suggest joint support is needed</strong> — Stiffness after rest (especially noticeable first thing in the morning), reluctance to jump or climb stairs, limping that improves after warming up, reduced activity or play, difficulty getting comfortable in bed, audible clicking from joints. If you observe any of these, book a vet examination (£35–£65) before starting supplements.",
            "<strong>Step 2: Understand the key active ingredients</strong> — Glucosamine hydrochloride: supports cartilage repair (therapeutic dose: 20mg/kg body weight daily). Chondroitin sulphate: slows cartilage breakdown (therapeutic dose: 10–15mg/kg daily). Omega-3 fatty acids (EPA/DHA from fish oil): anti-inflammatory (therapeutic dose: 50–75mg/kg combined EPA+DHA daily). Green-lipped mussel (GLM): natural source of omega-3s and glycosaminoglycans (dose: 15–25mg/kg daily).",
            "<strong>Step 3: Calculate the correct dose for your dog</strong> — Example for a 25kg Labrador: glucosamine 500mg/day, chondroitin 250–375mg/day, omega-3 (EPA+DHA) 1,250–1,875mg/day. Check the supplement label for amounts per tablet/scoop. Many over-the-counter products contain sub-therapeutic doses — compare the per-dose amount against the therapeutic ranges above.",
            "<strong>Step 4: Choose the right supplement format</strong> — Tablets/capsules (£10–£25/month): precise dosing, but some dogs refuse them. Liquid supplements (£12–£30/month): easy to add to food, good for fussy dogs. Powder supplements (£10–£20/month): mix into wet food. Chewable treats (£12–£25/month): palatable but check for added sugars and fillers. Topical or injectable (vet-administered): for severe cases under veterinary guidance.",
            "<strong>Step 5: Allow adequate time for results</strong> — Joint supplements typically take 4–8 weeks to show noticeable effects. Continue for a minimum of 12 weeks before concluding whether the supplement is effective. Glucosamine and chondroitin work by supporting cartilage maintenance, not providing immediate pain relief. If pain is acute, your vet may prescribe NSAIDs alongside supplements.",
            "<strong>Step 6: Support joint health with weight management</strong> — Excess weight is the single biggest modifiable risk factor for joint disease. A dog just 10% overweight experiences 20–30% more stress on joints. Target BCS 4–5 out of 9. For a 30kg dog that should be 27kg: reduce daily calories by 15–20% and increase low-impact exercise (swimming, slow walks) until target weight is reached over 8–12 weeks.",
            "<strong>Step 7: Adjust exercise for joint health</strong> — Low-impact activities: swimming (excellent — many UK hydrotherapy centres charge £25–£50 per session), lead walks on soft ground, controlled short walks (20–30 minutes, 2–3 times daily). Avoid: jumping, sharp turns, ball chasing on hard ground, excessive stair climbing. For large breeds: avoid running on hard surfaces until growth plates close (12–18 months).",
            "<strong>Step 8: Create an orthopaedic sleeping environment</strong> — Memory foam bed (£40–£80) with at least 10cm depth supports arthritic joints. Place the bed in a warm, draught-free location. A heated pet pad (£15–£25, low wattage, thermostatically controlled) provides additional comfort in UK winter months. Ensure the bed has a low entry point (below 8cm) so the dog does not need to step up.",
            "<strong>Step 9: Know when to escalate to veterinary treatment</strong> — Supplements are appropriate for: mild stiffness, early-stage joint wear, preventive care in predisposed breeds. Escalate to your vet for: persistent limping, pain on joint manipulation, sudden onset lameness, significant mobility loss. Veterinary options include: prescription NSAIDs (£15–£30/month), disease-modifying osteoarthritis agents (monthly injection, £30–£60), physiotherapy (£30–£60/session), or surgery in severe cases (£1,500–£5,000+).",
            "<strong>Step 10: Budget for long-term joint care</strong> — Monthly supplement: £10–£30. Orthopaedic bed: £40–£80 (replaced every 2–3 years). Weight management food (if needed): +£5–£15/month vs standard food. Hydrotherapy (if recommended): £25–£50/session, typically weekly or fortnightly. Annual vet joint assessment (included in health check): £35–£65. Total annual joint care budget: £200–£700 depending on severity.",
            "<strong>Breed-specific note</strong> — Breeds at highest risk: Labrador Retrievers, German Shepherds, Golden Retrievers, Rottweilers, and Bernese Mountain Dogs (hip and elbow dysplasia). Large and giant breeds benefit from preventive supplementation from 12 months of age. Small breeds (Dachshunds, Cavalier King Charles Spaniels) are prone to intervertebral disc disease (IVDD) — different from joint arthritis; discuss with your vet.",
            "<strong>UK regulation note</strong> — Pet supplements in the UK are regulated as 'complementary feed' under The Animal Feed (England) Regulations 2010. Unlike veterinary medicines, they do not require proof of efficacy before sale. Choose products from PFMA member companies or those with published clinical evidence. The Veterinary Medicines Directorate (VMD) oversees products making medicinal claims."
        ]
    },
    4103: {  # Best Dog Flea Treatment UK
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Understand the flea lifecycle</strong> — Adult fleas (5%) live on your dog. Eggs (50%), larvae (35%), and pupae (10%) live in your home — carpets, bedding, furniture. A single female flea lays up to 50 eggs per day. The lifecycle from egg to adult takes 2–8 weeks depending on temperature. This is why treating only the dog is insufficient — you must treat the home simultaneously.",
            "<strong>Step 2: Check your dog for fleas regularly</strong> — Use a fine-tooth flea comb (£2–£4) weekly, especially behind ears, around the neck, base of tail, and groin. Comb onto a white tissue or paper towel. If you see black specks, add a drop of water — flea dirt turns reddish-brown (digested blood). One live flea means there are likely 100+ in the home environment at various life stages.",
            "<strong>Step 3: Choose the right treatment type</strong> — Spot-on treatments (£5–£15/month): applied to the back of the neck. Oral tablets (£8–£20/month): systemic protection. Flea collars (£15–£30 for 6–8 months): continuous release. Sprays (£8–£15): for immediate kill but short duration. Vet-prescribed products (prescription spot-ons or tablets) are generally more effective than shop-bought alternatives. Always consult your vet for puppies under 8 weeks.",
            "<strong>Step 4: Apply treatment correctly for maximum effectiveness</strong> — Spot-on: part the fur at the base of the skull, apply directly to the skin (not the coat). Do not bathe the dog 48 hours before or after application. Oral tablets: give with food for maximum absorption. Flea collar: fit snugly (two-finger rule), trim excess length, check monthly for skin irritation. Follow the product's weight range exactly — never split doses between dogs.",
            "<strong>Step 5: Treat your home simultaneously</strong> — Wash all pet bedding at 60°C. Vacuum all carpets, rugs, sofas, and under furniture thoroughly (then dispose of the vacuum bag or empty the canister outside). Apply a household flea spray containing an insect growth regulator (IGR) such as methoprene (£8–£15 per can, covers 1–2 rooms). Repeat vacuuming daily for 2 weeks. Hot-wash soft furnishing covers where possible.",
            "<strong>Step 6: Treat all pets in the household</strong> — If you have multiple dogs or cats, every pet must be treated on the same day. Untreated pets serve as flea reservoirs, reinfesting treated animals. CRITICAL: never use dog flea products on cats — permethrin (common in dog treatments) is lethal to cats. Use species-specific products only.",
            "<strong>Step 7: Maintain a year-round prevention schedule</strong> — UK homes with central heating sustain fleas year-round. Do not stop treatment in winter. Apply monthly treatments on the same date each month (set a phone reminder). Mark your calendar: January flea treatment, February flea treatment, etc. Gaps in treatment allow re-infestation within 2–3 weeks.",
            "<strong>Step 8: Combine flea treatment with worming</strong> — Fleas carry tapeworm larvae — dogs can become infected by ingesting a flea during grooming. If your dog has had fleas, administer a tapeworm treatment (praziquantel, £3–£8) alongside flea treatment. Many combination products treat both fleas and worms in a single dose (£10–£20/month, vet-prescribed).",
            "<strong>Step 9: Monitor for treatment failure</strong> — If you still see fleas 48 hours after treatment, check: was the product applied correctly? Is it within date? Is the weight range correct? Are all household pets treated? Is the home environment treated? Resistance to some over-the-counter products is increasing in the UK — your vet can prescribe newer active ingredients (e.g., afoxolaner, fluralaner, sarolaner) with different mechanisms of action.",
            "<strong>Step 10: Budget for annual flea prevention</strong> — Shop-bought spot-on: £60–£120/year. Vet-prescribed spot-on or tablet: £96–£240/year. Combination flea + worm product: £120–£240/year. Household spray (1–2 applications/year): £8–£30. Flea comb: £2–£4 (one-off). Total annual prevention: £70–£270. Treatment of an established infestation (home treatment + vet products): £50–£150 one-off. Prevention is significantly cheaper than cure.",
            "<strong>Puppy-specific note</strong> — Most flea treatments are licensed from 8 weeks of age and a minimum body weight (often 1–2kg). For younger puppies with fleas, use a flea comb manually and wash bedding at 60°C. Consult your vet — they may prescribe a product suitable for very young puppies. Never use essential oil-based 'natural' flea treatments on puppies without veterinary approval.",
            "<strong>UK environmental note</strong> — Mild, wet UK winters increasingly support year-round flea activity outdoors. Hedgehog and fox fleas can infest dogs — particularly in gardens frequented by wildlife. If you have a wildlife-friendly garden, maintain strict monthly prevention and check your dog after evening garden access."
        ]
    },
    4096: {  # Best Dog Dental Care UK
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Start dental care from puppyhood</strong> — Begin handling your puppy's mouth from 8 weeks of age. Lift lips, touch teeth, and reward with treats for 30 seconds daily. Introduce a finger brush at 10 weeks. By 14 weeks, your puppy should tolerate 60 seconds of brushing. This early investment prevents a lifetime of dental disease — approximately 80% of dogs over 3 show signs of periodontal disease (BVA).",
            "<strong>Step 2: Choose the right dental tools</strong> — Finger brush (£3–£5 for 3-pack): ideal for beginners and small dogs. Dual-headed dog toothbrush (£2–£4): angled head reaches back molars. Enzymatic dog toothpaste (£4–£8): breaks down plaque biochemically. NEVER use human toothpaste (contains fluoride, toxic to dogs) or baking soda (causes stomach upset). Replace toothbrushes every 3 months.",
            "<strong>Step 3: Brush teeth daily using the correct technique</strong> — Hold the brush at a 45-degree angle to the gum line. Use small circular motions. Focus on the outer (cheek-facing) surfaces — this is where 85% of plaque accumulates. Brush from the back molars forward. Duration: 2 minutes total (30 seconds per quadrant). The inner surfaces are naturally cleaned by the tongue and saliva.",
            "<strong>Step 4: Supplement brushing with dental chews</strong> — Choose products with the VOHC (Veterinary Oral Health Council) seal of acceptance. One dental chew per day after the main meal. Calorie content: typically 50–90 kcal per chew for medium dogs — deduct from daily food ration. Monthly cost: £8–£15. Dental chews reduce plaque by up to 70% when combined with brushing (VOHC data).",
            "<strong>Step 5: Add a dental water additive for extra protection</strong> — VOHC-accepted water additives (£8–£12 per bottle, lasts 1–2 months) reduce bacterial load in the mouth. Add to fresh water daily as directed. Tasteless and odourless varieties are available for fussy dogs. This is a supplementary measure — not a replacement for brushing.",
            "<strong>Step 6: Schedule annual professional dental checks</strong> — Your vet should examine teeth and gums at every annual health check (£35–£65). Grade 1 dental disease (mild tartar, no gum recession): manage with home care. Grade 2–3 (moderate tartar, early gum recession): professional cleaning recommended. Grade 4 (severe disease, loose teeth, bone loss): extraction likely required. Early detection saves both suffering and money.",
            "<strong>Step 7: Understand professional dental cleaning</strong> — Requires general anaesthetic (UK). Includes: full oral examination, dental X-rays (identify sub-gum disease), ultrasonic scaling, polishing, and extraction of damaged teeth if needed. Cost: £150–£400 for a scale and polish; £300–£600+ if extractions are required. Recovery: soft food for 3–5 days, pain relief as prescribed. Most dogs eat normally within 24–48 hours.",
            "<strong>Step 8: Recognise dental emergencies</strong> — Broken tooth with visible pulp (pink/red centre): vet within 24–48 hours. Facial swelling (tooth root abscess): same-day vet visit. Bleeding from the mouth: apply gentle pressure, vet same day. Sudden refusal to eat hard food: dental pain likely, book vet within 48 hours. Emergency dental treatment: £200–£500+. Many pet insurance policies cover dental treatment caused by accident (check your policy).",
            "<strong>Step 9: Choose tooth-friendly treats and toys</strong> — Avoid: cooked bones (splinter risk), antlers, ice cubes, and nylon chews harder than the tooth enamel. The 'thumbnail test': if you cannot dent it with your thumbnail, it is too hard. Safe options: rubber Kong toys, rope toys (supervised), dental sticks, raw carrots. Toy rotation every 2–3 days maintains interest and distributes chewing forces across different tooth surfaces.",
            "<strong>Step 10: Budget for lifetime dental care</strong> — Monthly toothpaste + brush: £2–£4. Monthly dental chews: £8–£15. Annual vet dental check (included in health check): £0 extra (£35–£65 for the check-up). Professional cleaning every 1–3 years: £150–£400 per session. Total 12-year dental budget (medium breed): £1,200–£3,600. Investment in daily brushing reduces professional cleaning frequency by 50% or more, saving £500–£1,500 over a dog's lifetime.",
            "<strong>Breed-specific dental note</strong> — Toy and small breeds (Yorkshire Terriers, Chihuahuas, Maltese, Pomeranians): highest dental disease prevalence due to dental crowding. Begin professional cleanings earlier (often from age 2). Greyhounds: breed predisposition to periodontal disease — require vigilant home care. Brachycephalic breeds: misaligned teeth trap food — use interdental brushes (£3–£5) for accessible gaps.",
            "<strong>UK regulatory note</strong> — Only qualified veterinary surgeons (registered with the RCVS) may perform dental extractions on dogs in the UK. Non-veterinary 'anesthesia-free dental cleaning' is available but can only address visible cosmetic tartar — it cannot treat disease below the gum line, take X-rays, or perform extractions. The BVA position is that professional dental treatment under anaesthetic is the gold standard."
        ]
    },
    4089: {  # Best Dog Health and Care UK – Complete Guide
        "title": "Step-by-Step Practical Guide",
        "steps": [
            "<strong>Step 1: Register with an RCVS-accredited veterinary practice</strong> — Find a practice near your home (findavet.rcvs.org.uk). Look for RCVS Practice Standards Scheme accreditation. Register before you need emergency care. Typical UK consultation fee: £35–£65 for a standard appointment. Many practices offer free initial puppy/kitten checks and new client consultations.",
            "<strong>Step 2: Establish a preventive health calendar</strong> — Monthly: flea and worm treatment. Annually: vaccination booster + health check. Every 6 months (for seniors 7+): comprehensive health check with blood work. Weekly at home: check eyes, ears, teeth, skin, and body condition. Record observations in a health diary or phone notes app.",
            "<strong>Step 3: Maintain vaccinations on schedule</strong> — Core vaccines (DHP: distemper, hepatitis, parvovirus): primary course as a puppy, first annual booster, then every 3 years. Leptospirosis: annual booster (essential in the UK due to environmental risk). Kennel cough: annual if boarding or attending day-care (£20–£40 per dose). Keep the vaccination card safe and up to date.",
            "<strong>Step 4: Implement a nutrition plan based on life stage</strong> — Puppy: complete growth food, 3–4 meals/day reducing to 2. Adult: complete maintenance food, 2 meals/day. Senior (7+): senior-formulated food with joint support, moderate protein, 2 meals/day. Weigh food with a scale. Adjust portions based on monthly weight and BCS (ideal: 4–5 out of 9). Budget: £25–£60/month for mid-range food depending on breed size.",
            "<strong>Step 5: Establish a dental care routine</strong> — Daily brushing with enzymatic dog toothpaste (£4–£8). Weekly dental chews (VOHC-approved, £8–£15/month). Annual dental check at the vet. Professional cleaning when tartar is visible (£150–£400 under anaesthetic). Start from 8 weeks of age — prevention is far cheaper than treatment of advanced periodontal disease.",
            "<strong>Step 6: Maintain appropriate exercise for health</strong> — Small breeds: 30–60 minutes daily. Medium breeds: 60–90 minutes. Large/working breeds: 90–120+ minutes. Include both physical exercise (walking, running, swimming) and mental stimulation (puzzle feeders £8–£15, sniff walks, training sessions). Adjust for age: reduce high-impact exercise for puppies (5 minutes per month of age rule) and seniors (joint-friendly activities).",
            "<strong>Step 7: Monitor weight and body condition monthly</strong> — Weigh your dog monthly using a scale. Assess BCS: ribs should be easily felt without excess fat covering. View from above: visible waist behind ribs. View from side: abdominal tuck. Obesity affects approximately 1 in 3 UK dogs (PFMA data) and contributes to joint disease, diabetes, and reduced lifespan by 1.8–2.5 years.",
            "<strong>Step 8: Manage parasite prevention year-round</strong> — Fleas: monthly treatment (vet-prescribed, £8–£20/month). Worms: monthly to quarterly depending on risk (£3–£15/treatment). Ticks: monthly treatment during tick season (March–November, £5–£15/month). Lungworm: monthly prevention (endemic in many UK areas). Use vet-prescribed products for best efficacy. Annual cost: £96–£240.",
            "<strong>Step 9: Know when to seek veterinary help</strong> — Same-day vet visit: limping for more than 24 hours, vomiting more than twice, diarrhoea with blood, eye injury, skin wound more than 1cm, sudden behaviour change. Emergency (immediate): difficulty breathing, collapse, seizure, suspected poisoning (VPIS accessible through your vet), bloat symptoms, road traffic accident. Programme your vet's emergency number into your phone.",
            "<strong>Step 10: Budget for annual and lifetime healthcare</strong> — Annual routine costs: vaccinations £30–£50, parasite control £96–£240, health check £35–£65, dental maintenance £50–£100, food £300–£720. Total routine annual: £511–£1,175. Insurance (highly recommended): £15–£40/month (£180–£480/year). Without insurance, a single emergency surgery: £1,500–£5,000+. Lifetime cost of dog ownership (12 years, medium breed): £16,000–£33,000 (PDSA estimate).",
            "<strong>UK-specific health resources</strong> — PDSA: free veterinary care for eligible owners (means-tested, pdsa.org.uk). Blue Cross: reduced-cost veterinary care. RSPCA: welfare and rehoming. BVA: evidence-based pet health guidance (bva.co.uk). Kennel Club: breed-specific health information and DNA testing schemes.",
            "<strong>Senior dog health note (7+ years)</strong> — Biannual vet checks recommended. Screening for: arthritis (affects 80% of dogs over 8), dental disease, cognitive dysfunction syndrome (doggy dementia), kidney and liver function changes. Senior blood panel: £80–£150. Early detection of age-related conditions enables management that adds quality of life. Discuss a 'senior wellness plan' with your vet."
        ]
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# COMPARISON TABLES (Phase 10BN)
# ══════════════════════════════════════════════════════════════════════════════

COMPARISON_TABLES = {
    # ─── DOG FOOD ────────────────────────────────────────────────────────
    7172: [
        {
            "headers": ["Ingredient Type", "Common Examples", "Protein Quality", "Digestibility", "Typical Cost Impact", "Suitability"],
            "rows": [
                ["Fresh named meat", "Chicken 30%, Salmon 25%", "High (complete amino acid profile)", "85–95%", "Higher (premium tier)", "All life stages"],
                ["Dehydrated meat", "Dehydrated chicken 20%", "High (concentrated protein)", "80–90%", "Mid to high", "All life stages"],
                ["Meat meal", "Chicken meal, Lamb meal", "Moderate to high", "75–85%", "Mid-range", "Adult maintenance"],
                ["Meat and animal derivatives", "Unspecified blend", "Variable", "65–80%", "Lower (budget tier)", "Adult maintenance"],
                ["Plant protein", "Pea protein, Soya", "Moderate (may lack some amino acids)", "70–80%", "Lower", "Supplementary use"],
                ["Hydrolysed protein", "Hydrolysed poultry", "High (pre-broken for absorption)", "90–95%", "Higher (veterinary diets)", "Sensitive or allergic dogs"],
            ],
            "caption": "Protein Source Comparison in UK Dog Food"
        }
    ],
    3836: [
        {
            "headers": ["Factor", "Dry Kibble", "Wet / Tinned", "Raw (BARF/Prey Model)", "Freeze-Dried", "Fresh Cooked"],
            "rows": [
                ["Daily cost (25kg dog)", "£0.80–£1.80", "£2.50–£4.50", "£2.00–£5.00", "£3.00–£6.00", "£2.50–£5.00"],
                ["Moisture content", "6–10%", "70–85%", "60–75%", "2–5% (rehydrate to 70%+)", "60–75%"],
                ["Shelf life (opened)", "6 weeks (sealed container)", "48 hours (refrigerated)", "3–5 days (refrigerated)", "12+ months (sealed)", "5–7 days (refrigerated)"],
                ["Storage requirements", "Cool, dry cupboard", "Fridge after opening", "Freezer (-18°C) + fridge", "Cool, dry cupboard", "Fridge or freezer"],
                ["Dental benefit", "Mild mechanical abrasion", "Minimal", "Some (raw meaty bones)", "Minimal", "Minimal"],
                ["Preparation time", "None (scoop and serve)", "None (open and serve)", "15–30 min (thawing + portioning)", "5 min (rehydration)", "None (pre-portioned)"],
                ["PFMA/FEDIAF regulated", "Yes", "Yes", "Yes (if commercially produced)", "Yes", "Yes"],
            ],
            "caption": "Dog Food Format Comparison: Cost, Storage, and Practicality"
        },
        {
            "headers": ["Breed Size", "Daily Dry Food Amount", "Daily Wet Food Amount", "Estimated Monthly Cost (Mid-Range Dry)", "Estimated Monthly Cost (Mid-Range Wet)"],
            "rows": [
                ["Toy (2–5kg)", "40–100g", "150–400g", "£12–£20", "£30–£60"],
                ["Small (5–10kg)", "100–180g", "400–700g", "£15–£30", "£45–£80"],
                ["Medium (10–25kg)", "180–350g", "700–1,400g", "£25–£50", "£65–£120"],
                ["Large (25–40kg)", "350–500g", "1,400–2,000g", "£40–£70", "£100–£170"],
                ["Giant (40kg+)", "500–700g", "2,000–2,800g", "£55–£95", "£140–£230"],
            ],
            "caption": "Daily Feeding Amounts and Monthly Costs by Breed Size"
        }
    ],
    3837: [
        {
            "headers": ["Nutrient", "FEDIAF Minimum (Adult)", "FEDIAF Minimum (Growth)", "Typical Budget Dry", "Typical Mid-Range Dry", "Typical Premium Dry"],
            "rows": [
                ["Crude protein", "18%", "25%", "20–22%", "24–28%", "28–35%"],
                ["Crude fat", "5.5%", "8.5%", "8–10%", "12–16%", "14–18%"],
                ["Crude fibre", "No set max", "No set max", "3–5%", "2–4%", "2–3%"],
                ["Calcium", "0.5%", "0.8% (1.0% large breed max)", "0.8–1.2%", "1.0–1.4%", "1.0–1.5%"],
                ["Omega-3 (DHA+EPA)", "No minimum set", "0.05% DHA recommended", "Rarely added", "0.1–0.3%", "0.2–0.5%"],
                ["Ash content", "No set max", "No set max", "7–9%", "6–8%", "5–7%"],
            ],
            "caption": "Dry Dog Food Nutritional Comparison Against FEDIAF Standards"
        }
    ],
    3838: [
        {
            "headers": ["Feature", "Dry Kibble", "Wet Food (Tins/Trays)", "Mixed Feeding (75% Dry / 25% Wet)"],
            "rows": [
                ["Protein (dry-matter basis)", "24–32%", "35–50%", "Varies by ratio"],
                ["Hydration contribution", "Minimal (8–10% moisture)", "Significant (70–85% moisture)", "Moderate boost"],
                ["Dental impact", "Mild abrasion on tooth surfaces", "No mechanical cleaning", "Partial benefit from dry portion"],
                ["Palatability", "Moderate (varies by brand)", "High (strong aroma and texture)", "Enhanced by wet food addition"],
                ["Portion weight per meal (25kg dog)", "150–200g", "500–700g", "115–150g dry + 125–175g wet"],
                ["Waste and packaging", "1 bag per 4–6 weeks", "1–2 tins/trays per day", "Moderate (less wet food waste)"],
                ["Suitability for travel", "Highly portable", "Bulky, requires refrigeration", "Carry dry; add wet at destination"],
            ],
            "caption": "Dry vs Wet vs Mixed Feeding: A Side-by-Side Comparison"
        }
    ],
    3839: [
        {
            "headers": ["Life Stage", "Age Range", "Meals Per Day", "Protein Target (Minimum)", "Key Nutritional Priority", "Typical Monthly Cost"],
            "rows": [
                ["Weaning", "4–8 weeks", "4–5 (small portions)", "28%+", "Energy density, easy digestion", "£15–£25 (small breed)"],
                ["Early puppy", "8–16 weeks", "4 meals", "25–30%", "DHA, calcium, high energy", "£20–£35"],
                ["Growing puppy", "4–6 months", "3 meals", "25–28%", "Balanced growth, bone development", "£25–£45"],
                ["Adolescent", "6–12 months", "2–3 meals", "22–26%", "Lean muscle, joint support", "£30–£55"],
                ["Young adult (small/med)", "12–18 months", "2 meals", "22–26%", "Transition to adult maintenance", "£25–£50"],
                ["Young adult (large/giant)", "12–24 months", "2 meals", "22–26%", "Continued growth plate support", "£35–£65"],
            ],
            "caption": "Puppy Feeding Stages: From Weaning to Adult Transition"
        }
    ],

    # ─── TRAINING ────────────────────────────────────────────────────────
    4118: [
        {
            "headers": ["Training Method", "Core Principle", "Evidence Base", "Welfare Position (ABTC/BVA)", "Best For", "Limitation"],
            "rows": [
                ["Positive reinforcement", "Reward desired behaviours", "Strong (multiple peer-reviewed studies)", "Recommended", "All dogs, all ages", "Requires consistency and patience"],
                ["Clicker training", "Precise marker + reward", "Strong (operant conditioning research)", "Recommended (subset of positive reinforcement)", "Precision behaviours, tricks", "Requires timing practice"],
                ["Negative punishment", "Remove something desired to reduce behaviour", "Moderate (effective when humane)", "Acceptable when appropriate", "Jumping up, demand barking", "Must not cause distress"],
                ["Positive punishment", "Add aversive to reduce behaviour", "Limited long-term efficacy; welfare concerns", "Not recommended (ABTC, BVA)", "Not recommended", "Increases fear and aggression risk"],
                ["Dominance-based", "Assert 'alpha' status", "Debunked (based on flawed wolf studies)", "Condemned by ABTC, APBC, BVA", "Not recommended", "Damages trust, increases aggression"],
                ["Relationship-based", "Build communication and trust", "Growing evidence base", "Supported", "Multi-dog households, rescue dogs", "Less structured; harder to measure progress"],
            ],
            "caption": "Dog Training Methods: Evidence, Welfare, and Suitability"
        },
        {
            "headers": ["Behaviour Issue", "Positive Approach", "Expected Timeline", "When to Seek Professional Help"],
            "rows": [
                ["Pulling on lead", "Stop-start method + front-clip harness", "2–6 weeks of daily practice", "No improvement after 6 weeks"],
                ["Jumping on people", "Turn away, reward four paws on floor", "1–3 weeks with consistency", "If aggressive or uncontrollable"],
                ["Recall failure", "Long line training, high-value rewards", "4–8 weeks progressive distance", "No improvement after 8 weeks"],
                ["Separation anxiety", "Gradual departure training + enrichment", "4–12 weeks (may need medication)", "If dog causes self-harm"],
                ["Reactivity to other dogs", "Counter-conditioning at safe distance", "8–16 weeks or longer", "From the start — complex issue"],
                ["Resource guarding", "Trade-up exercises, management", "4–8 weeks (management ongoing)", "If any aggression toward people"],
            ],
            "caption": "Common Behaviour Issues: Positive Approaches and Timelines"
        }
    ],
    4125: [
        {
            "headers": ["Treat Type", "Calorie Content (approx.)", "Training Suitability", "Cost Per 100g", "Shelf Life (Opened)", "Allergy Risk"],
            "rows": [
                ["Freeze-dried liver", "3–4 kcal per piece", "Excellent (high value, quick to eat)", "£5–£8", "12 months (sealed)", "Low (single protein)"],
                ["Soft commercial training treats", "3–5 kcal per piece", "Excellent (soft, fast consumption)", "£2–£5", "4–8 weeks", "Varies (check ingredients)"],
                ["Cooked chicken breast (homemade)", "1.5–2 kcal per 1cm cube", "Excellent (very high value)", "£0.80–£1.20", "3–5 days (refrigerated)", "Low"],
                ["Mild cheddar cheese", "3–4 kcal per 1cm cube", "Good (high value, strong scent)", "£0.60–£0.90", "7 days (refrigerated)", "Moderate (dairy sensitivity)"],
                ["Daily kibble", "3–4 kcal per piece", "Low value (maintenance tasks only)", "£0.20–£0.50", "6 weeks", "Varies"],
                ["Dental chew sticks", "50–90 kcal per stick", "Poor (too large, slow to eat)", "£0.60–£1.00 per stick", "6 months (sealed)", "Varies"],
                ["Raw carrot sticks", "4 kcal per stick", "Low value (distraction only)", "£0.10", "5 days (refrigerated)", "Very low"],
            ],
            "caption": "Training Treat Comparison: Calories, Cost, and Suitability"
        }
    ],
    4139: [
        {
            "headers": ["Lead Type", "Length", "Material", "Typical Price", "Best Use", "Drawback"],
            "rows": [
                ["Standard fixed lead", "1.2–1.8m", "Nylon, leather, or biothane", "£8–£20", "Everyday walking, urban areas", "Limited range for training"],
                ["Long training line", "3–10m", "Lightweight nylon or biothane", "£10–£25", "Recall training, open spaces", "Can tangle; needs handling skill"],
                ["Adjustable multi-lead", "1–2m (variable)", "Nylon with ring adjustments", "£12–£25", "Versatile: short or long modes", "Rings can snag or confuse"],
                ["Slip lead", "1.2–1.5m", "Rope or nylon", "£5–£12", "Quick on/off (vets, shows)", "Tightens around neck; not for pullers"],
                ["Retractable lead", "3–8m", "Cord or tape in plastic housing", "£10–£25", "Not recommended for training", "Inconsistent tension; safety concerns"],
                ["Double-ended lead", "1.5–2m", "Nylon with 2 clips", "£12–£20", "Dual-clip harness training", "Heavier than single-clip leads"],
            ],
            "caption": "Dog Lead Types: Length, Cost, and Use Case Comparison"
        }
    ],
    4132: [
        {
            "headers": ["Training Milestone", "Age Range", "Key Skills to Develop", "Session Length", "Recommended Approach"],
            "rows": [
                ["Foundation period", "8–12 weeks", "Socialisation, name recognition, toilet training", "2–3 min, 5–6× daily", "Positive exposure, treat pairing"],
                ["Early learning", "12–16 weeks", "Sit, down, first lead walks, bite inhibition", "5 min, 3–4× daily", "Lure-reward, clicker introduction"],
                ["Skill building", "4–6 months", "Stay, recall (on lead), leave it, grooming tolerance", "5–10 min, 2–3× daily", "Progressive difficulty, varied environments"],
                ["Adolescence management", "6–9 months", "Impulse control, loose-lead walking, extended recall", "10–15 min, 2× daily", "Variable reward, proofing in distractions"],
                ["Consolidation", "9–12 months", "Reliable recall (off-lead), settle on command, manners", "15 min, 1–2× daily", "Real-world proofing, reduced treat frequency"],
                ["Ongoing maintenance", "12 months+", "All skills maintained, new tricks, mental enrichment", "10–15 min daily", "Variable reinforcement, ongoing socialisation"],
            ],
            "caption": "Puppy Training Milestones: First Year Progression"
        }
    ],
    4042: [
        {
            "headers": ["Walking Equipment", "Function", "Cost Range", "Recommended For", "Not Suitable For"],
            "rows": [
                ["Flat collar + standard lead", "Basic identification and control", "£13–£35 total", "Trained dogs, calm walkers", "Pullers, brachycephalic breeds"],
                ["Front-clip harness + standard lead", "Anti-pull training", "£23–£50 total", "Pullers, training in progress", "Already well-trained dogs (unnecessary)"],
                ["Back-clip harness + standard lead", "Comfortable daily walking", "£20–£45 total", "Trained walkers, small breeds", "Persistent pullers (can encourage pulling)"],
                ["Head collar + standard lead", "Maximum steering control", "£18–£35 total", "Strong pullers under professional guidance", "Unsupervised use, dogs not desensitised"],
                ["Martingale collar + standard lead", "Prevents slip-outs", "£15–£30 total", "Sighthounds, narrow-headed breeds", "Pullers (still puts pressure on neck)"],
                ["Long line (5–10m)", "Recall training, distance work", "£10–£25", "Training in open spaces", "Urban walking, near traffic"],
            ],
            "caption": "Dog Walking Equipment Combinations: Use Cases and Costs"
        }
    ],
    4791: [
        {
            "headers": ["Treat Category", "Examples", "When to Use", "Calorie Impact", "Monthly Budget"],
            "rows": [
                ["Ultra-high value", "Fresh chicken, cheese, liver paste", "Breakthrough moments, extreme distractions", "Moderate per treat (use small quantities)", "£3–£6 (homemade) or £8–£15 (shop)"],
                ["High value", "Freeze-dried liver, sprats, soft commercial treats", "New behaviours, challenging environments", "3–5 kcal each", "£5–£10"],
                ["Medium value", "Semi-moist training treats, dried fish skins", "Proofing known behaviours in new settings", "3–5 kcal each", "£4–£8"],
                ["Low value", "Daily kibble portion, plain rice cakes", "Well-known behaviours, easy repetitions", "3–4 kcal each", "£0 (from food ration)"],
                ["Environmental reward", "Access to sniffing, toy play, off-lead freedom", "Reward after recall, sustained good behaviour", "Zero calories", "£0"],
                ["Long-lasting chew", "Stuffed Kong, lick mat, pizzle stick", "Calm settling, crate training, alone time", "50–150 kcal", "£8–£20"],
            ],
            "caption": "Training Reward Hierarchy: Types, Uses, and Costs"
        }
    ],

    # ─── EDUCATIONAL ─────────────────────────────────────────────────────
    4568: [
        {
            "headers": ["Dental Care Method", "Plaque Reduction", "Ease of Use", "Daily Time Required", "Monthly Cost", "Evidence Level"],
            "rows": [
                ["Daily tooth brushing", "Up to 80–90% (outer surfaces)", "Moderate (requires training)", "2 minutes", "£2–£4 (paste + brush)", "Strong (BVDA recommended)"],
                ["VOHC dental chews", "Up to 70% (in studies)", "Easy (give after meals)", "2–3 minutes chewing", "£8–£15", "Good (VOHC-accepted)"],
                ["Dental water additive", "20–40% bacterial reduction", "Very easy (add to water)", "None", "£5–£10", "Moderate"],
                ["Dental-specific diet", "Variable (VOHC diet accepted)", "Easy (replace normal food)", "None extra", "£5–£15 above standard food", "Moderate (for VOHC products)"],
                ["Raw bones (recreational)", "Some mechanical cleaning", "Requires supervision", "10–15 min supervised", "£2–£5 per bone", "Limited; tooth fracture risk noted"],
                ["Professional cleaning", "100% (under anaesthetic)", "Requires vet visit + anaesthetic", "One-off procedure", "£150–£400 per session", "Strong (gold standard)"],
            ],
            "caption": "Dog Dental Care Methods: Effectiveness and Practicality Compared"
        }
    ],
    4566: [
        {
            "headers": ["Season", "Top 3 Hazards", "Preventive Actions", "Key Cost/Budget Item"],
            "rows": [
                ["Spring (Mar–May)", "Toxic plants, ticks, pollen allergies", "Garden audit, start tick prevention, monitor scratching", "Tick treatment: £5–£15/month"],
                ["Summer (Jun–Aug)", "Heatstroke, burnt paw pads, blue-green algae", "Walk early/late, test pavements, avoid stagnant water", "Cooling mat: £10–£20 one-off"],
                ["Autumn (Sep–Nov)", "Conkers/acorns, fireworks, lungworm", "Avoid fallen nuts, desensitise sounds, treat for lungworm", "DAP diffuser: £15–£20; lungworm: £8–£15/month"],
                ["Winter (Dec–Feb)", "Antifreeze, road salt, hypothermia", "Clean paws, store antifreeze safely, use dog coats", "Waterproof coat: £10–£25; paw wax: £5–£8"],
                ["Year-round (all)", "Fleas, obesity, dental disease", "Monthly flea treatment, weigh monthly, brush teeth daily", "Flea: £8–£20/month; toothpaste: £4–£8"],
                ["Year-round (indoor)", "Chocolate, xylitol, small objects", "Store safely, dog-proof rooms, educate family", "Child locks: £5–£10; bitter spray: £5–£8"],
            ],
            "caption": "Seasonal Dog Care: Hazards, Prevention, and Costs by Season"
        }
    ],
    4563: [
        {
            "headers": ["Coat Type", "Breeds (Examples)", "Brushing Frequency", "Professional Grooming", "Recommended Brush", "Annual Grooming Cost (DIY + Professional)"],
            "rows": [
                ["Smooth/short", "Staffie, Boxer, Beagle", "Weekly", "Rarely needed", "Rubber curry brush, bristle brush", "£30–£60"],
                ["Short double", "Labrador, Husky, GSD", "2–3× weekly (daily during moult)", "Optional de-shedding 2×/year", "Slicker brush, undercoat rake", "£60–£160"],
                ["Long single", "Setter, Afghan Hound, Maltese", "Daily", "Every 6–8 weeks", "Pin brush, wide-tooth comb", "£250–£500"],
                ["Wire/rough", "Terriers, Schnauzer, Wirehaired Pointer", "2–3× weekly", "Hand-stripping or clipping every 6–8 weeks", "Stripping knife, slicker brush", "£280–£550"],
                ["Curly/wool", "Poodle, Bichon Frise, Labradoodle", "Daily", "Every 4–6 weeks", "Slicker brush, steel comb", "£350–£700"],
                ["Hairless/minimal", "Chinese Crested, Xoloitzcuintli", "Weekly (skin care)", "Rarely needed", "Soft cloth, moisturiser", "£40–£80 (skin products)"],
            ],
            "caption": "Dog Grooming Needs by Coat Type: Frequency and Cost Comparison"
        }
    ],
    4414: [
        {
            "headers": ["Factor", "Flat Collar", "Front-Clip Harness", "Back-Clip Harness", "Head Collar", "Martingale Collar"],
            "rows": [
                ["Neck pressure", "High when pulling", "None (chest distribution)", "None (back distribution)", "Moderate (muzzle and neck)", "Moderate (limited tightening)"],
                ["Anti-pull effect", "None", "Strong (redirects dog's direction)", "None (may encourage pulling)", "Very strong (controls head direction)", "Mild"],
                ["Ease of fitting", "Very easy", "Moderate (multiple straps)", "Easy (step-in or clip-on)", "Moderate (needs desensitisation)", "Easy"],
                ["ID tag legal compliance (UK)", "Yes", "Yes (if tag attached)", "Yes (if tag attached)", "No (separate collar needed)", "Yes"],
                ["Risk of escape", "Moderate (if not fitted correctly)", "Low", "Low", "Low (if fitted properly)", "Very low (tightens when pulled)"],
                ["Typical cost", "£8–£20", "£15–£35", "£12–£25", "£10–£20", "£10–£15"],
                ["Suitability for brachycephalic breeds", "Not recommended", "Recommended", "Recommended", "Not suitable", "Not recommended"],
            ],
            "caption": "Collar and Harness Types: Safety, Function, and Cost Comparison"
        }
    ],
    7341: [
        {
            "headers": ["Day", "Priority Tasks", "Toilet Trips (Minimum)", "Expected Challenges", "Key Tip"],
            "rows": [
                ["Day 1", "Settle in, show toilet area, first meal", "8–10", "Whining, not eating, hiding", "Keep calm, limit to 1–2 rooms"],
                ["Day 2", "Establish meal times, begin toilet routine", "8–10", "Overnight accidents, restlessness", "Set a 3-hour alarm overnight"],
                ["Day 3", "Start gentle handling (paws, ears, mouth)", "8–10", "Mouthing, nipping during handling", "Pair every touch with a treat"],
                ["Day 4", "Introduce crate for naps, name recognition", "6–8", "Whining in crate, over-tiredness", "Keep crate sessions under 30 min"],
                ["Day 5", "First night in crate (if ready), socialisation", "6–8", "Night whining in crate", "Place crate beside your bed"],
                ["Day 6–7", "Continue routine, first vet registration call", "6–8", "Testing boundaries, increased confidence", "Consistency is more important than perfection"],
            ],
            "caption": "First Week with a New Puppy: Day-by-Day Priority Guide"
        }
    ],
    7337: [
        {
            "headers": ["Vaccine Type", "Diseases Covered", "Schedule", "Booster Frequency", "Estimated Cost (UK)", "Required or Optional"],
            "rows": [
                ["DHP (core)", "Distemper, hepatitis, parvovirus", "8 weeks + 10–12 weeks", "12 months, then every 3 years", "£40–£70 per dose", "Core (strongly recommended)"],
                ["Leptospirosis (L2 or L4)", "2 or 4 strains of leptospirosis", "8 weeks + 10–12 weeks", "Annually", "Included in primary or £20–£40", "Core in the UK"],
                ["Kennel cough (intranasal)", "Bordetella + parainfluenza", "From 3 weeks before boarding", "Annually", "£20–£40", "Optional (required by kennels)"],
                ["Rabies", "Rabies virus", "From 12 weeks", "Every 1–3 years (for travel)", "£50–£80", "Optional (required for travel)"],
                ["Canine herpesvirus", "Neonatal herpes (breeding dogs)", "During pregnancy", "Per pregnancy", "£30–£50", "Optional (breeding bitches only)"],
                ["Lyme disease", "Borrelia burgdorferi", "From 12 weeks", "Annually", "£30–£50", "Optional (high-risk areas only)"],
            ],
            "caption": "UK Dog Vaccination Schedule: Types, Timing, and Costs"
        }
    ],
    7340: [
        {
            "headers": ["Teething Stage", "Age Range", "Teeth Involved", "Typical Signs", "Recommended Soothing Method"],
            "rows": [
                ["Deciduous eruption", "3–6 weeks", "28 baby teeth emerge", "Gum sensitivity, beginning to chew", "Soft toys, mother's milk"],
                ["Incisors replacement", "12–16 weeks", "Front teeth (12 incisors)", "Increased mouthing, found teeth", "Frozen flannel, cold carrot sticks"],
                ["Canine replacement", "16–20 weeks", "4 canine teeth", "Peak discomfort, heavy chewing", "Frozen rubber toys, gentle play"],
                ["Premolar replacement", "16–20 weeks", "16 premolars", "Drooling, reluctance to eat kibble", "Soaked kibble, soft treats"],
                ["Molar emergence", "20–28 weeks", "10 molars (new, no baby equivalent)", "Back-jaw chewing, gum redness", "Rubber chew toys, frozen Kongs"],
                ["Complete adult dentition", "6–7 months", "42 adult teeth present", "Chewing decreases, comfort returns", "Maintain appropriate chew toys"],
            ],
            "caption": "Puppy Teething Timeline: Stages, Signs, and Soothing Methods"
        }
    ],
    4089: [
        {
            "headers": ["Health Area", "Preventive Action", "Frequency", "UK Cost Range", "Consequence of Neglect"],
            "rows": [
                ["Vaccination", "Core vaccines (DHP + lepto)", "Annual booster", "£30–£50/year", "Fatal diseases (parvovirus, distemper)"],
                ["Parasite control", "Flea, worm, tick treatment", "Monthly", "£96–£240/year", "Disease transmission, discomfort, anaemia"],
                ["Dental care", "Daily brushing + annual check", "Daily / annually", "£50–£100/year (home) + £150–£400 (professional)", "Periodontal disease (80% of dogs over 3)"],
                ["Weight management", "Weigh monthly, BCS assessment", "Monthly", "£0 (home scales) or free at vet nurse clinics", "2-year reduced lifespan, joint disease, diabetes"],
                ["Exercise", "Age-appropriate daily exercise", "Daily", "£0–£15/walk (if using dog walker)", "Obesity, behavioural problems, muscle loss"],
                ["Health screening", "Annual vet check (biannual for seniors)", "Annually / biannually", "£35–£65 per check; £80–£150 with bloods", "Late diagnosis of treatable conditions"],
            ],
            "caption": "Dog Health Essentials: Prevention, Frequency, and Cost Summary"
        }
    ],
}


# ══════════════════════════════════════════════════════════════════════════════
# CITATION / UK AUTHORITY REFERENCES (Phase 10BM)
# ══════════════════════════════════════════════════════════════════════════════

CITATION_PARAGRAPHS = {
    # ─── DOG FOOD (3+ additional UK authority references per post) ────
    7172: (
        '<p>According to the <strong>Pet Food Manufacturers\' Association (PFMA)</strong>, over 90% of UK pet food is produced by PFMA members who adhere to the PFMA Code of Practice for the Manufacture of Pet Food. '
        'The <strong>FEDIAF (European Pet Food Industry Federation)</strong> publishes annually updated nutritional guidelines that set minimum and maximum nutrient levels for complete pet foods — the 2023 revision recommends a minimum of 18% crude protein for adult dog maintenance and 25% for growth. '
        'Under <strong>The Animal Feed (England) Regulations 2010</strong>, all pet food sold in the UK must be accurately labelled with a full ingredient declaration, analytical constituents, and feeding guidelines. '
        'The <strong>Food Standards Agency (FSA)</strong> oversees food safety across the supply chain, while <strong>DEFRA</strong> (Department for Environment, Food and Rural Affairs) is responsible for animal feed legislation and enforcement. '
        'The <strong>BVA (British Veterinary Association)</strong> recommends that owners consult their vet before making significant dietary changes, particularly when considering raw, grain-free, or prescription diets.</p>'
    ),
    3836: (
        '<p>The <strong>PFMA</strong> reports that approximately 12 million UK households own a pet, with dogs being the most popular companion animal at an estimated 13 million dogs nationwide. '
        'All complete dog foods sold in the UK must comply with <strong>FEDIAF nutritional guidelines</strong>, which are reviewed annually by independent nutritional scientists and set evidence-based minimum and maximum nutrient levels for each life stage. '
        'The <strong>BVA</strong> advises that selecting a diet labelled "complete" and appropriate for the dog\'s life stage is the single most important nutritional decision an owner can make. '
        '<strong>DEFRA</strong> enforcement officers conduct regular inspections of pet food manufacturers to ensure compliance with The Animal Feed (England) Regulations 2010 and EU-retained feed hygiene regulations. '
        'The <strong>RCVS (Royal College of Veterinary Surgeons)</strong> maintains that veterinary professionals are best placed to advise on nutrition, particularly for dogs with health conditions requiring dietary management.</p>'
    ),
    3837: (
        '<p>The <strong>PFMA Code of Practice</strong> requires member manufacturers to conduct nutritional adequacy testing and maintain full traceability of ingredients. '
        '<strong>FEDIAF nutritional guidelines (2023 revision)</strong> set the minimum crude protein level for adult maintenance at 18% on a dry-matter basis, with higher requirements for growth (25%) and reproduction (25%). '
        'The <strong>FSA</strong> monitors mycotoxin levels in cereals used in pet food production, with UK maximum limits aligned with EU-retained Regulation (EC) No 1881/2006. '
        'According to <strong>DEFRA\'s</strong> Code of Practice for the Welfare of Dogs, owners have a legal duty under the Animal Welfare Act 2006 to provide a suitable diet — this includes ensuring food is nutritionally complete and appropriate for the dog\'s age, breed, and health status. '
        'The <strong>BVA</strong> has published position statements noting that grain-free diets have not been shown to be nutritionally superior for the majority of dogs and may be associated with dilated cardiomyopathy (DCM) in certain cases.</p>'
    ),
    3838: (
        '<p>Research published in the <strong>British Veterinary Association\'s Veterinary Record</strong> has examined the nutritional differences between wet and dry dog food formats, noting that both can meet FEDIAF standards when formulated as complete diets. '
        'The <strong>PFMA</strong> states that the choice between wet and dry food should be based on the individual dog\'s needs, owner lifestyle, and veterinary advice rather than a blanket recommendation. '
        '<strong>FEDIAF guidelines</strong> require that moisture content be declared on the label, enabling owners to compare nutritional values on a dry-matter basis. '
        'The <strong>DEFRA</strong>-enforced labelling regulations require all pet food to display "complementary" or "complete" status clearly, preventing confusion about whether a product can serve as a sole diet. '
        'The <strong>BVA</strong> recommends that dogs with specific dental, renal, or digestive conditions discuss food format choices with their veterinary surgeon, as the physical form of food can impact health outcomes.</p>'
    ),
    3839: (
        '<p>The <strong>PFMA Puppy Contract</strong>, developed in partnership with the RSPCA and the Animal Welfare Foundation, includes nutritional guidance recommending that new puppy owners continue the breeder\'s diet for at least two weeks before transitioning. '
        '<strong>FEDIAF nutritional guidelines</strong> set specific requirements for growth: minimum 25% crude protein, minimum 8.5% crude fat, and controlled calcium levels (maximum 1.0% for large breed puppies) to support healthy skeletal development. '
        'The <strong>BVA</strong> and <strong>BSAVA (British Small Animal Veterinary Association)</strong> publish guidance stating that large and giant breed puppies require specially formulated growth diets to reduce the risk of developmental orthopaedic disease. '
        '<strong>DEFRA</strong> requires that all puppy food labels include the specific life stage ("for growth" or "puppy") and feeding guidelines based on expected adult body weight. '
        'The <strong>Kennel Club</strong> recommends consulting breed-specific feeding guides and using growth charts to track puppy development against expected weight milestones.</p>'
    ),

    # ─── TRAINING (2+ additional UK authority references per post) ────
    4118: (
        '<p>The <strong>Animal Behaviour and Training Council (ABTC)</strong>, recognised by the UK Government as the regulatory body for animal behaviourists and trainers, maintains a public register of practitioners who meet defined standards of knowledge and practice. '
        'The <strong>BVA</strong> and <strong>BSAVA</strong> jointly advocate for positive reinforcement-based training methods, stating that aversive techniques increase the risk of fear, anxiety, and aggression. '
        'The <strong>RSPCA</strong> reports that behavioural issues are the leading reason for dog rehoming in the UK, underlining the importance of early, evidence-based training.</p>'
    ),
    4125: (
        '<p>Under <strong>The Animal Feed (England) Regulations 2010</strong>, dog treats sold in the UK must include a full ingredient list and analytical constituents, enabling owners to calculate calorie contributions accurately. '
        'The <strong>PFMA</strong> publishes guidelines recommending that treats should not exceed 10% of a dog\'s daily calorie intake to prevent nutritional imbalance and weight gain. '
        'The <strong>BVA</strong> advises that treat selection should consider the individual dog\'s health conditions, including obesity, allergies, and dental disease.</p>'
    ),
    4132: (
        '<p>The <strong>Kennel Club Good Citizen Dog Scheme</strong> — the largest dog training programme in the UK — offers Puppy Foundation, Bronze, Silver, and Gold awards providing a structured training pathway from 10 weeks of age. '
        'The <strong>ABTC</strong> publishes a Code of Practice requiring registered trainers to use humane, evidence-based methods and maintain continuing professional development. '
        'The <strong>RSPCA</strong> and <strong>Dogs Trust</strong> both publish free puppy training resources aligned with current veterinary behavioural science.</p>'
    ),
    4139: (
        '<p>Under the <strong>Road Traffic Act 1988</strong>, dogs must be on a lead on designated roads in the UK. The <strong>Dangerous Dogs Act 1991</strong> places liability on owners for dogs that are dangerously out of control in any place. '
        'The <strong>Countryside Code</strong>, published by <strong>Natural England</strong>, recommends keeping dogs on leads near livestock, with farmers legally permitted to protect their animals under the Animals Act 1971. '
        'The <strong>BVA</strong> supports the use of harnesses over collars for dogs that pull, citing reduced risk of tracheal and cervical spine pressure.</p>'
    ),
    4042: (
        '<p>The <strong>Highway Code (Rule 56)</strong> advises that dogs should be kept on a short lead when walking on or near a road. '
        'Under the <strong>Control of Dogs Order 1992</strong>, every dog in a public place must wear a collar with a tag displaying the owner\'s name and address — a lead alone does not fulfil this requirement. '
        'The <strong>Kennel Club</strong> provides guidance on appropriate lead types for different training stages through its Good Citizen Dog Scheme resources.</p>'
    ),
    4791: (
        '<p>The <strong>PFMA</strong> recommends that all dog treats, including training treats, should be factored into the dog\'s daily calorie allowance to prevent weight gain — with the PFMA reporting that an estimated 51% of UK dogs are overweight or obese. '
        'The <strong>Animal Feed (England) Regulations 2010</strong> require treat manufacturers to declare ingredients and analytical constituents, allowing informed choices. '
        'The <strong>BVA</strong> advises owners to select single-ingredient treats for dogs with suspected food sensitivities and to seek veterinary advice before starting elimination diets.</p>'
    ),

    # ─── EDUCATIONAL (2+ additional UK authority references per post) ──
    7341: (
        '<p>The <strong>RSPCA</strong> publishes comprehensive new puppy guides advising a structured first-week approach to minimise stress for both puppy and owner. '
        'Under the <strong>Microchipping of Dogs (England) Regulations 2015</strong>, all puppies must be microchipped by 8 weeks of age and registered on a DEFRA-approved database. '
        'The <strong>BVA</strong> recommends registering with a vet and booking a health check within 48 hours of bringing a new puppy home.</p>'
    ),
    7340: (
        '<p>The <strong>British Veterinary Dental Association (BVDA)</strong> recommends introducing dental care during the teething phase to establish lifelong oral hygiene habits. '
        'The <strong>BVA</strong> advises that retained deciduous teeth should be assessed by a veterinary surgeon, as they can cause malocclusion and dental disease if not addressed. '
        'The <strong>RCVS</strong> requires that any dental extraction on a dog is performed by a qualified veterinary surgeon under appropriate anaesthesia.</p>'
    ),
    7339: (
        '<p>Research published in the <strong>Journal of Veterinary Behavior</strong> confirms that adequate sleep is essential for puppy cognitive development and learning consolidation. '
        'The <strong>RSPCA</strong> advises that puppies should not be crated for longer than their age in months plus one hour as a guideline for crate training. '
        'The <strong>BVA</strong> notes that sudden changes in sleep patterns may indicate underlying health issues and should be assessed by a vet.</p>'
    ),
    7338: (
        '<p>The <strong>Veterinary Poisons Information Service (VPIS)</strong>, accessible through veterinary practices, is the UK\'s authoritative resource for animal poisoning guidance and reports that household products are among the top five causes of pet poisoning. '
        'The <strong>RSPCA</strong> publishes a list of toxic household plants and foods that all dog owners should familiarise themselves with. '
        'Under the <strong>Animal Welfare Act 2006</strong>, owners have a duty to ensure their dog\'s environment is safe and suitable, which includes puppy-proofing the home against foreseeable hazards.</p>'
    ),
    7337: (
        '<p>The <strong>BVA</strong> strongly recommends that all dogs in the UK complete their primary vaccination course and receive annual boosters as appropriate, describing vaccination as one of the most important preventive health measures available. '
        'The <strong>RCVS</strong> publishes Practice Standards that include vaccination protocols aligned with WSAVA (World Small Animal Veterinary Association) guidelines. '
        '<strong>DEFRA</strong> administers the Pet Travel Scheme, which requires rabies vaccination for dogs travelling outside the UK.</p>'
    ),
    7336: (
        '<p>The <strong>Furniture and Furnishings (Fire) (Safety) Regulations 1988</strong> (as amended) apply to dog beds sold in the UK, requiring compliant fire-resistant filling and covering materials. '
        'The <strong>OEKO-TEX Standard 100</strong> certification is an internationally recognised testing system for harmful substances in textiles, relevant when selecting non-toxic dog bedding. '
        'The <strong>RSPCA</strong> advises providing comfortable, appropriate bedding as part of the duty of care under the Animal Welfare Act 2006.</p>'
    ),
    7334: (
        '<p>The <strong>ABTC</strong> registers practitioners who can assist with settling and bed-training difficulties using humane, evidence-based methods. '
        'The <strong>Dogs Trust</strong> publishes free guides on crate and bed training that align with current positive reinforcement practices. '
        'The <strong>BVA</strong> advises that persistent nighttime distress may indicate underlying health or behavioural issues requiring veterinary assessment.</p>'
    ),
    7170: (
        '<p>The <strong>RCVS (Royal College of Veterinary Surgeons)</strong> regulates all veterinary professionals in the UK and maintains a searchable register at findavet.rcvs.org.uk. '
        'The <strong>BVA</strong> publishes evidence-based guidance on a wide range of dog health topics, accessible free of charge at bva.co.uk. '
        '<strong>DEFRA</strong> is responsible for the legislative framework governing animal welfare, including the Animal Welfare Act 2006 which places a legal duty of care on all dog owners in England and Wales.</p>'
    ),
    7169: (
        '<p>The <strong>Kennel Club</strong> provides breed-specific health information and operates DNA testing schemes to reduce the prevalence of inherited conditions. '
        'The <strong>PDSA PAW Report</strong> (published annually) provides the most comprehensive overview of UK pet welfare, including veterinary costs, ownership trends, and common health conditions. '
        'The <strong>Animal Welfare Act 2006</strong> requires owners to meet five welfare needs: a suitable environment, a suitable diet, the ability to exhibit normal behaviour, appropriate housing, and protection from pain and disease.</p>'
    ),
    5417: (
        '<p>The <strong>PFMA</strong> publishes size-of-pet-population data annually, providing the UK\'s most reliable estimates of dog ownership and spending patterns. '
        'The <strong>ABTC</strong> provides a public register of qualified animal behaviourists and trainers, ensuring owners can find practitioners who meet nationally recognised standards. '
        'The <strong>BVA</strong> and <strong>BSAVA</strong> publish joint guidance on puppy care essentials, covering nutrition, vaccination, socialisation, and preventive healthcare.</p>'
    ),
    4792: (
        '<p>The <strong>APBC (Association of Pet Behaviour Counsellors)</strong> publishes evidence-based guidance on puppy socialisation, emphasising the critical 3–14 week window identified in veterinary behavioural science. '
        'The <strong>Kennel Club Good Citizen Puppy Foundation</strong> programme includes structured socialisation exercises designed by qualified behaviourists. '
        'The <strong>RSPCA</strong> advises that positive socialisation experiences during the critical period are the single most effective way to prevent behavioural problems in adult dogs.</p>'
    ),
    4570: (
        '<p>The <strong>PDSA</strong> publishes annual estimates of the lifetime cost of dog ownership (currently £16,000–£33,000 for a medium breed over 12 years), providing essential budgeting information for prospective owners. '
        'The <strong>BVA</strong> recommends that all first-time dog owners take out lifetime pet insurance as a financial safety net against unexpected veterinary costs. '
        'Under the <strong>Control of Dogs Order 1992</strong>, dogs must wear a collar and tag in public displaying the owner\'s name and address — a microchip alone does not satisfy this legal requirement.</p>'
    ),
    4568: (
        '<p>The <strong>British Veterinary Dental Association (BVDA)</strong> recommends daily tooth brushing as the gold standard for preventive dental care in dogs. '
        'The <strong>VOHC (Veterinary Oral Health Council)</strong> maintains a list of accepted products (dental chews, diets, and water additives) that have demonstrated efficacy in plaque and tartar reduction through controlled clinical trials. '
        'The <strong>RCVS</strong> mandates that dental extractions in dogs must be performed by a veterinary surgeon under appropriate anaesthesia and analgesia.</p>'
    ),
    4566: (
        '<p>The <strong>Met Office</strong> issues weather warnings that can impact dog walking safety — owners should monitor alerts during heatwaves, storms, and icy conditions. '
        'The <strong>RSPCA</strong> runs annual campaigns including "Die in a Hot Car" (summer) and firework awareness (autumn) to educate pet owners about seasonal hazards. '
        'The <strong>BVA</strong> publishes seasonal pet care advice, including guidance on antifreeze toxicity (ethylene glycol is lethal at 1.5ml/kg body weight) and the importance of year-round parasite prevention.</p>'
    ),
    4563: (
        '<p>The <strong>Pet Industry Federation (PIF)</strong> maintains a register of professional groomers who have met industry training standards, including City &amp; Guilds qualifications. '
        'The <strong>BVA</strong> advises against shaving double-coated breeds, as the coat provides essential insulation and UV protection. '
        'The <strong>RCVS</strong> notes that grooming activities that involve medicinal treatment (e.g., treating skin conditions) should be performed under veterinary guidance.</p>'
    ),
    4414: (
        '<p>The <strong>Control of Dogs Order 1992</strong> requires all dogs in public places to wear a collar with an ID tag showing the owner\'s name and address — a harness alone does not satisfy this requirement unless an ID tag is attached. '
        'A study published in <strong>Veterinary Record</strong> found that collar pressure during pulling can increase intraocular pressure, a concern for breeds predisposed to glaucoma. '
        'The <strong>BVA</strong> supports the use of well-fitted harnesses, particularly for brachycephalic breeds and dogs with cervical or tracheal conditions.</p>'
    ),
    4413: (
        '<p>The <strong>BVA</strong> recommends that harness fit be checked regularly, as ill-fitting equipment can cause chafing, restricted movement, and long-term musculoskeletal issues. '
        'The <strong>ABTC</strong> advises that harness introduction should follow positive reinforcement principles to prevent negative associations with being handled. '
        'The <strong>Dogs Trust</strong> provides free resources on measuring and fitting harnesses, collars, and other walking equipment.</p>'
    ),
    4411: (
        '<p>The <strong>BVA</strong> has published guidance supporting the use of well-fitted Y-shaped harnesses that do not restrict shoulder movement, particularly for growing puppies. '
        'Under the <strong>Control of Dogs Order 1992</strong>, a harness used as the primary restraint in public must still display an ID tag — owners should attach a tag to the harness D-ring or use a separate collar. '
        'The <strong>RSPCA</strong> recommends harnesses over collars for small breeds and brachycephalic breeds to reduce the risk of tracheal collapse and breathing difficulties.</p>'
    ),
    4110: (
        '<p>The <strong>Veterinary Medicines Directorate (VMD)</strong> regulates veterinary medicines in the UK, while pet supplements are classified as "complementary feed" under The Animal Feed (England) Regulations 2010 and do not require proof of therapeutic efficacy before sale. '
        'The <strong>BVA</strong> recommends that owners consult a veterinary surgeon before starting any joint supplement, as symptoms may indicate conditions requiring medical treatment rather than supplementation. '
        'The <strong>BSAVA</strong> formulary provides evidence-based dosing recommendations for glucosamine, chondroitin, and omega-3 fatty acids used in canine joint support.</p>'
    ),
    4103: (
        '<p>The <strong>BVA</strong> strongly advises year-round flea prevention, noting that UK homes with central heating can sustain flea populations throughout the winter. '
        '<strong>DEFRA</strong> and the <strong>VMD (Veterinary Medicines Directorate)</strong> regulate flea treatments sold in the UK, with prescription-only products (POM-V) available exclusively through veterinary practices. '
        'The <strong>RSPCA</strong> warns that permethrin-based dog flea treatments are lethal to cats — a critical safety consideration in multi-pet households.</p>'
    ),
    4096: (
        '<p>The <strong>British Veterinary Dental Association (BVDA)</strong> is the specialist dental division of the BVA, providing evidence-based guidance on small animal dentistry. '
        'The <strong>VOHC (Veterinary Oral Health Council)</strong> awards its seal of acceptance only to dental products that have demonstrated plaque or tartar reduction in controlled clinical trials. '
        'The <strong>RCVS</strong> Practice Standards require that practices offering dental services have appropriate equipment, including dental radiography, for sub-gingival assessment.</p>'
    ),
    4089: (
        '<p>The <strong>PDSA</strong> PAW Report (2024) estimates the average annual cost of veterinary care for a dog in the UK at approximately £1,875, with lifetime costs ranging from £16,000 to £33,000 depending on breed. '
        'The <strong>BVA</strong> recommends annual health checks for adult dogs and biannual checks for senior dogs (7+), with blood work to screen for age-related conditions. '
        'The <strong>RCVS Practice Standards Scheme</strong> provides accreditation at Core, General Practice, and Hospital levels, helping owners identify practices that meet defined quality standards.</p>'
    ),
}


# ══════════════════════════════════════════════════════════════════════════════
# TRUST DEPTH / RESEARCH SOURCES (Phase 10BO)
# ══════════════════════════════════════════════════════════════════════════════

RESEARCH_SOURCES = {
    # ─── DOG FOOD ────────────────────────────────────────────────────────
    7172: [
        "FEDIAF Nutritional Guidelines for Complete and Complementary Pet Food for Cats and Dogs (2023 revision)",
        "PFMA Code of Practice for the Manufacture of Pet Food",
        "The Animal Feed (England) Regulations 2010 (SI 2010/2503)",
        "BVA position on commercial pet food and raw feeding",
        "Food Standards Agency (FSA) guidance on pet food labelling and safety",
    ],
    3836: [
        "PFMA Pet Population Data (2024) — 13 million dogs in the UK",
        "FEDIAF Nutritional Guidelines for Complete and Complementary Pet Food (2023 revision)",
        "DEFRA Code of Practice for the Welfare of Dogs (under Animal Welfare Act 2006)",
        "RCVS Practice Standards Scheme accreditation framework",
        "BVA guidance on selecting appropriate commercial dog food",
    ],
    3837: [
        "FEDIAF Nutritional Guidelines (2023) — minimum protein, fat, and mineral requirements by life stage",
        "PFMA Code of Practice — quality standards for UK pet food manufacturers",
        "FSA mycotoxin monitoring programme for animal feed ingredients",
        "BVA position statement on grain-free diets and dilated cardiomyopathy",
        "The Animal Feed (England) Regulations 2010 — labelling and declaration requirements",
    ],
    3838: [
        "British Veterinary Association Veterinary Record — research on wet vs dry food formats",
        "FEDIAF guidelines on moisture content declaration and dry-matter comparison",
        "PFMA member manufacturing standards and quality assurance protocols",
        "DEFRA feed labelling enforcement guidance",
        "BVA dietary advice for dogs with dental and renal conditions",
    ],
    3839: [
        "FEDIAF Nutritional Guidelines — growth requirements: protein, calcium, DHA, and energy density",
        "PFMA Puppy Contract (developed with RSPCA and Animal Welfare Foundation)",
        "BVA/BSAVA guidance on large breed puppy nutrition and developmental orthopaedic disease",
        "Kennel Club breed-specific growth charts and feeding recommendations",
        "DEFRA labelling requirements for life-stage-specific pet food",
    ],

    # ─── TRAINING ────────────────────────────────────────────────────────
    4118: [
        "Animal Behaviour and Training Council (ABTC) — UK regulatory body and practitioner register",
        "BVA/BSAVA position statement on humane dog training methods",
        "RSPCA rehoming data — behavioural issues as the leading cause of relinquishment",
        "Kennel Club Good Citizen Dog Scheme — structured training framework",
        "APBC (Association of Pet Behaviour Counsellors) — evidence-based behaviour guidance",
    ],
    4125: [
        "PFMA guidelines on treat calorie contribution (maximum 10% of daily intake)",
        "The Animal Feed (England) Regulations 2010 — treat labelling requirements",
        "BVA guidance on treat selection for dogs with health conditions",
        "FEDIAF complementary feed standards for dog treats",
    ],
    4132: [
        "Kennel Club Good Citizen Puppy Foundation — nationwide puppy training programme",
        "ABTC Code of Practice for animal trainers and behaviourists",
        "RSPCA and Dogs Trust puppy training resources",
        "BVA advice on the critical socialisation window (3–14 weeks)",
    ],
    4139: [
        "Road Traffic Act 1988 — legal requirement for dogs on leads near roads",
        "Dangerous Dogs Act 1991 — owner liability for out-of-control dogs",
        "Countryside Code (Natural England) — livestock and lead guidance",
        "BVA position on harness use for tracheal health",
    ],
    4042: [
        "Highway Code Rule 56 — dogs on leads near roads",
        "Control of Dogs Order 1992 — collar and ID tag requirements",
        "Kennel Club Good Citizen Dog Scheme lead training resources",
        "Animals Act 1971 — livestock protection provisions",
    ],
    4791: [
        "PFMA pet obesity data — estimated 51% of UK dogs overweight or obese",
        "The Animal Feed (England) Regulations 2010 — treat ingredient declaration",
        "BVA guidance on dietary management for dogs with food sensitivities",
        "FEDIAF complementary feed nutritional standards",
    ],

    # ─── EDUCATIONAL ─────────────────────────────────────────────────────
    7341: [
        "Microchipping of Dogs (England) Regulations 2015 — compulsory microchipping by 8 weeks",
        "RSPCA new puppy care guidance and welfare advice",
        "BVA first puppy health check recommendations",
        "PFMA Puppy Contract — ethical purchasing and early care standards",
    ],
    7340: [
        "British Veterinary Dental Association (BVDA) — puppy dental care guidance",
        "BVA guidance on retained deciduous teeth assessment and management",
        "RCVS standards for dental procedures requiring veterinary qualification",
        "BSAVA Manual of Canine and Feline Dentistry — teething timeline reference",
    ],
    7339: [
        "Journal of Veterinary Behavior — research on sleep and puppy cognitive development",
        "RSPCA crate training duration guidelines for puppies",
        "BVA advice on sleep pattern changes as health indicators",
        "Kennel Club puppy settling and sleep resources",
    ],
    7338: [
        "Veterinary Poisons Information Service (VPIS) — UK animal poisoning data and guidance",
        "RSPCA list of toxic household plants and foods for dogs",
        "Animal Welfare Act 2006 — duty of care for safe environment provision",
        "PDSA poisoning awareness campaigns and first-aid guidance",
    ],
    7337: [
        "BVA vaccination policy — core and non-core vaccine recommendations for UK dogs",
        "RCVS Practice Standards — vaccination protocols aligned with WSAVA guidelines",
        "DEFRA Pet Travel Scheme — rabies vaccination requirements",
        "Kennel Club health guidance on breed-specific vaccination considerations",
    ],
    7336: [
        "Furniture and Furnishings (Fire) (Safety) Regulations 1988 (as amended)",
        "OEKO-TEX Standard 100 — textile safety certification for harmful substances",
        "RSPCA guidance on suitable bedding as part of Animal Welfare Act 2006 duty of care",
        "CertiPUR certification for low-emission foam materials",
    ],
    7334: [
        "ABTC registered practitioner standards for settling and training support",
        "Dogs Trust bed and crate training guides (positive reinforcement approach)",
        "BVA advice on persistent nighttime distress as a health/behaviour indicator",
    ],
    7170: [
        "RCVS veterinary professional register and practice finder (findavet.rcvs.org.uk)",
        "BVA evidence-based pet health guidance (bva.co.uk)",
        "DEFRA Animal Welfare Act 2006 — legal duty of care framework",
        "PDSA PAW Report — annual UK pet welfare survey data",
    ],
    7169: [
        "Kennel Club Breed Information Centre — breed-specific health data and DNA testing",
        "PDSA PAW Report — comprehensive UK pet welfare and cost data",
        "Animal Welfare Act 2006 — five welfare needs framework",
        "ABTC practitioner register for qualified trainers and behaviourists",
    ],
    5417: [
        "PFMA annual pet population survey and spending data",
        "ABTC national register of qualified animal behaviour practitioners",
        "BVA/BSAVA joint guidance on puppy care essentials",
        "ABI (Association of British Insurers) pet insurance comparison guidance",
    ],
    4792: [
        "APBC evidence-based socialisation guidance and critical period research",
        "Kennel Club Good Citizen Puppy Foundation socialisation programme",
        "RSPCA puppy socialisation advice and behavioural prevention guidance",
        "BVA position on the importance of early socialisation for welfare outcomes",
    ],
    4570: [
        "PDSA lifetime cost of dog ownership estimates (£16,000–£33,000 for medium breeds)",
        "BVA pet insurance recommendations for new dog owners",
        "Control of Dogs Order 1992 — collar and ID tag legal requirements",
        "Kennel Club Breed Information Centre — breed selection guidance",
        "RSPCA rehoming and adoption support resources",
    ],
    4568: [
        "British Veterinary Dental Association (BVDA) daily brushing recommendations",
        "VOHC (Veterinary Oral Health Council) accepted product list",
        "RCVS dental procedure standards and veterinary qualifications",
        "BVA data on prevalence of periodontal disease in dogs over 3 years",
    ],
    4566: [
        "Met Office weather warnings and seasonal safety advisories",
        "RSPCA seasonal safety campaigns (heatstroke, fireworks, antifreeze)",
        "BVA seasonal pet care guidance and antifreeze toxicity data",
        "DEFRA Countryside Code — seasonal land access and dog control",
    ],
    4563: [
        "Pet Industry Federation (PIF) professional groomer register",
        "BVA position on coat management for double-coated breeds",
        "RCVS guidance on grooming activities involving medicinal treatment",
        "City and Guilds grooming qualifications framework",
    ],
    4414: [
        "Control of Dogs Order 1992 — ID tag requirements in public places",
        "Veterinary Record research on collar pressure and intraocular pressure",
        "BVA support for harness use in brachycephalic and tracheal-sensitive breeds",
        "RSPCA small breed harness recommendations",
    ],
    4413: [
        "BVA guidance on equipment fit and musculoskeletal health",
        "ABTC positive reinforcement principles for equipment introduction",
        "Dogs Trust harness fitting and measurement resources",
    ],
    4411: [
        "BVA guidance on Y-shaped harness design and shoulder movement",
        "Control of Dogs Order 1992 — ID tag compliance with harness use",
        "RSPCA harness recommendations for small and brachycephalic breeds",
    ],
    4110: [
        "Veterinary Medicines Directorate (VMD) — supplement regulation framework",
        "BVA guidance on joint supplement use and veterinary assessment",
        "BSAVA formulary — evidence-based dosing for glucosamine, chondroitin, omega-3",
        "The Animal Feed (England) Regulations 2010 — complementary feed classification",
    ],
    4103: [
        "BVA year-round flea prevention guidance",
        "DEFRA and VMD flea treatment regulation (POM-V classification)",
        "RSPCA permethrin cat toxicity warning for multi-pet households",
        "ESCCAP (European Scientific Counsel Companion Animal Parasites) UK guidelines",
    ],
    4096: [
        "British Veterinary Dental Association (BVDA) — specialist dental guidance",
        "VOHC seal of acceptance — clinical trial requirements for dental products",
        "RCVS Practice Standards for dental radiography and sub-gingival assessment",
        "BVA prevalence data — periodontal disease in 80% of dogs over 3 years",
    ],
    4089: [
        "PDSA PAW Report (2024) — annual veterinary cost estimates and lifetime ownership data",
        "BVA annual and biannual health check recommendations",
        "RCVS Practice Standards Scheme — Core, General Practice, and Hospital accreditation levels",
        "Animal Welfare Act 2006 — five welfare needs legal framework",
        "PFMA pet population and obesity prevalence data",
    ],
}


# ══════════════════════════════════════════════════════════════════════════════
# At-a-Glance and Key Takeaway STRENGTHENING (Phase 10BM — Dog Food priority)
# ══════════════════════════════════════════════════════════════════════════════

AT_A_GLANCE_ADDITIONS = {
    7172: '<li><strong>Regulatory framework</strong> — UK dog food labelling is governed by The Animal Feed (England) Regulations 2010, with FEDIAF providing nutritional standards and PFMA members covering over 90% of the market</li>',
    3836: '<li><strong>Market context</strong> — The PFMA reports approximately 13 million dogs in 12 million UK households, with FEDIAF-compliant complete foods meeting all nutritional needs for specified life stages</li>',
    3837: '<li><strong>Nutritional benchmark</strong> — FEDIAF guidelines set minimum 18% crude protein for adult maintenance, with quality dry foods typically providing 24–28% alongside controlled fat and fibre levels</li>',
    3838: '<li><strong>Regulatory parity</strong> — Both wet and dry dog foods sold in the UK must comply with identical FEDIAF nutritional standards and The Animal Feed (England) Regulations 2010 labelling requirements</li>',
    3839: '<li><strong>Growth-specific standards</strong> — FEDIAF sets higher requirements for puppy food: minimum 25% protein, controlled calcium (max 1.0% for large breeds), and DHA at 0.05%+ for brain development</li>',
}


# ══════════════════════════════════════════════════════════════════════════════
# MAIN PROCESSING ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def find_insertion_point_practical(content):
    """Find where to insert Practical Guide — BEFORE Evaluation Framework,
    Troubleshooting, Scenario, How to Evaluate blocks."""
    # Insertion targets in priority order
    targets = [
        'How to Evaluate',
        'Evaluation Framework',
        'Common Problems and Solutions',
        'Troubleshooting',
        'Which Option Suits Your Situation',
        'Scenario Guidance',
    ]
    for target in targets:
        pattern = re.compile(
            r'(<!-- wp:group[^>]*-->.*?<h4[^>]*>' + re.escape(target) + r'</h4>)',
            re.DOTALL
        )
        m = pattern.search(content)
        if m:
            # Find the start of the wp:group block containing this heading
            # Walk backward to find the <!-- wp:group line
            start = m.start()
            # Search backward for the opening wp:group comment
            group_start = content.rfind('<!-- wp:group', 0, start + 50)
            if group_start >= 0:
                return group_start
    return None


def find_insertion_point_research(content):
    """Find where to insert Research Sources — AFTER Scenario Guidance,
    BEFORE Quick Checklist."""
    # Look for Quick Checklist block
    pattern = re.compile(
        r'<!-- wp:group[^>]*-->.*?<h4[^>]*>Quick Checklist</h4>',
        re.DOTALL
    )
    m = pattern.search(content)
    if m:
        group_start = content.rfind('<!-- wp:group', 0, m.start() + 50)
        if group_start >= 0:
            return group_start

    # Fallback: look for "What to Do Next"
    pattern2 = re.compile(
        r'<!-- wp:group[^>]*-->.*?<h4[^>]*>What to Do Next</h4>',
        re.DOTALL
    )
    m2 = pattern2.search(content)
    if m2:
        group_start = content.rfind('<!-- wp:group', 0, m2.start() + 50)
        if group_start >= 0:
            return group_start

    # Last fallback: end of content
    return None


def process_post(post_id, title, cluster):
    """Process a single post with all 4 phases."""
    print(f"\n{'='*70}")
    print(f"Processing: ID {post_id} — {title} [{cluster}]")
    print(f"{'='*70}")

    # Fetch raw content
    post_data = wp_get("posts/" + str(post_id), {"context": "edit", "_fields": "id,content"})
    if "content" not in post_data:
        print(f"  ERROR: Could not fetch post {post_id}: {post_data}")
        return {"practical": False, "tables": 0, "citations": 0, "trust": False, "status": "FETCH_ERROR"}

    content = post_data["content"]["raw"]
    original_len = len(content)
    changes_made = []

    # Track what we add
    practical_added = False
    tables_added = 0
    citations_added = 0
    trust_added = False

    # ── Phase 10BK: Practical Guide ──────────────────────────────────
    if post_id in PRACTICAL_GUIDES and "Step-by-Step Practical Guide" not in content:
        guide = PRACTICAL_GUIDES[post_id]
        steps_html = make_list_block(guide["steps"], ordered=True)
        practical_block = make_group_block("#ecfdf5", "#6ee7b7", guide["title"], steps_html)

        insert_pos = find_insertion_point_practical(content)
        if insert_pos is not None:
            content = content[:insert_pos] + practical_block + "\n\n" + content[insert_pos:]
        else:
            # Insert before the last block
            content = content + "\n\n" + practical_block
        practical_added = True
        changes_made.append("10BK Practical Guide")
        print(f"  [10BK] Added Practical Guide ({len(guide['steps'])} steps)")

    # ── Phase 10BN: Comparison Tables ────────────────────────────────
    if post_id in COMPARISON_TABLES:
        for table_data in COMPARISON_TABLES[post_id]:
            caption = table_data.get("caption", "")
            # Check if this table already exists (by caption)
            if caption and caption in content:
                print(f"  [10BN] Table '{caption}' already exists, skipping")
                continue
            table_block = make_table_block(
                table_data["headers"],
                table_data["rows"],
                caption
            )
            # Insert comparison tables after the practical guide block (if added)
            # or before the Research Sources insertion point
            # Simple approach: add after practical guide or before Scenario/Quick Checklist
            insert_pos = find_insertion_point_practical(content)
            if insert_pos:
                # Find the end of the practical guide block if it was just added
                if practical_added:
                    pg_end = content.find('<!-- /wp:group -->', content.find('Step-by-Step Practical Guide'))
                    if pg_end > 0:
                        insert_pos = pg_end + len('<!-- /wp:group -->') + 1
                content = content[:insert_pos] + "\n\n" + table_block + "\n\n" + content[insert_pos:]
            else:
                content = content + "\n\n" + table_block
            tables_added += 1
            changes_made.append(f"10BN Table: {caption[:40]}")
        if tables_added > 0:
            print(f"  [10BN] Added {tables_added} comparison table(s)")

    # ── Phase 10BM: Citation References ──────────────────────────────
    if post_id in CITATION_PARAGRAPHS:
        citation_html = CITATION_PARAGRAPHS[post_id]
        # Check if this citation paragraph already exists
        # Use a unique phrase to detect
        check_phrase = "PFMA" if "PFMA" in citation_html else "BVA"
        # Count existing PFMA/BVA references vs what we're adding
        # Insert the citation paragraph near the beginning of the main content
        # after any initial intro paragraphs but before the first block

        # Find a good insertion point: after the first 1-2 paragraphs
        # Look for the first wp:group block
        first_group = content.find('<!-- wp:group')
        if first_group > 0:
            content = content[:first_group] + "\n" + citation_html + "\n\n" + content[first_group:]
        else:
            content = citation_html + "\n\n" + content
        citations_added = citation_html.count('<strong>') # Count unique refs
        changes_made.append(f"10BM Citations ({citations_added} refs)")
        print(f"  [10BM] Added citation paragraph with {citations_added} authority references")

    # ── Phase 10BM (Dog Food): Strengthen At a Glance ────────────────
    if post_id in AT_A_GLANCE_ADDITIONS:
        addition = AT_A_GLANCE_ADDITIONS[post_id]
        # Find the At a Glance list and add our item
        at_glance_pattern = re.compile(
            r'(<h4[^>]*>At a Glance</h4>.*?<ul[^>]*>)(.*?)(</ul>)',
            re.DOTALL
        )
        m = at_glance_pattern.search(content)
        if m and addition not in content:
            content = content[:m.end(2)] + "\n" + addition + content[m.end(2):]
            print(f"  [10BM] Strengthened At a Glance with regulatory context")

    # ── Phase 10BO: Research Sources and Standards ────────────────────
    if post_id in RESEARCH_SOURCES and "Research Sources and Standards" not in content:
        sources = RESEARCH_SOURCES[post_id]
        sources_html = make_list_block([s for s in sources], ordered=False)
        research_block = make_group_block("#f0f9ff", "#bae6fd",
                                         "Research Sources and Standards", sources_html)

        insert_pos = find_insertion_point_research(content)
        if insert_pos is not None:
            content = content[:insert_pos] + research_block + "\n\n" + content[insert_pos:]
        else:
            content = content + "\n\n" + research_block
        trust_added = True
        changes_made.append("10BO Research Sources")
        print(f"  [10BO] Added Research Sources and Standards ({len(sources)} sources)")

    # ── Apply changes ────────────────────────────────────────────────
    if changes_made:
        print(f"  Updating post... (content grew from {original_len} to {len(content)} chars)")
        success, result = wp_update_post(post_id, content)
        if success:
            print(f"  SUCCESS — Post {post_id} updated")
            status = "UPDATED"
        else:
            print(f"  FAILED — {result}")
            status = f"UPDATE_FAILED: {result}"
    else:
        print(f"  No changes needed (all phases already applied)")
        status = "ALREADY_COMPLETE"

    return {
        "practical": practical_added,
        "tables": tables_added,
        "citations": citations_added,
        "trust": trust_added,
        "status": status
    }


def main():
    print("=" * 70)
    print("Phase 10BK/10BM/10BN/10BO Engine — pethubonline.com")
    print("Clusters: Dog Food, Dog Training, Educational")
    print("=" * 70)

    # Fetch all posts
    print("\nFetching cluster posts...")
    clusters = fetch_cluster_posts()

    for cluster_name, posts in clusters.items():
        print(f"\n{cluster_name}: {len(posts)} posts")
        for pid, title, cats in posts:
            print(f"  ID {pid}: {title}")

    # Process all posts and collect results
    csv_rows = []

    for cluster_name, posts in clusters.items():
        for pid, title, cats in posts:
            time.sleep(1)  # Rate limiting
            result = process_post(pid, title, cluster_name)
            csv_rows.append({
                "id": pid,
                "title": title,
                "cluster": cluster_name,
                "practical_guide_added": "Yes" if result["practical"] else "No",
                "comparison_tables_added": result["tables"],
                "citation_refs_added": result["citations"],
                "trust_sources_added": "Yes" if result["trust"] else "No",
                "status": result["status"]
            })

    # Write CSV
    print(f"\n{'='*70}")
    print(f"Writing CSV to {CSV_PATH}")
    with open(CSV_PATH, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "title", "cluster", "practical_guide_added",
            "comparison_tables_added", "citation_refs_added",
            "trust_sources_added", "status"
        ])
        writer.writeheader()
        writer.writerows(csv_rows)

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    total = len(csv_rows)
    updated = sum(1 for r in csv_rows if r["status"] == "UPDATED")
    practical_count = sum(1 for r in csv_rows if r["practical_guide_added"] == "Yes")
    table_count = sum(r["comparison_tables_added"] for r in csv_rows)
    citation_count = sum(r["citation_refs_added"] for r in csv_rows)
    trust_count = sum(1 for r in csv_rows if r["trust_sources_added"] == "Yes")

    print(f"Total posts processed: {total}")
    print(f"Posts updated: {updated}")
    print(f"Practical Guides added (10BK): {practical_count}")
    print(f"Comparison Tables added (10BN): {table_count}")
    print(f"Citation references added (10BM): {citation_count}")
    print(f"Research Sources blocks added (10BO): {trust_count}")
    print(f"\nCSV saved to: {CSV_PATH}")


if __name__ == "__main__":
    main()
