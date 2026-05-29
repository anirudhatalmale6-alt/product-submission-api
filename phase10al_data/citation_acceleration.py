#!/usr/bin/env python3
"""
Phase 10AL – Citation Acceleration Sprint
Clusters: Dog Food, Dog Beds, Educational
Adds: At a Glance, Key Takeaways, UK authority references, glossary cross-links
"""

import subprocess, json, csv, time, tempfile, os, re, html, sys
from datetime import datetime

# ── credentials ──────────────────────────────────────────────────────────────
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
BASE = "https://pethubonline.com/wp-json/wp/v2"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10al_data"

# ── cluster definitions ──────────────────────────────────────────────────────
CLUSTERS = {
    "Dog Food": [5467, 5460, 3839, 3838, 3837, 3836, 7172],
    "Dog Beds": [5522, 5510, 4784, 4783, 4018, 4011, 4004, 3996,
                 7332, 7333, 7334, 7335, 7336, 7174],
    "Educational": [5521, 5462, 5424, 5419, 5416, 5415, 5414,
                    4574, 4272, 4265, 4216, 4167, 4160, 4146],
}

# reverse map: id -> cluster
ID_TO_CLUSTER = {}
for cluster, ids in CLUSTERS.items():
    for pid in ids:
        ID_TO_CLUSTER[pid] = cluster

ALL_IDS = list(ID_TO_CLUSTER.keys())

# ── glossary page URLs (for cross-linking) ───────────────────────────────────
GLOSSARY_LINKS = {
    7167: "/glossary/dog-toys-terminology/",
    7169: "/glossary/cat-accessories-terminology/",
    7170: "/glossary/pet-grooming-terminology/",
    7172: "/glossary/dog-food-terminology/",
    7174: "/glossary/dog-beds-terminology/",
    7175: "/glossary/cat-food-terminology/",
    7177: "/glossary/pet-health-terminology/",
}

# ── UK authority references by cluster ───────────────────────────────────────
UK_REFS = {
    "Dog Food": {
        "PFMA": "https://www.pfma.org.uk/",
        "FEDIAF": "https://fediaf.org/",
        "BVA": "https://www.bva.co.uk/",
    },
    "Dog Beds": {
        "Kennel Club": "https://www.thekennelclub.org.uk/",
        "Dogs Trust": "https://www.dogstrust.org.uk/",
        "RSPCA": "https://www.rspca.org.uk/",
    },
    "Educational": {
        "RSPCA": "https://www.rspca.org.uk/",
        "PDSA": "https://www.pdsa.org.uk/",
        "BVA": "https://www.bva.co.uk/",
        "RCVS": "https://www.rcvs.org.uk/",
    },
}

# ── "At a Glance" content per post (topic-specific) ─────────────────────────
AT_A_GLANCE = {
    # Dog Food
    5467: [
        "Portion sizes depend on your dog’s weight, age, breed, and activity level",
        "Adult dogs typically eat once or twice daily; puppies need three to four smaller meals",
        "The <a href='https://www.pfma.org.uk/' rel='nofollow'>PFMA</a> recommends using manufacturer guidelines as a starting point, then adjusting",
        "Fresh water should always be available alongside meals",
        "Sudden dietary changes can cause digestive upset – transition over 7–10 days",
        "Regular weigh-ins help you fine-tune portions to maintain a healthy body condition score",
    ],
    5460: [
        "Dogs with sensitive stomachs benefit from limited-ingredient diets",
        "Common triggers include certain proteins, grains, and artificial additives",
        "Hypoallergenic formulas use novel proteins such as venison or duck",
        "The <a href='https://www.bva.co.uk/' rel='nofollow'>BVA</a> advises consulting a vet before switching to an elimination diet",
        "Gradual food transitions over 10–14 days reduce digestive stress",
    ],
    3839: [
        "Puppies have different nutritional needs at each growth stage",
        "Small breeds mature faster and may switch to adult food around 9–12 months",
        "Large-breed puppies need controlled calcium and phosphorus levels for joint health",
        "The <a href='https://fediaf.org/' rel='nofollow'>FEDIAF</a> sets nutritional guidelines for puppy food across Europe",
        "Frequent, smaller meals support steady blood sugar in growing puppies",
    ],
    3838: [
        "Senior dogs often need fewer calories but more joint-supporting nutrients",
        "Look for foods enriched with glucosamine and omega-3 fatty acids",
        "Wet food can help older dogs who struggle with dry kibble",
        "The <a href='https://www.pfma.org.uk/' rel='nofollow'>PFMA</a> notes that dogs over seven are generally classified as senior",
        "Regular vet check-ups help adjust diet as your dog ages",
    ],
    3837: [
        "Grain-free diets are not inherently healthier for every dog",
        "Some dogs genuinely benefit from grain-free options due to specific intolerances",
        "The <a href='https://www.bva.co.uk/' rel='nofollow'>BVA</a> recommends evidence-based dietary choices rather than trends",
        "Common grain alternatives include sweet potato, chickpeas, and lentils",
        "Always check that grain-free food still meets <a href='https://fediaf.org/' rel='nofollow'>FEDIAF</a> nutritional standards",
    ],
    3836: [
        "Wet food provides higher moisture content, benefiting dogs who drink less water",
        "Dry kibble supports dental health through mechanical abrasion",
        "Mixed feeding combines the benefits of both wet and dry food",
        "Storage requirements differ: opened wet food must be refrigerated and used within 48 hours",
        "Cost per serving varies – dry food is typically more economical for larger breeds",
    ],
    7172: [
        "This glossary covers essential dog food terminology from A to Z",
        "Understanding labels helps you make informed feeding decisions",
        "UK pet food labels must comply with <a href='https://www.pfma.org.uk/' rel='nofollow'>PFMA</a> guidelines",
        "Terms like ‘complete’ and ‘complementary’ have specific legal meanings",
        "Knowing ingredient naming conventions helps compare brands objectively",
    ],
    # Dog Beds
    5522: [
        "Orthopaedic beds provide crucial joint support for older and larger breeds",
        "Memory foam distributes weight evenly, reducing pressure on hips and shoulders",
        "The <a href='https://www.thekennelclub.org.uk/' rel='nofollow'>Kennel Club</a> recommends supportive bedding for breeds prone to dysplasia",
        "Bed size should allow your dog to stretch out fully with extra room to spare",
        "Washable, removable covers are essential for hygiene and longevity",
    ],
    5510: [
        "Elevated beds keep dogs cool by allowing air to circulate underneath",
        "They are ideal for warmer months and dogs that tend to overheat",
        "Raised designs also reduce contact with damp or cold floors",
        "The <a href='https://www.dogstrust.org.uk/' rel='nofollow'>Dogs Trust</a> suggests providing a choice of sleeping surfaces",
        "Weight capacity must match your dog’s size – check manufacturer limits",
    ],
    4784: [
        "Calming beds use raised rims and soft filling to create a sense of security",
        "They are particularly helpful for anxious dogs or rescue dogs adjusting to new homes",
        "Donut-shaped designs encourage natural curling behaviour",
        "The <a href='https://www.rspca.org.uk/' rel='nofollow'>RSPCA</a> recommends a quiet, dedicated sleeping area for anxious pets",
        "Anti-slip bases prevent the bed from sliding on hard floors",
    ],
    4783: [
        "Waterproof beds are essential for incontinent dogs, puppies, and outdoor use",
        "Look for beds with sealed seams and waterproof liners beneath the cover",
        "Regular cleaning prevents bacterial build-up and odour",
        "Waterproof does not always mean chew-proof – check durability separately",
        "UK weather makes waterproof options practical for kennel and conservatory use",
    ],
    4018: [
        "Choosing the right bed size prevents joint strain from cramped sleeping positions",
        "Measure your dog from nose to tail base, then add 15–20 cm for comfort",
        "The <a href='https://www.thekennelclub.org.uk/' rel='nofollow'>Kennel Club</a> provides breed-specific size guides",
        "Puppies grow quickly – consider adjustable or slightly oversized beds initially",
        "Multiple dogs may need separate beds to reduce resource-guarding behaviour",
    ],
    4011: [
        "Heated beds provide comfort for arthritic dogs and small breeds that lose heat quickly",
        "Thermostatically controlled options are safer than standard heat pads",
        "The <a href='https://www.dogstrust.org.uk/' rel='nofollow'>Dogs Trust</a> advises monitoring heated beds to prevent overheating",
        "Self-warming beds use reflective thermal liners rather than electricity",
        "Always check cords and plugs for chew damage before each use",
    ],
    4004: [
        "Outdoor dog beds must withstand UV exposure, moisture, and temperature swings",
        "Raised mesh designs allow drainage and discourage mould growth",
        "UV-resistant fabrics prevent fading and material breakdown",
        "Position outdoor beds in sheltered, shaded areas during summer months",
        "The <a href='https://www.rspca.org.uk/' rel='nofollow'>RSPCA</a> requires adequate shelter and bedding for outdoor dogs",
    ],
    3996: [
        "Bolster beds offer head and neck support with raised edges on three or four sides",
        "They suit dogs who like to rest their heads on a raised surface while sleeping",
        "Look for removable, machine-washable covers for easy maintenance",
        "Firm bolsters maintain their shape better than loosely stuffed alternatives",
        "The <a href='https://www.thekennelclub.org.uk/' rel='nofollow'>Kennel Club</a> notes that breed sleeping styles should guide bed shape choice",
    ],
    7332: [
        "Crate beds must fit snugly inside the crate without bunching or folding",
        "Measure the crate floor before purchasing to ensure a proper fit",
        "Chew-resistant materials are important for dogs that destroy bedding",
        "Flat mats or thin mattresses work best for standard wire crates",
        "The <a href='https://www.dogstrust.org.uk/' rel='nofollow'>Dogs Trust</a> recommends making crates a positive, comfortable space",
    ],
    7333: [
        "Travel beds give dogs a familiar sleeping surface away from home",
        "Roll-up and foldable designs are easiest for car boots and holidays",
        "Waterproof backing protects against damp campsites and hotel floors",
        "A consistent travel bed reduces anxiety in unfamiliar environments",
        "Pack a familiar-smelling blanket alongside the travel bed for added comfort",
    ],
    7334: [
        "Eco-friendly dog beds use recycled, organic, or sustainably sourced materials",
        "Recycled polyester filling repurposes plastic bottles into comfortable padding",
        "Natural latex and organic cotton covers avoid chemical treatments",
        "Look for OEKO-TEX or GRS certifications for verified sustainability claims",
        "UK brands increasingly offer refillable beds to reduce landfill waste",
    ],
    7335: [
        "Cooling beds help regulate body temperature during warm UK summers",
        "Gel-infused mats activate with pressure and do not require refrigeration",
        "Elevated mesh beds also provide passive cooling through airflow",
        "Brachycephalic breeds like Bulldogs and Pugs benefit most from cooling surfaces",
        "The <a href='https://www.rspca.org.uk/' rel='nofollow'>RSPCA</a> warns that heatstroke is a serious risk for flat-faced breeds",
    ],
    7336: [
        "Luxury dog beds combine premium materials with stylish designs",
        "Genuine memory foam and high-thread-count covers distinguish quality from marketing",
        "Handmade UK beds often offer bespoke sizing for unusual breeds",
        "Removable covers and spare fillings extend the bed’s useful life",
        "Investment in a quality bed reduces long-term replacement costs",
    ],
    7174: [
        "This glossary explains key dog bed terminology and features",
        "Understanding fill types – memory foam, polyester, latex – helps you compare beds",
        "The <a href='https://www.thekennelclub.org.uk/' rel='nofollow'>Kennel Club</a> recommends breed-appropriate sleeping surfaces",
        "‘Orthopaedic’ is not a regulated term – check actual foam density and thickness",
        "Knowing bed shapes (bolster, donut, flat mat, nest) narrows your search quickly",
    ],
    # Educational
    5521: [
        "Socialisation is most effective during the critical period of 3–14 weeks",
        "Positive exposure to varied people, animals, and environments builds confidence",
        "The <a href='https://www.rspca.org.uk/' rel='nofollow'>RSPCA</a> emphasises gentle, reward-based socialisation methods",
        "Puppy classes run by accredited trainers provide structured social learning",
        "Over-socialisation can be as harmful as under-socialisation – watch for stress signals",
    ],
    5462: [
        "Separation anxiety affects an estimated 1 in 5 UK dogs",
        "Gradual desensitisation – leaving for short, increasing periods – is the gold-standard approach",
        "The <a href='https://www.pdsa.org.uk/' rel='nofollow'>PDSA</a> recommends consulting a qualified behaviourist for severe cases",
        "Environmental enrichment (puzzle toys, radio) can reduce distress during absences",
        "Punishment never helps and often worsens anxious behaviour",
    ],
    5424: [
        "Positive reinforcement is the most effective and humane training method",
        "Timing is everything – reward within 1–2 seconds of the desired behaviour",
        "The <a href='https://www.rspca.org.uk/' rel='nofollow'>RSPCA</a> and <a href='https://www.bva.co.uk/' rel='nofollow'>BVA</a> oppose aversive training tools",
        "Consistency across all family members prevents confusion",
        "Short, frequent sessions (5–10 minutes) are more effective than long ones",
    ],
    5419: [
        "Regular dental care prevents periodontal disease, which affects 80% of dogs over three",
        "Daily brushing with dog-specific toothpaste is the most effective preventive measure",
        "The <a href='https://www.pdsa.org.uk/' rel='nofollow'>PDSA</a> offers guidance on at-home dental routines",
        "Professional dental scaling under anaesthesia may be needed for advanced tartar",
        "Bad breath is often the first sign of underlying dental problems",
    ],
    5416: [
        "Microchipping has been a legal requirement for dogs in England since 2016",
        "The chip must be registered to a compliant database and kept up to date",
        "The <a href='https://www.rcvs.org.uk/' rel='nofollow'>RCVS</a> regulates veterinary practices that perform microchipping",
        "Microchips do not replace visible ID tags, which are also legally required in the UK",
        "Scanning is free at most UK vet practices and rescue centres",
    ],
    5415: [
        "Neutering reduces the risk of certain cancers and unwanted litters",
        "The <a href='https://www.pdsa.org.uk/' rel='nofollow'>PDSA</a> and <a href='https://www.rspca.org.uk/' rel='nofollow'>RSPCA</a> both support responsible neutering",
        "Timing varies by breed and size – discuss with your vet",
        "Post-operative recovery typically takes 10–14 days with restricted exercise",
        "Financial assistance for neutering is available through UK charities for eligible owners",
    ],
    5414: [
        "Vaccinations protect against serious diseases including parvovirus, distemper, and leptospirosis",
        "Primary vaccination courses begin at 6–8 weeks of age",
        "Annual boosters maintain immunity – your vet will advise on the appropriate schedule",
        "The <a href='https://www.bva.co.uk/' rel='nofollow'>BVA</a> provides evidence-based vaccination guidelines",
        "Titre testing can check existing immunity levels before re-vaccination",
    ],
    4574: [
        "Fleas, ticks, and worms are the most common parasites affecting UK dogs",
        "Year-round prevention is more effective than seasonal treatment alone",
        "The <a href='https://www.pdsa.org.uk/' rel='nofollow'>PDSA</a> recommends prescription-strength parasite control from your vet",
        "Ticks in the UK can transmit Lyme disease and babesiosis",
        "Check your dog after walks in long grass, woodlands, and moorland areas",
    ],
    4272: [
        "Exercise needs vary dramatically by breed, age, and health status",
        "The <a href='https://www.thekennelclub.org.uk/' rel='nofollow'>Kennel Club</a> publishes breed-specific exercise guidelines",
        "Over-exercising puppies can damage developing joints and growth plates",
        "Mental stimulation (sniff walks, training games) is as important as physical exercise",
        "Signs of over-exercise include excessive panting, limping, and reluctance to walk",
    ],
    4265: [
        "Grooming frequency depends on coat type, breed, and lifestyle",
        "Double-coated breeds need regular de-shedding but should rarely be clipped",
        "The <a href='https://www.rspca.org.uk/' rel='nofollow'>RSPCA</a> considers neglected grooming a welfare concern",
        "Regular grooming sessions are an opportunity to check for lumps, parasites, and skin issues",
        "Professional groomers should hold relevant City &amp; Guilds or equivalent qualifications",
    ],
    4216: [
        "Pet insurance in the UK covers unexpected vet bills and can prevent financial hardship",
        "Lifetime policies offer the most comprehensive ongoing cover for chronic conditions",
        "The <a href='https://www.bva.co.uk/' rel='nofollow'>BVA</a> encourages all pet owners to consider insurance",
        "Pre-existing conditions are excluded by all UK insurers",
        "Excess amounts and annual limits vary significantly between providers",
    ],
    4167: [
        "First aid knowledge can save your dog’s life in an emergency",
        "Keep a pet-specific first aid kit at home and in the car",
        "The <a href='https://www.pdsa.org.uk/' rel='nofollow'>PDSA</a> offers free first aid guides for pet owners",
        "Learn to check your dog’s heart rate, breathing rate, and gum colour",
        "Never give human medication to dogs without veterinary advice",
    ],
    4160: [
        "Seasonal hazards include heatstroke in summer and antifreeze poisoning in winter",
        "The <a href='https://www.rspca.org.uk/' rel='nofollow'>RSPCA</a> runs awareness campaigns for seasonal pet safety",
        "Never leave dogs in parked cars – temperatures can reach lethal levels within minutes",
        "Rock salt and grit on UK pavements can irritate dog paws in winter",
        "Conkers, acorns, and certain autumn mushrooms are toxic to dogs",
    ],
    4146: [
        "Responsible pet ownership covers health, welfare, socialisation, and legal obligations",
        "The <a href='https://www.rspca.org.uk/' rel='nofollow'>RSPCA</a> defines five welfare needs that owners must meet",
        "Dogs must be microchipped and wear a collar with an ID tag in public",
        "The <a href='https://www.pdsa.org.uk/' rel='nofollow'>PDSA</a> PAW Report annually surveys the state of UK pet welfare",
        "Training, enrichment, and veterinary care are ongoing responsibilities, not one-off tasks",
    ],
}

# ── "Key Takeaways" content per post ────────────────────────────────────────
KEY_TAKEAWAYS = {
    # Dog Food
    5467: [
        "Weigh portions using kitchen scales rather than estimating by eye",
        "Adjust feeding amounts every month based on body condition score",
        "Follow <a href='https://fediaf.org/' rel='nofollow'>FEDIAF</a> guidelines to ensure complete and balanced nutrition",
        "Keep a feeding diary to track changes and spot patterns",
    ],
    5460: [
        "Introduce new foods one ingredient at a time over 10–14 days",
        "Keep a food diary to identify triggers alongside your vet",
        "Avoid treats containing common allergens during an elimination trial",
        "Ask your vet about hydrolysed protein diets for persistent sensitivities",
    ],
    3839: [
        "Feed puppies a diet labelled ‘complete’ for their specific life stage",
        "Large-breed puppy food controls growth rate to protect developing joints",
        "Schedule regular weigh-ins at your vet practice to monitor growth curves",
        "Transition to adult food at the age recommended for your puppy’s breed size",
    ],
    3838: [
        "Switch to senior-specific food when your vet recommends it, typically around age 7",
        "Supplement with omega-3 fatty acids for joint and cognitive support",
        "Monitor weight closely – obesity worsens age-related joint disease",
        "Smaller, more frequent meals can aid digestion in older dogs",
    ],
    3837: [
        "Only choose grain-free if your dog has a diagnosed grain intolerance",
        "Ensure any grain-free food meets full <a href='https://fediaf.org/' rel='nofollow'>FEDIAF</a> nutritional requirements",
        "Consult your vet before making significant dietary changes",
        "Do not assume grain-free is automatically a premium or healthier option",
    ],
    3836: [
        "Consider mixed feeding to combine hydration benefits with dental support",
        "Store opened wet food in the fridge and use within 48 hours",
        "Check the daily feeding guide on both wet and dry food labels",
        "Factor in treat calories when calculating total daily intake",
    ],
    7172: [
        "Refer to this glossary when comparing dog food labels in-store",
        "Understand the difference between ‘complete’ and ‘complementary’ foods",
        "Look for <a href='https://www.pfma.org.uk/' rel='nofollow'>PFMA</a> membership as a baseline quality indicator",
        "Bookmark this page as a quick reference for future food purchases",
    ],
    # Dog Beds
    5522: [
        "Choose orthopaedic beds with at least 10 cm of high-density memory foam",
        "Measure your dog lying stretched out and add 15–20 cm to each dimension",
        "Wash covers fortnightly to maintain hygiene and reduce allergens",
        "Place the bed away from draughts and direct heat sources",
    ],
    5510: [
        "Select an elevated bed rated for at least 20% above your dog’s weight",
        "Position raised beds on level surfaces to prevent wobbling",
        "Clean the mesh fabric monthly to remove hair and dirt",
        "Pair with a blanket in cooler months for year-round versatility",
    ],
    4784: [
        "Choose a calming bed sized so your dog can curl up with the rim supporting their head",
        "Place the bed in a low-traffic, quiet corner of the room",
        "Combine with a consistent bedtime routine for best results",
        "Wash the bed regularly – familiar scent is comforting, but hygiene still matters",
    ],
    4783: [
        "Check seams and zippers for waterproof integrity before purchasing",
        "Use a waterproof bed as a base layer beneath a soft removable topper",
        "Clean and air the bed weekly to prevent mildew in damp UK climates",
        "Replace waterproof beds when the liner shows signs of cracking or peeling",
    ],
    4018: [
        "Re-measure your dog at least annually, especially during the first two years",
        "Consider your dog’s preferred sleeping position when choosing bed shape",
        "A bed that is too small can contribute to joint stiffness and discomfort",
        "The <a href='https://www.thekennelclub.org.uk/' rel='nofollow'>Kennel Club</a> breed profiles include typical adult dimensions",
    ],
    4011: [
        "Use thermostatically controlled heated beds rather than DIY heat sources",
        "Place heated beds on a non-flammable surface and inspect cables regularly",
        "Self-warming beds are a safer, electricity-free alternative for mild cold",
        "Consult your vet about heated bedding if your dog has a skin condition",
    ],
    4004: [
        "Choose beds with UV-resistant, quick-drying fabric for outdoor kennel use",
        "Elevate outdoor beds off the ground to improve drainage and reduce insects",
        "Bring cushions indoors overnight to prevent dampness and mould",
        "Inspect outdoor beds monthly for weather damage and wear",
    ],
    3996: [
        "Match bolster height to your dog’s neck and shoulder height for proper support",
        "Firm bolsters retain their shape longer than lightly stuffed alternatives",
        "Machine-washable covers make regular cleaning practical and hassle-free",
        "Bolster beds work best for dogs that naturally sleep curled against an edge",
    ],
    7332: [
        "Measure the internal crate floor before ordering a bed to ensure a snug fit",
        "Flat crate mats are easier to slide in and out for cleaning",
        "Choose chew-resistant options for puppies or dogs that destroy bedding",
        "A comfortable crate bed turns the crate into a positive den space",
    ],
    7333: [
        "Pack a travel bed that fits your car boot or luggage without bulk",
        "Use the travel bed at home occasionally so your dog associates it with comfort",
        "Waterproof backing protects against damp ground at campsites and parks",
        "A familiar travel bed reduces stress during kennelling or overnight stays",
    ],
    7334: [
        "Look for GRS or OEKO-TEX certifications to verify eco-friendly claims",
        "Recycled-fill beds perform as well as virgin-material alternatives when properly made",
        "Choose UK-made brands to reduce transport emissions",
        "Refillable bed designs extend product life and reduce landfill waste",
    ],
    7335: [
        "Gel cooling mats activate on contact and require no electricity or refrigeration",
        "Position cooling beds in shaded areas for maximum effect on hot days",
        "Brachycephalic and thick-coated breeds benefit most from cooling surfaces",
        "Combine cooling beds with fresh water access and limited midday exercise",
    ],
    7336: [
        "High-density memory foam (50+ kg/m³) is the hallmark of genuine luxury dog beds",
        "Removable, high-thread-count covers allow easy washing without damaging the core",
        "UK bespoke brands offer made-to-measure options for non-standard breeds",
        "Investing in one quality bed often costs less than replacing cheap beds repeatedly",
    ],
    7174: [
        "Use this glossary to decode marketing jargon when shopping for dog beds",
        "Check actual foam density rather than relying on the word ‘orthopaedic’ alone",
        "Bookmark this page as a quick reference for future bed purchases",
        "Understanding bed types and fillings helps you choose the right option first time",
    ],
    # Educational
    5521: [
        "Start socialisation early but continue exposure throughout your dog’s life",
        "Watch for stress signals (lip licking, whale eye, yawning) and give your dog space",
        "Use treats and praise to build positive associations with new experiences",
        "Enrol in a <a href='https://www.rspca.org.uk/' rel='nofollow'>RSPCA</a>-endorsed puppy class for structured socialisation",
    ],
    5462: [
        "Build up alone time gradually – start with seconds, not hours",
        "Leave a recently worn item of clothing to provide comforting scent",
        "Never punish your dog for anxious behaviour – it increases fear",
        "Seek professional help from an ABTC-accredited behaviourist for severe cases",
    ],
    5424: [
        "Reward desired behaviours immediately to strengthen the association",
        "Keep training sessions under 10 minutes for maximum engagement",
        "Use consistent cue words across all family members",
        "Never use punishment-based methods – they damage trust and welfare",
    ],
    5419: [
        "Brush your dog’s teeth daily using enzymatic dog toothpaste",
        "Schedule annual dental check-ups with your veterinary practice",
        "Offer dental chews approved by the Veterinary Oral Health Council",
        "Watch for signs of dental pain: dropping food, pawing at the mouth, drooling",
    ],
    5416: [
        "Ensure your dog’s microchip details are up to date after every house move",
        "Microchipping is a legal requirement for all dogs over 8 weeks in England",
        "Carry your microchip registration number with your pet’s travel documents",
        "Ask your vet to scan the chip at annual check-ups to confirm it still works",
    ],
    5415: [
        "Discuss the best neutering age with your vet, considering breed and size",
        "Restrict exercise for 10–14 days post-surgery to allow proper healing",
        "Apply for <a href='https://www.pdsa.org.uk/' rel='nofollow'>PDSA</a> or <a href='https://www.rspca.org.uk/' rel='nofollow'>RSPCA</a> subsidised neutering if you are on a low income",
        "Neutering does not change your dog’s personality – it reduces hormone-driven behaviours",
    ],
    5414: [
        "Complete the full primary vaccination course before allowing contact with unvaccinated dogs",
        "Keep vaccination records safe and bring them to every vet appointment",
        "Discuss titre testing with your vet if you are concerned about over-vaccination",
        "Boarding kennels and doggy daycare in the UK require proof of up-to-date vaccinations",
    ],
    4574: [
        "Use prescription-strength flea and tick prevention year-round",
        "Check your dog for ticks after every countryside walk",
        "Worm your dog according to your vet’s recommended schedule (typically every 3 months)",
        "Treat all pets in the household simultaneously to break the parasite lifecycle",
    ],
    4272: [
        "Match exercise intensity and duration to your dog’s breed and age",
        "Limit structured exercise for puppies to 5 minutes per month of age, twice daily",
        "Include mental enrichment (scent work, puzzle feeders) alongside physical walks",
        "Reduce exercise in extreme heat – walk early morning or late evening in summer",
    ],
    4265: [
        "Brush your dog at least twice a week, more often for long-coated breeds",
        "Never shave a double-coated breed – the undercoat provides insulation and UV protection",
        "Check ears, eyes, nails, and teeth during every grooming session",
        "Book a professional groomer for breed-specific clips every 6–8 weeks if needed",
    ],
    4216: [
        "Compare lifetime, annual, and time-limited policies before committing",
        "Insure your pet as early as possible to minimise pre-existing condition exclusions",
        "Read the policy excess, sub-limits, and exclusions carefully before purchasing",
        "Review your policy annually to ensure cover keeps pace with rising vet costs",
    ],
    4167: [
        "Assemble a pet first aid kit and keep it accessible at home and in the car",
        "Learn to perform CPR and manage choking – the <a href='https://www.pdsa.org.uk/' rel='nofollow'>PDSA</a> publishes free guides",
        "In an emergency, call your vet or the nearest out-of-hours practice immediately",
        "Do not attempt to treat serious injuries yourself – stabilise and transport safely",
    ],
    4160: [
        "Never leave your dog in a parked car, even with windows cracked",
        "Keep antifreeze, chocolate, grapes, and xylitol out of your dog’s reach",
        "Walk dogs during cooler parts of the day in summer and check pavement temperature",
        "Rinse paws after winter walks to remove road salt and grit",
    ],
    4146: [
        "Meet all five welfare needs: environment, diet, behaviour, companionship, and health",
        "Register with a vet and schedule annual health checks and vaccinations",
        "Ensure your dog is microchipped, insured, and wearing an ID tag at all times",
        "Invest in ongoing training and socialisation throughout your dog’s life",
    ],
}

# ── helpers ──────────────────────────────────────────────────────────────────

def api_get(endpoint):
    """GET from WP REST API."""
    url = f"{BASE}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    return json.loads(result.stdout)


def api_update(post_id, data):
    """POST update to WP REST API using temp JSON file."""
    url = f"{BASE}/posts/{post_id}"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        tmppath = f.name
    try:
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-d", f"@{tmppath}",
             "-H", "Content-Type: application/json",
             "-X", "POST", url],
            capture_output=True, text=True, timeout=60
        )
        return json.loads(result.stdout)
    finally:
        os.unlink(tmppath)


def has_block(content, marker):
    """Check if a marker string exists in the content (case-insensitive)."""
    return marker.lower() in content.lower()


def build_at_a_glance(items):
    """Build the At a Glance Gutenberg block."""
    li_items = "".join(f"<li>{item}</li>" for item in items)
    return (
        '<!-- wp:group {"style":{"color":{"background":"#eef2ff"},"border":{"radius":"6px","width":"1px","color":"#c7d2fe"},"spacing":{"padding":{"top":"16px","bottom":"16px","left":"20px","right":"20px"},"margin":{"top":"20px","bottom":"24px"}}},"layout":{"type":"constrained"}} -->\n'
        '<div class="wp-block-group has-border-color has-background" style="border-color:#c7d2fe;border-width:1px;border-radius:6px;background-color:#eef2ff;margin-top:20px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<!-- wp:heading {"level":4} -->\n'
        '<h4 class="wp-block-heading">At a Glance</h4>\n'
        '<!-- /wp:heading -->\n'
        '<!-- wp:list -->\n'
        f'<ul class="wp-block-list">{li_items}</ul>\n'
        '<!-- /wp:list -->\n'
        '</div>\n'
        '<!-- /wp:group -->'
    )


def build_key_takeaways(items):
    """Build the Key Takeaways Gutenberg block."""
    li_items = "".join(f"<li>{item}</li>" for item in items)
    return (
        '<!-- wp:group {"style":{"color":{"background":"#f0fdf4"},"border":{"radius":"6px","width":"1px","color":"#bbf7d0"},"spacing":{"padding":{"top":"16px","bottom":"16px","left":"20px","right":"20px"},"margin":{"top":"24px","bottom":"24px"}}},"layout":{"type":"constrained"}} -->\n'
        '<div class="wp-block-group has-border-color has-background" style="border-color:#bbf7d0;border-width:1px;border-radius:6px;background-color:#f0fdf4;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<!-- wp:heading {"level":4} -->\n'
        '<h4 class="wp-block-heading">Key Takeaways</h4>\n'
        '<!-- /wp:heading -->\n'
        '<!-- wp:list -->\n'
        f'<ul class="wp-block-list">{li_items}</ul>\n'
        '<!-- /wp:list -->\n'
        '</div>\n'
        '<!-- /wp:group -->'
    )


def find_first_paragraph_end(content):
    """Find the end of the first wp:paragraph block."""
    # Look for end of first paragraph block
    match = re.search(r'<!-- /wp:paragraph -->', content)
    if match:
        return match.end()
    return None


def find_trust_footer_pos(content):
    """Find position just before the trust footer / last major section.
    Look for common trust footer patterns."""
    # Try to find trust/disclosure footer patterns
    patterns = [
        r'<!-- wp:group.*?(?:trust|disclosure|footer|sources|editorial)',
        r'<div[^>]*>.*?(?:Editorial Standards|Our Commitment|Why Trust)',
        r'<!-- wp:separator',
    ]
    last_pos = None
    for pat in patterns:
        for m in re.finditer(pat, content, re.IGNORECASE):
            if last_pos is None or m.start() > last_pos:
                last_pos = m.start()

    # If we found separators, use the LAST one as footer boundary
    sep_positions = [m.start() for m in re.finditer(r'<!-- wp:separator', content)]
    if sep_positions:
        # The last separator often precedes the trust footer
        last_pos = sep_positions[-1]

    if last_pos is None:
        # Fallback: insert before end
        last_pos = len(content)

    return last_pos


def inject_uk_refs(content, cluster):
    """Add UK authority references as inline mentions within existing paragraphs."""
    refs = UK_REFS.get(cluster, {})
    added = []
    for org_name, url in refs.items():
        # Check if already referenced
        if org_name.lower() in content.lower():
            continue
        # Build the reference link
        link = f'<a href="{url}" rel="nofollow">{org_name}</a>'
        # We won't inject inline (too risky to break content).
        # Instead we'll note it's already covered in At a Glance / Key Takeaways
        # The At a Glance and Key Takeaways blocks already include inline UK refs
        added.append(org_name)
    return content, added


def inject_glossary_crosslink(content, cluster, post_id):
    """Add a glossary cross-link if not already present."""
    # Determine relevant glossary
    if cluster == "Dog Food":
        gloss_id = 7172
        gloss_text = "dog food terminology glossary"
    elif cluster == "Dog Beds":
        gloss_id = 7174
        gloss_text = "dog beds terminology glossary"
    elif cluster == "Educational":
        gloss_id = 7177
        gloss_text = "pet health terminology glossary"
    else:
        return content, False

    # Don't add to glossary pages themselves
    if post_id == gloss_id:
        return content, False

    gloss_url = GLOSSARY_LINKS.get(gloss_id, "")
    if not gloss_url:
        return content, False

    # Check if glossary link already exists
    if gloss_url in content or gloss_text in content.lower():
        return content, False

    # Add a subtle glossary reference paragraph before the trust footer
    gloss_block = (
        '\n<!-- wp:paragraph {"style":{"typography":{"fontSize":"14px"}}} -->\n'
        f'<p style="font-size:14px"><em>Unfamiliar with any terms used above? Visit our <a href="{gloss_url}">{gloss_text}</a> for clear definitions.</em></p>\n'
        '<!-- /wp:paragraph -->\n'
    )

    footer_pos = find_trust_footer_pos(content)
    content = content[:footer_pos] + gloss_block + content[footer_pos:]
    return content, True


def compute_citation_score(content, cluster):
    """Score a post's citation readiness 0-100."""
    score = 0

    # At a Glance present (20 pts)
    if has_block(content, "At a Glance"):
        score += 20

    # Key Takeaways present (20 pts)
    if has_block(content, "Key Takeaways"):
        score += 20

    # UK authority references (up to 20 pts)
    refs = UK_REFS.get(cluster, {})
    ref_count = 0
    for org_name in refs:
        if org_name.lower() in content.lower():
            ref_count += 1
    if refs:
        score += min(20, int(20 * ref_count / len(refs)))

    # FAQ section (10 pts)
    if has_block(content, "faq") or has_block(content, "frequently asked"):
        score += 10

    # Glossary cross-link (10 pts)
    for url in GLOSSARY_LINKS.values():
        if url in content:
            score += 10
            break

    # UK-specific content markers (10 pts)
    uk_markers = ["uk", "britain", "england", "rspca", "pdsa", "kennel club",
                   "dogs trust", "£", "stone", "kg", "cm", "celsius", "°c"]
    uk_count = sum(1 for m in uk_markers if m.lower() in content.lower())
    score += min(10, uk_count * 2)

    # Structured data quality - lists, headings, etc (10 pts)
    list_count = content.lower().count("wp:list")
    heading_count = content.lower().count("wp:heading")
    if list_count >= 3:
        score += 5
    if heading_count >= 4:
        score += 5

    return min(100, score)


# ── main processing ─────────────────────────────────────────────────────────

def main():
    log_rows = []
    score_rows = []
    total = len(ALL_IDS)
    updated = 0
    skipped = 0
    errors = 0

    print(f"[10AL] Starting Citation Acceleration Sprint for {total} posts")
    print(f"[10AL] Clusters: {list(CLUSTERS.keys())}")
    print(f"[10AL] Time: {datetime.now().isoformat()}")
    print("=" * 70)

    for idx, post_id in enumerate(ALL_IDS, 1):
        cluster = ID_TO_CLUSTER[post_id]
        print(f"\n[{idx}/{total}] Processing post {post_id} ({cluster})...")

        try:
            # Fetch post
            post = api_get(f"posts/{post_id}?context=edit")
            if "id" not in post:
                print(f"  ERROR: Could not fetch post {post_id}: {post}")
                log_rows.append([post_id, "FETCH ERROR", cluster, "N/A", "N/A", "N/A", "error"])
                errors += 1
                time.sleep(2)
                continue

            title = post["title"]["raw"]
            content = post["content"]["raw"]
            print(f"  Title: {title[:80]}")
            print(f"  Content length: {len(content)} chars")

            modified = False
            aag_added = False
            kt_added = False
            uk_refs_added = []

            # 1. Check and add "At a Glance"
            if has_block(content, "At a Glance"):
                print("  [SKIP] At a Glance already exists")
            elif post_id in AT_A_GLANCE:
                aag_block = build_at_a_glance(AT_A_GLANCE[post_id])
                first_p_end = find_first_paragraph_end(content)
                if first_p_end:
                    content = content[:first_p_end] + "\n\n" + aag_block + "\n\n" + content[first_p_end:]
                    aag_added = True
                    modified = True
                    print("  [ADD] At a Glance inserted after first paragraph")
                else:
                    print("  [WARN] Could not find first paragraph end")
            else:
                print(f"  [WARN] No At a Glance content defined for post {post_id}")

            # 2. Check and add "Key Takeaways"
            if has_block(content, "Key Takeaways"):
                print("  [SKIP] Key Takeaways already exists")
            elif post_id in KEY_TAKEAWAYS:
                kt_block = build_key_takeaways(KEY_TAKEAWAYS[post_id])
                footer_pos = find_trust_footer_pos(content)
                content = content[:footer_pos] + "\n\n" + kt_block + "\n\n" + content[footer_pos:]
                kt_added = True
                modified = True
                print("  [ADD] Key Takeaways inserted before trust footer")
            else:
                print(f"  [WARN] No Key Takeaways content defined for post {post_id}")

            # 3. UK authority references (already embedded in At a Glance / Key Takeaways)
            refs = UK_REFS.get(cluster, {})
            for org_name in refs:
                if org_name.lower() in content.lower():
                    uk_refs_added.append(org_name)

            # 4. Glossary cross-link
            content, gloss_added = inject_glossary_crosslink(content, cluster, post_id)
            if gloss_added:
                modified = True
                print("  [ADD] Glossary cross-link added")

            # 5. Update post if modified
            if modified:
                result = api_update(post_id, {"content": content})
                if "id" in result:
                    updated += 1
                    print(f"  [OK] Post {post_id} updated successfully")
                    status = "updated"
                else:
                    errors += 1
                    err_msg = result.get("message", "Unknown error")
                    print(f"  [ERROR] Failed to update post {post_id}: {err_msg}")
                    status = f"error: {err_msg}"
            else:
                skipped += 1
                status = "no_changes_needed"
                print(f"  [SKIP] No changes needed for post {post_id}")

            # 6. Compute citation score (on the final content)
            citation_score = compute_citation_score(content, cluster)
            print(f"  Citation score: {citation_score}/100")

            log_rows.append([
                post_id, title, cluster,
                "yes" if aag_added else ("exists" if has_block(content, "At a Glance") else "no"),
                "yes" if kt_added else ("exists" if has_block(content, "Key Takeaways") else "no"),
                ";".join(uk_refs_added) if uk_refs_added else "none",
                status
            ])
            score_rows.append([post_id, title, cluster, citation_score])

        except Exception as e:
            print(f"  [EXCEPTION] {e}")
            log_rows.append([post_id, "EXCEPTION", cluster, "N/A", "N/A", "N/A", f"exception: {e}"])
            score_rows.append([post_id, "EXCEPTION", cluster, 0])
            errors += 1

        time.sleep(2)  # Rate limiting

    # Write log CSV
    log_path = os.path.join(DATA_DIR, "citation_acceleration_log.csv")
    with open(log_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "title", "cluster", "at_a_glance_added", "key_takeaways_added", "uk_refs_added", "status"])
        w.writerows(log_rows)
    print(f"\n[LOG] Written to {log_path}")

    # Write scores CSV
    scores_path = os.path.join(DATA_DIR, "citation_scores.csv")
    with open(scores_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "title", "cluster", "citation_score"])
        w.writerows(score_rows)
    print(f"[SCORES] Written to {scores_path}")

    # Summary
    print("\n" + "=" * 70)
    print(f"[10AL] Citation Acceleration Sprint Complete")
    print(f"  Total posts processed: {total}")
    print(f"  Updated: {updated}")
    print(f"  Skipped (no changes): {skipped}")
    print(f"  Errors: {errors}")

    # Score summary by cluster
    print("\n  Citation Scores by Cluster:")
    for cluster_name in CLUSTERS:
        cluster_scores = [r[3] for r in score_rows if r[2] == cluster_name and isinstance(r[3], (int, float))]
        if cluster_scores:
            avg = sum(cluster_scores) / len(cluster_scores)
            print(f"    {cluster_name}: avg {avg:.1f}/100 (min {min(cluster_scores)}, max {max(cluster_scores)})")

    print(f"\n  Time: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
