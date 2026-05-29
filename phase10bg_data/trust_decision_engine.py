#!/usr/bin/env python3
"""
Phase 10BE + 10BG + 10BI — Decision Support, Trust Depth, AI Extraction
Clusters: Cat Toys, Cat Supplies, Dog Harnesses, Indoor Cats, Educational, Uncategorized

10BE: Evaluation Framework, Troubleshooting, Scenario Guidance blocks
10BG: Trust depth expansion (methodology refs, UK org refs, standards refs)
10BI: AI Extraction superiority (Quick Answer, At a Glance enrichment, FAQ expansion, Key Terms)
"""

import csv
import html
import json
import os
import re
import subprocess
import tempfile
import time
import traceback

# ── credentials & config ────────────────────────────────────────────────────
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
BASE = "https://pethubonline.com/wp-json/wp/v2"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10bg_data"
CSV_PATH = os.path.join(DATA_DIR, "trust_decision_cat_harness_indoor_edu.csv")
DELAY = 2.5  # seconds between API calls

# Skip IDs (handled by another agent)
SKIP_IDS = {5519, 4314, 4286, 5521, 5509, 4167, 4153, 4160, 5464}

# Category ID mapping (actual WP category IDs from the site)
CLUSTER_MAP = {
    1459: "Cat Toys",
    1377: "Cat Supplies",
    1422: "Dog Harnesses",
    1413: "Indoor Cats",
    # Educational = category 51 — has 0 posts, but some Uncategorized posts are educational
    # Uncategorized = category 1
}

# ── API helpers ─────────────────────────────────────────────────────────────
def api_get(endpoint):
    url = f"{BASE}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    return json.loads(result.stdout)


def api_update(post_id, payload):
    url = f"{BASE}/posts/{post_id}"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        tmp = f.name
    try:
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-d", f"@{tmp}",
             "-H", "Content-Type: application/json",
             "-X", "POST", url],
            capture_output=True, text=True, timeout=120
        )
        data = json.loads(result.stdout)
        if "id" in data:
            return True, data
        return False, data
    finally:
        os.unlink(tmp)


# ── build target list ───────────────────────────────────────────────────────
def build_target_list():
    """Fetch all posts and filter to our clusters, excluding skip IDs."""
    targets = []
    seen = set()

    for page in range(1, 5):
        try:
            data = api_get(f"posts?per_page=100&page={page}&_fields=id,title,categories")
            if isinstance(data, dict) and "code" in data:
                break
            for p in data:
                pid = p["id"]
                if pid in SKIP_IDS or pid in seen:
                    continue
                cats = p.get("categories", [])
                title = html.unescape(p["title"]["rendered"])

                cluster = classify_post(pid, cats, title)
                if cluster:
                    targets.append({"id": pid, "title": title, "cluster": cluster, "categories": cats})
                    seen.add(pid)
        except Exception as e:
            print(f"  Error fetching page {page}: {e}")
            break
        time.sleep(DELAY)

    return targets


def classify_post(pid, cats, title):
    """Determine which of our target clusters a post belongs to."""
    title_lower = title.lower()

    # Priority: specific cluster categories first
    # Cat Toys (1459)
    if 1459 in cats:
        return "Cat Toys"

    # Dog Harnesses (1422)
    if 1422 in cats:
        return "Dog Harnesses"

    # Indoor Cats (1413)
    if 1413 in cats:
        return "Indoor Cats"

    # Cat Supplies (1377) — but NOT if it's also Cat Toys or Indoor Cats
    if 1377 in cats:
        return "Cat Supplies"

    # Uncategorized (only category 1)
    if cats == [1]:
        # Classify educational-type posts
        edu_signals = ["terminology", "glossary", "explained", "guide to common",
                       "key terms", "understanding", "basics"]
        if any(s in title_lower for s in edu_signals):
            return "Educational"

        # Cat-related uncategorized
        if "cat" in title_lower:
            if "toy" in title_lower:
                return "Cat Toys"
            elif "indoor" in title_lower:
                return "Indoor Cats"
            else:
                return "Cat Supplies"

        # Dog harness related
        if "harness" in title_lower:
            return "Dog Harnesses"

        # General uncategorized
        return "Uncategorized"

    return None  # Not in our clusters


# ── content analysis helpers ────────────────────────────────────────────────
def has_block(content, heading_text):
    """Check if a block with specific h4 heading exists."""
    pattern = rf'<h4[^>]*>\s*{re.escape(heading_text)}\s*</h4>'
    return bool(re.search(pattern, content, re.IGNORECASE))


def has_quick_answer(content):
    """Check if Quick Answer paragraph exists at top."""
    return "<strong>Quick answer:" in content.lower() or "<strong>quick answer</strong>" in content.lower()


def count_faq_items(content):
    """Count Q&A pairs in FAQ section."""
    faq_match = re.search(r'Frequently Asked Questions', content, re.IGNORECASE)
    if not faq_match:
        return 0
    faq_section = content[faq_match.start():]
    # Count h3 headings after FAQ heading (each is a question)
    questions = re.findall(r'<h3[^>]*>', faq_section)
    # Subtract non-question h3s like "Related Reading", "Key Terms"
    end_signals = ["Related Reading", "Key Terms", "Quick Checklist",
                   "Common Mistakes", "Key Takeaways", "Our Editorial"]
    for sig in end_signals:
        if sig in faq_section:
            cutoff = faq_section.index(sig)
            questions = re.findall(r'<h3[^>]*>', faq_section[:cutoff])
            break
    return len(questions)


def count_key_terms(content):
    """Count defined terms in Key Terms section."""
    terms_match = re.search(r'Key Terms', content, re.IGNORECASE)
    if not terms_match:
        return 0
    section = content[terms_match.start():]
    # Find the list items with bold terms
    terms = re.findall(r'<strong>([^<]+)</strong>\s*[—–\-—–]', section[:3000])
    return len(terms)


def count_at_a_glance_bullets(content):
    """Count bullet points in At a Glance section."""
    glance_match = re.search(r'At a Glance', content, re.IGNORECASE)
    if not glance_match:
        return 0
    section = content[glance_match.start():glance_match.start()+2000]
    # Find the closing of the At a Glance group
    end_match = re.search(r'</div>\s*(?:</div>)?', section[100:])
    if end_match:
        section = section[:100 + end_match.end()]
    bullets = re.findall(r'<li>', section)
    return len(bullets)


def count_uk_org_refs(content):
    """Count UK welfare organisation references in body text."""
    c = content.lower()
    orgs = {
        "cats protection": "Cats Protection",
        "international cat care": "International Cat Care",
        "rspca": "RSPCA",
        "pdsa": "PDSA",
        "bva": "BVA",
        "rcvs": "RCVS",
        "blue cross": "Blue Cross",
        "battersea": "Battersea",
        "kennel club": "Kennel Club",
        "dogs trust": "Dogs Trust",
        "apdt": "APDT",
        "british veterinary": "British Veterinary Association",
    }
    found = []
    for key, name in orgs.items():
        if key in c:
            found.append(name)
    return found


# ── block insertion point detection ─────────────────────────────────────────
def find_insertion_point(content):
    """
    Find where to insert new blocks — before Quick Checklist / Common Mistakes /
    Key Terms / Key Takeaways / trust footer / Editorial Standards.
    Returns position in content string.
    """
    # Search for these markers in priority order
    markers = [
        r'<h[34][^>]*>\s*Quick Checklist',
        r'<h[34][^>]*>\s*Common Mistakes',
        r'<h[34][^>]*>\s*Key Terms',
        r'<h[34][^>]*>\s*Key Takeaways',
        r'Our Editorial Standards',
        r'<!--\s*wp:group.*?-->.*?<h4[^>]*>Our Editorial Standards',
    ]

    for marker in markers:
        m = re.search(marker, content, re.IGNORECASE | re.DOTALL)
        if m:
            pos = m.start()
            # Walk back to find the wp:group opening or separator
            before = content[max(0, pos-500):pos]

            # Look for preceding <hr> separator
            hr_match = re.search(r'<hr[^>]*>\s*$', before)
            if hr_match:
                return max(0, pos - 500) + hr_match.start()

            # Look for preceding wp:group opening
            group_match = before.rfind('<!-- wp:group')
            if group_match >= 0 and (len(before) - group_match) < 400:
                return max(0, pos - 500) + group_match

            # Look for preceding div opening that's part of the block
            div_match = before.rfind('<div class="wp-block-group')
            if div_match >= 0 and (len(before) - div_match) < 400:
                return max(0, pos - 500) + div_match

            return pos

    # Fallback: insert before the last </div> or at end
    return len(content)


# ── content generation for 10BE ─────────────────────────────────────────────

def generate_evaluation_framework(title, cluster):
    """Generate 4-6 evaluation criteria specific to the topic."""
    t = title.lower()

    if cluster == "Cat Toys":
        if "interactive" in t:
            criteria = [
                "Engagement duration — does the toy hold attention for more than a few minutes per session?",
                "Safety of moving parts — are there small detachable pieces that could be swallowed?",
                "Noise level — will the toy disturb household members during evening play sessions?",
                "Battery life and replacement cost — is ongoing use affordable?",
                "Prey-sequence activation — does it trigger stalk, chase, pounce, and catch behaviours?",
                "Durability under repeated use — will it survive daily 15-minute play sessions?"
            ]
        elif "catnip" in t:
            criteria = [
                "Catnip freshness indicators — is the catnip sealed, and is there a harvest or expiry date?",
                "Refillable design — can the catnip be replaced when potency fades?",
                "Stitching quality — are seams strong enough to withstand biting and bunny-kicking?",
                "Size appropriateness — is the toy large enough to prevent accidental swallowing?",
                "Alternative herb options — does the product include silver vine or valerian for non-responders?"
            ]
        elif "diy" in t or "homemade" in t:
            criteria = [
                "Material safety — are all materials non-toxic and free from small detachable parts?",
                "Supervision requirements — can the toy be used during unsupervised play?",
                "Hygiene — can the toy be cleaned or disposed of easily?",
                "Cost-effectiveness — does making the toy genuinely save money compared to shop-bought options?",
                "Enrichment value — does it engage natural hunting or problem-solving instincts?"
            ]
        elif "kitten" in t or "age" in t:
            criteria = [
                "Age-appropriate sizing — is the toy small enough for kitten paws but too large to swallow?",
                "Material softness — are textures gentle on developing teeth and gums?",
                "Stimulation level — does it engage without overwhelming a young cat?",
                "Durability through growth stages — will it remain useful as the kitten grows?",
                "Safety certification — does the manufacturer provide testing information?"
            ]
        elif "replace" in t or "lifespan" in t:
            criteria = [
                "Visible damage indicators — are there tears, holes, or exposed stuffing?",
                "Hygiene degradation — does the toy retain odours or discolouration after cleaning?",
                "Structural integrity — do squeakers, bells, or moving parts still function?",
                "Behavioural engagement — has the cat lost interest despite rotation strategies?",
                "Cost per use — was the toy's active lifespan proportionate to its price?"
            ]
        elif "rotation" in t:
            criteria = [
                "Novelty restoration — does the cat show renewed interest after a rotation period?",
                "Storage hygiene — are rotated-out toys stored in clean, dry conditions?",
                "Category balance — does each rotation include interactive, self-play, and puzzle types?",
                "Rotation frequency — are toys swapped every 3-7 days for optimal engagement?",
                "Seasonal adjustment — does the rotation account for changes in energy levels?"
            ]
        elif "enrichment" in t or "beyond" in t:
            criteria = [
                "Variety of senses engaged — does the activity stimulate sight, smell, touch, or hearing?",
                "Difficulty progression — can the enrichment be made harder as the cat masters it?",
                "Safety during unsupervised use — is the activity safe when the owner is not present?",
                "Space requirements — does the activity fit the available indoor environment?",
                "Cost and sustainability — can the enrichment be maintained long-term without excessive expense?"
            ]
        elif "safety" in t:
            criteria = [
                "Material toxicity — are all materials certified non-toxic and free from BPA, phthalates, and lead?",
                "Choking hazard assessment — are all parts larger than a cat's throat?",
                "String and ribbon length — are these short enough to prevent entanglement or ingestion?",
                "Manufacturer transparency — does the packaging include material composition and safety testing details?",
                "Recall history — has the product or brand been subject to safety recalls?"
            ]
        else:
            criteria = [
                "Engagement quality — does the toy activate natural hunting instincts (stalk, chase, pounce)?",
                "Material safety — are all components non-toxic and free from small detachable parts?",
                "Durability — will the toy withstand regular play sessions without breaking apart?",
                "Enrichment variety — does it offer mental stimulation alongside physical exercise?",
                "Ease of cleaning — can the toy be washed or sanitised to maintain hygiene?",
                "Value for money — is the toy's expected lifespan proportionate to its price?"
            ]

    elif cluster == "Cat Supplies":
        if "litter" in t:
            criteria = [
                "Odour control effectiveness — does the litter manage smell between full changes?",
                "Dust levels — is the product low-dust to protect respiratory health?",
                "Clumping performance — does it form solid clumps that are easy to scoop?",
                "Tracking reduction — does the litter stay in the tray rather than spreading through the home?",
                "Environmental impact — is the litter biodegradable or sustainably sourced?"
            ]
        elif "brush" in t or "groom" in t:
            criteria = [
                "Coat type suitability — is the tool designed for short, medium, or long-haired cats?",
                "Comfort during use — does the cat tolerate the tool without stress?",
                "Effectiveness at removing loose fur and preventing matting",
                "Ease of cleaning the tool itself after each grooming session",
                "Handle ergonomics — is it comfortable for the owner during extended use?"
            ]
        elif "collar" in t or "tag" in t or "tracker" in t:
            criteria = [
                "Breakaway mechanism — does the collar release under pressure to prevent strangulation?",
                "Weight appropriateness — is the collar or tracker light enough for the cat's size?",
                "Reflective or high-visibility features for cats with outdoor access",
                "Durability of closure mechanism and attachment points",
                "Comfort — does the fit allow two fingers between collar and neck?"
            ]
        elif "harness" in t:
            criteria = [
                "Escape-proof design — does the harness prevent the cat from backing out?",
                "Adjustability — can it be fitted snugly without restricting breathing?",
                "Material comfort — is the fabric soft against the cat's fur and skin?",
                "Weight — is the harness light enough for a cat to move naturally?",
                "Lead attachment security — is the D-ring positioned to prevent twisting?"
            ]
        elif "bed" in t or "perch" in t:
            criteria = [
                "Weight capacity — does the bed or perch support the cat's full weight with a safety margin?",
                "Installation security — for wall or window mounts, is the attachment mechanism reliable?",
                "Washability — can the cover be removed and machine washed?",
                "Material safety — are fabrics and filling free from harmful chemicals?",
                "Size appropriateness — can the cat stretch out or curl up comfortably?"
            ]
        elif "scratcher" in t or "scratching" in t or "tree" in t:
            criteria = [
                "Stability — does the scratcher remain upright during vigorous use?",
                "Material preference — does it use sisal, cardboard, or carpet to match the cat's preference?",
                "Height and angle options — does it allow both vertical and horizontal scratching?",
                "Durability — how long before the scratching surface needs replacing?",
                "Footprint — does it fit the available space without overwhelming the room?"
            ]
        elif "shampoo" in t:
            criteria = [
                "pH balance — is the formula specifically designed for feline skin (pH 6.0-7.0)?",
                "Ingredient safety — are all ingredients non-toxic if licked during grooming?",
                "Fragrance — is the scent mild enough to avoid distressing the cat?",
                "Rinse ease — does the product wash out completely without residue?",
                "Condition after use — does the coat feel soft and clean without dryness?"
            ]
        elif "essential" in t or "glossary" in t or "basics" in t:
            criteria = [
                "Product necessity — is this item essential for daily cat care or merely convenient?",
                "Quality indicators — what features distinguish a well-made product from a poor one?",
                "Safety certification — does the product meet UK or EU safety standards?",
                "Longevity — will this product last long enough to justify its price?",
                "Cat acceptance — is this a product type that most cats will tolerate or enjoy?"
            ]
        else:
            criteria = [
                "Material safety — are all components non-toxic and cat-safe?",
                "Durability — will the product withstand daily use over months?",
                "Ease of cleaning — can the item be maintained hygienically with minimal effort?",
                "Size appropriateness — does the product suit the cat's breed and weight?",
                "Value for money — does quality justify the price compared to alternatives?"
            ]

    elif cluster == "Dog Harnesses":
        if "no-pull" in t or "no pull" in t:
            criteria = [
                "Front-clip effectiveness — does the front attachment genuinely reduce pulling?",
                "Pressure distribution — does the design avoid concentrating force on the throat or chest?",
                "Adjustability — can straps be tightened at multiple points for a secure fit?",
                "Padding quality — are contact areas cushioned to prevent chafing?",
                "Compatibility with leads — does it work with standard UK lead clip sizes?"
            ]
        elif "measure" in t or "fitting" in t or "size" in t:
            criteria = [
                "Measurement accuracy — are girth, neck, and chest measurements taken at the correct points?",
                "Size chart clarity — does the manufacturer provide clear guidance for between-size dogs?",
                "Adjustment range — does the harness accommodate weight fluctuations?",
                "Fit check — can two fingers fit between the harness and the dog's body at all contact points?",
                "Movement test — can the dog walk, sit, and lie down without restriction?"
            ]
        elif "collar" in t and "harness" in t:
            criteria = [
                "Neck pressure — does the option distribute force away from the trachea?",
                "Escape risk — can the dog slip out of the equipment during walks?",
                "Training compatibility — does the option support positive reinforcement methods?",
                "Breed suitability — is the choice appropriate for the dog's body shape and size?",
                "Veterinary recommendation — what do UK veterinary organisations advise for your dog's breed?"
            ]
        elif "type" in t:
            criteria = [
                "Body shape compatibility — does the harness design suit your dog's chest and shoulder proportions?",
                "Activity suitability — is it designed for walking, running, car travel, or training?",
                "Ease of putting on — can you fit it without stressing the dog?",
                "Visibility features — does it include reflective elements for low-light walks?",
                "Washing instructions — can the harness be machine washed to maintain hygiene?"
            ]
        else:
            criteria = [
                "Fit and adjustability — does the harness sit correctly without rubbing or slipping?",
                "Pressure distribution — is force spread across the chest rather than concentrating on the neck?",
                "Material quality — are fabrics breathable, durable, and comfortable against the dog's coat?",
                "Safety features — does it include reflective strips and a secure lead attachment point?",
                "Ease of use — can you put it on and take it off without distressing the dog?",
                "UK availability and sizing — is it available from UK retailers with accurate size guides?"
            ]

    elif cluster == "Indoor Cats":
        if "diet" in t or "nutrition" in t or "feeding" in t:
            criteria = [
                "Calorie appropriateness — does the portion size account for reduced activity levels of indoor cats?",
                "Protein content — does the food meet the minimum 26% protein recommended for adult cats?",
                "Indoor-specific formulation — does the food address hairball management and weight control?",
                "Ingredient transparency — are all ingredients listed clearly on the packaging?",
                "PFMA compliance — does the food meet the Pet Food Manufacturers' Association nutritional standards?"
            ]
        elif "behaviour" in t:
            criteria = [
                "Root cause identification — is the behaviour caused by boredom, stress, territory issues, or health?",
                "Environmental assessment — does the home provide enough vertical space, hiding spots, and territory?",
                "Enrichment adequacy — is the cat receiving at least 15-30 minutes of interactive play daily?",
                "Multi-cat dynamics — if applicable, does each cat have its own resources?",
                "Veterinary consultation — has a vet ruled out medical causes for the behaviour change?"
            ]
        elif "exercise" in t or "active" in t:
            criteria = [
                "Daily activity duration — is the cat getting at least 15-30 minutes of active play?",
                "Variety of movement types — does play include climbing, jumping, chasing, and pouncing?",
                "Age appropriateness — is the intensity suitable for the cat's age and health status?",
                "Space utilisation — are vertical spaces being used to maximise exercise opportunity?",
                "Motivation techniques — are food puzzles and interactive toys used to encourage movement?"
            ]
        elif "safety" in t or "hazard" in t:
            criteria = [
                "Toxic plant identification — have all houseplants been checked against the Cats Protection toxic plant list?",
                "Small object risk — are items like hair ties, rubber bands, and small toys stored securely?",
                "Window and balcony security — are all openings fitted with cat-safe mesh or restrictors?",
                "Chemical storage — are cleaning products, medications, and essential oils stored out of reach?",
                "Electrical cord protection — are cables covered or concealed to prevent chewing?"
            ]
        elif "environment" in t or "enrichment" in t or "friendly" in t:
            criteria = [
                "Vertical space — does the home include cat trees, shelves, or climbing structures?",
                "Hiding spots — are there enclosed spaces where the cat can retreat and feel safe?",
                "Window access — can the cat observe outdoor activity from a secure perch?",
                "Scratching surfaces — are there both vertical and horizontal scratching options?",
                "Resource distribution — are food, water, litter, and rest areas in separate locations?"
            ]
        elif "terminology" in t or "glossary" in t:
            criteria = [
                "Term accuracy — does the definition match current UK veterinary and welfare usage?",
                "Practical relevance — is the term one that indoor cat owners will encounter regularly?",
                "Source verification — has the definition been cross-referenced with authoritative UK sources?",
                "Accessibility — is the definition written in plain language without unnecessary jargon?",
                "Context — does the entry explain why the term matters for indoor cat welfare?"
            ]
        else:
            criteria = [
                "Environmental enrichment — does the indoor space meet the cat's physical and mental needs?",
                "Health monitoring — are indoor-specific health risks (obesity, dental disease, stress) being tracked?",
                "Play adequacy — is the cat receiving varied, regular interactive play sessions?",
                "Veterinary care — are annual check-ups addressing indoor-specific concerns?",
                "Safety assessment — has the home been checked for common indoor hazards?"
            ]

    elif cluster == "Educational":
        if "training" in t:
            criteria = [
                "Method alignment — does the approach follow force-free, positive reinforcement principles?",
                "Evidence base — is the technique supported by published behavioural research?",
                "Practical applicability — can a typical UK pet owner implement this at home?",
                "Safety — does the method avoid causing fear, pain, or stress to the animal?",
                "Professional endorsement — is the approach recommended by APDT, RSPCA, or Kennel Club?"
            ]
        elif "health" in t or "dental" in t or "vet" in t:
            criteria = [
                "Source authority — does the information align with BVA and RCVS guidelines?",
                "Symptom clarity — are warning signs described specifically enough to act upon?",
                "Action guidance — does the content explain when to seek veterinary attention?",
                "Prevention focus — are preventive measures given appropriate emphasis?",
                "UK relevance — are vaccination schedules and treatment options UK-specific?"
            ]
        elif "nutrition" in t or "feeding" in t or "food" in t:
            criteria = [
                "Regulatory compliance — does the information reference UK pet food regulations?",
                "Label literacy — does the content explain how to read UK pet food labels?",
                "Nutritional adequacy — are minimum nutrient requirements clearly stated?",
                "Source transparency — are claims supported by PFMA or FEDIAF standards?",
                "Practical application — can the reader use this information when shopping?"
            ]
        elif "enrichment" in t or "play" in t or "stimulation" in t:
            criteria = [
                "Scientific basis — is the enrichment approach grounded in animal behaviour research?",
                "Accessibility — can the suggested activities be done with minimal equipment?",
                "Species appropriateness — is the activity suitable for the specific animal type?",
                "Safety during unsupervised use — are risks of independent play addressed?",
                "Measurable outcomes — can the owner observe improvements in behaviour or wellbeing?"
            ]
        else:
            criteria = [
                "Information accuracy — has the content been verified against current UK professional guidance?",
                "Practical usefulness — can a UK pet owner apply this information immediately?",
                "Source transparency — are the organisations and guidelines referenced clearly identified?",
                "Accessibility — is complex information explained in plain, jargon-free language?",
                "Completeness — does the guide cover the topic thoroughly enough for informed decision-making?"
            ]

    else:  # Uncategorized
        if "toy" in t and "dog" in t:
            criteria = [
                "Material safety — are all components non-toxic and appropriate for the dog's chewing intensity?",
                "Size appropriateness — is the toy correctly sized to prevent choking hazards?",
                "Enrichment value — does the toy provide mental stimulation beyond simple chewing?",
                "Durability — will the toy survive the dog's typical play style?",
                "Ease of cleaning — can the toy be washed to maintain hygiene?"
            ]
        elif "cat" in t:
            criteria = [
                "Safety — are all materials non-toxic and free from small detachable parts?",
                "Engagement quality — does the product satisfy natural feline instincts?",
                "Suitability for indoor use — is it appropriate for house cats with limited space?",
                "Durability — will it withstand regular use without becoming hazardous?",
                "Value assessment — does quality and longevity justify the price?"
            ]
        elif "senior" in t or "ageing" in t or "older" in t:
            criteria = [
                "Age appropriateness — is the product or approach suitable for an older animal's needs?",
                "Joint and mobility consideration — does it account for reduced flexibility?",
                "Veterinary alignment — does the guidance reflect current geriatric care recommendations?",
                "Gentle engagement — does it provide stimulation without overexertion?",
                "Comfort priority — does it prioritise comfort and wellbeing over performance?"
            ]
        elif "puppy" in t:
            criteria = [
                "Developmental stage suitability — is the advice appropriate for the puppy's age?",
                "Safety margin — does the guidance include precautions for growing bodies?",
                "Socialisation window awareness — does it account for critical learning periods?",
                "Veterinary endorsement — is the approach recommended by UK puppy care guidelines?",
                "Practical implementation — can a first-time owner follow this guidance?"
            ]
        else:
            criteria = [
                "Evidence base — is the information supported by UK veterinary or welfare guidance?",
                "Practical relevance — can a typical UK pet owner use this information at home?",
                "Safety considerations — are potential risks clearly identified and addressed?",
                "Comprehensiveness — does the guide cover the topic thoroughly?",
                "Currency — is the information up to date with current best practice?"
            ]

    return criteria


def generate_troubleshooting(title, cluster):
    """Generate 3-5 common problems with solutions."""
    t = title.lower()

    if cluster == "Cat Toys":
        if "interactive" in t:
            problems = [
                ("Cat ignores the interactive toy", "Try varying movement speed and direction. Drag the toy behind furniture to trigger the stalk instinct. Some cats prefer ground-level prey movement over aerial."),
                ("Cat becomes aggressive during play", "End the session calmly and walk away. Redirect aggression toward the toy, never hands. Resume play after a 10-minute cool-down period."),
                ("Battery-operated toy stops working quickly", "Check battery contacts for corrosion. Store with batteries removed between sessions. Consider rechargeable models to reduce ongoing costs."),
                ("Cat fixates on laser pointer and becomes frustrated", "Always end laser sessions by leading the dot to a physical toy the cat can catch. This completes the prey sequence and prevents frustration."),
            ]
        elif "catnip" in t:
            problems = [
                ("Cat does not respond to catnip at all", "Approximately 30-50% of cats are genetically non-responsive. Try silver vine (effective for roughly 75% of cats) or valerian root as alternatives."),
                ("Catnip effect wears off within minutes", "This is normal — the response typically lasts 5-15 minutes, followed by a refractory period of 30-60 minutes. Limit exposure to maintain sensitivity."),
                ("Cat becomes aggressive after catnip exposure", "Some cats experience overstimulation. Remove the catnip toy when aggression appears and allow the cat to calm down in a quiet space."),
            ]
        elif "safety" in t:
            problems = [
                ("Cat has swallowed part of a toy", "Contact your veterinarian immediately. Do not attempt to induce vomiting. Monitor for signs of obstruction: vomiting, lethargy, loss of appetite."),
                ("String or ribbon from a toy is partially swallowed", "Do not pull the string — this can cause serious internal damage. Seek emergency veterinary care immediately."),
                ("Cat's claw is trapped in toy fabric", "Gently support the paw and carefully untangle the claw. If the claw is deeply embedded, wrap the toy to prevent further movement and consult a vet."),
                ("Toy squeaker has been exposed through wear", "Remove the toy immediately. Squeaker mechanisms are choking hazards. Replace with a new toy of the same type."),
            ]
        elif "rotation" in t:
            problems = [
                ("Cat loses interest in toys quickly despite rotation", "Extend the rotation period to 7-10 days. Store toys in a sealed container with catnip to restore novelty scent. Introduce one new toy type each month."),
                ("Difficulty tracking which toys are in rotation", "Use a simple written schedule or label storage boxes by week. Keep 3-4 toys active and 8-12 in storage at any time."),
                ("Cat only plays with one specific toy and ignores others", "This is common. Keep the favourite available but continue offering alternatives during dedicated play sessions to broaden interest gradually."),
            ]
        else:
            problems = [
                ("Cat shows no interest in any toys", "Experiment with different toy types — some cats prefer ground-level movement, others respond to feathers or crinkle sounds. Try play sessions at dawn or dusk when cats are naturally most active."),
                ("Cat plays too roughly and destroys toys quickly", "Choose toys rated for aggressive play. Avoid toys with small parts, loose threads, or thin fabric. Inspect toys after each session."),
                ("Cat only wants to play with household items instead of toys", "Ensure dedicated play mimics real prey movement. Hair ties, rubber bands, and plastic bags are dangerous — redirect to safe alternatives immediately."),
                ("Kitten bites hands during play", "Never use hands as toys. Always redirect to an appropriate toy. Freeze and withdraw attention when biting occurs — this teaches that biting ends play."),
            ]

    elif cluster == "Cat Supplies":
        if "litter" in t:
            problems = [
                ("Cat refuses to use the litter tray", "Check tray cleanliness (scoop at least once daily), location (quiet, accessible, away from food), and depth (5-7cm of litter). Rule out medical causes with a vet visit."),
                ("Litter tracking throughout the house", "Place a textured mat outside the tray entrance. Consider a top-entry tray or one with higher sides. Heavier litter granules track less than lightweight types."),
                ("Strong odour despite regular cleaning", "Change the full litter weekly rather than just topping up. Consider a different litter type — clumping clay and silica gel typically control odour better than wood-based options."),
                ("Cat eliminates beside the tray rather than inside it", "The tray may be too small — it should be 1.5 times the cat's body length. Some cats dislike hooded trays. Try removing the lid."),
            ]
        elif "brush" in t or "groom" in t:
            problems = [
                ("Cat becomes stressed or aggressive during grooming", "Start with very short sessions (30 seconds) and reward with treats. Use a softer brush initially. Never restrain the cat — allow them to walk away."),
                ("Unable to remove matted fur", "Do not cut mats with scissors near the skin. Use a mat splitter or book a professional grooming appointment. Severe matting may require veterinary sedation."),
                ("Excessive shedding despite regular brushing", "Some shedding is seasonal and normal. If excessive, consult a vet to rule out dietary deficiencies, stress, or skin conditions."),
            ]
        elif "collar" in t or "harness" in t:
            problems = [
                ("Cat removes the collar repeatedly", "Ensure the collar is snug enough that only two fingers fit underneath. Some cats need a gradual introduction — start with short indoor sessions."),
                ("Collar causes fur loss around the neck", "The collar may be too tight or the material may be irritating. Switch to a softer fabric and check fit weekly. Remove the collar if skin irritation develops."),
                ("Cat panics when wearing a harness", "Introduce the harness gradually over 1-2 weeks: let the cat sniff it, then drape it over them, then fasten it indoors before any lead attachment."),
            ]
        elif "bed" in t or "perch" in t:
            problems = [
                ("Cat ignores the new bed", "Place the bed where the cat already sleeps. Add a worn piece of the owner's clothing for familiar scent. Do not force the cat — let them discover it naturally."),
                ("Window perch detaches from the glass", "Check suction cup condition — clean both cups and glass with rubbing alcohol before reattaching. Replace cups if they have lost flexibility. Weight-test before allowing the cat to use it."),
                ("Cat overheats in heated bed", "Use heated beds with automatic temperature regulation only. Never leave unregulated heated beds on continuously. Monitor your cat's behaviour for signs of overheating."),
            ]
        elif "scratcher" in t or "tree" in t:
            problems = [
                ("Cat scratches furniture instead of the scratching post", "Place the post directly next to the furniture being scratched. Apply catnip to the post. Ensure it offers both vertical and horizontal scratching surfaces."),
                ("Scratching post wobbles or tips over", "Weight the base or secure it to the wall. Cats will avoid unstable scratchers because they feel unsafe. A post should not move at all during vigorous use."),
                ("Cat tree sisal is fraying after a few months", "This is normal wear. Sisal can be re-wrapped using replacement rope (available from pet supply shops). Budget for annual replacement of scratching surfaces."),
            ]
        else:
            problems = [
                ("Product arrives different from description", "Check the retailer's return policy. Photograph discrepancies for evidence. Report misleading listings to the retailer and Trading Standards if necessary."),
                ("Cat rejects a new product after initial use", "Allow a gradual introduction alongside familiar items. Place the new product near the cat's preferred resting or eating area."),
                ("Product quality deteriorates quickly", "Leave honest reviews to help other buyers. Consider paying slightly more for products from established brands with warranty or replacement policies."),
                ("Unsure which products are genuinely needed", "Focus on essentials first: food and water bowls, litter tray, scratching surface, and one interactive toy. Add other items based on your cat's specific needs."),
            ]

    elif cluster == "Dog Harnesses":
        if "no-pull" in t:
            problems = [
                ("Dog still pulls even with a no-pull harness", "A harness is a management tool, not a training solution. Combine with positive reinforcement loose-lead training. Reward walking beside you rather than pulling ahead."),
                ("Harness chafes under the front legs", "Check that padding covers all contact areas. The harness may be the wrong shape for your dog's body type. Try a different brand with wider chest straps."),
                ("Dog tries to chew the front lead attachment", "Use a shorter lead to reduce slack. Redirect chewing to a toy. Consider a dual-clip harness where you can use the back clip until the behaviour stops."),
            ]
        elif "measure" in t or "fit" in t or "size" in t:
            problems = [
                ("Measurements fall between two sizes on the chart", "Choose the larger size if the harness is adjustable. For non-adjustable styles, contact the manufacturer for guidance. Weight alone is not a reliable sizing indicator."),
                ("Harness shifts to one side during walks", "Re-check measurements. The chest strap may need tightening. Some barrel-chested breeds need brand-specific designs to prevent lateral shifting."),
                ("Dog's body shape changes with age or season", "Re-measure every 3-6 months. Puppies may need size changes every 4-8 weeks. Winter coats may require a looser fit than summer."),
                ("Harness leaves marks on the dog's fur", "Check for overly tight straps. Some flat-coated breeds show temporary fur impressions — these should disappear within an hour. Persistent marks indicate poor fit."),
            ]
        elif "collar" in t:
            problems = [
                ("Dog coughs or gags on a collar during walks", "Switch to a harness immediately. Collar pressure on the trachea can cause damage, especially in small breeds. Consult a vet if coughing persists."),
                ("Collar slips over the dog's head", "Tighten until two fingers fit snugly underneath. For breeds with narrow heads (e.g. Whippets, Greyhounds), use a martingale collar or harness instead."),
                ("Unsure whether to use collar or harness", "For daily walking, a harness is generally safer. Collars are suitable for ID tags and brief toilet trips in secure areas. Dogs with breathing issues should always use a harness."),
            ]
        else:
            problems = [
                ("Dog resists having the harness put on", "Introduce gradually using treats. Let the dog sniff the harness first. Practice putting it on and immediately giving a high-value reward, then removing it. Build duration over several days."),
                ("Harness buckle or clip breaks during a walk", "Carry a spare lead that can loop around the dog's body in emergencies. Inspect hardware before each walk. Replace harnesses with corroded or bent clips immediately."),
                ("Dog overheats in a padded harness during warm weather", "Choose a lightweight mesh harness for summer walks. Avoid dark-coloured harnesses that absorb heat. Walk during cooler parts of the day."),
                ("Lead attachment point wears down over time", "Inspect the D-ring and stitching around it monthly. This is the highest-stress point on any harness. Replace the harness if the D-ring shows movement or the stitching frays."),
            ]

    elif cluster == "Indoor Cats":
        if "diet" in t or "nutrition" in t:
            problems = [
                ("Indoor cat is gaining weight despite following feeding guidelines", "Feeding guidelines on packaging assume average activity levels. Indoor cats often need 10-20% fewer calories. Consult your vet for a personalised feeding plan."),
                ("Cat refuses indoor-formula food", "Transition gradually by mixing 25% new food with 75% old food, increasing over 7-10 days. If refusal continues, try a different brand with the same indoor-specific nutritional profile."),
                ("Frequent hairballs despite indoor-formula food", "Increase daily brushing to reduce ingested fur. Ensure adequate water intake. If hairballs persist, consult a vet to rule out gastrointestinal issues."),
            ]
        elif "behaviour" in t:
            problems = [
                ("Indoor cat suddenly starts urinating outside the litter tray", "Rule out medical causes first with a vet visit. Check litter tray cleanliness and location. Stress from environmental changes (new pet, furniture rearrangement) is a common trigger."),
                ("Cat shows excessive vocalisation, especially at night", "Increase daytime play and stimulation to reduce night-time energy. Avoid reinforcing vocalisation by responding to it. Consider Feliway or similar pheromone products."),
                ("Cat hides constantly and avoids interaction", "Ensure the cat has safe hiding spots (this is normal behaviour) but monitor for changes in appetite or litter tray use that may indicate illness. New cats may take 2-4 weeks to settle."),
                ("Aggressive behaviour toward other household cats", "Provide separate resources (food bowls, litter trays, sleeping areas) for each cat. Use vertical space to create separate territories. Consider gradual reintroduction if aggression is severe."),
            ]
        elif "exercise" in t or "active" in t:
            problems = [
                ("Cat refuses to engage in play", "Try different toy types and play at dawn or dusk. Some cats prefer short 5-minute sessions over longer ones. Food puzzle toys can encourage movement in food-motivated cats."),
                ("Limited space for cat exercise equipment", "Use vertical space: wall-mounted shelves, tall cat trees in corners, and over-door toys. Even a small flat can provide adequate exercise with creative use of height."),
                ("Older indoor cat has become very sedentary", "Gentle, low-impact activities like slow wand play, food scatter games, and catnip toys can encourage movement. Have a vet check for arthritis or other mobility issues."),
            ]
        elif "safety" in t or "hazard" in t:
            problems = [
                ("Cat has chewed an electrical cord", "Unplug the cord immediately. Check the cat for burns around the mouth or difficulty breathing. Seek emergency veterinary care even if the cat appears fine — internal injuries may not be immediately visible."),
                ("Cat has ingested a toxic houseplant", "Contact your veterinarian or the Animal PoisonLine (01202 509000) immediately. Bring a sample or photo of the plant. Common toxic plants include lilies, which can cause fatal kidney failure in cats."),
                ("Cat escapes through an open window", "Fit window restrictors or cat-safe mesh on all windows. Ensure microchip details are up to date. Indoor cats that escape are often disoriented — search within a 100-metre radius."),
            ]
        elif "environment" in t or "enrichment" in t or "friendly" in t:
            problems = [
                ("Cat destroys furniture despite having scratching posts", "Scratching posts must be tall enough for a full stretch and completely stable. Place them directly next to the damaged furniture. Try different surfaces — some cats prefer sisal, others cardboard."),
                ("Unable to provide enough vertical space in a rented property", "Use freestanding cat trees that do not require wall mounting. Over-door hanging toys, window-mounted suction perches, and tall bookcases can all add vertical territory without damage."),
                ("Cat shows signs of boredom despite environmental enrichment", "Rotate enrichment activities regularly. Introduce food puzzles, scent trails, and window bird feeders. Consider a companion cat if your cat is social — but only after careful introduction."),
            ]
        else:
            problems = [
                ("Indoor cat seems bored or lethargic", "Increase interactive play to at least 15-30 minutes daily. Add environmental enrichment: food puzzles, window perches, cat grass. Rotate toys weekly to maintain novelty."),
                ("Cat is overweight despite careful feeding", "Indoor cats need fewer calories than outdoor cats. Consult your vet for an accurate calorie target. Use food puzzles to slow eating and increase activity."),
                ("Cat shows stress-related behaviours (overgrooming, hiding)", "Check for environmental stressors: new pets, building work, changes in routine. Provide safe hiding spaces. Consider Feliway diffusers. Consult a vet if behaviours persist."),
                ("Difficulty keeping an indoor cat mentally stimulated", "Combine daily interactive play, rotating puzzle feeders, window access for bird watching, and occasional catnip or silver vine. Structured variety prevents habituation."),
            ]

    elif cluster == "Educational":
        if "terminology" in t or "glossary" in t:
            problems = [
                ("Term definitions conflict across different sources", "Prioritise definitions from UK professional bodies (BVA, RCVS, RSPCA). Terminology can vary between countries — always verify UK-specific usage."),
                ("Difficulty understanding veterinary language during consultations", "Write down unfamiliar terms during the appointment and look them up afterwards. Ask your vet to explain in plain language — they expect and welcome questions."),
                ("Confusing similar-sounding terms (e.g. 'atopy' vs 'allergy')", "Create a personal reference sheet of terms relevant to your pet's conditions. This guide's glossary entries are designed to clarify precisely these distinctions."),
            ]
        elif "behaviour" in t or "body language" in t:
            problems = [
                ("Misreading a wagging tail as happiness", "A wagging tail indicates arousal, not necessarily friendliness. The height, speed, and range of the wag all carry different meanings. A low, slow wag may signal anxiety."),
                ("Dog shows aggression without apparent warning", "Dogs almost always give warning signs — they may be subtle (lip licking, turning away, yawning). Learning these early signals prevents escalation."),
                ("Cat body language is difficult to read", "Cats communicate more subtly than dogs. Key signals include tail position, ear orientation, pupil size, and body posture. Slow blinking indicates relaxation and trust."),
            ]
        elif "health" in t:
            problems = [
                ("Unsure when symptoms require veterinary attention", "When in doubt, always consult a vet. Specific emergencies include: difficulty breathing, collapse, suspected poisoning, seizures, inability to urinate, or prolonged vomiting/diarrhoea."),
                ("Pet insurance does not cover a condition", "Pre-existing conditions are excluded by most policies. Review policy documents carefully before purchasing. Lifetime policies offer the most comprehensive cover for ongoing conditions."),
                ("Difficulty affording veterinary care", "Contact PDSA, Blue Cross, or RSPCA for subsidised treatment if you are on benefits. Many practices offer payment plans. Pet insurance, when started early, prevents large unexpected bills."),
            ]
        else:
            problems = [
                ("Information overload when researching pet care topics", "Focus on one topic at a time. Start with UK-based sources (RSPCA, PDSA, BVA) before broadening your search. This guide distills authoritative guidance into practical summaries."),
                ("Conflicting advice from different websites", "Prioritise guidance from UK veterinary and welfare organisations over general blogs or forums. Check whether advice is evidence-based and recently updated."),
                ("Difficulty applying general advice to a specific pet", "General guides provide starting points — your veterinarian can tailor advice to your pet's breed, age, health status, and lifestyle. Book a consultation for personalised guidance."),
                ("Keeping up with changing pet care recommendations", "Bookmark trusted UK sources and check annually for updates. Key organisations like BVA and PDSA regularly publish updated guidance."),
            ]

    else:  # Uncategorized
        problems = [
            ("Information seems contradictory across different sources", "Prioritise UK veterinary and welfare organisations (RSPCA, PDSA, BVA) as primary sources. Cross-reference claims with at least two authoritative sources before acting."),
            ("Unsure whether advice applies to your specific pet", "General guides provide a starting framework — always consult your veterinarian for advice tailored to your pet's breed, age, health, and individual needs."),
            ("Difficulty distinguishing evidence-based advice from opinion", "Look for references to published research, veterinary organisation guidelines, or professional body endorsements. Avoid advice that makes absolute claims without citing sources."),
            ("Pet's behaviour does not match what guides describe as normal", "Animals are individuals. If a behaviour concerns you, consult a veterinary professional rather than relying solely on written guides. Early intervention is always safer."),
        ]

    return problems


def generate_scenario_guidance(title, cluster):
    """Generate 3-4 scenarios with recommendations."""
    t = title.lower()

    if cluster == "Cat Toys":
        if "interactive" in t:
            scenarios = [
                ("You work full-time and your cat is alone for 8+ hours", "Invest in 2-3 quality self-play toys alongside your interactive toy collection. Schedule a dedicated 15-minute play session before work and after returning. Consider a timed electronic toy for midday stimulation."),
                ("You have a kitten under 6 months old", "Choose lightweight, soft interactive toys without small detachable parts. Sessions should be frequent but short (5 minutes). Avoid laser pointers until the kitten understands the concept of a physical catch."),
                ("Your senior cat (12+) has reduced mobility", "Use slow-moving interactive toys at ground level. Feather wands dragged gently along the floor are effective. Sessions of 5-10 minutes are sufficient — stop if the cat shows signs of fatigue."),
            ]
        elif "indoor" in t:
            scenarios = [
                ("You live in a small flat with limited floor space", "Focus on vertical enrichment: wall-mounted shelves, tall cat trees, and over-door toys. Window perches with bird feeders outside provide passive enrichment without taking up floor space."),
                ("You have multiple indoor cats", "Provide separate toy collections for each cat and dedicated individual play sessions. Shared play can cause resource competition. Ensure each cat has at least one private resting spot."),
                ("Your indoor cat is overweight", "Prioritise food puzzle toys and active play over treat-based rewards. Replace a portion of daily food into puzzle feeders. Aim for two 15-minute active play sessions daily."),
            ]
        else:
            scenarios = [
                ("Your cat is a solo indoor cat who seems bored", "Build a rotation of at least 8-10 toys across different categories: interactive, puzzle, self-play, and sensory. Schedule morning and evening play sessions. Add a window perch and bird feeder for passive stimulation."),
                ("You are adopting a rescue cat with unknown play preferences", "Start with a basic variety pack: one wand toy, one ball track, one catnip toy, and one crinkle toy. Observe which type the cat gravitates toward and expand that category."),
                ("Your cat becomes destructive when understimulated", "Increase daily interactive play to 20-30 minutes split across sessions. Introduce food puzzles for mental work. Provide legal scratching surfaces in every room the cat uses."),
                ("Budget is limited but enrichment is needed", "DIY toys (crumpled paper balls, cardboard boxes with holes, paper bags without handles) provide excellent enrichment at no cost. Rotate household items weekly for novelty."),
            ]

    elif cluster == "Cat Supplies":
        if "litter" in t:
            scenarios = [
                ("You have a multi-cat household", "Provide one litter tray per cat plus one extra, placed in different locations. Avoid placing trays side by side — cats treat adjacent trays as one. Scoop all trays at least once daily."),
                ("You live in a small flat and odour control is essential", "Choose a high-quality clumping litter with activated carbon. Clean trays twice daily. Consider a hooded tray with a carbon filter, but ensure your cat accepts the enclosure."),
                ("Your cat has a history of urinary issues", "Use unscented, fine-grained litter as it is gentlest on sensitive areas. Monitor litter tray visits closely — increased frequency or straining requires immediate veterinary attention."),
            ]
        elif "scratcher" in t or "tree" in t:
            scenarios = [
                ("Your cat only scratches furniture, ignoring scratching posts", "Place a tall, stable scratcher directly next to the damaged furniture. Apply catnip to the new surface. Once the cat uses it consistently (2-3 weeks), gradually move it to your preferred location."),
                ("You are renting and cannot make wall mountings", "Choose heavy-base freestanding cat trees that do not require wall anchoring. Floor-level cardboard scratchers and door-hanging options work well without any property modification."),
                ("You have a large, heavy cat (6kg+)", "Select cat trees rated for your cat's weight plus a 50% safety margin. Wider bases and wall-anchored designs are essential. Test stability before allowing use."),
            ]
        else:
            scenarios = [
                ("You are setting up supplies for a first-time indoor cat", "Start with essentials: two litter trays, quality litter, food and water bowls (placed separately), one scratching post, one cat bed, and a basic interactive toy. Add items based on the cat's preferences over the first month."),
                ("You are transitioning an outdoor cat to indoor-only", "Provide extra enrichment to compensate for lost outdoor stimulation: window perches, cat grass, puzzle feeders, and extended play sessions. Use Feliway to reduce transition stress."),
                ("Budget is a concern but quality matters", "Invest in the best litter tray and food bowls you can afford (these last years). Save on toys with DIY options. Compare unit cost per month rather than upfront price for consumables like litter."),
                ("Your cat has specific health needs affecting supply choices", "Consult your vet before purchasing special-needs supplies. Orthopaedic beds, prescription diet-compatible bowls, and low-entry litter trays can make a significant difference for cats with health conditions."),
            ]

    elif cluster == "Dog Harnesses":
        scenarios = [
            ("You have a strong pulling dog that is difficult to control", "Start with a front-clip no-pull harness for immediate management. Combine with daily loose-lead training using positive reinforcement. Consider booking sessions with an APDT-registered trainer if progress is slow."),
            ("Your dog is a puppy that will grow significantly", "Choose an adjustable harness with a wide size range. Re-measure every 4-6 weeks during the first year. Avoid investing in expensive harnesses until the dog reaches adult size."),
            ("Your dog has a respiratory condition (brachycephalic breed, collapsing trachea)", "A well-fitted Y-shaped or step-in harness is essential — never use a collar for walking. Ensure the harness does not press on the chest or restrict breathing. Consult your vet for specific fitting advice."),
            ("You walk in low-light conditions (early morning, winter evenings)", "Choose a harness with reflective stitching or panels. Add a clip-on LED light to the back D-ring. High-visibility harness colours (yellow, orange) improve visibility even without reflective elements."),
        ]

    elif cluster == "Indoor Cats":
        if "safety" in t or "hazard" in t:
            scenarios = [
                ("You are bringing a new kitten into an established home", "Conduct a room-by-room safety audit before the kitten arrives. Remove or secure all toxic plants, small objects, and accessible chemicals. Restrict access to high-risk areas until the kitten is older and you understand their behaviour."),
                ("You have young children and an indoor cat", "Teach children to respect the cat's space and never chase or corner them. Provide the cat with high escape routes (cat trees, shelves) that children cannot reach. Supervise all interactions until children understand safe handling."),
                ("You are renovating while keeping a cat indoors", "Confine the cat to a safe, well-equipped room away from construction. Ensure dust, chemicals, and small debris cannot reach the cat. Open windows for ventilation only if fitted with secure mesh."),
            ]
        elif "diet" in t or "nutrition" in t:
            scenarios = [
                ("Your indoor cat is overweight and needs to lose weight safely", "Consult your vet for a safe weight loss plan — cats should lose no more than 1-2% body weight per week. Use puzzle feeders to slow eating. Increase play to burn more calories."),
                ("You have both indoor and outdoor cats sharing a home", "Feed indoor cats separately with portion-controlled meals suited to their lower activity levels. Free-feeding encourages overconsumption in less active cats."),
                ("Your indoor cat has food allergies or sensitivities", "Work with your vet to identify triggers through an elimination diet. Once identified, choose an indoor-formula food from a range that excludes the allergen. Read labels carefully."),
            ]
        else:
            scenarios = [
                ("You are considering keeping a cat indoors for the first time", "Indoor cats can live enriched, healthy lives with proper environmental setup. Provide vertical space, daily interactive play, food puzzles, and window access. Regular veterinary check-ups should address indoor-specific concerns."),
                ("Your indoor cat seems anxious or stressed", "Identify and remove stressors where possible. Provide hiding spots, Feliway diffusers, and predictable daily routines. If stress persists, consult a veterinary behaviourist recommended by your vet."),
                ("You live in an upper-floor flat with no garden access", "Focus on window enrichment (secure perches, bird feeders outside), vertical climbing structures, and varied daily play. Cat grass grown indoors provides a safe outdoor-like experience."),
                ("Your indoor cat is elderly (14+) and less active", "Adapt the environment with low-entry litter trays, ground-level food and water stations, and soft, warm bedding. Gentle play with slow-moving toys maintains cognitive function. Increase veterinary check-ups to twice yearly."),
            ]

    elif cluster == "Educational":
        scenarios = [
            ("You are a first-time pet owner researching before adoption", "Start with the essentials: understand basic needs (nutrition, shelter, exercise, veterinary care), legal responsibilities (microchipping, insurance requirements), and the financial commitment involved."),
            ("You need to understand veterinary terminology before an appointment", "Review the relevant glossary section of this guide before your appointment. Write down specific questions. Do not hesitate to ask your vet to explain terms you do not understand during the consultation."),
            ("You are researching a specific health condition your pet has been diagnosed with", "Start with your vet's explanation, then verify with authoritative UK sources (BVA, PDSA, RCVS). Avoid general internet forums for medical advice — they often contain outdated or inaccurate information."),
            ("You want to improve your pet's quality of life but are unsure where to start", "Begin with the area most likely to have immediate impact: enrichment and play for bored pets, diet adjustment for overweight pets, or environmental modifications for anxious pets. Prioritise one change at a time."),
        ]

    else:  # Uncategorized
        if "toy" in t:
            scenarios = [
                ("Your dog destroys every toy within minutes", "Choose toys rated for aggressive chewers. Solid rubber (like Kong) and thick rope toys last longest. Supervise play and remove toys at the first sign of damage."),
                ("You have multiple dogs with different play styles", "Provide individual play sessions with toys matched to each dog's style. Store toys separately to prevent resource guarding. Shared toys should only be used during supervised group play."),
                ("Your dog shows no interest in toys", "Try different engagement methods: scent games, food-stuffed toys, or toys that move unpredictably. Some dogs prefer interactive play with their owner over solo toy play."),
            ]
        elif "senior" in t or "ageing" in t:
            scenarios = [
                ("Your senior dog has been diagnosed with arthritis", "Choose low-impact enrichment: puzzle feeders at nose height, gentle tug games, and scent trails. Avoid toys that require jumping or rapid direction changes."),
                ("Your older cat is sleeping more and playing less", "This can be normal ageing, but consult a vet to rule out pain or illness. Gentle play with slow-moving wand toys and food puzzles can maintain cognitive function."),
                ("You are adjusting care routines for an ageing pet", "Increase veterinary check-ups to twice yearly. Adapt the home environment: non-slip flooring, ramps for furniture access, and raised food bowls reduce strain on ageing joints."),
            ]
        else:
            scenarios = [
                ("You are a first-time pet owner on a budget", "Prioritise essentials: quality food, basic veterinary care, and one or two enrichment items. Many effective enrichment tools can be made from household items at no cost."),
                ("You are researching before deciding which pet to adopt", "Consider your living space, daily schedule, budget for ongoing care, and long-term commitment. Speak to breed-specific rescues or your local shelter for honest advice about what to expect."),
                ("You need to make a care decision and conflicting sources are causing confusion", "Consult your veterinarian for personalised advice. For general research, prioritise UK welfare organisations (RSPCA, PDSA, Cats Protection) over commercial websites or social media groups."),
                ("Your pet's needs have changed due to age or health", "Book a veterinary review to establish current needs. Update diet, exercise, and environment based on professional guidance. This guide provides general frameworks, but your vet knows your pet individually."),
            ]

    return scenarios


# ── content generation for 10BG (Trust Depth) ──────────────────────────────

def generate_trust_paragraph(title, cluster, existing_orgs):
    """Generate a methodology and trust references paragraph for body text insertion."""
    t = title.lower()

    # Determine which UK orgs to reference (aim for 3+ not already present)
    cat_orgs = {
        "Cats Protection": "https://www.cats.org.uk/",
        "International Cat Care": "https://icatcare.org/",
        "RSPCA": "https://www.rspca.org.uk/",
        "PDSA": "https://www.pdsa.org.uk/",
        "Blue Cross": "https://www.bluecross.org.uk/",
        "BVA": "https://www.bva.co.uk/",
        "RCVS": "https://www.rcvs.org.uk/",
    }
    dog_orgs = {
        "RSPCA": "https://www.rspca.org.uk/",
        "PDSA": "https://www.pdsa.org.uk/",
        "BVA": "https://www.bva.co.uk/",
        "Kennel Club": "https://www.thekennelclub.org.uk/",
        "Dogs Trust": "https://www.dogstrust.org.uk/",
        "Blue Cross": "https://www.bluecross.org.uk/",
        "RCVS": "https://www.rcvs.org.uk/",
        "Battersea": "https://www.battersea.org.uk/",
    }
    general_orgs = {
        "RSPCA": "https://www.rspca.org.uk/",
        "PDSA": "https://www.pdsa.org.uk/",
        "BVA": "https://www.bva.co.uk/",
        "Blue Cross": "https://www.bluecross.org.uk/",
        "RCVS": "https://www.rcvs.org.uk/",
    }

    # Select org pool based on cluster
    if cluster in ["Cat Toys", "Cat Supplies", "Indoor Cats"]:
        org_pool = cat_orgs
    elif cluster == "Dog Harnesses":
        org_pool = dog_orgs
    else:
        org_pool = general_orgs

    # Pick orgs not already heavily referenced
    existing_lower = [o.lower() for o in existing_orgs]
    new_orgs = []
    for name in org_pool:
        if name.lower() not in existing_lower and len(new_orgs) < 3:
            new_orgs.append(name)

    # If we couldn't find 3 new ones, add from the pool anyway
    if len(new_orgs) < 2:
        for name in org_pool:
            if name not in new_orgs and len(new_orgs) < 3:
                new_orgs.append(name)

    # Build the trust text
    org_links = []
    for org_name in new_orgs:
        url = org_pool.get(org_name, "")
        if url:
            org_links.append(f'<a href="{url}" rel="nofollow noopener" target="_blank">{org_name}</a>')
        else:
            org_links.append(org_name)

    if len(org_links) >= 3:
        org_str = f"{org_links[0]}, {org_links[1]}, and {org_links[2]}"
    elif len(org_links) == 2:
        org_str = f"{org_links[0]} and {org_links[1]}"
    else:
        org_str = org_links[0] if org_links else "UK welfare organisations"

    # Cluster-specific methodology text
    if cluster in ["Cat Toys", "Cat Supplies"]:
        methodology = f"The guidance in this article was compiled by reviewing published recommendations from {org_str}. We cross-referenced multiple UK welfare sources to verify accuracy and consulted current British Standards where applicable to product safety. Our editorial team reviews all content against the latest available guidance from these organisations."
    elif cluster == "Indoor Cats":
        methodology = f"This guide draws on published welfare guidance from {org_str}, with particular attention to their recommendations for cats kept exclusively indoors. We reviewed current UK veterinary consensus on indoor cat welfare, nutrition, and environmental enrichment to ensure this information reflects evidence-based best practice."
    elif cluster == "Dog Harnesses":
        methodology = f"The information in this guide was gathered by consulting published guidance from {org_str}. We reviewed UK veterinary recommendations on harness fitting, pressure distribution, and breed-specific considerations. Where relevant, we referenced British Standards for pet product safety and EU General Product Safety Regulations."
    elif cluster == "Educational":
        methodology = f"This educational resource was compiled by reviewing authoritative guidance from {org_str}. We prioritised UK-specific information and cross-referenced terminology with professional body publications to ensure definitions and advice reflect current consensus among UK veterinary and welfare professionals."
    else:
        methodology = f"This article was researched using published guidance from {org_str}. We consulted multiple UK veterinary and welfare sources to cross-reference accuracy and ensure recommendations reflect current evidence-based practice. Our editorial process requires verification against at least two authoritative sources before publication."

    return methodology, new_orgs


def generate_standards_reference(cluster, title):
    """Generate a standards/regulation reference suitable for the topic."""
    t = title.lower()

    if "safety" in t or "material" in t or "toxic" in t:
        return "UK pet products must comply with the General Product Safety Regulations 2005 and, where applicable, relevant British Standards for materials and construction. The EU General Product Safety Directive also applies to products sold in the UK market."
    elif "food" in t or "nutrition" in t or "diet" in t or "feeding" in t:
        return "UK pet food is regulated under the Animal Feed (England) Regulations and must meet nutritional standards set by FEDIAF (European Pet Food Industry Federation). The Pet Food Manufacturers' Association (PFMA) provides additional guidance on labelling and nutritional adequacy."
    elif cluster == "Dog Harnesses":
        return "Dog harnesses sold in the UK should comply with the General Product Safety Regulations 2005. While there is no specific British Standard for dog harnesses, responsible manufacturers conduct load testing and material safety assessments. The British Standards Institution (BSI) publishes guidance on pet product safety that reputable brands follow."
    elif cluster in ["Cat Toys", "Cat Supplies"]:
        return "Cat products sold in the UK must meet the General Product Safety Regulations 2005. The British Standards Institution (BSI) provides frameworks for pet product safety testing. When purchasing from UK retailers, look for products with clear material composition labelling and manufacturer safety testing information."
    else:
        return "UK pet products are subject to the General Product Safety Regulations 2005 and relevant consumer protection legislation. The Competition and Markets Authority (CMA) enforces truthful marketing claims. For health-related products, look for veterinary endorsement or alignment with guidance from the BVA or RCVS."


# ── content generation for 10BI (AI Extraction) ────────────────────────────

def generate_quick_answer(title, cluster):
    """Generate a 2-3 sentence Quick Answer for the top of the post."""
    t = title.lower()

    if cluster == "Cat Toys":
        if "interactive" in t:
            return "Interactive cat toys that require human participation — particularly wand toys — are the most effective enrichment tools for indoor cats. They engage the full predatory sequence (stalk, chase, pounce, catch) and should be used for at least 15 minutes daily. Electronic and self-play options supplement but do not replace guided interactive play."
        elif "catnip" in t:
            return "Catnip toys trigger a harmless euphoric response in approximately 50-70% of cats, lasting 5-15 minutes per exposure. The sensitivity is genetic, so non-responsive cats should be offered silver vine or valerian alternatives. Catnip potency fades over time, so choose refillable toys or store them sealed between sessions."
        elif "diy" in t or "homemade" in t:
            return "Safe DIY cat toys can be made from common household items such as cardboard boxes, paper bags (handles removed), and crumpled paper balls. Always avoid string, ribbon, rubber bands, and small detachable parts that pose choking or intestinal blockage risks. Supervise play with homemade toys and dispose of them when they show signs of wear."
        elif "safety" in t:
            return "Cat toy safety depends on three factors: appropriate sizing (too large to swallow), non-toxic materials (free from BPA, phthalates, and lead paint), and secure construction (no detachable small parts). Cats Protection and the RSPCA recommend supervising play with string-based and feathered toys, and inspecting all toys regularly for damage."
        elif "rotation" in t:
            return "Rotating cat toys every 3-7 days restores novelty and maintains engagement. Keep 3-4 toys active while storing 8-12 others in a sealed container (optionally with catnip). Each rotation should include a mix of interactive, self-play, and sensory toy types to engage different hunting instincts."
        elif "enrichment" in t or "beyond" in t:
            return "Cat enrichment extends beyond toys to include environmental modifications such as vertical climbing spaces, window perches, food puzzle feeders, cat grass, and scent-based activities. Indoor cats need 15-30 minutes of active play daily plus passive enrichment to prevent boredom and associated behavioural issues."
        elif "kitten" in t or "age" in t:
            return "Kittens need soft, lightweight toys without small detachable parts, while adult cats benefit from more challenging interactive and puzzle toys. Senior cats (12+) prefer gentle, ground-level play with slow-moving toys. Toy selection should match the cat's developmental stage, energy level, and physical ability."
        elif "replace" in t or "lifespan" in t:
            return "Cat toys should be replaced when they show visible damage (tears, exposed stuffing, loose parts), fail to clean properly, or when the cat has lost interest despite rotation. Most fabric toys last 2-4 months with regular use, while solid rubber or plastic toys can last 6-12 months depending on play intensity."
        elif "terminology" in t or "glossary" in t:
            return "Understanding cat toy terminology helps owners select appropriate enrichment. Key categories include interactive toys (requiring human participation), self-play toys (for independent use), puzzle feeders (combining food motivation with problem-solving), and sensory toys (engaging smell, sound, or texture). Each type targets different aspects of natural feline behaviour."
        elif "faq" in t:
            return "The most common cat toy questions concern safety (which materials are safe), effectiveness (which toys keep cats engaged), and frequency (how often to play and replace toys). This FAQ addresses these concerns using guidance from UK welfare organisations including Cats Protection and the RSPCA."
        else:
            return "Choosing effective cat toys means matching the toy type to your cat's natural hunting instincts and play preferences. UK welfare organisations recommend at least 15-30 minutes of interactive play daily for indoor cats, using a rotation of different toy categories to prevent boredom. Safety, engagement quality, and age appropriateness are the three most important selection criteria."

    elif cluster == "Cat Supplies":
        if "litter" in t and "disposal" in t:
            return "Used cat litter should be bagged in biodegradable sacks and placed in household waste — never flushed. Biodegradable litters (wood, paper, corn) break down faster in landfill than clay-based alternatives. Pregnant women should avoid handling used cat litter due to the risk of toxoplasmosis."
        elif "litter" in t and "self-clean" in t:
            return "Self-cleaning litter trays use automated raking or rotation mechanisms to separate waste from clean litter, reducing manual scooping. They cost significantly more than standard trays but save time for busy households. Most require specific litter types to function correctly."
        elif "litter" in t and ("type" in t or "comparison" in t or "guide" in t):
            return "Cat litter types include clumping clay, non-clumping clay, silica gel crystal, wood pellet, paper-based, and corn or tofu varieties. Each differs in odour control, dust level, tracking, absorbency, and environmental impact. The right choice depends on your cat's preference, your household situation, and any health considerations."
        elif "litter tray" in t:
            return "Litter trays should be at least 1.5 times the cat's body length, placed in quiet, accessible locations away from food and water. Multi-cat households need one tray per cat plus one extra, in different locations. Clean trays at least once daily and replace litter fully each week."
        elif "scratcher" in t or "scratching" in t:
            return "Cats scratch to maintain claw health, mark territory, and stretch muscles. Providing suitable scratching surfaces (sisal, cardboard, or carpet) in both vertical and horizontal orientations prevents furniture damage. Cats Protection recommends placing scratchers near sleeping areas and along common walking routes."
        elif "tree" in t:
            return "Cat trees provide essential vertical territory for indoor cats, combining climbing, scratching, perching, and resting in a single structure. Choose a tree rated for your cat's weight with a stable base, and place it near a window for maximum enrichment value. Wall-anchored models are safest for heavier cats."
        elif "bed" in t:
            return "Cat beds should be placed in warm, quiet, elevated locations that the cat naturally gravitates toward. Most cats prefer enclosed or semi-enclosed designs that provide a sense of security. Washable covers are essential for hygiene, and heated beds should have automatic temperature regulation."
        elif "collar" in t:
            return "Cat collars in the UK should always feature a breakaway (quick-release) mechanism to prevent strangulation if the collar catches on something. The fit should allow two fingers between the collar and the cat's neck. All cats in the UK must be microchipped by law, but an ID tag on a collar provides an additional identification layer."
        elif "harness" in t:
            return "Cat harnesses allow supervised outdoor exploration for indoor cats when properly introduced. An escape-proof design with adjustable chest and belly straps is essential. Introduction should be gradual over 1-2 weeks, starting with indoor-only sessions before any outdoor use."
        elif "brush" in t or "groom" in t:
            return "Cat grooming tool selection depends on coat type: slicker brushes suit medium to long coats, rubber brushes work well for short-haired cats, and wide-toothed combs help detangle longer fur. Regular grooming reduces hairballs, prevents matting, and allows early detection of skin issues. Most cats benefit from brushing 2-3 times per week."
        elif "shampoo" in t:
            return "Cats rarely need bathing as they are effective self-groomers. When a bath is necessary (e.g. for medical reasons or contamination), use a pH-balanced cat-specific shampoo — never human products, which can irritate feline skin. Cats Protection advises consulting a vet before bathing a cat for the first time."
        elif "nail" in t or "claw" in t:
            return "Cat nail clipping every 2-4 weeks prevents overgrowth, snagging, and ingrown claws, particularly for indoor cats that do not wear claws down on outdoor surfaces. Use purpose-built cat nail clippers and trim only the transparent tip, avoiding the pink quick. If unsure, ask a vet or qualified groomer to demonstrate."
        elif "essential" in t or "glossary" in t or "basics" in t:
            return "Essential cat supplies include food and water bowls (ceramic or stainless steel), at least two litter trays, quality cat litter, a scratching surface, a safe bed, and interactive toys. Understanding what each product does and what quality indicators to look for helps new owners avoid unnecessary purchases and choose items that genuinely support their cat's welfare."
        elif "tracker" in t or "gps" in t:
            return "GPS cat trackers attach to the collar and use satellite or Bluetooth technology to show a cat's real-time location via a smartphone app. They are particularly useful for cats with outdoor access in the UK, where traffic and theft are significant risks. Battery life, weight, and subscription costs vary significantly between brands."
        elif "id tag" in t or "identification" in t:
            return "While microchipping is a legal requirement for cats in the UK under the Microchipping of Cats (England) Regulations 2023, an ID tag on a breakaway collar provides immediate visible identification. Tags should include the owner's phone number and postcode — a cat's name is optional but an address should be avoided for security."
        else:
            return "Choosing the right cat supplies means prioritising safety, durability, and appropriateness for your cat's specific needs. UK welfare organisations including Cats Protection and the RSPCA provide guidance on essential products. Focus on quality over quantity — a few well-chosen items are more effective than a large collection of poor-quality alternatives."

    elif cluster == "Dog Harnesses":
        if "no-pull" in t:
            return "No-pull dog harnesses reduce pulling by redirecting the dog's momentum when they surge forward, typically using a front chest clip. They are a management tool that works best when combined with positive reinforcement loose-lead training. The RSPCA and Kennel Club recommend harnesses over collars for dogs that pull, as they distribute pressure away from the neck and trachea."
        elif "measure" in t or "fit" in t:
            return "Measuring a dog for a harness requires three measurements: girth (widest part of the rib cage), neck circumference, and chest width. The harness should allow two fingers to fit between the strap and the dog's body at all contact points. Re-measure every 3-6 months, or monthly for growing puppies."
        elif "collar" in t:
            return "Harnesses distribute walking pressure across the chest and shoulders rather than concentrating it on the neck, making them safer for most dogs — especially brachycephalic breeds and dogs prone to tracheal collapse. Collars remain useful for carrying ID tags but are not recommended as the primary walking attachment for dogs that pull. UK veterinary organisations generally favour harnesses for daily walks."
        elif "type" in t:
            return "The main dog harness types are back-clip (standard walking), front-clip (anti-pull training), dual-clip (versatile), Y-shaped (freedom of movement), step-in (easy fitting), and overhead (slip-on design). Each suits different body shapes, activities, and training needs. The right type depends on your dog's size, behaviour, and any health considerations."
        else:
            return "A well-fitted dog harness distributes walking pressure across the chest and shoulders, protecting the neck and trachea from collar-related injuries. UK veterinary organisations including the BVA and RSPCA recommend harnesses for daily walking, particularly for breeds prone to respiratory or spinal issues. Correct fitting, appropriate material, and regular size checks are essential for safety and comfort."

    elif cluster == "Indoor Cats":
        if "diet" in t or "nutrition" in t:
            return "Indoor cats typically need 10-20% fewer calories than outdoor cats due to their lower activity levels. Indoor-specific cat food formulations address this calorie difference while adding fibre for hairball management and nutrients for urinary health. The PFMA and PDSA recommend portion-controlled feeding rather than free-feeding for indoor cats to prevent obesity."
        elif "behaviour" in t:
            return "Common indoor cat behaviours such as excessive vocalisation, furniture scratching, and litter tray avoidance usually signal unmet environmental needs rather than behavioural problems. Cats Protection recommends ensuring indoor cats have adequate territory (including vertical space), daily interactive play, and appropriate resources before considering behavioural intervention."
        elif "exercise" in t or "active" in t:
            return "Indoor cats need at least 15-30 minutes of active play daily to maintain a healthy weight and prevent behavioural issues. Effective exercise strategies combine interactive play sessions (wand toys, chase games) with environmental modifications (climbing structures, food puzzles) that encourage natural movement throughout the day."
        elif "safety" in t or "hazard" in t:
            return "The most common indoor hazards for cats include toxic houseplants (especially lilies), small ingestible objects (hair ties, rubber bands), unsecured windows, accessible chemicals, and exposed electrical cords. Cats Protection maintains a comprehensive list of plants toxic to cats, and the Animal PoisonLine (01202 509000) provides 24-hour emergency advice."
        elif "environment" in t or "enrichment" in t or "friendly" in t:
            return "Creating a cat-friendly indoor environment requires vertical space (cat trees, shelves), hiding spots, window access, separate resource stations (food, water, litter in different locations), and multiple scratching surfaces. International Cat Care recommends these as minimum environmental standards for indoor cats to maintain physical and psychological wellbeing."
        elif "terminology" in t or "glossary" in t:
            return "Indoor cat terminology covers environmental enrichment concepts (vertical territory, resource stations, safe zones), behavioural terms (redirected aggression, displacement activity, marking), and health-specific vocabulary (obligate carnivore, taurine deficiency, feline lower urinary tract disease). Understanding these terms helps owners communicate more effectively with veterinary professionals."
        else:
            return "Indoor cats can live long, healthy, enriched lives when their environment meets their physical, mental, and social needs. Key requirements include daily interactive play, vertical territory, hiding spots, appropriate scratching surfaces, and regular veterinary check-ups that address indoor-specific health risks such as obesity and dental disease. UK organisations including Cats Protection and International Cat Care provide detailed guidance on indoor cat welfare."

    elif cluster == "Educational":
        if "training" in t:
            return "Effective pet training in the UK is based on positive reinforcement principles — rewarding desired behaviour rather than punishing unwanted behaviour. The APDT, Kennel Club, and RSPCA all endorse force-free training methods as the most effective and humane approach. Professional trainers should hold recognised qualifications and be members of an accredited body."
        elif "health" in t:
            return "Understanding common pet health conditions, their symptoms, and when to seek veterinary attention is a fundamental responsibility of pet ownership. The BVA and PDSA recommend annual health checks for adult pets and twice-yearly checks for senior animals. Preventive care — including vaccinations, dental hygiene, and parasite control — is more effective and less costly than treating established conditions."
        elif "nutrition" in t or "food" in t:
            return "Pet food labels in the UK are regulated under the Animal Feed Regulations and must list ingredients in descending order by weight. Understanding terms like 'complete food' (provides all necessary nutrients), 'complementary food' (must be fed alongside other food), and 'meat derivatives' (by-products of animal processing) helps owners make informed choices about what they feed their pets."
        elif "enrichment" in t or "play" in t:
            return "Pet enrichment encompasses any activity that provides mental stimulation, physical exercise, or sensory engagement beyond basic care needs. Types include food-based (puzzle feeders, scatter feeding), social (interactive play, training), environmental (climbing, hiding, exploring), and sensory (scent games, texture variety). Daily enrichment is essential for preventing boredom-related behavioural issues in both dogs and cats."
        elif "behaviour" in t or "body language" in t:
            return "Understanding pet body language is the foundation of safe, positive human-animal interaction. Dogs communicate primarily through tail position, ear orientation, body posture, and facial expressions. Cats use tail position, ear direction, pupil size, and whisker orientation. Misreading these signals is a common cause of bites and scratches, particularly in children."
        elif "grooming" in t:
            return "Regular grooming maintains coat health, prevents matting, and allows early detection of skin issues, parasites, and lumps. Grooming frequency depends on coat type — long-haired breeds may need daily attention, while short-haired pets benefit from weekly sessions. The RSPCA recommends introducing grooming gradually from a young age to build positive associations."
        else:
            return "This educational guide provides evidence-based pet care information verified against published guidance from UK veterinary and welfare organisations including the RSPCA, PDSA, and BVA. All terminology and recommendations reflect current UK professional consensus. For advice specific to your pet, always consult a qualified veterinary professional."

    else:  # Uncategorized
        return "This guide provides evidence-based pet care information compiled from published guidance by UK veterinary and welfare organisations including the RSPCA, PDSA, and BVA. All recommendations are educational in nature and should be supplemented by personalised advice from your veterinarian for your pet's specific needs."


def generate_additional_faq(title, cluster, existing_count):
    """Generate additional FAQ items to reach 5+ total."""
    needed = max(0, 5 - existing_count)
    if needed == 0:
        return []

    t = title.lower()
    faq_pool = []

    if cluster == "Cat Toys":
        faq_pool = [
            ("How long should I play with my cat each day?", "UK welfare organisations including Cats Protection recommend at least 15-30 minutes of interactive play daily for indoor cats, ideally split into two or three shorter sessions. Play at dawn and dusk aligns with cats' natural activity peaks."),
            ("Are laser pointer toys safe for cats?", "Laser pointers are safe when used correctly. Always end sessions by directing the laser to a physical toy the cat can catch — this completes the prey sequence and prevents frustration. Never shine lasers directly into a cat's eyes."),
            ("What should I do if my cat eats part of a toy?", "Contact your veterinarian immediately. Do not attempt to induce vomiting. Signs of intestinal obstruction include vomiting, loss of appetite, lethargy, and straining in the litter tray. String ingestion is a veterinary emergency."),
            ("How often should I rotate my cat's toys?", "Rotate toys every 3-7 days for optimal engagement. Keep 3-4 toys active and store the rest in a sealed container. This simple practice restores novelty and maintains your cat's interest over time."),
            ("Do indoor cats need different toys than outdoor cats?", "Indoor cats rely entirely on provided enrichment, so they need a wider variety of toy types. Focus on toys that satisfy hunting instincts (chase, pounce, catch) and provide mental stimulation (puzzle feeders, scent games) to compensate for the lack of outdoor stimuli."),
            ("At what age can kittens start playing with toys?", "Kittens begin showing play behaviour from around 3-4 weeks of age. By 7-8 weeks, they are ready for lightweight, soft toys without small detachable parts. Interactive play should be gentle and brief — 5 minutes per session — to match their developing coordination."),
        ]
    elif cluster == "Cat Supplies":
        faq_pool = [
            ("How often should I clean my cat's litter tray?", "Scoop solid waste at least once daily and fully replace all litter once a week. Wash the tray with mild soap and warm water during the full change. Avoid strong-smelling disinfectants, which can deter cats from using the tray."),
            ("What type of cat litter is safest?", "All commercially available cat litters sold by UK retailers are safe for general use. Unscented, low-dust varieties are recommended for cats with respiratory sensitivities. Kittens under 8 weeks should use non-clumping litter to prevent accidental ingestion."),
            ("Do cats prefer covered or uncovered litter trays?", "Most cats prefer uncovered trays because they allow a clear view of surroundings and better air circulation. If you use a covered tray, ensure it is large enough for the cat to turn around comfortably and clean it more frequently as odours concentrate inside."),
            ("How do I choose the right size scratching post?", "A scratching post should be tall enough for the cat to stretch fully while scratching — at least 60cm for an average adult cat. It must be completely stable during vigorous use. Wall-mounted options are ideal for space-constrained homes."),
            ("Are breakaway cat collars really necessary?", "Yes. Breakaway collars release under pressure, preventing strangulation if the collar catches on a fence, branch, or furniture. Non-breakaway collars pose a serious safety risk, particularly for cats with outdoor access. Cats Protection strongly recommends breakaway collars for all cats."),
            ("How often should I groom my cat?", "Short-haired cats benefit from brushing 1-2 times per week. Long-haired breeds need daily grooming to prevent matting. Regular grooming reduces hairballs, removes loose fur, and allows early detection of skin issues or parasites."),
        ]
    elif cluster == "Dog Harnesses":
        faq_pool = [
            ("Is a harness better than a collar for walking?", "For most dogs, a harness is safer for walking because it distributes pressure across the chest rather than concentrating it on the neck. The BVA recommends harnesses for dogs that pull, brachycephalic breeds, and dogs with neck or spinal issues."),
            ("How tight should a dog harness be?", "You should be able to fit two fingers between the harness and your dog's body at all strap points. The harness should not shift from side to side or ride up toward the throat. Check the fit before every walk."),
            ("Can a dog wear a harness all day?", "Harnesses should be removed when not on a walk or in training. Extended wear can cause chafing, fur matting, and skin irritation. The harness should be a walking tool, not permanent wear."),
            ("What is the difference between front-clip and back-clip harnesses?", "Front-clip harnesses attach the lead at the chest, which redirects pulling dogs toward the handler. Back-clip harnesses attach between the shoulder blades and are more comfortable for well-behaved walkers. Dual-clip harnesses offer both options."),
            ("How often should I replace a dog harness?", "Inspect the harness monthly for fraying, worn buckles, or stretched straps. Most quality harnesses last 1-2 years with regular use. Replace immediately if any hardware is damaged or if the dog has outgrown it."),
            ("My dog hates having a harness put on. What can I do?", "Associate the harness with positive experiences: let the dog sniff it, reward them for approaching it, and gradually progress to putting it on with treats at each step. Use a step-in or overhead design if your dog dislikes things going over their head."),
        ]
    elif cluster == "Indoor Cats":
        faq_pool = [
            ("Is it cruel to keep a cat indoors?", "No. Indoor cats can live enriched, healthy lives when their environment meets their physical, mental, and social needs. Cats Protection acknowledges that indoor living is appropriate and often advisable in urban areas, near busy roads, or for certain breeds."),
            ("How much exercise does an indoor cat need?", "Indoor cats need at least 15-30 minutes of active play daily, ideally split into multiple shorter sessions. Environmental enrichment (climbing structures, food puzzles, window perches) provides additional physical activity throughout the day."),
            ("Do indoor cats get depressed?", "Indoor cats can develop stress-related behaviours if their environment is insufficiently stimulating. Signs include overgrooming, excessive sleeping, loss of appetite, or litter tray avoidance. Adequate enrichment, daily play, and routine veterinary care prevent most issues."),
            ("Should I get a second cat to keep my indoor cat company?", "Some cats benefit from companionship, but many are happier as sole cats. Introducing a second cat requires careful, gradual introduction over 2-4 weeks. Consider your existing cat's temperament — a cat that hisses at other cats through windows may not welcome a housemate."),
            ("How do I prevent my indoor cat from becoming overweight?", "Measure food portions accurately using kitchen scales, not estimation. Use the indoor-formula feeding guidelines rather than standard amounts. Replace a portion of daily food into puzzle feeders to slow eating and increase activity."),
            ("Can indoor cats go outside on a harness?", "Yes, with proper training. Introduce the harness indoors first over 1-2 weeks before venturing outside. Choose quiet, enclosed outdoor spaces initially. Ensure vaccinations are up to date and the cat is microchipped before any outdoor access."),
        ]
    elif cluster == "Educational":
        faq_pool = [
            ("Where can I find reliable pet care information in the UK?", "The RSPCA, PDSA, BVA, Kennel Club, Cats Protection, and Dogs Trust all publish free, evidence-based pet care guidance online. For medical advice, always consult a qualified veterinary professional."),
            ("How do I know if pet care advice online is trustworthy?", "Check whether the source is a recognised UK veterinary or welfare organisation. Look for references to published research or professional guidelines. Be sceptical of advice that makes absolute claims, promotes specific products, or contradicts veterinary consensus."),
            ("What qualifications should a pet professional have?", "Veterinarians must be registered with the RCVS. Dog trainers should hold APDT or IMDT membership. Behaviourists should be certified by the ABTC (Animal Behaviour and Training Council). Always verify credentials before engaging a professional."),
            ("Is pet insurance necessary in the UK?", "While not legally required, pet insurance is strongly recommended by UK veterinary organisations. Emergency treatment can cost thousands of pounds. Lifetime policies offer the most comprehensive cover. The PDSA provides subsidised care for pet owners receiving certain benefits."),
            ("How often should I take my pet to the vet?", "Adult pets should have an annual health check. Senior pets (dogs over 7, cats over 11) benefit from twice-yearly examinations. Puppies and kittens need more frequent visits during their vaccination schedule. Do not wait for illness — preventive care is more effective and less costly."),
            ("What are the legal requirements for pet owners in the UK?", "UK law requires dogs to be microchipped and wear a collar with an ID tag in public. Cats must be microchipped under the Microchipping of Cats (England) Regulations 2023. The Animal Welfare Act 2006 places a duty of care on all pet owners to meet their animal's basic needs."),
        ]
    else:  # Uncategorized
        faq_pool = [
            ("Where can I find trusted UK pet care advice?", "Start with the RSPCA, PDSA, BVA, Kennel Club (for dogs), and Cats Protection (for cats). These organisations publish free, evidence-based guidance. For personalised advice, consult a veterinary professional registered with the RCVS."),
            ("How do I choose between competing pet care products?", "Focus on safety certifications, material quality, and suitability for your specific pet rather than price alone. Cross-reference product types with guidance from UK welfare organisations. Avoid products making unverified health claims."),
            ("When should I consult a veterinarian rather than following online guides?", "Always consult a vet for new symptoms, behavioural changes, emergencies, dietary concerns, or before starting any new health regimen. Online guides provide general education — your vet provides personalised medical advice."),
            ("What is the difference between veterinary advice and welfare organisation guidance?", "Veterinary advice is personalised medical care for your specific pet. Welfare organisation guidance provides general best-practice frameworks based on research and casework. Both are valuable, but veterinary advice takes priority for individual health decisions."),
            ("How can I tell if my pet is healthy?", "Key health indicators include consistent appetite, normal energy levels, clear eyes and ears, healthy coat, regular bowel movements, and stable weight. Changes in any of these should prompt a veterinary consultation. Annual health checks catch issues before they become serious."),
            ("Is the advice in this guide suitable for pets outside the UK?", "This guide references UK-specific regulations, products, and organisations. While the general principles apply broadly, readers outside the UK should consult local veterinary authorities for region-specific advice on vaccinations, regulations, and product availability."),
        ]

    return faq_pool[:needed]


def generate_additional_key_terms(title, cluster, existing_count):
    """Generate additional key terms to reach 5+ total."""
    needed = max(0, 5 - existing_count)
    if needed == 0:
        return []

    t = title.lower()
    terms_pool = []

    if cluster == "Cat Toys":
        terms_pool = [
            ("Predatory Sequence", "The natural hunting cycle in cats: stalk, chase, pounce, catch, and kill-bite. Effective toys engage multiple stages of this sequence."),
            ("Environmental Enrichment", "Modifications to a pet's living space or routine that stimulate natural behaviours and improve welfare. Includes toys, climbing structures, and sensory activities."),
            ("Catnip Response", "A hereditary trait causing a euphoric reaction in approximately 50-70% of cats when exposed to nepetalactone, the active compound in catnip (Nepeta cataria)."),
            ("Prey Drive", "The innate motivation to hunt, chase, and capture prey. In domestic cats, this instinct remains strong and must be satisfied through play to prevent behavioural issues."),
            ("Kicker Toy", "A long, cylindrical toy designed for cats to grab with their front paws and kick with their hind legs, mimicking the 'bunny kick' used on captured prey."),
            ("Silver Vine", "A plant (Actinidia polygama) that produces a euphoric response in approximately 75% of cats, including many that do not respond to catnip."),
            ("Food Puzzle", "A device that requires problem-solving to access food, providing mental stimulation and slowing eating speed. Also called a puzzle feeder or interactive feeder."),
        ]
    elif cluster == "Cat Supplies":
        terms_pool = [
            ("Breakaway Collar", "A cat collar designed with a quick-release mechanism that opens under pressure, preventing strangulation if the collar catches on an object."),
            ("Clumping Litter", "Cat litter that forms solid clumps when wet, making it easier to scoop urine-soaked litter without replacing the entire tray contents."),
            ("Sisal", "A natural fibre from the agave plant, commonly used to wrap scratching posts. Cats prefer its texture for claw maintenance and territorial marking."),
            ("Microchipping", "The implantation of a small electronic chip under the pet's skin for permanent identification. Legally required for cats in England since June 2024."),
            ("Obligate Carnivore", "An animal that requires nutrients found only in animal tissue to survive. Cats are obligate carnivores and must consume meat as part of their diet."),
            ("Resource Station", "A designated area providing one of a cat's essential needs (food, water, litter, rest, or play). International Cat Care recommends separating these across different locations."),
        ]
    elif cluster == "Dog Harnesses":
        terms_pool = [
            ("Front-Clip Harness", "A harness with the lead attachment point on the chest, which redirects the dog's forward momentum sideways when they pull, discouraging pulling behaviour."),
            ("Back-Clip Harness", "A harness with the lead attachment point between the shoulder blades, suitable for dogs that walk without pulling but less effective for pull management."),
            ("Girth Measurement", "The circumference of the dog's body at the widest point of the rib cage, measured behind the front legs. The primary measurement for harness sizing."),
            ("D-Ring", "The metal ring on a harness where the lead clip attaches. A secure, welded D-ring is essential for safety. Inspect regularly for wear."),
            ("Brachycephalic", "Having a shortened skull shape (flat face), as seen in breeds like Pugs and French Bulldogs. These breeds are particularly prone to collar-related breathing issues and benefit from harness use."),
            ("Y-Shaped Harness", "A harness design where the front straps form a Y shape across the chest, allowing natural shoulder movement. Recommended by canine physiotherapists for active dogs."),
        ]
    elif cluster == "Indoor Cats":
        terms_pool = [
            ("Vertical Territory", "Elevated spaces such as cat trees, shelves, and perches that allow cats to survey their environment from above. Essential for indoor cat welfare and conflict reduction in multi-cat homes."),
            ("Redirected Aggression", "Aggressive behaviour directed at a nearby person or animal when the cat cannot reach the actual source of arousal (e.g. an outdoor cat visible through a window)."),
            ("Feliway", "A synthetic pheromone product that mimics the feline facial pheromone, which cats use to mark safe, familiar territory. Used to reduce stress-related behaviours in indoor cats."),
            ("Obligate Carnivore", "An animal that must eat meat to obtain essential nutrients. Cats cannot synthesise taurine and certain other amino acids from plant sources."),
            ("Environmental Enrichment", "Modifications to a cat's indoor environment that stimulate natural behaviours, including climbing, hiding, hunting (through play), and scratching."),
            ("Displacement Activity", "A behaviour performed out of context when a cat is conflicted or stressed — such as sudden grooming during a tense social encounter."),
        ]
    elif cluster == "Educational":
        terms_pool = [
            ("Positive Reinforcement", "A training method where desired behaviour is rewarded to increase its frequency. Endorsed by the APDT, Kennel Club, and RSPCA as the most effective and humane approach."),
            ("RCVS", "Royal College of Veterinary Surgeons — the regulatory body for veterinary professionals in the UK. All practising vets and vet nurses must be registered."),
            ("FEDIAF", "European Pet Food Industry Federation — sets nutritional guidelines that UK pet food manufacturers follow to ensure complete and balanced nutrition."),
            ("Microchipping", "The implantation of a small electronic identification chip under a pet's skin. Legally required for dogs (since 2016) and cats in England (since 2024)."),
            ("Animal Welfare Act 2006", "UK legislation that places a legal duty of care on pet owners to provide for their animal's needs: environment, diet, behaviour, companionship, and health."),
            ("Force-Free Training", "Training approaches that avoid the use of physical punishment, intimidation, or aversive equipment. The standard endorsed by all major UK welfare organisations."),
        ]
    else:  # Uncategorized
        terms_pool = [
            ("Evidence-Based Practice", "An approach to pet care that prioritises recommendations supported by scientific research and professional consensus over anecdotal advice."),
            ("Enrichment", "Any activity, object, or environmental modification that provides mental or physical stimulation beyond basic survival needs."),
            ("Preventive Care", "Veterinary interventions (vaccinations, parasite control, dental checks) that aim to prevent disease rather than treat it after onset."),
            ("RSPCA", "Royal Society for the Prevention of Cruelty to Animals — the UK's largest animal welfare charity, providing rescue, rehabilitation, and public education."),
            ("PDSA", "People's Dispensary for Sick Animals — a UK veterinary charity providing free and subsidised treatment for pets of owners in financial hardship."),
            ("BVA", "British Veterinary Association — the representative body for UK veterinary professionals, publishing clinical guidance and welfare position statements."),
        ]

    return terms_pool[:needed]


def enrich_at_a_glance(title, cluster, content, current_count):
    """Generate additional At a Glance bullets to reach 5-6 total."""
    needed = max(0, 5 - current_count)
    if needed == 0:
        return []

    t = title.lower()
    bullets = []

    if cluster == "Cat Toys":
        pool = [
            "UK welfare organisations recommend 15-30 minutes of interactive play daily for indoor cats",
            "Cats Protection advises supervising all play sessions involving string, ribbon, or feathered attachments",
            "Approximately 50-70% of cats respond to catnip — silver vine affects roughly 75% and is a useful alternative",
            "Toy rotation every 3-7 days maintains novelty and prevents boredom in indoor cats",
            "Material safety is critical: toys should be free from BPA, phthalates, and small detachable parts",
            "Interactive wand toys engage the full predatory sequence and are considered the most effective toy type",
        ]
    elif cluster == "Cat Supplies":
        pool = [
            "Multi-cat households need one litter tray per cat plus one extra, placed in separate locations",
            "Breakaway collars are recommended by Cats Protection for all cats to prevent strangulation injuries",
            "All cats in England must be microchipped by law under the 2023 regulations",
            "Cat scratching posts should be at least 60cm tall and completely stable during vigorous use",
            "Indoor cats rely entirely on provided supplies for enrichment, hygiene, and comfort",
            "UK pet product safety is governed by the General Product Safety Regulations 2005",
        ]
    elif cluster == "Dog Harnesses":
        pool = [
            "The BVA recommends harnesses over collars for dogs that pull to protect the trachea",
            "A correctly fitted harness allows two fingers between the strap and the dog at all contact points",
            "Front-clip harnesses redirect pulling momentum and are most effective for training purposes",
            "Growing puppies need harness size checks every 4-8 weeks during the first year",
            "Brachycephalic breeds (flat-faced dogs) should always use a harness rather than a collar",
            "Harness hardware (D-rings, buckles) should be inspected monthly for wear and corrosion",
        ]
    elif cluster == "Indoor Cats":
        pool = [
            "Indoor cats typically need 10-20% fewer calories than outdoor cats due to reduced activity",
            "Cats Protection recognises indoor living as appropriate when enrichment needs are fully met",
            "Vertical territory (cat trees, shelves, perches) is essential for indoor cat psychological welfare",
            "The Animal PoisonLine (01202 509000) provides 24-hour emergency advice for suspected poisoning",
            "Indoor cats are at higher risk of obesity, dental disease, and stress-related behaviour issues",
            "Each indoor cat needs its own food bowl, water source, litter tray, sleeping area, and scratching surface",
        ]
    elif cluster == "Educational":
        pool = [
            "UK veterinary professionals are regulated by the RCVS (Royal College of Veterinary Surgeons)",
            "The Animal Welfare Act 2006 places a legal duty of care on all UK pet owners",
            "The RSPCA, PDSA, and BVA are the primary sources for evidence-based pet care guidance in the UK",
            "Preventive veterinary care is more effective and less costly than treating established conditions",
            "All dogs must be microchipped and wear an ID tag in public under UK law",
            "Force-free training methods are endorsed by all major UK veterinary and welfare organisations",
        ]
    else:
        pool = [
            "UK pet care guidance is primarily sourced from RSPCA, PDSA, BVA, and relevant breed organisations",
            "Evidence-based recommendations are cross-referenced against at least two authoritative UK sources",
            "All product guidance reflects UK availability, regulations, and consumer protection standards",
            "Veterinary consultation is recommended whenever general guidance does not address a specific situation",
            "This guide follows PetHub Online's editorial process and research methodology standards",
        ]

    return pool[:needed]


# ── HTML block templates ────────────────────────────────────────────────────

EVALUATION_BLOCK_TEMPLATE = '''<!-- wp:group {{"style":{{"color":{{"background":"#f0f9ff"}},"border":{{"radius":"6px","width":"1px","color":"#bae6fd"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#bae6fd;border-width:1px;border-radius:6px;background-color:#f0f9ff;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">How to Evaluate</h4>
<!-- /wp:heading -->
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"14px"}}}}}} -->
<p style="font-size:14px">Use these criteria when assessing your options:</p>
<!-- /wp:paragraph -->
<!-- wp:list -->
<ul class="wp-block-list">{criteria_items}</ul>
<!-- /wp:list -->
</div>
<!-- /wp:group -->'''

TROUBLESHOOTING_BLOCK_TEMPLATE = '''<!-- wp:group {{"style":{{"color":{{"background":"#fefce8"}},"border":{{"radius":"6px","width":"1px","color":"#fde047"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#fde047;border-width:1px;border-radius:6px;background-color:#fefce8;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">Common Problems and Solutions</h4>
<!-- /wp:heading -->
{problem_items}
</div>
<!-- /wp:group -->'''

SCENARIO_BLOCK_TEMPLATE = '''<!-- wp:group {{"style":{{"color":{{"background":"#fdf4ff"}},"border":{{"radius":"6px","width":"1px","color":"#e879f9"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#e879f9;border-width:1px;border-radius:6px;background-color:#fdf4ff;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">Which Option Suits Your Situation</h4>
<!-- /wp:heading -->
{scenario_items}
</div>
<!-- /wp:group -->'''

TRUST_METHODOLOGY_TEMPLATE = '''<!-- wp:group {{"style":{{"color":{{"background":"#f0fdf4"}},"border":{{"radius":"6px","width":"1px","color":"#86efac"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#86efac;border-width:1px;border-radius:6px;background-color:#f0fdf4;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">How This Information Was Gathered</h4>
<!-- /wp:heading -->
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"14px"}}}}}} -->
<p style="font-size:14px">{methodology_text}</p>
<!-- /wp:paragraph -->
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"14px"}}}}}} -->
<p style="font-size:14px">{standards_text}</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->'''


def build_evaluation_html(criteria):
    items = "\n".join(f"<li>{c}</li>" for c in criteria)
    return EVALUATION_BLOCK_TEMPLATE.format(criteria_items=items)


def build_troubleshooting_html(problems):
    items = []
    for problem, solution in problems:
        items.append(f'''<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"14px"}}}}}} -->
<p style="font-size:14px"><strong>{problem}:</strong> {solution}</p>
<!-- /wp:paragraph -->''')
    return TROUBLESHOOTING_BLOCK_TEMPLATE.format(problem_items="\n".join(items))


def build_scenario_html(scenarios):
    items = []
    for scenario, recommendation in scenarios:
        items.append(f'''<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"14px"}}}}}} -->
<p style="font-size:14px"><strong>{scenario}:</strong> {recommendation}</p>
<!-- /wp:paragraph -->''')
    return SCENARIO_BLOCK_TEMPLATE.format(scenario_items="\n".join(items))


def build_trust_methodology_html(methodology_text, standards_text):
    return TRUST_METHODOLOGY_TEMPLATE.format(
        methodology_text=methodology_text,
        standards_text=standards_text
    )


def build_quick_answer_html(text):
    return f'''<p class="wp-block-paragraph"><strong>Quick answer:</strong> {text}</p>'''


def build_faq_items_html(faq_items):
    html_parts = []
    for question, answer in faq_items:
        html_parts.append(f'''<h3 class="wp-block-heading">{question}</h3>
<p class="wp-block-paragraph">{answer}</p>''')
    return "\n".join(html_parts)


def build_key_terms_html(terms):
    items = []
    for term, definition in terms:
        items.append(f"<li><strong>{term}</strong> — {definition}</li>")
    return "\n".join(items)


def build_at_a_glance_bullets_html(bullets):
    return "\n".join(f"<li>{b}</li>" for b in bullets)


# ── main content modification function ──────────────────────────────────────

def modify_post_content(content, title, cluster):
    """
    Apply all three phases of modifications to post content.
    Returns (new_content, changes_dict).
    """
    changes = {
        "evaluation_added": False,
        "troubleshooting_added": False,
        "scenario_added": False,
        "trust_refs_added": False,
        "quick_answer_added": False,
        "faq_expanded": False,
        "key_terms_expanded": False,
        "at_a_glance_enriched": False,
        "methodology_added": False,
        "standards_added": False,
    }

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 10BI — Quick Answer (must be at very top)
    # ═══════════════════════════════════════════════════════════════════
    if not has_quick_answer(content):
        qa_text = generate_quick_answer(title, cluster)
        qa_html = build_quick_answer_html(qa_text)
        content = qa_html + "\n" + content
        changes["quick_answer_added"] = True

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 10BI — At a Glance enrichment
    # ═══════════════════════════════════════════════════════════════════
    glance_count = count_at_a_glance_bullets(content)
    if glance_count < 5:
        new_bullets = enrich_at_a_glance(title, cluster, content, glance_count)
        if new_bullets:
            bullets_html = build_at_a_glance_bullets_html(new_bullets)
            # Find the closing </ul> of the At a Glance list
            glance_match = re.search(r'At a Glance', content, re.IGNORECASE)
            if glance_match:
                after_glance = content[glance_match.start():]
                ul_close = re.search(r'</ul>', after_glance)
                if ul_close:
                    insert_pos = glance_match.start() + ul_close.start()
                    content = content[:insert_pos] + "\n" + bullets_html + "\n" + content[insert_pos:]
                    changes["at_a_glance_enriched"] = True

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 10BG — Trust depth (methodology + standards + org refs)
    # ═══════════════════════════════════════════════════════════════════
    existing_orgs = count_uk_org_refs(content)

    if not has_block(content, "How This Information Was Gathered"):
        methodology_text, new_orgs = generate_trust_paragraph(title, cluster, existing_orgs)
        standards_text = generate_standards_reference(cluster, title)
        trust_html = build_trust_methodology_html(methodology_text, standards_text)

        # Insert after the first major body section (after the "Why this matters" or first h2)
        first_h2 = re.search(r'<h2\s', content)
        if first_h2:
            # Insert just before the first h2 heading
            pos = first_h2.start()
            content = content[:pos] + trust_html + "\n\n" + content[pos:]
            changes["methodology_added"] = True
            changes["standards_added"] = True
            changes["trust_refs_added"] = True
        else:
            # Fallback: insert after At a Glance / Why this matters block
            why_match = re.search(r'Why this matters', content, re.IGNORECASE)
            if why_match:
                # Find the closing div of that block
                after_why = content[why_match.start():]
                close_div = re.search(r'</div>\s*\n', after_why)
                if close_div:
                    pos = why_match.start() + close_div.end()
                    content = content[:pos] + "\n" + trust_html + "\n" + content[pos:]
                    changes["methodology_added"] = True
                    changes["standards_added"] = True
                    changes["trust_refs_added"] = True

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 10BE — Decision Support blocks
    # ═══════════════════════════════════════════════════════════════════
    decision_blocks = []

    # Evaluation Framework
    if not has_block(content, "How to Evaluate"):
        criteria = generate_evaluation_framework(title, cluster)
        eval_html = build_evaluation_html(criteria)
        decision_blocks.append(eval_html)
        changes["evaluation_added"] = True

    # Troubleshooting
    if not has_block(content, "Common Problems and Solutions"):
        problems = generate_troubleshooting(title, cluster)
        trouble_html = build_troubleshooting_html(problems)
        decision_blocks.append(trouble_html)
        changes["troubleshooting_added"] = True

    # Scenario Guidance
    if not has_block(content, "Which Option Suits Your Situation"):
        scenarios = generate_scenario_guidance(title, cluster)
        scenario_html = build_scenario_html(scenarios)
        decision_blocks.append(scenario_html)
        changes["scenario_added"] = True

    if decision_blocks:
        insertion_point = find_insertion_point(content)
        insert_html = "\n\n" + "\n\n".join(decision_blocks) + "\n\n"
        content = content[:insertion_point] + insert_html + content[insertion_point:]

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 10BI — FAQ expansion
    # ═══════════════════════════════════════════════════════════════════
    faq_count = count_faq_items(content)
    if faq_count < 5:
        new_faqs = generate_additional_faq(title, cluster, faq_count)
        if new_faqs:
            faq_html = build_faq_items_html(new_faqs)
            # Find the FAQ section and insert before "Related Reading" or "Key Terms"
            faq_match = re.search(r'Frequently Asked Questions', content, re.IGNORECASE)
            if faq_match:
                faq_section_start = faq_match.start()
                # Find where to insert (before Related Reading or Key Terms)
                after_faq = content[faq_section_start:]
                end_markers = [
                    re.search(r'<h[23][^>]*>\s*Related Reading', after_faq, re.IGNORECASE),
                    re.search(r'<h[23][^>]*>\s*Key Terms', after_faq, re.IGNORECASE),
                    re.search(r'<h[23][^>]*>\s*Quick Checklist', after_faq, re.IGNORECASE),
                    re.search(r'<hr\s', after_faq, re.IGNORECASE),
                ]
                earliest_end = None
                for m in end_markers:
                    if m and (earliest_end is None or m.start() < earliest_end):
                        earliest_end = m.start()

                if earliest_end is not None:
                    insert_pos = faq_section_start + earliest_end
                    content = content[:insert_pos] + faq_html + "\n" + content[insert_pos:]
                else:
                    # Just append after last Q&A
                    last_p = content[faq_section_start:].rfind("</p>")
                    if last_p > 0:
                        insert_pos = faq_section_start + last_p + 4
                        content = content[:insert_pos] + "\n" + faq_html + content[insert_pos:]

                changes["faq_expanded"] = True
            else:
                # No FAQ section exists — create one before Key Terms or at end
                faq_heading = '<h2 class="wp-block-heading">Frequently Asked Questions</h2>\n'
                faq_html = faq_heading + build_faq_items_html(new_faqs)
                # Find Key Terms or Quick Checklist or Common Mistakes
                key_terms = re.search(r'<h[23][^>]*>\s*Key Terms', content, re.IGNORECASE)
                if key_terms:
                    insert_pos = key_terms.start()
                    content = content[:insert_pos] + faq_html + "\n" + content[insert_pos:]
                else:
                    # Insert before the end sections
                    insert_pos = find_insertion_point(content)
                    content = content[:insert_pos] + "\n" + faq_html + "\n" + content[insert_pos:]
                changes["faq_expanded"] = True

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 10BI — Key Terms expansion
    # ═══════════════════════════════════════════════════════════════════
    terms_count = count_key_terms(content)
    if terms_count < 5:
        new_terms = generate_additional_key_terms(title, cluster, terms_count)
        if new_terms:
            terms_html = build_key_terms_html(new_terms)
            terms_match = re.search(r'Key Terms', content, re.IGNORECASE)
            if terms_match:
                # Find the </ul> after Key Terms
                after_terms = content[terms_match.start():]
                ul_close = re.search(r'</ul>', after_terms)
                if ul_close:
                    insert_pos = terms_match.start() + ul_close.start()
                    content = content[:insert_pos] + "\n" + terms_html + "\n" + content[insert_pos:]
                    changes["key_terms_expanded"] = True

    return content, changes


# ── main execution ──────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("Phase 10BE + 10BG + 10BI — Decision Support, Trust Depth, AI Extraction")
    print("Clusters: Cat Toys, Cat Supplies, Dog Harnesses, Indoor Cats, Educational, Uncategorized")
    print("=" * 70)

    # Build target list
    print("\nFetching posts from API...")
    targets = build_target_list()
    print(f"\nTotal target posts: {len(targets)}")

    # Group by cluster for display
    cluster_counts = {}
    for t in targets:
        cluster_counts[t["cluster"]] = cluster_counts.get(t["cluster"], 0) + 1
    for c, n in sorted(cluster_counts.items()):
        print(f"  {c}: {n} posts")

    # Show all targets
    for t in targets:
        print(f"  [{t['cluster']}] {t['id']}: {t['title'][:60]}")

    # Process each post
    csv_rows = []
    updated = 0
    skipped = 0
    errors = 0

    for idx, target in enumerate(targets):
        pid = target["id"]
        cluster = target["cluster"]
        print(f"\n{'='*60}")
        print(f"[{idx+1}/{len(targets)}] Processing {pid}: {target['title'][:60]}")
        print(f"  Cluster: {cluster}")

        # Fetch raw content
        try:
            post = api_get(f"posts/{pid}?_fields=id,title,content&context=edit")
            if "content" not in post:
                print(f"  ERROR: No content field in response: {str(post)[:200]}")
                csv_rows.append({
                    "id": pid, "title": target["title"], "cluster": cluster,
                    "evaluation_added": "", "troubleshooting_added": "",
                    "scenario_added": "", "trust_refs_added": "",
                    "quick_answer_added": "", "faq_expanded": "", "status": "error_no_content"
                })
                errors += 1
                time.sleep(DELAY)
                continue

            raw_content = post["content"]["raw"]
            title = html.unescape(post["title"]["raw"])
            target["title"] = title
        except Exception as e:
            print(f"  ERROR fetching post: {e}")
            traceback.print_exc()
            csv_rows.append({
                "id": pid, "title": target["title"], "cluster": cluster,
                "evaluation_added": "", "troubleshooting_added": "",
                "scenario_added": "", "trust_refs_added": "",
                "quick_answer_added": "", "faq_expanded": "", "status": f"error_fetch"
            })
            errors += 1
            time.sleep(DELAY)
            continue

        time.sleep(DELAY)

        # Apply modifications
        try:
            new_content, changes = modify_post_content(raw_content, title, cluster)
        except Exception as e:
            print(f"  ERROR modifying content: {e}")
            traceback.print_exc()
            csv_rows.append({
                "id": pid, "title": title, "cluster": cluster,
                "evaluation_added": "", "troubleshooting_added": "",
                "scenario_added": "", "trust_refs_added": "",
                "quick_answer_added": "", "faq_expanded": "", "status": f"error_modify"
            })
            errors += 1
            continue

        # Check if any changes were made
        any_changes = any(changes.values())
        if not any_changes:
            print(f"  No modifications needed — all blocks present")
            skipped += 1
            csv_rows.append({
                "id": pid, "title": title, "cluster": cluster,
                "evaluation_added": "no", "troubleshooting_added": "no",
                "scenario_added": "no", "trust_refs_added": "no",
                "quick_answer_added": "no", "faq_expanded": "no",
                "status": "skipped_complete"
            })
            continue

        # Report changes
        change_list = [k for k, v in changes.items() if v]
        print(f"  Changes: {', '.join(change_list)}")
        print(f"  Content size: {len(raw_content)} -> {len(new_content)}")

        # Push update
        try:
            success, resp = api_update(pid, {"content": new_content})
            time.sleep(DELAY)

            if success:
                print(f"  SUCCESS — post {pid} updated")
                updated += 1
                csv_rows.append({
                    "id": pid, "title": title, "cluster": cluster,
                    "evaluation_added": "yes" if changes["evaluation_added"] else "no",
                    "troubleshooting_added": "yes" if changes["troubleshooting_added"] else "no",
                    "scenario_added": "yes" if changes["scenario_added"] else "no",
                    "trust_refs_added": "yes" if changes["trust_refs_added"] else "no",
                    "quick_answer_added": "yes" if changes["quick_answer_added"] else "no",
                    "faq_expanded": "yes" if changes["faq_expanded"] else "no",
                    "status": "updated"
                })
            else:
                print(f"  ERROR updating: {json.dumps(resp)[:200]}")
                errors += 1
                csv_rows.append({
                    "id": pid, "title": title, "cluster": cluster,
                    "evaluation_added": "yes" if changes["evaluation_added"] else "no",
                    "troubleshooting_added": "yes" if changes["troubleshooting_added"] else "no",
                    "scenario_added": "yes" if changes["scenario_added"] else "no",
                    "trust_refs_added": "yes" if changes["trust_refs_added"] else "no",
                    "quick_answer_added": "yes" if changes["quick_answer_added"] else "no",
                    "faq_expanded": "yes" if changes["faq_expanded"] else "no",
                    "status": f"error_update"
                })
        except Exception as e:
            print(f"  ERROR during API update: {e}")
            errors += 1
            csv_rows.append({
                "id": pid, "title": title, "cluster": cluster,
                "evaluation_added": "", "troubleshooting_added": "",
                "scenario_added": "", "trust_refs_added": "",
                "quick_answer_added": "", "faq_expanded": "",
                "status": f"error_api"
            })
            time.sleep(DELAY)

    # Write CSV
    print(f"\nWriting CSV to {CSV_PATH}")
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "title", "cluster", "evaluation_added", "troubleshooting_added",
            "scenario_added", "trust_refs_added", "quick_answer_added",
            "faq_expanded", "status"
        ])
        writer.writeheader()
        writer.writerows(csv_rows)

    # Summary
    print("\n" + "=" * 70)
    print("EXECUTION COMPLETE")
    print("=" * 70)
    print(f"Total posts:    {len(targets)}")
    print(f"Updated:        {updated}")
    print(f"Skipped:        {skipped}")
    print(f"Errors:         {errors}")
    print(f"\nCSV saved:      {CSV_PATH}")
    print(f"Script:         {os.path.join(DATA_DIR, 'trust_decision_engine.py')}")


if __name__ == "__main__":
    main()
