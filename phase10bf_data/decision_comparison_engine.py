#!/usr/bin/env python3
"""
Phase 10BE (Decision Support Dominance) + 10BF (Comparison Saturation)
Clusters: Dog Toys, Dog Training, Dog Grooming
pethubonline.com — WordPress REST API

Adds 3 new block types to every post:
  1. Evaluation Framework (sky blue)
  2. Troubleshooting (yellow)
  3. Scenario Guidance (fuchsia)

Also adds 30-40 new comparison tables (wp:table is-style-stripes) across clusters.
"""

import subprocess
import json
import csv
import re
import os
import sys
import tempfile
import time
import html as html_mod
from collections import defaultdict

# ── Configuration ──────────────────────────────────────────────────────────
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
BASE = "https://pethubonline.com/wp-json/wp/v2"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10bf_data"
INVENTORY = "/var/lib/freelancer/projects/40416335/phase10af_data/post_authority_inventory.csv"
DELAY = 2.5  # seconds between API updates
SKIP_IDS = {4057, 5523, 5464}

os.makedirs(DATA_DIR, exist_ok=True)

# ── API Helpers ────────────────────────────────────────────────────────────

def api_get(endpoint):
    """GET from WP REST API."""
    url = f"{BASE}/{endpoint}"
    r = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    return json.loads(r.stdout)


def api_get_all(endpoint, per_page=100):
    """GET all pages from WP REST API."""
    results = []
    page = 1
    while True:
        sep = "&" if "?" in endpoint else "?"
        url = f"{BASE}/{endpoint}{sep}per_page={per_page}&page={page}"
        r = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True, timeout=60
        )
        try:
            data = json.loads(r.stdout)
        except json.JSONDecodeError:
            break
        if isinstance(data, dict) and "code" in data:
            break
        if not data:
            break
        results.extend(data)
        if len(data) < per_page:
            break
        page += 1
        time.sleep(0.3)
    return results


def api_update(post_id, content):
    """Update post content via WP REST API using temp file for large payloads."""
    url = f"{BASE}/posts/{post_id}"
    payload = {"content": content}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        tmp = f.name
    try:
        r = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-d", f"@{tmp}",
             "-H", "Content-Type: application/json",
             "-X", "POST", url],
            capture_output=True, text=True, timeout=120
        )
        data = json.loads(r.stdout)
        if "id" in data:
            return True, data
        else:
            return False, data
    except Exception as e:
        return False, {"error": str(e)}
    finally:
        os.unlink(tmp)


def strip_html(raw):
    """Remove HTML tags and decode entities."""
    if not raw:
        return ""
    text = re.sub(r'<[^>]+>', ' ', raw)
    text = html_mod.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ── Cluster Identification ─────────────────────────────────────────────────

def build_cluster_map():
    """Build mapping of post_id -> cluster for our 3 target clusters."""
    cluster_map = {}

    # From inventory
    if os.path.exists(INVENTORY):
        with open(INVENTORY, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = int(row["id"])
                cluster = row["cluster"].strip()
                if cluster in ("Dog Toys", "Dog Training", "Dog Grooming"):
                    cluster_map[pid] = cluster

    # Additional posts identified by keyword matching for completeness
    extra_assignments = {
        # Dog Toys extras not in inventory or labelled differently
        6048: "Dog Toys",   # Confidence-Building Play (was Uncategorized)
        5415: "Dog Toys",   # Dog Play Styles (was Educational)
        # Dog Training extras
        5462: "Dog Training",  # Dog Training Terminology (was Educational)
        4139: "Dog Training",  # Dog Training Leads (was Dog Harnesses)
    }
    for pid, cluster in extra_assignments.items():
        if pid not in cluster_map:
            cluster_map[pid] = cluster

    return cluster_map


# ── Decision Support Block Generators ──────────────────────────────────────

# Topic-aware content for each block type, keyed by cluster + keywords in title

DOG_TOYS_EVAL = {
    "default": [
        "Size appropriateness — Ensure the toy matches your dog's jaw size to prevent choking risks",
        "Material safety — Check for non-toxic materials free from BPA, phthalates, and lead-based dyes",
        "Durability rating — Consider your dog's chewing strength and select materials that withstand their play style",
        "Enrichment value — Assess whether the toy provides mental stimulation beyond simple chewing",
        "Ease of cleaning — Prioritise toys that are machine-washable or easy to sanitise regularly",
        "Supervision requirement — Determine whether the toy is safe for unsupervised play or requires monitoring",
    ],
    "puzzle|mental|enrichment|cognitive|stimulat": [
        "Difficulty level — Match puzzle complexity to your dog's problem-solving experience",
        "Frustration threshold — Choose puzzles that challenge without causing distress or disengagement",
        "Treat compatibility — Ensure the toy works with your preferred healthy treats or kibble",
        "Progressive challenge — Look for toys offering adjustable difficulty as your dog improves",
        "Engagement duration — Consider how long the toy keeps your dog mentally occupied",
        "Safety during solo use — Assess whether puzzles have removable parts that could pose risks",
    ],
    "chew|destruct|tough|indestruc|durabl": [
        "Chew strength rating — Match the toy's durability class to your dog's jaw power and chewing style",
        "Material composition — Prioritise solid rubber or nylon over multi-material construction",
        "Breakage pattern — Check whether the toy crumbles into small pieces or stays intact under pressure",
        "Replacement indicators — Learn the signs that a tough toy has worn beyond safe use",
        "Dental safety — Ensure the toy is firm enough to resist shredding but not so hard it damages teeth",
        "Size-to-breed ratio — Select an appropriately sized toy that cannot be swallowed whole",
    ],
    "senior|old|age|mobility|limited": [
        "Softness level — Choose toys gentle on ageing teeth and gums without being easily destroyed",
        "Weight — Lightweight options reduce strain on joints and are easier for senior dogs to carry",
        "Sensory engagement — Prioritise scent-based or textured toys that work with declining vision",
        "Physical demand — Select toys requiring minimal vigorous movement to enjoy",
        "Comfort factor — Consider toys that double as comfort objects for resting periods",
    ],
    "puppy|young|teething": [
        "Teething suitability — Look for toys that soothe sore gums during the teething phase",
        "Size progression — Choose appropriate sizes that grow with your puppy's development",
        "Material softness — Ensure materials are gentle on developing teeth and gums",
        "Supervision needs — Assess whether the toy requires constant supervision for young dogs",
        "Training compatibility — Consider whether the toy reinforces positive play behaviours",
        "Washability — Prioritise easy-to-clean options given puppies' developing immune systems",
    ],
    "tug|rope|fetch|play style": [
        "Play style match — Ensure the toy supports your dog's natural play preference",
        "Grip design — Check handle comfort for human players and tooth safety for dogs",
        "Indoor vs outdoor use — Consider whether the toy works in your available play spaces",
        "Material shedding — Assess whether fibres or pieces come loose during vigorous play",
        "Multi-dog suitability — Evaluate whether the toy works safely with multiple dogs",
    ],
    "clean|hygien|wash|storage|organis": [
        "Cleaning method compatibility — Check whether the toy survives machine washing, hand washing, or dishwasher cycles",
        "Drying requirements — Assess how quickly the toy dries to prevent bacterial or mould growth",
        "Material porosity — Non-porous materials harbour fewer bacteria than porous alternatives",
        "Inspection frequency — Establish a routine check schedule based on how heavily the toy is used",
        "Storage accessibility — Ensure your storage system keeps toys clean while remaining easy for daily access",
    ],
    "scent|smell|nosework|snuffle": [
        "Scent retention — Evaluate how well the toy holds treats or scent markers over time",
        "Difficulty scaling — Choose options that allow you to adjust challenge levels progressively",
        "Material washability — Ensure scent work toys can be thoroughly cleaned between sessions",
        "Indoor suitability — Assess whether the activity works well within your home environment",
        "Engagement monitoring — Look for designs that let you observe your dog's progress during play",
    ],
    "safety|hazard|toxic|risk": [
        "Material certification — Look for toys tested to recognised safety standards",
        "Size-to-mouth ratio — Ensure the toy is large enough to prevent accidental swallowing",
        "Component security — Check that squeakers, stuffing, and attachments are firmly secured",
        "Wear indicators — Identify visual cues that signal when a toy should be replaced",
        "Supervision guidelines — Understand which toys require active monitoring during play",
    ],
    "rotation|boredom|interest|engaged": [
        "Variety planning — Ensure your rotation includes different toy types covering multiple play styles",
        "Novelty duration — Track how long each toy maintains your dog's interest before switching",
        "Storage condition — Keep rotated-out toys clean and in good condition during storage periods",
        "Seasonal adjustment — Modify your rotation to suit weather conditions and energy levels",
        "Individual preference tracking — Note which toys your dog consistently returns to after absence",
    ],
    "indoor|outdoor|crate|space": [
        "Space requirements — Match the toy to your available play area without risking damage",
        "Noise level — Consider the impact on household members and neighbours",
        "Surface compatibility — Ensure the toy works on your flooring type without causing damage",
        "Containment suitability — Assess whether the toy is safe within a crate or pen",
        "Weather resilience — For outdoor use, check whether the toy withstands moisture and UV exposure",
    ],
    "multi.*dog|resource guard|sharing": [
        "Conflict potential — Choose toys that minimise resource guarding triggers between dogs",
        "Size differentiation — Provide appropriately sized versions for each dog in the household",
        "Supervision protocol — Establish clear monitoring rules for shared play sessions",
        "Individual allocation — Determine which toys should be personal and which can be communal",
        "De-escalation design — Select toys that can be easily separated if tension develops",
    ],
    "cat|feline": [
        "Species-appropriate design — Ensure the toy matches feline hunting instincts and play patterns",
        "Size safety — Choose items small enough to bat and chase but too large to swallow",
        "Material durability — Select fabrics and materials that withstand clawing and biting",
        "Interactive vs solo — Determine whether the toy is best for human-led or independent play",
        "Enrichment variety — Provide a mix of stalking, pouncing, and batting opportunities",
    ],
    "DIY|homemade": [
        "Material safety — Ensure all components used are non-toxic and free from sharp edges",
        "Structural integrity — Test the toy thoroughly before giving it to your dog unsupervised",
        "Choking hazard review — Remove or secure any small components that could detach",
        "Durability estimation — Be honest about how long a homemade toy will withstand your dog's play",
        "Cost vs safety — Never compromise on safety materials to reduce cost",
    ],
}

DOG_TOYS_TROUBLESHOOT = {
    "default": [
        ("Dog destroys toy within minutes", "Switch to solid rubber or nylon toys rated for power chewers. Avoid plush or rope toys until you identify your dog's chewing intensity."),
        ("Dog loses interest in toys quickly", "Implement a toy rotation system — keep 3-4 toys available and swap them weekly to maintain novelty."),
        ("Dog swallows pieces of toys", "Remove the toy immediately and consult your vet. Switch to one-piece designs without detachable components."),
        ("Dog guards toys aggressively", "Practice trade-up exercises — offer a higher-value treat in exchange for the toy. Consult an ABTC-registered behaviourist if guarding escalates."),
        ("Dog only plays with human interaction", "Introduce self-play options gradually, such as treat-dispensing toys that reward independent engagement."),
    ],
    "puzzle|mental|enrichment|cognitive|stimulat": [
        ("Dog gives up on puzzle too quickly", "Start with the easiest setting and only increase difficulty after consistent success. Frustration kills engagement."),
        ("Dog flips or smashes puzzle instead of solving it", "Use a heavier puzzle base or hold it steady during early sessions. Some dogs need to learn the mechanics before working independently."),
        ("Treats get stuck inside the toy", "Use smaller, drier treats or kibble. Apply a thin layer of dog-safe paste for easier dispensing."),
        ("Dog finishes puzzle too fast", "Increase difficulty settings, freeze the treats inside, or combine multiple puzzle types in one session."),
    ],
    "chew|destruct|tough|indestruc|durabl": [
        ("Even tough toys get destroyed quickly", "Consider solid rubber kongs or nylon bones. No toy is truly indestructible — always supervise and replace at first signs of damage."),
        ("Dog chips teeth on hard toys", "Avoid antlers, hooves, and extremely hard nylon. If a toy doesn't give slightly under thumbnail pressure, it may be too hard."),
        ("Dog only chews on furniture despite having toys", "Redirect consistently and ensure chew toys are more appealing — try stuffing with frozen treats."),
    ],
    "senior|old|age|mobility|limited": [
        ("Senior dog shows no interest in any toys", "Try scent-based enrichment or food puzzles. Declining vision or joint pain often changes play preferences, not desire."),
        ("Dog can't grip toys due to dental issues", "Offer flat lick mats, snuffle mats, or soft puzzle feeders that don't require strong jaw grip."),
        ("Toys cause joint discomfort during play", "Switch to stationary enrichment — frozen kongs, snuffle mats, and nosework games that require minimal movement."),
    ],
    "puppy|young|teething": [
        ("Puppy chews everything except designated toys", "Make toys more appealing with treats or frozen fillings. Puppy-proof the environment and redirect consistently."),
        ("Puppy swallows toy fragments", "Remove all toys showing wear immediately. Use size-appropriate, single-material toys and supervise all play."),
        ("Teething puppy is in visible discomfort", "Offer frozen damp flannels or freezable teething toys to soothe gums. Consult your vet if discomfort persists."),
    ],
    "tug|rope|fetch|play style": [
        ("Dog won't release during tug", "Train a reliable 'drop it' cue using high-value treat exchanges before resuming tug play."),
        ("Rope toy fibres coming loose", "Replace the toy immediately — ingested fibres can cause intestinal blockages. Switch to rubber tug toys."),
        ("Dog gets too excited during fetch", "Build in structured pauses between throws. Use a 'wait' cue before each throw to maintain calm."),
    ],
    "clean|hygien|wash|storage|organis": [
        ("Toy develops persistent odour despite washing", "The material may be degrading internally. Replace toys that smell after thorough cleaning — odour indicates bacterial growth."),
        ("Mould appears on toys", "Ensure toys dry completely after washing. Store in ventilated containers, not sealed bags."),
        ("Dog avoids toys after washing", "The cleaning product scent may be off-putting. Rinse thoroughly or use fragrance-free detergent."),
    ],
    "scent|smell|nosework|snuffle": [
        ("Dog paws at snuffle mat aggressively", "The mat may be too challenging. Start with treats placed on top and gradually hide them deeper."),
        ("Dog eats the snuffle mat fabric", "Switch to a heavier, rubber-based scent toy and supervise all sessions."),
        ("Dog loses interest in nosework quickly", "Vary the hiding locations and difficulty. Short, frequent sessions maintain motivation better than long ones."),
    ],
    "safety|hazard|toxic|risk": [
        ("Squeaker becomes exposed during play", "Remove the toy immediately. Squeakers are a serious choking hazard — switch to squeakerless alternatives."),
        ("Dog has allergic reaction after playing with new toy", "Remove the toy, note the material, and consult your vet. Some dogs react to dyes or chemical coatings."),
        ("Toy paint is flaking or peeling", "Discard immediately. Ingesting paint flakes poses toxicity risks."),
    ],
    "rotation|boredom|interest|engaged": [
        ("Dog ignores rotated-in toys", "Re-introduce with a game or treat stuffing to rebuild interest. Not all dogs respond to rotation equally."),
        ("Owner forgets to rotate toys", "Set a weekly reminder. Keep a simple log of which toys are in and out to maintain the system."),
        ("Dog only wants one specific toy", "Respect the preference but ensure the favoured toy stays in good condition. Offer variety alongside, not instead of, the favourite."),
    ],
    "indoor|outdoor|crate|space": [
        ("Toy causes damage indoors", "Switch to soft or lightweight indoor-specific toys. Reserve hard or bouncy toys for outdoor use."),
        ("Dog refuses to play in crate", "Build positive associations first — place treats and familiar items inside before introducing crate-specific toys."),
        ("Outdoor toy gets muddy and dog brings inside", "Keep an outdoor toy basket separately. Clean toys before allowing them indoors."),
    ],
    "multi.*dog|resource guard|sharing": [
        ("Dogs fight over a specific toy", "Remove the trigger toy entirely. Provide separate play sessions with individual toys until guarding behaviour reduces."),
        ("One dog dominates all toys", "Feed and play with dogs separately. Ensure each dog has protected access to enrichment."),
        ("New dog disrupts existing toy dynamics", "Introduce shared play gradually with supervision. Maintain individual toy allocations during the transition period."),
    ],
    "cat|feline": [
        ("Cat ignores new toy completely", "Try different movement patterns — drag, flick, or hide the toy. Cats prefer prey-like motion over static objects."),
        ("Cat eats string or ribbon from toys", "Remove all string-based toys immediately. Ingested linear objects can cause serious intestinal damage."),
        ("Cat only plays at night, disturbing household", "Provide an intensive play session before bedtime to tire your cat out during your waking hours."),
    ],
    "DIY|homemade": [
        ("Homemade toy falls apart quickly", "Reinforce construction and test durability before giving to your dog. Accept that DIY toys need more frequent replacement."),
        ("Dog ingests part of DIY toy", "Consult your vet immediately. Review materials used and switch to safer alternatives."),
        ("Unsure if DIY materials are safe", "When in doubt, do not use it. Stick to untreated natural cotton, food-grade silicone, and non-toxic materials only."),
    ],
}

DOG_TOYS_SCENARIOS = {
    "default": [
        ("If your dog is a power chewer who destroys everything", "Focus on solid rubber kongs, thick nylon bones, and treat-dispensing toys. Avoid plush, rope, and thin plastic entirely. Replace at first signs of wear."),
        ("If you have a low-energy dog or a senior with limited mobility", "Prioritise scent-based enrichment like snuffle mats and gentle puzzle feeders. Frozen stuffed kongs provide long-lasting calm engagement without physical strain."),
        ("If your dog plays alone while you are at work", "Choose self-play options such as treat-dispensing balls and frozen kongs. Avoid toys with detachable parts when unsupervised. Implement a rotation to prevent boredom."),
        ("If you have multiple dogs with different play styles", "Provide individual toy sets matched to each dog's size and play preference. Supervise shared play sessions and separate dogs showing resource guarding."),
    ],
    "puzzle|mental|enrichment|cognitive|stimulat": [
        ("If your dog is new to puzzle toys", "Start with the simplest level — treats visible and easy to access. Build complexity gradually over weeks, not days."),
        ("If your dog is a puzzle expert who solves everything quickly", "Combine multiple puzzles, freeze treats inside, or create multi-step challenges that link several toys together."),
        ("If your dog gets frustrated and gives up", "Reduce difficulty immediately. Success should come within 1-2 minutes at first. Frustration destroys motivation for future sessions."),
        ("If you want enrichment for a dog with limited mobility", "Choose stationary puzzles, lick mats, and nosework activities that require minimal physical movement."),
    ],
    "chew|destruct|tough|indestruc|durabl": [
        ("If your dog destroys toys in under 10 minutes", "Invest in heavy-duty rubber toys (solid, not hollow). Accept that no toy is eternal — budget for regular replacements."),
        ("If your dog is a moderate chewer", "Mid-range rubber and reinforced fabric toys offer good value. Monitor for wear and replace proactively."),
        ("If your dog barely chews at all", "Plush toys and softer options work well. Focus on comfort and play engagement rather than durability."),
    ],
    "senior|old|age|mobility|limited": [
        ("If your senior dog has dental issues", "Provide soft, flexible toys and lick mats. Avoid anything that requires strong biting pressure."),
        ("If your senior dog seems uninterested in everything", "Try scent-enrichment activities — hide treats around the room or use nosework games that tap into their strongest remaining sense."),
        ("If your dog has arthritis or joint pain", "Bring enrichment to your dog rather than expecting them to move. Stationary puzzle feeders and snuffle mats work well at their resting spot."),
    ],
    "puppy|young|teething": [
        ("If your puppy is teething and miserable", "Offer frozen damp flannels, freezable rubber toys, and cold carrot sticks (under supervision) to soothe sore gums."),
        ("If your puppy chews everything except toys", "Make toys more rewarding than household items — stuff with treats, play together, and redirect consistently."),
        ("If you are preparing a toy kit for a new puppy", "Include a mix of teething toys, a soft comfort toy, a simple puzzle feeder, and an age-appropriate tug toy."),
    ],
    "tug|rope|fetch|play style": [
        ("If your dog prefers tug above all other play", "Use tug as a training reward. Establish clear start and stop rules with a reliable 'drop it' cue."),
        ("If your dog loves fetch but gets overexcited", "Implement structured fetch with pauses, sits, and waits between throws to maintain calm arousal levels."),
        ("If your dog enjoys solo play", "Provide self-rewarding toys like treat dispensers and puzzle feeders that offer engagement without a human partner."),
    ],
    "clean|hygien|wash|storage|organis": [
        ("If you have limited storage space", "Use a single breathable basket and rotate a small selection of 4-5 clean toys at a time."),
        ("If your dog's toys smell despite regular cleaning", "Replace porous materials more frequently. Switch to non-porous rubber or silicone that resists bacterial buildup."),
        ("If you have multiple dogs sharing toys", "Increase cleaning frequency to weekly minimum. Label toy baskets per dog if resource guarding is a concern."),
    ],
    "safety|hazard|toxic|risk": [
        ("If your dog has a history of swallowing toy parts", "Use only one-piece solid rubber toys. Eliminate all toys with squeakers, stuffing, or detachable components."),
        ("If you are choosing toys for unsupervised play", "Select only items rated for solo use — solid kongs, frozen treat toys, and heavy-duty puzzle feeders with no removable parts."),
        ("If your dog has allergies or sensitivities", "Choose unscented, undyed, natural rubber options. Introduce one new toy at a time and monitor for reactions."),
    ],
    "cat|feline": [
        ("If your cat only plays for brief bursts", "This is normal feline behaviour. Provide 2-3 short interactive sessions daily rather than expecting extended play."),
        ("If your indoor cat seems bored", "Create vertical play spaces, window perches, and rotate toys weekly. Add puzzle feeders for mealtime enrichment."),
        ("If you have multiple cats with different energy levels", "Provide both active play opportunities and calm enrichment spots. Ensure each cat has access to resources without competition."),
    ],
    "DIY|homemade": [
        ("If you want to save money on dog toys", "Use clean, sturdy household items — old t-shirt braids, muffin tin puzzles, and frozen stuffed items are safe and cheap."),
        ("If you enjoy crafting for your dog", "Focus on non-toxic materials and test durability thoroughly. Never leave DIY toys unsupervised until proven safe."),
        ("If your dog has special needs", "Custom DIY options can address specific requirements that commercial toys miss. Consult your vet about material safety."),
    ],
    "scent|smell|nosework|snuffle": [
        ("If your dog is a beginner at nosework", "Start with visible treats and simple hiding spots. Build to more complex scent challenges over several weeks."),
        ("If your dog is physically limited but mentally alert", "Nosework is ideal — it provides intense mental engagement with minimal physical demand."),
        ("If you want to use scent games as daily enrichment", "Rotate between snuffle mats, scatter feeding, and indoor nosework trails to maintain variety."),
    ],
    "rotation|boredom|interest|engaged": [
        ("If your dog seems bored despite having many toys", "Reduce visible options to 3-4 and rotate weekly. Abundance paradoxically reduces engagement."),
        ("If rotation isn't working for your dog", "Your dog may have strong preferences — respect them. Ensure the favourite toy is always available alongside rotated options."),
        ("If you travel frequently with your dog", "Maintain a small travel toy kit with 2-3 versatile favourites that provide comfort and enrichment in unfamiliar settings."),
    ],
    "indoor|outdoor|crate|space": [
        ("If you live in a small flat with a large dog", "Focus on compact enrichment — puzzle feeders, snuffle mats, and frozen kongs that don't require throwing space."),
        ("If your dog spends time in a crate during the day", "Provide crate-safe toys: frozen stuffed kongs, lick mats, and sturdy chew toys without detachable parts."),
        ("If your garden is the main play space", "Use durable, washable outdoor toys and bring them inside for cleaning regularly to prevent bacterial buildup."),
    ],
    "multi.*dog|resource guard|sharing": [
        ("If one dog guards toys from others", "Provide separate play areas and individual toy access. Consult an ABTC-registered behaviourist if guarding behaviour intensifies."),
        ("If you are introducing a new dog to the household", "Keep toy interactions supervised initially. Maintain existing dogs' toy access and introduce shared play gradually."),
        ("If your dogs happily share most toys", "Continue supervised sharing but maintain individual high-value items that each dog can access privately."),
    ],
}

# ── Dog Training Decision Support Content ──────────────────────────────────

DOG_TRAINING_EVAL = {
    "default": [
        "Method alignment with learning science — Prioritise approaches backed by peer-reviewed behavioural research and endorsed by organisations like the ABTC",
        "Safety for dog and handler — Ensure the method does not cause physical pain, fear, or chronic stress to your dog",
        "Suitability for your dog's temperament — Consider whether the approach matches your dog's confidence level, anxiety triggers, and previous learning history",
        "Consistency requirements — Assess whether all household members can apply the method reliably and uniformly",
        "Time investment — Understand the realistic daily time commitment needed for meaningful progress",
        "Professional guidance needs — Determine whether you need a qualified trainer (ABTC-registered) or can progress independently",
    ],
    "treat|reward|reinforce": [
        "Treat value hierarchy — Understand which treats motivate your dog most and reserve high-value options for challenging tasks",
        "Calorie management — Factor training treat calories into your dog's daily food allowance to prevent weight gain",
        "Timing accuracy — Reward delivery within 1-2 seconds of the desired behaviour for effective association",
        "Fading strategy — Plan how to gradually reduce treat frequency while maintaining the learned behaviour",
        "Alternative reward options — Consider using play, praise, or life rewards alongside food reinforcement",
    ],
    "lead|leash|harness|walk": [
        "Equipment fit — Ensure the lead, harness, or collar fits correctly without causing rubbing or restricted breathing",
        "Control vs comfort balance — Choose equipment that gives you adequate control without causing your dog discomfort",
        "Training compatibility — Select equipment that supports your training approach rather than replacing it",
        "Durability for your dog's size — Match equipment strength to your dog's weight and pulling force",
        "Transition planning — Have a strategy for moving from training equipment to everyday gear as behaviour improves",
    ],
    "behavio|body language|communication|signal": [
        "Observation accuracy — Learn to distinguish between similar signals that have different meanings depending on context",
        "Context awareness — Always interpret body language within the full situation, not as isolated signals",
        "Response appropriateness — Match your response to the intensity and urgency of your dog's communication",
        "Stress signal recognition — Prioritise learning the subtle early signs of discomfort before escalation occurs",
        "Consistency in your signals — Ensure your own body language and cues are clear and consistent for your dog",
    ],
    "sociali|puppy|exposure|confidence": [
        "Quality over quantity — Prioritise positive, controlled experiences over sheer number of exposures",
        "Critical period awareness — Understand the socialisation window timing (typically 3-14 weeks) and its significance",
        "Pace of exposure — Let your puppy set the pace and never force interactions that cause visible stress",
        "Environment selection — Choose controlled, predictable settings for early socialisation sessions",
        "Recovery monitoring — Watch for signs of overwhelm and provide adequate rest between socialisation outings",
    ],
    "equipment|tool|collar|clicker": [
        "Evidence base — Choose tools supported by behavioural science rather than tradition or marketing claims",
        "Welfare impact — Assess whether the tool causes any aversive effects on your dog's physical or emotional wellbeing",
        "Skill requirement — Consider your own competence level and whether you need professional guidance to use the tool correctly",
        "Replacement pathway — Plan when and how to phase out training-specific equipment as your dog progresses",
        "Cost vs longevity — Balance initial investment against how long the tool will remain useful in your training journey",
    ],
}

DOG_TRAINING_TROUBLESHOOT = {
    "default": [
        ("Dog doesn't respond to cues in new environments", "Practice in gradually more distracting settings. Start in a quiet room, then the garden, then a quiet street, building up systematically."),
        ("Training progress has stalled", "Review your criteria — you may have increased difficulty too quickly. Go back to the last successful level and progress more gradually."),
        ("Dog is fearful during training sessions", "Stop immediately and assess what is causing fear. Reduce environmental stressors and consult an ABTC-registered behaviourist if fear persists."),
        ("Multiple household members train inconsistently", "Hold a family training meeting to agree on cues, rules, and approaches. Consistency across all handlers is essential for clear learning."),
        ("Dog seems to 'know' a command but refuses to comply", "Dogs do not refuse out of spite. Check for pain, fear, confusion, or insufficient motivation. Adjust the environment or reward value."),
    ],
    "treat|reward|reinforce": [
        ("Dog only performs for treats", "You may need to fade treats more gradually. Use variable reinforcement schedules and introduce life rewards like play and access to sniff spots."),
        ("Dog is gaining weight from training treats", "Use tiny pea-sized pieces, deduct treat calories from meals, or switch to part of their daily kibble allowance."),
        ("Dog won't take treats in stressful situations", "This indicates the dog is over-threshold. Move further from the stressor until your dog can take treats calmly."),
    ],
    "lead|leash|harness|walk": [
        ("Dog pulls constantly on lead", "Stop walking when the lead goes taut. Resume only when it slackens. Reward loose-lead position consistently."),
        ("Dog lunges at other dogs on walks", "Increase distance from triggers and reward calm behaviour. Consult an ABTC-registered behaviourist for a structured desensitisation plan."),
        ("Harness causes chafing", "Check fit — ensure two fingers fit beneath all straps. Try a different style or padded design."),
    ],
    "behavio|body language|communication|signal": [
        ("Dog shows stress signals you don't understand", "Photograph or video the behaviour and consult a qualified behaviourist. Common subtle signals include lip licking, yawning, and whale eye."),
        ("Dog's behaviour changes suddenly", "Rule out medical causes first with a vet check. Pain, illness, and hormonal changes all affect behaviour."),
        ("Dog seems anxious in specific situations", "Identify triggers precisely and create a systematic desensitisation plan. Avoid flooding (forcing exposure)."),
    ],
    "sociali|puppy|exposure|confidence": [
        ("Puppy shows fear of strangers", "Allow the puppy to approach at their own pace. Never force greetings. Use treats at a comfortable distance."),
        ("Missed the socialisation window", "Socialisation can still occur after 14 weeks, but requires more patience and gradual positive exposure."),
        ("Puppy is overwhelmed at puppy class", "Speak to the trainer about reducing group size or taking breaks. Not all classes suit all puppies."),
    ],
    "equipment|tool|collar|clicker": [
        ("Dog is frightened of the clicker sound", "Use a softer marker (a verbal 'yes' or a pen click) until the dog habituates. Some dogs never tolerate sharp sounds."),
        ("Equipment doesn't seem to be helping", "The tool is never a substitute for training. Ensure you have a clear training plan and the tool supports, not replaces, the method."),
        ("Unsure which equipment to choose", "Consult an ABTC-registered trainer who can recommend tools based on your specific dog and training goals."),
    ],
}

DOG_TRAINING_SCENARIOS = {
    "default": [
        ("If you are a first-time dog owner", "Start with basic positive reinforcement techniques — reward desired behaviours with treats and praise. Consider enrolling in an ABTC-accredited puppy class for structured guidance."),
        ("If your dog has anxiety or fearfulness", "Prioritise building confidence through gradual, positive exposure. Avoid punishment-based methods entirely, as these worsen anxiety. Consult an ABTC-registered behaviourist."),
        ("If you have limited time for daily training", "Focus on 5-10 minute sessions twice daily rather than one long session. Incorporate training into daily routines like mealtime and walks."),
        ("If you are training an adult rescue dog", "Allow an adjustment period of at least two weeks before starting formal training. Focus on building trust and learning your dog's individual triggers and preferences."),
    ],
    "treat|reward|reinforce": [
        ("If your dog is food-motivated", "Use treat-based training as your primary tool but plan a fading schedule to prevent dependency."),
        ("If your dog is not food-motivated", "Use play, toys, or access to activities as alternative rewards. Every dog has something that motivates them."),
        ("If you are training multiple behaviours simultaneously", "Use different reward levels for different difficulty levels — easy tasks get kibble, challenging tasks get high-value treats."),
    ],
    "lead|leash|harness|walk": [
        ("If your dog is a strong puller", "Consider a front-clip harness combined with consistent loose-lead training. Avoid equipment that relies solely on discomfort to reduce pulling."),
        ("If your dog is reactive on lead", "Increase distance from triggers, use high-value rewards for calm behaviour, and follow a structured counter-conditioning programme."),
        ("If you walk in busy urban areas", "Practise lead skills in quieter settings first, then gradually introduce more challenging environments as your dog's skills improve."),
    ],
    "sociali|puppy|exposure|confidence": [
        ("If you have a young puppy under 14 weeks", "Prioritise safe, positive exposure to a wide range of people, animals, surfaces, and sounds during this critical developmental window."),
        ("If your puppy missed early socialisation", "Proceed with gentle, gradual exposure. Progress will be slower but meaningful improvement is still very achievable."),
        ("If your puppy is naturally confident", "Continue providing varied experiences to maintain confidence. Even bold puppies benefit from structured socialisation."),
    ],
}

# ── Dog Grooming Decision Support Content ──────────────────────────────────

DOG_GROOMING_EVAL = {
    "default": [
        "Coat type compatibility — Match grooming tools and techniques to your dog's specific coat type (smooth, double, wire, curly, or long)",
        "Skin sensitivity — Assess your dog's skin condition and choose products formulated for their sensitivity level",
        "Frequency requirements — Establish a realistic grooming schedule based on your dog's breed, lifestyle, and coat condition",
        "Tool quality — Invest in well-made tools that perform effectively without causing discomfort or coat damage",
        "Professional vs home grooming — Determine which tasks you can handle confidently at home and which require professional assistance",
    ],
    "brush|coat|fur|shed|deshed": [
        "Bristle type match — Select brush bristles (pin, slicker, bristle, or rubber) based on coat texture and length",
        "Pressure sensitivity — Learn the correct pressure for your dog's coat to remove tangles without pulling skin",
        "Frequency calibration — Double-coated breeds may need daily brushing during shedding season but weekly otherwise",
        "Direction technique — Brush in the direction of hair growth for comfort, then against for thorough undercoat removal",
        "Mat detection — Check for hidden mats in armpits, behind ears, and around the collar area before general brushing",
    ],
    "nail|trim|clip|grind": [
        "Tool selection — Choose between guillotine clippers, scissor-style clippers, or electric grinders based on your dog's nail type and your confidence",
        "Quick identification — Learn to identify the quick (blood vessel) in both light and dark nails to avoid painful cuts",
        "Frequency assessment — Most dogs need nail trims every 2-4 weeks, but lifestyle and surface exposure affect growth rate",
        "Desensitisation level — Ensure your dog is comfortable with paw handling before attempting nail care",
        "Emergency preparedness — Keep styptic powder on hand in case of accidental quick cuts",
    ],
    "shampoo|bath|wash|skin": [
        "pH balance — Dog skin has a different pH to human skin; always use species-specific shampoo formulations",
        "Ingredient safety — Avoid products containing parabens, artificial fragrances, and sodium lauryl sulphate",
        "Condition-specific needs — Match shampoo type to any existing skin conditions (dry skin, allergies, parasites)",
        "Frequency balance — Overbathing strips natural oils; most dogs need bathing every 4-6 weeks unless medically indicated",
        "Rinsing thoroughness — Residual shampoo causes irritation; rinse until water runs completely clear",
    ],
    "cat|feline": [
        "Temperament assessment — Gauge your cat's tolerance for handling before beginning any grooming session",
        "Coat maintenance needs — Long-haired cats need daily brushing; short-haired breeds typically need weekly sessions",
        "Nail anatomy — Cat claws retract; learn the gentle squeeze technique to extend them safely for trimming",
        "Bathing necessity — Most cats self-groom effectively; bathing is rarely needed unless medically required",
        "Stress minimisation — Keep sessions short and positive. Stop immediately if your cat shows signs of distress",
    ],
}

DOG_GROOMING_TROUBLESHOOT = {
    "default": [
        ("Dog becomes aggressive during grooming", "Stop immediately — aggression during grooming often indicates pain or fear. Consult your vet to rule out pain, then work with an ABTC-registered behaviourist on desensitisation."),
        ("Dog's coat mats frequently despite brushing", "You may be brushing only the surface. Use a slicker brush to reach the undercoat, and work through tangles with a dematting comb from the tips upward."),
        ("Dog develops skin irritation after grooming", "Check your products for harsh chemicals. Switch to hypoallergenic, fragrance-free options and reduce bathing frequency."),
        ("Owner is nervous about grooming tasks", "Start with the easiest tasks and build confidence gradually. Professional groomers can demonstrate techniques and handle complex tasks."),
    ],
    "brush|coat|fur|shed|deshed": [
        ("Brush causes discomfort or yelping", "You may be pressing too hard or using the wrong bristle type. Switch to a softer brush and reduce pressure."),
        ("Excessive shedding despite regular brushing", "Some shedding is normal, especially seasonally. If shedding seems abnormal, consult your vet to rule out dietary or health issues."),
        ("Undercoat remains tangled after brushing", "Use an undercoat rake or deshedding tool specifically designed to reach the dense underlayer."),
    ],
    "nail|trim|clip|grind": [
        ("Accidentally cut the quick", "Apply styptic powder immediately and apply gentle pressure. Stay calm — your dog will pick up on your anxiety."),
        ("Dog pulls paw away during trimming", "Practise paw handling without clippers first. Reward calm behaviour. Trim one nail at a time with breaks between."),
        ("Nails are too overgrown to trim safely", "Trim small amounts frequently (every 3-4 days) to encourage the quick to recede gradually. Consult a vet if severely overgrown."),
    ],
    "shampoo|bath|wash|skin": [
        ("Dog panics in the bath", "Use treats and a calm voice. Start with shallow water and a non-slip mat. Build positive associations gradually over multiple sessions."),
        ("Skin becomes dry and flaky after bathing", "Reduce bathing frequency and switch to a moisturising, soap-free shampoo. Consult your vet if dryness persists."),
        ("Shampoo doesn't seem to clean effectively", "You may need a pre-rinse to remove surface dirt before applying shampoo. Ensure you're using enough product for your dog's coat density."),
    ],
    "cat|feline": [
        ("Cat scratches or bites during grooming", "Never force grooming on a resistant cat. Use short sessions, favourite treats, and stop at the first sign of agitation."),
        ("Cat's coat has persistent mats", "For severe matting, consult a professional groomer. Pulling mats can tear delicate skin."),
        ("Cat vomits hairballs frequently", "Increase brushing frequency to reduce loose hair ingestion. Consult your vet about hairball management supplements."),
    ],
}

DOG_GROOMING_SCENARIOS = {
    "default": [
        ("If you have a double-coated breed", "Invest in an undercoat rake and slicker brush. Brush thoroughly 2-3 times weekly, increasing to daily during shedding season. Never shave a double coat as it disrupts temperature regulation."),
        ("If your dog has sensitive skin or allergies", "Use hypoallergenic, fragrance-free products and reduce bathing frequency. Consult your vet before trying new grooming products."),
        ("If you are grooming a puppy for the first time", "Start with gentle handling exercises well before actual grooming is needed. Make every early experience positive with treats and short sessions."),
        ("If you are considering professional grooming", "Visit the salon beforehand, check qualifications, and ask about their approach to anxious dogs. A good groomer will discuss your dog's needs before starting."),
    ],
    "brush|coat|fur|shed|deshed": [
        ("If your dog has a smooth, short coat", "A rubber curry brush or soft bristle brush used weekly is usually sufficient."),
        ("If your dog has a long or silky coat", "Use a pin brush for daily maintenance and a wide-tooth comb for tangles. Focus on tangle-prone areas."),
        ("If your dog sheds heavily", "During shedding season, brush daily with a deshedding tool. Regular grooming reduces household hair significantly."),
    ],
    "nail|trim|clip|grind": [
        ("If you have never trimmed nails before", "Ask your vet or groomer to demonstrate the technique first. Start with just one nail per session to build confidence."),
        ("If your dog has dark nails", "Trim small amounts at a time and look for the chalky ring that indicates you are approaching the quick."),
        ("If your dog has a fear of nail clipping", "Try a scratch board or nail grinder as alternatives. Desensitise gradually with counter-conditioning."),
    ],
    "shampoo|bath|wash|skin": [
        ("If your dog has a skin condition", "Use a veterinary-recommended medicated shampoo and follow the specific contact-time instructions carefully."),
        ("If your dog rarely gets dirty", "A bath every 6-8 weeks is typically sufficient. Overbathing causes more problems than it solves."),
        ("If you prefer natural grooming products", "Look for oatmeal-based or coconut oil shampoos. Check that 'natural' claims are backed by actual ingredient transparency."),
    ],
    "cat|feline": [
        ("If your cat has never been groomed before", "Begin with very gentle, brief brush strokes during relaxed moments. Build tolerance gradually over weeks."),
        ("If your cat has long, mat-prone fur", "Brush daily to prevent mats from forming. Prevention is far easier and less stressful than removal."),
        ("If you need to bathe your cat", "Only bathe when medically necessary. Use warm water, a calm environment, and have everything prepared before starting."),
    ],
}


# ── Comparison Table Definitions ───────────────────────────────────────────
# Target: 30-40 new tables across 3 clusters

COMPARISON_TABLES = {
    # ── DOG TOYS CLUSTER (15-18 tables) ────────────────────────────────────

    # Play style comparisons
    3: {  # Dog Toys UK pillar page
        "intro": "Different play types serve different developmental and enrichment needs. Understanding these distinctions helps you choose activities that match your dog's natural preferences.",
        "headers": ["Play Type", "Physical Demand", "Mental Engagement", "Best Environment", "Supervision Level"],
        "rows": [
            ["Fetch", "High", "Low to moderate", "Open outdoor space", "Active supervision"],
            ["Tug-of-war", "Moderate to high", "Moderate", "Indoor or outdoor", "Active supervision"],
            ["Puzzle solving", "Low", "High", "Indoor preferred", "Minimal once learned"],
            ["Scent work", "Low to moderate", "Very high", "Any environment", "Initial guidance needed"],
            ["Chewing", "Low", "Low to moderate", "Any environment", "Periodic checks"],
            ["Chase games", "High", "Moderate", "Open outdoor space", "Active supervision"],
        ],
    },
    5950: {  # Dog Toy Durability Guide
        "intro": "Toy materials vary significantly in their lifespan depending on a dog's chewing intensity. This comparison helps match material choices to your dog's chewing habits.",
        "headers": ["Material", "Light Chewer Lifespan", "Moderate Chewer", "Heavy Chewer", "Cleaning Method"],
        "rows": [
            ["Natural rubber", "6-12 months", "3-6 months", "1-3 months", "Dishwasher safe"],
            ["Nylon", "12+ months", "6-12 months", "2-4 months", "Hand wash"],
            ["Cotton rope", "3-6 months", "1-3 months", "Days to weeks", "Machine wash"],
            ["Plush fabric", "6-12 months", "1-4 weeks", "Hours to days", "Machine wash"],
            ["Thermoplastic rubber", "6-12 months", "3-6 months", "1-2 months", "Dishwasher safe"],
            ["Canvas/denim", "3-6 months", "1-3 months", "1-4 weeks", "Machine wash"],
        ],
    },
    5946: {  # Dog Toy Materials Compared
        "intro": "Different toy materials suit different play contexts and dog temperaments. Understanding environmental considerations helps inform purchasing decisions.",
        "headers": ["Material", "Indoor Use", "Outdoor Use", "Water Resistance", "Environmental Impact"],
        "rows": [
            ["Natural rubber", "Excellent", "Excellent", "High", "Biodegradable over time"],
            ["Recycled plastic", "Good", "Good", "High", "Reduces landfill waste"],
            ["Organic cotton", "Excellent", "Fair", "Low", "Compostable"],
            ["Nylon", "Good", "Good", "High", "Non-biodegradable"],
            ["Hemp fibre", "Good", "Good", "Moderate", "Sustainable crop"],
            ["Bamboo fibre", "Good", "Fair", "Low", "Fast-growing resource"],
        ],
    },
    5476: {  # Mental Stimulation Toys
        "intro": "Puzzle toy formats offer different types of mental challenge. This overview helps match enrichment style to your dog's problem-solving experience.",
        "headers": ["Puzzle Type", "Difficulty Range", "Session Length", "Solo Play Suitable", "Best For"],
        "rows": [
            ["Treat-dispensing ball", "Easy to moderate", "10-30 minutes", "Yes", "Food-motivated dogs"],
            ["Sliding puzzle board", "Moderate to hard", "5-20 minutes", "With training", "Problem solvers"],
            ["Snuffle mat", "Easy", "5-15 minutes", "Yes", "Scent-driven dogs"],
            ["Frozen stuffed toy", "Easy to moderate", "15-45 minutes", "Yes", "Anxious or teething dogs"],
            ["Multi-step puzzle", "Hard", "10-30 minutes", "With experience", "Advanced learners"],
            ["Lick mat", "Easy", "10-20 minutes", "Yes", "Calming enrichment"],
        ],
    },
    5473: {  # Senior Dog Toys
        "intro": "Senior dogs have different enrichment needs based on their physical capabilities and cognitive health. Matching activity type to your dog's condition ensures safe, effective stimulation.",
        "headers": ["Activity Type", "Physical Demand", "Cognitive Benefit", "Joint Impact", "Dental Safety"],
        "rows": [
            ["Snuffle mat foraging", "Very low", "High", "Minimal", "Safe"],
            ["Frozen kong", "Low", "Moderate", "Minimal", "Gentle on teeth"],
            ["Gentle tug (soft toy)", "Low to moderate", "Moderate", "Low", "Soft materials only"],
            ["Scent trail games", "Low", "Very high", "Low", "Not applicable"],
            ["Lick mat", "Very low", "Low to moderate", "None", "Safe"],
            ["Slow puzzle feeder", "Very low", "High", "None", "Safe"],
        ],
    },
    5421: {  # Puppy-Safe Dog Toys
        "intro": "Puppy toy needs change as they develop through growth stages. Choosing age-appropriate options supports healthy development while minimising safety risks.",
        "headers": ["Growth Stage", "Recommended Toy Types", "Materials to Prioritise", "Toys to Avoid", "Supervision Level"],
        "rows": [
            ["8-12 weeks", "Soft plush, teething rings", "Soft rubber, fleece", "Hard nylon, small balls", "Constant"],
            ["3-4 months", "Teething toys, gentle tug", "Textured rubber, cotton rope", "Rawhide, brittle plastic", "Constant"],
            ["4-6 months", "Puzzle feeders, larger chews", "Durable rubber, canvas", "Toys with small parts", "High"],
            ["6-9 months", "Interactive toys, fetch", "Medium-grade rubber", "Thin plastic, tiny toys", "Moderate to high"],
            ["9-12 months", "Adult-transition toys", "Breed-appropriate durability", "Undersized toys", "Moderate"],
        ],
    },
    5422: {  # Indoor vs Outdoor Dog Toys
        "intro": "Choosing between indoor and outdoor toy use depends on more than just space availability. Each environment presents distinct safety and engagement considerations.",
        "headers": ["Factor", "Indoor Play", "Outdoor Play", "Key Consideration"],
        "rows": [
            ["Space needed", "Minimal to moderate", "Moderate to extensive", "Match toy size to play area"],
            ["Noise level", "Low preferred", "Less restricted", "Consider neighbours for both"],
            ["Weather exposure", "None", "UV, rain, mud", "Outdoor toys need weather resistance"],
            ["Supervision ease", "Easy to monitor", "Harder in large spaces", "Recall reliability matters outdoors"],
            ["Hygiene control", "Easier to maintain", "More contamination sources", "Clean outdoor toys before bringing inside"],
            ["Enrichment type", "Puzzles, nosework, gentle play", "Fetch, chase, exploration", "Vary activities across both settings"],
        ],
    },
    5509: {  # Pet Toy Safety
        "intro": "Different toy hazard categories present varying risk levels. Understanding these helps prioritise safety checks during regular toy inspections.",
        "headers": ["Hazard Type", "Risk Level", "Common Causes", "Prevention", "Warning Signs"],
        "rows": [
            ["Choking", "High", "Small parts, torn pieces", "Size-appropriate selection", "Pieces breaking off"],
            ["Intestinal blockage", "High", "Swallowed fragments", "Supervise, remove damaged toys", "Vomiting, lethargy"],
            ["Dental damage", "Moderate", "Overly hard materials", "Thumbnail pressure test", "Bleeding gums, tooth chips"],
            ["Toxic exposure", "Moderate", "Cheap dyes, untested materials", "Choose certified products", "Unusual odour, discolouration"],
            ["Strangulation", "Moderate", "Long strings, loops", "Supervised use only", "Fraying, stretched loops"],
            ["Skin irritation", "Low", "Rough textures, chemicals", "Wash before first use", "Redness, excessive scratching"],
        ],
    },
    4789: {  # Best Types of Dog Toys for Different Play Styles
        "intro": "Understanding the cost implications of different toy categories helps owners budget effectively while ensuring adequate enrichment variety.",
        "headers": ["Toy Category", "Typical Price Range", "Expected Lifespan", "Replacement Frequency", "Cost per Month (Estimate)"],
        "rows": [
            ["Basic rubber chew", "Low", "3-12 months", "Quarterly to annually", "Very low"],
            ["Puzzle feeder", "Moderate", "6-24 months", "Annually", "Low"],
            ["Plush toy", "Low to moderate", "Days to months", "Monthly for chewers", "Moderate to high"],
            ["Interactive electronic", "High", "6-18 months", "When broken", "Moderate"],
            ["Rope tug toy", "Low", "1-6 months", "Monthly to quarterly", "Low"],
            ["Frozen treat toy (kong-style)", "Moderate", "12-36 months", "Rarely", "Very low"],
        ],
    },
    6039: {  # Dog Toy Anxiety Reduction
        "intro": "Different calming enrichment approaches work through different mechanisms. Matching the method to your dog's specific anxiety type improves outcomes.",
        "headers": ["Calming Method", "Anxiety Type Suited", "Mechanism", "Duration of Effect", "Ease of Implementation"],
        "rows": [
            ["Frozen stuffed toy", "Separation, general", "Sustained licking = calming", "30-60 minutes", "Very easy"],
            ["Snuffle mat", "Mild anxiety, boredom", "Foraging = natural calming", "10-20 minutes", "Easy"],
            ["Lick mat with paste", "Acute stress, vet visits", "Repetitive licking = soothing", "10-30 minutes", "Very easy"],
            ["Scent enrichment", "General anxiety", "Olfactory engagement = grounding", "Varies", "Moderate"],
            ["Compression toy/wrap", "Noise phobia, travel", "Gentle pressure = calming", "As worn", "Easy"],
            ["Gentle puzzle feeder", "Mild anxiety, rehab", "Cognitive distraction", "15-30 minutes", "Easy"],
        ],
    },
    6045: {  # Safe Multi-Dog Toy Management
        "intro": "Managing toys in a multi-dog household requires understanding how different approaches affect social dynamics between dogs.",
        "headers": ["Management Approach", "Resource Guarding Risk", "Effort Required", "Best For", "Limitation"],
        "rows": [
            ["Separate toy sets per dog", "Low", "Moderate", "Dogs with guarding history", "Requires space and organisation"],
            ["Supervised shared play", "Moderate", "High", "Well-socialised dogs", "Requires constant attention"],
            ["Timed rotation between dogs", "Low to moderate", "Moderate", "Different-sized dogs", "Scheduling overhead"],
            ["Communal toy basket", "Higher", "Low", "Very bonded, confident dogs", "Not suitable for guarders"],
            ["Individual enrichment sessions", "Very low", "High", "Any multi-dog household", "Time-intensive for owner"],
        ],
    },
    6046: {  # Dog Toy Hygiene Schedules
        "intro": "Cleaning methods vary in effectiveness depending on the toy material. Choosing the right approach extends toy life while maintaining hygiene.",
        "headers": ["Material", "Recommended Method", "Cleaning Frequency", "Drying Time", "Disinfection Option"],
        "rows": [
            ["Solid rubber", "Dishwasher or boiling water", "Weekly", "1-2 hours", "Dilute vinegar soak"],
            ["Rope/cotton", "Machine wash (hot)", "Weekly", "Line dry fully", "Replace if smell persists"],
            ["Plush fabric", "Machine wash (gentle)", "Weekly to fortnightly", "Tumble dry low", "Not reliably disinfected"],
            ["Nylon", "Hand wash with soap", "Fortnightly", "1-2 hours", "Dilute bleach rinse"],
            ["Silicone", "Dishwasher or boiling water", "After each use", "30 minutes", "Boiling is sufficient"],
            ["Plastic", "Hand wash warm soapy water", "Weekly", "1 hour", "Dilute vinegar wipe"],
        ],
    },
    5483: {  # Dog Toy Lifespan
        "intro": "Knowing when to replace toys prevents safety incidents. These indicators apply across common toy categories.",
        "headers": ["Replacement Indicator", "Applies To", "Risk If Ignored", "How to Check"],
        "rows": [
            ["Visible cracks or tears", "Rubber, plastic", "Choking on fragments", "Visual inspection weekly"],
            ["Exposed squeaker", "Plush, rubber", "Swallowed squeaker", "Squeeze and feel for shifting"],
            ["Persistent odour after washing", "All materials", "Bacterial growth", "Smell test after cleaning"],
            ["Fraying or loose threads", "Rope, fabric", "Intestinal blockage", "Pull gently to test integrity"],
            ["Colour fading or flaking", "Painted items", "Toxin ingestion", "Rub surface, check for residue"],
            ["Reduced structural integrity", "All materials", "Unexpected breakage", "Flex and compress to test"],
        ],
    },
    5935: {  # Dog Toy Storage and Organisation
        "intro": "Different storage solutions offer trade-offs between accessibility, hygiene, and space efficiency. Choosing the right system depends on your household setup.",
        "headers": ["Storage Method", "Hygiene Rating", "Accessibility", "Space Needed", "Best For"],
        "rows": [
            ["Open breathable basket", "Moderate", "Excellent", "Floor space", "Daily rotation toys"],
            ["Sealed container", "High (if dry)", "Moderate", "Shelf or cupboard", "Clean stored toys"],
            ["Wall-mounted hooks", "Good (air-dried)", "Good", "Wall space only", "Rope and tug toys"],
            ["Drawer with dividers", "Good", "Moderate", "Furniture drawer", "Organised collections"],
            ["Outdoor waterproof box", "Low to moderate", "Good", "Garden/patio", "Outdoor-only toys"],
        ],
    },
    5938: {  # Enrichment Schedules for Dogs
        "intro": "Different enrichment activities suit different times of day based on energy levels and household routines. Planning prevents both under- and over-stimulation.",
        "headers": ["Time of Day", "Recommended Activity", "Energy Level Target", "Duration", "Supervision Needed"],
        "rows": [
            ["Morning (pre-walk)", "Puzzle feeder at breakfast", "Moderate focus", "10-15 minutes", "Minimal"],
            ["Mid-morning", "Training session or scent game", "Moderate to high", "10-20 minutes", "Active"],
            ["Afternoon", "Calm chew or lick mat", "Low", "20-40 minutes", "Periodic"],
            ["Pre-dinner", "Interactive play (fetch/tug)", "High", "15-20 minutes", "Active"],
            ["Evening", "Frozen kong or snuffle mat", "Low, winding down", "20-30 minutes", "Minimal"],
        ],
    },

    # ── DOG TRAINING CLUSTER (8-10 tables) ─────────────────────────────────

    4118: {  # Best Dog Training and Behaviour UK
        "intro": "Different training approaches have distinct characteristics and welfare implications. Understanding these distinctions helps owners choose methods aligned with current behavioural science.",
        "headers": ["Approach", "Core Principle", "Welfare Assessment", "Evidence Base", "UK Organisation Alignment"],
        "rows": [
            ["Positive reinforcement", "Reward desired behaviour", "Supports welfare", "Strong scientific support", "ABTC, RSPCA, BVA endorsed"],
            ["Negative punishment", "Remove reward for unwanted behaviour", "Generally acceptable", "Moderate evidence", "Accepted when proportionate"],
            ["Lure-reward", "Guide with food then fade lure", "Supports welfare", "Well-established", "Widely used in puppy classes"],
            ["Clicker training", "Precise marker for correct behaviour", "Supports welfare", "Strong scientific support", "ABTC endorsed"],
            ["Relationship-based", "Build cooperation through trust", "Supports welfare", "Growing evidence base", "Emerging recognition"],
            ["Aversive methods", "Use discomfort to suppress behaviour", "Welfare concerns", "Associated with fallout risks", "Opposed by RSPCA, BVA, ABTC"],
        ],
    },
    5512: {  # Dog Behaviour Explained
        "intro": "Dogs communicate through a system of body language signals that vary in intensity. Recognising signal categories helps owners respond appropriately before behaviour escalates.",
        "headers": ["Signal Category", "Examples", "What It Typically Means", "Recommended Response"],
        "rows": [
            ["Calming signals", "Lip licking, yawning, turning away", "Mild discomfort or de-escalation attempt", "Reduce pressure, give space"],
            ["Stress indicators", "Panting, whale eye, tucked tail", "Moderate anxiety or unease", "Remove from situation calmly"],
            ["Fear signals", "Cowering, trembling, ears flat", "Significant distress", "Create distance, do not force interaction"],
            ["Arousal signs", "Forward posture, stiff body, intense stare", "High excitement or alertness", "Redirect attention, manage environment"],
            ["Relaxation cues", "Soft eyes, loose body, play bow", "Comfort and willingness to engage", "Safe to interact normally"],
            ["Warning signals", "Growling, lip curling, air snapping", "Clear communication of boundary", "Respect the signal, do not punish"],
        ],
    },
    4792: {  # Puppy Socialisation
        "intro": "The socialisation process involves exposure to different categories of experiences. Each category has a different optimal approach and timeline.",
        "headers": ["Experience Category", "Optimal Window", "Exposure Method", "Signs of Positive Response", "Signs to Pause"],
        "rows": [
            ["People (varied ages, appearances)", "3-12 weeks", "Gradual, treat-paired introductions", "Approaches willingly, relaxed body", "Hiding, trembling, avoidance"],
            ["Other dogs (vaccinated, calm)", "3-14 weeks", "Controlled, supervised meetings", "Play bows, relaxed interaction", "Cowering, freezing, excessive submissive signals"],
            ["Surfaces and textures", "3-12 weeks", "Allow exploration at own pace", "Investigates confidently", "Refuses to walk, plants feet"],
            ["Sounds and environments", "3-14 weeks", "Start quiet, increase gradually", "Curious, recovers quickly", "Prolonged startle, panting, hiding"],
            ["Handling and grooming", "3-14 weeks", "Short sessions with treats", "Stays relaxed, accepts touch", "Struggling, mouthing, whale eye"],
            ["Travel and novel places", "8-16 weeks", "Short positive outings", "Explores with interest", "Shaking, refusing to leave vehicle"],
        ],
    },
    4791: {  # How to Choose the Right Dog Training Treats
        "intro": "Training treat selection involves balancing motivation, health impact, and practical handling. Different treat categories serve different training contexts.",
        "headers": ["Treat Category", "Motivation Level", "Calorie Impact", "Handling Ease", "Best Training Context"],
        "rows": [
            ["Regular kibble", "Low to moderate", "Minimal (part of meal)", "Excellent", "Easy, familiar tasks"],
            ["Commercial training treats", "Moderate", "Low per piece", "Good", "General training sessions"],
            ["Dried meat or fish", "High", "Moderate", "Good (can crumble)", "Challenging tasks or distractions"],
            ["Fresh meat or cheese", "Very high", "Moderate to high", "Messy", "Breakthrough moments, high distraction"],
            ["Vegetables (carrot, cucumber)", "Low", "Very low", "Good", "Food-obsessed dogs needing calorie control"],
            ["Commercial paste (tube)", "High", "Low per lick", "Excellent", "Sustained focus, lick-reward training"],
        ],
    },
    4125: {  # Best Dog Training Treats UK
        "intro": "Treat usage strategies affect both training effectiveness and long-term behaviour maintenance. Understanding when to apply each strategy supports structured progress.",
        "headers": ["Reward Strategy", "When to Use", "Advantage", "Risk If Overused", "Fading Plan"],
        "rows": [
            ["Continuous (every correct response)", "New behaviour learning", "Fast initial acquisition", "Creates treat dependency", "Move to variable once behaviour is reliable"],
            ["Variable (random correct responses)", "Maintaining learned behaviour", "Builds persistence", "Frustration if introduced too early", "Gradually increase randomness"],
            ["Differential (higher reward for better quality)", "Improving precision", "Sharpens behaviour quality", "Over-complexity", "Use for refinement only"],
            ["Life reward (access to desired activity)", "Real-world generalisation", "Natural and sustainable", "Delayed reinforcement timing", "Combine with food initially"],
            ["Jackpot (sudden large reward)", "Breakthrough moments", "Creates strong positive memory", "Inflation of expectations", "Reserve for genuine breakthroughs"],
        ],
    },
    4132: {  # Best Puppy Training Guide UK
        "intro": "Puppy training milestones typically follow a developmental timeline. Understanding realistic expectations at each stage reduces frustration for both owner and puppy.",
        "headers": ["Age Range", "Realistic Expectations", "Priority Skills", "Session Length", "Common Mistake"],
        "rows": [
            ["8-10 weeks", "Very short attention span", "Name recognition, toilet habits", "1-2 minutes", "Expecting too much too soon"],
            ["10-12 weeks", "Beginning to learn associations", "Sit, come when called (close range)", "2-3 minutes", "Punishing accidents"],
            ["3-4 months", "Can follow simple cues", "Loose lead, basic recall, settle", "3-5 minutes", "Insufficient socialisation"],
            ["4-6 months", "Testing boundaries (adolescence begins)", "Reliable recall, impulse control", "5-10 minutes", "Reducing training during adolescence"],
            ["6-12 months", "Adolescent regression is normal", "Proofing in distractions, duration", "10-15 minutes", "Assuming the dog 'should know by now'"],
        ],
    },
    5036: {  # Understanding Cat Play Behaviour
        "intro": "Cat play behaviours reflect different hunting instincts. Recognising these patterns helps owners choose appropriate interactive toys and activities.",
        "headers": ["Play Pattern", "Hunting Instinct Served", "Typical Toy Preference", "Session Approach", "Engagement Duration"],
        "rows": [
            ["Stalking and pouncing", "Bird/mouse hunting", "Feather wands, moving targets", "Slow approach, sudden pounce", "5-10 minutes"],
            ["Batting and swatting", "Insect catching", "Small balls, dangling items", "Quick movements", "2-5 minutes"],
            ["Grabbing and bunny kicking", "Prey capture", "Stuffed kick toys", "Offer toy to grab", "1-3 minutes per bout"],
            ["Chasing", "Pursuit prey drive", "Laser pointer (with physical reward), toy on string", "Fast movement away from cat", "3-8 minutes"],
            ["Hiding and ambush", "Concealment hunting", "Tunnel toys, boxes, paper bags", "Hide-and-seek setup", "Intermittent throughout day"],
        ],
    },
    5458: {  # Cat Scratching Behaviour
        "intro": "Scratching surface preferences vary between individual cats. Providing the right type in the right location reduces unwanted furniture damage.",
        "headers": ["Surface Type", "Cat Preference Level", "Durability", "Placement", "Maintenance"],
        "rows": [
            ["Sisal rope (vertical)", "Very popular", "High", "Near resting areas, entrances", "Replace when frayed"],
            ["Corrugated cardboard", "Popular", "Low to moderate", "Floor or angled", "Replace when shredded"],
            ["Carpet-covered post", "Moderate", "High", "Near furniture targets", "Vacuum regularly"],
            ["Wood/bark log", "Variable", "High", "Indoor or outdoor", "Minimal — natural weathering"],
            ["Sisal fabric (flat)", "Popular", "Moderate to high", "Wall-mounted or floor", "Replace when worn smooth"],
        ],
    },

    # ── DOG GROOMING CLUSTER (7-8 tables) ──────────────────────────────────

    4563: {  # Dog Grooming Basics
        "intro": "Different coat types require distinct grooming approaches. Matching your technique and tools to your dog's coat ensures effective grooming without causing discomfort.",
        "headers": ["Coat Type", "Brush Type Needed", "Brushing Frequency", "Professional Grooming Frequency", "Common Issues"],
        "rows": [
            ["Smooth/short (e.g., Boxer)", "Rubber curry, soft bristle", "Weekly", "Quarterly or as needed", "Skin irritation from over-brushing"],
            ["Double coat (e.g., Labrador)", "Undercoat rake, slicker", "2-3 times weekly, daily when shedding", "Seasonal deshed sessions", "Matting in undercoat"],
            ["Wire/rough (e.g., Border Terrier)", "Slicker, stripping knife", "2-3 times weekly", "Hand-stripping quarterly", "Coat softening if clipped instead of stripped"],
            ["Long/silky (e.g., Shih Tzu)", "Pin brush, wide-tooth comb", "Daily", "Every 4-6 weeks", "Tangling and matting"],
            ["Curly/wool (e.g., Poodle)", "Slicker, metal comb", "Daily to every other day", "Every 4-6 weeks", "Matting close to skin"],
            ["Hairless (e.g., Chinese Crested)", "Soft cloth", "Skin cleaning 2-3 times weekly", "Rarely needed", "Sunburn, skin dryness"],
        ],
    },
    4064: {  # Best Dog Brushes UK
        "intro": "Brush types serve different purposes in a grooming routine. Understanding each tool's function helps build an effective grooming kit.",
        "headers": ["Brush Type", "Primary Function", "Best Coat Type", "Ease of Use", "Risk If Used Incorrectly"],
        "rows": [
            ["Slicker brush", "Remove loose hair and minor tangles", "Medium to long coats", "Easy", "Brush burn from excessive pressure"],
            ["Pin brush", "Gentle detangling for long coats", "Long, silky coats", "Easy", "Minimal risk"],
            ["Bristle brush", "Distribute natural oils, smooth coat", "Short, smooth coats", "Very easy", "Minimal risk"],
            ["Undercoat rake", "Remove loose undercoat", "Double-coated breeds", "Moderate", "Skin scratching if angle is wrong"],
            ["Dematting comb", "Cut through severe mats", "Long or curly coats", "Requires care", "Cutting skin if pulled too fast"],
            ["Rubber curry", "Massage and loose hair removal", "Short, smooth coats", "Very easy", "Minimal risk"],
            ["Deshedding tool", "Remove dead undercoat efficiently", "Heavy-shedding breeds", "Moderate", "Over-thinning the coat"],
        ],
    },
    4071: {  # Best Dog Shampoo UK
        "intro": "Dog shampoo formulations address different skin and coat needs. Selecting the right type prevents adverse reactions and supports coat health.",
        "headers": ["Shampoo Type", "Best For", "Key Ingredients", "Frequency of Use", "Precaution"],
        "rows": [
            ["General purpose", "Healthy skin and coat", "Mild surfactants, aloe vera", "Every 4-6 weeks", "Rinse thoroughly"],
            ["Hypoallergenic", "Sensitive or allergy-prone skin", "Oatmeal, chamomile, no fragrance", "As needed", "Patch test first"],
            ["Medicated", "Specific skin conditions", "Chlorhexidine, ketoconazole, benzoyl peroxide", "As directed by vet", "Vet supervision required"],
            ["Deodorising", "Dogs prone to odour", "Baking soda, enzymatic cleaners", "As needed, not frequently", "May mask underlying issues"],
            ["Puppy-specific", "Young dogs under 12 months", "Extra-gentle, tearless formula", "Infrequently", "Avoid adult-strength products"],
            ["Whitening", "Light-coloured coats with staining", "Optical brighteners, bluing agents", "Monthly maximum", "Can cause dryness if overused"],
        ],
    },
    4078: {  # Best Dog Nail Clippers UK
        "intro": "Nail care tools serve different functions and suit different owner confidence levels. Choosing the right tool reduces stress for both dog and owner.",
        "headers": ["Tool Type", "Best For", "Skill Level Needed", "Noise Level", "Risk Factor"],
        "rows": [
            ["Guillotine clipper", "Small to medium dogs, thin nails", "Beginner", "Silent", "Can crush if blade is dull"],
            ["Scissor/plier clipper", "All sizes, thick nails", "Beginner to intermediate", "Silent", "Over-cutting if not careful"],
            ["Electric grinder", "Precise shaping, nervous dogs", "Intermediate", "Moderate hum", "Heat buildup on nail"],
            ["Scratch board (DIY filing)", "Anxious dogs, maintenance", "Beginner", "Minimal", "Very slow progress"],
            ["Vet/groomer service", "Severely overgrown or dark nails", "Professional", "Varies", "Cost per visit"],
        ],
    },
    4251: {  # Best Cat Shampoo UK
        "intro": "Cats rarely need bathing, but when they do, choosing an appropriate product is essential. Cat skin differs significantly from dog skin.",
        "headers": ["Product Type", "When Needed", "Application Method", "Cat Tolerance", "Safety Note"],
        "rows": [
            ["Cat-specific shampoo", "Soiling, medical need", "Full bath with warm water", "Low for most cats", "Never use dog products"],
            ["Waterless/dry shampoo", "Mild soiling, elderly cats", "Spray or foam, wipe off", "Moderate", "Check for licking safety"],
            ["Medicated (vet-prescribed)", "Ringworm, dermatitis", "As directed by vet", "Low", "Strict vet supervision"],
            ["Wipes (grooming)", "Spot cleaning, sensitive areas", "Gentle wipe, no rinse", "Generally good", "Fragrance-free preferred"],
            ["Oatmeal-based", "Dry or irritated skin", "Gentle bath", "Low to moderate", "Ensure cat-safe formulation"],
        ],
    },
    4244: {  # Best Cat Nail Clippers UK
        "intro": "Cat nail care requires understanding feline claw anatomy and behaviour. Different tools suit different experience levels.",
        "headers": ["Tool Type", "Best For", "Cat Tolerance", "Ease of Use", "Key Tip"],
        "rows": [
            ["Scissor-style clipper", "Most cats, all sizes", "Moderate", "Beginner-friendly", "Extend claw gently before cutting"],
            ["Guillotine clipper", "Small to medium cats", "Moderate", "Requires nail positioning", "Replace blade when dull"],
            ["Human nail clipper", "Kittens only", "Good", "Very easy", "Not suitable for adult claws"],
            ["Electric grinder", "Cats tolerant of vibration", "Low initially", "Intermediate", "Desensitise to sound first"],
            ["Professional service", "Aggressive or anxious cats", "Handled by expert", "Not applicable", "Less stress for everyone"],
        ],
    },
    4237: {  # Best Cat Brushes UK
        "intro": "Cat coat types require specific brush choices. Using the wrong brush can damage coat texture or cause skin irritation.",
        "headers": ["Cat Coat Type", "Recommended Brush", "Brushing Frequency", "Technique", "Watch For"],
        "rows": [
            ["Short and smooth", "Rubber mitt or soft bristle", "Weekly", "Gentle strokes following coat direction", "Over-brushing causing irritation"],
            ["Medium length", "Slicker brush", "2-3 times weekly", "Section by section, base to tip", "Hidden mats near skin"],
            ["Long and silky", "Wide-tooth comb then pin brush", "Daily", "Start at tips, work toward body", "Mat formation in armpits and belly"],
            ["Double coat", "Undercoat rake then bristle brush", "2-3 times weekly, daily when shedding", "Undercoat first, then topcoat", "Not reaching the undercoat layer"],
            ["Rex/curly", "Soft rubber brush only", "Weekly, very gently", "Light strokes to avoid damaging curls", "Breaking or straightening curls"],
        ],
    },
}


# ── Block HTML Generators ──────────────────────────────────────────────────

def make_evaluation_block(criteria_list):
    """Generate Evaluation Framework block HTML."""
    items = "\n".join(
        f'<li><strong>{c.split(" — ")[0]}</strong> — {c.split(" — ", 1)[1] if " — " in c else c}</li>'
        for c in criteria_list
    )
    return f'''<!-- wp:group {{"style":{{"border":{{"color":"#bae6fd","width":"1px","radius":"6px"}},"color":{{"background":"#f0f9ff"}},"spacing":{{"padding":{{"top":"16px","right":"20px","bottom":"16px","left":"20px"}},"margin":{{"top":"20px","bottom":"20px"}}}}}},"borderColor":"custom"}} -->
<div class="wp-block-group has-border-color has-background is-layout-constrained" style="border-color:#bae6fd;border-width:1px;border-radius:6px;background-color:#f0f9ff;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<h4 class="wp-block-heading">How to Evaluate</h4>
<p class="wp-block-paragraph" style="font-size:14px">Use these criteria to assess your options systematically before making a decision:</p>
<ul class="wp-block-list" style="font-size:14px">
{items}
</ul>
</div>
<!-- /wp:group -->'''


def make_troubleshooting_block(problems):
    """Generate Troubleshooting block HTML."""
    items = "\n".join(
        f'<li><strong>{prob}</strong> — {sol}</li>'
        for prob, sol in problems
    )
    return f'''<!-- wp:group {{"style":{{"border":{{"color":"#fde047","width":"1px","radius":"6px"}},"color":{{"background":"#fefce8"}},"spacing":{{"padding":{{"top":"16px","right":"20px","bottom":"16px","left":"20px"}},"margin":{{"top":"20px","bottom":"20px"}}}}}},"borderColor":"custom"}} -->
<div class="wp-block-group has-border-color has-background is-layout-constrained" style="border-color:#fde047;border-width:1px;border-radius:6px;background-color:#fefce8;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<h4 class="wp-block-heading">Common Problems and Solutions</h4>
<p class="wp-block-paragraph" style="font-size:14px">If you encounter these common issues, here is how to address them:</p>
<ul class="wp-block-list" style="font-size:14px">
{items}
</ul>
</div>
<!-- /wp:group -->'''


def make_scenario_block(scenarios):
    """Generate Scenario Guidance block HTML."""
    items = "\n".join(
        f'<li><strong>{scenario}:</strong> {recommendation}</li>'
        for scenario, recommendation in scenarios
    )
    return f'''<!-- wp:group {{"style":{{"border":{{"color":"#e879f9","width":"1px","radius":"6px"}},"color":{{"background":"#fdf4ff"}},"spacing":{{"padding":{{"top":"16px","right":"20px","bottom":"16px","left":"20px"}},"margin":{{"top":"20px","bottom":"20px"}}}}}},"borderColor":"custom"}} -->
<div class="wp-block-group has-border-color has-background is-layout-constrained" style="border-color:#e879f9;border-width:1px;border-radius:6px;background-color:#fdf4ff;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<h4 class="wp-block-heading">Which Option Suits Your Situation</h4>
<p class="wp-block-paragraph" style="font-size:14px">Different circumstances call for different approaches. Find the scenario closest to yours:</p>
<ul class="wp-block-list" style="font-size:14px">
{items}
</ul>
</div>
<!-- /wp:group -->'''


def make_comparison_table(table_data):
    """Generate wp:table is-style-stripes block HTML."""
    intro = table_data["intro"]
    headers = table_data["headers"]
    rows = table_data["rows"]

    header_cells = "".join(f"<th>{h}</th>" for h in headers)
    body_rows = "".join(
        "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        for row in rows
    )

    return f'''<!-- wp:paragraph -->
<p>{intro}</p>
<!-- /wp:paragraph -->

<!-- wp:table {{"className":"is-style-stripes"}} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr>{header_cells}</tr></thead><tbody>{body_rows}</tbody></table></figure>
<!-- /wp:table -->'''


# ── Content Selection Logic ────────────────────────────────────────────────

def match_content_key(title, content_dict):
    """Find the best matching content key based on title keywords."""
    title_lower = title.lower()
    best_match = "default"

    for key_pattern in content_dict:
        if key_pattern == "default":
            continue
        # Handle regex-like patterns with | separator
        keywords = key_pattern.split("|")
        for kw in keywords:
            if kw.strip() in title_lower:
                best_match = key_pattern
                break
        if best_match != "default":
            break

    return best_match


def get_decision_content(post_id, title, cluster):
    """Return (eval_criteria, troubleshoot_items, scenario_items) for a post."""
    if cluster == "Dog Toys":
        eval_dict = DOG_TOYS_EVAL
        trouble_dict = DOG_TOYS_TROUBLESHOOT
        scenario_dict = DOG_TOYS_SCENARIOS
    elif cluster == "Dog Training":
        eval_dict = DOG_TRAINING_EVAL
        trouble_dict = DOG_TRAINING_TROUBLESHOOT
        scenario_dict = DOG_TRAINING_SCENARIOS
    elif cluster == "Dog Grooming":
        eval_dict = DOG_GROOMING_EVAL
        trouble_dict = DOG_GROOMING_TROUBLESHOOT
        scenario_dict = DOG_GROOMING_SCENARIOS
    else:
        return None, None, None

    eval_key = match_content_key(title, eval_dict)
    trouble_key = match_content_key(title, trouble_dict)
    scenario_key = match_content_key(title, scenario_dict)

    return (
        eval_dict[eval_key],
        trouble_dict[trouble_key],
        scenario_dict[scenario_key],
    )


# ── Insertion Logic ────────────────────────────────────────────────────────

# Order of anchor blocks to insert BEFORE (first match wins)
ANCHOR_PATTERNS = [
    "Quick Checklist",
    "Common Mistakes",
    "Key Terms",
    "Key Takeaways",
    "Our Editorial Standards",
    "Decision summary",
    "Why we reference these sources",
]


def find_insertion_point(content):
    """Find the best insertion point — returns index in content string."""
    for anchor in ANCHOR_PATTERNS:
        idx = content.find(anchor)
        if idx >= 0:
            # Walk back to the start of the containing wp:group or wp:heading block
            search_region = content[max(0, idx - 500):idx]
            # Find nearest group opening or heading
            for marker in ['<!-- wp:group', '<div class="wp-block-group']:
                last_marker = search_region.rfind(marker)
                if last_marker >= 0:
                    return max(0, idx - 500) + last_marker
            # If no group found, insert right before the anchor text region
            return max(0, idx - 200)
    # Fallback: before the last <!-- /wp:group -->
    last_close = content.rfind('<!-- /wp:group -->')
    if last_close > 0:
        return last_close
    return len(content)


def has_block_already(content, block_heading):
    """Check if a decision support block is already present."""
    return block_heading in content


def insert_decision_blocks(content, eval_block, trouble_block, scenario_block):
    """Insert the 3 decision support blocks into content."""
    insertion_idx = find_insertion_point(content)

    # Combine blocks with spacing
    combined_blocks = f"\n\n{eval_block}\n\n{trouble_block}\n\n{scenario_block}\n\n"

    new_content = content[:insertion_idx] + combined_blocks + content[insertion_idx:]
    return new_content


def insert_comparison_table(content, table_html):
    """Insert a comparison table before the decision support blocks or anchors."""
    # Try to insert before "How to Evaluate" block if it exists
    eval_idx = content.find("How to Evaluate")
    if eval_idx >= 0:
        # Walk back to the group start
        search_region = content[max(0, eval_idx - 500):eval_idx]
        for marker in ['<!-- wp:group', '<div class="wp-block-group']:
            last_marker = search_region.rfind(marker)
            if last_marker >= 0:
                insertion_idx = max(0, eval_idx - 500) + last_marker
                return content[:insertion_idx] + f"\n\n{table_html}\n\n" + content[insertion_idx:]

    # Otherwise use standard anchor insertion
    insertion_idx = find_insertion_point(content)
    return content[:insertion_idx] + f"\n\n{table_html}\n\n" + content[insertion_idx:]


# ══════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ══════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("Phase 10BE + 10BF: Decision Support + Comparison Saturation")
    print("Clusters: Dog Toys, Dog Training, Dog Grooming")
    print("=" * 70)

    # Step 1: Build cluster map
    print("\n[1] Building cluster map...")
    cluster_map = build_cluster_map()
    print(f"    Mapped {len(cluster_map)} posts to target clusters")

    # Filter out skip IDs
    target_posts = {pid: cluster for pid, cluster in cluster_map.items() if pid not in SKIP_IDS}
    print(f"    After excluding skip IDs: {len(target_posts)} posts")

    by_cluster = defaultdict(list)
    for pid, cluster in target_posts.items():
        by_cluster[cluster].append(pid)
    for c in sorted(by_cluster):
        print(f"    {c}: {len(by_cluster[c])} posts")

    # Step 2: Fetch all target posts
    print("\n[2] Fetching all target post content from WordPress API...")
    all_post_data = {}
    sorted_ids = sorted(target_posts.keys())

    for i, pid in enumerate(sorted_ids):
        post = api_get(f"posts/{pid}?context=edit")
        if "id" not in post:
            print(f"    [{i+1}/{len(sorted_ids)}] SKIP post {pid} — fetch failed: {str(post)[:100]}")
            continue
        all_post_data[pid] = post
        if (i + 1) % 20 == 0:
            print(f"    Fetched {i+1}/{len(sorted_ids)} posts...")
        time.sleep(0.3)

    print(f"    Fetched {len(all_post_data)} posts successfully")

    # Step 3: Process each post
    print("\n[3] Processing posts — adding decision support blocks + comparison tables...")
    results = []
    tables_added_count = 0
    updates_count = 0
    errors_count = 0

    for i, pid in enumerate(sorted_ids):
        if pid not in all_post_data:
            results.append({
                "id": pid, "title": "FETCH_FAILED", "cluster": target_posts[pid],
                "evaluation_added": "no", "troubleshooting_added": "no",
                "scenario_added": "no", "tables_added": 0, "status": "fetch_error"
            })
            continue

        post = all_post_data[pid]
        title = post["title"]["raw"]
        content = post["content"]["raw"]
        cluster = target_posts[pid]

        print(f"\n  [{i+1}/{len(sorted_ids)}] ID={pid}: {title[:60]}... ({cluster})")

        # Track what we add
        eval_added = False
        trouble_added = False
        scenario_added = False
        table_count = 0
        modified = False

        # Phase 10BE: Decision Support Blocks
        eval_criteria, trouble_items, scenario_items = get_decision_content(pid, title, cluster)

        if eval_criteria and not has_block_already(content, "How to Evaluate"):
            eval_block = make_evaluation_block(eval_criteria)
            trouble_block = make_troubleshooting_block(trouble_items)
            scenario_block = make_scenario_block(scenario_items)

            # Check each individually
            if not has_block_already(content, "How to Evaluate"):
                eval_added = True
            if not has_block_already(content, "Common Problems and Solutions"):
                trouble_added = True
            if not has_block_already(content, "Which Option Suits Your Situation"):
                scenario_added = True

            if eval_added or trouble_added or scenario_added:
                content = insert_decision_blocks(content, eval_block, trouble_block, scenario_block)
                modified = True
                print(f"    + Decision support blocks added")

        # Phase 10BF: Comparison Table
        if pid in COMPARISON_TABLES:
            table_data = COMPARISON_TABLES[pid]
            # Check if post already has an is-style-stripes table with the same intro
            intro_preview = table_data["intro"][:50]
            if intro_preview not in content:
                table_html = make_comparison_table(table_data)
                content = insert_comparison_table(content, table_html)
                table_count = 1
                tables_added_count += 1
                modified = True
                print(f"    + Comparison table added ('{table_data['headers'][0]}...')")
            else:
                print(f"    ~ Comparison table already present, skipping")

        # Update post if modified
        if modified:
            success, resp = api_update(pid, content)
            if success:
                updates_count += 1
                status = "updated"
                print(f"    ✓ Post updated successfully")
            else:
                errors_count += 1
                status = f"update_error: {str(resp)[:100]}"
                print(f"    ✗ Update error: {str(resp)[:100]}")
            time.sleep(DELAY)
        else:
            status = "no_changes_needed"
            print(f"    ~ No changes needed")

        results.append({
            "id": pid,
            "title": title,
            "cluster": cluster,
            "evaluation_added": "yes" if eval_added else "no",
            "troubleshooting_added": "yes" if trouble_added else "no",
            "scenario_added": "yes" if scenario_added else "no",
            "tables_added": table_count,
            "status": status,
        })

    # Step 4: Write CSV
    csv_path = os.path.join(DATA_DIR, "decision_comparison_toys_training_grooming.csv")
    print(f"\n[4] Writing CSV to {csv_path}...")
    fieldnames = ["id", "title", "cluster", "evaluation_added", "troubleshooting_added",
                   "scenario_added", "tables_added", "status"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total posts processed: {len(results)}")
    print(f"  Posts updated: {updates_count}")
    print(f"  Errors: {errors_count}")
    print(f"  Comparison tables added: {tables_added_count}")
    eval_yes = sum(1 for r in results if r["evaluation_added"] == "yes")
    trouble_yes = sum(1 for r in results if r["troubleshooting_added"] == "yes")
    scenario_yes = sum(1 for r in results if r["scenario_added"] == "yes")
    print(f"  Evaluation Framework blocks: {eval_yes}")
    print(f"  Troubleshooting blocks: {trouble_yes}")
    print(f"  Scenario Guidance blocks: {scenario_yes}")
    print(f"\n  CSV: {csv_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
