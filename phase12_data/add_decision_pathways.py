#!/usr/bin/env python3
"""
Phase 12O: Add Decision Pathway sections to 52 posts missing them.
Inserts a contextually appropriate "How to Choose" / decision guide
section before the last H2 in each post's content.
"""

import subprocess
import json
import time
import re
import os
import tempfile
from html.parser import HTMLParser


WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = f"{WP_USER}:{WP_PASS}"

POST_IDS = [5417,6044,8172,8171,7177,5462,6052,6039,5950,5942,5938,5931,5511,5476,5471,5469,5034,5458,5296,4415,4410,4408,4407,4335,7346,7345,7344,7343,7342,7175,7167,6050,6049,6047,6046,6045,6042,5932,5520,5519,5512,5508,5483,5036,4409,4314,4307,4300,4195,4181,4174,696]


def curl_get(url):
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def curl_post_json(url, data):
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(data, tmp)
    tmp.close()
    try:
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", f"@{tmp.name}",
             url],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            return None
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return result.stdout[:200]
    finally:
        os.unlink(tmp.name)


def strip_html(html_str):
    if not html_str:
        return ""
    return re.sub(r'<[^>]+>', '', html_str).strip()


def generate_decision_pathway(title, content_html):
    """Generate a decision pathway section based on post topic."""
    title_lower = title.lower()
    content_text = strip_html(content_html)[:500].lower()

    # Determine topic category for contextual guidance
    if 'cat toy' in title_lower or 'cat play' in title_lower or 'interactive cat' in title_lower:
        return generate_cat_toy_pathway(title)
    elif 'cat litter' in title_lower or 'litter tray' in title_lower:
        return generate_cat_litter_pathway(title)
    elif 'cat scratch' in title_lower:
        return generate_cat_scratch_pathway(title)
    elif 'indoor cat' in title_lower:
        return generate_indoor_cat_pathway(title)
    elif 'cat' in title_lower and ('supply' in title_lower or 'essential' in title_lower or 'glossary' in title_lower):
        return generate_cat_general_pathway(title)
    elif 'dog toy' in title_lower or 'enrichment' in title_lower or 'puzzle' in title_lower:
        return generate_dog_toy_pathway(title)
    elif 'dog train' in title_lower:
        return generate_dog_training_pathway(title)
    elif 'puppy' in title_lower:
        return generate_puppy_pathway(title)
    elif 'dog health' in title_lower or 'dog behaviour' in title_lower:
        return generate_dog_health_pathway(title)
    elif 'dog' in title_lower and ('boredom' in title_lower or 'rotation' in title_lower or 'lifespan' in title_lower):
        return generate_dog_toy_pathway(title)
    elif 'scent' in title_lower or 'sensory' in title_lower:
        return generate_enrichment_pathway(title)
    elif 'anxiety' in title_lower or 'calm' in title_lower or 'overstimul' in title_lower:
        return generate_anxiety_pathway(title)
    elif 'senior' in title_lower or 'ageing' in title_lower or 'low-mobility' in title_lower:
        return generate_senior_pathway(title)
    elif 'surgery' in title_lower or 'recovery' in title_lower or 'healing' in title_lower:
        return generate_recovery_pathway(title)
    elif 'hygiene' in title_lower or 'cleaning' in title_lower:
        return generate_hygiene_pathway(title)
    elif 'multi-dog' in title_lower or 'resource guard' in title_lower:
        return generate_multidog_pathway(title)
    elif 'breed' in title_lower:
        return generate_breed_pathway(title)
    elif 'research' in title_lower or 'why' in title_lower and 'exist' in title_lower:
        return generate_trust_page_pathway(title)
    elif 'kitten' in title_lower:
        return generate_kitten_pathway(title)
    elif 'development' in title_lower or 'stages' in title_lower:
        return generate_development_pathway(title)
    else:
        return generate_generic_pathway(title)


def generate_cat_toy_pathway(title):
    return """<!-- wp:heading {"level":2} -->
<h2>How to Choose: Decision Pathway</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Use this quick decision guide to find the right option for your cat:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>If your cat is highly active and under 7 years:</strong> Choose interactive toys with movement features — wand toys, motorised chasers, or puzzle feeders that reward effort.</li>
<li><strong>If your cat is older or less mobile:</strong> Opt for gentle stimulation — catnip-infused plush toys, slow-rolling balls, or elevated perches near windows for visual enrichment.</li>
<li><strong>If your cat is home alone for long periods:</strong> Prioritise self-play options — automated toys with timers, treat-dispensing puzzles, or crinkle tunnels they can explore independently.</li>
<li><strong>If you have multiple cats:</strong> Select toys that encourage parallel play without competition — multiple puzzle stations, long wand toys, or separate catnip items for each cat.</li>
<li><strong>If safety is your primary concern:</strong> Avoid small detachable parts, string longer than 15cm, and toxic materials. Choose reinforced stitching and non-toxic, pet-safe materials.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Key principle:</strong> Match the toy to your cat's natural play style (stalking, pouncing, batting, or chewing) rather than choosing based on appearance alone.</p>
<!-- /wp:paragraph -->"""


def generate_cat_litter_pathway(title):
    return """<!-- wp:heading {"level":2} -->
<h2>How to Choose: Decision Pathway</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Follow this decision guide based on your household situation:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>If odour control is your top priority:</strong> Choose clumping clay or activated charcoal-enhanced litters. These trap odours at source and allow spot-cleaning.</li>
<li><strong>If you prefer eco-friendly options:</strong> Wood pellet, recycled paper, or corn-based litters are biodegradable and often flushable (check local regulations first).</li>
<li><strong>If your cat has respiratory sensitivities:</strong> Avoid heavily fragranced or dusty clay litters. Opt for dust-free paper or crystal alternatives.</li>
<li><strong>If you have multiple cats:</strong> Use larger trays (one per cat plus one extra) with fast-clumping formulas that handle higher usage volumes.</li>
<li><strong>If convenience matters most:</strong> Self-cleaning or crystal litters require less frequent changes, though they have higher upfront costs.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Key principle:</strong> Your cat's preference matters more than marketing claims — introduce new litters gradually by mixing with the existing type over 7-10 days.</p>
<!-- /wp:paragraph -->"""


def generate_cat_scratch_pathway(title):
    return """<!-- wp:heading {"level":2} -->
<h2>How to Choose: Decision Pathway</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Match the scratcher type to your cat's scratching preferences:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>If your cat scratches vertically (door frames, sofa arms):</strong> Choose tall vertical posts or wall-mounted scratchers at least 80cm tall for full stretch.</li>
<li><strong>If your cat scratches horizontally (carpet, rugs):</strong> Flat cardboard pads or angled ramps placed on the floor work best.</li>
<li><strong>If space is limited:</strong> Wall-mounted or door-hanging scratchers save floor space while still providing satisfying scratch surfaces.</li>
<li><strong>If your cat is a heavy scratcher:</strong> Sisal rope posts or solid wood options outlast cardboard significantly and handle aggressive use.</li>
<li><strong>If you want to protect specific furniture:</strong> Place the scratcher directly beside the furniture being targeted — cats prefer familiar locations.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Key principle:</strong> Observe where and how your cat naturally scratches before buying — this tells you whether they prefer vertical or horizontal surfaces and what material texture they favour.</p>
<!-- /wp:paragraph -->"""


def generate_indoor_cat_pathway(title):
    return """<!-- wp:heading {"level":2} -->
<h2>How to Choose: Decision Pathway</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Use this guide based on your indoor cat's specific needs:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>If your cat shows signs of boredom (overgrooming, excessive vocalisation):</strong> Increase environmental enrichment — cat trees, window perches, puzzle feeders, and scheduled interactive play sessions twice daily.</li>
<li><strong>If weight management is a concern:</strong> Focus on active play solutions and portion-controlled feeding puzzles. Vertical space encourages climbing and jumping for exercise.</li>
<li><strong>If your cat is anxious or hiding frequently:</strong> Create safe retreat spaces, use pheromone diffusers, and introduce changes gradually. Avoid forcing interaction.</li>
<li><strong>If you have a multi-cat household:</strong> Ensure separate resources (food, water, litter, resting spots) for each cat plus one extra. Vertical territory reduces conflict.</li>
<li><strong>If you want to provide outdoor-like experiences safely:</strong> Consider catios, window boxes, or supervised harness training for controlled outdoor access.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Key principle:</strong> Indoor cats need deliberate enrichment planning — what outdoor cats get naturally (hunting, territory patrol, varied stimuli) must be replicated through thoughtful environmental design.</p>
<!-- /wp:paragraph -->"""


def generate_cat_general_pathway(title):
    return """<!-- wp:heading {"level":2} -->
<h2>How to Choose: Decision Pathway</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Navigate your choices based on your situation:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>If you are a first-time cat owner:</strong> Start with essentials — quality food and water bowls, an appropriately sized litter tray, a scratching post, and safe toys. Add complexity as you learn your cat's preferences.</li>
<li><strong>If you are adopting a kitten:</strong> Choose kitten-specific food, smaller toys without detachable parts, and a covered litter tray with low sides for easy access.</li>
<li><strong>If you are adopting an adult or senior cat:</strong> Prioritise comfort items — orthopaedic beds, easy-access food stations, and gentle enrichment suited to their energy level.</li>
<li><strong>If budget is a primary concern:</strong> Invest in quality food and litter first. DIY enrichment (cardboard boxes, paper bags, homemade puzzle feeders) supplements purchased items effectively.</li>
<li><strong>If your cat has health conditions:</strong> Consult your vet about specific product requirements — raised bowls for neck issues, dust-free litter for respiratory problems, or specialist diets.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Key principle:</strong> Every cat is individual — observe your cat's reactions to new items and adjust based on their actual behaviour rather than breed generalisations.</p>
<!-- /wp:paragraph -->"""


def generate_dog_toy_pathway(title):
    return """<!-- wp:heading {"level":2} -->
<h2>How to Choose: Decision Pathway</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Select the right approach based on your dog's needs:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>If your dog is a power chewer:</strong> Choose reinforced rubber or nylon toys rated for aggressive chewing. Avoid plush toys and thin plastic that can be shredded and swallowed.</li>
<li><strong>If your dog needs mental stimulation:</strong> Puzzle feeders, snuffle mats, and treat-dispensing toys engage their problem-solving instincts. Start easy and increase difficulty gradually.</li>
<li><strong>If your dog shows anxiety or destructive behaviour:</strong> Lick mats, stuffable toys (frozen fillings last longer), and calm-inducing chew items redirect anxious energy productively.</li>
<li><strong>If you have limited time for interactive play:</strong> Self-entertaining toys — automatic ball launchers, wobble dispensers, or rope toys for solo tug — provide independent enrichment.</li>
<li><strong>If your dog plays with other dogs:</strong> Choose toys designed for shared play (tug ropes, large balls) and avoid resource-guarding triggers like high-value chews during group play.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Key principle:</strong> Match toy type to your dog's play motivation (chasing, chewing, problem-solving, or social play) and always supervise with new toys until you know how your dog interacts with them.</p>
<!-- /wp:paragraph -->"""


def generate_dog_training_pathway(title):
    return """<!-- wp:heading {"level":2} -->
<h2>How to Choose: Decision Pathway</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Find the right training approach for your situation:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>If you have a new puppy (8-16 weeks):</strong> Focus on socialisation, name recognition, and basic cues (sit, recall). Keep sessions under 5 minutes. Use high-value soft treats.</li>
<li><strong>If your dog pulls on the lead:</strong> Start with equipment (front-clip harness) while training loose-lead walking. Reward proximity, stop when pulling occurs, and be consistent on every walk.</li>
<li><strong>If your dog has recall issues:</strong> Use a long line for safety while building value in coming back. Practice in low-distraction environments first before adding difficulty.</li>
<li><strong>If your dog shows reactive behaviour:</strong> Increase distance from triggers, reward calm behaviour, and consider working with a qualified behaviourist. Avoid punishment which worsens reactivity.</li>
<li><strong>If you want to advance beyond basics:</strong> Trick training, scent work, or agility provide mental stimulation while strengthening your bond. Build on what your dog naturally enjoys.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Key principle:</strong> Positive reinforcement (rewarding wanted behaviour) is supported by current behavioural science as both more effective and more welfare-friendly than aversive methods.</p>
<!-- /wp:paragraph -->"""


def generate_puppy_pathway(title):
    return """<!-- wp:heading {"level":2} -->
<h2>How to Choose: Decision Pathway</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Guide your decisions based on your puppy's stage:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>If your puppy is teething (3-6 months):</strong> Provide appropriate chew items — frozen rubber toys, textured teething rings, and dampened flannels. Redirect from furniture immediately.</li>
<li><strong>If your puppy is in their socialisation window (3-14 weeks):</strong> Prioritise positive exposure to varied people, environments, surfaces, and sounds. Quality matters more than quantity.</li>
<li><strong>If your puppy nips or mouths during play:</strong> Redirect to toys immediately, end play briefly if teeth touch skin, and reward gentle mouth interactions. This is normal developmental behaviour.</li>
<li><strong>If your puppy struggles with alone time:</strong> Build independence gradually — start with seconds apart, not hours. Puzzle toys and safe chews make alone time positive.</li>
<li><strong>If you are unsure about vaccinations and outdoor access:</strong> Carry your puppy in public for socialisation before full vaccination. Use private gardens and vaccinated dogs' homes for safe ground-level exploration.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Key principle:</strong> The first 16 weeks are critical for socialisation — balanced positive experiences during this period shape your dog's confidence and temperament for life.</p>
<!-- /wp:paragraph -->"""


def generate_dog_health_pathway(title):
    return """<!-- wp:heading {"level":2} -->
<h2>How to Choose: Decision Pathway</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Determine the right course of action for your dog:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>If you notice sudden behaviour changes:</strong> Book a vet check first — pain, illness, or discomfort often presents as behavioural shifts before obvious physical symptoms appear.</li>
<li><strong>If your dog shows mild, ongoing symptoms:</strong> Monitor and record for 48 hours (frequency, severity, triggers). Provide this log to your vet for more accurate assessment.</li>
<li><strong>If you are choosing between home monitoring and a vet visit:</strong> Always seek veterinary advice for: persistent vomiting/diarrhoea (24+ hours), lethargy, loss of appetite, breathing changes, or any sudden onset symptom.</li>
<li><strong>If your dog needs preventive care:</strong> Follow your vet's recommended schedule for vaccinations, parasite prevention, and dental checks. Prevention is significantly more cost-effective than treatment.</li>
<li><strong>If you are researching a specific condition:</strong> Use this guide as general education, then discuss your dog's individual situation with your veterinary team who knows their medical history.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Key principle:</strong> This content provides educational information only and does not replace professional veterinary advice. When in doubt, contact your vet.</p>
<!-- /wp:paragraph -->"""


def generate_enrichment_pathway(title):
    return """<!-- wp:heading {"level":2} -->
<h2>How to Choose: Decision Pathway</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Select the right enrichment approach for your dog:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>If your dog is new to enrichment activities:</strong> Start simple — scatter feeding on grass, basic snuffle mats, or a Kong with visible treats. Build confidence before adding complexity.</li>
<li><strong>If your dog gives up quickly on puzzles:</strong> Reduce difficulty immediately. Success builds motivation. Make the first few attempts very easy, then increase challenge by tiny increments.</li>
<li><strong>If your dog is highly food-motivated:</strong> Leverage this with puzzle feeders, scatter feeding, and foraging games. Feed entire meals through enrichment to maximise daily mental stimulation.</li>
<li><strong>If your dog prefers physical over mental play:</strong> Combine both — hide toys in the garden for finding, use flirt poles, or try dock diving. Not all enrichment needs to be food-based.</li>
<li><strong>If your dog has physical limitations:</strong> Focus on nose work and gentle cognitive games that don't require jumping, running, or prolonged standing.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Key principle:</strong> Effective enrichment matches your dog's current ability level and natural inclinations — it should be challenging enough to engage but easy enough to succeed.</p>
<!-- /wp:paragraph -->"""


def generate_anxiety_pathway(title):
    return """<!-- wp:heading {"level":2} -->
<h2>How to Choose: Decision Pathway</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Navigate calming approaches based on your dog's situation:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>If overstimulation happens during play:</strong> End the session calmly, redirect to a settle mat or quiet chew, and note the trigger point. Next session, stop before that threshold.</li>
<li><strong>If your dog shows anxiety in specific situations:</strong> Gradual desensitisation at distance works better than flooding. Pair the trigger with high-value rewards at a distance where your dog remains calm.</li>
<li><strong>If general anxiety affects daily life:</strong> Establish predictable routines, provide safe retreat spaces, and consider veterinary assessment for anxiety medication alongside behavioural work.</li>
<li><strong>If your dog is reactive to other dogs or people:</strong> Increase distance, reward calm behaviour, and avoid putting your dog in situations that exceed their current threshold.</li>
<li><strong>If calming products are being considered:</strong> Pheromone diffusers, pressure wraps, and calming supplements may help mild cases. Severe anxiety typically requires professional behavioural support.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Key principle:</strong> Anxiety is a welfare concern, not a training problem. Address the emotional state (how the dog feels) rather than just suppressing the behavioural symptoms.</p>
<!-- /wp:paragraph -->"""


def generate_senior_pathway(title):
    return """<!-- wp:heading {"level":2} -->
<h2>How to Choose: Decision Pathway</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Adapt your approach based on your senior dog's capabilities:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>If your dog has joint stiffness but is otherwise well:</strong> Choose low-impact enrichment — snuffle mats at ground level, gentle tug games, and short scatter-feeding sessions on soft surfaces.</li>
<li><strong>If cognitive decline is noticeable:</strong> Keep activities familiar and achievable. Revisit simpler versions of previously enjoyed games. Routine and predictability provide comfort.</li>
<li><strong>If your dog tires quickly:</strong> Shorter, more frequent sessions (5 minutes, 3-4 times daily) are better than one long play period. Rest is enrichment too.</li>
<li><strong>If your dog still has enthusiasm but limited mobility:</strong> Nose work is ideal — it provides intense mental engagement with minimal physical demand. Hide treats at nose height.</li>
<li><strong>If you are unsure what level of activity is appropriate:</strong> Let your dog set the pace. Offer opportunities without pressure. If they choose to rest, respect that choice.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Key principle:</strong> Senior enrichment prioritises quality of experience over intensity. The goal is engagement and contentment, not exhaustion or physical challenge.</p>
<!-- /wp:paragraph -->"""


def generate_recovery_pathway(title):
    return """<!-- wp:heading {"level":2} -->
<h2>How to Choose: Decision Pathway</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Guide your recovery enrichment decisions carefully:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>If your dog is in the first week post-surgery:</strong> Prioritise rest. Only offer lick mats or frozen Kongs that require no physical movement. Follow your vet's specific instructions.</li>
<li><strong>If your dog is restless during crate rest:</strong> Rotate calm enrichment items frequently — stuffed toys, chew items, and scent-based activities. Frozen fillings last longer and encourage calm licking.</li>
<li><strong>If exercise restrictions are being gradually lifted:</strong> Follow your vet's phased plan precisely. Increase duration before intensity. Lead walks before off-lead freedom.</li>
<li><strong>If your dog is frustrated by restricted movement:</strong> Mental enrichment compensates for reduced physical activity. Training new calm behaviours (chin rest, settle) gives them a job to focus on.</li>
<li><strong>If you are unsure whether an activity is safe:</strong> When in doubt, do not proceed. Contact your vet or veterinary physiotherapist. Reinjury from premature activity is common and costly.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Key principle:</strong> Recovery enrichment must never compromise healing. Always prioritise your veterinary team's guidance over your dog's apparent enthusiasm for activity.</p>
<!-- /wp:paragraph -->"""


def generate_hygiene_pathway(title):
    return """<!-- wp:heading {"level":2} -->
<h2>How to Choose: Decision Pathway</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Determine the right cleaning routine for your situation:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>If you need a daily quick-clean routine:</strong> Wipe hard toys with pet-safe disinfectant, shake out fabric toys, and inspect for damage. Takes under 5 minutes.</li>
<li><strong>If doing a weekly deep clean:</strong> Machine-wash fabric toys (gentle cycle, no fabric softener), soak rubber toys in diluted pet-safe cleaning solution, and air-dry completely before returning.</li>
<li><strong>If your pet has allergies or sensitivities:</strong> Use fragrance-free, hypoallergenic cleaning products. Rinse thoroughly to remove all residue. Hot water alone handles most surface bacteria.</li>
<li><strong>If a toy shows mould, deep staining, or damage:</strong> Replace immediately. No amount of cleaning makes a compromised toy safe. Mould spores persist even after visible cleaning.</li>
<li><strong>If you want to minimise effort long-term:</strong> Choose materials that clean easily — solid rubber, nylon, and silicone require less maintenance than rope, plush, or porous materials.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Key principle:</strong> Regular light cleaning prevents the build-up that requires intensive deep cleaning. A consistent routine is more effective than occasional thorough sessions.</p>
<!-- /wp:paragraph -->"""


def generate_multidog_pathway(title):
    return """<!-- wp:heading {"level":2} -->
<h2>How to Choose: Decision Pathway</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Manage multi-dog toy situations based on your dogs' dynamics:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>If resource guarding occurs with specific toys:</strong> Remove the trigger item during group time. Offer it only in separated, supervised one-on-one sessions.</li>
<li><strong>If dogs play well together generally:</strong> Provide enough toys for each dog plus extras. Rotate toys to maintain novelty and reduce competition for favourites.</li>
<li><strong>If introducing new toys to the group:</strong> Give each dog their own identical item simultaneously in separate spaces. Once excitement reduces, allow shared access.</li>
<li><strong>If tension rises during play:</strong> Interrupt calmly before escalation. Redirect each dog to their own enrichment activity. Do not punish guarding behaviour — it worsens the underlying anxiety.</li>
<li><strong>If one dog consistently dominates resources:</strong> Feed and provide enrichment separately. Shared play should only happen when all dogs are relaxed and the dynamic is equitable.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Key principle:</strong> Resource guarding is a normal canine behaviour that requires management and gradual behaviour modification — not punishment. Preventing conflict situations is more effective than correcting them.</p>
<!-- /wp:paragraph -->"""


def generate_breed_pathway(title):
    return """<!-- wp:heading {"level":2} -->
<h2>How to Choose: Decision Pathway</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Tailor enrichment to your dog's breed instincts:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>If your dog is from a working/herding breed:</strong> Provide structured tasks — trick training, agility, or activities that use their problem-solving drive. These breeds need a "job" to feel satisfied.</li>
<li><strong>If your dog is from a scent hound breed:</strong> Nose work is essential — scatter feeding, scent trails, and tracking games align with their strongest natural instinct.</li>
<li><strong>If your dog is from a terrier breed:</strong> Digging pits, tug toys, and fast-moving chase games satisfy their prey drive. Channel energy into appropriate outlets.</li>
<li><strong>If your dog is from a retriever/gundog breed:</strong> Fetch variations, water play, and carrying-based activities meet their inherent retrieving motivation.</li>
<li><strong>If your dog is from a companion/toy breed:</strong> Social interaction and proximity to their owner often matters more than intense physical activity. Puzzle feeders and trick training work well.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Key principle:</strong> Breed tendencies are starting points, not rules. Every dog is an individual — observe what specifically motivates your dog and build on that, regardless of breed expectations.</p>
<!-- /wp:paragraph -->"""


def generate_trust_page_pathway(title):
    return """<!-- wp:heading {"level":2} -->
<h2>How to Use This Information</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Navigate our content based on your needs:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>If you want to verify a specific claim:</strong> Check the Sources section at the bottom of each article. We link to the primary research, veterinary guidelines, or manufacturer specifications that support each factual statement.</li>
<li><strong>If you are comparing products:</strong> Use our comparison tables which present standardised criteria across options. We do not rank products we have not evaluated against our research standards.</li>
<li><strong>If you notice outdated information:</strong> Our content is reviewed regularly, but products and guidelines change. If something appears incorrect, this reflects a gap in our review cycle rather than intentional misinformation.</li>
<li><strong>If you need professional advice:</strong> Our content is educational, not prescriptive. For health concerns, always consult a qualified veterinarian. For behavioural issues, seek a certified behaviourist.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Key principle:</strong> We aim to provide evidence-informed educational content that helps you make better decisions — not to replace professional advice or personal judgement about your individual pet.</p>
<!-- /wp:paragraph -->"""


def generate_kitten_pathway(title):
    return """<!-- wp:heading {"level":2} -->
<h2>How to Choose: Decision Pathway</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Select appropriate options based on your kitten's age:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>If your kitten is under 12 weeks:</strong> Choose small, soft toys without detachable parts. Supervised play only. Avoid string, ribbon, or anything that could be swallowed.</li>
<li><strong>If your kitten is 3-6 months (peak play drive):</strong> Provide variety — wand toys for interactive sessions, small balls for solo play, and crinkle toys for auditory stimulation. Rotate frequently.</li>
<li><strong>If your kitten is 6-12 months (adolescent):</strong> Increase challenge with puzzle feeders and multi-level cat trees. Their coordination improves rapidly, so toys can be more complex.</li>
<li><strong>If your kitten plays too roughly with hands/feet:</strong> Always redirect to appropriate toys immediately. Never use hands as play objects — this teaches biting habits that persist into adulthood.</li>
<li><strong>If transitioning to adult toys:</strong> Gradually introduce larger, more durable options. Most cats settle into their preferred play style by 12-18 months.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Key principle:</strong> Kittens learn through play — the toys and interactions you provide now shape their adult behaviour, confidence, and relationship with play for life.</p>
<!-- /wp:paragraph -->"""


def generate_development_pathway(title):
    return """<!-- wp:heading {"level":2} -->
<h2>How to Choose: Decision Pathway</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Support your pet's development at each stage:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>If you are in the early socialisation window:</strong> Maximise positive, varied experiences while keeping sessions short and stress-free. Quality of experience matters more than quantity.</li>
<li><strong>If your pet is in adolescence (testing boundaries):</strong> Maintain consistency in rules and training. Regression is normal — it does not mean previous training failed. Patience and repetition work.</li>
<li><strong>If you notice fear periods (sudden wariness of familiar things):</strong> Do not force exposure. Allow retreat, reward bravery, and give time. Fear periods pass naturally with supportive handling.</li>
<li><strong>If you are concerned about developmental progress:</strong> Compare against general milestones but remember individual variation is normal. Consult your vet if you notice significant delays.</li>
<li><strong>If transitioning between life stages:</strong> Adjust diet, exercise, and enrichment gradually. Abrupt changes are stressful — phase new routines in over 7-14 days.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Key principle:</strong> Development is not linear — expect plateaus, regressions, and sudden leaps. Consistent, patient, positive approaches produce the best long-term outcomes regardless of temporary setbacks.</p>
<!-- /wp:paragraph -->"""


def generate_generic_pathway(title):
    topic = strip_html(title).split(':')[0] if ':' in strip_html(title) else strip_html(title)
    return f"""<!-- wp:heading {{"level":2}} -->
<h2>How to Choose: Decision Pathway</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Use this decision guide to navigate your options:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>If you are new to this topic:</strong> Start with the basics outlined in the sections above. Focus on understanding the core principles before making purchasing or care decisions.</li>
<li><strong>If you need a quick recommendation:</strong> Check the Quick Answer section at the top of this guide and the comparison table for a summary of key options.</li>
<li><strong>If your pet has specific needs or health conditions:</strong> Consult your veterinarian before making changes. General guides cannot account for individual medical circumstances.</li>
<li><strong>If budget is a concern:</strong> The most expensive option is not always the best. Focus on quality in the areas that matter most for safety and welfare, and economise where cosmetic differences are the main variable.</li>
<li><strong>If you want to learn more:</strong> Check the Sources section for links to the research and guidelines that informed this content.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Key principle:</strong> The best choice depends on your individual pet's needs, your household situation, and your budget. Use this guide as a starting framework, then adapt based on what works for your specific circumstances.</p>
<!-- /wp:paragraph -->"""


def insert_decision_pathway(content_html, pathway_html):
    """Insert pathway section before the last H2 (usually FAQ or Sources)."""
    h2_positions = [m.start() for m in re.finditer(r'<!-- wp:heading\s*(?:\{[^}]*\})?\s*-->\s*<h2', content_html)]

    if len(h2_positions) >= 2:
        insert_pos = h2_positions[-1]
    elif len(h2_positions) == 1:
        insert_pos = h2_positions[0]
    else:
        insert_pos = len(content_html)

    return content_html[:insert_pos] + pathway_html + "\n\n" + content_html[insert_pos:]


def main():
    print("=" * 70)
    print("Phase 12O: Decision Pathway Insertion")
    print(f"Target: {len(POST_IDS)} posts")
    print("=" * 70)
    print()

    success = 0
    errors = 0

    for i, post_id in enumerate(POST_IDS, 1):
        url = f"{WP_API}/posts/{post_id}?_fields=id,title,content"
        post = curl_get(url)
        if not post:
            print(f"[{i:2d}/{len(POST_IDS)}] Post {post_id}: FETCH ERROR")
            errors += 1
            time.sleep(3)
            continue

        title = post['title']['rendered'] if isinstance(post['title'], dict) else str(post['title'])
        content = post['content']['rendered'] if isinstance(post['content'], dict) else str(post['content'])
        title_clean = strip_html(title)[:60]

        if 'How to Choose: Decision Pathway' in content or 'How to Use This Information' in content:
            print(f"[{i:2d}/{len(POST_IDS)}] Post {post_id}: {title_clean} — ALREADY HAS PATHWAY, skipping")
            time.sleep(1)
            continue

        pathway = generate_decision_pathway(title, content)
        new_content = insert_decision_pathway(content, pathway)

        update_data = {"content": new_content}
        resp = curl_post_json(f"{WP_API}/posts/{post_id}", update_data)

        if resp and isinstance(resp, dict) and resp.get('id'):
            success += 1
            print(f"[{i:2d}/{len(POST_IDS)}] Post {post_id}: {title_clean} — INSERTED")
        else:
            errors += 1
            err_msg = resp.get('message', str(resp)[:80]) if isinstance(resp, dict) else str(resp)[:80]
            print(f"[{i:2d}/{len(POST_IDS)}] Post {post_id}: {title_clean} — ERROR: {err_msg}")

        time.sleep(5)

    print()
    print("=" * 70)
    print(f"RESULTS: {success} inserted, {errors} errors")
    print("=" * 70)


if __name__ == '__main__':
    main()
