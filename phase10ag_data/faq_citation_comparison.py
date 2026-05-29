#!/usr/bin/env python3
"""
PetHub Online - Phase 10AG: Quick Answers, Sources Verification, and Comparison Tables
Processes posts in three lanes:
1. Quick Answer blocks for posts missing them
2. Sources verification (already complete per audit)
3. Comparison tables for posts missing them (target: 30 posts)
"""

import subprocess
import json
import time
import csv
import os
import re
import tempfile

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
API_BASE = "https://pethubonline.com/wp-json/wp/v2"
LOG_PATH = "/var/lib/freelancer/projects/40416335/phase10ag_data/faq_citation_comparison_log.csv"
DELAY = 0.5

# ─── POST LISTS ───────────────────────────────────────────────────────────

# Part 1: Posts that need Quick Answer (from inventory + audit)
QUICK_ANSWER_POST_IDS = [
    5930,  # Dog Toy Safety by Breed Size
    6052, 6050, 6049, 6048, 6047, 6046, 6045, 6044, 6042, 6039,
    5950, 5946, 5942, 5938, 5935,
    3996, 3959, 3957, 3956,
]

# Part 2: Posts that need Sources - NONE (all already have them per audit)
SOURCES_POST_IDS = []

# Part 3: Posts that need Comparison Tables (30 posts, prioritized by cluster)
# Priority: Dog Toys > Dog Beds > Puppy Care > Dog Health > Dog Training > Indoor Cats
COMPARISON_TABLE_POST_IDS = [
    # Dog Toys cluster (from listed posts)
    5942, 5938, 5935, 5934, 5933, 5932, 5931, 3957,
    # Dog Toys extended
    5425, 5424, 5423, 5421, 5415,
    # Indoor Cats
    5519, 5296, 5034, 5033, 5032,
    # Puppy Care
    4792, 4791, 4790, 4789, 4788, 4787,
    # Dog Beds
    4786, 4785, 4783,
    # Dog Health
    4574, 4571, 4568,
    # Dog Training
    5462,
]

# All unique post IDs to process
ALL_POST_IDS = sorted(set(QUICK_ANSWER_POST_IDS + SOURCES_POST_IDS + COMPARISON_TABLE_POST_IDS))


def api_get(endpoint):
    """Fetch from WP API using curl subprocess."""
    url = f"{API_BASE}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    return json.loads(result.stdout)


def api_update_post(post_id, content):
    """Update post content using curl with temp file for payload."""
    url = f"{API_BASE}/posts/{post_id}"
    payload = json.dumps({"content": content})

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(payload)
        tmpfile = f.name

    try:
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", f"@{tmpfile}",
             url],
            capture_output=True, text=True, timeout=60
        )
        resp = json.loads(result.stdout)
        if 'id' in resp:
            return True
        else:
            print(f"  ERROR updating {post_id}: {result.stdout[:300]}")
            return False
    finally:
        os.unlink(tmpfile)


def generate_quick_answer(title, content_snippet):
    """Generate a contextual 2-3 sentence quick answer based on the post title and content."""
    title_lower = title.lower()

    # ─── Dog Toys cluster ───
    if "toy safety by breed size" in title_lower or "choosing the right size toy" in title_lower:
        return "Choosing the correct toy size for your dog's breed is essential for safety. Toys that are too small pose a choking hazard, while oversized toys can cause jaw strain or frustration. As a general rule, the toy should be large enough that your dog cannot fit it entirely in their mouth, yet light enough for comfortable play."

    if "toy durability" in title_lower or "what lasts" in title_lower:
        return "Not all dog toys are built to last equally. Natural rubber and reinforced nylon tend to outlast plush and rope toys, especially for strong chewers. Understanding your dog's chewing style helps you choose toys that provide lasting enrichment without becoming a safety hazard."

    if "toy materials compared" in title_lower or "rubber, rope, plush" in title_lower:
        return "Each dog toy material offers different benefits and risks. Natural rubber is durable and safe for most chewers, rope toys support dental health but need monitoring for fraying, plush toys suit gentle players, and nylon provides long-lasting chewing satisfaction. Choosing the right material depends on your dog's play style and chewing strength."

    if "cognitive enrichment for senior" in title_lower:
        return "Senior dogs benefit greatly from gentle mental stimulation that accounts for reduced mobility and slower processing. Food puzzles, scent games, and low-impact problem-solving activities keep ageing minds sharp without causing physical strain. Adjusting difficulty levels ensures your older dog stays engaged without becoming frustrated."

    if "enrichment schedules" in title_lower:
        return "Structuring your dog's daily enrichment ensures they receive balanced mental and physical stimulation throughout the day. A good schedule combines active play sessions, food puzzles, training exercises, and rest periods. Consistency helps dogs feel secure while variety prevents boredom."

    if "toy storage and organisation" in title_lower:
        return "Proper toy storage keeps your dog's toys clean, safe, and interesting. Rotating toys in and out of a designated storage area maintains novelty, while regular inspection helps you remove damaged items before they become hazards. A simple organisation system saves time and keeps your home tidy."

    if "crate and play enrichment" in title_lower or "crate enrichment" in title_lower:
        return "Crate enrichment transforms confined time into positive, mentally stimulating experiences for your dog. Safe toys, food puzzles, and calming activities like lick mats help dogs associate their crate with comfort rather than boredom. The right enrichment choices depend on your dog's size, temperament, and the duration of crate time."

    if "safe tug play" in title_lower or "tug play" in title_lower:
        return "Tug play is a natural, beneficial activity for dogs when done with proper rules and boundaries. Using a designated tug toy, teaching a reliable drop command, and keeping sessions short prevents overexcitement. Contrary to common myths, structured tug games do not encourage aggression and can actually strengthen your bond with your dog."

    if "scent-game enrichment" in title_lower or "scent game" in title_lower:
        return "Scent games tap into your dog's most powerful sense, providing intense mental stimulation with minimal physical effort. Activities like treat trails, hidden toy searches, and snuffle mats can tire a dog out as effectively as a long walk. Scent work builds confidence and is suitable for dogs of all ages, sizes, and fitness levels."

    if "toy overstimulation" in title_lower and "signs" in title_lower:
        return "Recognising the signs of toy overstimulation helps you intervene before play escalates into stress or reactive behaviour. Common indicators include frantic movements, inability to settle, excessive vocalisation, and resource guarding. Learning when to end a play session is just as important as knowing how to start one."

    # ─── Dog Toys extended ───
    if "dog toys faq" in title_lower:
        return "Dog toy safety, suitability, and maintenance are the most common concerns for pet owners. Choosing age-appropriate toys, supervising play, and replacing damaged items are fundamental practices. This FAQ addresses the questions veterinarians and behaviourists hear most often about dog toys."

    if "aggressive chewer" in title_lower or "power chewer" in title_lower:
        return "Power chewers need toys specifically designed to withstand intense jaw pressure without breaking into dangerous fragments. Natural rubber, solid nylon, and reinforced composite toys are the safest options for aggressive chewers. Always supervise play and replace any toy showing signs of significant wear."

    if "toy enrichment" in title_lower and "beyond basic fetch" in title_lower:
        return "Dog toy enrichment goes far beyond throwing a ball. Food-dispensing puzzles, scent work toys, and interactive games challenge your dog's problem-solving abilities and reduce boredom-related behaviour. Varying enrichment types throughout the week keeps your dog mentally engaged and emotionally balanced."

    if "puppy-safe dog toys" in title_lower or "puppy safe" in title_lower:
        return "Puppies need toys that are safe for developing teeth and gums while satisfying their natural urge to chew. Soft rubber teething toys, appropriately sized plush toys without small detachable parts, and frozen enrichment items are ideal choices. Avoid toys with button eyes, squeakers that can be swallowed, or materials that splinter."

    if "dog play styles" in title_lower:
        return "Understanding your dog's natural play style helps you choose the most engaging toys and activities. Common play styles include chasers, tuggers, wrestlers, and solitary chewers, with many dogs showing a preference for one or two styles. Matching toys to your dog's play personality increases enjoyment and reduces frustration."

    # ─── Indoor Cats ───
    if "indoor cat care" in title_lower and "complete guide" in title_lower:
        return "Indoor cats live longer on average than outdoor cats, but they need specific environmental enrichment to stay physically and mentally healthy. Providing vertical space, interactive play sessions, window access, and rotating toys prevents the boredom and stress that can lead to behavioural and health problems."

    if "indoor cat toys" in title_lower and "enrichment" in title_lower:
        return "House cats depend entirely on their owners for mental and physical stimulation. The best indoor cat toys mimic natural hunting behaviours through movement, texture, and unpredictability. A combination of wand toys, puzzle feeders, and self-play toys ensures your indoor cat stays active and content."

    if "cat toy rotation" in title_lower:
        return "Rotating your cat's toys on a regular schedule prevents habituation and maintains their interest in play. Cats are naturally drawn to novelty, so swapping toys every few days mimics the variety they would encounter outdoors. A simple rotation system using two or three toy groups keeps play sessions engaging without buying new toys constantly."

    if "choose the right cat toy" in title_lower or "cat's personality" in title_lower:
        return "Every cat has a unique play personality shaped by breed, age, and individual temperament. Some cats prefer stalking and pouncing, while others enjoy batting, wrestling, or chasing. Observing your cat's natural hunting style helps you select toys that provide the most satisfying play experience."

    if "cat toys faq" in title_lower:
        return "Cat toy safety, frequency of play, and knowing when to replace toys are the most common questions from cat owners. Interactive play for at least 15 to 20 minutes daily is recommended for most cats, with toy inspections for wear and damage forming a regular habit. This FAQ covers the essential questions about keeping your cat entertained and safe."

    # ─── Puppy Care ───
    if "puppy socialisation" in title_lower:
        return "The critical socialisation window for puppies runs from roughly 3 to 14 weeks of age, during which positive exposure to diverse people, animals, sounds, and environments shapes lifelong temperament. Early, gentle socialisation reduces the risk of fear-based aggression and anxiety in adult dogs. A structured timeline helps ensure you cover all key experiences safely."

    if "choose the right dog training treats" in title_lower or ("training treats" in title_lower and "choose" in title_lower):
        return "The best training treats are small, soft, and highly appealing to your dog, allowing rapid delivery during training sessions without filling them up. Treats should make up no more than 10 per cent of your dog's daily calorie intake to maintain a healthy weight. Varying treat value helps you reward different levels of effort appropriately."

    if "diy dog toys" in title_lower:
        return "Homemade dog toys can be safe, affordable, and just as engaging as shop-bought options when made with appropriate materials. Old t-shirts, tennis balls, and muffin tins can be transformed into enrichment activities with minimal effort. Always supervise play with DIY toys and remove them if any parts start to come loose."

    if "types of dog toys for different play styles" in title_lower or "best types of dog toys" in title_lower:
        return "Different dogs enjoy different types of play, and matching toy types to your dog's natural preferences maximises engagement. Fetch toys suit chase-driven dogs, tug toys satisfy wrestling instincts, puzzle toys challenge problem-solvers, and chew toys meet the needs of oral fixators. Offering a variety ensures well-rounded enrichment."

    if "mental stimulation for dogs" in title_lower:
        return "Mental exercise is just as important as physical activity for a dog's overall wellbeing. Puzzle toys, training games, scent work, and novel experiences tire the brain and reduce common behaviour problems linked to boredom. Even 10 to 15 minutes of focused mental enrichment can be as tiring as a 30-minute walk."

    if "dog toy safety" in title_lower and "every owner" in title_lower:
        return "Dog toy safety starts with choosing the right size, material, and type for your individual dog. Regularly inspecting toys for damage, removing broken pieces promptly, and supervising play sessions are the most effective ways to prevent choking, intestinal blockages, and other toy-related injuries."

    # ─── Dog Beds ───
    if "where to place your dog" in title_lower and "bed" in title_lower:
        return "Where you place your dog's bed significantly affects their sleep quality and sense of security. Ideal locations are quiet, draught-free areas away from direct heat sources and heavy foot traffic. Most dogs prefer sleeping near their family, so a corner of the living room or bedroom often works best."

    if "wash and maintain" in title_lower and "dog" in title_lower and "bed" in title_lower:
        return "Regular washing keeps your dog's bed hygienic and extends its lifespan. Most dog bed covers can be machine washed at 30 to 40 degrees Celsius using pet-safe detergent, while memory foam inserts should be spot-cleaned and aired. Washing every one to two weeks, or more frequently for dogs with allergies, is recommended."

    if "choose the right dog bed size" in title_lower:
        return "A properly sized dog bed allows your dog to stretch out fully in their preferred sleeping position with a few centimetres to spare on each side. Measure your dog from nose to tail base while lying down, then add 15 to 20 centimetres to determine the minimum bed length. Choosing between flat, bolster, and nest styles depends on whether your dog sleeps curled, sprawled, or nestled."

    # ─── Dog Health ───
    if "pet hydration" in title_lower:
        return "Dogs typically need 50 to 60 millilitres of water per kilogram of body weight daily, while cats need around 40 to 60 millilitres per kilogram. Factors like diet, activity level, and weather significantly affect hydration needs. Monitoring water intake and recognising early signs of dehydration helps prevent serious health problems."

    if "pet first aid" in title_lower:
        return "Knowing basic pet first aid can stabilise your animal in an emergency and potentially save their life before you reach a veterinarian. Essential skills include controlling bleeding, recognising signs of poisoning, performing rescue breathing, and safely transporting an injured pet. A well-stocked pet first aid kit at home and in the car is a practical starting point."

    if "dog dental health" in title_lower:
        return "Dental disease affects the majority of dogs over the age of three and can lead to pain, infection, and organ damage if left untreated. Daily tooth brushing with dog-specific toothpaste is the most effective preventive measure, supplemented by dental chews and regular veterinary check-ups. Early signs include bad breath, red gums, and reluctance to eat hard food."

    # ─── Dog Training ───
    if "dog training terminology" in title_lower:
        return "Understanding dog training terminology helps you follow training guides accurately and communicate effectively with trainers and behaviourists. Key concepts like positive reinforcement, classical conditioning, and marker training form the foundation of modern, science-based dog training. This glossary explains the most important terms in plain language."

    # ─── Toy Overstimulation Recovery ───
    if "toy overstimulation recovery" in title_lower or "calming down an overexcited" in title_lower:
        return "When a dog becomes overexcited during play, the priority is to calmly reduce stimulation and give them space to decompress. Remove the toy, avoid loud commands, and guide them to a quiet area with a familiar blanket or mat. Structured cool-down routines after play help dogs learn to self-regulate over time."

    # ─── Sensory Enrichment ───
    if "sensory enrichment" in title_lower:
        return "Dogs experience the world primarily through smell, sound, and touch, and engaging all five senses creates the most fulfilling enrichment. Scent trails, textured surfaces, calming music, and novel visual stimuli each activate different neural pathways. A multi-sensory approach to play and enrichment supports cognitive health and emotional balance."

    # ─── Confidence-Building Play ───
    if "confidence-building play" in title_lower or "shy and fearful dogs" in title_lower:
        return "Shy and fearful dogs benefit from structured, low-pressure play that allows them to succeed and build confidence gradually. Starting with solo enrichment toys at the dog's own pace, then slowly introducing gentle interactive games, helps rewire anxious responses. Patience and consistency are more effective than flooding a nervous dog with new experiences."

    # ─── Play Recovery After Surgery ───
    if "play recovery after surgery" in title_lower or "gentle enrichment for healing" in title_lower:
        return "Dogs recovering from surgery still need mental stimulation, but activities must be gentle enough to avoid disrupting the healing process. Lick mats, snuffle mats, and low-movement puzzle feeders provide engagement without physical strain. Always follow your veterinarian's specific guidance on when and how to reintroduce different types of play."

    # ─── Dog Toy Hygiene ───
    if "toy hygiene" in title_lower:
        return "Regular toy cleaning prevents the build-up of harmful bacteria, mould, and allergens that can affect your dog's health. Rubber and plastic toys can be washed in warm soapy water or run through the dishwasher, while rope toys should be microwaved damp for one minute. Establishing a weekly cleaning routine keeps toys safe and extends their usable life."

    # ─── Safe Multi-Dog Toy Management ───
    if "multi-dog toy management" in title_lower or "resource guarding" in title_lower:
        return "Managing toys in a multi-dog household requires awareness of each dog's temperament and careful supervision to prevent resource guarding. Providing enough toys for all dogs, feeding and giving high-value items separately, and teaching a reliable drop command are key strategies. Recognising early warning signs of guarding behaviour allows you to intervene before conflicts escalate."

    # ─── Rotating Puzzle Complexity ───
    if "rotating puzzle complexity" in title_lower or "progressive challenge" in title_lower:
        return "Gradually increasing puzzle difficulty keeps smart dogs engaged without causing frustration. Start with simple food-dispensing toys and progress to multi-step puzzles as your dog's problem-solving skills develop. Rotating between difficulty levels and puzzle types prevents boredom while maintaining an appropriate level of mental challenge."

    # ─── Enrichment by Breed Group ───
    if "enrichment by breed group" in title_lower:
        return "Different breed groups were developed for specific tasks, and their enrichment needs reflect those original purposes. Herding breeds thrive on problem-solving and movement games, terriers love digging and chase activities, and scent hounds need nose-work challenges. Tailoring play to your dog's breed instincts provides the most satisfying and effective enrichment."

    # ─── Dog Toy Anxiety Reduction ───
    if "toy anxiety reduction" in title_lower or "using toys to calm" in title_lower:
        return "The right toys can help anxious dogs self-soothe and manage stress through repetitive, calming activities. Lick mats, stuffed Kongs, and gentle chew toys activate the parasympathetic nervous system, reducing cortisol levels. Pairing calming toys with a safe space creates a reliable coping strategy your dog can use during stressful situations."

    # ─── Low-Mobility Enrichment ───
    if "low-mobility enrichment" in title_lower or "limited movement" in title_lower:
        return "Dogs with limited mobility due to age, injury, or disability still need regular mental stimulation to maintain quality of life. Stationary enrichment activities like snuffle mats, lick mats, and hand-fed training games provide engagement without requiring physical movement. Adapting enrichment to your dog's specific limitations ensures they stay mentally sharp and emotionally fulfilled."

    # ─── Best Dog Beds UK ───
    if "best dog beds uk" in title_lower:
        return "Choosing the right dog bed depends on your dog's size, age, sleeping style, and any health conditions. Orthopaedic beds suit senior dogs and large breeds prone to joint issues, while bolster beds provide security for dogs who like to nest. Quality materials, washable covers, and appropriate sizing are the key factors for a good night's sleep."

    # ─── Best Interactive Dog Toys UK ───
    if "best interactive dog toys" in title_lower:
        return "Interactive dog toys engage your dog's problem-solving abilities and provide mental stimulation that goes beyond simple fetch or chew toys. Puzzle feeders, treat-dispensing balls, and snuffle mats are among the most effective enrichment options available in the UK. The best choice depends on your dog's experience level, size, and motivation style."

    # ─── Best Indestructible Dog Toys UK ───
    if "best indestructible dog toys" in title_lower:
        return "No dog toy is truly indestructible, but heavy-duty options made from solid rubber, reinforced nylon, and composite materials withstand aggressive chewing far better than standard toys. Choosing the right tough toy depends on your dog's size, jaw strength, and chewing style. Regular inspection remains essential even with the most durable products."

    # ─── Best Dog Toys UK ───
    if "best dog toys uk" in title_lower:
        return "The right dog toy depends on your dog's breed, age, play style, and chewing strength. A well-rounded toy collection includes options for fetch, tug, chewing, and mental enrichment. Prioritising safety, durability, and suitability over novelty ensures your dog gets the most benefit from their toys."

    # Fallback
    return f"This guide covers the essential information you need about {title.lower().split(':')[0].replace('best ', '').strip()}. Read on for practical, evidence-based advice to help you make informed decisions for your pet's wellbeing."


def generate_comparison_table(title):
    """Generate an educational comparison table based on post topic."""
    title_lower = title.lower()

    # ─── Cognitive Enrichment for Senior Dogs ───
    if "cognitive enrichment for senior" in title_lower:
        return ("Senior Dog Enrichment by Activity Type", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Activity Type</th><th>Physical Demand</th><th>Mental Stimulation</th><th>Best For</th></tr></thead><tbody>
<tr><td>Snuffle mats</td><td>Very low</td><td>Moderate</td><td>Dogs with limited mobility</td></tr>
<tr><td>Lick mats with paste</td><td>Minimal</td><td>Moderate</td><td>Calming anxious seniors</td></tr>
<tr><td>Simple puzzle feeders</td><td>Low</td><td>High</td><td>Maintaining cognitive function</td></tr>
<tr><td>Gentle scent trails</td><td>Low to moderate</td><td>Very high</td><td>Active seniors with good mobility</td></tr>
<tr><td>Hand-fed training games</td><td>Very low</td><td>High</td><td>Bonding and brain exercise</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Enrichment Schedules for Dogs ───
    if "enrichment schedules" in title_lower:
        return ("Daily Enrichment Schedule Overview", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Time of Day</th><th>Activity Type</th><th>Duration</th><th>Enrichment Benefit</th></tr></thead><tbody>
<tr><td>Morning</td><td>Food puzzle breakfast</td><td>10–15 minutes</td><td>Mental stimulation to start the day</td></tr>
<tr><td>Mid-morning</td><td>Scent walk or garden sniffing</td><td>15–20 minutes</td><td>Sensory engagement and exercise</td></tr>
<tr><td>Afternoon</td><td>Training session or trick practice</td><td>5–10 minutes</td><td>Cognitive challenge and bonding</td></tr>
<tr><td>Early evening</td><td>Interactive play (tug, fetch)</td><td>10–15 minutes</td><td>Physical exercise and social play</td></tr>
<tr><td>Evening</td><td>Chew toy or lick mat</td><td>15–20 minutes</td><td>Calming activity before rest</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Dog Toy Storage and Organisation ───
    if "toy storage" in title_lower:
        return ("Toy Storage Methods Compared", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Storage Method</th><th>Hygiene</th><th>Accessibility</th><th>Best For</th></tr></thead><tbody>
<tr><td>Open basket or bin</td><td>Moderate – needs regular cleaning</td><td>High – dogs can self-select</td><td>Everyday toys for confident dogs</td></tr>
<tr><td>Sealed plastic container</td><td>High – keeps dust and pests out</td><td>Low – owner-controlled</td><td>Rotation toys and seasonal storage</td></tr>
<tr><td>Mesh laundry bag</td><td>Good – allows airflow</td><td>Moderate</td><td>Drying toys after washing</td></tr>
<tr><td>Wall-mounted hooks</td><td>Good – keeps toys off floor</td><td>High for owners</td><td>Tug ropes and larger toys</td></tr>
<tr><td>Drawer or cupboard</td><td>High</td><td>Low – owner-controlled</td><td>High-value or interactive toys</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Crate and Play Enrichment ───
    if "crate" in title_lower and "enrichment" in title_lower:
        return ("Crate Enrichment Options by Safety Level", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Enrichment Type</th><th>Supervised Only</th><th>Safe Unsupervised</th><th>Best For</th></tr></thead><tbody>
<tr><td>Stuffed Kong (frozen)</td><td>No</td><td>Yes</td><td>Long crate sessions</td></tr>
<tr><td>Lick mat with spread</td><td>No</td><td>Yes (suction-mounted)</td><td>Calming anxious dogs</td></tr>
<tr><td>Snuffle mat</td><td>Yes</td><td>No – chewing risk</td><td>Short enrichment periods</td></tr>
<tr><td>Rope toy</td><td>Yes</td><td>No – ingestion risk</td><td>Gentle chewers only</td></tr>
<tr><td>Solid rubber chew</td><td>No</td><td>Yes (size-appropriate)</td><td>Moderate to strong chewers</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Safe Tug Play ───
    if "tug play" in title_lower:
        return ("Tug Toy Materials Compared", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Material</th><th>Durability</th><th>Dental Safety</th><th>Best For</th></tr></thead><tbody>
<tr><td>Braided fleece</td><td>Moderate</td><td>Gentle on teeth</td><td>Puppies and small dogs</td></tr>
<tr><td>Natural cotton rope</td><td>Moderate to high</td><td>May aid plaque removal</td><td>Medium dogs with moderate bite</td></tr>
<tr><td>Rubber tug with handles</td><td>High</td><td>Tooth-safe if solid</td><td>Strong pullers and large breeds</td></tr>
<tr><td>Firehose fabric</td><td>Very high</td><td>Gentle on gums</td><td>Heavy tuggers and working dogs</td></tr>
<tr><td>Leather tug</td><td>High</td><td>Soft on teeth</td><td>Competition and sport training</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Scent-Game Enrichment ───
    if "scent-game" in title_lower or "scent game" in title_lower:
        return ("Scent Game Types by Difficulty", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Scent Game</th><th>Difficulty</th><th>Space Needed</th><th>Best For</th></tr></thead><tbody>
<tr><td>Scatter feeding on grass</td><td>Beginner</td><td>Small garden or room</td><td>All dogs, first-time sniffers</td></tr>
<tr><td>Muffin tin puzzle</td><td>Beginner to intermediate</td><td>Indoor tabletop or floor</td><td>Food-motivated dogs</td></tr>
<tr><td>Box search (multiple boxes)</td><td>Intermediate</td><td>One room</td><td>Building search confidence</td></tr>
<tr><td>Trail following (outdoor)</td><td>Intermediate to advanced</td><td>Garden or park</td><td>Active dogs and scent hounds</td></tr>
<tr><td>Multi-room hide and seek</td><td>Advanced</td><td>Full house</td><td>Experienced sniffers</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Signs of Toy Overstimulation ───
    if "overstimulation" in title_lower and "signs" in title_lower:
        return ("Overstimulation Warning Signs by Severity", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Severity</th><th>Behavioural Signs</th><th>Physical Signs</th><th>Recommended Response</th></tr></thead><tbody>
<tr><td>Mild</td><td>Increased speed, louder vocalisation</td><td>Slightly elevated breathing</td><td>Slow the game, lower energy</td></tr>
<tr><td>Moderate</td><td>Ignoring commands, frantic movements</td><td>Heavy panting, dilated pupils</td><td>Remove toy, redirect to calm activity</td></tr>
<tr><td>High</td><td>Snapping, guarding, inability to settle</td><td>Trembling, whale eye, tense body</td><td>End play immediately, provide quiet space</td></tr>
<tr><td>Post-play</td><td>Restlessness, destructive behaviour</td><td>Continued heavy breathing at rest</td><td>Calm environment, lick mat or chew</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Best Indestructible Dog Toys ───
    if "indestructible" in title_lower:
        return ("Tough Toy Materials Compared", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Material</th><th>Durability</th><th>Safety Profile</th><th>Best For</th></tr></thead><tbody>
<tr><td>Solid natural rubber</td><td>High</td><td>Non-toxic, flexible</td><td>Strong chewers, all sizes</td></tr>
<tr><td>Reinforced nylon</td><td>Very high</td><td>Hard surface, monitor for wear</td><td>Extreme chewers</td></tr>
<tr><td>Composite rubber-nylon</td><td>Very high</td><td>Good if no small parts</td><td>Large breed power chewers</td></tr>
<tr><td>Hard polyethylene (HDPE)</td><td>High</td><td>Food-safe grades available</td><td>Treat-dispensing toys</td></tr>
<tr><td>Compressed rawhide alternatives</td><td>Moderate</td><td>Digestible, less choking risk</td><td>Moderate chewers who ingest pieces</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Dog Toys FAQ ───
    if "dog toys faq" in title_lower:
        return ("Common Dog Toy Concerns at a Glance", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Concern</th><th>Risk Level</th><th>Prevention</th><th>When to Act</th></tr></thead><tbody>
<tr><td>Choking on small parts</td><td>High</td><td>Size-appropriate toys, supervision</td><td>Immediately if gagging or pawing at mouth</td></tr>
<tr><td>Intestinal blockage</td><td>High</td><td>Remove damaged toys promptly</td><td>Vomiting, lethargy, refusal to eat</td></tr>
<tr><td>Tooth damage</td><td>Moderate</td><td>Avoid hard nylon and antlers for puppies</td><td>Bleeding gums, broken teeth</td></tr>
<tr><td>Bacterial build-up</td><td>Low to moderate</td><td>Weekly cleaning routine</td><td>Visible mould or strong odour</td></tr>
<tr><td>Allergic reaction</td><td>Low</td><td>Choose natural, dye-free materials</td><td>Skin irritation, excessive scratching</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Aggressive Chewer Guide ───
    if "aggressive chewer" in title_lower:
        return ("Toy Suitability by Chewing Intensity", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Chewing Level</th><th>Suitable Materials</th><th>Avoid</th><th>Example Toys</th></tr></thead><tbody>
<tr><td>Light chewer</td><td>Plush, soft rubber, rope</td><td>Nothing specific</td><td>Stuffed toys, fleece braids</td></tr>
<tr><td>Moderate chewer</td><td>Natural rubber, thick rope</td><td>Thin plush toys</td><td>Standard Kongs, braided rope</td></tr>
<tr><td>Strong chewer</td><td>Solid rubber, reinforced nylon</td><td>Plush, thin rope, tennis balls</td><td>Extreme Kongs, solid nylon bones</td></tr>
<tr><td>Extreme chewer</td><td>Heavy-duty rubber, composite</td><td>Most standard toys</td><td>Black Kong, Goughnuts rings</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Dog Toy Enrichment Beyond Fetch ───
    if "enrichment" in title_lower and "beyond" in title_lower:
        return ("Enrichment Activities Beyond Fetch", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Activity</th><th>Enrichment Type</th><th>Equipment Needed</th><th>Best For</th></tr></thead><tbody>
<tr><td>Food puzzle toys</td><td>Cognitive</td><td>Puzzle feeder or Kong</td><td>Food-motivated dogs</td></tr>
<tr><td>Snuffle mat foraging</td><td>Sensory (scent)</td><td>Snuffle mat</td><td>All dogs, especially anxious ones</td></tr>
<tr><td>Tug-of-war sessions</td><td>Social and physical</td><td>Tug rope or toy</td><td>Dogs who enjoy interactive play</td></tr>
<tr><td>Hide and seek (toys)</td><td>Cognitive and scent</td><td>Favourite toys</td><td>Curious, scent-driven dogs</td></tr>
<tr><td>Trick training with toys</td><td>Cognitive and social</td><td>Any toy as reward</td><td>Eager learners and working breeds</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Puppy-Safe Dog Toys ───
    if "puppy-safe" in title_lower or ("puppy" in title_lower and "safe" in title_lower and "toy" in title_lower):
        return ("Puppy Toy Safety by Age Stage", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Age Stage</th><th>Safe Toy Types</th><th>Avoid</th><th>Key Consideration</th></tr></thead><tbody>
<tr><td>8–12 weeks</td><td>Soft rubber, small plush (no parts)</td><td>Hard chews, rawhide, small balls</td><td>Delicate baby teeth</td></tr>
<tr><td>12–16 weeks</td><td>Puppy Kongs, teething rings</td><td>Heavy rope, antlers</td><td>Teething pain relief</td></tr>
<tr><td>4–6 months</td><td>Frozen Kongs, medium rubber toys</td><td>Toys sized for adult dogs</td><td>Adult teeth emerging</td></tr>
<tr><td>6–12 months</td><td>Size-appropriate adult toys</td><td>Toys from puppyhood (now too small)</td><td>Jaw strength increasing</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Dog Play Styles ───
    if "play styles" in title_lower:
        return ("Dog Play Styles and Matching Toys", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Play Style</th><th>Behaviour Signs</th><th>Ideal Toy Types</th><th>Common Breeds</th></tr></thead><tbody>
<tr><td>Chaser</td><td>Loves running after moving objects</td><td>Balls, frisbees, flirt poles</td><td>Collies, Spaniels, Whippets</td></tr>
<tr><td>Tugger</td><td>Grabs and pulls, shakes toys</td><td>Tug ropes, rubber rings</td><td>Staffies, Terriers, Rottweilers</td></tr>
<tr><td>Wrestler</td><td>Body slams, play bows, mouth play</td><td>Sturdy plush toys, large rubber toys</td><td>Boxers, Labradors, Bulldogs</td></tr>
<tr><td>Solitary chewer</td><td>Settles with a toy, gnaws quietly</td><td>Chew bones, stuffed Kongs</td><td>Mastiffs, Basset Hounds</td></tr>
<tr><td>Problem solver</td><td>Manipulates objects, persistent</td><td>Puzzle feeders, treat balls</td><td>Poodles, Border Collies, GSDs</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Indoor Cat Care ───
    if "indoor cat care" in title_lower:
        return ("Indoor vs Outdoor Cat Environmental Needs", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Need</th><th>Outdoor Cats</th><th>Indoor Cats</th><th>Indoor Solutions</th></tr></thead><tbody>
<tr><td>Exercise</td><td>Natural roaming and hunting</td><td>Owner-provided play sessions</td><td>Wand toys, cat wheels, climbing trees</td></tr>
<tr><td>Mental stimulation</td><td>Varied environment daily</td><td>Risk of boredom without enrichment</td><td>Puzzle feeders, rotating toys</td></tr>
<tr><td>Territory marking</td><td>Trees, fences, posts</td><td>Limited surfaces available</td><td>Scratching posts and pads</td></tr>
<tr><td>Social interaction</td><td>Encounters with other animals</td><td>Dependent on household members</td><td>Interactive play, window perches</td></tr>
<tr><td>Sunlight and fresh air</td><td>Freely available</td><td>Limited by window access</td><td>Window perches, catios, safe balconies</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Best Indoor Cat Toys ───
    if "indoor cat toys" in title_lower:
        return ("Indoor Cat Toy Types Compared", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Toy Type</th><th>Engagement Level</th><th>Independent Play</th><th>Best For</th></tr></thead><tbody>
<tr><td>Wand and feather toys</td><td>Very high</td><td>No – requires owner</td><td>Active cats, bonding time</td></tr>
<tr><td>Puzzle feeders</td><td>High</td><td>Yes</td><td>Food-motivated cats, slow feeding</td></tr>
<tr><td>Spring toys and balls</td><td>Moderate to high</td><td>Yes</td><td>Playful cats, solo entertainment</td></tr>
<tr><td>Catnip toys</td><td>High (for sensitive cats)</td><td>Yes</td><td>Cats responsive to catnip</td></tr>
<tr><td>Electronic motion toys</td><td>High initially, may wane</td><td>Yes</td><td>Supplementing owner play</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Cat Toy Rotation ───
    if "cat toy rotation" in title_lower:
        return ("Cat Toy Rotation Schedule", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Rotation Group</th><th>Toy Examples</th><th>Duration Available</th><th>Storage Between Rotations</th></tr></thead><tbody>
<tr><td>Group A (active)</td><td>Feather wand, spring toy, ball</td><td>3–4 days</td><td>Sealed bag to preserve novelty</td></tr>
<tr><td>Group B (puzzle)</td><td>Treat ball, puzzle feeder, tunnel</td><td>3–4 days</td><td>Clean and store dry</td></tr>
<tr><td>Group C (scent)</td><td>Catnip mouse, silvervine stick</td><td>2–3 days</td><td>Airtight container for scent</td></tr>
<tr><td>Permanent toys</td><td>Scratching post, cat tree</td><td>Always available</td><td>N/A – fixed environmental items</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Choose Right Cat Toy ───
    if "choose the right cat toy" in title_lower or "cat's personality" in title_lower:
        return ("Cat Play Personality and Toy Matching", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Play Personality</th><th>Behaviour Signs</th><th>Ideal Toys</th><th>Play Tips</th></tr></thead><tbody>
<tr><td>Stalker</td><td>Crouches, wiggles before pouncing</td><td>Wand toys, laser pointers (with treat)</td><td>Slow, ground-level movements</td></tr>
<tr><td>Pouncer</td><td>Leaps on toys from above</td><td>Mice toys, crinkle balls</td><td>Toss toys for aerial catches</td></tr>
<tr><td>Batter</td><td>Swats at objects with paws</td><td>Spring toys, track balls</td><td>Toys that roll unpredictably</td></tr>
<tr><td>Wrestler</td><td>Grabs and bunny-kicks toys</td><td>Kicker toys, large stuffed mice</td><td>Toys sized for body wrapping</td></tr>
<tr><td>Observer</td><td>Watches more than plays</td><td>Window bird feeders, fish videos</td><td>Low-pressure, visual stimulation</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Cat Toys FAQ ───
    if "cat toys faq" in title_lower:
        return ("Cat Toy Safety and Replacement Guide", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Toy Type</th><th>Typical Lifespan</th><th>Replace When</th><th>Safety Check</th></tr></thead><tbody>
<tr><td>Feather wand attachments</td><td>2–4 weeks</td><td>Feathers detaching or fraying</td><td>Loose parts, exposed wire</td></tr>
<tr><td>Plush mice</td><td>1–3 months</td><td>Seams opening, filling visible</td><td>Eyes or nose pieces loose</td></tr>
<tr><td>Crinkle balls</td><td>2–4 months</td><td>Outer fabric tearing</td><td>Internal material exposed</td></tr>
<tr><td>Puzzle feeders</td><td>6–12 months</td><td>Cracks or sharp edges forming</td><td>Mould in crevices</td></tr>
<tr><td>Catnip toys</td><td>1–2 months (scent fades)</td><td>No longer attracting interest</td><td>Fabric integrity, loose stitching</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Puppy Socialisation ───
    if "puppy socialisation" in title_lower:
        return ("Puppy Socialisation Timeline", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Age Period</th><th>Focus Areas</th><th>Safe Activities</th><th>Key Considerations</th></tr></thead><tbody>
<tr><td>3–5 weeks</td><td>Litter socialisation</td><td>Gentle handling, varied surfaces</td><td>With breeder, minimal stress</td></tr>
<tr><td>5–8 weeks</td><td>Human interaction, novel sounds</td><td>Meeting calm adults, household noises</td><td>Still with litter ideally</td></tr>
<tr><td>8–12 weeks</td><td>New home, basic experiences</td><td>Puppy classes, car rides, vet visits</td><td>Before full vaccination: carry, don't walk in public</td></tr>
<tr><td>12–16 weeks</td><td>Wider world exposure</td><td>Walks in safe areas, meeting other dogs</td><td>Vaccination schedule permitting</td></tr>
<tr><td>4–6 months</td><td>Continued positive exposure</td><td>Group classes, varied environments</td><td>Adolescent fear period may occur</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Dog Training Treats ───
    if "training treats" in title_lower:
        return ("Training Treat Types Compared", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Treat Type</th><th>Calorie Level</th><th>Delivery Speed</th><th>Best For</th></tr></thead><tbody>
<tr><td>Soft commercial treats</td><td>Low to moderate</td><td>Fast – easy to break</td><td>Repetitive training sessions</td></tr>
<tr><td>Freeze-dried meat</td><td>Moderate</td><td>Fast</td><td>High-value rewards, recall training</td></tr>
<tr><td>Cheese or hot dog pieces</td><td>Higher</td><td>Fast</td><td>Emergency recall, challenging tasks</td></tr>
<tr><td>Kibble (regular food)</td><td>Low</td><td>Fast</td><td>Food-motivated dogs, basic training</td></tr>
<tr><td>Dental chews</td><td>Higher</td><td>Slow</td><td>End-of-session jackpot rewards</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── DIY Dog Toys ───
    if "diy dog toys" in title_lower:
        return ("DIY Dog Toy Safety by Material", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>DIY Material</th><th>Safety Level</th><th>Supervision Needed</th><th>Suitable Activities</th></tr></thead><tbody>
<tr><td>Old t-shirts (braided)</td><td>Moderate</td><td>Yes – ingestion risk</td><td>Light tug play</td></tr>
<tr><td>Tennis ball in sock</td><td>Moderate</td><td>Yes – sock ingestion risk</td><td>Fetch and tug</td></tr>
<tr><td>Muffin tin + tennis balls</td><td>High</td><td>Minimal</td><td>Food puzzle</td></tr>
<tr><td>Cardboard boxes</td><td>High</td><td>Minimal</td><td>Scent games, destruction play</td></tr>
<tr><td>Plastic bottles (cap removed)</td><td>Moderate</td><td>Yes – sharp edges if crushed</td><td>Noisy enrichment</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Types of Dog Toys for Different Play Styles ───
    if "types of dog toys" in title_lower or ("different play styles" in title_lower and "dog" in title_lower):
        return ("Dog Toy Types by Play Category", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Toy Category</th><th>Primary Purpose</th><th>Durability Needed</th><th>Best For</th></tr></thead><tbody>
<tr><td>Fetch toys (balls, frisbees)</td><td>Physical exercise, chase instinct</td><td>Moderate to high</td><td>Active, chase-driven dogs</td></tr>
<tr><td>Tug toys (ropes, rings)</td><td>Interactive play, bonding</td><td>High</td><td>Dogs who enjoy pulling</td></tr>
<tr><td>Chew toys (bones, rubber)</td><td>Dental health, calming</td><td>Very high</td><td>Strong chewers, anxious dogs</td></tr>
<tr><td>Puzzle toys (feeders, mazes)</td><td>Mental stimulation</td><td>Moderate</td><td>Intelligent, food-motivated dogs</td></tr>
<tr><td>Comfort toys (soft plush)</td><td>Emotional security</td><td>Low</td><td>Gentle dogs, puppies, seniors</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Mental Stimulation for Dogs ───
    if "mental stimulation" in title_lower:
        return ("Mental Stimulation Activities Compared", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Activity</th><th>Mental Effort</th><th>Physical Effort</th><th>Best For</th></tr></thead><tbody>
<tr><td>Puzzle feeders</td><td>High</td><td>Low</td><td>Mealtimes, alone time</td></tr>
<tr><td>Scent work / nose games</td><td>Very high</td><td>Low to moderate</td><td>All dogs, especially scent breeds</td></tr>
<tr><td>Trick training</td><td>High</td><td>Low to moderate</td><td>Eager learners, bonding</td></tr>
<tr><td>Interactive toys with owner</td><td>Moderate</td><td>Moderate</td><td>Social dogs, relationship building</td></tr>
<tr><td>Novel environment walks</td><td>High</td><td>Moderate</td><td>Curious dogs, under-stimulated dogs</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Dog Toy Safety ───
    if "dog toy safety" in title_lower:
        return ("Toy Safety Checklist by Material", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Material</th><th>Common Hazards</th><th>Safety Check</th><th>When to Discard</th></tr></thead><tbody>
<tr><td>Rubber</td><td>Tearing into chunks</td><td>Squeeze test – should bounce back</td><td>Deep bite marks, missing pieces</td></tr>
<tr><td>Rope</td><td>Fibre ingestion, blockage risk</td><td>Check for loose threads</td><td>Fraying, threads pulling free</td></tr>
<tr><td>Plush</td><td>Squeaker ingestion, stuffing</td><td>Seam integrity, squeaker secure</td><td>Seams opening, stuffing visible</td></tr>
<tr><td>Tennis balls</td><td>Abrasive felt wears teeth, choking</td><td>Size appropriate, felt intact</td><td>Felt worn through, compressed flat</td></tr>
<tr><td>Nylon / hard plastic</td><td>Tooth fractures, sharp edges</td><td>No cracks or sharp chips</td><td>Visible cracks, splintering edges</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Where to Place Dog Bed ───
    if "where to place" in title_lower and "bed" in title_lower:
        return ("Dog Bed Placement Considerations", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Location</th><th>Advantages</th><th>Disadvantages</th><th>Best For</th></tr></thead><tbody>
<tr><td>Living room corner</td><td>Near family, feels included</td><td>May be noisy during evenings</td><td>Social dogs who like company</td></tr>
<tr><td>Owner's bedroom</td><td>Reduces separation anxiety</td><td>May disrupt owner sleep</td><td>Anxious dogs, new puppies</td></tr>
<tr><td>Hallway or landing</td><td>Central, can monitor household</td><td>Draughty, high foot traffic</td><td>Guardian breeds</td></tr>
<tr><td>Dedicated dog room</td><td>Quiet, fully their space</td><td>May feel isolated</td><td>Confident, independent dogs</td></tr>
<tr><td>Kitchen</td><td>Easy-clean flooring, warm</td><td>Cooking hazards, hot appliances</td><td>Dogs who stay underfoot</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── How to Wash Dog Bed ───
    if "wash" in title_lower and "dog" in title_lower and "bed" in title_lower:
        return ("Dog Bed Cleaning Methods by Material", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Bed Type</th><th>Cleaning Method</th><th>Frequency</th><th>Special Care</th></tr></thead><tbody>
<tr><td>Removable cover (fabric)</td><td>Machine wash 30–40°C</td><td>Every 1–2 weeks</td><td>Pet-safe detergent, no fabric softener</td></tr>
<tr><td>Memory foam insert</td><td>Spot clean, air dry</td><td>Monthly or as needed</td><td>Never machine wash – damages foam</td></tr>
<tr><td>Waterproof liner</td><td>Wipe with damp cloth</td><td>Weekly</td><td>Check for cracks in coating</td></tr>
<tr><td>Bolster / pillow bed</td><td>Machine wash if size permits</td><td>Every 2 weeks</td><td>Reshape while damp</td></tr>
<tr><td>Elevated / cot bed</td><td>Hose down frame, wash fabric</td><td>Monthly</td><td>Check joints for rust</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Choose Right Dog Bed Size ───
    if "choose" in title_lower and "dog bed size" in title_lower:
        return ("Dog Bed Sizing Guide by Sleep Position", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Sleep Position</th><th>Space Needed</th><th>Recommended Bed Shape</th><th>Sizing Rule</th></tr></thead><tbody>
<tr><td>Side sleeper (stretched)</td><td>Maximum</td><td>Flat mat or large rectangular</td><td>Nose to tail + 20cm each side</td></tr>
<tr><td>Curled up (doughnut)</td><td>Moderate</td><td>Round or oval nest bed</td><td>Dog length × 0.75 for diameter</td></tr>
<tr><td>Back sleeper (legs up)</td><td>Wide</td><td>Flat bed with low sides</td><td>Shoulder width + 15cm each side</td></tr>
<tr><td>Head rester (chin on edge)</td><td>Moderate</td><td>Bolster bed with raised rim</td><td>Standard size + bolster height</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Pet Hydration ───
    if "pet hydration" in title_lower:
        return ("Daily Water Needs by Pet Type and Size", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Pet Type</th><th>Daily Water Guideline</th><th>Factors That Increase Need</th><th>Dehydration Signs</th></tr></thead><tbody>
<tr><td>Small dog (under 10kg)</td><td>300–600ml</td><td>Hot weather, dry food diet</td><td>Dry nose, tacky gums</td></tr>
<tr><td>Medium dog (10–25kg)</td><td>600–1500ml</td><td>Exercise, illness, lactation</td><td>Skin tenting, lethargy</td></tr>
<tr><td>Large dog (25kg+)</td><td>1500–3000ml+</td><td>Working activity, medications</td><td>Sunken eyes, rapid breathing</td></tr>
<tr><td>Cat (average 4–5kg)</td><td>200–300ml</td><td>Dry food only, kidney issues</td><td>Reduced urination, dry gums</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Pet First Aid ───
    if "pet first aid" in title_lower:
        return ("Pet First Aid Kit Essentials", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Item</th><th>Purpose</th><th>When to Use</th><th>Notes</th></tr></thead><tbody>
<tr><td>Sterile gauze pads</td><td>Wound covering</td><td>Cuts, abrasions, bleeding</td><td>Non-adhesive type preferred</td></tr>
<tr><td>Self-adhesive bandage</td><td>Securing dressings</td><td>Limb injuries, pressure wounds</td><td>Do not wrap too tightly</td></tr>
<tr><td>Saline solution</td><td>Wound flushing, eye rinsing</td><td>Debris in wounds or eyes</td><td>Sterile, single-use sachets ideal</td></tr>
<tr><td>Blunt-ended scissors</td><td>Cutting bandage, removing fur</td><td>Wound access, dressing changes</td><td>Keep clean and sharp</td></tr>
<tr><td>Digital thermometer</td><td>Checking temperature</td><td>Suspected fever or hypothermia</td><td>Normal dog: 38.3–39.2°C</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Dog Dental Health ───
    if "dog dental" in title_lower:
        return ("Dog Dental Care Methods Compared", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Method</th><th>Effectiveness</th><th>Frequency</th><th>Best For</th></tr></thead><tbody>
<tr><td>Tooth brushing</td><td>Very high</td><td>Daily</td><td>All dogs (gold standard)</td></tr>
<tr><td>Dental chews (VOHC approved)</td><td>Moderate</td><td>Daily</td><td>Dogs who resist brushing</td></tr>
<tr><td>Water additives</td><td>Low to moderate</td><td>Daily</td><td>Supplementary care</td></tr>
<tr><td>Dental diets</td><td>Moderate</td><td>Every meal</td><td>Dogs prone to plaque build-up</td></tr>
<tr><td>Professional veterinary clean</td><td>Very high</td><td>Annually or as advised</td><td>Removing established tartar</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # ─── Dog Training Terminology ───
    if "training terminology" in title_lower:
        return ("Key Dog Training Methods Compared", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Method</th><th>Approach</th><th>Tools Used</th><th>Suitability</th></tr></thead><tbody>
<tr><td>Positive reinforcement</td><td>Reward desired behaviour</td><td>Treats, toys, praise</td><td>All dogs – widely recommended</td></tr>
<tr><td>Clicker / marker training</td><td>Precise timing of reward signal</td><td>Clicker or verbal marker</td><td>Precision behaviours, tricks</td></tr>
<tr><td>Lure-reward training</td><td>Guide with food, then reward</td><td>Treats as lure</td><td>Beginners, basic commands</td></tr>
<tr><td>Shaping</td><td>Reward successive approximations</td><td>Clicker, treats</td><td>Complex behaviours, creative dogs</td></tr>
<tr><td>Capturing</td><td>Reward naturally offered behaviour</td><td>Marker, treats</td><td>Calm behaviours, settling</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")

    # Fallback generic table - use "Option A" marker so we can skip it
    return ("Comparison Overview", """<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table class="has-fixed-layout"><thead><tr><th>Option</th><th>Key Features</th><th>Considerations</th><th>Best For</th></tr></thead><tbody>
<tr><td>Option A</td><td>Feature details</td><td>Consideration details</td><td>Use case</td></tr>
<tr><td>Option B</td><td>Feature details</td><td>Consideration details</td><td>Use case</td></tr>
</tbody></table></figure>
<!-- /wp:table -->""")


def find_insertion_point_after_first_heading(content):
    """Find the position right after the first H1/H2/H3 heading and its following paragraph."""
    # Look for first heading block pattern
    # Try wp:heading block first
    m = re.search(r'(<!-- wp:heading[^>]*-->.*?<!-- /wp:heading -->)', content, re.DOTALL)
    if m:
        # Check if there's a paragraph right after
        after = content[m.end():]
        mp = re.match(r'\s*(<!-- wp:paragraph -->.*?<!-- /wp:paragraph -->)', after, re.DOTALL)
        if mp:
            return m.end() + mp.end()
        return m.end()

    # Try raw heading tags
    m = re.search(r'(<h[1-3][^>]*>.*?</h[1-3]>)', content, re.DOTALL)
    if m:
        after = content[m.end():]
        mp = re.match(r'\s*(<p[^>]*>.*?</p>)', after, re.DOTALL)
        if mp:
            return m.end() + mp.end()
        return m.end()

    # If no heading found, insert after first paragraph
    m = re.search(r'(<p[^>]*>.*?</p>)', content, re.DOTALL)
    if m:
        return m.end()

    # Fallback: insert at very beginning
    return 0


def find_insertion_point_for_sources(content):
    """Find position to insert sources - before the editorial standards section or at end."""
    markers = [
        "About Our Editorial Standards",
        "editorial methodology",
    ]
    for marker in markers:
        idx = content.find(marker)
        if idx > 0:
            # Go back to find the start of the block
            search_area = content[:idx]
            # Look for the last separator before this
            sep_idx = search_area.rfind("<!-- wp:separator")
            if sep_idx > 0:
                return sep_idx
            heading_idx = search_area.rfind("<!-- wp:heading")
            if heading_idx > 0:
                return heading_idx
            # Try raw heading
            heading_idx = search_area.rfind("<h3")
            if heading_idx > 0:
                return heading_idx
            return idx

    return len(content)


def find_insertion_point_for_table(content):
    """Find a good mid-content position to insert a comparison table."""
    h2_positions = []
    for m in re.finditer(r'<!-- wp:heading\s*(?:\{[^}]*\})?\s*-->\s*<h2', content):
        h2_positions.append(m.start())
    for m in re.finditer(r'<h2\s', content):
        if m.start() not in h2_positions:
            h2_positions.append(m.start())

    h2_positions = sorted(set(h2_positions))

    if len(h2_positions) >= 3:
        return h2_positions[2]
    elif len(h2_positions) >= 2:
        return h2_positions[1]
    elif len(h2_positions) >= 1:
        return h2_positions[0]

    return int(len(content) * 0.4)


def generate_sources_for_topic(title):
    """Generate relevant UK authority source links based on post topic."""
    title_lower = title.lower()
    sources = []

    if 'dog' in title_lower or 'puppy' in title_lower:
        sources.append(("https://www.rspca.org.uk/adviceandwelfare/pets/dogs", "RSPCA – Dog Care Advice"))
        sources.append(("https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs", "PDSA – Dog Health and Care"))
        sources.append(("https://www.bluecross.org.uk/pet-advice/dog", "Blue Cross – Dog Advice"))
        if 'toy' in title_lower or 'play' in title_lower or 'enrichment' in title_lower:
            sources.append(("https://www.rspca.org.uk/adviceandwelfare/pets/dogs/play", "RSPCA – Dog Play and Enrichment"))
            sources.append(("https://www.dogstrust.org.uk/dog-advice/life-with-your-dog/at-home/dog-enrichment", "Dogs Trust – Dog Enrichment Ideas"))
        else:
            sources.append(("https://www.dogstrust.org.uk/dog-advice", "Dogs Trust – Dog Advice Hub"))
            sources.append(("https://www.thekennelclub.org.uk/health/", "The Kennel Club – Dog Health"))
    elif 'cat' in title_lower:
        sources.append(("https://www.rspca.org.uk/adviceandwelfare/pets/cats", "RSPCA – Cat Care Advice"))
        sources.append(("https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/kittens-cats", "PDSA – Cat Health and Care"))
        sources.append(("https://www.bluecross.org.uk/pet-advice/cat", "Blue Cross – Cat Advice"))
        sources.append(("https://www.battersea.org.uk/pet-advice/cat-advice", "Battersea – Cat Advice Hub"))
    else:
        sources.append(("https://www.rspca.org.uk/adviceandwelfare/pets", "RSPCA – Pet Care Advice"))
        sources.append(("https://www.pdsa.org.uk/pet-help-and-advice", "PDSA – Pet Health Advice"))
        sources.append(("https://www.bluecross.org.uk/pet-advice", "Blue Cross – Pet Advice"))
        sources.append(("https://www.pfma.org.uk/pet-care", "PFMA – Pet Care Guidelines"))

    seen = set()
    unique = []
    for s in sources:
        if s[0] not in seen:
            seen.add(s[0])
            unique.append(s)
    return unique[:5]


def process_post(post_id, needs_qa, needs_sources, needs_table):
    """Process a single post, adding missing blocks."""
    result = {
        'id': post_id,
        'title': '',
        'quick_answer_added': False,
        'sources_added': False,
        'source_count': 0,
        'comparison_added': False,
        'comparison_topic': '',
        'status': 'pending',
    }

    try:
        data = api_get(f"posts/{post_id}?context=edit&_fields=id,title,content")
        if 'id' not in data:
            result['status'] = f"error_fetch: {str(data)[:100]}"
            return result

        title = data['title']['raw']
        content = data['content']['raw']
        result['title'] = title
        modified = False

        # ─── QUICK ANSWER ───
        if needs_qa and 'Quick Answer' not in content:
            qa_text = generate_quick_answer(title, content[:500])
            qa_block = f"""

<!-- wp:group {{"style":{{"color":{{"background":"#f0f7ff"}},"border":{{"radius":"8px","color":"#d0e2ff","width":"1px"}},"spacing":{{"padding":{{"top":"20px","bottom":"20px","left":"24px","right":"24px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#d0e2ff;border-width:1px;border-radius:8px;background-color:#f0f7ff;margin-top:24px;margin-bottom:24px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">Quick Answer</h4>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>{qa_text}</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->

"""
            insert_pos = find_insertion_point_after_first_heading(content)
            content = content[:insert_pos] + qa_block + content[insert_pos:]
            result['quick_answer_added'] = True
            modified = True
            print(f"  + Quick Answer added")

        # ─── SOURCES ───
        if needs_sources and 'Sources and Further Reading' not in content:
            sources = generate_sources_for_topic(title)
            source_items = "\n".join([f'<li><a href="{url}" target="_blank" rel="noopener nofollow">{label}</a></li>' for url, label in sources])
            sources_block = f"""

<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">Sources and Further Reading</h3>
<!-- /wp:heading -->
<!-- wp:list -->
<ul class="wp-block-list">
{source_items}
</ul>
<!-- /wp:list -->

"""
            insert_pos = find_insertion_point_for_sources(content)
            content = content[:insert_pos] + sources_block + content[insert_pos:]
            result['sources_added'] = True
            result['source_count'] = len(sources)
            modified = True
            print(f"  + Sources added ({len(sources)} links)")

        # ─── COMPARISON TABLE ───
        if needs_table and 'wp:table' not in content and '<table' not in content:
            topic, table_html = generate_comparison_table(title)
            if "Option A" not in table_html:  # Skip fallback tables
                table_block = f"""

<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">{topic}</h3>
<!-- /wp:heading -->
{table_html}

"""
                insert_pos = find_insertion_point_for_table(content)
                content = content[:insert_pos] + table_block + content[insert_pos:]
                result['comparison_added'] = True
                result['comparison_topic'] = topic
                modified = True
                print(f"  + Comparison table added: {topic}")
            else:
                result['comparison_topic'] = 'skipped_no_match'
                print(f"  - Comparison table skipped (no specific match for topic)")

        # ─── SAVE ───
        if modified:
            success = api_update_post(post_id, content)
            if success:
                result['status'] = 'updated'
                print(f"  >>> Saved post {post_id}")
            else:
                result['status'] = 'error_save'
                print(f"  !!! Failed to save post {post_id}")
        else:
            result['status'] = 'no_changes_needed'
            print(f"  - No changes needed for post {post_id}")

    except Exception as e:
        result['status'] = f"error: {str(e)[:100]}"
        print(f"  !!! Error processing post {post_id}: {e}")

    return result


def main():
    print("=" * 70)
    print("PetHub Phase 10AG: Quick Answers, Sources, Comparison Tables")
    print("=" * 70)

    qa_set = set(QUICK_ANSWER_POST_IDS)
    sources_set = set(SOURCES_POST_IDS)
    table_set = set(COMPARISON_TABLE_POST_IDS)

    results = []
    batch_count = 0

    for i, post_id in enumerate(ALL_POST_IDS):
        needs_qa = post_id in qa_set
        needs_sources = post_id in sources_set
        needs_table = post_id in table_set

        print(f"\n[{i+1}/{len(ALL_POST_IDS)}] Processing post {post_id} "
              f"(QA:{needs_qa} SRC:{needs_sources} TBL:{needs_table})")

        result = process_post(post_id, needs_qa, needs_sources, needs_table)
        results.append(result)

        batch_count += 1
        if batch_count % 10 == 0:
            print(f"\n--- Batch pause (processed {batch_count}) ---")

        time.sleep(DELAY)

    # Write CSV log
    print(f"\n{'=' * 70}")
    print(f"Writing log to {LOG_PATH}")
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'id', 'title', 'quick_answer_added', 'sources_added',
            'source_count', 'comparison_added', 'comparison_topic', 'status'
        ])
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    # Summary
    qa_added = sum(1 for r in results if r['quick_answer_added'])
    src_added = sum(1 for r in results if r['sources_added'])
    tbl_added = sum(1 for r in results if r['comparison_added'])
    errors = sum(1 for r in results if 'error' in r['status'])

    print(f"\n{'=' * 70}")
    print(f"SUMMARY:")
    print(f"  Total posts processed: {len(results)}")
    print(f"  Quick Answers added:   {qa_added}")
    print(f"  Sources added:         {src_added}")
    print(f"  Comparison tables:     {tbl_added}")
    print(f"  Errors:                {errors}")
    print(f"  Log file:              {LOG_PATH}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
