#!/usr/bin/env python3
"""
Phase 10BK/10BL/10BN Engine — Practical Guidance, Decision Support, Comparison Tables
Clusters: Dog Toys (1441), Dog Harnesses (1422), Dog Supplies (1376)

Inserts:
  - Practical Guide block (emerald #ecfdf5/#6ee7b7) BEFORE Evaluation Framework
  - Decision Pathway block (orange #fff7ed/#fdba74) AFTER Scenario Guidance, BEFORE Quick Checklist
  - Comparison tables (wp:table is-style-stripes) distributed across posts
"""

import subprocess, json, time, csv, re, os, sys, html, tempfile

# ── Config ──────────────────────────────────────────────────────────────────
WP_API = "https://pethubonline.com/wp-json/wp/v2"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
AUTH = f"{WP_USER}:{WP_PASS}"

CLUSTERS = {
    1441: "Dog Toys",
    1422: "Dog Harnesses",
    1376: "Dog Supplies",
}

CSV_PATH = "/var/lib/freelancer/projects/40416335/phase10bn_data/practical_decision_toys_harness_supplies.csv"
DELAY = 1.0  # seconds between API writes

# ── API Helpers ─────────────────────────────────────────────────────────────
def api_get(endpoint):
    r = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, f"{WP_API}/{endpoint}"],
        capture_output=True, text=True, timeout=60
    )
    return json.loads(r.stdout)

def api_update_post(post_id, content):
    """Update post content using temp file for large payloads."""
    payload = json.dumps({"content": content})
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    tmp.write(payload)
    tmp.close()
    try:
        r = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", f"@{tmp.name}",
             f"{WP_API}/posts/{post_id}"],
            capture_output=True, text=True, timeout=120
        )
        resp = json.loads(r.stdout)
        if 'id' in resp:
            return True
        else:
            print(f"    ERROR updating {post_id}: {r.stdout[:300]}")
            return False
    finally:
        os.unlink(tmp.name)

def fetch_all_posts(category_id):
    """Fetch all posts for a category (paginated)."""
    posts = []
    page = 1
    while True:
        data = api_get(f"posts?categories={category_id}&per_page=100&page={page}&context=edit&_fields=id,title,content,categories")
        if not data or isinstance(data, dict):
            break
        posts.extend(data)
        if len(data) < 100:
            break
        page += 1
        time.sleep(0.5)
    return posts

# ── Content Classification ──────────────────────────────────────────────────
def classify_toy_topic(title, content_snippet):
    """Classify a Dog Toys post by topic keywords for content matching."""
    t = (title + " " + content_snippet[:2000]).lower()
    topics = []
    if any(w in t for w in ['puzzle', 'enrichment', 'mental', 'stimulation', 'brain', 'interactive', 'treat-dispensing']):
        topics.append('enrichment')
    if any(w in t for w in ['chew', 'aggressive', 'power chewer', 'indestructible', 'tough', 'durable', 'destroyer']):
        topics.append('chewer')
    if any(w in t for w in ['puppy', 'teething', 'young', 'first toy']):
        topics.append('puppy')
    if any(w in t for w in ['safety', 'safe', 'toxic', 'hazard', 'choking', 'danger']):
        topics.append('safety')
    if any(w in t for w in ['clean', 'wash', 'hygien', 'sanitise', 'disinfect']):
        topics.append('cleaning')
    if any(w in t for w in ['indoor', 'outdoor', 'fetch', 'garden', 'house']):
        topics.append('environment')
    if any(w in t for w in ['diy', 'homemade', 'make your own']):
        topics.append('diy')
    if any(w in t for w in ['faq', 'question', 'common']):
        topics.append('faq')
    if any(w in t for w in ['play style', 'types of', 'different play']):
        topics.append('playstyle')
    if not topics:
        topics.append('general')
    return topics

def classify_supply_topic(title, content_snippet):
    """Classify a Dog Supplies post by topic."""
    t = (title + " " + content_snippet[:2000]).lower()
    topics = []
    if any(w in t for w in ['bowl', 'feeding', 'feeder', 'slow feeder', 'elevated', 'water bottle']):
        topics.append('bowls')
    if any(w in t for w in ['collar', 'lead', 'leash', 'walking']):
        topics.append('collars_leads')
    if any(w in t for w in ['bed', 'sleeping', 'orthopaedic', 'cooling', 'crate']):
        topics.append('beds')
    if any(w in t for w in ['groom', 'brush', 'shampoo', 'nail', 'clipper']):
        topics.append('grooming')
    if any(w in t for w in ['train', 'treat', 'behaviour', 'reward']):
        topics.append('training')
    if any(w in t for w in ['health', 'dental', 'flea', 'supplement', 'joint', 'first aid']):
        topics.append('health')
    if any(w in t for w in ['food', 'nutrition', 'diet', 'dry food', 'wet food', 'puppy food']):
        topics.append('food')
    if any(w in t for w in ['harness', 'no-pull']):
        topics.append('harness')
    if any(w in t for w in ['toy', 'puzzle', 'chew', 'enrichment']):
        topics.append('toys')
    if any(w in t for w in ['puppy', 'first-time', 'essential', 'new owner', 'socialisation']):
        topics.append('puppy_general')
    if any(w in t for w in ['hydration', 'water', 'drinking']):
        topics.append('hydration')
    if any(w in t for w in ['seasonal', 'winter', 'summer', 'year-round']):
        topics.append('seasonal')
    if any(w in t for w in ['glossary', 'terminology', 'terms explained']):
        topics.append('glossary')
    if not topics:
        topics.append('general')
    return topics


# ── Practical Guide Content (Phase 10BK) ───────────────────────────────────

def get_practical_guide_toys(topics, title):
    """Generate practical guide content for Dog Toys posts based on topic."""
    items = []

    if 'enrichment' in topics or 'general' in topics or 'faq' in topics:
        items.extend([
            "<li><strong>Step 1 — Assess your dog’s enrichment needs:</strong> Observe which activities hold your dog’s attention longest. Dogs who sniff enthusiastically benefit from snuffle mats (£8–15), while those who paw at objects suit puzzle feeders (£12–25).</li>",
            "<li><strong>Step 2 — Start with beginner-level puzzles:</strong> Choose toys with 1–2 moving parts. Progress to multi-step puzzles only once your dog solves the basic version within 5–10 minutes consistently.</li>",
            "<li><strong>Step 3 — Rotate enrichment toys weekly:</strong> Keep 3–4 toys in active rotation and store the rest. Reintroduce stored toys after 7–14 days to maintain novelty and prevent boredom.</li>",
            "<li><strong>Step 4 — Adjust difficulty gradually:</strong> If your dog gives up within 2 minutes, the toy is too difficult. If solved in under 30 seconds, increase the challenge by using stickier treats or adding steps.</li>",
        ])
    if 'chewer' in topics:
        items.extend([
            "<li><strong>Step 1 — Identify your dog’s chew strength:</strong> Gentle chewers suit plush or latex toys (£5–10). Moderate chewers need thick rubber (£10–18). Power chewers require solid rubber or nylon rated for aggressive chewing (£12–25).</li>",
            "<li><strong>Step 2 — Apply the thumbnail test:</strong> Press your thumbnail into the toy surface. If it leaves no indent, the toy may be too hard and could damage teeth. If it tears easily, it will not survive power chewing.</li>",
            "<li><strong>Step 3 — Size the toy correctly:</strong> The toy should be large enough that your dog cannot fit it entirely in their mouth. For Staffies and similar breeds, choose toys at least 10cm diameter for balls, 15cm for chew toys.</li>",
            "<li><strong>Step 4 — Supervise the first 3 play sessions:</strong> Watch for excessive fragmentation, pieces breaking off, or attempts to swallow chunks. Remove the toy immediately if any pieces detach.</li>",
            "<li><strong>Step 5 — Inspect weekly and replace every 3–6 months:</strong> Check for cracks, deep tooth marks, missing chunks, or exposed inner material. Replace immediately if structural integrity is compromised.</li>",
        ])
    if 'puppy' in topics:
        items.extend([
            "<li><strong>Step 1 — Choose age-appropriate textures:</strong> Puppies under 12 weeks need soft rubber or fabric toys (£4–8). From 12–24 weeks during peak teething, use chilled rubber teething toys (£6–12) to soothe gums.</li>",
            "<li><strong>Step 2 — Follow the size progression:</strong> Start with toys 5–8cm for small-breed puppies, 8–12cm for medium breeds, 12–15cm for large breeds. Upgrade sizes as your puppy grows — check monthly.</li>",
            "<li><strong>Step 3 — Introduce one new toy at a time:</strong> Give your puppy 2–3 days with each new toy before adding another. This helps identify preferences and any adverse reactions to materials.</li>",
            "<li><strong>Step 4 — Establish supervised play sessions:</strong> Limit play sessions to 10–15 minutes for puppies under 6 months. Puppies tire quickly and may become destructive with over-stimulation.</li>",
            "<li><strong>Step 5 — Remove and replace as adult teeth emerge:</strong> Between 4–7 months, transition from soft teething toys to more durable options. Keep one teething toy available until all adult teeth are established (around 7–8 months).</li>",
        ])
    if 'safety' in topics:
        items.extend([
            "<li><strong>Step 1 — Perform the squeeze test before purchase:</strong> Squeeze the toy firmly. It should not be small enough to compress into a size your dog could swallow. The toy’s smallest dimension should exceed your dog’s throat width.</li>",
            "<li><strong>Step 2 — Check for detachable components:</strong> Remove all labels, ribbons, plastic eyes, and loose threads before giving any toy to your dog. If parts cannot be removed safely, choose a different toy.</li>",
            "<li><strong>Step 3 — Inspect daily for wear:</strong> Run your fingers over the entire toy surface. Feel for cracks, tears, thinning material, or exposed stuffing. Discard immediately if any damage is found.</li>",
            "<li><strong>Step 4 — Check material certifications:</strong> Look for BPA-free, phthalate-free, and non-toxic labels. UK-sold pet toys should comply with relevant safety standards — avoid unlabelled imports.</li>",
            "<li><strong>Step 5 — Know the emergency signs:</strong> If your dog vomits, stops eating, or has difficulty passing stool after playing with a toy, contact your vet immediately. These may indicate swallowed toy fragments.</li>",
        ])
    if 'cleaning' in topics:
        items.extend([
            "<li><strong>Step 1 — Sort toys by material type:</strong> Separate rubber/silicone, fabric/plush, rope, and nylon toys. Each material requires a different cleaning method for effective sanitisation.</li>",
            "<li><strong>Step 2 — Clean rubber toys weekly:</strong> Soak in warm water with pet-safe soap for 15 minutes, scrub with a bottle brush, rinse thoroughly, and air dry completely before returning to your dog.</li>",
            "<li><strong>Step 3 — Machine-wash fabric toys fortnightly:</strong> Use a gentle cycle at 30°C with pet-safe detergent. Place small toys in a mesh laundry bag. Tumble dry on low or air dry completely.</li>",
            "<li><strong>Step 4 — Sanitise rope toys monthly:</strong> Soak in a solution of 1 part white vinegar to 3 parts warm water for 30 minutes. Rinse thoroughly and hang to dry completely — damp rope breeds bacteria rapidly.</li>",
            "<li><strong>Step 5 — Deep-clean treat-dispensing toys after each use:</strong> Use a bottle brush or pipe cleaner to reach internal grooves. Soak in warm soapy water for 10 minutes, then rinse until no residue remains.</li>",
        ])
    if 'environment' in topics:
        items.extend([
            "<li><strong>Step 1 — Audit your indoor play space:</strong> Clear a 2m × 2m area minimum, remove breakable items, cover hard floor edges with mats. Indoor toys should be soft or lightweight to prevent property damage.</li>",
            "<li><strong>Step 2 — Choose indoor-appropriate toys:</strong> Soft plush toys (£5–12), puzzle feeders (£10–20), and snuffle mats (£8–15) work well indoors. Avoid hard balls and fetch toys that bounce unpredictably.</li>",
            "<li><strong>Step 3 — Select outdoor toys by surface type:</strong> For grass: rubber balls (£4–8), frisbees (£6–12). For hard surfaces: softer foam balls to protect joints. For water: floating toys rated for aquatic use (£8–15).</li>",
            "<li><strong>Step 4 — Inspect outdoor toys after each session:</strong> Check for mud, grit embedded in material, and damage from outdoor surfaces. Clean before bringing indoors to prevent bacteria transfer.</li>",
        ])
    if 'diy' in topics:
        items.extend([
            "<li><strong>Step 1 — Choose safe base materials:</strong> Use old cotton t-shirts (not synthetic), untreated natural rope (cotton or hemp), and food-grade silicone moulds. Never use materials with buttons, zips, or chemical treatments.</li>",
            "<li><strong>Step 2 — Make a basic braided tug toy:</strong> Cut 3 strips of cotton fabric, each 60cm × 5cm. Knot one end, braid tightly, and secure with another knot. Total cost: free from old clothing. Replace when fraying begins.</li>",
            "<li><strong>Step 3 — Create a frozen treat puzzle:</strong> Fill a cleaned empty yoghurt pot with a mixture of mashed banana, dog-safe peanut butter, and kibble. Freeze for 4–6 hours. Supervise use and discard the container after.</li>",
            "<li><strong>Step 4 — Build a snuffle mat from fleece strips:</strong> Cut fleece into 15cm × 3cm strips. Tie strips through a rubber sink mat grid. Hide kibble between strips. Materials cost approximately £4–6 from fabric shops.</li>",
            "<li><strong>Step 5 — Safety-check all DIY toys before use:</strong> Ensure no loose threads longer than 3cm, no small detachable parts, and no sharp edges. Supervise all play with homemade toys and discard at first sign of deterioration.</li>",
        ])
    if 'playstyle' in topics:
        items.extend([
            "<li><strong>Step 1 — Observe your dog’s natural play behaviour for 1 week:</strong> Note whether they prefer chewing, fetching, tugging, shaking, or nosework. Most dogs have 1–2 dominant play styles that guide toy selection.</li>",
            "<li><strong>Step 2 — Match toys to play style:</strong> Fetchers: balls and frisbees (£4–12). Tuggers: rope toys and tug rings (£6–15). Chewers: solid rubber and nylon (£8–20). Noseworkers: snuffle mats and puzzle feeders (£8–25).</li>",
            "<li><strong>Step 3 — Provide at least 3 toy types:</strong> Even dogs with a strong preference benefit from variety. Include one chew toy, one interactive toy, and one comfort toy as a baseline collection.</li>",
            "<li><strong>Step 4 — Adjust for breed tendencies:</strong> Retrievers typically prefer fetch toys. Terriers enjoy tug and shake toys. Working breeds (Collies, Shepherds) excel with puzzle and problem-solving toys. Sight hounds prefer chase toys.</li>",
        ])

    # Ensure minimum 8 items — add universal items if needed
    universal = [
        "<li><strong>Measure before buying:</strong> Ball diameter should be at least 1.5× your dog’s mouth width to prevent choking. For medium breeds (15–25kg), this typically means balls of 6.5cm diameter or larger.</li>",
        "<li><strong>Budget guide for a starter toy collection:</strong> Puzzle toys: £8–15. Durable chew toys: £10–25. Interactive fetch toys: £5–12. Comfort plush toys: £4–10. Total starter set: approximately £30–60.</li>",
        "<li><strong>Breed-specific safety considerations:</strong> Brachycephalic breeds (Pugs, Bulldogs): avoid small balls they cannot grip safely. Staffies and Bull Terriers: thick rubber only, rated for power chewers. Toy breeds (Chihuahuas, Yorkies): ensure toys are proportionally small enough to carry but too large to swallow.</li>",
        "<li><strong>Replacement timeline:</strong> Rubber toys: every 3–6 months. Rope toys: every 2–4 months or when fraying. Plush toys: every 1–3 months for heavy users. Nylon chews: every 6–12 months depending on wear.</li>",
        "<li><strong>Storage and hygiene routine:</strong> Keep a dedicated toy box or basket. Wash all toys at least fortnightly. Rotate 3–4 toys at a time, storing the rest. Inspect the entire collection monthly and discard worn items.</li>",
        "<li><strong>Seasonal toy adjustments:</strong> Summer: frozen stuffable toys, water-safe floating toys. Winter: indoor puzzle feeders, snuffle mats. Adjust fetch activities for ground conditions — avoid hard-frozen ground for ball play.</li>",
    ]

    while len(items) < 8:
        for u in universal:
            if u not in items:
                items.append(u)
                if len(items) >= 8:
                    break

    return items[:12]


def get_practical_guide_harness(topics, title):
    """Generate practical guide for Dog Harness posts."""
    items = []
    t = title.lower()

    if any(w in t for w in ['measure', 'fitting', 'fit', 'size']):
        items.extend([
            "<li><strong>Step 1 — Gather your measuring tools:</strong> Use a soft fabric tape measure (not metal). If unavailable, use a piece of string and measure it against a ruler afterwards. Measure when your dog is standing naturally, not sitting.</li>",
            "<li><strong>Step 2 — Measure the chest girth:</strong> Wrap the tape around the widest part of your dog’s ribcage, just behind the front legs. For most breeds, this is 5–10cm behind the armpits. Note the measurement in centimetres.</li>",
            "<li><strong>Step 3 — Measure the neck circumference:</strong> Place the tape where a collar would naturally sit, at the base of the neck. Add 2–3cm for comfort. This measurement helps with harnesses that have a neck loop.</li>",
            "<li><strong>Step 4 — Apply the two-finger rule:</strong> Once fitted, you should be able to slide two flat fingers between the harness and your dog’s body at any strap point. Tighter restricts movement; looser allows escape.</li>",
            "<li><strong>Step 5 — Check for chafing points:</strong> After the first 15-minute walk, remove the harness and check the armpits, chest, and behind the front legs for redness or rubbing. Adjust strap positions if needed.</li>",
            "<li><strong>Step 6 — Remeasure every 3 months:</strong> Puppies grow rapidly and even adult dogs’ weight fluctuates. Remeasure seasonally and after any significant weight change (gain or loss of more than 1kg).</li>",
        ])

    if any(w in t for w in ['no-pull', 'training', 'pull']):
        items.extend([
            "<li><strong>Step 1 — Identify your dog’s pulling pattern:</strong> Does your dog pull constantly, only when excited (seeing other dogs), or in specific environments? This determines whether you need a front-clip, dual-clip, or head halter style (£15–35).</li>",
            "<li><strong>Step 2 — Introduce the harness gradually:</strong> Day 1–2: let your dog sniff and investigate. Day 3–4: drape over back with treats. Day 5–7: buckle loosely indoors for 5–10 minutes. Day 8+: first outdoor walk.</li>",
            "<li><strong>Step 3 — Practise stop-start walking indoors first:</strong> Walk 3–4 steps, stop when the lead goes taut. Wait for your dog to look back or release tension. Reward and continue. Repeat 10–15 times per session.</li>",
            "<li><strong>Step 4 — Use the front clip attachment first:</strong> Front-clip harnesses redirect pulling energy sideways, making it physically harder to pull forward. Switch to back-clip only once loose-lead walking is consistent.</li>",
            "<li><strong>Step 5 — Pair with positive reinforcement:</strong> Reward every few steps of loose-lead walking with small treats (£3–8 per 100g training treats). Gradually increase the distance between rewards over 2–4 weeks.</li>",
        ])

    if any(w in t for w in ['type', 'explained', 'complete guide', 'collar']):
        items.extend([
            "<li><strong>Step 1 — Determine your primary use case:</strong> Daily walking: Y-shaped or H-shaped harness (£15–30). Running or hiking: padded sport harness (£25–45). Training: front-clip or dual-clip harness (£18–35). Car travel: crash-tested harness (£20–40).</li>",
            "<li><strong>Step 2 — Consider your dog’s body shape:</strong> Barrel-chested breeds (Bulldogs, Pugs): avoid step-in styles that press on the trachea. Deep-chested breeds (Greyhounds, Whippets): use figure-8 or custom-fitted styles. Standard builds: most harness types work well.</li>",
            "<li><strong>Step 3 — Check strap width for comfort:</strong> Minimum 2cm width for small dogs (under 10kg), 2.5–3cm for medium dogs (10–25kg), 3–4cm for large dogs (25kg+). Wider straps distribute pressure more evenly.</li>",
            "<li><strong>Step 4 — Test range of motion:</strong> With the harness on, your dog should be able to walk, trot, sit, and lie down without restriction. The front leg movement should be completely unimpeded — watch for shortened stride.</li>",
            "<li><strong>Step 5 — Check attachment point security:</strong> D-rings should be welded (not split rings). Buckles should be side-release with a double-lock mechanism. Test by pulling firmly — nothing should pop open or bend.</li>",
        ])

    # Universal harness items
    universal = [
        "<li><strong>Fitting timeline for puppies:</strong> Puppies need harness size reassessment every 2–4 weeks until 6 months, then monthly until fully grown (12–18 months depending on breed). Budget for 2–3 harness sizes during the first year (£15–30 each).</li>",
        "<li><strong>Material selection guide:</strong> Nylon webbing: durable, affordable (£10–20), dries quickly. Padded mesh: breathable, best for summer (£15–30). Leather: long-lasting, moulds to body shape over time (£25–50). Neoprene-lined: waterproof, ideal for wet UK conditions (£20–35).</li>",
        "<li><strong>Daily pre-walk harness check (30 seconds):</strong> Check all buckles click securely. Run your fingers under every strap for the two-finger gap. Inspect stitching at stress points (D-ring attachment, buckle junctions). Check for fraying on edges.</li>",
        "<li><strong>Washing and maintenance schedule:</strong> Hand wash monthly in lukewarm water with mild soap. Rinse thoroughly — soap residue causes skin irritation. Air dry completely before reuse (12–24 hours). Check hardware for rust or corrosion quarterly.</li>",
        "<li><strong>Breed-specific harness recommendations:</strong> Greyhounds/Whippets: Martingale-style or custom sighthound harness to prevent escape. Pugs/Bulldogs: step-through style with chest padding, never neck-pressure designs. German Shepherds/Labradors: padded Y-front with dual clip points.</li>",
        "<li><strong>When to replace your harness:</strong> Replace if stitching is fraying, buckles no longer click firmly, webbing is thinning or has cuts, padding is compressed flat, or reflective elements are peeling. Typical lifespan: 12–24 months with daily use.</li>",
        "<li><strong>Cost planning:</strong> Budget harness (nylon, basic): £8–15. Mid-range padded harness: £15–30. Premium sport/training harness: £30–50. Expect to spend £50–100 over a dog’s first year including size upgrades.</li>",
        "<li><strong>Safety check for escape-prone dogs:</strong> Test by gently pulling the harness upward and backward. If it slides over the head, tighten the neck strap or switch to a three-point harness with a belly strap. Houdini dogs need dual-buckle security harnesses.</li>",
    ]

    while len(items) < 8:
        for u in universal:
            if u not in items:
                items.append(u)
                if len(items) >= 8:
                    break

    return items[:12]


def get_practical_guide_supplies(topics, title):
    """Generate practical guide for Dog Supplies posts."""
    items = []

    if 'bowls' in topics or 'hydration' in topics:
        items.extend([
            "<li><strong>Step 1 — Choose bowl material by your dog’s needs:</strong> Stainless steel: most hygienic, dishwasher-safe (£4–12). Ceramic: heavy, non-slip, good for speed eaters (£8–18). Silicone collapsible: ideal for travel (£3–8). Avoid plastic — it harbours bacteria in scratches.</li>",
            "<li><strong>Step 2 — Size the bowl correctly:</strong> The bowl should hold 1.5× your dog’s meal portion to prevent spillage. Small dogs (under 10kg): 300–500ml. Medium dogs (10–25kg): 500ml–1L. Large dogs (25kg+): 1–2L capacity.</li>",
            "<li><strong>Step 3 — Position at the correct height:</strong> Standard floor bowls suit most dogs. Elevated bowls (10–30cm raised) benefit senior dogs, dogs with arthritis, or breeds prone to neck strain. Measure from floor to your dog’s lower chest for ideal height.</li>",
            "<li><strong>Step 4 — Implement a daily cleaning routine:</strong> Wash food bowls after every meal with hot soapy water. Wash water bowls daily and refill with fresh water. Deep sanitise weekly by soaking in a solution of 1 tablespoon white vinegar per litre of water.</li>",
            "<li><strong>Step 5 — Monitor water intake:</strong> Dogs need approximately 50–70ml of water per kilogram of body weight daily. A 20kg dog needs 1–1.4 litres. Increase by 50% during hot weather or after vigorous exercise.</li>",
        ])

    if 'collars_leads' in topics:
        items.extend([
            "<li><strong>Step 1 — Measure for a collar:</strong> Wrap a tape measure around your dog’s neck at the collar’s natural resting point. Add 5cm for comfort. The finished collar should allow two fingers to slide flat between collar and neck.</li>",
            "<li><strong>Step 2 — Choose the right collar width:</strong> Small dogs (under 10kg): 1–1.5cm width. Medium dogs (10–25kg): 2–2.5cm. Large dogs (25kg+): 3–4cm. Wider collars distribute pressure better and are more comfortable for strong dogs.</li>",
            "<li><strong>Step 3 — Select lead length by activity:</strong> Short training leads: 1–1.2m (£5–10). Standard walking leads: 1.5–2m (£8–15). Long training lines: 5–10m (£10–20). Retractable leads: not recommended near roads due to limited control.</li>",
            "<li><strong>Step 4 — Check collar fit weekly:</strong> Weight changes, coat growth, and wear affect fit. Run the two-finger check regularly. For puppies, check every 3–5 days as they grow rapidly.</li>",
            "<li><strong>Step 5 — Attach ID tags securely:</strong> UK law requires dogs to wear a tag with the owner’s name and address when in public. Use a split ring (not an S-hook) for secure attachment. Check tag legibility monthly.</li>",
        ])

    if 'beds' in topics:
        items.extend([
            "<li><strong>Step 1 — Measure your dog for a bed:</strong> Measure from nose to tail base with your dog in their natural sleeping position. Add 15–20cm for small–medium dogs, 20–30cm for large dogs. This ensures enough room to stretch comfortably.</li>",
            "<li><strong>Step 2 — Match bed type to sleeping style:</strong> Curlers: bolster or donut beds with raised edges (£15–35). Sprawlers: flat mat or mattress-style beds (£20–45). Burrowers: cave or hooded beds (£18–40). Leaners: beds with one firm side for back support.</li>",
            "<li><strong>Step 3 — Choose filling by health needs:</strong> Memory foam: for senior dogs or those with joint issues (£30–60). Polyester fibre: budget-friendly, good for healthy adults (£15–30). Orthopaedic foam: for post-surgery recovery or arthritis (£40–80). Cooling gel: for breeds prone to overheating (£25–50).</li>",
            "<li><strong>Step 4 — Place the bed in an optimal location:</strong> Choose a quiet corner away from draughts and direct heat sources. Keep at least 30cm from radiators. Avoid high-traffic areas. Many dogs prefer a spot where they can see the main room entrance.</li>",
            "<li><strong>Step 5 — Wash bedding fortnightly:</strong> Remove covers and machine wash at 30–40°C with pet-safe detergent. Vacuum the bed base weekly. Replace the entire bed when filling becomes permanently compressed (typically every 1–2 years).</li>",
        ])

    if 'grooming' in topics:
        items.extend([
            "<li><strong>Step 1 — Identify your dog’s coat type:</strong> Smooth/short coat: weekly brushing with a rubber curry brush (£4–8). Double coat: 2–3 times weekly with an undercoat rake (£8–15). Long/silky coat: daily brushing with a pin brush (£6–12). Wire coat: hand-stripping or weekly slicker brush (£6–10).</li>",
            "<li><strong>Step 2 — Establish a bathing schedule:</strong> Most dogs need bathing every 4–8 weeks. Use lukewarm water (around 37°C). Apply dog-specific shampoo (£5–15), lather for 2–3 minutes, rinse thoroughly. Never use human shampoo — the pH is wrong for canine skin.</li>",
            "<li><strong>Step 3 — Trim nails every 3–4 weeks:</strong> Use guillotine-style clippers for small dogs (£5–8) or plier-style for larger breeds (£8–15). Cut 1–2mm at a time, staying well clear of the quick. If nails click on hard floors, they are overdue.</li>",
            "<li><strong>Step 4 — Check ears weekly:</strong> Lift the ear flap and inspect for redness, discharge, or unusual odour. Clean the outer ear with a damp cotton pad — never insert anything into the ear canal. Floppy-eared breeds need more frequent checks.</li>",
            "<li><strong>Step 5 — Brush teeth 3–5 times per week:</strong> Use a dog-specific toothbrush and enzymatic toothpaste (£4–10). Start by letting your dog lick the paste, then progress to brushing in circular motions for 30–60 seconds per side.</li>",
        ])

    if 'training' in topics:
        items.extend([
            "<li><strong>Step 1 — Choose treats by training context:</strong> Low-value (daily practice): small kibble pieces or dry training treats (£3–6 per pack). Medium-value (new commands): soft semi-moist treats (£4–8). High-value (distracting environments): real meat, cheese, or liver paste (£5–12).</li>",
            "<li><strong>Step 2 — Size treats correctly:</strong> Training treats should be pea-sized (approximately 1cm) for medium dogs, smaller for toy breeds. You may need 30–50 treats per 10-minute training session — small size prevents overfeeding.</li>",
            "<li><strong>Step 3 — Reduce treat calories from meals:</strong> Training treats should not exceed 10% of daily calorie intake. If training heavily, reduce the next meal portion accordingly. For a 15kg dog, that is approximately 30–40 calories in treats.</li>",
            "<li><strong>Step 4 — Time your reward within 1–2 seconds:</strong> The treat must arrive within 2 seconds of the desired behaviour for your dog to make the association. Use a marker word (“yes”) or clicker (£2–4) to bridge the gap.</li>",
        ])

    if 'health' in topics:
        items.extend([
            "<li><strong>Step 1 — Schedule routine health checks:</strong> Puppies: vet visits at 8, 12, and 16 weeks for vaccinations (£100–200 total). Adults: annual check-up (£40–80). Seniors (7+ years): twice-yearly wellness checks (£80–160 per year).</li>",
            "<li><strong>Step 2 — Establish a dental care routine:</strong> Brush teeth daily if possible, minimum 3 times weekly. Dental chews (£4–8 per pack) provide supplementary cleaning. Schedule professional dental cleaning every 1–2 years (£200–400 under anaesthetic).</li>",
            "<li><strong>Step 3 — Maintain a flea and worming schedule:</strong> Flea treatment monthly (£5–15 per dose). Worming every 3 months for adults (£3–8 per treatment). Puppies need worming every 2 weeks until 12 weeks old, then monthly until 6 months.</li>",
            "<li><strong>Step 4 — Monitor joint health proactively:</strong> For breeds prone to joint issues (Labradors, German Shepherds, large breeds), start joint supplements from age 5–6 (£10–25 per month). Watch for stiffness after rest, reluctance to jump, or shortened stride.</li>",
            "<li><strong>Step 5 — Build a pet first aid kit (£15–30):</strong> Include: conforming bandages, non-stick wound pads, saline eye wash, tweezers, blunt-ended scissors, digital thermometer, antiseptic wipes, and your vet’s emergency number.</li>",
        ])

    if 'food' in topics:
        items.extend([
            "<li><strong>Step 1 — Calculate daily feeding amount:</strong> Follow the manufacturer’s guide as a starting point, based on your dog’s weight. Adjust by body condition: if ribs are easily felt with slight covering, the amount is correct. Reduce by 10% if overweight; increase if underweight.</li>",
            "<li><strong>Step 2 — Choose between wet and dry food:</strong> Dry kibble: more economical (£20–50 per month for a medium dog), better for dental health. Wet food: higher moisture content, often more palatable (£40–80 per month). Many owners mix both for balance.</li>",
            "<li><strong>Step 3 — Read ingredient labels correctly:</strong> The first ingredient should be a named meat source (e.g., “chicken” not “meat derivatives”). Minimum 25–30% protein for adults. Avoid artificial colourings, BHA/BHT preservatives, and excessive grain fillers.</li>",
            "<li><strong>Step 4 — Transition foods gradually over 7–10 days:</strong> Days 1–3: 75% old food, 25% new. Days 4–6: 50/50 mix. Days 7–9: 25% old, 75% new. Day 10: 100% new food. This prevents digestive upset.</li>",
            "<li><strong>Step 5 — Establish consistent feeding times:</strong> Feed adult dogs twice daily at the same times (e.g., 7am and 6pm). Puppies under 6 months: three meals daily. Remove uneaten wet food after 20 minutes to prevent spoilage.</li>",
        ])

    if 'seasonal' in topics:
        items.extend([
            "<li><strong>Step 1 — Summer preparation (April–September):</strong> Provide constant fresh water access. Walk during cooler hours (before 9am, after 7pm). Test pavement with your palm — if too hot for 5 seconds, it burns paws. Consider a cooling mat (£10–25).</li>",
            "<li><strong>Step 2 — Winter preparation (October–March):</strong> Dry your dog thoroughly after wet walks. Consider a waterproof coat for short-coated breeds (£12–30). Apply paw balm before walks on salted paths (£5–8). Check paw pads for ice ball build-up.</li>",
            "<li><strong>Step 3 — Adjust food portions seasonally:</strong> Active outdoor dogs may need 10–15% more calories in winter. Reduce portions in summer if activity decreases. Monitor body condition monthly and adjust accordingly.</li>",
            "<li><strong>Step 4 — Update flea and tick prevention:</strong> Tick activity peaks March–October in the UK. Use a tick prevention treatment during these months (£8–15 per dose). Check your dog’s coat after every countryside walk, focusing on ears, armpits, and groin.</li>",
        ])

    if 'puppy_general' in topics:
        items.extend([
            "<li><strong>Step 1 — Prepare your home before arrival:</strong> Puppy-proof one room: cover electrical cables, remove toxic plants, secure bin lids. Set up a crate or pen area (£25–60) with a bed, water bowl, and toilet pads. Budget £200–400 for initial supplies.</li>",
            "<li><strong>Step 2 — Establish a routine from day one:</strong> Set fixed times for meals, toilet breaks, play, and sleep. Puppies thrive on predictability. Take outside for toileting every 1–2 hours during the day and immediately after meals, naps, and play.</li>",
            "<li><strong>Step 3 — Begin socialisation within the first 16 weeks:</strong> Expose your puppy to 3–5 new experiences daily: different surfaces, sounds, people, and once vaccinated, other dogs. Keep sessions positive and brief (5–10 minutes).</li>",
            "<li><strong>Step 4 — Register with a vet within the first week:</strong> Book initial health check (£30–50), vaccinations (£100–200 for primary course), and microchipping if not already done (£15–25). Discuss neutering timeline with your vet.</li>",
            "<li><strong>Step 5 — Budget for the first year:</strong> Food: £300–600. Vet care (vaccinations, neutering): £300–500. Insurance: £200–500. Supplies (bed, crate, bowls, toys, leads): £200–400. Total first year: approximately £1,000–2,000.</li>",
        ])

    if 'glossary' in topics:
        items.extend([
            "<li><strong>Step 1 — Use this glossary as a reference when shopping:</strong> Before purchasing any product, cross-reference the terminology on the label with the definitions provided. Understanding terms like “hydrolysed protein” or “orthopaedic foam” helps you make informed choices.</li>",
            "<li><strong>Step 2 — Check ingredient lists against the glossary:</strong> When comparing products, use the terminology guide to identify marketing language versus meaningful claims. “Natural” is unregulated, but “complete food” has a legal definition in the UK.</li>",
            "<li><strong>Step 3 — Discuss terms with your vet:</strong> If a product label uses medical or nutritional terms you are unsure about, note them down and discuss at your next vet appointment. This is especially important for supplements and medicated products.</li>",
            "<li><strong>Step 4 — Bookmark for ongoing reference:</strong> Pet product terminology evolves as new materials and formulations enter the market. Return to this guide periodically when encountering unfamiliar terms on new products.</li>",
        ])

    # Universal supply items
    universal = [
        "<li><strong>Budget planning for essential supplies:</strong> Starter kit (bowls, collar, lead, bed, toys): £60–120. Monthly ongoing costs (food, treats, flea treatment): £40–80. Annual vet care: £200–400. Pet insurance: £15–40 per month.</li>",
        "<li><strong>Product quality indicators:</strong> Look for double-stitched seams, welded (not split) metal rings, BPA-free certifications, and clear manufacturer contact details on packaging. Avoid products with no identifiable brand or safety information.</li>",
        "<li><strong>UK consumer protections:</strong> Pet products sold in the UK must meet relevant safety standards. If a product causes harm, you have rights under the Consumer Rights Act 2015. Keep receipts and photograph any product defects.</li>",
        "<li><strong>Cleaning and maintenance schedule:</strong> Daily: wash food bowls, check collar fit. Weekly: wash water bowl, inspect toys, check harness stitching. Monthly: deep-clean bed, wash harness, check all equipment for wear. Quarterly: audit entire supply inventory.</li>",
        "<li><strong>Storage tips:</strong> Store dry food in an airtight container, not the original bag. Keep treats sealed after opening. Store leather products away from moisture. Keep grooming tools clean and dry between uses.</li>",
        "<li><strong>Sustainable choices:</strong> Choose durable products that last longer over disposable alternatives. Look for recycled materials, natural fibres, and brands with take-back schemes. Quality products cost more initially but reduce long-term waste and spending.</li>",
    ]

    while len(items) < 8:
        for u in universal:
            if u not in items:
                items.append(u)
                if len(items) >= 8:
                    break

    return items[:12]


# ── Decision Pathway Content (Phase 10BL) ──────────────────────────────────

def get_decision_pathway_toys(topics, title):
    """Decision pathway for Dog Toys posts."""
    paths = []

    if 'enrichment' in topics or 'general' in topics or 'faq' in topics:
        paths.extend([
            "<li><strong>If your dog loses interest in toys quickly →</strong> Rotate 3–4 toys weekly and store the rest. Introduce puzzle feeders (£10–20) that dispense treats to maintain engagement through food motivation.</li>",
            "<li><strong>If you want to keep your dog occupied while you work from home →</strong> Frozen stuffable toys (fill and freeze overnight) provide 20–40 minutes of quiet engagement. Snuffle mats (£8–15) are another hands-off option.</li>",
        ])
    if 'chewer' in topics:
        paths.extend([
            "<li><strong>If your dog destroys every toy within hours →</strong> Switch to solid rubber or nylon toys rated for aggressive chewers (£12–25). Avoid plush, rope, and thin plastic entirely. The higher upfront cost prevents repeated replacements and potential vet bills.</li>",
            "<li><strong>If your dog chews furniture or shoes instead of toys →</strong> Provide high-value chew alternatives immediately: frozen stuffed rubber toys, thick rubber bones (£8–15). Redirect chewing within 2 seconds and reward engagement with appropriate toys.</li>",
        ])
    if 'puppy' in topics:
        paths.extend([
            "<li><strong>If your puppy is under 12 weeks →</strong> Start with soft fabric toys and lightweight rubber toys (£4–8). Avoid hard materials that could damage developing teeth. Supervise all play sessions and limit to 10 minutes.</li>",
            "<li><strong>If your puppy is actively teething (12–24 weeks) →</strong> Prioritise textured rubber teething toys that can be chilled in the fridge (£6–12). The cold soothes inflamed gums. Offer 2–3 options and note which textures your puppy prefers.</li>",
        ])
    if 'safety' in topics:
        paths.extend([
            "<li><strong>If you need toys safe for unsupervised play →</strong> Choose solid one-piece rubber toys with no detachable parts (£8–15). Avoid toys with squeakers, stuffing, rope, or small components. Size up rather than down.</li>",
            "<li><strong>If you are concerned about toxic materials →</strong> Look for BPA-free, phthalate-free, and EU-compliant certifications on packaging. Natural rubber is generally safer than PVC. Budget £10–20 per toy for certified options.</li>",
        ])

    # Universal decision paths
    universal = [
        "<li><strong>If you have a multi-dog household with different sizes →</strong> Buy size-appropriate toys for each dog individually. A toy safe for a Labrador can be a choking hazard for a Chihuahua. Store each dog’s toys separately and supervise shared play.</li>",
        "<li><strong>If your budget is limited (under £20 total) →</strong> Prioritise one durable rubber chew toy (£8–12) and one puzzle feeder (£8–15). These cover both physical and mental stimulation. Supplement with safe DIY options from household items.</li>",
        "<li><strong>If your dog is elderly or has dental issues →</strong> Choose softer rubber toys, fabric toys, or lick mats (£6–12). Avoid hard nylon, antlers, and bones. Frozen mashed banana in a rubber toy provides gentle enrichment without dental strain.</li>",
        "<li><strong>If your dog prefers fetch over chewing →</strong> Invest in a durable rubber ball (£4–8) sized correctly for your dog. For water play, choose floating toys (£6–12). Tennis balls are acceptable for short sessions but wear teeth with prolonged use.</li>",
        "<li><strong>If you want toys that also clean teeth →</strong> Textured rubber toys with ridges and grooves help remove plaque during chewing (£8–18). They are not a replacement for brushing but provide supplementary dental benefits.</li>",
        "<li><strong>If your dog shows resource guarding with toys →</strong> Work with a qualified behaviourist before introducing new toys. Start with low-value items and practise structured swap games. Never forcibly remove a toy from a guarding dog.</li>",
    ]

    while len(paths) < 4:
        for u in universal:
            if u not in paths:
                paths.append(u)
                if len(paths) >= 4:
                    break

    return paths[:6]


def get_decision_pathway_harness(topics, title):
    """Decision pathway for Dog Harness posts."""
    paths = []

    paths.extend([
        "<li><strong>If your dog pulls constantly on walks →</strong> A front-clip harness (£18–30) redirects forward motion sideways, making pulling physically harder. Combine with stop-start training for results within 2–4 weeks.</li>",
        "<li><strong>If you have a brachycephalic breed (Pug, Bulldog, French Bulldog) →</strong> Always use a harness rather than a collar. Choose a Y-shaped design that distributes pressure across the chest, never the throat. Padded options (£20–35) prevent chafing around the face folds.</li>",
        "<li><strong>If your dog is an escape artist →</strong> Choose a three-point harness with neck, chest, and belly straps (£25–40). Dual buckles and a snug fit are essential. Some sighthound-specific harnesses include an extra belly panel for escape-prone breeds.</li>",
        "<li><strong>If you run or hike with your dog →</strong> A padded sport harness with a back-clip attachment (£25–45) allows full range of motion. Choose breathable mesh for warm weather, waterproof nylon for wet conditions. Reflective strips are essential for low-light visibility.</li>",
        "<li><strong>If you need a car travel harness →</strong> Choose a crash-tested harness that attaches to the seatbelt system (£20–40). Uncertified “car harnesses” may not provide meaningful protection. Check for independent crash test results before purchasing.</li>",
        "<li><strong>If your puppy is still growing →</strong> Buy an adjustable harness with multiple size settings rather than a fixed-size option. Expect to resize every 2–4 weeks. Budget-friendly adjustable harnesses (£12–20) save money during the rapid growth phase.</li>",
    ])
    return paths[:6]


def get_decision_pathway_supplies(topics, title):
    """Decision pathway for Dog Supplies posts."""
    paths = []

    if 'bowls' in topics or 'hydration' in topics:
        paths.extend([
            "<li><strong>If your dog eats too quickly →</strong> A slow feeder bowl with internal ridges or maze patterns (£8–18) can extend meal times from 30 seconds to 5–10 minutes, reducing bloat risk and improving digestion.</li>",
            "<li><strong>If your senior dog has neck or joint pain →</strong> An elevated bowl stand at lower-chest height (£12–25) reduces strain when eating and drinking. Combine with a non-slip mat to prevent the stand from sliding on hard floors.</li>",
            "<li><strong>If you travel frequently with your dog →</strong> A collapsible silicone bowl (£3–8) clips to your bag and weighs almost nothing. Pair with a portable water bottle with built-in bowl (£8–15) for walks and car journeys.</li>",
        ])
    if 'collars_leads' in topics:
        paths.extend([
            "<li><strong>If your dog has sensitive skin or allergies →</strong> Choose a padded neoprene or leather collar (£12–25) rather than rough nylon. Avoid collars with metal components that touch the skin directly, as some dogs react to nickel.</li>",
            "<li><strong>If you walk in low-light conditions →</strong> A reflective or LED collar (£8–18) and reflective lead (£10–15) significantly improve visibility. USB-rechargeable LED options are more economical than battery-powered alternatives.</li>",
            "<li><strong>If you are training recall →</strong> A long training line (5–10m, £10–20) gives your dog freedom to practise recall while maintaining safety. Never use retractable leads for recall training as they teach pulling rather than returning.</li>",
        ])
    if 'beds' in topics:
        paths.extend([
            "<li><strong>If your dog has arthritis or joint issues →</strong> An orthopaedic memory foam bed (£40–80) provides targeted pressure relief. Choose at least 10cm foam depth. A removable, washable cover is essential for hygiene.</li>",
            "<li><strong>If your dog overheats easily →</strong> A cooling gel mat (£10–25) or elevated mesh bed (£20–40) allows air circulation underneath. These are particularly important for brachycephalic breeds and heavy-coated dogs during UK summers.</li>",
            "<li><strong>If you are crate training a puppy →</strong> Choose a flat, washable mat (£10–18) rather than a thick bed for the first 6 months. Puppies may chew bedding — avoid stuffed beds until the chewing phase passes.</li>",
        ])
    if 'grooming' in topics:
        paths.extend([
            "<li><strong>If your dog has a thick double coat →</strong> Invest in an undercoat rake (£8–15) and a slicker brush (£6–10). Brush 2–3 times weekly to prevent matting. During spring and autumn shedding seasons, daily brushing may be needed.</li>",
            "<li><strong>If your dog hates being groomed →</strong> Start with 30-second sessions paired with high-value treats. Gradually increase duration over 2–4 weeks. Use a soft rubber curry brush (£4–8) initially as it feels more like a massage than brushing.</li>",
        ])
    if 'training' in topics:
        paths.extend([
            "<li><strong>If your dog is not food-motivated →</strong> Try different treat types: freeze-dried liver, cheese, or cooked chicken often work when commercial treats fail. Alternatively, use a favourite toy as the reward instead of food.</li>",
            "<li><strong>If you are training a reactive dog →</strong> Use extra-high-value treats (real meat, £5–10 per pack) and work at a distance where your dog notices the trigger but does not react. Gradually decrease distance over weeks, not days.</li>",
        ])
    if 'health' in topics:
        paths.extend([
            "<li><strong>If your dog has dental disease →</strong> Start with enzymatic toothpaste (£4–8) applied with a finger brush for dogs who resist bristle brushes. Add dental water additives (£5–10) as supplementary protection. Discuss professional cleaning with your vet.</li>",
            "<li><strong>If you cannot afford regular vet visits →</strong> Look into PDSA or Blue Cross charitable clinics which offer reduced-cost care. Pet insurance (£15–40/month) spreads unexpected costs. Always prioritise vaccinations and parasite prevention.</li>",
        ])
    if 'food' in topics:
        paths.extend([
            "<li><strong>If your dog has a sensitive stomach →</strong> Choose a limited-ingredient diet with a single protein source (£25–50 per month). Transition very gradually over 10–14 days rather than the standard 7. Keep a food diary to identify triggers.</li>",
            "<li><strong>If you are unsure about raw feeding →</strong> Raw feeding requires careful nutritional balancing and strict hygiene. If interested, start with commercially prepared raw meals (£50–100 per month) rather than DIY, and discuss with your vet first.</li>",
        ])

    universal = [
        "<li><strong>If you are a first-time dog owner →</strong> Start with essential basics: stainless steel bowls (£8–15), a nylon collar with ID tag (£8–12), a 1.5m lead (£8–15), a basic bed (£15–30), and 2–3 toys. Total starter kit: approximately £60–100.</li>",
        "<li><strong>If you want to reduce ongoing costs →</strong> Buy quality products that last rather than cheap replacements. Bulk-buy food when on offer and store in airtight containers. Groom at home between professional sessions. Compare pet insurance annually.</li>",
        "<li><strong>If your dog has specific breed-related needs →</strong> Research your breed’s common health conditions and invest in preventative supplies. For example, breeds prone to hip dysplasia benefit from orthopaedic beds; flat-faced breeds need harnesses rather than collars.</li>",
    ]

    while len(paths) < 4:
        for u in universal:
            if u not in paths:
                paths.append(u)
                if len(paths) >= 4:
                    break

    return paths[:6]


# ── Comparison Tables (Phase 10BN) ──────────────────────────────────────────

COMPARISON_TABLES = {
    # Dog Toys tables
    'toy_material_durability': {
        'title': 'Dog Toy Material Durability Comparison',
        'headers': ['Material', 'Durability', 'Suitable For', 'Typical UK Price', 'Key Consideration'],
        'rows': [
            ['Natural rubber', 'High', 'Power chewers, fetch, solo play', '£8–20', 'Non-toxic, flexible, check for latex allergies'],
            ['Nylon', 'Very high', 'Aggressive chewers, unsupervised play', '£10–25', 'Long-lasting but can be too hard for some teeth'],
            ['Cotton rope', 'Moderate', 'Tug games, light chewing, interactive play', '£4–12', 'Fibres can cause intestinal issues if ingested'],
            ['Plush fabric', 'Low', 'Comfort, gentle play, puppies', '£4–10', 'Not suitable for power chewers, check for loose parts'],
            ['TPR (thermoplastic rubber)', 'Moderate–high', 'Fetch, water play, moderate chewers', '£6–15', 'Flexible and lightweight, bounces well'],
            ['Silicone', 'Moderate', 'Treat-dispensing, lick mats, puppies', '£8–18', 'Food-safe, easy to clean, dishwasher-safe options'],
            ['Canvas/cordura', 'Moderate–high', 'Fetch, tug, multi-dog play', '£6–14', 'Tear-resistant but not chew-proof'],
        ],
    },
    'toy_enrichment_types': {
        'title': 'Enrichment Toy Types and Benefits',
        'headers': ['Enrichment Type', 'Mental Effort', 'Engagement Time', 'Typical UK Price', 'Suitable Age'],
        'rows': [
            ['Puzzle feeder (sliding)', 'Moderate–high', '5–20 minutes', '£12–25', 'Adult dogs, 6 months+'],
            ['Snuffle mat', 'Low–moderate', '5–15 minutes', '£8–15', 'All ages, including puppies'],
            ['Stuffable rubber toy', 'Low–moderate', '10–40 minutes (frozen)', '£8–15', 'All ages'],
            ['Lick mat', 'Low', '5–15 minutes', '£6–12', 'All ages, calming effect'],
            ['Treat ball/dispenser', 'Moderate', '10–30 minutes', '£8–18', '4 months+'],
            ['Multi-step puzzle box', 'High', '10–30 minutes', '£18–35', 'Experienced dogs, 12 months+'],
        ],
    },
    'toy_price_by_category': {
        'title': 'Dog Toy Price Guide by Category (UK)',
        'headers': ['Toy Category', 'Budget Option', 'Mid-Range', 'Premium', 'Expected Lifespan'],
        'rows': [
            ['Rubber chew toys', '£5–8', '£8–15', '£15–25', '3–6 months (power chewers)'],
            ['Puzzle feeders', '£8–12', '£12–20', '£20–35', '12–24 months'],
            ['Fetch balls', '£2–4', '£4–8', '£8–15', '1–3 months (outdoor use)'],
            ['Tug toys (rope/rubber)', '£4–8', '£8–15', '£15–22', '2–4 months'],
            ['Plush/comfort toys', '£3–6', '£6–12', '£12–20', '1–3 months'],
            ['Interactive/electronic', '£10–18', '£18–30', '£30–50', '6–12 months'],
            ['Snuffle mats', '£6–10', '£10–18', '£18–28', '6–12 months'],
        ],
    },
    'toy_safety_by_material': {
        'title': 'Dog Toy Safety Considerations by Material',
        'headers': ['Material', 'Choking Risk', 'Toxicity Risk', 'Supervision Needed', 'Key Warning Signs'],
        'rows': [
            ['Natural rubber', 'Low (if correctly sized)', 'Low', 'Moderate', 'Deep cracks, chunks missing, flattening'],
            ['Nylon', 'Low', 'Low', 'Low', 'Sharp edges from wear, splintering'],
            ['Rope (cotton/hemp)', 'Moderate (fibre ingestion)', 'Low', 'High', 'Fraying ends, loose threads, thinning'],
            ['Plush with stuffing', 'High', 'Low–moderate', 'High', 'Exposed stuffing, torn seams, loose eyes'],
            ['PVC/vinyl', 'Low–moderate', 'Moderate (phthalates)', 'Moderate', 'Strong chemical smell, cracking, fading'],
            ['Latex', 'Moderate (tears easily)', 'Low', 'High', 'Thin spots, tear marks, pieces missing'],
            ['Rawhide', 'High', 'Low–moderate', 'High', 'Softening, breaking into large chunks, discolouration'],
        ],
    },
    'toy_age_appropriate': {
        'title': 'Age-Appropriate Dog Toy Guide',
        'headers': ['Age Stage', 'Recommended Toy Types', 'Materials to Choose', 'Materials to Avoid', 'Typical Budget'],
        'rows': [
            ['Puppy (8–12 weeks)', 'Soft teething toys, small plush', 'Soft rubber, fabric', 'Hard nylon, rawhide, small balls', '£10–20'],
            ['Puppy (3–6 months)', 'Teething rings, frozen toys, puppy puzzles', 'Textured rubber, chilled silicone', 'Bones, antlers, hard plastic', '£15–25'],
            ['Junior (6–12 months)', 'Transition chew toys, fetch toys, tug toys', 'Medium-firm rubber, rope', 'Extremely hard toys, very small toys', '£15–30'],
            ['Adult (1–7 years)', 'Full range based on play style', 'Rubber, nylon, rope, puzzle feeders', 'Undersized toys, worn-out toys', '£20–40'],
            ['Senior (7+ years)', 'Soft chews, lick mats, gentle puzzles', 'Soft rubber, silicone, fabric', 'Hard nylon, tough chews, high-impact fetch', '£15–30'],
        ],
    },

    # Dog Harness tables
    'harness_types_by_activity': {
        'title': 'Dog Harness Types by Activity',
        'headers': ['Activity', 'Recommended Harness Style', 'Key Features', 'Typical UK Price', 'Best Suited For'],
        'rows': [
            ['Daily walking', 'Y-shaped or H-shaped', 'Even pressure distribution, comfortable padding', '£15–30', 'All breeds and sizes'],
            ['No-pull training', 'Front-clip or dual-clip', 'Redirects pulling, training ring at chest', '£18–35', 'Dogs learning lead manners'],
            ['Running/jogging', 'Padded sport harness', 'Breathable mesh, back clip, reflective', '£25–45', 'Active dogs, medium–large breeds'],
            ['Hiking/adventure', 'Multi-point sport harness', 'Handle on back, durable material, waterproof', '£30–50', 'Outdoor-active dogs'],
            ['Car travel', 'Crash-tested harness', 'Seatbelt attachment, impact absorption', '£20–40', 'Dogs travelling by car regularly'],
            ['Swimming/water', 'Waterproof with handle', 'Quick-dry material, buoyancy aid option', '£25–45', 'Water-loving breeds'],
        ],
    },
    'harness_fit_by_breed': {
        'title': 'Harness Fit Guide by Breed Body Shape',
        'headers': ['Body Shape', 'Example Breeds', 'Recommended Style', 'Common Fitting Issues', 'Sizing Tip'],
        'rows': [
            ['Barrel-chested', 'Bulldog, Pug, French Bulldog', 'Step-through, Y-shaped', 'Standard harnesses ride up to throat', 'Measure chest at widest rib point'],
            ['Deep-chested', 'Greyhound, Whippet, Dobermann', 'Figure-8 or sighthound-specific', 'Standard harnesses slip over head', 'Measure deepest chest point + neck'],
            ['Standard build', 'Labrador, Spaniel, Beagle', 'Most types suitable', 'Few common issues', 'Standard chest + neck measurements'],
            ['Long-backed', 'Dachshund, Corgi, Basset Hound', 'Short-backed harness, no spinal pressure', 'Long harnesses press on lower back', 'Ensure harness ends before ribcage ends'],
            ['Muscular/broad', 'Staffie, Rottweiler, Boxer', 'Wide-strap padded, dual buckle', 'Narrow straps dig into muscle', 'Choose straps 3cm+ width'],
            ['Toy/miniature', 'Chihuahua, Yorkie, Pomeranian', 'Lightweight vest-style', 'Most harnesses too heavy or bulky', 'Weigh the harness — under 100g ideal'],
        ],
    },
    'harness_material_comparison': {
        'title': 'Harness Material Comparison',
        'headers': ['Material', 'Durability', 'Comfort', 'Weather Resistance', 'Typical UK Price', 'Maintenance'],
        'rows': [
            ['Nylon webbing', 'High', 'Moderate', 'Good (quick-drying)', '£10–25', 'Machine wash, air dry'],
            ['Padded mesh', 'Moderate', 'High', 'Moderate (breathable)', '£15–30', 'Hand wash, air dry'],
            ['Leather', 'Very high', 'High (moulds to shape)', 'Moderate (needs conditioning)', '£25–50', 'Leather conditioner monthly'],
            ['Neoprene-lined', 'High', 'High', 'Excellent (waterproof)', '£20–35', 'Rinse after wet walks, air dry'],
            ['Reflective nylon', 'High', 'Moderate', 'Good', '£15–30', 'Machine wash, check reflective strips'],
            ['Bamboo fibre', 'Moderate', 'High', 'Low (slow-drying)', '£18–32', 'Hand wash only, gentle detergent'],
        ],
    },
    'harness_price_tiers': {
        'title': 'Dog Harness Price Tiers and What to Expect (UK)',
        'headers': ['Price Tier', 'Typical Cost', 'Materials', 'Features', 'Durability', 'Suitable For'],
        'rows': [
            ['Budget', '£8–15', 'Basic nylon, plastic buckles', 'Single clip, minimal padding', '6–12 months', 'Light use, puppies who will outgrow quickly'],
            ['Mid-range', '£15–30', 'Padded nylon, metal D-rings', 'Front and back clips, reflective strips', '12–24 months', 'Daily walking, moderate pullers'],
            ['Premium', '£30–50', 'Reinforced nylon/neoprene, welded hardware', 'Dual clips, handle, padded chest plate', '2–3 years', 'Active dogs, training, adventure use'],
            ['Specialist', '£40–70+', 'Custom-fit materials, crash-tested', 'Activity-specific design, certified safety', '2–4 years', 'Working dogs, car travel, rehabilitation'],
        ],
    },

    # Dog Supplies tables
    'bowl_types_comparison': {
        'title': 'Dog Bowl Types Comparison',
        'headers': ['Bowl Type', 'Material', 'Typical UK Price', 'Hygiene', 'Durability', 'Best For'],
        'rows': [
            ['Standard floor bowl', 'Stainless steel', '£4–12', 'Excellent (dishwasher-safe)', 'Very high', 'Everyday feeding, all dogs'],
            ['Ceramic weighted bowl', 'Glazed ceramic', '£8–18', 'Good (dishwasher-safe)', 'Moderate (breakable)', 'Speed eaters, non-slip needed'],
            ['Slow feeder bowl', 'Plastic or silicone', '£8–18', 'Good (hand wash ridges)', 'Moderate', 'Fast eaters, bloat prevention'],
            ['Elevated/raised bowl', 'Steel on stand', '£12–30', 'Excellent', 'High', 'Senior dogs, large breeds, arthritis'],
            ['Collapsible travel bowl', 'Silicone', '£3–8', 'Good (hand wash)', 'Moderate', 'Travel, walks, car journeys'],
            ['Automatic water fountain', 'Plastic/steel', '£18–40', 'Good (filter changes needed)', 'High', 'Multi-pet households, cats and dogs'],
        ],
    },
    'collar_materials_comparison': {
        'title': 'Dog Collar Material Comparison',
        'headers': ['Material', 'Durability', 'Comfort', 'Weather Resistance', 'Typical UK Price', 'Maintenance'],
        'rows': [
            ['Nylon', 'High', 'Moderate', 'Good (quick-drying)', '£5–15', 'Machine washable'],
            ['Leather', 'Very high', 'High (softens over time)', 'Moderate', '£15–35', 'Condition every 2–3 months'],
            ['Biothane (synthetic leather)', 'Very high', 'Moderate–high', 'Excellent (waterproof)', '£12–28', 'Wipe clean, virtually maintenance-free'],
            ['Padded neoprene', 'Moderate–high', 'Very high', 'Excellent', '£10–22', 'Rinse and air dry'],
            ['Cotton/hemp', 'Moderate', 'High', 'Low (slow-drying)', '£8–18', 'Machine wash on gentle cycle'],
            ['Reflective nylon', 'High', 'Moderate', 'Good', '£8–18', 'Machine washable, check reflective strip'],
        ],
    },
    'lead_types_comparison': {
        'title': 'Dog Lead Types Comparison',
        'headers': ['Lead Type', 'Length', 'Typical UK Price', 'Control Level', 'Best Activity', 'Key Consideration'],
        'rows': [
            ['Standard fixed lead', '1.2–1.8m', '£8–15', 'High', 'Daily walking, urban areas', 'Most versatile everyday option'],
            ['Training long line', '5–10m', '£10–20', 'Moderate', 'Recall training, open spaces', 'Needs practice to handle safely'],
            ['Slip lead', '1.2–1.5m', '£5–10', 'High', 'Vet visits, temporary use', 'Not for pulling dogs — tightens on neck'],
            ['Double-ended training lead', '2m (adjustable)', '£12–20', 'High', 'Training, dual-clip harness use', 'Versatile but takes practice to master'],
            ['Hands-free waist lead', '1.2–1.8m', '£12–25', 'Moderate', 'Running, hiking', 'Requires good lead manners first'],
            ['Retractable lead', '3–8m', '£10–25', 'Low', 'Open, quiet areas only', 'Limited control near roads or other dogs'],
        ],
    },
    'feeding_equipment_comparison': {
        'title': 'Dog Feeding Equipment Comparison',
        'headers': ['Equipment', 'Purpose', 'Typical UK Price', 'Cleaning Frequency', 'Suitability'],
        'rows': [
            ['Standard food bowl', 'Daily meals', '£4–12', 'After every meal', 'All dogs'],
            ['Slow feeder bowl', 'Speed eating prevention', '£8–18', 'After every meal', 'Fast eaters, breeds prone to bloat'],
            ['Snuffle mat', 'Enrichment feeding', '£8–15', 'Weekly machine wash', 'All dogs, mental stimulation'],
            ['Lick mat', 'Calming, dental benefit', '£6–12', 'After every use', 'Anxious dogs, grooming distraction'],
            ['Treat-dispensing toy', 'Extended meal time', '£8–18', 'After every use', 'Dogs left alone, food-motivated dogs'],
            ['Automatic feeder', 'Timed portion control', '£25–60', 'Weekly deep clean', 'Owners with irregular schedules'],
            ['Portable water bottle', 'Hydration on walks', '£8–15', 'Daily rinse, weekly deep clean', 'Active dogs, warm weather walks'],
        ],
    },
    'grooming_tools_by_coat': {
        'title': 'Grooming Tools by Dog Coat Type',
        'headers': ['Coat Type', 'Example Breeds', 'Primary Tool', 'Secondary Tool', 'Grooming Frequency', 'Tool Cost'],
        'rows': [
            ['Smooth/short', 'Beagle, Dalmatian, Boxer', 'Rubber curry brush', 'Bristle brush', 'Weekly', '£4–8'],
            ['Double coat', 'Labrador, Husky, German Shepherd', 'Undercoat rake', 'Slicker brush', '2–3 times weekly', '£8–15'],
            ['Long/silky', 'Yorkshire Terrier, Shih Tzu, Afghan', 'Pin brush', 'Wide-tooth comb', 'Daily', '£6–12'],
            ['Wire/rough', 'Schnauzer, Airedale, Fox Terrier', 'Slicker brush', 'Stripping comb', 'Weekly + hand-stripping', '£6–15'],
            ['Curly/woolly', 'Poodle, Bichon, Cockapoo', 'Slicker brush', 'Dematting comb', '3–4 times weekly', '£8–15'],
            ['Hairless/minimal', 'Chinese Crested, Xoloitzcuintli', 'Soft cloth', 'Moisturising balm', 'Weekly skin care', '£4–10'],
        ],
    },
    'dental_care_options': {
        'title': 'Dog Dental Care Options Comparison',
        'headers': ['Method', 'Effectiveness', 'Typical UK Price', 'Frequency', 'Dog Acceptance', 'Best For'],
        'rows': [
            ['Tooth brushing', 'Very high', '£4–10 (brush + paste)', 'Daily or 3–5x weekly', 'Varies — needs training', 'All dogs with consistent routine'],
            ['Dental chews', 'Moderate', '£4–8 per pack', 'Daily', 'Generally high', 'Dogs resistant to brushing'],
            ['Water additive', 'Low–moderate', '£5–10 per bottle', 'Daily (added to water)', 'High (no effort from dog)', 'Supplementary use alongside brushing'],
            ['Dental toys (textured)', 'Low–moderate', '£8–18', 'During play', 'High', 'Supplementary, not a replacement'],
            ['Professional cleaning', 'Very high', '£200–400 (under anaesthetic)', 'Every 1–2 years', 'N/A (veterinary procedure)', 'Dogs with existing dental disease'],
            ['Raw bones (supervised)', 'Moderate', '£2–5 each', '1–2 times weekly', 'Very high', 'Dogs without dental damage, supervised only'],
        ],
    },
    'training_supplies_starter': {
        'title': 'Dog Training Supplies Comparison',
        'headers': ['Supply', 'Purpose', 'Typical UK Price', 'When to Use', 'Key Consideration'],
        'rows': [
            ['Training treats (soft)', 'Positive reinforcement', '£3–8 per 100g', 'Every session', 'Pea-sized, max 10% of daily calories'],
            ['Clicker', 'Marker signal for timing', '£2–4', 'During initial training', 'Consistent sound bridges reward gap'],
            ['Long training line (5–10m)', 'Recall practice', '£10–20', 'Recall and distance work', 'Lightweight material, never retractable'],
            ['Treat pouch', 'Hands-free treat access', '£5–12', 'Every outdoor session', 'Choose clip-on, not drawstring while walking'],
            ['Front-clip harness', 'Lead manners', '£18–35', 'Walking training', 'Redirects pulling without discomfort'],
            ['Puppy training pads', 'House training', '£8–15 per 50 pack', 'First 4–12 weeks', 'Transition to outdoor toileting gradually'],
        ],
    },
    'flea_treatment_comparison': {
        'title': 'Dog Flea Treatment Methods Comparison',
        'headers': ['Method', 'Application', 'Typical UK Price', 'Duration', 'Effectiveness', 'Key Consideration'],
        'rows': [
            ['Spot-on treatment', 'Applied to back of neck', '£5–15 per dose', 'Monthly', 'High', 'Avoid bathing 48 hours before/after'],
            ['Oral tablet', 'Given with food', '£8–20 per dose', 'Monthly or 3-monthly', 'Very high', 'Prescription required for some brands'],
            ['Flea collar', 'Worn continuously', '£8–25', '3–8 months', 'Moderate–high', 'Not suitable for dogs who swim frequently'],
            ['Flea shampoo', 'Used during bathing', '£4–8', 'Immediate (no lasting protection)', 'Low (kills existing fleas only)', 'Not a prevention method — treatment only'],
            ['Household spray', 'Sprayed on soft furnishings', '£8–15 per can', '3–12 months', 'High (environmental control)', 'Essential alongside pet treatment'],
        ],
    },
    'supplement_types': {
        'title': 'Dog Health Supplements Comparison',
        'headers': ['Supplement Type', 'Purpose', 'Typical UK Price', 'When to Consider', 'Key Consideration'],
        'rows': [
            ['Glucosamine + chondroitin', 'Joint support', '£10–25/month', 'Large breeds, senior dogs, joint issues', 'Takes 4–6 weeks to show effects'],
            ['Omega-3 fish oil', 'Skin, coat, joints', '£8–18/month', 'Dry skin, dull coat, general wellness', 'Choose marine-sourced, not plant-based'],
            ['Probiotics', 'Digestive health', '£8–20/month', 'After antibiotics, sensitive stomachs', 'Dog-specific strains, not human probiotics'],
            ['Multivitamin', 'General nutrition gap', '£8–15/month', 'Home-cooked diets, picky eaters', 'Unnecessary if feeding complete commercial food'],
            ['Calming supplement', 'Anxiety reduction', '£10–20/month', 'Fireworks, travel, separation anxiety', 'Not a substitute for behavioural work'],
        ],
    },
}

# Which tables go to which cluster/topic
TABLE_ASSIGNMENTS = {
    # Dog Toys cluster
    'toy_material_durability': {'cluster': 'Dog Toys', 'topics': ['chewer', 'safety', 'general', 'playstyle']},
    'toy_enrichment_types': {'cluster': 'Dog Toys', 'topics': ['enrichment', 'general', 'faq']},
    'toy_price_by_category': {'cluster': 'Dog Toys', 'topics': ['general', 'faq', 'playstyle']},
    'toy_safety_by_material': {'cluster': 'Dog Toys', 'topics': ['safety', 'general', 'chewer', 'puppy']},
    'toy_age_appropriate': {'cluster': 'Dog Toys', 'topics': ['puppy', 'general', 'safety']},

    # Dog Harness cluster
    'harness_types_by_activity': {'cluster': 'Dog Harnesses', 'topics': ['all']},
    'harness_fit_by_breed': {'cluster': 'Dog Harnesses', 'topics': ['all']},
    'harness_material_comparison': {'cluster': 'Dog Harnesses', 'topics': ['all']},
    'harness_price_tiers': {'cluster': 'Dog Harnesses', 'topics': ['all']},

    # Dog Supplies cluster
    'bowl_types_comparison': {'cluster': 'Dog Supplies', 'topics': ['bowls', 'hydration', 'general']},
    'collar_materials_comparison': {'cluster': 'Dog Supplies', 'topics': ['collars_leads', 'general']},
    'lead_types_comparison': {'cluster': 'Dog Supplies', 'topics': ['collars_leads', 'training', 'general']},
    'feeding_equipment_comparison': {'cluster': 'Dog Supplies', 'topics': ['bowls', 'food', 'general']},
    'grooming_tools_by_coat': {'cluster': 'Dog Supplies', 'topics': ['grooming']},
    'dental_care_options': {'cluster': 'Dog Supplies', 'topics': ['health', 'grooming']},
    'training_supplies_starter': {'cluster': 'Dog Supplies', 'topics': ['training', 'puppy_general']},
    'flea_treatment_comparison': {'cluster': 'Dog Supplies', 'topics': ['health']},
    'supplement_types': {'cluster': 'Dog Supplies', 'topics': ['health', 'food']},
}


def build_comparison_table_html(table_key):
    """Build a wp:table is-style-stripes HTML block."""
    tbl = COMPARISON_TABLES[table_key]
    headers = tbl['headers']
    rows = tbl['rows']

    thead = "<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>"
    tbody_rows = []
    for row in rows:
        tbody_rows.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")

    table_html = (
        f'<figure class="wp-block-table is-style-stripes" style="margin-top:24px;margin-bottom:24px">'
        f'<table><caption class="wp-element-caption"><strong>{tbl["title"]}</strong></caption>'
        f'<thead>{thead}</thead>'
        f'<tbody>{"".join(tbody_rows)}</tbody>'
        f'</table></figure>'
    )
    return table_html


def get_tables_for_post(cluster_name, topics):
    """Get list of comparison table keys suitable for this post."""
    matching = []
    for tbl_key, assignment in TABLE_ASSIGNMENTS.items():
        if assignment['cluster'] != cluster_name:
            continue
        if 'all' in assignment['topics']:
            matching.append(tbl_key)
        elif any(t in assignment['topics'] for t in topics):
            matching.append(tbl_key)
    return matching


# ── Block Construction ──────────────────────────────────────────────────────

def build_practical_guide_block(items):
    """Build the Practical Guide HTML block."""
    items_html = "\n".join(items)
    return (
        '<div class="wp-block-group has-border-color has-background is-layout-constrained wp-block-group-is-layout-constrained" '
        'style="border-color:#6ee7b7;border-width:1px;border-radius:6px;background-color:#ecfdf5;'
        'margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<h4 class="wp-block-heading">Step-by-Step Practical Guide</h4>\n'
        '<p class="wp-block-paragraph" style="font-size:14px">Follow these practical steps for the guidance covered in this article:</p>\n'
        f'<ol class="wp-block-list" style="font-size:14px">\n{items_html}\n</ol>\n'
        '</div>'
    )


def build_decision_pathway_block(paths):
    """Build the Decision Pathway HTML block."""
    paths_html = "\n".join(paths)
    return (
        '<div class="wp-block-group has-border-color has-background is-layout-constrained wp-block-group-is-layout-constrained" '
        'style="border-color:#fdba74;border-width:1px;border-radius:6px;background-color:#fff7ed;'
        'margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<h4 class="wp-block-heading">Your Decision Pathway</h4>\n'
        '<p class="wp-block-paragraph" style="font-size:14px">Find the situation closest to yours for a targeted recommendation:</p>\n'
        f'<ul class="wp-block-list" style="font-size:14px">\n{paths_html}\n</ul>\n'
        '</div>'
    )


# ── Insertion Logic ─────────────────────────────────────────────────────────

def find_insertion_point_practical(content):
    """Find where to insert Practical Guide — BEFORE Evaluation Framework.
    Evaluation Framework = 'How to Evaluate' heading.
    If not found, insert before 'Common Problems' or 'Which Option Suits' or 'Quick Checklist'.
    """
    # Look for the div containing "How to Evaluate"
    markers = ['How to Evaluate', 'How We Evaluated', 'Common Problems and Solutions', 'Which Option Suits', 'Quick Checklist']
    for marker in markers:
        idx = content.find(marker)
        if idx >= 0:
            # Walk backwards to find the opening <div of this block
            search_back = content[:idx]
            # Find the last <div before this heading
            div_start = search_back.rfind('<div class="wp-block-group')
            if div_start >= 0:
                return div_start
            # If no div, insert just before the heading's h3/h4
            h_start = search_back.rfind('<h3')
            if h_start < 0:
                h_start = search_back.rfind('<h4')
            if h_start >= 0:
                return h_start
            return idx

    # Fallback: before "Sources and Further Reading" or "Our Editorial Standards" or "Key Takeaways"
    for fallback in ['Sources and Further Reading', 'Our Editorial Standards', 'Key Takeaways']:
        idx = content.find(fallback)
        if idx >= 0:
            search_back = content[:idx]
            h_start = search_back.rfind('<h3')
            if h_start < 0:
                h_start = search_back.rfind('<h4')
            if h_start >= 0:
                div_start = search_back[:h_start].rfind('<div class="wp-block-group')
                if div_start >= 0 and h_start - div_start < 200:
                    return div_start
                return h_start

    # Last resort: append before end
    return len(content)


def find_insertion_point_decision(content):
    """Find where to insert Decision Pathway — AFTER Scenario Guidance, BEFORE Quick Checklist.
    Scenario Guidance = 'Which Option Suits Your Situation'.
    """
    # After "Which Option Suits" block
    scenario_idx = content.find('Which Option Suits')
    if scenario_idx >= 0:
        # Find the end of this block's div
        # Look for the closing </div> after the list
        after_scenario = content[scenario_idx:]
        # Find </ul> then </div>
        ul_end = after_scenario.find('</ul>')
        if ul_end >= 0:
            div_end = after_scenario.find('</div>', ul_end)
            if div_end >= 0:
                insert_pos = scenario_idx + div_end + len('</div>')
                return insert_pos

    # Before Quick Checklist
    checklist_idx = content.find('Quick Checklist')
    if checklist_idx >= 0:
        search_back = content[:checklist_idx]
        div_start = search_back.rfind('<div class="wp-block-group')
        if div_start >= 0 and checklist_idx - div_start < 300:
            return div_start
        h_start = search_back.rfind('<h3')
        if h_start < 0:
            h_start = search_back.rfind('<h4')
        if h_start >= 0:
            return h_start

    # After "Common Problems" block if it exists
    problems_idx = content.find('Common Problems and Solutions')
    if problems_idx >= 0:
        after_problems = content[problems_idx:]
        ul_end = after_problems.find('</ul>')
        if ul_end >= 0:
            div_end = after_problems.find('</div>', ul_end)
            if div_end >= 0:
                return problems_idx + div_end + len('</div>')

    # Fallback: before Sources or Editorial
    for fallback in ['Sources and Further Reading', 'Our Editorial Standards', 'Key Takeaways']:
        idx = content.find(fallback)
        if idx >= 0:
            search_back = content[:idx]
            h_start = search_back.rfind('<h3')
            if h_start < 0:
                h_start = search_back.rfind('<h4')
            if h_start >= 0:
                div_start = search_back[:h_start].rfind('<div class="wp-block-group')
                if div_start >= 0 and h_start - div_start < 200:
                    return div_start
                return h_start

    return len(content)


def find_insertion_point_tables(content):
    """Find where to insert comparison tables — after main article content, before evaluation blocks."""
    # Insert before "How to Evaluate" or before Practical Guide if already inserted
    markers = ['Step-by-Step Practical Guide', 'How to Evaluate', 'How We Evaluated',
               'Common Problems and Solutions', 'Which Option Suits',
               'Quick Checklist', 'Sources and Further Reading']
    for marker in markers:
        idx = content.find(marker)
        if idx >= 0:
            search_back = content[:idx]
            div_start = search_back.rfind('<div class="wp-block-group')
            if div_start >= 0 and idx - div_start < 300:
                return div_start
            h_start = search_back.rfind('<h3')
            if h_start < 0:
                h_start = search_back.rfind('<h4')
            if h_start >= 0:
                return h_start
            return idx
    return len(content)


# ── Main Processing ─────────────────────────────────────────────────────────

def process_all():
    """Main processing function."""
    # Track which tables have been assigned
    table_assignment_tracker = {k: False for k in COMPARISON_TABLES}

    # Determine table distribution plan
    # We need 20-30 tables total distributed across posts
    # Collect all posts first
    all_posts_by_cluster = {}
    all_post_ids_seen = set()  # Handle overlapping categories

    for cat_id, cluster_name in CLUSTERS.items():
        posts = fetch_all_posts(cat_id)
        print(f"\nFetched {len(posts)} posts for {cluster_name} (cat {cat_id})")
        # Filter out already-seen posts (Dog Supplies overlaps with Toys/Harnesses)
        unique_posts = []
        for p in posts:
            if p['id'] not in all_post_ids_seen:
                unique_posts.append(p)
                all_post_ids_seen.add(p['id'])
            else:
                print(f"  Skipping duplicate post {p['id']} (already in another cluster)")
        all_posts_by_cluster[cluster_name] = unique_posts
        time.sleep(0.5)

    # But for Dog Supplies, we need to handle posts that overlap with Toys/Harnesses
    # Those posts already got processed under their primary cluster
    # We need to process them under Dog Supplies too for the supplies-specific content
    # Let me re-fetch Dog Supplies including overlapping posts
    supplies_posts_full = fetch_all_posts(1376)
    time.sleep(0.5)

    # Build processing plan
    csv_rows = []
    processed_count = 0
    tables_added_total = 0

    # Assign tables to posts
    # Dog Toys: 5 tables across 14 posts
    # Dog Harnesses: 4 tables across 7 posts
    # Dog Supplies: ~10 tables across remaining unique supplies posts
    # Total: 19 defined tables, need to distribute them

    # First pass: process Dog Toys cluster
    print("\n" + "="*60)
    print("PROCESSING DOG TOYS CLUSTER")
    print("="*60)

    toys_posts = fetch_all_posts(1441)
    time.sleep(0.5)
    toys_table_idx = 0
    toys_tables = ['toy_material_durability', 'toy_enrichment_types', 'toy_price_by_category', 'toy_safety_by_material', 'toy_age_appropriate']

    for i, post in enumerate(toys_posts):
        post_id = post['id']
        title_raw = post['title']['raw']
        title = html.unescape(title_raw)
        content = post['content']['raw']

        print(f"\n[{i+1}/{len(toys_posts)}] Processing: {title[:60]}... (ID: {post_id})")

        # Check if already has our blocks
        has_practical = 'Step-by-Step Practical Guide' in content
        has_decision = 'Your Decision Pathway' in content

        if has_practical and has_decision:
            print(f"  SKIP — already has both blocks")
            csv_rows.append([post_id, title, 'Dog Toys', 'already_present', 'already_present', 0, 'skipped'])
            continue

        topics = classify_toy_topic(title, content)
        print(f"  Topics: {topics}")
        modified = False
        tables_this_post = 0

        # Phase 10BK: Practical Guide
        if not has_practical:
            guide_items = get_practical_guide_toys(topics, title)
            guide_block = build_practical_guide_block(guide_items)
            insert_pos = find_insertion_point_practical(content)
            content = content[:insert_pos] + "\n" + guide_block + "\n" + content[insert_pos:]
            modified = True
            print(f"  Added Practical Guide ({len(guide_items)} items) at position {insert_pos}")

        # Phase 10BL: Decision Pathway
        if not has_decision:
            decision_items = get_decision_pathway_toys(topics, title)
            decision_block = build_decision_pathway_block(decision_items)
            insert_pos = find_insertion_point_decision(content)
            content = content[:insert_pos] + "\n" + decision_block + "\n" + content[insert_pos:]
            modified = True
            print(f"  Added Decision Pathway ({len(decision_items)} items) at position {insert_pos}")

        # Phase 10BN: Comparison Tables (distribute across posts)
        matching_tables = get_tables_for_post('Dog Toys', topics)
        for tbl_key in matching_tables:
            if not table_assignment_tracker[tbl_key]:
                table_html = build_comparison_table_html(tbl_key)
                insert_pos = find_insertion_point_tables(content)
                content = content[:insert_pos] + "\n" + table_html + "\n" + content[insert_pos:]
                table_assignment_tracker[tbl_key] = True
                tables_this_post += 1
                tables_added_total += 1
                modified = True
                print(f"  Added table: {tbl_key}")
                if tables_this_post >= 2:  # Max 2 tables per post
                    break

        if modified:
            time.sleep(DELAY)
            success = api_update_post(post_id, content)
            status = 'updated' if success else 'error'
            print(f"  Status: {status}")
        else:
            status = 'no_changes'

        csv_rows.append([post_id, title, 'Dog Toys',
                        'added' if not has_practical else 'already_present',
                        'added' if not has_decision else 'already_present',
                        tables_this_post, status])
        processed_count += 1

    # Second pass: process Dog Harnesses cluster
    print("\n" + "="*60)
    print("PROCESSING DOG HARNESSES CLUSTER")
    print("="*60)

    harness_posts = fetch_all_posts(1422)
    time.sleep(0.5)
    harness_tables = ['harness_types_by_activity', 'harness_fit_by_breed', 'harness_material_comparison', 'harness_price_tiers']

    for i, post in enumerate(harness_posts):
        post_id = post['id']
        title_raw = post['title']['raw']
        title = html.unescape(title_raw)
        content = post['content']['raw']

        print(f"\n[{i+1}/{len(harness_posts)}] Processing: {title[:60]}... (ID: {post_id})")

        has_practical = 'Step-by-Step Practical Guide' in content
        has_decision = 'Your Decision Pathway' in content

        if has_practical and has_decision:
            print(f"  SKIP — already has both blocks")
            csv_rows.append([post_id, title, 'Dog Harnesses', 'already_present', 'already_present', 0, 'skipped'])
            continue

        topics = ['all']  # Harness posts get all harness content
        modified = False
        tables_this_post = 0

        # Phase 10BK: Practical Guide
        if not has_practical:
            guide_items = get_practical_guide_harness(topics, title)
            guide_block = build_practical_guide_block(guide_items)
            insert_pos = find_insertion_point_practical(content)
            content = content[:insert_pos] + "\n" + guide_block + "\n" + content[insert_pos:]
            modified = True
            print(f"  Added Practical Guide ({len(guide_items)} items) at position {insert_pos}")

        # Phase 10BL: Decision Pathway
        if not has_decision:
            decision_items = get_decision_pathway_harness(topics, title)
            decision_block = build_decision_pathway_block(decision_items)
            insert_pos = find_insertion_point_decision(content)
            content = content[:insert_pos] + "\n" + decision_block + "\n" + content[insert_pos:]
            modified = True
            print(f"  Added Decision Pathway ({len(decision_items)} items) at position {insert_pos}")

        # Phase 10BN: Tables
        for tbl_key in harness_tables:
            if not table_assignment_tracker[tbl_key]:
                table_html = build_comparison_table_html(tbl_key)
                insert_pos = find_insertion_point_tables(content)
                content = content[:insert_pos] + "\n" + table_html + "\n" + content[insert_pos:]
                table_assignment_tracker[tbl_key] = True
                tables_this_post += 1
                tables_added_total += 1
                modified = True
                print(f"  Added table: {tbl_key}")
                if tables_this_post >= 2:
                    break

        if modified:
            time.sleep(DELAY)
            success = api_update_post(post_id, content)
            status = 'updated' if success else 'error'
            print(f"  Status: {status}")
        else:
            status = 'no_changes'

        csv_rows.append([post_id, title, 'Dog Harnesses',
                        'added' if not has_practical else 'already_present',
                        'added' if not has_decision else 'already_present',
                        tables_this_post, status])
        processed_count += 1

    # Third pass: Dog Supplies (only unique posts not already processed)
    print("\n" + "="*60)
    print("PROCESSING DOG SUPPLIES CLUSTER (unique posts)")
    print("="*60)

    # Get IDs already processed
    processed_ids = set()
    for row in csv_rows:
        processed_ids.add(row[0])

    supplies_unique = [p for p in supplies_posts_full if p['id'] not in processed_ids]
    print(f"  {len(supplies_unique)} unique Dog Supplies posts to process (excluding overlaps)")

    supplies_tables = ['bowl_types_comparison', 'collar_materials_comparison', 'lead_types_comparison',
                       'feeding_equipment_comparison', 'grooming_tools_by_coat', 'dental_care_options',
                       'training_supplies_starter', 'flea_treatment_comparison', 'supplement_types']

    for i, post in enumerate(supplies_unique):
        post_id = post['id']
        title_raw = post['title']['raw']
        title = html.unescape(title_raw)
        content = post['content']['raw']

        print(f"\n[{i+1}/{len(supplies_unique)}] Processing: {title[:60]}... (ID: {post_id})")

        has_practical = 'Step-by-Step Practical Guide' in content
        has_decision = 'Your Decision Pathway' in content

        if has_practical and has_decision:
            print(f"  SKIP — already has both blocks")
            csv_rows.append([post_id, title, 'Dog Supplies', 'already_present', 'already_present', 0, 'skipped'])
            continue

        topics = classify_supply_topic(title, content)
        print(f"  Topics: {topics}")
        modified = False
        tables_this_post = 0

        # Phase 10BK: Practical Guide
        if not has_practical:
            guide_items = get_practical_guide_supplies(topics, title)
            guide_block = build_practical_guide_block(guide_items)
            insert_pos = find_insertion_point_practical(content)
            content = content[:insert_pos] + "\n" + guide_block + "\n" + content[insert_pos:]
            modified = True
            print(f"  Added Practical Guide ({len(guide_items)} items) at position {insert_pos}")

        # Phase 10BL: Decision Pathway
        if not has_decision:
            decision_items = get_decision_pathway_supplies(topics, title)
            decision_block = build_decision_pathway_block(decision_items)
            insert_pos = find_insertion_point_decision(content)
            content = content[:insert_pos] + "\n" + decision_block + "\n" + content[insert_pos:]
            modified = True
            print(f"  Added Decision Pathway ({len(decision_items)} items) at position {insert_pos}")

        # Phase 10BN: Tables
        matching_tables = get_tables_for_post('Dog Supplies', topics)
        for tbl_key in matching_tables:
            if not table_assignment_tracker[tbl_key]:
                table_html = build_comparison_table_html(tbl_key)
                insert_pos = find_insertion_point_tables(content)
                content = content[:insert_pos] + "\n" + table_html + "\n" + content[insert_pos:]
                table_assignment_tracker[tbl_key] = True
                tables_this_post += 1
                tables_added_total += 1
                modified = True
                print(f"  Added table: {tbl_key}")
                if tables_this_post >= 2:
                    break

        if modified:
            time.sleep(DELAY)
            success = api_update_post(post_id, content)
            status = 'updated' if success else 'error'
            print(f"  Status: {status}")
        else:
            status = 'no_changes'

        csv_rows.append([post_id, title, 'Dog Supplies',
                        'added' if not has_practical else 'already_present',
                        'added' if not has_decision else 'already_present',
                        tables_this_post, status])
        processed_count += 1

    # Check for any unassigned tables — add to suitable posts
    unassigned = [k for k, v in table_assignment_tracker.items() if not v]
    if unassigned:
        print(f"\n  {len(unassigned)} tables still unassigned, assigning to remaining posts...")
        # Re-fetch posts that can accept more tables
        for tbl_key in unassigned:
            assignment = TABLE_ASSIGNMENTS[tbl_key]
            cluster = assignment['cluster']
            cat_map = {'Dog Toys': 1441, 'Dog Harnesses': 1422, 'Dog Supplies': 1376}
            cat_id = cat_map[cluster]

            # Find a post in this cluster that has fewer tables
            posts = fetch_all_posts(cat_id)
            time.sleep(0.3)
            for p in posts:
                pid = p['id']
                raw = p['content']['raw']
                # Check how many tables already
                existing_tables = raw.count('wp-block-table is-style-stripes')
                if existing_tables < 3 and 'Step-by-Step Practical Guide' in raw:
                    # Add table to this post
                    table_html = build_comparison_table_html(tbl_key)
                    insert_pos = find_insertion_point_tables(raw)
                    new_content = raw[:insert_pos] + "\n" + table_html + "\n" + raw[insert_pos:]
                    time.sleep(DELAY)
                    success = api_update_post(pid, new_content)
                    if success:
                        table_assignment_tracker[tbl_key] = True
                        tables_added_total += 1
                        print(f"    Added {tbl_key} to post {pid}")
                        # Update CSV row
                        for row in csv_rows:
                            if row[0] == pid:
                                row[5] = int(row[5]) + 1
                                break
                    break

    # Write CSV
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'title', 'cluster', 'practical_guide_added', 'decision_pathway_added', 'comparison_tables_added', 'status'])
        for row in csv_rows:
            writer.writerow(row)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total posts processed: {processed_count}")
    print(f"Total comparison tables added: {tables_added_total}")

    tables_assigned = sum(1 for v in table_assignment_tracker.values() if v)
    print(f"Tables assigned: {tables_assigned}/{len(table_assignment_tracker)}")

    updated = sum(1 for r in csv_rows if r[6] == 'updated')
    skipped = sum(1 for r in csv_rows if r[6] == 'skipped')
    errors = sum(1 for r in csv_rows if r[6] == 'error')
    print(f"Updated: {updated}, Skipped: {skipped}, Errors: {errors}")
    print(f"\nCSV saved to: {CSV_PATH}")


if __name__ == '__main__':
    process_all()
