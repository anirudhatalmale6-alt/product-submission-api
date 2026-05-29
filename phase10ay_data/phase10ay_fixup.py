#!/usr/bin/env python3
"""
Phase 10AV/10AW/10AY Fixup: Add missing Quick Checklist and What to Do Next
to all 29 posts that are still missing them.
"""

import subprocess, json, time, csv, os, tempfile, html, re

API_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ay_data"
LOG_FILE = os.path.join(DATA_DIR, "multi_cluster_dominance.csv")
DELAY = 2

# Posts still needing checklist + next steps
MISSING_IDS = [4209, 4202, 696, 4409, 4408, 4407, 4406, 4307, 4300, 4286,
               4188, 4181, 4174, 4251, 4244, 4237, 4230, 4078, 4071, 4064,
               4057, 6048, 6044, 4573, 4576, 4328, 4293, 4223, 4153]

# Cluster mapping
CLUSTERS = {
    "Cat Supplies": [4335, 4321, 4314, 4209, 4202, 696, 7175],
    "Cat Toys": [5033, 5032, 4409, 4408, 4407, 4406, 4307, 4300, 4286, 4188, 4181, 4174, 7177],
    "Dog Grooming": [5464, 4563, 4251, 4244, 4237, 4230, 4078, 4071, 4064, 4057],
    "Indoor Cats": [5519, 5296, 7342, 7343, 7344, 7345, 7346, 7167],
    "Uncategorized": [6048, 6044, 4786, 4785, 4573, 4570, 4576, 4574, 4571, 4328, 4293, 4223, 4153, 8172, 8171],
}
POST_CLUSTER = {}
for cluster, ids in CLUSTERS.items():
    for pid in ids:
        POST_CLUSTER[pid] = cluster


def api_get(endpoint):
    url = f"{API_BASE}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    return json.loads(result.stdout)


def api_update(post_id, data):
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(data, tmp)
    tmp.close()
    url = f"{API_BASE}/posts/{post_id}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, "-d", f"@{tmp.name}",
         "-H", "Content-Type: application/json", "-X", "POST", url],
        capture_output=True, text=True, timeout=60
    )
    os.unlink(tmp.name)
    resp = json.loads(result.stdout)
    if "id" in resp:
        return True
    print(f"  ERROR: {result.stdout[:300]}")
    return False


def find_best_insertion_point(content):
    """Find the best point to insert Quick Checklist + What to Do Next.
    Strategy: before Common Mistakes section (any format), or before
    Key Takeaways, or before WHY WE REFERENCE, or before DECISION SUMMARY,
    or before Editorial Standards footer.
    """
    # Pattern 1: wp:group wrapped Common Mistakes (h3 or h4)
    for tag in ['h4', 'h3', 'h2']:
        pat = f'<{tag} class="wp-block-heading">Common Mistakes'
        idx = content.find(pat)
        if idx >= 0:
            # Walk back to find wp:group or wp:heading comment
            search = content[:idx]
            wp_g = search.rfind('<!-- wp:group')
            if wp_g >= 0 and (idx - wp_g) < 800:
                return wp_g
            wp_h = search.rfind('<!-- wp:heading')
            if wp_h >= 0 and (idx - wp_h) < 200:
                return wp_h
            return idx

    # Pattern 2: h2 "Common Mistakes to Avoid"
    idx = content.find('Common Mistakes to Avoid')
    if idx >= 0:
        search = content[:idx]
        wp_h = search.rfind('<!-- wp:heading')
        if wp_h >= 0 and (idx - wp_h) < 200:
            return wp_h
        h_tag = search.rfind('<h')
        if h_tag >= 0 and (idx - h_tag) < 100:
            return h_tag
        return idx

    # Pattern 3: div-based Common Mistakes block (red border)
    idx = content.find('>Common Mistakes<')
    if idx >= 0:
        search = content[:idx]
        div_start = search.rfind('<div class="wp-block-group')
        if div_start >= 0 and (idx - div_start) < 500:
            wp_g = content[:div_start].rfind('<!-- wp:group')
            if wp_g >= 0 and (div_start - wp_g) < 200:
                return wp_g
            return div_start

    # Pattern 4: <strong>Common Mistakes</strong>
    idx = content.find('<strong>Common Mistakes</strong>')
    if idx >= 0:
        search = content[:idx]
        div_start = search.rfind('<div class="wp-block-group')
        if div_start >= 0:
            wp_g = content[:div_start].rfind('<!-- wp:group')
            if wp_g >= 0 and (div_start - wp_g) < 200:
                return wp_g
            return div_start
        return idx

    # Pattern 5: Before Key Takeaways
    for tag in ['h4', 'h3', 'h2']:
        pat = f'<{tag} class="wp-block-heading">Key Takeaways'
        idx = content.find(pat)
        if idx >= 0:
            search = content[:idx]
            wp_g = search.rfind('<!-- wp:group')
            if wp_g >= 0 and (idx - wp_g) < 800:
                return wp_g
            return idx

    # Pattern 6: Before WHY WE REFERENCE
    idx = content.find('WHY WE REFERENCE')
    if idx >= 0:
        search = content[:idx]
        div_start = search.rfind('<div ')
        if div_start >= 0:
            return div_start

    # Pattern 7: Before DECISION SUMMARY
    idx = content.find('DECISION SUMMARY')
    if idx >= 0:
        search = content[:idx]
        div_start = search.rfind('<div ')
        if div_start >= 0:
            return div_start

    # Pattern 8: Before Editorial Standards footer
    idx = content.find('Editorial Standards')
    if idx >= 0:
        search = content[:idx]
        div_start = search.rfind('<div ')
        if div_start >= 0:
            return div_start

    return -1


def generate_checklist(title, cluster):
    title_lower = title.lower()

    if cluster == "Cat Supplies":
        if "heated" in title_lower and "bed" in title_lower:
            items = [
                "Check that the heating element has an automatic shut-off or thermostat",
                "Choose low-voltage (12V) options to reduce burn risk for cats who sleep deeply",
                "Position heated beds away from draughts but not directly against radiators",
                "Inspect power cords regularly for chewing damage — use cord protectors if needed",
                "Provide an unheated alternative nearby so your cat can self-regulate temperature",
                "Wash removable covers according to manufacturer instructions to maintain hygiene",
            ]
        elif "cat bed" in title_lower:
            items = [
                "Measure your cat while sleeping stretched out to determine minimum bed size",
                "Choose machine-washable beds or beds with removable, washable covers",
                "Place beds in quiet, elevated spots where your cat naturally chooses to rest",
                "Provide multiple bed options — some cats prefer enclosed igloos, others prefer open bolsters",
                "Replace beds when padding becomes flat or fabric shows signs of heavy wear",
                "Avoid beds with small detachable decorations that could be chewed and swallowed",
            ]
        elif "essential" in title_lower or "must-have" in title_lower:
            items = [
                "Set up food and water stations before bringing your cat home",
                "Purchase a suitable litter tray and litter type before your cat arrives",
                "Provide at least one scratching post to protect furniture and support claw health",
                "Have a secure cat carrier ready for vet visits and emergencies",
                "Choose age-appropriate toys for enrichment and daily play sessions",
                "Register with a local vet and schedule an initial health check within the first week",
                "Ensure all windows and balconies are secured if keeping your cat indoors",
            ]
        else:
            items = [
                "Research your cat's specific breed needs before purchasing supplies",
                "Choose products with clear safety certifications appropriate for UK sale",
                "Read the full ingredients or materials list before buying",
                "Start with essentials and add specialist items as you learn your cat's preferences",
                "Replace any supply showing signs of wear, damage, or hygiene concerns",
                "Consult your vet if unsure whether a product is suitable for your cat's health needs",
            ]

    elif cluster == "Cat Toys":
        if "kitten" in title_lower or "age" in title_lower:
            items = [
                "Choose soft, lightweight toys for kittens under 6 months",
                "Avoid small parts, long strings, and elastic bands for young kittens",
                "Increase toy complexity as your kitten grows and develops coordination",
                "Introduce puzzle feeders from around 4 months to encourage problem-solving",
                "Reduce high-energy toys for senior cats and introduce gentler alternatives",
                "Reassess toy suitability at each life stage transition",
            ]
        elif "replace" in title_lower or "how often" in title_lower:
            items = [
                "Inspect all toys before each play session for loose parts or damage",
                "Replace feather toys when feathers become detached or frayed",
                "Discard any toy with exposed stuffing, broken squeakers, or separated parts",
                "Check elastic and string components weekly for signs of weakening",
                "Keep a spare set of your cat's favourite toys to ensure seamless rotation",
                "Replace catnip toys when they lose their scent — typically every 2-4 weeks",
            ]
        elif "diy" in title_lower or "homemade" in title_lower:
            items = [
                "Use only non-toxic materials — avoid glue, paint, or treated fabrics",
                "Ensure all components are securely attached to prevent swallowing hazards",
                "Avoid small beads, buttons, or bells that could detach during play",
                "Test homemade toys under supervision before leaving them with your cat",
                "Replace DIY toys more frequently than commercial ones as they wear faster",
                "Never use rubber bands, hair ties, or dental floss as toy components",
            ]
        elif "indoor" in title_lower and "interactive" in title_lower:
            items = [
                "Provide toys that simulate hunting — feathers, fur-textured mice, moving targets",
                "Create vertical play spaces using cat trees and wall-mounted shelves",
                "Rotate toys on a weekly schedule to prevent environmental monotony",
                "Combine play with feeding by using puzzle toys for a portion of daily food",
                "Ensure at least one interactive play session daily to prevent inactivity",
                "Place toys in different rooms to encourage exploration and movement",
            ]
        elif "wall" in title_lower and "scratch" in title_lower:
            items = [
                "Mount scratchers at a height that allows your cat to stretch fully while scratching",
                "Check wall fixings regularly to ensure the scratcher remains securely attached",
                "Choose sisal-wrapped options for durability or cardboard for budget-friendly replacement",
                "Position near sleeping areas — cats often scratch upon waking",
                "Replace scratching surfaces when they become heavily worn or frayed through",
                "Provide at least one scratcher per cat in multi-cat households",
            ]
        elif "cardboard" in title_lower and "scratch" in title_lower:
            items = [
                "Replace cardboard scratchers when the surface becomes flat and compacted",
                "Position on flat ground or at a slight angle near your cat's favourite resting spot",
                "Sprinkle a small amount of catnip on new scratchers to encourage use",
                "Choose scratchers with reversible inserts for longer usable life",
                "Collect and dispose of cardboard debris regularly to maintain cleanliness",
                "Provide both horizontal and vertical scratching options to match your cat's preference",
            ]
        elif "scratching post" in title_lower or "scratch" in title_lower:
            items = [
                "Choose a post tall enough for your cat to stretch fully — at least 80cm for adult cats",
                "Ensure the base is heavy and stable enough to prevent tipping during vigorous scratching",
                "Position near sleeping areas and room entrances where cats naturally mark territory",
                "Offer both vertical and horizontal scratching surfaces to match your cat's preference",
                "Replace sisal rope or fabric when it becomes heavily frayed and loses texture",
                "Provide one scratching post per cat plus one extra in multi-cat homes",
            ]
        elif "catnip" in title_lower:
            items = [
                "Test with a small amount of catnip first to check your cat's sensitivity",
                "Store catnip in an airtight container to preserve potency",
                "Limit catnip exposure to 2-3 times per week to maintain effectiveness",
                "Try silver vine as an alternative if your cat does not respond to catnip",
                "Remove catnip toys after 15 minutes to prevent overstimulation",
                "Keep catnip products away from kittens under 6 months",
            ]
        elif "wand" in title_lower or ("interactive" in title_lower and "puzzle" in title_lower):
            items = [
                "Move wand toys in erratic, prey-like patterns rather than repetitive circles",
                "Let your cat 'catch' the toy periodically to prevent frustration",
                "Check the attachment point between wand and toy before each session",
                "Store wand toys in a closed cupboard to prevent unsupervised string access",
                "Replace frayed strings and worn attachments promptly",
                "Use wand play to bond with shy or newly adopted cats",
            ]
        else:
            items = [
                "Inspect all toys before each play session for loose parts or damage",
                "Rotate toys weekly to maintain your cat's interest and engagement",
                "Provide a mixture of interactive and self-play toy options",
                "Schedule at least two daily play sessions of 10-15 minutes each",
                "Store string and ribbon toys safely away when not supervised",
                "Replace any toy showing signs of wear before parts become detachable",
            ]

    elif cluster == "Dog Grooming":
        if "shampoo" in title_lower or "bathe" in title_lower:
            items = [
                "Choose a shampoo formulated for the correct species — never use human shampoo on pets",
                "Test new shampoo on a small area first if your pet has sensitive skin",
                "Rinse thoroughly — residual shampoo causes irritation and flaking",
                "Bathe cats only when necessary; most cats groom themselves adequately",
                "Use lukewarm water and keep bathing sessions as calm and brief as possible",
                "Dry your pet fully after bathing to prevent skin issues, especially in cold weather",
            ]
        elif "nail" in title_lower or "claw" in title_lower:
            items = [
                "Identify the quick (blood vessel) before cutting — use a torch on light-coloured nails",
                "Trim small amounts frequently rather than large amounts infrequently",
                "Keep styptic powder on hand in case of accidental quick nicks",
                "Use sharp, species-appropriate clippers — dull blades crush rather than cut",
                "Handle your pet's paws regularly from a young age to build comfort with nail trims",
                "Consult a vet or groomer if nails are overgrown or you are unsure about trimming",
            ]
        elif "brush" in title_lower or "coat" in title_lower:
            items = [
                "Identify your pet's coat type before selecting brushes and combs",
                "Brush in the direction of hair growth to avoid discomfort",
                "Use a slicker brush for tangles and an undercoat rake for double-coated breeds",
                "Check for mats behind ears, under legs, and around the collar area",
                "Brush before bathing — water tightens mats and makes them harder to remove",
                "Make brushing a positive experience with treats and calm praise",
            ]
        elif "grooming supplies" in title_lower or "complete guide" in title_lower:
            items = [
                "Assemble a basic grooming toolkit suited to your pet's coat type and breed",
                "Choose tools with ergonomic handles to reduce hand fatigue during grooming",
                "Clean grooming tools after every use to prevent bacterial buildup",
                "Replace scissors and clipper blades when they become dull",
                "Store grooming supplies in a dedicated, clean container or bag",
                "Consult a professional groomer for breed-specific tool recommendations",
            ]
        else:
            items = [
                "Groom your pet regularly based on their breed and coat type requirements",
                "Use tools designed for your pet's specific coat — one size does not fit all",
                "Introduce grooming gradually with positive associations and rewards",
                "Check skin condition during every grooming session for lumps, irritation, or parasites",
                "Keep grooming equipment clean and replace worn tools promptly",
                "Consult a veterinary professional if you notice persistent skin or coat problems",
            ]

    elif cluster == "Uncategorized":
        if "confidence" in title_lower or "shy" in title_lower or "fearful" in title_lower:
            items = [
                "Start with low-pressure toys placed near your dog's safe space — never force interaction",
                "Use treat-dispensing toys to create positive associations with play",
                "Keep initial sessions under 5 minutes and end before your dog shows stress",
                "Avoid sudden movements, loud toys, or high-energy games with anxious dogs",
                "Gradually increase challenge only after consistent comfortable engagement",
                "Consult a certified behaviourist if fear responses do not improve over several weeks",
            ]
        elif "puzzle" in title_lower or "rotating" in title_lower:
            items = [
                "Begin with beginner-level puzzles and advance only after consistent success",
                "Rotate puzzle types (sliding, lifting, spinning) to exercise different skills",
                "Increase difficulty in small increments — frustration undoes progress",
                "Use your dog's regular food in puzzles to prevent overfeeding",
                "Clean puzzles after each use to prevent mould and bacterial growth",
                "Monitor engagement — reduced interest may mean the puzzle is too easy or too hard",
            ]
        elif "seasonal" in title_lower or "safety" in title_lower:
            items = [
                "Check for seasonal hazards before they become a risk — antifreeze in winter, heatstroke in summer",
                "Adjust walking times to avoid extreme temperatures",
                "Keep toxic seasonal plants (lilies, poinsettia, conkers) out of reach",
                "Ensure your pet has access to shade and fresh water during warm months",
                "Check paws for ice, salt, or grit damage after winter walks",
                "Update your pet's ID tag and microchip details before holiday travel",
            ]
        elif "multi-pet" in title_lower or "multi pet" in title_lower:
            items = [
                "Introduce new pets gradually using scent swapping and controlled visual contact first",
                "Provide separate food and water stations for each species",
                "Ensure cats have high escape routes and safe spaces dogs cannot access",
                "Monitor body language during interactions and separate at the first sign of stress",
                "Feed pets separately to prevent resource guarding and dietary mix-ups",
                "Maintain individual play time and attention for each pet",
            ]
        elif "self-cleaning" in title_lower or "automatic" in title_lower:
            items = [
                "Research your cat's comfort with automated devices before purchasing",
                "Introduce self-cleaning trays gradually alongside the existing manual tray",
                "Check waste receptacles and sensors regularly to ensure proper function",
                "Keep a manual backup tray available in case of mechanical failure or power cuts",
                "Clean the unit's sensors and surfaces according to manufacturer instructions",
                "Monitor your cat's usage to ensure they are not avoiding the new tray",
            ]
        elif "cat tree" in title_lower or "climbing" in title_lower:
            items = [
                "Measure your ceiling height and available floor space before purchasing",
                "Choose a tree with a sturdy, weighted base to prevent tipping",
                "Position near a window to provide environmental stimulation and bird watching",
                "Check all platforms, fixings, and sisal wrapping monthly for wear",
                "Ensure platforms are large enough for your cat to lie down comfortably",
                "Provide one tall resting platform per cat in multi-cat households",
            ]
        elif "window perch" in title_lower:
            items = [
                "Check your window frame type (wood, uPVC, aluminium) for mounting compatibility",
                "Verify the weight capacity against your cat's actual weight plus a safety margin",
                "Test suction cup adhesion on clean, dry glass before allowing your cat to use it",
                "Position at a height your cat can access easily, especially for older cats",
                "Check suction cups or brackets weekly and reattach if grip has weakened",
                "Add a non-slip cover or blanket to the perch surface for comfort",
            ]
        elif "slow feeder" in title_lower or "speed eating" in title_lower:
            items = [
                "Choose a slow feeder design suited to your dog's muzzle shape and size",
                "Introduce the slow feeder with easy food first so your dog learns the pattern",
                "Clean the feeder thoroughly after every meal — ridges trap food debris",
                "Monitor your dog's frustration level and switch to a simpler design if needed",
                "Use the slow feeder for at least one meal per day for maximum benefit",
                "Replace the feeder if your dog chews or damages the material",
            ]
        else:
            items = [
                "Research your pet's specific needs before purchasing any product",
                "Choose products with clear safety certifications suitable for UK sale",
                "Introduce new items gradually while supervising your pet's interaction",
                "Inspect toys and products regularly for wear, damage, or hygiene concerns",
                "Replace items promptly when they show signs of deterioration",
                "Consult your vet if you are unsure whether a product is appropriate for your pet",
            ]
    else:
        items = [
            "Research your pet's specific needs before making purchases",
            "Choose products with appropriate safety certifications",
            "Introduce new items gradually and monitor your pet's response",
            "Inspect products regularly for wear and damage",
            "Replace worn items before they become a safety hazard",
            "Consult your vet if you have concerns about product suitability",
        ]

    li_items = "".join(f"<li>{item}</li>" for item in items)
    return (
        '<!-- wp:group {"style":{"color":{"background":"#f5f3ff"},"border":{"radius":"6px","width":"1px","color":"#ddd6fe"},"spacing":{"padding":{"top":"16px","bottom":"16px","left":"20px","right":"20px"},"margin":{"top":"24px","bottom":"24px"}}},"layout":{"type":"constrained"}} -->\n'
        '<div class="wp-block-group has-border-color has-background" style="border-color:#ddd6fe;border-width:1px;border-radius:6px;background-color:#f5f3ff;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<!-- wp:heading {"level":4} --><h4 class="wp-block-heading">Quick Checklist</h4><!-- /wp:heading -->\n'
        f'<!-- wp:list --><ul class="wp-block-list">{li_items}</ul><!-- /wp:list -->\n'
        '</div><!-- /wp:group -->'
    )


def generate_next_steps(title, cluster):
    title_lower = title.lower()

    if cluster == "Cat Supplies":
        if "heated" in title_lower and "bed" in title_lower:
            steps = [
                "Check your current cat bed for warmth adequacy — observe whether your cat seeks warmer spots in winter",
                "Compare heated bed options focusing on voltage, thermostat features, and washability",
                "Test the bed in your cat's preferred sleeping area before committing to a permanent location",
                "Monitor your cat's use over the first week and adjust placement if they avoid it",
            ]
        elif "cat bed" in title_lower:
            steps = [
                "Observe where your cat naturally sleeps to identify their preferred bed style and location",
                "Measure your cat while resting to determine minimum bed size requirements",
                "Select two or three bed options in different styles to discover your cat's preference",
                "Place beds in quiet, elevated spots and monitor which your cat uses most frequently",
            ]
        elif "essential" in title_lower or "must-have" in title_lower:
            steps = [
                "Create a checklist of essential supplies needed before your cat arrives",
                "Purchase food, water bowls, litter tray, and carrier as a minimum first set",
                "Set up a designated quiet room with all essentials for the first few days",
                "Register with a local veterinary practice and book an introductory appointment",
            ]
        else:
            steps = [
                "Assess your current cat supply setup against the recommendations in this guide",
                "Identify any gaps or items needing replacement",
                "Research suitable alternatives using the criteria described above",
                "Make changes gradually and monitor your cat's response to new products",
            ]

    elif cluster == "Cat Toys":
        if "kitten" in title_lower or "age" in title_lower:
            steps = [
                "Determine your cat's current life stage and match toys to the age-appropriate recommendations",
                "Remove any toys from your collection that are unsuitable for your cat's current age",
                "Plan a toy transition schedule as your kitten approaches adulthood",
                "Consult your vet about appropriate play intensity if your cat has any health conditions",
            ]
        elif "replace" in title_lower or "how often" in title_lower:
            steps = [
                "Audit every toy your cat currently has access to using the safety criteria in this guide",
                "Remove and replace any toys that fail the inspection immediately",
                "Set a monthly calendar reminder to conduct toy safety checks",
                "Keep a small stock of replacement toys so worn ones can be swapped out promptly",
            ]
        elif "diy" in title_lower or "homemade" in title_lower:
            steps = [
                "Gather materials from the safe list provided in this guide",
                "Start with the simplest project to build your confidence",
                "Test every homemade toy under supervision before leaving it with your cat",
                "Replace DIY toys at the first sign of wear — they deteriorate faster than commercial options",
            ]
        elif "indoor" in title_lower and "interactive" in title_lower:
            steps = [
                "Audit your home for play opportunities — vertical space, window perches, hiding spots",
                "Create a toy rotation schedule covering at least 10-14 different toys",
                "Introduce one puzzle feeder for at least one meal per day",
                "Review your cat's activity levels monthly and adjust play provision accordingly",
            ]
        elif "wall" in title_lower and "scratch" in title_lower:
            steps = [
                "Identify the walls where your cat naturally tries to scratch or stretch",
                "Select a wall-mounted scratcher appropriate for your wall type and cat's size",
                "Install at a height that allows your cat to stretch to full length",
                "Monitor use and adjust height or location if your cat shows no interest within a week",
            ]
        elif "cardboard" in title_lower and "scratch" in title_lower:
            steps = [
                "Observe your cat's current scratching preferences — horizontal, vertical, or angled",
                "Select a cardboard scratcher that matches your cat's preferred scratching angle",
                "Place the scratcher near your cat's usual scratching targets or sleeping area",
                "Replace the insert when the surface becomes flat and compacted from use",
            ]
        elif "scratching post" in title_lower or "scratch" in title_lower:
            steps = [
                "Observe where your cat currently scratches to identify preferred locations and angles",
                "Select a scratching post that matches your cat's preferred scratching style",
                "Position the new post near the area your cat currently targets for scratching",
                "Encourage use with a light dusting of catnip and redirect your cat when they scratch elsewhere",
            ]
        elif "catnip" in title_lower:
            steps = [
                "Test your cat's catnip sensitivity with a small pinch on a cloth",
                "If no response, try silver vine or valerian root as alternatives",
                "Establish a 2-3 times per week schedule for catnip enrichment",
                "Store all catnip products in airtight containers between uses",
            ]
        elif "wand" in title_lower or ("interactive" in title_lower and "puzzle" in title_lower):
            steps = [
                "Schedule two daily interactive play sessions of 10-15 minutes each",
                "Practise prey-like movements — start slow, build speed, then allow the catch",
                "Inspect your wand toy's attachment point and string before each session",
                "Experiment with different wand attachments to find what excites your cat most",
            ]
        else:
            steps = [
                "Audit your current cat toy collection for safety and variety",
                "Identify any gaps in toy types based on the categories described in this guide",
                "Purchase or create toys to fill those gaps, prioritising safety and your cat's preferences",
                "Establish a regular toy rotation and play schedule",
            ]

    elif cluster == "Dog Grooming":
        if "shampoo" in title_lower or "bathe" in title_lower:
            steps = [
                "Determine how often your pet needs bathing based on coat type and activity level",
                "Select an appropriate shampoo based on your pet's skin sensitivity and coat needs",
                "Prepare your bathing area with towels, shampoo, and treats before starting",
                "Follow the bathing technique described in this guide for best results",
            ]
        elif "nail" in title_lower or "claw" in title_lower:
            steps = [
                "Examine your pet's nails and identify the quick on each nail where visible",
                "Gather appropriate tools — sharp clippers, styptic powder, and treats",
                "Start with one or two nails per session if your pet is anxious",
                "Build up to full trims as your pet becomes comfortable with the process",
            ]
        elif "brush" in title_lower or "coat" in title_lower:
            steps = [
                "Identify your pet's coat type using the descriptions in this guide",
                "Select the correct brush type for your pet's coat",
                "Start with short brushing sessions in areas your pet finds comfortable",
                "Gradually work up to full-body brushing over several sessions",
            ]
        elif "grooming supplies" in title_lower or "complete guide" in title_lower:
            steps = [
                "Identify your pet's coat type and create a list of essential tools needed",
                "Purchase the core items first — brush, comb, nail clippers, and shampoo",
                "Establish a regular grooming schedule based on your pet's breed requirements",
                "Book a professional grooming consultation if your pet's coat needs specialist techniques",
            ]
        else:
            steps = [
                "Assess your current grooming routine against the recommendations in this guide",
                "Identify any grooming tasks you have been overlooking",
                "Gather any tools or products you need to address gaps",
                "Establish a consistent grooming schedule suited to your pet's breed and coat type",
            ]

    elif cluster == "Uncategorized":
        if "confidence" in title_lower or "shy" in title_lower:
            steps = [
                "Identify your dog's specific fear triggers by observing their behaviour in different contexts",
                "Select one low-pressure play activity from this guide to try this week",
                "Keep a brief daily log of your dog's response to track progress over time",
                "Consult a certified behaviourist (ABTC-registered) if fear responses are severe or worsening",
            ]
        elif "puzzle" in title_lower or "rotating" in title_lower:
            steps = [
                "Assess your dog's current puzzle-solving ability using the difficulty scale in this guide",
                "Select a puzzle at the appropriate starting level and introduce it with high-value treats",
                "Record your dog's completion time and success rate over the first week",
                "Advance to the next difficulty level only after consistent success at the current one",
            ]
        elif "seasonal" in title_lower:
            steps = [
                "Review the seasonal checklist for the current time of year and address any gaps",
                "Set calendar reminders at the start of each season to review relevant hazards",
                "Prepare an emergency kit appropriate for the most common seasonal risks in your area",
                "Consult your vet about seasonal health concerns specific to your pet's breed",
            ]
        elif "multi-pet" in title_lower or "multi pet" in title_lower:
            steps = [
                "Assess your current resource setup — ensure each pet has their own food, water, and rest areas",
                "Identify any tension points between your pets and address the most pressing one this week",
                "Create vertical escape routes for cats if you have both dogs and cats",
                "Schedule individual attention time for each pet daily",
            ]
        elif "self-cleaning" in title_lower or "automatic" in title_lower:
            steps = [
                "Research self-cleaning models compatible with your cat's size and litter preference",
                "Keep your existing manual tray available during the 2-4 week transition period",
                "Monitor your cat's willingness to use the new tray before removing the manual backup",
                "Set a regular maintenance schedule for cleaning sensors and emptying waste receptacles",
            ]
        elif "cat tree" in title_lower:
            steps = [
                "Measure your available space and ceiling height before selecting a cat tree",
                "Choose a tree with a configuration that matches your cat's preferred activities (climbing, scratching, resting)",
                "Position the tree near a window for maximum enrichment value",
                "Observe your cat's usage over the first week and reposition if they show little interest",
            ]
        elif "window perch" in title_lower:
            steps = [
                "Identify the window with the best view for environmental stimulation",
                "Check your window type for mounting compatibility before purchasing",
                "Install the perch and test weight capacity before allowing your cat to use it",
                "Re-check suction cups or brackets weekly to maintain secure attachment",
            ]
        elif "slow feeder" in title_lower:
            steps = [
                "Observe your dog's current eating speed to confirm they would benefit from a slow feeder",
                "Select a design suited to your dog's muzzle shape and eating style",
                "Introduce the slow feeder with a small amount of food first to build familiarity",
                "Monitor your dog's meal completion time and adjust the feeder design if frustration occurs",
            ]
        else:
            steps = [
                "Review the guidance in this article against your current pet care practices",
                "Identify the most relevant recommendation for your situation",
                "Implement one change this week and observe your pet's response",
                "Return to this guide periodically as your pet's needs change with age or season",
            ]
    else:
        steps = [
            "Review the key points in this article against your current setup",
            "Identify the single most impactful change you can make this week",
            "Implement that change and monitor your pet's response",
            "Revisit this guide in one month to assess progress and plan next steps",
        ]

    li_items = "".join(f"<li>{step}</li>" for step in steps)
    return (
        '<!-- wp:group {"style":{"color":{"background":"#f0fdfa"},"border":{"radius":"6px","width":"1px","color":"#99f6e4"},"spacing":{"padding":{"top":"16px","bottom":"16px","left":"20px","right":"20px"},"margin":{"top":"24px","bottom":"24px"}}},"layout":{"type":"constrained"}} -->\n'
        '<div class="wp-block-group has-border-color has-background" style="border-color:#99f6e4;border-width:1px;border-radius:6px;background-color:#f0fdfa;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<!-- wp:heading {"level":4} --><h4 class="wp-block-heading">What to Do Next</h4><!-- /wp:heading -->\n'
        f'<!-- wp:list {{"ordered":true}} --><ol class="wp-block-list">{li_items}</ol><!-- /wp:list -->\n'
        '</div><!-- /wp:group -->'
    )


def main():
    print("=" * 70)
    print("Phase 10AV/10AW/10AY FIXUP: Adding missing blocks")
    print(f"Posts to fix: {len(MISSING_IDS)}")
    print("=" * 70)

    results = []

    for i, post_id in enumerate(MISSING_IDS):
        cluster = POST_CLUSTER[post_id]
        print(f"\n[{i+1}/{len(MISSING_IDS)}] Post {post_id} ({cluster})")

        data = api_get(f"posts/{post_id}?context=edit")
        if "id" not in data:
            print(f"  ERROR fetching post")
            results.append({"id": post_id, "status": "fetch_error"})
            continue

        title = data["title"]["raw"]
        content = data["content"]["raw"]
        print(f"  Title: {title[:60]}")
        print(f"  Length: {len(content)}")

        has_cl = "Quick Checklist" in content
        has_ns = "What to Do Next" in content

        if has_cl and has_ns:
            print(f"  Already has both blocks - skipping")
            results.append({"id": post_id, "status": "already_done"})
            if i < len(MISSING_IDS) - 1:
                time.sleep(DELAY)
            continue

        insert_pos = find_best_insertion_point(content)
        print(f"  Insertion point: {insert_pos}")

        if insert_pos <= 0:
            print(f"  WARNING: No insertion point found, appending at end")
            insert_pos = len(content)

        checklist_html = generate_checklist(title, cluster)
        next_html = generate_next_steps(title, cluster)

        combined = "\n\n" + checklist_html + "\n\n" + next_html + "\n\n"

        if insert_pos >= len(content):
            new_content = content + combined
        else:
            new_content = content[:insert_pos] + combined + content[insert_pos:]

        # Verify the blocks are in the new content
        if "Quick Checklist" not in new_content:
            print(f"  CRITICAL: Checklist not in generated content!")
            results.append({"id": post_id, "status": "generation_error"})
            continue

        print(f"  New length: {len(new_content)}")
        print(f"  Updating...")

        success = api_update(post_id, {"content": new_content})
        print(f"  Update result: {success}")

        if success:
            # Verify it persisted
            time.sleep(1)
            verify = api_get(f"posts/{post_id}?context=edit")
            vc = verify.get("content", {}).get("raw", "")
            persisted = "Quick Checklist" in vc and "What to Do Next" in vc
            print(f"  Persisted: {persisted}")
            if not persisted:
                print(f"  WARNING: Content did not persist! Length: {len(vc)} vs expected {len(new_content)}")
            results.append({"id": post_id, "status": "updated" if persisted else "not_persisted"})
        else:
            results.append({"id": post_id, "status": "update_failed"})

        if i < len(MISSING_IDS) - 1:
            time.sleep(DELAY)

    # Summary
    print(f"\n{'='*70}")
    print("FIXUP SUMMARY")
    updated = sum(1 for r in results if r["status"] == "updated")
    not_persisted = sum(1 for r in results if r["status"] == "not_persisted")
    errors = sum(1 for r in results if "error" in r["status"])
    already = sum(1 for r in results if r["status"] == "already_done")
    print(f"  Updated & persisted: {updated}")
    print(f"  Not persisted: {not_persisted}")
    print(f"  Already done: {already}")
    print(f"  Errors: {errors}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
