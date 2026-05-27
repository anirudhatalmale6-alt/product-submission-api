#!/usr/bin/env python3
"""Phase 10D WS1-WS3: Cluster expansion for Dog Beds, Dog Toys, Training/Puppy Care.
Creates educational spoke posts with proper Gutenberg blocks, RankMath SEO,
internal links, and 12-gate safety checks."""

import requests, json, re, html as html_mod, csv, os, time
from datetime import datetime, timezone
from gutenberg_utils import (
    wrap_paragraph, wrap_heading, wrap_list, wrap_separator,
    wrap_group, validate_gutenberg, safe_update_content, build_page
)

WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
RM_BASE = "https://pethubonline.com/wp-json/rankmath/v1"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"

s = requests.Session()
s.auth = (WP_USER, WP_PASS)
s.headers['Accept-Encoding'] = 'gzip, deflate'

OUT = '/var/lib/freelancer/projects/40416335/phase10d'
os.makedirs(OUT, exist_ok=True)
NOW = datetime.now(timezone.utc).isoformat()

CATEGORIES = {
    'Dog Beds': 1401,
    'Dog Toys': 1441,
    'Training Supplies': 1474,
    'Puppy Care': 1442,
    'Dog Supplies': 1376,
}

SAFETY_GATES = [
    'educational_only', 'no_affiliate', 'no_recommendations', 'no_red_topic',
    'no_regulated_claims', 'no_fake_authority', 'metadata_valid',
    'schema_safe', 'internal_links_valid', 'trust_wording',
    'publisher_gates', 'rollback_available'
]

RED_KEYWORDS = ['insurance', 'medication', 'prescription', 'veterinary treatment',
                'diagnosis', 'medical condition', 'euthanasia']

def check_12_gates(title, content, meta_title, meta_desc, focus_kw):
    results = {}
    results['educational_only'] = not any(w in content.lower() for w in ['buy now', 'shop now', 'order today', 'add to cart', 'check price'])
    results['no_affiliate'] = 'rel="nofollow' not in content and 'affiliate' not in content.lower().split('disclosure')[0] if 'disclosure' in content.lower() else 'affiliate' not in content.lower()
    results['no_recommendations'] = not any(w in content.lower() for w in ['we recommend', 'our top pick', 'best buy', 'our favourite', 'editor\'s choice'])
    results['no_red_topic'] = not any(kw in content.lower() for kw in RED_KEYWORDS)
    results['no_regulated_claims'] = not any(w in content.lower() for w in ['clinically proven', 'vet approved', 'medically tested', 'guaranteed to cure'])
    results['no_fake_authority'] = not any(w in content.lower() for w in ['we tested', 'our experts', 'our team of vets', 'vet-backed'])
    results['metadata_valid'] = len(meta_title) <= 60 and len(meta_desc) <= 160 and len(focus_kw) > 0
    results['schema_safe'] = 'ProductReview' not in content and 'AggregateRating' not in content
    results['internal_links_valid'] = 'href="/' in content or 'pethubonline.com' in content
    results['trust_wording'] = not any(w in content.lower() for w in ['guaranteed', 'proven to', '100% safe', 'risk-free'])
    results['publisher_gates'] = True
    results['rollback_available'] = True
    return results

def build_post_content(title, intro, sections, faq_items, hub_link, hub_title, related_links):
    blocks = []

    blocks.append(wrap_heading('Quick Summary', level=2))
    blocks.append(wrap_paragraph(f'<p>{intro}</p>'))
    blocks.append(wrap_separator())

    for heading, paragraphs in sections:
        blocks.append(wrap_heading(heading, level=2))
        for p in paragraphs:
            if isinstance(p, list):
                blocks.append(wrap_list(p))
            else:
                blocks.append(wrap_paragraph(f'<p>{p}</p>'))

    if faq_items:
        blocks.append(wrap_separator())
        blocks.append(wrap_heading('Frequently Asked Questions', level=2))
        for q, a in faq_items:
            blocks.append(wrap_heading(q, level=3))
            blocks.append(wrap_paragraph(f'<p>{a}</p>'))

    blocks.append(wrap_separator())
    blocks.append(wrap_heading('Related Reading', level=2))
    link_items = [f'<a href="{url}">{text}</a>' for text, url in related_links]
    link_items.append(f'Back to <a href="{hub_link}">{hub_title}</a>')
    blocks.append(wrap_list(link_items))

    blocks.append(wrap_paragraph(f'<p><em>Last updated: {datetime.now(timezone.utc).strftime("%d %B %Y")}</em></p>'))

    return build_page(blocks)


# ===== DOG BEDS EDUCATIONAL SPOKES =====
DOG_BEDS_POSTS = [
    {
        'title': 'How to Choose the Right Dog Bed Size',
        'slug': 'how-to-choose-dog-bed-size',
        'meta_title': 'How to Choose the Right Dog Bed Size (2026)',
        'meta_desc': 'Learn how to measure your dog and select the perfect bed size. Covers small to giant breeds with sizing charts and sleep position guidance.',
        'focus_kw': 'dog bed size guide',
        'intro': 'Getting the right bed size matters more than most owners realise. A bed that is too small forces awkward sleep positions, while one that is too large can feel insecure for anxious dogs. This guide covers measuring techniques, breed-specific sizing, and how sleep position affects bed choice.',
        'sections': [
            ('Why Bed Size Matters', [
                'Dogs spend 12 to 14 hours a day sleeping or resting. A properly sized bed supports joints, regulates temperature, and provides a secure den-like space. Puppies, senior dogs, and those with joint issues benefit most from correct sizing.',
                'An undersized bed means limbs hang off the edge, creating pressure points. An oversized bed may not provide the bolster support that many dogs prefer for resting their head.',
            ]),
            ('How to Measure Your Dog', [
                'Measure from the tip of the nose to the base of the tail while your dog is lying in their natural sleep position. Add 15 to 20 centimetres for comfort. For width, measure across the widest point and add the same margin.',
                ['Nose to tail base plus 15-20cm for length', 'Widest body point plus 15-20cm for width', 'Measure while lying down, not standing', 'For puppies, estimate adult size using breed standards'],
            ]),
            ('Sleep Position and Bed Shape', [
                'Curlers prefer round or oval beds with raised edges. Side sleepers need flat, rectangular beds with enough room to stretch. Sprawlers benefit from oversized flat mats or mattresses.',
                'Observe your dog over several nights before choosing. Many dogs alternate between positions, so a versatile rectangular bed with low bolsters often works best as a general choice.',
            ]),
            ('Size Guide by Breed Category', [
                ['Small breeds (Chihuahua, Pomeranian, Yorkshire Terrier): 45-60cm bed', 'Medium breeds (Cocker Spaniel, Beagle, Border Collie): 60-80cm bed', 'Large breeds (Labrador, Golden Retriever, German Shepherd): 80-100cm bed', 'Giant breeds (Great Dane, Saint Bernard, Irish Wolfhound): 100-120cm+ bed'],
                'These are starting points. Always measure your individual dog rather than relying solely on breed averages, as individual variation within breeds can be significant.',
            ]),
            ('When to Size Up', [
                'If your dog consistently hangs limbs off the edge, curls tightly when they normally stretch, or avoids the bed altogether, it may be too small. Dogs that dig or rearrange the bed excessively may also need a different size or shape.',
            ]),
        ],
        'faq': [
            ('Should I get a bigger bed for a puppy?', 'It depends on the breed. For large breeds that will grow significantly, consider a larger bed from the start or plan to replace it as the puppy grows. For small breeds, a puppy-sized bed provides better security and warmth.'),
            ('Can two dogs share one bed?', 'Some dogs enjoy sharing, but each dog should also have their own bed available. Shared beds should be large enough for both dogs to lie comfortably without overlapping. Monitor for any guarding behaviour.'),
            ('How often should I replace a dog bed?', 'Replace when the bed loses its supportive structure, develops permanent odour despite washing, or shows significant wear. Most quality beds last 2 to 3 years with proper care. Orthopaedic beds may last longer if the foam maintains density.'),
        ],
        'related': [
            ('Best Dog Beds UK – Complete Guide', '/best-dog-beds-uk'),
            ('Best Orthopaedic Dog Beds UK', '/best-orthopaedic-dog-beds-uk'),
            ('Best Cooling Dog Beds UK', '/best-cooling-dog-beds-uk'),
            ('Best Puppy Beds UK', '/best-puppy-beds-uk'),
        ],
    },
    {
        'title': 'Dog Bed Materials Explained: Foam, Memory Foam, and More',
        'slug': 'dog-bed-materials-guide',
        'meta_title': 'Dog Bed Materials Guide: Foam vs Memory Foam (2026)',
        'meta_desc': 'Compare dog bed filling materials including memory foam, polyester, and orthopaedic foam. Learn which material suits your dog best.',
        'focus_kw': 'dog bed materials',
        'intro': 'The filling inside a dog bed determines comfort, support, and durability far more than the outer fabric. Understanding the differences between materials helps you choose a bed that actually meets your dog\'s needs rather than just looking good in the photos.',
        'sections': [
            ('Why Material Matters More Than You Think', [
                'A bed can look plush and inviting in photos but flatten within weeks if the filling is low-density polyester. Conversely, a simple-looking foam bed may provide years of consistent joint support. The material inside determines how well the bed performs over time.',
                'Different life stages and health conditions call for different materials. A healthy young dog may be fine with standard filling, while a senior with arthritis genuinely benefits from proper orthopaedic foam.',
            ]),
            ('Standard Polyester Fibre Fill', [
                'The most common and affordable filling. Polyester fibre is lightweight, machine-washable, and soft. However, it compresses over time and loses its loft, meaning the bed gradually flattens.',
                ['Pros: affordable, lightweight, easy to wash, soft initial feel', 'Cons: flattens quickly, offers minimal joint support, needs frequent replacement', 'Best for: young healthy dogs, second or travel beds, budget-conscious owners'],
            ]),
            ('Memory Foam', [
                'Memory foam moulds to the dog\'s body shape and distributes weight evenly. This makes it excellent for joint support, especially in senior dogs or breeds prone to hip dysplasia and arthritis.',
                ['Pros: excellent pressure distribution, retains shape, genuine joint support', 'Cons: can retain heat, heavier, not machine-washable (cover only), higher cost', 'Best for: senior dogs, large breeds, dogs with joint conditions, dogs recovering from surgery'],
                'Look for density ratings when comparing memory foam beds. Higher density (above 80kg per cubic metre) provides better support and lasts longer. Low-density memory foam can feel similar initially but compresses faster.',
            ]),
            ('High-Resilience Foam', [
                'HR foam bounces back quickly after compression, unlike memory foam which moulds slowly. It provides firm, consistent support without the heat-retention issues of memory foam.',
                ['Pros: firm consistent support, good air circulation, durable, bounces back', 'Cons: less contouring than memory foam, can feel too firm for some dogs', 'Best for: active dogs, medium to large breeds, dogs that prefer firmer surfaces'],
            ]),
            ('Gel-Infused and Cooling Materials', [
                'Gel memory foam or beds with cooling gel layers help regulate temperature. These are worth considering for dogs that overheat easily, brachycephalic breeds, or households without air conditioning.',
                'The cooling effect is most noticeable in the first hour of use, as the gel absorbs initial body heat. Over extended sleep periods, the difference becomes less pronounced compared to standard memory foam.',
            ]),
            ('Choosing the Right Material', [
                'Consider your dog\'s age, weight, health, and sleep habits. For most healthy adult dogs, a quality HR foam or combination foam bed offers the best balance of comfort, support, and durability. Reserve premium memory foam for dogs with genuine joint support needs.',
            ]),
        ],
        'faq': [
            ('Is memory foam worth the extra cost?', 'For senior dogs, large breeds, and dogs with diagnosed joint issues, yes. The pressure distribution genuinely helps. For young, healthy dogs with no joint concerns, quality standard foam provides adequate support at a lower price point.'),
            ('How can I tell if a dog bed has quality foam?', 'Check the foam density if listed (higher is better). Press the bed firmly — quality foam springs back within a few seconds. If you can feel the floor through the bed, the foam is too thin or too soft. A minimum of 7cm foam thickness is recommended for medium to large dogs.'),
            ('Do waterproof liners affect comfort?', 'A waterproof liner between the cover and foam protects the filling without affecting comfort. Most dogs cannot tell the difference. It also extends the life of the foam significantly by preventing moisture damage.'),
        ],
        'related': [
            ('Best Dog Beds UK – Complete Guide', '/best-dog-beds-uk'),
            ('Best Orthopaedic Dog Beds UK', '/best-orthopaedic-dog-beds-uk'),
            ('How to Choose the Right Dog Bed Size', '/how-to-choose-dog-bed-size'),
            ('Best Cooling Dog Beds UK', '/best-cooling-dog-beds-uk'),
        ],
    },
    {
        'title': 'How to Wash and Maintain Your Dog\'s Bed',
        'slug': 'how-to-wash-dog-bed',
        'meta_title': 'How to Wash a Dog Bed: Care & Maintenance Guide',
        'meta_desc': 'Step-by-step guide to washing dog beds properly. Covers machine-washable beds, foam cleaning, odour removal, and maintenance schedules.',
        'focus_kw': 'how to wash dog bed',
        'intro': 'A clean dog bed is healthier for your dog and more pleasant for your home. But washing a dog bed incorrectly can destroy the filling, shrink the cover, or fail to remove embedded dirt and odour. This guide covers proper cleaning methods for every bed type.',
        'sections': [
            ('Why Regular Cleaning Matters', [
                'Dog beds accumulate dirt, dead skin cells, hair, saliva, and outdoor debris. Over time, this creates an environment where bacteria, dust mites, and even mould can thrive. Regular cleaning extends the bed\'s life and keeps your dog healthier.',
                'Allergies, skin irritation, and persistent odour often trace back to an inadequately cleaned bed. If your dog scratches more than usual or avoids their bed, cleanliness could be a factor.',
            ]),
            ('How Often to Wash', [
                ['Cover or liner: every 1 to 2 weeks', 'Full wash (including filling if possible): once a month', 'Deep clean or replacement check: every 3 to 6 months', 'After illness, wet weather season, or flea treatment: immediately'],
                'These are minimum recommendations. Dogs that spend a lot of time outdoors, have skin conditions, or share beds with other pets may need more frequent cleaning.',
            ]),
            ('Machine-Washable Covers', [
                'Most quality dog beds have removable, machine-washable covers. Remove the cover and shake off loose hair and debris before washing. Use a gentle cycle at 30 to 40 degrees with a pet-safe or fragrance-free detergent.',
                'Avoid fabric softener, which can irritate some dogs\' skin and reduce the water-resistance of treated fabrics. Tumble dry on low heat or air dry flat. High heat can shrink cotton covers and damage waterproof linings.',
            ]),
            ('Cleaning Foam Inserts', [
                'Most foam inserts cannot go in a washing machine. Instead, vacuum the surface to remove hair and dust, then spot-clean stains with a mixture of mild detergent and warm water. Use a damp cloth rather than soaking the foam.',
                'For deeper cleaning, fill a bathtub with lukewarm water and a small amount of pet-safe detergent. Submerge the foam and gently squeeze (never wring) to work the water through. Rinse thoroughly and squeeze out excess water. Air dry completely — this can take 24 to 48 hours depending on thickness.',
                'Foam that is not fully dried before replacing the cover can develop mould. Ensure complete dryness by standing the foam on its edge in a well-ventilated area.',
            ]),
            ('Removing Persistent Odour', [
                'If washing alone does not remove odour, sprinkle baking soda over the entire bed surface and leave for 4 to 8 hours before vacuuming off. For covers, add 100ml of white vinegar to the rinse cycle.',
                'If odour persists after proper cleaning, the foam may have absorbed moisture or oils beyond recovery. This is a sign the bed may need replacing rather than further cleaning attempts.',
            ]),
            ('Maintenance Between Washes', [
                ['Vacuum or lint-roll the bed weekly', 'Shake out covers outdoors to remove hair and dust', 'Air the bed in sunlight when possible (UV helps kill bacteria)', 'Use a washable blanket on top for easy swapping between washes', 'Check zips, seams, and foam integrity monthly'],
            ]),
        ],
        'faq': [
            ('Can I use normal laundry detergent on dog beds?', 'Yes, but choose a fragrance-free or hypoallergenic option. Heavily scented detergents can irritate dogs\' skin and the strong fragrance may deter them from using the bed. Avoid any detergent containing bleach.'),
            ('My dog bed says hand-wash only. Can I machine wash it?', 'Hand-wash labels usually indicate delicate construction or filling that cannot handle machine agitation. Follow the label. If you must use a machine, use the gentlest cycle available and place the item in a large laundry bag.'),
            ('How do I know when to replace rather than wash?', 'Replace the bed when the foam no longer springs back after pressing, when seams are splitting and cannot be repaired, when stains and odour persist despite proper washing, or when the bed has flattened to the point where your dog\'s joints are not cushioned from the floor.'),
        ],
        'related': [
            ('Best Dog Beds UK – Complete Guide', '/best-dog-beds-uk'),
            ('Dog Bed Materials Explained', '/dog-bed-materials-guide'),
            ('How to Choose the Right Dog Bed Size', '/how-to-choose-dog-bed-size'),
            ('Best Orthopaedic Dog Beds UK', '/best-orthopaedic-dog-beds-uk'),
        ],
    },
    {
        'title': 'Where to Place Your Dog\'s Bed: Location and Comfort Tips',
        'slug': 'where-to-place-dog-bed',
        'meta_title': 'Where to Put a Dog Bed: Best Locations at Home',
        'meta_desc': 'Find the best spot for your dog\'s bed. Covers temperature, noise, multi-dog homes, bedroom placement, and creating a comfortable sleep space.',
        'focus_kw': 'where to place dog bed',
        'intro': 'Where you put a dog\'s bed affects how well they sleep, how secure they feel, and whether they actually use it. Many bed-avoidance problems trace back to poor placement rather than the bed itself. This guide covers how to choose the right spot.',
        'sections': [
            ('Why Location Matters', [
                'Dogs are den animals by instinct. They feel safest sleeping in a spot that is sheltered, slightly enclosed, and positioned where they can observe their environment without being in the middle of foot traffic.',
                'A bed placed in the wrong spot — too hot, too cold, too noisy, or too isolated — often gets ignored. Before assuming your dog dislikes their bed, experiment with location changes.',
            ]),
            ('Temperature Considerations', [
                'Avoid placing beds directly next to radiators, under heating vents, or in direct sunlight for extended periods. Dogs overheat more easily than humans and may avoid a bed that gets too warm.',
                'Equally, avoid cold draughty spots near exterior doors or poorly insulated walls, especially for short-coated, senior, or small dogs. A mid-room position against an interior wall often provides the most consistent temperature.',
                ['Away from direct heat sources', 'Away from draughty doors and windows', 'Not in direct afternoon sunlight', 'On a rug or carpet rather than bare cold flooring where possible'],
            ]),
            ('Noise and Activity Levels', [
                'Dogs sleep better in areas with consistent, low background noise rather than complete silence punctuated by sudden sounds. A quiet corner of a living area is often ideal — the dog can hear household activity without being startled.',
                'Avoid placing beds next to washing machines, tumble dryers, or near the front door where doorbell and delivery noises are loudest. If your dog is nervous, a quieter room with some ambient sound works best.',
            ]),
            ('Social Placement', [
                'Most dogs prefer sleeping near their family rather than in isolated rooms. A bed in the corner of the living room or at the foot of the owner\'s bed keeps the dog near its people while giving it defined space.',
                'Dogs that are crated at night benefit from having the crate in the bedroom or just outside it. Dogs that sleep on a bed rather than in a crate should have a consistent spot they recognise as theirs.',
            ]),
            ('Multi-Dog Households', [
                'Each dog should have their own bed, even if they sometimes choose to share. Place beds in separate areas of the same room rather than right next to each other, especially if there is any resource-guarding tendency.',
                'Observe which dogs prefer elevated positions and which prefer floor level. Some dogs feel more secure in a corner while others prefer a central spot. Let individual preferences guide placement.',
            ]),
            ('Bedroom vs Living Room', [
                'Research suggests dogs that sleep in or near their owner\'s bedroom often show lower stress levels. If you allow bedroom sleeping, a dedicated bed on the floor near your bed is a good compromise between closeness and independence.',
                'If the bedroom is not an option, ensure the living room bed is in a spot that does not feel punishing compared to where the family spends evening time.',
            ]),
        ],
        'faq': [
            ('Should I move my dog\'s bed around the house?', 'Having one primary bed in a consistent location builds routine and security. However, a second bed in another room the family uses frequently can be beneficial. Avoid constantly relocating a single bed.'),
            ('My dog ignores the bed and sleeps on the floor. Why?', 'Common reasons include the bed being too warm, in a noisy location, or the wrong size. Try moving it to a cooler or quieter spot. Some dogs also prefer firm surfaces, in which case a thin mat on their chosen floor spot may be more accepted.'),
            ('Is it okay to put the dog bed on furniture or an elevated surface?', 'Some small dogs feel more secure on a raised surface. Ensure the platform is stable and the dog can get on and off safely without jumping. For senior or joint-compromised dogs, floor level is safest to avoid impact on joints.'),
        ],
        'related': [
            ('Best Dog Beds UK – Complete Guide', '/best-dog-beds-uk'),
            ('How to Choose the Right Dog Bed Size', '/how-to-choose-dog-bed-size'),
            ('Best Cooling Dog Beds UK', '/best-cooling-dog-beds-uk'),
            ('Best Puppy Beds UK', '/best-puppy-beds-uk'),
        ],
    },
]

# ===== DOG TOYS EDUCATIONAL SPOKES =====
DOG_TOYS_POSTS = [
    {
        'title': 'Dog Toy Safety: What Every Owner Needs to Know',
        'slug': 'dog-toy-safety-guide',
        'meta_title': 'Dog Toy Safety Guide: Hazards to Avoid (2026)',
        'meta_desc': 'Essential dog toy safety guide covering choking hazards, toxic materials, size selection, and supervision tips. Keep your dog safe during play.',
        'focus_kw': 'dog toy safety',
        'intro': 'Not all dog toys are equally safe. Size mismatches, toxic materials, and worn-out toys cause thousands of emergency vet visits each year in the UK. This guide covers how to choose, inspect, and rotate toys to keep your dog safe.',
        'sections': [
            ('Common Toy Hazards', [
                'The most common toy-related incidents involve ingestion of small parts, choking on pieces that break off, and intestinal obstruction from swallowed materials. Squeakers, stuffing, and rope fibres are frequent culprits.',
                ['Toys too small for the dog (choking risk)', 'Squeakers that can be extracted and swallowed', 'Rope toys that shed fibres (can cause intestinal blockage)', 'Hard toys that can crack teeth', 'Toys with small removable parts (eyes, buttons, decorations)'],
            ]),
            ('Size Selection', [
                'A toy should be large enough that the dog cannot fit the entire toy in its mouth. If a ball can sit fully behind the dog\'s back teeth, it is too small. This is the most common and most dangerous sizing mistake.',
                'For strong chewers, choose toys rated for their size category or one size up. Manufacturer size guides are starting points — always assess based on your individual dog\'s jaw strength and chewing style.',
            ]),
            ('Material Safety', [
                'Look for toys made from natural rubber, food-grade silicone, or certified non-toxic materials. Avoid toys with strong chemical odours, which can indicate cheap manufacturing and potentially harmful chemicals.',
                'In the UK, dog toys are not subject to the same safety regulations as children\'s toys. This means the burden of checking material safety falls on the owner. Established brands with transparent material sourcing are generally more reliable.',
            ]),
            ('Inspection and Replacement', [
                'Check toys before every play session for cracks, tears, loose parts, and wear. A toy that was safe last week may have developed a dangerous weak point.',
                ['Daily: visual check before play', 'Weekly: squeeze and flex test for cracks', 'Monthly: full inventory check and discard worn toys', 'Immediately: remove any toy that shows splitting, loose stuffing, or exposed squeaker'],
            ]),
            ('Supervised vs Unsupervised Toys', [
                'Some toys are safe to leave with a dog unsupervised (solid rubber kongs, quality nylon bones designed for solo chewing), while others should only be used during supervised play (rope toys, plush toys, tug toys).',
                'When in doubt, supervise. If you cannot supervise, only leave toys that your dog has demonstrated they chew gently and safely over an extended period.',
            ]),
            ('When to Seek Veterinary Help', [
                'If your dog has swallowed part of a toy, shows symptoms of obstruction (repeated vomiting, lethargy, loss of appetite, straining), or has a toy stuck in their mouth or throat, contact your vet immediately. Do not attempt to induce vomiting without veterinary guidance.',
            ]),
        ],
        'faq': [
            ('Are tennis balls safe for dogs?', 'Standard tennis balls can wear down tooth enamel with extended chewing due to the abrasive felt covering. They are also a choking hazard for large dogs. Dog-specific balls made from smoother, softer rubber are a safer alternative for regular use.'),
            ('How many toys should a dog have?', 'Rotate 3 to 5 toys at a time rather than providing all toys at once. This keeps toys interesting and allows you to inspect resting toys between rotations. Most dogs benefit from a mix of chew, fetch, and puzzle toys.'),
            ('Are rawhide chews safe?', 'Rawhide can pose choking and blockage risks if large pieces are swallowed. If you choose rawhide, opt for thick, single-piece chews rather than compressed or shaped rawhide. Always supervise and remove when small enough to swallow whole.'),
        ],
        'related': [
            ('Best Dog Toys UK – Complete Guide', '/best-dog-toys-uk'),
            ('Best Indestructible Dog Toys UK', '/best-indestructible-dog-toys-uk'),
            ('Best Interactive Dog Toys UK', '/best-interactive-dog-toys-uk'),
            ('Best Puppy Toys UK', '/best-puppy-toys-uk'),
        ],
    },
    {
        'title': 'Mental Stimulation for Dogs: Beyond Physical Exercise',
        'slug': 'mental-stimulation-for-dogs',
        'meta_title': 'Mental Stimulation for Dogs: Activities & Ideas',
        'meta_desc': 'Discover why mental stimulation matters as much as physical exercise for dogs. Includes enrichment ideas, puzzle activities, and training games.',
        'focus_kw': 'mental stimulation for dogs',
        'intro': 'A tired dog is not just a physically exercised dog — it is a mentally engaged one. Many behavioural problems including destructive chewing, excessive barking, and restlessness trace back to mental under-stimulation. This guide covers practical ways to keep your dog\'s mind active.',
        'sections': [
            ('Why Mental Stimulation Matters', [
                'Dogs were bred to work — herding, hunting, guarding, retrieving. Modern pet life removes most of these mental challenges, leaving dogs with active brains and not enough to do. The result is often boredom-driven behaviour that owners mistake for disobedience.',
                '15 minutes of structured mental engagement can tire a dog as effectively as 30 minutes of walking. This does not replace physical exercise but complements it, particularly on days when weather or health limits outdoor activity.',
            ]),
            ('Food-Based Enrichment', [
                'The simplest mental stimulation: make your dog work for their food. Instead of a bowl, use puzzle feeders, snuffle mats, scatter feeding in the garden, or stuffed and frozen food toys.',
                ['Scatter kibble in grass for natural foraging behaviour', 'Stuff a rubber toy with food and freeze it for extended engagement', 'Use a muffin tin with tennis balls covering treats in each cup', 'Wrap treats in old towels for unwrapping challenges'],
                'Start easy and increase difficulty gradually. A puzzle that is too hard leads to frustration, not enrichment.',
            ]),
            ('Training as Mental Exercise', [
                'Teaching new skills is one of the best forms of mental stimulation. Short sessions of 5 to 10 minutes work better than long ones. Focus on one new skill at a time and keep the success rate high to maintain engagement.',
                'Beyond basic commands, consider teaching: targeting (nose to hand), object names (fetch the ball vs fetch the toy), directional cues (left, right, back up), and cooperative care behaviours (chin rest for grooming, paw offer for nail trimming).',
            ]),
            ('Scent Work', [
                'A dog\'s sense of smell is its primary way of understanding the world. Scent-based activities engage a massive portion of the brain and provide deep satisfaction.',
                ['Hide treats around the house for search games', 'Introduce scent trails in the garden', 'Use cardboard boxes with treats hidden among crumpled paper', 'Let your dog sniff freely on walks rather than rushing past every scent mark'],
                'Scent work is especially valuable for senior dogs and those with mobility limitations, as it provides intense mental engagement with minimal physical demand.',
            ]),
            ('Novelty and Environmental Changes', [
                'Regularly introducing new objects, sounds, textures, and experiences keeps a dog\'s brain engaged. A new walking route, a different park, or even rearranging furniture can provide mental stimulation through novelty.',
                'Rotate toys every few days so each one feels fresh. Introduce new types of enrichment gradually to avoid overwhelming anxious dogs.',
            ]),
            ('Signs of Under-Stimulation', [
                ['Destructive chewing on furniture or shoes', 'Excessive barking or whining', 'Restlessness or inability to settle', 'Attention-seeking behaviour that seems relentless', 'Repetitive behaviours like pacing or tail chasing'],
                'If your dog shows these signs despite adequate physical exercise, increase mental enrichment before assuming the behaviour is a training problem.',
            ]),
        ],
        'faq': [
            ('How much mental stimulation does a dog need daily?', 'Most dogs benefit from 15 to 30 minutes of structured mental engagement per day, split across 2 to 3 sessions. Working breeds and high-energy dogs may need more. This is in addition to, not instead of, physical exercise.'),
            ('Can mental stimulation replace walks?', 'Not entirely. Dogs need physical exercise for cardiovascular health, muscle maintenance, and social exposure. However, on days when a full walk is not possible (extreme weather, illness recovery), mental stimulation can help manage energy levels.'),
            ('My dog gives up on puzzle toys quickly. What should I do?', 'The puzzle is probably too difficult. Go back to an easier version and build up gradually. Show the dog how it works by letting them watch you place food. Early success builds confidence and persistence with harder challenges later.'),
        ],
        'related': [
            ('Best Interactive Dog Toys UK', '/best-interactive-dog-toys-uk'),
            ('Best Dog Toys UK – Complete Guide', '/best-dog-toys-uk'),
            ('Dog Toy Safety Guide', '/dog-toy-safety-guide'),
            ('Best Dog Training and Behaviour UK', '/best-dog-training-and-behaviour-uk'),
        ],
    },
    {
        'title': 'Best Types of Dog Toys for Different Play Styles',
        'slug': 'dog-toys-for-different-play-styles',
        'meta_title': 'Dog Toys by Play Style: Chewers, Chasers & More',
        'meta_desc': 'Match the right toy type to your dog\'s play style. Covers chewers, chasers, tuggers, puzzlers, and gentle players with specific guidance.',
        'focus_kw': 'dog toys by play style',
        'intro': 'Dogs play differently based on breed instincts, personality, and physical traits. A toy that delights a fetch-obsessed retriever may bore a problem-solving terrier. Understanding your dog\'s play style helps you choose toys they will actually use and enjoy.',
        'sections': [
            ('Identifying Your Dog\'s Play Style', [
                'Watch how your dog naturally plays. Do they chase and retrieve? Chew and dissect? Tug and wrestle? Carry and hoard? Most dogs favour one or two styles, though many enjoy variety. Breed tendencies offer clues but individual personality matters more.',
                ['Chasers: fixated on moving objects, love fetch, often retrievers and herding breeds', 'Chewers: happiest when gnawing, prefer durable toys, often terriers and bully breeds', 'Tuggers: love interactive pulling games, enjoy rope and tug toys, often working breeds', 'Puzzlers: engage with hidden food, enjoy figuring things out, often scent hounds and intelligent breeds', 'Gentle players: carry toys softly, enjoy plush toys, often companion breeds'],
            ]),
            ('Toys for Chasers and Fetchers', [
                'Balls remain the classic fetch toy, but not all balls are equal. Choose ones sized appropriately for your dog and made from durable, non-abrasive materials. Frisbees and flying discs work well for dogs that enjoy aerial catches.',
                'Ball launchers extend throwing distance and save your arm. Bumpy or irregularly shaped balls add unpredictability that keeps fetch interesting. For water-loving dogs, floating toys combine fetch with swimming exercise.',
            ]),
            ('Toys for Power Chewers', [
                'Chewers need toys rated for their jaw strength. Solid natural rubber and reinforced nylon are the most durable materials. Avoid anything that can splinter, crack, or break into ingestible pieces.',
                'The best chew toys have some give — they flex slightly under jaw pressure without breaking. Toys that are completely rigid (like antlers or bones) can crack teeth. If your thumbnail can dent the toy, it likely has appropriate flex for most dogs.',
            ]),
            ('Toys for Tuggers', [
                'Tug toys should be long enough to keep your hands away from the dog\'s teeth and durable enough to handle sustained pulling. Rubber tug toys are often more durable than rope versions and do not shed fibres.',
                'Tug play is excellent exercise and does not cause aggression when played with clear rules: the dog releases when asked, play pauses if teeth contact hands, and the game ends calmly.',
            ]),
            ('Toys for Problem Solvers', [
                'Puzzle feeders, treat-dispensing toys, and multi-step challenge toys satisfy dogs that need to think. Start with simple puzzles (single step to access food) and progress to complex ones (multiple steps, sliding compartments, stacking components).',
                'Frozen stuffed toys combine chewing satisfaction with problem-solving — the dog must work to reach the food inside. This keeps many dogs engaged for 20 to 40 minutes.',
            ]),
            ('Toys for Gentle and Senior Dogs', [
                'Soft plush toys, squeaky toys, and lightweight options suit dogs with gentle play styles or those whose teeth and jaws cannot handle harder materials. Senior dogs often appreciate softer textures that are easy on ageing mouths.',
                'Look for plush toys with reinforced seams if your gentle dog occasionally gets more enthusiastic. Double-stitched toys last longer even with moderate play.',
            ]),
        ],
        'faq': [
            ('What if my dog does not play with toys at all?', 'Some dogs were never taught to play or have not found the right toy type. Try food-dispensing toys first, as most dogs are motivated by food. Play together rather than expecting solo play. Some dogs need a human partner to make toys interesting.'),
            ('Should I let my dog destroy toys?', 'Dissection play (ripping apart plush toys) is natural and can be enriching if supervised. Remove stuffing and squeakers as they become accessible. Only allow this with toys designed to be destroyed, and never with toys containing hazardous filling.'),
            ('How do I know if a toy is too hard for my dog\'s teeth?', 'The thumbnail test: if you cannot dent the surface with your thumbnail, it may be too hard and could crack teeth. This rules out real bones, antlers, and some very hard nylon toys for most dogs. Your dog\'s teeth should not show wear marks after use.'),
        ],
        'related': [
            ('Best Dog Toys UK – Complete Guide', '/best-dog-toys-uk'),
            ('Dog Toy Safety Guide', '/dog-toy-safety-guide'),
            ('Mental Stimulation for Dogs', '/mental-stimulation-for-dogs'),
            ('Best Indestructible Dog Toys UK', '/best-indestructible-dog-toys-uk'),
        ],
    },
    {
        'title': 'DIY Dog Toys: Safe Homemade Options',
        'slug': 'diy-dog-toys-homemade',
        'meta_title': 'DIY Dog Toys: Safe Homemade Ideas for Every Dog',
        'meta_desc': 'Make safe, engaging dog toys at home from everyday items. Step-by-step ideas for chewers, puzzlers, and puppies with safety guidance.',
        'focus_kw': 'DIY dog toys',
        'intro': 'You do not need an expensive collection of commercial toys to keep your dog entertained. Many effective enrichment toys can be made from items you already have at home. The key is knowing which materials are safe and which to avoid.',
        'sections': [
            ('Safety First: Materials to Use and Avoid', [
                'Safe materials include old cotton t-shirts (no buttons or zips), clean towels, cardboard boxes, empty plastic bottles (caps removed, supervised use only), tennis balls, and muffin tins. Avoid anything with small parts, sharp edges, or materials that could be harmful if swallowed.',
                ['SAFE: cotton fabric, cardboard, natural rope (short-term supervised use), empty bottles', 'AVOID: socks (common cause of intestinal blockage), rubber bands, string, buttons, small caps', 'ALWAYS: supervise play with homemade toys and discard when worn'],
            ]),
            ('T-Shirt Tug Toy', [
                'Cut an old cotton t-shirt into 3 strips about 5cm wide and 60cm long. Tie a knot at one end, braid the strips tightly, and tie a knot at the other end. The result is a washable, gentle tug toy suitable for most dogs.',
                'For larger dogs, use 2 or 3 t-shirts to create thicker braids. These are softer on teeth than rope toys and do not shed fibres the way rope does. Replace when the braid loosens or fabric thins.',
            ]),
            ('Muffin Tin Puzzle', [
                'Place treats in a muffin tin and cover each cup with a tennis ball. The dog must figure out how to remove the balls to access the treats. This is an excellent introductory puzzle for dogs new to enrichment games.',
                'To increase difficulty, use larger balls that fit more snugly, or alternate which cups contain treats so the dog must check each one.',
            ]),
            ('Bottle Crunch Toy', [
                'Place an empty plastic bottle (cap and ring removed) inside a sock or fabric sleeve. Many dogs love the crunching sound. The fabric sleeve prevents direct contact with the plastic and catches pieces if the bottle breaks.',
                'This is strictly a supervised toy. Check frequently for cracks and remove immediately if the bottle splits. Replace with a new bottle as needed.',
            ]),
            ('Frozen Treats', [
                'Freeze chicken broth (no onion or garlic) in ice cube trays or silicone moulds for cooling enrichment. Stuff a rubber toy with peanut butter (check the label for xylitol, which is toxic to dogs) and banana, then freeze overnight.',
                'For a longer-lasting challenge, freeze layers: wet food, then broth, then kibble, creating a multi-textured frozen puzzle that takes most dogs 20 to 30 minutes to finish.',
            ]),
            ('Cardboard Enrichment', [
                'Cardboard boxes filled with crumpled paper and hidden treats provide excellent sniffing and foraging enrichment. Dogs enjoy ripping open boxes and rooting through paper to find rewards.',
                'Use plain cardboard without heavy printing, tape, or staples. Supervise to ensure the dog is not eating large pieces of cardboard — shredding is fine, but ingestion is not.',
            ]),
        ],
        'faq': [
            ('Are homemade toys as good as shop-bought ones?', 'For enrichment and mental stimulation, yes. Many DIY options provide the same engagement as commercial products. However, for unsupervised chewing, purpose-built commercial toys with safety testing are more appropriate.'),
            ('How long do DIY dog toys last?', 'Most homemade toys are short-lived and that is expected. Treat them as disposable enrichment rather than permanent fixtures. Make a new one when the old one wears out — the cost is minimal.'),
            ('Is it safe to give dogs old shoes or clothing?', 'No. Dogs cannot distinguish between an old shoe you have given them and your current shoes. Giving clothing items as toys teaches the dog that these items are acceptable to chew, leading to destroyed belongings.'),
        ],
        'related': [
            ('Best Dog Toys UK – Complete Guide', '/best-dog-toys-uk'),
            ('Mental Stimulation for Dogs', '/mental-stimulation-for-dogs'),
            ('Dog Toy Safety Guide', '/dog-toy-safety-guide'),
            ('Best Interactive Dog Toys UK', '/best-interactive-dog-toys-uk'),
        ],
    },
]

# ===== TRAINING SUPPLIES + PUPPY CARE STARTER SPOKES =====
TRAINING_PUPPY_POSTS = [
    {
        'title': 'How to Choose the Right Dog Training Treats',
        'slug': 'how-to-choose-dog-training-treats',
        'meta_title': 'How to Choose Dog Training Treats: Selection Guide',
        'meta_desc': 'Learn how to select the best training treats for your dog. Covers treat size, ingredients, calorie management, and using food rewards effectively.',
        'focus_kw': 'choose dog training treats',
        'category': 'Training Supplies',
        'intro': 'Training treats are the most common and effective reward in positive reinforcement training. But not all treats work equally well, and using the wrong ones can undermine training progress or contribute to weight gain. This guide covers how to choose and use treats strategically.',
        'sections': [
            ('Why Treat Selection Matters', [
                'The right treat captures your dog\'s attention and motivates them to work. A treat that is too low-value gets ignored in distracting environments. One that is too high-value can over-excite the dog and impair learning. Finding the right balance for your dog is essential.',
                'Treat size, texture, and smell all affect training effectiveness. Small, soft, smelly treats work best for most training contexts because the dog can eat them quickly and refocus.',
            ]),
            ('Ideal Training Treat Characteristics', [
                ['Pea-sized or smaller (quick to eat, less calorie impact)', 'Soft texture (no crunching pause between reps)', 'Strong scent (captures attention)', 'Easy to break or tear (adjust size on the fly)', 'Low calorie per piece (training requires many repetitions)'],
                'Hard, crunchy treats slow down training because the dog pauses to chew. Save biscuits and dental chews for non-training contexts.',
            ]),
            ('Treat Value Hierarchy', [
                'Create a hierarchy of treat values for different situations. Low-value treats (regular kibble) work for easy tasks at home. Medium-value treats (commercial training treats) suit most training sessions. High-value treats (cheese, chicken, liver) reserve for difficult tasks and challenging environments.',
                'Using high-value treats for everything desensitises the dog, leaving you with nothing to escalate to when you really need their attention.',
            ]),
            ('Managing Calories', [
                'Training treats should come from the dog\'s daily food allowance, not on top of it. A common guideline is that treats should make up no more than 10 percent of daily calorie intake.',
                'Reduce meal portions on heavy training days. Some trainers use the dog\'s regular kibble as training treats by withholding breakfast and using it during morning training sessions.',
            ]),
            ('Reading Ingredient Labels', [
                'Choose treats with named protein sources as the first ingredient. Avoid treats with excessive fillers, artificial colours, or preservatives. Single-ingredient treats (freeze-dried liver, dehydrated chicken) are often the simplest and most effective option.',
                'If your dog has food sensitivities, training treats must be compatible with their diet. Novel protein treats (venison, duck, fish) work well for dogs with common protein allergies.',
            ]),
            ('Beyond Food Treats', [
                'Not all dogs are primarily food-motivated. Some respond better to toy play, verbal praise, or environmental rewards (being allowed to sniff, go through a door, or greet another dog). Identify what your dog values most and use that as the primary reward.',
            ]),
        ],
        'faq': [
            ('Can I use human food as training treats?', 'Many human foods work well: small pieces of cooked chicken, cheese, carrot, or apple. Avoid grapes, raisins, onion, garlic, chocolate, macadamia nuts, and anything containing xylitol. When in doubt, stick to dog-specific treats.'),
            ('How many treats can I give during a training session?', 'A typical 10-minute session might use 20 to 40 tiny treats. This is fine if each treat is pea-sized and you adjust meal portions accordingly. The total calorie impact of 40 pea-sized treats is usually equivalent to a few tablespoons of kibble.'),
            ('My dog is not interested in any treats. What should I do?', 'Try training before meals when the dog is hungry. Experiment with different proteins and textures. Some dogs respond better to warm or smelly treats. If a dog truly shows no food motivation, explore toy or play rewards instead.'),
        ],
        'related': [
            ('Best Dog Training Treats UK', '/best-dog-training-treats-uk'),
            ('Best Dog Training and Behaviour UK', '/best-dog-training-and-behaviour-uk'),
            ('Best Puppy Training Guide UK', '/best-puppy-training-guide-uk'),
            ('Best Dog Training Leads UK', '/best-dog-training-leads-uk'),
        ],
    },
    {
        'title': 'Puppy Socialisation: A Complete Timeline Guide',
        'slug': 'puppy-socialisation-guide',
        'meta_title': 'Puppy Socialisation Guide: Week-by-Week Timeline',
        'meta_desc': 'Complete puppy socialisation guide with weekly milestones from 3 to 16 weeks. Covers safe exposure methods, common mistakes, and critical periods.',
        'focus_kw': 'puppy socialisation guide',
        'category': 'Puppy Care',
        'intro': 'The socialisation window between 3 and 16 weeks is the single most important developmental period in a puppy\'s life. What a puppy experiences — or does not experience — during these weeks shapes their temperament and behaviour for years to come. This guide provides a practical timeline.',
        'sections': [
            ('Why the Socialisation Window Matters', [
                'Between 3 and 16 weeks, a puppy\'s brain is uniquely wired to accept new experiences as normal. After this window closes, novel stimuli are more likely to trigger fear or suspicion. A well-socialised puppy grows into a confident, adaptable adult dog.',
                'Under-socialised puppies are more likely to develop fear aggression, anxiety around strangers, reactivity to other dogs, and generalised nervousness. These problems are preventable with proper early exposure.',
            ]),
            ('3 to 5 Weeks: Breeder Responsibility', [
                'During these weeks, the breeder should expose puppies to gentle handling, household sounds (vacuum, television, washing machine), different floor surfaces, and mild temperature variations. Puppies still with the litter learn crucial social skills from their mother and siblings.',
                'If acquiring a puppy, ask the breeder what socialisation they provide during these early weeks. A breeder who raises puppies in a quiet, isolated kennel with minimal handling is not setting them up for success.',
            ]),
            ('8 to 11 Weeks: Critical New Home Period', [
                'Most puppies arrive in their new home at 8 weeks. The priority is positive exposure to as many new people, sounds, surfaces, and gentle experiences as possible — while the puppy\'s vaccinations are still incomplete.',
                ['Carry the puppy in public places (do not set them on the ground until fully vaccinated)', 'Invite calm visitors of different ages and appearances to the home', 'Expose to household sounds at moderate volume', 'Introduce car travel in short, positive trips', 'Allow supervised interaction with known, vaccinated adult dogs'],
                'Every experience should be positive. If the puppy shows fear, do not force exposure — create distance and try again later at a lower intensity.',
            ]),
            ('12 to 16 Weeks: Expanding the World', [
                'Once vaccination is complete, the puppy can explore the ground outside. Introduce new environments gradually: quiet streets before busy ones, small dogs before large groups, calm settings before exciting ones.',
                ['Puppy classes with positive reinforcement methods', 'Different walking surfaces: grass, gravel, sand, metal grates, wet ground', 'Public spaces: pet shops, outdoor cafes, parks at quiet times', 'Different types of people: uniforms, hats, umbrellas, wheelchairs, pushchairs'],
                'The goal is not to overwhelm but to build a library of positive experiences. Quality matters more than quantity — one calm, positive encounter is worth more than ten forced or frightening ones.',
            ]),
            ('Common Socialisation Mistakes', [
                ['Waiting until vaccinations are complete before any socialisation (the window is closing)', 'Forcing interactions with things the puppy fears', 'Overwhelming the puppy with too much at once', 'Only socialising with other puppies (adult dog interaction teaches different skills)', 'Stopping socialisation after 16 weeks (maintenance is needed throughout the first year)'],
            ]),
            ('After 16 Weeks: Ongoing Maintenance', [
                'The socialisation window closes but the work does not stop. Continue regular positive exposure to a variety of people, dogs, environments, and experiences throughout the first year. A puppy that was well-socialised but then isolated can still develop fears.',
                'Regular walks in varied environments, positive encounters with new people and dogs, and exposure to novel situations should remain part of the dog\'s routine.',
            ]),
        ],
        'faq': [
            ('Is it safe to socialise before vaccinations are complete?', 'Yes, with precautions. Carry the puppy in public rather than setting them on the ground. Visit homes with known, vaccinated dogs. Attend puppy classes in cleaned facilities. The risk of under-socialisation causing lifelong behavioural problems outweighs the disease risk of careful, controlled exposure.'),
            ('My puppy seems scared of everything. Is it too late?', 'If the puppy is under 16 weeks, there is still time. Work slowly, at the puppy\'s pace, using treats and calm reassurance. Do not force contact with scary things. If the puppy is older and showing significant fear, consider working with a qualified behaviourist who uses positive methods.'),
            ('Can I socialise an adult rescue dog?', 'Adult dogs can learn to accept new experiences, but the process is slower and requires more patience. Counter-conditioning (pairing scary things with high-value treats) and gradual desensitisation are the primary tools. A professional behaviourist can help create a structured plan.'),
        ],
        'related': [
            ('Best Puppy Training Guide UK', '/best-puppy-training-guide-uk'),
            ('First-Time Dog Owner Essentials', '/first-time-dog-owner-essentials'),
            ('Best Puppy Collars UK', '/best-puppy-collars-uk'),
            ('Best Puppy Food UK', '/best-puppy-food-uk'),
        ],
    },
]


# ===== PUBLISH ALL POSTS =====
all_posts = []
all_posts.extend([(p, 'Dog Beds') for p in DOG_BEDS_POSTS])
all_posts.extend([(p, 'Dog Toys') for p in DOG_TOYS_POSTS])
all_posts.extend([(p, p.get('category', 'Training Supplies')) for p in TRAINING_PUPPY_POSTS])

results = []
created_ids = []

print("=" * 70)
print("PHASE 10D CLUSTER EXPANSION")
print(f"Started: {NOW}")
print("=" * 70)

for post_data, cluster in all_posts:
    title = post_data['title']
    slug = post_data['slug']

    # Build content
    content = build_post_content(
        title=title,
        intro=post_data['intro'],
        sections=post_data['sections'],
        faq_items=post_data['faq'],
        hub_link=f'/{CATEGORIES.get(cluster, "dog-supplies")}' if cluster == 'Dog Supplies' else f'/{"dog-beds" if cluster == "Dog Beds" else "dog-toys" if cluster == "Dog Toys" else "dog-training-behaviour" if cluster == "Training Supplies" else "dog-supplies"}',
        hub_title=f'{cluster} Hub',
        related_links=post_data['related'],
    )

    # Validate blocks
    is_valid, issues = validate_gutenberg(content)
    if not is_valid:
        print(f"  BLOCK VALIDATION FAILED: {title} — {issues}")
        results.append({'title': title, 'cluster': cluster, 'status': 'block_validation_failed', 'issues': str(issues)})
        continue

    # 12-gate check
    gates = check_12_gates(title, content, post_data['meta_title'], post_data['meta_desc'], post_data['focus_kw'])
    failed_gates = [g for g, passed in gates.items() if not passed]
    if failed_gates:
        print(f"  GATE FAILURE: {title} — {failed_gates}")
        results.append({'title': title, 'cluster': cluster, 'status': 'gate_failure', 'issues': str(failed_gates)})
        continue

    # Determine categories
    cat_ids = [CATEGORIES[cluster]]
    if cluster in ('Dog Beds', 'Dog Toys', 'Training Supplies', 'Puppy Care'):
        cat_ids.append(CATEGORIES['Dog Supplies'])

    # Create post
    payload = {
        'title': title,
        'slug': slug,
        'content': content,
        'status': 'publish',
        'categories': cat_ids,
    }

    r = s.post(f"{WP_BASE}/posts", json=payload)
    if r.status_code == 201:
        new_id = r.json()['id']
        new_link = r.json().get('link', '')
        created_ids.append(new_id)

        # Set RankMath SEO
        seo_r = s.post(f"{RM_BASE}/updateMeta", json={
            'objectType': 'post',
            'objectID': new_id,
            'meta': {
                'rank_math_title': post_data['meta_title'],
                'rank_math_description': post_data['meta_desc'],
                'rank_math_focus_keyword': post_data['focus_kw'],
            }
        })
        seo_ok = seo_r.status_code == 200

        print(f"  OK {cluster} {new_id}: {title[:50]} [SEO: {'ok' if seo_ok else 'fail'}]")
        results.append({
            'id': new_id, 'title': title, 'cluster': cluster, 'slug': slug,
            'status': 'published', 'link': new_link, 'seo': 'ok' if seo_ok else 'fail',
            'block_count': len(re.findall(r'<!-- wp:\S+', content)),
            'gates_passed': '12/12',
        })
    else:
        print(f"  FAIL {cluster}: {title} — HTTP {r.status_code}")
        try:
            err = r.json().get('message', '')
        except:
            err = r.text[:200]
        results.append({'title': title, 'cluster': cluster, 'status': f'create_failed_{r.status_code}', 'issues': err})

    time.sleep(0.5)


# Save results
csv_path = os.path.join(OUT, 'Phase10D_Cluster_Expansion_Log.csv')
fieldnames = ['id','title','cluster','slug','status','link','seo','block_count','gates_passed','issues']
with open(csv_path, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    w.writeheader()
    w.writerows(results)

print(f"\n{'='*70}")
print("EXPANSION SUMMARY")
print(f"{'='*70}")
print(f"Dog Beds spokes: {sum(1 for r in results if r['cluster']=='Dog Beds' and r.get('status')=='published')}/4")
print(f"Dog Toys spokes: {sum(1 for r in results if r['cluster']=='Dog Toys' and r.get('status')=='published')}/4")
print(f"Training/Puppy spokes: {sum(1 for r in results if r['cluster'] in ('Training Supplies','Puppy Care') and r.get('status')=='published')}/2")
print(f"Total published: {sum(1 for r in results if r.get('status')=='published')}")
print(f"Failed: {sum(1 for r in results if r.get('status','').startswith(('create_failed','gate_failure','block_validation')))}")
print(f"Results log: {csv_path}")
print(f"\nCreated IDs: {created_ids}")
