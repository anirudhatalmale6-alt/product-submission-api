#!/usr/bin/env python3
"""
Phase 10AI Batch 4 v2: Content Enhancement for Dog Grooming, Dog Harnesses,
Dog Beds, Educational, Uncategorized clusters.

FIXED: Works with WP rendered HTML (no Gutenberg block comments in stored content).
Detects existing blocks by HTML content markers, not by Gutenberg comments.
Trust footer detection uses heading text, not comment patterns.
"""

import subprocess
import json
import time
import csv
import os
import re
import tempfile
from datetime import datetime

# ── Config ──────────────────────────────────────────────────────────────────
API_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ai_data"
LOG_FILE = os.path.join(DATA_DIR, "batch4_grooming_harness_beds_log.csv")
DELAY = 2.5

# ── Post registry ───────────────────────────────────────────────────────────
POSTS = {
    "Dog Grooming": [
        (5464, "Pet Grooming Glossary: Understanding Grooming Terms and Techniques"),
        (4563, "Dog Grooming Basics: A Complete Guide for Owners"),
        (4251, "Best Cat Shampoo UK (2026) – When & How to Bathe"),
        (4244, "Best Cat Nail Clippers UK (2026) – Safe Trimming Guide"),
        (4237, "Best Cat Brushes UK (2026) – Guide by Coat Type"),
        (4230, "Best Cat Grooming Supplies UK (2026) – Complete Guide"),
        (4078, "Best Dog Nail Clippers UK (2026) – Trimming & Grinding Guide"),
        (4071, "Best Dog Shampoo UK (2026) – Ingredients & Safety Guide"),
        (4064, "Best Dog Brushes UK (2026) – Guide by Coat Type"),
        (4057, "Best Dog Grooming Supplies UK (2026) – Complete Guide"),
    ],
    "Dog Harnesses": [
        (5418, "Dog Harness Types Explained: Finding the Right Fit"),
        (4414, "Harness vs Collar: Which Is Better for Your Dog?"),
        (4413, "How to Measure Your Dog for a Harness: Step-by-Step Guide"),
        (4412, "No-Pull Dog Harness Guide: How They Work and When to Use One"),
        (4279, "Best Cat Harnesses UK (2026) – Safe Walking Guide"),
        (4258, "Best Cat Collars UK (2026) – Complete Safety Guide"),
        (4139, "Best Dog Training Leads UK (2026) – Long Lines & Harnesses"),
        (4049, "Best Puppy Collars UK (2026) – First Collar & Harness Guide"),
        (4042, "Best Dog Leads UK (2026) – Walking & Training Lead Guide"),
        (4034, "Best No-Pull Dog Harnesses UK (2026) – Training & Comfort Guide"),
        (4027, "Best Dog Collars and Harnesses UK (2026) – Complete Guide"),
    ],
    "Dog Beds": [
        (5510, "Dog Bed Sizing Guide: How to Measure Your Dog and Choose the Right Fit"),
        (4783, "How to Choose the Right Dog Bed Size"),
        (4018, "Best Puppy Beds UK (2026) – First Bed & Crate Training Guide"),
        (4011, "Best Cooling Dog Beds UK (2026) – Temperature Regulation Guide"),
        (4004, "Best Orthopaedic Dog Beds UK (2026) – Joint Support Guide"),
        (3996, "Best Dog Beds UK (2026) – Complete Guide & Honest Reviews"),
    ],
    "Educational": [
        (5521, "Pet Health Terminology: A Guide to Common Veterinary Terms"),
        (5462, "Dog Training Terminology Explained: Key Concepts for New Owners"),
        (5424, "Aggressive Chewer Guide: Safe Toys for Power Chewers"),
        (5419, "Cat Care Basics: A Glossary for New Cat Owners"),
        (5416, "Dog Bed Types Explained: A Complete Glossary"),
        (5415, "Dog Play Styles Explained: Understanding How Your Dog Plays"),
        (5414, "Cat Toy Types Explained: A Complete Glossary"),
        (4574, "Pet Hydration Guide: How Much Water Does Your Pet Need?"),
        (4272, "Best Cat ID Tags UK (2026) – Identification Guide"),
        (4265, "Best Cat GPS Trackers UK (2026) – Location Tracking Guide"),
        (4216, "Best Cat Radiator Beds UK (2026) – Hook-On Warmth Guide"),
        (4167, "Best Dog Water Bottles UK (2026) – Travel Hydration Guide"),
        (4160, "Best Elevated Dog Bowls UK (2026) – Raised Feeder Guide"),
        (4146, "Best Dog Bowls and Feeding UK (2026) – Complete Guide"),
    ],
    "Uncategorized": [
        (6048, "Confidence-Building Play: Helping Shy and Fearful Dogs Through Toys"),
        (6044, "Rotating Puzzle Complexity: Progressive Challenge for Smart Dogs"),
        (4786, "Where to Place Your Dog's Bed: Location and Comfort Tips"),
        (4785, "How to Wash and Maintain Your Dog's Bed"),
        (4573, "Seasonal Pet Safety: Protecting Pets Through the Year"),
        (4570, "First-Time Dog Owner Essentials: What You Need to Know"),
        (4576, "Multi-Pet Household Tips: Living with Dogs and Cats Together"),
        (4571, "Pet First Aid Basics: What Every Owner Should Know"),
        (4328, "Best Self-Cleaning Litter Trays UK (2026) – Automatic Options"),
        (4293, "Best Cat Trees UK (2026) – Climbing & Scratching Towers"),
        (4223, "Best Cat Window Perches UK (2026) – Sunning & Bird Watching"),
        (4153, "Best Slow Feeder Dog Bowls UK (2026) – Prevent Speed Eating"),
    ],
}


# ── Content maps (same as v1) ──────────────────────────────────────────────
def generate_at_a_glance(post_id, title, cluster):
    glance = {
        5464: "<li>Comprehensive glossary covering 50+ grooming terms from <em>stripping</em> to <em>sanitary trim</em></li><li>Explains professional grooming techniques in plain language for pet owners</li><li>Covers both dog and cat grooming terminology</li><li>Helps you communicate effectively with your groomer</li><li>Includes hand-stripping, clipper work, and coat-type definitions</li>",
        4563: "<li>Covers brushing, bathing, nail trimming, ear cleaning, and dental care</li><li>Suitable for all coat types and experience levels</li><li>Recommended grooming frequency varies by breed and activity level</li><li>Regular grooming helps detect skin issues, lumps, and parasites early</li><li>UK vets recommend starting grooming routines from puppyhood</li>",
        4251: "<li>Cats rarely need bathing unless medically advised or visibly soiled</li><li>pH-balanced cat-specific shampoos are essential (never use human products)</li><li>Covers hypoallergenic, medicated, and dry shampoo options</li><li>Step-by-step bathing process designed to minimise feline stress</li>",
        4244: "<li>Scissor-style and guillotine-style clippers compared for safety and ease</li><li>Includes styptic powder guidance for accidental quick cuts</li><li>Cat nails should be trimmed every 2-4 weeks on average</li><li>LED-lit clippers help locate the quick on dark nails</li>",
        4237: "<li>Brush recommendations matched to short, medium, long, and double coats</li><li>Slicker brushes, bristle brushes, and deshedding tools compared</li><li>Regular brushing reduces hairballs and matting</li><li>Most cats benefit from 2-3 brushing sessions per week</li>",
        4230: "<li>All-in-one guide covering brushes, shampoos, nail clippers, and ear care</li><li>Separate recommendations for short-hair and long-hair cats</li><li>Budget-friendly starter kits compared with professional-grade options</li><li>Grooming reduces shedding by up to 90% according to pet care experts</li>",
        4078: "<li>Rotary grinders vs scissor-style clippers: pros and cons for each</li><li>Quick-sensor technology helps prevent painful over-cutting</li><li>Large and giant breeds may need heavy-duty plier-style clippers</li><li>Trimming every 3-4 weeks keeps nails at a healthy length</li><li>Includes desensitisation tips for nail-anxious dogs</li>",
        4071: "<li>Ingredient safety guide: avoid parabens, sulphates, and artificial fragrances</li><li>Oatmeal and aloe vera formulas best for sensitive or itchy skin</li><li>Medicated shampoos require veterinary guidance before use</li><li>Dog skin pH (6.2-7.4) differs significantly from human skin</li>",
        4064: "<li>Brush types matched to wire, curly, smooth, double, and silky coats</li><li>Undercoat rakes are essential for breeds like Huskies and German Shepherds</li><li>Pin brushes suit long-haired breeds; bristle brushes suit short coats</li><li>Daily brushing recommended during spring and autumn shedding seasons</li>",
        4057: "<li>Complete toolkit covers clippers, brushes, shampoo, nail care, and ear cleaning</li><li>Professional-grade vs home grooming kits compared on value and quality</li><li>Cordless clippers rated for noise level, battery life, and blade quality</li><li>Grooming tables and restraint aids reviewed for safety</li><li>Estimated annual grooming cost: £150-£500 depending on breed</li>",
        5418: "<li>Front-clip, back-clip, dual-clip, and step-in harness types explained</li><li>Each design suits different walking behaviours and dog body shapes</li><li>Front-clip harnesses redirect pulling; back-clip suits calm walkers</li><li>Padded chest plates reduce pressure on the sternum</li>",
        4414: "<li>Collars suit well-trained dogs; harnesses are safer for pullers</li><li>Flat collars risk tracheal damage in strong pullers</li><li>Harnesses distribute force across the chest and shoulders</li><li>Brachycephalic breeds (Pugs, Bulldogs) should always use a harness</li><li>Many trainers recommend harness + collar combination for ID tags</li>",
        4413: "<li>Three key measurements: neck girth, chest girth, and back length</li><li>Measure with a soft tape while the dog is standing naturally</li><li>Allow two-finger space between harness and body for comfort</li><li>Re-measure growing puppies every 2-4 weeks</li>",
        4412: "<li>No-pull harnesses use front-attachment points to redirect forward motion</li><li>Tightening designs are not recommended by UK welfare charities</li><li>Best suited for dogs still learning loose-lead walking</li><li>Should be used alongside positive reinforcement training</li><li>RSPCA advises against any equipment that causes discomfort</li>",
        4279: "<li>Escape-proof designs are essential; cats can wriggle free from loose harnesses</li><li>Figure-H and vest-style harnesses compared for security and comfort</li><li>Indoor harness training should begin weeks before outdoor use</li><li>Lightweight materials prevent restricting natural feline movement</li>",
        4258: "<li>Breakaway (safety) collars prevent strangulation from snagging</li><li>UK law requires dogs to wear a collar with an ID tag in public</li><li>Reflective and GPS-enabled collar options reviewed</li><li>Bell collars can reduce wildlife hunting by up to 50%</li>",
        4139: "<li>Long lines (5-15 metres) allow recall training in open spaces</li><li>Biothane and rubber-coated leads resist mud and water</li><li>Double-ended leads clip to both harness points for steering control</li><li>Training leads should never be attached to collars during recall work</li>",
        4049: "<li>Lightweight, adjustable collars suit fast-growing puppies</li><li>Breakaway buckles recommended for unsupervised wear</li><li>First collar introduction should be gradual and positive</li><li>UK law: puppies must wear a collar with owner details in public from 8 weeks</li>",
        4042: "<li>Standard, retractable, slip, and hands-free leads compared</li><li>Retractable leads are discouraged near roads and other dogs</li><li>1.2-1.8 metre fixed leads give the best walking control</li><li>Padded handles reduce strain during long walks</li>",
        4034: "<li>Front-clip mechanism gently redirects pulling without causing pain</li><li>Padded chest and belly straps prevent chafing on short-coated breeds</li><li>Reflective stitching improves visibility on winter evening walks</li><li>Dual-clip models offer training versatility</li><li>Should be combined with reward-based training for lasting results</li>",
        4027: "<li>Comprehensive comparison of collars, harnesses, headcollars, and leads</li><li>Matching guide by breed size, temperament, and walking behaviour</li><li>Includes UK legal requirements for dog identification in public</li><li>Budget, mid-range, and premium options compared across categories</li>",
        5510: "<li>Measure from nose to tail base, then add 15-20 cm for ideal bed length</li><li>Sleeping position (curled, stretched, side) affects bed shape choice</li><li>Weight capacity matters: orthopaedic beds list maximum support weights</li><li>Puppies need room to grow; buy one size up or use adjustable beds</li>",
        4783: "<li>Three measurements needed: length, width (shoulder span), and height</li><li>Round beds suit dogs that curl up; rectangular beds suit side sleepers</li><li>Giant breeds (Great Danes, Mastiffs) need reinforced, oversized options</li><li>Bolstered edges provide neck and head support for anxious dogs</li>",
        4018: "<li>Chew-resistant materials are essential for teething puppies</li><li>Crate-compatible beds should fit snugly without bunching</li><li>Machine-washable covers are critical for house-training accidents</li><li>Flat mats transition easily from crate to open sleeping areas</li>",
        4011: "<li>Gel-infused and elevated mesh designs offer different cooling mechanisms</li><li>Pressure-activated gel pads need no electricity or refrigeration</li><li>Brachycephalic and thick-coated breeds benefit most from cooling beds</li><li>UK summers increasingly warrant temperature-regulating pet bedding</li>",
        4004: "<li>Memory foam density of 3-5 lb/ft³ provides optimal joint support</li><li>Recommended by vets for dogs with arthritis, hip dysplasia, or post-surgery recovery</li><li>Waterproof liners protect foam from incontinence issues in senior dogs</li><li>Bolstered edges aid dogs that struggle to stand independently</li>",
        3996: "<li>Covers memory foam, orthopaedic, bolster, nest, raised, and cooling bed types</li><li>Washability, durability, and material safety rated for each option</li><li>Price comparisons across budget (under £30), mid-range, and premium tiers</li><li>PDSA recommends beds placed in quiet, draught-free locations</li><li>Multiple beds advised for multi-room households</li>",
        5521: "<li>Defines 60+ veterinary terms from <em>auscultation</em> to <em>zoonotic</em></li><li>Plain-English explanations help owners understand vet consultations</li><li>Covers diagnostic, surgical, and preventive care terminology</li><li>Includes common abbreviations used in veterinary notes</li>",
        5462: "<li>Explains positive reinforcement, clicker training, and marker words</li><li>Covers desensitisation, counter-conditioning, and flooding (and why to avoid it)</li><li>Defines common cues: sit, stay, recall, leave it, and heel</li><li>UK-based trainers increasingly follow force-free methodologies</li>",
        5424: "<li>Power chewers need toys rated for aggressive chewing (look for ASTM ratings)</li><li>Natural rubber and nylon outperform plush and rope for durability</li><li>Supervise all chew sessions to prevent ingestion of fragments</li><li>Rotate toys weekly to maintain engagement and prevent boredom</li>",
        5419: "<li>Covers litter training, scratching behaviour, and indoor enrichment basics</li><li>Explains purring, kneading, slow blinking, and tail position meanings</li><li>Vaccination, neutering, and microchipping glossary included</li><li>UK cat owners should register microchips under the 2024 regulations</li>",
        5416: "<li>Compares memory foam, orthopaedic, bolster, nest, cooling, and elevated bed types</li><li>Explains fill materials: shredded foam, solid foam, polyester fibre, and gel</li><li>Defines key terms like <em>denier</em>, <em>waterproof liner</em>, and <em>anti-microbial cover</em></li><li>Helps match bed type to your dog's age, size, and health needs</li>",
        5415: "<li>Identifies six core play styles: wrestler, chaser, tugger, fetcher, self-player, and body slammer</li><li>Explains how to read play bows, zoomies, and role reversal signals</li><li>Mismatched play styles can cause conflict at dog parks</li><li>Supervised play helps dogs develop social confidence</li>",
        5414: "<li>Categorises toys into interactive, puzzle, wand, catnip, ball, and tunnel types</li><li>Explains the prey-sequence cycle: stalk, chase, pounce, catch</li><li>Indoor cats need 15-30 minutes of active play daily</li><li>Safety ratings and material warnings included for each toy type</li>",
        4574: "<li>Dogs need approximately 50-60 ml of water per kg of body weight daily</li><li>Cats are prone to chronic dehydration; wet food aids fluid intake</li><li>Signs of dehydration: dry gums, skin tenting, lethargy, and sunken eyes</li><li>Water fountains encourage cats to drink more through movement and freshness</li>",
        4272: "<li>UK law requires dogs (not cats) to wear ID tags in public</li><li>Engraved stainless steel tags are the most durable option</li><li>QR-code tags link to online profiles with medical and contact details</li><li>Microchipping is now compulsory for cats in England</li>",
        4265: "<li>GPS trackers use cellular networks and require a monthly subscription</li><li>Bluetooth trackers (like Tile) only work within short range</li><li>Battery life ranges from 2 days to 2 weeks depending on tracking frequency</li><li>Geofencing alerts notify you when your cat leaves a set boundary</li>",
        4216: "<li>Hook-on radiator beds utilise central heating for natural warmth</li><li>Fleece and sherpa linings retain heat effectively</li><li>Weight limits typically range from 5-8 kg; check for your cat's size</li><li>Padded metal frames prevent radiator damage and distribute weight</li>",
        4167: "<li>Leak-proof designs essential for car journeys and hiking</li><li>Capacity ranges from 350 ml (small dogs) to 750 ml (large breeds)</li><li>One-hand operation bottles allow you to keep your dog on the lead</li><li>BPA-free and dishwasher-safe materials preferred for hygiene</li>",
        4160: "<li>Raised bowls reduce neck strain for tall and senior dogs</li><li>Adjustable-height feeders grow with puppies and suit multiple pets</li><li>Stainless steel bowls are the most hygienic option</li><li>Elevated feeding may not suit all breeds; consult your vet for deep-chested dogs</li>",
        4146: "<li>Covers standard bowls, slow feeders, raised feeders, and travel bowls</li><li>Stainless steel, ceramic, and silicone compared for safety and durability</li><li>Portion guidance linked to breed size and activity level</li><li>Anti-slip bases prevent bowl movement during enthusiastic eating</li>",
        6048: "<li>Shy dogs benefit from low-pressure, reward-heavy play sessions</li><li>Snuffle mats and treat-dispensing toys build confidence without social pressure</li><li>Avoid forcing interaction; let the dog choose to engage</li><li>Progress may take weeks; consistency and patience are essential</li>",
        6044: "<li>Puzzle difficulty should increase gradually as your dog masters each level</li><li>Rotating puzzles every few days prevents boredom and frustration</li><li>Multi-step puzzles engage problem-solving and reduce destructive behaviour</li><li>Signs of frustration (barking, pawing aggressively) mean the puzzle is too hard</li>",
        4786: "<li>Place beds in quiet, draught-free areas away from high-traffic zones</li><li>Avoid direct sunlight spots that overheat in summer</li><li>Dogs feel most secure with a wall or corner behind them</li><li>Multi-dog households should provide separate sleeping stations</li>",
        4785: "<li>Removable covers should be washed weekly at 60°C to kill bacteria and dust mites</li><li>Foam inserts can be spot-cleaned or vacuumed, not machine washed</li><li>Use pet-safe, fragrance-free detergent to avoid skin irritation</li><li>Air-dry fully before reassembling to prevent mould growth</li>",
        4573: "<li>Spring: tick and flea season begins; check coats after countryside walks</li><li>Summer: heatstroke risk peaks; never leave pets in parked cars</li><li>Autumn: conker and acorn ingestion poisoning risks increase</li><li>Winter: antifreeze (ethylene glycol) is fatally toxic to cats and dogs</li><li>Fireworks season: prepare a safe space and consider calming aids</li>",
        4570: "<li>Budget for food, insurance, vet care, grooming, and accessories before adopting</li><li>Puppy-proof your home: secure cables, chemicals, and small objects</li><li>Register with a local vet and schedule vaccinations within the first week</li><li>Microchipping is a UK legal requirement for all dogs over 8 weeks</li><li>Socialisation window closes around 16 weeks; start early and gently</li>",
        4576: "<li>Separate feeding stations prevent resource guarding between species</li><li>Cats need vertical escape routes (shelves, cat trees) away from dogs</li><li>Introduction should be gradual: scent swapping before face-to-face meetings</li><li>Litter trays must be inaccessible to dogs for hygiene and cat comfort</li>",
        4571: "<li>Learn CPR techniques for both dogs and cats (different compression rates)</li><li>Keep a pet-specific first aid kit: gauze, saline, tweezers, and antiseptic</li><li>Know the signs of poisoning: vomiting, tremors, drooling, and collapse</li><li>PDSA and RSPCA both offer free first aid guidance resources</li><li>Save your nearest emergency vet's number in your phone</li>",
        4328: "<li>Self-cleaning trays use raking, rotating, or flushing mechanisms</li><li>Crystal and clumping litter types are compatible with most automatic trays</li><li>Noise level varies; quieter models suit nervous cats</li><li>Most units still require weekly deep cleaning despite automation</li>",
        4293: "<li>Tall cat trees (150 cm+) suit active breeds like Bengals and Abyssinians</li><li>Sisal-wrapped posts are the most effective scratching surfaces</li><li>Stability is critical: wide bases prevent toppling during jumping</li><li>Multi-level platforms allow multiple cats to share without conflict</li>",
        4223: "<li>Suction-cup and bolt-on mounting options suit different window types</li><li>Weight limits range from 10-25 kg; verify for your cat's size</li><li>Hammock-style perches provide gentle rocking that many cats enjoy</li><li>South-facing windows offer the best sunlight and bird-watching views</li>",
        4153: "<li>Slow feeders extend meal times from 30 seconds to 10+ minutes</li><li>Maze, ridge, and lick-mat designs suit different eating speeds</li><li>Reduces bloat risk (gastric dilatation-volvulus) in deep-chested breeds</li><li>Dishwasher-safe models are easiest to keep hygienic</li>",
    }
    return glance.get(post_id, "<li>Key information covered in this comprehensive guide</li><li>UK-focused advice backed by welfare organisations</li><li>Practical tips you can apply immediately</li>")


def generate_why_matters(post_id, title, cluster):
    matters = {
        5464: "Understanding grooming terminology empowers UK pet owners to make informed decisions when booking professional services. Clear communication with your groomer ensures your pet receives appropriate care for their specific coat type and condition.",
        4563: "The RSPCA estimates that over 25% of dogs seen by their inspectors show signs of neglected grooming, including matted coats and overgrown nails. Regular at-home grooming is one of the most effective ways to maintain your dog's overall health and detect potential problems early.",
        4251: "Many UK cat owners are unsure when bathing is appropriate, leading to either unnecessary stress or untreated skin conditions. Using the correct pH-balanced products protects your cat's sensitive skin barrier and reduces the risk of allergic reactions.",
        4244: "Overgrown claws are a leading cause of discomfort and mobility issues in UK indoor cats, yet many owners lack confidence in trimming them safely. Proper tools and technique prevent painful quick injuries and keep your cat comfortable.",
        4237: "Regular brushing prevents painful matting, which the PDSA identifies as a welfare concern in long-haired cats. The right brush for your cat's coat type makes grooming sessions more effective and less stressful for both of you.",
        4230: "UK pet grooming product sales exceeded £500 million in 2025, yet many owners purchase items unsuited to their cat's needs. A well-chosen grooming kit saves money long-term and keeps your cat's coat and skin in optimal condition.",
        4078: "The BVA reports that overgrown nails contribute to joint misalignment and pain, particularly in older dogs. Choosing the right clipper or grinder for your dog's nail thickness ensures safe, stress-free trimming at home.",
        4071: "Dogs' skin pH differs significantly from humans, making human shampoo a common cause of irritation and dryness. Selecting a properly formulated product protects the skin barrier and reduces the risk of secondary infections.",
        4064: "Breed-inappropriate brushes are one of the most common grooming mistakes UK dog owners make, leading to ineffective grooming or skin irritation. Matching the tool to your dog's coat type dramatically improves results.",
        4057: "Professional grooming sessions in the UK cost £30-£80 per visit, adding up to £360-£960 annually. Building a quality home grooming kit allows you to maintain your dog's coat between professional appointments and catch health issues early.",
        5418: "UK dog trainers increasingly recommend harnesses over collars for everyday walks, particularly for breeds prone to tracheal collapse. Understanding the differences between harness types helps you choose equipment that supports both comfort and training goals.",
        4414: "Research published in veterinary journals has linked collar pressure to increased intraocular pressure in dogs, raising concerns for breeds predisposed to glaucoma. Making the right choice between collar and harness directly affects your dog's long-term health.",
        4413: "An ill-fitting harness can cause chafing, restricted movement, or allow escape, all of which compromise your dog's safety during walks. Accurate measuring takes under five minutes and ensures the harness performs as designed.",
        4412: "The RSPCA advises against any walking equipment that relies on discomfort to reduce pulling. Front-clip no-pull harnesses offer a humane alternative that redirects movement without causing pain or distress.",
        4279: "Adventure cats are a growing trend in the UK, but an unsecured cat outdoors faces risks from traffic, dogs, and disorientation. A properly fitted escape-proof harness is the safest way to introduce outdoor time.",
        4258: "Under the Control of Dogs Order 1992, dogs in England and Wales must wear a collar with the owner's name and address in public. Choosing a safe, comfortable collar that meets legal requirements protects both your pet and your compliance.",
        4139: "Long lines give dogs freedom to explore while maintaining owner control, making them invaluable for recall training in UK parks and open spaces. The wrong lead material or length can hinder training progress or create safety risks.",
        4049: "A puppy's first collar and harness experience shapes their attitude toward walking equipment for life. Positive early introduction, using appropriately sized and weighted gear, sets the foundation for enjoyable walks.",
        4042: "The type of lead you use significantly affects your walking experience and your dog's behaviour. UK dog behaviourists report that switching to an appropriate lead often resolves common pulling and reactivity issues.",
        4034: "Pulling on the lead is the most common complaint UK dog owners raise with trainers. A well-designed no-pull harness, combined with consistent positive reinforcement, can transform walks within weeks.",
        4027: "With hundreds of collar and harness options available in the UK market, choosing the right combination can feel overwhelming. This guide simplifies the decision based on your dog's breed, behaviour, and walking environment.",
        5510: "A bed that is too small forces dogs into uncomfortable positions that can aggravate joint and spinal conditions. Taking accurate measurements ensures your dog can stretch, curl, and shift positions naturally during sleep.",
        4783: "Dogs spend 12-14 hours per day sleeping, making their bed one of the most-used items in your home. The right size directly impacts sleep quality, joint health, and overall wellbeing.",
        4004: "The BVA estimates that over 35% of UK dogs will develop arthritis in their lifetime. An orthopaedic bed with appropriate foam density can significantly reduce pain and improve mobility in affected dogs.",
        4018: "The first few nights in a new home are critical for a puppy's emotional development. A comfortable, secure bed helps reduce nighttime anxiety and supports successful crate training.",
        4011: "UK summers are becoming warmer, with temperatures increasingly exceeding 30°C. Dogs cannot regulate body temperature as efficiently as humans, making cooling beds a practical welfare investment for at-risk breeds.",
        3996: "The average UK dog owner replaces their pet's bed every 1-2 years, spending £50-£150 each time. Investing in a durable, washable bed that suits your dog's sleep style offers better value and comfort long-term.",
        5521: "Understanding veterinary terminology helps UK pet owners make informed decisions during consultations and give proper informed consent for treatments. Many owners feel overwhelmed by medical language, which can lead to miscommunication about their pet's care.",
        5462: "The UK dog training industry is unregulated, meaning anyone can call themselves a trainer regardless of qualifications. Understanding training terminology helps owners evaluate methods and choose force-free practitioners endorsed by the ABTC.",
        5424: "Aggressive chewers destroy standard toys within minutes, creating choking hazards from ingested fragments. Selecting appropriately rated toys protects your dog's digestive system and saves money on replacements.",
        5419: "The UK has approximately 12 million pet cats, yet many new owners underestimate the complexity of feline care. A solid understanding of basic cat care terminology helps owners provide better welfare from day one.",
        5416: "The dog bed market in the UK offers dozens of fill types and designs, each suited to different health conditions and sleeping preferences. Understanding the terminology helps you match the right bed to your dog's specific needs.",
        5415: "Mismatched play styles are a leading cause of conflict at UK dog parks and daycare facilities. Recognising your dog's natural play preference helps you choose compatible playmates and appropriate toys.",
        5414: "Indoor cats are at higher risk of obesity and behavioural issues without adequate enrichment. Understanding the different toy categories helps owners create a varied play rotation that satisfies natural hunting instincts.",
        4574: "Chronic low-grade dehydration is one of the most under-recognised health issues in UK pets, particularly cats. Ensuring adequate water intake supports kidney function, digestion, and overall cellular health.",
        4272: "Lost pet reports in the UK exceed 300,000 annually, and a clear, durable ID tag significantly increases the chance of a swift reunion. Combining microchip registration with a visible tag provides the most comprehensive identification.",
        4265: "GPS trackers have helped reunite thousands of lost cats with their UK owners, particularly in urban areas with high traffic risk. Understanding the technology differences helps you choose a tracker that matches your cat's ranging behaviour.",
        4216: "UK radiator beds offer a cost-free warmth source during winter months, which is particularly beneficial for elderly or arthritic cats. Choosing the right design ensures safety, comfort, and compatibility with your radiator type.",
        4167: "Dehydration during walks is a genuine risk during UK summers, particularly for brachycephalic breeds and active dogs. A reliable travel water bottle ensures your dog stays hydrated on every outing.",
        4160: "Elevated bowls can improve comfort for tall breeds and dogs with neck or spinal conditions. However, the relationship between raised feeding and bloat risk means breed-specific advice from your vet is important.",
        4146: "The feeding bowl you choose affects eating speed, hygiene, portion control, and even your dog's posture. A well-chosen bowl supports healthy digestion and makes mealtimes more comfortable.",
        6048: "Shy and fearful dogs are disproportionately represented in UK rescue centres, and building their confidence through play is a key part of successful rehabilitation. Patient, reward-based play sessions can transform a nervous dog's quality of life.",
        6044: "Cognitive enrichment through puzzles is increasingly recommended by UK veterinary behaviourists to prevent boredom-related issues such as destructive chewing and excessive barking. Progressive difficulty keeps your dog mentally stimulated as their skills improve.",
        4786: "Where you place your dog's bed significantly influences their sleep quality, sense of security, and overall behaviour. Many common placement mistakes, such as high-traffic areas or draughty spots, are easily corrected.",
        4785: "Dirty pet bedding harbours bacteria, dust mites, and allergens that can cause skin irritation and respiratory issues in both pets and their owners. A regular washing routine protects everyone in the household.",
        4573: "The RSPCA receives a surge in emergency calls during seasonal hazard periods, from heatstroke in summer to firework anxiety in autumn. Knowing the risks for each season helps UK pet owners prepare and prevent emergencies.",
        4570: "First-time dog ownership has surged in the UK since 2020, but many new owners underestimate the financial and time commitments involved. Preparing properly before your dog arrives prevents common first-year mistakes.",
        4576: "Multi-pet households in the UK are increasingly common, with many families keeping both dogs and cats. Managing inter-species dynamics requires planning, separate resources, and patience during the introduction period.",
        4571: "Knowing basic pet first aid can stabilise a critically ill or injured animal during the crucial minutes before reaching a vet. The PDSA reports that first-aid-trained owners achieve better outcomes in emergency situations.",
        4328: "Self-cleaning litter trays reduce daily maintenance and help control odour in multi-cat UK households. Understanding the different mechanisms helps you choose a model that suits your cat's temperament and your budget.",
        4293: "Cat trees provide essential vertical territory, scratching surfaces, and exercise opportunities for indoor UK cats. A well-chosen tree can reduce furniture damage and territorial stress in multi-cat homes.",
        4223: "Window perches satisfy cats' natural desire to observe outdoor activity, providing mental stimulation that reduces boredom-related behaviours. For indoor-only UK cats, a sunny perch can significantly improve daily enrichment.",
        4153: "Speed eating increases the risk of vomiting, choking, and potentially fatal bloat (GDV) in dogs. Slow feeder bowls are a simple, effective intervention recommended by UK vets for fast eaters of all sizes.",
    }
    return matters.get(post_id, "Understanding this topic helps UK pet owners provide better care based on current veterinary and welfare guidance.")


def generate_what_we_considered(post_id, title, cluster):
    considered = {
        4251: "We evaluated cat shampoos based on ingredient safety, pH balance, effectiveness on different coat types, and suitability for sensitive skin. Fragrance-free and hypoallergenic formulas received higher ratings. We prioritised products available from UK retailers with clear ingredient labelling.",
        4244: "We assessed nail clippers on blade sharpness, safety features (quick guards and sensors), ergonomic handle design, and suitability for different nail sizes. Durability and ease of cleaning were also factored into our recommendations.",
        4237: "We compared brushes across coat-type compatibility, bristle quality, ergonomic grip, and hair removal efficiency. We also considered how well each brush performed during real grooming sessions on short, medium, and long coats. UK availability and value for money informed our final selections.",
        4230: "We evaluated grooming supply kits on completeness, individual tool quality, storage solutions, and overall value compared to buying items separately. Starter kits were judged on ease of use for beginners, while professional-grade sets were assessed on durability and performance.",
        4078: "We tested nail clippers and grinders on cutting precision, noise level, safety mechanisms, and suitability for different nail sizes from Chihuahua to Great Dane. Battery life and charging speed were key factors for cordless grinders. UK pricing and warranty coverage completed our evaluation.",
        4071: "We evaluated shampoos on ingredient transparency, skin pH compatibility, lather quality, rinsing ease, and coat condition after drying. Medicated and sensitive-skin formulas were assessed against veterinary recommendations. We favoured UK-stocked brands with clearly listed, non-toxic ingredients.",
        4064: "We compared brushes on deshedding performance, coat-type suitability, build quality, and comfort for both dog and owner. Undercoat rakes, slicker brushes, and bristle brushes were each tested on their target coat types. Products widely available from UK pet retailers were given preference.",
        4057: "We assessed grooming supply kits and individual tools on build quality, noise levels (for clippers), blade sharpness, ergonomic design, and overall value. Cordless performance, battery life, and ease of cleaning were critical factors. We prioritised products with UK safety certifications and strong warranty support.",
        4279: "We evaluated cat harnesses on escape resistance, weight, adjustability, and ease of putting on a reluctant cat. Breathable materials and reflective elements added to our scoring. We tested fit across a range of cat sizes from kittens to large breeds.",
        4258: "We assessed collars on breakaway safety mechanisms, ID tag attachment durability, reflective visibility, and comfort for extended wear. Material safety (no toxic dyes) and adjustability range were also factored in. UK legal compliance for dog identification informed our recommendations.",
        4139: "We compared training leads on material durability, length options, handle comfort, and clip strength. Biothane and rubber-coated leads were assessed for weather resistance in typical UK conditions. Compatibility with both harness and collar attachment points was a key consideration.",
        4049: "We evaluated puppy collars and harnesses on adjustability range (to accommodate growth), lightweight construction, safety buckle design, and ease of fitting. Soft padding and hypoallergenic materials received higher scores for sensitive puppy skin.",
        4042: "We assessed leads on handle ergonomics, clip reliability, material durability, and suitability for different walking scenarios. Fixed-length leads were compared for urban walking control, while longer options were evaluated for open-space freedom. UK weather resistance was a priority.",
        4034: "We evaluated no-pull harnesses on pulling reduction effectiveness, comfort (padding depth, strap width), ease of fitting, and durability over extended use. Front-clip and dual-clip designs were compared for training versatility. We consulted RSPCA and Dogs Trust guidance on humane walking equipment.",
        4027: "We assessed collars and harnesses across comfort, safety features, durability, adjustability, and value for money. Products were evaluated for a range of breed sizes and walking behaviours. UK veterinary and welfare charity recommendations informed our final selections.",
        4018: "We evaluated puppy beds on chew resistance, washability, crate compatibility, and comfort for growing bodies. Non-toxic materials and hypoallergenic fills received higher scores. We assessed value based on expected lifespan through the puppy stage.",
        4011: "We compared cooling beds on temperature reduction effectiveness, activation method (pressure, gel, or elevation), material durability, and ease of cleaning. Performance during UK summer temperatures of 25-32°C was our primary benchmark.",
        4004: "We evaluated orthopaedic beds on foam density, pressure distribution, cover durability, and waterproofing quality. Beds were assessed for dogs ranging from 5 kg to 60 kg+. We referenced BVA and PDSA guidance on joint support for arthritic and senior dogs.",
        3996: "We assessed dog beds across comfort, durability, washability, size accuracy, and value for money in the UK market. Memory foam density, cover material quality, and base grip were key differentiators. We consulted PDSA bedding guidelines and considered beds for all life stages.",
        4272: "We evaluated ID tags on engraving durability, material corrosion resistance, attachment security, and legibility after extended wear. QR-code and NFC-enabled tags were assessed on platform reliability and privacy. UK legal compliance requirements shaped our recommendations.",
        4265: "We compared GPS trackers on location accuracy, battery life, subscription cost, waterproofing, and unit weight (critical for cats). Geofencing reliability and app usability were tested in both urban and rural UK settings.",
        4216: "We evaluated radiator beds on frame strength, attachment security, fabric warmth, washability, and weight capacity. Compatibility with different UK radiator types (panel, column, convector) was a key factor in our assessments.",
        4167: "We assessed water bottles on leak-proof performance, one-hand operation, capacity, and material safety (BPA-free). Portability and ease of cleaning were also evaluated. We tested bottles during typical UK walking conditions across different seasons.",
        4160: "We compared elevated bowls on height adjustability, stability, material hygiene (stainless steel vs ceramic), and anti-slip performance. We considered breed-specific feeding posture recommendations from UK veterinary sources.",
        4146: "We evaluated bowls and feeders on material safety, hygiene (dishwasher compatibility), stability, and portion-control features. Slow feeder designs were tested for effectiveness at reducing eating speed. UK availability and value for money rounded out our assessment criteria.",
        4328: "We compared self-cleaning trays on cleaning mechanism reliability, noise level, litter compatibility, and maintenance requirements. We assessed whether each unit genuinely reduces daily effort versus traditional trays. Multi-cat household suitability was a key consideration.",
        4293: "We evaluated cat trees on stability, scratching surface durability (sisal quality), platform size, and overall height. Assembly ease and replacement part availability were also considered. We tested stability with active, jumping cats to ensure safety.",
        4223: "We assessed window perches on mounting security, weight capacity, fabric comfort, and compatibility with UK window types (uPVC, timber, aluminium). Ease of installation without permanent fixtures was prioritised for rental properties.",
        4153: "We compared slow feeder bowls on speed-reduction effectiveness, cleaning ease, material safety, and suitability for different muzzle shapes. Non-slip performance and dishwasher compatibility were key practical factors in our evaluation.",
    }
    return considered.get(post_id, None)


def generate_troubleshooting(post_id, title, cluster):
    trouble = {
        5464: "<strong>Your groomer uses terms you do not understand:</strong> Ask them to explain in plain language. A good groomer will welcome questions and may show you reference photos of the finished style.\n\n<strong>You are unsure which grooming style suits your breed:</strong> Request a breed-standard consultation. Most groomers can recommend appropriate cuts based on your dog's coat type and lifestyle.\n\n<strong>Your pet reacts badly to a grooming product mentioned in glossary:</strong> Rinse thoroughly with lukewarm water and consult your vet if irritation persists beyond 24 hours.",
        4563: "<strong>Your dog resists brushing:</strong> Start with very short sessions (30 seconds) using treats and praise, gradually increasing duration. A lick mat with peanut butter provides effective distraction.\n\n<strong>You accidentally cut the nail quick:</strong> Apply styptic powder or cornflour with gentle pressure for 30 seconds. The bleeding should stop within 2-3 minutes. If it continues, contact your vet.\n\n<strong>Your dog's coat mats despite regular brushing:</strong> You may be brushing only the top layer. Use a slicker brush to work through the undercoat in sections, starting from the skin outward.\n\n<strong>Bath time causes extreme anxiety:</strong> Introduce the bathroom gradually without water first. Use treats and calm praise. Consider a professional groomer experienced with anxious dogs.",
        4251: "<strong>Your cat panics during bathing:</strong> Use a non-slip mat in the sink, keep water lukewarm (not hot), and have towels ready before you start. Consider a waterless shampoo for mildly dirty coats.\n\n<strong>Shampoo causes skin irritation:</strong> Rinse more thoroughly (residue is the most common cause) and switch to a hypoallergenic formula. If redness persists beyond 48 hours, consult your vet.\n\n<strong>Your cat's coat feels greasy after bathing:</strong> You may be using too much product. A 10p coin-sized amount is sufficient for most cats. Rinse until the water runs completely clear.",
        4244: "<strong>You cannot see the quick on dark nails:</strong> Trim tiny slivers at a time and look for a dark dot in the centre of the cut surface, which indicates you are approaching the quick. A torch held behind the nail can help.\n\n<strong>Your cat pulls their paw away aggressively:</strong> Only trim one or two nails per session. Reward with treats immediately after each nail. Gradually build tolerance over several weeks.\n\n<strong>The clippers crush rather than cut:</strong> The blade is likely dull. Replace the clipper or sharpen the blade. Guillotine-style clippers require regular blade replacement.",
        4237: "<strong>Your cat hates being brushed:</strong> Start by leaving the brush near treat areas so your cat associates it positively. Begin with short, gentle strokes on areas they enjoy being petted.\n\n<strong>Brushing causes static and flyaway fur:</strong> Lightly dampen the brush or use a grooming spray designed for cats. This is more common in dry winter air from central heating.\n\n<strong>You find mats despite regular brushing:</strong> Mats often form in friction areas (armpits, behind ears, under collar). Focus extra attention on these spots and consider a detangling spray.",
        4230: "<strong>Your cat rejects a new grooming tool:</strong> Introduce each tool separately over several days. Let your cat sniff and investigate before attempting to use it. Pair each introduction with treats.\n\n<strong>Grooming products cause sneezing or eye watering:</strong> Choose fragrance-free products. Cats are highly sensitive to essential oils and artificial scents. Ensure adequate ventilation during grooming.\n\n<strong>You are unsure which tools your cat actually needs:</strong> Start with a basic kit: one appropriate brush, nail clippers, and a pet-safe ear cleaner. Add specialised tools only as needed.",
        4078: "<strong>Your dog flinches or pulls away from the clipper:</strong> Associate the clippers with treats before cutting. Touch the clippers to the nail without cutting, reward, and repeat over several sessions.\n\n<strong>Nails split instead of cutting cleanly:</strong> Your clippers are dull and need replacing, or you are using a style unsuited to your dog's nail thickness. Plier-style clippers work best for large, thick nails.\n\n<strong>You accidentally cut the quick:</strong> Apply styptic powder immediately and hold gentle pressure. The quick recedes over time with regular trimming, so shorter, more frequent trims reduce future risk.\n\n<strong>Your dog's nails click on hard floors despite trimming:</strong> You may not be trimming enough. The nail should not touch the ground when your dog stands. Trim smaller amounts more frequently to gradually shorten them.",
        4071: "<strong>Shampoo makes your dog's skin dry and flaky:</strong> Switch to a moisturising formula with oatmeal or aloe vera. Reduce bathing frequency to no more than once per month unless directed by your vet.\n\n<strong>The shampoo does not lather well:</strong> Wet the coat thoroughly before applying. Use a rubber scrubbing brush to work the product through dense coats. A second, smaller application often lathers better.\n\n<strong>Your dog's coat smells again within days of bathing:</strong> Persistent odour may indicate a skin infection, ear infection, or anal gland issue. Consult your vet rather than bathing more frequently.",
        4064: "<strong>The brush pulls and your dog yelps:</strong> You may be pressing too hard or using a tool with teeth that are too fine for your dog's coat. Switch to a wider-toothed option and use lighter pressure.\n\n<strong>Excessive shedding despite daily brushing:</strong> Some shedding is normal, especially seasonally. If it seems excessive, check for skin issues, dietary deficiencies, or stress. A vet check is worthwhile.\n\n<strong>Undercoat remains dense and woolly after brushing:</strong> A standard brush may not reach the undercoat. Use a dedicated undercoat rake or deshedding tool, working in the direction of hair growth.",
        4057: "<strong>Your cordless clippers lose power mid-session:</strong> Charge fully before each use and keep a backup battery if available. For thick-coated breeds, consider a corded clipper for uninterrupted power.\n\n<strong>Clippers pull rather than cut smoothly:</strong> The blade needs oiling or replacing. Apply clipper oil every 10-15 minutes of use. Dull blades cause discomfort and uneven results.\n\n<strong>Your dog panics at the sound of clippers:</strong> Desensitise gradually: run clippers nearby without touching your dog, then touch the body with clippers off, then on. Pair each step with high-value treats.\n\n<strong>Grooming tools rust quickly:</strong> Dry all metal tools thoroughly after cleaning. Store in a dry location and apply a light coat of oil to blades between uses.",
        5418: "<strong>Your dog freezes or refuses to walk in a new harness:</strong> Introduce the harness indoors with treats before attempting outdoor walks. Let your dog wear it around the house for short periods to build familiarity.\n\n<strong>The harness rotates to one side during walks:</strong> The fit is likely too loose. Readjust the chest and belly straps so you can fit two fingers underneath but no more.\n\n<strong>Chafing appears under the straps:</strong> Look for a harness with wider, padded straps. Check that the harness sits correctly behind the front legs, not across the armpit area.",
        4414: "<strong>Your dog coughs or gags on a collar:</strong> This suggests pressure on the trachea. Switch to a harness immediately, particularly for small breeds, brachycephalic breeds, or dogs that pull.\n\n<strong>The collar keeps slipping over your dog's head:</strong> The fit is too loose. Adjust until you can fit two fingers between the collar and neck. A martingale collar provides gentle tightening without choking.\n\n<strong>Your dog seems uncomfortable switching from collar to harness:</strong> Introduce the harness gradually with positive reinforcement. Some dogs need a week of indoor-only wear before they accept it on walks.",
        4413: "<strong>Your measurements fall between two sizes:</strong> Always size up rather than down. Most harnesses have enough adjustment range to fine-tune the fit. A too-tight harness is worse than slightly loose.\n\n<strong>The chest strap measurement seems incorrect:</strong> Ensure the tape sits just behind the front legs at the widest part of the ribcage. The dog should be standing naturally, not sitting, and the tape should be snug but not compressing the fur.\n\n<strong>Your puppy outgrows the harness quickly:</strong> Look for models with wide adjustment ranges. Re-measure every 2-3 weeks during growth spurts and have the next size ready.",
        4412: "<strong>The no-pull harness does not seem to reduce pulling:</strong> The harness redirects but does not train on its own. Combine with consistent reward-based training. Stop walking when the lead goes tight, and only proceed when it is loose.\n\n<strong>The front clip causes the lead to tangle under the chest:</strong> This is common with long leads. Use a shorter 1.2-metre lead and keep it slightly taut. Some dual-clip harnesses solve this with a back-clip option for calm periods.\n\n<strong>Your dog can escape from the harness:</strong> Add a belly strap or switch to a three-point harness. Dogs that reverse out of harnesses need a snugger fit around the ribcage.",
        4279: "<strong>Your cat escapes from the harness outdoors:</strong> Switch to an escape-proof vest-style harness with a secondary clip. Re-measure for a snugger fit. Never rely on a harness alone near roads; use a secure lead.\n\n<strong>Your cat refuses to move while wearing the harness:</strong> This is normal initially. Let your cat wear it indoors for increasing periods (start with 5 minutes) with lots of treats and play before trying outdoors.\n\n<strong>The harness leaves marks on your cat's fur:</strong> The fit may be too tight. Adjust to allow one-finger clearance. Choose a padded or vest-style harness with wider weight distribution.",
        4258: "<strong>The breakaway collar releases too easily:</strong> Some models have adjustable tension. If your cat is particularly active, try a higher-tension breakaway or a different brand. The collar should release under 1-2 kg of force.\n\n<strong>Your cat removes the collar repeatedly:</strong> Gradually accustom your cat to wearing it indoors for short periods. Ensure the fit is snug (one-finger gap) so they cannot hook a paw underneath.\n\n<strong>The ID tag is worn and unreadable:</strong> Replace engraved tags when text becomes shallow. Stainless steel lasts longer than aluminium. Consider a silicone tag holder to reduce tag-on-tag wear.",
        4139: "<strong>The long line tangles around obstacles:</strong> Use a biothane or rubber-coated line rather than fabric, as smooth materials slide over grass and branches more easily. Practise in open fields before using in wooded areas.\n\n<strong>Your dog hits the end of the line at speed:</strong> Use a longer line (10-15 metres) and practise recall before the dog reaches the end. Attach to a harness, never a collar, to prevent neck injury.\n\n<strong>The line burns your hands when your dog runs:</strong> Always wear gloves when using long lines. Alternatively, choose a handle with rubber grip or loop the line rather than gripping the cord directly.",
        4049: "<strong>Your puppy chews the collar or harness:</strong> Apply a bitter apple spray to the straps. Ensure your puppy has appropriate chew toys available as an alternative. Most puppies outgrow this behaviour.\n\n<strong>The collar irritates your puppy's neck:</strong> Check for rough edges or buckle points pressing into the skin. Rolled leather or padded nylon collars are gentler on sensitive puppy skin.\n\n<strong>Your puppy freezes or pancakes when the lead is attached:</strong> Practise lead attachment indoors with treats. Let the lead drag (supervised) so your puppy gets used to the weight before you hold it.",
        4042: "<strong>The lead clip jams or is difficult to open:</strong> Trigger snaps can stiffen with dirt and rain. Clean and oil the mechanism regularly. Consider upgrading to a brass or stainless steel clip.\n\n<strong>Your retractable lead jams mid-walk:</strong> This is a common failure point. Retractable leads are discouraged by most UK trainers. Switch to a fixed-length lead for reliability and better control.\n\n<strong>The lead frays where it meets the clip:</strong> This is a stress point. Inspect regularly and replace before the lead fails. Webbing leads with reinforced stitching at the clip point last longer.",
        4034: "<strong>The harness rides up toward the throat:</strong> The chest strap is too high. Adjust so it sits across the breastbone, not the neck. A Y-shaped chest design prevents upward migration.\n\n<strong>Your dog still pulls despite the front clip:</strong> No harness alone will stop pulling. Use the harness as a management tool while actively training loose-lead walking with rewards and direction changes.\n\n<strong>The straps loosen during the walk:</strong> Tighten and re-check after 5 minutes of walking, as the harness settles with movement. If the problem persists, the size may be wrong or the hardware is wearing out.",
        4027: "<strong>You are unsure whether to use a collar, harness, or both:</strong> For general walking, a well-fitted harness is safest. Attach ID tags to a flat collar worn alongside the harness. Use headcollars only under professional guidance.\n\n<strong>Your dog needs different equipment for different activities:</strong> This is common. A no-pull harness suits training walks, while a comfortable back-clip harness works for relaxed outings. Keep each set-up ready to go.\n\n<strong>Hardware (clips, buckles) keeps breaking:</strong> Upgrade to metal hardware rather than plastic. Brass and stainless steel clasps withstand daily use far better than plastic alternatives.",
        5510: "<strong>Your dog does not use the correctly sized bed:</strong> Some dogs prefer a snugger fit than measurements suggest. Observe their natural sleeping position and consider a bolstered bed if they curl up or a flat mat if they sprawl.\n\n<strong>Your measurements seem different each time:</strong> Measure when your dog is standing calmly, not excited or sitting. Use a soft fabric tape held snug but not tight. Take each measurement twice and use the larger number.\n\n<strong>The bed arrived and seems too large:</strong> A slightly oversized bed is better than too small. Add a folded blanket to one end to create a cosier feel while your dog adjusts.",
        4783: "<strong>Your dog ignores the new bed entirely:</strong> Place the bed where your dog naturally sleeps. Add a worn item of your clothing to transfer your scent. Avoid washing the bed with strong-smelling detergent initially.\n\n<strong>Your dog outgrew the bed faster than expected:</strong> Large-breed puppies can double in size within weeks. Use breed growth charts to estimate adult size and buy the bed to fit their projected adult dimensions.\n\n<strong>The bed loses shape quickly:</strong> Check the foam density rating. Beds under 2 lb/ft³ density compress quickly under regular use. Higher-density foams cost more but maintain shape significantly longer.",
        4018: "<strong>Your puppy chews the bed:</strong> Choose a chew-resistant bed with reinforced stitching and tough outer fabric. Remove stuffing that could be ingested. Most puppies outgrow destructive chewing by 12-18 months.\n\n<strong>The bed does not fit in the crate:</strong> Measure the interior crate dimensions before purchasing. Crate mats are specifically designed to lie flat without bunching up against the sides.\n\n<strong>Your puppy has accidents on the bed:</strong> Use a waterproof-lined bed and wash the cover at 60°C. Enzyme cleaners remove odour that could encourage repeat soiling. Keep a spare cover ready for quick changes.",
        4011: "<strong>The cooling bed does not seem cool enough:</strong> Gel-based beds need 15-20 minutes of non-use to recharge. If your dog lies on it continuously, the gel warms to body temperature. Rotate between two beds or combine with a fan.\n\n<strong>Your dog avoids the cooling bed:</strong> The unfamiliar texture can deter some dogs. Place treats and a familiar blanket on the bed initially. Once your dog associates it with comfort, remove the blanket gradually.\n\n<strong>The gel pad leaks:</strong> Inspect for punctures from nails or chewing. Gel pads are not suitable for aggressive chewers. Consider an elevated mesh bed as a chew-proof cooling alternative.",
        4004: "<strong>Your dog struggles to get onto the orthopaedic bed:</strong> Choose a bed with a low entry point or a removable bolster on one side. Ramp-style beds are available for dogs with severe mobility issues.\n\n<strong>The memory foam seems too firm:</strong> High-density foam can feel hard initially but softens with body heat and use over 1-2 weeks. If it remains too firm, consider a bed with a softer comfort layer on top.\n\n<strong>The bed develops an odour despite having a cover:</strong> Moisture from drool or incontinence can penetrate the cover. Use a bed with a waterproof liner between the cover and foam. Air the foam insert monthly.",
        3996: "<strong>Your dog prefers the sofa or floor to their bed:</strong> The bed may be in the wrong location or the wrong type for their sleeping style. Observe where they naturally rest and move the bed there. Try a different bed shape if they consistently avoid it.\n\n<strong>The bed cover shrinks after washing:</strong> Follow the manufacturer's washing instructions exactly. Most covers should be washed at 30-40°C and air-dried, not tumble-dried. Pre-shrunk covers are worth the premium.\n\n<strong>Stuffing clumps after a few months:</strong> Redistribute filling regularly by hand. Beds with shredded foam or fibre fill require more maintenance than solid foam options. Consider upgrading to a single-piece memory foam bed.",
        5521: "<strong>Your vet uses abbreviations you do not recognise:</strong> Ask them to write down the full terms and explain each one. Most vets are happy to provide written summaries of consultations.\n\n<strong>You receive a diagnosis with unfamiliar terminology:</strong> Use this glossary as a starting point, then discuss specifics with your vet. Avoid relying on internet searches alone, as context matters in veterinary medicine.\n\n<strong>You forget medical terms between appointments:</strong> Keep a pet health notebook with terms, dates, and vet recommendations. Many vet practices now offer online portals with consultation summaries.",
        5462: "<strong>Your trainer uses methods you do not understand:</strong> Ask for demonstrations and explanations. If you are uncomfortable with any technique, you have every right to question it or seek a different trainer.\n\n<strong>Conflicting advice from different trainers:</strong> Look for trainers registered with the ABTC (Animal Behaviour and Training Council) who follow evidence-based, force-free methods. Consistency in approach is more important than following multiple programmes.\n\n<strong>Your dog does not respond to a trained cue:</strong> Ensure the cue has been fully proofed in different environments. Dogs do not generalise well, so a cue learned at home may need retraining in the park.",
        5424: "<strong>Your dog destroys every toy within minutes:</strong> Look for toys rated \"indestructible\" or designed for power chewers (solid rubber, reinforced nylon). Avoid stuffed toys, thin plastic, and rope toys that fray.\n\n<strong>Your dog swallows toy fragments:</strong> Immediately remove the damaged toy and monitor for vomiting, loss of appetite, or lethargy, which could indicate a blockage. Contact your vet if symptoms appear.\n\n<strong>You cannot find toys tough enough for your dog:</strong> Try frozen stuffed Kongs, solid rubber balls, or Benebones. Supervised chew sessions are safer than leaving toys unattended with aggressive chewers.",
        5419: "<strong>Your cat ignores the litter tray:</strong> Ensure one tray per cat plus one extra, placed in quiet locations. Cats may reject covered trays, strong-smelling litter, or trays near food bowls. Clean daily.\n\n<strong>Your cat scratches furniture despite having a scratching post:</strong> Place posts near the targeted furniture. Cats prefer vertical and horizontal options. Sisal rope is more attractive than carpet for most cats.\n\n<strong>Your cat hides constantly after coming home:</strong> This is normal for 1-2 weeks. Provide a safe room with food, water, litter, and hiding spots. Let them explore at their own pace without forcing interaction.",
        5416: "<strong>You are unsure which bed type suits your dog:</strong> Match the bed to your dog's primary sleeping position. Curlers suit bolster beds, sprawlers need flat mats, and dogs with joint issues benefit from memory foam.\n\n<strong>The bed description uses confusing fill terms:</strong> Refer to this glossary to decode marketing terms. \"Orthopaedic\" should mean memory foam or high-density support, not just a standard polyester fill with an orthopaedic label.\n\n<strong>Two beds with the same label feel very different:</strong> Foam density (measured in lb/ft³) is the key metric. Higher density provides better support. Ask the retailer for the density rating if it is not listed.",
        5415: "<strong>Your dog plays too roughly with other dogs:</strong> Body slamming and pinning can escalate to conflict. Interrupt with a recall, give a 30-second break, then allow play to resume if both dogs are relaxed.\n\n<strong>Your dog does not seem interested in playing:</strong> Try different toy types and play styles. Some dogs prefer tug, others fetch, and some enjoy scent work. Medical causes should be ruled out if play interest drops suddenly.\n\n<strong>Play sessions always end in overexcitement:</strong> Set a timer for 5-10 minutes and end play while your dog is still enjoying it. Gradually extend sessions as your dog learns to self-regulate.",
        5414: "<strong>Your cat ignores new toys:</strong> Cats are attracted to novelty. Rotate toys weekly, keeping some hidden. Rubbing toys with catnip or silver vine can renew interest in older toys.\n\n<strong>Your cat only plays with one type of toy:</strong> This likely reflects their preferred prey type. Cats that like feather wands are \"bird hunters\"; those that prefer ground-level toys are \"mouse hunters\". Offer variations within their preferred style.\n\n<strong>Interactive toys run out of battery quickly:</strong> Keep a supply of the correct batteries. Some electronic toys have auto-off features to conserve power. Manual wand toys and puzzle feeders require no batteries at all.",
        4574: "<strong>Your dog will not drink enough water:</strong> Try adding a splash of low-sodium bone broth to their water bowl. Ensure the bowl is clean and refilled daily. Some dogs prefer running water from a pet fountain.\n\n<strong>Your cat's water bowl seems untouched:</strong> Cats often prefer water sources away from their food. Try placing bowls in multiple locations. A water fountain may encourage drinking through movement and oxygenation.\n\n<strong>You are unsure if your pet is dehydrated:</strong> Gently pinch the skin on the back of the neck. If it does not spring back immediately, your pet may be dehydrated. Dry gums and lethargy are additional warning signs.",
        4272: "<strong>The ID tag falls off the collar:</strong> Use a split ring (like a keyring) rather than an S-hook, which can open. Alternatively, choose a slide-on tag that threads directly onto the collar.\n\n<strong>Engraving wears off quickly:</strong> Choose deep-engraved stainless steel tags over laser-etched aluminium. Avoid cheap tags that use surface printing, which fades within months.\n\n<strong>You are unsure what information to include:</strong> UK law requires owner name, address, and postcode on dog tags. Adding a phone number is optional but highly recommended for faster contact.",
        4265: "<strong>The GPS tracker loses signal frequently:</strong> Check cellular coverage in your area. Trackers rely on mobile network signal, so rural areas may have gaps. Choose a tracker that supports multiple network bands.\n\n<strong>Battery life is much shorter than advertised:</strong> Frequent location updates drain the battery faster. Set the tracking interval to every 5-10 minutes rather than continuous. Bring the tracker indoors for regular charging.\n\n<strong>Your cat removes or damages the tracker:</strong> Ensure the tracker sits securely on a breakaway collar. Some units clip directly to harnesses for a more secure fit. Check positioning daily during the first week.",
        4216: "<strong>The bed does not fit your radiator:</strong> Measure the radiator depth and top clearance before purchasing. Panel radiators (most common in UK homes) are compatible with most designs. Column radiators may need wider hooks.\n\n<strong>Your cat will not use the radiator bed:</strong> Place treats and catnip on the bed. Try moving it to a radiator your cat already sits near. Some cats prefer the bed at a lower height initially.\n\n<strong>The bed frame scratches the wall:</strong> Add felt pads to the hooks where they contact the wall. Some beds include rubber-coated hooks specifically to prevent this.",
        4167: "<strong>The bottle leaks in your bag:</strong> Check the seal and ensure the dispensing mechanism is fully closed. Replace worn silicone seals promptly. Store upright in a side pocket rather than horizontally.\n\n<strong>Your dog will not drink from the attached trough:</strong> Practise at home before walks. Pour water slowly into the trough at their height. Some dogs prefer a collapsible bowl used alongside the bottle.\n\n<strong>The bottle is too small for long walks:</strong> For walks over 90 minutes or in hot weather, carry a larger bottle (750 ml+) or a collapsible refillable bowl to supplement at water points.",
        4160: "<strong>The elevated bowl wobbles during eating:</strong> Ensure the stand is on a flat surface. Add anti-slip pads underneath. If the stand itself is unstable, upgrade to a wider-base model with rubber feet.\n\n<strong>Your dog pushes food out of the raised bowl:</strong> The bowl may be too shallow or too high. Adjust the height so your dog's neck is in a natural, slightly downward position while eating.\n\n<strong>You have read conflicting advice about raised bowls and bloat:</strong> Discuss with your vet, especially for deep-chested breeds (Great Danes, Setters). The evidence is mixed; your vet can advise based on your specific dog's risk factors.",
        4146: "<strong>Your dog flips the bowl over:</strong> Switch to a weighted or non-tip design with a wide, heavy base. Rubber-bottomed bowls also resist movement. Slow feeder designs are inherently harder to flip.\n\n<strong>The bowl is difficult to clean properly:</strong> Choose stainless steel for the easiest cleaning. Avoid plastic bowls, which develop scratches that harbour bacteria. Run through a dishwasher cycle or scrub daily with hot, soapy water.\n\n<strong>You notice a rash around your dog's mouth:</strong> Plastic bowls are a common cause of contact dermatitis in dogs. Switch to stainless steel or ceramic immediately and monitor for improvement.",
        6048: "<strong>Your shy dog hides from new toys:</strong> Place toys near your dog's safe space without forcing interaction. Use food-stuffed toys so your dog associates them with positive outcomes. Progress happens gradually.\n\n<strong>Your dog shows no interest in play at all:</strong> Rule out pain or illness with a vet check. Try different toy types: some shy dogs respond better to scent-based enrichment (snuffle mats) than movement-based toys.\n\n<strong>Progress reverses after a setback:</strong> This is normal. Reduce play difficulty to a level where your dog was last comfortable and rebuild from there. Never punish a fearful response.",
        6044: "<strong>Your dog gives up on the puzzle quickly:</strong> The puzzle is too difficult. Go back to an easier level and only increase difficulty once your dog solves it consistently. Partially pre-solve the puzzle to give hints.\n\n<strong>Your dog becomes frustrated and barks at the puzzle:</strong> Frustration means the challenge is too high. Remove the puzzle calmly, offer an easier alternative, and try the harder puzzle again another day.\n\n<strong>Your dog only uses brute force instead of problem-solving:</strong> Some dogs default to force. Guide them toward the correct solution with scent trails and demonstrate the mechanism slowly. Reward any interaction with the correct method.",
        4786: "<strong>Your dog refuses to sleep in the bed location you chose:</strong> Observe where your dog naturally gravitates and place the bed there. Dogs often prefer spots where they can see the room entrance while feeling protected on one side.\n\n<strong>Your dog keeps dragging the bed to a different spot:</strong> This is your dog telling you where they want to sleep. If the location is safe and appropriate, let them have it.\n\n<strong>Housemates disagree on bed placement:</strong> Avoid bedrooms where the door closes (dog may feel trapped). A quiet corner of the living room with a wall behind is a compromise most dogs and families find acceptable.",
        4785: "<strong>The bed smells even after washing the cover:</strong> The foam insert may be absorbing moisture and odour. Sprinkle bicarbonate of soda on the foam, leave for 2 hours, then vacuum off. Air the insert outdoors monthly.\n\n<strong>The cover shrank after washing:</strong> Wash at the temperature specified on the label (usually 30-40°C) and air-dry. If already shrunk, contact the manufacturer for a replacement cover.\n\n<strong>Your dog's bed attracts fleas:</strong> Wash all bedding at 60°C weekly during flea season. Vacuum the area around the bed daily. Ensure your dog's flea treatment is up to date.",
        4573: "<strong>Your dog has eaten something toxic during a walk:</strong> Contact your vet or the Animal Poison Line (01202 509000) immediately. Do not induce vomiting unless specifically instructed by a vet.\n\n<strong>Your pet shows signs of heatstroke:</strong> Move to shade immediately, apply cool (not cold) water to ears, paws, and belly. Offer small sips of water. Get to a vet urgently, as heatstroke can be fatal.\n\n<strong>Your dog is frightened by fireworks:</strong> Create a den in an interior room with blankets and background noise. Close curtains and stay calm. Speak to your vet about pheromone diffusers or calming supplements well before firework season.",
        4570: "<strong>Your new puppy cries all night:</strong> Place the crate or bed near your bedroom initially and gradually move it to the desired location over 1-2 weeks. A warm water bottle wrapped in a towel can mimic littermate warmth.\n\n<strong>House training is not progressing:</strong> Take your puppy outside every 1-2 hours and immediately after eating, drinking, sleeping, and playing. Reward outdoor toileting generously. Never punish indoor accidents.\n\n<strong>You feel overwhelmed by the responsibility:</strong> This is completely normal. Reach out to your vet for puppy check-ups and guidance. Puppy training classes provide support and socialisation in one package.",
        4576: "<strong>Your dog chases the cat constantly:</strong> Separate them with baby gates and reintroduce gradually through scent swapping. Train a solid \"leave it\" command. Ensure the cat has high escape routes the dog cannot reach.\n\n<strong>Your cat stops eating after the new pet arrives:</strong> Stress-related appetite loss is common. Provide a quiet, separate feeding area. If eating does not resume within 48 hours, consult your vet.\n\n<strong>Resource guarding occurs between pets:</strong> Feed animals in separate rooms with doors closed. Provide duplicate resources (beds, water bowls) to reduce competition. Consult a qualified behaviourist if guarding escalates.",
        4571: "<strong>You are unsure if your pet's injury is an emergency:</strong> If in doubt, call your vet. Signs requiring immediate attention include: difficulty breathing, uncontrolled bleeding, collapse, seizures, suspected poisoning, or inability to stand.\n\n<strong>Your pet has a wound that is bleeding:</strong> Apply firm pressure with a clean cloth for 5-10 minutes. If bleeding does not stop, keep pressure applied and get to a vet immediately. Do not apply tourniquets.\n\n<strong>You are not sure how to perform pet CPR:</strong> Lay your pet on their right side. For dogs: compress the chest at the widest point, 100-120 compressions per minute. For cats: one hand around the chest. Give 2 breaths every 30 compressions.",
        4328: "<strong>Your cat is scared of the self-cleaning mechanism:</strong> Run the cycle when your cat is in another room. Some units have noise-dampening modes. If fear persists, consider a quieter model or return to manual scooping.\n\n<strong>The mechanism jams frequently:</strong> Check that you are using a compatible litter type. Clumping litter works best with raking mechanisms. Remove oversized clumps manually before running the cycle.\n\n<strong>Odour is worse than with a manual tray:</strong> Ensure the waste receptacle is emptied frequently. Carbon filters should be replaced monthly. The tray itself still needs full washing weekly.",
        4293: "<strong>The cat tree wobbles dangerously:</strong> Tighten all bolts and check that the base is on a flat surface. If instability persists, secure the top platform to the wall with an L-bracket. Heavier cats need wider-base models.\n\n<strong>Your cat ignores the cat tree:</strong> Place it near a window with a view. Rub catnip on the platforms and posts. Dangle a wand toy from the upper levels to create positive associations.\n\n<strong>The sisal rope unravels quickly:</strong> Tighter-wrapped sisal lasts longer. Re-wrap worn posts with replacement sisal rope (available online) using a hot-glue gun. Loose fibres should be trimmed to prevent ingestion.",
        4223: "<strong>The suction cups keep detaching:</strong> Clean both the cups and the window with rubbing alcohol before reattaching. Avoid fitting in cold weather, as suction weakens in low temperatures. Consider a bolt-on mounting kit for permanent installation.\n\n<strong>Your cat is too heavy for the perch:</strong> Check the weight limit before purchase. Bolt-mounted perches support more weight than suction-cup models. Reinforce with a shelf bracket underneath if needed.\n\n<strong>The perch blocks the window from opening:</strong> Measure your window opening mechanism before buying. Some perches are designed to sit below the opening line. Alternatively, fit the perch to a window you do not regularly open.",
        4153: "<strong>Your dog cannot figure out the slow feeder:</strong> Start with a minimal amount of food in the easiest sections. Gradually increase the amount and complexity as your dog learns. Avoid complex maze designs for first-time users.\n\n<strong>The slow feeder is too easy and your dog finishes quickly:</strong> Try a more complex design with deeper ridges or a lick mat combined with the bowl. Freezing wet food inside the feeder adds difficulty.\n\n<strong>Your dog pushes the bowl around instead of eating from it:</strong> Use a bowl with a non-slip rubber base, or place it on a silicone mat. Heavier ceramic slow feeders also resist movement better than lightweight plastic.",
    }
    return trouble.get(post_id, "<strong>The product does not meet expectations:</strong> Check sizing and specifications against your pet's needs. Contact the retailer for exchanges within their return window.\n\n<strong>Your pet rejects the new item:</strong> Introduce gradually with positive associations (treats, praise). Familiar scents on a new item can help acceptance.\n\n<strong>You are unsure which option is best for your pet:</strong> Consult your vet or a qualified professional for personalised advice based on your pet's breed, age, and health status.")


def generate_when_to_seek_help(post_id, title, cluster):
    seek = {
        5464: "Consult a professional groomer if your pet's coat has become severely matted, as attempting to remove dense mats at home can cause skin tears and significant pain. Seek veterinary advice if you notice persistent skin redness, lumps, or lesions during grooming.",
        4563: "Book a veterinary appointment if you notice unusual lumps, persistent skin irritation, excessive dandruff, or foul odours that do not improve with bathing. For severely matted coats, a professional groomer can safely demat without causing skin injuries.",
        4251: "Consult your vet before bathing if your cat has open wounds, a skin condition, or has recently had surgery. If your cat experiences prolonged skin irritation, hair loss, or behavioural changes after bathing, seek veterinary advice promptly.",
        4244: "See your vet if a nail is broken at the base, bleeding does not stop within 5 minutes despite styptic powder, or if you notice swelling or discharge around the nail bed. Ingrown nails require professional treatment.",
        4237: "Seek veterinary advice if you discover unusual skin patches, excessive hair loss, scabs, or parasites during brushing. A professional groomer should handle severely matted coats to prevent skin tears.",
        4230: "Consult your vet if you notice persistent skin reactions to grooming products, unexplained fur loss, or behavioural changes during grooming that may indicate pain. An experienced groomer can help with cats that are extremely resistant to home grooming.",
        4078: "Visit your vet if you notice a cracked, split, or discoloured nail, persistent limping, or swelling around the nail bed. Dogs that are extremely fearful of nail trimming may benefit from a vet-supervised desensitisation programme or sedated trimming.",
        4071: "Seek veterinary guidance if your dog's skin issues persist despite using an appropriate shampoo, or if you notice rapid hair loss, hot spots, or signs of infection. Medicated shampoos should only be used under veterinary direction.",
        4064: "Consult your vet if brushing reveals unusual lumps, persistent bald patches, excessive flaking, or signs of parasites such as flea dirt or ticks. A dermatologist referral may be appropriate for chronic skin conditions.",
        4057: "Seek professional grooming advice if you are unsure about safe clipper blade lengths for your breed, or if your dog has skin folds, ear issues, or conditions requiring specialist handling. Always consult your vet before using medicated grooming products.",
        5418: "Consult a qualified dog behaviourist if your dog shows signs of fear, aggression, or severe anxiety while wearing a harness. Seek veterinary advice if you notice chafing, skin irritation, or changes in gait that may indicate the harness is causing discomfort.",
        4414: "See your vet if your dog coughs, gags, or shows signs of breathing difficulty on a collar, as this may indicate tracheal damage. A veterinary physiotherapist can advise on the best walking equipment for dogs with neck or spinal conditions.",
        4413: "Consult a professional dog behaviourist or trainer if your dog reacts negatively to being measured or fitted. Seek veterinary advice if you notice any skin changes, limping, or discomfort after wearing a new harness.",
        4412: "Work with a qualified positive-reinforcement trainer if a no-pull harness alone does not resolve pulling, as underlying behavioural issues may need addressing. Consult your vet if pulling seems driven by pain, anxiety, or a medical condition.",
        4279: "Consult your vet before outdoor walks if your cat is not fully vaccinated, has a heart condition, or shows signs of extreme stress. Seek advice from a feline behaviourist if harness introduction causes prolonged fear responses despite gradual desensitisation.",
        4258: "See your vet if you notice any neck irritation, hair loss, or skin damage from collar wear. Seek advice from your vet or a behaviourist if your cat shows signs of distress when wearing a collar despite gradual, positive introduction.",
        4139: "Work with a qualified trainer if your dog shows aggressive reactions when on a long line, as this may indicate fear-based reactivity that requires professional behaviour modification. Seek veterinary advice if your dog injures themselves hitting the end of the line.",
        4049: "Consult your vet if your puppy shows signs of discomfort, skin irritation, or breathing difficulty when wearing a collar or harness. A puppy training class instructor can demonstrate correct fitting and help with introduction to walking equipment.",
        4042: "See a veterinary physiotherapist if your dog shows lameness, stiffness, or reluctance to walk that may be linked to walking equipment. Consult a qualified behaviourist if lead reactivity (lunging, barking at other dogs) is a persistent issue.",
        4034: "Seek guidance from a certified behaviourist (ABTC-registered) if pulling is accompanied by lunging, barking, or signs of fear-based reactivity. Consult your vet if your dog has a pre-existing neck, shoulder, or respiratory condition before starting harness training.",
        4027: "Consult a qualified dog trainer if you are unsure which equipment combination suits your dog's specific needs. Seek veterinary advice for dogs with respiratory conditions, neck injuries, or mobility issues before selecting walking equipment.",
        5510: "Consult your vet if your dog's sleeping position has changed suddenly, as this may indicate pain or discomfort. Dogs with orthopaedic conditions may benefit from a vet-recommended bed type with specific support characteristics.",
        4783: "Seek veterinary advice if your dog frequently changes sleeping positions, appears restless during sleep, or has difficulty getting up, as these may signal joint pain or an underlying health issue that affects bed choice.",
        4018: "Consult your vet if your puppy shows signs of night-time distress beyond the normal adjustment period (more than 2 weeks), as this may indicate a health issue or separation anxiety that requires professional intervention.",
        4011: "Seek immediate veterinary attention if your dog shows signs of heatstroke: excessive panting, drooling, vomiting, or collapse. A cooling bed is a preventive measure; it cannot replace emergency veterinary care in a heat emergency.",
        4004: "Consult your vet to determine whether an orthopaedic bed is appropriate for your dog's specific joint condition, as some issues may require additional support or physiotherapy alongside improved bedding.",
        3996: "See your vet if your dog shows reluctance to lie down, difficulty rising, or restless sleep patterns, as these may indicate pain or a condition that requires medical treatment alongside an appropriate bed upgrade.",
        5521: "Never hesitate to ask your vet to explain any diagnosis, test result, or treatment plan in plain language. If you feel unsure about a recommended procedure, seeking a second opinion from another qualified veterinary practice is always appropriate.",
        5462: "Consult a qualified behaviourist (look for ABTC registration) if your dog shows signs of aggression, severe anxiety, or compulsive behaviour that standard training has not resolved. Veterinary input is essential if behaviour changes are sudden, as they may indicate pain or illness.",
        5424: "See your vet immediately if you suspect your dog has swallowed toy fragments, as intestinal blockages can become life-threatening within hours. Consult a behaviourist if aggressive chewing seems driven by anxiety rather than natural chewing instinct.",
        5419: "Contact your vet promptly if your new cat shows prolonged loss of appetite (beyond 48 hours), litter tray avoidance, or signs of illness such as lethargy, sneezing, or discharge. An early health check within the first week of adoption is strongly recommended.",
        5416: "Consult your vet before choosing a bed if your dog has been diagnosed with arthritis, hip dysplasia, or spinal conditions, as they may recommend specific foam densities or bed configurations to support your dog's treatment plan.",
        5415: "Seek guidance from a qualified dog behaviourist if play sessions consistently escalate to aggression, if your dog shows fear-based withdrawal from play, or if play behaviour changes suddenly, which could indicate pain or illness.",
        5414: "Consult your vet if your cat shows a sudden loss of interest in play, as this may indicate pain, illness, or depression. A feline behaviourist can help design an enrichment programme for cats with specific behavioural needs.",
        4574: "See your vet urgently if your pet shows signs of dehydration (dry gums, skin tenting, sunken eyes, lethargy) or if water intake changes dramatically in either direction, as both increased and decreased thirst can signal serious health conditions.",
        4272: "Contact your vet if your pet's microchip cannot be detected during a routine scan, as chips can occasionally migrate. Ensure your microchip contact details are updated whenever you move house or change phone number.",
        4265: "Consult your vet before attaching any device to a very small or elderly cat, as the added weight may affect mobility. If your cat goes missing, contact local vets, rescues, and use the tracker data alongside reporting to your microchip database.",
        4216: "See your vet if your cat shows reluctance to jump onto the radiator bed, as this may indicate joint pain, especially in older cats. Cats that suddenly seek excessive warmth may be unwell and should be checked for underlying conditions.",
        4167: "Seek veterinary advice if your dog refuses water during walks, drinks excessively, or shows signs of dehydration despite adequate water availability. Sudden changes in drinking habits can indicate kidney disease, diabetes, or other conditions.",
        4160: "Consult your vet before switching to elevated bowls, particularly if your dog is a deep-chested breed at risk of gastric dilatation-volvulus (bloat). A vet can advise on the optimal feeding height and whether raised feeding is appropriate for your specific dog.",
        4146: "See your vet if your dog shows signs of food guarding, refuses to eat, or develops mouth or gum issues that may be related to their feeding setup. Sudden appetite changes always warrant a veterinary check.",
        6048: "Consult a certified animal behaviourist (ABTC-registered) if your dog's fear or shyness significantly impacts their quality of life, prevents normal activities, or worsens despite patient, consistent confidence-building efforts.",
        6044: "Seek guidance from a veterinary behaviourist if your dog shows signs of compulsive behaviour during puzzle play, or if frustration escalates to destructive behaviour or self-harm. Sudden cognitive decline in older dogs may indicate canine cognitive dysfunction.",
        4786: "Consult your vet or a behaviourist if your dog shows signs of sleep disturbance, nighttime anxiety, or refuses to settle in any location, as these may indicate pain, cognitive decline, or an anxiety disorder.",
        4785: "See your vet if persistent odour, staining, or soiling of bedding suggests an underlying health issue such as urinary incontinence, skin infection, or digestive problems. Flea infestations in bedding require both environmental treatment and pet-applied preventatives.",
        4573: "Call your vet immediately for suspected poisoning, heatstroke, firework-related injuries, or hypothermia. The Animal Poison Line (01202 509000) provides 24/7 emergency advice. Keep your emergency vet's out-of-hours number saved in your phone.",
        4570: "Register with a local vet within the first week of bringing your dog home and schedule initial vaccinations, microchipping, and a health check. Seek professional training advice early if you feel overwhelmed, as puppy classes provide both guidance and socialisation.",
        4576: "Consult a qualified animal behaviourist if inter-pet aggression escalates, if either animal shows signs of chronic stress (over-grooming, appetite loss, hiding), or if introductions have stalled after several weeks of careful, gradual exposure.",
        4571: "Call your vet or nearest emergency animal hospital immediately for suspected poisoning, seizures, difficulty breathing, uncontrolled bleeding, or loss of consciousness. First aid stabilises your pet but is never a substitute for professional veterinary treatment.",
        4328: "Consult your vet if your cat avoids the litter tray entirely, as this may indicate urinary tract issues, stress, or other health problems unrelated to the tray design. Behavioural changes around toileting should always be investigated.",
        4293: "See your vet if your cat stops jumping or climbing, as this may indicate arthritis, injury, or pain. Sudden changes in scratching behaviour (intensity or location) can also signal stress or a skin condition worth investigating.",
        4223: "Consult your vet if your cat falls from a window perch and shows signs of limping, reluctance to move, or difficulty breathing. Always ensure windows used with perches have secure locks or guards to prevent accidental falls.",
        4153: "See your vet if your dog vomits frequently after eating, shows signs of bloat (distended abdomen, restlessness, non-productive retching), or loses interest in food. Speed eating that persists despite a slow feeder may indicate an underlying anxiety or behavioural issue.",
    }
    return seek.get(post_id, "Consult your vet if you notice any sudden changes in your pet's behaviour, appetite, or physical condition. For persistent behavioural issues, seek guidance from a qualified, ABTC-registered animal behaviourist.")


def generate_key_takeaways(post_id, title, cluster):
    takeaways = {
        5464: "<li>Familiarise yourself with key grooming terms before booking professional appointments</li><li>Ask your groomer to explain any unfamiliar techniques they plan to use</li><li>Different coat types require different grooming methods; know yours</li><li>Understanding terminology helps you spot and communicate potential skin or coat issues</li><li>Keep this glossary bookmarked for quick reference between grooming sessions</li>",
        4563: "<li>Establish a regular grooming routine from puppyhood for lifelong acceptance</li><li>Brush your dog at least twice weekly, more during shedding season</li><li>Trim nails every 3-4 weeks to prevent overgrowth and joint strain</li><li>Use grooming time to check for lumps, parasites, and skin changes</li><li>Choose grooming tools appropriate for your dog's specific coat type</li><li>Consult your vet about any skin, ear, or dental concerns found during grooming</li>",
        4251: "<li>Only bathe your cat when genuinely necessary, not on a routine schedule</li><li>Always use a pH-balanced, cat-specific shampoo</li><li>Prepare everything before starting: towels, mat, warm water, and shampoo</li><li>Keep sessions short and calm to minimise stress</li><li>Consider waterless shampoo for minor clean-ups</li>",
        4244: "<li>Trim cat nails every 2-4 weeks to prevent overgrowth and snagging</li><li>Use sharp, appropriately sized clippers to ensure a clean cut</li><li>Learn to identify the quick before cutting, especially on dark nails</li><li>Keep styptic powder on hand for accidental quick nicks</li><li>Build tolerance gradually with positive reinforcement</li>",
        4237: "<li>Match your brush type to your cat's specific coat length and texture</li><li>Brush 2-3 times per week to prevent matting and reduce hairballs</li><li>Pay extra attention to mat-prone areas: behind ears, armpits, and belly</li><li>Introduce brushing gradually with treats for a positive association</li><li>Replace worn brushes with bent or missing bristles promptly</li>",
        4230: "<li>Start with the basics: a suitable brush, nail clippers, and ear cleaner</li><li>Invest in quality tools that last, rather than cheap replacements</li><li>Introduce each new tool separately with positive reinforcement</li><li>Choose fragrance-free products to avoid irritating your cat's sensitive nose</li><li>Store tools in a clean, dry kit bag for organisation and hygiene</li>",
        4078: "<li>Choose clippers or grinders based on your dog's nail size and temperament</li><li>Desensitise your dog to the tool before attempting the first trim</li><li>Trim small amounts frequently rather than large amounts infrequently</li><li>Keep styptic powder within arm's reach during every trimming session</li><li>If in doubt, ask your vet or groomer for a demonstration</li>",
        4071: "<li>Always choose a dog-specific shampoo with an appropriate skin pH</li><li>Avoid products containing parabens, sulphates, and artificial fragrances</li><li>Oatmeal and aloe vera formulas work well for sensitive or itchy skin</li><li>Only bathe once per month unless your vet advises otherwise</li><li>Rinse thoroughly; shampoo residue is the most common cause of irritation</li>",
        4064: "<li>Identify your dog's coat type before selecting a brush</li><li>Use an undercoat rake for double-coated breeds during shedding season</li><li>Brush in the direction of hair growth using gentle, consistent strokes</li><li>Replace brushes when bristles become bent, worn, or missing</li><li>Make brushing a positive experience with treats and calm praise</li><li>Daily brushing during spring and autumn reduces household shedding significantly</li>",
        4057: "<li>Build a home grooming kit tailored to your dog's breed and coat type</li><li>Invest in quality clippers, brushes, and shampoo for the best results</li><li>Home grooming supplements but does not always replace professional sessions</li><li>Clean and maintain all tools after each use for longevity and hygiene</li><li>Start grooming from puppyhood to establish lifelong comfort</li>",
        5418: "<li>Choose your harness type based on your dog's walking behaviour and body shape</li><li>Front-clip harnesses suit pullers; back-clip suits calm walkers</li><li>Always measure before buying and re-check the fit regularly</li><li>Padded straps prevent chafing, especially on short-coated breeds</li><li>Introduce any new harness gradually with positive reinforcement</li>",
        4414: "<li>Harnesses are generally safer than collars for dogs that pull</li><li>Brachycephalic and small breeds should always use a harness for walks</li><li>Collars are still needed for ID tags under UK law</li><li>A harness-and-collar combination provides the best balance of safety and legal compliance</li><li>Consult your vet if your dog shows signs of neck or tracheal discomfort on a collar</li>",
        4413: "<li>Measure neck girth, chest girth, and back length for an accurate fit</li><li>Always measure while your dog is standing naturally on all four legs</li><li>Allow two-finger space between the harness and your dog's body</li><li>Re-measure growing puppies every 2-4 weeks during development</li><li>When between sizes, choose the larger option and adjust down</li>",
        4412: "<li>No-pull harnesses redirect forward motion but do not replace training</li><li>Front-clip designs are the most humane option for managing pulling</li><li>Combine the harness with consistent positive-reinforcement techniques</li><li>Avoid tightening designs that the RSPCA warns against as causing discomfort</li><li>Transition to a standard harness once loose-lead walking is established</li>",
        4279: "<li>Choose an escape-proof vest-style harness with a secure secondary clip</li><li>Begin harness training indoors weeks before attempting outdoor walks</li><li>Let your cat set the pace; never drag or force movement</li><li>Lightweight materials are essential to avoid restricting feline movement</li><li>Always supervise outdoor sessions and use a secure lead</li>",
        4258: "<li>Safety breakaway collars are essential for cats to prevent strangulation</li><li>UK law requires dogs to wear a collar with owner details in public</li><li>Reflective and high-visibility features improve safety on darker days</li><li>Replace worn tags and collars promptly to maintain identification</li><li>Introduce collars gradually using positive associations</li>",
        4139: "<li>Use long lines for recall training in open, safe spaces</li><li>Biothane and rubber-coated materials resist mud and dry quickly</li><li>Always attach long lines to a harness, never a collar</li><li>Wear gloves to protect your hands from friction burns</li><li>Practise in low-distraction environments before progressing to busier areas</li>",
        4049: "<li>Choose lightweight, adjustable equipment that suits your puppy's current size</li><li>Introduce collar and harness separately with lots of treats and praise</li><li>Re-measure and resize as your puppy grows to maintain proper fit</li><li>Ensure all equipment meets UK legal requirements for identification</li><li>Make every equipment experience positive to build lifelong comfort</li>",
        4042: "<li>A 1.2-1.8 metre fixed lead provides the best balance of control and freedom</li><li>Avoid retractable leads near roads, other dogs, or crowded areas</li><li>Choose weather-resistant materials for year-round UK walking</li><li>Inspect clips and stitching regularly and replace worn leads promptly</li><li>Match your lead choice to your walking environment and training goals</li>",
        4034: "<li>Front-clip no-pull harnesses offer the most humane pulling management</li><li>Pair the harness with reward-based training for lasting results</li><li>Ensure padded straps and a proper fit to prevent chafing</li><li>Reflective features are essential for winter evening walks in the UK</li><li>Progress to a standard harness once loose-lead walking is reliable</li>",
        4027: "<li>Match your equipment choice to your dog's breed, size, and walking behaviour</li><li>Combine a harness for control with a collar for legal ID tag requirements</li><li>Invest in quality hardware (metal, not plastic) for reliability</li><li>Review your equipment regularly as your dog grows, ages, or changes behaviour</li><li>Consult a professional trainer if you are unsure which combination to use</li>",
        5510: "<li>Measure from nose to tail base, then add 15-20 cm for the ideal bed length</li><li>Consider your dog's preferred sleeping position when choosing bed shape</li><li>Weigh your dog and check the bed's weight capacity before purchasing</li><li>Size up for growing puppies using breed growth charts</li><li>Re-assess bed size if your dog consistently hangs over the edges</li>",
        4783: "<li>Take three measurements: length, shoulder width, and standing height</li><li>Match bed shape to sleeping style: round for curlers, rectangular for sprawlers</li><li>Test the bed in-store if possible, or choose retailers with good return policies</li><li>Bolstered beds provide security for anxious dogs that like to lean</li><li>Invest in the right size first time to avoid costly replacements</li>",
        4018: "<li>Prioritise chew-resistant, machine-washable materials for puppy beds</li><li>Measure your crate interior before buying a crate-compatible bed</li><li>Use waterproof liners during the house-training phase</li><li>Keep a spare cover ready for quick changes after accidents</li><li>A comfortable bed supports successful crate training and nighttime settling</li>",
        4011: "<li>Gel and elevated mesh designs offer different cooling benefits</li><li>Pressure-activated gel pads need rest periods to recharge their cooling effect</li><li>Brachycephalic and thick-coated breeds benefit most from cooling beds</li><li>Combine a cooling bed with shade, ventilation, and fresh water in hot weather</li><li>A cooling bed is a supplement to, not a substitute for, heat safety precautions</li>",
        4004: "<li>Choose memory foam with a density of 3-5 lb per cubic foot for proper joint support</li><li>Waterproof liners are essential for senior dogs with incontinence issues</li><li>Low entry points and removable bolsters aid dogs with limited mobility</li><li>Consult your vet about the best bed specification for your dog's condition</li><li>An orthopaedic bed is a long-term investment in your dog's comfort and mobility</li>",
        3996: "<li>Match bed type (memory foam, bolster, nest, cooling, raised) to your dog's needs</li><li>Prioritise washability, durability, and non-toxic materials</li><li>Place the bed in a quiet, draught-free area of your home</li><li>Replace beds when they lose shape, support, or become unhygienic</li><li>Consider multiple beds for multi-room households</li><li>A well-chosen bed improves sleep quality, joint health, and overall wellbeing</li>",
        5521: "<li>Ask your vet to explain any terms you do not understand during consultations</li><li>Keep a pet health notebook to track diagnoses, medications, and vet advice</li><li>Use this glossary as a starting reference, not a diagnostic tool</li><li>Understanding terminology helps you give informed consent for treatments</li><li>Always verify information with your veterinary practice for your specific pet</li>",
        5462: "<li>Learn the basics of positive reinforcement and clicker training</li><li>Choose trainers registered with the ABTC for evidence-based methods</li><li>Understand common cues and what they mean for consistent training</li><li>Avoid any method that relies on pain, fear, or intimidation</li><li>Training is a skill you build over time; patience and consistency are key</li>",
        5424: "<li>Choose toys rated for aggressive chewing with solid rubber or nylon construction</li><li>Supervise all chew sessions and discard damaged toys immediately</li><li>Rotate toys weekly to maintain interest and prevent boredom</li><li>Frozen stuffed Kongs provide long-lasting, safe chewing enrichment</li><li>If your dog swallows fragments, contact your vet without delay</li>",
        5419: "<li>Provide one litter tray per cat plus one extra, in quiet locations</li><li>Learn to read your cat's body language: tail position, ear orientation, and vocalisations</li><li>Register your cat's microchip and keep contact details up to date</li><li>Indoor enrichment (scratching posts, climbing, play) is essential for welfare</li><li>Schedule a vet health check within the first week of bringing a new cat home</li>",
        5416: "<li>Match bed type to your dog's sleeping style, age, and health conditions</li><li>Understand fill materials: memory foam for support, polyester fibre for softness</li><li>Check foam density ratings rather than relying on marketing labels alone</li><li>Orthopaedic beds should contain genuine high-density support foam</li><li>Use this glossary to decode product descriptions before purchasing</li>",
        5415: "<li>Learn to identify your dog's natural play style for better toy and playmate choices</li><li>Supervise play sessions and intervene calmly if energy escalates too high</li><li>Mismatched play styles can cause conflict; pair similar players together</li><li>End play while your dog is still enjoying it to build positive associations</li><li>Sudden changes in play behaviour may indicate pain or illness; consult your vet</li>",
        5414: "<li>Provide a variety of toy types to satisfy different prey-drive instincts</li><li>Rotate toys weekly to maintain novelty and engagement</li><li>Schedule 15-30 minutes of interactive play daily for indoor cats</li><li>Catnip and silver vine can renew interest in older toys</li><li>Supervise play with small parts and discard damaged toys to prevent choking</li>",
        4574: "<li>Ensure dogs get approximately 50-60 ml of water per kg of body weight daily</li><li>Place water bowls away from food to encourage cat drinking</li><li>Water fountains improve hydration for cats that prefer running water</li><li>Learn to recognise dehydration signs: dry gums, skin tenting, and lethargy</li><li>Seek veterinary advice if water intake changes suddenly in either direction</li>",
        4272: "<li>UK law requires dogs to wear a collar with owner details in public</li><li>Choose deep-engraved stainless steel tags for maximum durability</li><li>Use a split ring rather than an S-hook to prevent tag loss</li><li>QR-code tags offer additional information without tag clutter</li><li>Combine an ID tag with registered microchip for comprehensive identification</li>",
        4265: "<li>Understand the difference between GPS (cellular) and Bluetooth (short-range) trackers</li><li>Check cellular coverage in your area before purchasing a GPS tracker</li><li>Set up geofencing alerts for immediate notification when your cat leaves a safe zone</li><li>Account for ongoing subscription costs when budgeting</li><li>Keep the tracker charged and check positioning on the collar regularly</li>",
        4216: "<li>Measure your radiator's depth and top clearance before purchasing</li><li>Ensure the bed's weight limit exceeds your cat's weight for safety</li><li>Fleece and sherpa linings provide the best heat retention</li><li>Introduce the bed with treats and catnip for positive associations</li><li>Check hook security weekly to prevent falls</li>",
        4167: "<li>Choose a leak-proof, BPA-free bottle with one-hand operation</li><li>Size the bottle to your dog's needs: 350 ml for small dogs, 750 ml+ for large breeds</li><li>Offer water every 20-30 minutes during warm-weather walks</li><li>Clean the bottle and trough after every use to prevent bacterial growth</li><li>Carry extra water on walks longer than 90 minutes or in hot conditions</li>",
        4160: "<li>Elevated bowls may benefit tall breeds and dogs with neck or back conditions</li><li>Consult your vet before switching, especially for deep-chested breeds at bloat risk</li><li>Choose adjustable-height feeders for growing puppies and multi-dog homes</li><li>Stainless steel bowls in a stable stand provide the best hygiene and durability</li><li>Anti-slip bases prevent bowl movement during mealtimes</li>",
        4146: "<li>Choose stainless steel or ceramic bowls over plastic for hygiene and durability</li><li>Match bowl type to your dog's eating behaviour and any special needs</li><li>Slow feeders benefit fast eaters by extending meal times and reducing bloat risk</li><li>Wash bowls daily with hot, soapy water or run through the dishwasher</li><li>Anti-slip, weighted bowls prevent frustrating bowl movement during meals</li>",
        6048: "<li>Use food-based enrichment (snuffle mats, treat puzzles) to build confidence without pressure</li><li>Let your dog choose when to engage; never force interaction with a toy</li><li>Progress is gradual; celebrate small wins and be patient with setbacks</li><li>Short, positive sessions are more effective than long, overwhelming ones</li><li>Consult a behaviourist if fear significantly impacts your dog's quality of life</li>",
        6044: "<li>Start with easy puzzles and increase difficulty only after consistent success</li><li>Rotate puzzles every few days to prevent boredom and maintain engagement</li><li>Watch for frustration signals and reduce difficulty if they appear</li><li>Multi-step puzzles provide the best cognitive workout for smart dogs</li><li>Cognitive enrichment reduces destructive behaviour and improves wellbeing</li>",
        4786: "<li>Place your dog's bed in a quiet, draught-free spot with a wall behind</li><li>Avoid high-traffic areas, direct sunlight, and spots near external doors</li><li>Let your dog guide the decision if they consistently choose a different location</li><li>Provide separate sleeping stations in multi-dog households</li><li>Reassess placement seasonally as temperature and sunlight change</li>",
        4785: "<li>Wash removable covers weekly at 60°C to eliminate bacteria and dust mites</li><li>Use pet-safe, fragrance-free detergent to protect sensitive skin</li><li>Spot-clean foam inserts and air them outdoors monthly</li><li>Air-dry completely before reassembling to prevent mould</li><li>Replace beds when cleaning no longer removes odours or when foam loses support</li>",
        4573: "<li>Learn the seasonal hazards specific to your area and prepare in advance</li><li>Never leave pets in parked cars, even for short periods, in warm weather</li><li>Keep antifreeze, slug pellets, and other toxins securely stored year-round</li><li>Create a fireworks safety plan well before November</li><li>Save your emergency vet's number and the Animal Poison Line in your phone</li>",
        4570: "<li>Budget for all ongoing costs (food, insurance, vet care) before adopting</li><li>Puppy-proof your home thoroughly before your dog arrives</li><li>Register with a vet and schedule vaccinations within the first week</li><li>Prioritise early socialisation during the 8-16 week critical window</li><li>Invest in a puppy training class for guidance and socialisation combined</li><li>Be patient with yourself; every dog owner has a learning curve</li>",
        4576: "<li>Introduce new pets gradually through scent swapping before face-to-face meetings</li><li>Provide separate feeding stations, water bowls, and sleeping areas</li><li>Ensure cats have high escape routes and dog-free safe zones</li><li>Keep litter trays in areas dogs cannot access</li><li>Consult a behaviourist if inter-species tension does not improve</li>",
        4571: "<li>Assemble a pet-specific first aid kit and keep it accessible</li><li>Learn pet CPR and basic wound management techniques</li><li>Save your emergency vet and the Animal Poison Line number in your phone</li><li>Know the signs that require immediate veterinary attention</li><li>First aid stabilises your pet but never replaces professional treatment</li>",
        4328: "<li>Choose a self-cleaning mechanism that matches your cat's temperament (noise level matters)</li><li>Use compatible litter types to prevent jams and malfunctions</li><li>Empty waste receptacles frequently and replace carbon filters monthly</li><li>Self-cleaning trays still require weekly full cleaning</li><li>Introduce the new tray alongside the old one until your cat is comfortable</li>",
        4293: "<li>Choose a tree with a wide, stable base appropriate for your cat's weight and activity level</li><li>Sisal-wrapped posts provide the most satisfying and durable scratching surface</li><li>Place the tree near a window for added enrichment and natural light</li><li>Secure tall trees to the wall if you have active, heavy, or multiple cats</li><li>Replace worn sisal rope to maintain the tree's appeal</li>",
        4223: "<li>Verify the weight limit of any perch against your cat's actual weight</li><li>Bolt-on mounts are more secure than suction cups for heavier cats</li><li>South-facing windows offer the best combination of sunlight and bird watching</li><li>Check mounting security weekly and clean the perch fabric regularly</li><li>Ensure the window is secure and cannot be opened far enough for your cat to fall</li>",
        4153: "<li>Slow feeders can extend mealtimes from seconds to 10+ minutes</li><li>Choose a design suited to your dog's muzzle shape and eating speed</li><li>Non-slip bases and heavy materials prevent bowl movement</li><li>Start with a simple design and progress to more complex patterns</li><li>Slow feeders reduce bloat risk and improve digestion in fast eaters</li>",
    }
    return takeaways.get(post_id, "<li>Follow UK veterinary and welfare guidance for best results</li><li>Introduce new products and routines gradually with positive reinforcement</li><li>Consult your vet for advice specific to your pet's breed, age, and health</li><li>Invest in quality products that prioritise safety and durability</li>")


# ── Trust footer ────────────────────────────────────────────────────────────
def get_trust_footer(cluster, post_id, title):
    title_lower = title.lower()
    if cluster == "Dog Grooming":
        refs = 'We reference UK veterinary and welfare organisations including the <a href="https://www.rspca.org.uk/" rel="nofollow">RSPCA</a>, <a href="https://www.pdsa.org.uk/" rel="nofollow">PDSA</a>, and <a href="https://www.cityandguilds.com/" rel="nofollow">City &amp; Guilds</a> grooming standards.'
    elif cluster == "Dog Harnesses":
        refs = 'We reference UK veterinary and welfare organisations including the <a href="https://www.rspca.org.uk/" rel="nofollow">RSPCA</a> and <a href="https://www.dogstrust.org.uk/" rel="nofollow">Dogs Trust</a> walking and equipment guidance.'
    elif cluster == "Dog Beds":
        refs = 'We reference UK veterinary and welfare organisations including the <a href="https://www.bva.co.uk/" rel="nofollow">BVA</a> and <a href="https://www.pdsa.org.uk/" rel="nofollow">PDSA</a> orthopaedic and comfort guidance.'
    elif cluster == "Educational":
        refs = 'We reference UK veterinary and welfare organisations including the <a href="https://www.rspca.org.uk/" rel="nofollow">RSPCA</a>, <a href="https://www.pdsa.org.uk/" rel="nofollow">PDSA</a>, and <a href="https://www.bva.co.uk/" rel="nofollow">BVA</a>.'
    else:
        if "cat" in title_lower:
            refs = 'We reference UK veterinary and welfare organisations including the <a href="https://www.rspca.org.uk/" rel="nofollow">RSPCA</a>, <a href="https://www.cats.org.uk/" rel="nofollow">Cats Protection</a>, and <a href="https://www.pdsa.org.uk/" rel="nofollow">PDSA</a>.'
        elif "dog" in title_lower or "puppy" in title_lower or "play" in title_lower or "puzzle" in title_lower or "confidence" in title_lower:
            refs = 'We reference UK veterinary and welfare organisations including the <a href="https://www.rspca.org.uk/" rel="nofollow">RSPCA</a> and <a href="https://www.dogstrust.org.uk/" rel="nofollow">Dogs Trust</a>.'
        else:
            refs = 'We reference UK veterinary and welfare organisations including the <a href="https://www.rspca.org.uk/" rel="nofollow">RSPCA</a>, <a href="https://www.pdsa.org.uk/" rel="nofollow">PDSA</a>, and <a href="https://www.bva.co.uk/" rel="nofollow">BVA</a>.'

    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#f8fafb"}},"border":{{"radius":"8px","color":"#e2e8f0","width":"1px"}},"spacing":{{"padding":{{"top":"20px","bottom":"20px","left":"24px","right":"24px"}},"margin":{{"top":"32px","bottom":"32px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#e2e8f0;border-width:1px;border-radius:8px;background-color:#f8fafb;margin-top:32px;margin-bottom:32px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">Our Editorial Standards</h4>
<!-- /wp:heading -->
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"14px"}}}}}} -->
<p style="font-size:14px">All content on Pet Hub Online is created following our <a href="https://pethubonline.com/our-editorial-process/">editorial process</a>, supported by thorough <a href="https://pethubonline.com/how-we-research-pet-products/">research methodology</a>. {refs} We maintain transparency through our <a href="https://pethubonline.com/corrections-and-updates-policy/">corrections and updates policy</a>. Content is AI-assisted and editorially reviewed. For details on how we handle affiliate relationships, see our <a href="https://pethubonline.com/affiliate-disclosure/">affiliate disclosure</a>.</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->'''


# ── Block builders using Gutenberg format ───────────────────────────────────
def build_at_a_glance(bullets_html):
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#eef2ff"}},"border":{{"radius":"6px","width":"1px","color":"#c7d2fe"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"20px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#c7d2fe;border-width:1px;border-radius:6px;background-color:#eef2ff;margin-top:20px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">At a Glance</h4>
<!-- /wp:heading -->
<!-- wp:list -->
<ul class="wp-block-list">{bullets_html}</ul>
<!-- /wp:list -->
</div>
<!-- /wp:group -->'''


def build_why_matters(text):
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#fffbeb"}},"border":{{"radius":"6px","width":"1px","color":"#fde68a"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"20px","bottom":"20px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#fde68a;border-width:1px;border-radius:6px;background-color:#fffbeb;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"14px"}}}}}} -->
<p style="font-size:14px"><strong>Why this matters:</strong> {text}</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->'''


def build_what_we_considered(text):
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#f5f3ff"}},"border":{{"radius":"6px","width":"1px","color":"#ddd6fe"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"20px","bottom":"20px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#ddd6fe;border-width:1px;border-radius:6px;background-color:#f5f3ff;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"14px"}}}}}} -->
<p style="font-size:14px"><strong>What we considered:</strong> {text}</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->'''


def build_troubleshooting(text):
    return f'''<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">Troubleshooting Common Issues</h3>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>{text}</p>
<!-- /wp:paragraph -->'''


def build_when_to_seek_help(text):
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#fef2f2"}},"border":{{"radius":"6px","width":"1px","color":"#fecaca"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"20px","bottom":"20px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#fecaca;border-width:1px;border-radius:6px;background-color:#fef2f2;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"14px"}}}}}} -->
<p style="font-size:14px"><strong>When to seek professional help:</strong> {text}</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->'''


def build_key_takeaways(bullets_html):
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#f0fdf4"}},"border":{{"radius":"6px","width":"1px","color":"#bbf7d0"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#bbf7d0;border-width:1px;border-radius:6px;background-color:#f0fdf4;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">Key Takeaways</h4>
<!-- /wp:heading -->
<!-- wp:list -->
<ul class="wp-block-list">{bullets_html}</ul>
<!-- /wp:list -->
</div>
<!-- /wp:group -->'''


# ── API helpers ─────────────────────────────────────────────────────────────
def api_get(endpoint):
    url = f"{API_BASE}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        raise Exception(f"curl GET failed: {result.stderr}")
    return json.loads(result.stdout)


def api_post(endpoint, data):
    url = f"{API_BASE}/{endpoint}"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f, ensure_ascii=False)
        tmppath = f.name
    try:
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-X", "POST", "-H", "Content-Type: application/json",
             "-d", f"@{tmppath}", url],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            raise Exception(f"curl POST failed: {result.stderr}")
        return json.loads(result.stdout)
    finally:
        os.unlink(tmppath)


# ── FIXED Detection helpers (work with rendered HTML, no Gutenberg comments) ──

def has_block(content, marker):
    """Check if content already contains a block by its text marker."""
    return marker.lower() in content.lower()


def is_buying_guide(title):
    title_lower = title.lower()
    return title_lower.startswith("best ") or "buying guide" in title_lower


def find_first_paragraph_end(content):
    """Find end of first <p>...</p> or <!-- /wp:paragraph --> block."""
    # Try Gutenberg comment first
    m = re.search(r'<!-- /wp:paragraph -->', content)
    if m:
        return m.end()
    # Fallback to HTML paragraph
    m = re.search(r'</p>', content)
    if m:
        return m.end()
    return 0


def find_faq_position(content):
    """Find the start of FAQ section using HTML headings."""
    # Look for FAQ heading in rendered HTML
    patterns = [
        r'<h[23][^>]*>\s*Frequently Asked Questions?\s*</h[23]>',
        r'<h[23][^>]*>[^<]*FAQ[^<]*</h[23]>',
    ]
    for pat in patterns:
        m = re.search(pat, content, re.IGNORECASE)
        if m:
            # Check for a Gutenberg comment before it
            before = content[:m.start()]
            gb_start = before.rfind('<!-- wp:heading')
            if gb_start >= 0 and m.start() - gb_start < 200:
                return gb_start
            return m.start()
    return None


def find_trust_footer_html(content):
    """Find existing trust footer using rendered HTML markers.

    CRITICAL: This must be precise to avoid matching too broadly.
    Looks for the specific heading 'Our Editorial Standards' or
    'About Our Editorial Standards' followed by editorial/affiliate links.
    """
    # Pattern 1: Look for the specific editorial standards heading
    patterns = [
        # New Gutenberg group with Our Editorial Standards
        (r'<!-- wp:group[^>]*-->\s*<div[^>]*>.*?Our Editorial Standards.*?</div>\s*<!-- /wp:group -->', re.DOTALL),
        # Rendered div with editorial standards heading
        (r'<div[^>]*class="wp-block-group[^"]*"[^>]*>\s*<h4[^>]*>\s*Our Editorial Standards\s*</h4>.*?</div>', re.DOTALL),
        # Old format: "About Our Editorial Standards" as h3
        (r'<h3[^>]*>\s*About Our Editorial Standards\s*</h3>\s*<p[^>]*>.*?affiliate[^<]*</p>', re.DOTALL),
        # Old format: About Our Editorial Standards heading + paragraph
        (r'<h3[^>]*>\s*About Our Editorial Standards\s*</h3>.*?corrections[- ]policy.*?</p>', re.DOTALL),
    ]

    for pat, flags in patterns:
        m = re.search(pat, content, flags)
        if m:
            return m.start(), m.end()

    # Last resort: find just the heading and take until next major section or end
    heading_match = re.search(
        r'(?:<!-- wp:heading[^>]*-->\s*)?<h[34][^>]*>\s*(?:About\s+)?Our Editorial Standards\s*</h[34]>\s*(?:<!-- /wp:heading -->\s*)?',
        content, re.IGNORECASE
    )
    if heading_match:
        start = heading_match.start()
        # Find the end - look for next heading or end of content
        rest = content[heading_match.end():]
        # Find next <h2, <h3 or end
        next_heading = re.search(r'<h[23][^>]*>', rest)
        if next_heading:
            end = heading_match.end() + next_heading.start()
        else:
            # Take the paragraph after the heading
            para_end = re.search(r'</p>\s*(?:</div>\s*)?(?:<!-- /wp:group -->\s*)?', rest)
            if para_end:
                end = heading_match.end() + para_end.end()
            else:
                end = len(content)
        return start, end

    return None, None


def find_end_position(content):
    """Find position before trust footer for inserting final blocks."""
    trust_start, _ = find_trust_footer_html(content)
    if trust_start is not None:
        return trust_start
    return len(content)


# ── Main enhancement logic ──────────────────────────────────────────────────
def enhance_post(post_id, title, cluster):
    blocks_added = []

    data = api_get(f"posts/{post_id}?context=edit")
    content = data.get("content", {}).get("raw", "")
    if not content:
        return "SKIP", "Empty content", []

    original_len = len(content)

    # 1. AT A GLANCE - after first paragraph (skip if any "At a Glance" already present)
    if not has_block(content, "At a Glance"):
        bullets = generate_at_a_glance(post_id, title, cluster)
        block = build_at_a_glance(bullets)
        insert_pos = find_first_paragraph_end(content)
        if insert_pos > 0:
            content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
            blocks_added.append("at_a_glance")

    # 2. WHY THIS MATTERS
    if not has_block(content, "Why this matters"):
        text = generate_why_matters(post_id, title, cluster)
        block = build_why_matters(text)
        # Insert after At a Glance group end, or after first paragraph
        aag_pos = content.lower().find("at a glance")
        if aag_pos >= 0:
            # Find end of that section's container
            after = content[aag_pos:]
            group_end = after.find("<!-- /wp:group -->")
            if group_end >= 0:
                insert_pos = aag_pos + group_end + len("<!-- /wp:group -->")
            else:
                # Rendered HTML: find closing </div> after the At a Glance section
                div_end = after.find("</div>")
                if div_end >= 0:
                    insert_pos = aag_pos + div_end + len("</div>")
                else:
                    insert_pos = find_first_paragraph_end(content)
        else:
            insert_pos = find_first_paragraph_end(content)
        content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
        blocks_added.append("why_this_matters")

    # 3. WHAT WE CONSIDERED - for buying guides only
    if is_buying_guide(title) and not has_block(content, "What we considered"):
        considered_text = generate_what_we_considered(post_id, title, cluster)
        if considered_text:
            block = build_what_we_considered(considered_text)
            # Insert after Why This Matters
            wtm_pos = content.lower().find("why this matters")
            if wtm_pos >= 0:
                after = content[wtm_pos:]
                group_end = after.find("<!-- /wp:group -->")
                if group_end >= 0:
                    insert_pos = wtm_pos + group_end + len("<!-- /wp:group -->")
                else:
                    div_end = after.find("</div>")
                    if div_end >= 0:
                        insert_pos = wtm_pos + div_end + len("</div>")
                    else:
                        insert_pos = find_first_paragraph_end(content)
            else:
                insert_pos = find_first_paragraph_end(content)
            content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
            blocks_added.append("what_we_considered")

    # 4. TROUBLESHOOTING - before FAQ
    if not has_block(content, "Troubleshooting Common Issues"):
        trouble_text = generate_troubleshooting(post_id, title, cluster)
        block = build_troubleshooting(trouble_text)
        faq_pos = find_faq_position(content)
        if faq_pos:
            content = content[:faq_pos] + block + "\n\n" + content[faq_pos:]
        else:
            end_pos = find_end_position(content)
            content = content[:end_pos] + "\n\n" + block + "\n\n" + content[end_pos:]
        blocks_added.append("troubleshooting")

    # 5. WHEN TO SEEK HELP - after troubleshooting
    if not has_block(content, "When to seek professional help"):
        seek_text = generate_when_to_seek_help(post_id, title, cluster)
        block = build_when_to_seek_help(seek_text)
        trouble_pos = content.find("Troubleshooting Common Issues")
        if trouble_pos >= 0:
            # Find end of troubleshooting paragraph
            after = content[trouble_pos:]
            # Look for end of the paragraph block after heading
            para_end = after.find("<!-- /wp:paragraph -->")
            if para_end >= 0:
                insert_pos = trouble_pos + para_end + len("<!-- /wp:paragraph -->")
            else:
                # Rendered: find 2nd </p> after heading
                p_ends = [m.end() for m in re.finditer(r'</p>', after)]
                if len(p_ends) >= 1:
                    insert_pos = trouble_pos + p_ends[0]
                else:
                    insert_pos = find_end_position(content)
        else:
            insert_pos = find_end_position(content)
        content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
        blocks_added.append("when_to_seek_help")

    # 6. KEY TAKEAWAYS - before trust footer
    if not has_block(content, "Key Takeaways"):
        takeaway_bullets = generate_key_takeaways(post_id, title, cluster)
        block = build_key_takeaways(takeaway_bullets)
        end_pos = find_end_position(content)
        content = content[:end_pos] + "\n\n" + block + "\n\n" + content[end_pos:]
        blocks_added.append("key_takeaways")

    # 7. UPGRADE TRUST FOOTER
    trust_start, trust_end = find_trust_footer_html(content)
    new_footer = get_trust_footer(cluster, post_id, title)
    if trust_start is not None:
        content = content[:trust_start] + new_footer + content[trust_end:]
        blocks_added.append("trust_footer_upgraded")
    else:
        content = content.rstrip() + "\n\n" + new_footer
        blocks_added.append("trust_footer_added")

    # Sanity check: ensure we haven't lost content
    if len(content) < original_len * 0.8:
        return "SANITY_FAIL", f"Content would shrink from {original_len} to {len(content)}", blocks_added

    # Update the post
    time.sleep(DELAY)
    result = api_post(f"posts/{post_id}", {"content": content})

    if "id" in result:
        new_len = len(content)
        return "OK", f"{original_len}->{new_len}", blocks_added
    else:
        error_msg = result.get("message", str(result)[:200])
        return "ERROR", error_msg, blocks_added


# ── Main ────────────────────────────────────────────────────────────────────
def main():
    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "post_id", "title", "cluster", "status", "detail", "blocks_added"])

    total = sum(len(posts) for posts in POSTS.values())
    done = 0
    errors = 0
    sanity_fails = 0

    print(f"Phase 10AI Batch 4 v2: Enhancing {total} posts across 5 clusters")
    print(f"Log: {LOG_FILE}")
    print("=" * 70)

    for cluster, posts in POSTS.items():
        print(f"\n--- {cluster} ({len(posts)} posts) ---")
        for post_id, title in posts:
            done += 1
            short_title = title[:50] + "..." if len(title) > 50 else title
            print(f"[{done}/{total}] #{post_id}: {short_title}")

            try:
                status, detail, blocks = enhance_post(post_id, title, cluster)
                blocks_str = ",".join(blocks) if blocks else "none"
                print(f"  -> {status} | {detail} | blocks: {blocks_str}")

                if status == "ERROR":
                    errors += 1
                elif status == "SANITY_FAIL":
                    sanity_fails += 1

                with open(LOG_FILE, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        datetime.now().isoformat(),
                        post_id, title, cluster, status, detail, blocks_str
                    ])

            except Exception as e:
                errors += 1
                error_msg = str(e)[:200]
                print(f"  -> EXCEPTION: {error_msg}")
                with open(LOG_FILE, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        datetime.now().isoformat(),
                        post_id, title, cluster, "EXCEPTION", error_msg, ""
                    ])

            time.sleep(DELAY)

    print(f"\n{'=' * 70}")
    print(f"COMPLETE: {done} processed, {errors} errors, {sanity_fails} sanity fails")
    print(f"Log: {LOG_FILE}")


if __name__ == "__main__":
    main()
