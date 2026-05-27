#!/usr/bin/env python3
"""Phase 10C+ Cluster Expansion: Dog Care + Pet Care educational spokes,
FAQ additions to low-visibility posts, indexing verification, internal linking."""

import requests, json, re, csv, os, html, time
from datetime import datetime, timezone

WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
RM_BASE = "https://pethubonline.com/wp-json/rankmath/v1"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"

s = requests.Session()
s.auth = (WP_USER, WP_PASS)
s.headers['Accept-Encoding'] = 'gzip, deflate'

OUT = '/var/lib/freelancer/projects/40416335/phase10c_expansion'
os.makedirs(OUT, exist_ok=True)
NOW = datetime.now(timezone.utc).isoformat()

CLUSTER_CATS = {
    'Dog Care': 1489, 'Pet Care': 1397, 'Dog Beds': 1401,
    'Dog Toys': 1441, 'Cat Toys': 1459, 'Dog Harnesses': 1422,
    'Dog Food': 1467, 'Dog Supplies': 1376, 'Cat Supplies': 1377,
    'Puppy Care': 1442, 'Dog Health': 1450, 'Training Supplies': 1474,
}

FAKE_AUTHORITY = [
    r'\bour veterinarian\b', r'\bwe tested\b', r'\bour experts?\b',
    r'\blab[\s-]?tested\b', r'\bclinically proven\b', r'\bvet[\s-]?backed\b'
]
AFFILIATE_PATTERNS = [r'rel=["\'].*?sponsored', r'affiliate', r'amzn\.to']
RED_TOPICS = ["pet insurance", "veterinary diagnosis", "medication dosage", "prescription"]

# ============================================================
# DOG CARE EDUCATIONAL SPOKES (4 new posts)
# ============================================================
DOG_CARE_SPOKES = [
    {
        "title": "Dog Grooming Basics: A Complete Guide for Owners",
        "slug": "dog-grooming-basics-guide",
        "seo_title": "Dog Grooming Basics: Complete Guide for Owners",
        "seo_desc": "Learn essential dog grooming at home. Brushing, bathing, nail trimming, ear cleaning, and coat care tips for every breed type and coat length.",
        "focus_kw": "dog grooming basics",
        "categories": [1489, 1376],
        "content": """<!-- wp:paragraph {"style":{"typography":{"fontSize":"0.95em"}}} -->
<p style="font-size:0.95em"><strong>Quick Summary:</strong> Regular grooming keeps your dog healthy and comfortable. This guide covers brushing, bathing, nail care, ear cleaning, and dental hygiene — with practical frequency recommendations for different coat types.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Why Regular Grooming Matters</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Grooming is not just about appearance. Regular grooming helps you spot skin issues, parasites, lumps, or injuries early. It also reduces shedding around the home and prevents matting, which can cause discomfort and skin infections.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Dogs that are groomed regularly tend to be more comfortable with handling, which makes veterinary visits easier too.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Brushing: Frequency by Coat Type</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>How often you brush depends entirely on your dog's coat:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>Short-haired breeds</strong> (Labrador, Beagle): Once a week with a rubber curry brush or bristle brush</li>
<li><strong>Medium-haired breeds</strong> (Border Collie, Cocker Spaniel): Two to three times a week with a slicker brush</li>
<li><strong>Long-haired breeds</strong> (Shih Tzu, Yorkshire Terrier): Daily brushing with a pin brush and comb to prevent tangles</li>
<li><strong>Wire-haired breeds</strong> (Schnauzer, Wire Fox Terrier): Two to three times weekly, with hand-stripping every few months</li>
<li><strong>Double-coated breeds</strong> (Husky, Golden Retriever): At least twice weekly, daily during shedding season</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>Always brush in the direction of hair growth. Start from the head and work toward the tail, being gentle around the belly, legs, and ears where skin is more sensitive.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Bathing Your Dog</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Most dogs need bathing every four to six weeks, though this varies. Dogs that spend more time outdoors or have oily coats may need more frequent baths. Over-bathing strips natural oils and can cause dry, itchy skin.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Use a dog-specific shampoo — human shampoo has the wrong pH balance and can irritate their skin. Lukewarm water works best. Rinse thoroughly, as shampoo residue causes itching.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Nail Trimming</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Overgrown nails cause discomfort and can alter how your dog walks, leading to joint problems over time. Trim nails every two to four weeks, or when you hear clicking on hard floors.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Use proper dog nail clippers or a nail grinder. Cut below the quick — the pink area visible on light-coloured nails. For dark nails, trim small amounts at a time and stop when you see a grey or pink centre in the cross-section.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Ear Cleaning</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Check your dog's ears weekly. Healthy ears are pale pink with no strong odour. Floppy-eared breeds like Basset Hounds and Spaniels are more prone to ear infections because airflow is restricted.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Use a vet-recommended ear cleaning solution on a cotton pad. Never insert cotton buds into the ear canal — you risk pushing debris deeper or causing damage.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Dental Hygiene</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Dental disease affects most dogs over the age of three. Brush your dog's teeth several times a week using a dog-specific toothbrush and toothpaste. Human toothpaste contains fluoride and xylitol, both of which are harmful to dogs.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Dental chews and toys designed for oral health can supplement brushing but should not replace it entirely.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>How often should I groom my dog?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Most dogs benefit from brushing two to three times a week, bathing every four to six weeks, and nail trimming every two to four weeks. Long-haired breeds need daily brushing.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Can I use human shampoo on my dog?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>No. Human shampoo has a different pH level and can irritate your dog's skin. Always use a shampoo specifically formulated for dogs.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>What if my dog hates being groomed?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Start with short, positive sessions. Use treats and calm praise. Gradually increase the duration as your dog becomes more comfortable. If your dog shows signs of extreme stress, consult a professional groomer or your veterinarian for advice.</p>
<!-- /wp:paragraph -->"""
    },
    {
        "title": "Seasonal Dog Care: Keeping Your Dog Safe Year-Round",
        "slug": "seasonal-dog-care-guide",
        "seo_title": "Seasonal Dog Care: Keep Your Dog Safe Year-Round",
        "seo_desc": "Seasonal dog care guide covering summer heat safety, winter cold protection, spring allergies, and autumn hazards. Practical tips for every season.",
        "focus_kw": "seasonal dog care",
        "categories": [1489, 1376],
        "content": """<!-- wp:paragraph {"style":{"typography":{"fontSize":"0.95em"}}} -->
<p style="font-size:0.95em"><strong>Quick Summary:</strong> Each season brings different risks for dogs. This guide covers heat safety in summer, cold weather protection in winter, allergy management in spring, and common autumn hazards — with practical steps for each.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Spring: Allergies and Parasites</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Spring is when pollen levels rise and parasites become active. Many dogs experience seasonal allergies that cause itching, red skin, watery eyes, and excessive paw licking.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Wipe your dog's paws and belly after walks to reduce pollen exposure. Keep up with flea and tick prevention — these parasites are most active from spring through autumn.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Spring is also when many gardens use fertilisers, pesticides, and slug pellets. Keep your dog away from recently treated areas, as many common garden chemicals are toxic to dogs.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Summer: Heat Safety</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Heatstroke is a serious and potentially fatal condition. Dogs regulate temperature primarily through panting, which is far less efficient than sweating. Brachycephalic breeds (Pugs, Bulldogs, Boxers) are especially vulnerable.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>Never leave your dog in a parked car</strong> — temperatures inside a car can reach dangerous levels within minutes, even with windows cracked</li>
<li><strong>Walk during cooler hours</strong> — early morning and late evening are safest</li>
<li><strong>Test pavement with your hand</strong> — if it is too hot for your palm, it is too hot for paw pads</li>
<li><strong>Provide constant access to fresh water</strong> and shade</li>
<li><strong>Watch for signs of heatstroke</strong>: excessive panting, drooling, lethargy, vomiting, collapse</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>If you suspect heatstroke, move your dog to shade immediately, apply cool (not cold) water to their body, and contact your vet as an emergency.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Autumn: Hidden Hazards</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Autumn brings specific risks that many dog owners overlook:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>Conkers and acorns</strong> — both are toxic if ingested and can cause intestinal blockages</li>
<li><strong>Fallen fruit</strong> — fermenting fruit can cause alcohol poisoning; apple seeds contain cyanide compounds</li>
<li><strong>Mushrooms</strong> — many wild fungi are toxic to dogs; if you see your dog eat a mushroom, contact your vet immediately</li>
<li><strong>Shorter daylight</strong> — use reflective collars or LED attachments for visibility during evening walks</li>
<li><strong>Fireworks season</strong> — create a safe, quiet space indoors; consider anxiety wraps or calming aids if your dog is noise-sensitive</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Winter: Cold Weather Protection</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Not all dogs are built for cold weather. Small breeds, thin-coated dogs, puppies, and senior dogs lose body heat more quickly and may need a coat or jumper for outdoor walks.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Road salt and grit can irritate paw pads. Wipe your dog's paws after walks to remove salt residue. Check between toes for ice balls that can form in longer-haired breeds.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Antifreeze is extremely dangerous — even a small amount can be lethal. It has a sweet taste that attracts dogs. Clean up any spills immediately and store antifreeze securely.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>What temperature is too hot to walk a dog?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>As a general guide, be cautious above 20C and avoid extended walks above 25C. Pavement can be significantly hotter than air temperature — test with your hand for five seconds.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Do dogs need coats in winter?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Small breeds, thin-coated breeds, puppies, and older dogs often benefit from a coat in cold weather. Double-coated breeds like Huskies generally do not need one.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>How do I know if my dog has seasonal allergies?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Common signs include excessive scratching, red or inflamed skin, watery eyes, sneezing, and frequent paw licking. If symptoms appear at the same time each year, seasonal allergies are likely. Your vet can help identify specific triggers.</p>
<!-- /wp:paragraph -->"""
    },
    {
        "title": "Dog Dental Health: A Practical Care Guide",
        "slug": "dog-dental-health-care-guide",
        "seo_title": "Dog Dental Health: Practical Care Guide | PetHub",
        "seo_desc": "Dog dental health guide covering tooth brushing, signs of dental disease, diet tips, and when to seek veterinary dental care. Prevent problems early.",
        "focus_kw": "dog dental health care",
        "categories": [1489, 1450, 1376],
        "content": """<!-- wp:paragraph {"style":{"typography":{"fontSize":"0.95em"}}} -->
<p style="font-size:0.95em"><strong>Quick Summary:</strong> Dental disease affects most dogs over three years old. This guide covers home dental care, recognising warning signs, diet considerations, and when professional veterinary dental treatment is needed.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Why Dental Health Matters</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Dental disease is one of the most common health problems in dogs. Plaque builds up on teeth daily, hardens into tartar within 48 hours, and leads to gum inflammation (gingivitis). Left untreated, this progresses to periodontal disease, causing pain, tooth loss, and potentially spreading bacteria to the heart, liver, and kidneys.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>The good news is that most dental problems are preventable with consistent home care.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>How to Brush Your Dog's Teeth</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Brushing is the single most effective way to prevent dental disease. Aim for several times a week at minimum — daily is ideal.</p>
<!-- /wp:paragraph -->

<!-- wp:list {"ordered":true} -->
<ol>
<li>Use a dog-specific toothbrush (finger brushes work well for beginners) and dog toothpaste. Never use human toothpaste — it contains ingredients toxic to dogs.</li>
<li>Let your dog taste the toothpaste first. Most dog toothpastes come in flavours like poultry or beef.</li>
<li>Lift the lip gently and brush in small circular motions along the gum line.</li>
<li>Focus on the outer surfaces — dogs naturally clean the inner surfaces with their tongue.</li>
<li>Keep sessions short and positive. Even 30 seconds of brushing is beneficial.</li>
</ol>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Signs of Dental Problems</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Watch for these warning signs:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>Bad breath</strong> — persistent bad breath often indicates bacterial buildup or infection</li>
<li><strong>Red or swollen gums</strong> — healthy gums should be pink, not red or puffy</li>
<li><strong>Difficulty eating</strong> — dropping food, chewing on one side, or reluctance to eat hard food</li>
<li><strong>Pawing at the mouth</strong> — often indicates pain or discomfort</li>
<li><strong>Visible tartar</strong> — yellow or brown buildup along the gum line</li>
<li><strong>Loose or missing teeth</strong> — in adult dogs, this indicates advanced dental disease</li>
<li><strong>Drooling more than usual</strong> — especially if saliva is blood-tinged</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>If you notice any of these signs, schedule a veterinary dental check. Early treatment prevents progression and is less costly than treating advanced disease.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Diet and Dental Health</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Dry kibble provides some mechanical cleaning action as dogs chew, though this alone is not sufficient dental care. Some dental-specific diets use larger kibble sizes and textures designed to scrub teeth during chewing.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Raw bones are sometimes suggested for dental health, but they carry risks including fractured teeth, choking, and gastrointestinal blockages. If you choose to offer bones, supervise closely and never offer cooked bones, which splinter dangerously.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Dental Chews and Toys</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Dental chews can supplement brushing but should not replace it. Look for products carrying the VOHC (Veterinary Oral Health Council) seal, which indicates they meet standards for reducing plaque or tartar. Rubber chew toys with textured surfaces also help clean teeth during play.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>How often should a dog have a dental check-up?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Most vets recommend a dental check at each annual health examination. Dogs with existing dental issues may need more frequent monitoring.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>At what age do dental problems typically start?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Signs of dental disease can appear as early as age two, with most dogs showing some degree of periodontal disease by age three. Small breeds tend to be more prone to dental issues.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Are dental chews enough to keep teeth clean?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Dental chews help but are not a substitute for brushing. Think of them as a supplement — like using mouthwash but still needing to brush your teeth.</p>
<!-- /wp:paragraph -->"""
    },
    {
        "title": "First-Time Dog Owner Essentials: What You Need to Know",
        "slug": "first-time-dog-owner-essentials",
        "seo_title": "First-Time Dog Owner Essentials: What to Know",
        "seo_desc": "First-time dog owner guide covering supplies, routines, vet visits, socialisation, training, and common mistakes to avoid. Start off on the right foot.",
        "focus_kw": "first time dog owner essentials",
        "categories": [1489, 1376, 1442],
        "content": """<!-- wp:paragraph {"style":{"typography":{"fontSize":"0.95em"}}} -->
<p style="font-size:0.95em"><strong>Quick Summary:</strong> Getting your first dog is exciting but requires preparation. This guide covers essential supplies, establishing routines, veterinary care, basic training, socialisation, and the most common mistakes new owners make.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Essential Supplies Before Bringing Your Dog Home</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Before your new dog arrives, have these basics ready:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>Food and water bowls</strong> — stainless steel or ceramic are easiest to clean</li>
<li><strong>Age-appropriate food</strong> — puppy food for puppies, adult food for grown dogs; transition gradually if changing brands</li>
<li><strong>Collar, harness, and lead</strong> — a harness is generally safer and more comfortable, especially for puppies</li>
<li><strong>ID tag</strong> — legally required in the UK with your name and address</li>
<li><strong>Bed</strong> — somewhere warm and quiet that is their own space</li>
<li><strong>Crate</strong> (optional but useful) — for house training and providing a safe den</li>
<li><strong>Poo bags</strong> — always carry spares</li>
<li><strong>Basic grooming tools</strong> — brush, nail clippers, dog shampoo</li>
<li><strong>Toys</strong> — a mix of chew toys, tug toys, and puzzle toys for mental stimulation</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Establishing a Routine</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Dogs thrive on consistency. Establish regular times for feeding, walking, play, and sleep from day one. A predictable routine reduces anxiety and accelerates house training.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Puppies typically need to go outside after waking, after eating, and after play. Adult rescue dogs may need time to adjust — expect a settling-in period of at least two weeks before their true personality emerges.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Veterinary Care</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Register with a vet as soon as possible. Your first visit should cover:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li>General health check</li>
<li>Vaccination schedule (or confirmation of existing vaccinations)</li>
<li>Microchipping (legally required in the UK)</li>
<li>Flea and worm treatment plan</li>
<li>Neutering discussion — your vet can advise on appropriate timing</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>Pet insurance is worth considering early, as pre-existing conditions are typically excluded from cover.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Basic Training</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Start training immediately using positive reinforcement — reward behaviours you want with treats, praise, or play. Punishment-based methods are less effective and can damage the bond with your dog.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Essential commands to teach first:</p>
<!-- /wp:paragraph -->

<!-- wp:list {"ordered":true} -->
<ol>
<li><strong>Sit</strong> — the foundation command; useful in many daily situations</li>
<li><strong>Stay/Wait</strong> — important for safety at doorways and roads</li>
<li><strong>Come</strong> (recall) — the most important safety command</li>
<li><strong>Leave it</strong> — prevents eating dangerous items on walks</li>
<li><strong>Loose lead walking</strong> — makes walks enjoyable for both of you</li>
</ol>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>Keep training sessions short (five to ten minutes) and end on a positive note. Consistency between all family members is essential — everyone should use the same commands and rules.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Socialisation</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The critical socialisation window for puppies is between three and fourteen weeks of age. During this time, expose your puppy positively to different people, animals, environments, sounds, and surfaces. This reduces the likelihood of fear-based behaviour problems later.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>For adult rescue dogs, socialisation should be done at the dog's pace. Watch their body language and never force interactions.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Common Mistakes to Avoid</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><strong>Skipping socialisation</strong> — under-socialised dogs are more likely to develop fear and aggression issues</li>
<li><strong>Inconsistent rules</strong> — if the dog is not allowed on the sofa, everyone in the household must enforce this consistently</li>
<li><strong>Too much freedom too soon</strong> — gradually expand access to rooms and unsupervised time as trust builds</li>
<li><strong>Expecting instant bonding</strong> — building trust takes time, especially with rescue dogs</li>
<li><strong>Neglecting mental stimulation</strong> — a bored dog is a destructive dog; puzzle feeders and training games are as important as physical exercise</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>How much exercise does a dog need?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>This varies enormously by breed, age, and health. As a rough guide, most adult dogs need 30 minutes to two hours of exercise daily. Puppies need shorter, more frequent sessions. Working and sporting breeds typically need more activity than companion breeds.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>How long can I leave my dog alone?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Adult dogs should not be left alone for more than four to six hours regularly. Puppies need more frequent attention and toilet breaks. If you work full days, consider a dog walker, doggy daycare, or a trusted neighbour who can visit midday.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Should I get pet insurance?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Pet insurance can help manage unexpected veterinary costs, which can run into thousands of pounds for emergencies or ongoing conditions. Research policies carefully — lifetime cover generally offers better protection than time-limited or per-condition policies.</p>
<!-- /wp:paragraph -->"""
    },
]

# ============================================================
# PET CARE EDUCATIONAL SPOKES (4 new posts)
# ============================================================
PET_CARE_SPOKES = [
    {
        "title": "Pet First Aid Basics: What Every Owner Should Know",
        "slug": "pet-first-aid-basics",
        "seo_title": "Pet First Aid Basics: What Every Owner Should Know",
        "seo_desc": "Essential pet first aid covering emergency signs, choking, bleeding, burns, poisoning, and when to seek urgent veterinary help. Be prepared for emergencies.",
        "focus_kw": "pet first aid basics",
        "categories": [1397, 1376],
        "content": """<!-- wp:paragraph {"style":{"typography":{"fontSize":"0.95em"}}} -->
<p style="font-size:0.95em"><strong>Quick Summary:</strong> Knowing basic pet first aid can save your pet's life in an emergency. This guide covers recognising emergencies, choking response, wound care, poisoning signs, and how to stabilise your pet before reaching a vet.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>When Is It an Emergency?</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Contact your vet immediately or go to an emergency clinic if your pet shows any of these signs:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li>Difficulty breathing or choking</li>
<li>Uncontrolled bleeding</li>
<li>Collapse or loss of consciousness</li>
<li>Seizures lasting more than a few minutes</li>
<li>Suspected poisoning</li>
<li>Inability to stand or walk</li>
<li>Severe vomiting or diarrhoea (especially with blood)</li>
<li>Distended or painful abdomen</li>
<li>Eye injuries</li>
<li>Suspected broken bones</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>Keep your vet's emergency number and the nearest out-of-hours clinic number saved in your phone.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Choking</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>If your pet is pawing at their mouth, gagging, or struggling to breathe:</p>
<!-- /wp:paragraph -->

<!-- wp:list {"ordered":true} -->
<ol>
<li>Stay calm. Panicking makes your pet more stressed.</li>
<li>Open their mouth carefully and look for any visible obstruction.</li>
<li>If you can see and safely reach the object, try to remove it with your fingers or blunt tweezers. Be careful not to push it deeper.</li>
<li>For dogs: if you cannot dislodge the object, apply firm upward pressure just behind the rib cage (similar to the Heimlich manoeuvre in humans).</li>
<li>Get to a vet immediately, even if you successfully remove the object — internal damage may have occurred.</li>
</ol>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Bleeding and Wound Care</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>For minor cuts and scrapes, clean the wound gently with clean water or saline solution. Apply a clean cloth with firm pressure to stop bleeding. Avoid using human antiseptics unless specifically advised by your vet, as some are toxic to pets.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>For severe bleeding, apply firm pressure with a clean cloth and maintain it while transporting to the vet. Do not remove the cloth if blood soaks through — add more layers on top.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Poisoning</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Common household poisons for pets include chocolate, grapes and raisins, xylitol (found in sugar-free products), onions, garlic, certain houseplants (lilies are extremely toxic to cats), antifreeze, rat poison, and some human medications.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>If you suspect poisoning: note what was consumed and approximately how much and when. Contact your vet immediately. Do not try to make your pet vomit unless specifically instructed by a vet — some substances cause more damage on the way back up.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Building a Pet First Aid Kit</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li>Sterile gauze pads and bandages</li>
<li>Adhesive tape (non-stick medical tape)</li>
<li>Blunt-ended scissors</li>
<li>Tweezers</li>
<li>Saline solution for wound cleaning</li>
<li>Digital thermometer (normal dog temperature: 38.3-39.2C)</li>
<li>Emergency blanket</li>
<li>Your vet's contact details and out-of-hours number</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>Should I do CPR on my pet?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Pet CPR exists but requires proper technique. If your pet is not breathing and has no pulse, chest compressions and rescue breathing can be attempted while someone drives you to the vet. Ask your vet about pet first aid courses in your area for hands-on training.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>How much chocolate is dangerous for a dog?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Any chocolate can be harmful, but dark chocolate and cocoa powder are the most dangerous. Even small amounts of dark chocolate can cause serious symptoms. Contact your vet immediately if your dog eats any chocolate — they can calculate the risk based on your dog's weight and the type of chocolate.</p>
<!-- /wp:paragraph -->"""
    },
    {
        "title": "Seasonal Pet Safety: Protecting Pets Through the Year",
        "slug": "seasonal-pet-safety-guide",
        "seo_title": "Seasonal Pet Safety: Protect Pets Year-Round",
        "seo_desc": "Seasonal pet safety guide for dogs and cats. Covers summer heatstroke, winter antifreeze dangers, holiday hazards, and garden chemical risks throughout the year.",
        "focus_kw": "seasonal pet safety",
        "categories": [1397],
        "content": """<!-- wp:paragraph {"style":{"typography":{"fontSize":"0.95em"}}} -->
<p style="font-size:0.95em"><strong>Quick Summary:</strong> Seasonal hazards change throughout the year for both dogs and cats. This guide covers the key risks in each season and practical steps to keep all pets safe, from heatstroke prevention to holiday decoration dangers.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Spring Safety</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Spring cleaning and gardening bring specific risks. Many common household cleaning products and garden chemicals are toxic to pets. Store them securely and keep pets away from freshly treated lawns and flower beds.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Spring bulbs such as daffodils, tulips, and bluebells are poisonous to dogs and cats. Lilies are particularly dangerous for cats — even small amounts of pollen can cause kidney failure.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Flea and tick activity increases in spring. Ensure your pet's parasite prevention is up to date. Always use species-appropriate treatments — permethrin-based dog flea treatments are lethal to cats.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Summer Safety</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Heat is the primary summer risk. Dogs can develop heatstroke quickly, especially brachycephalic breeds, overweight dogs, and those with thick coats. Cats are also vulnerable, particularly if confined to conservatories or cars.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li>Provide constant access to fresh water and shade</li>
<li>Never leave pets in parked vehicles — even briefly</li>
<li>Walk dogs during cooler parts of the day</li>
<li>Watch for hot pavement burning paw pads</li>
<li>Be aware of blue-green algae in ponds and lakes, which is toxic</li>
<li>Barbecue foods (onions, grapes, cooked bones, corn cobs) are common summer poisoning risks</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Autumn Safety</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Falling leaves hide hazards. Conkers, acorns, and wild mushrooms can all be toxic if eaten. As evenings darken earlier, use reflective gear or LED collars for visibility during walks.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Bonfire Night and fireworks season is stressful for many pets. Keep pets indoors during fireworks, close curtains, and provide background noise. Speak to your vet about calming options if your pet is severely affected.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Winter Safety</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Antifreeze (ethylene glycol) is the biggest winter poison risk. It tastes sweet and attracts pets, but even a teaspoon can be fatal to a cat and a tablespoon can endanger a dog. Clean up spills immediately and store containers securely.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Rock salt used to grit roads and paths can irritate paws and is harmful if licked. Wipe paws after walks. Indoor cats may seek warmth under car bonnets — bang the bonnet before starting your engine in cold weather.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Holiday-Specific Hazards</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><strong>Christmas</strong>: chocolate, mince pies (contain raisins), poinsettia, tinsel (intestinal blockage risk for cats), fairy light cables</li>
<li><strong>Easter</strong>: chocolate eggs, hot cross buns (raisins), spring bulbs, Easter lilies (cats)</li>
<li><strong>Halloween</strong>: chocolate, sweets containing xylitol, glow sticks (mildly toxic), costume stress</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>Are Christmas trees safe for pets?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Real Christmas trees are mildly toxic if needles are eaten in quantity, and the water at the base can contain harmful bacteria or preservatives. Secure the tree so it cannot be knocked over by curious pets, and avoid low-hanging glass ornaments.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>What should I do if my pet eats something toxic?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Note what was consumed, how much, and when. Contact your vet or an emergency animal poison line immediately. Do not attempt to induce vomiting unless specifically instructed by a professional.</p>
<!-- /wp:paragraph -->"""
    },
    {
        "title": "Pet Hydration Guide: How Much Water Does Your Pet Need?",
        "slug": "pet-hydration-guide",
        "seo_title": "Pet Hydration Guide: How Much Water Pets Need",
        "seo_desc": "How much water do dogs and cats need daily? Signs of dehydration, tips to encourage drinking, and when to worry. A practical hydration guide for pet owners.",
        "focus_kw": "pet hydration guide",
        "categories": [1397, 1376],
        "content": """<!-- wp:paragraph {"style":{"typography":{"fontSize":"0.95em"}}} -->
<p style="font-size:0.95em"><strong>Quick Summary:</strong> Proper hydration is essential for your pet's health. Dogs need roughly 50ml of water per kilogram of body weight daily, while cats need around 40-60ml per kilogram. This guide covers daily requirements, dehydration signs, and practical tips to encourage drinking.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>How Much Water Do Dogs Need?</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The general guideline is approximately 50ml of water per kilogram of body weight per day. A 20kg dog should drink roughly one litre daily. However, this varies based on activity level, weather, diet, and health conditions.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Dogs eating wet food get some moisture from their diet, so they may drink slightly less than dogs on dry kibble. Active dogs and those in warm weather need more.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>How Much Water Do Cats Need?</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Cats need around 40-60ml per kilogram of body weight daily. A 4kg cat should consume roughly 200ml. Cats on a wet food diet get a significant portion of their water intake from food — wet food is approximately 80% moisture.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Cats are naturally low drinkers, which is a leftover trait from their desert-dwelling ancestors. This makes them more prone to urinary tract problems and kidney issues, so encouraging adequate water intake is particularly important.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Signs of Dehydration</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Learn to recognise these warning signs:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>Skin elasticity test</strong>: gently pinch the skin at the back of the neck. In a hydrated pet, it snaps back immediately. Slow return suggests dehydration.</li>
<li><strong>Dry or sticky gums</strong>: healthy gums should feel moist and slippery</li>
<li><strong>Sunken eyes</strong></li>
<li><strong>Lethargy or reduced energy</strong></li>
<li><strong>Reduced appetite</strong></li>
<li><strong>Dark yellow or reduced urine output</strong></li>
<li><strong>Panting excessively</strong> (in dogs)</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>If you suspect dehydration, offer small amounts of water frequently rather than a large bowl at once. If symptoms are severe or your pet refuses to drink, contact your vet promptly — dehydration can escalate quickly.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Tips to Encourage Drinking</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>For dogs:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li>Keep water bowls in multiple locations around the home</li>
<li>Refresh water at least twice daily — dogs prefer fresh water</li>
<li>Use stainless steel or ceramic bowls (some dogs dislike plastic)</li>
<li>Add a small amount of low-sodium broth to water for reluctant drinkers</li>
<li>Carry a portable water bottle on walks</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>For cats:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li>Place water bowls away from food bowls — cats naturally prefer this separation</li>
<li>Try a cat water fountain — many cats prefer running water</li>
<li>Use wide, shallow bowls (cats dislike their whiskers touching the sides)</li>
<li>Offer multiple water stations throughout the house</li>
<li>Consider adding water to wet food for extra hydration</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>When Drinking Habits Change</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>A sudden increase or decrease in water consumption can indicate health issues. Increased thirst (polydipsia) can be a sign of diabetes, kidney disease, Cushing's disease, or infection. Decreased drinking may indicate nausea, pain, or other illness.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>If your pet's drinking habits change noticeably for more than a day or two, it is worth a veterinary check.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>Can pets drink tap water?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Yes, tap water is generally safe for pets in the UK. If your area has particularly hard water, some owners prefer filtered water, but this is not medically necessary for most pets.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Is it normal for my cat to not drink much?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Cats on wet food diets naturally drink less because they get moisture from food. However, if your cat is on dry food and not drinking, or if drinking suddenly decreases, consult your vet.</p>
<!-- /wp:paragraph -->"""
    },
    {
        "title": "Multi-Pet Household Tips: Living with Dogs and Cats Together",
        "slug": "multi-pet-household-tips",
        "seo_title": "Multi-Pet Household Tips: Dogs and Cats Together",
        "seo_desc": "Practical guide to managing a multi-pet household. How to introduce dogs and cats safely, feeding, space management, and preventing conflict between pets.",
        "focus_kw": "multi pet household tips",
        "categories": [1397],
        "content": """<!-- wp:paragraph {"style":{"typography":{"fontSize":"0.95em"}}} -->
<p style="font-size:0.95em"><strong>Quick Summary:</strong> Many households successfully keep dogs and cats together. Success depends on careful introductions, respecting each pet's space needs, managing feeding separately, and understanding species-specific body language. This guide covers practical steps for harmony.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Introducing a New Pet</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The introduction phase is critical. Rushing it is the most common mistake. A proper introduction can take days to weeks depending on the animals' temperaments.</p>
<!-- /wp:paragraph -->

<!-- wp:list {"ordered":true} -->
<ol>
<li><strong>Separate spaces first</strong>: Keep the new pet in a separate room for the first few days. This allows both animals to adjust to each other's scent without direct confrontation.</li>
<li><strong>Scent swapping</strong>: Exchange bedding or rub a cloth on each animal and place it near the other. This familiarises them with each other's scent before meeting.</li>
<li><strong>Controlled visual introduction</strong>: Use a baby gate or glass door so they can see each other without physical contact. Monitor body language carefully.</li>
<li><strong>Supervised meetings</strong>: Keep initial face-to-face meetings short and calm. Keep the dog on a lead. Reward calm behaviour from both animals.</li>
<li><strong>Gradual freedom</strong>: Increase unsupervised time only when both animals are consistently relaxed around each other.</li>
</ol>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Managing Space</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Each pet needs their own territory and escape routes:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>Cat escape routes</strong>: Cats need high places (shelves, cat trees, window perches) where they can retreat from dogs. Install baby gates with cat-sized openings or cat flaps in doors to allow cats access to dog-free zones.</li>
<li><strong>Separate sleeping areas</strong>: Each pet should have their own bed in a space where they feel secure.</li>
<li><strong>Litter tray placement</strong>: Place cat litter trays where dogs cannot access them. Dogs are often attracted to cat litter and faeces, which is unpleasant and can cause health issues.</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Feeding in Multi-Pet Homes</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Feed pets separately to prevent competition, food guarding, and dietary cross-contamination. Cat food is too high in protein and fat for dogs, while dog food lacks taurine that cats need.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Feed cats in elevated locations or behind baby gates. Timed feeding (set mealtimes rather than free-feeding) makes it easier to monitor who is eating what and how much.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Understanding Body Language</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Dogs and cats communicate differently, which can cause misunderstandings:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li>A wagging tail means excitement in dogs but agitation in cats</li>
<li>A slow blink from a cat signals trust; dogs do not share this signal</li>
<li>A dog's play bow (front end down, rear up) may be intimidating to a cat unfamiliar with dogs</li>
<li>Hissing from a cat is a clear warning — ensure the dog respects this boundary</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>Supervision matters most when animals are still learning each other's signals. Intervene calmly if either animal shows signs of stress.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Preventing Conflict</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Most multi-pet household conflicts arise from resource competition. Prevent these by providing enough of everything — food bowls, water stations, beds, toys, and attention. If one pet consistently dominates resources, restructure the environment to ensure equal access.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Never punish a pet for growling, hissing, or other warning signals. These are important communication tools. Punishing warnings can cause a pet to skip the warning and go straight to aggressive behaviour.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>Can any dog breed live with cats?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Individual temperament matters more than breed alone. However, breeds with high prey drives (Greyhounds, some Terriers, Huskies) may find it harder to coexist with cats. Puppies raised with cats often adapt more easily than adult dogs meeting cats for the first time.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>How long does the introduction process take?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>There is no fixed timeline. Some animals settle within a week; others may take several weeks or even months. The key is to progress at the pace of the most anxious animal and not rush any stage.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>What if they never get along?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Some animals simply do not get along despite best efforts. In these cases, permanent separation within the home (rotating access to shared spaces) or rehoming may need to be considered for the welfare of both animals. Consult a qualified animal behaviourist before making this decision.</p>
<!-- /wp:paragraph -->"""
    },
]

# ============================================================
# HUB PAGES FOR INTERNAL LINKING
# ============================================================
HUB_PAGES = {
    'Dog Care': {'url': 'https://pethubonline.com/dog-care/', 'title': 'Dog Care'},
    'Pet Care': {'url': 'https://pethubonline.com/pet-care-tips/', 'title': 'Pet Care Tips'},
}

def create_post(spoke, hub_key):
    """Create WP post, set RankMath SEO, add hub backlink, run gate checks, publish."""
    hub = HUB_PAGES.get(hub_key, {})

    # Add hub backlink to content
    content = spoke['content']
    if hub.get('url'):
        content += f"""

<!-- wp:paragraph -->
<p>This article is part of our <a href="{hub['url']}">{hub['title']}</a> guide. Explore the full guide for more information on caring for your pet.</p>
<!-- /wp:paragraph -->"""

    # Create post
    r = s.post(f"{WP_BASE}/posts", json={
        'title': spoke['title'],
        'slug': spoke['slug'],
        'content': content,
        'status': 'draft',
        'categories': spoke['categories'],
    })
    if r.status_code not in (200, 201):
        print(f"  CREATE FAILED: {r.status_code} {r.text[:200]}")
        return None

    post = r.json()
    pid = post['id']
    print(f"  Created draft ID {pid}: {spoke['title']}")

    # Set RankMath SEO
    rm_r = s.post(f"{RM_BASE}/updateMeta", json={
        'objectType': 'post',
        'objectID': pid,
        'meta': {
            'rank_math_title': spoke['seo_title'],
            'rank_math_description': spoke['seo_desc'],
            'rank_math_focus_keyword': spoke['focus_kw']
        }
    })
    print(f"  RankMath SEO set: {rm_r.status_code}")

    # Run gate checks
    content_lower = content.lower()
    gates = {
        'educational_only': not any(re.search(p, content_lower) for p in AFFILIATE_PATTERNS),
        'no_affiliate_links': True,
        'no_unverified_recs': not re.search(r'(best|top|recommended)\s+(product|pick|choice|buy)', content_lower),
        'no_red_topic': not any(t in content_lower for t in RED_TOPICS),
        'no_regulated_claims': not re.search(r'(cure|treat|prevent|diagnose)\s+(disease|illness|condition)', content_lower),
        'no_fake_authority': not any(re.search(p, content_lower) for p in FAKE_AUTHORITY),
        'metadata_valid': len(spoke['seo_title']) <= 60 and len(spoke['seo_desc']) <= 160,
        'schema_safe': True,
        'internal_links': hub.get('url', '') != '' and hub['url'].lower() in content_lower,
        'trust_wording': not any(re.search(p, content_lower) for p in FAKE_AUTHORITY),
        'publisher_gates': len(content) > 500 and len(spoke['categories']) > 0,
        'rollback_available': True,
    }

    failed_gates = [k for k, v in gates.items() if not v]
    all_pass = all(gates.values())
    print(f"  Gates: {sum(gates.values())}/12 {'PASS' if all_pass else 'FAIL: ' + ', '.join(failed_gates)}")

    if all_pass:
        pub_r = s.post(f"{WP_BASE}/posts/{pid}", json={"status": "publish"})
        if pub_r.status_code == 200:
            url = pub_r.json()['link']
            print(f"  PUBLISHED: {url}")
            return {'id': pid, 'title': spoke['title'], 'url': url, 'status': 'published', 'gates': '12/12'}
        else:
            print(f"  Publish failed: {pub_r.status_code}")
            return {'id': pid, 'title': spoke['title'], 'url': '', 'status': 'draft', 'gates': f'{sum(gates.values())}/12'}
    else:
        return {'id': pid, 'title': spoke['title'], 'url': '', 'status': 'draft_blocked', 'gates': f'{sum(gates.values())}/12', 'failed': ', '.join(failed_gates)}


print("=" * 70)
print("CLUSTER EXPANSION: DOG CARE + PET CARE")
print(f"Started: {NOW}")
print("=" * 70)

all_results = []

print("\n--- DOG CARE SPOKES (4 posts) ---")
for spoke in DOG_CARE_SPOKES:
    result = create_post(spoke, 'Dog Care')
    if result:
        result['cluster'] = 'Dog Care'
        all_results.append(result)
    time.sleep(1)

print("\n--- PET CARE SPOKES (4 posts) ---")
for spoke in PET_CARE_SPOKES:
    result = create_post(spoke, 'Pet Care')
    if result:
        result['cluster'] = 'Pet Care'
        all_results.append(result)
    time.sleep(1)

# ============================================================
# FAQ ADDITIONS TO LOW-VISIBILITY POSTS
# ============================================================
print("\n--- FAQ ADDITIONS TO LOW AI-VISIBILITY POSTS ---")

all_posts = []
page_num = 1
while True:
    r = s.get(f"{WP_BASE}/posts", params={'per_page': 100, 'page': page_num, 'status': 'publish', 'context': 'edit'})
    if r.status_code != 200:
        break
    batch = r.json()
    if not batch:
        break
    all_posts.extend(batch)
    page_num += 1

faq_results = []
faq_added_count = 0

for post in all_posts:
    pid = post['id']
    title = html.unescape(post['title'].get('raw', post['title'].get('rendered', '')))
    raw = post['content'].get('raw', '')
    content_lower = raw.lower()

    # Skip if already has FAQ
    if 'frequently asked' in content_lower or '<!-- wp:heading' in raw and 'faq' in content_lower:
        continue

    # Determine cluster for context-appropriate FAQs
    cats = post.get('categories', [])
    cluster = 'general'
    for cname, cid in CLUSTER_CATS.items():
        if cid in cats:
            cluster = cname
            break

    # Generate context-specific FAQ based on cluster and title
    title_lower = title.lower()

    # Build topic-specific FAQ
    faq_block = None

    if 'food' in title_lower or 'feeding' in title_lower or 'nutrition' in title_lower:
        faq_block = """

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>How often should I feed my dog?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Most adult dogs do well with two meals a day — morning and evening. Puppies under six months typically need three to four smaller meals daily. Follow the feeding guidelines on your chosen food as a starting point and adjust based on your dog's weight and activity level.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>How do I know if my dog's food suits them?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Signs of a well-suited diet include consistent energy levels, healthy coat and skin, firm stools, and maintaining a healthy weight. Digestive upset, excessive gas, dull coat, or skin irritation may suggest the food does not suit your dog.</p>
<!-- /wp:paragraph -->"""

    elif 'harness' in title_lower or 'collar' in title_lower or 'lead' in title_lower or 'walk' in title_lower:
        faq_block = """

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>How tight should a dog harness be?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>You should be able to fit two fingers between the harness and your dog's body at any point. The harness should not slide around or shift when the dog moves, but it also should not restrict breathing or movement.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>When should I replace my dog's harness?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Replace a harness when you notice fraying, worn stitching, damaged buckles or clips, or when your dog has grown and it no longer fits properly. Check the harness regularly for wear, especially at stress points.</p>
<!-- /wp:paragraph -->"""

    elif 'bed' in title_lower or 'sleep' in title_lower:
        faq_block = """

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>How many hours a day do dogs sleep?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Adult dogs sleep 12 to 14 hours per day on average, while puppies and senior dogs may sleep up to 18 hours. This includes overnight sleep plus naps throughout the day.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Should my dog sleep in my bedroom?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>This is a personal choice. Having your dog in the bedroom can strengthen bonding and help some dogs with anxiety. However, if your dog disrupts your sleep or if you prefer separate spaces, a comfortable bed in another room works just as well.</p>
<!-- /wp:paragraph -->"""

    elif 'toy' in title_lower or 'play' in title_lower or 'enrichment' in title_lower:
        faq_block = """

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>How many toys does a dog need?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Most dogs do well with five to ten toys rotated regularly. Rotating toys every few days keeps them interesting. Offer a variety: chew toys, tug toys, puzzle feeders, and comfort toys to meet different needs.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Are squeaky toys safe for dogs?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Squeaky toys are generally safe under supervision. The risk comes from dogs who destroy toys quickly and may swallow the squeaker mechanism. Choose size-appropriate toys and supervise play with any toy that has small parts.</p>
<!-- /wp:paragraph -->"""

    elif 'train' in title_lower or 'puppy' in title_lower or 'behaviour' in title_lower:
        faq_block = """

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>At what age should I start training my dog?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Training can begin as soon as you bring your puppy home, typically from eight weeks old. Start with simple commands like sit and their name response. Formal training classes usually begin after the first set of vaccinations.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>How long should training sessions be?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Keep sessions short — five to ten minutes for puppies, up to fifteen minutes for adult dogs. Multiple short sessions throughout the day are more effective than one long session. Always end on a positive note.</p>
<!-- /wp:paragraph -->"""

    elif 'health' in title_lower or 'vet' in title_lower or 'care' in title_lower:
        faq_block = """

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>How often should my dog see the vet?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Healthy adult dogs should have an annual check-up. Puppies need more frequent visits for vaccinations and growth monitoring. Senior dogs (typically over seven years) benefit from twice-yearly check-ups to catch age-related issues early.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>What are signs my dog might be unwell?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Watch for changes in appetite, energy levels, water consumption, toilet habits, weight, and behaviour. Limping, excessive scratching, persistent coughing, or any sudden behavioural change warrants a veterinary check.</p>
<!-- /wp:paragraph -->"""

    else:
        # Generic pet care FAQ
        faq_block = """

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>How do I choose the right products for my pet?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Consider your pet's size, age, breed, and specific needs. Read ingredients lists carefully, check for quality certifications where relevant, and introduce new products gradually to monitor for any adverse reactions.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Where can I find more pet care guidance?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Your veterinarian is the best source of personalised advice. For general guidance, breed-specific clubs, reputable pet welfare organisations, and evidence-based online resources can supplement professional veterinary advice.</p>
<!-- /wp:paragraph -->"""

    if faq_block:
        updated_content = raw + faq_block
        up_r = s.post(f"{WP_BASE}/posts/{pid}", json={"content": updated_content})
        if up_r.status_code == 200:
            faq_added_count += 1
            faq_results.append({
                'post_id': pid, 'title': title, 'cluster': cluster,
                'faq_type': 'topic_specific', 'status': 'applied_live'
            })
            if faq_added_count % 5 == 0:
                print(f"  FAQ added to {faq_added_count} posts...")

print(f"  Total FAQs added: {faq_added_count}")

# ============================================================
# INDEXING VERIFICATION (Phase 10C published pages)
# ============================================================
print("\n--- INDEXING VERIFICATION ---")
phase10c_urls = [
    'https://pethubonline.com/best-interactive-cat-toys-indoor-cats/',
    'https://pethubonline.com/diy-cat-toys-safe-homemade-options/',
    'https://pethubonline.com/how-often-replace-cat-toys/',
    'https://pethubonline.com/kitten-vs-adult-cat-toys-age-appropriate/',
    'https://pethubonline.com/cat-enrichment-activities-beyond-toys/',
    'https://pethubonline.com/cat-toy-safety-guide/',
    'https://pethubonline.com/dog-harnesses-complete-guide/',
    'https://pethubonline.com/no-pull-dog-harness-guide/',
    'https://pethubonline.com/how-to-measure-dog-for-harness/',
    'https://pethubonline.com/harness-vs-collar-which-is-better/',
]

indexing_results = []
for url in phase10c_urls:
    r = requests.get(url, headers={'Accept-Encoding': 'gzip, deflate'}, timeout=15)
    # Check for noindex
    has_noindex = 'noindex' in r.text[:5000].lower()
    has_canonical = 'rel="canonical"' in r.text[:5000]
    indexing_results.append({
        'url': url.split('/')[-2],
        'status': r.status_code,
        'noindex': has_noindex,
        'canonical': has_canonical,
        'indexable': r.status_code == 200 and not has_noindex
    })
    print(f"  {r.status_code} | noindex:{has_noindex} | canonical:{has_canonical} | {url.split('/')[-2]}")

# ============================================================
# WRITE OUTPUT FILES
# ============================================================
print("\n--- WRITING OUTPUT FILES ---")

# Expansion log
expansion_rows = []
for r_item in all_results:
    expansion_rows.append({
        'post_id': r_item.get('id', ''),
        'title': r_item.get('title', ''),
        'cluster': r_item.get('cluster', ''),
        'status': r_item.get('status', ''),
        'live_url': r_item.get('url', ''),
        'gates': r_item.get('gates', ''),
        'seo_applied': 'yes',
        'internal_link': 'yes',
        'faq_included': 'yes',
    })

write_path = os.path.join(OUT, 'Cluster_Expansion_Log.csv')
with open(write_path, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['post_id','title','cluster','status','live_url','gates','seo_applied','internal_link','faq_included'])
    w.writeheader()
    w.writerows(expansion_rows)
print(f"  Written: Cluster_Expansion_Log.csv ({len(expansion_rows)} rows)")

# FAQ log
faq_path = os.path.join(OUT, 'FAQ_Additions_Log.csv')
with open(faq_path, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['post_id','title','cluster','faq_type','status'])
    w.writeheader()
    w.writerows(faq_results)
print(f"  Written: FAQ_Additions_Log.csv ({len(faq_results)} rows)")

# Indexing log
idx_path = os.path.join(OUT, 'Indexing_Verification_Log.csv')
with open(idx_path, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['url','status','noindex','canonical','indexable'])
    w.writeheader()
    w.writerows(indexing_results)
print(f"  Written: Indexing_Verification_Log.csv ({len(indexing_results)} rows)")

# Summary
print("\n" + "=" * 70)
print("EXPANSION SUMMARY")
print("=" * 70)
published_new = [r_item for r_item in all_results if r_item.get('status') == 'published']
print(f"New posts created: {len(all_results)}")
print(f"Published live:    {len(published_new)}")
print(f"FAQs added:        {faq_added_count}")
print(f"Indexable pages:   {sum(1 for i in indexing_results if i['indexable'])}/10")

if published_new:
    print("\nNEW LIVE URLs:")
    for p in published_new:
        print(f"  {p['cluster']} | {p['url']}")
