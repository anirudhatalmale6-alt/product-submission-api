#!/usr/bin/env python3
"""
Phase 12O: Expand FAQs from 1-2 questions to 5+ questions for 34 posts.
Adds contextually appropriate FAQ items based on post topic.
"""

import subprocess
import json
import time
import re
import os
import tempfile


WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = f"{WP_USER}:{WP_PASS}"

POST_IDS = [5417,6044,6048,4406,6052,6039,5950,5942,5938,5931,5511,5476,5471,5469,5034,5933,5510,5423,5421,5420,5419,5418,4415,4410,4408,4407,4335,4314,4307,4300,4195,4181,4174,696]


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


def generate_faq_items(title):
    """Generate 5 FAQ question-answer pairs based on post topic."""
    title_lower = title.lower()

    if 'cat toy' in title_lower or 'interactive cat' in title_lower:
        return cat_toy_faqs()
    elif 'cat litter' in title_lower:
        return cat_litter_faqs()
    elif 'cat scratch' in title_lower:
        return cat_scratch_faqs()
    elif 'cat' in title_lower and ('rotation' in title_lower or 'replace' in title_lower):
        return cat_toy_rotation_faqs()
    elif 'cat' in title_lower and ('safety' in title_lower or 'safe' in title_lower):
        return cat_safety_faqs()
    elif 'cat' in title_lower and ('enrichment' in title_lower or 'diy' in title_lower):
        return cat_enrichment_faqs()
    elif 'cat' in title_lower and ('supply' in title_lower or 'essential' in title_lower or 'glossary' in title_lower or 'basics' in title_lower):
        return cat_general_faqs()
    elif 'puppy' in title_lower and ('toy' in title_lower or 'safe' in title_lower):
        return puppy_toy_faqs()
    elif 'puppy' in title_lower:
        return puppy_care_faqs()
    elif 'dog toy' in title_lower and ('clean' in title_lower or 'hygiene' in title_lower):
        return dog_toy_cleaning_faqs()
    elif 'dog toy' in title_lower and ('durabl' in title_lower or 'last' in title_lower or 'lifespan' in title_lower):
        return dog_toy_durability_faqs()
    elif 'rotation' in title_lower and 'dog' in title_lower:
        return dog_rotation_faqs()
    elif 'anxiety' in title_lower or 'calm' in title_lower:
        return dog_anxiety_faqs()
    elif 'senior' in title_lower or 'ageing' in title_lower or 'cognitive' in title_lower:
        return senior_dog_faqs()
    elif 'enrichment' in title_lower and 'schedule' in title_lower:
        return enrichment_schedule_faqs()
    elif 'overstimul' in title_lower:
        return overstimulation_faqs()
    elif 'low-mobility' in title_lower or 'limited movement' in title_lower:
        return low_mobility_faqs()
    elif 'puzzle' in title_lower or 'mental stimulation' in title_lower:
        return puzzle_toy_faqs()
    elif 'boredom' in title_lower:
        return boredom_faqs()
    elif 'enrichment' in title_lower or 'fetch' in title_lower:
        return enrichment_general_faqs()
    elif 'tug' in title_lower:
        return tug_play_faqs()
    elif 'confidence' in title_lower or 'shy' in title_lower:
        return confidence_faqs()
    elif 'harness' in title_lower:
        return harness_faqs()
    elif 'bed' in title_lower and 'siz' in title_lower:
        return bed_sizing_faqs()
    elif 'pet' in title_lower and 'enrichment' in title_lower:
        return pet_enrichment_faqs()
    else:
        return generic_pet_faqs(title)


def cat_toy_faqs():
    return [
        ("How often should I play with my cat?", "Most cats benefit from two to three interactive play sessions daily, lasting 10 to 15 minutes each. Kittens and young adults may need more. Observe your cat's energy levels and adjust accordingly."),
        ("Are laser pointers safe for cats?", "Laser pointers provide good exercise but should always end with a physical toy catch to prevent frustration. Never shine directly in your cat's eyes. Supplement with tangible toys your cat can actually catch and 'kill'."),
        ("How many toys does a cat need?", "Most cats do well with 5 to 10 toys available, rotated weekly to maintain novelty. Quality and variety matter more than quantity. Include a mix of chase toys, kick toys, and puzzle feeders."),
        ("What materials are safest for cat toys?", "Look for non-toxic materials without small detachable parts. Avoid string longer than 15cm, loose feathers that can be swallowed, and toys with sharp edges. Natural materials like sisal and cotton are generally safe."),
        ("How do I know if my cat is bored with their toys?", "Signs include ignoring previously loved toys, increased destructive behaviour, over-grooming, excessive vocalisation, and sleeping more than usual. Try rotating toys or introducing new play styles to re-engage."),
    ]


def cat_litter_faqs():
    return [
        ("How often should cat litter be completely changed?", "Clumping litter should be fully replaced every 2 to 4 weeks with daily scooping. Non-clumping litter needs full replacement every 5 to 7 days. Crystal litter typically lasts 2 to 4 weeks for one cat."),
        ("How much litter should I put in the tray?", "Fill to a depth of 5 to 8 centimetres for clumping litter, or 3 to 5 centimetres for non-clumping. Too shallow prevents proper burying; too deep wastes litter and some cats dislike deep substrate."),
        ("Can you flush cat litter down the toilet?", "Most clay and crystal litters should never be flushed as they can block pipes. Some plant-based litters claim to be flushable, but check local water authority guidance as cat waste can contain Toxoplasma parasites."),
        ("Why does my cat go outside the litter tray?", "Common causes include dirty trays, medical issues (UTI, kidney problems), stress, inappropriate tray size or location, dislike of litter type, or insufficient trays in multi-cat homes. Rule out health issues first."),
        ("How many litter trays do I need?", "The recommended formula is one tray per cat plus one extra. In multi-level homes, provide at least one tray per floor. Place trays in quiet, accessible locations away from food and water."),
    ]


def cat_scratch_faqs():
    return [
        ("How do I stop my cat scratching furniture?", "Place a scratcher directly next to the targeted furniture. Make it more attractive with catnip. Cover the furniture temporarily with double-sided tape or aluminium foil. Never punish scratching — redirect it instead."),
        ("What height should a cat scratcher be?", "Vertical scratchers should be at least 80cm tall to allow a full body stretch. The post must be stable enough not to wobble when used — instability deters cats from using it again."),
        ("How long do cat scratchers last?", "Cardboard scratchers typically last 1 to 3 months depending on usage. Sisal-wrapped posts last 1 to 3 years. Solid wood scratchers can last 5+ years with minimal maintenance."),
        ("Can I train a kitten to use a scratcher?", "Yes — place the scratcher near their sleeping area (cats often stretch and scratch after waking). Gently guide their paws along the surface. Reward any interaction with the scratcher. Start early for best results."),
        ("Why does my cat scratch even though they have a scratcher?", "They may prefer a different orientation (vertical vs horizontal), material (sisal vs cardboard), or location. Some cats scratch to mark territory near doorways or social areas rather than in quiet corners."),
    ]


def cat_toy_rotation_faqs():
    return [
        ("How often should I rotate my cat's toys?", "Rotate every 3 to 7 days for optimal engagement. Keep 3 to 4 toys out at a time and store the rest. When reintroduced after a break, familiar toys feel novel again to your cat."),
        ("Do cats actually get bored of toys?", "Yes — cats experience habituation, where repeated exposure reduces interest. This is normal feline behaviour. Rotation mimics the novelty of hunting different prey, keeping play instincts engaged."),
        ("Should I throw away toys my cat ignores?", "Not immediately. Store ignored toys for 2 to 4 weeks then reintroduce. Cats often rediscover interest in forgotten toys. Only discard toys that are damaged, soiled beyond cleaning, or missing parts."),
        ("How many toys should a cat have in total?", "A collection of 10 to 15 toys works well for rotation, with 3 to 5 available at any time. Variety in texture, size, and play style matters more than sheer quantity."),
        ("What types of toys should I include in rotation?", "Include at least one from each category: chase toys (balls, mice), kick toys (larger plush), puzzle feeders, wand toys (supervised only), and self-play toys (crinkle, spring). This covers different play motivations."),
    ]


def cat_safety_faqs():
    return [
        ("What cat toys are dangerous?", "Avoid string, ribbon, and yarn (intestinal obstruction risk), small detachable parts (choking hazard), rubber bands, plastic bags, and toys with toxic dyes. Always supervise play with feather wands and string toys."),
        ("Can cats choke on toy parts?", "Yes — small bells, button eyes, feathers, and elastic strings are common choking hazards. Choose toys with securely attached components. If a toy shows signs of damage, replace it immediately."),
        ("Are catnip toys safe?", "Yes, catnip is non-toxic and non-addictive for cats. About 30 to 50 percent of cats do not respond to it at all. Kittens under 6 months rarely react. Excessive exposure may cause temporary digestive upset."),
        ("How do I know if a cat toy is age-appropriate?", "For kittens: soft, small, no detachable parts. For adults: match to play style and energy level. For seniors: lightweight, easy to bat, low physical demand. Always size-appropriate — too small means swallowing risk."),
        ("Should I supervise my cat with all toys?", "Supervise with wand toys, string toys, and any toy with feathers or small attachments. Self-play toys like solid balls, sturdy mice, and puzzle feeders are generally safe for unsupervised use if intact."),
    ]


def cat_enrichment_faqs():
    return [
        ("What is environmental enrichment for cats?", "Environmental enrichment provides mental and physical stimulation that mimics natural behaviours like hunting, climbing, scratching, and exploring. It prevents boredom and reduces stress-related behavioural problems."),
        ("Are DIY cat toys safe?", "Many homemade toys are safe — cardboard boxes, paper bags (handles removed), toilet roll puzzles, and sock toys. Avoid anything with small parts, toxic glues, or materials that shed fibres that could be ingested."),
        ("How do I enrich my cat's environment on a budget?", "Free options include cardboard boxes, paper bags, crinkled paper balls, ice cubes to bat, and windowsill bird-watching stations. Scatter feeding on textured surfaces costs nothing extra beyond regular food."),
        ("Can too much enrichment stress a cat?", "Yes — some cats, especially anxious ones, can be overwhelmed by too many new items at once. Introduce changes gradually. Provide retreat spaces. Watch for signs of stress: hiding, over-grooming, or loss of appetite."),
        ("What enrichment do indoor cats need most?", "Vertical space (cat trees, shelves), window access for visual stimulation, daily interactive play, puzzle feeders, and scratching surfaces. Indoor cats lack natural hunting and territory-patrolling stimulation."),
    ]


def cat_general_faqs():
    return [
        ("What supplies do I need for a new cat?", "Essential items: food and water bowls, litter tray and litter, scratching post, carrier for vet visits, age-appropriate food, and basic toys. Add a bed, brush, and cat tree once your cat is settled."),
        ("How much does basic cat care cost per month?", "Budget approximately 40 to 80 pounds monthly for food, litter, and routine supplies. Add 15 to 30 pounds monthly averaged for vet care (vaccinations, flea treatment, check-ups). Insurance is extra."),
        ("What is the most important supply for a new cat?", "A secure, appropriately sized litter tray in a quiet location. Litter tray problems are the most common reason cats are surrendered to shelters. Get this right first, then add other items."),
        ("Do cats need different supplies at different ages?", "Yes — kittens need smaller bowls, kitten food, low-sided litter trays, and size-appropriate toys. Senior cats benefit from raised food bowls, orthopaedic beds, steps to favourite spots, and easy-access trays."),
        ("How often should cat supplies be replaced?", "Food and water bowls: when chipped or stained. Litter trays: annually or when scratched/odour-retaining. Scratchers: when flattened. Beds: when hygiene declines. Toys: when damaged or showing wear."),
    ]


def puppy_toy_faqs():
    return [
        ("When can puppies start playing with toys?", "Puppies can start with soft, appropriately sized toys from 8 weeks. Choose toys too large to swallow and soft enough for developing teeth. Avoid hard nylon or antler chews until adult teeth are fully in (around 7 months)."),
        ("How many toys does a puppy need?", "Start with 5 to 8 toys of different types — a soft plush, a rubber chew, a rope toy, a ball, and a treat-dispensing puzzle. Rotate to maintain interest. Always have appropriate chew items available during teething."),
        ("Are rope toys safe for puppies?", "Rope toys are good for supervised play but should be removed when frayed. Ingested rope fibres can cause dangerous linear intestinal obstruction. Replace rope toys at the first sign of unravelling."),
        ("What puppy toys help with teething?", "Frozen rubber toys (like Kongs filled with wet food then frozen), dampened and frozen flannels, and textured teething rings soothe sore gums. The cold reduces inflammation while the texture satisfies chewing urges."),
        ("Should puppies play with tennis balls?", "Standard tennis balls are safe for supervised fetch but the fuzzy coating wears down tooth enamel over time with heavy chewing. For dedicated chewers, use smooth rubber balls designed for dogs instead."),
    ]


def puppy_care_faqs():
    return [
        ("What is the most important thing for a new puppy?", "Socialisation during the critical window (3 to 14 weeks) is the single most impactful investment. Positive exposure to varied people, environments, surfaces, and sounds shapes lifelong confidence and temperament."),
        ("How long can a puppy be left alone?", "As a guideline: their age in months plus one equals maximum hours alone (e.g., 3-month-old = 4 hours max). Build alone time gradually from minutes. Puppies under 4 months should rarely be left more than 2 hours."),
        ("When should a puppy start training?", "Training begins the moment your puppy arrives home. Start with name recognition, toilet training, and basic settle behaviour. Formal cue training (sit, down, recall) can begin at 8 weeks using positive methods."),
        ("How much sleep does a puppy need?", "Puppies need 18 to 20 hours of sleep daily. Overtired puppies become hyperactive, nippy, and unable to learn. Enforce nap times in a quiet crate or pen after every 45 to 60 minutes of activity."),
        ("What vaccinations does a puppy need?", "Core UK vaccinations cover distemper, parvovirus, hepatitis, and leptospirosis (typically at 8 and 10 weeks). Kennel cough is recommended if mixing with other dogs. Your vet will advise on the schedule for your area."),
    ]


def dog_toy_cleaning_faqs():
    return [
        ("How often should I clean my dog's toys?", "Wash fabric toys weekly in a machine (no fabric softener). Wipe rubber toys daily and deep-clean weekly. Replace rope toys when frayed. High-use items like Kongs should be cleaned after each use to prevent bacteria."),
        ("Can I put dog toys in the dishwasher?", "Solid rubber and hard plastic toys (without electronics or squeakers) can go on the top rack of a dishwasher. Use no detergent or a pet-safe option. The heat sanitises effectively. Air-dry completely before returning."),
        ("What cleaning products are safe for dog toys?", "Use pet-safe disinfectants, diluted white vinegar (1:1 with water), or baking soda paste. Avoid bleach, essential oils, and standard household cleaners. Rinse thoroughly — residue from any product can irritate."),
        ("When should I throw away a dog toy instead of cleaning it?", "Discard toys with: mould that persists after cleaning, exposed stuffing or foam, cracked rubber, missing pieces, persistent odour despite washing, or any damage that creates small swallowable pieces."),
        ("Can dirty dog toys make my dog ill?", "Yes — bacteria, mould, and yeast accumulate on unwashed toys, potentially causing gastrointestinal upset or skin reactions. Toys used outdoors also collect soil bacteria. Regular cleaning reduces illness risk."),
    ]


def dog_toy_durability_faqs():
    return [
        ("What material is most durable for dog toys?", "Natural rubber and industrial-grade nylon are the most durable options for aggressive chewers. Solid rubber Kongs, Nylabone products, and reinforced fire hose toys outlast plush and rope alternatives significantly."),
        ("How long should a dog toy last?", "Durable rubber toys can last 6 to 12 months even with daily use. Plush toys may only survive days with aggressive chewers. Rope toys typically last 2 to 4 weeks. Replace any toy showing damage or wear."),
        ("Are 'indestructible' dog toys really indestructible?", "No toy is truly indestructible. Marketing claims of indestructibility are relative to average use. Determined power chewers can damage any toy. Always supervise and remove toys showing cracks, tears, or pieces breaking off."),
        ("Why does my dog destroy toys so quickly?", "Breed instinct (terriers, herding breeds), high drive, boredom, insufficient mental stimulation, or anxiety can all cause rapid toy destruction. Channel the urge to appropriate heavy-duty items rather than suppressing it."),
        ("Is it bad for dogs to destroy their toys?", "Moderate destruction is natural and satisfying for dogs. The danger is ingesting pieces. Provide toys designed for shredding (like layered rubber) and remove debris. If your dog swallows pieces, switch to indestructible options only."),
    ]


def dog_rotation_faqs():
    return [
        ("How many toys should I rotate for my dog?", "Keep 3 to 5 toys available at a time from a collection of 10 to 15. Rotate every 3 to 5 days. This provides enough variety for daily engagement while maintaining the novelty effect when stored toys return."),
        ("Does toy rotation actually work for dogs?", "Yes — research shows dogs habituate to familiar objects but show renewed interest in items removed and reintroduced after a gap. Even 2 days of absence is enough to restore novelty for most dogs."),
        ("Should I include different types in each rotation?", "Yes — each rotation should include at least one chew item, one interactive/puzzle toy, and one fetch or tug toy. This ensures all play motivations are covered regardless of which specific toys are available."),
        ("How do I start toy rotation with a possessive dog?", "Begin by adding new toys rather than removing favourites. Once your dog has multiple favourites, start swapping less valued items. Never remove a toy the dog is actively using or guarding."),
        ("Can I rotate toys for multiple dogs?", "Yes, but track which toys each dog prefers and ensure favourites are available to avoid conflict. In multi-dog homes, each dog should have their own rotation plus shared items they enjoy together."),
    ]


def dog_anxiety_faqs():
    return [
        ("Can toys really help with dog anxiety?", "Yes — lick mats, Kongs, and chew items trigger calming endorphin release. They redirect anxious energy into a productive activity. They work best alongside broader anxiety management, not as sole treatment."),
        ("What toys are best for separation anxiety?", "Stuffable toys with frozen fillings (lasting 20-30 minutes), lick mats with spreadable paste, and calm chew items work well. Give them only when you leave so they become a positive departure cue."),
        ("How do I know if my dog is anxious or just excited?", "Anxiety signs: lip licking, whale eye (showing whites), panting without exercise, tucked tail, yawning, pacing, and inability to settle. Excitement: play bows, loose body, wide-open mouth, bouncy movement."),
        ("Should I leave toys out for an anxious dog when alone?", "Leave 2 to 3 safe, familiar, high-value enrichment items (not interactive toys that could frustrate). Avoid toys that could be destroyed and ingested. A stuffed Kong and a lick mat are safer than a plush toy."),
        ("When should I seek professional help for dog anxiety?", "Seek help when: anxiety affects daily quality of life, destructive behaviour causes self-harm, your dog cannot eat when stressed, symptoms worsen over time, or basic management strategies show no improvement after 4 weeks."),
    ]


def senior_dog_faqs():
    return [
        ("At what age is a dog considered senior?", "It depends on size — small breeds (under 10kg) around 10 to 12 years, medium breeds around 8 to 10, large breeds around 6 to 8, and giant breeds as early as 5 to 6 years. Veterinary guidance is individual."),
        ("What mental stimulation is safe for senior dogs?", "Nose work at ground level, simple puzzle feeders, short gentle training sessions, calm sensory experiences (sniff walks), and food-based enrichment. Avoid activities requiring jumping, sustained standing, or fast reactions."),
        ("How do I know if my senior dog has cognitive decline?", "Watch for: disorientation in familiar spaces, altered sleep patterns (restlessness at night), loss of house training, reduced social interaction, staring at walls, forgetting learned behaviours. Report changes to your vet."),
        ("Should senior dogs still play?", "Absolutely — play maintains cognitive function, strengthens bonds, and provides gentle exercise. Adapt the type and duration to their capability. Let them set the pace and always allow rest when they choose to stop."),
        ("How can I keep my senior dog's brain active?", "Rotate novel scents (herbs, spices on toys), teach new gentle tricks, vary walking routes for different smells, use food puzzles at their difficulty level, and provide calm social interaction with people they enjoy."),
    ]


def enrichment_schedule_faqs():
    return [
        ("How much enrichment does a dog need daily?", "Most dogs benefit from 30 to 60 minutes of total enrichment daily, split across multiple sessions. This includes puzzle feeding, training, social play, and exploration. Working breeds may need more."),
        ("What does a good daily enrichment schedule look like?", "Morning: scatter feed or puzzle breakfast. Midday: 10-minute training or nose work session. Afternoon: interactive play or food-stuffed toy. Evening: calm enrichment (lick mat, gentle chew). Adjust to your dog's energy."),
        ("Can you over-enrich a dog?", "Yes — signs include inability to settle, frustration with puzzles, refusing food rewards, or hyperactivity. Balance enrichment with enforced calm time. Dogs also need to learn to do nothing without stimulation."),
        ("Should enrichment replace walks?", "No — walks provide physical exercise, environmental exploration, and social opportunities that enrichment at home cannot fully replicate. Enrichment supplements walks rather than replacing them, especially for mobile dogs."),
        ("How do I enrich a dog with limited time?", "Feed all meals through slow feeders or scatter feeding (takes the same time to prepare, adds 15+ minutes of enrichment). Frozen Kongs prepared in batches last 20-30 minutes each with minimal daily effort."),
    ]


def overstimulation_faqs():
    return [
        ("What does toy overstimulation look like in dogs?", "Signs include: frantic behaviour, inability to release the toy, growling or snapping when interrupted, glazed eyes, increasingly rough play, panting excessively, and inability to respond to cues they normally know."),
        ("How do I calm an overstimulated dog?", "Remove the stimulating item calmly. Guide your dog to a quiet area or settle mat. Offer a calm activity (lick mat, gentle chew). Speak softly. Wait for their breathing to normalise before any further interaction."),
        ("How long does it take an overstimulated dog to calm down?", "Typically 10 to 30 minutes depending on arousal level. Some dogs need 1 to 2 hours after extreme arousal. Physical distance from the trigger and a calm environment speed recovery. Avoid adding further stimulation."),
        ("Can overstimulation cause aggression?", "Yes — dogs in a highly aroused state have reduced impulse control and may redirect frustration into nipping, snapping, or guarding behaviour. This is reactive, not deliberate aggression. Prevention is easier than correction."),
        ("How do I prevent toy overstimulation?", "End play sessions before peak arousal. Learn your dog's escalation signs (faster breathing, harder grabbing, louder vocalisation). Use calm cues to break intensity. Keep sessions to 10 to 15 minutes maximum."),
    ]


def low_mobility_faqs():
    return [
        ("What enrichment works for dogs that cannot walk far?", "Nose work (scatter feeding, snuffle mats), lick mats, puzzle feeders at resting height, gentle training from a lying position, and window watching. Mental engagement does not require physical movement."),
        ("Can dogs with arthritis still play?", "Yes, with adaptations. Short, gentle sessions on soft surfaces. Avoid jumping, sharp turns, and sustained standing. Slow-moving toys, nose work, and calm food puzzles provide enrichment without joint stress."),
        ("How do I keep a crate-rested dog mentally engaged?", "Frozen Kongs (multiple per day), lick mats attached to crate sides, calm chews, nose work within reach, gentle trick training (paw touches, chin rest), and calm human interaction. Rotate items frequently."),
        ("Is sniffing enough exercise for a low-mobility dog?", "Sniffing provides significant mental exercise — 10 minutes of focused nose work can be as tiring as a 30-minute walk. For low-mobility dogs, structured sniff activities are the primary enrichment tool available."),
        ("How do I know if my low-mobility dog is bored?", "Signs include: destructive behaviour within their space, excessive licking or chewing themselves, vocalisation changes, reduced appetite (boredom, not pain), repetitive movements, and increased restlessness."),
    ]


def puzzle_toy_faqs():
    return [
        ("What level puzzle should I start my dog on?", "Start at the easiest level regardless of your dog's intelligence. Early success builds confidence and motivation. Only increase difficulty once your dog solves the current level quickly and without frustration."),
        ("How long should a puzzle toy take my dog?", "For food-dispensing puzzles: 5 to 20 minutes is ideal. If solved in under 2 minutes, increase difficulty. If your dog gives up, make it easier. Frozen stuffed toys should last 15 to 30 minutes."),
        ("Can puzzle toys replace a meal?", "Yes — feeding entire meals through puzzle feeders is excellent enrichment. Measure out the normal portion and distribute across 2 to 3 puzzles for extended engagement. This mimics natural foraging behaviour."),
        ("Are puzzle toys safe to leave with my dog unsupervised?", "Simple dispensing toys (Kongs, wobble feeders) are generally safe. Complex puzzles with removable parts should be supervised — some dogs destroy the puzzle rather than solve it, risking ingestion of pieces."),
        ("How many puzzle toys does a dog need?", "Three to five different types allows good rotation: a stuffable toy, a rolling dispenser, a snuffle mat, a slider puzzle, and a lick mat. Variety prevents habituation and engages different problem-solving approaches."),
    ]


def boredom_faqs():
    return [
        ("How do I know if my dog is bored?", "Common signs: destructive chewing (furniture, shoes), excessive barking or whining, digging, pacing, tail chasing, attention-seeking behaviour, and loss of interest in usual activities. Bored dogs create their own entertainment."),
        ("How much activity prevents dog boredom?", "Most adult dogs need 1 to 2 hours of physical exercise plus 30 to 60 minutes of mental enrichment daily. High-energy breeds may need more. The ratio of physical to mental work depends on breed type and age."),
        ("Can dogs be bored even with lots of toys?", "Yes — dogs need variety, novelty, and interactive engagement, not just access to objects. A pile of familiar toys cannot replace human interaction, novel experiences, and appropriately challenging activities."),
        ("What is the fastest way to engage a bored dog?", "Scatter a handful of kibble in grass for foraging (instant nose work), play a 5-minute training game with treats, or offer a new novel item to investigate. Quick engagement breaks prevent boredom escalation."),
        ("Do some breeds get bored more easily?", "Yes — working breeds (collies, spaniels, terriers) were bred for sustained mental and physical tasks. Without appropriate outlets, they are more likely to develop boredom-related behaviours than naturally calmer companion breeds."),
    ]


def enrichment_general_faqs():
    return [
        ("What counts as enrichment for a dog?", "Anything that provides mental or sensory stimulation beyond basic needs: puzzle feeders, training, novel experiences, social play, scent work, exploration, varied environments, and opportunities to make choices."),
        ("Is enrichment the same as exercise?", "No — exercise addresses physical needs while enrichment addresses cognitive and sensory needs. A tired dog can still be mentally under-stimulated. Effective care provides both: physical activity and mental engagement."),
        ("Can enrichment help behavioural problems?", "Often yes — many problem behaviours (destruction, barking, digging) stem from unmet mental needs. Appropriate enrichment provides legal outlets for natural behaviours. Severe issues may also need professional behavioural support."),
        ("How do I know what enrichment my dog prefers?", "Offer different types and observe: Does your dog prefer nose work or physical play? Solving puzzles or shredding? Chasing or tugging? Build your enrichment programme around what genuinely engages your individual dog."),
        ("Is food-based enrichment OK for overweight dogs?", "Yes — use their daily food allowance in enrichment feeders rather than a bowl. This adds mental stimulation without extra calories. Reduce treat-based enrichment and increase non-food options like nose work and play."),
    ]


def tug_play_faqs():
    return [
        ("Is tug of war bad for dogs?", "No — when played with rules, tug is excellent exercise and bonding. It does not cause aggression. Research shows dogs who play tug with owners are actually more obedient and confident, not more dominant."),
        ("What are the rules for safe tug play?", "Use a designated tug toy only. Dog must release on cue (train 'drop'). Stop immediately if teeth touch skin. Keep tugging motions side-to-side (not up and down to protect neck). You initiate and end the game."),
        ("Is tug safe for puppies?", "Gentle tug is fine for puppies over 12 weeks with adult teeth emerging. Use soft rope toys, let the puppy set the intensity, and avoid jerking motions. Stop if the puppy becomes overly aroused or mouthy."),
        ("What is the best tug toy material?", "Natural rubber handles with fleece or rope centres work well — they are gentle on teeth and easy to grip. Avoid hard plastic handles, thin string, and anything that could snap and recoil. Length of 40cm+ is ideal."),
        ("How do I teach my dog to let go during tug?", "Hold the toy still (boring) and present a treat near their nose. Mark and reward the moment they release. Practice 'drop' separately before incorporating into play. Most dogs learn within 5 to 10 short sessions."),
    ]


def confidence_faqs():
    return [
        ("How do I build confidence in a fearful dog?", "Start in a safe environment with low-pressure activities. Reward any brave exploration. Let the dog choose to approach new things — never force. Gradual positive exposure at the dog's pace builds lasting confidence."),
        ("What toys help shy dogs?", "Soft, non-threatening toys initially — snuffle mats, gentle treat dispensers, familiar scented items. Avoid noisy, fast-moving, or unpredictable toys which may startle. Introduce novelty very gradually."),
        ("How long does it take to build a shy dog's confidence?", "Weeks to months depending on the cause and severity. Rescue dogs with trauma may take 3 to 6 months of patient work. Consistency matters more than speed. Celebrate small progress rather than expecting rapid change."),
        ("Can play really help anxious dogs?", "Yes — play releases endorphins, builds positive associations with environments, and strengthens the human-dog bond (a major anxiety buffer). Keep sessions short, pressure-free, and always let the dog opt out."),
        ("Should I push a shy dog to try new things?", "Never force or flood. Offer opportunities without pressure. If the dog retreats, respect that choice. Forced exposure worsens fear. Let curiosity develop naturally — confident dogs choose to explore; frightened ones need time."),
    ]


def harness_faqs():
    return [
        ("Is a harness better than a collar for dogs?", "Harnesses distribute pressure across the chest rather than concentrating it on the throat. They are particularly recommended for small breeds, dogs with respiratory issues, puppies, and dogs that pull on the lead."),
        ("What type of harness stops pulling?", "Front-clip harnesses redirect pulling energy sideways, naturally discouraging forward pulling. They are a management tool — combine with training for lasting behaviour change. Back-clip harnesses do not reduce pulling."),
        ("How tight should a dog harness be?", "You should fit two fingers flat between the harness and your dog at any point. Check the neck, chest, and behind the front legs. Too tight causes rubbing; too loose allows escape or leg entrapment."),
        ("Can a dog wear a harness all day?", "Harnesses should be removed when unsupervised indoors to prevent rubbing, overheating, and strap entanglement. They are designed for walks and outdoor activities, not continuous wear."),
        ("At what age can a puppy wear a harness?", "Puppies can wear a properly fitted harness from 8 weeks. Choose adjustable models that grow with them. Introduce gradually with positive associations (treats while wearing it) before attaching a lead."),
    ]


def bed_sizing_faqs():
    return [
        ("How do I measure my dog for a bed?", "Measure from nose tip to tail base while your dog lies on their side in a natural sleeping position. Add 15 to 20cm to both length and width for comfort. Measure height at the shoulder for bolster beds."),
        ("What size bed does my dog need?", "Your dog should be able to stretch out fully in any direction without hanging over edges. For curlers, the bed diameter should be at least 1.5 times their curled-up body length."),
        ("Do dogs prefer bigger or smaller beds?", "Most dogs prefer a bed that fits closely enough to feel secure but large enough to stretch. Giant oversized beds can feel exposed for smaller dogs. Bolsters or sides provide a sense of enclosure many dogs prefer."),
        ("Should I get a bigger bed for a growing puppy?", "For puppies, either buy for adult size with a removable bolster insert, or expect to replace the bed 2 to 3 times as they grow. A bed that is too large offers less warmth and security for very young puppies."),
        ("How often should a dog bed be replaced?", "Replace when the bed loses support (flat padding), smells persist after washing, the cover is damaged beyond repair, or your dog's needs change (orthopaedic support for ageing joints). Typically every 1 to 3 years."),
    ]


def pet_enrichment_faqs():
    return [
        ("What is pet enrichment and why does it matter?", "Pet enrichment provides mental, physical, and sensory stimulation that mimics natural behaviours. It prevents boredom, reduces stress, and improves welfare. Pets without enrichment often develop behavioural problems."),
        ("Do all pets need enrichment?", "Yes — every pet benefits from appropriate stimulation, though types and amounts vary. Dogs need more interactive enrichment than cats, who need more independent exploration opportunities. Even fish benefit from varied environments."),
        ("How do I know if my pet is under-stimulated?", "Common signs across species: repetitive behaviours (pacing, circling), destructive actions, excessive vocalisation, lethargy or depression, aggression, over-grooming, and changes in eating patterns."),
        ("Can enrichment replace human interaction?", "No — for social species like dogs, human interaction is itself a form of enrichment. Puzzles and toys supplement but cannot replace the bonding, communication, and social stimulation that direct engagement provides."),
        ("What is the easiest daily enrichment to implement?", "Feed meals through puzzle feeders rather than bowls. This requires zero extra time or cost but adds 15 to 30 minutes of mental engagement to every meal. It works for both dogs and cats."),
    ]


def generic_pet_faqs(title):
    topic = strip_html(title).split(':')[0] if ':' in strip_html(title) else strip_html(title)
    return [
        (f"What should I consider first when learning about {topic.lower()}?", "Start by understanding your pet's individual needs, age, and health status. General guides provide frameworks, but every pet is different. Observe your pet's responses and adjust recommendations to suit them specifically."),
        ("Where can I find reliable information about pet care?", "Look for content citing veterinary organisations (BVA, RCVS), peer-reviewed research, or established animal welfare charities (RSPCA, Cats Protection, Dogs Trust). Be cautious of anecdotal advice without evidence."),
        ("When should I consult a professional instead of researching online?", "Always consult a vet for health concerns, sudden behaviour changes, or emergency situations. Online guides are educational — they cannot assess your individual pet or replace hands-on professional evaluation."),
        ("How often do pet care recommendations change?", "Best practices evolve as research progresses. Training methods, nutrition guidelines, and welfare understanding have changed significantly in the last decade. Check publication dates and prefer recent, evidence-based sources."),
        ("Is expensive always better for pet products?", "Not necessarily. Price does not always correlate with quality or suitability. Focus on safety certification, appropriate materials, correct sizing, and your pet's actual preferences rather than brand prestige or cost alone."),
    ]


def build_faq_html(faq_items):
    """Build Gutenberg FAQ block HTML from question-answer pairs."""
    blocks = []
    for q, a in faq_items:
        blocks.append(f"""<!-- wp:heading {{"level":3}} -->
<h3>{q}</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>{a}</p>
<!-- /wp:paragraph -->""")
    return "\n\n".join(blocks)


def insert_faq_items(content_html, faq_html):
    """Insert FAQ items into existing FAQ section or append before Sources."""
    # Look for existing FAQ section end (before Sources or end of content)
    faq_heading = re.search(
        r'(<!-- wp:heading[^>]*-->\s*<h2[^>]*>.*?(?:FAQ|Frequently Asked).*?</h2>\s*<!-- /wp:heading -->)',
        content_html, re.IGNORECASE | re.DOTALL
    )

    if faq_heading:
        # Find the next H2 after the FAQ heading (Sources, References, etc.)
        faq_start = faq_heading.end()
        next_h2 = re.search(r'<!-- wp:heading\s*(?:\{[^}]*\})?\s*-->\s*<h2', content_html[faq_start:])
        if next_h2:
            insert_pos = faq_start + next_h2.start()
        else:
            insert_pos = len(content_html)
        # Insert before the next section
        return content_html[:insert_pos] + "\n\n" + faq_html + "\n\n" + content_html[insert_pos:]
    else:
        # No FAQ section found — create one before Sources or at end
        sources_match = re.search(
            r'<!-- wp:heading[^>]*-->\s*<h2[^>]*>.*?(?:Sources|References).*?</h2>',
            content_html, re.IGNORECASE | re.DOTALL
        )
        faq_section = """<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

""" + faq_html

        if sources_match:
            insert_pos = sources_match.start()
            return content_html[:insert_pos] + faq_section + "\n\n" + content_html[insert_pos:]
        else:
            return content_html + "\n\n" + faq_section


def count_faq_questions(content_html):
    """Count existing FAQ H3 questions."""
    faq_section_start = re.search(
        r'<!-- wp:heading[^>]*-->\s*<h2[^>]*>.*?(?:FAQ|Frequently Asked).*?</h2>',
        content_html, re.IGNORECASE | re.DOTALL
    )
    if not faq_section_start:
        return 0
    section_content = content_html[faq_section_start.end():]
    next_h2 = re.search(r'<!-- wp:heading\s*(?:\{[^}]*\})?\s*-->\s*<h2', section_content)
    if next_h2:
        section_content = section_content[:next_h2.start()]
    return len(re.findall(r'<h3[^>]*>.*?\?</h3>', section_content, re.IGNORECASE))


def main():
    print("=" * 70)
    print("Phase 12O: FAQ Expansion")
    print(f"Target: {len(POST_IDS)} posts (expand to 5+ questions)")
    print("=" * 70)
    print()

    success = 0
    errors = 0
    skipped = 0

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

        existing_count = count_faq_questions(content)
        if existing_count >= 5:
            print(f"[{i:2d}/{len(POST_IDS)}] Post {post_id}: {title_clean} — ALREADY HAS {existing_count} FAQs, skipping")
            skipped += 1
            time.sleep(1)
            continue

        faq_items = generate_faq_items(title)
        # Only add enough to reach 5+ total
        items_needed = max(0, 5 - existing_count)
        faq_items = faq_items[:items_needed] if items_needed < len(faq_items) else faq_items

        faq_html = build_faq_html(faq_items)
        new_content = insert_faq_items(content, faq_html)

        update_data = {"content": new_content}
        resp = curl_post_json(f"{WP_API}/posts/{post_id}", update_data)

        if resp and isinstance(resp, dict) and resp.get('id'):
            success += 1
            new_count = existing_count + len(faq_items)
            print(f"[{i:2d}/{len(POST_IDS)}] Post {post_id}: {title_clean} — EXPANDED ({existing_count}->{new_count} FAQs)")
        else:
            errors += 1
            err_msg = resp.get('message', str(resp)[:80]) if isinstance(resp, dict) else str(resp)[:80]
            print(f"[{i:2d}/{len(POST_IDS)}] Post {post_id}: {title_clean} — ERROR: {err_msg}")

        time.sleep(5)

    print()
    print("=" * 70)
    print(f"RESULTS: {success} expanded, {skipped} skipped, {errors} errors")
    print("=" * 70)


if __name__ == '__main__':
    main()
