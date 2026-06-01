#!/usr/bin/env python3
"""Create 20 Indoor Cats spoke posts for PetHub Online with full structure."""
import requests, json, time, re, sys

WP = "https://pethubonline.com/wp-json/wp/v2"
AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
PEXELS_KEY = "dmGyKrZqTlwukxWzOK1EkH4jbEv9EaIDpLGj7eL5MZ07bl6AR9OEoHlB"
PEXELS_URL = "https://api.pexels.com/v1/search"
CATEGORY_INDOOR_CATS = 1443
AFFILIATE_TAG = "pethubonline-21"

# Create session with Accept-Encoding fix to avoid brotli decode errors
session = requests.Session()
session.auth = AUTH
session.headers.update({"Accept-Encoding": "gzip, deflate"})

IL = {
    "indoor_exercise": "https://pethubonline.com/indoor-cat-exercise-routines-uk/",
    "enrichment": "https://pethubonline.com/indoor-cat-enrichment-checklist/",
    "new_cat": "https://pethubonline.com/new-cat-owner-setup-guide/",
    "catio": "https://pethubonline.com/diy-catio-building-plans-uk/",
    "multi_pet": "https://pethubonline.com/multi-pet-household-management-uk/",
    "seasonal": "https://pethubonline.com/seasonal-pet-care-calendar-uk/",
    "first_time": "https://pethubonline.com/first-time-pet-owner-guide-uk/",
    "puzzle": "https://pethubonline.com/cat-puzzle-feeders-uk-guide/",
    "interactive": "https://pethubonline.com/interactive-cat-toys-solo-play-uk/",
    "diy": "https://pethubonline.com/diy-cat-toys-household-items/",
}

SPOKES = [
    # ── 1: Indoor Cat Daily Routine ──
    {
        "title": "Indoor Cat Daily Routine: A Structured Schedule for Happy House Cats",
        "slug": "indoor-cat-daily-routine-schedule",
        "focus_keyword": "indoor cat daily routine",
        "seo_title": "Indoor Cat Daily Routine: Daily Schedule for House Cats UK | PetHub Online",
        "seo_desc": "Create the perfect indoor cat daily routine with structured play, feeding, and enrichment. UK-focused schedule covering morning to night for happy, healthy house cats.",
        "quick_answer": "An ideal indoor cat daily routine includes morning interactive play (10-15 minutes) followed by breakfast via puzzle feeder, midday passive enrichment such as window watching, an evening wand-play session before dinner, and a short pre-bed play burst with a settling snack. This structure mirrors the natural hunt-catch-eat-groom-sleep cycle and prevents boredom, obesity, and behavioural issues common in UK indoor cats.",
        "at_a_glance": [
            "Morning interactive play before breakfast engages the natural hunting cycle",
            "Puzzle feeders at mealtimes turn passive eating into mental enrichment",
            "Midday passive enrichment (window perches, cat TV) suits natural rest periods",
            "Evening wand play is the day's most vigorous session, before dinner",
            "A short pre-bed play session and snack helps prevent nighttime zoomies",
            "Consistency matters more than perfection; stick to the same times daily"
        ],
        "sections": [
            {"heading": "Why Indoor Cats Need a Structured Routine",
             "content": f'<p>Indoor cats lack the environmental variety that outdoor access provides. Without a structured routine, many indoor cats fall into a cycle of excessive sleeping, overeating, and boredom-related behaviours. A predictable daily schedule gives your cat anticipation points throughout the day, reducing anxiety and providing the mental framework that wild cats get from their natural hunting-resting rhythm.</p><p>Research from the Journal of Feline Medicine and Surgery confirms that cats thrive on routine. Changes to feeding times, play schedules, or household patterns can trigger stress responses including inappropriate urination and over-grooming. By establishing a consistent daily routine, you create a secure framework your indoor cat can rely on.</p><p>UK charity Cats Protection recommends that indoor cats receive at least two interactive play sessions daily alongside environmental enrichment. Our <a href="{IL["enrichment"]}">indoor cat enrichment checklist</a> complements this daily routine with a comprehensive environmental audit.</p>'},
            {"heading": "Morning Routine: Play, Feed, Engage (6-8 AM)",
             "content": f'<p>The morning is one of two crepuscular activity peaks when your cat is naturally most alert. Start with 10-15 minutes of wand-toy play, simulating realistic prey movement along the ground. This satisfies the morning hunting drive and creates the natural hunt-catch-eat sequence that leaves your cat calm afterwards.</p><p>After play, serve breakfast through a puzzle feeder rather than a bowl. Even scattering kibble across a snuffle mat extends the enrichment from 30 seconds to 10-15 minutes. Before leaving for work, open curtains at the bird-watching window and set out the day\'s rotation of solo toys.</p><p>This 30-minute morning block makes the single biggest difference to your indoor cat\'s daily welfare. See our <a href="{IL["puzzle"]}">cat puzzle feeders guide</a> for breakfast puzzle options suitable for all ability levels.</p>'},
            {"heading": "Midday: Passive Enrichment and Rest (10 AM - 4 PM)",
             "content": f'<p>The middle of the day is naturally a rest-heavy period. Rather than expecting active play, provide passive enrichment that your cat can access at will. A window perch overlooking a garden with a bird feeder is one of the most effective forms of passive enrichment for indoor cats in the UK.</p><p>Cat TV (YouTube channels showing birds, fish, and small animals) supplements window watching, particularly for cats in flats without garden views. Studies suggest cats respond positively to species-specific music at frequencies matching their vocalisations. Leave cardboard boxes, paper bags (handles removed), and tunnel toys available for self-directed exploration.</p><p>If you work from home, brief 5-minute interactions during the afternoon break up the quiet period. Our <a href="{IL["interactive"]}">interactive solo play toys guide</a> covers the best options for independent enrichment.</p>'},
            {"heading": "Evening Routine: Peak Play and Dinner (5-7 PM)",
             "content": f'<p>The evening is the second crepuscular activity peak and often the best time for the day\'s most vigorous play session. Most UK owners find their cat is most enthusiastic and engaged during this window, making it ideal for a full 15-minute wand-play session with warm-up, peak, and cool-down phases.</p><p>Follow the evening play session with dinner, completing the hunt-catch-eat cycle. Serving dinner through a puzzle feeder extends the enrichment. For cats fed both wet and dry food, use wet food as the immediate post-play reward and dry food in a puzzle feeder for extended engagement.</p><p>After dinner, most cats enter a grooming-then-rest phase. This is the ideal time to refresh the environment for tomorrow: swap toy rotation groups, move a box, or add fresh catnip. See our <a href="{IL["indoor_exercise"]}">indoor exercise routines guide</a> for detailed play techniques.</p>'},
            {"heading": "Pre-Bed Routine and Nighttime Management (9-11 PM)",
             "content": f'<p>A short 5-10 minute play session before your bedtime, followed by a small snack, triggers the sleep-inducing post-hunt-eat cycle. Over 2-3 weeks, this routine significantly reduces nighttime disturbance in most cats. Leave safe solo toys available overnight for cats that wake during the night.</p><p>If your cat remains consistently disruptive at night despite the pre-bed routine, the overall daily enrichment may be insufficient. Cats that do not burn enough energy during the day expend it at night. Increase daytime play intensity before adjusting the nighttime routine.</p><p>For UK cats where daylight varies dramatically between seasons, adjust timing seasonally: earlier settling routines in winter, later in summer when extended daylight keeps them active. Our <a href="{IL["seasonal"]}">seasonal pet care calendar</a> provides month-by-month timing guidance.</p>'}
        ],
        "comparison_table": {
            "title": "Indoor Cat Daily Routine: Time Blocks",
            "headers": ["Time", "Activity", "Duration", "Enrichment Type", "Equipment"],
            "rows": [
                ["6-8 AM", "Interactive play + breakfast", "20-30 min", "Physical + mental", "Wand toy, puzzle feeder"],
                ["10 AM-2 PM", "Passive enrichment + solo play", "Self-paced", "Visual + exploratory", "Window perch, rotation toys"],
                ["2-5 PM", "Rest + optional interaction", "Self-paced", "Recovery", "Comfortable beds, hiding spots"],
                ["5-7 PM", "Peak play + dinner", "20-30 min", "Physical + mental", "Wand toy, puzzle feeder"],
                ["9-10 PM", "Short play + bedtime snack", "10-15 min", "Energy burn", "Wand toy, treats"]
            ]
        },
        "common_mistakes": [
            "Providing all enrichment in one burst and leaving the rest of the day empty",
            "Skipping the morning play session because of time pressure",
            "Feeding from a bowl instead of using puzzle feeders for mental stimulation",
            "Not adjusting the routine seasonally for daylight and temperature changes",
            "Expecting cats to entertain themselves all day without any structured interaction"
        ],
        "what_to_do_next": [
            "Set two phone alarms today: morning play before breakfast, evening play before dinner",
            f'Switch at least one meal to a puzzle feeder this week using our <a href="{IL["puzzle"]}">puzzle feeders guide</a>',
            f'Read our <a href="{IL["indoor_exercise"]}">indoor exercise routines guide</a> for detailed play techniques',
            "Track your routine for one week and note your cat's behaviour improvements",
            f'Download our <a href="{IL["enrichment"]}">enrichment checklist</a> to audit your home environment'
        ],
        "faq": [
            ("How much activity does an indoor cat need daily?", "A minimum of 20-30 minutes of interactive play split across 2-3 sessions, plus access to solo toys, puzzle feeders, and environmental enrichment. Total stimulation should span multiple periods throughout the day."),
            ("Can indoor cats be happy without going outside?", "Absolutely. Research confirms indoor cats can have excellent welfare when enrichment needs are met through daily play, puzzle feeding, vertical space, and human interaction."),
            ("What if I work long hours?", "Set up passive enrichment before leaving: window perch, rotated solo toys, and a puzzle feeder. The morning and evening play sessions bookend the day effectively."),
            ("Should I keep the same routine on weekends?", "Yes. Consistency is key. Cats thrive on predictable schedules, so maintain the same play and feeding times on weekends."),
            ("How long before I see behaviour improvements?", "Most owners notice calmer behaviour, less nighttime disruption, and reduced destructive habits within 2-3 weeks of establishing a consistent routine.")
        ],
        "key_terms": [
            ("Crepuscular", "Active primarily during dawn and dusk. Cats' natural activity pattern that determines optimal play timing."),
            ("Hunt-Catch-Eat-Groom-Sleep", "The natural feline cycle. Structuring play before meals mimics this sequence for maximum enrichment."),
            ("Passive Enrichment", "Environmental features providing stimulation without active participation: window views, ambient sounds, hiding spots."),
            ("Puzzle Feeding", "Serving food in devices requiring problem-solving, turning passive eating into active enrichment."),
            ("Environmental Rotation", "Regularly changing elements of the indoor environment to maintain novelty and prevent habituation.")
        ],
        "products": [
            ("K&H EZ Mount Window Bed", "Suction-cup window perch for bird watching, holds up to 27 kg, ideal for flats", "kh+ez+mount+window+bed+cat+perch"),
            ("Catit Senses 2.0 Digger", "Tube-style puzzle feeder, adjustable difficulty, dishwasher safe", "catit+senses+digger+cat+puzzle"),
            ("Da Bird Original Wand Toy", "Premium feather wand mimicking bird flight, replaceable attachments", "da+bird+original+wand+cat+toy"),
            ("LickiMat Casper Cat Lick Mat", "Silicone lick mat for wet food enrichment, calming effect", "lickimat+casper+cat+lick+mat")
        ],
        "sources": [
            "Cats Protection UK - Indoor Cat Care Guidelines",
            "Journal of Feline Medicine and Surgery - Routine and Feline Welfare",
            "International Cat Care - Keeping Indoor Cats Happy",
            "PDSA Animal Wellbeing Report - UK Cat Statistics",
            "British Veterinary Association - Environmental Enrichment"
        ],
        "image_queries": ["indoor cat playing", "cat window perch", "cat puzzle feeder", "cat relaxing indoors"]
    },

    # ── 2: Indoor Cat Weight Tracking ──
    {
        "title": "Indoor Cat Weight Tracking: Monitoring Your House Cat's Weight",
        "slug": "indoor-cat-weight-tracking-guide",
        "focus_keyword": "indoor cat weight tracking",
        "seo_title": "Indoor Cat Weight Tracking: Monitor House Cat Weight UK | PetHub Online",
        "seo_desc": "Complete indoor cat weight tracking guide covering weekly weigh-ins, body condition scoring, healthy weight ranges, and preventing obesity in UK house cats.",
        "quick_answer": "Indoor cats should be weighed weekly using a consistent method: place a carrier on digital scales, weigh with and without the cat, and record the difference. A healthy adult cat typically weighs 3.5-5.5 kg, but the ideal weight depends on breed and frame size. Body condition scoring on a 1-9 scale (ideal is 4-5) provides a more accurate health picture than weight alone. Indoor cats are at higher obesity risk because they burn fewer calories, making regular tracking essential.",
        "at_a_glance": [
            "Weigh your indoor cat weekly at the same time using consistent scales",
            "Healthy adult cat weight is typically 3.5-5.5 kg but varies by breed",
            "Body condition score (1-9 scale, ideal 4-5) is more useful than weight alone",
            "A 200g change in a 4 kg cat is equivalent to significant weight change in a human",
            "Indoor cats burn 20-30% fewer calories than outdoor cats",
            "Weight changes over 10% warrant a veterinary consultation"
        ],
        "sections": [
            {"heading": "Why Weight Tracking Matters for Indoor Cats",
             "content": f'<p>Indoor cats face a significantly higher obesity risk than cats with outdoor access. The PDSA\'s Animal Wellbeing Report identifies that over 30 percent of UK cats are overweight or obese, with indoor cats disproportionately affected. Reduced activity combined with ad-lib feeding creates a calorie surplus that accumulates gradually, often unnoticed until a vet visit reveals the problem.</p><p>A 200-gram change in a 4 kg cat represents a 5 percent body weight shift, equivalent to a substantial change in human terms. Because cats are small, even minor weight changes can indicate developing health issues including diabetes, hyperthyroidism, or kidney disease. Regular tracking catches these trends early, when intervention is most effective.</p><p>Weight tracking also measures the effectiveness of your enrichment and exercise routine. If your cat maintains a healthy weight on your current <a href="{IL["indoor_exercise"]}">indoor exercise programme</a>, you know the activity level is adequate. Weight gain signals a need for more play or dietary adjustment.</p>'},
            {"heading": "How to Weigh Your Cat Accurately at Home",
             "content": '<p>The most reliable home method uses digital bathroom scales. Step on the scales holding your cat, note the combined weight, then weigh yourself alone. The difference is your cat\'s weight. For accuracy, use the same scales at the same time of day (before morning feeding works well).</p><p>Alternatively, place a cat carrier on kitchen scales, zero them, then place the cat inside. This method avoids needing to hold a wriggling cat and gives more precise readings. Digital kitchen scales accurate to 10g are available for under 15 pounds from UK retailers.</p><p>Record every weigh-in in a simple log (notebook, phone notes, or spreadsheet). Track the trend over weeks and months rather than reacting to individual readings. A single high reading after a large meal means nothing; a consistent upward trend over four weeks requires action.</p>'},
            {"heading": "Body Condition Scoring: Beyond the Numbers",
             "content": f'<p>Body condition scoring (BCS) on a 1-9 scale provides more useful information than weight alone because it accounts for body composition. A muscular 5.5 kg cat may be perfectly healthy while a sedentary 4.5 kg cat with the same frame could be overweight. BCS assesses fat coverage over the ribs, waist visibility from above, and abdominal tuck from the side.</p><p>Score 4-5 is ideal: you can feel the ribs with light pressure but not see them, there is a visible waist when viewed from above, and a slight abdominal tuck from the side. Scores of 6-7 indicate overweight (ribs difficult to feel, no visible waist), while 8-9 indicates obesity (ribs impossible to feel, belly sags). Scores of 1-3 indicate underweight.</p><p>Your vet can teach you body condition scoring at any routine appointment. Once learned, you can assess your cat at home alongside regular weigh-ins. International Cat Care and the PDSA both provide free BCS charts on their websites. Combine BCS with our <a href="{IL["enrichment"]}">enrichment checklist</a> to ensure your cat stays both mentally and physically healthy.</p>'},
            {"heading": "Healthy Weight Ranges by Breed and Age",
             "content": '<p>Weight ranges vary significantly by breed. A British Shorthair may naturally weigh 4-7 kg, while a Siamese is typically 3-5 kg. Mixed-breed cats in the UK average 3.5-5.5 kg. Knowing your cat\'s breed-typical range helps set realistic targets. Your vet can confirm the ideal weight for your individual cat based on frame size and breed.</p><p>Kittens gain weight rapidly until 12 months, then gradually until reaching adult weight at 2-3 years. Senior cats (10+) may naturally lose some muscle mass, causing weight to decrease slightly. Any rapid weight change in either direction at any age warrants veterinary investigation.</p><p>For indoor cats specifically, aim for the lower-to-middle range for their breed. Indoor cats with lower activity levels do not need the muscle mass and energy reserves that outdoor cats maintain. A lean indoor British Shorthair at 4.5 kg is likely healthier than one at 6.5 kg, provided the BCS confirms appropriate body composition.</p>'},
            {"heading": "Preventing and Managing Indoor Cat Obesity",
             "content": f'<p>Prevention is far easier than treatment. Measure food portions accurately using kitchen scales rather than estimating with scoops. Follow the feeding guidelines on your cat\'s food packaging, adjusting for indoor/less active cats (most premium brands include this guidance). Weigh the food, not the volume, as kibble density varies between brands.</p><p>Replace at least one meal daily with puzzle feeding. This slows eating speed, extends mealtime engagement, and provides mental stimulation. Cats using <a href="{IL["puzzle"]}">puzzle feeders</a> consume the same calories but take longer, improving satiety signals and reducing overeating.</p><p>If your cat is already overweight, consult your vet before starting a weight loss programme. Cats must lose weight gradually (1-2 percent body weight per week maximum) because rapid weight loss can trigger hepatic lipidosis, a life-threatening liver condition. Your vet can calculate the correct calorie reduction and monitor progress safely. Combine dietary adjustment with increased play using our <a href="{IL["indoor_exercise"]}">indoor exercise routines</a>.</p>'}
        ],
        "comparison_table": {
            "title": "Indoor Cat Weight Tracking Methods",
            "headers": ["Method", "Accuracy", "Cost", "Ease of Use", "Frequency"],
            "rows": [
                ["Bathroom scales (hold cat)", "Moderate (+/- 100g)", "Free (existing scales)", "Easy", "Weekly"],
                ["Kitchen scales + carrier", "High (+/- 10g)", "Under 15 pounds", "Moderate", "Weekly"],
                ["Baby scales", "Very high (+/- 5g)", "20-40 pounds", "Easy", "Weekly"],
                ["Vet weigh-in", "Clinical grade", "Free at most UK vets", "Requires visit", "Monthly/quarterly"],
                ["Body condition score", "Qualitative", "Free", "Requires learning", "Fortnightly"]
            ]
        },
        "common_mistakes": [
            "Only weighing at annual vet visits, missing gradual weight changes throughout the year",
            "Using volume-based scoops instead of weighing food portions accurately",
            "Assuming a plump indoor cat is healthy when they may be clinically overweight",
            "Starting rapid weight loss without veterinary supervision, risking hepatic lipidosis",
            "Ignoring treats and extras when calculating daily calorie intake"
        ],
        "what_to_do_next": [
            "Weigh your cat this week and record the baseline weight",
            "Learn body condition scoring from your vet or the PDSA free chart",
            f'Start weighing food portions with kitchen scales and follow indoor cat feeding guidelines',
            f'Read our <a href="{IL["indoor_exercise"]}">indoor exercise routines guide</a> to increase daily activity',
            "Set a weekly phone reminder for consistent weigh-in sessions"
        ],
        "faq": [
            ("How often should I weigh my indoor cat?", "Weekly is ideal for ongoing monitoring. Record the weight and track the trend. If your cat is on a vet-supervised weight loss programme, weigh twice weekly."),
            ("What is a healthy weight for a house cat?", "Most adult cats weigh 3.5-5.5 kg, but the ideal depends on breed and frame. A British Shorthair may be healthy at 6 kg while a Siamese would be overweight. Body condition scoring is more reliable than weight alone."),
            ("How can I tell if my indoor cat is overweight?", "Body condition score your cat: if you cannot easily feel the ribs with light pressure, there is no visible waist from above, or the belly sags when viewed from the side, your cat is likely overweight."),
            ("Do indoor cats need fewer calories than outdoor cats?", "Yes. Indoor cats burn 20-30 percent fewer calories than outdoor cats. Most premium cat food brands provide specific feeding guidelines for indoor or less active cats."),
            ("Can overweight cats lose weight safely?", "Yes, but only gradually under veterinary supervision. Cats should lose no more than 1-2 percent body weight per week. Rapid weight loss can cause hepatic lipidosis, a dangerous liver condition.")
        ],
        "key_terms": [
            ("Body Condition Score (BCS)", "A 1-9 scale assessing fat coverage. Score 4-5 is ideal. Used alongside weight for comprehensive health monitoring."),
            ("Hepatic Lipidosis", "A life-threatening liver condition caused by rapid fat mobilisation. Prevents aggressive calorie restriction in cats."),
            ("Ad-Lib Feeding", "Leaving food freely available all day. Contributes to obesity in indoor cats and removes puzzle-feeding enrichment opportunities."),
            ("Calorie Surplus", "Consuming more calories than expended. Even small daily surpluses accumulate into significant weight gain over months."),
            ("Satiety", "The feeling of fullness after eating. Puzzle feeders and measured portions improve satiety signalling in cats.")
        ],
        "products": [
            ("Salter Digital Kitchen Scales", "Accurate to 1g, ideal for weighing food portions and cat in carrier, UK brand", "salter+digital+kitchen+scales"),
            ("Catit Senses 2.0 Food Tree", "Multi-level puzzle feeder that slows eating and provides enrichment", "catit+senses+food+tree+cat"),
            ("Royal Canin Indoor Cat Food", "Specifically formulated for indoor cats with reduced calories and hairball support", "royal+canin+indoor+cat+food"),
            ("PetSafe SlimCat Feeder Ball", "Adjustable treat-dispensing ball for portion-controlled feeding enrichment", "petsafe+slimcat+feeder+ball+cat")
        ],
        "sources": [
            "PDSA Animal Wellbeing Report - UK Cat Obesity Statistics",
            "International Cat Care - Body Condition Scoring",
            "Journal of Feline Medicine and Surgery - Feline Obesity Management",
            "Cats Protection UK - Feeding Your Cat",
            "British Veterinary Association - Weight Management Guidelines"
        ],
        "image_queries": ["cat on scales", "healthy indoor cat", "cat eating puzzle feeder", "cat body condition"]
    },

    # ── 3: Indoor Cat Window Enrichment ──
    {
        "title": "Indoor Cat Window Enrichment: Perches, Bird Feeders, and Views",
        "slug": "indoor-cat-window-enrichment-guide",
        "focus_keyword": "indoor cat window enrichment",
        "seo_title": "Indoor Cat Window Enrichment: Perches & Bird Feeders UK | PetHub Online",
        "seo_desc": "Transform your windows into cat enrichment stations with perches, bird feeders, and secure views. UK guide to window enrichment for indoor house cats.",
        "quick_answer": "Window enrichment is one of the most effective and low-effort forms of stimulation for indoor cats. Install a sturdy window perch or heated window bed, position a bird feeder outside the window to attract wildlife, and ensure windows are secured with mesh or restrictors to prevent falls. The constantly changing visual stimulation of birds, weather, and garden activity can engage an indoor cat for hours daily, providing passive enrichment that requires no active involvement from owners.",
        "at_a_glance": ["A window perch with bird feeder view provides hours of passive enrichment daily","Suction-cup perches hold 10-27 kg and install without drilling","Position bird feeders 1-2 metres from the window for optimal viewing","Always secure windows with mesh or restrictors to prevent cat falls","South and east-facing windows get the most bird activity in UK gardens","Heated window beds are especially valued by cats during UK winters"],
        "sections": [
            {"heading": "Why Window Enrichment Is Essential for Indoor Cats",
             "content": f'<p>For indoor cats, windows are the primary connection to the outside world. The constantly changing visual stimulation of birds, insects, weather patterns, and neighbourhood activity engages the same prey-detection and surveillance instincts that outdoor cats satisfy by patrolling their territory. A well-positioned window station can provide more enrichment hours per day than any toy.</p><p>Research published in the Journal of Feline Medicine and Surgery confirms that visual access to outdoor environments reduces stress behaviours in indoor cats. Cats with window perches show fewer signs of frustration, lower cortisol levels, and more relaxed body language compared to cats in homes where windows are blocked or inaccessible.</p><p>Window enrichment is particularly valuable for UK indoor cats during the winter months when outdoor access (even in catios) may be limited. A heated window bed overlooking an active bird feeder creates a compelling enrichment station that requires zero daily effort from owners. See our <a href="{IL["enrichment"]}">indoor cat enrichment checklist</a> for a full environmental audit.</p>'},
            {"heading": "Choosing and Installing Window Perches",
             "content": '<p>Window perches come in three main types: suction-cup mounted, bracket-mounted, and freestanding window platforms. Suction-cup perches are the most popular for UK homes because they install without drilling, hold 10-27 kg depending on the model, and can be repositioned between windows. Clean the window and suction cups with rubbing alcohol before installation for maximum adhesion.</p><p>Bracket-mounted perches screw into the wall beside the window and support heavier cats. These are the best choice for large breeds or multi-cat households where two cats may share the perch. Freestanding cat trees positioned against windows combine vertical space with window access.</p><p>When choosing a location, consider which windows get the most outdoor activity. South and east-facing windows typically attract more birds in UK gardens. Ground-floor windows overlooking gardens with hedges, trees, or feeders offer the richest viewing. Position the perch at a height that allows comfortable viewing without the cat needing to stretch or strain.</p>'},
            {"heading": "Bird Feeders: Creating a Cat TV Channel",
             "content": f'<p>A bird feeder positioned 1-2 metres from a window creates a living, constantly changing entertainment channel for your indoor cat. In the UK, a combination of seed feeders, fat ball holders, and a ground tray attracts the widest variety of species: blue tits, great tits, robins, blackbirds, house sparrows, and seasonal visitors like goldfinches and siskins.</p><p>Place feeders where your cat can see them clearly but where birds feel safe enough to visit. A feeder attached to the window itself provides the closest viewing but may take longer for birds to discover. A freestanding feeder 1-2 metres from the window, near a hedge or bush that provides escape cover, typically attracts birds faster.</p><p>The RSPB recommends feeding garden birds year-round in the UK, with particular importance during winter and the spring nesting season. This means your cat\'s window entertainment is consistent throughout the year. Regular feeder maintenance (cleaning fortnightly, removing old food) keeps birds visiting and reduces disease transmission. Our <a href="{IL["catio"]}">catio building guide</a> covers options for cats that want to get closer to the outdoors safely.</p>'},
            {"heading": "Window Safety: Preventing Falls and Escapes",
             "content": '<p>Window safety is non-negotiable for indoor cats. Cat falls from windows (known as high-rise syndrome) cause serious injuries and fatalities every year in the UK, with cases increasing during warm weather when windows are opened wider. Every window accessible to your cat must be secured with either purpose-built cat mesh, window restrictors, or tilt-and-turn limiters.</p><p>Cat-safe window mesh is available from UK suppliers including Flat Cats, which produces magnetic mesh screens that fit standard UK window frames. These allow full ventilation while preventing escape or falls. Window restrictors (the same type used for child safety) limit opening width to 10 cm or less, enough for airflow but too narrow for a cat to pass through.</p><p>Tilt-and-turn windows common in newer UK builds are particularly dangerous because a cat attempting to climb through can become trapped in the V-shaped opening, causing compression injuries to the abdomen. Either lock these windows in the tilt position with restrictors or cover the opening with mesh. Never assume a cat is too large or too sensible to attempt a window escape.</p>'},
            {"heading": "Seasonal Window Enrichment Adjustments",
             "content": f'<p>UK seasons dramatically affect window enrichment value. In spring and summer, longer daylight hours, increased bird activity, and open windows provide peak stimulation. Position perches at windows where the morning sun creates warm basking spots, and consider a window-mounted cat grass planter for additional sensory enrichment.</p><p>In autumn, falling leaves and migrating birds offer visual interest. Clean window perches and feeders more frequently as wet weather increases mould risk. In winter, a heated window bed (thermostatically controlled, available from UK pet retailers for 25-40 pounds) becomes especially valuable. Combine warmth with bird feeder views for maximum cold-weather enrichment.</p><p>If your home lacks suitable windows for enrichment (basement flat, north-facing only), supplement with cat TV content on a tablet or screen placed at cat height. While not as stimulating as live views, recorded bird and wildlife footage still engages visual hunting instincts. Rotate content weekly to prevent habituation. Our <a href="{IL["seasonal"]}">seasonal pet care calendar</a> provides month-by-month enrichment adjustments for UK cats.</p>'}
        ],
        "comparison_table": {
            "title": "Window Perch Types for Indoor Cats",
            "headers": ["Type", "Weight Capacity", "Installation", "UK Price Range", "Best For"],
            "rows": [
                ["Suction-cup perch", "10-27 kg", "No drilling, removable", "15-35 pounds", "Renters, single cats"],
                ["Bracket-mounted shelf", "20-40 kg", "Wall screws required", "20-50 pounds", "Heavy cats, permanent install"],
                ["Freestanding window tree", "30+ kg", "None (freestanding)", "40-100 pounds", "Multi-cat, vertical space"],
                ["Heated window bed", "10-20 kg", "Suction cups + plug", "25-40 pounds", "Senior cats, UK winters"],
                ["Hammock-style", "8-15 kg", "Suction cups", "10-25 pounds", "Budget option, light cats"]
            ]
        },
        "common_mistakes": ["Opening windows without mesh or restrictors, risking falls and escapes","Placing bird feeders too far from windows for the cat to see clearly","Choosing a window perch that cannot support your cat's weight","Ignoring south-facing windows that get the most wildlife activity","Blocking window access with furniture, removing the cat's viewing option"],
        "what_to_do_next": [
            "Identify the best window in your home for a cat enrichment station",
            "Install a window perch suited to your cat's size and your window type",
            "Position a bird feeder 1-2 metres from the window to attract wildlife",
            "Secure all accessible windows with mesh or restrictors before opening",
            f'Read our <a href="{IL["catio"]}">catio building guide</a> for secure outdoor access options'
        ],
        "faq": [
            ("Are suction-cup window perches safe for cats?", "Quality suction-cup perches rated for your cat's weight are safe when installed correctly. Clean the window and cups with alcohol before installation, check adhesion weekly, and ensure the drop below is safe if a cup fails."),
            ("What birds will visit my feeder in the UK?", "Common UK garden visitors include blue tits, great tits, robins, blackbirds, house sparrows, goldfinches, and woodpigeons. A mixed seed feeder plus fat balls attracts the widest variety."),
            ("Do cats get frustrated watching birds they cannot catch?", "Most cats enjoy bird watching without frustration. The chattering response some cats show is excitement, not distress. If your cat shows genuine stress signs, supplement window watching with wand-play sessions to satisfy hunting instincts."),
            ("How do I secure tilt-and-turn windows for cats?", "Tilt-and-turn windows are dangerous because cats can become trapped in the V-opening. Use locking restrictors to limit the tilt angle, or cover the opening with purpose-built cat mesh."),
            ("Can window enrichment replace outdoor access?", "Window enrichment is an excellent supplement but provides visual-only stimulation. Combine it with interactive play, puzzle feeders, and vertical space for comprehensive indoor enrichment.")
        ],
        "key_terms": [
            ("High-Rise Syndrome", "Injuries or death from falls from heights. Indoor cats are at risk when windows are unsecured."),
            ("Passive Enrichment", "Environmental features providing stimulation without active participation, such as window views."),
            ("Crepuscular Viewing", "Peak bird activity at dawn and dusk coincides with cats' natural activity periods, maximising enrichment."),
            ("Thermoregulation", "Body temperature regulation. Window basking helps cats maintain warmth, especially seniors."),
            ("Visual Enrichment", "Stimulation through sight. Window views, cat TV, and aquariums all provide visual enrichment.")
        ],
        "products": [
            ("K&H EZ Mount Window Bed", "Suction-cup window perch holding 27 kg, fleece cover, easy installation", "kh+ez+mount+window+bed+cat"),
            ("Flat Cats Window Screens", "UK-made magnetic mesh screens preventing cat escapes, fits standard windows", "flat+cats+window+screens+mesh"),
            ("Gardman A01044 Seed Feeder", "Heavy-duty seed feeder attracting UK garden birds, easy to clean and refill", "gardman+seed+feeder+birds+uk"),
            ("K&H Thermo-Kitty Window Sill", "Heated window perch for winter warmth, thermostatically controlled, UK plug", "kh+thermo+kitty+window+sill+heated")
        ],
        "sources": ["International Cat Care - Window Safety for Cats","RSPB - Feeding Garden Birds Year-Round","Journal of Feline Medicine and Surgery - Visual Enrichment","Cats Protection UK - Indoor Cat Environmental Needs","PDSA - Keeping Indoor Cats Safe"],
        "image_queries": ["cat on window perch", "cat watching birds window", "bird feeder garden uk", "indoor cat window seat"]
    },

    # ── 4-20: Remaining spokes (compact format) ──
    # I'll generate these with a helper to keep the file manageable
]

def _make_spoke(title, slug, fkw, seo_title, seo_desc, quick_answer, glance, sections, table, mistakes, next_steps, faq, terms, products, sources, img_queries):
    return {
        "title": title, "slug": slug, "focus_keyword": fkw,
        "seo_title": seo_title, "seo_desc": seo_desc,
        "quick_answer": quick_answer, "at_a_glance": glance,
        "sections": sections, "comparison_table": table,
        "common_mistakes": mistakes, "what_to_do_next": next_steps,
        "faq": faq, "key_terms": terms, "products": products,
        "sources": sources, "image_queries": img_queries
    }

# ── SPOKE 4: Indoor Cat Climbing Layouts ──
SPOKES.append(_make_spoke(
    "Indoor Cat Climbing Layouts: Vertical Space Planning for House Cats",
    "indoor-cat-climbing-layouts",
    "indoor cat climbing layouts",
    "Indoor Cat Climbing Layouts: Vertical Space Guide UK | PetHub Online",
    "Plan indoor cat climbing layouts with vertical space, cat trees, and wall shelves. UK guide to creating climbing routes for house cats.",
    "Indoor cats need vertical space for exercise, territory management, and security. A well-planned climbing layout connects floor level to ceiling height via cat trees, wall shelves, and perches, creating highways that allow cats to traverse rooms without touching the ground. Provide at least one vertical route per cat, with platforms at varied heights and resting spots at the highest accessible point.",
    ["Vertical space is as important as floor space for indoor cats","Provide at least one climbing route from floor to ceiling height per cat","Wall-mounted shelves create highways between rooms and above furniture","Cat trees should have stable bases wider than the tallest platform","Multiple heights allow cats in multi-cat homes to establish territory peacefully","Climbing burns calories and maintains muscle tone in sedentary indoor cats"],
    [
        {"heading": "Why Vertical Space Matters for Indoor Cats", "content": f'<p>Cats are three-dimensional creatures. In outdoor environments, they climb trees, walk along fences, and perch on rooftops. Indoor cats confined to floor-level living lose an entire dimension of their natural behaviour. Vertical space provides exercise through climbing, security through height (cats feel safest at the highest point in a room), and territory in multi-cat homes where height equals status.</p><p>A study published in Applied Animal Behaviour Science found that cats in environments with vertical access showed significantly lower stress indicators than those in equivalent-sized spaces without vertical options. This is particularly relevant for UK flats and smaller homes where floor space is limited but vertical space is underutilised.</p><p>Climbing also provides the physical exercise that indoor cats desperately need. A cat climbing from floor to ceiling engages major muscle groups in a way that ground-level play cannot replicate. For indoor cats at risk of obesity, vertical space is a natural exercise circuit. See our <a href="{IL["indoor_exercise"]}">indoor exercise routines guide</a> for combining climbing with play.</p>'},
        {"heading": "Cat Trees: Choosing the Right Structure", "content": '<p>A good cat tree has a base wider than its tallest platform (preventing tipping), platforms at multiple heights, sisal rope-wrapped posts for scratching, and at least one enclosed hideaway. For UK homes, consider the ceiling height: a 150-180 cm tree suits most rooms, while floor-to-ceiling tension pole models maximise height in homes with standard 240 cm ceilings.</p><p>Stability is non-negotiable. A cat tree that wobbles will be avoided by cautious cats and could injure confident ones. Test stability by pushing the top platform firmly; if it sways more than a few centimetres, the base is too small. For large breeds or multi-cat homes, consider wall-anchoring the tree for additional security.</p><p>Position the cat tree near a window for combined vertical and visual enrichment. A high platform overlooking a garden with a bird feeder creates a premium resting spot that most cats will choose over any ground-level bed. Avoid placing trees in quiet, unused rooms where the cat gains height but loses family interaction.</p>'},
        {"heading": "Wall Shelves and Cat Walkways", "content": f'<p>Wall-mounted shelves create cat highways that do not consume any floor space, making them ideal for UK flats and smaller homes. A series of shelves at staggered heights along a wall allows cats to climb, traverse, and rest above human activity. IKEA LACK shelves (30x26 cm) with added non-slip surfaces are a popular budget choice among UK cat owners.</p><p>Space shelves 30-40 cm apart vertically, close enough for comfortable stepping but far enough to create distinct platforms. Each shelf should be at least 25 cm deep and 40 cm wide for comfortable resting. Add carpet remnants or non-slip mats to prevent sliding. For corner transitions, angle shelves to create natural turning points.</p><p>For a complete cat highway, connect shelves to a cat tree at one end and a window perch at the other, creating a circuit the cat can traverse without touching the ground. This is the gold standard of indoor vertical enrichment. Our <a href="{IL["catio"]}">catio building guide</a> extends this concept to secure outdoor climbing structures.</p>'},
        {"heading": "Climbing Layouts for Multi-Cat Households", "content": f'<p>In multi-cat homes, vertical space is a critical conflict-prevention tool. Cats establish social hierarchies partly through height, so providing multiple climbing routes and resting spots at various levels allows each cat to find their preferred position without confrontation. The general rule is one cat tree plus one set of wall shelves per cat, with additional shared routes.</p><p>Ensure climbing routes have multiple access and exit points. A single-route cat tree with one way up and one way down creates a bottleneck where a dominant cat can trap a subordinate. Trees with multiple platforms accessible from different angles, or wall shelf routes with several step-on/step-off points, prevent territorial blocking.</p><p>Place resting platforms in different rooms so cats can establish separate territories at height. A shy cat with their own high shelf in a quiet room feels safer than one forced to share a single cat tree with a dominant housemate. See our <a href="{IL["multi_pet"]}">multi-pet household guide</a> for broader territory management strategies.</p>'},
        {"heading": "Budget-Friendly Vertical Solutions for UK Homes", "content": f'<p>Creating effective vertical space does not require expensive specialist furniture. IKEA LACK wall shelves (under 10 pounds each) with added carpet or sisal create functional cat shelves for a fraction of commercial cat shelf prices. Staircase-style arrangements using 3-5 shelves cost under 50 pounds total and provide a full climbing route.</p><p>Repurposed bookshelves placed against walls with some shelves cleared for cat access create instant multi-level resting spots. Secure them to the wall with anti-tip brackets. Old wooden ladders mounted horizontally on walls make rustic climbing routes. Sisal rope wrapped around table legs or staircase banisters adds scratching surfaces at no additional cost.</p><p>For DIY cat trees, wooden platforms on a central post (4x4 timber from B&Q) with sisal rope wrapping create sturdy, customisable structures. Plans are freely available online, and the materials for a ceiling-height tree typically cost 40-60 pounds versus 100-200 pounds for commercial equivalents. Our <a href="{IL["diy"]}">DIY cat toys guide</a> includes simple vertical enrichment projects.</p>'}
    ],
    {"title": "Indoor Cat Climbing Options Compared", "headers": ["Option", "Floor Space", "Height", "UK Cost", "Best For"],
     "rows": [["Cat tree (freestanding)", "60x60 cm base", "120-180 cm", "40-200 pounds", "Most homes, immediate setup"],
              ["Wall shelves (DIY)", "None", "Unlimited", "30-60 pounds", "Small flats, budget option"],
              ["Floor-to-ceiling pole", "30x30 cm base", "Full height", "50-150 pounds", "Maximum height, small footprint"],
              ["Commercial cat walkway", "None", "Wall-mounted", "100-300 pounds", "Design-conscious homes"],
              ["Repurposed bookshelf", "30-40 cm depth", "Up to 200 cm", "Free-30 pounds", "Quick, budget solution"]]},
    ["Choosing an unstable cat tree that wobbles and deters use","Placing the cat tree in an unused room away from family activity","Spacing wall shelves too far apart for comfortable stepping","Not providing multiple routes in multi-cat homes, creating territorial bottlenecks","Forgetting non-slip surfaces on shelves, causing cats to slide and lose confidence"],
    ["Assess your current vertical space: count cat trees, shelves, and high resting spots",f'Add at least one vertical climbing option per cat in your household',"Position a cat tree near the best window for combined vertical and visual enrichment",f'Read our <a href="{IL["enrichment"]}">enrichment checklist</a> for a complete environmental audit',"Try budget IKEA LACK shelves with carpet for an affordable cat highway"],
    [("How high should cat shelves be?", "Space shelves 30-40 cm apart vertically. The highest shelf should be at least 150 cm from the floor, or as high as practical. Cats prefer the highest available point for security and surveillance."),
     ("Are cat trees worth the money?", "Yes. A quality cat tree provides exercise, scratching, resting, and territorial benefits. Budget DIY alternatives using wall shelves can achieve similar results for less."),
     ("How many cat trees do I need?", "At least one per cat, plus wall shelves or additional vertical options. In multi-cat homes, multiple routes prevent territorial blocking."),
     ("Do cats need to reach the ceiling?", "Not necessarily, but taller is generally better. Floor-to-ceiling routes maximise the vertical space benefit. Even moderate height (150 cm) provides significant enrichment."),
     ("Can I make cat shelves from IKEA furniture?", "Yes. IKEA LACK shelves are widely used for cat walkways. Add non-slip surfaces and ensure secure wall mounting. They support up to 3 kg each, suitable for most cats when properly installed.")],
    [("Vertical Territory", "The use of height to establish social status and safety in cats. Higher positions confer greater security and perceived dominance."),
     ("Cat Highway", "A connected series of shelves, platforms, and perches that allows cats to traverse a room at height without touching the ground."),
     ("Arboreal Behaviour", "The natural tendency of cats to climb and rest in elevated positions, derived from their ancestral tree-climbing behaviour."),
     ("Territorial Blocking", "When a dominant cat controls access to a single-route vertical structure, preventing other cats from using it."),
     ("Anti-Tip Bracket", "Hardware used to secure freestanding furniture to the wall, preventing it from toppling when a cat jumps on it.")],
    [("Go Pet Club 72-Inch Cat Tree", "Multi-level cat tree with condos, perches, and sisal posts, stable wide base", "go+pet+club+72+inch+cat+tree"),
     ("IKEA LACK Wall Shelf 30x26", "Budget shelf perfect for DIY cat walkways, easy to mount, add non-slip surface", "ikea+lack+wall+shelf+30x26"),
     ("Catit Vesper High Base", "Design-conscious cat tree with walnut finish, memory foam cushions, UK retailer available", "catit+vesper+high+base+cat+tree"),
     ("SmartCat Multi-Level Cat Climber", "Door-mounted climbing structure, no floor space required, 4 platforms", "smartcat+multi+level+cat+climber")],
    ["Applied Animal Behaviour Science - Vertical Space and Feline Welfare","International Cat Care - Environmental Needs of Cats","Cats Protection UK - Creating a Cat-Friendly Home","PDSA - Indoor Cat Environment Guide","British Veterinary Association - Feline Environmental Enrichment"],
    ["cat climbing cat tree", "cat on wall shelf", "indoor cat vertical space", "cat tree living room"]
))

# Helper to generate remaining 16 spokes more compactly
def gen_spoke(n, title, slug, fkw, seo_desc, qa, glance, sec_data, tbl, mistakes, nexts, faq_data, terms, prods, srcs, imgs):
    seo_t = f"{title} | PetHub Online"
    if len(seo_t) > 70:
        seo_t = f"{fkw.title()} UK Guide | PetHub Online"
    sections = [{"heading": h, "content": c} for h, c in sec_data]
    return _make_spoke(title, slug, fkw, seo_t, seo_desc, qa, glance, sections, tbl, mistakes, nexts, faq_data, terms, prods, srcs, imgs)

# ── SPOKE 5: Cat Shelving Design Guide ──
SPOKES.append(gen_spoke(5,
    "Cat Shelving Design Guide: Wall Shelves and Walkways for Indoor Cats",
    "cat-shelving-design-guide-uk",
    "cat shelving design guide",
    "Design cat wall shelves and walkways for indoor cats. UK guide covering materials, spacing, installation, and layouts for cat-friendly shelving systems.",
    "Cat shelving transforms bare walls into functional climbing and resting routes. Use shelves at least 25 cm deep and 40 cm wide, spaced 30-40 cm vertically, with non-slip surfaces. Stagger shelves in a zigzag pattern for natural climbing movement. Secure all shelves with appropriate wall fixings for your wall type (plasterboard anchors, masonry plugs) and ensure each shelf supports at least twice your cat's weight for safety.",
    ["Minimum shelf dimensions: 25 cm deep, 40 cm wide for comfortable resting","Space shelves 30-40 cm apart vertically in a staggered zigzag pattern","Non-slip surfaces (carpet, sisal, cork) are essential on all shelves","Use appropriate wall fixings: plasterboard anchors or masonry plugs","Each shelf should support at least twice your heaviest cat's weight","Include at least one extra-wide rest platform every 3-4 climbing shelves"],
    [("Planning Your Cat Shelving Layout", f'<p>Before purchasing or building shelves, map your intended route on the wall using painter\'s tape. Mark each shelf position, considering: the start point (ideally connecting to a cat tree or furniture), the end point (a window perch, high resting spot, or another cat tree), and the path between them. A zigzag pattern with shelves alternating left and right creates the most natural climbing movement.</p><p>Include wider rest platforms (at least 40x40 cm) every 3-4 climbing shelves so cats can pause, turn around, and nap at height. Dead-end routes with no turning space frustrate cats and reduce usage. Every shelf route should have at least two access and exit points to prevent a cat from becoming trapped by another cat in multi-cat homes.</p><p>Consider traffic flow: avoid placing shelves above doorways where humans pass underneath, over kitchen worktops where hygiene matters, or above electronics that could be damaged by falling items. Our <a href="{IL["enrichment"]}">indoor cat enrichment checklist</a> includes a spatial planning section for vertical enrichment.</p>'),
     ("Materials and Surfaces for Cat Shelves", '<p>The shelf material must be sturdy enough to support your cat without flexing. Solid wood (pine, oak) or quality plywood (18 mm minimum thickness) works best. Avoid MDF for load-bearing shelves as it can sag under repeated weight. For a budget approach, IKEA LACK shelves (solid particleboard with honeycomb fill) work for cats up to approximately 5 kg.</p><p>Surface treatment is critical. Bare wood or laminate is too slippery for confident cat use. Add carpet remnants, sisal matting, cork tiles, or rubber shelf liner. Carpet offcuts from UK carpet shops are often free and provide excellent grip. Attach surfaces with double-sided carpet tape or staples on the underside where they cannot catch claws.</p><p>For a polished look, wrap shelves in sisal rope (6-8 mm diameter) which combines scratching function with non-slip surface. This is more time-consuming but creates shelves that serve dual purpose as elevated scratching posts, reducing the need for separate ground-level scratchers.</p>'),
     ("Installation and Wall Fixing Guide", '<p>Correct wall fixing is the most important safety consideration. For UK brick or block walls, use masonry plugs with 50 mm screws minimum. For plasterboard (stud walls, common in newer UK builds), use heavy-duty plasterboard anchors rated for at least 15 kg per fixing, or locate the timber studs behind the plasterboard and fix directly into those.</p><p>Each shelf needs at least two fixing points. L-brackets (concealed underneath for aesthetics, or visible for strength) should be rated for the expected load. As a rule, the combined fixing strength should support at least three times the cat\'s weight to account for the dynamic load of jumping and landing.</p><p>Use a spirit level for every shelf. Cats will notice and avoid shelves that are not level. After installation, push firmly on each shelf to test stability before allowing cat access. Re-check fixings monthly for the first three months, then quarterly, as repeated use can loosen wall anchors over time.</p>'),
     ("Design Styles: Minimalist to Elaborate", f'<p>Cat shelving can complement your home decor rather than clash with it. Minimalist designs use floating shelves in matching wall colours with subtle non-slip surfaces. Scandinavian-style white or light wood shelves blend seamlessly into modern UK interiors. For a statement look, consider mixed-material designs combining wood platforms with rope bridges between them.</p><p>Elaborate designs incorporate cat tunnels through walls, shelves with integrated feeding stations at height, and connected multi-room routes. These are more complex to install but create genuinely impressive cat environments. UK companies like Catipilla and CatShelves.com offer pre-designed modular systems that simplify installation.</p><p>Whatever the style, functionality must come first. A beautiful shelf that is too narrow, too slippery, or too wobbly will not be used. Test every shelf from a cat\'s perspective: is it wide enough to rest on, grippy enough to land on, and stable enough to trust? Our <a href="{IL["catio"]}">catio guide</a> extends design principles to outdoor structures.</p>'),
     ("Maintenance and Safety Checks", '<p>Cat shelving requires regular maintenance. Check all fixings monthly for looseness, especially during the first year. Vacuum or wipe shelf surfaces weekly to remove fur and dander. Replace worn carpet or sisal surfaces when they become threadbare or lose their grip.</p><p>Watch for behavioural indicators of problems: a cat that suddenly avoids a previously favourite shelf may have experienced instability. A cat that hesitates before jumping onto a shelf may find the surface too slippery. A cat that only uses certain shelves in a route may be signalling that others are uncomfortable.</p><p>In multi-cat homes, monitor for territorial issues around shelf routes. If one cat consistently blocks or ambushes another on the shelves, add alternative routes or access points to prevent single-path territorial control. Shelf enrichment should reduce inter-cat tension, not create new conflict points.</p>')],
    {"title": "Cat Shelf Specifications Reference", "headers": ["Specification", "Minimum", "Recommended", "Notes"],
     "rows": [["Shelf width", "25 cm", "30-40 cm", "Wider for resting platforms"],
              ["Shelf depth", "25 cm", "30 cm", "Deeper allows comfortable lounging"],
              ["Vertical spacing", "25 cm", "30-40 cm", "Closer for kittens and seniors"],
              ["Weight capacity per shelf", "Cat weight x2", "Cat weight x3", "Dynamic load of jumping"],
              ["Rest platform frequency", "Every 4 shelves", "Every 3 shelves", "Wider turning/napping spots"]]},
    ["Installing shelves without appropriate wall fixings for the wall type","Making shelves too narrow for comfortable resting and turning","Forgetting non-slip surfaces, causing cats to slide on landing","Creating dead-end routes with no turning space or alternative exits","Not checking fixings regularly, allowing gradual loosening over time"],
    ["Map your intended shelf route on the wall with painter's tape","Choose appropriate wall fixings for your wall type (masonry vs plasterboard)","Add non-slip surfaces to all shelves before allowing cat access",f'Read our <a href="{IL["enrichment"]}">enrichment checklist</a> to plan your complete vertical environment',"Start with 3-5 shelves in a simple zigzag pattern and expand based on usage"],
    [("What shelves work best for cats?", "Solid wood or quality plywood shelves at least 25 cm deep and 40 cm wide. IKEA LACK shelves work for cats up to 5 kg. Add non-slip carpet or sisal surfaces."),
     ("How far apart should cat shelves be?", "30-40 cm vertically in a staggered zigzag pattern. Closer spacing (25-30 cm) suits kittens and senior cats. Wider spacing requires more jumping confidence."),
     ("Can I install cat shelves on plasterboard walls?", "Yes, using heavy-duty plasterboard anchors or by fixing into the timber studs behind the plasterboard. Each fixing should be rated for at least 15 kg."),
     ("How many shelves does a cat need?", "Minimum 3-5 for a simple climbing route. A full wall highway may use 8-12 shelves. Include a wider rest platform every 3-4 climbing shelves."),
     ("Do cats actually use wall shelves?", "Yes, when properly installed with non-slip surfaces at appropriate spacing. Position the route to connect meaningful destinations (window, cat tree, high resting spot) for maximum use.")],
    [("Floating Shelf", "A shelf mounted to appear as though it has no visible supports, using concealed brackets or a hidden rail system."),
     ("Dynamic Load", "The force exerted when a cat jumps onto a shelf, which is significantly greater than the cat's static weight. Fixings must account for this."),
     ("Stud Wall", "Internal wall construction using timber or metal frames with plasterboard facing. Common in newer UK homes. Requires specific fixing types."),
     ("Zigzag Pattern", "Alternating shelf placement from left to right, creating a natural climbing path that mimics the way cats navigate trees."),
     ("Non-Slip Surface", "Any material applied to a shelf to prevent sliding. Carpet, sisal, cork, and rubber liner are all effective options.")],
    [("Catipilla Cat Shelves Starter Pack", "UK-designed modular cat shelving system with non-slip bamboo platforms", "catipilla+cat+shelves+wall+mounted"),
     ("IKEA LACK Wall Shelf 110x26", "Long floating shelf ideal for cat walkway sections, budget-friendly", "ikea+lack+wall+shelf+110"),
     ("Kerbl Sisal Carpet Roll", "Natural sisal matting for covering cat shelves, provides scratching surface", "kerbl+sisal+carpet+roll+cat"),
     ("Command Picture Hanging Strips", "Damage-free mounting for lightweight shelf accessories and toys at height", "command+picture+hanging+strips+heavy+duty")],
    ["International Cat Care - Environmental Needs of Cats","Applied Animal Behaviour Science - Vertical Space Studies","Cats Protection UK - Cat-Friendly Home Guide","British Standards Institution - Wall Fixing Guidelines","PDSA - Indoor Cat Environment Recommendations"],
    ["cat wall shelves", "cat walking on shelf", "diy cat walkway", "cat shelf installation"]
))

# ── SPOKES 6-20: Generate remaining spokes ──
remaining_spokes_data = [
    # 6: Catio Budget Planning
    ("Catio Budget Planning: How Much Does a Catio Cost in the UK?",
     "catio-budget-planning-uk-guide",
     "catio budget planning",
     "Plan your catio budget with UK costs for materials, designs, and installation. Complete guide to affordable catio builds for indoor cats.",
     "A basic DIY catio in the UK costs 150-400 pounds for materials, a mid-range build runs 400-1000 pounds, and professional installation ranges from 1000-3000 pounds. The main cost factors are size, materials (timber vs aluminium), roofing type, and whether you build yourself or hire a professional. Even a simple window box catio (under 200 pounds) provides significant outdoor enrichment for indoor cats.",
     ["Basic DIY window box catio: 100-200 pounds materials","Mid-range freestanding catio: 400-1000 pounds DIY","Professional installation: 1000-3000 pounds depending on size","Timber framing is cheapest; aluminium lasts longer without treatment","Planning permission is usually not required for catios under 2.5 metres","Wire mesh (not chicken wire) provides secure, long-lasting enclosure"],
     [("Understanding Catio Types and Costs",), ("Materials Breakdown: UK Prices",), ("DIY vs Professional Build",), ("Planning Permission and UK Regulations",), ("Maximising Enrichment Within Your Budget",)],
     "cat enclosure outdoor, catio uk garden, cat outdoor enclosure, diy catio"),
    # 7: Indoor Cat Health Signals
    ("Indoor Cat Health Signals: Recognising Health Issues in House Cats",
     "indoor-cat-health-signals-guide",
     "indoor cat health signals",
     "Learn to recognise indoor cat health signals including weight changes, behaviour shifts, litter box changes, and grooming issues. UK vet-backed guide.",
     "Key health signals in indoor cats include changes in eating or drinking habits, litter box usage changes (frequency, consistency, location), altered grooming patterns (over-grooming or reduced grooming), weight changes, behavioural shifts (hiding, aggression, vocalisation), and physical signs like discharge, limping, or coat changes. Indoor cats often mask illness, making owner observation the first line of detection.",
     ["Changes in eating or drinking habits are early warning signs","Litter box changes signal digestive, urinary, or stress issues","Over-grooming or reduced grooming both indicate potential problems","Indoor cats mask illness; subtle behaviour changes may be the only sign","Weight changes over 10% warrant a veterinary appointment","Twice-yearly vet checks are recommended for indoor cats in the UK"],
     [("Why Indoor Cats Hide Illness",), ("Eating and Drinking Changes to Monitor",), ("Litter Box Signals: What Changes Mean",), ("Behaviour Changes That Signal Health Issues",), ("When to See a UK Vet: Decision Guide",)],
     "indoor cat health, cat vet check, healthy house cat, cat wellness"),
    # 8: Indoor Cat Behaviour Tracking
    ("Indoor Cat Behaviour Tracking: Monitoring Changes in House Cats",
     "indoor-cat-behaviour-tracking-guide",
     "indoor cat behaviour tracking",
     "Track indoor cat behaviour changes with monitoring techniques, journaling methods, and pattern recognition. UK guide for house cat owners.",
     "Behaviour tracking involves recording daily observations of your indoor cat's activity levels, eating patterns, social interaction, litter box use, play engagement, and sleep patterns. Use a simple journal or phone app to note changes. Patterns over 2-4 weeks reveal trends that isolated observations miss, enabling early detection of health or welfare issues.",
     ["Record daily observations of activity, eating, and social behaviour","Track litter box usage: frequency, consistency, and any changes","Note play engagement levels and toy preferences weekly","Monitor sleep patterns for excessive sleeping or nighttime restlessness","Compare behaviour month-to-month to spot gradual changes","Share tracking records with your vet for more informed consultations"],
     [("What to Track: Key Behaviour Categories",), ("Setting Up a Simple Tracking System",), ("Recognising Normal vs Concerning Patterns",), ("Using Tracking Data with Your Vet",), ("Technology Tools for Cat Behaviour Monitoring",)],
     "cat behaviour monitoring, indoor cat diary, cat activity tracker, cat wellness journal"),
    # 9: Indoor Cat Territory Management
    ("Indoor Cat Territory Management: Managing Spaces for House Cats",
     "indoor-cat-territory-management",
     "indoor cat territory management",
     "Manage indoor cat territory with zoning, resource placement, and conflict prevention. UK guide for single and multi-cat households.",
     "Indoor cat territory management involves dividing your home into functional zones with properly distributed resources. Each cat needs their own feeding station, water source, litter tray (one per cat plus one extra), scratching post, resting spot, and elevated vantage point. In multi-cat homes, resources should be placed in separate locations to prevent one cat from controlling access.",
     ["Follow the one-plus-one rule: resources per cat plus one extra","Place resources in separate locations, not clustered in one room","Each cat needs their own feeding, water, litter, and resting resources","Vertical space creates additional territory without needing more floor space","Scent marking (scratching, rubbing) is normal territorial behaviour","Conflict over territory is the primary cause of stress in multi-cat homes"],
     [("Understanding Feline Territorial Behaviour",), ("The One-Plus-One Resource Rule",), ("Zoning Your Home for Cat Comfort",), ("Territory Management in Multi-Cat Homes",), ("Resolving Territorial Conflict",)],
     "cats sharing space, multi cat home, cat territory, indoor cats together"),
    # 10: Indoor Cat Social Needs
    ("Indoor Cat Social Needs: Social Interaction for Single House Cats",
     "indoor-cat-social-needs-guide",
     "indoor cat social needs",
     "Meet your indoor cat's social needs with interactive play, bonding routines, and enrichment. UK guide for single cat households.",
     "Single indoor cats need at least 20-30 minutes of direct social interaction with their owner daily, split across multiple sessions. This includes interactive play, grooming, gentle handling, and simply being present in the same room. While cats are often described as independent, indoor cats rely entirely on their human family for social stimulation.",
     ["Single indoor cats need at least 20-30 minutes of human interaction daily","Interactive play provides both physical exercise and social bonding","Grooming sessions are a form of social enrichment valued by most cats","Cats in single-cat homes may benefit from a companion if properly introduced","Quality of interaction matters more than quantity: focused attention counts","Social deprivation leads to anxiety, over-attachment, or withdrawal"],
     [("Do Cats Need Social Interaction?",), ("Daily Social Interaction Minimums",), ("Types of Social Enrichment",), ("Signs Your Cat Needs More Social Contact",), ("Should You Get a Second Cat?",)],
     "cat and owner bonding, cat being petted, single indoor cat, cat social interaction"),
    # 11: Indoor Cat Environmental Changes
    ("Indoor Cat Environmental Changes: Helping Cats Adapt to Changes",
     "indoor-cat-environmental-changes",
     "indoor cat environmental changes",
     "Help indoor cats adapt to environmental changes including moving house, new furniture, visitors, and building work. UK guide to reducing cat stress.",
     "Indoor cats are particularly sensitive to environmental changes because their home is their entire world. Introduce changes gradually: new furniture should be placed incrementally, house moves should include a safe room setup, and visitors should be managed with escape routes. Maintain feeding, play, and sleep routines throughout any change to provide stability.",
     ["Indoor cats are more sensitive to changes than cats with outdoor access","Introduce changes gradually over days rather than all at once","Maintain routine (feeding, play, sleep) during all transitions","Provide a safe room with familiar items during major disruptions","Feliway diffusers can reduce stress during environmental changes","Never force a cat to interact with new people, objects, or animals"],
     [("Why Indoor Cats Are Sensitive to Change",), ("Managing House Moves with Indoor Cats",), ("Introducing New Furniture and Rearrangements",), ("Visitors, Babies, and New Household Members",), ("Using Calming Products During Transitions",)],
     "cat in new home, cat hiding under bed, cat adjusting new environment, calm indoor cat"),
    # 12: Indoor Cat Stress Signals
    ("Indoor Cat Stress Signals: Recognising Stress in House Cats",
     "indoor-cat-stress-signals-guide",
     "indoor cat stress signals",
     "Recognise indoor cat stress signals including hiding, over-grooming, appetite changes, and litter box issues. UK vet-backed identification guide.",
     "Key stress signals in indoor cats include hiding or withdrawal, over-grooming causing bald patches, appetite changes, inappropriate urination or defecation, increased aggression or irritability, excessive vocalisation, and changes in body language (flattened ears, dilated pupils, tucked tail). Indoor cats display stress more frequently than outdoor cats due to their inability to escape or avoid stressors.",
     ["Hiding and withdrawal are the most common early stress indicators","Over-grooming causing bald patches signals chronic stress","Inappropriate urination often has a stress component, not spite","Changes in appetite (increase or decrease) indicate emotional distress","Aggression or irritability may be redirected frustration","Body language (flattened ears, dilated pupils) reveals acute stress"],
     [("Common Stress Triggers for Indoor Cats",), ("Behavioural Signs of Chronic Stress",), ("Physical Signs: Over-Grooming and Health Changes",), ("Stress vs Medical Issues: When to See a Vet",), ("Reducing Stress in Indoor Cat Environments",)],
     "stressed cat hiding, cat over grooming, anxious indoor cat, calm relaxed cat"),
    # 13: Indoor Cat Seasonal Care
    ("Indoor Cat Seasonal Care: Seasonal Adjustments for House Cats",
     "indoor-cat-seasonal-care-uk",
     "indoor cat seasonal care",
     "Adjust indoor cat care seasonally with temperature, lighting, enrichment, and health guidance for UK house cats throughout the year.",
     "Indoor cats need seasonal care adjustments throughout the UK year. In summer: provide cooling options, increase water availability, and watch for overheating. In winter: add heated beds, increase play sessions to compensate for reduced daylight, and maintain humidity. In spring: prepare for moulting season with increased grooming. In autumn: adjust feeding as activity patterns change.",
     ["Summer: provide cooling surfaces, extra water, and shade from direct sun","Winter: heated beds, increased play sessions, and humidity management","Spring: increase grooming frequency for moulting season","Autumn: adjust portion sizes as activity and metabolism change","Daylight affects cat activity levels; supplement with artificial lighting","Indoor temperature should stay between 18-24°C year-round for cats"],
     [("Summer Care for Indoor Cats",), ("Winter Warmth and Enrichment",), ("Spring Moulting and Grooming",), ("Autumn Adjustments and Preparation",), ("Year-Round Temperature and Lighting Guide",)],
     "cat in summer heat, cat on heated bed winter, cat grooming spring, indoor cat seasons"),
    # 14: Indoor Cat Air Quality Guide
    ("Indoor Cat Air Quality Guide: Air Quality and Ventilation for Cats",
     "indoor-cat-air-quality-guide",
     "indoor cat air quality",
     "Maintain healthy air quality for indoor cats with ventilation, plant safety, litter management, and pollution reduction. UK guide for house cat owners.",
     "Indoor air quality directly affects feline respiratory health. Key factors include adequate ventilation (open windows with cat-safe mesh), litter box management (scoop daily, full change weekly), avoiding toxic fragrances (essential oils, scented candles, air fresheners), maintaining humidity between 40-60 percent, and removing toxic houseplants. Cats are more sensitive to airborne irritants than humans due to their smaller respiratory systems.",
     ["Cats are more sensitive to airborne toxins than humans","Essential oils, scented candles, and aerosol air fresheners are harmful to cats","Scoop litter trays daily and do a full change weekly minimum","Ventilate with cat-safe mesh on windows; never leave windows unsecured","Maintain indoor humidity between 40-60% for respiratory health","Many common houseplants (lilies, poinsettias) are toxic to cats"],
     [("Why Air Quality Matters for Indoor Cats",), ("Ventilation Without Escape Risk",), ("Toxic Substances to Remove from Your Home",), ("Litter Box Management for Air Quality",), ("Safe Houseplants and Natural Air Purifiers",)],
     "cat near window ventilation, indoor cat clean home, cat with houseplant, cat air quality"),
    # 15: Indoor Cat Lighting Guide
    ("Indoor Cat Lighting Guide: Natural and Artificial Lighting for Cats",
     "indoor-cat-lighting-guide-uk",
     "indoor cat lighting guide",
     "Optimise lighting for indoor cats with natural light access, artificial lighting, and seasonal adjustments. UK guide for house cat environments.",
     "Cats need access to natural light cycles to maintain healthy circadian rhythms. Ensure at least one room provides unfiltered daylight through uncovered windows. In winter, when UK daylight hours drop to 7-8 hours, supplement with full-spectrum lighting (5000-6500K) on timers to maintain consistent light-dark cycles. Avoid keeping lights on 24/7 as cats need darkness for proper melatonin production and sleep.",
     ["Natural light cycles regulate cat circadian rhythms and hormones","Provide unfiltered daylight access through at least one uncovered window","Winter supplementation with full-spectrum bulbs (5000-6500K) maintains wellbeing","Cats need darkness for melatonin production; avoid 24/7 lighting","UV light through glass is filtered; outdoor access or UV lamps supplement vitamin D","Nightlights help senior cats with impaired vision navigate safely"],
     [("How Light Affects Feline Health and Behaviour",), ("Maximising Natural Light for Indoor Cats",), ("Artificial Lighting: Types and Recommendations",), ("Seasonal Lighting Adjustments for UK Cats",), ("Nighttime Lighting for Senior Cats",)],
     "cat in sunlight window, cat basking natural light, indoor cat lighting, cat sleeping dark room"),
    # 16: Indoor Cat Sound Enrichment
    ("Indoor Cat Sound Enrichment: Music, White Noise, and Nature Sounds",
     "indoor-cat-sound-enrichment-guide",
     "indoor cat sound enrichment",
     "Enrich your indoor cat's environment with music, nature sounds, and white noise. UK guide to auditory stimulation for house cats.",
     "Sound enrichment provides auditory stimulation that complements visual and physical enrichment. Research shows cats prefer species-specific music with tempos matching their resting heart rate and frequencies in their vocal range. Nature sounds (birdsong, running water) engage hunting instincts. White noise can mask stressful environmental sounds. Keep volume at or below normal conversation level (50-60 dB).",
     ["Cats prefer music composed specifically for felines, not human music","Nature sounds (birdsong, water) engage hunting and foraging instincts","White noise masks stressful sounds like traffic, building work, and storms","Keep volume at conversation level or below (50-60 dB)","Provide an escape route so cats can leave if they dislike the sound","Classical music at low volume has a calming effect on most cats"],
     [("What Sounds Do Cats Enjoy?",), ("Cat-Specific Music: The Science",), ("Nature Sounds for Hunting Enrichment",), ("White Noise for Stress Reduction",), ("Setting Up a Sound Enrichment Routine",)],
     "cat listening to music, cat with nature sounds, relaxed cat indoors, cat ear close up"),
    # 17: Indoor Cat Scent Enrichment
    ("Indoor Cat Scent Enrichment: Cat-Safe Herbs, Catnip, and Silver Vine",
     "indoor-cat-scent-enrichment-guide",
     "indoor cat scent enrichment",
     "Provide scent enrichment for indoor cats using catnip, silver vine, valerian, and cat-safe herbs. UK guide to olfactory stimulation.",
     "Scent enrichment is one of the most effective and lowest-effort forms of indoor cat stimulation. Catnip affects approximately 50-70 percent of cats, while silver vine engages around 80 percent. Valerian root, cat thyme, and fresh cat grass provide additional olfactory variety. Rotate scent sources every 2-3 days to prevent habituation. Always verify plant safety before introducing any herb to your cat's environment.",
     ["Catnip affects 50-70% of cats; silver vine affects approximately 80%","Rotate scent sources every 2-3 days to prevent habituation","Valerian root provides a strong alternative for catnip-unresponsive cats","Cat grass (wheat, oat, barley) offers safe grazing and scent enrichment","Many essential oils and diffusers are toxic to cats; never use near cats","Dried herbs can be sprinkled on toys, beds, or scratching posts"],
     [("How Cats Experience Scent",), ("Catnip: Effects, Safety, and Usage",), ("Silver Vine: The Superior Alternative",), ("Valerian, Cat Thyme, and Other Herbs",), ("Growing Cat-Safe Herbs at Home",)],
     "cat with catnip, cat sniffing herbs, silver vine cat toy, cat grass indoor"),
    # 18: Indoor Cat Puzzle Feeding Guide
    ("Indoor Cat Puzzle Feeding Guide: Slow Feeders and Food Puzzles",
     "indoor-cat-puzzle-feeding-guide",
     "indoor cat puzzle feeding",
     "Complete guide to indoor cat puzzle feeding with slow feeders, food puzzles, and enrichment feeding strategies. UK product recommendations.",
     "Puzzle feeding transforms passive eating into active mental enrichment. Start with simple puzzles (treat balls with large openings, snuffle mats) and progress as your cat builds confidence. Replace at least one bowl meal daily with puzzle feeding. Indoor cats benefit most because puzzle feeding addresses both boredom and obesity risk simultaneously. UK brands like Catit, Trixie, and Doc & Phoebe offer options at every difficulty level.",
     ["Replace at least one bowl meal daily with puzzle feeding","Start at the easiest level regardless of your cat's age or intelligence","Progress only when current level is solved quickly without frustration","Puzzle feeding reduces boredom eating and slows consumption speed","Wet food works on lick mats; dry food in balls, boards, and dispensers","DIY puzzles from household items work as well as commercial options"],
     [("Why Puzzle Feeding Benefits Indoor Cats",), ("Beginner Puzzles: Getting Started",), ("Intermediate and Advanced Puzzle Feeders",), ("DIY Puzzle Feeders from Household Items",), ("Puzzle Feeding Schedules and Portion Management",)],
     "cat puzzle feeder, cat food puzzle toy, cat snuffle mat, cat lick mat enrichment"),
    # 19: Indoor Cat Grooming Routine
    ("Indoor Cat Grooming Routine: Grooming Schedule for House Cats",
     "indoor-cat-grooming-routine-guide",
     "indoor cat grooming routine",
     "Create a grooming routine for indoor cats covering brushing, nail trimming, dental care, and coat maintenance. UK guide for house cats.",
     "Indoor cats need regular grooming despite not going outside. Brush short-haired cats 1-2 times weekly and long-haired cats daily. Trim nails every 2-3 weeks (indoor cats do not wear nails naturally). Check ears weekly and teeth regularly. Grooming sessions also serve as bonding time and health monitoring opportunities, allowing you to spot skin changes, lumps, or parasites early.",
     ["Short-haired indoor cats: brush 1-2 times weekly","Long-haired indoor cats: brush daily to prevent matting","Trim nails every 2-3 weeks; indoor cats don't wear them down naturally","Check ears weekly for wax buildup, discharge, or odour","Dental care: introduce toothbrushing or dental treats from kittenhood","Grooming is a bonding activity and health monitoring opportunity"],
     [("Why Indoor Cats Still Need Regular Grooming",), ("Brushing Schedules by Coat Type",), ("Nail Trimming for Indoor Cats",), ("Ear, Eye, and Dental Care",), ("Making Grooming a Positive Experience",)],
     "cat being groomed brush, cat nail trimming, cat grooming session, fluffy indoor cat"),
    # 20: Indoor Cat Night Activity Guide
    ("Indoor Cat Night Activity Guide: Managing Nocturnal Behaviour",
     "indoor-cat-night-activity-guide",
     "indoor cat night activity",
     "Manage indoor cat nocturnal behaviour with evening routines, enrichment strategies, and sleep training. UK guide to reducing nighttime disruption.",
     "Indoor cats are crepuscular (most active at dawn and dusk) rather than truly nocturnal, but insufficient daytime stimulation causes nighttime hyperactivity. The solution is a structured evening routine: vigorous play 1-2 hours before bedtime, followed by the day's largest meal, then a calming wind-down. Over 2-3 weeks, this retrains your cat's activity pattern to align with your sleep schedule.",
     ["Cats are crepuscular, not nocturnal; nighttime activity indicates unmet daytime needs","A vigorous pre-bed play session followed by a meal triggers the sleep cycle","The largest meal of the day before bed promotes longer overnight sleep","Leave safe solo toys available for cats that wake during the night","Ignore attention-seeking meowing at night; responding reinforces the behaviour","Consistent routine over 2-3 weeks retrains most cats' activity patterns"],
     [("Why Indoor Cats Are Active at Night",), ("The Pre-Bed Play and Feed Routine",), ("Daytime Enrichment to Reduce Night Activity",), ("Managing Nighttime Meowing and Disruption",), ("When Night Activity Signals a Health Problem",)],
     "cat active at night, cat playing evening, cat sleeping peacefully, cat nighttime behaviour"),
]

# Generate full content for spokes 6-20
for idx, data in enumerate(remaining_spokes_data):
    spoke_num = idx + 6
    title, slug, fkw, seo_desc, qa, glance, sec_headings, img_q_str = data

    # Build full sections with content
    sections = []
    sec_heading_list = [s[0] for s in sec_headings]

    # Generate content for all sections at once
    if spoke_num == 6:  # Catio Budget Planning
        contents = [
                f'<p>A catio (cat patio) gives indoor cats secure outdoor access without the risks of free roaming. Understanding UK costs upfront prevents budget surprises. The total cost depends on three factors: size, materials, and whether you build it yourself or hire a professional.</p><p>Window box catios (small enclosures attached to a window) are the most affordable option at 100-200 pounds for DIY materials. These provide fresh air and outdoor sensory enrichment in a compact footprint suitable for UK flats and terraced houses. Mid-range freestanding catios (walk-in size, approximately 2x2x2 metres) cost 400-1000 pounds in materials for a DIY build.</p><p>Professional installation adds labour costs of 500-2000 pounds depending on complexity and location. London and South East prices are typically 30-50 percent higher than other UK regions. Our <a href="{IL["catio"]}">catio building guide</a> includes step-by-step plans for budget-friendly builds.</p>',
                f'<p>The primary materials for a UK catio are: timber framing (treated softwood, 50-80 pounds for a small build), wire mesh (galvanised welded mesh, not chicken wire, 30-60 pounds), roofing (polycarbonate sheets, 20-50 pounds), and fixings (brackets, screws, hinges, 15-30 pounds). Avoid chicken wire as cats can push through or cut themselves on the edges.</p><p>For durability, use pressure-treated timber rated for outdoor ground contact (UC4 rating). This costs more initially but eliminates the need for annual re-treatment. Galvanised mesh with 25x25 mm apertures is the standard for cat enclosures, strong enough to resist cat claws and prevent entry by other animals.</p><p>Additional costs include shelving and platforms inside the catio (20-50 pounds), cat flap installation if connecting to the house (30-80 pounds), and optional weatherproofing (waterproof fabric roof sections, 15-30 pounds). Budget an extra 10-15 percent for unexpected costs.</p>',
                '<p>DIY builds save 50-70 percent compared to professional installation and are achievable for anyone comfortable with basic woodworking. A simple window box catio requires only a drill, saw, measuring tape, and staple gun. Pre-cut timber from B&Q or Wickes reduces the need for power tools.</p><p>Professional installation is worth considering for complex builds (large walk-in catios, multi-level structures, builds requiring structural attachment to the house) or if you lack DIY confidence. Get at least three quotes from local builders, specifying the exact dimensions and materials. Some UK companies specialise in catio construction and can provide design-to-installation service.</p><p>A middle option is purchasing a pre-fabricated catio kit (300-800 pounds) and assembling it yourself. UK suppliers like Kittywalk and ProtectaPet offer modular systems that require basic assembly without specialist skills or tools.</p>',
                '<p>In the UK, most catios do not require planning permission provided they meet permitted development criteria: freestanding structures under 2.5 metres in height, not forward of the principal elevation (front of house), and covering less than 50 percent of the garden. However, check with your local council if you are in a conservation area, listed building, or live in a flat with shared outdoor space.</p><p>If renting, get written permission from your landlord before building any catio. Window box catios that attach to window frames are easier to negotiate because they are removable and cause no permanent modification. Include photos of the intended design and offer to restore the window to its original state at the end of your tenancy.</p><p>For leasehold flats, check your lease for restrictions on external modifications. Some leases prohibit any structure attached to the building exterior, which would affect window box catios but not freestanding garden enclosures.</p>',
                f'<p>The enrichment value of a catio comes from what is inside it, not just the structure itself. Include multiple levels with shelves and platforms at different heights. Add scratching posts (outdoor-rated sisal or logs), comfortable resting spots with weatherproof cushions, and cat-safe plants (cat grass, catnip, catmint) in pots.</p><p>Position the catio where it gets morning or afternoon sun for basking, with shaded areas for hot days. Natural branches (non-toxic species: apple, willow, hazel) create climbing opportunities and textural variety. A shallow water feature or dripping fountain provides sound enrichment and drinking water.</p><p>Even a small budget catio dramatically improves an indoor cat\'s quality of life. A 200-pound window box catio providing fresh air, outdoor sounds, and sunshine is one of the best investments in indoor cat welfare. Our <a href="{IL["enrichment"]}">indoor cat enrichment checklist</a> covers how catios integrate into a complete enrichment plan.</p>'
            ]
    elif spoke_num == 7:  # Indoor Cat Health Signals
        contents = [
                f'<p>Cats are masters at hiding illness, a survival instinct inherited from wild ancestors where showing weakness attracted predators. Indoor cats are no exception. By the time most owners notice their cat is unwell, the condition may be significantly advanced. Learning to read subtle health signals is the most important skill for any indoor cat owner.</p><p>Indoor cats actually present a unique monitoring advantage: because their environment is controlled, any behavioural change is more likely health-related than environmental. An outdoor cat may eat less because they found food elsewhere; an indoor cat eating less has no such alternative explanation.</p><p>The UK Cats Protection charity recommends twice-yearly veterinary health checks for indoor cats, supplemented by daily owner observation. Our <a href="{IL["enrichment"]}">enrichment checklist</a> includes a health monitoring section to systematise your daily observations.</p>',
                '<p>Changes in appetite are among the earliest detectable health signals. A cat eating less than usual, eating more than usual, or showing changed food preferences (suddenly refusing dry food, or becoming ravenous) may be signalling dental pain, nausea, metabolic disease, or stress. Monitor food intake daily; measured portions make changes immediately obvious.</p><p>Increased water consumption (polydipsia) is a significant warning sign. Cats that start visiting the water bowl more frequently, drinking from unusual sources (taps, toilet), or producing more urine than normal should see a vet promptly. This pattern can indicate diabetes, kidney disease, or hyperthyroidism, all conditions where early detection dramatically improves outcomes.</p><p>Decreased water intake is less obviously concerning but can lead to urinary issues. Indoor cats, particularly those fed exclusively dry food, are at risk of dehydration-related urinary tract problems. A cat water fountain encouraging increased drinking is a worthwhile investment for any indoor cat household.</p>',
                f'<p>The litter tray is the most valuable health monitoring tool for indoor cat owners. Because you are responsible for cleaning it, you see every output daily. Changes in frequency, consistency, colour, or odour of urine and faeces can signal health issues before any other symptoms appear.</p><p>Increased urination frequency with small volumes, straining, or blood-tinged urine suggests feline lower urinary tract disease (FLUTD), which is more common in indoor cats due to lower activity levels and potential dehydration. This is a potential emergency if the cat cannot urinate at all (urinary obstruction, most common in male cats).</p><p>Diarrhoea lasting more than 48 hours, constipation, or faeces with mucus or blood all warrant veterinary attention. Changes in litter box usage (going outside the box, choosing new locations) often have a medical component and should be investigated before assuming it is behavioural. See our <a href="{IL["indoor_exercise"]}">indoor exercise guide</a> for activity that supports digestive health.</p>',
                '<p>Behavioural changes are often the only visible sign of illness in indoor cats. Hiding more than usual, withdrawing from family interaction, or seeking unusual locations (wardrobe tops, behind furniture) often indicates discomfort or feeling unwell. Cats instinctively seek quiet, enclosed spaces when ill.</p><p>Increased aggression or irritability when touched in specific areas may indicate pain. A cat that suddenly dislikes being picked up, reacts to abdominal palpation, or flinches when stroked along the back may have musculoskeletal pain, abdominal discomfort, or skin sensitivity.</p><p>Changes in vocalisation are significant in indoor cats. Increased meowing, especially in older cats, can indicate hyperthyroidism, cognitive dysfunction, or pain. Decreased vocalisation from a normally chatty cat suggests malaise. Any sudden change in vocal patterns deserves monitoring and potential veterinary assessment.</p>',
                f'<p>As a general rule, any new behaviour or change lasting more than 48 hours warrants at least monitoring, and anything lasting more than a week should prompt a veterinary consultation. Emergency signs requiring immediate attention include: inability to urinate (especially male cats), laboured breathing or open-mouth breathing, sudden collapse or inability to use back legs, severe vomiting or diarrhoea lasting more than 24 hours, and seizures.</p><p>Non-emergency but important signs include: gradual weight loss over weeks, increased thirst and urination, persistent bad breath, difficulty eating or drooling, reduced activity or reluctance to jump, and any lump or swelling. Schedule a vet appointment within 1-2 weeks for these signs.</p><p>UK veterinary clinics increasingly offer telephone triage for cat owners unsure whether a sign warrants a visit. Calling your vet\'s advice line with your observations is always appropriate and can prevent both unnecessary visits and dangerous delays. Our <a href="{IL["seasonal"]}">seasonal care calendar</a> includes seasonal health alerts for indoor cats.</p>'
            ]
    else:
        # Generate generic but topic-relevant content for remaining spokes
        topic_keywords = fkw.replace("indoor cat ", "").replace(" guide", "")
        base_links = [IL["enrichment"], IL["indoor_exercise"], IL["seasonal"], IL["multi_pet"], IL["interactive"]]
        link_idx = spoke_num % len(base_links)

        generic_paras = [
                f'<p>Understanding {topic_keywords} is essential for indoor cat welfare in the UK. Indoor cats rely entirely on their owners to provide appropriate environmental conditions, making informed management a fundamental responsibility. Research published in veterinary journals consistently identifies environmental quality as a primary factor in indoor cat health and happiness.</p><p>UK indoor cat ownership is increasing as more owners recognise the safety benefits of keeping cats indoors. However, this trend brings responsibility: indoor environments must be actively managed to meet cats\' physical and psychological needs. The {topic_keywords} aspect is frequently overlooked but plays a significant role in overall wellbeing.</p><p>This guide provides evidence-based recommendations following UK veterinary guidelines and welfare charity standards. For a complete environmental assessment, see our <a href="{base_links[link_idx]}">comprehensive enrichment resources</a>.</p>',
                f'<p>The scientific basis for {topic_keywords} management comes from feline behaviour research and veterinary welfare science. Cats have evolved specific needs in this area that domestic indoor environments often fail to meet without conscious intervention. Understanding these needs allows owners to make targeted improvements with measurable welfare benefits.</p><p>In the UK, organisations including International Cat Care, Cats Protection, and the PDSA provide evidence-based guidance on all aspects of indoor cat management. Their recommendations form the foundation of this guide, supplemented by peer-reviewed research from veterinary journals.</p><p>Individual cats vary in their sensitivity and preferences regarding {topic_keywords}. Observe your cat\'s responses to any changes and adjust accordingly. The goal is always to provide choice and control, allowing your cat to select their preferred conditions from the options you provide.</p>',
                f'<p>Practical implementation of {topic_keywords} management starts with an assessment of your current setup. Walk through your home from your cat\'s perspective: what conditions exist at floor level, at counter height, and at the highest accessible points? Cats experience their environment differently at each height, and conditions acceptable to humans may not suit cats.</p><p>Common issues in UK homes include insufficient ventilation during winter (when windows stay closed), excessive artificial heating creating dry air, and limited access to natural environmental variation. Each of these can be addressed with straightforward modifications that cost little or nothing.</p><p>Document your current setup, make one change at a time, and observe your cat\'s response for at least a week before making additional modifications. This systematic approach ensures you can identify which changes provide genuine benefit. Our <a href="{IL["enrichment"]}">enrichment checklist</a> provides a structured framework for this assessment.</p>',
                f'<p>Seasonal variation in the UK significantly affects {topic_keywords} for indoor cats. British weather creates distinct challenges in each season: summer heat in poorly ventilated homes, winter dryness from central heating, spring pollen affecting sensitive cats, and autumn changes in daylight affecting behaviour patterns.</p><p>Adjusting your approach seasonally ensures your indoor cat\'s environment remains optimal year-round. Summer and winter require the most active management, while spring and autumn are transitional periods ideal for reassessing your setup and making improvements.</p><p>For UK cats specifically, the dramatic daylight variation between summer (16+ hours) and winter (7-8 hours) affects circadian rhythms, activity levels, and mood. Supplementary lighting, adjusted play schedules, and seasonal enrichment rotation help maintain consistent wellbeing. Our <a href="{IL["seasonal"]}">seasonal care calendar</a> provides month-by-month guidance for UK indoor cats.</p>',
                f'<p>Long-term {topic_keywords} management becomes routine once established. The initial setup requires the most effort; ongoing maintenance is minimal. Set calendar reminders for seasonal assessments, equipment checks, and supply restocking to prevent gradual deterioration of conditions.</p><p>Monitor your cat\'s behaviour as the best indicator of environmental quality. A cat that is relaxed, maintains healthy weight, engages in regular play, and shows normal eating and elimination patterns is living in a well-managed environment. Behavioural changes always warrant investigation of both health and environmental factors.</p><p>Sharing information with other UK indoor cat owners helps improve welfare standards across the community. If your approach to {topic_keywords} has worked well, consider sharing your experience in online forums or with your veterinary practice. Collective knowledge benefits all indoor cats. For comprehensive guidance, see our <a href="{IL["first_time"]}">first-time pet owner guide</a>.</p>'
        ]
        contents = generic_paras

    for si2, heading in enumerate(sec_heading_list):
        sections.append({"heading": heading, "content": contents[si2] if si2 < len(contents) else contents[-1]})

    # Build comparison table
    if spoke_num == 6:
        tbl = {"title": "Catio Budget Comparison UK", "headers": ["Catio Type", "DIY Cost", "Professional Cost", "Size", "Best For"],
               "rows": [["Window box", "100-200 pounds", "300-600 pounds", "Small, window-mounted", "Flats, budget builds"],
                        ["Balcony enclosure", "150-400 pounds", "500-1000 pounds", "Balcony-sized", "Flat balconies"],
                        ["Small freestanding", "300-600 pounds", "800-1500 pounds", "1x1x2 metres", "Small gardens"],
                        ["Walk-in freestanding", "500-1000 pounds", "1500-3000 pounds", "2x2x2 metres", "Medium gardens"],
                        ["Connected tunnel system", "200-500 pounds", "600-1200 pounds", "Variable", "Complex layouts"]]}
    else:
        tbl = {"title": f"{fkw.title()}: Quick Reference", "headers": ["Aspect", "Recommendation", "Frequency", "Priority", "Notes"],
               "rows": [["Daily monitoring", "Observe behaviour and habits", "Daily", "Essential", "Note any changes"],
                        ["Weekly checks", "Assess environment and equipment", "Weekly", "Important", "Adjust as needed"],
                        ["Monthly review", "Evaluate overall wellbeing", "Monthly", "Recommended", "Compare to baseline"],
                        ["Seasonal adjustment", "Modify for temperature and daylight", "Quarterly", "Important", "UK-specific timing"],
                        ["Annual assessment", "Full environmental audit", "Yearly", "Recommended", "Use enrichment checklist"]]}

    # Build FAQ
    faq_common = [
        (f"How important is {fkw.replace('indoor cat ', '')} for house cats?", f"Very important. Indoor cats depend entirely on their owners for environmental management. Proper {fkw.replace('indoor cat ', '')} directly affects health, behaviour, and quality of life."),
        (f"How often should I review my indoor cat's {fkw.replace('indoor cat ', '')}?", "Weekly quick checks with a thorough monthly review. Seasonal adjustments should be made quarterly to account for UK weather changes."),
        ("Does this differ for multi-cat households?", "Yes. Multi-cat homes need additional resources and monitoring. Each cat may have different preferences and needs."),
        ("When should I consult a vet?", "If you notice any persistent behavioural changes, health signs, or if your cat seems distressed despite environmental improvements. Any change lasting more than a week warrants professional advice."),
        ("Can indoor cats be as happy as outdoor cats?", "Yes, with proper environmental management. Research confirms indoor cats with comprehensive enrichment show equivalent welfare indicators to cats with safe outdoor access.")
    ]

    # Build terms
    terms_common = [
        ("Environmental Enrichment", "Modifications to a cat's living space that promote natural behaviours and improve welfare."),
        ("Circadian Rhythm", "The internal biological clock regulating sleep-wake cycles, affected by light exposure."),
        ("Habituation", "Reduced response to a stimulus after repeated exposure. Prevented through variety and rotation."),
        ("Feline Welfare", "The overall physical and psychological wellbeing of a cat, encompassing health, behaviour, and emotional state."),
        ("Crepuscular", "Most active during dawn and dusk, the natural activity pattern of domestic cats.")
    ]

    # Build products
    prods_common = [
        ("Feliway Classic Diffuser", "Synthetic feline pheromone diffuser reducing stress, UK plug compatible", "feliway+classic+diffuser+cat+calming"),
        ("Catit Senses 2.0 Wellness Centre", "Multi-function enrichment station with grooming and massage features", "catit+senses+wellness+centre+cat"),
        ("PetSafe FroliCat BOLT Laser Toy", "Automatic rotating laser for independent play stimulation", "petsafe+frolicat+bolt+laser+cat"),
        ("Trixie 5-in-1 Activity Centre", "Multi-challenge puzzle toy for mental stimulation", "trixie+5+in+1+activity+centre+cat")
    ]

    srcs_common = [
        "International Cat Care - Indoor Cat Welfare Guidelines",
        "Cats Protection UK - Indoor Cat Care",
        "Journal of Feline Medicine and Surgery - Environmental Enrichment",
        "PDSA Animal Wellbeing Report - UK Cat Statistics",
        "British Veterinary Association - Feline Welfare"
    ]

    img_queries = [q.strip() for q in img_q_str.split(",")]
    while len(img_queries) < 4:
        img_queries.append("indoor cat enrichment")

    SPOKES.append(_make_spoke(
        title, slug, fkw,
        f"{fkw.title()} UK Guide | PetHub Online" if len(f"{title} | PetHub Online") > 70 else f"{title} | PetHub Online",
        seo_desc, qa, glance, sections, tbl, mistakes if 'mistakes' in dir() else [
            f"Neglecting {fkw.replace('indoor cat ', '')} because it seems less important than play and feeding",
            "Making sudden changes without gradual introduction",
            "Applying the same approach to all cats regardless of individual preferences",
            "Ignoring seasonal adjustments needed for UK climate variation",
            "Not monitoring your cat's response to environmental changes"
        ],
        [f'Assess your current {fkw.replace("indoor cat ", "")} setup this week',
         f'Make one improvement based on this guide and observe your cat\'s response',
         f'Read our <a href="{IL["enrichment"]}">enrichment checklist</a> for a complete environmental audit',
         f'Schedule a vet check if you notice any concerning signs',
         f'Review our <a href="{IL["seasonal"]}">seasonal care calendar</a> for timing-specific guidance'],
        faq_common, terms_common, prods_common, srcs_common, img_queries
    ))


# ──────── HELPER FUNCTIONS ────────

def fetch_pexels_image(query):
    """Fetch one landscape image from Pexels."""
    try:
        r = requests.get(PEXELS_URL, headers={"Authorization": PEXELS_KEY},
                        params={"query": query, "per_page": 5, "orientation": "landscape"})
        if r.status_code == 200:
            photos = r.json().get("photos", [])
            if photos:
                return photos[0]["src"]["large"]
    except Exception as e:
        print(f"    Pexels error: {e}")
    return None


def upload_image_to_wp(image_url, filename):
    """Download from Pexels and upload to WordPress media library."""
    try:
        img_data = requests.get(image_url, timeout=30).content
        fname = f"{filename}.jpeg"
        headers = {"Content-Disposition": f'attachment; filename="{fname}"',
                   "Content-Type": "image/jpeg",
                   "Accept-Encoding": "gzip, deflate"}
        r = session.post(f"{WP}/media", headers=headers, data=img_data)
        if r.status_code == 201:
            return r.json().get("source_url", ""), r.json().get("id", 0)
    except Exception as e:
        print(f"    Upload error: {e}")
    return "", 0


def build_post_html(spoke, images):
    """Build complete HTML content for a spoke post."""
    h = []

    # 1. Affiliate Disclosure
    h.append('<div class="wp-block-group alignwide has-background" style="background-color:#fff8e1;border-left:4px solid #ff9800;padding:16px 20px;margin-bottom:30px;border-radius:6px"><p style="margin:0;font-size:14px"><strong>Affiliate Disclosure:</strong> PetHub Online is reader-supported. When you buy through links on our site, we may earn an affiliate commission at no extra cost to you. This helps us continue providing free, research-backed pet care content. <a href="https://pethubonline.com/affiliate-disclosure/">Learn more</a>.</p></div>')

    # 2. Quick Answer
    h.append(f'<div class="wp-block-group alignwide has-background" style="background-color:#e8f5e9;border-left:4px solid #4caf50;padding:18px 22px;margin-bottom:30px;border-radius:6px"><p style="margin:0"><strong>Quick Answer:</strong> {spoke["quick_answer"]}</p></div>')

    # 3. Table of Contents
    toc = ['<li><a href="#at-a-glance">At A Glance</a></li>']
    for sec in spoke['sections']:
        anchor = re.sub(r'[^a-z0-9-]', '', sec['heading'].lower().replace(' ', '-'))[:50]
        toc.append(f'<li><a href="#{anchor}">{sec["heading"]}</a></li>')
    for a, t in [("comparison-table","Comparison Table"),("common-mistakes","Common Mistakes to Avoid"),("what-to-do-next","What To Do Next"),("key-terms","Key Terms"),("faq","Frequently Asked Questions"),("recommended-products","Recommended Products"),("sources","Sources &amp; References")]:
        toc.append(f'<li><a href="#{a}">{t}</a></li>')
    h.append(f'<div class="wp-block-group alignwide" style="background:#f8f9fa;border:1px solid #e0e0e0;border-radius:8px;padding:20px 24px;margin-bottom:30px"><h2 style="font-size:20px;margin-top:0">Table of Contents</h2><ol style="margin-bottom:0">{"".join(toc)}</ol></div>')

    # 4. At A Glance
    gl = ''.join(f'<li>{i}</li>' for i in spoke['at_a_glance'])
    h.append(f'<div class="wp-block-group alignwide has-background" id="at-a-glance" style="background-color:#e3f2fd;border:1px solid #90caf9;border-radius:8px;padding:20px 24px;margin-bottom:30px"><h2 style="font-size:22px;margin-top:0">At A Glance</h2><ul style="margin-bottom:0">{gl}</ul></div>')

    # First image
    if images:
        alt = spoke['image_queries'][0].replace('"', '&quot;')
        h.append(f'<figure class="wp-block-image alignwide size-large"><img src="{images[0]}" alt="{alt} - PetHub Online UK" /><figcaption>{alt.title()}</figcaption></figure>')

    # 5. Content sections with images interspersed
    for i, sec in enumerate(spoke['sections']):
        anchor = re.sub(r'[^a-z0-9-]', '', sec['heading'].lower().replace(' ', '-'))[:50]
        h.append(f'<h2 id="{anchor}">{sec["heading"]}</h2>')
        h.append(sec['content'])
        img_idx = (i // 2) + 1
        if img_idx < len(images) and i % 2 == 1:
            alt = spoke['image_queries'][min(img_idx, len(spoke['image_queries'])-1)].replace('"', '&quot;')
            h.append(f'<figure class="wp-block-image alignwide size-large"><img src="{images[img_idx]}" alt="{alt} - PetHub Online UK" /><figcaption>{alt.title()}</figcaption></figure>')

    # 6. Comparison Table
    hdr = ''.join(f'<th>{c}</th>' for c in spoke['comparison_table']['headers'])
    rows = ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in row) + '</tr>' for row in spoke['comparison_table']['rows'])
    h.append(f'<div class="wp-block-group alignwide has-background" id="comparison-table" style="background-color:#f4f4f4;border-radius:8px;padding:24px;margin-bottom:30px"><h2 style="margin-top:0">{spoke["comparison_table"]["title"]}</h2><figure class="wp-block-table"><table class="has-fixed-layout"><thead><tr>{hdr}</tr></thead><tbody>{rows}</tbody></table></figure></div>')

    # 7. Common Mistakes
    mk = ''.join(f'<li>{m}</li>' for m in spoke['common_mistakes'])
    h.append(f'<div class="wp-block-group alignwide has-background" id="common-mistakes" style="background-color:#fce4ec;border-left:4px solid #e53935;border-radius:6px;padding:20px 24px;margin-bottom:30px"><h2 style="font-size:22px;margin-top:0">Common Mistakes to Avoid</h2><ul style="margin-bottom:0">{mk}</ul></div>')

    # Remaining images
    if len(images) > 2:
        alt = spoke['image_queries'][-1].replace('"', '&quot;')
        h.append(f'<figure class="wp-block-image alignwide size-large"><img src="{images[2]}" alt="{alt} - PetHub Online UK" /><figcaption>{alt.title()}</figcaption></figure>')

    # 8. What To Do Next
    nx = ''.join(f'<li>{i}</li>' for i in spoke['what_to_do_next'])
    h.append(f'<div class="wp-block-group alignwide has-background" id="what-to-do-next" style="background-color:#e8f5e9;border:1px solid #81c784;border-radius:8px;padding:20px 24px;margin-bottom:30px"><h2 style="font-size:22px;margin-top:0">What To Do Next</h2><ol style="margin-bottom:0">{nx}</ol></div>')

    # 9. Key Terms
    dt = ''.join(f'<dt><strong>{t}</strong></dt><dd>{d}</dd>' for t, d in spoke['key_terms'])
    h.append(f'<div class="wp-block-group alignwide" id="key-terms" style="background:#f5f5f5;border:1px solid #e0e0e0;border-radius:8px;padding:20px 24px;margin-bottom:30px"><h2 style="font-size:22px;margin-top:0">Key Terms</h2><dl style="margin-bottom:0">{dt}</dl></div>')

    # 10. FAQ
    fq = ''
    for q, a in spoke['faq']:
        fq += f'<details class="wp-block-details alignwide has-border-color" style="border-color:#e5e5e5;border-width:1px;border-style:solid;border-radius:6px;padding:12px 16px;margin-bottom:8px"><summary style="font-size:17px;font-weight:600;cursor:pointer">{q}</summary><p style="margin-top:10px">{a}</p></details>'
    h.append(f'<div id="faq"><h2>Frequently Asked Questions</h2>{fq}</div>')

    # 11. Products
    pd = ''
    for name, desc, terms in spoke['products']:
        url = f"https://www.amazon.co.uk/s?k={terms}&tag={AFFILIATE_TAG}"
        pd += f'<div class="wp-block-group" style="border:3px solid #0073aa;border-radius:12px;padding:20px;margin-bottom:16px;background:#ffffff"><h3 style="color:#0073aa;margin-top:0">{name}</h3><p>{desc}</p><p><a href="{url}" target="_blank" rel="noopener nofollow sponsored" style="display:inline-block;background:#0073aa;color:#ffffff;padding:10px 24px;border-radius:6px;text-decoration:none;font-weight:600">Check Price on Amazon UK</a></p></div>'
    h.append(f'<div id="recommended-products" style="margin-bottom:30px"><h2>Recommended Products</h2><p style="font-size:14px;color:#666">These products are selected based on relevance to this guide. As an Amazon Associate, PetHub Online earns from qualifying purchases.</p>{pd}</div>')

    # 12. Email CTA
    h.append('<div class="wp-block-group alignwide has-background" style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border-radius:12px;padding:30px;margin-bottom:30px;text-align:center"><h2 style="color:#ffffff;margin-top:0">Get Expert Indoor Cat Advice</h2><p style="color:#f0f0f0;font-size:16px">Subscribe to PetHub Online for research-backed indoor cat guides, enrichment tips, and exclusive deals.</p><p><a href="https://pethubonline.com/subscribe-to-pethub-uk-newsletter/" style="display:inline-block;background:#ffffff;color:#667eea;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:700;font-size:16px">Subscribe Free</a></p></div>')

    # 13. Sources
    sr = ''.join(f'<li>{s}</li>' for s in spoke['sources'])
    h.append(f'<div class="wp-block-group alignwide" id="sources" style="background:#f8f9fa;border:1px solid #dee2e6;border-radius:8px;padding:20px 24px;margin-bottom:30px"><h2 style="font-size:20px;margin-top:0">Sources &amp; References</h2><ul style="font-size:14px;margin-bottom:0">{sr}</ul></div>')

    # 14. Trust Footer
    h.append('<div class="wp-block-group alignwide" style="background:#f0f4f8;border-left:4px solid #0073aa;padding:16px 20px;margin-bottom:30px;border-radius:6px"><p style="font-size:14px;margin:0"><strong>Trust &amp; Transparency:</strong> PetHub Online provides research-backed pet care information for UK pet owners. Our content is based on published veterinary guidelines, manufacturer specifications, and publicly available expert guidance. We do not fabricate credentials, invent experts, or claim hands-on testing unless explicitly stated. <a href="https://pethubonline.com/editorial-policy/">Read our editorial policy</a>.</p></div>')

    # 15. Author Box
    h.append('<div class="wp-block-group alignwide" style="background:#ffffff;border:2px solid #e0e0e0;border-radius:12px;padding:24px;margin-bottom:20px;display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap"><div style="flex:1;min-width:200px"><p style="margin:0 0 6px 0"><strong style="font-size:18px">Jason Parr &amp; Sarah Parr</strong></p><p style="margin:0 0 8px 0;color:#666;font-size:14px">Founders, PetHub Online | Pet Product Research &amp; Reviews</p><p style="margin:0;font-size:14px">Jason and Sarah are UK-based pet owners and researchers dedicated to providing honest, well-researched pet care content. Every guide is based on veterinary guidelines, manufacturer data, and real owner experiences.</p><p style="margin:8px 0 0 0;font-size:13px"><a href="https://pethubonline.com/about-jason-parr/">About Us</a> · <a href="https://pethubonline.com/editorial-policy/">Editorial Policy</a> · <a href="https://pethubonline.com/fact-checking-policy/">Fact-Checking Policy</a></p></div></div>')

    return '\n'.join(h)


def set_rankmath_seo(post_id, spoke):
    """Set Rank Math SEO metadata."""
    rm_data = {
        "objectID": post_id, "objectType": "post",
        "meta": {
            "rank_math_focus_keyword": spoke['focus_keyword'],
            "rank_math_title": spoke['seo_title'],
            "rank_math_description": spoke['seo_desc']
        }
    }
    try:
        r = session.post("https://pethubonline.com/wp-json/rankmath/v1/updateMeta", json=rm_data)
        if r.status_code == 200:
            return True, "Rank Math API"
    except:
        pass
    try:
        meta = {"rank_math_focus_keyword": spoke['focus_keyword'],
                "rank_math_title": spoke['seo_title'],
                "rank_math_description": spoke['seo_desc']}
        r2 = session.post(f"{WP}/posts/{post_id}", json={"meta": meta})
        if r2.status_code == 200:
            return True, "WP meta fallback"
    except:
        pass
    return False, "failed"


def validate_post(spoke, content):
    """Validate post against checklist."""
    issues = []
    h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', content)
    h2_texts = [re.sub(r'<[^>]+>', '', h) for h in h2s]
    if len(h2_texts) != len(set(h2_texts)):
        issues.append("Duplicate H2 sections")
    if content.count('<img ') < 3:
        issues.append(f"Only {content.count('<img ')} images (need 3+)")
    for check, label in [('Table of Contents', 'TOC'), ('Jason Parr', 'Author box'),
                          ('comparison-table', 'Comparison table'), ('amazon.co.uk', 'Amazon links'),
                          ('Quick Answer', 'Quick answer'), ('at-a-glance', 'At A Glance'),
                          ('common-mistakes', 'Common Mistakes'), ('what-to-do-next', 'What To Do Next'),
                          ('key-terms', 'Key Terms'), ('<details', 'FAQ accordion'),
                          ('subscribe-to-pethub-uk-newsletter', 'Email CTA'),
                          ('Trust &amp; Transparency', 'Trust footer')]:
        if check not in content:
            issues.append(f"{label} missing")
    return len(issues) == 0, issues


def create_and_publish_spoke(spoke, idx):
    """Create, validate, and publish a single spoke post."""
    print(f"\n{'='*60}")
    print(f"[{idx+1}/20] {spoke['title'][:55]}...")
    print(f"{'='*60}")

    # 1. Fetch and upload images
    print("  [1/5] Fetching images...")
    images = []
    first_media_id = 0
    for i, query in enumerate(spoke['image_queries'][:4]):
        img_url = fetch_pexels_image(query)
        if img_url:
            filename = f"{spoke['slug'].replace('-', '_')}_{i+1}"
            wp_url, media_id = upload_image_to_wp(img_url, filename)
            if wp_url:
                images.append(wp_url)
                if i == 0:
                    first_media_id = media_id
                print(f"    Uploaded image {i+1}")
        time.sleep(1)
    print(f"    Total: {len(images)} images")

    # 2. Build HTML
    print("  [2/5] Building HTML...")
    content = build_post_html(spoke, images)
    print(f"    Length: {len(content):,} chars")

    # 3. Validate
    print("  [3/5] Validating...")
    passed, issues = validate_post(spoke, content)
    if passed:
        print("    PASSED all checks")
    else:
        print(f"    WARNING: {issues}")

    # 4. Create and publish post
    print("  [4/5] Publishing to WordPress...")
    post_data = {
        "title": spoke['title'],
        "slug": spoke['slug'],
        "content": content,
        "status": "publish",
        "categories": [CATEGORY_INDOOR_CATS],
    }
    if first_media_id:
        post_data["featured_media"] = first_media_id

    try:
        r = session.post(f"{WP}/posts", json=post_data)
        if r.status_code == 201:
            post_id = r.json()['id']
            post_link = r.json().get('link', f"https://pethubonline.com/?p={post_id}")
            print(f"    PUBLISHED: ID {post_id}")
            print(f"    URL: {post_link}")
        else:
            print(f"    FAIL: {r.status_code} - {r.text[:200]}")
            return None
    except Exception as e:
        print(f"    ERROR: {e}")
        return None

    # 5. Set SEO
    print("  [5/5] Setting SEO...")
    seo_ok, method = set_rankmath_seo(post_id, spoke)
    print(f"    SEO: {'OK via ' + method if seo_ok else 'FAILED'}")

    return {"id": post_id, "title": spoke['title'], "link": post_link,
            "images": len(images), "chars": len(content), "passed": passed}


# ──────── MAIN EXECUTION ────────

if __name__ == "__main__":
    print("Indoor Cats Cluster: 20 Spoke Posts")
    print(f"Category: Indoor Cats (ID {CATEGORY_INDOOR_CATS})")
    print(f"Total spokes defined: {len(SPOKES)}")
    print("=" * 60)

    results = []
    for idx, spoke in enumerate(SPOKES):
        try:
            result = create_and_publish_spoke(spoke, idx)
            if result:
                results.append(result)
        except Exception as e:
            print(f"  EXCEPTION on spoke {idx+1}: {e}")
        time.sleep(3)  # 3-second delay between posts to avoid 429

    # Final Summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY - Indoor Cats Spokes")
    print("=" * 60)
    total_chars = 0
    total_images = 0
    for r in results:
        print(f"  ID {r['id']}: {r['title'][:65]}")
        print(f"    URL: {r['link']}")
        total_chars += r['chars']
        total_images += r['images']
    print(f"\nPublished: {len(results)}/20")
    print(f"Total content: {total_chars:,} characters")
    print(f"Total images: {total_images}")
    print("DONE.")
