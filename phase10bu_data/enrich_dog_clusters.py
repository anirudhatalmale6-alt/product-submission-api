#!/usr/bin/env python3
"""
Phase 10BU/10BV/10BY Content Enrichment for Dog-related clusters.
Clusters: Dog Food, Dog Health, Dog Beds, Puppy Care, Dog Care, Dog Supplies
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
TARGET_CLUSTERS = {"Dog Food", "Dog Health", "Dog Beds", "Puppy Care", "Dog Care", "Dog Supplies"}
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
    "Dog Food": {
        "research_sources": (
            "Our recommendations align with the Pet Food Manufacturers' Association (PFMA) guidelines "
            "on complete and complementary pet foods, which set nutritional standards across the UK market. "
            "We reference the FEDIAF (European Pet Food Industry Federation) Nutritional Guidelines 2024, "
            "which establish minimum and maximum nutrient levels for dogs at different life stages. "
            "The British Veterinary Association (BVA) position on pet nutrition and the Royal Veterinary "
            "College (RVC) research on canine dietary requirements inform our ingredient analysis. "
            "Where relevant, we consult PDSA Animal Wellbeing (PAW) Report data on feeding practices across UK households."
        ),
        "why_sources": (
            "We reference PFMA, FEDIAF, and BVA guidelines because pet nutrition claims vary widely across "
            "the UK market. By grounding our information in standards set by recognised UK and European "
            "bodies, we help owners distinguish evidence-based feeding advice from marketing language. "
            "Our methodology focuses on ingredient transparency, nutritional adequacy statements, and "
            "manufacturing standards rather than brand reputation alone."
        ),
    },
    "Dog Health": {
        "research_sources": (
            "Our health guidance references the British Veterinary Association (BVA) clinical position "
            "statements and the PDSA's annual PAW Report, which surveys veterinary professionals and "
            "pet owners across the UK on common health concerns. We consult Royal Veterinary College (RVC) "
            "published research on canine health conditions and treatment outcomes. "
            "The Kennel Club's health screening programmes and breed-specific guidance inform our "
            "breed-related health recommendations. RSPCA welfare standards and Blue Cross veterinary "
            "advice pages provide additional UK-specific clinical context."
        ),
        "why_sources": (
            "Pet health information online varies significantly in accuracy and currency. We reference "
            "the BVA, RVC, and PDSA because these UK institutions maintain peer-reviewed, regularly "
            "updated clinical guidance. Our approach prioritises evidence from UK veterinary practice "
            "and registered charity welfare standards, ensuring advice reflects the medications, "
            "treatments, and preventive care available to UK dog owners."
        ),
    },
    "Dog Beds": {
        "research_sources": (
            "Our bedding guidance draws on the RSPCA's five welfare needs framework, particularly the "
            "need for a suitable environment including appropriate resting areas. The British Veterinary "
            "Association (BVA) recommendations on orthopaedic support for ageing and arthritic dogs "
            "inform our joint-support bed assessments. We reference PDSA guidance on sleeping environments "
            "and the Kennel Club's advice on crate training and bed sizing for different breeds. "
            "Material safety assessments align with UK trading standards and REACH chemical regulations "
            "applicable to pet products sold in the UK."
        ),
        "why_sources": (
            "Dog bed marketing frequently makes unsupported orthopaedic or therapeutic claims. We "
            "reference RSPCA welfare standards and BVA clinical guidance to help owners evaluate "
            "bed features based on evidence rather than branding. Our assessments focus on measurable "
            "factors such as foam density, washability, and size appropriateness as recommended by "
            "UK veterinary professionals."
        ),
    },
    "Puppy Care": {
        "research_sources": (
            "Our puppy care guidance is informed by the Kennel Club's Assured Breeder Scheme standards "
            "and their published puppy socialisation guidelines. We reference the British Veterinary "
            "Association (BVA) and British Small Animal Veterinary Association (BSAVA) protocols for "
            "puppy vaccination schedules, worming, and developmental milestones specific to UK practice. "
            "The RSPCA's puppy welfare guidance and PDSA's new puppy owner resources provide additional "
            "UK-specific frameworks. Blue Cross puppy care advice contributes to our behavioural and "
            "training recommendations."
        ),
        "why_sources": (
            "Puppy care advice is particularly sensitive because early-life decisions significantly "
            "impact long-term health and behaviour. We reference the Kennel Club, BVA, and BSAVA "
            "because their puppy care protocols reflect current UK veterinary consensus. Our approach "
            "ensures vaccination schedules, feeding transitions, and socialisation windows align with "
            "what UK veterinary practices actually recommend."
        ),
    },
    "Dog Care": {
        "research_sources": (
            "Our care guidance references the RSPCA's Animal Welfare Act 2006 compliance framework "
            "and their five welfare needs model. The British Veterinary Association (BVA) position "
            "statements on grooming, dental care, and preventive health inform our practical advice. "
            "We consult the PDSA PAW Report for UK-wide data on dog care practices and veterinary "
            "access. The Kennel Club's breed-specific grooming guides and the Blue Cross's general "
            "care resources provide additional UK-specific context for our recommendations."
        ),
        "why_sources": (
            "Dog care encompasses grooming, dental health, seasonal safety, and routine maintenance "
            "where incorrect practices can cause harm. We reference BVA, RSPCA, and PDSA standards "
            "because they represent the UK veterinary and welfare consensus. Our methodology evaluates "
            "care practices and products against these established standards rather than relying on "
            "manufacturer claims alone."
        ),
    },
    "Dog Supplies": {
        "research_sources": (
            "Our supply recommendations reference the RSPCA's equipment guidance for dogs, covering "
            "bowls, leads, and feeding accessories. The British Veterinary Association (BVA) published "
            "guidance on elevated feeding, slow feeders, and hydration informs our product category "
            "assessments. We consult PDSA's pet care equipment recommendations and the Kennel Club's "
            "guidance on appropriate supplies for different breeds and life stages. Material safety "
            "standards align with UK product safety regulations and relevant British Standards (BS) "
            "for pet accessories."
        ),
        "why_sources": (
            "The dog supplies market includes thousands of products with varying quality and suitability "
            "claims. We reference RSPCA, BVA, and PDSA guidelines because these organisations evaluate "
            "pet equipment based on animal welfare outcomes, not commercial interests. Our approach "
            "assesses supplies against measurable criteria such as durability, safety standards, and "
            "suitability for specific needs as defined by UK veterinary and welfare bodies."
        ),
    },
}

# Glossary terms per cluster
GLOSSARY_TERMS = {
    "Dog Food": [
        ("Complete food", "A dog food that provides all required nutrients at correct levels, meeting FEDIAF/PFMA standards, so no supplementation is needed."),
        ("Complementary food", "A dog food designed to be fed alongside other products; it does not meet full nutritional requirements on its own."),
        ("Crude protein", "The total protein content measured by nitrogen analysis, listed as a percentage on UK pet food labels under analytical constituents."),
        ("Analytical constituents", "The mandatory nutritional breakdown on UK pet food labels showing protein, fat, fibre, and ash percentages."),
        ("Life-stage feeding", "Adjusting food type and portion size to match a dog's developmental stage: puppy, adult, or senior, as recommended by PFMA."),
    ],
    "Dog Health": [
        ("Prophylactic treatment", "Preventive medical care given before disease occurs, such as flea or worm treatments administered on a regular schedule."),
        ("Titre testing", "A blood test measuring antibody levels to determine whether a dog's existing immunity is sufficient without re-vaccination."),
        ("NSAID", "Non-Steroidal Anti-Inflammatory Drug; commonly prescribed by UK vets for pain relief in conditions like arthritis or post-surgery recovery."),
        ("Glucosamine", "A naturally occurring compound used in joint supplements to support cartilage health, commonly recommended by UK vets for older dogs."),
        ("Body Condition Score (BCS)", "A standardised 1-9 scale used by UK veterinary professionals to assess whether a dog is underweight, ideal, or overweight."),
    ],
    "Dog Beds": [
        ("Memory foam", "Viscoelastic foam that moulds to a dog's body shape, redistributing weight to reduce pressure on joints; density is measured in kg/m3."),
        ("Orthopaedic bed", "A bed specifically designed with supportive foam or filling to relieve joint pressure, typically recommended for senior or arthritic dogs."),
        ("Bolster bed", "A dog bed with raised edges that provide head and neck support and a sense of security for dogs that like to lean or nest."),
        ("Denier (D)", "A unit measuring fabric thickness and durability; higher denier numbers (e.g., 600D, 1200D) indicate more chew-resistant and waterproof covers."),
        ("Calming bed", "A round, deep-sided bed with soft faux-fur lining designed to reduce anxiety by mimicking the warmth of nestling with littermates."),
    ],
    "Puppy Care": [
        ("Socialisation window", "The critical developmental period between approximately 3 and 14 weeks of age when puppies are most receptive to new experiences."),
        ("Primary vaccination course", "The initial series of vaccinations (typically at 8 and 10-12 weeks in the UK) that establishes baseline immunity against core diseases."),
        ("Crate training", "A positive-reinforcement method of teaching a puppy to accept a crate as a safe resting space, aiding housetraining and travel."),
        ("Teething phase", "The period from approximately 12 to 24 weeks when puppies lose deciduous teeth and permanent teeth emerge, often causing increased chewing."),
        ("Recall training", "Teaching a puppy to return when called; a foundational skill recommended by the Kennel Club before off-lead exercise."),
    ],
    "Dog Care": [
        ("Double coat", "A coat consisting of a dense undercoat beneath longer guard hairs; common in breeds like Labradors and German Shepherds, requiring specific grooming tools."),
        ("Stripping", "A grooming technique for wire-coated breeds that removes dead outer coat by hand or with a stripping knife, maintaining coat texture and colour."),
        ("Quick (nail)", "The blood vessel and nerve inside a dog's nail; cutting into the quick causes pain and bleeding, which is why gradual trimming is recommended."),
        ("Desensitisation", "Gradually exposing a dog to a grooming tool or procedure at low intensity to reduce fear or stress responses over time."),
        ("Enzymatic cleaner", "A cleaning product that uses enzymes to break down organic matter (urine, saliva, food); preferred over chemical cleaners for pet-safe hygiene."),
    ],
    "Dog Supplies": [
        ("Slow feeder", "A bowl with internal ridges or patterns that force a dog to eat around obstacles, reducing eating speed and improving digestion."),
        ("Elevated feeder", "A raised bowl stand that positions food and water at a dog's chest height, sometimes recommended for large breeds or dogs with mobility issues."),
        ("BPA-free", "A product manufactured without bisphenol A, a chemical compound found in some plastics that can leach into food and water."),
        ("Stainless steel (304 grade)", "Food-grade stainless steel commonly used in quality dog bowls; resistant to bacteria buildup, rust, and scratching."),
        ("Collapsible bowl", "A silicone or fabric bowl that folds flat for travel, typically holding 300-500ml and meeting food-contact safety standards."),
    ],
}

# Comparison tables per post (tailored)
def get_comparison_table(post_id, title, cluster):
    """Generate comparison table HTML specific to the post topic"""
    tables = {
        # Dog Food posts - educational comparison only (commercial content blocked)
        3836: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Dog Food Types Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Feature</th><th>Complete Dry (Kibble)</th><th>Complete Wet</th><th>Raw / BARF</th></tr></thead><tbody><tr><td>Moisture Content</td><td>8-10% (PFMA standard)</td><td>75-85% moisture</td><td>60-70% moisture</td></tr><tr><td>Storage</td><td>Shelf-stable 12-18 months unopened</td><td>Refrigerate after opening, use within 48 hours</td><td>Frozen storage required, thaw before serving</td></tr><tr><td>Dental Impact</td><td>Some abrasive action on teeth (BVA notes limited evidence)</td><td>No mechanical cleaning effect</td><td>Raw bones may help but carry fracture risk (BVA caution)</td></tr><tr><td>Typical Cost (UK)</td><td>Lower per-day feeding cost</td><td>Higher per-day cost for equivalent nutrition</td><td>Variable; DIY lower, commercial higher</td></tr><tr><td>Best Suited For</td><td>Owners wanting convenience and portion control</td><td>Dogs needing extra hydration or with dental issues</td><td>Experienced owners with food-handling knowledge</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        3839: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Puppy Food Types Compared by Life Stage</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Feature</th><th>Small Breed Puppy</th><th>Medium Breed Puppy</th><th>Large Breed Puppy</th></tr></thead><tbody><tr><td>Growth Period</td><td>Reaches adult size by 10-12 months</td><td>Reaches adult size by 12-15 months</td><td>Reaches adult size by 18-24 months</td></tr><tr><td>Calorie Density Need</td><td>Higher kcal/kg due to fast metabolism</td><td>Moderate kcal/kg</td><td>Controlled kcal/kg to prevent too-rapid growth</td></tr><tr><td>Calcium:Phosphorus Ratio</td><td>1.2:1 (FEDIAF guideline)</td><td>1.2:1 (FEDIAF guideline)</td><td>1.2:1 with lower maximum calcium (FEDIAF large breed guideline)</td></tr><tr><td>Feeding Frequency</td><td>3-4 meals/day until 6 months, then 2/day</td><td>3 meals/day until 6 months, then 2/day</td><td>3 meals/day until 6 months, then 2/day</td></tr><tr><td>Key Risk</td><td>Hypoglycaemia if meals skipped</td><td>Obesity if overfed</td><td>Developmental orthopaedic disease if calcium/calories too high</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        # Dog Beds posts
        4004: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Orthopaedic Dog Bed Fill Types Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Feature</th><th>Memory Foam (Solid)</th><th>Egg-Crate Memory Foam</th><th>Orthopaedic Fibre Fill</th></tr></thead><tbody><tr><td>Pressure Relief</td><td>Moulds to body shape; redistributes weight across surface</td><td>Air channels between peaks improve airflow and pressure distribution</td><td>Moderate support; less contouring than foam options</td></tr><tr><td>Durability</td><td>High-density (50+ kg/m3) lasts 3-5 years without sagging</td><td>Slightly less durable due to thinner foam sections</td><td>May flatten over time; requires periodic refluffing</td></tr><tr><td>Temperature</td><td>Retains body heat; may be warm in summer</td><td>Better airflow between peaks; cooler than solid foam</td><td>Breathable; does not retain heat</td></tr><tr><td>Washability</td><td>Foam not machine-washable; removable cover essential</td><td>Foam not machine-washable; removable cover essential</td><td>Some fibre fills are machine-washable; check label</td></tr><tr><td>Best For</td><td>Arthritic or post-surgery dogs needing maximum joint support</td><td>Dogs needing orthopaedic support who tend to overheat</td><td>Budget-conscious owners or dogs without severe joint issues</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        3996: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Dog Bed Styles Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Feature</th><th>Bolster / Sofa Bed</th><th>Flat Mat / Cushion</th><th>Donut / Calming Bed</th></tr></thead><tbody><tr><td>Support Type</td><td>Raised edges support head and neck; central mattress area</td><td>Even surface; no raised edges</td><td>Deep circular walls; nesting design</td></tr><tr><td>Size Range</td><td>Small to XXL; suits most breeds</td><td>Easily trimmed to fit crates or car boots</td><td>Typically small to large; less common for giant breeds</td></tr><tr><td>Insulation</td><td>Moderate; bolster edges add warmth around body</td><td>Minimal; relies on fill thickness alone</td><td>High; enclosed shape traps body warmth</td></tr><tr><td>Ease of Washing</td><td>Removable covers common; larger sizes need big machine</td><td>Often fully machine-washable due to flat design</td><td>Check label; faux fur covers may require gentle cycle</td></tr><tr><td>Best For</td><td>Dogs that lean or rest their head on edges</td><td>Crate use, travel, or dogs that stretch out flat</td><td>Anxious dogs or breeds that naturally curl to sleep</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        # Dog Health posts
        4110: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Common Joint Supplement Ingredients Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Ingredient</th><th>Glucosamine HCl</th><th>Chondroitin Sulphate</th><th>Green-Lipped Mussel (GLM)</th></tr></thead><tbody><tr><td>Primary Function</td><td>Supports cartilage formation and repair</td><td>Helps cartilage retain water and elasticity</td><td>Contains omega-3 fatty acids and glycosaminoglycans</td></tr><tr><td>Evidence Level</td><td>Moderate veterinary evidence; widely used in UK practice</td><td>Often combined with glucosamine; limited standalone studies</td><td>Growing evidence from RVC and international studies</td></tr><tr><td>Typical Dosage (medium dog)</td><td>500-1000mg daily (consult vet for exact dose)</td><td>400-800mg daily (usually paired with glucosamine)</td><td>Varies by product; follow manufacturer and vet guidance</td></tr><tr><td>Onset of Effect</td><td>4-6 weeks for noticeable improvement</td><td>4-6 weeks (usually taken alongside glucosamine)</td><td>4-8 weeks depending on formulation</td></tr><tr><td>Best For</td><td>General joint maintenance in active or ageing dogs</td><td>Combined therapy with glucosamine for arthritis management</td><td>Owners seeking a natural-source supplement with anti-inflammatory properties</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        4089: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Routine Dog Health Checks by Frequency</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Check Type</th><th>Daily</th><th>Weekly</th><th>Monthly</th><th>Annually (Vet)</th></tr></thead><tbody><tr><td>Eyes and Ears</td><td>Quick visual check for discharge</td><td>Clean ears if needed; check for redness</td><td>—</td><td>Full ophthalmic and otic exam</td></tr><tr><td>Teeth and Gums</td><td>—</td><td>Brush teeth 2-3 times</td><td>Check for tartar buildup</td><td>Professional dental assessment</td></tr><tr><td>Coat and Skin</td><td>Visual check during walks</td><td>Brush and check for parasites</td><td>Full body check for lumps or sores</td><td>Dermatological assessment if needed</td></tr><tr><td>Weight</td><td>—</td><td>—</td><td>Weigh and record; assess BCS</td><td>Full body condition assessment</td></tr><tr><td>Parasite Prevention</td><td>—</td><td>—</td><td>Apply flea/tick treatment per vet schedule</td><td>Review prevention plan with vet</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        # Dog Supplies posts
        4167: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Dog Water Bottle Types Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Feature</th><th>Squeeze Bottle with Tray</th><th>Clip-On Bowl Bottle</th><th>Filter Bottle</th></tr></thead><tbody><tr><td>Capacity</td><td>Typically 300-550ml</td><td>Typically 250-500ml</td><td>Typically 350-500ml</td></tr><tr><td>Mechanism</td><td>Squeeze to release water into attached trough</td><td>Pour into detachable or flip-out bowl</td><td>Water passes through activated carbon filter</td></tr><tr><td>Leak Prevention</td><td>Lock button prevents accidental squeeze</td><td>Sealed cap; bowl is separate</td><td>Sealed with filter cartridge</td></tr><tr><td>Ease of Cleaning</td><td>Wide-mouth designs easier; trough needs regular rinse</td><td>Bowl and bottle clean separately</td><td>Filter requires periodic replacement (typically monthly)</td></tr><tr><td>Best For</td><td>Quick drinks on walks and hikes</td><td>Dogs that prefer drinking from a bowl shape</td><td>Areas with variable water quality or long travel days</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        4160: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Elevated Bowl Stand Types Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Feature</th><th>Fixed-Height Stand</th><th>Adjustable-Height Stand</th><th>Wall-Mounted Bracket</th></tr></thead><tbody><tr><td>Height Options</td><td>Single height; must buy correct size for breed</td><td>Multiple height settings; grows with puppy or suits multiple dogs</td><td>Set at installation; adjustable mounting height</td></tr><tr><td>Stability</td><td>Wide base; low tip-over risk</td><td>Generally stable; check locking mechanism quality</td><td>Fixed to wall; no floor tip risk</td></tr><tr><td>Materials</td><td>Wood, bamboo, or powder-coated metal</td><td>Usually metal or plastic with sliding columns</td><td>Metal bracket with detachable bowls</td></tr><tr><td>Floor Space</td><td>Moderate footprint</td><td>Moderate footprint; may be wider than fixed stands</td><td>No floor space used; bowls mounted on wall</td></tr><tr><td>Best For</td><td>Single-dog households with known breed adult height</td><td>Multi-dog homes or growing puppies</td><td>Small spaces or messy drinkers where floor cleanup is a concern</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
        # Dog Care posts
        4057: """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Grooming Tool Types Compared by Coat</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Tool</th><th>Slicker Brush</th><th>Undercoat Rake</th><th>Bristle Brush</th></tr></thead><tbody><tr><td>Coat Type</td><td>Medium to long coats; curly or wavy coats</td><td>Double-coated breeds (e.g., Husky, Retriever)</td><td>Short, smooth coats (e.g., Boxer, Dachshund)</td></tr><tr><td>Primary Function</td><td>Removes tangles and loose fur; smooths coat</td><td>Penetrates topcoat to remove dead undercoat</td><td>Distributes natural oils; removes surface dust</td></tr><tr><td>Frequency</td><td>2-3 times per week; daily during shedding season</td><td>Weekly; more frequently during spring/autumn moult</td><td>2-3 times per week for coat shine</td></tr><tr><td>Caution</td><td>Use gentle pressure to avoid brush burn on sensitive skin</td><td>Do not use on single-coated breeds; can damage coat</td><td>Limited detangling ability; not for matted coats</td></tr><tr><td>Best For</td><td>Poodles, Spaniels, Collies, and mixed long coats</td><td>Labradors, German Shepherds, Huskies, Malamutes</td><td>Whippets, Beagles, Staffies, and short-haired crosses</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
    }
    return tables.get(post_id)

# Practical step-by-step guides per post
def get_practical_guide(post_id, title, cluster):
    """Generate practical guide HTML specific to the post topic"""
    guides = {
        3836: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: How to Evaluate Dog Food Labels (UK)</h4>
<ol><li><strong>Step 1 — Check the declaration:</strong> Look for "Complete pet food" on the label. Under UK/PFMA regulations, only foods labelled "complete" provide all required nutrients. If it says "complementary," it must be fed alongside a complete food.</li><li><strong>Step 2 — Read the composition list:</strong> Ingredients are listed by weight in descending order. Identify the first named meat source (e.g., "chicken 26%"). Percentage declarations above 4% are meaningful indicators of primary protein.</li><li><strong>Step 3 — Check analytical constituents:</strong> Compare crude protein (typically 20-30% for adult dogs in dry food), crude fat (8-18%), crude fibre (2-5%), and crude ash (under 8%). These ranges align with FEDIAF 2024 adult maintenance guidelines.</li><li><strong>Step 4 — Verify life-stage suitability:</strong> Match the food to your dog's stage: puppy (growth), adult (maintenance), or senior (typically 7+ years). PFMA guidelines note that puppies require higher protein and calcium ratios than adult dogs.</li><li><strong>Step 5 — Transition gradually:</strong> When switching foods, mix 25% new food with 75% old food for 2-3 days, then 50/50 for 2-3 days, then 75/25 for 2-3 days. This 7-10 day transition helps prevent digestive upset, as recommended by most UK veterinary practices.</li></ol>
</div>
<!-- /wp:group -->""",
        3839: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: Transitioning Your Puppy's Food by Growth Stage</h4>
<ol><li><strong>Step 1 — Confirm breed size category:</strong> Determine whether your puppy is small (&lt;10kg adult), medium (10-25kg), or large/giant (&gt;25kg). This affects growth rate, calorie needs, and when to transition to adult food (PFMA guidelines).</li><li><strong>Step 2 — Set feeding frequency by age:</strong> From weaning to 4 months: 4 meals per day. From 4-6 months: 3 meals per day. From 6 months onward: 2 meals per day. Adjust portions per the food manufacturer's weight-based feeding chart.</li><li><strong>Step 3 — Weigh fortnightly and adjust:</strong> Use scales (not visual assessment alone) to track growth. Compare against breed-specific growth curves where available. The Kennel Club provides general weight guidelines for registered breeds.</li><li><strong>Step 4 — Plan the adult food transition:</strong> Small breeds: transition at 10-12 months. Medium breeds: 12-15 months. Large/giant breeds: 18-24 months. Begin the switch using a 7-10 day gradual mix as recommended by UK vets.</li><li><strong>Step 5 — Monitor and consult:</strong> Track stool quality (firm and well-formed indicates good digestion), coat condition, and energy levels. If stools are loose for more than 48 hours after transition, slow down and consult your vet.</li></ol>
</div>
<!-- /wp:group -->""",
        4089: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: Setting Up a Home Health Check Routine</h4>
<ol><li><strong>Step 1 — Schedule weekly checks:</strong> Choose a consistent day each week for a 5-minute physical check. Handle your dog's paws, ears, mouth, and body so they become comfortable with being examined — this also helps your vet during consultations.</li><li><strong>Step 2 — Eyes and ears:</strong> Check eyes for cloudiness, redness, or discharge. Look inside ears for dark wax, odour, or redness — these may indicate infection. The PDSA recommends cleaning ears only if visibly dirty, using vet-approved ear cleaner.</li><li><strong>Step 3 — Teeth and gums:</strong> Lift lips to check gum colour (healthy gums are pink, not white or red). Look for tartar buildup along the gum line. The BVA reports that over 80% of dogs over age three show signs of dental disease.</li><li><strong>Step 4 — Skin and coat:</strong> Run your hands over the entire body feeling for lumps, bumps, or areas of sensitivity. Part the fur to check for fleas, ticks, or skin irritation. Note any new lumps and measure them so you can report changes to your vet.</li><li><strong>Step 5 — Weight and body condition:</strong> Weigh your dog monthly using bathroom scales (hold dog, weigh together, subtract your weight). Assess using the BCS 1-9 scale: you should feel ribs without pressing hard, see a visible waist from above, and a tucked abdomen from the side (BCS 4-5 is ideal).</li></ol>
</div>
<!-- /wp:group -->""",
    }
    return guides.get(post_id)

# "At a Glance" blocks per post
def get_at_a_glance(post_id, title, cluster):
    """Generate At a Glance block specific to the post topic"""
    glances = {
        4004: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">Orthopaedic Dog Beds: At a Glance</h4>
<ul><li><strong>What makes a bed orthopaedic:</strong> High-density memory foam (50+ kg/m3) or layered support foam that distributes weight and reduces pressure on joints.</li><li><strong>Who benefits most:</strong> Senior dogs, breeds prone to hip dysplasia or arthritis, post-surgery recovery dogs, and large breeds over 25kg.</li><li><strong>Key feature to check:</strong> Foam density and thickness — a minimum of 7cm solid memory foam provides meaningful joint support according to veterinary physiotherapy guidance.</li><li><strong>Cover considerations:</strong> Removable, machine-washable covers rated at 600D or higher denier for durability and ease of hygiene.</li><li><strong>Expected lifespan:</strong> Quality orthopaedic beds with high-density foam typically maintain support for 3-5 years with regular cover washing.</li></ul>
</div>
<!-- /wp:group -->""",
        4110: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">Dog Joint Supplements: At a Glance</h4>
<ul><li><strong>Common active ingredients:</strong> Glucosamine HCl, chondroitin sulphate, green-lipped mussel extract, omega-3 fatty acids, and MSM (methylsulfonylmethane).</li><li><strong>When to start:</strong> Veterinary guidance varies, but supplements are commonly introduced for dogs showing early stiffness, typically from age 5-7 for large breeds and 7-9 for smaller breeds.</li><li><strong>Time to see results:</strong> Most joint supplements require 4-8 weeks of consistent daily use before noticeable improvement in mobility.</li><li><strong>Regulation in the UK:</strong> Pet supplements are not regulated as veterinary medicines unless they make medicinal claims. Look for products manufactured to GMP standards.</li><li><strong>Always consult your vet:</strong> Joint supplements may interact with prescribed NSAIDs or other medications. A vet can also rule out conditions requiring surgical rather than supplementary intervention.</li></ul>
</div>
<!-- /wp:group -->""",
        4167: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">Dog Water Bottles: At a Glance</h4>
<ul><li><strong>Daily water needs:</strong> Dogs typically need 40-60ml of water per kilogram of body weight daily, increasing with exercise and warm weather (PDSA guideline).</li><li><strong>Ideal travel bottle capacity:</strong> 350-550ml covers a 30-60 minute walk for most medium-sized dogs; carry extra on hot days or long hikes.</li><li><strong>Material safety:</strong> Choose BPA-free plastics or food-grade stainless steel. Silicone trough attachments should be labelled food-safe.</li><li><strong>Cleaning frequency:</strong> Rinse the trough after each use and deep-clean the bottle with warm soapy water at least twice per week to prevent bacterial buildup.</li><li><strong>Signs of dehydration to watch:</strong> Dry gums, loss of skin elasticity (pinch test), lethargy, and dark-coloured urine indicate your dog needs water immediately.</li></ul>
</div>
<!-- /wp:group -->""",
        4057: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">Dog Grooming Supplies: At a Glance</h4>
<ul><li><strong>Core tools needed:</strong> Breed-appropriate brush, nail clippers or grinder, dog-specific shampoo, ear cleaner, and styptic powder for nail accidents.</li><li><strong>Grooming frequency:</strong> Short coats need brushing 1-2 times weekly; long or double coats need 3-5 times weekly, with daily brushing during shedding season.</li><li><strong>Shampoo pH:</strong> Dog skin has a pH of approximately 7.0-7.5 (neutral to slightly alkaline), so human shampoos (pH 4.5-5.5) are too acidic and can cause irritation.</li><li><strong>Nail trimming interval:</strong> Every 2-4 weeks depending on activity level and surface exposure. If you hear clicking on hard floors, nails are overdue for a trim.</li><li><strong>UK regulatory note:</strong> Under the Animal Welfare Act 2006, owners have a duty to meet grooming needs as part of the requirement to protect dogs from pain, suffering, and disease.</li></ul>
</div>
<!-- /wp:group -->""",
        4160: """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">Elevated Dog Bowls: At a Glance</h4>
<ul><li><strong>Recommended height:</strong> The bowl rim should sit level with the bottom of your dog's chest. Measure from the floor to the point where the front legs meet the chest.</li><li><strong>Who benefits most:</strong> Large and giant breeds, senior dogs with arthritis or neck stiffness, and dogs recovering from surgery affecting the neck or spine.</li><li><strong>Bloat (GDV) consideration:</strong> Research on elevated feeders and bloat risk is inconclusive. The BVA recommends discussing feeding position with your vet if your dog's breed is prone to gastric dilatation-volvulus.</li><li><strong>Material options:</strong> Stainless steel bowls in wooden, bamboo, or metal stands. Ensure bowls are removable for thorough cleaning.</li><li><strong>Stability check:</strong> A good elevated stand should not slide or tip when your dog eats. Non-slip feet or a weighted base are important features for enthusiastic eaters.</li></ul>
</div>
<!-- /wp:group -->""",
    }
    return glances.get(post_id)


def build_research_sources_block(cluster):
    """Build the Research Sources and Standards block"""
    refs = UK_REFS.get(cluster, UK_REFS["Dog Care"])
    return f"""<!-- wp:group {{"style":{{"border":{{"width":"1px","radius":"8px"}},"spacing":{{"padding":{{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}}}}},"borderColor":"","backgroundColor":""}} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#f0f9ff;border-color:#bae6fd">
<h4 class="wp-block-heading">Research Sources and Standards</h4>
<p>{refs['research_sources']}</p>
</div>
<!-- /wp:group -->"""

def build_why_sources_block(cluster):
    """Build the Why We Reference Sources block"""
    refs = UK_REFS.get(cluster, UK_REFS["Dog Care"])
    return f"""<!-- wp:group {{"style":{{"border":{{"width":"1px","radius":"8px"}},"spacing":{{"padding":{{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}}}}},"borderColor":"","backgroundColor":""}} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#f0f9ff;border-color:#bae6fd">
<h4 class="wp-block-heading">Why We Reference Sources</h4>
<p>{refs['why_sources']}</p>
</div>
<!-- /wp:group -->"""

def build_glossary_block(cluster):
    """Build the Key Terms glossary block"""
    terms = GLOSSARY_TERMS.get(cluster, GLOSSARY_TERMS["Dog Care"])
    items = "".join([f'<li><strong>{t}:</strong> {d}</li>' for t, d in terms])
    return f"""<!-- wp:group {{"style":{{"border":{{"width":"1px","radius":"8px"}},"spacing":{{"padding":{{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}}}}},"borderColor":"","backgroundColor":""}} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#f8fafc;border-color:#e2e8f0">
<h4 class="wp-block-heading">Key Terms</h4>
<ul>{items}</ul>
</div>
<!-- /wp:group -->"""

# Generic practical guides for non-priority posts
GENERIC_PRACTICAL = {
    "Dog Food": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: Assessing Your Dog's Food</h4>
<ol><li><strong>Step 1 — Verify completeness:</strong> Check the label states "Complete pet food for adult dogs" (or appropriate life stage). Under UK PFMA regulations, this confirms the food meets all nutritional requirements.</li><li><strong>Step 2 — Identify the protein source:</strong> The first ingredient should be a named animal protein (e.g., "chicken," "salmon," "lamb") with a declared percentage. Avoid vague terms like "meat and animal derivatives" if transparency matters to you.</li><li><strong>Step 3 — Check the feeding guide:</strong> Follow the manufacturer's recommended daily amount for your dog's weight, then adjust by 10-15% based on activity level and body condition over 2-4 weeks.</li><li><strong>Step 4 — Monitor over 4-6 weeks:</strong> Assess stool quality (firm and well-formed), coat condition (glossy, not dry), energy levels, and weight stability. These are practical indicators that the food suits your dog.</li><li><strong>Step 5 — Review annually:</strong> Reassess food suitability at each annual vet check. Nutritional needs change with age, activity level, and health status. Transition to senior formulas when your vet recommends it.</li></ol>
</div>
<!-- /wp:group -->""",
    "Dog Health": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: When to Contact Your Vet</h4>
<ol><li><strong>Step 1 — Know the emergency signs:</strong> Difficulty breathing, collapse, seizures, bloated/hard abdomen, inability to urinate, or suspected poisoning require immediate emergency vet contact.</li><li><strong>Step 2 — Track non-emergency symptoms:</strong> Note the onset, duration, and severity of symptoms such as vomiting, diarrhoea, limping, or appetite loss. Record this information to share with your vet.</li><li><strong>Step 3 — Apply the 24-48 hour rule:</strong> For mild symptoms (single vomit episode, slight lethargy), monitor for 24-48 hours. If symptoms persist, worsen, or multiply, book a vet appointment.</li><li><strong>Step 4 — Use your vet's triage service:</strong> Many UK practices offer telephone triage. Call your practice first to determine urgency — they can advise whether your dog needs same-day, routine, or emergency attention.</li><li><strong>Step 5 — Keep records accessible:</strong> Maintain a simple log of vaccinations, parasite treatments, and any health events. Bring this to appointments so your vet has a complete history for accurate diagnosis.</li></ol>
</div>
<!-- /wp:group -->""",
    "Dog Beds": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: Choosing and Maintaining a Dog Bed</h4>
<ol><li><strong>Step 1 — Measure your dog:</strong> Measure from nose to tail base while your dog is lying in their natural sleeping position. Add 15-20cm to get the minimum bed length. For width, measure shoulder-to-shoulder and add 15cm.</li><li><strong>Step 2 — Match the bed to sleeping style:</strong> Curlers suit donut or bolster beds. Stretchers need flat mats or large cushions. Leaners benefit from beds with supportive raised edges.</li><li><strong>Step 3 — Check the fill and cover:</strong> For dogs over 7 years or with joint issues, choose memory foam with density rated 50+ kg/m3. Ensure the cover is removable and machine-washable at 30-40°C.</li><li><strong>Step 4 — Place in a suitable location:</strong> Position away from draughts and direct heat sources, in a quiet area where your dog can rest undisturbed. The RSPCA recommends dogs have access to a comfortable resting place at all times.</li><li><strong>Step 5 — Maintain on a schedule:</strong> Wash the cover weekly or fortnightly. Vacuum the bed base monthly. Replace the bed when foam no longer springs back within 10 seconds of pressing, or when the cover cannot be cleaned effectively.</li></ol>
</div>
<!-- /wp:group -->""",
    "Puppy Care": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: Your Puppy's First 12 Weeks at Home</h4>
<ol><li><strong>Step 1 — Puppy-proof your home (Day 1):</strong> Secure cables, remove toxic plants (lilies, daffodils, azaleas), block access to stairs, and store cleaning products out of reach. The RSPCA lists common household hazards for puppies on their website.</li><li><strong>Step 2 — Register with a vet (Week 1):</strong> Book a health check within the first week. Confirm vaccination status and schedule the primary vaccination course (typically 8 and 10-12 weeks). Discuss microchipping if not already done — it is a legal requirement in England under the Microchipping of Dogs Regulations 2015.</li><li><strong>Step 3 — Begin socialisation (Weeks 1-4):</strong> During the critical socialisation window (up to 14 weeks), expose your puppy to different sounds, surfaces, people, and experiences in a positive, controlled way. The Kennel Club's Puppy Socialisation Plan provides a structured checklist.</li><li><strong>Step 4 — Establish routine (Weeks 2-8):</strong> Set consistent feeding times (3-4 meals daily), toilet breaks every 1-2 hours, and short 5-minute training sessions. Puppies thrive on predictability during this adjustment period.</li><li><strong>Step 5 — Start basic training (Weeks 4-12):</strong> Focus on name recognition, sit, and recall using positive reinforcement only. The Kennel Club and RSPCA both recommend reward-based training methods. Avoid punishment-based techniques, which the BVA position statement advises against.</li></ol>
</div>
<!-- /wp:group -->""",
    "Dog Care": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: Establishing a Dog Care Routine</h4>
<ol><li><strong>Step 1 — Set a daily structure:</strong> Dogs benefit from consistent wake, feed, walk, and rest times. Aim for at least two walks daily (minimum 30 minutes each for adult dogs, adjusted for breed and age) plus a regular feeding schedule.</li><li><strong>Step 2 — Schedule grooming by coat type:</strong> Short coats: brush 1-2 times weekly. Medium coats: 2-3 times weekly. Long or double coats: daily during shedding season. Bath only when needed (typically every 4-8 weeks) using dog-specific shampoo.</li><li><strong>Step 3 — Maintain dental hygiene:</strong> Brush teeth 2-3 times per week using dog-specific toothpaste (never human toothpaste, which contains xylitol). The BVA estimates 80%+ of dogs over three have dental disease, making routine care essential.</li><li><strong>Step 4 — Keep parasite prevention current:</strong> Follow your vet's recommended schedule for flea, tick, and worm treatments. Treatment intervals vary by product (monthly, quarterly, or annually). Mark treatment dates on a calendar or use a vet reminder app.</li><li><strong>Step 5 — Book annual vet checks:</strong> Even healthy dogs should see a vet annually for a physical examination, booster vaccinations (or titre testing if preferred), and a dental check. Senior dogs (7+ years) benefit from twice-yearly check-ups as recommended by the PDSA.</li></ol>
</div>
<!-- /wp:group -->""",
    "Dog Supplies": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#ecfdf5;border-color:#6ee7b7">
<h4 class="wp-block-heading">Step-by-Step: Choosing the Right Dog Supplies</h4>
<ol><li><strong>Step 1 — Assess your dog's needs:</strong> Consider breed size, age, activity level, and any health conditions. A large-breed senior dog has different supply requirements than an active young terrier.</li><li><strong>Step 2 — Prioritise safety materials:</strong> Choose BPA-free bowls, food-grade stainless steel (304 grade) or ceramic for feeding. Avoid plastic bowls that can harbour bacteria in scratches and may cause chin acne in some dogs.</li><li><strong>Step 3 — Size appropriately:</strong> Bowls should hold enough for one meal without overflowing. Water bowls should be large enough that your dog can drink comfortably without tipping. The RSPCA recommends fresh water available at all times.</li><li><strong>Step 4 — Check cleaning requirements:</strong> Before purchasing, confirm that all components are dishwasher-safe or easy to hand-wash. Supplies that are difficult to clean thoroughly become bacterial hazards over time.</li><li><strong>Step 5 — Replace on a schedule:</strong> Inspect supplies monthly for cracks, chips, rust, or wear. Replace stainless steel bowls when scratched deeply enough to harbour bacteria. Replace plastic items at the first sign of cracking or discolouration.</li></ol>
</div>
<!-- /wp:group -->""",
}

# Generic At a Glance for non-priority posts
GENERIC_AT_A_GLANCE = {
    "Dog Food": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">At a Glance</h4>
<ul><li><strong>UK labelling requirement:</strong> All dog food sold in the UK must declare whether it is "complete" or "complementary" under PFMA/FEDIAF regulations.</li><li><strong>Protein minimum:</strong> FEDIAF recommends a minimum of 18% crude protein for adult maintenance and 25% for growth (on a dry matter basis).</li><li><strong>Feeding guide accuracy:</strong> Manufacturer feeding guides are starting points only — adjust by 10-15% based on your individual dog's body condition and activity level.</li><li><strong>Transition period:</strong> UK vets typically recommend a 7-10 day gradual transition when switching between dog foods to prevent digestive upset.</li></ul>
</div>
<!-- /wp:group -->""",
    "Dog Health": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">At a Glance</h4>
<ul><li><strong>Annual vet check:</strong> The BVA recommends at least one veterinary health check per year for adult dogs, and twice yearly for senior dogs (7+ years).</li><li><strong>Vaccination schedule:</strong> UK puppies receive primary vaccinations at 8 and 10-12 weeks, with annual or triennial boosters depending on the vaccine type.</li><li><strong>Dental disease prevalence:</strong> Over 80% of dogs aged three and above show signs of dental disease according to UK veterinary surveys.</li><li><strong>Parasite prevention:</strong> Year-round flea, tick, and worm prevention is recommended by UK vets, with treatment frequency varying by product (monthly to quarterly).</li></ul>
</div>
<!-- /wp:group -->""",
    "Dog Beds": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">At a Glance</h4>
<ul><li><strong>Sizing rule:</strong> Measure your dog nose-to-tail-base in their natural sleeping position and add 15-20cm to determine minimum bed length.</li><li><strong>Memory foam density:</strong> For orthopaedic support, choose foam rated 50+ kg/m3 density with a minimum thickness of 7cm.</li><li><strong>Washing frequency:</strong> The RSPCA recommends regular bed washing; most covers should be washed at 30-40°C every 1-2 weeks.</li><li><strong>Replacement indicators:</strong> Replace a dog bed when foam does not spring back within 10 seconds, or when odour persists despite thorough washing.</li></ul>
</div>
<!-- /wp:group -->""",
    "Puppy Care": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">At a Glance</h4>
<ul><li><strong>Socialisation window:</strong> The critical socialisation period is approximately 3-14 weeks of age, during which positive exposure to varied experiences is essential.</li><li><strong>Vaccination timing:</strong> UK puppies receive first vaccination at 8 weeks and second at 10-12 weeks. Full immunity is typically reached 1-2 weeks after the final jab.</li><li><strong>Feeding frequency:</strong> Puppies under 4 months need 4 meals daily, reducing to 3 meals at 4-6 months, and 2 meals from 6 months onward.</li><li><strong>Microchipping law:</strong> All dogs in England must be microchipped by 8 weeks of age under the Microchipping of Dogs (England) Regulations 2023.</li></ul>
</div>
<!-- /wp:group -->""",
    "Dog Care": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">At a Glance</h4>
<ul><li><strong>Legal duty of care:</strong> Under the Animal Welfare Act 2006, UK dog owners must meet five welfare needs: environment, diet, behaviour, companionship, and health.</li><li><strong>Exercise minimum:</strong> Most adult dogs need at least 30-60 minutes of exercise twice daily, though requirements vary significantly by breed and age.</li><li><strong>Dental care:</strong> Brush your dog's teeth 2-3 times per week with dog-specific toothpaste. The BVA reports dental disease is one of the most common conditions seen in UK veterinary practice.</li><li><strong>Grooming frequency:</strong> Varies by coat type: short coats need 1-2 weekly brushings; long or double coats may need daily grooming during shedding seasons.</li></ul>
</div>
<!-- /wp:group -->""",
    "Dog Supplies": """<!-- wp:group {"style":{"border":{"width":"1px","radius":"8px"},"spacing":{"padding":{"top":"20px","right":"24px","bottom":"20px","left":"24px"}}},"borderColor":"","backgroundColor":""} -->
<div class="wp-block-group has-border-color has-background" style="border-width:1px;border-radius:8px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px;background-color:#eef2ff;border-color:#c7d2fe">
<h4 class="wp-block-heading">At a Glance</h4>
<ul><li><strong>Bowl material recommendation:</strong> Stainless steel (304 grade) is recommended by most UK vets for food and water bowls due to its durability and hygiene properties.</li><li><strong>Water access:</strong> The RSPCA states dogs must have access to fresh, clean water at all times. Change water at least twice daily.</li><li><strong>Supply safety:</strong> Check all pet supplies for UK product safety compliance. Avoid products with small detachable parts that could be swallowed.</li><li><strong>Replacement cycle:</strong> Inspect bowls, leads, and accessories monthly for damage. Replace any item showing cracks, rust, or significant wear.</li></ul>
</div>
<!-- /wp:group -->""",
}

# Generic comparison tables for non-priority posts
GENERIC_COMPARISON = {
    "Dog Health": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Preventive Care Schedule Overview</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Care Type</th><th>Puppies (0-12 months)</th><th>Adults (1-7 years)</th><th>Seniors (7+ years)</th></tr></thead><tbody><tr><td>Vet Check-ups</td><td>Monthly during vaccination course</td><td>Annually</td><td>Every 6 months (PDSA recommendation)</td></tr><tr><td>Vaccinations</td><td>Primary course at 8 and 10-12 weeks</td><td>Annual or triennial boosters per vet advice</td><td>Boosters continue; titre testing may be discussed</td></tr><tr><td>Parasite Treatment</td><td>Worming from 2 weeks; flea treatment from 8 weeks</td><td>Monthly or quarterly per product type</td><td>Continues; adjust if on concurrent medications</td></tr><tr><td>Dental Care</td><td>Introduce tooth brushing from 12 weeks</td><td>Brush 2-3 times weekly; annual dental check</td><td>Increased monitoring; professional cleaning if needed</td></tr><tr><td>Weight Monitoring</td><td>Fortnightly weighing during growth</td><td>Monthly weighing; BCS assessment at each vet visit</td><td>Monthly weighing; watch for unexplained changes</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
    "Dog Beds": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Dog Bed Fill Materials Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Feature</th><th>Memory Foam</th><th>Polyester Fibre Fill</th><th>Shredded Foam</th></tr></thead><tbody><tr><td>Support Level</td><td>High; moulds to body shape</td><td>Moderate; even support</td><td>Moderate; adjustable loft</td></tr><tr><td>Durability</td><td>3-5 years at 50+ kg/m3 density</td><td>1-2 years before flattening</td><td>2-3 years; may clump over time</td></tr><tr><td>Temperature</td><td>Retains heat; warm in winter</td><td>Breathable; temperature neutral</td><td>Good airflow between pieces</td></tr><tr><td>Washability</td><td>Foam is not machine-washable</td><td>Some fills are machine-washable</td><td>Not machine-washable as a unit</td></tr><tr><td>Best For</td><td>Joint support and orthopaedic needs</td><td>General comfort and budget options</td><td>Dogs that like to nest and adjust their bed shape</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
    "Dog Supplies": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Dog Bowl Materials Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Feature</th><th>Stainless Steel</th><th>Ceramic</th><th>Plastic (BPA-Free)</th></tr></thead><tbody><tr><td>Hygiene</td><td>Non-porous; resists bacteria</td><td>Non-porous when glazed; chip-resistant glazes are safest</td><td>Micro-scratches harbour bacteria over time</td></tr><tr><td>Durability</td><td>Very durable; dent-resistant</td><td>Can chip or crack if dropped</td><td>Lightweight but prone to scratching</td></tr><tr><td>Weight/Stability</td><td>Light to moderate; may need rubber base</td><td>Heavy; less likely to slide</td><td>Very light; easily pushed around</td></tr><tr><td>Dishwasher Safe</td><td>Yes</td><td>Usually yes; check manufacturer label</td><td>Usually yes; may warp at high temperatures</td></tr><tr><td>Best For</td><td>Everyday use for all dogs; vet-recommended standard</td><td>Dogs that push bowls; decorative options</td><td>Travel and temporary use only</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
    "Dog Care": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Grooming Needs by Coat Type</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Coat Type</th><th>Brushing Frequency</th><th>Bathing Frequency</th><th>Primary Tool</th></tr></thead><tbody><tr><td>Short/Smooth</td><td>1-2 times per week</td><td>Every 6-8 weeks</td><td>Bristle brush or rubber grooming mitt</td></tr><tr><td>Double Coat</td><td>3-5 times per week (daily when moulting)</td><td>Every 6-8 weeks</td><td>Undercoat rake plus slicker brush</td></tr><tr><td>Long/Silky</td><td>Daily to prevent matting</td><td>Every 4-6 weeks</td><td>Pin brush and wide-tooth comb</td></tr><tr><td>Wire/Rough</td><td>2-3 times per week</td><td>Every 6-8 weeks</td><td>Stripping knife or slicker brush</td></tr><tr><td>Curly/Non-Shedding</td><td>Daily to prevent matting</td><td>Every 3-4 weeks</td><td>Slicker brush plus steel comb</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
    "Dog Food": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Dog Food Label Terms Compared</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Label Term</th><th>Meaning (UK/PFMA)</th><th>What to Look For</th></tr></thead><tbody><tr><td>Complete</td><td>Provides all required nutrients at correct levels</td><td>Can be fed as sole diet for the stated life stage</td></tr><tr><td>Complementary</td><td>Does not meet full requirements alone</td><td>Must be fed alongside a complete food or other items</td></tr><tr><td>"With [ingredient]"</td><td>Contains at least 4% of the named ingredient</td><td>Check percentage; 4% is a low threshold</td></tr><tr><td>"[Ingredient] flavour"</td><td>May contain less than 4% of the named ingredient</td><td>Flavouring may be artificial; check composition list</td></tr><tr><td>"Rich in [ingredient]"</td><td>Contains at least 14% of the named ingredient</td><td>A more meaningful inclusion than "with"</td></tr></tbody></table></figure>
<!-- /wp:table -->""",
    "Puppy Care": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Puppy Development Milestones</h3>
<!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Age</th><th>Physical Development</th><th>Behavioural Milestone</th><th>Key Action</th></tr></thead><tbody><tr><td>8-10 weeks</td><td>Baby teeth present; rapid growth</td><td>Bonding with new family; exploring</td><td>First vaccination; register with vet</td></tr><tr><td>10-14 weeks</td><td>Coordination improving</td><td>Peak socialisation window closing</td><td>Second vaccination; begin socialisation outings</td></tr><tr><td>14-16 weeks</td><td>Stronger, more active</td><td>Testing boundaries; mouthing phase</td><td>Basic training; redirect biting to appropriate toys</td></tr><tr><td>4-6 months</td><td>Teething begins; adult teeth emerge</td><td>Increased chewing; may regress on training</td><td>Provide appropriate chew toys; reduce meals to 3/day</td></tr><tr><td>6-12 months</td><td>Approaching adult size (breed-dependent)</td><td>Adolescence; may test recall and boundaries</td><td>Continue training consistency; reduce meals to 2/day</td></tr></tbody></table></figure>
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

# Priority order: posts closest to 90 first
PRIORITY_IDS = [3836, 4004, 4089, 3996, 3839, 4110, 4167, 4057, 4160]

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
print(f"Phase 10BU/10BV/10BY Dog Cluster Enrichment")
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
output_csv = os.path.join(OUTPUT_DIR, "citation_moat_trust_dog_clusters.csv")
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
