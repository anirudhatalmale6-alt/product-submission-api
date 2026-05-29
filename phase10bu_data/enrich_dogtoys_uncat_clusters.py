#!/usr/bin/env python3
"""
Phase 10BU Content Enrichment for Dog Toys and Uncategorized clusters.
Clusters: Dog Toys, Uncategorized

Appends Gutenberg blocks (Research Sources, Why We Reference Sources,
Key Terms, At a Glance, Comparison Tables, Practical Guides) to posts
that score below threshold in citation_preference and authority_moat CSVs.

Usage:
    python3 enrich_dogtoys_uncat_clusters.py
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
TARGET_CLUSTERS = {"Dog Toys", "Uncategorized"}
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

print(f"Found {len(target_posts)} posts in target clusters (Dog Toys + Uncategorized)")

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

# ── UK institution references per cluster ──────────────────────────────
UK_REFS = {
    "Dog Toys": {
        "research_sources": (
            "Our toy safety guidance references the RSPCA's advice on safe toys for dogs, "
            "including their recommendations on appropriate toy sizes, materials, and supervision "
            "during play. The PDSA's published guidance on choosing safe dog toys and recognising "
            "toy-related hazards informs our material assessments. Blue Cross veterinary advice "
            "on toy safety, including guidance on which toys to avoid for different dog sizes "
            "and chewing strengths, provides additional UK-specific context. "
            "We consult the British Veterinary Association (BVA) position on foreign body "
            "ingestion risks associated with unsuitable toys, which remains one of the most "
            "common emergency presentations in UK veterinary practice."
        ),
        "why_sources": (
            "Dog toy marketing frequently makes durability and safety claims that are difficult "
            "for owners to verify independently. We reference the RSPCA, PDSA, and Blue Cross "
            "because these UK animal welfare organisations evaluate toy safety based on veterinary "
            "evidence and reported injury data rather than manufacturer claims. Our approach "
            "focuses on material composition, size appropriateness, and supervision requirements "
            "as recommended by UK veterinary professionals, helping owners make informed choices "
            "about toy safety for their individual dog."
        ),
    },
    "Uncategorized": {
        "research_sources": (
            "Our pet welfare guidance draws on multiple UK authoritative sources. The RSPCA's "
            "five welfare needs framework, derived from the Animal Welfare Act 2006, provides "
            "the foundation for our care recommendations covering environment, diet, behaviour, "
            "companionship, and health. The British Veterinary Association (BVA) clinical position "
            "statements on preventive care, nutrition, and behavioural health inform our practical "
            "advice. We reference the PDSA's annual PAW Report for UK-wide data on pet welfare "
            "trends and veterinary access. The Kennel Club's published guidance on breed-specific "
            "care, socialisation, and training supports our breed-related content. Blue Cross "
            "veterinary advice pages contribute general pet welfare context across species."
        ),
        "why_sources": (
            "Pet care information online varies significantly in accuracy, currency, and regional "
            "relevance. We reference the RSPCA, BVA, PDSA, Kennel Club, and Blue Cross because "
            "these UK organisations maintain evidence-based, regularly updated guidance that reflects "
            "the medications, treatments, products, and legal requirements available to UK pet owners. "
            "Our methodology prioritises information grounded in UK veterinary consensus and animal "
            "welfare legislation, helping owners distinguish reliable advice from unverified claims."
        ),
    },
}

# ── Glossary terms per cluster ─────────────────────────────────────────
GLOSSARY_TERMS = {
    "Dog Toys": [
        ("TPR (Thermoplastic Rubber)", "A flexible, rubber-like material commonly used in dog toys that combines the properties of rubber with the recyclability of plastic. Generally considered durable and non-toxic when food-grade."),
        ("Natural rubber", "Derived from the latex of rubber trees, natural rubber is used in many premium dog toys. It is biodegradable, typically free from BPA and phthalates, and offers good elasticity and durability for chewing."),
        ("Food-grade silicone", "A non-toxic, heat-resistant silicone material approved for food contact. Used in some dog toys and treat-dispensing products, it does not leach chemicals and is dishwasher-safe for easy cleaning."),
        ("Denier (D)", "A unit measuring the linear mass density of fibres used in toy fabrics and rope toys. Higher denier numbers (e.g., 600D, 1200D) indicate thicker, more durable, and more chew-resistant materials."),
        ("Fetch toy vs tug toy", "Fetch toys (balls, frisbees) are designed for throwing and retrieving, encouraging aerobic exercise. Tug toys (ropes, rubber handles) are designed for interactive pulling games that build jaw strength and reinforce bonding between dog and owner."),
    ],
    "Uncategorized": [
        ("Enrichment", "Activities, environments, and objects that stimulate a pet's physical, mental, and sensory needs beyond basic care. Includes puzzle toys, scent games, training sessions, and varied walking routes."),
        ("Socialisation window", "The critical developmental period, approximately 3 to 14 weeks of age in puppies, during which positive exposure to varied people, animals, sounds, and environments has the greatest impact on lifelong behaviour."),
        ("Body Condition Score (BCS)", "A standardised assessment scale (typically 1-9) used by UK veterinary professionals to evaluate whether a pet is underweight, at an ideal weight, or overweight by examining rib coverage, waist definition, and abdominal tuck."),
        ("Prophylactic treatment", "Preventive medical care administered before disease occurs, such as routine flea, tick, or worm treatments given on a regular schedule to reduce the risk of parasitic infestation or infection."),
        ("Positive reinforcement", "A training method that rewards desired behaviour with treats, praise, or play to increase the likelihood of that behaviour being repeated. Recommended by the BVA, RSPCA, and Kennel Club as the preferred approach to pet training."),
    ],
}

# ── Comparison tables ──────────────────────────────────────────────────

# Generic comparison table for Dog Toys cluster
GENERIC_COMPARISON_DOG_TOYS = """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Dog Toy Materials Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Feature</th><th>Natural Rubber</th><th>Rope (Cotton/Jute)</th><th>Plush (Polyester Fill)</th><th>Nylon</th></tr></thead><tbody><tr><td>Durability</td><td>High; withstands sustained chewing for most dogs</td><td>Moderate; fibres fray with heavy chewing</td><td>Low to moderate; seams and filling are vulnerable</td><td>High; resistant to tearing and abrasion</td></tr><tr><td>Safety Consideration</td><td>Generally non-toxic when food-grade; check for small detachable parts</td><td>Loose fibres can be swallowed and cause intestinal blockage (BVA caution)</td><td>Stuffing and squeakers are choking hazards if toy is torn open</td><td>Hard nylon can chip teeth in aggressive chewers; choose appropriate hardness</td></tr><tr><td>Cleaning</td><td>Dishwasher-safe or hand-wash with warm soapy water</td><td>Machine-washable on gentle cycle; air-dry to prevent mildew</td><td>Machine-washable; check label for temperature guidance</td><td>Dishwasher-safe or hand-wash; dries quickly</td></tr><tr><td>Play Type</td><td>Chewing, fetching, treat-dispensing</td><td>Tug-of-war, gentle chewing, interactive play</td><td>Comfort, light fetching, squeaker play</td><td>Heavy chewing, solo play, dental chewing</td></tr><tr><td>Supervision Level</td><td>Moderate; inspect regularly for cracks or torn pieces</td><td>High; remove when fibres begin to separate</td><td>High; remove immediately if torn or if stuffing is exposed</td><td>Moderate; inspect for chips or sharp edges from wear</td></tr></tbody></table></figure>
<!-- /wp:table -->"""

# Generic comparison table for Uncategorized cluster
GENERIC_COMPARISON_UNCATEGORIZED = """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Pet Care Approaches Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Care Area</th><th>Preventive Approach</th><th>Reactive Approach</th><th>Key UK Guidance</th></tr></thead><tbody><tr><td>Health</td><td>Regular vet check-ups, vaccinations on schedule, parasite prevention year-round</td><td>Seeking veterinary care only when symptoms appear</td><td>BVA recommends annual checks for adults, twice-yearly for seniors (7+ years)</td></tr><tr><td>Nutrition</td><td>Feeding complete, life-stage-appropriate food with regular weight monitoring</td><td>Adjusting diet only after weight problems or health issues develop</td><td>PFMA guidelines define complete vs complementary food standards for the UK market</td></tr><tr><td>Behaviour and Training</td><td>Early socialisation, consistent positive reinforcement training from day one</td><td>Addressing behavioural problems only after they become established</td><td>Kennel Club and RSPCA recommend reward-based training; BVA advises against punishment-based methods</td></tr><tr><td>Enrichment</td><td>Daily mental and physical stimulation through varied activities, toys, and social interaction</td><td>Providing enrichment only when boredom behaviours (destructiveness, barking) appear</td><td>RSPCA five welfare needs include the need to exhibit normal behaviour patterns</td></tr><tr><td>Dental Care</td><td>Regular tooth brushing (2-3 times weekly) and annual dental checks</td><td>Professional dental treatment only when disease is advanced</td><td>BVA reports over 80% of dogs aged 3+ show dental disease signs; prevention is significantly less costly than treatment</td></tr></tbody></table></figure>
<!-- /wp:table -->"""

# Post-specific comparison tables (for high-priority posts)
def get_comparison_table(post_id, title, cluster):
    """Generate comparison table HTML specific to the post topic"""
    tables = {
        # Dog Toys posts
        3960: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Puppy Toy Types Compared by Age Stage</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Feature</th><th>Soft Teething Toys</th><th>Rubber Chew Toys</th><th>Rope Toys</th><th>Puzzle / Treat Toys</th></tr></thead><tbody><tr><td>Suitable Age</td><td>8-16 weeks (primary teething)</td><td>12 weeks onward</td><td>12 weeks onward (supervised)</td><td>16 weeks onward</td></tr><tr><td>Primary Purpose</td><td>Soothe sore gums during teething</td><td>Redirect chewing to appropriate items</td><td>Interactive tug play and bonding</td><td>Mental stimulation and slow feeding</td></tr><tr><td>Material</td><td>Soft rubber or fabric; can be frozen for cooling relief</td><td>Natural rubber or TPR; food-grade preferred</td><td>Cotton or jute fibres</td><td>Rubber, silicone, or hard plastic</td></tr><tr><td>Supervision Needed</td><td>Moderate; check for tears regularly</td><td>Moderate; inspect for cracks after heavy chewing</td><td>High; remove when fibres begin to fray (RSPCA guidance)</td><td>Low to moderate; ensure treat pieces are size-appropriate</td></tr><tr><td>Lifespan</td><td>Short; replace as puppy's jaw strength increases</td><td>Moderate to long; upgrade size as puppy grows</td><td>Short to moderate; discard when fraying begins</td><td>Long; durable designs last into adulthood</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        3957: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Tough Toy Materials Compared for Heavy Chewers</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Feature</th><th>Solid Natural Rubber</th><th>Hard Nylon</th><th>TPR (Thermoplastic Rubber)</th><th>Ballistic Nylon Fabric</th></tr></thead><tbody><tr><td>Chew Resistance</td><td>High; flexes without breaking for most chewers</td><td>Very high; resists sustained gnawing</td><td>Moderate to high; softer than solid rubber</td><td>High tear-resistance; used in covers and reinforced plush</td></tr><tr><td>Tooth Safety</td><td>Gives slightly under pressure, reducing fracture risk</td><td>Can chip teeth if too hard; choose appropriate hardness rating</td><td>Softer than nylon; generally tooth-safe</td><td>Fabric does not pose tooth-chip risk</td></tr><tr><td>Toxicity Concern</td><td>Non-toxic when food-grade; free from BPA and phthalates</td><td>Generally safe; avoid products with chemical odour</td><td>Food-grade TPR is non-toxic; check manufacturer certification</td><td>Safe when stitched securely; hazard is ingestion of fabric pieces</td></tr><tr><td>Cleaning</td><td>Dishwasher-safe or warm soapy water</td><td>Dishwasher-safe; dries quickly</td><td>Hand-wash or dishwasher top rack</td><td>Machine-washable; air-dry</td></tr><tr><td>Supervision Level</td><td>Moderate; inspect weekly for deep gouges</td><td>Moderate; discard if chips or sharp edges appear</td><td>Moderate; replace if pieces break off</td><td>High; check seams and stitching regularly</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        5509: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Common Dog Toy Materials and Safety Considerations</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Material</th><th>Common Uses</th><th>Safety Consideration</th><th>Inspection Frequency</th></tr></thead><tbody><tr><td>Natural rubber (latex)</td><td>Chew toys, balls, treat dispensers</td><td>Non-toxic when food-grade; latex allergy possible in rare cases</td><td>Weekly; check for cracks and tears</td></tr><tr><td>Polyester fibre (stuffing)</td><td>Plush toys, soft toys</td><td>Choking and intestinal blockage risk if ingested (BVA caution)</td><td>Before each use; discard if seams open</td></tr><tr><td>Cotton/jute rope</td><td>Tug toys, fetch ropes</td><td>Loose fibres can cause linear foreign body if swallowed</td><td>Before each use; discard when fraying</td></tr><tr><td>PVC/vinyl</td><td>Squeaky toys, some balls</td><td>May contain phthalates; choose phthalate-free products</td><td>Weekly; check for punctures and material breakdown</td></tr><tr><td>Food-grade silicone</td><td>Lick mats, treat moulds, soft toys</td><td>Non-toxic, BPA-free, heat-resistant; generally considered safest synthetic option</td><td>Monthly; very durable under normal use</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        5522: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Joint Support Options for Dogs Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Approach</th><th>What It Involves</th><th>When Typically Recommended</th><th>Key Consideration</th></tr></thead><tbody><tr><td>Weight management</td><td>Maintaining ideal BCS through portion control and appropriate exercise</td><td>All dogs; particularly important for breeds prone to joint conditions</td><td>The single most impactful factor in reducing joint stress (BVA guidance)</td></tr><tr><td>Joint supplements</td><td>Glucosamine, chondroitin, green-lipped mussel, or omega-3 fatty acids</td><td>Dogs showing early stiffness; typically from age 5-7 for large breeds</td><td>Allow 4-8 weeks for noticeable effect; consult vet before starting</td></tr><tr><td>Orthopaedic bedding</td><td>Memory foam or supportive foam beds that reduce pressure on joints</td><td>Senior dogs, post-surgery, breeds prone to hip or elbow dysplasia</td><td>Foam density of 50+ kg/m3 provides meaningful joint support</td></tr><tr><td>Physiotherapy</td><td>Structured exercises, hydrotherapy, or massage prescribed by a veterinary physiotherapist</td><td>Post-surgery rehabilitation, chronic arthritis, mobility decline</td><td>Must be delivered by or under supervision of a qualified veterinary physiotherapist</td></tr><tr><td>Veterinary treatment</td><td>NSAIDs, disease-modifying drugs, or surgical intervention</td><td>Moderate to severe joint disease diagnosed by a veterinarian</td><td>Prescription-only in the UK; regular blood monitoring may be required for long-term NSAID use</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        5520: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Common Dog Health Conditions by Life Stage</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Life Stage</th><th>Common Conditions</th><th>Prevention Focus</th><th>Vet Check Frequency</th></tr></thead><tbody><tr><td>Puppy (0-12 months)</td><td>Parvovirus, kennel cough, intestinal parasites, developmental issues</td><td>Vaccination course, worming schedule, growth monitoring</td><td>Monthly during vaccination course (BVA recommendation)</td></tr><tr><td>Adult (1-7 years)</td><td>Dental disease, obesity, skin allergies, ear infections</td><td>Dental hygiene, weight management, parasite prevention</td><td>Annually</td></tr><tr><td>Senior (7+ years)</td><td>Arthritis, dental disease, kidney disease, cognitive decline, lumps</td><td>Joint support, regular blood tests, dental care, lump monitoring</td><td>Every 6 months (PDSA recommendation)</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        5467: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Feeding Methods Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Method</th><th>How It Works</th><th>Advantages</th><th>Considerations</th></tr></thead><tbody><tr><td>Scheduled meals</td><td>Set portions at fixed times (typically 2 meals/day for adults)</td><td>Easy to monitor intake; supports weight management and housetraining</td><td>Most widely recommended approach by UK vets and the PDSA</td></tr><tr><td>Free feeding</td><td>Food available at all times; pet eats at will</td><td>Convenient for owners; suits some cats and grazing dogs</td><td>Difficult to monitor intake; contributes to obesity risk, especially in dogs</td></tr><tr><td>Slow feeding</td><td>Using puzzle feeders, slow-feed bowls, or scatter feeding</td><td>Reduces eating speed; provides mental enrichment; aids digestion</td><td>Recommended for dogs that eat too quickly or need additional mental stimulation</td></tr><tr><td>Raw / BARF</td><td>Raw meat, bones, and vegetables prepared at home or purchased commercially</td><td>Some owners report improved coat condition and energy</td><td>BVA notes risks including bacterial contamination and nutritional imbalance if not properly formulated</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        5510: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Dog Bed Sizes by Breed Category</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Breed Size</th><th>Typical Weight Range</th><th>Minimum Bed Length</th><th>Measurement Method</th></tr></thead><tbody><tr><td>Small (e.g., Chihuahua, Pomeranian)</td><td>Under 10kg</td><td>45-60cm</td><td>Nose to tail base + 15cm while lying in natural position</td></tr><tr><td>Medium (e.g., Cocker Spaniel, Beagle)</td><td>10-25kg</td><td>60-80cm</td><td>Nose to tail base + 15-20cm; allow extra for stretchers</td></tr><tr><td>Large (e.g., Labrador, German Shepherd)</td><td>25-40kg</td><td>80-110cm</td><td>Nose to tail base + 20cm; consider bolster beds for leaners</td></tr><tr><td>Giant (e.g., Great Dane, Mastiff)</td><td>Over 40kg</td><td>110-150cm</td><td>Nose to tail base + 20-25cm; orthopaedic foam recommended</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        5523: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Dog Training Tools Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Tool</th><th>Purpose</th><th>UK Guidance</th><th>Important Note</th></tr></thead><tbody><tr><td>Flat collar</td><td>ID tag holder, lead attachment for trained dogs</td><td>Must carry ID tag with owner's name and address (Control of Dogs Order 1992)</td><td>Not suitable for dogs that pull; pressure on trachea</td></tr><tr><td>Harness (front-clip)</td><td>Reduces pulling by redirecting forward motion; distributes pressure across chest</td><td>Recommended by RSPCA and Blue Cross for dogs learning lead manners</td><td>Ensure correct fit; should not restrict shoulder movement</td></tr><tr><td>Head collar</td><td>Guides head direction to reduce pulling; used for training transitions</td><td>Requires gradual desensitisation before use (Kennel Club advice)</td><td>Never use with a retractable lead; risk of neck injury if dog lunges</td></tr><tr><td>Long line (5-10m)</td><td>Allows controlled freedom for recall training in open spaces</td><td>Recommended by Kennel Club for recall training before off-lead exercise</td><td>Always use with a harness, not a collar, to prevent neck injury</td></tr><tr><td>Clicker</td><td>Marks exact moment of desired behaviour; used with treats in positive reinforcement</td><td>Supported by BVA, RSPCA, and Kennel Club as part of reward-based training</td><td>Timing is essential; click must coincide precisely with the desired action</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
    }
    return tables.get(post_id)


# ── Practical step-by-step guides ──────────────────────────────────────

# Post-specific practical guides (for high-priority posts)
def get_practical_guide(post_id, title, cluster):
    """Generate practical guide HTML specific to the post topic"""
    guides = {
        3960: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: Choosing Safe Toys for Your Puppy</h4>
<ol><li><strong>Step 1 — Match toy size to puppy size:</strong> The toy should be large enough that your puppy cannot fit it entirely in their mouth, but small enough for them to carry comfortably. The RSPCA advises that if a toy can fit behind a puppy's back teeth, it is too small and poses a choking risk.</li><li><strong>Step 2 — Choose age-appropriate materials:</strong> For puppies under 16 weeks (teething phase), select soft rubber toys that can be frozen to soothe gums. Avoid hard nylon toys until adult teeth are fully established at around 6-7 months.</li><li><strong>Step 3 — Check for detachable parts:</strong> Before giving any toy, inspect for loose eyes, buttons, ribbons, or squeakers that could be chewed off and swallowed. The BVA notes that foreign body ingestion from toys is a common emergency in puppies.</li><li><strong>Step 4 — Introduce one toy at a time:</strong> Start with 2-3 toys and rotate them every few days to maintain interest. This also helps you observe how your puppy interacts with each type and identify their play preferences.</li><li><strong>Step 5 — Supervise and inspect regularly:</strong> Always supervise play with new toys. After each play session, check for cracks, tears, or pieces missing. Discard any toy that shows signs of breaking apart, as even small ingested pieces can cause intestinal blockage.</li></ol>
</div>
<!-- /wp:group -->""",
        3957: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: Finding Durable Toys for Heavy Chewers</h4>
<ol><li><strong>Step 1 — Assess your dog's chew style:</strong> Observe whether your dog nibbles gently, chews steadily, or destroys toys aggressively within minutes. This determines the material strength needed — gentle chewers suit rope and plush, while power chewers need solid rubber or hard nylon.</li><li><strong>Step 2 — Choose the right material:</strong> For heavy chewers, solid natural rubber (not hollow) and food-grade TPR offer the best combination of durability and tooth safety. Hard nylon is very durable but should give slightly when pressed with a thumbnail to avoid tooth fracture risk.</li><li><strong>Step 3 — Size up, not down:</strong> Always choose a toy one size larger than you think necessary for power chewers. A larger toy is harder to break apart and reduces the risk of pieces being bitten off and swallowed.</li><li><strong>Step 4 — Avoid reinforced plush for destroyers:</strong> Even "indestructible" plush toys with reinforced stitching will eventually be torn open by determined chewers. The stuffing and squeaker inside become immediate choking hazards once exposed.</li><li><strong>Step 5 — Implement a weekly inspection routine:</strong> Check all toys weekly for deep gouges, cracks, missing pieces, or significant wear. Replace any toy that shows structural damage. The PDSA recommends treating toy replacement as a regular part of pet care, not an exception.</li></ol>
</div>
<!-- /wp:group -->""",
        5467: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: Establishing a Feeding Routine for Your Pet</h4>
<ol><li><strong>Step 1 — Determine portion size:</strong> Use the feeding guide on your pet's food packaging as a starting point, adjusting for their current body condition score (BCS). The PDSA recommends using kitchen scales to measure portions accurately rather than estimating by eye.</li><li><strong>Step 2 — Set consistent meal times:</strong> Feed adult dogs twice daily and adult cats 2-4 smaller meals. Choose fixed times that fit your routine and stick to them. Consistency supports digestion and helps with housetraining for dogs.</li><li><strong>Step 3 — Monitor and adjust over 2-4 weeks:</strong> Weigh your pet monthly and assess body condition. If gaining weight, reduce portions by 10%. If losing weight, increase by 10%. Adjust gradually rather than making large changes.</li><li><strong>Step 4 — Account for treats:</strong> Treats should make up no more than 10% of daily calorie intake (PFMA guideline). Reduce meal portions slightly on days when training treats are used to avoid overfeeding.</li><li><strong>Step 5 — Review at annual vet check:</strong> Discuss feeding type, portions, and weight trends with your vet annually. Nutritional needs change with age, activity level, neutering status, and health conditions.</li></ol>
</div>
<!-- /wp:group -->""",
        5520: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: Recognising When Your Dog Needs Veterinary Attention</h4>
<ol><li><strong>Step 1 — Know the emergency signs:</strong> Difficulty breathing, collapse, seizures, a bloated or hard abdomen, inability to urinate, or suspected poisoning require immediate emergency vet contact. Do not wait to see if symptoms improve.</li><li><strong>Step 2 — Track non-emergency symptoms:</strong> Note when the symptom started, how often it occurs, and whether it is getting worse. Record details such as vomiting frequency, stool consistency, or limping severity to report accurately to your vet.</li><li><strong>Step 3 — Apply the 24-48 hour guideline:</strong> For mild, single-episode symptoms (one vomit, slight lethargy, brief appetite loss), monitor for 24-48 hours. If symptoms persist, worsen, or if multiple symptoms appear together, book a vet appointment promptly.</li><li><strong>Step 4 — Use your practice's triage service:</strong> Many UK veterinary practices offer telephone triage. Call your practice first to determine whether your dog needs same-day, routine, or emergency attention. Describe symptoms clearly using your recorded observations.</li><li><strong>Step 5 — Maintain a health record:</strong> Keep a simple log of vaccinations, parasite treatments, weight measurements, and any health events. Bring this to every vet visit so your veterinarian has a complete history for accurate assessment.</li></ol>
</div>
<!-- /wp:group -->""",
    }
    return guides.get(post_id)


# Generic practical guides for non-priority posts
GENERIC_PRACTICAL = {
    "Dog Toys": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: How to Choose Safe Dog Toys</h4>
<ol><li><strong>Step 1 — Assess your dog's size and chew strength:</strong> Choose toys sized so your dog cannot fit the entire toy behind their back teeth. For heavy chewers, select solid rubber or TPR toys rather than plush or rope. The RSPCA advises that a toy too small for your dog's mouth is a choking hazard.</li><li><strong>Step 2 — Check materials and labelling:</strong> Look for toys labelled as non-toxic, BPA-free, and phthalate-free. Food-grade natural rubber and food-grade silicone are generally considered safe materials. Avoid toys with a strong chemical odour, which may indicate unsafe plasticisers.</li><li><strong>Step 3 — Inspect before first use:</strong> Before giving any new toy to your dog, check for loose parts (eyes, squeakers, ribbons), weak seams, and sharp edges. Remove all packaging, tags, and ties. If any component can be pulled off by hand, the toy is not suitable.</li><li><strong>Step 4 — Match toy type to play style:</strong> Fetch dogs benefit from balls and frisbees. Tug players need sturdy rope or rubber tug toys. Solo chewers need durable chew toys. Puzzle-motivated dogs benefit from treat-dispensing toys. Offering variety keeps dogs engaged.</li><li><strong>Step 5 — Establish a regular inspection and replacement routine:</strong> Check all toys weekly for cracks, tears, missing pieces, and significant wear. The PDSA recommends discarding any toy that is breaking apart. Rotate toys every few days to maintain novelty and extend toy lifespan.</li></ol>
</div>
<!-- /wp:group -->""",
    "Uncategorized": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: General Pet Welfare Assessment</h4>
<ol><li><strong>Step 1 — Check environment suitability:</strong> Ensure your pet has access to a clean, safe, and comfortable living space with appropriate temperature, shelter from extremes, and a quiet resting area. The RSPCA's first welfare need is a suitable environment.</li><li><strong>Step 2 — Assess diet and hydration:</strong> Confirm your pet is eating a complete, life-stage-appropriate diet and has constant access to fresh water. Weigh your pet monthly and assess their body condition score (BCS) — you should be able to feel ribs without pressing hard, with a visible waist from above.</li><li><strong>Step 3 — Evaluate behaviour and enrichment:</strong> Observe your pet's daily behaviour for signs of boredom (destructiveness, excessive barking or vocalisation, repetitive movements) or stress (hiding, aggression, appetite changes). Provide daily mental and physical stimulation appropriate to species and breed.</li><li><strong>Step 4 — Review health and preventive care:</strong> Confirm vaccinations, parasite prevention, and dental care are up to date. Schedule annual vet checks for adults and twice-yearly checks for senior pets (7+ years). Keep a simple health log of treatments and any concerns.</li><li><strong>Step 5 — Consider social needs:</strong> The RSPCA's fifth welfare need is the need to be housed with or apart from other animals as appropriate. Dogs generally need regular social interaction with people and other dogs. Cats may prefer solitary living or companionship depending on individual temperament.</li></ol>
</div>
<!-- /wp:group -->""",
}


# ── At a Glance blocks ─────────────────────────────────────────────────

# Post-specific At a Glance blocks
def get_at_a_glance(post_id, title, cluster):
    """Generate At a Glance block specific to the post topic"""
    glances = {
        3960: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">Puppy Toys: At a Glance</h4>
<ul><li><strong>Teething timeline:</strong> Puppies begin teething at approximately 12 weeks, with adult teeth fully in place by 6-7 months. Toy selection should change with each stage.</li><li><strong>Size rule:</strong> A toy should be too large to fit entirely behind the puppy's back teeth. If in doubt, choose the next size up.</li><li><strong>Frozen toys:</strong> Soft rubber toys can be soaked in water and frozen to provide cooling relief for sore teething gums.</li><li><strong>Supervision is essential:</strong> The RSPCA and PDSA both recommend supervising all puppy play with toys, especially during the teething phase when chewing intensity increases.</li><li><strong>Rotation matters:</strong> Rotating 2-3 toys every few days maintains novelty and prevents boredom without overwhelming your puppy with too many options.</li></ul>
</div>
<!-- /wp:group -->""",
        3957: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">Tough Dog Toys: At a Glance</h4>
<ul><li><strong>Material hierarchy for heavy chewers:</strong> Solid natural rubber and hard nylon offer the highest durability. TPR provides moderate durability with more flexibility. Rope and plush are unsuitable for power chewers.</li><li><strong>Tooth safety check:</strong> Press your thumbnail into the toy surface. If it does not give at all, it may be too hard and could chip teeth. A slight indentation indicates an appropriate hardness level.</li><li><strong>No toy is truly indestructible:</strong> Marketing claims of "indestructible" are not regulated. All toys will eventually show wear. The key is choosing toys that withstand your dog's chew strength long enough to be safe between inspections.</li><li><strong>Sizing up reduces risk:</strong> For aggressive chewers, always select a toy one size larger than the manufacturer's breed recommendation to minimise the risk of pieces being bitten off.</li><li><strong>Weekly inspection schedule:</strong> Check all chew toys weekly for deep gouges, cracks, and missing material. Replace immediately if structural integrity is compromised.</li></ul>
</div>
<!-- /wp:group -->""",
        5509: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">Pet Toy Safety: At a Glance</h4>
<ul><li><strong>Most common toy-related emergency:</strong> Foreign body ingestion from toy parts is one of the most frequent emergency presentations in UK veterinary practice (BVA data).</li><li><strong>Material safety priority:</strong> Food-grade natural rubber, food-grade silicone, and BPA-free materials are generally considered safest. Avoid toys with strong chemical odours.</li><li><strong>Size matters most:</strong> A toy that fits entirely behind your pet's back teeth is a choking hazard regardless of material quality.</li><li><strong>Supervision varies by toy type:</strong> Rope and plush toys require active supervision; solid rubber toys can be used with moderate supervision; puzzle toys generally need the least supervision.</li><li><strong>No UK-specific toy safety standard:</strong> Unlike children's toys, pet toys do not have a dedicated UK safety standard. The general Product Safety Regulations 2005 apply, but owners should evaluate safety individually.</li></ul>
</div>
<!-- /wp:group -->""",
        5522: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">Orthopaedic Care for Dogs: At a Glance</h4>
<ul><li><strong>Weight is the primary factor:</strong> Maintaining an ideal body condition score (BCS 4-5 on a 1-9 scale) is the single most impactful action for reducing joint stress in dogs of all ages.</li><li><strong>Early signs to watch:</strong> Reluctance to jump, stiffness after rest, slowing down on walks, or difficulty with stairs may indicate early joint discomfort. Report these to your vet.</li><li><strong>Supplement timing:</strong> Joint supplements typically require 4-8 weeks of consistent use before noticeable improvement. They are not a substitute for veterinary assessment and treatment.</li><li><strong>Exercise adaptation:</strong> Dogs with joint conditions benefit from regular, moderate exercise (such as lead walking and swimming) rather than high-impact activities like ball-chasing on hard surfaces.</li><li><strong>Bedding support:</strong> Orthopaedic beds with memory foam density of 50+ kg/m3 and at least 7cm thickness provide meaningful pressure relief for dogs with joint conditions.</li></ul>
</div>
<!-- /wp:group -->""",
        5467: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">Pet Feeding: At a Glance</h4>
<ul><li><strong>Feeding frequency:</strong> Adult dogs typically need 2 meals per day; adult cats benefit from 2-4 smaller meals. Puppies under 4 months need 4 meals daily, reducing to 2 by 6 months.</li><li><strong>Portion accuracy:</strong> Use kitchen scales rather than measuring cups for more accurate portions. Manufacturer feeding guides are starting points — adjust based on body condition over 2-4 weeks.</li><li><strong>Treat limit:</strong> The PFMA recommends that treats make up no more than 10% of a pet's daily calorie intake. Reduce meal portions on heavy training days.</li><li><strong>Water access:</strong> Fresh, clean water must be available at all times (RSPCA guidance). Change water at least twice daily and clean bowls regularly.</li><li><strong>Transition rule:</strong> When changing foods, mix old and new food gradually over 7-10 days to prevent digestive upset, as recommended by UK veterinary practices.</li></ul>
</div>
<!-- /wp:group -->""",
        5520: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">Dog Health Basics: At a Glance</h4>
<ul><li><strong>Annual vet check:</strong> The BVA recommends at least one veterinary health check per year for adult dogs, and every six months for senior dogs (7+ years).</li><li><strong>Vaccination schedule:</strong> UK puppies receive primary vaccinations at 8 and 10-12 weeks, with annual or triennial boosters depending on vaccine type and vet guidance.</li><li><strong>Dental disease prevalence:</strong> Over 80% of dogs aged three and above show signs of dental disease according to UK veterinary surveys. Regular brushing (2-3 times weekly) significantly reduces risk.</li><li><strong>Parasite prevention:</strong> Year-round flea, tick, and worm prevention is recommended by UK vets. Treatment frequency varies by product — monthly, quarterly, or as directed by your vet.</li><li><strong>Emergency awareness:</strong> Know your nearest emergency vet and their out-of-hours number before you need it. Breathing difficulty, collapse, seizures, and suspected poisoning require immediate emergency contact.</li></ul>
</div>
<!-- /wp:group -->""",
    }
    return glances.get(post_id)


# Generic At a Glance for non-priority posts
GENERIC_AT_A_GLANCE = {
    "Dog Toys": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">At a Glance</h4>
<ul><li><strong>Size safety rule:</strong> A toy should be too large to fit entirely behind your dog's back teeth. When in doubt, choose the next size up.</li><li><strong>Safest materials:</strong> Food-grade natural rubber, food-grade silicone, and BPA-free TPR are generally considered the safest synthetic materials for dog toys.</li><li><strong>Supervision levels:</strong> Rope and plush toys require active supervision. Solid rubber toys need moderate supervision. Treat-dispensing puzzle toys generally require the least supervision.</li><li><strong>Inspection frequency:</strong> Check all toys weekly for cracks, tears, and missing pieces. The PDSA recommends discarding any toy that is breaking apart, regardless of how recently it was purchased.</li></ul>
</div>
<!-- /wp:group -->""",
    "Uncategorized": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">At a Glance</h4>
<ul><li><strong>Five welfare needs:</strong> Under the Animal Welfare Act 2006, UK pet owners must meet five needs: suitable environment, suitable diet, ability to exhibit normal behaviour, companionship needs, and protection from pain, suffering, injury, and disease.</li><li><strong>Vet check frequency:</strong> Annual health checks for adult pets; every six months for seniors (7+ years for dogs, 11+ years for cats), as recommended by the BVA and PDSA.</li><li><strong>Weight monitoring:</strong> Monthly weighing and body condition scoring helps catch weight changes early. The PDSA PAW Report consistently identifies obesity as one of the top welfare concerns for UK pets.</li><li><strong>Preventive care:</strong> Year-round parasite prevention, up-to-date vaccinations, and regular dental care form the foundation of good pet health management as recommended by UK veterinary professionals.</li></ul>
</div>
<!-- /wp:group -->""",
}


# ── Decision Summary block (bonus trust block) ────────────────────────
# Used for posts with very low trust_depth or trust_moat scores
def build_decision_summary(cluster):
    """Build a Decision Summary block with cluster-appropriate content"""
    summaries = {
        "Dog Toys": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#a7f3d0">
<h4 class="wp-block-heading">Decision Summary</h4>
<ul><li><strong>Prioritise safety over durability claims:</strong> No toy is truly indestructible. Choose toys made from food-grade, non-toxic materials sized appropriately for your dog.</li><li><strong>Match toy to chew style:</strong> Gentle chewers can enjoy a wider range of materials. Power chewers should be limited to solid rubber and hard nylon toys.</li><li><strong>Supervise and inspect:</strong> All toy play should be supervised initially. Establish a weekly inspection routine and discard damaged toys immediately.</li><li><strong>Consult your vet if unsure:</strong> If your dog has a history of foreign body ingestion or resource guarding around toys, discuss toy selection and play management with your veterinarian.</li></ul>
</div>
<!-- /wp:group -->""",
        "Uncategorized": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#a7f3d0">
<h4 class="wp-block-heading">Decision Summary</h4>
<ul><li><strong>Start with the five welfare needs:</strong> Use the RSPCA's framework (environment, diet, behaviour, companionship, health) as a checklist for your pet's overall wellbeing.</li><li><strong>Prevention is more effective than reaction:</strong> Regular vet checks, up-to-date parasite prevention, consistent dental care, and daily enrichment prevent most common welfare issues.</li><li><strong>Monitor weight and behaviour:</strong> Monthly weighing and daily behaviour observation are the most practical ways to detect health changes early.</li><li><strong>When in doubt, consult your vet:</strong> UK veterinary practices offer telephone triage for non-emergency concerns. A quick call can determine whether a vet visit is needed.</li></ul>
</div>
<!-- /wp:group -->""",
    }
    return summaries.get(cluster)


# ── Block builders ─────────────────────────────────────────────────────

def build_research_sources_block(cluster):
    """Build the Research Sources and Standards block"""
    refs = UK_REFS.get(cluster, UK_REFS["Uncategorized"])
    return f"""<!-- wp:group {{"style":{{"border":{{"width":"1px","radius":"8px"}},"spacing":{{"padding":{{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}}}}},"borderColor":"","backgroundColor":""}} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#f0f9ff;border-color:#bae6fd">
<h4 class="wp-block-heading">Research Sources and Standards</h4>
<p>{refs['research_sources']}</p>
</div>
<!-- /wp:group -->"""

def build_why_sources_block(cluster):
    """Build the Why We Reference Sources block"""
    refs = UK_REFS.get(cluster, UK_REFS["Uncategorized"])
    return f"""<!-- wp:group {{"style":{{"border":{{"width":"1px","radius":"8px"}},"spacing":{{"padding":{{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}}}}},"borderColor":"","backgroundColor":""}} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#f0f9ff;border-color:#bae6fd">
<h4 class="wp-block-heading">Why We Reference Sources</h4>
<p>{refs['why_sources']}</p>
</div>
<!-- /wp:group -->"""

def build_glossary_block(cluster):
    """Build the Key Terms glossary block"""
    terms = GLOSSARY_TERMS.get(cluster, GLOSSARY_TERMS["Uncategorized"])
    items = "".join([f'<li><strong>{t}:</strong> {d}</li>' for t, d in terms])
    return f"""<!-- wp:group {{"style":{{"border":{{"width":"1px","radius":"8px"}},"spacing":{{"padding":{{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}}}}},"borderColor":"","backgroundColor":""}} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#f8fafc;border-color:#e2e8f0">
<h4 class="wp-block-heading">Key Terms</h4>
<ul>{items}</ul>
</div>
<!-- /wp:group -->"""


# ── Main processing ────────────────────────────────────────────────────

def find_insert_position(content):
    """Find position to insert new blocks — before trust footer or at end"""
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
        if not has_block(content, "Compared") and not has_block(content, "wp-block-table is-style-stripes"):
            # Try post-specific table first, then generic
            table = get_comparison_table(pid, title, cluster)
            if table is None:
                if cluster == "Dog Toys":
                    table = GENERIC_COMPARISON_DOG_TOYS
                else:
                    table = GENERIC_COMPARISON_UNCATEGORIZED
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

# Priority order: highest-scoring posts first (closest to 90 threshold)
PRIORITY_IDS = [
    # Dog Toys high-priority
    3960, 3957,
    # Uncategorized high-priority (diverse topics)
    5467, 5509, 5460, 5522, 5510, 5523, 5520,
]

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
print(f"Phase 10BU Dog Toys + Uncategorized Cluster Enrichment")
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
output_csv = os.path.join(OUTPUT_DIR, "citation_moat_trust_dogtoys_uncat_clusters.csv")
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
